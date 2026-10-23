"""Pixel-stroke checks over synthetic images; no source facts, OCR or model."""
import hashlib

import cv2
import numpy as np
import pytest

from src.evidence_a1_strokes import verify_chart_connectors


def chart(tmp_path, *, diagonal=False, broken=False, obstruction=False):
    image = np.full((400, 600), 255, np.uint8)
    root = [50, 150, 150, 230]
    category = [350, 40 if diagonal else 150, 550, 120 if diagonal else 230]
    for left, top, right, bottom in (root, category):
        cv2.rectangle(image, (left, top), (right, bottom), 0, 2)
    start = (150, 150 if diagonal else 190)
    end = (350, 120 if diagonal else 190)
    cv2.line(image, start, end, 0, 2)
    if broken:
        cv2.rectangle(image, (238, 168), (266, 210), 255, -1)
    nodes = [{"id": "root", "kind": "root", "region": [root[1]/400, root[0]/600, root[3]/400, root[2]/600]},
             {"id": "category", "kind": "category", "region": [category[1]/400, category[0]/600, category[3]/400, category[2]/600]}]
    if obstruction:
        box = [220, 160, 290, 220]
        cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), 0, 2)
        nodes.append({"id": "other", "kind": "category", "region": [box[1]/400, box[0]/600, box[3]/400, box[2]/600]})
    path = tmp_path / "chart.png"
    assert cv2.imwrite(str(path), image)
    graph = {"root_id": "root", "nodes": nodes, "edges": []}
    return path, graph


@pytest.mark.parametrize("diagonal", [False, True])
def test_continuous_stroke_has_correct_interbox_evidence_and_no_arrow_claim(tmp_path, diagonal):
    path, graph = chart(tmp_path, diagonal=diagonal)
    result = verify_chart_connectors(path, graph)
    record = result["records"][0]
    assert result["verified_count"] == 1
    assert record["verified"] is True
    assert record["image_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["direction"] == "undirected"
    assert record["arrow_direction"] == "not_asserted"
    assert record["measurements"]["ink_coverage"] >= .97
    assert record["pixel_endpoints"][0][0] == pytest.approx(150, abs=2)
    assert record["pixel_endpoints"][1][0] == pytest.approx(350, abs=2)
    assert record["region"] != graph["nodes"][0]["region"]
    assert record["region"] != graph["nodes"][1]["region"]


def test_large_missing_stroke_is_not_inferred_from_endpoint_boxes(tmp_path):
    path, graph = chart(tmp_path, broken=True)
    result = verify_chart_connectors(path, graph)
    assert result["verified_count"] == 0
    assert result["records"][0]["reason"] == "no_continuous_connector_stroke"


def test_stroke_through_another_box_is_not_a_direct_connection(tmp_path):
    path, graph = chart(tmp_path, obstruction=True)
    result = verify_chart_connectors(path, graph)
    record = next(item for item in result["records"] if item["to_id"] == "category")
    assert record["verified"] is False


def test_source_pixels_cannot_be_replaced_under_declared_hash(tmp_path):
    path, graph = chart(tmp_path)
    graph["source_binding"] = {"asset_sha256": "0" * 64}
    with pytest.raises(ValueError, match="SOURCE_MISMATCH"):
        verify_chart_connectors(path, graph)
