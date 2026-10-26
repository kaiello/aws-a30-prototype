"""Declarative specifications for Annex B Archetype 3 figures (Figures B1–B6).

Source: AWS A3.0M/A3.0:2020 (printed pp. 82–89, PDF indices 94–101).
All figure titles are cross-verified against List of Figures (printed pp. x–xi, PDF indices 10–11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SubPanelSpec:
    letter: str
    name: str
    page_number: int  # printed page
    pdf_index: int
    quadrant: str  # "TL", "TR", "BL", "BR", "FULL", "ROW_1", "ROW_2", etc.
    expected_callouts: List[str] = field(default_factory=list)
    applicable_welds: List[str] = field(default_factory=list)
    cross_clause_refs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SpatialCalloutSpec:
    figure_id: str
    official_title: str
    short_title: str
    pages: List[Tuple[int, int]]  # (pdf_index, printed_page)
    crop_box: Tuple[float, float, float, float]
    sub_panels: List[SubPanelSpec]
    callout_vocabulary: List[str]
    has_embedded_table: bool = False
    embedded_table_header: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    source_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    clause4_terms: List[str] = field(default_factory=list)
    annex_c_clauses: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Figure B1: Joint Types (printed p. 82, PDF index 94)
# ---------------------------------------------------------------------------
SPEC_B1 = SpatialCalloutSpec(
    figure_id="Figure B1",
    official_title="Joint Types",
    short_title="Joint Types",
    pages=[(94, 82)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    has_embedded_table=True,
    embedded_table_header="APPLICABLE WELD TYPES",
    sub_panels=[
        SubPanelSpec(
            letter="(A)",
            name="BUTT JOINT",
            page_number=82,
            pdf_index=94,
            quadrant="ROW_1",
            applicable_welds=[
                "BEVEL-GROOVE",
                "FLARE-BEVEL-GROOVE",
                "FLARE-V-GROOVE",
                "J-GROOVE",
                "SQUARE GROOVE",
                "U-GROOVE",
                "V-GROOVE",
                "BRAZE",
            ],
            cross_clause_refs=["butt joint", "skewed joint"],
        ),
        SubPanelSpec(
            letter="(B)",
            name="CORNER JOINT",
            page_number=82,
            pdf_index=94,
            quadrant="ROW_2",
            applicable_welds=[
                "FILLET",
                "BEVEL-GROOVE",
                "FLARE-BEVEL-GROOVE",
                "FLARE-V-GROOVE",
                "J-GROOVE",
                "SQUARE-GROOVE",
                "U-GROOVE",
                "V-GROOVE",
                "PLUG",
                "SLOT",
                "SPOT",
                "SEAM",
                "PROJECTION",
                "BRAZE",
            ],
            cross_clause_refs=["corner joint", "skewed joint"],
        ),
        SubPanelSpec(
            letter="(C)",
            name="T-JOINT",
            page_number=82,
            pdf_index=94,
            quadrant="ROW_3",
            applicable_welds=[
                "FILLET",
                "BEVEL-GROOVE",
                "FLARE-BEVEL-GROOVE",
                "J-GROOVE",
                "SQUARE-GROOVE",
                "PLUG",
                "SLOT",
                "SPOT",
                "SEAM",
                "PROJECTION",
                "BRAZE",
            ],
            cross_clause_refs=["T-joint", "t-joint", "skewed joint"],
        ),
        SubPanelSpec(
            letter="(D)",
            name="LAP JOINT",
            page_number=82,
            pdf_index=94,
            quadrant="ROW_4",
            applicable_welds=[
                "FILLET",
                "BEVEL-GROOVE",
                "FLARE-BEVEL-GROOVE",
                "J-GROOVE",
                "PLUG",
                "SLOT",
                "SPOT",
                "SEAM",
                "PROJECTION",
                "BRAZE",
            ],
            cross_clause_refs=["lap joint", "skewed joint"],
        ),
        SubPanelSpec(
            letter="(E)",
            name="PARALLEL JOINT",
            page_number=82,
            pdf_index=94,
            quadrant="ROW_5",
            applicable_welds=[
                "BEVEL-GROOVE",
                "FLARE-BEVEL-GROOVE",
                "FLARE-V-GROOVE",
                "J-GROOVE",
                "SQUARE-GROOVE",
                "U-GROOVE",
                "V-GROOVE",
                "EDGE",
                "SEAM",
                "SPOT",
                "PROJECTION",
                "BRAZE",
            ],
            cross_clause_refs=["parallel joint", "edge joint", "skewed joint"],
        ),
    ],
    callout_vocabulary=[
        "BEVEL-GROOVE", "FLARE-BEVEL-GROOVE", "FLARE-V-GROOVE", "J-GROOVE",
        "SQUARE GROOVE", "SQUARE-GROOVE", "U-GROOVE", "V-GROOVE", "BRAZE",
        "FILLET", "PLUG", "SLOT", "SPOT", "SEAM", "PROJECTION", "EDGE"
    ],
    source_anomalies=[
        {
            "anomaly_id": "B1-ANOMALY-01",
            "type": "TYPOGRAPHICAL_HYPHENATION_VARIATION",
            "description": "In panel (A) BUTT JOINT, 'SQUARE GROOVE' is printed without a hyphen, whereas panels (B), (C), and (E) print 'SQUARE-GROOVE'.",
            "source_location": "Figure B1, printed p. 82, PDF index 94, sub-panel (A)",
            "normative_resolution": "Both forms denote square-groove weld per Clause 4 standard designation.",
        },
        {
            "anomaly_id": "B1-ANOMALY-02",
            "type": "TERMINOLOGY_REVISION_C1_5_7",
            "description": "Sub-panel (E) is printed as '(E) PARALLEL JOINT' in the 2020 edition, replacing 'edge joint' from the 2010 edition per Annex C1.5.7. Clause 4 defines 'edge joint' as 'See parallel joint.'",
            "source_location": "Figure B1, printed p. 82, PDF index 94, sub-panel (E)",
            "normative_resolution": "Parallel joint is the normative basic joint type in the 2020 edition (Annex C1.5.7).",
        },
    ],
    clause4_terms=["butt joint", "corner joint", "T-joint", "lap joint", "parallel joint", "edge joint"],
    annex_c_clauses=["C1.5.7"],
)


# ---------------------------------------------------------------------------
# Figure B2: Flanged Joints (printed p. 83, PDF index 95)
# ---------------------------------------------------------------------------
SPEC_B2 = SpatialCalloutSpec(
    figure_id="Figure B2",
    official_title="Flanged Joints",
    short_title="Flanged Joints",
    pages=[(95, 83)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    sub_panels=[
        SubPanelSpec(letter="(A)", name="FLANGED BUTT JOINTS", page_number=83, pdf_index=95, quadrant="TL", cross_clause_refs=["flanged butt joint", "flanged joint"]),
        SubPanelSpec(letter="(B)", name="FLANGED CORNER JOINT", page_number=83, pdf_index=95, quadrant="TR", cross_clause_refs=["flanged corner joint", "flanged joint"]),
        SubPanelSpec(letter="(C)", name="FLANGED T-JOINT", page_number=83, pdf_index=95, quadrant="ML", cross_clause_refs=["flanged T-joint", "flanged joint"]),
        SubPanelSpec(letter="(D)", name="FLANGED LAP JOINTS", page_number=83, pdf_index=95, quadrant="MR", cross_clause_refs=["flanged lap joint", "flanged joint"]),
        SubPanelSpec(letter="(E)", name="FLANGED PARALLEL JOINTS", page_number=83, pdf_index=95, quadrant="BOTTOM", cross_clause_refs=["flanged edge joint", "parallel joint", "flanged joint"]),
    ],
    callout_vocabulary=["FLANGED BUTT JOINTS", "FLANGED CORNER JOINT", "FLANGED T-JOINT", "FLANGED LAP JOINTS", "FLANGED PARALLEL JOINTS"],
    source_anomalies=[
        {
            "anomaly_id": "B2-ANOMALY-01",
            "type": "CROSS_REFERENCE_DIVERGENCE",
            "description": "Sub-panel (E) is labeled '(E) FLANGED PARALLEL JOINTS' in the 2020 figure, but Clause 4's entry for 'flanged edge joint' still says 'See Figure B2(E).' The entry for 'parallel joint' also cites 'See Figures B1(E) and B2(E).'",
            "source_location": "Figure B2, printed p. 83, PDF index 95, sub-panel (E)",
            "normative_resolution": "Figure B2(E) illustrates flanged parallel joints in 2020 edition per C1.5.7.",
        },
        {
            "anomaly_id": "B2-ANOMALY-02",
            "type": "OUTLINED_VECTOR_FONT_LAYER",
            "description": "Sub-panels (A) through (D) labels were rendered as vector outline paths in CAD, while panel (E) was updated as a live text span in the 2020 edition.",
            "source_location": "Figure B2, printed p. 83, PDF index 95",
            "normative_resolution": "Extracted via dual vector geometry correlation and live text span inspection.",
        },
    ],
    clause4_terms=["flanged joint", "flanged butt joint", "flanged corner joint", "flanged T-joint", "flanged lap joint", "flanged edge joint", "parallel joint"],
    annex_c_clauses=["C1.5.7"],
)


# ---------------------------------------------------------------------------
# Figure B3: Spliced Butt Joints (printed p. 84, PDF index 96)
# ---------------------------------------------------------------------------
SPEC_B3 = SpatialCalloutSpec(
    figure_id="Figure B3",
    official_title="Spliced Butt Joints",
    short_title="Spliced Butt Joints",
    pages=[(96, 84)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    sub_panels=[
        SubPanelSpec(
            letter="(A)",
            name="SINGLE-SPLICED BUTT JOINT",
            page_number=84,
            pdf_index=96,
            quadrant="TOP",
            expected_callouts=["SPLICE MEMBER", "JOINT MEMBER"],
            cross_clause_refs=["single-spliced butt joint", "single-spliced joint", "splice member"],
        ),
        SubPanelSpec(
            letter="(B)",
            name="DOUBLE-SPLICED EDGE JOINT WITH FILLER",
            page_number=84,
            pdf_index=96,
            quadrant="BOTTOM",
            expected_callouts=["JOINT MEMBER", "SPLICE MEMBER", "FILLER"],
            cross_clause_refs=["double-spliced butt joint", "filler", "splice member"],
        ),
    ],
    callout_vocabulary=["SPLICE MEMBER", "JOINT MEMBER", "FILLER"],
    source_anomalies=[
        {
            "anomaly_id": "B3-ANOMALY-01",
            "type": "TITLE_SUBPANEL_DISCREPANCY",
            "description": "Figure B3 is titled 'Spliced Butt Joints' and Clause 4 defines 'double-spliced butt joint' with 'See Figure B3(B)', but the printed text in sub-panel (B) reads '(B) DOUBLE-SPLICED EDGE JOINT WITH FILLER'.",
            "source_location": "Figure B3, printed p. 84, PDF index 96, sub-panel (B)",
            "normative_resolution": "The figure illustrates spliced butt joint geometry with splice members and filler; Clause 4 cross-references B3(B) under double-spliced butt joint.",
        },
    ],
    clause4_terms=["single-spliced butt joint", "single-spliced joint", "double-spliced butt joint", "splice member", "filler"],
)


# ---------------------------------------------------------------------------
# Figure B4: Joint Root (printed p. 85, PDF index 97)
# ---------------------------------------------------------------------------
SPEC_B4 = SpatialCalloutSpec(
    figure_id="Figure B4",
    official_title="Joint Root",
    short_title="Joint Root",
    pages=[(97, 85)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    sub_panels=[
        SubPanelSpec(letter="(A)", name="SQUARE-GROOVE BUTT JOINT ROOT", page_number=85, pdf_index=97, quadrant="TL"),
        SubPanelSpec(letter="(B)", name="SINGLE-V-GROOVE BUTT JOINT ROOT", page_number=85, pdf_index=97, quadrant="TR"),
        SubPanelSpec(letter="(C)", name="DOUBLE-V-GROOVE BUTT JOINT ROOT", page_number=85, pdf_index=97, quadrant="ML"),
        SubPanelSpec(letter="(D)", name="FILLET WELD T-JOINT ROOT", page_number=85, pdf_index=97, quadrant="MR"),
        SubPanelSpec(letter="(E)", name="CORNER JOINT ROOT", page_number=85, pdf_index=97, quadrant="BL"),
        SubPanelSpec(letter="(F)", name="LAP JOINT ROOT", page_number=85, pdf_index=97, quadrant="BR"),
    ],
    callout_vocabulary=["Joint root denoted by shading."],
    notes=["Note: Joint root denoted by shading."],
    source_anomalies=[],
    clause4_terms=["joint root"],
)


# ---------------------------------------------------------------------------
# Figure B5: Groove Face, Root Edge, and Root Face (printed p. 86, PDF index 98)
# ---------------------------------------------------------------------------
SPEC_B5 = SpatialCalloutSpec(
    figure_id="Figure B5",
    official_title="Groove Face, Root Edge, and Root Face",
    short_title="Groove Face, Root Edge, and Root Face",
    pages=[(98, 86)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    sub_panels=[
        SubPanelSpec(letter="(A)", name="BEVEL GROOVE WITH ROOT EDGE", page_number=86, pdf_index=98, quadrant="TL", expected_callouts=["ROOT FACE AND GROOVE FACE", "ROOT EDGE"]),
        SubPanelSpec(letter="(B)", name="BEVEL GROOVE WITH ROOT FACE", page_number=86, pdf_index=98, quadrant="TR", expected_callouts=["ROOT FACE AND GROOVE FACE", "GROOVE FACE"]),
        SubPanelSpec(letter="(C)", name="J-GROOVE WITH ROOT FACE", page_number=86, pdf_index=98, quadrant="BL", expected_callouts=["ROOT FACE AND GROOVE FACE", "GROOVE FACE"]),
        SubPanelSpec(letter="(D)", name="U-GROOVE WITH ROOT FACE", page_number=86, pdf_index=98, quadrant="BR", expected_callouts=["ROOT FACE AND GROOVE FACE", "GROOVE FACE"]),
    ],
    callout_vocabulary=["ROOT FACE AND GROOVE FACE", "GROOVE FACE", "ROOT EDGE"],
    source_anomalies=[],
    clause4_terms=["groove face", "root edge", "root face"],
)


# ---------------------------------------------------------------------------
# Figure B6: Bevel Angle, Bevel Face, Bevel Depth, Groove Angle,
# Groove Depth, Bevel Radius, and Root Opening (printed pp. 87–89, PDF indices 99–101)
# ---------------------------------------------------------------------------
SPEC_B6 = SpatialCalloutSpec(
    figure_id="Figure B6",
    official_title="Bevel Angle, Bevel Face, Bevel Depth, Groove Angle, Groove Depth, Bevel Radius, and Root Opening",
    short_title="Bevel Angle and Groove Dimensions",
    pages=[(99, 87), (100, 88), (101, 89)],
    crop_box=(50.0, 45.0, 560.0, 740.0),
    sub_panels=[
        # Page 1 (printed p. 87, PDF index 99)
        SubPanelSpec(letter="(A)", name="SINGLE-BEVEL GROOVE ANGLE AND DEPTH", page_number=87, pdf_index=99, quadrant="TL", expected_callouts=["BEVEL DEPTH", "BEVEL ANGLE", "BEVEL FACE"]),
        SubPanelSpec(letter="(B)", name="SINGLE-J GROOVE RADIUS AND DEPTH", page_number=87, pdf_index=99, quadrant="TR", expected_callouts=["BEVEL DEPTH", "BEVEL ANGLE", "BEVEL RADIUS"]),
        SubPanelSpec(letter="(C)", name="DOUBLE-BEVEL GROOVE DEPTH AND ANGLE", page_number=87, pdf_index=99, quadrant="BL", expected_callouts=["BEVEL DEPTH", "BEVEL ANGLE", "BEVEL FACE"]),
        SubPanelSpec(letter="(D)", name="DOUBLE-J GROOVE DEPTH AND ANGLE", page_number=87, pdf_index=99, quadrant="BR", expected_callouts=["BEVEL DEPTH", "BEVEL ANGLE", "BEVEL FACE"]),
        # Page 2 (printed p. 88, PDF index 100)
        SubPanelSpec(letter="(E)", name="SINGLE-V GROOVE ANGLE AND ROOT OPENING", page_number=88, pdf_index=100, quadrant="TL", expected_callouts=["GROOVE ANGLE", "GROOVE DEPTH", "ROOT OPENING"]),
        SubPanelSpec(letter="(F)", name="SINGLE-U GROOVE ANGLE AND RADIUS", page_number=88, pdf_index=100, quadrant="TR", expected_callouts=["GROOVE ANGLE", "GROOVE DEPTH", "BEVEL RADIUS"]),
        SubPanelSpec(letter="(G)", name="DOUBLE-V GROOVE ANGLE AND DEPTH", page_number=88, pdf_index=100, quadrant="BL", expected_callouts=["GROOVE ANGLE", "GROOVE DEPTH"]),
        SubPanelSpec(letter="(H)", name="DOUBLE-U GROOVE ANGLE AND DEPTH", page_number=88, pdf_index=100, quadrant="BR", expected_callouts=["GROOVE ANGLE", "GROOVE DEPTH"]),
        # Page 3 (printed p. 89, PDF index 101)
        SubPanelSpec(letter="(I)", name="FLARE-BEVEL GROOVE ANGLE", page_number=89, pdf_index=101, quadrant="TL", expected_callouts=["GROOVE ANGLE"]),
        SubPanelSpec(letter="(J)", name="FLARE-V GROOVE ANGLE AND DEPTH", page_number=89, pdf_index=101, quadrant="TR", expected_callouts=["GROOVE ANGLE", "GROOVE DEPTH"]),
        SubPanelSpec(letter="(K)", name="COMPOUND BEVEL AND GROOVE DEPTH", page_number=89, pdf_index=101, quadrant="BL", expected_callouts=["GROOVE ANGLE", "BEVEL DEPTH AND GROOVE DEPTH"]),
        SubPanelSpec(letter="(L)", name="GROOVE IN SOLID MATERIAL", page_number=89, pdf_index=101, quadrant="BR", expected_callouts=["GROOVE DEPTH", "GROOVE IN SOLID MATERIAL"]),
    ],
    callout_vocabulary=[
        "BEVEL DEPTH", "BEVEL ANGLE", "BEVEL FACE", "BEVEL RADIUS",
        "GROOVE ANGLE", "GROOVE DEPTH", "ROOT OPENING",
        "BEVEL DEPTH AND GROOVE DEPTH", "GROOVE IN SOLID MATERIAL"
    ],
    source_anomalies=[
        {
            "anomaly_id": "B6-ANOMALY-01",
            "type": "MULTI_PAGE_CONTINUATION_UNIFICATION",
            "description": "Figure B6 spans 3 consecutive pages (printed pp. 87, 88, 89; PDF indices 99, 100, 101) with 12 sub-panels (A through L). Pages 2 and 3 carry the running caption 'Figure B6 (Continued)—...'",
            "source_location": "Figure B6, printed pp. 87–89, PDF indices 99–101",
            "normative_resolution": "Unified into a single multi-page figure graph with 3 page crops, CONTINUED_ON_PAGE edges, and panel-level page bindings.",
        },
        {
            "anomaly_id": "B6-ANOMALY-02",
            "type": "PROMPT_EDGE_SHAPES_REFERENCE_RECONCILIATION",
            "description": "User prompt refers to Figure B6 as 'Edge Shapes' (the title of Figure B7 on p. 90) spanning (A) through (R). Authentic Figure B6 on pp. 87–89 is 'Bevel Angle... and Root Opening' spanning (A) through (L).",
            "source_location": "Figure B6 vs Figure B7, printed pp. 87–90",
            "normative_resolution": "Figure B6 is ingested across its 3 continuation pages (panels A through L); Figure B7 is noted as the Edge Shapes figure.",
        },
    ],
    clause4_terms=["bevel angle", "bevel depth", "bevel face", "bevel radius", "groove angle", "groove depth", "root opening"],
)

ANNEX_B_SPECS: Dict[str, SpatialCalloutSpec] = {
    "Figure B1": SPEC_B1,
    "Figure B2": SPEC_B2,
    "Figure B3": SPEC_B3,
    "Figure B4": SPEC_B4,
    "Figure B5": SPEC_B5,
    "Figure B6": SPEC_B6,
}
