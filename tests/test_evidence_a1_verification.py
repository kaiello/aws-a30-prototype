"""Small pixel/observation admission regressions; no AWS answers or OCR calls."""
from copy import deepcopy
import hashlib

import cv2
import numpy as np

from src.evidence_a1_raster import _rectangles
from src.evidence_a1_verification import verify_raster_records, relation_key, _glyphs, _glyph_corrob


def fixture(tmp_path):
    image = np.full((500, 800, 3), 255, dtype="uint8")
    cv2.rectangle(image, (20, 180), (160, 280), (0, 0, 0), 1)
    cv2.rectangle(image, (250, 80), (750, 420), (0, 0, 0), 1)
    cv2.line(image, (160, 230), (250, 230), (0, 0, 0), 2)
    observations = []

    def row(identifier, items):
        words = []
        for index, (text, x, baseline) in enumerate(items):
            (width, height), descender = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, .65, 1)
            cv2.putText(image, text, (x, baseline), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 0, 0), 1)
            word = {"id": identifier+f"w{index}", "kind": "ocr_word", "text": text,
                    "pixel_bbox": [x, baseline-height, width, height+descender], "confidence": 96.0}
            words.append(word); observations.append(word)
        left = min(item["pixel_bbox"][0] for item in words)
        top = min(item["pixel_bbox"][1] for item in words)
        right = max(item["pixel_bbox"][0]+item["pixel_bbox"][2] for item in words)
        bottom = max(item["pixel_bbox"][1]+item["pixel_bbox"][3] for item in words)
        observed = {"id": identifier, "kind": "ocr_row", "text": " ".join(item["text"] for item in words),
                    "pixel_bbox": [left, top, right-left, bottom-top], "confidence": 96.0,
                    "word_observation_ids": [item["id"] for item in words]}
        observations.append(observed)
        return observed

    row("rootrow", [("ROOT", 50, 230)])
    row("heading", [("FOLDING (F)", 280, 120)])
    row("body", [("ribbon", 280, 180), ("fold", 360, 180), ("RF", 650, 180)])
    boxes, _ = _rectangles(image, repair_border_gaps=True)
    root_box = next(box for box in boxes if box[0] < 100)
    category_box = next(box for box in boxes if box[0] > 200)
    observations.extend([{"id": "rootbox", "kind": "visual_rectangle", "pixel_bbox": root_box},
                         {"id": "categorybox", "kind": "visual_rectangle", "pixel_bbox": category_box}])
    graph = {"root_id": "root", "nodes": [
        {"id": "root", "kind": "root", "label": "ROOT", "observation_ids": ["rootbox", "rootrow"]},
        {"id": "category", "kind": "category", "label": "FOLDING (F)", "observation_ids": ["categorybox", "heading"]},
        {"id": "process", "kind": "process", "label": "ribbon fold", "code": "RF", "observation_ids": ["body"]}],
        "edges": [{"from": "category", "to": "process", "type": "ENCLOSES_ROW"},
                  {"from": "root", "to": "category", "type": "CHART_CONNECTOR"}]}
    value = {"graph": graph, "ocr": {"input": {"edition_id": "synthetic", "width": 800, "height": 500},
                                     "observations": observations}}
    path = tmp_path / "pixels.png"
    update(path, image, value)
    connectors = {"records": [{"from_id": "root", "to_id": "category", "type": "CHART_CONNECTOR", "verified": True,
                               "polyline": [[230/500, 160/800], [230/500, 250/800]]}]}
    return path, image, value, connectors


def update(path, image, value):
    path.write_bytes(cv2.imencode(".png", image)[1].tobytes())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    value["input_image_sha256"] = value["ocr"]["input"]["image_sha256"] = digest
    for item in value["ocr"]["observations"]:
        item.update(image_sha256=digest, edition_id="synthetic")


def test_exact_pixel_anchored_rows_have_scoped_completeness(tmp_path):
    path, _, value, connectors = fixture(tmp_path)
    original = deepcopy(value)
    result = verify_raster_records(path, value, connectors)
    assert result["nodes"]["process"]["label_supported"]
    assert result["nodes"]["process"]["designation_supported"]
    assert result["enclosures"][relation_key("category", "process", "ENCLOSES_ROW")]["verified"]
    assert result["coverage"]["category"]["complete"]
    assert result["chart_coverage"]["complete"]
    assert value == original  # Verification is evidence, not a graph/status mutation.


def test_missing_projected_edge_blocks_exhaustive_claim(tmp_path):
    path, _, value, connectors = fixture(tmp_path)
    value["graph"]["edges"] = [edge for edge in value["graph"]["edges"] if edge["type"] != "ENCLOSES_ROW"]
    result = verify_raster_records(path, value, connectors)
    assert not result["coverage"]["category"]["observed_rows_complete"]
    assert not result["chart_coverage"]["complete"]


def test_retained_nodes_cannot_hide_an_omitted_pixel_rectangle(tmp_path):
    path, image, value, connectors = fixture(tmp_path)
    cv2.rectangle(image, (20, 20), (160, 100), (0, 0, 0), 1)
    update(path, image, value)
    result = verify_raster_records(path, value, connectors)
    assert result["coverage"]["category"]["complete"]
    assert not result["chart_coverage"]["pixel_rectangle_coverage"]
    assert not result["chart_coverage"]["complete"]


def test_unrecognized_body_ink_blocks_row_completeness(tmp_path):
    path, image, value, connectors = fixture(tmp_path)
    cv2.putText(image, "unread", (300, 300), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 0, 0), 1)
    update(path, image, value)
    result = verify_raster_records(path, value, connectors)
    assert result["coverage"]["category"]["unexplained_ink_components"]
    assert not result["coverage"]["category"]["complete"]


def test_corrected_code_needs_pixels_not_dictionary_agreement(tmp_path):
    path, _, value, connectors = fixture(tmp_path)
    value["graph"]["nodes"][-1]["code"] = "RZ"
    result = verify_raster_records(path, value, connectors)
    decision = result["nodes"]["process"]
    assert decision["label_supported"]
    assert not decision["designation_supported"]
    assert not result["coverage"]["category"]["accepted_literals_complete"]


def test_glyph_corroboration_uses_other_observed_word_and_excludes_self():
    ink = np.zeros((50, 100), dtype=bool)
    ink[10:35, 10:14] = True
    word = {"id": "target", "pixel_bbox": [8, 8, 10, 30]}
    glyph, box = _glyphs(ink, word)[0]
    supported, evidence = _glyph_corrob(ink, word, "I", {"I": [(glyph, "other", 0, box)]})
    assert supported and evidence["recognized_code"] == "I"
    assert evidence["glyphs"][0]["template_word_id"] == "other"
    supported, _ = _glyph_corrob(ink, word, "I", {"I": [(glyph, "target", 0, box)]})
    assert not supported
