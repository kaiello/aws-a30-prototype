"""Scoped, replayable raster admission evidence; no OCR, model or answer input.

This verifies retained observations against their consumed pixels. Recognition
confidence is evidence, not mathematical certainty. Low-confidence/corrected
codes need independent same-image glyph corroboration; dictionary agreement is
never sufficient. Printed enclosure/connection is not semantic subtype.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import cv2
import numpy as np

VERSION = "a1-raster-record-verification-1.0"
MIN_LITERAL_CONFIDENCE = 90.0
MIN_GLYPH_IOU = .80
MIN_GLYPH_MARGIN = .05


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def relation_key(source, target, kind):
    return json.dumps([source, target, kind], separators=(",", ":"))


def _tokens(value):
    return re.findall(r"[a-z0-9]+", str(value).casefold())


def _contains(outer, inner, margin=2):
    x, y, w, h = outer
    a, b, c, d = inner
    return x-margin <= a and y-margin <= b and a+c <= x+w+margin and b+d <= y+h+margin


def _crop(ink, box):
    x, y, w, h = box
    if (any(type(v) is not int for v in box) or x < 0 or y < 0 or w <= 0 or h <= 0
            or y+h > ink.shape[0] or x+w > ink.shape[1]):
        raise ValueError("RASTER_VERIFICATION_ANCHOR_INVALID")
    return ink[y:y+h, x:x+w]


def _ink_word(ink, word):
    crop = _crop(ink, word["pixel_bbox"])
    density = float(crop.mean())
    return bool(str(word.get("text", "")).strip()) and .01 <= density <= .95


def _runs(mask):
    ids = np.flatnonzero(mask)
    if not len(ids):
        return []
    cuts = np.flatnonzero(np.diff(ids) > 1)
    return [(int(a), int(b)+1) for a, b in zip(np.r_[ids[0], ids[cuts+1]], np.r_[ids[cuts], ids[-1]])]


def _glyphs(ink, word):
    crop = _crop(ink, word["pixel_bbox"])
    result = []
    for first, last in _runs(crop.any(axis=0)):
        rows = np.flatnonzero(crop[:, first:last].any(axis=1))
        if not len(rows):
            continue
        top, bottom = int(rows[0]), int(rows[-1])+1
        glyph = crop[top:bottom, first:last]
        scale = 28 / max(glyph.shape)
        sized = cv2.resize(glyph.astype("uint8"),
            (max(1, round(glyph.shape[1]*scale)), max(1, round(glyph.shape[0]*scale))),
            interpolation=cv2.INTER_NEAREST).astype(bool)
        normalized = np.zeros((32, 32), dtype=bool)
        y, x = (32-sized.shape[0])//2, (32-sized.shape[1])//2
        normalized[y:y+sized.shape[0], x:x+sized.shape[1]] = sized
        bx, by, _, _ = word["pixel_bbox"]
        result.append((normalized, [bx+first, by+top, last-first, bottom-top]))
    return result


def _word_rows(node, observations):
    rows = [observations[item] for item in node.get("observation_ids", [])
            if item in observations and observations[item]["kind"] == "ocr_row"]
    rows.sort(key=lambda item: (item["pixel_bbox"][1], item["pixel_bbox"][0]))
    words = []
    for row in rows:
        ids = row.get("word_observation_ids", [])
        if not ids or any(identifier not in observations or observations[identifier]["kind"] != "ocr_word" for identifier in ids):
            raise ValueError("RASTER_VERIFICATION_WORD_PROOF_MISSING")
        ordered = sorted((observations[identifier] for identifier in ids), key=lambda item: item["pixel_bbox"][0])
        if " ".join(item["text"] for item in ordered) != row["text"]:
            raise ValueError("RASTER_VERIFICATION_WORD_TEXT_MISMATCH")
        words.extend(ordered)
    return rows, words


def _glyph_bank(ink, graph, observations):
    bank = {}
    for node in graph["nodes"]:
        if node["kind"] != "process":
            continue
        rows, words = _word_rows(node, observations)
        if len(rows) != 1 or len(words) < 2:
            continue
        word = words[-1]
        raw = word["text"]
        if (float(word["confidence"]) < MIN_LITERAL_CONFIDENCE or raw != node.get("code")
                or node.get("normalization", {}).get("method") == "exact_name_single_code_edit"
                or node.get("normalization", {}).get("status") == "ambiguous"
                or not re.fullmatch(r"[A-Z][A-Z0-9-]*", raw) or not _ink_word(ink, word)):
            continue
        glyphs = _glyphs(ink, word)
        if len(glyphs) != len(raw):
            continue  # No speculative split of touching glyphs.
        for index, (letter, (mask, box)) in enumerate(zip(raw, glyphs)):
            bank.setdefault(letter, []).append((mask, word["id"], index, box))
    return bank


def _glyph_corrob(ink, word, expected, bank):
    glyphs = _glyphs(ink, word)
    if len(glyphs) != len(expected):
        return False, {"reason": "glyph_segmentation_ambiguous", "segments": len(glyphs)}
    evidence, recognized = [], []
    for mask, box in glyphs:
        scores = []
        for letter, samples in bank.items():
            choices = []
            for template, word_id, index, template_box in samples:
                if word_id == word["id"]:
                    continue
                union = int(np.logical_or(mask, template).sum())
                iou = float(np.logical_and(mask, template).sum()) / union if union else 0.0
                choices.append((iou, word_id, index, template_box))
            if choices:
                score, source_word, index, source_box = max(choices, key=lambda item: item[0])
                scores.append((score, letter, source_word, index, source_box))
        scores.sort(reverse=True)
        if not scores:
            return False, {"reason": "source_glyph_template_missing"}
        best = scores[0]
        runner = scores[1][0] if len(scores) > 1 else 0.0
        evidence.append({"recognized": best[1], "pixel_bbox": box,
            "template_word_id": best[2], "template_character_index": best[3], "template_pixel_bbox": best[4],
            "iou": round(best[0], 8), "next_class_iou": round(runner, 8)})
        if best[0] < MIN_GLYPH_IOU or best[0]-runner < MIN_GLYPH_MARGIN:
            return False, {"reason": "glyph_match_uncertain", "glyphs": evidence}
        recognized.append(best[1])
    text = "".join(recognized)
    return text == expected, {"reason": "source_local_glyph_correspondence" if text == expected else "glyph_sequence_conflict",
                              "recognized_code": text, "glyphs": evidence}


def _border_support(ink, box):
    x, y, w, h = box
    radius = 6  # Includes the earlier small contour tolerance without filling ink.
    height, width = ink.shape
    spans = [ink[max(0, y-radius):min(height, y+radius+1), x:x+w].any(axis=0),
             ink[max(0, y+h-1-radius):min(height, y+h+radius), x:x+w].any(axis=0),
             ink[y:y+h, max(0, x-radius):min(width, x+radius+1)].any(axis=1),
             ink[y:y+h, max(0, x+w-1-radius):min(width, x+w+radius)].any(axis=1)]
    values = [round(float(span.mean()), 8) for span in spans]
    return all(value >= .95 for value in values), dict(zip(("top", "bottom", "left", "right"), values))


def _row_bands(ink, box, rows):
    x, y, w, h = box
    margin = 10
    inner = ink[y+margin:y+h-margin, x+margin:x+w-margin]
    bands = _runs(inner.sum(axis=1) >= max(3, inner.shape[1]*.003))
    missing = []
    for first, last in bands:
        first, last = first+y+margin, last+y+margin
        if not any(first < row["pixel_bbox"][1]+row["pixel_bbox"][3]+5
                   and row["pixel_bbox"][1]-5 < last for row in rows):
            missing.append([first, last])
    return missing


def _unexplained_ink(ink, box, rows, observations, header_ids):
    """Catch unrecognized text within the detected box, not page captions/footer."""
    x, y, w, h = box
    residual = ink[y:y+h, x:x+w].copy().astype("uint8")
    residual[:10] = residual[-10:] = 0
    residual[:, :10] = residual[:, -10:] = 0
    for row in rows:
        anchors = ([row["pixel_bbox"]] if row["id"] in header_ids else
                   [observations[item]["pixel_bbox"] for item in row["word_observation_ids"]])
        for a, b, c, d in anchors:
            pad = 6 if row["id"] in header_ids else 2
            residual[max(0, b-y-pad):min(h, b-y+d+pad), max(0, a-x-pad):min(w, a-x+c+pad)] = 0
    count, _, stats, _ = cv2.connectedComponentsWithStats(residual, 8)
    return [[int(item[0]+x), int(item[1]+y), int(item[2]), int(item[3]), int(item[4])]
            for item in stats[1:count] if item[4] >= 4]


def _chart_closure(ink, boxes, observations, node_rows, node_rectangles, connectors):
    if not boxes:
        return {"complete": False, "reason": "no_chart_rectangle_envelope"}
    x = min(box[0] for box in boxes); y = min(box[1] for box in boxes)
    right = max(box[0]+box[2] for box in boxes); bottom = max(box[1]+box[3] for box in boxes)
    row_ids = {row["id"] for rows in node_rows.values() for row in rows}
    word_ids = [item for row_id in row_ids for item in observations[row_id]["word_observation_ids"]]
    word_counts = {identifier: word_ids.count(identifier) for identifier in set(word_ids)}
    orphans = [item["id"] for item in observations.values() if item["kind"] == "ocr_word"
               and _contains([x, y, right-x, bottom-y], item["pixel_bbox"])
               and word_counts.get(item["id"]) != 1]
    residual = ink.astype("uint8").copy()
    for identifier in word_counts:
        a, b, c, d = observations[identifier]["pixel_bbox"]
        residual[max(0, b-2):b+d+2, max(0, a-2):a+c+2] = 0
    for rectangle in node_rectangles.values():
        a, b, c, d = rectangle["pixel_bbox"]
        cv2.rectangle(residual, (a, b), (a+c-1, b+d-1), 0, 14)
    for rows in node_rows.values():
        for row in rows:
            # Heading underline is decoration; never mask a body row's spacing.
            if any(row["id"] in [r["id"] for r in node_rows.get(identifier, [])]
                   for identifier in node_rectangles):
                a, b, c, d = row["pixel_bbox"]
                residual[max(0, b-6):b+d+6, max(0, a-6):a+c+6] = 0
    for record in connectors:
        if record.get("verified") and record.get("polyline"):
            points = np.array([[round(point[1]*ink.shape[1]), round(point[0]*ink.shape[0])]
                               for point in record["polyline"]], dtype="int32")
            cv2.polylines(residual, [points], False, 0, 7)
    count, _, stats, _ = cv2.connectedComponentsWithStats(residual[y:bottom, x:right], 8)
    unexplained = [[int(item[0]+x), int(item[1]+y), int(item[2]), int(item[3]), int(item[4])]
                   for item in stats[1:count] if item[4] >= 4]
    return {"complete": not orphans and not unexplained, "pixel_bbox": [x, y, right-x, bottom-y],
            "orphan_or_duplicate_word_ids": sorted(orphans), "unexplained_ink_components": unexplained,
            "qualification": "Pixel-derived chart rectangle envelope; page header/caption/footer are outside this scope."}


def verify_raster_records(image_path, ingest_result, connector_receipt=None):
    """Recompute source-literal/enclosure evidence and scoped row completeness.

    The input is a retained extraction, never a reference graph or answer set.
    Results are admission evidence only; this function changes no graph/status.
    """
    pixels = Path(image_path).read_bytes()
    image_hash = hashlib.sha256(pixels).hexdigest()
    source = ingest_result["ocr"]["input"]
    graph = ingest_result["graph"]
    if image_hash != source["image_sha256"] or image_hash != ingest_result["input_image_sha256"]:
        raise ValueError("RASTER_VERIFICATION_IMAGE_MISMATCH")
    binding = graph.get("source_binding", {})
    if binding and (binding.get("asset_sha256") != image_hash or binding.get("edition_id") != source["edition_id"]):
        raise ValueError("RASTER_VERIFICATION_GRAPH_SCOPE_MISMATCH")
    image = cv2.imdecode(np.frombuffer(pixels, dtype="uint8"), cv2.IMREAD_GRAYSCALE)
    if image is None or [image.shape[1], image.shape[0]] != [source["width"], source["height"]]:
        raise ValueError("RASTER_VERIFICATION_IMAGE_GEOMETRY_MISMATCH")
    ink = image < 180
    observations = {item["id"]: item for item in ingest_result["ocr"]["observations"]}
    if len(observations) != len(ingest_result["ocr"]["observations"]) or any(
            item["image_sha256"] != image_hash or item["edition_id"] != source["edition_id"]
            for item in observations.values()):
        raise ValueError("RASTER_VERIFICATION_OBSERVATION_SCOPE_MISMATCH")
    rectangles = {key: value for key, value in observations.items() if value["kind"] == "visual_rectangle"}
    bank = _glyph_bank(ink, graph, observations)
    decisions, node_rows, node_rectangles = {}, {}, {}
    for node in graph["nodes"]:
        rows, words = _word_rows(node, observations)
        node_rows[node["id"]] = rows
        rectangle_ids = [identifier for identifier in node.get("observation_ids", []) if identifier in rectangles]
        if len(rectangle_ids) == 1:
            node_rectangles[node["id"]] = rectangles[rectangle_ids[0]]
        record = {"label": node["label"], "code": node.get("code"), "kind": node["kind"],
                  "label_supported": False, "designation_supported": False,
                  "label_rule": "candidate", "designation_rule": "candidate",
                  "label_observation_ids": [], "designation_observation_ids": [],
                  "row_observation_ids": [row["id"] for row in rows],
                  "word_anchors": [{"id": word["id"], "text": word["text"],
                      "pixel_bbox": word["pixel_bbox"], "confidence": word["confidence"]} for word in words],
                  "support_node_ids": [], "reasons": []}
        label_words = words[:-1] if node["kind"] == "process" else words
        exact_label = bool(label_words) and _tokens(" ".join(word["text"] for word in label_words)) == _tokens(node["label"])
        anchored = bool(rows) and all(_ink_word(ink, word) for word in words)
        if node["kind"] in {"category", "root"}:
            rectangle = node_rectangles.get(node["id"])
            box_rows = ([] if rectangle is None else sorted([item for item in observations.values()
                if item["kind"] == "ocr_row" and _contains(rectangle["pixel_bbox"], item["pixel_bbox"])],
                key=lambda item: item["pixel_bbox"][1]))
            anchored = anchored and bool(box_rows) and (rows == box_rows if node["kind"] == "root"
                else len(rows) == 1 and rows[0]["id"] == box_rows[0]["id"])
        label_confident = bool(label_words) and min(float(word["confidence"]) for word in label_words) >= MIN_LITERAL_CONFIDENCE
        if exact_label and anchored and label_confident:
            record.update(label_supported=True, label_rule="pixel-anchored-exact-ocr-label-1",
                          label_observation_ids=[word["id"] for word in label_words])
        else:
            record["reasons"].append("label_missing_conflicting_unanchored_or_low_confidence")
        if node.get("code") and node["kind"] == "process" and words:
            word, expected = words[-1], node["code"]
            if (anchored and word["text"] == expected and float(word["confidence"]) >= MIN_LITERAL_CONFIDENCE):
                record.update(designation_supported=True, designation_rule="pixel-anchored-exact-ocr-code-1")
            elif anchored:
                supported, proof = _glyph_corrob(ink, word, expected, bank)
                record["glyph_evidence"] = proof
                if supported:
                    record.update(designation_supported=True, designation_rule="source-local-pixel-glyph-code-1")
                    template_words = {item["template_word_id"] for item in proof.get("glyphs", [])}
                    record["support_node_ids"] = sorted({other["id"] for other in graph["nodes"]
                        if any(template_words.intersection(observations[row_id].get("word_observation_ids", []))
                               for row_id in other.get("observation_ids", [])
                               if row_id in observations and observations[row_id]["kind"] == "ocr_row")})
            if record["designation_supported"]:
                record["designation_observation_ids"] = [word["id"]]
            else:
                record["reasons"].append("code_requires_additional_source_evidence")
        decisions[node["id"]] = record
    categories = [node for node in graph["nodes"] if node["kind"] == "category"]
    processes = [node for node in graph["nodes"] if node["kind"] == "process"]
    enclosures, coverage = {}, {}
    for category in categories:
        identifier = category["id"]
        rectangle = node_rectangles.get(identifier)
        if rectangle is None:
            coverage[identifier] = {"observed_rows_complete": False, "accepted_literals_complete": False,
                                    "complete": False, "reasons": ["category_rectangle_missing"]}
            continue
        box = rectangle["pixel_bbox"]
        border_ok, border = _border_support(ink, box)
        rows = sorted([row for row in observations.values() if row["kind"] == "ocr_row"
                       and _contains(box, row["pixel_bbox"])], key=lambda row: row["pixel_bbox"][1])
        header_ids = {row["id"] for row in node_rows[identifier]}
        body = [row for row in rows if row["id"] not in header_ids]
        assigned = {row["id"]: [node["id"] for node in processes if row in node_rows[node["id"]]] for row in body}
        missing_bands = _row_bands(ink, box, rows)
        row_words = {item for row in rows for item in row["word_observation_ids"]}
        orphan_words = [item["id"] for item in observations.values() if item["kind"] == "ocr_word"
                        and _contains(box, item["pixel_bbox"]) and item["id"] not in row_words]
        unexplained_ink = _unexplained_ink(ink, box, rows, observations, header_ids)
        for edge in graph["edges"]:
            if edge["type"] != "ENCLOSES_ROW" or edge["from"] != identifier:
                continue
            child_rows = node_rows.get(edge["to"], [])
            unique = (len(child_rows) == 1 and child_rows[0]["id"] in assigned
                      and assigned[child_rows[0]["id"]] == [edge["to"]]
                      and sum(_contains(other["pixel_bbox"], child_rows[0]["pixel_bbox"])
                              for other in node_rectangles.values()) == 1)
            key = relation_key(edge["from"], edge["to"], edge["type"])
            enclosures[key] = {"from_id": edge["from"], "to_id": edge["to"], "type": edge["type"],
                "verified": bool(border_ok and unique), "rule": "pixel-rectangle-row-enclosure-1",
                "observation_ids": [rectangle["id"], *[row["id"] for row in child_rows]],
                "border_support": border, "reasons": [] if border_ok and unique else ["border_or_unique_row_enclosure_not_established"]}
        selected = [ids[0] for ids in assigned.values() if len(ids) == 1]
        enclosure_complete = all(sum(edge["from"] == identifier and edge["to"] == child
            and edge["type"] == "ENCLOSES_ROW" for edge in graph["edges"]) == 1
            and enclosures.get(relation_key(identifier, child, "ENCLOSES_ROW"), {}).get("verified")
            for child in selected)
        observed_complete = (bool(body) and border_ok and all(len(ids) == 1 for ids in assigned.values())
                             and not missing_bands and not orphan_words and not unexplained_ink and enclosure_complete)
        literals_complete = decisions[identifier]["label_supported"] and all(
            decisions[item]["label_supported"] and decisions[item]["designation_supported"] for item in selected)
        coverage[identifier] = {"scope": "selected_category_body", "observed_rows_complete": observed_complete,
            "accepted_literals_complete": bool(literals_complete), "complete": bool(observed_complete and literals_complete),
            "body_observation_ids": [row["id"] for row in body], "process_ids": selected,
            "unassigned_or_duplicate_rows": [key for key, ids in assigned.items() if len(ids) != 1],
            "unassigned_ink_bands": missing_bands, "orphan_word_ids": orphan_words,
            "unexplained_ink_components": unexplained_ink, "border_support": border,
            "projected_enclosures_complete": bool(enclosure_complete),
            "reasons": ([] if observed_complete else ["observed_row_or_pixel_band_coverage_incomplete"])
                + ([] if literals_complete else ["literal_or_designation_evidence_incomplete"])}
    represented_rectangles = {value["id"] for value in node_rectangles.values()}
    # Recompute the existing pixel-only rectangle detector; omitted cached boxes
    # must not disappear merely because the supplied graph/observations omit them.
    from src.evidence_a1_raster import _rectangles
    pixel_rectangles, _ = _rectangles(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), repair_border_gaps=True)
    rectangle_coverage = sorted(pixel_rectangles) == sorted(item["pixel_bbox"] for item in rectangles.values())
    connectors = [] if connector_receipt is None else connector_receipt.get("records", [])
    graph_connections = {(edge["from"], edge["to"]) for edge in graph["edges"] if edge["type"] == "CHART_CONNECTOR"}
    connected = {item["to_id"] for item in connectors if item.get("verified") and item.get("from_id") == graph["root_id"]
                 and (item["from_id"], item["to_id"]) in graph_connections}
    chart_closure = _chart_closure(ink, pixel_rectangles, observations, node_rows, node_rectangles, connectors)
    root_supported = decisions.get(graph["root_id"], {}).get("label_supported", False)
    observed_complete = (bool(coverage) and rectangle_coverage and chart_closure["complete"]
                         and represented_rectangles == set(rectangles)
                         and all(value["observed_rows_complete"] for value in coverage.values())
                         and connected == {node["id"] for node in categories})
    literals_complete = root_supported and all(value["accepted_literals_complete"] for value in coverage.values())
    return {"schema_version": VERSION, "image_sha256": image_hash,
        "source_scope": {"edition_id": source["edition_id"], "source_identity_id": binding.get("source_identity_id")},
        "input_graph_sha256": hashlib.sha256(_canonical(graph)).hexdigest(),
        "criteria": {"minimum_literal_confidence": MIN_LITERAL_CONFIDENCE, "minimum_glyph_iou": MIN_GLYPH_IOU,
                     "minimum_glyph_class_margin": MIN_GLYPH_MARGIN, "minimum_border_support": .95,
                     "qualification": "Scoped printed observations under the rectangular-chart adapter, not semantic subtype or other-source completeness."},
        "nodes": decisions, "enclosures": enclosures, "coverage": coverage,
        "chart_coverage": {"scope": "selected_raster_chart_rectangles", "observed_rows_complete": observed_complete,
            "accepted_literals_complete": bool(literals_complete), "complete": bool(observed_complete and literals_complete),
            "represented_rectangle_ids": sorted(represented_rectangles), "observed_rectangle_ids": sorted(rectangles),
            "pixel_rectangle_coverage": rectangle_coverage,
            "pixel_chart_closure": chart_closure,
            "unverified_category_connections": sorted({node["id"] for node in categories}-connected),
            "reasons": ([] if observed_complete else ["structure_or_row_coverage_incomplete"])
                + ([] if literals_complete else ["literal_evidence_incomplete"])}}
