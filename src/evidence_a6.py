"""Figure A6 (Brazing and Soldering Classification Chart) source specification and CLI.

Instantiates the reusable Archetype 2 Engine (characteristic_decision_tree):
- Stage A: Manifest & crop lock (PDF index 91, printed page 79, viewer page 92).
- Stage B: Text, footnote & 21-entry legend table with underlined designations.
- Stage C: 5-column tree, multi-branch (B-CA, DFB, FB, FS, IB, WS, DS, INS, AB, IRB, EBB, LBB), AB collision.
- Stage D: Multihop, cross-chart join & offline deterministic QA / preflight.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

from src.archetype_decision_tree import (
    DecisionTreeSpec, decision_tree_main, answer_decision_tree_query, run_decision_tree_questions,
)

ELEMENT = "Figure A6"
TITLE = "Brazing and Soldering Classification Chart"
FIGURE_ID = "figure:figure_a6"
PDF_INDEX = 91
PRINTED_PAGE = "79"
REGION = [0.065, 0.085, 0.925, 0.915]
DPI = 300
CROP_SHA256 = "d16a13a7c839e99e253ad1e4d74e579e76b01f0a297601a3a625206f85773ff8"

def _c(nid: str, label: str, col: str, cidx: int, reg: list[float], **extra) -> Dict[str, Any]:
    return {"id": nid, "kind": "category", "label": label, "column": col, "column_index": cidx, "region": reg, "literal_region": reg, **extra}

def _p(nid: str, code: str, label: str, reg: list[float], branch: str, path: str, **extra) -> Dict[str, Any]:
    return {"id": nid, "kind": "process", "code": code, "label": label, "column": "Process", "column_index": 4, "region": reg, "literal_region": reg, "branch_summary": branch, "path_summary": path, **extra}

ROOT_NODE = _c("a6node:brazing_soldering_root", "See Figure A3 <- Brazing and Soldering", "Root", -1, [0.380, 0.120, 0.420, 0.220], kind="root", source_figure="Figure A3")
FOOTNOTES = [_c("a6node:footnote_asterisk", "Footnote *: Pressure normal to faying surfaces.", "Footnote", -1, [0.143, 0.106, 0.164, 0.220], subtype="footnote", text="*Pressure normal to faying surfaces.", marker="*", target_term="Mechanical Loading*")]

CHARACTERISTIC_NODES = [
    # Column 0: Energy Source
    _c("a6node:energy_electrical", "Electrical", "Energy Source", 0, [0.320, 0.246, 0.350, 0.318]),
    _c("a6node:energy_chemical", "Chemical", "Energy Source", 0, [0.650, 0.246, 0.680, 0.318]),
    # Column 1: Thermal Source (Electrical)
    _c("a6node:thermal_elec_arc", "Arc", "Thermal Source", 1, [0.130, 0.360, 0.155, 0.435], energy_source="Electrical"),
    _c("a6node:thermal_elec_resistance", "Resistance", "Thermal Source", 1, [0.180, 0.360, 0.205, 0.435], energy_source="Electrical"),
    _c("a6node:thermal_elec_conduction", "Conduction", "Thermal Source", 1, [0.235, 0.360, 0.260, 0.435], energy_source="Electrical"),
    _c("a6node:thermal_elec_induction", "Induction", "Thermal Source", 1, [0.340, 0.360, 0.365, 0.435], energy_source="Electrical"),
    _c("a6node:thermal_elec_radiation", "Radiation", "Thermal Source", 1, [0.470, 0.360, 0.495, 0.435], energy_source="Electrical"),
    # Column 1: Thermal Source (Chemical)
    _c("a6node:thermal_chem_flame", "Flame Contact", "Thermal Source", 1, [0.590, 0.360, 0.615, 0.435], energy_source="Chemical"),
    _c("a6node:thermal_chem_radiation", "Radiation", "Thermal Source", 1, [0.650, 0.360, 0.675, 0.435], energy_source="Chemical"),
    _c("a6node:thermal_chem_conduction", "Conduction", "Thermal Source", 1, [0.705, 0.360, 0.730, 0.435], energy_source="Chemical"),
    # Column 2: Mechanical Loading* (Pressure)
    _c("a6node:load_elec_res_p", "Pressure", "Mechanical Loading*", 2, [0.180, 0.470, 0.205, 0.550]),
    _c("a6node:load_elec_ind_p", "Pressure", "Mechanical Loading*", 2, [0.390, 0.470, 0.415, 0.550]),
    _c("a6node:load_elec_rad_p", "Pressure", "Mechanical Loading*", 2, [0.540, 0.470, 0.565, 0.550]),
    # Column 3: Shielding
    _c("a6node:shield_arc_flux", "Flux", "Shielding", 3, [0.115, 0.580, 0.135, 0.650]),
    _c("a6node:shield_arc_gas", "Gas", "Shielding", 3, [0.145, 0.580, 0.165, 0.650]),
    _c("a6node:shield_res_flux", "Flux", "Shielding", 3, [0.180, 0.580, 0.200, 0.650]),
    _c("a6node:shield_elec_cond_flux_top", "Flux", "Shielding", 3, [0.220, 0.580, 0.240, 0.650]),
    _c("a6node:shield_elec_cond_flux_bot", "Flux", "Shielding", 3, [0.255, 0.580, 0.275, 0.650]),
    _c("a6node:shield_ind_gas_top", "Gas", "Shielding", 3, [0.305, 0.580, 0.325, 0.650]),
    _c("a6node:shield_ind_flux_top", "Flux", "Shielding", 3, [0.335, 0.580, 0.355, 0.650]),
    _c("a6node:shield_ind_vac_top", "Vacuum", "Shielding", 3, [0.365, 0.580, 0.385, 0.650]),
    _c("a6node:shield_ind_gas_bot", "Gas", "Shielding", 3, [0.395, 0.580, 0.415, 0.650]),
    _c("a6node:shield_ind_vac_bot", "Vacuum", "Shielding", 3, [0.420, 0.580, 0.440, 0.650]),
    _c("a6node:shield_rad_gas_top", "Gas", "Shielding", 3, [0.450, 0.580, 0.470, 0.650]),
    _c("a6node:shield_rad_flux_top", "Flux", "Shielding", 3, [0.480, 0.580, 0.500, 0.650]),
    _c("a6node:shield_rad_vac_top", "Vacuum", "Shielding", 3, [0.510, 0.580, 0.530, 0.650]),
    _c("a6node:shield_rad_gas_bot", "Gas", "Shielding", 3, [0.535, 0.580, 0.555, 0.650]),
    _c("a6node:shield_rad_vac_bot", "Vacuum", "Shielding", 3, [0.560, 0.580, 0.580, 0.650]),
    _c("a6node:shield_chem_flame_flux", "Flux", "Shielding", 3, [0.590, 0.580, 0.610, 0.650]),
    _c("a6node:shield_chem_rad_flux", "Flux", "Shielding", 3, [0.630, 0.580, 0.650, 0.650]),
    _c("a6node:shield_chem_rad_gas", "Gas", "Shielding", 3, [0.660, 0.580, 0.680, 0.650]),
    _c("a6node:shield_chem_cond_flux_top", "Flux", "Shielding", 3, [0.690, 0.580, 0.710, 0.650]),
    _c("a6node:shield_chem_cond_flux_bot", "Flux", "Shielding", 3, [0.720, 0.580, 0.740, 0.650]),
]

PROCESS_NODES = [
    # Electrical -> Arc
    _p("a6node:proc_ab_arc_flux", "AB", "arc brazing", [0.115, 0.710, 0.135, 0.750], "Electrical -> Arc -> [No Mechanical Loading] -> Flux", "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> AB"),
    _p("a6node:proc_ab_arc_gas", "AB", "arc brazing", [0.145, 0.710, 0.165, 0.750], "Electrical -> Arc -> [No Mechanical Loading] -> Gas", "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> AB"),
    # Electrical -> Resistance
    _p("a6node:proc_rb", "RB", "resistance brazing", [0.175, 0.710, 0.195, 0.750], "Electrical -> Resistance -> Pressure -> Flux", "Electrical -> Resistance -> Pressure -> Flux -> RB"),
    _p("a6node:proc_rs", "RS", "resistance soldering", [0.175, 0.760, 0.195, 0.800], "Electrical -> Resistance -> Pressure -> Flux", "Electrical -> Resistance -> Pressure -> Flux -> RS"),
    # Electrical -> Conduction
    _p("a6node:proc_db", "DB", "dip brazing", [0.215, 0.710, 0.235, 0.750], "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Top)", "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Top) -> DB"),
    _p("a6node:proc_uss", "USS", "ultrasonic soldering", [0.215, 0.760, 0.235, 0.800], "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Top)", "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Top) -> USS"),
    _p("a6node:proc_ws_elec", "WS", "wave soldering", [0.250, 0.710, 0.270, 0.750], "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> WS"),
    _p("a6node:proc_ds_elec", "DS", "dip soldering", [0.250, 0.760, 0.270, 0.800], "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> DS"),
    _p("a6node:proc_ins_elec", "INS", "iron soldering", [0.250, 0.810, 0.270, 0.850], "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Electrical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> INS"),
    # Electrical -> Induction
    _p("a6node:proc_ib_ind_gas", "IB", "induction brazing", [0.305, 0.710, 0.325, 0.750], "Electrical -> Induction -> [No Mechanical Loading] -> Gas", "Electrical -> Induction -> [No Mechanical Loading] -> Gas -> IB"),
    _p("a6node:proc_bca_ind_gas", "B-CA", "controlled-atmosphere brazing", [0.305, 0.760, 0.325, 0.800], "Electrical -> Induction -> [No Mechanical Loading] -> Gas", "Electrical -> Induction -> [No Mechanical Loading] -> Gas -> B-CA", is_underlined=True),
    _p("a6node:proc_ib_ind_flux", "IB", "induction brazing", [0.335, 0.710, 0.355, 0.750], "Electrical -> Induction -> [No Mechanical Loading] -> Flux", "Electrical -> Induction -> [No Mechanical Loading] -> Flux -> IB"),
    _p("a6node:proc_is_ind_flux", "IS", "induction soldering", [0.335, 0.760, 0.355, 0.800], "Electrical -> Induction -> [No Mechanical Loading] -> Flux", "Electrical -> Induction -> [No Mechanical Loading] -> Flux -> IS"),
    _p("a6node:proc_ib_ind_vac", "IB", "induction brazing", [0.365, 0.710, 0.385, 0.750], "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum", "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum -> IB"),
    _p("a6node:proc_bca_ind_vac", "B-CA", "controlled-atmosphere brazing", [0.365, 0.760, 0.385, 0.800], "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum", "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum -> B-CA", is_underlined=True),
    _p("a6node:proc_dfb_ind_gas", "DFB", "diffusion brazing", [0.395, 0.710, 0.415, 0.750], "Electrical -> Induction -> Pressure -> Gas", "Electrical -> Induction -> Pressure -> Gas -> DFB"),
    _p("a6node:proc_dfb_ind_vac", "DFB", "diffusion brazing", [0.420, 0.710, 0.440, 0.750], "Electrical -> Induction -> Pressure -> Vacuum", "Electrical -> Induction -> Pressure -> Vacuum -> DFB"),
    # Electrical -> Radiation (Top: No Mechanical Loading)
    _p("a6node:proc_fb_rad_gas", "FB", "furnace brazing", [0.450, 0.710, 0.465, 0.740], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> FB"),
    _p("a6node:proc_irb_rad_gas", "IRB", "infrared brazing", [0.450, 0.745, 0.465, 0.775], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> IRB"),
    _p("a6node:proc_ebb_rad_gas", "EBB", "electron beam brazing", [0.450, 0.780, 0.465, 0.810], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> EBB", is_underlined=True),
    _p("a6node:proc_lbb_rad_gas", "LBB", "laser beam brazing", [0.450, 0.815, 0.465, 0.845], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> LBB", is_underlined=True),
    _p("a6node:proc_bca_rad_gas", "B-CA", "controlled-atmosphere brazing", [0.450, 0.850, 0.465, 0.880], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> B-CA", is_underlined=True),
    _p("a6node:proc_fs_rad_gas", "FS", "furnace soldering", [0.450, 0.885, 0.465, 0.915], "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas -> FS"),
    _p("a6node:proc_fb_rad_flux", "FB", "furnace brazing", [0.480, 0.710, 0.495, 0.740], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> FB"),
    _p("a6node:proc_irb_rad_flux", "IRB", "infrared brazing", [0.480, 0.745, 0.495, 0.775], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> IRB"),
    _p("a6node:proc_irs_rad_flux", "IRS", "infrared soldering", [0.480, 0.780, 0.495, 0.810], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> IRS"),
    _p("a6node:proc_fs_rad_flux", "FS", "furnace soldering", [0.480, 0.815, 0.495, 0.845], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> FS"),
    _p("a6node:proc_ebb_rad_flux", "EBB", "electron beam brazing", [0.480, 0.850, 0.495, 0.880], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> EBB", is_underlined=True),
    _p("a6node:proc_lbb_rad_flux", "LBB", "laser beam brazing", [0.480, 0.885, 0.495, 0.915], "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux -> LBB", is_underlined=True),
    _p("a6node:proc_fb_rad_vac", "FB", "furnace brazing", [0.510, 0.710, 0.525, 0.740], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> FB"),
    _p("a6node:proc_irb_rad_vac", "IRB", "infrared brazing", [0.510, 0.745, 0.525, 0.775], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> IRB"),
    _p("a6node:proc_ebb_rad_vac", "EBB", "electron beam brazing", [0.510, 0.780, 0.525, 0.810], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> EBB", is_underlined=True),
    _p("a6node:proc_lbb_rad_vac", "LBB", "laser beam brazing", [0.510, 0.815, 0.525, 0.845], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> LBB", is_underlined=True),
    _p("a6node:proc_bca_rad_vac", "B-CA", "controlled-atmosphere brazing", [0.510, 0.850, 0.525, 0.880], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> B-CA", is_underlined=True),
    _p("a6node:proc_fs_rad_vac", "FS", "furnace soldering", [0.510, 0.885, 0.525, 0.915], "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> FS"),
    # Electrical -> Radiation (Bottom: Pressure)
    _p("a6node:proc_dfb_rad_gas", "DFB", "diffusion brazing", [0.535, 0.710, 0.555, 0.750], "Electrical -> Radiation -> Pressure -> Gas", "Electrical -> Radiation -> Pressure -> Gas -> DFB"),
    _p("a6node:proc_dfb_rad_vac", "DFB", "diffusion brazing", [0.560, 0.710, 0.580, 0.750], "Electrical -> Radiation -> Pressure -> Vacuum", "Electrical -> Radiation -> Pressure -> Vacuum -> DFB"),
    # Chemical -> Flame Contact
    _p("a6node:proc_tb", "TB", "torch brazing", [0.590, 0.710, 0.610, 0.750], "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flux", "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flux -> TB"),
    _p("a6node:proc_ts", "TS", "torch soldering", [0.590, 0.760, 0.610, 0.800], "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flux", "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flux -> TS"),
    # Chemical -> Radiation
    _p("a6node:proc_fb_chem_flux", "FB", "furnace brazing", [0.630, 0.710, 0.645, 0.750], "Chemical -> Radiation -> [No Mechanical Loading] -> Flux", "Chemical -> Radiation -> [No Mechanical Loading] -> Flux -> FB"),
    _p("a6node:proc_fs_chem_flux", "FS", "furnace soldering", [0.630, 0.760, 0.645, 0.800], "Chemical -> Radiation -> [No Mechanical Loading] -> Flux", "Chemical -> Radiation -> [No Mechanical Loading] -> Flux -> FS"),
    _p("a6node:proc_fb_chem_gas", "FB", "furnace brazing", [0.660, 0.710, 0.675, 0.740], "Chemical -> Radiation -> [No Mechanical Loading] -> Gas", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas -> FB"),
    _p("a6node:proc_bca_chem_gas", "B-CA", "controlled-atmosphere brazing", [0.660, 0.745, 0.675, 0.775], "Chemical -> Radiation -> [No Mechanical Loading] -> Gas", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas -> B-CA", is_underlined=True),
    _p("a6node:proc_fs_chem_gas", "FS", "furnace soldering", [0.660, 0.780, 0.675, 0.810], "Chemical -> Radiation -> [No Mechanical Loading] -> Gas", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas -> FS"),
    # Chemical -> Conduction
    _p("a6node:proc_exb", "EXB", "exothermic brazing", [0.690, 0.710, 0.710, 0.750], "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Top)", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Top) -> EXB", is_underlined=True),
    _p("a6node:proc_ws_chem", "WS", "wave soldering", [0.720, 0.710, 0.740, 0.750], "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> WS"),
    _p("a6node:proc_ds_chem", "DS", "dip soldering", [0.720, 0.760, 0.740, 0.800], "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> DS"),
    _p("a6node:proc_ins_chem", "INS", "iron soldering", [0.720, 0.810, 0.740, 0.850], "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom)", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux (Bottom) -> INS"),
]

LEGEND_TABLE = [
    _c(f"a6node:legend_{code.lower().replace('-', '_')}", f"{code}: {name}", "Legend", -1,
       [round(0.770 + (i % 7) * 0.015, 3), round(0.108 + (i // 7) * 0.270, 3), round(0.770 + (i % 7) * 0.015 + 0.012, 3), round(0.108 + (i // 7) * 0.270 + 0.250, 3)],
       subtype="legend_row", code=code, name=name, is_underlined=code in {"B-CA", "EBB", "EXB", "LBB"})
    for i, (code, name) in enumerate([
        ("AB", "arc brazing"), ("B-CA", "controlled-atmosphere brazing"), ("DB", "dip brazing"),
        ("DS", "dip soldering"), ("DFB", "diffusion brazing"), ("EBB", "electron beam brazing"),
        ("EXB", "exothermic brazing"), ("FB", "furnace brazing"), ("FS", "furnace soldering"),
        ("IB", "induction brazing"), ("IS", "induction soldering"), ("IRB", "infrared brazing"),
        ("IRS", "infrared soldering"), ("INS", "iron soldering"), ("LBB", "laser beam brazing"),
        ("RB", "resistance brazing"), ("RS", "resistance soldering"), ("TB", "torch brazing"),
        ("TS", "torch soldering"), ("USS", "ultrasonic soldering"), ("WS", "wave soldering"),
    ])
]

def _e(src: str, dst: str) -> Dict[str, Any]:
    return {"from": src, "to": dst, "type": "ENCLOSES_ROW" if dst.startswith("a6node:proc_") else "CHART_CONNECTOR"}

EDGES = [
    # Root -> Energy Sources
    _e("a6node:brazing_soldering_root", "a6node:energy_electrical"), _e("a6node:brazing_soldering_root", "a6node:energy_chemical"),
    # Energy -> Thermal
    _e("a6node:energy_electrical", "a6node:thermal_elec_arc"), _e("a6node:energy_electrical", "a6node:thermal_elec_resistance"),
    _e("a6node:energy_electrical", "a6node:thermal_elec_conduction"), _e("a6node:energy_electrical", "a6node:thermal_elec_induction"),
    _e("a6node:energy_electrical", "a6node:thermal_elec_radiation"), _e("a6node:energy_chemical", "a6node:thermal_chem_flame"),
    _e("a6node:energy_chemical", "a6node:thermal_chem_radiation"), _e("a6node:energy_chemical", "a6node:thermal_chem_conduction"),
    # Thermal -> Loading (Pressure branches)
    _e("a6node:thermal_elec_resistance", "a6node:load_elec_res_p"),
    _e("a6node:thermal_elec_induction", "a6node:load_elec_ind_p"),
    _e("a6node:thermal_elec_radiation", "a6node:load_elec_rad_p"),
    # Thermal -> Shielding (Direct branches without Mechanical Loading)
    _e("a6node:thermal_elec_arc", "a6node:shield_arc_flux"), _e("a6node:thermal_elec_arc", "a6node:shield_arc_gas"),
    _e("a6node:thermal_elec_conduction", "a6node:shield_elec_cond_flux_top"), _e("a6node:thermal_elec_conduction", "a6node:shield_elec_cond_flux_bot"),
    _e("a6node:thermal_elec_induction", "a6node:shield_ind_gas_top"), _e("a6node:thermal_elec_induction", "a6node:shield_ind_flux_top"),
    _e("a6node:thermal_elec_induction", "a6node:shield_ind_vac_top"), _e("a6node:thermal_elec_radiation", "a6node:shield_rad_gas_top"),
    _e("a6node:thermal_elec_radiation", "a6node:shield_rad_flux_top"), _e("a6node:thermal_elec_radiation", "a6node:shield_rad_vac_top"),
    _e("a6node:thermal_chem_flame", "a6node:shield_chem_flame_flux"), _e("a6node:thermal_chem_radiation", "a6node:shield_chem_rad_flux"),
    _e("a6node:thermal_chem_radiation", "a6node:shield_chem_rad_gas"), _e("a6node:thermal_chem_conduction", "a6node:shield_chem_cond_flux_top"),
    _e("a6node:thermal_chem_conduction", "a6node:shield_chem_cond_flux_bot"),
    # Loading -> Shielding
    _e("a6node:load_elec_res_p", "a6node:shield_res_flux"), _e("a6node:load_elec_ind_p", "a6node:shield_ind_gas_bot"),
    _e("a6node:load_elec_ind_p", "a6node:shield_ind_vac_bot"), _e("a6node:load_elec_rad_p", "a6node:shield_rad_gas_bot"),
    _e("a6node:load_elec_rad_p", "a6node:shield_rad_vac_bot"),
    # Shielding -> Process
    _e("a6node:shield_arc_flux", "a6node:proc_ab_arc_flux"), _e("a6node:shield_arc_gas", "a6node:proc_ab_arc_gas"),
    _e("a6node:shield_res_flux", "a6node:proc_rb"), _e("a6node:shield_res_flux", "a6node:proc_rs"),
    _e("a6node:shield_elec_cond_flux_top", "a6node:proc_db"), _e("a6node:shield_elec_cond_flux_top", "a6node:proc_uss"),
    _e("a6node:shield_elec_cond_flux_bot", "a6node:proc_ws_elec"), _e("a6node:shield_elec_cond_flux_bot", "a6node:proc_ds_elec"),
    _e("a6node:shield_elec_cond_flux_bot", "a6node:proc_ins_elec"), _e("a6node:shield_ind_gas_top", "a6node:proc_ib_ind_gas"),
    _e("a6node:shield_ind_gas_top", "a6node:proc_bca_ind_gas"), _e("a6node:shield_ind_flux_top", "a6node:proc_ib_ind_flux"),
    _e("a6node:shield_ind_flux_top", "a6node:proc_is_ind_flux"), _e("a6node:shield_ind_vac_top", "a6node:proc_ib_ind_vac"),
    _e("a6node:shield_ind_vac_top", "a6node:proc_bca_ind_vac"), _e("a6node:shield_ind_gas_bot", "a6node:proc_dfb_ind_gas"),
    _e("a6node:shield_ind_vac_bot", "a6node:proc_dfb_ind_vac"), _e("a6node:shield_rad_gas_top", "a6node:proc_fb_rad_gas"),
    _e("a6node:shield_rad_gas_top", "a6node:proc_irb_rad_gas"), _e("a6node:shield_rad_gas_top", "a6node:proc_ebb_rad_gas"),
    _e("a6node:shield_rad_gas_top", "a6node:proc_lbb_rad_gas"), _e("a6node:shield_rad_gas_top", "a6node:proc_bca_rad_gas"),
    _e("a6node:shield_rad_gas_top", "a6node:proc_fs_rad_gas"), _e("a6node:shield_rad_flux_top", "a6node:proc_fb_rad_flux"),
    _e("a6node:shield_rad_flux_top", "a6node:proc_irb_rad_flux"), _e("a6node:shield_rad_flux_top", "a6node:proc_irs_rad_flux"),
    _e("a6node:shield_rad_flux_top", "a6node:proc_fs_rad_flux"), _e("a6node:shield_rad_flux_top", "a6node:proc_ebb_rad_flux"),
    _e("a6node:shield_rad_flux_top", "a6node:proc_lbb_rad_flux"), _e("a6node:shield_rad_vac_top", "a6node:proc_fb_rad_vac"),
    _e("a6node:shield_rad_vac_top", "a6node:proc_irb_rad_vac"), _e("a6node:shield_rad_vac_top", "a6node:proc_ebb_rad_vac"),
    _e("a6node:shield_rad_vac_top", "a6node:proc_lbb_rad_vac"), _e("a6node:shield_rad_vac_top", "a6node:proc_bca_rad_vac"),
    _e("a6node:shield_rad_vac_top", "a6node:proc_fs_rad_vac"), _e("a6node:shield_rad_gas_bot", "a6node:proc_dfb_rad_gas"),
    _e("a6node:shield_rad_vac_bot", "a6node:proc_dfb_rad_vac"), _e("a6node:shield_chem_flame_flux", "a6node:proc_tb"),
    _e("a6node:shield_chem_flame_flux", "a6node:proc_ts"), _e("a6node:shield_chem_rad_flux", "a6node:proc_fb_chem_flux"),
    _e("a6node:shield_chem_rad_flux", "a6node:proc_fs_chem_flux"), _e("a6node:shield_chem_rad_gas", "a6node:proc_fb_chem_gas"),
    _e("a6node:shield_chem_rad_gas", "a6node:proc_bca_chem_gas"), _e("a6node:shield_chem_rad_gas", "a6node:proc_fs_chem_gas"),
    _e("a6node:shield_chem_cond_flux_top", "a6node:proc_exb"), _e("a6node:shield_chem_cond_flux_bot", "a6node:proc_ws_chem"),
    _e("a6node:shield_chem_cond_flux_bot", "a6node:proc_ds_chem"), _e("a6node:shield_chem_cond_flux_bot", "a6node:proc_ins_chem"),
] + [_e("a6node:brazing_soldering_root", row["id"]) for row in LEGEND_TABLE]

SPEC_A6 = DecisionTreeSpec(
    figure_id=FIGURE_ID, element=ELEMENT, title=TITLE, pdf_index=PDF_INDEX, printed_page=PRINTED_PAGE,
    region=REGION, expected_crop_sha256=CROP_SHA256, dpi=DPI,
    columns=["Energy Source", "Thermal Source", "Mechanical Loading*", "Shielding", "Process"],
    root_node=ROOT_NODE, characteristic_nodes=CHARACTERISTIC_NODES, process_nodes=PROCESS_NODES, edges=EDGES,
    legend_table=LEGEND_TABLE, footnotes=FOOTNOTES,
    multi_branch_processes={
        "AB": ["Electrical -> Arc -> [No Mechanical Loading] -> Flux", "Electrical -> Arc -> [No Mechanical Loading] -> Gas"],
        "B-CA": ["Electrical -> Induction -> [No Mechanical Loading] -> Gas", "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum", "Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas"],
        "DFB": ["Electrical -> Induction -> Pressure -> Gas", "Electrical -> Induction -> Pressure -> Vacuum", "Electrical -> Radiation -> Pressure -> Gas", "Electrical -> Radiation -> Pressure -> Vacuum"],
        "FB": ["Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Chemical -> Radiation -> [No Mechanical Loading] -> Flux", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas"],
        "FS": ["Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum", "Chemical -> Radiation -> [No Mechanical Loading] -> Flux", "Chemical -> Radiation -> [No Mechanical Loading] -> Gas"],
        "IB": ["Electrical -> Induction -> [No Mechanical Loading] -> Gas", "Electrical -> Induction -> [No Mechanical Loading] -> Flux", "Electrical -> Induction -> [No Mechanical Loading] -> Vacuum"],
        "WS": ["Electrical -> Conduction -> [No Mechanical Loading] -> Flux", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux"],
        "DS": ["Electrical -> Conduction -> [No Mechanical Loading] -> Flux", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux"],
        "INS": ["Electrical -> Conduction -> [No Mechanical Loading] -> Flux", "Chemical -> Conduction -> [No Mechanical Loading] -> Flux"],
        "IRB": ["Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum"],
        "EBB": ["Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum"],
        "LBB": ["Electrical -> Radiation -> [No Mechanical Loading] -> Gas", "Electrical -> Radiation -> [No Mechanical Loading] -> Flux", "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum"],
    },
    source_anomalies=[
        {"kind": "designation_collision", "code": "AB", "title": "AB Designation Collision", "description": "Figure A6 defines AB = arc brazing, whereas Table A1/A2/A3/A4/Figure A1 and Clause 4 assign AB to adhesive bonding."},
        {"kind": "underlined_designations", "title": "Underlined Legend Designations", "description": "In Figure A6 bottom legend table, B-CA (controlled-atmosphere brazing), EBB (electron beam brazing), EXB (exothermic brazing), and LBB (laser beam brazing) are printed with underlines."},
        {"kind": "scoped_thermal_sources", "title": "Scoped Thermal Source Boxes", "description": "Radiation appears under both Electrical and Chemical energy, and Conduction appears under both Electrical and Chemical energy; each must be scoped to its respective Energy Source to prevent cross-tree branch collapse."},
    ],
    cross_chart_links=[{"from_figure": "Figure A3", "from_label": "Brazing and Soldering", "to_figure": "Figure A6", "to_node": "a6node:brazing_soldering_root"}],
    unsupported_topics=["Fusion Welding", "Arc Welding", "Solid-State Welding", "Oxyfuel Gas Welding", "Thermal Spraying"],
    adapter_version="a6-decision-tree-1.0",
)

def answer_a6_query(graph: Dict[str, Any], query: str, *, knowledge_store: Any = None):
    return answer_decision_tree_query(graph, query, SPEC_A6, knowledge_store=knowledge_store)

def run_questions(root: Path | str, graph_path: Path | str, payload: Dict[str, Any], **kwargs):
    return run_decision_tree_questions(root, graph_path, payload, SPEC_A6, **kwargs)

if __name__ == "__main__":
    decision_tree_main(SPEC_A6, Path("storage/evidence_v2/a6_ingest_001"))
