"""Focused invented-chart checks for compiled plans and result references."""
from copy import deepcopy

from test_evidence_a1_graph_qa_repair import graph, no_external_calls
from src.evidence_a1_graph_qa import answer_graph, execute_graph_plan


def plan(*operations):
    operations = [dict(operation, operation_id="op:" + str(index))
                  for index, operation in enumerate(operations)]
    return {"query": "An already validated generic request", "status": "ready",
            "operations": operations, "resolved_entities": list(dict.fromkeys(
                identifier for operation in operations for identifier in operation.get("subject_ids", []))),
            "diagnostics": [], "unresolved_selectors": [],
            "requested_parts": [{"id": "request:" + str(index), "text": "Requested graph operation",
                "kind": operation["kind"], "status": "planned", "operation_ids": [operation["operation_id"]],
                "subject_ids": operation.get("subject_ids", []), "subject_scope": "operation_results"}
                for index, operation in enumerate(operations)]}


def ref(operation, selection):
    return {"operation_id": "op:" + str(operation), "select": selection}


def test_relation_supplement_distinguishes_ancestry_from_physical_reachability(graph):
    request = plan({"kind": "layout_relation", "subject_ids": ["toy:ribbon", "toy:foil"],
        "left_ids": ["toy:ribbon"], "right_ids": ["toy:foil"], "query_layer": "evidence",
        "selection_origin": "existing_deterministic_intent_supplement"})
    request["coverage_authority"] = "MODEL_PROPOSED_UNVERIFIED"
    result = answer_graph(graph, request["query"], complete_chart=True,
        question_planner=lambda actual_graph, query, **kwargs: deepcopy(request))
    assert "ancestor/parent chains, not all physical reachability" in result["answer"]
    assert "reviewed semantic subtype is not established" in result["answer"]


def test_injected_planner_executes_once_without_changing_graph(graph):
    original = deepcopy(graph)
    calls = []
    def planner(actual_graph, query, *, concept_bindings=None):
        calls.append((query, concept_bindings))
        result = plan({"kind": "designation", "subject_ids": ["toy:ribbon"]})
        result["query"] = query
        return result
    result = answer_graph(graph, "An opaque request", question_planner=planner)
    assert len(calls) == 1
    assert result["answer_outcome"] == "graph_answer"
    assert result["rows"][0]["id"] == "toy:ribbon"
    assert graph == original


