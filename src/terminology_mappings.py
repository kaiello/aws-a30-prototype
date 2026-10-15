"""Pure, opt-in terminology records for supplied, reviewed entry boundaries.

This does not extract a glossary, read a manifest, invent ontology IDs, or persist
anything. ``manifest`` is an already loaded source-location view. Ontology rows
must explicitly carry ``verification_state='verified'`` and compatible spelling,
sense and process context; cached names alone cannot resolve an endpoint.

An entry supplies term, definition, sense, process_context, source_id and source.
Source includes document_id/source_sha256/section_id/pdf_index/printed_label,
record_id, a half-open span into text, and verification_state. Optional targets
give exact ``text`` boundaries and optional target_id/sense/provenance. They are
required for ambiguous top-level 'or'; parentheses and hyphens remain intact.
"""
from copy import deepcopy
import hashlib
import json
import re


def _normal(value):
    return " ".join(str(value or "").split()).casefold()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _unique(values):
    result, seen = [], set()
    for value in values:
        key = _json(value)
        if key not in seen:
            result.append(deepcopy(value))
            seen.add(key)
    return result


def _source_diagnostics(source, manifest, term, definition):
    required = ("document_id", "source_sha256", "section_id", "pdf_index",
                "printed_label", "record_id", "span", "text")
    if not isinstance(source, dict) or any(key not in source for key in required):
        return ["source_metadata_incomplete"]
    issues = []
    text, span = source["text"], source["span"]
    valid_span = (isinstance(text, str) and isinstance(span, list) and len(span) == 2
                  and all(type(value) is int for value in span)
                  and 0 <= span[0] < span[1] <= len(text))
    if (not valid_span or (term is not None and definition is not None
            and _normal(term + ". " + definition) != _normal(text[span[0]:span[1]]))):
        issues.append("source_span_mismatch")
    if not isinstance(source["record_id"], str) or not source["record_id"].strip():
        issues.append("source_record_missing")
    if source.get("verification_state") != "verified":
        issues.append("source_entry_unverified")
    if manifest is None:
        issues.append("source_manifest_unavailable")
        return issues
    document = manifest.document
    if (source["document_id"] != document["id"]
            or source["source_sha256"] != document["sha256"]
            or not isinstance(source["source_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", source["source_sha256"])):
        issues.append("source_document_mismatch")
    if (type(source["pdf_index"]) is not int
            or manifest.resolve(source["section_id"])["status"] != "exact"
            or not any(source["pdf_index"] == anchor["pdf_index"]
                       and source["printed_label"] == anchor["printed_label"]
                       for anchor in manifest.anchors(source["section_id"]))):
        issues.append("source_anchor_mismatch")
    return issues


def _top_level_parts(text, separator):
    """Return bounded separator spans; never split inside parenthesized context."""
    depth, start, parts = 0, 0, []
    index = 0
    while index < len(text):
        character = text[index]
        depth += (character == "(") - (character == ")")
        if depth < 0:
            raise ValueError("unbalanced_parentheses")
        match = re.match(separator, text[index:], flags=re.IGNORECASE) if depth == 0 else None
        if match:
            parts.append(text[start:index].strip())
            index += len(match.group())
            start = index
        else:
            index += 1
    if depth:
        raise ValueError("unbalanced_parentheses")
    parts.append(text[start:].strip())
    if not all(parts):
        raise ValueError("empty_target")
    return parts


def _target_parts(body, supplied):
    # Validate parenthesis balance even when the caller supplies target boundaries.
    semicolon_parts = _top_level_parts(body, r";")
    if supplied is not None:
        if not isinstance(supplied, list) or not supplied or any(
                not isinstance(part, dict) or not isinstance(part.get("text"), str)
                or not part["text"].strip() for part in supplied):
            raise ValueError("invalid_target_boundaries")
        pattern = r"(?:\s+or\s+|\s*;\s*)".join(re.escape(_normal(part["text"])) for part in supplied)
        if not re.fullmatch(pattern, _normal(body)):
            raise ValueError("target_boundaries_mismatch")
        return deepcopy(supplied)
    if any(len(_top_level_parts(part, r"\s+or\s+")) > 1 for part in semicolon_parts):
        raise ValueError("ambiguous_target_boundaries")
    return [{"text": part} for part in semicolon_parts]


def _target_wording(text):
    match = re.fullmatch(r"([^()]+?)\s*\(([^()]+)\)", text.strip())
    if match:
        return match[1].strip(), match[2].strip()
    if "(" in text or ")" in text:
        raise ValueError("unsupported_target_context")
    return text.strip(), ""


def _resolve_node(nodes, name, context, sense, requested_id=None):
    matches = [node for node in nodes if isinstance(node, dict) and node.get("verification_state") == "verified"
               and isinstance(node.get("id"), str) and node["id"]
               and (requested_id is None or node["id"] == requested_id)
               and _normal(node.get("name")) == _normal(name)
               and _normal(node.get("process_context")) == _normal(context)
               and _normal(node.get("sense")) == _normal(sense)]
    ids = list(dict.fromkeys(node["id"] for node in matches))
    return ids[0] if len(ids) == 1 else None


def _identity(record, *, include_target_id=True):
    source = record.get("source") or {}
    source_key = {key: source.get(key) for key in
                  ("document_id", "source_sha256", "section_id", "pdf_index", "printed_label", "record_id", "span", "text")}
    key = {field: _normal(record.get(field)) for field in
           ("nonstandard_term", "source_sense", "source_process_context", "preferred_term",
            "target_sense", "target_process_context", "relation_type", "qualification")}
    key.update(source=source_key, source_id=record.get("source_id"))
    if include_target_id:
        key["target_id"] = record.get("target_id")
    return "mapping:" + hashlib.sha256(_json(key).encode("utf-8")).hexdigest()


def _validate_record(record):
    if not isinstance(record, dict) or not isinstance(record.get("source"), dict):
        raise ValueError("invalid_mapping_record: source must be an object")
    for field in ("nonstandard_term", "preferred_term"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError("invalid_mapping_record: term labels must be nonempty strings")
    for field in ("source_id", "target_id"):
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("invalid_mapping_record: IDs must be strings or null")
    for field in ("provenance", "target_provenance", "diagnostics"):
        if not isinstance(record.get(field, []), list):
            raise ValueError("invalid_mapping_record: evidence and diagnostics must be lists")


def merge_mapping_records(records):
    """Merge normalized duplicates, preserving first labels and evidence order.

    Distinct source entries/pages, senses, processes or target IDs retain their
    identities. Conflicting resolutions of the same qualified target are kept as
    explicit candidates rather than choosing a last writer.
    """
    merged = {}
    for original in records:
        _validate_record(original)
        record = deepcopy(original)
        record["mapping_id"] = _identity(record)
        record.setdefault("diagnostics", [])
        record["provenance"] = _unique(record.get("provenance", []))
        record["target_provenance"] = _unique(record.get("target_provenance", []))
        previous = merged.get(record["mapping_id"])
        if previous is None:
            merged[record["mapping_id"]] = record
            continue
        for field in ("provenance", "target_provenance", "diagnostics"):
            previous[field] = _unique(previous[field] + record[field])
        if record.get("verification_state") != "verified":
            previous["verification_state"] = "candidate"
    groups = {}
    for record in merged.values():
        groups.setdefault(_identity(record, include_target_id=False), []).append(record)
    for group in groups.values():
        if len({record["target_id"] for record in group if record.get("target_id")}) > 1:
            for record in group:
                record["verification_state"] = "candidate"
                record["diagnostics"] = _unique(record["diagnostics"] + ["conflicting_target_resolution"])
    return list(merged.values())


def parse_nonstandard_entry(entry, *, manifest=None, ontology_nodes=()):
    """Parse one structured entry; diagnostics never imply full-page extraction.

    Source 'verified' means the caller has reviewed this entry/span. Manifest
    checks certify its location, not the wording's independent entailment.
    """
    if not isinstance(entry, dict):
        return {"records": [], "diagnostics": ["bounded_entry_required"]}
    term, definition = entry.get("term"), entry.get("definition")
    if (not isinstance(term, str) or not term.strip() or not isinstance(definition, str)
            or "\n" in definition or "\r" in definition):
        return {"records": [], "diagnostics": ["bounded_entry_required"]}
    match = re.fullmatch(r"A nonstandard term (?P<qualification>when used for|for)\s+(?P<targets>.+?)\.", definition.strip(), re.IGNORECASE)
    if not match or ". " in match["targets"]:
        return {"records": [], "diagnostics": ["unsupported_entry_formula"]}
    try:
        targets = _target_parts(match["targets"], entry.get("targets"))
        wordings = [_target_wording(target["text"]) for target in targets]
    except ValueError as error:
        return {"records": [], "diagnostics": [str(error)]}
    nodes = list(ontology_nodes)
    source = deepcopy(entry["source"]) if isinstance(entry.get("source"), dict) else {}
    source_issues = _source_diagnostics(source, manifest, term.strip(), definition.strip())
    source_id = _resolve_node(nodes, term, entry.get("process_context", ""), entry.get("sense", ""), entry.get("source_id"))
    if source_id is None:
        source_issues.append("source_ontology_unresolved")
    records = []
    for target, (wording, context) in zip(targets, wordings):
        target_id = _resolve_node(nodes, wording, context, target.get("sense", ""), target.get("target_id"))
        issues = list(source_issues)
        if target_id is None:
            issues.append("target_ontology_unresolved")
        target_provenance = deepcopy(target.get("provenance", []))
        if not isinstance(target_provenance, list):
            issues.append("invalid_target_provenance")
            target_provenance = []
        if target_provenance:
            # These are separate target-definition source records, not aliases'
            # evidence. Their reviewed text need not repeat this redirect.
            for proof in target_provenance:
                issues.extend(_source_diagnostics(proof, manifest, None, None))
        record = {"nonstandard_term": term.strip(), "source_id": source_id,
                  "source_sense": entry.get("sense", ""), "source_process_context": entry.get("process_context", ""),
                  "preferred_term": wording, "target_id": target_id, "target_sense": target.get("sense", ""),
                  "target_process_context": context, "relation_type": "NONSTANDARD_FOR",
                  "qualification": _normal(match["qualification"]), "source": source,
                  "provenance": [deepcopy(source)] if source else [], "target_provenance": target_provenance,
                  "verification_state": "candidate" if issues else "verified", "diagnostics": _unique(issues)}
        records.append(record)
    records = merge_mapping_records(records)
    return {"records": records, "diagnostics": _unique([issue for record in records for issue in record["diagnostics"]])}


def _owned_edge(attributes, key):
    return (attributes.get("projection_owner") == "terminology_mappings"
            and attributes.get("mapping_id") == key
            and attributes.get("rel_type") == "NONSTANDARD_FOR"
            and attributes.get("layer") == "ontology"
            and type(attributes.get("weight")) in (int, float)
            and attributes["weight"] == 1.0
            and attributes.get("verification_state") == "verified")


def project_mapping_records(graph, records):
    """Add derived edges only to the supplied directed multigraph, without I/O.

    Existing nodes and legacy edges are immutable here. New edge attributes are
    GraphML-safe scalars; canonical JSON retains the full structured record.
    Conflicting resolutions across calls reject the incoming record and require
    operator review; existing evidence is never silently replaced or downgraded.
    """
    if not graph.is_directed() or not graph.is_multigraph():
        raise ValueError("A directed multigraph is required")
    projected, diagnostics = [], []
    try:
        records = merge_mapping_records(records)
    except ValueError as error:
        return {"projected_ids": [], "diagnostics": [str(error)]}
    for record in records:
        key = record["mapping_id"]
        if record.get("verification_state") != "verified" or record.get("relation_type") != "NONSTANDARD_FOR":
            diagnostics.append("mapping_unverified:" + key)
            continue
        compatible = True
        for prefix, name in (("source", "nonstandard_term"), ("target", "preferred_term")):
            node_id = record.get(prefix + "_id")
            if node_id not in graph:
                compatible = False
                break
            node = dict(graph.nodes[node_id], id=node_id)
            if _resolve_node([node], record[name], record.get(prefix + "_process_context", ""),
                             record.get(prefix + "_sense", ""), node_id) is None:
                compatible = False
                break
        if not compatible:
            diagnostics.append("graph_endpoint_incompatible:" + key)
            continue
        source_id, target_id = record["source_id"], record["target_id"]
        existing = graph.get_edge_data(source_id, target_id, key)
        if existing is not None and not _owned_edge(existing, key):
            diagnostics.append("graph_edge_key_conflict:" + key)
            continue
        qualified_identity = _identity(record, include_target_id=False)
        previous_same_key, blocked = None, False
        for _, _, previous_key, attributes in graph.out_edges(source_id, keys=True, data=True):
            if not _owned_edge(attributes, previous_key):
                continue
            try:
                previous = json.loads(attributes.get("mapping_json"))
                _validate_record(previous)
            except (TypeError, ValueError):
                diagnostics.append("invalid_mapping_record: existing derived edge " + str(previous_key))
                blocked = True
                break
            if (_identity(previous, include_target_id=False) == qualified_identity
                    and previous.get("target_id") != target_id):
                diagnostics.append("conflicting_target_resolution:" + key)
                blocked = True
                break
            if previous_key == key:
                previous_same_key = previous
        if blocked:
            continue
        if existing is not None:
            try:
                combined = merge_mapping_records([previous_same_key, record])
                if len(combined) != 1 or combined[0]["mapping_id"] != key:
                    raise ValueError("mapping identity conflict")
                record = combined[0]
                if record.get("verification_state") != "verified":
                    raise ValueError("unverified existing mapping")
            except (TypeError, ValueError, KeyError):
                diagnostics.append("graph_edge_key_conflict:" + key)
                continue
        graph.add_edge(source_id, target_id, key=key, mapping_id=key,
                       rel_type="NONSTANDARD_FOR", layer="ontology", weight=1.0,
                       projection_owner="terminology_mappings",
                       verification_state=record["verification_state"], mapping_json=_json(record))
        projected.append(key)
    return {"projected_ids": projected, "diagnostics": diagnostics}
