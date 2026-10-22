"""Request coverage over actual toy execution/persisted proof, without QA gold."""
import sqlite3

import pytest

from src.evidence_a1 import bind_a1_graph_evidence
from src.evidence_a1_knowledge import prepare_a1_knowledge
from test_evidence_a1_provenance import fixture


@pytest.fixture
def prepared(tmp_path):
    graph, source = fixture()
    graph = bind_a1_graph_evidence(graph, **source)
    registry = tmp_path / "storage/dual_layer_registry.db"
    registry.parent.mkdir()
    with sqlite3.connect(registry) as connection:
        connection.execute("CREATE TABLE toy_registry(id TEXT PRIMARY KEY)")
    return graph, prepare_a1_knowledge(tmp_path, graph)


def execute(monkeypatch, prepared, operations, parts, status="ready", **kwargs):
    import src.evidence_a1_graph_qa as qa
    graph, store = prepared
    plan = {"query": "Synthetic compound request", "status": status,
            "resolved_entities": ["toy:child"], "operations": operations,
            "requested_parts": parts, "diagnostics": [], "unresolved_selectors": []}
    monkeypatch.setattr(qa, "plan_graph_query", lambda *args, **parameters: plan)
    return qa.answer_graph(graph, plan["query"], complete_chart=True, knowledge_store=store, **kwargs)


def operation(kind, identifier):
    return {"kind": kind, "subject_ids": ["toy:child"], "operation_id": identifier,
            "request_ids": [identifier.replace("op:", "intent:")],
            "query_layer": "knowledge" if kind in {"designation", "category"} else "evidence"}


def part(kind, identifier):
    return {"id": identifier.replace("op:", "intent:"), "text": kind,
            "kind": kind, "subject_ids": ["toy:child"], "operation_ids": [identifier], "status": "planned"}


def test_independent_answer_survives_unknown_requested_part(monkeypatch, prepared):
    missing = {"id": "intent:002", "text": "Unknown bind designation", "kind": "designation",
               "subject_ids": [], "operation_ids": [], "status": "unsupported", "reason": "unknown_source_entity"}
    result = execute(monkeypatch, prepared, [operation("designation", "op:001")],
                     [part("designation", "op:001"), missing], status="insufficient_evidence")
    assert "Pulsed fold" in result["answer"] and "ZZP" in result["answer"]
    assert "Unknown bind" in result["answer"] and "Unsupported requested part" in result["answer"]
    assert result["answer_outcome"] == "insufficient_evidence" and result["partial_completion"]
    coverage = result["coverage"]
    assert coverage["requested_count"] == 2 and coverage["answered_count"] == 1
    assert not coverage["all_parts_answered"] and coverage["every_part_accounted_for"]
    answered = coverage["parts"][0]
    assert answered["evidence_ids"] and answered["accepted_assertion_ids"]


def test_each_intent_retains_its_layer_and_evidence(monkeypatch, prepared):
    kinds = ["designation", "category", "parents"]
    operations = [operation(kind, "op:" + str(index)) for index, kind in enumerate(kinds)]
    parts = [part(item["kind"], item["operation_id"]) for item in operations]
    result = execute(monkeypatch, prepared, operations, parts)
    assert result["answer_outcome"] == "graph_answer"
    assert result["coverage"]["all_parts_answered"]
    assert [item["query_layer"] for item in result["operations"]] == ["knowledge", "knowledge", "evidence"]
    assert all(item["evidence_ids"] for item in result["coverage"]["parts"])
    assert "Ribbon fold" in result["answer"] and "candidate" in result["answer"].lower()
    assert all(assertion["status"] == "ACCEPTED" for item in result["operations"][:2]
               for assertion in item["knowledge_support"]["assertions"])
    forced = execute(monkeypatch, prepared, operations, parts, query_layer="knowledge")
    assert forced["answer_outcome"] == "insufficient_evidence"
    assert forced["coverage"]["parts"][2]["status"] == "unsupported"
    assert forced["operations"][2]["accepted_assertion_ids"] == []


