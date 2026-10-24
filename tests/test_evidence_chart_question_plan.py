"""Focused question-action checks over original synthetic chart data only."""
from copy import deepcopy
import json

from jsonschema import Draft202012Validator
import pytest

from test_evidence_a1_graph_qa import toy_graph, no_network
from test_evidence_a2_core import bind, nested
from src.evidence_a1_graph_qa import execute_graph_plan
from src.evidence_chart_contract import QUESTION_INTERFACE, COVERAGE
from src.evidence_chart_question_plan import build_prompt, output_schema, compile_plan


@pytest.fixture
def source(toy_graph):
    return bind(nested(toy_graph))


def action(identifier="lookup", kind="lookup_term", **changes):
    record = {"id": identifier, "kind": kind, "query_layer": "evidence",
        "subjects": ["n4"], "targets": [], "subjects_from": [], "targets_from": [],
        "fields": ["name", "acronym"], "mode": "", "information_fields": [], "scope": "selected"}
    record.update(changes)
    return record


def envelope(query, actions):
    return {"schema_version": QUESTION_INTERFACE["schema_version"], "source_element": "Figure A2",
        "query": query, "actions": actions, "parts": [{"id": "p1", "quote": query,
            "status": "planned", "action_ids": [item["id"] for item in actions], "reason": ""}]}


def test_full_printed_name_code_and_requested_fields_use_one_identity_anchor(source):
    query = "Give the name, acronym, group and voltage for ZZRP in Figure A2."
    payload = envelope(query, [action(subjects=["Ribbon folding pulsed", "ZZRP"],
        fields=["name", "acronym", "group"], information_fields=["voltage"])])
    original = deepcopy(payload)
    Draft202012Validator.check_schema(output_schema(source))
    Draft202012Validator(output_schema(source)).validate(payload)
    plan = compile_plan(source, query, payload)
    assert plan["status"] == "ready"
    assert [item["kind"] for item in plan["operations"]] == ["designation", "category", "operating_information"]
    assert plan["operations"][0]["subject_ids"] == ["toy:pulsed"]
    result = execute_graph_plan(source, plan, complete_chart=True)
    assert "ZZRP" in result["answer"] and "ALPHA FAMILY" in result["answer"]
    assert "voltage" in result["answer"] and "unavailable" in result["answer"]
    assert plan["external_plan"] == original == payload
    assert plan["coverage_authority"] == COVERAGE and plan["semantic_validation"] is False
    prompt = build_prompt(source, query)
    context = json.loads(prompt.split("\nINPUT=", 1)[1])
    assert context["linked_mentions"][0]["candidates"] == ["n5"]
    assert "edges" not in context and "answers" not in context
    assert "Fields=" + "/".join(QUESTION_INTERFACE["fields"]) in prompt
    assert all(kind + " modes=" in prompt for kind in QUESTION_INTERFACE["kinds"])


def test_planned_rationale_maps_metadata_without_changing_actions_or_legacy_rule(source):
    from src.evidence_chart_llm_plan import compile_plan as compile_legacy
    query = "Identify the selected printed entry."
    payload = envelope(query, [action()])
    payload["parts"][0]["reason"] = "A printed-identity lookup is requested; this is only my rationale."
    original = deepcopy(payload)
    schema = output_schema(source)
    Draft202012Validator(schema).validate(payload)
    description = QUESTION_INTERFACE["part_metadata"]["description"]
    assert schema["properties"]["parts"]["items"]["properties"]["reason"]["description"] == description
    assert description in build_prompt(source, query)
    plan = compile_plan(source, query, payload)
    assert plan["external_plan"] == payload == original
    assert plan["lowered_plan"]["parts"][0]["reason"] == ""
    assert plan["model_part_metadata"] == [{"part_id": "p1", "status": "planned",
        "original_reason": original["parts"][0]["reason"], "internal_reason": "",
        "authority": "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"}]
    result = execute_graph_plan(source, plan, complete_chart=True)
    assert result["answer_outcome"] == "graph_answer" and result["rows"][0]["id"] == "toy:ribbon"
    assert original["parts"][0]["reason"] not in result["answer"]
    # The internal compiler remains strict; only the advertised adapter maps
    # trace metadata. It cannot relax the legacy wire or unknown action refs.
    wire = deepcopy(plan["lowered_plan"])
    wire["parts"][0]["reason"] = original["parts"][0]["reason"]
    with pytest.raises(ValueError, match="PLANNED_PART_INVALID"):
        compile_legacy(source, query, wire)
    invalid = deepcopy(payload)
    invalid["parts"][0]["action_ids"] = []
    with pytest.raises(ValueError, match="PLANNED_PART_INVALID"):
        compile_plan(source, query, invalid)


