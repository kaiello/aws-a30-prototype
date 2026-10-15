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



@pytest.fixture
def isolated_bbox_registry(monkeypatch):
    """Substitute only synthetic geometry; source/figure registries stay real."""
    import src.figure_inspectors as inspectors

    key = "Figure B1"
    label = FIGURE_INSPECTORS[key]["groups"][0]["chips"][0]["label"]
    baseline = get_figure_data(key)

    def install(records):
        registry = {key: {"figure_id": key, "groups": [{"chips": records}]}}
        monkeypatch.setattr(inspectors, "_BBOX_MANIFEST", registry)
        return registry

    return key, label, baseline, install


def _synthetic_geometry(label, bbox, center=None):
    return {"label": label, "bbox": bbox, "center": center, "panel": "A"}


@pytest.mark.parametrize("bbox", [
    None, [], [0, 0, 1], [0, 0, 1, 1, 1], (0, 0, 1, 1),
    "0011", {"ymin": 0, "xmin": 0, "ymax": 1, "xmax": 1},
    [False, 0, 1, 1], [0, "0", 1, 1], [0, None, 1, 1],
    [float("nan"), 0, 1, 1], [0, 0, float("inf"), 1],
    [0, float("-inf"), 1, 1], [.7, .2, .1, .8], [.1, .8, .7, .2],
    [.2, .2, .2, .8], [.1, .5, .7, .5], [-.01, .2, .7, .8],
    [.1, .2, 1.01, .8], [100, 200, 600, 800],
], ids=[
    "none", "empty", "short", "long", "tuple", "string", "mapping",
    "bool", "numeric-string", "null-coordinate", "nan", "positive-infinity",
    "negative-infinity", "reversed-y", "reversed-x", "zero-height", "zero-width",
    "negative", "above-one", "wrong-scale",
])
def test_invalid_geometry_suppresses_focus_without_losing_figure_data(isolated_bbox_registry, bbox):
    key, label, baseline, install = isolated_bbox_registry
    registry = install([_synthetic_geometry(label, bbox, [.4, .5])])
    original = json.dumps(registry, sort_keys=True)

    data = get_figure_data(key)
    chip = data["groups"][0]["chips"][0]
    assert chip["bbox"] is None
    assert chip["center"] is None
    assert chip["panel"] == "A"
    assert chip["label"] == baseline["groups"][0]["chips"][0]["label"]
    assert chip["query"] == baseline["groups"][0]["chips"][0]["query"]
    for field in ("image_file", "image_files", "source_anchors", "title", "page"):
        assert data[field] == baseline[field]
    assert get_figure_bboxes("B1")["groups"][0]["chips"][0]["bbox"] is None
    assert "chip-focus-btn" not in get_inspector_html(key)
    catalog_item = next(item for item in get_all_figures_catalog() if item["id"] == key)
    assert catalog_item["groups"][0]["chips"][0]["bbox"] is None
    assert json.dumps(registry, sort_keys=True) == original


@pytest.mark.parametrize("center", [
    None, [], [.35], [.35, .5, .6], (.35, .5),
    [False, .5], [".35", .5], [float("nan"), .5],
    [.35, float("inf")], [.9, .5], [.35, .9],
], ids=["missing", "empty", "short", "long", "tuple", "bool", "string", "nan", "infinity", "outside-y", "outside-x"])
def test_valid_box_derives_midpoint_for_invalid_center(isolated_bbox_registry, center):
    key, label, _, install = isolated_bbox_registry
    box = [.1, .2, .6, .8]
    registry = install([_synthetic_geometry(label, box, center)])
    original = json.dumps(registry, sort_keys=True)

    data = get_figure_data(key)
    chip = data["groups"][0]["chips"][0]
    assert chip["bbox"] == box
    assert type(chip["bbox"]) is list
    assert chip["center"] == [.35, .5]
    raw_view = get_figure_bboxes(key)["groups"][0]["chips"][0]
    assert raw_view["center"] == [.35, .5]
    assert json.dumps(registry, sort_keys=True) == original


@pytest.mark.parametrize("box,center", [
    ([.1, .2, .6, .8], [.4, .6]),
    ([0, 0, 1, 1], [0, 1]),
])
def test_valid_geometry_preserves_values_axis_order_and_center(isolated_bbox_registry, box, center):
    key, label, _, install = isolated_bbox_registry
    registry = install([_synthetic_geometry(label, box, center)])
    original = json.dumps(registry, sort_keys=True)
    chip = get_figure_data(key)["groups"][0]["chips"][0]
    assert chip["bbox"] == box
    assert type(chip["bbox"]) is list
    assert chip["center"] == center
    assert type(chip["center"]) is list
    assert "chip-focus-btn" in get_inspector_html(key)
    assert json.dumps(registry, sort_keys=True) == original


@pytest.mark.parametrize("second_box", [[.4, .5, .9, .9], [.1, .2, .6, .8]], ids=["different", "identical"])
def test_duplicate_spatial_labels_are_ambiguous_not_last_writer(isolated_bbox_registry, second_box):
    key, label, baseline, install = isolated_bbox_registry
    registry = install([
        _synthetic_geometry(label, [.1, .2, .6, .8], [.35, .5]),
        _synthetic_geometry(label, second_box, [.5, .7]),
    ])
    original = json.dumps(registry, sort_keys=True)
    chip = get_figure_data(key)["groups"][0]["chips"][0]
    assert chip["bbox"] is None
    assert chip["center"] is None
    assert chip["query"] == baseline["groups"][0]["chips"][0]["query"]
    for record in get_figure_bboxes(key)["groups"][0]["chips"]:
        assert record["bbox"] is None
        assert record["center"] is None
    assert json.dumps(registry, sort_keys=True) == original


def test_absent_geometry_and_unknown_figure_contracts_remain_compatible(monkeypatch):
    import src.figure_inspectors as inspectors

    monkeypatch.setattr(inspectors, "_BBOX_MANIFEST", {})
    assert get_figure_bboxes("B1") is None
    chip = get_figure_data("B1")["groups"][0]["chips"][0]
    assert "bbox" not in chip and "center" not in chip
    assert get_figure_bboxes("B120") is None
    assert get_figure_data("B120") == {}
    assert get_inspector_html("B120") == ""
