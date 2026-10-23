"""Verify physical chart connectors against retained raster pixels.

Observed boxes restrict the search, but are not evidence that a link exists.
A pixel-supported line hypothesis must reach both box boundaries, remain
continuous between them, and avoid every other box interior. No native graph,
OCR rerun, dictionary or model output is consulted. This establishes scoped
physical adjacency only.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import cv2
import numpy as np


STROKE_VERSION = "raster-stroke-verification-1.0"


def _rectangle(node, width, height):
    region = node.get("region")
    if (not isinstance(region, list) or len(region) != 4
            or any(type(v) not in {int, float} or not math.isfinite(v) for v in region)
            or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1)):
        raise ValueError("STROKE_NODE_REGION_INVALID")
    return np.array([region[1]*width, region[0]*height,
                     region[3]*width, region[2]*height], dtype=float)


def _line_interval(point, unit, box):
    """Slab intersection of an infinite line and a closed rectangle."""
    first, last = -math.inf, math.inf
    for axis in range(2):
        low, high = box[axis], box[axis + 2]
        if abs(unit[axis]) < 1e-9:
            if not low <= point[axis] <= high:
                return None
            continue
        left, right = sorted(((low - point[axis])/unit[axis],
                              (high - point[axis])/unit[axis]))
        first, last = max(first, left), min(last, right)
        if first > last:
            return None
    return first, last


def _max_missing_run(hits):
    longest = current = 0
    for hit in hits:
        current = 0 if hit else current + 1
        longest = max(longest, current)
    return longest


def _candidate_stroke(segment, root_box, category_box, other_boxes,
                      dilated_ink, ink, contact_tolerance, max_gap, band, *,
                      refine=True, hypothesis_source="hough"):
    point, end = np.array(segment[:2], float), np.array(segment[2:], float)
    length = float(np.linalg.norm(end - point))
    if length <= 0:
        return None
    unit = (end - point)/length
    root_center = (root_box[:2] + root_box[2:])/2
    category_center = (category_box[:2] + category_box[2:])/2
    if np.dot(unit, category_center - root_center) < 0:
        point, end, unit = end, point, -unit
    root = _line_interval(point, unit, root_box)
    target = _line_interval(point, unit, category_box)
    if root is None or target is None:
        return None
    start, stop = root[1], target[0]
    outside_length = stop - start
    if outside_length < max(10, contact_tolerance*2):
        return None
    # Hough often splits a thick stroke into collinear subsegments. It supplies
    # only a line hypothesis; the full interbox span is checked against pixels
    # below, including both endpoint contacts. A text/border-only hypothesis has
    # no substantial overlap with this outside span and is rejected here.
    observed_fraction = max(0, min(length, stop) - max(0, start))/outside_length
    if observed_fraction < .25:
        return None
    for box in other_boxes:
        interior = box + np.array([contact_tolerance, contact_tolerance,
                                   -contact_tolerance, -contact_tolerance])
        if np.any(interior[2:] <= interior[:2]):
            continue
        crossing = _line_interval(point, unit, interior)
        if crossing and min(stop, crossing[1]) - max(start, crossing[0]) > contact_tolerance:
            return None
    count = max(2, math.ceil(outside_length) + 1)
    positions = point + np.linspace(start, stop, count)[:, None]*unit
    indices = np.rint(positions).astype(int)
    h, w = dilated_ink.shape
    if np.any(indices[:, 0] < 0) or np.any(indices[:, 0] >= w) or np.any(indices[:, 1] < 0) or np.any(indices[:, 1] >= h):
        return None
    hits = dilated_ink[indices[:, 1], indices[:, 0]] != 0
    missing = _max_missing_run(hits)
    coverage = float(np.mean(hits))
    if not hits[0] or not hits[-1] or coverage < .97 or missing > max_gap:
        return None
    if refine:
        # Fit actual outside-box ink, not Hough's jittered subsegment endpoints.
        # This prevents one diagonal touching a box corner from looking like
        # several distinct connectors solely because of angle quantization.
        normal = np.array([-unit[1], unit[0]])
        sampled = np.rint(positions[:, None, :] +
            np.arange(-2*band, 2*band + 1)[None, :, None]*normal).astype(int).reshape(-1, 2)
        valid = ((sampled[:, 0] >= 0) & (sampled[:, 0] < w) &
                 (sampled[:, 1] >= 0) & (sampled[:, 1] < h))
        sampled = sampled[valid]
        sampled = sampled[ink[sampled[:, 1], sampled[:, 0]] != 0]
        for box in (root_box, category_box):
            sampled = sampled[~((sampled[:, 0] >= box[0]) & (sampled[:, 0] <= box[2]) &
                                (sampled[:, 1] >= box[1]) & (sampled[:, 1] <= box[3]))]
        sampled = np.unique(sampled, axis=0)
        if len(sampled) < 20:
            return None
        vx, vy, cx, cy = cv2.fitLine(sampled.astype(np.float32), cv2.DIST_L2, 0, .01, .01).ravel()
        fitted_unit, center = np.array([vx, vy]), np.array([cx, cy])
        projected = (sampled - center) @ fitted_unit
        fitted = [*(center + projected.min()*fitted_unit),
                  *(center + projected.max()*fitted_unit)]
        refined = _candidate_stroke(fitted, root_box, category_box, other_boxes,
            dilated_ink, ink, contact_tolerance, max_gap, band, refine=False,
            hypothesis_source=hypothesis_source)
        if refined is not None:
            refined["hypothesis_segment"] = [int(value) for value in segment]
            refined["fit_ink_samples"] = len(sampled)
        return refined
    return {"endpoints": [positions[0].tolist(), positions[-1].tolist()],
            "ink_coverage": coverage, "max_gap_pixels": missing,
            "outside_length_pixels": outside_length,
            "hypothesis_segment": [int(value) for value in segment],
            "hypothesis_source": hypothesis_source,
            "hough_observed_fraction": observed_fraction,
            "root_ink_contact": bool(hits[0]),
            "category_ink_contact": bool(hits[-1])}


def _axis_pixel_hypotheses(left, right, near_ink):
    """Find fully ink-supported axis spans that global Hough may split/miss."""
    spans = []
    for swap in (False, True):
        first, second = (left[[1, 0, 3, 2]], right[[1, 0, 3, 2]]) if swap else (left, right)
        pixels = near_ink.T if swap else near_ink
        if first[2] < second[0]:
            start, stop = first[2], second[0]
        elif second[2] < first[0]:
            start, stop = second[2], first[0]
        else:
            continue
        lower = max(0, math.ceil(max(first[1], second[1])))
        upper = min(pixels.shape[0] - 1, math.floor(min(first[3], second[3])))
        lo, hi = max(0, math.ceil(start)), min(pixels.shape[1] - 1, math.floor(stop))
        if upper < lower or hi - lo < 10:
            continue
        rows = np.arange(lower, upper + 1)
        coverage = np.mean(pixels[rows, lo:hi + 1] != 0, axis=1)
        possible = rows[coverage >= .97]
        if not len(possible):
            continue
        groups = np.split(possible, np.where(np.diff(possible) > 1)[0] + 1)
        for group in groups:
            axis = float(np.median(group))
            spans.append([axis, start, axis, stop] if swap else [start, axis, stop, axis])
    return spans


def verify_chart_connectors(image_path, graph):
    """Return source-bound stroke receipts for every observed root/category pair.

    A verified result is an undirected physical connection, not a subtype or an
    arrow-direction claim. Endpoint order follows root-to-category solely for
    graph traversal and evidence presentation. Unknowns are never negatives.
    """
    payload = Path(image_path).read_bytes()
    image_sha = hashlib.sha256(payload).hexdigest()
    declared = [graph.get("source_binding", {}).get("asset_sha256"),
                graph.get("extraction_provenance", {}).get("input_asset_sha256")]
    if any(value is not None and value != image_sha for value in declared):
        raise ValueError("STROKE_IMAGE_SOURCE_MISMATCH")
    image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("STROKE_IMAGE_INVALID")
    height, width = image.shape
    nodes = [node for node in graph["nodes"] if node.get("kind") in {"root", "category"}]
    by_id = {node["id"]: node for node in nodes}
    if len(by_id) != len(nodes) or graph.get("root_id") not in by_id or by_id[graph["root_id"]]["kind"] != "root":
        raise ValueError("STROKE_ROOT_OR_NODE_ID_INVALID")
    boxes = {node["id"]: _rectangle(node, width, height) for node in nodes}
    scale = min(width, height)
    band = max(1, round(scale*.0008))
    contact = max(4, round(scale*.004))
    max_gap = max(3, round(scale*.0015))
    ink = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    near_ink = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_RECT, (2*band+1, 2*band+1)))
    lines = cv2.HoughLinesP(ink, 1, np.pi/1800, threshold=max(12, round(scale*.015)),
                          minLineLength=max(20, round(scale*.04)), maxLineGap=max_gap)
    segments = [] if lines is None else [line[0].tolist() for line in lines]
    records = []
    root_id = graph["root_id"]
    for node in nodes:
        if node["kind"] != "category":
            continue
        target = node["id"]
        other = [box for identifier, box in boxes.items() if identifier not in {root_id, target}]
        hypotheses = [(line, "hough") for line in segments]
        hypotheses.extend((line, "axis_pixel_span") for line in _axis_pixel_hypotheses(
            boxes[root_id], boxes[target], near_ink))
        candidates = [candidate for line, method in hypotheses if (candidate := _candidate_stroke(
            line, boxes[root_id], boxes[target], other, near_ink, ink, contact, max_gap, band,
            hypothesis_source=method)) is not None]
        candidates.sort(key=lambda item: (-item["ink_coverage"], item["max_gap_pixels"],
                                           -item["hough_observed_fraction"], -item["outside_length_pixels"]))
        distinct = []
        for candidate in candidates:
            endpoints = np.array(candidate["endpoints"])
            if not any(np.max(np.linalg.norm(endpoints - np.array(other["endpoints"]), axis=1)) <= contact
                       for other in distinct):
                distinct.append(candidate)
        item = {"from_id": root_id, "to_id": target, "type": "CHART_CONNECTOR",
                "verified": len(distinct) == 1, "direction": "undirected",
                "path_order": "root_to_category_for_traversal_only",
                "arrow_direction": "not_asserted",
                "image_sha256": image_sha, "method": STROKE_VERSION,
                "reason": "continuous_pixel_stroke_contacts_both_box_boundaries" if len(distinct) == 1 else
                          "no_continuous_connector_stroke" if not distinct else "multiple_distinct_strokes",
                "distinct_stroke_count": len(distinct)}
        if len(distinct) == 1:
            accepted = distinct[0]
            endpoints = np.array(accepted["endpoints"])
            lower = np.maximum(0, np.min(endpoints, axis=0) - band - 1)
            upper = np.minimum([width, height], np.max(endpoints, axis=0) + band + 1)
            item.update(pixel_endpoints=accepted["endpoints"],
                polyline=[[round(y/height, 8), round(x/width, 8)] for x, y in endpoints],
                region=[round(lower[1]/height, 8), round(lower[0]/width, 8),
                        round(upper[1]/height, 8), round(upper[0]/width, 8)],
                measurements={key: value for key, value in accepted.items() if key != "endpoints"})
        records.append(item)
    return {"version": STROKE_VERSION, "image_sha256": image_sha,
            "width": width, "height": height, "opencv_version": cv2.__version__,
            "criteria": {"minimum_ink_coverage": .97, "maximum_missing_run_pixels": max_gap,
                         "contact_tolerance_pixels": contact, "ink_band_radius_pixels": band,
                         "no_other_box_interior_crossing": True,
                         "unique_physical_stroke": True,
                         "hypotheses": "Hough segments or fully ink-supported axis spans; both reverified against pixels",
                         "arrow_or_semantic_direction_not_inferred": True},
            "records": records, "hough_segment_count": len(segments),
            "verified_count": sum(record["verified"] for record in records),
            "qualification": "Pixel-supported physical adjacency only; no semantic subtype or human review is asserted."}