@pytest.mark.parametrize("reason", [None, [], "x" * 1025])
def test_metadata_mapping_validates_original_reason_before_normalizing(source, reason):
    query = "Identify the selected printed entry."
    payload = envelope(query, [action()])
    payload["parts"][0]["reason"] = reason
    with pytest.raises(ValueError, match="PART_REASON_INVALID"):
        compile_plan(source, query, payload)


def test_unresolved_explanation_is_not_normalized_into_a_planned_answer(source):
    query = "Identify an unresolved entry."
    payload = envelope(query, [])
    payload["parts"][0].update(status="unresolved", reason="Select a printed identity first.")
    plan = compile_plan(source, query, payload)
    assert not plan["operations"]
    assert plan["lowered_plan"]["parts"][0]["reason"] == payload["parts"][0]["reason"]
    payload["parts"][0]["reason"] = ""
    with pytest.raises(ValueError, match="UNRESOLVED_PART_INVALID"):
        compile_plan(source, query, payload)


def test_ambiguous_or_fragment_selector_is_blocked_without_losing_safe_independent_lookup(toy_graph):
    graph = deepcopy(toy_graph)
    graph["nodes"][5]["code"] = "ZZR"
    source = bind(nested(graph))
    query = "Inspect the selected entries."
    payload = envelope(query, [action("uncertain", subjects=["ZZR"]),
        action("fragment", subjects=["Ribbon"]), action("navigation", subjects=["root"]),
        action("safe", subjects=["ZZS"])])
    plan = compile_plan(source, query, payload)
    assert plan["status"] == "partial"
    choices = plan["action_identity_choices"]["uncertain"][0]
    assert choices["status"] == "ambiguous" and set(choices["candidate_ids"]) == {"toy:ribbon", "toy:foil"}
    assert plan["action_identity_choices"]["fragment"][0]["status"] == "unknown"
    assert plan["action_identity_choices"]["navigation"][0]["status"] == "unknown"
    result = execute_graph_plan(source, plan, complete_chart=True)
    valid = [item for item in result["operations"] if item.get("answer_outcome") == "graph_answer"]
    assert len(valid) == 1 and valid[0]["rows"][0]["id"] == "toy:squeeze"


def test_follow_up_is_explicit_prior_lookup_result_not_most_recent_entity(source):
    query = "Identify both selected terms, then give the first term's group."
    payload = envelope(query, [action("first", subjects=["ZZR"]),
        action("second", subjects=["ZZS"]), action("follow", subjects=[], subjects_from=["first"], fields=["group"])])
    plan = compile_plan(source, query, payload)
    follow = next(item for item in plan["operations"] if item["external_operation_id"] == "action3_1")
    assert follow["result_refs"] == {"subject_ids": [{"operation_id": "model:action1_1", "select": "rows"}]}
    result = execute_graph_plan(source, plan, complete_chart=True)
    category = next(item for item in result["operations"] if item["kind"] == "category")
    assert category["rows"][0]["id"] == "toy:ribbon"
    assert "ALPHA FAMILY" in category["answer"] and "BETA FAMILY" not in category["answer"]


@pytest.mark.parametrize("mode,target,layer,ready,kinds", [
    ("membership", "n2", "evidence", True, ["membership"]),
    ("membership", "n4", "evidence", False, ["membership"]),
    ("semantic_subtype", "n4", "evidence", True, ["layout_relation", "epistemic_limits"]),
    ("semantic_subtype", "n4", "knowledge", False, ["unsupported"]),
])
def test_relation_modes_keep_membership_layout_and_knowledge_distinct(source, mode, target, layer, ready, kinds):
    query = "Check the requested relationship in Figure A2."
    payload = envelope(query, [action(kind="check_relationship", subjects=["n5"], targets=[target],
        query_layer=layer, mode=mode, fields=[])])
    plan = compile_plan(source, query, payload)
    assert (plan["status"] == "ready") is ready
    assert [item["kind"] for item in plan["operations"]] == kinds
    assert plan["external_plan"]["actions"][0]["mode"] == mode
    if ready and mode == "semantic_subtype":
        result = execute_graph_plan(source, plan, complete_chart=True)
        assert "candidate" in result["answer"].lower()
        assert "semantic" in result["answer"].lower()
        assert result["semantic_validation"] is False


