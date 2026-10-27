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
            name="Panel (A)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=90,
            pdf_index=102,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
    ],
    callout_vocabulary=['Edge Shapes', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['J-edge shape', 'bevel', 'bevel edge shape', 'double-J edge shape', 'double-bevel edge shape', 'edge shape', 'flanged edge shape', 'round edge shape', 'single-J edge shape', 'single-bevel edge shape', 'square edge shape', 'weld type'],
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
            name="Panel (A)",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=91,
            pdf_index=103,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=92,
            pdf_index=104,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=93,
            pdf_index=105,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
    ],
    callout_vocabulary=['Single-Groove Weld Types', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 3 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['J-groove weld', 'U-groove weld', 'V-groove weld', 'backing', 'bevel-groove weld', 'flare-V-groove weld', 'flare-bevel-groove weld', 'flare-groove weld', 'groove weld', 'single welded joint', 'single-J groove', 'single-J-groove weld', 'single-U groove', 'single-U-groove weld', 'single-V groove', 'single-V-groove weld', 'single-bevel groove', 'single-bevel-groove weld', 'single-flare-V groove', 'single-flare-V-groove weld', 'single-flare-bevel groove', 'single-flare-bevel-groove weld', 'single-groove weld', 'single-square-groove weld', 'square groove', 'square-groove weld', 'weld type'],
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
            name="Panel (A)",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=94,
            pdf_index=106,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=95,
            pdf_index=107,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
    ],
    callout_vocabulary=['Double-Groove Weld Types', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['J-groove weld', 'U-groove weld', 'V-groove weld', 'bevel-groove weld', 'double-J groove', 'double-J-groove weld', 'double-U groove', 'double-U-groove weld', 'double-V groove', 'double-V-groove weld', 'double-bevel groove', 'double-bevel-groove weld', 'double-flare-V groove', 'double-flare-V-groove weld', 'double-flare-bevel groove', 'double-flare-bevel-groove weld', 'double-groove weld', 'double-square-groove weld', 'double-welded joint', 'flare-V-groove weld', 'flare-bevel-groove weld', 'flare-groove weld', 'groove weld', 'square groove', 'square-groove weld', 'weld type'],
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
            name="Panel (A)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=96,
            pdf_index=108,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
    ],
    callout_vocabulary=['Welds in Flanged Joints', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['T-joint', 'butt joint', 'corner joint', 'edge weld', 'flanged T-joint', 'flanged butt joint', 'flanged corner joint', 'flanged joint', 'flare-V-groove weld', 'flare-bevel-groove weld', 'flare-groove weld', 'resistance spot weld', 'weld type'],
)

