"""Small synthetic contract checks. No model, provider, owner questions or gold."""
from copy import deepcopy
import json

from jsonschema import Draft202012Validator
import pytest

from test_evidence_a1_graph_qa import toy_graph, no_network
from test_evidence_a2_core import bind, nested
from src.evidence_chart_llm_plan import (
    SCHEMA_VERSION, COVERAGE, OPERATION_PROFILES, OPERATION_KEYS, PART_KEYS,
    INSTRUCTION_VERSION, build_prompt, output_schema, compile_plan,
)


@pytest.fixture
def source(toy_graph):
    return bind(nested(toy_graph))


def operation(kind="designation", identifier="o1", subjects=None, targets=None, **changes):
    value = {"id": identifier, "kind": kind, "query_layer": "evidence",
        "subject_ids": ["n4"] if subjects is None else subjects, "target_ids": targets or [],
        "result_refs": {"subjects": [], "targets": []}, "fields": [],
        "requested_fields": [], "requested_aspects": []}
    value.update(changes)
    return value


def envelope(query, operations, parts=None):
    return {"schema_version": SCHEMA_VERSION, "source_element": "Figure A2", "query": query,
        "parts": parts or [{"id": "p1", "quote": query, "status": "planned",
                           "operation_ids": [item["id"] for item in operations], "reason": ""}],
        "operations": operations}


@pytest.mark.parametrize("kind", OPERATION_PROFILES)
def test_each_profile_has_agreeing_schema_and_compiler(source, kind):
    op = operation(kind)
    if kind in {"direct_children", "descendants", "row_partition"}:
        op["subject_ids"] = ["n2"]
    elif kind == "physical_neighbors":
        op["subject_ids"] = ["n8"]
    elif kind == "paths":
        op.update(subject_ids=["n1"], target_ids=["n4"])
    elif kind == "membership":
        op["target_ids"] = ["n2"]
    elif kind == "layout_relation":
        op.update(subject_ids=["n5"], target_ids=["n4"])
    elif kind == "comparison":
        op.update(subject_ids=["n4", "n6"], fields=["designation", "category"])
    elif kind == "chart_layout":
        op["subject_ids"] = []
    query = "Inspect the selected source graph."
    payload = envelope(query, [op])
    schema = output_schema(source)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    plan = compile_plan(source, query, payload)
    assert plan["status"] == "ready"
    assert plan["coverage_authority"] == COVERAGE
    assert plan["semantic_validation"] is False
    assert all(operation["request_ids"] == ["p1"] for operation in plan["operations"])
    assert plan["requested_parts"][0]["span"] == [0, len(query)]


def test_result_references_compile_to_current_roles_without_executing(source):
    query = "List the neighbors and show paths from the root to those groups."
    first = operation("physical_neighbors", "neighbors", ["n8"])
    second = operation("paths", "paths", ["n1"],
        result_refs={"subjects": [], "targets": [{"operation_id": "neighbors", "select": "groups"}]})
    payload = envelope(query, [first, second])
    Draft202012Validator(output_schema(source)).validate(payload)
    result = compile_plan(source, query, payload)
    path = result["operations"][1]
    assert path["start_ids"] == ["toy:root"]
    assert path["result_refs"] == {"end_ids": [{"operation_id": "model:neighbors", "select": "groups"}]}
    assert path["result_constraints"]["start_ids"]["maximum"] == 1
    assert path["result_constraints"]["end_ids"]["kinds"] == ["root", "category", "process"]
    assert result["requested_parts"][0]["subject_scope"] == "operation_results"


def test_comparison_ids_cannot_collide_and_dynamic_minimum_is_retained(source):
    query = "Compare the listed entries and identify the other entry."
    first = operation("descendants", "listing", ["n2"])
    comparison = operation("comparison", "c", [],
        result_refs={"subjects": [{"operation_id": "listing", "select": "rows"}], "targets": []},
        fields=["designation"])
    last = operation("designation", "c_designation", ["n4"])
    result = compile_plan(source, query, envelope(query, [first, comparison, last]))
    ids = [item["operation_id"] for item in result["operations"]]
    assert len(ids) == len(set(ids))
    assert "model:c:designation" in ids and "model:c_designation" in ids
    assert result["operations"][1]["result_constraints"]["subject_ids"]["minimum"] == 2