def test_chart_source_limits_require_explicit_scope_and_no_implicit_empty_identity(source):
    query = "What does the selected whole chart establish?"
    selected = action(kind="check_relationship", subjects=[], mode="source_limits", fields=[])
    blocked = compile_plan(source, query, envelope(query, [selected]))
    assert blocked["action_errors"]["lookup"] == ["CHART_QUESTION_PLAN_SELECTED_SUBJECT_REQUIRED"]
    explicit = deepcopy(selected)
    explicit["scope"] = "chart"
    plan = compile_plan(source, query, envelope(query, [explicit]))
    assert plan["status"] == "ready"
    assert [item["kind"] for item in plan["operations"]] == ["chart_layout", "epistemic_limits"]
    assert plan["operations"][0]["scope"] == "chart"


def test_failed_action_blocks_its_dependents_but_safe_independent_action_runs(source):
    query = "Inspect the selected entries and their references."
    payload = envelope(query, [action("failed", subjects=["unprinted invented term"]),
        action("dependent", subjects=[], subjects_from=["failed"]), action("safe", subjects=["n6"]),
        action("mixed", subjects=["n4"], subjects_from=["safe"])])
    plan = compile_plan(source, query, payload)
    assert set(plan["action_errors"]) == {"failed", "dependent", "mixed"}
    assert "REFERENCE_PRODUCER_INVALID_OR_FAILED" in plan["action_errors"]["dependent"][0]
    assert plan["action_errors"]["mixed"] == ["CHART_QUESTION_PLAN_LITERALS_AND_REFERENCES_MIXED"]
    result = execute_graph_plan(source, plan, complete_chart=True)
    valid = [item for item in result["operations"] if item.get("answer_outcome") == "graph_answer"]
    assert len(valid) == 1 and valid[0]["rows"][0]["id"] == "toy:foil"


@pytest.mark.parametrize("mode,selection", [("parents", "parents"), ("physical_neighbors", "groups"),
                                           ("direct", "groups"), ("descendants", "groups")])
def test_list_follow_up_selects_actual_producer_results(source, mode, selection):
    query = "List the selected entries and identify those returned entries."
    first = action("list", "list_members", subjects=["n4"] if mode == "parents" else ["n8"], mode=mode, fields=[])
    second = action("lookup", subjects=[], subjects_from=["list"])
    plan = compile_plan(source, query, envelope(query, [first, second]))
    assert plan["status"] == "ready"
    assert plan["operations"][1]["result_refs"]["subject_ids"][0]["select"] == selection
    if mode in {"parents", "physical_neighbors"}:
        # The label-only list needs an explicit code projection on its results.
        first["fields"] = ["acronym"]
        projection = compile_plan(source, query, envelope(query, [first]))
        assert [item["kind"] for item in projection["operations"]] == [
            "parents" if mode == "parents" else "physical_neighbors", "designation"]
        assert projection["operations"][1]["result_refs"]["subject_ids"][0]["select"] == selection


def test_targetless_membership_lowers_to_category_and_selection_is_categories(source):
    query = "What category contains ZZRP in Figure A2?"
    act = action("category_lookup", kind="check_relationship", mode="membership",
                 subjects=["ZZRP"], targets=[], fields=["name", "acronym", "group"])
    plan = compile_plan(source, query, envelope(query, [act]))
    assert plan["status"] == "ready"
    assert [item["kind"] for item in plan["operations"]] == ["category", "designation"]
    result = execute_graph_plan(source, plan, complete_chart=True)
    assert "ALPHA FAMILY" in result["answer"]
    assert "ZZRP" in result["answer"]


def test_auxiliary_information_fields_do_not_block_valid_path(source):
    query = "Trace the path from ZZRP to the root."
    act = action("path_lookup", kind="explain_path", mode="from_to",
                 subjects=["ZZRP"], targets=["n1"],
                 information_fields=["kind of visible connection at each step"])
    plan = compile_plan(source, query, envelope(query, [act]))
    assert plan["status"] == "ready"
    assert [item["kind"] for item in plan["operations"]] == ["paths", "designation"]
    result = execute_graph_plan(source, plan, complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"


def test_chart_scope_with_figure_element_name_lowers_to_chart_layout_and_epistemic_limits(source):
    query = "What does Figure A2 establish regarding indentation and arrows?"
    act = action("chart_limits", kind="check_relationship", mode="source_limits",
                 subjects=["Figure A2"], targets=[], fields=["evidence", "source_limits"], scope="chart")
    plan = compile_plan(source, query, envelope(query, [act]))
    assert plan["status"] == "ready"
    assert [item["kind"] for item in plan["operations"]] == ["chart_layout", "epistemic_limits"]
    result = execute_graph_plan(source, plan, complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert "candidate" in result["answer"].lower()