# ---------------------------------------------------------------------------
# Figure B11: Butting and Nonbutting Workpiece or Workpieces
# ---------------------------------------------------------------------------
FIGURE_B11_SPEC = SpatialCalloutSpec(
    figure_id="Figure B11",
    official_title="Butting and Nonbutting Workpiece or Workpieces",
    short_title="Butting",
    pages=[(109, 97)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="MAIN",
            name="Butting",
            page_number=97,
            pdf_index=109,
            quadrant="FULL",
            expected_callouts=["Butting"],
        ),
    ],
    callout_vocabulary=['Butting'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['nonbutting workpiece'],
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
            letter="B",
            name="Panel (B)",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=98,
            pdf_index=110,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['End Dam', 'Panel (B)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['backing', 'run-off weld tab', 'run-on weld tab', 'shelf bar', 'split pipe backing', 'starting weld tab', 'weld tab'],
)

# ---------------------------------------------------------------------------
# Figure B13: Edge Weld, Scarf Groove, Joint Mismatch, Root Face Extension, Consumable Insert, and Preplaced Filler Metal in a Brazed Joint
# ---------------------------------------------------------------------------
FIGURE_B13_SPEC = SpatialCalloutSpec(
    figure_id="Figure B13",
    official_title="Edge Weld, Scarf Groove, Joint Mismatch, Root Face Extension, Consumable Insert, and Preplaced Filler Metal in a Brazed Joint",
    short_title="Edge Weld",
    pages=[(111, 99)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Panel (A)",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=99,
            pdf_index=111,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['Edge Weld', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['consumable insert', 'edge weld', 'joint mismatch', 'root face extension', 'scarf groove', 'weld type'],
)

# ---------------------------------------------------------------------------
# Figure B14: Seam and Spot Weld Types
# ---------------------------------------------------------------------------
FIGURE_B14_SPEC = SpatialCalloutSpec(
    figure_id="Figure B14",
    official_title="Seam and Spot Weld Types",
    short_title="Seam",
    pages=[(112, 100)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Panel (A)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=100,
            pdf_index=112,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
    ],
    callout_vocabulary=['Seam', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['arc seam weld', 'arc spot weld', 'high-energy beam seam weld', 'high-energy beam spot weld', 'overlap', 'resistance seam weld', 'resistance seam welding', 'resistance spot weld', 'resistance spot welding', 'seam weld', 'spot weld', 'weld type'],
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
            name="Panel (A)",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=101,
            pdf_index=113,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['Various Weld Types', 'Panel (A)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['plug weld', 'slot weld', 'surfacing weld', 'upset welding', 'weld type'],
)

# ---------------------------------------------------------------------------
# Figure B16A: Welding Position Diagram for Groove Welds and Surfacing Welds in Plate
# ---------------------------------------------------------------------------
FIGURE_B16A_SPEC = SpatialCalloutSpec(
    figure_id="Figure B16A",
    official_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Plate",
    short_title="Welding Position Diagram for Groove Welds",
    pages=[(114, 102)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="1G",
            name="Panel (1G)",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_1G",
            expected_callouts=["Panel (1G)"],
        ),
        SubPanelSpec(
            letter="2G",
            name="Panel (2G)",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_2G",
            expected_callouts=["Panel (2G)"],
        ),
        SubPanelSpec(
            letter="3G",
            name="Panel (3G)",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_3G",
            expected_callouts=["Panel (3G)"],
        ),
        SubPanelSpec(
            letter="4G",
            name="Panel (4G)",
            page_number=102,
            pdf_index=114,
            quadrant="PANEL_4G",
            expected_callouts=["Panel (4G)"],
        ),
    ],
    callout_vocabulary=['Welding Position Diagram for Groove Welds', 'Panel (1G)', 'Panel (2G)', 'Panel (3G)', 'Panel (4G)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['flat welding position', 'horizontal welding position', 'overhead welding position', 'vertical welding position', 'weld axis', 'welding position'],
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
            letter="1F",
            name="Panel (1F)",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_1F",
            expected_callouts=["Panel (1F)"],
        ),
        SubPanelSpec(
            letter="2F",
            name="Panel (2F)",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_2F",
            expected_callouts=["Panel (2F)"],
        ),
        SubPanelSpec(
            letter="3F",
            name="Panel (3F)",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_3F",
            expected_callouts=["Panel (3F)"],
        ),
        SubPanelSpec(
            letter="4F",
            name="Panel (4F)",
            page_number=103,
            pdf_index=115,
            quadrant="PANEL_4F",
            expected_callouts=["Panel (4F)"],
        ),
    ],
    callout_vocabulary=['Welding Position Diagram for Fillet Welds in Plate', 'Panel (1F)', 'Panel (2F)', 'Panel (3F)', 'Panel (4F)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['flat welding position', 'horizontal welding position', 'overhead welding position', 'vertical welding position', 'weld axis', 'welding position'],
)

# ---------------------------------------------------------------------------
# Figure B16C: Welding Position Diagram for Groove Welds and Surfacing Welds in Pipe
# ---------------------------------------------------------------------------
FIGURE_B16C_SPEC = SpatialCalloutSpec(
    figure_id="Figure B16C",
    official_title="Welding Position Diagram for Groove Welds and Surfacing Welds in Pipe",
    short_title="Welding Position Diagram for Groove Welds",
    pages=[(116, 104)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="1G",
            name="Panel (1G)",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_1G",
            expected_callouts=["Panel (1G)"],
        ),
        SubPanelSpec(
            letter="2G",
            name="Panel (2G)",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_2G",
            expected_callouts=["Panel (2G)"],
        ),
        SubPanelSpec(
            letter="5G",
            name="Panel (5G)",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_5G",
            expected_callouts=["Panel (5G)"],
        ),
        SubPanelSpec(
            letter="6G",
            name="Panel (6G)",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_6G",
            expected_callouts=["Panel (6G)"],
        ),
        SubPanelSpec(
            letter="6GR",
            name="Panel (6GR)",
            page_number=104,
            pdf_index=116,
            quadrant="PANEL_6GR",
            expected_callouts=["Panel (6GR)"],
        ),
    ],
    callout_vocabulary=['Welding Position Diagram for Groove Welds', 'Panel (1G)', 'Panel (2G)', 'Panel (5G)', 'Panel (6G)', 'Panel (6GR)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['flat welding position', 'horizontal welding position', 'overhead welding position', 'vertical welding position', 'weld axis', 'welding position'],
)

# ---------------------------------------------------------------------------
# Figure B17: Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Plate .  .   .   .  . . . 105
# ---------------------------------------------------------------------------
FIGURE_B17_SPEC = SpatialCalloutSpec(
    figure_id="Figure B17",
    official_title="Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Plate .  .   .   .  . . . 105",
    short_title="Welding Test Positions",
    pages=[(117, 105)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Panel (A)",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=105,
            pdf_index=117,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
    ],
    callout_vocabulary=['Welding Test Positions', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['1G', '2G', '3G', '4G', 'flat welding position', 'groove weld', 'horizontal welding position', 'overhead welding position', 'vertical welding position', 'welding position'],
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
            name="Panel (A)",
            page_number=106,
            pdf_index=118,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=106,
            pdf_index=118,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=107,
            pdf_index=119,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=107,
            pdf_index=119,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
    ],
    callout_vocabulary=['Welding Test Positions', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['1F', '2F', '3F', '4F', 'flat welding position', 'horizontal welding position', 'overhead welding position', 'vertical welding position', 'welding position'],
)

# ---------------------------------------------------------------------------
# Figure B19: Welding Test Positions and Their Designations for Groove Welds and Surfacing in Pipe
# ---------------------------------------------------------------------------
FIGURE_B19_SPEC = SpatialCalloutSpec(
    figure_id="Figure B19",
    official_title="Welding Test Positions and Their Designations for Groove Welds and Surfacing in Pipe",
    short_title="Welding Test Positions",
    pages=[(120, 108), (121, 109)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Panel (A)",
            page_number=108,
            pdf_index=120,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=108,
            pdf_index=120,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=108,
            pdf_index=120,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=109,
            pdf_index=121,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=109,
            pdf_index=121,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['Welding Test Positions', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['1G', '2G', '3G', '4G', '5G', '6G', '6GR', 'flat welding position', 'groove weld', 'horizontal welding position', 'welding position'],
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
            name="Panel (A)",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=110,
            pdf_index=122,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=111,
            pdf_index=123,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
    ],
    callout_vocabulary=['Welding Test Positions', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (F)', 'Panel (G)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['1F', '2F', '2FR', '3F', '4F', '5F', '6F', 'flat welding position', 'horizontal welding position', 'overhead welding position', 'welding position'],
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
            name="Panel (A)",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=112,
            pdf_index=124,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
    ],
    callout_vocabulary=['Position of Beam', 'Panel (A)', 'Panel (C)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['backhand welding', 'drag angle', 'forehand welding', 'groove weld', 'push angle', 'travel angle', 'weld axis', 'work angle'],
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
            name="Panel (A)",
            page_number=113,
            pdf_index=125,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=113,
            pdf_index=125,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Weld Bead Types', 'Panel (A)', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['stringer bead', 'weave bead', 'weld bead'],
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
            name="Panel (A)",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=114,
            pdf_index=126,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=115,
            pdf_index=127,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=116,
            pdf_index=128,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=116,
            pdf_index=128,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
        SubPanelSpec(
            letter="J",
            name="Panel (J)",
            page_number=116,
            pdf_index=128,
            quadrant="PANEL_J",
            expected_callouts=["Panel (J)"],
        ),
    ],
    callout_vocabulary=['Welding Application Nomenclature', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)', 'Panel (J)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 3 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['backstep sequence', 'block sequence', 'boxing', 'cascade sequence', 'chain intermittent weld', 'cross-sectional sequence', 'intermittent weld', 'layer', 'longitudinal sequence', 'resistance seam welding', 'split layer technique', 'staggered intermittent weld', 'temper bead sequence', 'temper pass', 'toe temper bead', 'toe temper pass', 'weld bead'],
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
            name="Panel (A)",
            page_number=117,
            pdf_index=129,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=117,
            pdf_index=129,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=117,
            pdf_index=129,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=118,
            pdf_index=130,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=118,
            pdf_index=130,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=118,
            pdf_index=130,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=119,
            pdf_index=131,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=119,
            pdf_index=131,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=119,
            pdf_index=131,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
        SubPanelSpec(
            letter="J",
            name="Panel (J)",
            page_number=120,
            pdf_index=132,
            quadrant="PANEL_J",
            expected_callouts=["Panel (J)"],
        ),
        SubPanelSpec(
            letter="K",
            name="Panel (K)",
            page_number=120,
            pdf_index=132,
            quadrant="PANEL_K",
            expected_callouts=["Panel (K)"],
        ),
        SubPanelSpec(
            letter="L",
            name="Panel (L)",
            page_number=120,
            pdf_index=132,
            quadrant="PANEL_L",
            expected_callouts=["Panel (L)"],
        ),
        SubPanelSpec(
            letter="M",
            name="Panel (M)",
            page_number=121,
            pdf_index=133,
            quadrant="PANEL_M",
            expected_callouts=["Panel (M)"],
        ),
        SubPanelSpec(
            letter="N",
            name="Panel (N)",
            page_number=121,
            pdf_index=133,
            quadrant="PANEL_N",
            expected_callouts=["Panel (N)"],
        ),
        SubPanelSpec(
            letter="O",
            name="Panel (O)",
            page_number=121,
            pdf_index=133,
            quadrant="PANEL_O",
            expected_callouts=["Panel (O)"],
        ),
        SubPanelSpec(
            letter="P",
            name="Panel (P)",
            page_number=122,
            pdf_index=134,
            quadrant="PANEL_P",
            expected_callouts=["Panel (P)"],
        ),
        SubPanelSpec(
            letter="Q",
            name="Panel (Q)",
            page_number=122,
            pdf_index=134,
            quadrant="PANEL_Q",
            expected_callouts=["Panel (Q)"],
        ),
        SubPanelSpec(
            letter="R",
            name="Panel (R)",
            page_number=122,
            pdf_index=134,
            quadrant="PANEL_R",
            expected_callouts=["Panel (R)"],
        ),
    ],
    callout_vocabulary=['Parts of a Weld', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)', 'Panel (J)', 'Panel (K)', 'Panel (L)', 'Panel (M)', 'Panel (N)', 'Panel (O)', 'Panel (P)', 'Panel (Q)', 'Panel (R)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 6 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['back weld', 'backing weld', 'base metal zone', 'dilution', 'double-groove weld', 'double-welded joint', 'face reinforcement', 'fillet weld leg', 'heat-affected zone', 'joint spacer', 'root reinforcement', 'root surface', 'weld bead toe', 'weld face', 'weld metal zone', 'weld root', 'weld toe'],
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
            name="Panel (A)",
            page_number=123,
            pdf_index=135,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=123,
            pdf_index=135,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=123,
            pdf_index=135,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=124,
            pdf_index=136,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=124,
            pdf_index=136,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=125,
            pdf_index=137,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=125,
            pdf_index=137,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=126,
            pdf_index=138,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=126,
            pdf_index=138,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
    ],
    callout_vocabulary=['Weld Sizes', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 4 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['actual throat', 'concave fillet weld', 'concavity', 'convex fillet weld', 'convexity', 'edge weld', 'edge weld size', 'effective throat', 'fillet weld leg', 'fillet weld size', 'projection weld size', 'root opening', 'seam weld size', 'spot weld size', 'theoretical throat'],
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
            name="Panel (A)",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=127,
            pdf_index=139,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=128,
            pdf_index=140,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=128,
            pdf_index=140,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=128,
            pdf_index=140,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=129,
            pdf_index=141,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=129,
            pdf_index=141,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
        SubPanelSpec(
            letter="J",
            name="Panel (J)",
            page_number=129,
            pdf_index=141,
            quadrant="PANEL_J",
            expected_callouts=["Panel (J)"],
        ),
    ],
    callout_vocabulary=['Groove Weld Size', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)', 'Panel (J)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 3 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['complete joint penetration', 'complete joint penetration weld', 'flare-bevel-groove weld', 'groove weld size', 'incomplete joint penetration', 'joint penetration', 'partial joint penetration weld', 'root penetration'],
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
            name="Panel (A)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=130,
            pdf_index=142,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
    ],
    callout_vocabulary=['Melt-Through', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['concave root surface', 'convex root surface', 'flanged butt joint', 'flanged corner joint', 'flanged joint', 'melt-through', 'root surface'],
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
            letter="MAIN",
            name="Complete Fusion",
            page_number=131,
            pdf_index=143,
            quadrant="FULL",
            expected_callouts=["Complete Fusion"],
        ),
    ],
    callout_vocabulary=['Complete Fusion'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['complete fusion'],
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
            letter="MAIN",
            name="Incomplete Fusion",
            page_number=132,
            pdf_index=144,
            quadrant="FULL",
            expected_callouts=["Incomplete Fusion"],
        ),
    ],
    callout_vocabulary=['Incomplete Fusion'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['incomplete fusion'],
)

# ---------------------------------------------------------------------------
# Figure B30: Fusion Welds (Transverse Section)
# ---------------------------------------------------------------------------
FIGURE_B30_SPEC = SpatialCalloutSpec(
    figure_id="Figure B30",
    official_title="Fusion Welds (Transverse Section)",
    short_title="Fusion Welds (Transverse Section)",
    pages=[(145, 133), (146, 134)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=133,
            pdf_index=145,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=134,
            pdf_index=146,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=134,
            pdf_index=146,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
    ],
    callout_vocabulary=['Fusion Welds (Transverse Section)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['faying surface', 'fusion depth', 'fusion face', 'fusion zone', 'mash seam welding', 'overlap', 'projection welding', 'resistance seam weld', 'resistance seam welding', 'resistance spot weld', 'resistance spot welding', 'spot weld size', 'surfacing weld', 'weld interface'],
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
            name="Panel (A)",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=135,
            pdf_index=147,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
    ],
    callout_vocabulary=['Joining Without Fusion', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['bond line', 'braze', 'braze interface', 'braze metal', 'friction welding', 'solder', 'solder interface', 'thermal spray deposit', 'upset welding', 'weld interface'],
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
            name="Panel (A)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=136,
            pdf_index=148,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
        SubPanelSpec(
            letter="H",
            name="Panel (H)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_H",
            expected_callouts=["Panel (H)"],
        ),
        SubPanelSpec(
            letter="I",
            name="Panel (I)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_I",
            expected_callouts=["Panel (I)"],
        ),
        SubPanelSpec(
            letter="J",
            name="Panel (J)",
            page_number=137,
            pdf_index=149,
            quadrant="PANEL_J",
            expected_callouts=["Panel (J)"],
        ),
        SubPanelSpec(
            letter="K",
            name="Panel (K)",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_K",
            expected_callouts=["Panel (K)"],
        ),
        SubPanelSpec(
            letter="L",
            name="Panel (L)",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_L",
            expected_callouts=["Panel (L)"],
        ),
        SubPanelSpec(
            letter="M",
            name="Panel (M)",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_M",
            expected_callouts=["Panel (M)"],
        ),
        SubPanelSpec(
            letter="O",
            name="Panel (O)",
            page_number=138,
            pdf_index=150,
            quadrant="PANEL_O",
            expected_callouts=["Panel (O)"],
        ),
    ],
    callout_vocabulary=['Weld Discontinuities', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)', 'Panel (H)', 'Panel (I)', 'Panel (J)', 'Panel (K)', 'Panel (L)', 'Panel (M)', 'Panel (O)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 3 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['bead reentrant angle', 'burn-through', 'overlap', 'reentrant angle', 'root surface underfill', 'toe crack', 'toe reentrant angle', 'underbead crack', 'undercut', 'underfill', 'weld face underfill'],
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
            name="Panel (A)",
            page_number=139,
            pdf_index=151,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=139,
            pdf_index=151,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Crack Types', 'Panel (A)', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
        "Contains numbered key legend.",
    ],
    source_anomalies=[],
    clause4_terms=['crack', 'crater crack', 'face crack', 'heat-affected zone crack', 'lamellar tear', 'root crack', 'root surface crack', 'throat crack', 'toe crack', 'transverse crack', 'underbead crack', 'weld crack', 'weld metal crack'],
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
            name="Panel (A)",
            page_number=140,
            pdf_index=152,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=140,
            pdf_index=152,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Welding Current Polarity', 'Panel (A)', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['direct current electrode negative', 'direct current electrode positive', 'electrode lead', 'ground connection', 'welding leads', 'workpiece connector', 'workpiece lead'],
)

# ---------------------------------------------------------------------------
# Figure B35: Plasma Arc Torch Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B35_SPEC = SpatialCalloutSpec(
    figure_id="Figure B35",
    official_title="Plasma Arc Torch Nomenclature",
    short_title="Plasma Arc Torch Nomenclature",
    pages=[(153, 141)],
    crop_box=(0.05, 0.05, 0.52, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="MAIN",
            name="Plasma Arc Torch Nomenclature",
            page_number=141,
            pdf_index=153,
            quadrant="FULL",
            expected_callouts=["Plasma Arc Torch Nomenclature"],
        ),
    ],
    callout_vocabulary=['Plasma Arc Torch Nomenclature'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['arc welding torch', 'constricting nozzle', 'constricting orifice', 'constricting orifice diameter', 'constricting orifice length', 'electrode extension', 'electrode setback', 'gas nozzle', 'nonconsumable electrode', 'orifice gas', 'plasma arc cutting torch', 'plasma arc welding torch', 'plenum chamber', 'standoff distance'],
)

