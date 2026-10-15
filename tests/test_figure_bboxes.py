"""
test_figure_bboxes.py: Automated test suite for visual bounding boxes,
spatial coordinate validity, and figure registry enrichment in AWS A3.0.
"""

import sys
import json
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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


def test_figure_b1_layout_and_applicable_welds_alignment():
    """Verify Figure B1 separates illustrations (left column) from applicable welds (right column)."""
    fig = get_figure_data("Figure B1")
    chips_by_label = {c["label"]: c for g in fig["groups"] for c in g["chips"]}
    
    # Left column illustrations should be on left (xmax <= 0.60)
    for p in ["Panel (A) Butt Joint", "Panel (B) Corner Joint", "Panel (C) T-Joint", "Panel (D) Lap Joint", "Panel (E) Parallel Joint"]:
        assert p in chips_by_label
        assert chips_by_label[p]["bbox"][3] <= 0.60, f"{p} exceeds left column"
        assert chips_by_label[p]["bbox"][0] >= 0.035, f"{p} invalid ymin"
        
    # Right column applicable welds should be on right (xmin >= 0.58)
    for w in ["Butt Joint Applicable Welds", "Corner Joint Applicable Welds", "T-Joint Applicable Welds", "Lap Joint Applicable Welds", "Parallel Joint Applicable Welds"]:
        assert w in chips_by_label
        assert chips_by_label[w]["bbox"][1] >= 0.58, f"{w} not in right column"


def test_figure_b2_non_overlapping_vertical_hierarchy():
    """Verify Figure B2 subpanels follow strict vertical ordering without bounding box collision."""
    fig = get_figure_data("Figure B2")
    chips = {c["label"]: c for g in fig["groups"] for c in g["chips"]}
    
    butt = chips["Flanged Butt Joint (A)"]
    corner = chips["Flanged Corner Joint (B)"]
    t_joint = chips["Flanged T-Joint (C)"]
    lap = chips["Flanged Lap Joint (D)"]
    parallel = chips["Flanged Parallel Joint (E)"]
    
    # Butt Joint (A) is completely above Corner (B) and T-Joint (C)
    assert butt["bbox"][2] <= corner["bbox"][0] + 0.05
    assert butt["bbox"][2] <= t_joint["bbox"][0] + 0.05
    
    # Corner (B) and T-Joint (C) are horizontal siblings (left vs right)
    assert corner["bbox"][3] <= t_joint["bbox"][1] + 0.05
    
    # Lap Joint (D) is below B and C
    assert lap["bbox"][0] >= corner["bbox"][2] - 0.05
    assert lap["bbox"][0] >= t_joint["bbox"][2] - 0.05
    
    # Parallel Joint (E) is below D
    assert parallel["bbox"][0] >= lap["bbox"][2] - 0.05


def test_figure_b40_correct_vertical_flame_stacking():
    """Verify Figure B40 flame types strictly follow AWS A3.0 vertical stack ordering."""
    fig = get_figure_data("Figure B40")
    chips = {c["label"]: c for g in fig["groups"] for c in g["chips"]}
    
    neutral = chips["Neutral Flame"]
    oxidizing = chips["Oxidizing Flame"]
    carburizing = chips["Carburizing (Reducing) Flame"]
    feather = chips["Acetylene Feather"]
    
    # Stack order: Neutral (B) -> Oxidizing (C) -> Carburizing (D)
    assert neutral["bbox"][0] < oxidizing["bbox"][0], "Neutral must be above Oxidizing"
    assert oxidizing["bbox"][0] < carburizing["bbox"][0], "Oxidizing must be above Carburizing"
    
    # Acetylene Feather is inside the Carburizing Flame boundary
    assert carburizing["bbox"][0] <= feather["bbox"][0] <= carburizing["bbox"][2]
    assert carburizing["bbox"][1] <= feather["bbox"][1] <= carburizing["bbox"][3]


def test_figure_b25_throat_and_convexity_positions():
    """Verify Figure B25 convexity is in the convex panel and throats match standard dimensions."""
    fig = get_figure_data("Figure B25")
    chips = {c["label"]: c for g in fig["groups"] for c in g["chips"]}
    
    convexity = chips["Convexity"]
    theor = chips["Theoretical Throat"]
    actual = chips["Actual Throat"]
    
    # Convexity is at the top convex fillet weld panel (ymin < 0.20)
    assert convexity["bbox"][0] < 0.20
    assert convexity["bbox"][1] > 0.50  # upper right callout
    
    # Theoretical throat is below actual throat
    assert theor["bbox"][0] > actual["bbox"][0]


def test_nlq_query_asset_and_bbox_resolution():
    """Verify natural language queries resolve figures with enriched bounding boxes."""
    from src.query import resolve_multimodal_assets
    
    test_queries = [
        ("What are the 5 basic joint types illustrated in Figure B1?", "Figure B1"),
        ("Show me the flanged joints in Figure B2", "Figure B2"),
        ("What is the difference between actual throat and theoretical throat on Figure B25?", "Figure B25"),
        ("Explain the three flame types on Figure B40", "Figure B40"),
        ("What are the advancing side and tool shoulder on Figure B46?", "Figure B46")
    ]
    
    for query_text, expected_fig in test_queries:
        resolved_figures, _ = resolve_multimodal_assets(query_text)
        fig_ids = [f["figure_id"] for f in resolved_figures]
        assert expected_fig in fig_ids, f"NLQ failed to resolve {expected_fig} from '{query_text}'"
        
        # Verify bounding box enrichment for resolved figure
        fig_data = get_figure_data(expected_fig)
        assert len(fig_data["groups"]) > 0
        for g in fig_data["groups"]:
            for c in g["chips"]:
                assert "bbox" in c and len(c["bbox"]) == 4
                assert "center" in c and len(c["center"]) == 2
                assert c["bbox"][0] < c["bbox"][2]
                assert c["bbox"][1] < c["bbox"][3]