@pytest.mark.parametrize("change,match", [
    (lambda op: op.update(subject_ids=["invented"]), "UNKNOWN_SOURCE_ID"),
    (lambda op: op.update(answer="unsupported extra field"), "OPERATION_KEYS_INVALID"),
    (lambda op: op.update(target_ids=["n2"]), "UNUSED_ROLE_NOT_EMPTY"),
    (lambda op: op.update(result_refs={"subjects": [{"operation_id": "later", "select": "rows"}], "targets": []}), "RESULT_REF_NOT_PRIOR"),
    (lambda op: op.update(query_layer="auto"), "LAYER_INVALID"),
])
def test_invalid_operations_are_explicit_nonexecuting_records(source, change, match):
    op = operation()
    change(op)
    query = "Inspect an entry."
    result = compile_plan(source, query, envelope(query, [op]))
    assert result["status"] == "invalid"
    assert any(match in code for code in result["operations"][0]["compilation_errors"])


def test_incompatible_result_selection_and_unresolved_parts_remain_explicit(source):
    query = "Inspect entry and report what is unsupported."
    first = operation("physical_neighbors", "first", ["n8"])
    second = operation("category", "second", [],
        result_refs={"subjects": [{"operation_id": "first", "select": "parents"}], "targets": []})
    compiled = compile_plan(source, query, envelope(query, [first, second]))
    assert compiled["status"] == "partial"
    assert "CHART_LLM_PLAN_RESULT_SELECTION_KIND_INVALID" in compiled["operations"][1]["compilation_errors"]
    payload = envelope(query, [operation()], [
        {"id": "p1", "quote": query, "status": "planned", "operation_ids": ["o1"], "reason": ""},
        {"id": "p2", "quote": "what is unsupported", "status": "unresolved", "operation_ids": [],
         "reason": "No admitted operation establishes this request."}])
    result = compile_plan(source, query, payload)
    assert result["requested_parts"][1]["status"] == "unsupported"
    assert result["unresolved_selectors"] == ["what is unsupported"]


@pytest.mark.parametrize("query", [
    "Inspect Figure A3.", "Inspect Figure A1.", "Inspect Figure A2 and A3.",
    "Inspect page 77.", "Inspect PDF page 90.", "Inspect PDF INDEX 89.",
])
def test_foreign_figure_or_page_is_rejected_even_with_matching_payload_source(source, query):
    with pytest.raises(ValueError, match="SOURCE_SCOPE_MISMATCH"):
        compile_plan(source, query, envelope(query, [operation()]))


def test_pdf_page_basis_is_exact_but_clause_labels_are_not_a_partition_gate(source):
    query = "Inspect Figure A2 on PDF INDEX 88 and PDF page 89."
    assert compile_plan(source, query, envelope(query, [operation()]))["status"] == "ready"
    query = "entry and entry"
    payload = envelope(query, [operation()])
    payload["parts"][0]["quote"] = "entry"
    compiled = compile_plan(source, query, payload)
    assert compiled["status"] == "ready"
    assert compiled["requested_parts"][0]["span"] is None
    assert compiled["semantic_validation"] is False
    payload["parts"][0]["quote"] = query
    payload["parts"][0]["start"] = 0
    with pytest.raises(ValueError, match="PART_KEYS_INVALID"):
        compile_plan(source, query, payload)


def test_information_fields_are_question_requests_not_invented_facts(source):
    query = "Does the chart provide current and shielding gas?"
    op = operation("operating_information", requested_fields=["current", "shielding gas"])
    result = compile_plan(source, query, envelope(query, [op]))
    assert result["operations"][0]["requested_fields"] == ["current", "shielding gas"]
    op["requested_fields"] = ["invented source value"]
    compiled = compile_plan(source, query, envelope(query, [op]))
    assert compiled["operations"][0]["compilation_errors"] == ["CHART_LLM_PLAN_INFORMATION_FIELD_NOT_IN_QUERY"]