# ---------------------------------------------------------------------------
# Figure B36: Gas Tungsten Arc Welding Torch Nomenclature
# ---------------------------------------------------------------------------
FIGURE_B36_SPEC = SpatialCalloutSpec(
    figure_id="Figure B36",
    official_title="Gas Tungsten Arc Welding Torch Nomenclature",
    short_title="Gas Tungsten Arc Welding Torch Nomenclature",
    pages=[(153, 141)],
    crop_box=(0.5, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="MAIN",
            name="Gas Tungsten Arc Welding Torch Nomenclature",
            page_number=141,
            pdf_index=153,
            quadrant="FULL",
            expected_callouts=["Gas Tungsten Arc Welding Torch Nomenclature"],
        ),
    ],
    callout_vocabulary=['Gas Tungsten Arc Welding Torch Nomenclature'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['arc welding torch', 'back cap', 'collet', 'electrode extension', 'electrode lead', 'gas nozzle', 'gas tungsten arc welding', 'gas tungsten arc welding torch', 'nonconsumable electrode', 'standoff distance', 'stickout', 'welding rod', 'welding wire'],
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
            letter="B",
            name="Panel (B)",
            page_number=142,
            pdf_index=154,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Electroslag Welding Process Nomenclature', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['backing', 'backing shoe', 'consumable guide electroslag welding', 'electroslag welding'],
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
            name="Panel (A)",
            page_number=143,
            pdf_index=155,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=143,
            pdf_index=155,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Gas Metal Arc', 'Panel (A)', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['arc welding gun', 'contact tip', 'contact tip setback', 'electrode extension', 'gas metal arc welding', 'gas nozzle', 'insulating nozzle', 'long electrode extension', 'standoff distance', 'stickout'],
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
            name="Panel (A)",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=144,
            pdf_index=156,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
    ],
    callout_vocabulary=['Metal Transfer in Gas Metal Arc Welding', 'Panel (A)', 'Panel (B)', 'Panel (C)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['contact tip', 'gas metal arc welding', 'gas nozzle', 'globular transfer', 'short circuiting transfer', 'spray transfer'],
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
            letter="B",
            name="Panel (B)",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=145,
            pdf_index=157,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
    ],
    callout_vocabulary=['Oxyacetylene Flame Types', 'Panel (B)', 'Panel (C)', 'Panel (D)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['acetylene feather', 'carburizing flame', 'cone', 'neutral flame', 'oxidizing flame', 'oxyacetylene welding', 'reducing flame'],
)

