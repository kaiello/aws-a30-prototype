"""One-image Figure A1 projection from native PDF geometry, without inference.

The legacy graph, generated anatomy summaries and table exports are not inputs.
No source labels or process/code pairs are embedded in this implementation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from copy import deepcopy
import math
from dataclasses import replace

from src.evidence_sources import _make, _section_note, _source
from src.evidence_a1_registry import a1_registry_binding
from src.standard_manifest import extract_reference_records

ELEMENT = "Figure A1"
RECORD_EVIDENCE_SCHEMA = "a1-record-evidence-1.0"


def _require(ok, code):
    if not ok:
        raise ValueError("A1_" + code)


def _graph_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _native_graph(graph):
    """Remove only this module's additive provenance, preserving native facts."""
    raw = deepcopy(graph)
    for key in ("source_binding", "record_evidence_schema_version", "native_graph_sha256"):
        raw.pop(key, None)
    for node in raw["nodes"]:
        node.pop("evidence", None)
    for edge in raw["edges"]:
        edge.pop("id", None)
        edge.pop("evidence", None)
    return raw


def _record_region(record):
    region = record.get("region")
    _require(isinstance(region, list) and len(region) == 4 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        for v in region), "RECORD_REGION_INVALID")
    ymin, xmin, ymax, xmax = region
    _require(0 <= ymin < ymax <= 1 and 0 <= xmin < xmax <= 1, "RECORD_REGION_INVALID")
    return region


def _validate_chart_source_binding(binding):
    _require(isinstance(binding, dict) and set(binding) == {
        "edition_id", "source_identity_id", "locator", "asset_sha256"}, "RECORD_SOURCE_INVALID")
    _require(all(isinstance(binding[k], str) and binding[k] for k in
        ("edition_id", "source_identity_id")), "RECORD_SOURCE_INVALID")
    _require(isinstance(binding["asset_sha256"], str) and re.fullmatch(
        r"[0-9a-f]{64}", binding["asset_sha256"]), "RECORD_ASSET_INVALID")
    locator = binding["locator"]
    profiles = {"Figure A1": "figure:figure_a1", "Figure A2": "figure:figure_a2"}
    _require(isinstance(locator, dict) and locator.get("element_id") in profiles
        and locator.get("canonical_element_id") == profiles[locator["element_id"]]
        and locator.get("source_identity_id") == binding["source_identity_id"]
        and isinstance(locator.get("pdf_index"), int) and not isinstance(locator["pdf_index"], bool)
        and locator["pdf_index"] >= 0 and bool(str(locator.get("printed_page", "")))
        and locator.get("order") == 0, "RECORD_LOCATOR_INVALID")
    if locator["element_id"] == ELEMENT:
        _require(locator.get("region_scope") == "full_page" and locator.get("region") is None,
                 "RECORD_LOCATOR_INVALID")
    else:
        _require(locator.get("region_scope") == "figure_region", "RECORD_LOCATOR_INVALID")
        _record_region(locator)


def _validate_source_binding(binding):
    """Keep the established A1-only interface strict."""
    _validate_chart_source_binding(binding)
    _require(binding["locator"]["element_id"] == ELEMENT, "RECORD_LOCATOR_INVALID")


