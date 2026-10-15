"""Golden pre-adapter expansion and injected retrieval behavior; no stores/models."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Dict, Any, List, Optional

import pytest
from src.standard_manifest import extract_references, _reference_groups

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/manifest_retrieval_baseline.json').read_text(encoding='utf-8'))


def actual_functions(filename, names, namespace):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names or
             isinstance(n, ast.Assign) and any(getattr(t, 'id', '') in names for t in n.targets)]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), namespace)
    return namespace


@pytest.mark.parametrize('case', FIXTURE['cases'], ids=lambda c: c['query'])
@pytest.mark.parametrize('rerank', [False, True])
def test_valid_enrichment_candidate_ids_order_and_scores_unchanged(case, rerank, tmp_path):
    namespace = dict(globals(), DUAL_SQLITE_PATH=tmp_path / 'absent.db', extract_references=extract_references,
                     get_terminology_evidence=lambda query: None)
    actual_functions('src/pre_retrieval.py', {'WELDING_ACRONYMS', 'extract_referenced_elements', 'expand_query'}, namespace)
    assert namespace['expand_query'](case['query']) == case['expansion']
    sparse, dense = deepcopy(FIXTURE['sparse']), deepcopy(FIXTURE['dense'])
    searches, pairs_seen = [], []
    def sparse_search(query, top_k):
        searches.append(['sparse', query, top_k])
        return sparse
    def dense_search(query, top_k):
        searches.append(['dense', query, top_k])
        return dense
    class Reranker:
        def predict(self, pairs):
            pairs_seen.extend(pairs)
            return [FIXTURE['cross_encoder_scores'][text] for _, text in pairs]
    namespace.update(get_vdb_data=lambda: {}, search_fts_chunks=sparse_search, search_dense_chunks=dense_search,
                     get_reranker_model=lambda: Reranker() if rerank else None)
    actual_functions('src/hybrid_retriever.py', {'reciprocal_rank_fusion', 'rerank_candidates', 'hybrid_retrieve'}, namespace)
    hits = namespace['hybrid_retrieve'](case['query'], top_k=4)
    assert searches == case['searches']
    assert hits == FIXTURE['reranked_hits' if rerank else 'rrf_hits']
    expected_pairs = [(case['query'], text) for text in FIXTURE['pair_contents']] if rerank else []
    assert pairs_seen == expected_pairs
    assert sparse == FIXTURE['sparse'] and dense == FIXTURE['dense']



@pytest.mark.parametrize("expression", [
    "Figure B1-B3", "Figure B1 – B3", "Figure B1—B3", "Fig. B1 to B3",
    "Figure B1 through B3", "Table D1/D3", "Figure B16A–B16C",
])
def test_singular_enrichment_does_not_expand_or_truncate_range_expressions(expression):
    namespace = dict(globals(), extract_references=extract_references)
    actual_functions('src/pre_retrieval.py', {'extract_referenced_elements'}, namespace)
    found = namespace['extract_referenced_elements'](expression + "; Figure B4")
    assert found == {"figures": ["Figure B4"], "tables": []}


def test_singular_enrichment_keeps_existing_shorthand_and_ignores_plural_lists():
    namespace = dict(globals(), extract_references=extract_references)
    actual_functions('src/pre_retrieval.py', {'extract_referenced_elements'}, namespace)
    assert namespace['extract_referenced_elements']("FigureB6; Fig. b.16c; Table D2") == {
        "figures": ["Figure B6", "Figure B16C"], "tables": ["Table D2"]}
    assert namespace['extract_referenced_elements']("Figures B1, B2 and B3") == {"figures": [], "tables": []}


@pytest.mark.parametrize("text", [
    "Use Figure B1 to explain the weld.",
    "Follow Figure B1 through the diagram notes.",
])
def test_singular_enrichment_preserves_reference_followed_by_prose(text):
    namespace = dict(globals(), extract_references=extract_references)
    actual_functions('src/pre_retrieval.py', {'extract_referenced_elements'}, namespace)
    assert namespace['extract_referenced_elements'](text) == {"figures": ["Figure B1"], "tables": []}


@pytest.mark.parametrize("text", [
    "Figure B1 to FigureB3", "Figure B1 to Fig.B3",
    "Figure B1 through FigureB3", "Figure B1 through Fig.B3",
])
def test_singular_enrichment_rejects_whole_repeated_shorthand_range(text):
    namespace = dict(globals(), extract_references=extract_references)
    actual_functions('src/pre_retrieval.py', {'extract_referenced_elements'}, namespace)
    assert namespace['extract_referenced_elements'](text + "; Figure B4") == {
        "figures": ["Figure B4"], "tables": []}