def test_ambiguity_is_explicit_without_suppressing_independent_operation(monkeypatch, prepared):
    ambiguous = {"id": "intent:002", "text": "fold parent", "kind": "parents",
                 "subject_ids": [], "operation_ids": [], "status": "ambiguous",
                 "reason": "name_is_not_unique", "candidate_ids": ["toy:parent", "toy:child"]}
    result = execute(monkeypatch, prepared, [operation("designation", "op:001")],
                     [part("designation", "op:001"), ambiguous], status="clarification_required")
    assert result["answer_outcome"] == "clarification_required"
    assert "ZZP" in result["answer"] and "Source-visible candidates" in result["answer"]
    assert "Ribbon fold" in result["answer"] and "Pulsed fold" in result["answer"]
    assert [item["status"] for item in result["coverage"]["parts"]] == ["answered", "ambiguous"]
    assert result["coverage"]["parts"][1]["evidence_ids"]
    assert {"toy:parent", "toy:child"} <= set(result["trace"]["visited_node_ids"])
    assert any(item["predicate"] == "clarification_candidate_label" for item in result["claims"])


def test_missing_operation_cannot_be_reported_complete(monkeypatch, prepared):
    requested = part("designation", "op:absent")
    result = execute(monkeypatch, prepared, [], [requested])
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["coverage"]["parts"][0]["status"] == "unsupported"
    assert "requested_operation_not_completed" in result["answer"]
    assert not result["coverage"]["all_parts_answered"]


def test_child_followup_does_not_consume_an_independent_list(monkeypatch, prepared):
    first = dict(operation("direct_children", "op:list-a"), subject_ids=["toy:parent"])
    independent = dict(operation("direct_children", "op:list-b"), subject_ids=["toy:family"])
    followup = dict(operation("category", "op:category-a"), subject_ids=["toy:parent"],
                    use_returned_children=True, after_operations=["direct_children"],
                    after_operation_ids=["op:list-a"])
    operations = [first, followup, independent]
    result = execute(monkeypatch, prepared, operations,
                     [part(item["kind"], item["operation_id"]) for item in operations])
    category = next(item for item in result["operations"] if item["kind"] == "category")
    assert {row["id"] for row in category["rows"]} == {"toy:child"}
    assert category["selector_subject_ids"] == ["toy:parent"]
    assert result["coverage"]["all_parts_answered"]


def test_source_box_partition_is_complete_ordered_qualified_and_evidence_only(monkeypatch, prepared):
    partition = dict(operation("row_partition", "op:partition"), subject_ids=["toy:family"])
    request = dict(part("row_partition", "op:partition"), subject_ids=["toy:family"])
    result = execute(monkeypatch, prepared, [partition], [request])
    actual = result["operations"][0]
    assert actual["query_layer"] == "evidence"
    assert actual["groups"][0]["unindented_node_ids"] == ["toy:parent"]
    assert actual["groups"][0]["indented_node_ids"] == ["toy:child"]
    assert [row["id"] for row in actual["rows"]] == ["toy:parent", "toy:child"]
    assert "candidate layout parent: Ribbon fold" in result["answer"]
    assert result["coverage"]["parts"][0]["evidence_ids"]
    assert all(edge["evidence"]["verification"] == "candidate" for edge in actual["trace"]["selected_edges"]
               if edge["type"] == "INDENTED_UNDER")
    forced = execute(monkeypatch, prepared, [partition], [request], query_layer="knowledge")
    assert forced["answer_outcome"] == "insufficient_evidence"
    assert forced["operations"][0]["rows"] == []
    assert forced["operations"][0]["accepted_assertion_ids"] == []


