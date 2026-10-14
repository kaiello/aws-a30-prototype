"""
test_figure_bboxes.py: Automated test suite for visual bounding boxes,
spatial coordinate validity, and figure registry enrichment in AWS A3.0.
"""

import json
import pytest
from pathlib import Path

from src.config import BASE_DIR
from src.figure_inspectors import (
    FIGURE_INSPECTORS,
    get_figure_data,
    get_figure_bboxes,
    get_all_figures_catalog,
    get_inspector_html,
    resolve_figure_image_filename
)

BBOX_MANIFEST_PATH = BASE_DIR / "parsed" / "figures" / "figure_bboxes.json"


def test_manifest_file_exists_and_valid():
    """Verify figure_bboxes.json exists and parses cleanly."""
    assert BBOX_MANIFEST_PATH.exists(), f"Missing manifest at {BBOX_MANIFEST_PATH}"
    data = json.loads(BBOX_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert len(data) >= 60, f"Expected at least 60 figures in manifest, found {len(data)}"


def test_all_registry_figures_mapped():
    """Verify all 62 figures in FIGURE_INSPECTORS have corresponding entries in manifest."""
    data = json.loads(BBOX_MANIFEST_PATH.read_text(encoding="utf-8"))
    for fig_id in FIGURE_INSPECTORS:
        assert fig_id in data, f"Figure '{fig_id}' missing from spatial manifest"
        assert "groups" in data[fig_id], f"Figure '{fig_id}' has no groups in manifest"


def test_normalized_coordinate_constraints():
    """Verify every bounding box strictly satisfies 0.0 <= min < max <= 1.0."""
    data = json.loads(BBOX_MANIFEST_PATH.read_text(encoding="utf-8"))
    total_bboxes_tested = 0

    for fig_id, fig_entry in data.items():
        for g in fig_entry.get("groups", []):
            for c in g.get("chips", []):
                bbox = c.get("bbox")
                assert bbox is not None, f"Chip '{c.get('label')}' in '{fig_id}' has no bbox"
                assert len(bbox) == 4, f"Bbox for '{c.get('label')}' must have 4 coordinates, got {bbox}"

                ymin, xmin, ymax, xmax = bbox
                # Bounds check
                assert 0.0 <= ymin < ymax <= 1.0, (
                    f"Invalid Y coordinates in {fig_id} -> '{c.get('label')}': ymin={ymin}, ymax={ymax}"
                )
                assert 0.0 <= xmin < xmax <= 1.0, (
                    f"Invalid X coordinates in {fig_id} -> '{c.get('label')}': xmin={xmin}, xmax={xmax}"
                )

                # Center check
                center = c.get("center")
                assert center is not None and len(center) == 2, f"Invalid center for '{c.get('label')}'"
                cy, cx = center
                assert ymin <= cy <= ymax, f"Center Y ({cy}) out of bbox [{ymin}, {ymax}] for {c.get('label')}"
                assert xmin <= cx <= xmax, f"Center X ({cx}) out of bbox [{xmin}, {xmax}] for {c.get('label')}"

                total_bboxes_tested += 1

    assert total_bboxes_tested >= 267, f"Expected >= 267 chips tested, got {total_bboxes_tested}"


def test_figure_data_enrichment():
    """Verify get_figure_data() properly injects bbox and center metadata."""
    fig_data = get_figure_data("Figure B25")
    assert fig_data, "Figure B25 data missing"
    assert "groups" in fig_data
    
    first_chip = fig_data["groups"][0]["chips"][0]
    assert "bbox" in first_chip, "Enriched chip missing bbox"
    assert "center" in first_chip, "Enriched chip missing center"
    assert len(first_chip["bbox"]) == 4


def test_catalog_bbox_availability():
    """Verify get_all_figures_catalog() supplies bounding box metadata to API clients."""
    catalog = get_all_figures_catalog()
    assert len(catalog) >= 60

    sample = next(f for f in catalog if f["id"] == "Figure B1")
    assert sample["image_file"].endswith(".png")
    assert len(sample["groups"]) > 0
    chip = sample["groups"][0]["chips"][0]
    assert "bbox" in chip
    assert chip["bbox"][0] < chip["bbox"][2]


def test_inspector_html_rendering_with_focus_buttons():
    """Verify get_inspector_html() renders clickable 🎯 focus buttons with serialized bboxes."""
    html = get_inspector_html("Figure B40")
    assert "chip-focus-btn" in html
    assert "🎯" in html
    assert "focusFeature" in html
    assert "Figure B40" in html
