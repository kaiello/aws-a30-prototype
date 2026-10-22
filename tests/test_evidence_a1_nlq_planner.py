"""Focused language contract checks use invented source vocabulary, no QA gold."""
from copy import deepcopy

from test_evidence_a1_graph_qa_repair import graph, no_external_calls
from src.evidence_a1_lexicon import source_dictionary
from src.evidence_a1_planner import plan_graph_query, resolve_mentions


def test_source_dictionary_includes_literal_root_and_rejects_unverified_aliases(graph):
    changed = deepcopy(graph)
    process = next(node for node in changed["nodes"] if node["id"] == "toy:ribbon")
    process["printed_aliases"] = [{"text": "Magic synonym", "verification": "candidate", "basis": "printed_alias"}]
    inventory = source_dictionary(changed)
    assert any(item["node_id"] == "toy:root" and item["text"] == "Toy joining chart" for item in inventory)
    assert not any(item["text"] == "Magic synonym" for item in inventory)
    linked = resolve_mentions(changed, "Toy joining chart: zzrp and Ribbon fold")
    assert [item["candidate_ids"] for item in linked] == [["toy:root"], ["toy:pulsed"], ["toy:ribbon"]]


def test_meaning_and_box_requests_compose_without_global_subject_loss(graph):
    plan = plan_graph_query(graph, "Give ZZR its printed meaning and which box encloses it.")
    assert plan["status"] == "ready"
    assert {item["kind"] for item in plan["operations"]} == {"designation", "category"}
    assert all(item["subject_ids"] == ["toy:ribbon"] for item in plan["operations"])
    assert len(plan["requested_parts"]) == 2 and not plan["unresolved_parts"]
    assert all(item["query_layer"] == "knowledge" for item in plan["operations"])


def test_route_direction_and_independent_followup_have_typed_parts(graph):
    plan = plan_graph_query(graph, "Show the route from Ribbon fold pulsed to ALPHA FAMILY; give Ribbon fold pulsed its acronym.")
    assert plan["status"] == "ready"
    path = next(item for item in plan["operations"] if item["kind"] == "paths")
    assert path["start_ids"] == ["toy:pulsed"] and path["end_ids"] == ["toy:alpha"]
    assert path["query_layer"] == "evidence"
    assert any(item["kind"] == "designation" for item in plan["operations"])
    ambiguous = plan_graph_query(graph, "Compare Ribbon fold and Squeeze join; give its acronym.")
    assert ambiguous["status"] == "clarification_required"
    assert any(item.get("reason") == "singular_reference_has_multiple_antecedents" for item in ambiguous["unresolved_parts"])
    multistart = plan_graph_query(graph, "Show paths from Ribbon fold and Foil bind to ALPHA FAMILY.")
    paths = [item for item in multistart["operations"] if item["kind"] == "paths"]
    assert [item["start_ids"] for item in paths] == [["toy:ribbon"], ["toy:foil"]]
    assert all(item.get("waypoint_ids") == [] for item in paths)


def test_separate_subjects_and_unknown_subquestion_are_not_silently_completed(graph):
    plan = plan_graph_query(graph, "What is the acronym for Ribbon fold? Which box contains Squeeze join? Give its cost.")
    assert plan["status"] != "ready"
    designation = next(item for item in plan["operations"] if item["kind"] == "designation")
    category = next(item for item in plan["operations"] if item["kind"] == "category")
    assert designation["subject_ids"] == ["toy:ribbon"]
    assert category["subject_ids"] == ["toy:squeeze"]
    assert any(item["status"] == "unsupported" and "cost" in item["text"] for item in plan["unresolved_parts"])
    residual = plan_graph_query(graph, "Give ZZR its meaning and cost.")
    assert residual["status"] != "ready"
    assert any("cost" in item["text"] for item in residual["unresolved_parts"])
    unknown = plan_graph_query(graph, "Give ZZR its meaning; give Mystery bind its code.")
    assert not any(item["subject_ids"] for item in unknown["operations"] if "Mystery" in
        next(part["text"] for part in unknown["requested_parts"] if part["id"] in item["request_ids"]))
    assert unknown["unresolved_parts"]
    explanation = plan_graph_query(graph, "Give ZZR its code and then explain why.")
    assert explanation["status"] != "ready"
    assert any("why" in item["text"] for item in explanation["unresolved_parts"])


def test_partial_name_exposes_source_choices_without_accepting_alias(graph):
    plan = plan_graph_query(graph, "What does fold pulsed mean?")
    assert plan["status"] == "clarification_required"
    unresolved = next(item for item in plan["unresolved_parts"] if item.get("candidate_ids"))
    assert set(unresolved["candidate_ids"]) == {"toy:pulsed", "toy:deep"}
    assert not plan["resolved_entities"]