def test_child_designation_coverage_tracks_rows_and_rejects_parent_or_empty_output(monkeypatch, prepared):
    producer = dict(operation("direct_children", "op:children"), subject_ids=["toy:parent"])
    request = dict(part("designation", "op:children"), subject_scope="returned_children",
                   subject_ids=[], selector_subject_ids=["toy:parent"])
    result = execute(monkeypatch, prepared, [producer], [request])
    coverage = result["coverage"]["parts"][0]
    assert coverage["subject_ids"] == coverage["target_node_ids"] == ["toy:child"]
    assert coverage["selector_subject_ids"] == ["toy:parent"]
    assert coverage["status"] == "answered" and "ZZP" in result["answer"]
    mixed = dict(producer, subject_ids=["toy:parent", "toy:family"])
    mixed_result = execute(monkeypatch, prepared, [mixed], [request])
    assert mixed_result["coverage"]["parts"][0]["target_node_ids"] == ["toy:child"]
    category_request = dict(request, kind="category")
    category_result = execute(monkeypatch, prepared, [producer], [category_request])
    assert category_result["coverage"]["parts"][0]["status"] == "unsupported"
    wrong = dict(operation("designation", "op:children"), subject_ids=["toy:parent"])
    wrong_result = execute(monkeypatch, prepared, [wrong], [request])
    assert not wrong_result["coverage"]["all_parts_answered"]
    assert wrong_result["coverage"]["parts"][0]["reason"] == "requested_child_scope_not_executed"
    empty = dict(producer, subject_ids=["toy:child"])
    empty_request = dict(request, selector_subject_ids=["toy:child"])
    empty_result = execute(monkeypatch, prepared, [empty], [empty_request])
    assert not empty_result["coverage"]["all_parts_answered"]
    assert empty_result["coverage"]["parts"][0]["target_node_ids"] == []


def test_process_parent_absence_is_complete_chart_scoped_with_positive_box(prepared):
    from src.evidence_a1_graph_qa import _GraphView, _operation
    graph, _ = prepared
    requested = {"kind": "parents", "subject_ids": ["toy:parent"]}
    full = _operation(_GraphView(graph), requested, complete_chart=True)
    assert full["parent_groups"] == [{"subject_id": "toy:parent", "parent_ids": ["toy:family"]}]
    assert full["process_parent_details"] == [{"subject_id": "toy:parent", "process_parent_ids": [],
                                                "process_parent_status": "none_shown_in_complete_chart"}]
    assert "No directly indented process parent is shown" in full["answer"]
    assert "ALPHA (AF)" in full["answer"] and "universal semantic negative" in full["answer"]
    partial = _operation(_GraphView(graph), requested, complete_chart=False)
    assert partial["answer_outcome"] == "insufficient_evidence"
    assert "complete_chart_required_for_process_parent_absence" in partial["trace"]["diagnostics"]


def test_truthful_source_limit_is_distinct_from_unknown_planning_part(monkeypatch, prepared):
    limit = operation("operating_information", "op:limit")
    request = part("operating_information", "op:limit")
    result = execute(monkeypatch, prepared, [limit], [request])
    coverage = result["coverage"]["parts"][0]
    assert coverage["status"] == "unsupported" and coverage["resolution_kind"] == "source_or_admission_limit"
    assert coverage["limitation_explained"] and not result["coverage"]["all_parts_answered"]


@pytest.mark.parametrize("kind", ["direct_children", "descendants", "row_partition"])
def test_forced_knowledge_child_codes_keep_metadata_and_abstain(monkeypatch, prepared, kind):
    producer = dict(operation(kind, "op:children"), subject_ids=["toy:family"],
                    selector_subject_ids=["toy:family"], dependency_operation_ids=["op:upstream"])
    request = dict(part("designation", "op:children"), subject_scope="returned_children",
                   subject_ids=[], selector_subject_ids=["toy:family"])
    result = execute(monkeypatch, prepared, [producer], [request], query_layer="knowledge")
    actual = result["operations"][0]
    assert actual["selector_subject_ids"] == ["toy:family"]
    assert actual["subject_scope"] == "selectors"
    assert actual["dependency_operation_ids"] == ["op:upstream"]
    assert actual["answer_outcome"] == "insufficient_evidence"
    assert actual["rows"] == actual["accepted_assertion_ids"] == []
    assert actual["knowledge_support"]["assertions"] == []
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["coverage"]["parts"][0]["target_node_ids"] == []
    assert not result["coverage"]["all_parts_answered"]
