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


def model_plan(kind, subject_ids, **changes):
    operation = {"operation_id": "model:synthetic", "kind": kind, "subject_ids": subject_ids,
                 "query_layer": "evidence", **changes}
    return {"query": "Synthetic model operation.", "status": "ready", "diagnostics": [],
        "unresolved_selectors": [], "resolved_entities": subject_ids, "operations": [operation],
        "coverage_authority": "MODEL_PROPOSED_UNVERIFIED", "requested_parts": [{"id": "synthetic:part",
            "text": "Synthetic operation.", "kind": kind, "subject_ids": subject_ids,
            "operation_ids": [operation["operation_id"]], "status": "planned"}]}


def test_evidence_relations_render_bound_store_assertion_status_and_rules(prepared):
    from src.evidence_a1_graph_qa import execute_graph_plan
    graph, store = prepared
    result = execute_graph_plan(graph, model_plan("evidence", ["toy:child"]), complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    support = operation["relation_support"]
    accepted = [item for item in support if item["type"] == "ENCLOSES_ROW"]
    candidate = [item for item in support if item["type"] == "INDENTED_UNDER"]
    assert accepted and all(item["assertions"][0]["status"] == "ACCEPTED" for item in accepted)
    assert candidate and candidate[0]["assertions"][0]["status"] == "CANDIDATE"
    assert all(assertion["support_evidence_ids"] and assertion["rule_id"]
               for item in support for assertion in item["assertions"])
    assert "ACCEPTED CHART_MEMBER_OF" in result["answer"]
    assert "CANDIDATE CANDIDATE_LAYOUT_PARENT" in result["answer"]
    assert "source-layout-1" in result["answer"]
    assert operation["query_layer"] == "evidence"
    assert operation["accepted_assertion_ids"] == []


def test_exact_accepted_structural_path_is_separate_from_evidence_query_layer(prepared):
    from src.evidence_a1_graph_qa import execute_graph_plan
    graph, store = prepared
    result = execute_graph_plan(graph, model_plan("paths", ["toy:parent", "toy:root"],
        requested_direction="from_to", start_ids=["toy:parent"], end_ids=["toy:root"], waypoint_ids=[]),
        complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    assert operation["query_layer"] == "evidence"
    assert operation["knowledge_paths"] == []
    assert len(operation["accepted_structural_paths"]) == 1
    path = operation["accepted_structural_paths"][0]
    assert path["node_ids"] == ["toy:parent", "toy:family", "toy:root"]
    assert len(path["edge_assertion_ids"]) == 2
    assert path["literal_assertion_ids"] and path["semantic_validation"] is False
    assert set(path["evidence_ids"]) <= {item["proof"]["evidence_id"]
        for item in operation["knowledge_support"]["observations"]}
    assert result["accepted_structural_paths"] == operation["accepted_structural_paths"]


def test_candidate_path_never_gets_an_alternate_accepted_projection(prepared):
    from src.evidence_a1_graph_qa import execute_graph_plan
    graph, store = prepared
    result = execute_graph_plan(graph, model_plan("paths", ["toy:child", "toy:root"],
        requested_direction="from_to", start_ids=["toy:child"], end_ids=["toy:root"], waypoint_ids=[]),
        complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    assert any("INDENTED_UNDER" in path["edge_types"] for path in operation["paths"])
    assert operation["accepted_structural_paths"] == []
    assert operation["query_layer"] == "evidence"


def test_accepted_projection_requires_every_literal_and_actual_support(prepared):
    from src.evidence_a1_graph_qa import _GraphView, _accepted_structural_paths, _operation
    graph, store = prepared
    view = _GraphView(graph)
    result = _operation(view, {"kind": "paths", "subject_ids": ["toy:parent", "toy:root"],
        "requested_direction": "from_to", "start_ids": ["toy:parent"], "end_ids": ["toy:root"], "waypoint_ids": []}, True)
    records = result["trace"]["visited_node_ids"] + [edge["id"] for edge in result["trace"]["selected_edges"]]
    support = store.support_for(record_ids=records)
    assert _accepted_structural_paths(view, result, support)
    disputed = deepcopy(support)
    next(item for item in disputed["assertions"] if item["predicate"] == "PRINTED_DESIGNATION")["status"] = "DISPUTED"
    assert _accepted_structural_paths(view, result, disputed) == []
    missing = deepcopy(support)
    missing["observations"] = []
    assert _accepted_structural_paths(view, result, missing) == []


def test_compilation_block_does_not_read_operation_assertion_support(prepared, monkeypatch):
    from src.evidence_a1_graph_qa import execute_graph_plan
    graph, store = prepared
    def forbidden(*args, **kwargs):
        pytest.fail("Blocked operation must not query assertion support")
    monkeypatch.setattr(store, "support_for", forbidden)
    result = execute_graph_plan(graph, model_plan("unsupported", [], compilation_errors=["UNKNOWN_OPERATION"]),
        complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    assert operation["graph_executed"] is False
    assert operation["execution_status"] == "blocked"
    assert operation["knowledge_support"]["assertions"] == []


def test_model_path_has_named_semantic_nonentailment_and_only_returned_placements(prepared):
    from src.evidence_a1_graph_qa import execute_graph_plan
    graph, store = prepared
    plan = model_plan("paths", ["toy:parent", "toy:root"], requested_direction="from_to",
                      start_ids=["toy:parent"], end_ids=["toy:root"], waypoint_ids=[])
    original = deepcopy(plan)
    result = execute_graph_plan(graph, plan, complete_chart=True, knowledge_store=store)
    judgment = result["relationship_judgments"][0]
    assert judgment["verdict"] == "not_established_by_this_path"
    assert judgment["start_id"] == "toy:parent" and judgment["end_id"] == "toy:root"
    assert judgment["positive_placements"][0]["process_id"] == "toy:parent"
    assert judgment["positive_placements"][0]["category_id"] == "toy:family"
    assert "Ribbon fold" in result["answer"] and "Toy chart" in result["answer"]
    assert "does not establish a reviewed semantic subtype relation" in result["answer"]
    assert result["operations"][0]["kind"] == "paths"
    assert result["operations"][0]["query_layer"] == "evidence"
    assert plan == original


def test_path_judgment_keeps_separate_semantic_assertions_and_avoids_unreturned_enclosures(prepared):
    from src.evidence_a1_graph_qa import _GraphView, _model_path_judgments, execute_graph_plan
    graph, store = prepared
    result = execute_graph_plan(graph, model_plan("paths", ["toy:child", "toy:parent"],
        requested_direction="from_to", start_ids=["toy:child"], end_ids=["toy:parent"], waypoint_ids=[]),
        complete_chart=True, knowledge_store=store)
    operation = deepcopy(result["operations"][0])
    labels = {item["origin_record_ids"][0]: item["subject_id"] for item in operation["knowledge_support"]["assertions"]
              if item["predicate"] == "PRINTED_LABEL"}
    # A synthetic returned-ledger entry tests separation; it is never admitted to the store.
    operation["knowledge_support"]["assertions"].append({"assertion_id": "synthetic:separate-semantic",
        "predicate": "IS_A", "status": "ACCEPTED", "subject_id": labels["toy:child"],
        "object_value": labels["toy:parent"], "support_evidence_ids": [], "counter_evidence_ids": []})
    judgments, text = _model_path_judgments(_GraphView(graph), operation)
    assert judgments[0]["positive_placements"] == []
    assert judgments[0]["separate_semantic_assertions"][0]["assertion_id"] == "synthetic:separate-semantic"
    assert "separate ACCEPTED IS_A assertion" in text
    assert judgments[0]["verdict"] == "not_established_by_this_path"


def test_arrow_limit_uses_retained_undirected_connector_and_selected_proofs(prepared):
    from types import SimpleNamespace
    from src.evidence_a1_graph_qa import _model_connector_limit, execute_graph_plan
    graph, store = prepared
    result = execute_graph_plan(graph, model_plan("physical_neighbors", ["toy:root"]),
        complete_chart=True, knowledge_store=store)
    operation = result["operations"][0]
    view = SimpleNamespace(graph={"raster_verification": {"connector_receipt": {"direction": "undirected"}}})
    limit, text = _model_connector_limit(view, operation)
    assert limit["retained_direction"] == "undirected"
    assert limit["evidence_ids"]
    assert "do not establish arrow direction" in text
    assert "no arrowheads" not in text and "detected" not in text
    unsupported = deepcopy(operation)
    unsupported["knowledge_support"]["observations"] = []
    assert _model_connector_limit(view, unsupported) == (None, "")
