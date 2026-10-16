from src.epistemic_verifier import _decision_status
"""Existing metadata consumers, tested without running extraction or graph code."""
import ast
import importlib.util
from pathlib import Path
import sys
import types
from unittest.mock import patch
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import re
import pytest

from src.standard_manifest import get_manifest
from src.citation_checker import extract_citations

ROOT = Path(__file__).resolve().parents[1]


def test_config_offsets_are_source_indices_without_reading_dotenv():
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: False
    spec = importlib.util.spec_from_file_location("isolated_manifest_config", ROOT / "src/config.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"dotenv": dotenv}):
        spec.loader.exec_module(module)
    assert module.GLOSSARY_START_PAGE == 17
    assert module.ANNEX_A_START_PAGE == 81
    assert module.ANNEX_B_START_PAGE == 93
    assert module.ANNEX_B_END_PAGE == 169
    assert module.EMBEDDING_DIM == 1024


def test_graph_constants_project_existing_ids_and_actual_pages():
    tree = ast.parse((ROOT / "src/build_dual_graph.py").read_text(encoding="utf-8"))
    names = {"DOCUMENT_META", "STANDARD_CLAUSES", "STANDARD_TABLES"}
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") in names for t in n.targets)]
    ns = {"get_manifest": get_manifest}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual_graph_metadata", "exec"), ns)
    assert ns["DOCUMENT_META"]["total_pages"] == 190
    assert len(ns["STANDARD_TABLES"]) == 11
    assert next(t for t in ns["STANDARD_TABLES"] if t["id"] == "table:table_d2")["page"] == "167-168"
    assert next(c for c in ns["STANDARD_CLAUSES"] if c["id"] == "clause:clause_4")["pages"] == "5-68"


def test_cached_graph_pages_cannot_override_source_locations():
    tree = ast.parse((ROOT / "src/answer_routes.py").read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_apply_source_metadata")
    ns = {"get_manifest": get_manifest, "FIGURE_INSPECTORS": {}, "Path": Path}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "actual_evidence_overlay", "exec"), ns)
    item = types.SimpleNamespace(evidence_type="figure", element_id="FIGURE B6", page="999",
                                 file_path="untrusted-cache.png", callout_chips=[], metadata={})
    ns[fn.name](item)
    assert item.element_id == "Figure B6"
    assert item.page == "87-89"
    assert Path(item.file_path).name == "Figure_B6_p99.png"
    assert [a["pdf_index"] for a in item.metadata["source_anchors"]] == [99, 100, 101]
    assert item.metadata["source_anchors"][0]["normative_status"] == "conflicting"


@pytest.mark.parametrize("label,node_type,expected", [
    ("Figure B16", "Figure", "INSUFFICIENT_EVIDENCE"),
    ("Figure B55", "Figure", "INSUFFICIENT_EVIDENCE"),
    ("Figure B1.5", "Figure", "INSUFFICIENT_EVIDENCE"),
    ("Table A10", "Table", "INSUFFICIENT_EVIDENCE"),
    ("Table A1.5", "Table", "INSUFFICIENT_EVIDENCE"),
    ("Figure B6", "Figure", "INSUFFICIENT_EVIDENCE"),
])
def test_unknown_cached_elements_cannot_satisfy_route_grounding(label, node_type, expected):
    tree = ast.parse((ROOT / "src/answer_routes.py").read_text(encoding="utf-8"))
    names = {"EvidenceItem", "AnswerRoute", "_apply_source_metadata", "_clean_term_for_fts", "resolve_answer_route"}
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]

    class Cursor:
        statement = ''
        def execute(self, statement, *args):
            self.statement = statement
        def fetchall(self):
            if 'FROM ontology_nodes' in self.statement:
                return [('concept:fixture', 'fixture weld', 'Term', 'preferred', 'Synthetic description')]
            return [('ILLUSTRATED_BY', 'candidate', 'fixture:evidence', node_type, label, '999', 'untrusted.png', '')]

    cursor = Cursor()
    connection = types.SimpleNamespace(cursor=lambda: cursor, close=lambda: None)
    ns = dict(globals(), get_manifest=get_manifest, FIGURE_INSPECTORS={}, check_abstention=lambda x: False,
              sqlite3=types.SimpleNamespace(connect=lambda p: connection),
              DUAL_SQLITE_PATH=types.SimpleNamespace(exists=lambda: True),
              PARSED_FIGURES_DIR=ROOT / 'parsed/figures', PARSED_TABLES_DIR=ROOT / 'parsed/tables',
              os=types.SimpleNamespace(path=types.SimpleNamespace(exists=lambda p: False)))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual_route_with_synthetic_rows", "exec"), ns)
    route = ns['resolve_answer_route']('Show fixture weld figure or table')
    assert route.status == expected
    assert not route.all_evidence_recovered
    assert route.evidence_recall_score is None
    if label != 'Figure B6':
        assert not route.all_evidence_recovered
        assert route.evidence_group[0].page is None
        assert route.evidence_group[0].file_path is None
        assert route.evidence_group[0].metadata['source_location_verification'] == 'legacy_unverified'

    else:
        assert route.evidence_group[0].metadata['source_location_verification'] == 'verified'
        assert route.evidence_group[0].page == '87-89'
        assert route.evidence_group[0].metadata['source_anchors']
