"""Declarative specifications for remaining Annex B figures (Figures B7–B43, B46–B48, B52).

Source: AWS A3.0M/A3.0:2020.
Covers all multi-page continuations, embedded tables, and Clause 4 cross-references.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from src.evidence_annex_b_specs import SpatialCalloutSpec, SubPanelSpec


# ---------------------------------------------------------------------------
# Figure B7: Edge Shapes
# ---------------------------------------------------------------------------
FIGURE_B7_SPEC = SpatialCalloutSpec(
    figure_id="Figure B7",
    official_title="Edge Shapes",
    short_title="Edge Shapes",
    pages=[(102, 90)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Square Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_A",
            expected_callouts=["Square Edge Shape"],
        ),
        SubPanelSpec(
            letter="B",
            name="Single-Bevel Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_B",
            expected_callouts=["Single-Bevel Edge Shape"],
        ),
        SubPanelSpec(
            letter="C",
            name="Double-Bevel Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_C",
            expected_callouts=["Double-Bevel Edge Shape"],
        ),
        SubPanelSpec(
            letter="D",
            name="Single-J Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_D",
            expected_callouts=["Single-J Edge Shape"],
        ),
        SubPanelSpec(
            letter="E",
            name="Double-J Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_E",
            expected_callouts=["Double-J Edge Shape"],
        ),
        SubPanelSpec(
            letter="F",
            name="Flanged Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_F",
            expected_callouts=["Flanged Edge Shape"],
        ),
        SubPanelSpec(
            letter="G",
            name="Round Edge Shape",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_G",
            expected_callouts=["Round Edge Shape"],
        ),
    ],
    callout_vocabulary=[
        "Edge Shapes", "Square Edge Shape", "Single-Bevel Edge Shape", "Double-Bevel Edge Shape",
        "Single-J Edge Shape", "Double-J Edge Shape", "Flanged Edge Shape", "Round Edge Shape",
        "Applicable Weld Types", "Square-Groove", "Single-Bevel-Groove", "Double-Bevel-Groove",
        "Single-J-Groove", "Double-J-Groove", "Single-V-Groove", "Double-V-Groove",
        "Single-U-Groove", "Double-U-Groove", "Single-Flare-Bevel-Groove", "Double-Flare-Bevel-Groove",
        "Single-Flare-V-Groove", "Double-Flare-V-Groove", "Braze", "Edge", "Fillet", "Seam", "Projection",
    ],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping of edge shapes to applicable weld types.",
    ],
    source_anomalies=[],
    clause4_terms=["J-edge shape", "bevel", "bevel edge shape", "double-J edge shape", "double-bevel edge shape", "edge shape", "flanged edge shape", "round edge shape", "single-J edge shape", "single-bevel edge shape", "square edge shape", "weld type"],
)

# ---------------------------------------------------------------------------
# Figure B8: Single-Groove Weld Types
# ---------------------------------------------------------------------------
FIGURE_B8_SPEC = SpatialCalloutSpec(
    figure_id="Figure B8",
    official_title="Single-Groove Weld Types",
    short_title="Single-Groove Weld Types",
    pages=[(103, 91), (104, 92), (105, 93)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Square-Groove Weld",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_A",
            expected_callouts=["Square-Groove Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Single-V-Groove Weld",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_B",
            expected_callouts=["Single-V-Groove Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="Single-Bevel-Groove Weld",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_C",
            expected_callouts=["Single-Bevel-Groove Weld"],
        ),
        SubPanelSpec(
            letter="D",
            name="Single-U-Groove Weld",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_D",
            expected_callouts=["Single-U-Groove Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Single-J-Groove Weld",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_E",
            expected_callouts=["Single-J-Groove Weld"],
        ),
        SubPanelSpec(
            letter="F",
            name="Single-Flare-V-Groove Weld",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_F",
            expected_callouts=["Single-Flare-V-Groove Weld"],
        ),
        SubPanelSpec(
            letter="G",
            name="Single-Flare-Bevel-Groove Weld",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_G",
            expected_callouts=["Single-Flare-Bevel-Groove Weld"],
        ),
        SubPanelSpec(
            letter="H",
            name="Scarf-Groove Weld",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_H",
            expected_callouts=["Scarf-Groove Weld"],
        ),
        SubPanelSpec(
            letter="I",
            name="Single-Groove Weld with Backing",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_I",
            expected_callouts=["Single-Groove Weld with Backing"],
        ),
    ],
    callout_vocabulary=[
        "Single-Groove Weld Types", "Square-Groove Weld", "Single-V-Groove Weld",
        "Single-Bevel-Groove Weld", "Single-U-Groove Weld", "Single-J-Groove Weld",
        "Single-Flare-V-Groove Weld", "Single-Flare-Bevel-Groove Weld", "Scarf-Groove Weld", "Backing",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 91, 92, and 93 (PDF indices 103..105).",
    ],
    source_anomalies=[],
    clause4_terms=["backing", "groove weld", "scarf groove", "single-bevel-groove weld", "single-flare-bevel-groove weld", "single-flare-V-groove weld", "single-J-groove weld", "single-U-groove weld", "single-V-groove weld", "square-groove weld"],
)

# ---------------------------------------------------------------------------
# Figure B9: Double-Groove Weld Types
# ---------------------------------------------------------------------------
FIGURE_B9_SPEC = SpatialCalloutSpec(
    figure_id="Figure B9",
    official_title="Double-Groove Weld Types",
    short_title="Double-Groove Weld Types",
    pages=[(106, 94), (107, 95)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Double-V-Groove Weld",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_A",
            expected_callouts=["Double-V-Groove Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Double-Bevel-Groove Weld",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_B",
            expected_callouts=["Double-Bevel-Groove Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="Double-U-Groove Weld",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_C",
            expected_callouts=["Double-U-Groove Weld"],
        ),
        SubPanelSpec(
            letter="D",
            name="Double-J-Groove Weld",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_D",
            expected_callouts=["Double-J-Groove Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Double-Flare-V-Groove Weld",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_E",
            expected_callouts=["Double-Flare-V-Groove Weld"],
        ),
        SubPanelSpec(
            letter="F",
            name="Double-Flare-Bevel-Groove Weld",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_F",
            expected_callouts=["Double-Flare-Bevel-Groove Weld"],
        ),
        SubPanelSpec(
            letter="G",
            name="Symmetrical Double-Groove Weld",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_G",
            expected_callouts=["Symmetrical Double-Groove Weld"],
        ),
    ],
    callout_vocabulary=[
        "Double-Groove Weld Types", "Double-V-Groove Weld", "Double-Bevel-Groove Weld",
        "Double-U-Groove Weld", "Double-J-Groove Weld", "Double-Flare-V-Groove Weld",
        "Double-Flare-Bevel-Groove Weld", "Symmetrical Double-Groove Weld",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 94 and 95 (PDF indices 106..107).",
    ],
    source_anomalies=[],
    clause4_terms=["double-bevel-groove weld", "double-flare-bevel-groove weld", "double-flare-V-groove weld", "double-groove weld", "double-J-groove weld", "double-U-groove weld", "double-V-groove weld"],
)

# ---------------------------------------------------------------------------
# Figure B10: Welds in Flanged Joints
# ---------------------------------------------------------------------------
FIGURE_B10_SPEC = SpatialCalloutSpec(
    figure_id="Figure B10",
    official_title="Welds in Flanged Joints",
    short_title="Welds in Flanged Joints",
    pages=[(108, 96)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Flanged Butt Joint Weld",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_A",
            expected_callouts=["Flanged Butt Joint Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Flanged Corner Joint Weld",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_B",
            expected_callouts=["Flanged Corner Joint Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="Flanged T-Joint Weld",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_C",
            expected_callouts=["Flanged T-Joint Weld"],
        ),
        SubPanelSpec(
            letter="D",
            name="Flanged Lap Joint Weld",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_D",
            expected_callouts=["Flanged Lap Joint Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Flanged Edge Joint Weld",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_E",
            expected_callouts=["Flanged Edge Joint Weld"],
        ),
        SubPanelSpec(
            letter="F",
            name="Edge Weld in Flanged Joint",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_F",
            expected_callouts=["Edge Weld in Flanged Joint"],
        ),
    ],
    callout_vocabulary=[
        "Welds in Flanged Joints", "Flanged Butt Joint", "Flanged Corner Joint",
        "Flanged T-Joint", "Flanged Lap Joint", "Flanged Edge Joint", "Edge Weld",
    ],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["edge weld", "flanged butt joint", "flanged corner joint", "flanged edge joint", "flanged joint", "flanged lap joint", "flanged T-joint"],
)

# ---------------------------------------------------------------------------
# Figure B11: Butting and Nonbutting Workpiece or Workpieces
# ---------------------------------------------------------------------------
FIGURE_B11_SPEC = SpatialCalloutSpec(
    figure_id="Figure B11",
    official_title="Butting and Nonbutting Workpiece or Workpieces",
    short_title="Butting and Nonbutting Workpiece or Workpieces",
    pages=[(109, 97)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Butting Workpiece",
            page_number=97,
            pdf_index=109,
            quadrant="PANEL_A",
            expected_callouts=["Butting Workpiece"],
        ),
        SubPanelSpec(
            letter="B",
            name="Nonbutting Workpiece",
            page_number=97,
            pdf_index=109,
            quadrant="PANEL_B",
            expected_callouts=["Nonbutting Workpiece"],
        ),
    ],
    callout_vocabulary=["Butting Workpiece", "Nonbutting Workpiece", "Workpiece"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["butting workpiece", "nonbutting workpiece", "workpiece"],
)

# ---------------------------------------------------------------------------
# Figure B12: End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab
# ---------------------------------------------------------------------------
FIGURE_B12_SPEC = SpatialCalloutSpec(
    figure_id="Figure B12",
    official_title="End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab",
    short_title="End Dam",
    pages=[(110, 98)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="End Dam",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_A",
            expected_callouts=["END DAM", "SECTION A-A"],
        ),
        SubPanelSpec(
            letter="B",
            name="Shelf Bar",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_B",
            expected_callouts=["SHELF BAR"],
        ),
        SubPanelSpec(
            letter="C",
            name="Split Back Piping",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_C",
            expected_callouts=["SPLIT PIPE BACKING", "REINFORCING BAR"],
        ),
        SubPanelSpec(
            letter="D",
            name="Sump",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_D",
            expected_callouts=["SUMP"],
        ),
        SubPanelSpec(
            letter="E",
            name="Runoff Weld Tab, Starting Weld Tab",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_E",
            expected_callouts=["EGW OR ESW WORKPIECES"],
        ),
    ],
    callout_vocabulary=[
        "END DAM", "SHELF BAR", "SPLIT BACK PIPING", "SPLIT PIPE BACKING",
        "REINFORCING BAR", "SUMP", "RUNOFF WELD TAB, STARTING WELD TAB",
        "EGW OR ESW WORKPIECES", "SECTION A-A",
    ],
    has_embedded_table=False,
    notes=[
        "Contains auxiliary electroslag and electrogas welding apparatus components.",
    ],
    source_anomalies=[],
    clause4_terms=["end dam", "runoff weld tab", "shelf bar", "starting weld tab"],
)

# ---------------------------------------------------------------------------
# Figure B13: Edge Weld, Scarf Groove, Joint Mismatch, Root Face Extension, Consumable Insert
# ---------------------------------------------------------------------------
FIGURE_B13_SPEC = SpatialCalloutSpec(
    figure_id="Figure B13",
    official_title="Edge Weld, Scarf Groove, Joint Mismatch, Root Face Extension, Consumable Insert",
    short_title="Edge Weld",
    pages=[(111, 99)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Edge Weld",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_A",
            expected_callouts=["Edge Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Scarf Groove",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_B",
            expected_callouts=["Scarf Groove"],
        ),
        SubPanelSpec(
            letter="C",
            name="Joint Mismatch",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_C",
            expected_callouts=["Joint Mismatch"],
        ),
        SubPanelSpec(
            letter="D",
            name="Root Face Extension",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_D",
            expected_callouts=["Root Face Extension"],
        ),
        SubPanelSpec(
            letter="E",
            name="Consumable Insert",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_E",
            expected_callouts=["Consumable Insert"],
        ),
    ],
    callout_vocabulary=["Edge Weld", "Scarf Groove", "Joint Mismatch", "Root Face Extension", "Consumable Insert"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["consumable insert", "edge weld", "joint mismatch", "root face extension", "scarf groove"],
)

# ---------------------------------------------------------------------------
# Figure B14: Seam and Spot Weld Types
# ---------------------------------------------------------------------------
FIGURE_B14_SPEC = SpatialCalloutSpec(
    figure_id="Figure B14",
    official_title="Seam and Spot Weld Types",
    short_title="Seam and Spot Weld Types",
    pages=[(112, 100)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Arc Seam Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_A",
            expected_callouts=["Arc Seam Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Arc Spot Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_B",
            expected_callouts=["Arc Spot Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="High-Energy Beam Seam Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_C",
            expected_callouts=["HIGH-ENERGY BEAM SEAM WELD"],
        ),
        SubPanelSpec(
            letter="D",
            name="Resistance Seam Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_D",
            expected_callouts=["Resistance Seam Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Resistance Spot Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_E",
            expected_callouts=["Resistance Spot Weld"],
        ),
        SubPanelSpec(
            letter="F",
            name="Friction Stir Seam Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_F",
            expected_callouts=["Friction Stir Seam Weld"],
        ),
        SubPanelSpec(
            letter="G",
            name="Projection Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_G",
            expected_callouts=["Projection Weld"],
        ),
        SubPanelSpec(
            letter="H",
            name="High-Energy Beam Spot Weld",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_H",
            expected_callouts=["HIGH-ENERGY BEAM SPOT WELD"],
        ),
    ],
    callout_vocabulary=[
        "Seam and Spot Weld Types", "HIGH-ENERGY BEAM SEAM WELD", "HIGH-ENERGY BEAM SPOT WELD",
        "Resistance Seam Weld", "Resistance Spot Weld", "Arc Seam Weld", "Arc Spot Weld", "Projection Weld",
    ],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["arc seam weld", "arc spot weld", "friction stir seam weld", "high-energy beam seam weld", "high-energy beam spot weld", "projection weld", "resistance seam weld", "resistance spot weld", "seam weld", "spot weld"],
)

# ---------------------------------------------------------------------------
# Figure B15: Various Weld Types
# ---------------------------------------------------------------------------
FIGURE_B15_SPEC = SpatialCalloutSpec(
    figure_id="Figure B15",
    official_title="Various Weld Types",
    short_title="Various Weld Types",
    pages=[(113, 101)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Upset Weld",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_A",
            expected_callouts=["Upset Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Flash Weld",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_B",
            expected_callouts=["Flash Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="Surfacing Weld",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_C",
            expected_callouts=["Surfacing Weld"],
        ),
        SubPanelSpec(
            letter="D",
            name="Slot Weld",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_D",
            expected_callouts=["Slot Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Plug Weld",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_E",
            expected_callouts=["Plug Weld"],
        ),
    ],
    callout_vocabulary=["Various Weld Types", "Upset Weld", "Flash Weld", "Surfacing Weld", "Slot Weld", "Plug Weld"],
    has_embedded_table=False,
    notes=[
        "Illustrates plug weld (E), slot weld (D), surfacing weld (C), flash weld (B), and upset weld (A).",
    ],
    source_anomalies=[],
    clause4_terms=["flash weld", "plug weld", "slot weld", "surfacing weld", "upset weld"],
)

# ---------------------------------------------------------------------------
# Figure B16A: Welding Position Diagram for Groove Welds and Surfacing Welds in Plate
# ---------------------------------------------------------------------------
FIGURE_B16A_SPEC = SpatialCalloutSpec(
    figure_id="Figure B16A",
    official_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Plate",
    short_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Plate",
    pages=[(114, 102)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Flat Position",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_A",
            expected_callouts=["Flat", "A"],
        ),
        SubPanelSpec(
            letter="B",
            name="Horizontal Position",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_B",
            expected_callouts=["Horizontal", "B"],
        ),
        SubPanelSpec(
            letter="C",
            name="Overhead Position",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_C",
            expected_callouts=["Overhead", "C"],
        ),
        SubPanelSpec(
            letter="D",
            name="Vertical Position",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_D",
            expected_callouts=["Vertical", "D"],
        ),
        SubPanelSpec(
            letter="E",
            name="Vertical Position (80° to 90°)",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_E",
            expected_callouts=["Vertical", "E"],
        ),
    ],
    callout_vocabulary=[
        "Flat", "Horizontal", "Overhead", "Vertical", "Diagram Reference",
        "Inclination of Axis", "Rotation of Face", "Tabulation of Positions of Groove Welds and Surfacing Welds",
    ],
    has_embedded_table=True,
    notes=[
        "Contains embedded position tabulation table mapping positions A..E to inclination and rotation angles.",
    ],
    source_anomalies=[],
    clause4_terms=["flat welding position", "horizontal welding position", "inclination of axis", "overhead welding position", "rotation of face", "vertical welding position", "welding position"],
)

# ---------------------------------------------------------------------------
# Figure B16B: Welding Position Diagram for Fillet Welds in Plate
# ---------------------------------------------------------------------------
FIGURE_B16B_SPEC = SpatialCalloutSpec(
    figure_id="Figure B16B",
    official_title="Welding Position Diagram for Fillet Welds in Plate",
    short_title="Welding Position Diagram for Fillet Welds in Plate",
    pages=[(115, 103)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Flat Position",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_A",
            expected_callouts=["Flat", "A"],
        ),
        SubPanelSpec(
            letter="B",
            name="Horizontal Position",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_B",
            expected_callouts=["Horizontal", "B"],
        ),
        SubPanelSpec(
            letter="C",
            name="Overhead Position",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_C",
            expected_callouts=["Overhead", "C"],
        ),
        SubPanelSpec(
            letter="D",
            name="Vertical Position",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_D",
            expected_callouts=["Vertical", "D"],
        ),
        SubPanelSpec(
            letter="E",
            name="Vertical Position (80° to 90°)",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_E",
            expected_callouts=["Vertical", "E"],
        ),
    ],
    callout_vocabulary=[
        "Flat", "Horizontal", "Overhead", "Vertical", "Diagram Reference",
        "Inclination of Axis", "Rotation of Face", "Tabulation of Positions of Fillet Welds",
    ],
    has_embedded_table=True,
    notes=[
        "Contains embedded position tabulation table for fillet welds in plate.",
    ],
    source_anomalies=[],
    clause4_terms=["flat welding position", "horizontal welding position", "overhead welding position", "vertical welding position"],
)

# ---------------------------------------------------------------------------
# Figure B16C: Welding Position Diagram for Groove Welds and Surfacing Welds in Pipe
# ---------------------------------------------------------------------------
FIGURE_B16C_SPEC = SpatialCalloutSpec(
    figure_id="Figure B16C",
    official_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Pipe",
    short_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Pipe",
    pages=[(116, 104)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Circumferential Groove and Surfacing Welds in Pipe",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_A",
            expected_callouts=["Circumferential Groove and Surfacing Welds"],
        ),
    ],
    callout_vocabulary=[
        "POSITIONS FOR CIRCUMFERENTIAL GROOVE", "AND SURFACING WELDS INDICATED BY SHADED",
        "AREAS FOR PIPE WITH AXIS VARYING FROM", "HORIZONTAL (0°) TO VERTICAL (90°)",
        "Circumferential Groove and Surfacing Welds",
    ],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["welding position"],
)

# ---------------------------------------------------------------------------
# Figure B17: Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Plate
# ---------------------------------------------------------------------------
FIGURE_B17_SPEC = SpatialCalloutSpec(
    figure_id="Figure B17",
    official_title="Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Plate",
    short_title="Welding Test Positions",
    pages=[(117, 105)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="1G Flat",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_A",
            expected_callouts=["1G"],
        ),
        SubPanelSpec(
            letter="B",
            name="2G Horizontal",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_B",
            expected_callouts=["2G"],
        ),
        SubPanelSpec(
            letter="C",
            name="3G Vertical",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_C",
            expected_callouts=["3G"],
        ),
        SubPanelSpec(
            letter="D",
            name="4G Overhead",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_D",
            expected_callouts=["4G"],
        ),
    ],
    callout_vocabulary=["1G", "2G", "3G", "4G", "Flat", "Horizontal", "Vertical", "Overhead"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["1G", "2G", "3G", "4G", "welding test position"],
)

# ---------------------------------------------------------------------------
# Figure B18: Welding Test Positions and Their Designations for Fillet Welds in Plate
# ---------------------------------------------------------------------------
FIGURE_B18_SPEC = SpatialCalloutSpec(
    figure_id="Figure B18",
    official_title="Welding Test Positions and Their Designations for Fillet Welds in Plate",
    short_title="Welding Test Positions",
    pages=[(118, 106), (119, 107)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="1F Flat",
            page_number=106,
            pdf_index=118,
            quadrant="PANEL_A",
            expected_callouts=["1F"],
        ),
        SubPanelSpec(
            letter="B",
            name="2F Horizontal",
            page_number=106,
            pdf_index=118,
            quadrant="PANEL_B",
            expected_callouts=["2F"],
        ),
        SubPanelSpec(
            letter="C",
            name="3F Vertical",
            page_number=107,
            pdf_index=119,
            quadrant="PANEL_C",
            expected_callouts=["3F"],
        ),
        SubPanelSpec(
            letter="D",
            name="4F Overhead",
            page_number=107,
            pdf_index=119,
            quadrant="PANEL_D",
            expected_callouts=["4F"],
        ),
    ],
    callout_vocabulary=["1F", "2F", "3F", "4F", "Flat", "Horizontal", "Vertical", "Overhead"],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 106 and 107 (PDF indices 118..119).",
    ],
    source_anomalies=[],
    clause4_terms=["1F", "2F", "3F", "4F", "welding test position"],
)

# ---------------------------------------------------------------------------
# Figure B19: Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Pipe
# ---------------------------------------------------------------------------
FIGURE_B19_SPEC = SpatialCalloutSpec(
    figure_id="Figure B19",
    official_title="Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Pipe",
    short_title="Welding Test Positions",
    pages=[(120, 108), (121, 109)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="1G Rotated",
            page_number=108,
            pdf_index=120,
            quadrant="PANEL_A",
            expected_callouts=["1G"],
        ),
        SubPanelSpec(
            letter="B",
            name="2G Fixed Horizontal",
            page_number=108,
            pdf_index=120,
            quadrant="PANEL_B",
            expected_callouts=["2G"],
        ),
        SubPanelSpec(
            letter="C",
            name="5G Fixed Vertical",
            page_number=109,
            pdf_index=121,
            quadrant="PANEL_C",
            expected_callouts=["5G"],
        ),
        SubPanelSpec(
            letter="D",
            name="6G Inclined",
            page_number=109,
            pdf_index=121,
            quadrant="PANEL_D",
            expected_callouts=["6G"],
        ),
        SubPanelSpec(
            letter="E",
            name="6GR Inclined with Restriction Ring",
            page_number=109,
            pdf_index=121,
            quadrant="PANEL_E",
            expected_callouts=["6GR"],
        ),
    ],
    callout_vocabulary=["1G", "2G", "5G", "6G", "6GR", "Rotated", "Fixed Horizontal", "Fixed Vertical", "Inclined"],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 108 and 109 (PDF indices 120..121).",
    ],
    source_anomalies=[],
    clause4_terms=["1G", "2G", "5G", "6G", "6GR", "welding test position"],
)

# ---------------------------------------------------------------------------
# Figure B20: Welding Test Positions and Their Designations for Fillet Welds in Pipe
# ---------------------------------------------------------------------------
FIGURE_B20_SPEC = SpatialCalloutSpec(
    figure_id="Figure B20",
    official_title="Welding Test Positions and Their Designations for Fillet Welds in Pipe",
    short_title="Welding Test Positions",
    pages=[(122, 110), (123, 111)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="1F Rotated",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_A",
            expected_callouts=["1F"],
        ),
        SubPanelSpec(
            letter="B",
            name="2F Fixed Horizontal",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_B",
            expected_callouts=["2F"],
        ),
        SubPanelSpec(
            letter="C",
            name="2FR Rotated",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_C",
            expected_callouts=["2FR"],
        ),
        SubPanelSpec(
            letter="D",
            name="4F Fixed Overhead",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_D",
            expected_callouts=["4F"],
        ),
        SubPanelSpec(
            letter="E",
            name="4F Alternative",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_E",
            expected_callouts=["4F"],
        ),
        SubPanelSpec(
            letter="F",
            name="5F Fixed Vertical",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_F",
            expected_callouts=["5F"],
        ),
        SubPanelSpec(
            letter="G",
            name="6F Inclined",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_G",
            expected_callouts=["6F"],
        ),
    ],
    callout_vocabulary=["1F", "2F", "2FR", "4F", "5F", "6F", "Rotated", "Fixed Horizontal", "Fixed Overhead", "Fixed Vertical", "Inclined"],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 110 and 111 (PDF indices 122..123).",
    ],
    source_anomalies=[],
    clause4_terms=["1F", "2F", "2FR", "4F", "5F", "6F", "welding test position"],
)

# ---------------------------------------------------------------------------
# Figure B21: Position of Beam, Filler Material, Gun, or Torch
# ---------------------------------------------------------------------------
FIGURE_B21_SPEC = SpatialCalloutSpec(
    figure_id="Figure B21",
    official_title="Position of Beam, Filler Material, Gun, or Torch",
    short_title="Position of Beam",
    pages=[(124, 112)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Travel Angle (Groove Weld)",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_A",
            expected_callouts=["Travel Angle"],
        ),
        SubPanelSpec(
            letter="B",
            name="Work Angle (Fillet Weld)",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_B",
            expected_callouts=["Work Angle"],
        ),
        SubPanelSpec(
            letter="C",
            name="Pipe Weld",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_C",
            expected_callouts=["PIPE WELD"],
        ),
        SubPanelSpec(
            letter="D",
            name="Push Angle and Drag Angle",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_D",
            expected_callouts=["Push Angle", "Drag Angle"],
        ),
    ],
    callout_vocabulary=["Travel Angle", "Work Angle", "PIPE WELD", "Push Angle", "Drag Angle", "Lead Angle", "Progression of Welding"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["backhand welding", "drag angle", "forehand welding", "lead angle", "push angle", "travel angle", "work angle"],
)

# ---------------------------------------------------------------------------
# Figure B22: Weld Bead Types
# ---------------------------------------------------------------------------
FIGURE_B22_SPEC = SpatialCalloutSpec(
    figure_id="Figure B22",
    official_title="Weld Bead Types",
    short_title="Weld Bead Types",
    pages=[(125, 113)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Stringer Bead",
            page_number=113,
            pdf_index=125,
            quadrant="PANEL_A",
            expected_callouts=["Stringer Bead"],
        ),
        SubPanelSpec(
            letter="B",
            name="Weave Bead",
            page_number=113,
            pdf_index=125,
            quadrant="PANEL_B",
            expected_callouts=["Weave Bead"],
        ),
    ],
    callout_vocabulary=["Stringer Bead", "Weave Bead", "Weld Bead"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["stringer bead", "weave bead", "weld bead"],
)

# ---------------------------------------------------------------------------
# Figure B23: Welding Application Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B23_SPEC = SpatialCalloutSpec(
    figure_id="Figure B23",
    official_title="Welding Application Nomenclature",
    short_title="Welding Application Nomenclature",
    pages=[(126, 114), (127, 115), (128, 116)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Single-Pass Weld",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_A",
            expected_callouts=["Single-Pass Weld"],
        ),
        SubPanelSpec(
            letter="B",
            name="Multipass Weld",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_B",
            expected_callouts=["Multipass Weld"],
        ),
        SubPanelSpec(
            letter="C",
            name="Weld Layer",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_C",
            expected_callouts=["Weld Layer"],
        ),
        SubPanelSpec(
            letter="D",
            name="Root Pass",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_D",
            expected_callouts=["Root Pass"],
        ),
        SubPanelSpec(
            letter="E",
            name="Hot Pass",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_E",
            expected_callouts=["Hot Pass"],
        ),
        SubPanelSpec(
            letter="F",
            name="Fill Pass",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_F",
            expected_callouts=["Fill Pass"],
        ),
        SubPanelSpec(
            letter="G",
            name="Cap Pass",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_G",
            expected_callouts=["Cap Pass"],
        ),
        SubPanelSpec(
            letter="H",
            name="Backing Weld",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_H",
            expected_callouts=["Backing Weld"],
        ),
        SubPanelSpec(
            letter="I",
            name="Back Weld",
            page_number=116,
            pdf_index=128,
            quadrant="PANEL_I",
            expected_callouts=["Back Weld"],
        ),
        SubPanelSpec(
            letter="J",
            name="Weld Sequence",
            page_number=116,
            pdf_index=128,
            quadrant="PANEL_J",
            expected_callouts=["Weld Sequence"],
        ),
    ],
    callout_vocabulary=[
        "Single-Pass Weld", "Multipass Weld", "Weld Layer", "Root Pass",
        "Hot Pass", "Fill Pass", "Cap Pass", "Backing Weld", "Back Weld", "Weld Sequence",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 114, 115, and 116 (PDF indices 126..128).",
    ],
    source_anomalies=[],
    clause4_terms=["back weld", "backing weld", "cap pass", "fill pass", "hot pass", "multipass weld", "root pass", "single-pass weld", "weld layer", "weld pass"],
)

# ---------------------------------------------------------------------------
# Figure B24: Parts of a Weld
# ---------------------------------------------------------------------------
FIGURE_B24_SPEC = SpatialCalloutSpec(
    figure_id="Figure B24",
    official_title="Parts of a Weld",
    short_title="Parts of a Weld",
    pages=[(129, 117), (130, 118), (131, 119), (132, 120), (133, 121), (134, 122)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Face Reinforcement",
            page_number=117,
            pdf_index=129,
            quadrant="PANEL_A",
            expected_callouts=["Face Reinforcement"],
        ),
        SubPanelSpec(
            letter="B",
            name="Root Reinforcement",
            page_number=117,
            pdf_index=129,
            quadrant="PANEL_B",
            expected_callouts=["Root Reinforcement"],
        ),
        SubPanelSpec(
            letter="C",
            name="Weld Toe",
            page_number=118,
            pdf_index=130,
            quadrant="PANEL_C",
            expected_callouts=["Weld Toe"],
        ),
        SubPanelSpec(
            letter="D",
            name="Weld Root",
            page_number=118,
            pdf_index=130,
            quadrant="PANEL_D",
            expected_callouts=["Weld Root"],
        ),
        SubPanelSpec(
            letter="E",
            name="Weld Face",
            page_number=119,
            pdf_index=131,
            quadrant="PANEL_E",
            expected_callouts=["Weld Face"],
        ),
        SubPanelSpec(
            letter="F",
            name="Toe of Weld",
            page_number=119,
            pdf_index=131,
            quadrant="PANEL_F",
            expected_callouts=["Toe of Weld"],
        ),
        SubPanelSpec(
            letter="G",
            name="Weld Leg",
            page_number=120,
            pdf_index=132,
            quadrant="PANEL_G",
            expected_callouts=["Weld Leg"],
        ),
        SubPanelSpec(
            letter="H",
            name="Weld Throat",
            page_number=120,
            pdf_index=132,
            quadrant="PANEL_H",
            expected_callouts=["Weld Throat"],
        ),
        SubPanelSpec(
            letter="I",
            name="Faying Surface",
            page_number=121,
            pdf_index=133,
            quadrant="PANEL_I",
            expected_callouts=["Faying Surface"],
        ),
        SubPanelSpec(
            letter="J",
            name="Root Surface",
            page_number=122,
            pdf_index=134,
            quadrant="PANEL_J",
            expected_callouts=["Root Surface"],
        ),
    ],
    callout_vocabulary=[
        "Face Reinforcement", "Root Reinforcement", "Weld Toe", "Weld Root",
        "Weld Face", "Toe of Weld", "Weld Leg", "Weld Throat", "Faying Surface", "Root Surface",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation spanning 6 consecutive pages: printed pages 117–122 (PDF indices 129..134).",
    ],
    source_anomalies=[],
    clause4_terms=["face reinforcement", "faying surface", "root reinforcement", "root surface", "weld face", "weld leg", "weld root", "weld throat", "weld toe"],
)

# ---------------------------------------------------------------------------
# Figure B25: Weld Sizes
# ---------------------------------------------------------------------------
FIGURE_B25_SPEC = SpatialCalloutSpec(
    figure_id="Figure B25",
    official_title="Weld Sizes",
    short_title="Weld Sizes",
    pages=[(135, 123), (136, 124), (137, 125), (138, 126)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Equal Leg Fillet Weld Size",
            page_number=123,
            pdf_index=135,
            quadrant="PANEL_A",
            expected_callouts=["Fillet Weld Size"],
        ),
        SubPanelSpec(
            letter="B",
            name="Unequal Leg Fillet Weld Size",
            page_number=123,
            pdf_index=135,
            quadrant="PANEL_B",
            expected_callouts=["Fillet Weld Size"],
        ),
        SubPanelSpec(
            letter="C",
            name="Convex Fillet Weld Size",
            page_number=124,
            pdf_index=136,
            quadrant="PANEL_C",
            expected_callouts=["Convex Fillet Weld"],
        ),
        SubPanelSpec(
            letter="D",
            name="Concave Fillet Weld Size",
            page_number=124,
            pdf_index=136,
            quadrant="PANEL_D",
            expected_callouts=["Concave Fillet Weld"],
        ),
        SubPanelSpec(
            letter="E",
            name="Groove Weld Size",
            page_number=124,
            pdf_index=136,
            quadrant="PANEL_E",
            expected_callouts=["Groove Weld Size"],
        ),
        SubPanelSpec(
            letter="F",
            name="Spot Weld Size",
            page_number=125,
            pdf_index=137,
            quadrant="PANEL_F",
            expected_callouts=["Spot Weld Size"],
        ),
        SubPanelSpec(
            letter="G",
            name="Projection Weld Size",
            page_number=125,
            pdf_index=137,
            quadrant="PANEL_G",
            expected_callouts=["Projection Weld Size"],
        ),
        SubPanelSpec(
            letter="H",
            name="Seam Weld Size",
            page_number=126,
            pdf_index=138,
            quadrant="PANEL_H",
            expected_callouts=["Seam Weld Size"],
        ),
        SubPanelSpec(
            letter="I",
            name="Plug Weld Size",
            page_number=126,
            pdf_index=138,
            quadrant="PANEL_I",
            expected_callouts=["Plug Weld Size"],
        ),
    ],
    callout_vocabulary=[
        "Fillet Weld Size", "Groove Weld Size", "Equal Leg Fillet Weld",
        "Unequal Leg Fillet Weld", "Convex Fillet Weld", "Concave Fillet Weld",
        "Spot Weld Size", "Seam Weld Size", "Plug Weld Size",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 123–126 (PDF indices 135..138).",
    ],
    source_anomalies=[],
    clause4_terms=["fillet weld size", "groove weld size", "plug weld size", "seam weld size", "spot weld size", "weld size"],
)

# ---------------------------------------------------------------------------
# Figure B26: Groove Weld Size and Joint Penetration
# ---------------------------------------------------------------------------
FIGURE_B26_SPEC = SpatialCalloutSpec(
    figure_id="Figure B26",
    official_title="Groove Weld Size and Joint Penetration",
    short_title="Groove Weld Size",
    pages=[(139, 127), (140, 128), (141, 129)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Complete Joint Penetration Groove Weld",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_A",
            expected_callouts=["Complete Joint Penetration"],
        ),
        SubPanelSpec(
            letter="B",
            name="Partial Joint Penetration Groove Weld",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_B",
            expected_callouts=["Partial Joint Penetration"],
        ),
        SubPanelSpec(
            letter="C",
            name="Groove Weld Size Equal to Joint Penetration",
            page_number=128,
            pdf_index=140,
            quadrant="PANEL_C",
            expected_callouts=["Joint Penetration"],
        ),
        SubPanelSpec(
            letter="D",
            name="Groove Weld Size Less Than Joint Penetration",
            page_number=128,
            pdf_index=140,
            quadrant="PANEL_D",
            expected_callouts=["Joint Penetration"],
        ),
        SubPanelSpec(
            letter="E",
            name="Groove Weld Size Greater Than Joint Penetration",
            page_number=129,
            pdf_index=141,
            quadrant="PANEL_E",
            expected_callouts=["Joint Penetration"],
        ),
    ],
    callout_vocabulary=["Complete Joint Penetration", "Partial Joint Penetration", "Groove Weld Size", "Joint Penetration"],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 127–129 (PDF indices 139..141).",
    ],
    source_anomalies=[],
    clause4_terms=["complete joint penetration", "groove weld size", "joint penetration", "partial joint penetration"],
)

# ---------------------------------------------------------------------------
# Figure B27: Melt-Through and Root Surface Profile
# ---------------------------------------------------------------------------
FIGURE_B27_SPEC = SpatialCalloutSpec(
    figure_id="Figure B27",
    official_title="Melt-Through and Root Surface Profile",
    short_title="Melt-Through",
    pages=[(142, 130)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Melt-Through Profile",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_A",
            expected_callouts=["Melt-Through"],
        ),
        SubPanelSpec(
            letter="B",
            name="Root Surface Profile",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_B",
            expected_callouts=["Root Surface Profile"],
        ),
        SubPanelSpec(
            letter="C",
            name="Drop-Through",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_C",
            expected_callouts=["Drop-Through"],
        ),
        SubPanelSpec(
            letter="D",
            name="Excessive Melt-Through",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_D",
            expected_callouts=["Excessive Melt-Through"],
        ),
    ],
    callout_vocabulary=["Melt-Through", "Root Surface Profile", "Drop-Through", "Excessive Melt-Through"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["drop-through", "melt-through", "root surface", "root surface profile"],
)

# ---------------------------------------------------------------------------
# Figure B28: Complete Fusion
# ---------------------------------------------------------------------------
FIGURE_B28_SPEC = SpatialCalloutSpec(
    figure_id="Figure B28",
    official_title="Complete Fusion",
    short_title="Complete Fusion",
    pages=[(143, 131)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Complete Fusion",
            page_number=131,
            pdf_index=143,
            quadrant="PANEL_A",
            expected_callouts=["Complete Fusion"],
        ),
    ],
    callout_vocabulary=["Complete Fusion", "Fusion Zone", "Base Metal"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["complete fusion", "fusion zone"],
)

# ---------------------------------------------------------------------------
# Figure B29: Incomplete Fusion
# ---------------------------------------------------------------------------
FIGURE_B29_SPEC = SpatialCalloutSpec(
    figure_id="Figure B29",
    official_title="Incomplete Fusion",
    short_title="Incomplete Fusion",
    pages=[(144, 132)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Incomplete Fusion at Root",
            page_number=132,
            pdf_index=144,
            quadrant="PANEL_A",
            expected_callouts=["Incomplete Fusion at Root"],
        ),
        SubPanelSpec(
            letter="B",
            name="Incomplete Fusion at Side Wall",
            page_number=132,
            pdf_index=144,
            quadrant="PANEL_B",
            expected_callouts=["Incomplete Fusion at Side Wall"],
        ),
        SubPanelSpec(
            letter="C",
            name="Incomplete Interpass Fusion",
            page_number=132,
            pdf_index=144,
            quadrant="PANEL_C",
            expected_callouts=["Incomplete Interpass Fusion"],
        ),
        SubPanelSpec(
            letter="D",
            name="Incomplete Fusion in Fillet Weld",
            page_number=132,
            pdf_index=144,
            quadrant="PANEL_D",
            expected_callouts=["Incomplete Fusion in Fillet Weld"],
        ),
    ],
    callout_vocabulary=["Incomplete Fusion", "Lack of Fusion", "Root", "Side Wall"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["incomplete fusion"],
)

# ---------------------------------------------------------------------------
# Figure B30: Fusion Welds (Transverse Section)
# ---------------------------------------------------------------------------
FIGURE_B30_SPEC = SpatialCalloutSpec(
    figure_id="Figure B30",
    official_title="Fusion Welds (Transverse Section)",
    short_title="Fusion Welds",
    pages=[(145, 133), (146, 134)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Complete Joint Penetration Groove Weld",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_A",
            expected_callouts=["FUSION DEPTH"],
        ),
        SubPanelSpec(
            letter="B",
            name="Partial Joint Penetration Groove Weld",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_B",
            expected_callouts=["FUSION DEPTH"],
        ),
        SubPanelSpec(
            letter="C",
            name="Surfacing Weld",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_C",
            expected_callouts=["FUSION DEPTH"],
        ),
        SubPanelSpec(
            letter="D",
            name="Resistance Seam Weld / Spot Weld Nugget",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_D",
            expected_callouts=["FUSION DEPTH"],
        ),
        SubPanelSpec(
            letter="E",
            name="Seam Weld",
            page_number=134,
            pdf_index=146,
            quadrant="PANEL_E",
            expected_callouts=["Seam Weld"],
        ),
        SubPanelSpec(
            letter="F",
            name="Projection Weld / Cross Wire Weld",
            page_number=134,
            pdf_index=146,
            quadrant="PANEL_F",
            expected_callouts=["Projection Weld"],
        ),
        SubPanelSpec(
            letter="G",
            name="Edge Weld",
            page_number=134,
            pdf_index=146,
            quadrant="PANEL_G",
            expected_callouts=["Edge Weld"],
        ),
    ],
    callout_vocabulary=[
        "FUSION DEPTH", "Fusion Zone", "Complete Joint Penetration",
        "Partial Joint Penetration", "Surfacing Weld", "Resistance Seam Weld", "Spot Weld",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 133 and 134 (PDF indices 145..146).",
        "Note on page 133 specifies: Fusion zones indicated by shading.",
    ],
    source_anomalies=[],
    clause4_terms=["fusion depth", "fusion face", "fusion zone"],
)

# ---------------------------------------------------------------------------
# Figure B31: Joining Without Fusion
# ---------------------------------------------------------------------------
FIGURE_B31_SPEC = SpatialCalloutSpec(
    figure_id="Figure B31",
    official_title="Joining Without Fusion",
    short_title="Joining Without Fusion",
    pages=[(147, 135)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Solid-State Welding Joint",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_A",
            expected_callouts=["Solid-State Welding"],
        ),
        SubPanelSpec(
            letter="B",
            name="Diffusion Welding",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_B",
            expected_callouts=["Diffusion Welding"],
        ),
        SubPanelSpec(
            letter="C",
            name="Explosion Welding",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_C",
            expected_callouts=["Explosion Welding"],
        ),
        SubPanelSpec(
            letter="D",
            name="Ultrasonic Welding",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_D",
            expected_callouts=["Ultrasonic Welding"],
        ),
    ],
    callout_vocabulary=["Solid-State Welding", "Diffusion Welding", "Explosion Welding", "Ultrasonic Welding"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["diffusion welding", "explosion welding", "solid-state welding", "ultrasonic welding"],
)

# ---------------------------------------------------------------------------
# Figure B32: Weld Discontinuities
# ---------------------------------------------------------------------------
FIGURE_B32_SPEC = SpatialCalloutSpec(
    figure_id="Figure B32",
    official_title="Weld Discontinuities",
    short_title="Weld Discontinuities",
    pages=[(148, 136), (149, 137), (150, 138)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Toe Crack",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_A",
            expected_callouts=["Toe Crack"],
        ),
        SubPanelSpec(
            letter="B",
            name="Underbead Crack",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_B",
            expected_callouts=["Underbead Crack"],
        ),
        SubPanelSpec(
            letter="C",
            name="Overlap (Fillet Weld)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_C",
            expected_callouts=["OVERLAP"],
        ),
        SubPanelSpec(
            letter="D",
            name="Overlap (Groove Weld)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_D",
            expected_callouts=["OVERLAP"],
        ),
        SubPanelSpec(
            letter="E",
            name="Underfill (Groove Weld Face and Root Surface)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_E",
            expected_callouts=["UNDERFILL"],
        ),
        SubPanelSpec(
            letter="F",
            name="Underfill (Groove Weld Face)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_F",
            expected_callouts=["UNDERFILL"],
        ),
        SubPanelSpec(
            letter="G",
            name="Underfill (Fillet Weld Face)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_G",
            expected_callouts=["UNDERFILL"],
        ),
        SubPanelSpec(
            letter="H",
            name="Underfill (Edge Weld)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_H",
            expected_callouts=["UNDERFILL"],
        ),
        SubPanelSpec(
            letter="I",
            name="Reentrant Angles at Fillet Weld Toes",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_I",
            expected_callouts=["REENTRANT ANGLES AT FILLET WELD TOES"],
        ),
        SubPanelSpec(
            letter="J",
            name="Reentrant Angle at Weld Bead Toe",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_J",
            expected_callouts=["REENTRANT ANGLE AT WELD BEAD TOE"],
        ),
        SubPanelSpec(
            letter="K",
            name="Reentrant Angles at Groove Weld Face and Root Surface",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_K",
            expected_callouts=["REENTRANT ANGLES AT GROOVE WELD FACE AND ROOT SURFACE"],
        ),
        SubPanelSpec(
            letter="L",
            name="Reentrant Angles at Groove Weld Face",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_L",
            expected_callouts=["REENTRANT ANGLES AT GROOVE WELD FACE"],
        ),
        SubPanelSpec(
            letter="M",
            name="Fillet Weld with Acute and Obtuse Reentrant Angles",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_M",
            expected_callouts=["FILLET WELD WITH ACUTE AND OBTUSE REENTRANT ANGLES"],
        ),
        SubPanelSpec(
            letter="N",
            name="Unfilled Crater",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_N",
            expected_callouts=["UNFILLED CRATER"],
        ),
        SubPanelSpec(
            letter="O",
            name="Burn-Through",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_O",
            expected_callouts=["BURN-THROUGH"],
        ),
    ],
    callout_vocabulary=[
        "UNDERFILL", "OVERLAP", "UNFILLED CRATER", "BURN-THROUGH",
        "TOE REENTRANT ANGLE", "BEAD REENTRANT ANGLE", "OBTUSE TOE REENTRANT ANGLE",
        "ACUTE TOE REENTRANT ANGLE", "SECTION A-A",
    ],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation spanning 3 pages: printed pages 136–138 (PDF indices 148..150).",
    ],
    source_anomalies=[],
    clause4_terms=["burn-through", "discontinuity", "overlap", "reentrant angle", "toe crack", "underbead crack", "underfill", "unfilled crater"],
)

# ---------------------------------------------------------------------------
# Figure B33: Crack Types
# ---------------------------------------------------------------------------
FIGURE_B33_SPEC = SpatialCalloutSpec(
    figure_id="Figure B33",
    official_title="Crack Types",
    short_title="Crack Types",
    pages=[(151, 139)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Cracks in and Adjacent to Welds",
            page_number=139,
            pdf_index=151,
            quadrant="PANEL_A",
            expected_callouts=["Cracks in and Adjacent to Welds"],
        ),
        SubPanelSpec(
            letter="B",
            name="Lamellar Tear",
            page_number=139,
            pdf_index=151,
            quadrant="PANEL_B",
            expected_callouts=["Lamellar Tear"],
        ),
    ],
    callout_vocabulary=[
        "Crater crack", "Face crack", "Heat-affected zone crack", "Lamellar tear",
        "Longitudinal crack", "Root crack", "Root surface crack", "Throat crack",
        "Toe crack", "Transverse crack", "Underbead crack", "Weld interface crack", "Weld metal crack",
    ],
    has_embedded_table=False,
    notes=[
        "Contains numbered key legend 1 through 10/13 of crack types referenced in Clause 4.",
    ],
    source_anomalies=[],
    clause4_terms=["crater crack", "face crack", "heat-affected zone crack", "lamellar tear", "longitudinal crack", "root crack", "root surface crack", "throat crack", "toe crack", "transverse crack", "underbead crack", "weld crack", "weld metal crack"],
)

# ---------------------------------------------------------------------------
# Figure B34: Welding Current Polarity
# ---------------------------------------------------------------------------
FIGURE_B34_SPEC = SpatialCalloutSpec(
    figure_id="Figure B34",
    official_title="Welding Current Polarity",
    short_title="Welding Current Polarity",
    pages=[(152, 140)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Direct Current Electrode Negative (DCEN)",
            page_number=140,
            pdf_index=152,
            quadrant="PANEL_A",
            expected_callouts=["DCEN"],
        ),
        SubPanelSpec(
            letter="B",
            name="Direct Current Electrode Positive (DCEP)",
            page_number=140,
            pdf_index=152,
            quadrant="PANEL_B",
            expected_callouts=["DCEP"],
        ),
    ],
    callout_vocabulary=["DCEN", "DCEP", "Direct Current Electrode Negative", "Direct Current Electrode Positive"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["direct current electrode negative", "direct current electrode positive"],
)

# ---------------------------------------------------------------------------
# Figure B35: Plasma Arc Torch Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B35_SPEC = SpatialCalloutSpec(
    figure_id="Figure B35",
    official_title="Plasma Arc Torch Nomenclature",
    short_title="Plasma Arc Torch Nomenclature",
    pages=[(153, 141)],
    crop_box=(0.05, 0.05, 0.95, 0.50),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Plasma Arc Torch Nomenclature",
            page_number=141,
            pdf_index=153,
            quadrant="TOP_HALF",
            expected_callouts=["Plasma Arc Torch"],
        ),
    ],
    callout_vocabulary=["Orifice Gas", "Shielding Gas", "Electrode", "Constricting Nozzle", "Plasma Arc Torch"],
    has_embedded_table=False,
    notes=[
        "Shares printed page 141 with Figure B36 (occupies top half).",
    ],
    source_anomalies=[],
    clause4_terms=["constricting nozzle", "orifice gas", "plasma arc torch"],
)

# ---------------------------------------------------------------------------
# Figure B36: Gas Tungsten Arc Welding Torch Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B36_SPEC = SpatialCalloutSpec(
    figure_id="Figure B36",
    official_title="Gas Tungsten Arc Welding Torch Nomenclature",
    short_title="GTAW Torch Nomenclature",
    pages=[(153, 141)],
    crop_box=(0.05, 0.50, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="GTAW Torch Nomenclature",
            page_number=141,
            pdf_index=153,
            quadrant="BOTTOM_HALF",
            expected_callouts=["GTAW Torch"],
        ),
    ],
    callout_vocabulary=["Gas Nozzle", "Collet", "Tungsten Electrode", "Shielding Gas", "Torch Body", "GTAW Torch"],
    has_embedded_table=False,
    notes=[
        "Shares printed page 141 with Figure B35 (occupies bottom half).",
    ],
    source_anomalies=[],
    clause4_terms=["collet", "gas tungsten arc welding torch", "tungsten electrode"],
)

# ---------------------------------------------------------------------------
# Figure B37: Electroslag Welding Process Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B37_SPEC = SpatialCalloutSpec(
    figure_id="Figure B37",
    official_title="Electroslag Welding Process Nomenclature",
    short_title="Electroslag Welding Process Nomenclature",
    pages=[(154, 142)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Nonconsumable Guide Electroslag Welding",
            page_number=142,
            pdf_index=154,
            quadrant="PANEL_A",
            expected_callouts=["Electroslag Welding"],
        ),
        SubPanelSpec(
            letter="B",
            name="Consumable Guide Electroslag Welding",
            page_number=142,
            pdf_index=154,
            quadrant="PANEL_B",
            expected_callouts=["Consumable Guide"],
        ),
    ],
    callout_vocabulary=["Electroslag Welding", "Guide Tube", "Consumable Guide", "Slag Pool", "Weld Pool", "Molding Shoe"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["consumable guide electroslag welding", "electroslag welding", "electroslag welding electrode", "molding shoe"],
)

# ---------------------------------------------------------------------------
# Figure B38: Gas Metal Arc and Flux Cored Arc Welding Gun Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B38_SPEC = SpatialCalloutSpec(
    figure_id="Figure B38",
    official_title="Gas Metal Arc and Flux Cored Arc Welding Gun Nomenclature",
    short_title="Gas Metal Arc",
    pages=[(155, 143)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Air-Cooled GMAW/FCAW Gun",
            page_number=143,
            pdf_index=155,
            quadrant="PANEL_A",
            expected_callouts=["Gas Nozzle"],
        ),
        SubPanelSpec(
            letter="B",
            name="Water-Cooled GMAW/FCAW Gun",
            page_number=143,
            pdf_index=155,
            quadrant="PANEL_B",
            expected_callouts=["Contact Tip"],
        ),
    ],
    callout_vocabulary=["Gas Nozzle", "Contact Tip", "Gas Diffuser", "Gun Body", "Shielding Gas"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["contact tip", "gas diffuser", "gas metal arc welding gun"],
)

# ---------------------------------------------------------------------------
# Figure B39: Metal Transfer in Gas Metal Arc Welding
# ---------------------------------------------------------------------------
FIGURE_B39_SPEC = SpatialCalloutSpec(
    figure_id="Figure B39",
    official_title="Metal Transfer in Gas Metal Arc Welding",
    short_title="Metal Transfer in Gas Metal Arc Welding",
    pages=[(156, 144)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Spray Transfer",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_A",
            expected_callouts=["Spray Transfer"],
        ),
        SubPanelSpec(
            letter="B",
            name="Globular Transfer",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_B",
            expected_callouts=["Globular Transfer"],
        ),
        SubPanelSpec(
            letter="C",
            name="Short-Circuiting Transfer",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_C",
            expected_callouts=["Short-Circuiting Transfer"],
        ),
    ],
    callout_vocabulary=["Spray Transfer", "Globular Transfer", "Short-Circuiting Transfer", "Metal Transfer"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["globular transfer", "short circuiting transfer", "spray transfer"],
)

# ---------------------------------------------------------------------------
# Figure B40: Oxyacetylene Flame Types
# ---------------------------------------------------------------------------
FIGURE_B40_SPEC = SpatialCalloutSpec(
    figure_id="Figure B40",
    official_title="Oxyacetylene Flame Types",
    short_title="Oxyacetylene Flame Types",
    pages=[(157, 145)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Pure Acetylene Flame",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_A",
            expected_callouts=["Acetylene Flame"],
        ),
        SubPanelSpec(
            letter="B",
            name="Neutral Flame",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_B",
            expected_callouts=["Neutral Flame"],
        ),
        SubPanelSpec(
            letter="C",
            name="Oxidizing Flame",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_C",
            expected_callouts=["Oxidizing Flame"],
        ),
        SubPanelSpec(
            letter="D",
            name="Reducing Flame (Carburizing Flame)",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_D",
            expected_callouts=["Reducing Flame"],
        ),
    ],
    callout_vocabulary=["Neutral Flame", "Oxidizing Flame", "Reducing Flame", "Carburizing Flame", "Inner Cone", "Acetylene Feather", "Outer Envelope"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["carburizing flame", "cone", "neutral flame", "oxidizing flame", "reducing flame"],
)

# ---------------------------------------------------------------------------
# Figure B41: Oxygen Cutting
# ---------------------------------------------------------------------------
FIGURE_B41_SPEC = SpatialCalloutSpec(
    figure_id="Figure B41",
    official_title="Oxygen Cutting",
    short_title="Oxygen Cutting",
    pages=[(158, 146)],
    crop_box=(0.05, 0.05, 0.95, 0.50),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Oxygen Cutting Torch and Tip Nomenclature",
            page_number=146,
            pdf_index=158,
            quadrant="TOP_HALF",
            expected_callouts=["Oxygen Cutting"],
        ),
    ],
    callout_vocabulary=["Cutting Oxygen", "Preheat Oxygen", "Preheat Flame", "Cutting Tip", "Drag Lines", "Kerf", "Oxygen Cutting"],
    has_embedded_table=False,
    notes=[
        "Shares printed page 146 with Figure B42 (occupies top half).",
    ],
    source_anomalies=[],
    clause4_terms=["cutting tip", "drag", "drag angle", "kerf", "oxygen cutting"],
)

# ---------------------------------------------------------------------------
# Figure B42: Filler Metal Packaging
# ---------------------------------------------------------------------------
FIGURE_B42_SPEC = SpatialCalloutSpec(
    figure_id="Figure B42",
    official_title="Filler Metal Packaging",
    short_title="Filler Metal Packaging",
    pages=[(158, 146)],
    crop_box=(0.05, 0.50, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Spool Packaging",
            page_number=146,
            pdf_index=158,
            quadrant="PANEL_A",
            expected_callouts=["Spool"],
        ),
        SubPanelSpec(
            letter="B",
            name="Coil with Support / Drum Packaging",
            page_number=146,
            pdf_index=158,
            quadrant="PANEL_B",
            expected_callouts=["Drum Packaging"],
        ),
    ],
    callout_vocabulary=["Spool", "Coil with Support", "Drum", "Filler Metal Packaging"],
    has_embedded_table=False,
    notes=[
        "Shares printed page 146 with Figure B41 (occupies bottom half).",
    ],
    source_anomalies=[],
    clause4_terms=["coil with support", "coil without support", "drum", "spool"],
)

# ---------------------------------------------------------------------------
# Figure B43: Thermal Spraying Surface Preparation
# ---------------------------------------------------------------------------
FIGURE_B43_SPEC = SpatialCalloutSpec(
    figure_id="Figure B43",
    official_title="Thermal Spraying Surface Preparation",
    short_title="Thermal Spraying Surface Preparation",
    pages=[(159, 147)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Surface Roughening",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_A",
            expected_callouts=["Surface Roughening"],
        ),
        SubPanelSpec(
            letter="B",
            name="Threading and Grooving",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_B",
            expected_callouts=["Threading and Grooving"],
        ),
        SubPanelSpec(
            letter="C",
            name="Rotary Roughing",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_C",
            expected_callouts=["Rotary Roughing"],
        ),
        SubPanelSpec(
            letter="D",
            name="Dovetailing",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_D",
            expected_callouts=["Dovetailing"],
        ),
        SubPanelSpec(
            letter="E",
            name="Grit Blasting",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_E",
            expected_callouts=["Grit Blasting"],
        ),
    ],
    callout_vocabulary=["Surface Preparation", "Threading", "Grooving", "Rotary Roughing", "Dovetailing", "Grit Blasting"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["dovetailing", "grit blasting", "rotary roughing", "surface preparation", "threading and grooving"],
)

# ---------------------------------------------------------------------------
# Figure B46: Schematic of the Friction Stir Welding Process
# ---------------------------------------------------------------------------
FIGURE_B46_SPEC = SpatialCalloutSpec(
    figure_id="Figure B46",
    official_title="Schematic of the Friction Stir Welding Process",
    short_title="Schematic of the Friction Stir Welding Process",
    pages=[(162, 150)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="FSW Tool and Joint Schematic",
            page_number=150,
            pdf_index=162,
            quadrant="PANEL_A",
            expected_callouts=["Base Metal", "Direction of Tool Rotation", "Weld Tool", "Axial Force", "Tool Shoulder", "Probe", "Advancing Side of Weld", "Exit Hole", "Retreating Side of Weld", "Weld Face"],
        ),
    ],
    callout_vocabulary=[
        "Base Metal", "Direction of Tool Rotation", "Weld Tool", "Axial Force",
        "Tool Shoulder", "Probe", "Advancing Side of Weld", "Exit Hole",
        "Retreating Side of Weld", "Weld Face", "Direction of Welding",
        "Advancing Side", "Retreating Side", "Shoulder", "Stir Zone / Weld Nugget",
        "Thermo-mechanically affected zone", "Heat-affected zone",
    ],
    has_embedded_table=False,
    notes=[
        "Contains full printed Key (1 through 10) and FSW process zones.",
    ],
    source_anomalies=[],
    clause4_terms=["advancing side", "friction stir welding", "heat-affected zone", "retreating side", "stir zone", "thermo-mechanically affected zone"],
)

# ---------------------------------------------------------------------------
# Figure B47: Typical Arrangements for Multiple Spot Welding
# ---------------------------------------------------------------------------
FIGURE_B47_SPEC = SpatialCalloutSpec(
    figure_id="Figure B47",
    official_title="Typical Arrangements for Multiple Spot Welding",
    short_title="Typical Arrangements for Multiple Spot Welding",
    pages=[(163, 151)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Direct Multiple Spot Welding",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_A",
            expected_callouts=["Direct Welding"],
        ),
        SubPanelSpec(
            letter="B",
            name="Indirect Multiple Spot Welding",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_B",
            expected_callouts=["Indirect Welding"],
        ),
        SubPanelSpec(
            letter="C",
            name="Series Multiple Spot Welding",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_C",
            expected_callouts=["Series Welding"],
        ),
        SubPanelSpec(
            letter="D",
            name="Push-Pull Multiple Spot Welding",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_D",
            expected_callouts=["Push-Pull Welding"],
        ),
        SubPanelSpec(
            letter="E",
            name="Parallel Multiple Spot Welding",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_E",
            expected_callouts=["Parallel Welding"],
        ),
    ],
    callout_vocabulary=["Direct Welding", "Indirect Welding", "Series Welding", "Push-Pull Welding", "Parallel Welding", "Multiple Spot Welding"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["direct welding", "indirect welding", "multiple spot welding", "push-pull welding", "series welding"],
)

# ---------------------------------------------------------------------------
# Figure B48: Typical Arrangements for Single Spot Welds
# ---------------------------------------------------------------------------
FIGURE_B48_SPEC = SpatialCalloutSpec(
    figure_id="Figure B48",
    official_title="Typical Arrangements for Single Spot Welds",
    short_title="Typical Arrangements for Single Spot Welds",
    pages=[(164, 152)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Single-Spot Direct Welding",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_A",
            expected_callouts=["Single-Spot Direct Welding"],
        ),
        SubPanelSpec(
            letter="B",
            name="Single-Spot Indirect Welding",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_B",
            expected_callouts=["Single-Spot Indirect Welding"],
        ),
    ],
    callout_vocabulary=["Single Spot Welds", "Single-Spot Direct Welding", "Single-Spot Indirect Welding", "Direct Welding", "Indirect Welding"],
    has_embedded_table=False,
    notes=[],
    source_anomalies=[],
    clause4_terms=["direct welding", "indirect welding", "spot welding"],
)

# ---------------------------------------------------------------------------
# Figure B52: High-Frequency Resistance Welding
# ---------------------------------------------------------------------------
FIGURE_B52_SPEC = SpatialCalloutSpec(
    figure_id="Figure B52",
    official_title="High-Frequency Resistance Welding",
    short_title="High-Frequency Resistance Welding",
    pages=[(167, 155), (168, 156)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Tube/Pipe Mill Schematic",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_A",
            expected_callouts=["Tube/Pipe Mill"],
        ),
        SubPanelSpec(
            letter="B",
            name="High-Frequency Induction Welding",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_B",
            expected_callouts=["Induction Coil"],
        ),
        SubPanelSpec(
            letter="C",
            name="High-Frequency Contact Resistance Welding",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_C",
            expected_callouts=["Welding Contacts"],
        ),
        SubPanelSpec(
            letter="D",
            name="Squeeze Rolls and Impeder",
            page_number=156,
            pdf_index=168,
            quadrant="PANEL_D",
            expected_callouts=["Squeeze Rolls", "Impeder"],
        ),
        SubPanelSpec(
            letter="E",
            name="Welding Contacts and V-Angle",
            page_number=156,
            pdf_index=168,
            quadrant="PANEL_E",
            expected_callouts=["Welding Contacts", "Apex"],
        ),
    ],
    callout_vocabulary=["High-Frequency Resistance Welding", "Induction Coil", "Squeeze Rolls", "Impeder", "Welding Contacts", "Apex", "V-Angle"],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation across printed pages 155 and 156 (PDF indices 167..168).",
    ],
    source_anomalies=[],
    clause4_terms=["high-frequency resistance welding", "impeder", "squeeze rolls"],
)

# ---------------------------------------------------------------------------
# Master Spec Registry for Remaining Figures
# ---------------------------------------------------------------------------
REMAINING_ANNEX_B_SPECS: Dict[str, SpatialCalloutSpec] = {
    "Figure B7": FIGURE_B7_SPEC,
    "Figure B8": FIGURE_B8_SPEC,
    "Figure B9": FIGURE_B9_SPEC,
    "Figure B10": FIGURE_B10_SPEC,
    "Figure B11": FIGURE_B11_SPEC,
    "Figure B12": FIGURE_B12_SPEC,
    "Figure B13": FIGURE_B13_SPEC,
    "Figure B14": FIGURE_B14_SPEC,
    "Figure B15": FIGURE_B15_SPEC,
    "Figure B16A": FIGURE_B16A_SPEC,
    "Figure B16B": FIGURE_B16B_SPEC,
    "Figure B16C": FIGURE_B16C_SPEC,
    "Figure B17": FIGURE_B17_SPEC,
    "Figure B18": FIGURE_B18_SPEC,
    "Figure B19": FIGURE_B19_SPEC,
    "Figure B20": FIGURE_B20_SPEC,
    "Figure B21": FIGURE_B21_SPEC,
    "Figure B22": FIGURE_B22_SPEC,
    "Figure B23": FIGURE_B23_SPEC,
    "Figure B24": FIGURE_B24_SPEC,
    "Figure B25": FIGURE_B25_SPEC,
    "Figure B26": FIGURE_B26_SPEC,
    "Figure B27": FIGURE_B27_SPEC,
    "Figure B28": FIGURE_B28_SPEC,
    "Figure B29": FIGURE_B29_SPEC,
    "Figure B30": FIGURE_B30_SPEC,
    "Figure B31": FIGURE_B31_SPEC,
    "Figure B32": FIGURE_B32_SPEC,
    "Figure B33": FIGURE_B33_SPEC,
    "Figure B34": FIGURE_B34_SPEC,
    "Figure B35": FIGURE_B35_SPEC,
    "Figure B36": FIGURE_B36_SPEC,
    "Figure B37": FIGURE_B37_SPEC,
    "Figure B38": FIGURE_B38_SPEC,
    "Figure B39": FIGURE_B39_SPEC,
    "Figure B40": FIGURE_B40_SPEC,
    "Figure B41": FIGURE_B41_SPEC,
    "Figure B42": FIGURE_B42_SPEC,
    "Figure B43": FIGURE_B43_SPEC,
    "Figure B46": FIGURE_B46_SPEC,
    "Figure B47": FIGURE_B47_SPEC,
    "Figure B48": FIGURE_B48_SPEC,
    "Figure B52": FIGURE_B52_SPEC,
}