def _extraction_provenance(graph, binding, record=None):
    """Validate declared raster lineage; it does not verify extracted facts."""
    override = record is not None and "extraction_provenance" in record
    if "extraction_provenance" not in graph:
        _require(not override, "RECORD_EXTRACTION_REQUIRES_GRAPH_PROVENANCE")
        return None
    default = _extraction_provenance(graph, binding) if override else None
    provenance = record["extraction_provenance"] if override else graph["extraction_provenance"]
    _require(isinstance(provenance, dict) and set(provenance) == {
        "method", "engine", "version", "input_asset_sha256", "uncertainty", "parent_source"},
        "EXTRACTION_PROVENANCE_INVALID")
    _require(provenance["method"] in {"ocr", "vision"}
        and all(isinstance(provenance[key], str) and provenance[key].strip() for key in ("engine", "version"))
        and provenance["input_asset_sha256"] == binding["asset_sha256"]
        and provenance["uncertainty"] == "unreviewed_model_observation", "EXTRACTION_PROVENANCE_INVALID")
    parent = provenance["parent_source"]
    _validate_chart_source_binding(parent)
    _require(parent["edition_id"] == binding["edition_id"] and all(
        parent["locator"][key] == binding["locator"][key] for key in
        ("element_id", "canonical_element_id", "pdf_index", "printed_page", "order", "region", "region_scope")),
        "EXTRACTION_PARENT_SCOPE_MISMATCH")
    if override:
        _require(parent == default["parent_source"], "EXTRACTION_PARENT_SCOPE_MISMATCH")
    return provenance


def _record_proof(record, kind, graph, binding, native_hash):
    region = _record_region(record)
    crop = binding["locator"].get("region")
    if crop is not None:
        _require(crop[0] <= region[0] < region[2] <= crop[2]
                 and crop[1] <= region[1] < region[3] <= crop[3], "RECORD_OUTSIDE_FIGURE_REGION")
    if kind == "edge":
        qualification = graph["edge_qualifications"].get(record.get("type"))
        _require(isinstance(qualification, dict) and qualification.get("verification") in
            {"source_bound", "candidate"} and bool(qualification.get("qualification")),
            "RECORD_RELATION_UNQUALIFIED")
        _require(record.get("type") != "INDENTED_UNDER" or
            qualification["verification"] == "candidate", "INDENTATION_MUST_REMAIN_CANDIDATE")
        record_id = "a1edge:" + _graph_digest([binding, native_hash, record])
    else:
        _require(isinstance(record.get("id"), str) and bool(record["id"]), "RECORD_ID_INVALID")
        record_id = record["id"]
        qualification = {"verification": "source_bound", "qualification":
            "Literal native chart label/acronym and geometry; not reviewed semantic entailment."}
    provenance = _extraction_provenance(graph, binding, record)
    if provenance is not None:
        qualification = {"verification": "candidate", "qualification":
            "Unreviewed " + provenance["method"] + " extraction from the bound image; neither literal accuracy nor semantic relations are admitted."}
    locator = dict(binding["locator"], region=region, region_scope="record_region",
        region_space=graph["region_space"])
    proof = {"record_id": record_id, "record_kind": kind, **deepcopy(binding),
        "locator": locator, "native_graph_sha256": native_hash, **qualification}
    if provenance is not None:
        proof["extraction_provenance"] = deepcopy(provenance)
    proof["evidence_id"] = "record2:" + _graph_digest([proof, record])
    return record_id, proof


def bind_chart_graph_evidence(graph, edition_id, source_identity_id, locator, asset_sha256):
    """Bind immutable native records to a declared source, without authenticating it.

    The canonical loader authenticates PDF/manifest/image bytes separately. These
    hashes detect inconsistent records; caller-declared metadata is not proof
    that a supplied graph came from that source.
    """
    _require(not any(k in graph for k in ("selection", "source_binding")), "FULL_NATIVE_GRAPH_REQUIRED")
    _require(graph.get("schema_version") == "a1-geometry-1.0" and
        graph.get("region_space") == "normalized_pdf_page_ymin_xmin_ymax_xmax", "GRAPH_SCHEMA_INVALID")
    binding = deepcopy(dict(edition_id=edition_id, source_identity_id=source_identity_id,
        locator=locator, asset_sha256=asset_sha256))
    _validate_chart_source_binding(binding)
    provenance = _extraction_provenance(graph, binding)
    bound = deepcopy(graph)
    if provenance is not None:
        for qualification in bound["edge_qualifications"].values():
            qualification.update(verification="candidate", qualification=
                "Unreviewed " + provenance["method"] + " chart-layout extraction; no verified source relation or semantic subtype is established.")
    native_hash = _graph_digest(bound)
    bound.update(source_binding=binding, record_evidence_schema_version=RECORD_EVIDENCE_SCHEMA,
        native_graph_sha256=native_hash)
    identifiers = {n["id"] for n in bound["nodes"]}
    _require(len(identifiers) == len(bound["nodes"]) and bound["root_id"] in identifiers,
        "GRAPH_IDENTITY_INVALID")
    for node in bound["nodes"]:
        _, node["evidence"] = _record_proof(node, "node", bound, binding, native_hash)
    for edge in bound["edges"]:
        _require(edge["from"] in identifiers and edge["to"] in identifiers, "GRAPH_ENDPOINT_MISSING")
        identifier, proof = _record_proof(edge, "edge", bound, binding, native_hash)
        edge.update(id=identifier, evidence=proof)
    validate_chart_graph_evidence(bound)
    return bound