def test_prompt_contains_only_identity_catalog_not_relationships_or_prior_answers(source):
    prompt = build_prompt(source, "Inspect Figure A2.")
    body = json.loads(prompt.split("\nINPUT=", 1)[1])
    assert body["catalog_columns"] == ["id", "kind", "printed_label", "printed_code", "verified_aliases"]
    assert all(row[0].startswith("n") and len(row) == 5 for row in body["catalog"])
    assert "edges" not in body and "answers" not in body and "gold" not in body


def test_flat_grammar_encoding_keeps_every_shared_required_key(source):
    schema = output_schema(source)
    encoded = json.dumps(schema)
    assert not any('"' + key + '"' in encoded for key in ("oneOf", "anyOf", "allOf", "$ref", "$defs"))
    for branch, keys in (("operations", OPERATION_KEYS), ("parts", PART_KEYS)):
        record = schema["properties"][branch]["items"]
        assert record["type"] == "object" and record["additionalProperties"] is False
        assert set(record["required"]) == set(record["properties"]) == set(keys)
    query = "Inspect the selected source graph."
    incomplete = envelope(query, [{"kind": "designation", "query_layer": "evidence", "requested_fields": []}],
        [{"reason": "", "status": "planned"}])
    assert list(Draft202012Validator(schema).iter_errors(incomplete))
    # Flat structure is deliberately a superset. The unchanged compiler keeps
    # per-kind safety, not a silent repair of a model's incompatible fields.
    unused_target = envelope(query, [operation(targets=["n2"])])
    Draft202012Validator(schema).validate(unused_target)
    compiled = compile_plan(source, query, unused_target)
    assert compiled["operations"][0]["compilation_errors"] == ["CHART_LLM_PLAN_UNUSED_ROLE_NOT_EMPTY"]


@pytest.mark.parametrize("field,value,guard", [
    ("fields", ["designation"], "FIELDS_INVALID"),
    ("requested_fields", ["printed code"], "UNUSED_INFORMATION_FIELDS"),
    ("requested_aspects", ["visible evidence"], "UNUSED_INFORMATION_FIELDS"),
])
def test_information_rules_are_explicit_without_weakening_typed_guards(source, field, value, guard):
    query = "Inspect the printed code and visible evidence."
    prompt, schema = build_prompt(source, query), output_schema(source)
    properties = schema["properties"]["operations"]["items"]["properties"]
    assert properties[field]["description"] in prompt
    assert f"Every other operation requires {field}=[]." in prompt
    # Every profile spells out its empty-array rule rather than relying on an
    # implicit interpretation of the field name or a positive example elsewhere.
    for kind, profile in OPERATION_PROFILES.items():
        line = next(line for line in prompt.splitlines() if line.startswith(kind + ":"))
        if not profile[field]:
            assert f"{field}=[]" in line
    payload = envelope(query, [operation(**{field: value})])
    Draft202012Validator(schema).validate(payload)  # flat grammar is a documented superset
    compiled = compile_plan(source, query, payload)
    assert any(guard in code for code in compiled["operations"][0]["compilation_errors"])


@pytest.mark.parametrize("status,reason,operation_ids,guard", [
    ("planned", "This is only a planning rationale.", ["o1"], "PLANNED_PART_INVALID"),
    ("unresolved", "", [], "UNRESOLVED_PART_INVALID"),
])
def test_planned_and_unresolved_part_rules_are_explicit_and_enforced(source, status, reason, operation_ids, guard):
    query = "Inspect the selected entry."
    prompt, schema = build_prompt(source, query), output_schema(source)
    properties = schema["properties"]["parts"]["items"]["properties"]
    assert INSTRUCTION_VERSION in prompt and INSTRUCTION_VERSION in schema["description"]
    assert properties["reason"]["description"] in prompt
    assert properties["operation_ids"]["description"] in prompt
    assert 'Planned parts require reason="" exactly' in prompt
    payload = envelope(query, [operation()], [{"id": "p1", "quote": query,
        "status": status, "operation_ids": operation_ids, "reason": reason}])
    with pytest.raises(ValueError, match=guard):
        compile_plan(source, query, payload)


