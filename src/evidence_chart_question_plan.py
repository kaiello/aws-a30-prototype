"""Question actions lowered to the existing typed chart plan, without execution.

Names identify source observations only. The existing compiler and executor
retain authority over types, dependencies, evidence and knowledge admission.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re

from src.evidence_a1_lexicon import link_entities, source_dictionary, words
from src.evidence_a1_planner import resolve_mentions
from src.evidence_chart_contract import (
    QUESTION_INTERFACE, SCHEMA_VERSION, COVERAGE, ID_PATTERN, MAX_OPERATIONS,
    MAX_PARTS, MAX_LITERAL_IDS, MAX_RESULT_REFS, MAX_INFORMATION_FIELDS,
    MAX_QUERY_LENGTH, MAX_STRING_LENGTH, MAX_REASON_LENGTH, PLANNED_REASON,
)
from src import evidence_chart_llm_plan as legacy


def _reject(code):
    raise ValueError("CHART_QUESTION_PLAN_" + code)


def _strings(values, limit):
    if (not isinstance(values, list) or len(values) > limit
            or any(not isinstance(value, str) or not value.strip()
                   or len(value) > MAX_STRING_LENGTH for value in values)
            or len(set(values)) != len(values)):
        _reject("ARRAY_INVALID")


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(ID_PATTERN, value):
        _reject("RECORD_ID_INVALID")


def _request(graph, query):
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_LENGTH:
        _reject("QUERY_INVALID")
    nodes, aliases, element = legacy._source_index(graph)
    legacy._scope(graph, query)
    return nodes, aliases, element


def output_schema(graph):
    """A flat structural schema; typed lowering remains a separate safety gate."""
    _, _, element = legacy._source_index(graph)
    identifier = {"type": "string", "pattern": ID_PATTERN}
    def array(limit, items=None):
        return {"type": "array", "maxItems": limit, "uniqueItems": True,
                "items": items or {"type": "string", "minLength": 1,
                                   "maxLength": MAX_STRING_LENGTH}}
    return {"type": "object", "additionalProperties": False,
        "required": list(QUESTION_INTERFACE["envelope_keys"]), "properties": {
            "schema_version": {"type": "string", "const": QUESTION_INTERFACE["schema_version"]},
            "source_element": {"type": "string", "const": element},
            "query": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_LENGTH},
            "parts": {"type": "array", "minItems": 1, "maxItems": MAX_PARTS,
                "items": {"type": "object", "additionalProperties": False,
                    "required": list(QUESTION_INTERFACE["part_keys"]), "properties": {
                        "id": identifier, "quote": {"type": "string", "minLength": 1,
                            "maxLength": MAX_QUERY_LENGTH},
                        "status": {"type": "string", "enum": ["planned", "unresolved"]},
                        "action_ids": array(MAX_OPERATIONS, identifier),
                        "reason": {"type": "string", "maxLength": MAX_REASON_LENGTH,
                            "description": QUESTION_INTERFACE["part_metadata"]["description"]}}}},
            "actions": {"type": "array", "maxItems": MAX_OPERATIONS,
                "items": {"type": "object", "additionalProperties": False,
                    "required": list(QUESTION_INTERFACE["action_keys"]), "properties": {
                        "id": identifier,
                        "kind": {"type": "string", "enum": list(QUESTION_INTERFACE["kinds"])},
                        "query_layer": {"type": "string", "enum": ["evidence", "knowledge"]},
                        "subjects": array(MAX_LITERAL_IDS), "targets": array(MAX_LITERAL_IDS),
                        "subjects_from": array(MAX_RESULT_REFS, identifier),
                        "targets_from": array(MAX_RESULT_REFS, identifier),
                        "fields": array(len(QUESTION_INTERFACE["fields"]), {
                            "type": "string", "enum": list(QUESTION_INTERFACE["fields"])}),
                        "mode": {"type": "string", "enum": list(dict.fromkeys(
                            mode for modes in QUESTION_INTERFACE["modes"].values() for mode in modes))},
                        "information_fields": array(MAX_INFORMATION_FIELDS),
                        "scope": {"type": "string", "enum": list(QUESTION_INTERFACE["scopes"])}}}}}}


def build_prompt(graph, query):
    _, aliases, element = _request(graph, query)
    reverse = {identifier: alias for alias, identifier in aliases.items()}
    mentions = [{"text": item["text"], "span": [item["start"], item["end"]],
                 "status": item["status"],
                 "candidates": [reverse[value] for value in item["candidate_ids"]]}
                for item in resolve_mentions(graph, query)]
    lines = [QUESTION_INTERFACE["instruction_version"],
        "Envelope={" + ",".join(QUESTION_INTERFACE["envelope_keys"]) + "}.",
        "Action={" + ",".join(QUESTION_INTERFACE["action_keys"]) + "}.",
        "Part={" + ",".join(QUESTION_INTERFACE["part_keys"]) + "}.",
        f"At most {MAX_PARTS} parts and {MAX_OPERATIONS} total lowered operations; retain every request.",
        f"Per-action literal selector budget={MAX_LITERAL_IDS}, prior-result reference budget={MAX_RESULT_REFS}; "
        f"information_fields budget={MAX_INFORMATION_FIELDS}. Limits reject, never truncate.",
        "Fields=" + "/".join(QUESTION_INTERFACE["fields"]) + "; scopes="
            + "/".join(QUESTION_INTERFACE["scopes"]) + ".",
        *(kind + " modes=" + json.dumps(list(QUESTION_INTERFACE["modes"][kind])) + "."
          for kind in QUESTION_INTERFACE["kinds"]),
        QUESTION_INTERFACE["part_metadata"]["description"],
        *QUESTION_INTERFACE["guidance"]]
    data = {"schema_version": QUESTION_INTERFACE["schema_version"], "query": query,
        "source_element": element, "catalog_columns": ["id", "kind", "printed_label", "printed_code", "verified_aliases"],
        "catalog": legacy.identity_catalog(graph), "linked_mentions": mentions}
    return "\n".join(lines) + "\nINPUT=" + json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _selectors(graph, values, aliases):
    reverse, identifiers, choices = {value: key for key, value in aliases.items()}, [], []
    vocabulary = source_dictionary(graph)
    for value in values:
        if value in aliases:
            identifiers.append(value)
            continue
        literal = value.strip()
        matches = [item for item in link_entities(graph, literal)
                   if item["start"] == 0 and item["end"] == len(literal)]
        # The linker also supports question navigation ("the root"). This
        # interface promises printed identities only; a complete printed entry
        # must corroborate each candidate, while linker case/overlap guards stay
        # authoritative. A printed label literally named "root" remains valid.
        printed = {entry["node_id"] for entry in vocabulary
            if (entry["text"].casefold() == literal.casefold() if entry["method"].endswith("_code")
                else words(entry["text"]) == words(literal))}
        candidates = list(dict.fromkeys(candidate for item in matches
            for candidate in item["candidate_ids"] if candidate in printed))
        if len(candidates) != 1:
            choices.append({"selector": value, "status": "ambiguous" if candidates else "unknown",
                            "candidate_ids": candidates})
        else:
            identifiers.append(reverse[candidates[0]])
    return list(dict.fromkeys(identifiers)), choices


def _operation(identifier, kind, layer, subjects=(), targets=(), refs=None, fields=()):
    return {"id": identifier, "kind": kind, "query_layer": layer,
        "subject_ids": list(subjects), "target_ids": list(targets),
        "result_refs": deepcopy(refs or {"subjects": [], "targets": []}), "fields": [],
        "requested_fields": list(fields), "requested_aspects": []}


def _lower_action(graph, query, action, aliases, prior, prefix, element=None):
    if element is None:
        _, _, element = legacy._source_index(graph)
    if set(action) != set(QUESTION_INTERFACE["action_keys"]):
        _reject("ACTION_KEYS_INVALID")
    kind, mode, layer = action["kind"], action["mode"], action["query_layer"]
    if not isinstance(kind, str) or kind not in QUESTION_INTERFACE["kinds"]:
        _reject("KIND_INVALID")
    if mode not in QUESTION_INTERFACE["modes"][kind] or layer not in {"evidence", "knowledge"}:
        _reject("MODE_OR_LAYER_INVALID")
    for key in ("subjects", "targets", "subjects_from", "targets_from", "fields", "information_fields"):
        _strings(action[key], MAX_INFORMATION_FIELDS if key == "information_fields" else
                 MAX_RESULT_REFS if key.endswith("_from") else MAX_LITERAL_IDS)
    if (len(action["subjects"]) + len(action["targets"]) > MAX_LITERAL_IDS
            or len(action["subjects_from"]) + len(action["targets_from"]) > MAX_RESULT_REFS):
        _reject("COMBINED_BUDGET_EXCEEDED")
    if any(field not in QUESTION_INTERFACE["fields"] for field in action["fields"]):
        _reject("FIELD_INVALID")
    if action["scope"] not in QUESTION_INTERFACE["scopes"]:
        _reject("SCOPE_INVALID")
    chart_scope = action["scope"] == "chart"
    if chart_scope:
        if kind not in {"check_relationship", "list_members"}:
            _reject("CHART_SCOPE_UNSUPPORTED")
    chart_names = {element.casefold(), "figure a1", "figure a2", "a1", "a2"}
    raw_subjects = [s for s in action["subjects"] if s.casefold() not in chart_names] if chart_scope else action["subjects"]
    raw_targets = [t for t in action["targets"] if t.casefold() not in chart_names] if chart_scope else action["targets"]
    subjects, choices = _selectors(graph, raw_subjects, aliases)
    targets, target_choices = _selectors(graph, raw_targets, aliases)
    choices += target_choices
    if choices:
        return [], None, choices
    refs = {"subjects": [], "targets": []}
    for role in refs:
        if action[role] and action[role + "_from"]:
            _reject("LITERALS_AND_REFERENCES_MIXED")
        for previous in action[role + "_from"]:
            _identifier(previous)
            if previous not in prior:
                _reject("REFERENCE_NOT_PRIOR")
            producer = prior[previous]
            if not producer.get("anchor"):
                _reject("REFERENCE_PRODUCER_INVALID_OR_FAILED")
            refs[role].append({"operation_id": producer["anchor"], "select": producer["selection"]})
    if chart_scope:
        if layer != "evidence":
            _reject("EVIDENCE_LAYER_REQUIRED")
    elif not subjects and not refs["subjects"]:
        _reject("SELECTED_SUBJECT_REQUIRED")
    if kind in {"lookup_term", "list_members"} and (targets or refs["targets"]):
        _reject("UNUSED_TARGETS")
    targetless_membership = kind == "check_relationship" and mode == "membership" and not (targets or refs["targets"])
    targetless_layout = kind == "check_relationship" and mode in {"layout", "semantic_subtype"} and not (targets or refs["targets"])
    if kind == "explain_path" and not (targets or refs["targets"]):
        _reject("TARGET_REQUIRED")
    if kind == "check_relationship" and not chart_scope and mode != "source_limits" and not targetless_membership and not targetless_layout:
        if not (targets or refs["targets"]):
            _reject("TARGET_REQUIRED")
    if kind == "check_relationship" and mode in {"layout", "semantic_subtype", "source_limits"} and layer != "evidence":
        _reject("EVIDENCE_LAYER_REQUIRED")
    operations = []
    def add(operation_kind, selected=subjects, destinations=targets, references=refs, information=()):
        identifier = prefix + "_" + str(len(operations) + 1)
        operations.append(_operation(identifier, operation_kind, layer, selected, destinations,
                                     references, information))
        return identifier
    if kind == "lookup_term":
        anchor = add("designation", destinations=[])
        selection = "rows"
    elif kind == "list_members":
        if chart_scope and not subjects and not refs["subjects"]:
            anchor = add("chart_layout", selected=[], destinations=[])
            add("epistemic_limits", destinations=[])
            selection = None
        else:
            anchor = add({"direct": "direct_children", "descendants": "descendants", "parents": "parents",
                          "row_partition": "row_partition", "physical_neighbors": "physical_neighbors"}[mode], destinations=[])
            selection = {"parents": "parents", "physical_neighbors": "groups", "direct": "groups",
                         "descendants": "groups"}.get(mode, "rows")
    elif kind == "explain_path":
        anchor = add("paths")
        selection = None
    elif chart_scope:
        anchor = add("chart_layout", selected=[], destinations=[])
        add("epistemic_limits", selected=subjects, destinations=[])
        selection = None
    elif mode == "source_limits":
        if targets or refs["targets"]:
            _reject("UNUSED_TARGETS")
        anchor = add("epistemic_limits", destinations=[])
        selection = None
    elif targetless_membership:
        anchor = add("category", destinations=[])
        selection = "categories"
    elif targetless_layout:
        if mode == "layout":
            anchor = add("parents", destinations=[])
            selection = "parents"
        else:
            anchor = add("epistemic_limits", destinations=[])
            selection = None
    else:
        nodes = {n["id"]: n for n in graph["nodes"]}
        target_kinds = {nodes[aliases[t]]["kind"] for t in targets if t in aliases and aliases[t] in nodes}
        subject_kinds = {nodes[aliases[s]]["kind"] for s in subjects if s in aliases and aliases[s] in nodes}
        if mode in {"layout", "semantic_subtype"} and (("root" in subject_kinds or "category" in subject_kinds) or "root" in target_kinds):
            # Physical route / connector between non-process subjects or root target
            anchor = add("paths")
            selection = None
            if mode in {"layout", "semantic_subtype"}:
                add("epistemic_limits", destinations=[], references={"subjects": refs["subjects"], "targets": []})
        else:
            anchor = add("membership" if mode == "membership" else "layout_relation")
            selection = None
            if mode in {"layout", "semantic_subtype"}:
                add("epistemic_limits", destinations=[], references={"subjects": refs["subjects"], "targets": []})
    # Project requested fields over actual lookup/list results. For a relation or
    # path, identity/evidence projections cover both selected endpoints.
    if selection:
        projected, projections = [], {"subjects": [{"operation_id": anchor, "select": selection}], "targets": []}
    else:
        projected = list(dict.fromkeys(subjects + targets))
        projections = {"subjects": refs["subjects"] + refs["targets"], "targets": []}
    for field, operation_kind in (("group", "category"), ("evidence", "evidence"), ("source_limits", "epistemic_limits")):
        if field in action["fields"]:
            if chart_scope and field in {"group", "evidence"}:
                continue
            if (targetless_membership or targetless_layout) and field == "group":
                continue
            if not (field == "source_limits" and kind == "check_relationship" and mode != "membership"):
                if operation_kind == "category":
                    nodes = {n["id"]: n for n in graph["nodes"]}
                    cat_selected = [s for s in projected if nodes.get(aliases.get(s, s), {}).get("kind") == "process"] if not selection else projected
                    if cat_selected or selection:
                        add(operation_kind, selected=cat_selected, destinations=[], references=projections)
                else:
                    add(operation_kind, selected=projected, destinations=[], references=projections)
    if kind not in {"lookup_term", "list_members"} and set(action["fields"]) & {"name", "acronym"}:
        if chart_scope:
            pass
        elif targetless_membership or targetless_layout:
            add("designation", selected=subjects, destinations=[], references={"subjects": refs["subjects"], "targets": []})
        else:
            add("designation", selected=projected, destinations=[], references=projections)
    elif kind == "list_members" and mode in {"parents", "physical_neighbors"} and "acronym" in action["fields"]:
        # These list renderers print labels only. Resolve codes from their
        # actual returned parents/neighbors, never the original selector.
        add("designation", selected=projected, destinations=[], references=projections)
    valid_info = [field for field in action["information_fields"]
                  if field.strip() and field.casefold() in query.casefold()]
    if valid_info:
        add("operating_information", selected=projected, destinations=[], references=projections,
            information=valid_info)
    return operations, {"anchor": anchor, "selection": selection} if selection else None, []


def compile_plan(graph, query, payload, concept_bindings=None):
    """Lower question actions, retaining both original intent and execution wire.

    Invalid addressable actions become blocked operations. Independent valid
    actions remain executable; legacy guards still validate every lowered op.
    """
    _, aliases, element = _request(graph, query)
    if not isinstance(payload, dict) or set(payload) != set(QUESTION_INTERFACE["envelope_keys"]):
        _reject("ENVELOPE_INVALID")
    if (payload["schema_version"] != QUESTION_INTERFACE["schema_version"]
            or payload["source_element"] != element or payload["query"] != query):
        _reject("SCHEMA_QUERY_OR_SOURCE_MISMATCH")
    if (not isinstance(payload["actions"], list) or len(payload["actions"]) > MAX_OPERATIONS
            or not isinstance(payload["parts"], list) or not 1 <= len(payload["parts"]) <= MAX_PARTS):
        _reject("RECORD_BUDGET_INVALID")
    prior, action_operations, action_errors, identity_choices, operations = {}, {}, {}, {}, []
    for index, action in enumerate(payload["actions"]):
        if not isinstance(action, dict):
            _reject("ACTION_INVALID")
        identifier = action.get("id")
        _identifier(identifier)
        if identifier in prior:
            _reject("DUPLICATE_ACTION_ID")
        prefix, error = "action" + str(index + 1), None
        try:
            lowered, producer, choices = _lower_action(graph, query, action, aliases, prior, prefix, element)
            if choices:
                identity_choices[identifier] = choices
                _reject("SOURCE_SELECTOR_UNRESOLVED")
            # Reserve one placeholder for each remaining action, never truncate.
            if len(operations) + len(lowered) + len(payload["actions"]) - index - 1 > MAX_OPERATIONS:
                _reject("LOWERED_OPERATION_BUDGET_EXCEEDED")
        except (ValueError, TypeError) as exc:
            error = str(exc) if isinstance(exc, ValueError) else "CHART_QUESTION_PLAN_ACTION_VALUE_INVALID"
            lowered, producer = [_operation(prefix + "_blocked", "unsupported", "evidence")], None
        prior[identifier] = producer or {}
        if error:
            action_errors[identifier] = [error]
        action_operations[identifier] = [item["id"] for item in lowered]
        operations.extend(lowered)
    parts, part_metadata = [], []
    for part in payload["parts"]:
        if not isinstance(part, dict) or set(part) != set(QUESTION_INTERFACE["part_keys"]):
            _reject("PART_INVALID")
        # Validate external metadata before mapping it. A rationale has no
        # operation/evidence authority; the strict internal planned-part wire
        # uses the shared empty reason, while unresolved explanations retain
        # their existing required/nonblank semantics in the legacy compiler.
        if not isinstance(part["reason"], str) or len(part["reason"]) > MAX_REASON_LENGTH:
            _reject("PART_REASON_INVALID")
        if part["status"] not in ("planned", "unresolved"):
            _reject("PART_STATUS_INVALID")
        _strings(part["action_ids"], MAX_OPERATIONS)
        if any(identifier not in action_operations for identifier in part["action_ids"]):
            _reject("UNKNOWN_PART_ACTION")
        internal_reason = PLANNED_REASON if part["status"] == "planned" else part["reason"]
        part_metadata.append({"part_id": part["id"], "status": part["status"],
            "original_reason": part["reason"], "internal_reason": internal_reason,
            "authority": "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"})
        parts.append({key: deepcopy(value) for key, value in part.items() if key not in {"action_ids", "reason"}}
                     | {"operation_ids": [operation for identifier in part["action_ids"]
                                          for operation in action_operations[identifier]],
                        "reason": internal_reason})
    wire = {"schema_version": SCHEMA_VERSION, "query": query, "source_element": element,
            "parts": parts, "operations": operations}
    result = legacy.compile_plan(graph, query, wire, concept_bindings=concept_bindings,
                                 supplement_relation_intent=False)
    result.update(planner_version=QUESTION_INTERFACE["schema_version"],
        instruction_revision=QUESTION_INTERFACE["instruction_version"],
        external_plan=deepcopy(payload), lowered_plan=deepcopy(wire), model_part_metadata=part_metadata,
        question_actions=deepcopy(payload["actions"]), action_errors=action_errors,
        action_identity_choices=identity_choices,
        action_operation_ids={identifier: list(dict.fromkeys(actual
            for operation in selected for actual in result["operation_aliases"][operation]))
            for identifier, selected in action_operations.items()},
        coverage_authority=COVERAGE, semantic_validation=False)
    for action_id, errors in action_errors.items():
        for operation in result["operations"]:
            if operation["operation_id"] in result["action_operation_ids"][action_id]:
                operation.setdefault("compilation_errors", []).extend(errors)
    result["diagnostics"] = list(dict.fromkeys(result["diagnostics"] + [
        error for errors in action_errors.values() for error in errors]))
    return result
