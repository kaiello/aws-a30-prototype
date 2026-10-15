"""
test_hybrid_retrieval.py: Unit and integration tests for SQLite FTS5 BM25 search,
1024-dim BGE-Large dense search, Reciprocal Rank Fusion, and Annex B complete figure retrieval.
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.hybrid_retriever import (
    search_fts_chunks,
    search_dense_chunks,
    reciprocal_rank_fusion,
    hybrid_retrieve
)

def test_fts_chunks_search():
    results = search_fts_chunks("complete joint penetration", top_k=5)
    assert len(results) > 0
    # Must retrieve Clause 4 chunk mentioning complete joint penetration
    contents = " ".join(r["content"].lower() for r in results)
    assert "complete joint penetration" in contents

def test_dense_chunks_search():
    results = search_dense_chunks("gas tungsten arc welding electrode", top_k=5)
    assert len(results) > 0
    assert results[0]["score"] > 0.4
    assert len(results[0]["content"]) > 20

def test_reciprocal_rank_fusion():
    sparse_hits = [
        {"id": "doc_a", "content": "A"},
        {"id": "doc_b", "content": "B"},
        {"id": "doc_c", "content": "C"}
    ]
    dense_hits = [
        {"id": "doc_b", "content": "B"},
        {"id": "doc_a", "content": "A"},
        {"id": "doc_d", "content": "D"}
    ]
    fused = reciprocal_rank_fusion(sparse_hits, dense_hits, k=60, top_candidates=4)
    # doc_a: 1/61 + 1/62 = 0.01639 + 0.01613 = 0.03252
    # doc_b: 1/62 + 1/61 = 0.03252 (tied)
    # both doc_a and doc_b must rank ahead of doc_c and doc_d
    top_2_ids = {fused[0]["id"], fused[1]["id"]}
    assert top_2_ids == {"doc_a", "doc_b"}
    assert fused[0]["rrf_score"] > fused[2]["rrf_score"]

def test_hybrid_retrieve_fillet_weld_figure_b25():
    results = hybrid_retrieve("throat of a fillet weld in Figure B25", top_k=5)
    assert len(results) >= 3
    doc_ids = [r.get("full_doc_id", "") for r in results]
    # Verify that either Clause 4 definition or Figure B25 is in top hits
    assert any("figure_b25" in d.lower() or "clause_4_p25" in d.lower() for d in doc_ids)

def test_hybrid_retrieve_previously_missing_figures():
    # Test Figure B39 (Metal transfer modes in GMAW) - previously missing
    res_b39 = hybrid_retrieve("metal transfer modes in gas metal arc welding Figure B39", top_k=5)
    doc_ids_b39 = [r.get("full_doc_id", "").lower() for r in res_b39]
    assert any("b39" in d for d in doc_ids_b39)

    # Test Figure B40 (Oxyfuel gas cutting flame types) - previously missing
    res_b40 = hybrid_retrieve("carburizing oxidizing neutral flame Figure B40", top_k=5)
    doc_ids_b40 = [r.get("full_doc_id", "").lower() for r in res_b40]
    assert any("b40" in d for d in doc_ids_b40)

    # Test Figure B46 (Friction stir welding tool anatomy) - previously missing
    res_b46 = hybrid_retrieve("friction stir welding tool anatomy Figure B46", top_k=5)
    doc_ids_b46 = [r.get("full_doc_id", "").lower() for r in res_b46]
    assert any("b46" in d for d in doc_ids_b46)