def test_clause_coverage_stays_unverified_without_a_character_partition(source):
    query = "In Figure A2, inspect Ribbon folding and Foil binding."
    parts = [{"id": "p1", "quote": "inspect Ribbon folding", "status": "planned",
              "operation_ids": ["o1"], "reason": ""},
             {"id": "p2", "quote": "Foil binding", "status": "planned",
              "operation_ids": ["o2"], "reason": ""}]
    payload = envelope(query, [operation(), operation(identifier="o2", subjects=["n6"])], parts)
    assert compile_plan(source, query, payload)["status"] == "ready"
    for omitted in ["not", "all", "directly", "voltage", "Mystery"]:
        changed = query.replace("and Foil", "and " + omitted + " Foil")
        payload["query"] = changed
        compiled = compile_plan(source, changed, payload)
        assert compiled["status"] == "ready"
        # Captured operations are executable, not proof the model preserved the
        # omitted negation/quantifier/direction. The full query stays immutable.
        assert compiled["query"] == changed
        assert compiled["coverage_authority"] == COVERAGE
        assert compiled["semantic_validation"] is False
        assert compiled["quote_partition_required"] is False


def test_evidence_operation_is_not_rewritten_to_an_epistemic_limit(source):
    query = "Show evidence for Ribbon folding."
    payload = envelope(query, [operation("evidence", requested_aspects=["evidence"])])
    plan = compile_plan(source, query, payload)
    assert plan["operations"][0]["kind"] == "evidence"
    assert plan["operations"][0]["requested_aspects"] == ["evidence"]
    assert plan["external_plan"] == payload


@pytest.mark.parametrize("query", [
    "What is the acronym for Ribbon?",
    "What are the acronyms for Ribbon and Foil binding?",
])
def test_partial_source_identity_requires_clarification_even_with_another_exact_name(source, query):
    payload = envelope(query, [operation()])
    before = deepcopy(payload)
    plan = compile_plan(source, query, payload)
    assert plan["status"] == "clarification_required"
    assert all("CHART_LLM_PLAN_AMBIGUOUS_SOURCE_IDENTITY" in op["compilation_errors"]
               for op in plan["operations"])
    assert set(plan["requested_parts"][0]["candidate_ids"]) == {"toy:ribbon", "toy:pulsed"}
    assert plan["external_plan"] == payload == before
    assert plan["semantic_validation"] is False


def test_exact_name_and_quoted_lexical_premise_do_not_trigger_partial_name_clarification(source):
    for query in ["What is the acronym for Ribbon folding?",
                  "Does sharing 'Ribbon' make Foil binding a subtype of Ribbon folding?"]:
        payload = envelope(query, [operation("epistemic_limits")])
        assert compile_plan(source, query, payload)["status"] == "ready"


def test_wrong_model_depth_and_literal_followup_are_not_silently_corrected(source):
    query = "List all entries in ALPHA FAMILY and give the category for those entries."
    payload = envelope(query, [operation("direct_children", "list", ["n2"]),
                               operation("category", "follow", ["n4"])])
    plan = compile_plan(source, query, payload)
    assert plan["operations"][0]["kind"] == "direct_children"
    assert plan["operations"][1]["subject_ids"] == ["toy:ribbon"]
    assert "result_refs" not in plan["operations"][1]
    assert plan["external_plan"] == payload


def test_batch_retains_invalid_operation_and_dependencies_without_retyping(source):
    query = "Identify Ribbon folding; inspect its relationship and the returned entries."
    good = operation("designation", "good")
    bad = operation("membership", "bad", ["n5"], ["n4"])
    dependent = operation("designation", "follow", [], result_refs={
        "subjects": [{"operation_id": "bad", "select": "rows"}], "targets": []})
    payload = envelope(query, [good, bad, dependent])
    compiled = compile_plan(source, query, payload)
    assert compiled["status"] == "partial"
    assert "compilation_errors" not in compiled["operations"][0]
    assert compiled["operations"][1]["kind"] == "membership"  # never layout_relation
    assert compiled["operations"][1]["compilation_errors"] == ["CHART_LLM_PLAN_SOURCE_KIND_INVALID"]
    assert compiled["operations"][2]["dependency_operation_ids"] == ["model:bad"]
    assert compiled["requested_parts"][0]["operation_ids"] == ["model:good", "model:bad", "model:follow"]
    assert compiled["external_plan"] == payload


