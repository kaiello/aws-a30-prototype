"""Figure A5 (Solid-State Welding Classification Chart) source specification and CLI.

Instantiates the reusable Archetype 2 Engine (characteristic_decision_tree):
- Stage A: Manifest & crop lock (PDF index 90, printed page 78, viewer page 91).
- Stage B: Text, footnotes & legend table (5 columns, 15 legend entries CEW-UW).
- Stage C: 5-column tree, multi-branch (HPW, DFW, FOW/ROW/CEW, IW), anomalies (CW direct hop, scoped Radiation).
- Stage D: Multihop, cross-chart join & offline deterministic QA / preflight.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

from src.archetype_decision_tree import (
    DecisionTreeSpec,
    decision_tree_main,
    answer_decision_tree_query,
    run_decision_tree_questions,
)

ELEMENT = "Figure A5"
TITLE = "Solid-State Welding Classification Chart"
FIGURE_ID = "figure:figure_a5"
PDF_INDEX = 90
PRINTED_PAGE = "78"
REGION = [0.065, 0.085, 0.925, 0.915]
DPI = 300
CROP_SHA256 = "cc432ea468ffcd6cd3025f0b15c58b2a11a0027a76188698ea4c1809b4957732"

def _c(nid: str, label: str, col: str, cidx: int, reg: list[float], **extra) -> Dict[str, Any]:
    d = {"id": nid, "kind": "category", "label": label, "column": col, "column_index": cidx, "region": reg, "literal_region": reg}
    d.update(extra)
    return d

def _p(nid: str, code: str, label: str, reg: list[float], branch: str, path: str, **extra) -> Dict[str, Any]:
    d = {"id": nid, "kind": "process", "code": code, "label": label, "column": "Process", "column_index": 4, "region": reg, "literal_region": reg, "branch_summary": branch, "path_summary": path}
    d.update(extra)
    return d

ROOT_NODE = _c("a5node:solid_state_welding_root", "See Figure A3 <- Solid-State Welding", "Root", -1, [0.540, 0.120, 0.585, 0.220], kind="root", source_figure="Figure A3")
FOOTNOTES = [_c("a5node:footnote_asterisk", "Footnote *: Pressure normal to faying surfaces.", "Footnote", -1, [0.143, 0.106, 0.164, 0.220], subtype="footnote", text="*Pressure normal to faying surfaces.", marker="*", target_term="Mechanical Loading*")]

CHARACTERISTIC_NODES = [
    # Column 0: Energy Source
    _c("a5node:energy_electrical", "Electrical", "Energy Source", 0, [0.370, 0.246, 0.395, 0.318]),
    _c("a5node:energy_chemical", "Chemical", "Energy Source", 0, [0.560, 0.246, 0.585, 0.318]),
    _c("a5node:energy_mechanical", "Mechanical", "Energy Source", 0, [0.705, 0.246, 0.730, 0.318]),
    # Column 1: Thermal Source
    _c("a5node:thermal_elec_radiation", "Radiation", "Thermal Source", 1, [0.245, 0.360, 0.275, 0.435], energy_source="Electrical"),
    _c("a5node:thermal_elec_induction", "Induction", "Thermal Source", 1, [0.360, 0.360, 0.390, 0.435], energy_source="Electrical"),
    _c("a5node:thermal_elec_resistance", "Resistance", "Thermal Source", 1, [0.435, 0.360, 0.465, 0.435], energy_source="Electrical"),
    _c("a5node:thermal_chem_flame", "Flame Contact", "Thermal Source", 1, [0.495, 0.360, 0.525, 0.435], energy_source="Chemical"),
    _c("a5node:thermal_chem_radiation", "Radiation", "Thermal Source", 1, [0.555, 0.360, 0.585, 0.435], energy_source="Chemical"),
    _c("a5node:thermal_chem_explosion", "Explosion", "Thermal Source", 1, [0.615, 0.360, 0.645, 0.435], energy_source="Chemical"),
    _c("a5node:thermal_mech_friction", "Friction", "Thermal Source", 1, [0.675, 0.360, 0.705, 0.435], energy_source="Mechanical"),
    # Column 2: Mechanical Loading*
    _c("a5node:load_elec_rad_pd", "Pressure Deformation", "Mechanical Loading*", 2, [0.210, 0.470, 0.235, 0.550]),
    _c("a5node:load_elec_rad_p", "Pressure", "Mechanical Loading*", 2, [0.285, 0.470, 0.305, 0.550]),
    _c("a5node:load_elec_ind_p", "Pressure", "Mechanical Loading*", 2, [0.365, 0.470, 0.385, 0.550]),
    _c("a5node:load_elec_res_p", "Pressure", "Mechanical Loading*", 2, [0.420, 0.470, 0.440, 0.550]),
    _c("a5node:load_elec_res_pd", "Pressure Deformation", "Mechanical Loading*", 2, [0.455, 0.470, 0.475, 0.550]),
    _c("a5node:load_chem_flame_p", "Pressure", "Mechanical Loading*", 2, [0.500, 0.470, 0.520, 0.550]),
    _c("a5node:load_chem_rad_p", "Pressure", "Mechanical Loading*", 2, [0.540, 0.470, 0.560, 0.550]),
    _c("a5node:load_chem_rad_pd", "Pressure Deformation", "Mechanical Loading*", 2, [0.575, 0.470, 0.595, 0.550]),
    _c("a5node:load_chem_exp_def", "Deformation", "Mechanical Loading*", 2, [0.620, 0.470, 0.640, 0.550]),
    _c("a5node:load_mech_fric_p", "Pressure", "Mechanical Loading*", 2, [0.660, 0.470, 0.680, 0.550]),
    _c("a5node:load_mech_fric_pd", "Pressure Deformation", "Mechanical Loading*", 2, [0.685, 0.470, 0.705, 0.550]),
    _c("a5node:load_mech_direct_p", "Pressure", "Mechanical Loading*", 2, [0.720, 0.470, 0.740, 0.550]),
    _c("a5node:load_mech_direct_pd", "Pressure Deformation", "Mechanical Loading*", 2, [0.755, 0.470, 0.775, 0.550]),
    # Column 3: Shielding
    _c("a5node:shield_elec_rad_pd_gas", "Gas", "Shielding", 3, [0.150, 0.580, 0.170, 0.650]),
    _c("a5node:shield_elec_rad_pd_vac", "Vacuum", "Shielding", 3, [0.190, 0.580, 0.210, 0.650]),
    _c("a5node:shield_elec_rad_p_gas", "Gas", "Shielding", 3, [0.270, 0.580, 0.290, 0.650]),
    _c("a5node:shield_elec_rad_p_vac", "Vacuum", "Shielding", 3, [0.305, 0.580, 0.325, 0.650]),
    _c("a5node:shield_elec_ind_p_gas", "Gas", "Shielding", 3, [0.350, 0.580, 0.370, 0.650]),
    _c("a5node:shield_elec_ind_p_vac", "Vacuum", "Shielding", 3, [0.385, 0.580, 0.405, 0.650]),
    _c("a5node:shield_chem_rad_p_gas", "Gas", "Shielding", 3, [0.540, 0.580, 0.560, 0.650]),
]

PROCESS_NODES = [
    _p("a5node:proc_hpw_gas", "HPW", "hot pressure welding", [0.150, 0.710, 0.180, 0.750], "Electrical -> Radiation -> Pressure Deformation -> Gas", "Electrical -> Radiation -> Pressure Deformation -> Gas -> HPW"),
    _p("a5node:proc_hpw_vac", "HPW", "hot pressure welding", [0.190, 0.710, 0.220, 0.750], "Electrical -> Radiation -> Pressure Deformation -> Vacuum", "Electrical -> Radiation -> Pressure Deformation -> Vacuum -> HPW"),
    _p("a5node:proc_fow_elec", "FOW", "forge welding", [0.230, 0.710, 0.260, 0.750], "Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Electrical -> Radiation -> Pressure Deformation -> [No Shielding] -> FOW"),
    _p("a5node:proc_row_elec", "ROW", "roll welding", [0.230, 0.760, 0.260, 0.800], "Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Electrical -> Radiation -> Pressure Deformation -> [No Shielding] -> ROW"),
    _p("a5node:proc_cew_elec", "CEW", "coextrusion welding", [0.230, 0.810, 0.260, 0.850], "Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Electrical -> Radiation -> Pressure Deformation -> [No Shielding] -> CEW"),
    _p("a5node:proc_dfw_elec_gas", "DFW", "diffusion welding", [0.270, 0.710, 0.300, 0.750], "Electrical -> Radiation -> Pressure -> Gas", "Electrical -> Radiation -> Pressure -> Gas -> DFW"),
    _p("a5node:proc_dfw_elec_vac", "DFW", "diffusion welding", [0.305, 0.710, 0.335, 0.750], "Electrical -> Radiation -> Pressure -> Vacuum", "Electrical -> Radiation -> Pressure -> Vacuum -> DFW"),
    _p("a5node:proc_iw_gas", "IW", "induction welding", [0.345, 0.710, 0.375, 0.750], "Electrical -> Induction -> Pressure -> Gas", "Electrical -> Induction -> Pressure -> Gas -> IW"),
    _p("a5node:proc_iw_vac", "IW", "induction welding", [0.385, 0.710, 0.415, 0.750], "Electrical -> Induction -> Pressure -> Vacuum", "Electrical -> Induction -> Pressure -> Vacuum -> IW"),
    _p("a5node:proc_uw", "UW", "upset welding", [0.420, 0.710, 0.450, 0.750], "Electrical -> Resistance -> Pressure -> [No Shielding]", "Electrical -> Resistance -> Pressure -> [No Shielding] -> UW"),
    _p("a5node:proc_rsw", "RSW", "resistance spot welding", [0.460, 0.710, 0.490, 0.750], "Electrical -> Resistance -> Pressure Deformation -> [No Shielding]", "Electrical -> Resistance -> Pressure Deformation -> [No Shielding] -> RSW"),
    _p("a5node:proc_rsew", "RSEW", "resistance seam welding", [0.460, 0.760, 0.490, 0.800], "Electrical -> Resistance -> Pressure Deformation -> [No Shielding]", "Electrical -> Resistance -> Pressure Deformation -> [No Shielding] -> RSEW"),
    _p("a5node:proc_pgw", "PGW", "pressure gas welding", [0.500, 0.710, 0.530, 0.750], "Chemical -> Flame Contact -> Pressure -> [No Shielding]", "Chemical -> Flame Contact -> Pressure -> [No Shielding] -> PGW"),
    _p("a5node:proc_dfw_chem_gas", "DFW", "diffusion welding", [0.540, 0.710, 0.570, 0.750], "Chemical -> Radiation -> Pressure -> Gas", "Chemical -> Radiation -> Pressure -> Gas -> DFW"),
    _p("a5node:proc_fow_chem", "FOW", "forge welding", [0.580, 0.710, 0.610, 0.750], "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding] -> FOW"),
    _p("a5node:proc_row_chem", "ROW", "roll welding", [0.580, 0.760, 0.610, 0.800], "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding] -> ROW"),
    _p("a5node:proc_cew_chem", "CEW", "coextrusion welding", [0.580, 0.810, 0.610, 0.850], "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding] -> CEW"),
    _p("a5node:proc_exw", "EXW", "explosion welding", [0.620, 0.710, 0.650, 0.750], "Chemical -> Explosion -> Deformation -> [No Shielding]", "Chemical -> Explosion -> Deformation -> [No Shielding] -> EXW"),
    _p("a5node:proc_frw", "FRW", "friction welding", [0.660, 0.710, 0.690, 0.750], "Mechanical -> Friction -> Pressure -> [No Shielding]", "Mechanical -> Friction -> Pressure -> [No Shielding] -> FRW"),
    _p("a5node:proc_fsw", "FSW", "friction stir welding", [0.660, 0.760, 0.690, 0.800], "Mechanical -> Friction -> Pressure Deformation -> [No Shielding]", "Mechanical -> Friction -> Pressure Deformation -> [No Shielding] -> FSW"),
    _p("a5node:proc_usw", "USW", "ultrasonic welding", [0.720, 0.710, 0.750, 0.750], "Mechanical -> [No Thermal Source Box] -> Pressure -> [No Shielding]", "Mechanical -> [No Thermal Source Box] -> Pressure -> [No Shielding] -> USW"),
    _p("a5node:proc_cw", "CW", "cold welding", [0.760, 0.710, 0.790, 0.750], "Mechanical -> [No Thermal Source Box] -> Pressure Deformation -> [No Shielding]", "Mechanical -> [No Thermal Source Box] -> Pressure Deformation -> [No Shielding] -> CW"),
]

LEGEND_TABLE = [
    _c(f"a5node:legend_{code.lower()}", f"{code}: {name}", "Legend", -1, [round(0.790 + (i % 5) * 0.016, 3), round(0.110 + (i // 5) * 0.265, 3), round(0.790 + (i % 5) * 0.016 + 0.014, 3), round(0.110 + (i // 5) * 0.265 + 0.250, 3)], subtype="legend_row", code=code, name=name)
    for i, (code, name) in enumerate([
        ("CEW", "coextrusion welding"), ("CW", "cold welding"), ("DFW", "diffusion welding"),
        ("EXW", "explosion welding"), ("FOW", "forge welding"), ("FRW", "friction welding"),
        ("FSW", "friction stir welding"), ("HPW", "hot pressure welding"), ("IW", "induction welding"),
        ("PGW", "pressure gas welding"), ("RSEW", "resistance seam welding"), ("RSW", "resistance spot welding"),
        ("ROW", "roll welding"), ("USW", "ultrasonic welding"), ("UW", "upset welding"),
    ])
]

# Explicit Directed Structural Edges
def _e(src: str, dst: str) -> Dict[str, Any]:
    etype = "ENCLOSES_ROW" if dst.startswith("a5node:proc_") else "CHART_CONNECTOR"
    return {"from": src, "to": dst, "type": etype}

EDGES = [
    # Root -> Energy Sources
    _e("a5node:solid_state_welding_root", "a5node:energy_electrical"),
    _e("a5node:solid_state_welding_root", "a5node:energy_chemical"),
    _e("a5node:solid_state_welding_root", "a5node:energy_mechanical"),
    # Energy -> Thermal
    _e("a5node:energy_electrical", "a5node:thermal_elec_radiation"),
    _e("a5node:energy_electrical", "a5node:thermal_elec_induction"),
    _e("a5node:energy_electrical", "a5node:thermal_elec_resistance"),
    _e("a5node:energy_chemical", "a5node:thermal_chem_flame"),
    _e("a5node:energy_chemical", "a5node:thermal_chem_radiation"),
    _e("a5node:energy_chemical", "a5node:thermal_chem_explosion"),
    _e("a5node:energy_mechanical", "a5node:thermal_mech_friction"),
    # Direct skip from Mechanical to Loading (CW & USW)
    _e("a5node:energy_mechanical", "a5node:load_mech_direct_p"),
    _e("a5node:energy_mechanical", "a5node:load_mech_direct_pd"),
    # Thermal -> Loading
    _e("a5node:thermal_elec_radiation", "a5node:load_elec_rad_pd"),
    _e("a5node:thermal_elec_radiation", "a5node:load_elec_rad_p"),
    _e("a5node:thermal_elec_induction", "a5node:load_elec_ind_p"),
    _e("a5node:thermal_elec_resistance", "a5node:load_elec_res_p"),
    _e("a5node:thermal_elec_resistance", "a5node:load_elec_res_pd"),
    _e("a5node:thermal_chem_flame", "a5node:load_chem_flame_p"),
    _e("a5node:thermal_chem_radiation", "a5node:load_chem_rad_p"),
    _e("a5node:thermal_chem_radiation", "a5node:load_chem_rad_pd"),
    _e("a5node:thermal_chem_explosion", "a5node:load_chem_exp_def"),
    _e("a5node:thermal_mech_friction", "a5node:load_mech_fric_p"),
    _e("a5node:thermal_mech_friction", "a5node:load_mech_fric_pd"),
    # Loading -> Shielding
    _e("a5node:load_elec_rad_pd", "a5node:shield_elec_rad_pd_gas"),
    _e("a5node:load_elec_rad_pd", "a5node:shield_elec_rad_pd_vac"),
    _e("a5node:load_elec_rad_p", "a5node:shield_elec_rad_p_gas"),
    _e("a5node:load_elec_rad_p", "a5node:shield_elec_rad_p_vac"),
    _e("a5node:load_elec_ind_p", "a5node:shield_elec_ind_p_gas"),
    _e("a5node:load_elec_ind_p", "a5node:shield_elec_ind_p_vac"),
    _e("a5node:load_chem_rad_p", "a5node:shield_chem_rad_p_gas"),
    # Shielding -> Process
    _e("a5node:shield_elec_rad_pd_gas", "a5node:proc_hpw_gas"),
    _e("a5node:shield_elec_rad_pd_vac", "a5node:proc_hpw_vac"),
    _e("a5node:shield_elec_rad_p_gas", "a5node:proc_dfw_elec_gas"),
    _e("a5node:shield_elec_rad_p_vac", "a5node:proc_dfw_elec_vac"),
    _e("a5node:shield_elec_ind_p_gas", "a5node:proc_iw_gas"),
    _e("a5node:shield_elec_ind_p_vac", "a5node:proc_iw_vac"),
    _e("a5node:shield_chem_rad_p_gas", "a5node:proc_dfw_chem_gas"),
    # Loading -> Process directly (no shielding)
    _e("a5node:load_elec_rad_pd", "a5node:proc_fow_elec"),
    _e("a5node:load_elec_rad_pd", "a5node:proc_row_elec"),
    _e("a5node:load_elec_rad_pd", "a5node:proc_cew_elec"),
    _e("a5node:load_elec_res_p", "a5node:proc_uw"),
    _e("a5node:load_elec_res_pd", "a5node:proc_rsw"),
    _e("a5node:load_elec_res_pd", "a5node:proc_rsew"),
    _e("a5node:load_chem_flame_p", "a5node:proc_pgw"),
    _e("a5node:load_chem_rad_pd", "a5node:proc_fow_chem"),
    _e("a5node:load_chem_rad_pd", "a5node:proc_row_chem"),
    _e("a5node:load_chem_rad_pd", "a5node:proc_cew_chem"),
    _e("a5node:load_chem_exp_def", "a5node:proc_exw"),
    _e("a5node:load_mech_fric_p", "a5node:proc_frw"),
    _e("a5node:load_mech_fric_pd", "a5node:proc_fsw"),
    _e("a5node:load_mech_direct_p", "a5node:proc_usw"),
    _e("a5node:load_mech_direct_pd", "a5node:proc_cw"),
] + [_e("a5node:solid_state_welding_root", row["id"]) for row in LEGEND_TABLE]

SPEC_A5 = DecisionTreeSpec(
    figure_id=FIGURE_ID, element=ELEMENT, title=TITLE, pdf_index=PDF_INDEX, printed_page=PRINTED_PAGE,
    region=REGION, expected_crop_sha256=CROP_SHA256, dpi=DPI,
    columns=["Energy Source", "Thermal Source", "Mechanical Loading*", "Shielding", "Process"],
    root_node=ROOT_NODE,
    characteristic_nodes=CHARACTERISTIC_NODES,
    process_nodes=PROCESS_NODES,
    edges=EDGES,
    legend_table=LEGEND_TABLE,
    footnotes=FOOTNOTES,
    multi_branch_processes={
        "HPW": ["Electrical -> Radiation -> Pressure Deformation -> Gas", "Electrical -> Radiation -> Pressure Deformation -> Vacuum"],
        "DFW": ["Electrical -> Radiation -> Pressure -> Gas", "Electrical -> Radiation -> Pressure -> Vacuum", "Chemical -> Radiation -> Pressure -> Gas"],
        "FOW": ["Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]"],
        "ROW": ["Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]"],
        "CEW": ["Electrical -> Radiation -> Pressure Deformation -> [No Shielding]", "Chemical -> Radiation -> Pressure Deformation -> [No Shielding]"],
        "IW": ["Electrical -> Induction -> Pressure -> Gas", "Electrical -> Induction -> Pressure -> Vacuum"],
    },
    source_anomalies=[
        {"title": "CW and USW Direct Column Hop", "description": "Cold welding (CW) and ultrasonic welding (USW) branch directly from Mechanical energy to Mechanical Loading*, skipping the Thermal Source column entirely."},
        {"title": "Scoped Radiation Boxes", "description": "Radiation thermal source appears under both Electrical and Chemical energy as separate boxes that must remain distinct to avoid branch merging."},
    ],
    cross_chart_links=[{"from_figure": "Figure A3", "from_label": "Solid-State Welding", "to_figure": "Figure A5", "to_node": "a5node:solid_state_welding_root"}],
    unsupported_topics=["Fusion Welding", "Arc Welding", "Oxyfuel Gas Welding", "Brazing", "Soldering", "Thermal Spraying"],
    adapter_version="a5-decision-tree-1.0",
)

def answer_a5_query(graph: Dict[str, Any], query: str, *, knowledge_store: Any = None):
    return answer_decision_tree_query(graph, query, SPEC_A5, knowledge_store=knowledge_store)

def run_questions(root: Path | str, graph_path: Path | str, payload: Dict[str, Any], **kwargs):
    return run_decision_tree_questions(root, graph_path, payload, SPEC_A5, **kwargs)

if __name__ == "__main__":
    decision_tree_main(SPEC_A5, Path("storage/evidence_v2/a5_ingest_001"))
