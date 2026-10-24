"""Figure A4 (Fusion Welding Classification Chart) source specification and CLI.

Instantiates the reusable Archetype 2 Engine (characteristic_decision_tree):
- Stage A: Manifest & crop lock (PDF index 89, printed page 77, viewer page 90).
- Stage B: Text, footnotes & legend table (5 columns, 23 legend entries with MIAW underline).
- Stage C: 5-column characteristic tree & multi-branch relationships (EGW, EBW, AHW anomaly, Conduction leaf, 0 IS_A).
- Stage D: Multihop, cross-chart join & offline deterministic QA / preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.archetype_decision_tree import (
    DecisionTreeSpec,
    authenticate_source,
    build_decision_tree_graph,
    ingest_decision_tree,
    answer_decision_tree_query,
    run_decision_tree_questions,
    _private,
)
from src.evidence_a1_cli import write_private_output

ELEMENT = "Figure A4"
TITLE = "Fusion Welding Classification Chart"
FIGURE_ID = "figure:figure_a4"
PDF_INDEX = 89
PRINTED_PAGE = "77"
REGION = [0.065, 0.085, 0.925, 0.915]
DPI = 300
CROP_SHA256 = "ef4174d8e8bd73345423b4daf40a76db56907a19bbb4c6dad3472519ee7fb032"

COLUMNS = [
    "Energy Source",
    "Thermal Source",
    "Mechanical Loading*",
    "Shielding",
    "Process",
]

# Root entry node from Figure A3
ROOT_NODE = {
    "id": "a4node:fusion_welding_root",
    "kind": "root",
    "label": "See Figure A3 <- Fusion Welding",
    "source_figure": "Figure A3",
    "column": "Root",
    "column_index": -1,
    "region": [0.528, 0.106, 0.581, 0.214],
    "literal_region": [0.540, 0.157, 0.565, 0.202],
}

# Footnote *
FOOTNOTES = [
    {
        "id": "a4node:footnote_asterisk",
        "kind": "category",
        "subtype": "footnote",
        "label": "Footnote *: Pressure normal to faying surfaces.",
        "text": "*Pressure normal to faying surfaces.",
        "marker": "*",
        "target_term": "Mechanical Loading*",
        "region": [0.143, 0.106, 0.164, 0.220],
        "literal_region": [0.143, 0.106, 0.164, 0.220],
    }
]

# 5 Column Characteristic Nodes
CHARACTERISTIC_NODES = [
    # Column 0: Energy Source
    {
        "id": "a4node:energy_electrical",
        "kind": "category",
        "label": "Electrical",
        "column": "Energy Source",
        "column_index": 0,
        "region": [0.428, 0.246, 0.445, 0.318],
        "literal_region": [0.428, 0.246, 0.445, 0.318],
    },
    {
        "id": "a4node:energy_chemical",
        "kind": "category",
        "label": "Chemical",
        "column": "Energy Source",
        "column_index": 0,
        "region": [0.661, 0.246, 0.678, 0.318],
        "literal_region": [0.661, 0.246, 0.678, 0.318],
    },

    # Column 1: Thermal Source (under Electrical)
    {
        "id": "a4node:thermal_arc",
        "kind": "category",
        "label": "Arc",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Electrical",
        "region": [0.256, 0.361, 0.283, 0.433],
        "literal_region": [0.256, 0.361, 0.283, 0.433],
    },
    {
        "id": "a4node:thermal_resistance",
        "kind": "category",
        "label": "Resistance",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Electrical",
        "region": [0.392, 0.363, 0.419, 0.435],
        "literal_region": [0.392, 0.363, 0.419, 0.435],
    },
    {
        "id": "a4node:thermal_radiation",
        "kind": "category",
        "label": "Radiation",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Electrical",
        "region": [0.450, 0.363, 0.478, 0.435],
        "literal_region": [0.450, 0.363, 0.478, 0.435],
    },
    {
        "id": "a4node:thermal_conduction",
        "kind": "category",
        "label": "Conduction",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Electrical",
        "source_anomaly": "unconnected_branch_no_outgoing_edges",
        "region": [0.531, 0.363, 0.558, 0.435],
        "literal_region": [0.531, 0.363, 0.558, 0.435],
    },
    {
        "id": "a4node:thermal_induction",
        "kind": "category",
        "label": "Induction",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Electrical",
        "region": [0.568, 0.363, 0.595, 0.435],
        "literal_region": [0.568, 0.363, 0.595, 0.435],
    },

    # Column 1: Thermal Source (under Chemical)
    {
        "id": "a4node:thermal_flame_contact",
        "kind": "category",
        "label": "Flame Contact",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Chemical",
        "region": [0.615, 0.363, 0.642, 0.435],
        "literal_region": [0.615, 0.363, 0.642, 0.435],
    },
    {
        "id": "a4node:thermal_solid_reactants",
        "kind": "category",
        "label": "Solid Reactants",
        "column": "Thermal Source",
        "column_index": 1,
        "energy_source": "Chemical",
        "region": [0.698, 0.363, 0.725, 0.435],
        "literal_region": [0.698, 0.363, 0.725, 0.435],
    },

    # Column 2: Mechanical Loading*
    {
        "id": "a4node:loading_pressure_deformation",
        "kind": "category",
        "label": "Pressure Deformation",
        "column": "Mechanical Loading*",
        "column_index": 2,
        "footnote_anchor": "*",
        "region": [0.293, 0.464, 0.322, 0.549],
        "literal_region": [0.293, 0.464, 0.322, 0.549],
    },
    {
        "id": "a4node:loading_pressure",
        "kind": "category",
        "label": "Pressure",
        "column": "Mechanical Loading*",
        "column_index": 2,
        "footnote_anchor": "*",
        "region": [0.332, 0.462, 0.360, 0.547],
        "literal_region": [0.332, 0.462, 0.360, 0.547],
    },

    # Column 3: Shielding
    {
        "id": "a4node:shielding_gas",
        "kind": "category",
        "label": "Gas",
        "column": "Shielding",
        "column_index": 3,
        "region": [0.163, 0.574, 0.180, 0.653],
        "literal_region": [0.163, 0.574, 0.180, 0.653],
    },
    {
        "id": "a4node:shielding_flux",
        "kind": "category",
        "label": "Flux",
        "column": "Shielding",
        "column_index": 3,
        "region": [0.261, 0.574, 0.278, 0.653],
        "literal_region": [0.261, 0.574, 0.278, 0.653],
    },
    {
        "id": "a4node:shielding_vacuum",
        "kind": "category",
        "label": "Vacuum",
        "column": "Shielding",
        "column_index": 3,
        "region": [0.456, 0.574, 0.473, 0.653],
        "literal_region": [0.456, 0.574, 0.473, 0.653],
    },
    {
        "id": "a4node:shielding_flame",
        "kind": "category",
        "label": "Flame",
        "column": "Shielding",
        "column_index": 3,
        "region": [0.619, 0.574, 0.636, 0.653],
        "literal_region": [0.619, 0.574, 0.636, 0.653],
    },
]

# Column 4: Process Circles (26 instances, 24 distinct processes)
PROCESS_NODES = [
    # 1. Arc -> Gas
    {
        "id": "a4node:proc_gtaw",
        "kind": "process",
        "code": "GTAW",
        "label": "gas tungsten arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> GTAW",
        "region": [0.133, 0.693, 0.168, 0.738],
    },
    {
        "id": "a4node:proc_gmaw",
        "kind": "process",
        "code": "GMAW",
        "label": "gas metal arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> GMAW",
        "region": [0.133, 0.744, 0.168, 0.790],
    },
    {
        "id": "a4node:proc_paw",
        "kind": "process",
        "code": "PAW",
        "label": "plasma arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> PAW",
        "region": [0.133, 0.795, 0.168, 0.841],
    },
    {
        "id": "a4node:proc_egw_gas",
        "kind": "process",
        "code": "EGW",
        "label": "electrogas welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> EGW",
        "branches": [
            "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> EGW",
            "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> EGW",
        ],
        "region": [0.133, 0.848, 0.168, 0.893],
    },
    {
        "id": "a4node:proc_ahw",
        "kind": "process",
        "code": "AHW",
        "label": "atomic hydrogen welding",
        "column": "Process",
        "column_index": 4,
        "source_anomaly": "omitted_from_bottom_legend_table",
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> AHW",
        "region": [0.173, 0.693, 0.208, 0.738],
    },

    # 2. Arc -> [No Shielding]
    {
        "id": "a4node:proc_caw",
        "kind": "process",
        "code": "CAW",
        "label": "carbon arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> [No Shielding] -> CAW",
        "region": [0.212, 0.693, 0.247, 0.738],
    },
    {
        "id": "a4node:proc_sw",
        "kind": "process",
        "code": "SW",
        "label": "arc stud welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> [No Shielding] -> SW",
        "region": [0.290, 0.744, 0.325, 0.790],
    },

    # 3. Arc -> Flux
    {
        "id": "a4node:proc_smaw",
        "kind": "process",
        "code": "SMAW",
        "label": "shielded metal arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> SMAW",
        "region": [0.251, 0.693, 0.286, 0.738],
    },
    {
        "id": "a4node:proc_saw",
        "kind": "process",
        "code": "SAW",
        "label": "submerged arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> SAW",
        "region": [0.251, 0.744, 0.286, 0.790],
    },
    {
        "id": "a4node:proc_fcaw",
        "kind": "process",
        "code": "FCAW",
        "label": "flux cored arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> FCAW",
        "region": [0.251, 0.795, 0.286, 0.841],
    },
    {
        "id": "a4node:proc_esw_flux",
        "kind": "process",
        "code": "ESW",
        "label": "electroslag welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> ESW",
        "region": [0.368, 0.693, 0.403, 0.738],
    },
    {
        "id": "a4node:proc_egw_flux",
        "kind": "process",
        "code": "EGW",
        "label": "electrogas welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> EGW",
        "branches": [
            "Electrical -> Arc -> [No Mechanical Loading] -> Gas -> EGW",
            "Electrical -> Arc -> [No Mechanical Loading] -> Flux -> EGW",
        ],
        "region": [0.251, 0.848, 0.286, 0.893],
    },

    # 4. Resistance -> Pressure Deformation
    {
        "id": "a4node:proc_fw",
        "kind": "process",
        "code": "FW",
        "label": "flash welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure Deformation -> [No Shielding] -> FW",
        "region": [0.290, 0.693, 0.325, 0.738],
    },
    {
        "id": "a4node:proc_pew",
        "kind": "process",
        "code": "PEW",
        "label": "percussion welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure Deformation -> [No Shielding] -> PEW",
        "region": [0.328, 0.693, 0.363, 0.738],
    },

    # 5. Resistance -> Pressure
    {
        "id": "a4node:proc_miaw",
        "kind": "process",
        "code": "MIAW",
        "label": "magnetically impelled arc welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure -> [No Shielding] -> MIAW",
        "underline": True,
        "region": [0.329, 0.744, 0.364, 0.790],
    },
    {
        "id": "a4node:proc_rsw",
        "kind": "process",
        "code": "RSW",
        "label": "resistance spot welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure -> [No Shielding] -> RSW",
        "region": [0.406, 0.693, 0.441, 0.738],
    },
    {
        "id": "a4node:proc_rsew",
        "kind": "process",
        "code": "RSEW",
        "label": "resistance seam welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure -> [No Shielding] -> RSEW",
        "region": [0.406, 0.744, 0.441, 0.790],
    },
    {
        "id": "a4node:proc_pw",
        "kind": "process",
        "code": "PW",
        "label": "projection welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Resistance -> Pressure -> [No Shielding] -> PW",
        "region": [0.406, 0.795, 0.441, 0.841],
    },

    # 6. Radiation -> Vacuum & No Shielding
    {
        "id": "a4node:proc_ebw_vac",
        "kind": "process",
        "code": "EBW",
        "label": "electron beam welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> EBW",
        "branches": [
            "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> EBW",
            "Electrical -> Radiation -> [No Mechanical Loading] -> [No Shielding] -> EBW",
        ],
        "region": [0.445, 0.693, 0.480, 0.738],
    },
    {
        "id": "a4node:proc_lbw",
        "kind": "process",
        "code": "LBW",
        "label": "laser beam welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Radiation -> [No Mechanical Loading] -> [No Shielding] -> LBW",
        "region": [0.485, 0.693, 0.520, 0.738],
    },
    {
        "id": "a4node:proc_ebw_open",
        "kind": "process",
        "code": "EBW",
        "label": "electron beam welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Radiation -> [No Mechanical Loading] -> [No Shielding] -> EBW",
        "branches": [
            "Electrical -> Radiation -> [No Mechanical Loading] -> Vacuum -> EBW",
            "Electrical -> Radiation -> [No Mechanical Loading] -> [No Shielding] -> EBW",
        ],
        "region": [0.486, 0.744, 0.521, 0.790],
    },

    # 7. Induction -> [No Shielding]
    {
        "id": "a4node:proc_iw",
        "kind": "process",
        "code": "IW",
        "label": "induction welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Electrical -> Induction -> [No Mechanical Loading] -> [No Shielding] -> IW",
        "region": [0.563, 0.693, 0.598, 0.738],
    },

    # 8. Flame Contact -> Flame Shielding
    {
        "id": "a4node:proc_oaw",
        "kind": "process",
        "code": "OAW",
        "label": "oxyacetylene welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flame -> OAW",
        "region": [0.610, 0.693, 0.645, 0.738],
    },
    {
        "id": "a4node:proc_ohw",
        "kind": "process",
        "code": "OHW",
        "label": "oxyhydrogen welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Chemical -> Flame Contact -> [No Mechanical Loading] -> Flame -> OHW",
        "region": [0.610, 0.744, 0.645, 0.790],
    },

    # 9. Flame Contact -> Pressure
    {
        "id": "a4node:proc_pgw",
        "kind": "process",
        "code": "PGW",
        "label": "pressure gas welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Chemical -> Flame Contact -> Pressure -> [No Shielding] -> PGW",
        "region": [0.651, 0.693, 0.686, 0.738],
    },

    # 10. Solid Reactants -> [No Shielding]
    {
        "id": "a4node:proc_tw",
        "kind": "process",
        "code": "TW",
        "label": "thermite welding",
        "column": "Process",
        "column_index": 4,
        "path_summary": "Chemical -> Solid Reactants -> [No Mechanical Loading] -> [No Shielding] -> TW",
        "region": [0.692, 0.693, 0.727, 0.738],
    },
]

# 23-entry bottom legend table
LEGEND_TABLE_DATA = [
    # Column 1
    ("CAW", "carbon arc welding", False),
    ("EBW", "electron beam welding", False),
    ("EGW", "electrogas welding", False),
    ("ESW", "electroslag welding", False),
    ("FCAW", "flux cored arc welding", False),
    ("FW", "flash welding", False),
    ("GMAW", "gas metal arc welding", False),
    ("GTAW", "gas tungsten arc welding", False),
    # Column 2
    ("IW", "induction welding", False),
    ("LBW", "laser beam welding", False),
    ("MIAW", "magnetically impelled arc welding", True),  # Underlined
    ("OAW", "oxyacetylene welding", False),
    ("OHW", "oxyhydrogen welding", False),
    ("PAW", "plasma arc welding", False),
    ("PEW", "percussion welding", False),
    ("PGW", "pressure gas welding", False),
    # Column 3
    ("PW", "projection welding", False),
    ("RSEW", "resistance seam welding", False),
    ("RSW", "resistance spot welding", False),
    ("SAW", "submerged arc welding", False),
    ("SMAW", "shielded metal arc welding", False),
    ("SW", "arc stud welding", False),
    ("TW", "thermite welding", False),
]

LEGEND_TABLE_NODES = [
    {
        "id": f"a4node:legend_{code.lower()}",
        "kind": "category",
        "subtype": "legend_row",
        "code": code,
        "label": f"{code}: {name}",
        "name": name,
        "underline": underline,
        "column": "Legend",
        "column_index": 5,
        "region": [0.739, 0.106, 0.875, 0.893],
    }
    for code, name, underline in LEGEND_TABLE_DATA
]

# Epistemic Edges (0 IS_A promotions)
EDGES = [
    # Root -> Energy Sources
    {"from": "a4node:fusion_welding_root", "to": "a4node:energy_electrical", "type": "CHART_CONNECTOR"},
    {"from": "a4node:fusion_welding_root", "to": "a4node:energy_chemical", "type": "CHART_CONNECTOR"},

    # Energy Electrical -> Thermal Sources
    {"from": "a4node:energy_electrical", "to": "a4node:thermal_arc", "type": "CHART_CONNECTOR"},
    {"from": "a4node:energy_electrical", "to": "a4node:thermal_resistance", "type": "CHART_CONNECTOR"},
    {"from": "a4node:energy_electrical", "to": "a4node:thermal_radiation", "type": "CHART_CONNECTOR"},
    {"from": "a4node:energy_electrical", "to": "a4node:thermal_conduction", "type": "CHART_CONNECTOR"},
    {"from": "a4node:energy_electrical", "to": "a4node:thermal_induction", "type": "CHART_CONNECTOR"},

    # Energy Chemical -> Thermal Sources
    {"from": "a4node:energy_chemical", "to": "a4node:thermal_flame_contact", "type": "CHART_CONNECTOR"},
    {"from": "a4node:energy_chemical", "to": "a4node:thermal_solid_reactants", "type": "CHART_CONNECTOR"},

    # Arc -> Shielding
    {"from": "a4node:thermal_arc", "to": "a4node:shielding_gas", "type": "CHART_CONNECTOR"},
    {"from": "a4node:thermal_arc", "to": "a4node:shielding_flux", "type": "CHART_CONNECTOR"},
    {"from": "a4node:thermal_arc", "to": "a4node:proc_caw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:thermal_arc", "to": "a4node:proc_sw", "type": "ENCLOSES_ROW"},

    # Gas Shielding -> Arc Processes
    {"from": "a4node:shielding_gas", "to": "a4node:proc_gtaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_gas", "to": "a4node:proc_gmaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_gas", "to": "a4node:proc_paw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_gas", "to": "a4node:proc_egw_gas", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_gas", "to": "a4node:proc_ahw", "type": "ENCLOSES_ROW"},

    # Flux Shielding -> Arc Processes
    {"from": "a4node:shielding_flux", "to": "a4node:proc_smaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_flux", "to": "a4node:proc_saw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_flux", "to": "a4node:proc_fcaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_flux", "to": "a4node:proc_esw_flux", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_flux", "to": "a4node:proc_egw_flux", "type": "ENCLOSES_ROW"},

    # Resistance -> Mechanical Loading
    {"from": "a4node:thermal_resistance", "to": "a4node:loading_pressure_deformation", "type": "CHART_CONNECTOR"},
    {"from": "a4node:thermal_resistance", "to": "a4node:loading_pressure", "type": "CHART_CONNECTOR"},

    # Pressure Deformation -> Processes
    {"from": "a4node:loading_pressure_deformation", "to": "a4node:proc_fw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:loading_pressure_deformation", "to": "a4node:proc_pew", "type": "ENCLOSES_ROW"},

    # Pressure -> Resistance Processes
    {"from": "a4node:loading_pressure", "to": "a4node:proc_miaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:loading_pressure", "to": "a4node:proc_rsw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:loading_pressure", "to": "a4node:proc_rsew", "type": "ENCLOSES_ROW"},
    {"from": "a4node:loading_pressure", "to": "a4node:proc_pw", "type": "ENCLOSES_ROW"},

    # Radiation -> Shielding / Processes
    {"from": "a4node:thermal_radiation", "to": "a4node:shielding_vacuum", "type": "CHART_CONNECTOR"},
    {"from": "a4node:shielding_vacuum", "to": "a4node:proc_ebw_vac", "type": "ENCLOSES_ROW"},
    {"from": "a4node:thermal_radiation", "to": "a4node:proc_lbw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:thermal_radiation", "to": "a4node:proc_ebw_open", "type": "ENCLOSES_ROW"},

    # Induction -> Process
    {"from": "a4node:thermal_induction", "to": "a4node:proc_iw", "type": "ENCLOSES_ROW"},

    # Flame Contact -> Shielding / Pressure
    {"from": "a4node:thermal_flame_contact", "to": "a4node:shielding_flame", "type": "CHART_CONNECTOR"},
    {"from": "a4node:shielding_flame", "to": "a4node:proc_oaw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:shielding_flame", "to": "a4node:proc_ohw", "type": "ENCLOSES_ROW"},
    {"from": "a4node:thermal_flame_contact", "to": "a4node:proc_pgw", "type": "ENCLOSES_ROW"},

    # Solid Reactants -> Process
    {"from": "a4node:thermal_solid_reactants", "to": "a4node:proc_tw", "type": "ENCLOSES_ROW"},

    # Footnote Anchor Edge
    {"from": "a4node:loading_pressure", "to": "a4node:footnote_asterisk", "type": "CHART_CONNECTOR"},
]

UNSUPPORTED_TOPICS = [
    "solid-state welding",
    "cold welding",
    "diffusion welding",
    "explosion welding",
    "friction welding",
    "friction stir welding",
    "ultrasonic welding",
    "brazing",
    "soldering",
    "adhesive bonding",
    "thermal spraying",
    "thermal cutting",
    "arc cutting",
    "oxygen cutting",
]

SPEC_A4 = DecisionTreeSpec(
    figure_id=FIGURE_ID,
    element=ELEMENT,
    title=TITLE,
    pdf_index=PDF_INDEX,
    printed_page=PRINTED_PAGE,
    region=REGION,
    expected_crop_sha256=CROP_SHA256,
    dpi=DPI,
    columns=COLUMNS,
    root_node=ROOT_NODE,
    characteristic_nodes=CHARACTERISTIC_NODES,
    process_nodes=PROCESS_NODES,
    edges=EDGES,
    legend_table=LEGEND_TABLE_NODES,
    footnotes=FOOTNOTES,
    multi_branch_processes={
        "EGW": ["Gas", "Flux"],
        "EBW": ["Vacuum", "No Shielding"],
    },
    source_anomalies=[
        {"kind": "legend_omission", "code": "AHW", "description": "AHW is in the decision tree but omitted from the bottom legend table."},
        {"kind": "unconnected_branch", "node": "Conduction", "description": "Conduction under Electrical has no outgoing right-hand branch."},
    ],
    cross_chart_links=[
        {"from_figure": "Figure A3", "from_label": "Fusion Welding", "to_figure": "Figure A4", "to_label": "See Figure A3 <- Fusion Welding"},
    ],
    unsupported_topics=UNSUPPORTED_TOPICS,
)


def ingest(root: Path | str, directory: Path | str):
    return ingest_decision_tree(root, directory, SPEC_A4)


def answer_a4_query(graph: Dict[str, Any], query: str, *, knowledge_store: Any = None):
    return answer_decision_tree_query(graph, query, SPEC_A4, knowledge_store=knowledge_store)


def run_questions(
    root: Path | str,
    graph_path: Path | str,
    payload: Dict[str, Any],
    *,
    query_layer: str = "auto",
    question_planner: Any = None,
    source_observation_path: Path | str | None = None,
):
    return run_decision_tree_questions(
        root, graph_path, payload, SPEC_A4,
        query_layer=query_layer,
        question_planner=question_planner,
        source_observation_path=source_observation_path,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--directory", type=Path, default=Path("storage/evidence_v2/a4_ingest_001"))
    parser.add_argument("--run-questions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    receipt, graph, store = ingest(args.root, args.directory)
    print(f"Ingested {ELEMENT}: {receipt['nodes_count']} nodes, {receipt['edges_count']} edges.")
    print(f"Graph digest: {receipt['graph_sha256']}")

    if args.run_questions:
        q_payload = json.loads(args.run_questions.read_text(encoding="utf-8"))
        ans_receipt = run_questions(args.root, args.directory / "final_projection/graph.json", q_payload)
        if args.output:
            out_path = Path(args.output) if Path(args.output).is_absolute() else args.root / args.output
            if out_path.exists():
                out_path.unlink()
            write_private_output(args.root, args.output, ans_receipt)
            print(f"Answers written to {args.output}")
        else:
            print(f"Answered {len(ans_receipt['answers'])} questions.")


if __name__ == "__main__":
    main()