def test_only_equivalent_operations_deduplicate_and_all_parts_keep_their_mapping(source):
    query = "Identify Ribbon folding and report its printed designation; give the category too."
    parts = [{"id": "p1", "quote": "Identify Ribbon folding", "status": "planned",
        "operation_ids": ["first"], "reason": ""},
        {"id": "p2", "quote": "report its printed designation", "status": "planned",
        "operation_ids": ["same", "category"], "reason": ""}]
    compiled = compile_plan(source, query, envelope(query, [operation(identifier="first"),
        operation(identifier="same"), operation("category", "category")], parts))
    assert len(compiled["operations"]) == 2
    assert compiled["operation_aliases"]["same"] == ["model:first"]
    assert compiled["operations"][0]["request_ids"] == ["p1", "p2"]
    assert compiled["requested_parts"][1]["operation_ids"] == ["model:first", "model:category"]


def test_unresolved_source_name_gets_dictionary_candidates_and_explicit_chart_scope(source):
    query = "What is the acronym for Ribbon?"
    payload = envelope(query, [], [{"id": "p1", "quote": query, "status": "unresolved",
        "operation_ids": [], "reason": "The model cannot select one name."}])
    compiled = compile_plan(source, query, payload)
    assert compiled["status"] == "clarification_required"
    assert set(compiled["requested_parts"][0]["candidate_ids"]) == {"toy:ribbon", "toy:pulsed"}
    payload["parts"][0].update(id="request_identity", quote="the requested identity")
    compiled = compile_plan(source, query, payload)
    assert [part["id"] for part in compiled["requested_parts"]] == ["request_identity", "compiler:request_identity"]
    query = "Show the selected chart's whole layout."
    compiled = compile_plan(source, query, envelope(query, [operation("chart_layout", subjects=[])]))
    assert compiled["operations"][0]["scope"] == "chart"
    query = "Show source evidence."
    compiled = compile_plan(source, query, envelope(query, [operation("evidence", subjects=[])]))
    assert compiled["operations"][0]["scope"] == "source"


@pytest.mark.parametrize("invalid_kind", [[], {}])
def test_invalid_producer_kind_cannot_crash_an_independent_batch(source, invalid_kind):
    query = "Identify the entry, inspect an unsupported relation, and identify its results."
    payload = envelope(query, [operation(identifier="safe"),
        operation(invalid_kind, "bad"), operation(identifier="dependent", subjects=[],
            result_refs={"subjects": [{"operation_id": "bad", "select": "rows"}], "targets": []})])
    compiled = compile_plan(source, query, payload)
    assert compiled["status"] == "partial"
    assert "compilation_errors" not in compiled["operations"][0]
    assert compiled["operations"][1]["compilation_errors"] == ["CHART_LLM_PLAN_UNKNOWN_OPERATION"]
    assert compiled["operations"][2]["compilation_errors"] == ["CHART_LLM_PLAN_RESULT_DEPENDENCY_INVALID"]


def relationship_path_payload(query, *, reverse=False, layer="evidence"):
    start, end = (["n7"], ["n4"]) if reverse else (["n4"], ["n7"])
    return envelope(query, [operation("designation", "left", ["n4"], query_layer=layer),
        operation("designation", "right", ["n7"], query_layer=layer),
        operation("paths", "path", start, end, query_layer=layer)])