# ---------------------------------------------------------------------------
# Figure B41: Oxygen Cutting
# ---------------------------------------------------------------------------
FIGURE_B41_SPEC = SpatialCalloutSpec(
    figure_id="Figure B41",
    official_title="Oxygen Cutting",
    short_title="Oxygen Cutting",
    pages=[(158, 146)],
    crop_box=(0.05, 0.05, 0.52, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="MAIN",
            name="Oxygen Cutting",
            page_number=146,
            pdf_index=158,
            quadrant="FULL",
            expected_callouts=["Oxygen Cutting"],
        ),
    ],
    callout_vocabulary=['Oxygen Cutting'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['cutting tip', 'drag', 'kerf'],
)

# ---------------------------------------------------------------------------
# Figure B42: Filler Metal Packaging
# ---------------------------------------------------------------------------
FIGURE_B42_SPEC = SpatialCalloutSpec(
    figure_id="Figure B42",
    official_title="Filler Metal Packaging",
    short_title="Filler Metal Packaging",
    pages=[(158, 146)],
    crop_box=(0.5, 0.05, 0.95, 0.95),
    sub_panels=[
        SubPanelSpec(
            letter="A",
            name="Panel (A)",
            page_number=146,
            pdf_index=158,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=146,
            pdf_index=158,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
    ],
    callout_vocabulary=['Filler Metal Packaging', 'Panel (A)', 'Panel (B)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['coil with support', 'spool'],
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
            name="Panel (A)",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=147,
            pdf_index=159,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['Thermal Spraying Surface Preparation', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
    ],
    source_anomalies=[],
    clause4_terms=['collaring', 'dovetailing', 'groove and rotary roughening', 'knurling', 'rotary roughening', 'threading and knurling'],
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
            letter="MAIN",
            name="Schematic of the Friction Stir Welding Process",
            page_number=150,
            pdf_index=162,
            quadrant="FULL",
            expected_callouts=["Schematic of the Friction Stir Welding Process"],
        ),
    ],
    callout_vocabulary=['Schematic of the Friction Stir Welding Process'],
    has_embedded_table=False,
    notes=[
        "Contains numbered key legend.",
    ],
    source_anomalies=[],
    clause4_terms=['advancing side', 'resistance spot welding', 'retreating side'],
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
            name="Panel (A)",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=151,
            pdf_index=163,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['Typical Arrangements for Multiple Spot Welding', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['parallel resistance welding', 'push-pull resistance welding', 'resistance spot welding', 'series resistance welding'],
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
            name="Panel (A)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
        SubPanelSpec(
            letter="F",
            name="Panel (F)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_F",
            expected_callouts=["Panel (F)"],
        ),
        SubPanelSpec(
            letter="G",
            name="Panel (G)",
            page_number=152,
            pdf_index=164,
            quadrant="PANEL_G",
            expected_callouts=["Panel (G)"],
        ),
    ],
    callout_vocabulary=['Typical Arrangements for Single Spot Welds', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)', 'Panel (F)', 'Panel (G)'],
    has_embedded_table=True,
    notes=[
        "Contains embedded table / nomenclature mapping.",
    ],
    source_anomalies=[],
    clause4_terms=['direct resistance welding', 'indirect resistance welding', 'resistance spot welding'],
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
            name="Panel (A)",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_A",
            expected_callouts=["Panel (A)"],
        ),
        SubPanelSpec(
            letter="B",
            name="Panel (B)",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_B",
            expected_callouts=["Panel (B)"],
        ),
        SubPanelSpec(
            letter="C",
            name="Panel (C)",
            page_number=155,
            pdf_index=167,
            quadrant="PANEL_C",
            expected_callouts=["Panel (C)"],
        ),
        SubPanelSpec(
            letter="D",
            name="Panel (D)",
            page_number=156,
            pdf_index=168,
            quadrant="PANEL_D",
            expected_callouts=["Panel (D)"],
        ),
        SubPanelSpec(
            letter="E",
            name="Panel (E)",
            page_number=156,
            pdf_index=168,
            quadrant="PANEL_E",
            expected_callouts=["Panel (E)"],
        ),
    ],
    callout_vocabulary=['High-Frequency Resistance Welding', 'Panel (A)', 'Panel (B)', 'Panel (C)', 'Panel (D)', 'Panel (E)'],
    has_embedded_table=False,
    notes=[
        "Multi-page continuation figure spanning 2 printed pages.",
    ],
    source_anomalies=[],
    clause4_terms=['butt joint', 'high-frequency resistance welding', 'high-frequency seam welding', 'high-frequency upset welding', 'induction coil', 'induction upset welding', 'induction welding', 'induction work coil', 'lap joint', 'resistance seam welding', 'seam weld', 'upset welding'],
)

# Master mapping of remaining Annex B figures
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