def validate_chart_graph_evidence(graph, expected_source=None, require_complete=True):
    """Check record consistency and declared source scope, not caller authenticity."""
    _require(graph.get("record_evidence_schema_version") == RECORD_EVIDENCE_SCHEMA,
        "RECORD_EVIDENCE_SCHEMA_INVALID")
    binding = graph.get("source_binding")
    _validate_chart_source_binding(binding)
    if expected_source is not None:
        _require(binding == expected_source, "RECORD_SOURCE_MISMATCH")
    native_hash = graph.get("native_graph_sha256")
    _require(isinstance(native_hash, str) and re.fullmatch(r"[0-9a-f]{64}", native_hash),
        "NATIVE_GRAPH_HASH_INVALID")
    raw = _native_graph(graph)
    if require_complete:
        _require("selection" not in graph and _graph_digest(raw) == native_hash,
            "NATIVE_GRAPH_INCOMPLETE_OR_CHANGED")
    identifiers = {n["id"] for n in raw["nodes"]}
    _require(len(identifiers) == len(raw["nodes"]) and raw["root_id"] in identifiers,
        "GRAPH_IDENTITY_INVALID")
    evidence_ids = set()
    for kind, records, originals in (("node", graph["nodes"], raw["nodes"]),
                                      ("edge", graph["edges"], raw["edges"])):
        for record, original in zip(records, originals):
            if kind == "edge":
                _require(original["from"] in identifiers and original["to"] in identifiers,
                    "GRAPH_ENDPOINT_MISSING")
            identifier, proof = _record_proof(original, kind, raw, binding, native_hash)
            _require(record.get("evidence") == proof and (kind != "edge" or
                record.get("id") == identifier), "RECORD_EVIDENCE_MISMATCH")
            _require(proof["evidence_id"] not in evidence_ids, "RECORD_EVIDENCE_COLLISION")
            evidence_ids.add(proof["evidence_id"])
    return {"status": "source_binding_validated", "native_graph_sha256": native_hash,
        "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
        "record_evidence_count": len(evidence_ids),
        "qualification": "Declared record consistency only; source authenticity requires canonical loader and asset verification."}


def bind_a1_graph_evidence(graph, edition_id, source_identity_id, locator, asset_sha256):
    """A1-compatible binding; other figure adapters use the explicit chart API."""
    bound = bind_chart_graph_evidence(graph, edition_id, source_identity_id, locator, asset_sha256)
    _validate_source_binding(bound["source_binding"])
    return bound


def validate_a1_graph_evidence(graph, expected_source=None, require_complete=True):
    """Preserve the original A1-only validation boundary."""
    receipt = validate_chart_graph_evidence(graph, expected_source, require_complete)
    _validate_source_binding(graph["source_binding"])
    return receipt


def _bbox(value):
    return tuple(float(v) for v in value)


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _contains(outer, inner, tolerance=0.75):
    return (outer[0]-tolerance <= inner[0] and outer[1]-tolerance <= inner[1]
            and inner[2] <= outer[2]+tolerance and inner[3] <= outer[3]+tolerance)