def test_child_followups_reference_exact_clause_operations(graph):
    plan = plan_graph_query(graph, "List direct children of Ribbon fold and their categories; list direct children of Squeeze join and their categories.")
    children = [item for item in plan["operations"] if item["kind"] == "direct_children"]
    categories = [item for item in plan["operations"] if item["kind"] == "category"]
    assert len(children) == len(categories) == 2
    assert [item["dependency_operation_ids"] for item in categories] == [[children[0]["operation_id"]], [children[1]["operation_id"]]]


def test_concept_ids_are_link_metadata_not_new_source_or_relation_facts(graph):
    plan = plan_graph_query(graph, "What does ZZR stand for?", concept_bindings={"toy:ribbon": "concept:ribbon"})
    assert plan["mentions"][0]["candidate_concept_ids"] == ["concept:ribbon"]
    assert "concept:ribbon" not in plan["resolved_entities"]
    assert graph["nodes"][0].get("concept_bindings") is None


def test_list_attributes_and_ellipsis_keep_returned_row_scope(graph):
    plan = plan_graph_query(graph, "List all descendants of ALPHA FAMILY, including each acronym. Give each printed name and code; which broader box contains them?")
    attributes = [part for part in plan["requested_parts"] if part["kind"] in {"designation","category"}]
    assert attributes and all(part.get("subject_scope")=="returned_children" for part in attributes)
    assert all(not part["subject_ids"] and part["selector_subject_ids"]==["toy:alpha"] for part in attributes)
    category = next(operation for operation in plan["operations"] if operation["kind"]=="category")
    assert category["use_returned_children"] and category["dependency_operation_ids"]
    changed = plan_graph_query(graph, "List direct children of Ribbon fold; what is the code for Squeeze join; give its category.")
    final = [operation for operation in changed["operations"] if operation["kind"]=="category"][-1]
    assert final["subject_ids"]==["toy:squeeze"] and not final.get("use_returned_children")
    immediate = plan_graph_query(graph,"Show the indented rows immediately below Ribbon fold, including their codes.")
    producer = next(operation for operation in immediate["operations"] if operation["kind"]=="direct_children")
    assert producer["subject_ids"]==["toy:ribbon"]
    code = next(part for part in immediate["requested_parts"] if part["kind"]=="designation")
    assert code["subject_scope"]=="returned_children" and code["operation_ids"]==[producer["operation_id"]]
    interrupted = plan_graph_query(graph,"List direct children of Ribbon fold; give Mystery bind its code; give its category.")
    assert not any(operation["kind"]=="category" for operation in interrupted["operations"])
    assert any(part["kind"]=="category" and part["status"]=="unsupported" for part in interrupted["unresolved_parts"])


def test_qualified_identity_and_typed_modifier_roles_do_not_hide_unknowns(graph):
    modified = deepcopy(graph)
    next(node for node in modified["nodes"] if node["id"]=="toy:alpha")["label"]="ALPHA LONG FAMILY (AF)"
    plan = plan_graph_query(modified,"Is Ribbon fold in ALPHA FAMILY?",concept_bindings={"toy:alpha":"concept:alpha"})
    assert "toy:alpha" in plan["resolved_entities"]
    qualified = next(mention for mention in plan["mentions"] if mention.get("qualification"))
    assert qualified["qualification"]=="query_interpretation_not_verified_alias"
    assert qualified["candidate_concept_ids"]==["concept:alpha"]
    assert not plan["unresolved_parts"]
    modifier = plan_graph_query(graph,"Give ZZR its immediately displayed parent and its enclosing category.")
    assert any(role["role"]=="attribute_modifier" for role in modifier["language_roles"])
    assert not modifier["unresolved_parts"]
    unknown = plan_graph_query(graph,"Give ZZR its code and cost.")
    assert any("cost" in item["text"] for item in unknown["unresolved_parts"])


def test_partition_root_navigation_and_sparse_single_word_choices(graph):
    partition = plan_graph_query(graph,"Separate the unindented process rows in ALPHA FAMILY from its indented entries. Give each printed name and acronym.")
    operation = next(item for item in partition["operations"] if item["kind"]=="row_partition")
    assert operation["subject_ids"]==["toy:alpha"] and operation["query_layer"]=="evidence"
    assert any(item.get("subject_scope")=="returned_children" for item in partition["requested_parts"] if item["kind"]=="designation")
    route = plan_graph_query(graph,"Trace the displayed route from Ribbon fold to the central joining box.")
    path = next(item for item in route["operations"] if item["kind"]=="paths")
    assert path["start_ids"]==["toy:ribbon"] and path["end_ids"]==["toy:root"]
    root = next(item for item in route["mentions"] if "chart_root_navigation" in item["methods"])
    assert root["candidate_ids"]==["toy:root"]
    partial = plan_graph_query(graph,"What is the code for ribbon?")
    assert partial["status"]=="clarification_required"
    assert set(next(item["candidate_ids"] for item in partial["unresolved_parts"] if item.get("candidate_ids")))=={"toy:ribbon","toy:pulsed","toy:deep"}