def test_existing_relation_intent_supplements_wrong_path_without_rewriting_model(source):
    query = "Is Ribbon folding a subtype of Squeeze joining in Figure A2?"
    payload = relationship_path_payload(query)
    original = deepcopy(payload)
    compiled = compile_plan(source, query, payload)
    assert [item["kind"] for item in compiled["operations"]] == ["designation", "designation", "paths", "layout_relation"]
    supplement = compiled["operations"][-1]
    assert supplement["left_ids"] == ["toy:ribbon"] and supplement["right_ids"] == ["toy:squeeze"]
    assert supplement["query_layer"] == "evidence"
    assert supplement["selection_origin"] == "existing_deterministic_intent_supplement"
    assert supplement["request_ids"] == ["p1"]
    assert compiled["requested_parts"][0]["operation_ids"] == ["model:left", "model:right", "model:path", supplement["operation_id"]]
    trace = compiled["deterministic_supplements"][0]
    assert trace["model_selected_supplement"] is False
    assert trace["original_model_operations_retained"] is True
    assert trace["source_path_operation_id"] == "model:path"
    assert compiled["operation_aliases"]["path"] == ["model:path"]
    assert compiled["external_plan"] == payload == original
    assert compiled["coverage_authority"] == COVERAGE and compiled["semantic_validation"] is False


@pytest.mark.parametrize("query,reverse,layer", [
    ("Show the path from Ribbon folding to Squeeze joining in Figure A2.", False, "evidence"),
    ("Is Ribbon folding a subtype of Squeeze joining in Figure A2?", True, "evidence"),
    ("Is Ribbon folding a subtype of Squeeze joining in Figure A2?", False, "knowledge"),
    ("In accepted knowledge, is Ribbon folding a subtype of Squeeze joining in Figure A2?", False, "evidence"),
])
def test_relation_supplement_abstains_for_path_direction_mismatch_or_knowledge(source, query, reverse, layer):
    payload = relationship_path_payload(query, reverse=reverse, layer=layer)
    compiled = compile_plan(source, query, payload)
    assert [item["kind"] for item in compiled["operations"]] == ["designation", "designation", "paths"]
    assert "deterministic_supplements" not in compiled
    assert compiled["external_plan"] == payload


def test_relation_supplement_does_not_guess_ambiguity_or_rewrite_membership(source):
    query = "What is the acronym for Ribbon?"
    payload = relationship_path_payload(query)
    compiled = compile_plan(source, query, payload)
    assert compiled["status"] == "clarification_required"
    assert "deterministic_supplements" not in compiled
    query = "Is Ribbon folding a subtype of Squeeze joining in Figure A2?"
    payload = envelope(query, [operation("membership", "wrong", ["n4"], ["n7"])])
    compiled = compile_plan(source, query, payload)
    assert compiled["operations"][0]["kind"] == "membership"
    assert compiled["operations"][0]["compilation_errors"]
    assert "deterministic_supplements" not in compiled


def test_relation_supplement_preserves_compound_parts_and_result_dependencies(source):
    query = "Is Ribbon folding a subtype of Squeeze joining in Figure A2?"
    payload = relationship_path_payload(query)
    payload["parts"] = [{"id": "p1", "quote": "Ribbon folding", "status": "planned",
        "operation_ids": ["left"], "reason": ""}, {"id": "p2", "quote": "Squeeze joining", "status": "planned",
        "operation_ids": ["right", "path"], "reason": ""}]
    compiled = compile_plan(source, query, payload)
    assert "deterministic_supplements" not in compiled
    assert len(compiled["requested_parts"]) == 2
    payload = relationship_path_payload(query)
    payload["operations"][-1]["subject_ids"] = []
    payload["operations"][-1]["result_refs"]["subjects"] = [{"operation_id": "left", "select": "rows"}]
    compiled = compile_plan(source, query, payload)
    assert "deterministic_supplements" not in compiled
    assert compiled["operations"][-1]["dependency_operation_ids"] == ["model:left"]
    assert compiled["operations"][-1]["result_refs"]["start_ids"] == [{"operation_id": "model:left", "select": "rows"}]


def test_relation_supplement_respects_existing_operation_budget(source, monkeypatch):
    import src.evidence_chart_llm_plan as compiler
    query = "Is Ribbon folding a subtype of Squeeze joining in Figure A2?"
    payload = envelope(query, [operation("designation", "literal", ["n4"]),
        operation("paths", "path", ["n4"], ["n7"])])
    monkeypatch.setattr(compiler, "MAX_OPERATIONS", 2)
    compiled = compiler.compile_plan(source, query, payload)
    assert len(compiled["operations"]) == 2
    assert "deterministic_supplements" not in compiled