def _intersects(segment, box, tolerance=0.75):
    """Liang-Barsky segment/rectangle intersection, including hidden endpoints."""
    (x0, y0), (x1, y1) = segment
    xmin, ymin, xmax, ymax = box
    xmin, ymin, xmax, ymax = xmin-tolerance, ymin-tolerance, xmax+tolerance, ymax+tolerance
    dx, dy = x1-x0, y1-y0
    lo, hi = 0.0, 1.0
    for p, q in [(-dx, x0-xmin), (dx, xmax-x0), (-dy, y0-ymin), (dy, ymax-y0)]:
        if p == 0:
            if q < 0:
                return False
        else:
            ratio = q / p
            if p < 0:
                lo = max(lo, ratio)
            else:
                hi = min(hi, ratio)
            if lo > hi:
                return False
    return True


def extract_a1_chart(page, edition_id, *, element_id=ELEMENT):
    """Return a compact source geometry graph; ambiguous text/edges fail closed.

    Chart containment and physical connector adjacency are source-bound. An
    indentation parent is deliberately qualified as a layout candidate rather
    than an asserted semantic subtype. No graph edge certifies entailment.
    """
    _require(element_id == ELEMENT, "FIGURE_IDENTITY_REQUIRED")
    width, height = float(page.rect.width), float(page.rect.height)
    _require(width > 0 and height > 0, "PAGE_GEOMETRY_INVALID")

    def region(box):
        x0, y0, x1, y1 = box
        _require(0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height, "REGION_INVALID")
        return [round(y0/height, 6), round(x0/width, 6), round(y1/height, 6), round(x1/width, 6)]

    def identifier(kind, text, box, code=""):
        bound = [edition_id, element_id, kind, text, code, region(box)]
        return "a1:" + hashlib.sha256(json.dumps(bound, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()[:20]

    boxes, segments = [], []
    for drawing in page.get_drawings():
        if drawing["type"] != "s":
            continue
        for item in drawing["items"]:
            if item[0] == "re":
                box = _bbox(item[1])
                if box[2]-box[0] > 30 and box[3]-box[1] > 30:
                    _require(not any(_contains(b, box, 0.1) and _contains(box, b, 0.1) for b in boxes), "DUPLICATE_BOX")
                    boxes.append(box)
            elif item[0] == "l":
                segment = (tuple(map(float, item[1])), tuple(map(float, item[2])))
                if sum((a-b)**2 for a,b in zip(*segment)) > 20**2:
                    segments.append(segment)
    _require(len(boxes) == 9, "EXPECTED_ROOT_AND_EIGHT_BOXES")
    boxes.sort(key=lambda b: (b[1], b[0]))
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            text = "".join(s["text"] for s in spans).strip()
            if text:
                lines.append({"text": text, "box": _bbox(line["bbox"]),
                              "bold": all(s.get("flags", 0) & 16 for s in spans)})
    groups = []
    for box in boxes:
        members = [line for line in lines if _contains(box, line["box"])]
        _require(members, "BOX_WITHOUT_TEXT")
        groups.append((box, members))
    roots = [(b, members) for b, members in groups if len(members) > 1 and all(l["bold"] for l in members)]
    _require(len(roots) == 1, "ROOT_AMBIGUOUS")
    root_box, root_lines = roots[0]
    root_label = " ".join(l["text"] for l in sorted(root_lines, key=lambda l: l["box"][1]))
    root_id = identifier("root", root_label, root_box)
    nodes = [{"id": root_id, "kind": "root", "label": root_label, "region": region(root_box)}]
    edges, native_lines = [], []
    category_ids = {}
    for box, members in groups:
        if box == root_box:
            native_lines.extend(root_lines)
            continue
        headings = [l for l in members if l["bold"]]
        _require(len(headings) == 1, "CATEGORY_HEADING_AMBIGUOUS")
        heading = headings[0]
        _require(heading["text"] == heading["text"].upper(), "CATEGORY_CASE_AMBIGUOUS")
        category_id = identifier("category", heading["text"], box)
        category_ids[box] = category_id
        nodes.append({"id": category_id, "kind": "category", "label": heading["text"], "region": region(box)})
        body = [l for l in members if l is not heading]
        _require(body and all(l["box"][1] > heading["box"][1] for l in body), "CATEGORY_BODY_AMBIGUOUS")
        rows = []
        for line in sorted(body, key=lambda l: (l["box"][1], l["box"][0])):
            matches = [row for row in rows if abs(row[0]["box"][1] - line["box"][1]) <= 0.75]
            _require(len(matches) <= 1, "ROW_GEOMETRY_AMBIGUOUS")
            if matches:
                matches[0].append(line)
            else:
                rows.append([line])
        codes_x, pairs = [], []
        for row in rows:
            row.sort(key=lambda l: l["box"][0])
            codes = [l for l in row if re.fullmatch(r"[A-Z]+(?:-[A-Z]+)?", l["text"])]
            _require(len(codes) == 1, "ROW_CODE_AMBIGUOUS")
            code = codes[0]
            words = [l for l in row if l is not code]
            _require(words and all(l["box"][2] < code["box"][0] for l in words), "ROW_PAIRING_AMBIGUOUS")
            _require(all(b["box"][0]-a["box"][2] < 16 for a,b in zip(words, words[1:])), "SPLIT_LABEL_AMBIGUOUS")
            label = " ".join(l["text"] for l in words)
            label_box, row_box = _union([l["box"] for l in words]), _union([l["box"] for l in row])
            pair_id = identifier("process", label, row_box, code["text"])
            nodes.append({"id": pair_id, "kind": "process", "label": label, "code": code["text"], "region": region(row_box)})
            edges.append({"from": category_id, "to": pair_id, "type": "ENCLOSES_ROW", "region": region(row_box)})
            codes_x.append(code["box"][0])
            pairs.append((pair_id, label_box, row_box))
        _require(max(codes_x)-min(codes_x) <= 1.5, "CODE_COLUMN_AMBIGUOUS")
        left = min(b[0] for _,b,_ in pairs)
        parents = []
        for pair_id, label_box, row_box in pairs:
            indent = label_box[0]-left
            # Source A1 has at most one indentation level. Do not generalize
            # unfamiliar geometry into arbitrary semantic trees.
            _require(indent < 1.5 or 6 <= indent <= 14, "INDENTATION_AMBIGUOUS")
            if indent < 1.5:
                parents = [(pair_id, row_box)]
            else:
                _require(parents, "INDENT_WITHOUT_PARENT")
                edges.append({"from": parents[-1][0], "to": pair_id,
                              "type": "INDENTED_UNDER", "region": region(_union([parents[-1][1], row_box]))})
        native_lines.extend(members)
    # Lines are drawn behind white category/root boxes. A single horizontal
    # segment can cross the root and connect two different category boxes.
    seen = set()
    for segment in segments:
        if not _intersects(segment, root_box):
            continue
        touched = [box for box in category_ids if _intersects(segment, box)]
        _require(1 <= len(touched) <= 2, "CONNECTOR_TOPOLOGY_AMBIGUOUS")
        for box in touched:
            target = category_ids[box]
            _require(target not in seen, "DUPLICATE_CONNECTOR")
            seen.add(target)
            # Retain the complete physical line's region; orientation here is
            # organizational root/category identity, not a printed arrow.
            x0, y0 = segment[0]
            x1, y1 = segment[1]
            line_box = (max(0,min(x0,x1)-0.25), max(0,min(y0,y1)-0.25),
                        min(width,max(x0,x1)+0.25), min(height,max(y0,y1)+0.25))
            edges.append({"from": root_id, "to": target, "type": "CHART_CONNECTOR", "region": region(line_box)})
    _require(len(seen) == 8 and seen == set(category_ids.values()), "CONNECTOR_COVERAGE_INCOMPLETE")
    _require(len({n["id"] for n in nodes}) == len(nodes), "NODE_ID_COLLISION")
    native_text = "\n".join(l["text"] for l in sorted(native_lines, key=lambda l: (l["box"][1],l["box"][0])))
    return {"schema_version": "a1-geometry-1.0", "root_id": root_id, "nodes": nodes, "edges": edges,
            "edge_qualifications": {
                "ENCLOSES_ROW": {"verification": "source_bound", "qualification": "Native label/code aligned on one row enclosed by this category rectangle; not a reviewed semantic subtype."},
                "CHART_CONNECTOR": {"verification": "source_bound", "qualification": "Native vector line intersects root and category boxes. Undirected physical chart adjacency; no arrow direction is asserted."},
                "INDENTED_UNDER": {"verification": "candidate", "qualification": "Nearest preceding unindented row from source layout only; semantic parentage requires separate review."}},
            "region_space": "normalized_pdf_page_ymin_xmin_ymax_xmax",
            "native_text": native_text,
            "limits": ["One image and native page only; no other A1/Table/Annex content merged.",
                       "Rows and physical topology are source-bound extraction, not semantic/model validation.",
                       "Indentation preserves layout and does not certify a normative IS_A relationship.",
                       "Header, caption, page number and account footer are excluded from chart nodes/text."]}


def retrieve_a1_graph(graph, query):
    """Literal selection plus actual complete ancestor traversal, without top-k.

    All category boxes and their root connectors stay visible as chart context.
    Exact named/code rows seed traversal. Every enclosure or indentation parent
    is retained, including multiple candidate parents; no semantic choice is
    guessed. The original image remains outside this derived text projection.
    """
    _require(isinstance(query, str) and bool(query.strip()) and len(query) <= 16384,
             "QUERY_INVALID")
    query = " ".join(query.split())
    by_id = {n["id"]: n for n in graph["nodes"]}
    _require(len(by_id) == len(graph["nodes"]) and graph["root_id"] in by_id,
             "GRAPH_IDENTITY_INVALID")
    parents = {}
    for edge in graph["edges"]:
        _require(edge["from"] in by_id and edge["to"] in by_id, "GRAPH_ENDPOINT_MISSING")
        _require(edge["type"] in graph["edge_qualifications"], "GRAPH_RELATION_UNQUALIFIED")
        parents.setdefault(edge["to"], set()).add(edge["from"])
    names, selected = [], set()
    for node in graph["nodes"]:
        if node["kind"] != "process":
            selected.add(node["id"])
            continue
        pattern = r"(?<!\w)" + re.escape(node["label"]) + r"(?!\w)"
        names.extend((m.start(), m.end(), node["id"]) for m in re.finditer(pattern, query, re.IGNORECASE))
    seeds = {identifier for start,end,identifier in names if not any(
        other_start <= start and end <= other_end and other_end-other_start > end-start
        for other_start,other_end,_ in names)}
    for node in graph["nodes"]:
        if node["kind"] == "process" and re.search(
                r"(?<![\w-])" + re.escape(node["code"]) + r"(?![\w-])", query):
            seeds.add(node["id"])
    pending, ancestors = list(seeds), set()
    while pending:
        current = pending.pop()
        if current in ancestors:
            continue
        ancestors.add(current)
        pending.extend(parents.get(current, set()) - ancestors)
    selected.update(ancestors)
    nodes = [n for n in graph["nodes"] if n["id"] in selected]
    edges = [e for e in graph["edges"] if e["from"] in selected and e["to"] in selected]
    source_hash = hashlib.sha256(json.dumps(graph, ensure_ascii=False, sort_keys=True,
                                           allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    return {**graph, "schema_version": graph["schema_version"], "root_id": graph["root_id"],
            "nodes": nodes, "edges": edges, "edge_qualifications": graph["edge_qualifications"],
            "region_space": graph["region_space"],
            "native_text": "\n".join(n["label"] + (" " + n["code"] if "code" in n else "") for n in nodes),
            "full_source_graph_sha256": source_hash,
            "full_source_graph_counts": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])},
            "selection": {"method": "literal_full_name_or_case_sensitive_code_then_all_inbound_ancestor_closure",
                          "seed_ids": sorted(seeds), "ancestor_ids": sorted(ancestors - seeds),
                          "status": "literal_process_match" if seeds else "category_context_only",
                          "qualifications": ["No inferred relevance or top-k truncation.",
                                             "All candidate parents are traversed; no ambiguous semantic parent is chosen.",
                                             "No literal process selector means category context only, not recovery of an unnamed requested process.",
                                             "The complete original source image remains required."]},
            "limits": graph["limits"]}


def scope_query_diagnostics(query, manifest, anchor):
    """Validate every source/page mention against the single selected image.

    Canonical reference records resolve elements, ranges and printed pages.
    This helper only pluralizes a singular figure introducer when a bare-ID
    list follows, so ``Figure A1 and B6`` cannot hide its second element. This
    local lexer text never changes a user's query or the v1 reference grammar.
    Explicit PDF pages use ordinals; unqualified page labels remain printed.
    """
    diagnostics = []
    lexical = re.sub(
        r"\b(Figure|Fig\.?)\s+(?=[A-Za-z]\.?\d+(?:\([^\n;]*?\))?\s*(?:,\s*(?:and\s+)?|and\s+)[A-Za-z]?\.?\d)",
        "Figures ", str(query), flags=re.IGNORECASE)
    # Ordinal is a typed PDF-page spelling, never a printed-page offset guess.
    lexical = re.sub(r"\bPDF\s+(?:page\s+)?ordinal\s+", "PDF page ", lexical, flags=re.IGNORECASE)
    records = extract_reference_records(lexical, manifest=manifest)
    for record in records:
        resolution = record["resolution"]
        if record["kind"] != "page":
            if resolution["status"] != "exact":
                diagnostics.append("a1_reference_" + resolution["status"] + ":" + record["raw"])
            if any(label not in {ELEMENT, "Annex A"} for label in resolution.get("labels", [])):
                diagnostics.append("a1_external_reference:" + record["raw"])
        page_text = record.get("qualifiers", {}).get("page")
        if not page_text:
            continue
        if re.match(r"\s*(?:,\s*(?:and\s+)?|and\s+)\d", lexical[record["end"]:], re.IGNORECASE):
            diagnostics.append("a1_page_list_unsupported:" + page_text)
        explicit_pdf = (record["kind"] == "page" and re.search(
            r"\bPDF\s*$", lexical[:record["start"]], re.IGNORECASE) is not None)
        candidates = record.get("page_candidates", [])
        if explicit_pdf:
            value = record["requested_label"].removeprefix("Page ").strip()
            match = re.fullmatch(r"(\d+)(?:\s*[-\u2013\u2014]\s*(\d+))?", value)
            candidates = []
            page_count = len(manifest.document["pages"])
            if match and max(len(v) for v in match.groups() if v) <= len(str(page_count)):
                first, last = int(match[1]), int(match[2] or match[1])
                if 1 <= first <= last <= page_count:
                    candidates = [{"pdf_index": ordinal-1} for ordinal in range(first, last+1)]
        if not candidates:
            diagnostics.append("a1_page_unresolved:" + ("PDF " if explicit_pdf else "printed ") + page_text)
        elif any(candidate["pdf_index"] != anchor["pdf_index"] for candidate in candidates):
            diagnostics.append("a1_page_outside_selected_image:" + ("PDF " if explicit_pdf else "printed ") + page_text)
    return list(dict.fromkeys(diagnostics))


def a1_source_identity_id(edition_id, canonical_element_id, anchor, asset_sha256):
    """Stable source identity; independent of query, selected graph and view ID."""
    locus = {key: anchor[key] for key in ("pdf_index", "printed_label", "order", "role", "region")}
    raw = json.dumps([edition_id, canonical_element_id, locus, asset_sha256],
                     ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))
    return "source2:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_a1_evidence(root: Path, query=None):
    """Return only canonical Figure A1's original image and required Annex A note."""
    import fitz
    root = Path(root)
    manifest, edition, pdf_path = _source(root)
    record = manifest.element(ELEMENT)
    _require(record and record["id"] == "figure:figure_a1" and record["label"] == ELEMENT
             and record["parent_id"] == "clause:annex_a", "MANIFEST_IDENTITY_INVALID")
    alternative = manifest.element("Table A1")
    _require(alternative and alternative["id"] == "table:table_a1"
             and alternative["label"] == "Table A1", "A1_ALTERNATIVE_IDENTITY_INVALID")
    anchors = record["anchors"]
    _require(len(anchors) == 1 and anchors[0]["order"] == 0 and anchors[0]["role"] == "start", "ONE_SOURCE_PAGE_REQUIRED")
    anchor = anchors[0]
    assets = [a for a in record["assets"] if a["source_anchor_orders"] == [0]
              and a["relpath"].lower().endswith(".png")]
    _require(len(assets) == 1 and len(record["assets"]) == 1, "ONE_ORIGINAL_IMAGE_REQUIRED")
    asset = assets[0]
    # Reuse the canonical per-asset integrity/containment checks; never resolve
    # an old graph filename or infer the PDF page from the image filename.
    checked = manifest.validated_assets(ELEMENT, {".png"})
    _require(len(checked) == 1 and checked[0]["status"] == "complete", "SOURCE_IMAGE_INVALID")
    _require(asset["verification"]["state"] == "verified" and anchor["verification"]["state"] == "verified", "SOURCE_BINDING_UNVERIFIED")
    with fitz.open(pdf_path) as pdf:
        page = pdf[anchor["pdf_index"]]
        graph = extract_a1_chart(page, edition)
        # The canonical source caption must be on the same selected native page.
        _require(re.search(r"\bFigure\s+A1\b", page.get_text()) is not None, "NATIVE_CAPTION_MISSING")
    note = _section_note(manifest, edition, "Annex A")
    source_identity = a1_source_identity_id(edition, record["id"], anchor, asset["sha256"])
    locator = {"element_id": ELEMENT, "canonical_element_id": record["id"],
               "source_identity_id": source_identity, "pdf_index": anchor["pdf_index"],
               "printed_page": anchor["printed_label"], "order": 0,
               "region": anchor["region"], "region_scope": "full_page"}
    graph = bind_a1_graph_evidence(graph, edition, source_identity, locator, asset["sha256"])
    if query is not None:
        graph = retrieve_a1_graph(graph, query)
    content = {"caption": record["title"], "asset_relpath": asset["relpath"],
               "source_identity_id": source_identity,
               "asset_sha256": asset["sha256"], "media_type": "image/png",
               "single_image_scope": True, "identity_alternatives": [ELEMENT, "Table A1"],
               "continuation_orders": [0], "required_evidence_ids": [note.evidence_id],
               "chart_graph": graph, "qualifiers": ["Single full page; no certified semantic subregion."],
               "exceptions": [], "notes": []}
    if query is not None:
        content["scope_query_diagnostics"] = scope_query_diagnostics(query, manifest, anchor)
    figure = _make(edition, "figure_region", locator, content, required_ids=(note.evidence_id,))
    binding = a1_registry_binding(root)
    figure = replace(figure, relationships=({
        "predicate": "CANDIDATE_REGISTRY", "target_id": binding["canonical_manifest_element_id"],
        "qualification": binding["qualification"], "verification": "candidate"},))
    return [note, figure]