def test_possessive_suffix_preserves_named_subject_and_unknown_fields(graph):
    for apostrophe in ("'", "\u2019"):
        plan = plan_graph_query(graph,"What amperage and shielding gas does this chart specify for Ribbon fold? "
            f"Also give the chart{apostrophe}s abbreviation and enclosing group.")
        followups = [operation for operation in plan["operations"] if operation["kind"] in {"designation","category"}]
        assert {operation["kind"] for operation in followups} == {"designation","category"}
        assert all(operation["subject_ids"]==["toy:ribbon"] for operation in followups)
        assert [part["text"] for part in plan["unresolved_parts"]] == ["shielding gas"]
        literal = plan_graph_query(graph,f"Give Ribbon fold{apostrophe}s code.")
        assert literal["status"]=="ready"
        assert next(operation for operation in literal["operations"] if operation["kind"]=="designation")["subject_ids"]==["toy:ribbon"]
        role = next(role for role in literal["language_roles"] if role["role"]=="possessive_grammar")
        assert role["text"]==f"{apostrophe}s"
        unknown = plan_graph_query(graph,f"Give ZZR its code; give Mystery bind{apostrophe}s code; give its category.")
        assert not any(operation["kind"]=="category" for operation in unknown["operations"])
        assert any("Mystery" in part["text"] or "mystery" in part["text"] for part in unknown["unresolved_parts"])


def test_state_is_typed_request_verb_not_entity_slot_stopword(graph):
    plan = plan_graph_query(graph,"Show direct children of Ribbon fold with their codes, then state which box encloses them.")
    assert not plan["unresolved_parts"]
    role = next(role for role in plan["language_roles"] if role["role"]=="request_verb")
    assert role["text"]=="state" and role["target_kinds"]==["category"]
    category = next(operation for operation in plan["operations"] if operation["kind"]=="category")
    assert category["subject_scope"]=="returned_children" and category["dependency_operation_ids"]
    changed = deepcopy(graph)
    next(node for node in changed["nodes"] if node["id"]=="toy:squeeze")["label"]="State join"
    selector = plan_graph_query(changed,"What is the code for state?")
    assert selector["status"]=="clarification_required"
    assert not any(role["role"]=="request_verb" for role in selector["language_roles"])
    assert any(part.get("candidate_ids")==["toy:squeeze"] for part in selector["unresolved_parts"])
    cost = plan_graph_query(graph,"State ZZR's cost.")
    assert any("cost" in part["text"] for part in cost["unresolved_parts"])


def test_coordinated_identity_and_parent_share_only_same_request_selector(graph):
    plan = plan_graph_query(graph,"In Figure A1, identify the process and its parent for ribbon.")
    fields = [part for part in plan["requested_parts"] if part["kind"] in {"designation","parents"}]
    assert {part["kind"] for part in fields}=={"designation","parents"}
    assert all(part["status"]=="ambiguous" and part["resolution_part_ids"] for part in fields)
    assert all(set(part["candidate_ids"])=={"toy:ribbon","toy:pulsed","toy:deep"} for part in fields)
    assert not plan["operations"] and not plan["resolved_entities"]
    literal = plan_graph_query(graph,"Identify the process and its parent for ZZR.")
    assert literal["status"]=="ready"
    assert {operation["kind"] for operation in literal["operations"]}=={"designation","parents"}
    assert all(operation["subject_ids"]==["toy:ribbon"] for operation in literal["operations"])
    separate = plan_graph_query(graph,"Identify the process; give Ribbon fold its parent.")
    identity = next(part for part in separate["requested_parts"] if part["kind"]=="designation")
    assert identity["status"]=="unsupported" and not identity["subject_ids"]


def test_bound_relation_predicate_role_preserves_unknown_selector_and_property(graph):
    query = "Does the chart place Foil bind under Ribbon fold; give its cost."
    plan = plan_graph_query(graph,query)
    role = next(role for role in plan["language_roles"] if role["role"]=="bound_relation_predicate")
    assert role["text"]=="place" and role["target_kinds"]==["layout_relation"]
    assert [query[first:last] for first,last in role["argument_spans"]]==["Foil bind","Ribbon fold"]
    assert any("cost" in part["text"] for part in plan["unresolved_parts"])
    assert not any(part["text"]=="place" for part in plan["unresolved_parts"])
    unknown = plan_graph_query(graph,"Does the chart place Mystery bind under Ribbon fold?")
    assert not any(role["role"]=="bound_relation_predicate" for role in unknown["language_roles"])
    assert any("Mystery" in part["text"] or "mystery" in part["text"] for part in unknown["unresolved_parts"])
    selector = plan_graph_query(graph,"What is the code for place?")
    assert not any(role["role"]=="bound_relation_predicate" for role in selector["language_roles"])
    assert selector["unresolved_parts"]
    selector_relation = plan_graph_query(graph,"What is the code for place Foil bind under Ribbon fold?")
    assert not any(role["role"]=="bound_relation_predicate" for role in selector_relation["language_roles"])
    assert any("place" in part["text"] for part in selector_relation["unresolved_parts"])
