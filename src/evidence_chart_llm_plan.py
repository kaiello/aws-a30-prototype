"""Model-to-typed-plan contract. This module never calls a model or executes a plan.

Schema, compact instructions and argument validation share operation profiles.
Source IDs identify observations; they grant no relationship admission authority.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re

from src.evidence_a1 import validate_chart_graph_evidence
from src.evidence_a1_graph_qa import _graph_index
from src.evidence_a1_lexicon import heading, source_dictionary
from src.evidence_chart_contract import (
    CONTRACT_VERSION, CONTRACT_SHA256, SCHEMA_VERSION, INSTRUCTION_VERSION,
    COVERAGE, MAX_OPERATIONS, MAX_PARTS, MAX_RESULT_REFS, MAX_LITERAL_IDS,
    MAX_RESOLVED_IDS, MAX_INFORMATION_FIELDS, MAX_QUERY_LENGTH, MAX_STRING_LENGTH,
    MAX_REASON_LENGTH, ALL_KINDS, ID_PATTERN, OPERATION_KEYS, PART_KEYS,
    ENVELOPE_KEYS, PLANNED_REASON, PART_REASON_RULE, PART_OPERATIONS_RULE,
    OPERATION_PROFILES, EMPTY_SUBJECT_SCOPES, planner_instructions,
)


def _information_rule(key):
    """The same explicit per-kind restriction is shown in prose and schema.

    These describe existing compiler guards, not additional output projections.
    The flat grammar schema intentionally cannot enforce every typed rule.
    """
    allowed = [kind for kind, profile in OPERATION_PROFILES.items() if profile[key]]
    if key == "fields":
        choices = list(dict.fromkeys(field for profile in OPERATION_PROFILES.values()
                                    for field in profile[key]))
        return ("fields: only " + "/".join(allowed) + " may use this array; require 1.."
                + str(len(choices)) + " values from " + "/".join(choices)
                + ". Every other operation requires fields=[].")
    return (key + ": only " + "/".join(allowed) + " may use this array; values must quote "
            "phrases in the question. Every other operation requires " + key + "=[].")


def _reject(code):
    raise ValueError("CHART_LLM_PLAN_" + code)


def _object(value, keys, code):
    if not isinstance(value, dict) or set(value) != set(keys):
        _reject(code)


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(ID_PATTERN, value):
        _reject("RECORD_ID_INVALID")


def _strings(value, limit, code="ARRAY_INVALID"):
    if (not isinstance(value, list) or len(value) > limit
            or any(not isinstance(item, str) or not item or len(item) > MAX_STRING_LENGTH for item in value)
            or len(set(value)) != len(value)):
        _reject(code)


def _source_index(graph):
    try:
        nodes, _, _ = _graph_index(graph)
        validate_chart_graph_evidence(graph)
        element = graph["source_binding"]["locator"]["element_id"]
    except (ValueError, KeyError, TypeError, AttributeError):
        _reject("SOURCE_GRAPH_INVALID")
    aliases = {f"n{index+1}": node["id"] for index, node in enumerate(graph["nodes"])}
    return nodes, aliases, element


def _scope(graph, query):
    """Use the existing reference lexer; do not reinterpret page numbers as facts."""
    from src.standard_manifest import extract_reference_records
    locator = graph["source_binding"]["locator"]
    lexical = re.sub(
        r"\b(Figure|Fig\.?)\s+(?=[A-Za-z]\.?\d+(?:\([^\n;]*?\))?\s*(?:,\s*(?:and\s+)?|and\s+)[A-Za-z]?\.?\d)",
        "Figures ", query, flags=re.I)
    # Explicit PDF index is zero based; PDF page/ordinal is one based.
    def pdf_page(match):
        first, last = int(match["first"]), int(match["last"] or match["first"])
        expected = locator["pdf_index"] + (0 if (match["basis"] or "").casefold() == "index" else 1)
        if first != expected or last != expected:
            _reject("SOURCE_SCOPE_MISMATCH")
        if re.match(r"\s*(?:,\s*(?:and\s+)?|and\s+)\d", lexical[match.end():], re.I):
            _reject("SOURCE_SCOPE_MISMATCH")
        return " " * len(match[0])
    lexical = re.sub(r"\bPDF\s+(?:page\s+)?(?:(?P<basis>index|ordinal)\s+)?"
        r"(?P<first>\d+)(?:\s*[-–—]\s*(?P<last>\d+))?", pdf_page, lexical, flags=re.I)
    for record in extract_reference_records(lexical):
        if record["kind"] != "page":
            resolution = record["resolution"]
            allowed = {locator["element_id"], "Annex A"}
            for n in graph.get("nodes", []):
                if n.get("source_figure"):
                    allowed.add(n["source_figure"])
                if n.get("target_figure"):
                    allowed.add(n["target_figure"])
            if (resolution["status"] != "exact"
                    or any(label not in allowed
                           for label in resolution.get("labels", []))):
                _reject("SOURCE_SCOPE_MISMATCH")
        if record.get("qualifiers", {}).get("page"):
            candidates = record.get("page_candidates", [])
            if (not candidates or any(item["pdf_index"] != locator["pdf_index"] for item in candidates)
                    or re.match(r"\s*(?:,\s*(?:and\s+)?|and\s+)\d", lexical[record["end"]:], re.I)):
                _reject("SOURCE_SCOPE_MISMATCH")


def _array(limit, *, items=None):
    return {"type": "array", "maxItems": limit, "uniqueItems": True,
            "items": items or {"type": "string", "minLength": 1, "maxLength": 256}}


def _identity_ambiguities(graph, query, parts):
    """Keep dictionary choices explicit for unresolved identity selectors.

    Reuse the existing lexical selector boundaries, never the deterministic
    operation planner or source relationships. Exact printed identities dominate
    overlapping fragments. Complex unrecognized selectors remain a limitation.
    """
    from src.evidence_a1_planner import _source_context_spans, _selector_bodies, resolve_mentions
    from src.evidence_a1_lexicon import suggest_identities
    found = []
    nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
    for part in parts:
        text = part["quote"]
        mentions = resolve_mentions(graph, text)
        choices = [dict(mention) for mention in mentions if mention["status"] == "ambiguous"]
        masked = list(text)
        for mention in mentions:
            masked[mention["start"]:mention["end"]] = " " * (mention["end"] - mention["start"])
        masked = "".join(masked)
        for first, last in _selector_bodies(text, graph):
            boundaries = [first]
            for separator in re.finditer(r",|\band\b|\bor\b", masked[first:last], re.I):
                boundaries.extend((first + separator.start(), first + separator.end()))
            boundaries.append(last)
            for start, end in zip(boundaries[::2], boundaries[1::2]):
                if any(start < item["end"] and item["start"] < end for item in mentions):
                    continue
                fragment = text[start:end].strip(" ,.? ")
                fragment = re.sub(r"^(?:the|a|an)\s+", "", fragment, flags=re.I)
                candidates = suggest_identities(graph, fragment)
                if len(candidates) > 1:
                    cand_nodes = [nodes_by_id[nid] for nid in candidates if nid in nodes_by_id]
                    codes = {n.get("code") for n in cand_nodes if n.get("kind") == "process" and n.get("code")}
                    same_code = len(codes) == 1 and len(cand_nodes) == len([n for n in cand_nodes if n.get("kind") == "process"])
                    labels = {n.get("label", "").casefold() for n in cand_nodes if n.get("kind") == "category" and n.get("label")}
                    same_label = len(labels) == 1 and len(cand_nodes) == len([n for n in cand_nodes if n.get("kind") == "category"])
                    if not (same_code or same_label):
                        choices.append({"text": fragment, "candidate_ids": candidates,
                                        "status": "ambiguous", "method": "source_name_fragment"})
        if choices:
            found.append({"part_id": part["id"], "choices": choices})
    return found


def output_schema(graph):
    """Flat structural schema for the local grammar converter.

    Do not combine common required fields with narrower oneOf/allOf branches:
    the installed converter drops their siblings. Per-kind, prior-result and
    combined-budget guards remain in the unchanged profiles/compiler. This
    schema is deliberately a structural superset, not permission to execute.
    """
    _, aliases, element = _source_index(graph)
    node_ids = _array(MAX_LITERAL_IDS, items={"type": "string", "enum": list(aliases)})
    result_refs = _array(MAX_RESULT_REFS, items={"type": "object", "additionalProperties": False,
        "required": ["operation_id", "select"], "properties": {
            "operation_id": {"type": "string", "pattern": ID_PATTERN},
            "select": {"type": "string", "enum": ["rows", "categories", "parents", "groups"]}}})
    fields = list(dict.fromkeys(field for profile in OPERATION_PROFILES.values() for field in profile["fields"]))
    layers = list(dict.fromkeys(layer for profile in OPERATION_PROFILES.values() for layer in profile["layers"]))
    return {"type": "object", "additionalProperties": False,
        "description": (INSTRUCTION_VERSION + ". Flat structural schema; generated descriptions specify "
            "typed restrictions enforced by the compiler. JSON-schema success alone grants no execution authority."),
        "required": list(ENVELOPE_KEYS),
        "properties": {"schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "source_element": {"type": "string", "const": element},
            "query": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_LENGTH},
            "parts": {"type": "array", "minItems": 1, "maxItems": MAX_PARTS, "items": {
                "type": "object", "additionalProperties": False, "required": list(PART_KEYS),
                "properties": {"id": {"type": "string", "pattern": ID_PATTERN},
                    "quote": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_LENGTH},
                    "status": {"type": "string", "enum": ["planned", "unresolved"]},
                    "operation_ids": {**_array(MAX_OPERATIONS, items={"type": "string", "pattern": ID_PATTERN}),
                                      "description": PART_OPERATIONS_RULE},
                    "reason": {"type": "string", "maxLength": MAX_REASON_LENGTH, "description": PART_REASON_RULE}}}},
            "operations": {"type": "array", "maxItems": MAX_OPERATIONS, "items": {
                "type": "object", "additionalProperties": False, "required": list(OPERATION_KEYS),
                "properties": {"id": {"type": "string", "pattern": ID_PATTERN},
                    "kind": {"type": "string", "enum": list(OPERATION_PROFILES)},
                    "query_layer": {"type": "string", "enum": layers},
                    "subject_ids": deepcopy(node_ids), "target_ids": deepcopy(node_ids),
                    "result_refs": {"type": "object", "additionalProperties": False, "required": ["subjects", "targets"],
                        "properties": {"subjects": deepcopy(result_refs), "targets": deepcopy(result_refs)}},
                    "fields": {**_array(len(fields), items={"type": "string", "enum": fields}),
                               "description": _information_rule("fields")},
                    "requested_fields": {**_array(MAX_INFORMATION_FIELDS), "description": _information_rule("requested_fields")},
                    "requested_aspects": {**_array(MAX_INFORMATION_FIELDS), "description": _information_rule("requested_aspects")}}}}}}


def operation_contract():
    lines = [INSTRUCTION_VERSION + ". Return JSON {" + ",".join(ENVELOPE_KEYS) + "}; schema_version=" + SCHEMA_VERSION + ". Copy query/source_element. No answers, SQL, new IDs, edges or facts.",
        "Part={" + ",".join(PART_KEYS) + "}. Operation={" + ",".join(OPERATION_KEYS) + "}.",
        "result_refs={subjects:[{operation_id,select}],targets:[{operation_id,select}]}; IDs refer to prior operation.id. subject_ids/target_ids contain catalog IDs. A ref adds actual prior results to that role.",
        "Each part labels a requested clause; quote is not a character-partition proof. Retain every substantive request, quantifier, negation, direction and follow-up. " + PART_OPERATIONS_RULE + " " + PART_REASON_RULE,
        "IDs are catalog aliases. result_refs subjects/targets select ACTUAL prior results only: rows=returned rows; categories=positive enclosing categories with source edges; parents=returned direct parents; groups=union of returned group.node_ids, not group subjects. Empty/failed refs fail, never guess.",
        f"At most {MAX_PARTS} parts/{MAX_OPERATIONS} operations. Per operation: subjects+targets literal aliases <= {MAX_LITERAL_IDS}; refs <= {MAX_RESULT_REFS}. Runtime resolved-role IDs <= {MAX_RESOLVED_IDS}; limits reject, never truncate.",
        "All operation keys are required; unused arrays are []. requested_fields/aspects describe missing operating information or evidence questions, never output columns or proposed source values.",
        *(_information_rule(key) for key in ("fields", "requested_fields", "requested_aspects")),
        "Layer is explicit: evidence includes qualified observations; knowledge uses admitted assertions only. Identity recognition never accepts a relationship. Physical connections are undirected; indentation is not semantic IS_A.",
        "JSON schema checks structure; compiler additionally checks exact source/query identity, combined budgets and typed prior-result guards. Schema validity alone is not executable-plan validity."]
    for kind, profile in OPERATION_PROFILES.items():
        subject = "0+" if not profile["minimum"] else ("1" if profile["single"] else str(profile["minimum"]) + "+")
        lines.append(kind + ": subjects=" + subject + " " + "/".join(profile["subjects"])
            + "; targets=" + ("/".join(profile["targets"]) if profile["targets"] else "none")
            + "; layer=" + "/".join(profile["layers"])
            + ("; fields=1..2 from " + "/".join(profile["fields"]) if profile["fields"] else "; fields=[]")
            + ("; requested_fields=question phrases" if profile["requested_fields"] else "; requested_fields=[]")
            + ("; requested_aspects=question phrases" if profile["requested_aspects"] else "; requested_aspects=[]")
            + "; " + profile["meaning"] + ".")
    lines.append(planner_instructions())
    return "\n".join(lines)


def identity_catalog(graph):
    """Literal dictionary identities only; no relationships or prior answers."""
    nodes, aliases, _ = _source_index(graph)
    vocabulary = source_dictionary(graph)

    # Context chains from layout edges
    incoming = {}
    for e in graph.get("edges", []):
        u, v = e.get("from"), e.get("to")
        if u and v:
            incoming.setdefault(v, []).append(u)

    context_chains = {}
    for nid, node in nodes.items():
        curr = nid
        chain = []
        visited = set()
        while curr in incoming and incoming[curr] and curr not in visited:
            visited.add(curr)
            parent_id = incoming[curr][0]
            p_node = nodes.get(parent_id)
            if p_node:
                p_label = p_node.get("label", "")
                if p_label and not p_label.startswith("MATERIALS") and not p_label.startswith("See Figure"):
                    chain.append(p_label)
            curr = parent_id
        if chain:
            chain.reverse()
            context_chains[nid] = " -> ".join(chain)

    rows = []
    for alias, identifier in aliases.items():
        node = nodes[identifier]
        label, code = heading(node) if node["kind"] == "category" else (node["label"], node.get("code"))
        if node.get("subtype") == "footnote" or "footnote" in identifier.lower():
            if identifier == "a3node:footnote_a":
                label = "Footnote a: Welding is considered to apply to the group of process categories. Fastening systems are omitted for simplicity."
            elif node.get("text"):
                label = f"Footnote {node.get('marker', '')}: {node['text']}".strip()
        names = list(dict.fromkeys(item["text"] for item in vocabulary
            if item["node_id"] == identifier and item["method"] == "source_bound_printed_alias"))
        if node.get("energy_source"):
            names.append(node["energy_source"])
            if node["energy_source"].casefold() not in label.casefold():
                label = f"{label} ({node['energy_source']})"
        if node.get("column"):
            names.append(node["column"])
        if identifier in context_chains:
            names.append(context_chains[identifier])
        if node.get("is_underlined") or node.get("underline"):
            names.append("underlined")
            if "underlined" not in label.casefold():
                label = f"{label} (underlined)"
        if "footnote" in identifier.lower() or node.get("subtype") == "footnote":
            names.extend(["footnote", f"footnote {node.get('marker', '')}".strip(), "omitted for simplicity", "fastening systems"])
        rows.append([alias, node["kind"], label, code or "", list(dict.fromkeys(names))])
    return rows


def build_prompt(graph, query):
    _, _, element = _source_index(graph)
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_LENGTH:
        _reject("QUERY_INVALID")
    _scope(graph, query)
    return operation_contract() + "\nINPUT=" + json.dumps({"query": query, "source_element": element,
        "catalog_columns": ["id", "kind", "printed_label", "printed_code", "verified_aliases"],
        "catalog": identity_catalog(graph)}, ensure_ascii=False, separators=(",", ":"))


def _arguments(operation, nodes, aliases, prior, query):
    profile = OPERATION_PROFILES[operation["kind"]]
    if operation["query_layer"] not in profile["layers"]:
        _reject("LAYER_INVALID")
    for key in ("subject_ids", "target_ids", "fields", "requested_fields", "requested_aspects"):
        _strings(operation[key], MAX_INFORMATION_FIELDS if key.startswith("requested_") else MAX_LITERAL_IDS)
    if len(operation["subject_ids"]) + len(operation["target_ids"]) > MAX_LITERAL_IDS:
        _reject("LITERAL_BUDGET_EXCEEDED")
    if any(identifier not in aliases for identifier in operation["subject_ids"] + operation["target_ids"]):
        _reject("UNKNOWN_SOURCE_ID")
    _object(operation["result_refs"], ("subjects", "targets"), "RESULT_REFS_INVALID")
    total = 0
    for role in ("subjects", "targets"):
        refs = operation["result_refs"][role]
        if not isinstance(refs, list) or len(refs) > MAX_RESULT_REFS:
            _reject("RESULT_REFS_INVALID")
        total += len(refs)
        seen = set()
        allowed = profile["subjects"] if role == "subjects" else profile["targets"]
        literal = operation["subject_ids" if role == "subjects" else "target_ids"]
        if not allowed and (literal or refs):
            _reject("UNUSED_ROLE_NOT_EMPTY")
        minimum = profile["minimum"] if role == "subjects" else bool(profile["targets"])
        if minimum and not refs and len(literal) < minimum:
            _reject("SUBJECT_OR_TARGET_REQUIRED")
        if role == "subjects" and profile["single"] and len(literal) + len(refs) != 1:
            _reject("SINGLE_SUBJECT_REQUIRED")
        if any(nodes[aliases[identifier]]["kind"] not in allowed for identifier in literal):
            _reject("SOURCE_KIND_INVALID")
        for ref in refs:
            _object(ref, ("operation_id", "select"), "RESULT_REF_INVALID")
            _identifier(ref["operation_id"])
            if not isinstance(ref["select"], str):
                _reject("RESULT_SELECTION_KIND_INVALID")
            key = (ref["operation_id"], ref["select"])
            if key in seen:
                _reject("DUPLICATE_RESULT_REF")
            seen.add(key)
            if ref["operation_id"] not in prior:
                _reject("RESULT_REF_NOT_PRIOR")
            producer_kind = prior[ref["operation_id"]].get("kind")
            producer_profile = OPERATION_PROFILES.get(producer_kind) if isinstance(producer_kind, str) else None
            if producer_profile is None:
                _reject("RESULT_DEPENDENCY_INVALID")
            producer = producer_profile["produces"]
            if ref["select"] not in producer or not set(producer[ref["select"]]) & set(allowed):
                _reject("RESULT_SELECTION_KIND_INVALID")
    if total > MAX_RESULT_REFS:
        _reject("RESULT_REF_BUDGET_EXCEEDED")
    if profile["fields"]:
        if not operation["fields"] or any(field not in profile["fields"] for field in operation["fields"]):
            _reject("FIELDS_INVALID")
        if "category" in operation["fields"] and any(nodes[aliases[item]]["kind"] != "process" for item in operation["subject_ids"]):
            _reject("CATEGORY_REQUIRES_PROCESS")
    elif operation["fields"]:
        _reject("FIELDS_INVALID")
    for key in ("requested_fields", "requested_aspects"):
        if operation[key] and not profile[key]:
            _reject("UNUSED_INFORMATION_FIELDS")
        if any(not field.strip() or field.casefold() not in query.casefold() for field in operation[key]):
            _reject("INFORMATION_FIELD_NOT_IN_QUERY")


def _supplement_existing_relation_intent(graph, nodes, plan, concept_bindings):
    """Keep a model path, adding only an independently selected literal relation.

    This reuses the existing intent planner rather than interpreting node kinds
    as a request. Its evidence-layer operation remains source qualified; the
    original model operations and unverified coverage authority are unchanged.
    """
    operations, parts = plan["operations"], plan["requested_parts"]
    if (plan["status"] != "ready" or len(operations) >= MAX_OPERATIONS
            or len(parts) != 1 or parts[0]["status"] != "planned"
            or any(item.get("compilation_errors") or item.get("result_refs")
                   or item.get("dependency_operation_ids")
                   or item["query_layer"] != "evidence"
                   or item["kind"] not in {"designation", "paths"} for item in operations)):
        return
    paths = [item for item in operations if item["kind"] == "paths"]
    if len(paths) != 1:
        return
    path = paths[0]
    left, right = path.get("start_ids", []), path.get("end_ids", [])
    if (len(left) != 1 or len(right) != 1 or left == right
            or path.get("waypoint_ids") or path.get("requested_direction") != "from_to"
            or any(not item["subject_ids"] or not set(item["subject_ids"]) <= set(left + right)
                   for item in operations)):
        return
    from src.evidence_a1_planner import plan_graph_query
    intent = plan_graph_query(graph, plan["query"], concept_bindings=concept_bindings)
    intent_parts = intent.get("requested_parts", [])
    if (intent["status"] != "ready" or intent.get("diagnostics")
            or intent.get("unresolved_parts") or intent.get("unresolved_selectors")
            or len(intent["operations"]) != 1 or len(intent_parts) != 1
            or intent_parts[0]["status"] != "planned"):
        return
    relation = intent["operations"][0]
    profile = OPERATION_PROFILES["layout_relation"]
    if (relation["kind"] != "layout_relation" or relation.get("query_layer") != "evidence"
            or relation.get("left_ids") != left or relation.get("right_ids") != right
            or relation.get("subject_ids") != left + right
            or relation.get("result_refs") or relation.get("dependency_operation_ids")
            or nodes[left[0]]["kind"] not in profile["subjects"]
            or nodes[right[0]]["kind"] not in profile["targets"]):
        return
    supplement = deepcopy(relation)
    supplement.update(operation_id="guard:layout_relation", request_ids=[parts[0]["id"]],
        dependency_operation_ids=[], selection_origin="existing_deterministic_intent_supplement")
    operations.append(supplement)
    parts[0]["operation_ids"].append(supplement["operation_id"])
    parts[0]["kind"] = "compound"
    plan["deterministic_supplements"] = [{
        "operation_id": supplement["operation_id"], "selection_origin": supplement["selection_origin"],
        "planner_version": intent["planner_version"], "source_operation_id": relation["operation_id"],
        "source_request_id": intent_parts[0]["id"], "source_path_operation_id": path["operation_id"],
        "model_selected_supplement": False, "original_model_operations_retained": True}]


def compile_plan(graph, query, payload, concept_bindings=None, *, supplement_relation_intent=True):
    """Compile one typed batch without granting semantic completeness.

    Envelope/source/reference integrity fails closed. An addressable invalid
    operation stays in the batch as a nonexecuting placeholder, so independent
    operations can run without hiding the failed request or its dependencies.
    The exact original model plan is retained. A narrow, explicitly recorded
    supplement can reuse an existing deterministic literal relationship intent.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_LENGTH:
        _reject("QUERY_INVALID")
    nodes, aliases, element = _source_index(graph)
    _scope(graph, query)
    _object(payload, ENVELOPE_KEYS, "TOP_LEVEL_INVALID")
    if payload["schema_version"] != SCHEMA_VERSION or payload["query"] != query or payload["source_element"] != element:
        _reject("SCHEMA_QUERY_OR_SOURCE_MISMATCH")
    if (not isinstance(payload["operations"], list) or len(payload["operations"]) > MAX_OPERATIONS
            or not isinstance(payload["parts"], list) or not 1 <= len(payload["parts"]) <= MAX_PARTS):
        _reject("RECORD_BUDGET_INVALID")
    prior, errors = {}, {}
    for operation in payload["operations"]:
        if not isinstance(operation, dict):
            _reject("OPERATION_RECORD_INVALID")
        _identifier(operation.get("id"))
        if operation["id"] in prior:
            _reject("DUPLICATE_OPERATION_ID")
        try:
            _object(operation, OPERATION_KEYS, "OPERATION_KEYS_INVALID")
            if not isinstance(operation["kind"], str) or operation["kind"] not in OPERATION_PROFILES:
                _reject("UNKNOWN_OPERATION")
            _arguments(operation, nodes, aliases, prior, query)
        except ValueError as exc:
            errors[operation["id"]] = [str(exc)]
        prior[operation["id"]] = operation
    referenced, seen_parts, spans = set(), set(), {}
    for part in payload["parts"]:
        _object(part, PART_KEYS, "PART_KEYS_INVALID")
        _identifier(part["id"])
        if part["id"] in seen_parts:
            _reject("DUPLICATE_PART_ID")
        seen_parts.add(part["id"])
        quote = part["quote"]
        if not isinstance(quote, str) or not quote.strip() or len(quote) > MAX_QUERY_LENGTH:
            _reject("PART_SPAN_INVALID")
        start = query.find(quote)
        spans[part["id"]] = ([start, start + len(quote)]
            if start >= 0 and query.find(quote, start + 1) < 0 else None)
        if not isinstance(part["reason"], str) or len(part["reason"]) > MAX_REASON_LENGTH:
            _reject("PART_REASON_INVALID")
        _strings(part["operation_ids"], MAX_OPERATIONS)
        if part["status"] == "planned":
            if not part["operation_ids"] or part["reason"] != PLANNED_REASON or any(item not in prior for item in part["operation_ids"]):
                _reject("PLANNED_PART_INVALID")
            referenced.update(part["operation_ids"])
        elif part["status"] != "unresolved" or part["operation_ids"] or not part["reason"].strip():
            _reject("UNRESOLVED_PART_INVALID")
    for identifier in set(prior) - referenced:
        errors.setdefault(identifier, []).append("CHART_LLM_PLAN_UNREFERENCED_OPERATION")
    ambiguities = _identity_ambiguities(graph, query, payload["parts"])
    # Inspect the original request too: clause labels must not hide an ambiguous
    # source name. This links identities only; it does not select graph facts.
    whole = _identity_ambiguities(graph, query, [{"id": "compiler:request_identity", "quote": query}])
    known_choices = {(choice["text"].casefold(), tuple(choice["candidate_ids"]))
        for item in ambiguities for choice in item["choices"]}
    omitted = [choice for item in whole for choice in item["choices"]
        if (choice["text"].casefold(), tuple(choice["candidate_ids"])) not in known_choices]
    if omitted:
        ambiguities.append({"part_id": "compiler:request_identity", "choices": omitted})
    ambiguous_parts = {item["part_id"]: item["choices"] for item in ambiguities}
    for part in payload["parts"]:
        if part["id"] in ambiguous_parts:
            for identifier in part["operation_ids"]:
                errors.setdefault(identifier, []).append("CHART_LLM_PLAN_AMBIGUOUS_SOURCE_IDENTITY")
    if omitted:
        # An omitted ambiguous name could affect any guessed operation. Preserve
        # all of them, but do not execute a subset whose identity scope is unsafe.
        for identifier in prior:
            errors.setdefault(identifier, []).append("CHART_LLM_PLAN_UNASSIGNED_IDENTITY_AMBIGUITY")
    compiled, operation_aliases, deduplications, equivalent = [], {}, [], {}
    for external in payload["operations"]:
        external_id = external["id"]
        if external_id in errors:
            identifier = "model:" + external_id
            literal = [value for role in ("subject_ids", "target_ids")
                for value in (external.get(role) if isinstance(external.get(role), list) else [])
                if isinstance(value, str) and value in aliases]
            refs = external.get("result_refs", {})
            dependencies = list(dict.fromkeys(dependency
                for values in (refs.values() if isinstance(refs, dict) else [])
                for ref in (values if isinstance(values, list) else [])
                if isinstance(ref, dict) and isinstance(ref.get("operation_id"), str)
                for dependency in operation_aliases.get(ref.get("operation_id"), [])))
            compiled.append({"operation_id": identifier,
                "kind": external.get("kind") if isinstance(external.get("kind"), str)
                    and external["kind"] in OPERATION_PROFILES else "unsupported",
                "query_layer": external.get("query_layer", "evidence"),
                "subject_ids": list(dict.fromkeys(aliases[value] for value in literal)),
                "request_ids": [], "external_operation_id": external_id,
                "external_kind": external.get("kind"), "compilation_errors": errors[external_id],
                "dependency_operation_ids": dependencies})
            operation_aliases[external_id] = [identifier]
            continue
        mapped = []
        fields = external["fields"] if external["kind"] == "comparison" else [external["kind"]]
        for field in fields:
            kind = field
            identifier = "model:" + external["id"] + (":" + field if external["kind"] == "comparison" else "")
            mapped.append(identifier)
            subject = [aliases[item] for item in external["subject_ids"]]
            target = [aliases[item] for item in external["target_ids"]]
            role_names = ("start_ids", "end_ids") if kind == "paths" else (
                ("left_ids", "right_ids") if kind in {"membership", "layout_relation"} else ("subject_ids", None))
            operation = {"operation_id": identifier, "kind": kind, "query_layer": external["query_layer"],
                "subject_ids": list(dict.fromkeys(subject + target)), "request_ids": [],
                "external_operation_id": external["id"], "external_kind": external["kind"]}
            if role_names[0] != "subject_ids":
                operation.update({role_names[0]: subject, role_names[1]: target})
            if kind == "paths":
                operation.update(requested_direction="from_to", waypoint_ids=[])
            result_refs, constraints = {}, {}
            profile = OPERATION_PROFILES[field if field != "evidence" else "evidence"]
            for role, internal in zip(("subjects", "targets"), role_names):
                if internal is None:
                    continue
                refs = external["result_refs"][role]
                if refs:
                    result_refs[internal] = [{"operation_id": dependency, "select": ref["select"]}
                        for ref in refs for dependency in operation_aliases[ref["operation_id"]]]
                minimum = (max(profile["minimum"], OPERATION_PROFILES[external["kind"]]["minimum"])
                           if role == "subjects" else bool(profile["targets"]))
                allowed = profile["subjects"] if role == "subjects" else profile["targets"]
                if allowed:
                    constraints[internal] = {"minimum": int(minimum),
                        "maximum": 1 if role == "subjects" and profile["single"] else MAX_RESOLVED_IDS,
                        "kinds": list(allowed)}
            if result_refs:
                operation.update(result_refs=result_refs, result_constraints=constraints)
            if external["requested_fields"]:
                operation["requested_fields"] = list(external["requested_fields"])
            if external["requested_aspects"]:
                operation["requested_aspects"] = list(external["requested_aspects"])
            if kind in EMPTY_SUBJECT_SCOPES and not subject and not operation.get("result_refs"):
                operation["scope"] = EMPTY_SUBJECT_SCOPES[kind]
            operation["dependency_operation_ids"] = list(dict.fromkeys(
                ref["operation_id"] for refs in result_refs.values() for ref in refs))
            # Equivalent execution only: fields/aspects, layer, direction,
            # constraints and dependency selections remain in the semantic key.
            key = json.dumps({key: value for key, value in operation.items()
                if key not in {"operation_id", "request_ids", "external_operation_id", "external_kind"}},
                sort_keys=True, separators=(",", ":"))
            if key in equivalent:
                survivor = equivalent[key]
                mapped[-1] = survivor
                deduplications.append({"operation_id": identifier, "equivalent_to": survivor})
            else:
                equivalent[key] = identifier
                compiled.append(operation)
        operation_aliases[external_id] = list(dict.fromkeys(mapped))
    parts = []
    by_operation = {item["operation_id"]: item for item in compiled}
    for part in payload["parts"]:
        identifiers = list(dict.fromkeys(item for external in part["operation_ids"]
                                        for item in operation_aliases[external]))
        subjects = list(dict.fromkeys(item for operation in identifiers for item in by_operation[operation]["subject_ids"]))
        actual_kind = by_operation[identifiers[0]]["kind"] if len(identifiers) == 1 else "compound"
        record = {"id": part["id"], "text": part["quote"], "span": spans[part["id"]],
            "kind": actual_kind if identifiers else "unresolved", "subject_ids": subjects,
            "operation_ids": identifiers, "status": "planned" if identifiers else "unsupported",
            "coverage_authority": COVERAGE}
        if not identifiers:
            # Free model prose is retained in external_plan, not asserted as a
            # source fact by the deterministic answer composer.
            record["reason"] = "model_reported_unresolved_requirement"
            record["model_reason"] = part["reason"]
        if part["id"] in ambiguous_parts:
            choices = ambiguous_parts[part["id"]]
            record.update(status="ambiguous", kind="entity_resolution",
                reason="ambiguous_source_identity", candidate_ids=list(dict.fromkeys(
                    value for choice in choices for value in choice["candidate_ids"])))
        if any(by_operation[item].get("result_refs") for item in identifiers):
            record["subject_scope"] = "operation_results"
        for identifier in identifiers:
            if part["id"] not in by_operation[identifier]["request_ids"]:
                by_operation[identifier]["request_ids"].append(part["id"])
        parts.append(record)
    if omitted:
        parts.append({"id": "compiler:request_identity", "text": query, "span": [0, len(query)],
            "kind": "entity_resolution", "subject_ids": [], "operation_ids": [],
            "status": "ambiguous", "reason": "ambiguous_source_identity",
            "candidate_ids": list(dict.fromkeys(value for choice in omitted for value in choice["candidate_ids"])),
            "coverage_authority": COVERAGE})
    resolved = list(dict.fromkeys(item for operation in compiled for item in operation["subject_ids"]))
    result = {"planner_version": SCHEMA_VERSION, "instruction_revision": INSTRUCTION_VERSION,
        "contract_version": CONTRACT_VERSION, "contract_sha256": CONTRACT_SHA256,
        "query": query, "status": ("partial" if errors and any(not item.get("compilation_errors") for item in compiled)
            else "clarification_required" if ambiguities else "invalid" if errors
            else "ready" if compiled else "unresolved"),
        "operations": compiled, "requested_parts": parts, "resolved_entities": resolved,
        "diagnostics": list(dict.fromkeys(error for values in errors.values() for error in values))
            or ([] if compiled else ["no_planned_operations"]),
        "unresolved_selectors": [part["quote"] for part in payload["parts"] if part["status"] == "unresolved"],
        "source_context": [{"source_element": element}], "coverage_authority": COVERAGE,
        "semantic_validation": False, "quote_partition_required": False,
        "identity_ambiguities": ambiguities, "operation_aliases": operation_aliases,
        "deduplications": deduplications, "external_plan": deepcopy(payload),
        "concept_bindings": dict(concept_bindings or {})}
    if supplement_relation_intent:
        _supplement_existing_relation_intent(graph, nodes, result, concept_bindings)
    return result