def test_category_reference_supplies_actual_path_endpoint(graph):
    result = execute_graph_plan(graph, plan(
        {"kind": "category", "subject_ids": ["toy:deep"]},
        {"kind": "paths", "subject_ids": ["toy:root"], "start_ids": ["toy:root"], "end_ids": [],
         "requested_direction": "from_to", "result_refs": {"end_ids": [ref(0, "categories")]}}),
        complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    operation = result["operations"][1]
    assert operation["paths"][0]["node_ids"] == ["toy:root", "toy:alpha"]
    assert operation["resolved_result_refs"][0]["node_ids"] == ["toy:alpha"]


def test_parent_and_group_references_use_returned_records_in_order(graph):
    parents = execute_graph_plan(graph, plan(
        {"kind": "parents", "subject_ids": ["toy:deep"]},
        {"kind": "designation", "subject_ids": [], "result_refs": {"subject_ids": [ref(0, "parents")]}}),
        complete_chart=True)
    assert [row["id"] for row in parents["operations"][1]["rows"]] == ["toy:pulsed"]
    groups = execute_graph_plan(graph, plan(
        {"kind": "direct_children", "subject_ids": ["toy:root"]},
        {"kind": "designation", "subject_ids": [], "result_refs": {"subject_ids": [ref(0, "groups")]}}),
        complete_chart=True)
    assert [row["id"] for row in groups["operations"][1]["rows"]] == ["toy:alpha", "toy:beta"]
    assert groups["coverage"]["parts"][1]["target_node_ids"] == ["toy:alpha", "toy:beta"]


def test_empty_result_dependency_fails_without_falling_back_to_literal_subject(graph):
    result = execute_graph_plan(graph, plan(
        {"kind": "direct_children", "subject_ids": ["toy:foil"]},
        {"kind": "designation", "subject_ids": ["toy:ribbon"],
         "result_refs": {"subject_ids": [ref(0, "rows")]}}), complete_chart=True)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["operations"][1]["rows"] == []
    assert "result_reference_empty" in result["operations"][1]["trace"]["diagnostics"]
    assert not result["coverage"]["all_parts_answered"]


def test_requested_operating_fields_and_authority_limits_remain_qualified(graph):
    result = execute_graph_plan(graph, plan(
        {"kind": "operating_information", "subject_ids": ["toy:ribbon"], "requested_fields": ["voltage"]},
        {"kind": "epistemic_limits", "subject_ids": ["toy:ribbon"], "requested_aspects": ["normative authority"]}))
    assert "voltage" in result["operations"][0]["missing_information"]["requested_fields"]
    assert "unavailable" in result["operations"][0]["answer"].lower()
    assert "normative authority" in result["operations"][1]["answer"]
    assert "does not establish reviewed semantic is_a" in result["operations"][1]["answer"].lower()
    assert "Requested scope: normative authority." in result["operations"][1]["answer"]


def test_reference_cardinality_and_record_kinds_are_enforced(graph):
    result = execute_graph_plan(graph, plan(
        {"kind": "direct_children", "subject_ids": ["toy:root"]},
        {"kind": "category", "subject_ids": [], "result_refs": {"subject_ids": [ref(0, "groups")]},
         "result_constraints": {"subject_ids": {"minimum": 1, "maximum": 1, "kinds": ["process"]}}}),
        complete_chart=True)
    assert result["operations"][1]["rows"] == []
    assert "result_reference_cardinality_invalid:subject_ids" in result["operations"][1]["trace"]["diagnostics"]
    assert "result_reference_kind_invalid:subject_ids" in result["operations"][1]["trace"]["diagnostics"]


def test_canonical_wrapper_plans_each_input_once_and_reuses_compiled_plan(graph, tmp_path, monkeypatch):
    import src.evidence_a1_graph_qa as engine
    from test_evidence_a1_graph_qa_repair import test_synthetic_wrapper_preserves_source_identity_image_and_graph_across_operations
    original = engine.run_graph_qa
    calls, recorded = [], []
    def planner(actual_graph, query, *, concept_bindings=None):
        calls.append(query)
        return engine.plan_graph_query(actual_graph, query, concept_bindings=concept_bindings)
    planner.record_result = recorded.append
    monkeypatch.setattr(engine, "run_graph_qa", lambda *args, **kwargs: original(
        *args, question_planner=planner, **kwargs))
    test_synthetic_wrapper_preserves_source_identity_image_and_graph_across_operations(graph, tmp_path, monkeypatch)
    assert len(calls) == 4
    assert len(set(calls)) == 4
    assert len(recorded) == 4
    assert all(answer["planning_model_invocation_count"] == 0 for answer in recorded)
    def model_stub(actual_graph, query, *, concept_bindings=None):
        compiled = engine.plan_graph_query(actual_graph, query, concept_bindings=concept_bindings)
        compiled["model_planning"] = {"model": "toy-local-planner", "provider": "toy-local",
                                      "model_invocation_count": 1}
        return compiled
    model_stub.metadata = {"model": "toy-local-planner", "provider": "toy-local"}
    result = original(tmp_path, {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1",
        "questions": [{"id": "metadata-only", "query": "What does ZZR stand for?"}]}, question_planner=model_stub)
    for value in (result, result["answers"][0]):
        assert value["evaluation_kind"] == "LLM_planned_deterministic_retrieval"
        assert value["model"] == value["planning_model"] == "toy-local-planner"
        assert value["provider"] == value["planning_provider"] == "toy-local"
        assert value["model_invocation_count"] == value["planning_model_invocation_count"] == 1
        assert value["generation_model"] == "NONE" and value["generation_model_invocation_count"] == 0
