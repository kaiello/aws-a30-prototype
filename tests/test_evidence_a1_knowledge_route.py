"""Actual persisted layer selection over invented chart facts, no owner gold."""
from copy import deepcopy
import sqlite3

import pytest

from test_evidence_a1_provenance import fixture
from src.evidence_a1 import bind_a1_graph_evidence
from src.evidence_a1_graph_qa import answer_graph
from src.evidence_a1_knowledge import prepare_a1_knowledge


@pytest.fixture
def prepared(tmp_path):
    graph, source = fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    registry = tmp_path / "storage/dual_layer_registry.db"
    registry.parent.mkdir()
    with sqlite3.connect(registry) as connection:
        connection.execute("CREATE TABLE synthetic_legacy_registry (id TEXT PRIMARY KEY)")
    before = registry.read_bytes()
    store = prepare_a1_knowledge(tmp_path, bound)
    assert registry.read_bytes() == before
    return bound, store


def test_auto_designation_executes_persisted_accepted_assertions(prepared):
    graph, store = prepared
    original = deepcopy(graph)
    result = answer_graph(graph, "What does ZZP stand for?", complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    assert operation["query_layer"] == "knowledge"
    assert operation["knowledge_support"]["assertions"]
    assert all(a["status"] == "ACCEPTED" for a in operation["knowledge_support"]["assertions"])
    assert "Pulsed fold" in result["answer"]
    assert result["source_binding_status"] != "canonical_source_and_image_validated"
    assert graph == original


def test_evidence_candidate_is_not_accepted_semantic_knowledge(prepared):
    graph, store = prepared
    query = "Is Pulsed fold a subtype of Ribbon fold?"
    evidence = answer_graph(graph, query, complete_chart=True, knowledge_store=store, query_layer="evidence")
    knowledge = answer_graph(graph, query, complete_chart=True, knowledge_store=store, query_layer="knowledge")
    assert evidence["verdict"] == knowledge["verdict"] == "not_established"
    assert "candidate" in evidence["answer"].lower()
    assert knowledge["answer_outcome"] == "insufficient_evidence"
    assert all(a["status"] == "ACCEPTED" for op in knowledge["operations"]
               for a in op["knowledge_support"]["assertions"])


def test_accepted_multihop_has_assertion_and_full_evidence_paths(prepared):
    graph, store = prepared
    query = "Show the path from Pulsed fold to ALPHA."
    # Use the exact complete synthetic category selector rather than infer an alias.
    query = query.replace("ALPHA.", "ALPHA (AF).")
    result = answer_graph(graph, query, complete_chart=True, knowledge_store=store, query_layer="knowledge")
    assert result["answer_outcome"] == "graph_answer"
    operation = next(op for op in result["operations"] if op["kind"] == "paths")
    assert operation["knowledge_paths"]
    path = operation["knowledge_paths"][0]
    assert len(path["concept_ids"]) == len(path["assertion_ids"]) + 1
    assert path["evidence_ids"]
    assert all(a["predicate"] != "CANDIDATE_LAYOUT_PARENT" for a in operation["knowledge_support"]["assertions"])
    proof = operation["knowledge_support"]
    assert set(path["evidence_ids"]) <= {item["proof"]["evidence_id"] for item in proof["observations"]}


def test_unadmitted_process_descendants_do_not_become_a_complete_empty_answer(prepared):
    graph, store = prepared
    result = answer_graph(graph, "List all descendants of Ribbon fold.", complete_chart=True,
                          knowledge_store=store, query_layer="knowledge")
    assert result["answer_outcome"] == "insufficient_evidence"
    assert "not_admitted" in " ".join(result["trace"]["diagnostics"])
    assert not any(op.get("expansion", {}).get("status") == "complete_within_supplied_chart"
                   for op in result["operations"])
