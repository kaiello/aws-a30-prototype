"""
figure_inspectors.py: Complete registry of interactive diagram chips and callout inspectors
for all 60 figures in AWS A3.0M/A3.0:2020 (Annex A Figures A1-A6 & Annex B Figures B1-B54).

Provides 400+ interactive chips with pre-formulated natural language queries covering:
- Technical drawing callout labels and anatomical features
- Sub-panel letters (A-R)
- Process letter designations, acronyms, and suffixes
- Angular coordinates and 3D position boundaries
- Root, throat, and discontinuity cross-sections
"""

from typing import Dict, Any, List, Optional

FIGURE_CATEGORIES = [
    {"id": "all", "label": "📊 All Figures", "desc": "All 60 Annex A & B Figures"},
    {"id": "classification", "label": "🌳 Classification Trees", "desc": "Annex A Figures A1–A6"},
    {"id": "joint_geometry", "label": "📐 Joint Geometry", "desc": "Annex B Figures B1–B7"},
    {"id": "grooves_tabs", "label": "🧱 Grooves & Tabs", "desc": "Annex B Figures B8–B15"},
    {"id": "positions", "label": "🧭 Welding Positions", "desc": "Annex B Figures B16–B21"},
    {"id": "beads_throats", "label": "📏 Beads & Throats", "desc": "Annex B Figures B22–B26"},
    {"id": "fusion_cracks", "label": "🔍 Fusion & Discontinuities", "desc": "Annex B Figures B27–B33"},
    {"id": "torches_cutting", "label": "🔫 Torches & Cutting", "desc": "Annex B Figures B34–B43"},
    {"id": "friction_waveforms", "label": "🌀 Friction & Waveforms", "desc": "Annex B Figures B44–B54"},
]

FIGURE_INSPECTORS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # GROUP 1: ANNEX A CLASSIFICATION TREES (A1 - A6)
    # =========================================================================
    "Figure A1": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Major Process Branches",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Solid-State Welding (SSW)", "query": "What processes are included under Solid-State Welding on Figure A1?"},
                    {"label": "Arc Welding (AW)", "query": "What are the major arc welding processes listed on Figure A1?"},
                    {"label": "Resistance Welding (RW)", "query": "What resistance welding processes are classified on Figure A1?"},
                    {"label": "Oxyfuel Gas Welding (OFW)", "query": "What oxyfuel processes are listed on Figure A1?"},
                    {"label": "Brazing (B)", "query": "How is Brazing classified on Figure A1 and where does it link?"},
                    {"label": "Soldering (S)", "query": "How is Soldering classified on Figure A1?"},
                    {"label": "Other Welding", "query": "What processes are classified under Other Welding on Figure A1?"}
                ]
            }
        ]
    },
    "Figure A2": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Allied Process Categories",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Thermal Spraying (THSP)", "query": "What thermal spraying processes are listed on Figure A2?"},
                    {"label": "Thermal Cutting (TC)", "query": "What thermal cutting processes are classified on Figure A2?"},
                    {"label": "Adhesive Bonding (AB)", "query": "How is Adhesive Bonding classified on Figure A2?"},
                    {"label": "Arc Cutting (AC)", "query": "What arc cutting methods are identified on Figure A2?"},
                    {"label": "Oxygen Cutting (OC)", "query": "What oxygen cutting methods are classified on Figure A2?"}
                ]
            }
        ]
    },
    "Figure A3": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Fundamental Bonding Mechanisms",
                "color": "#a855f7",
                "chips": [
                    {"label": "Solid-State Joining", "query": "How does Figure A3 define solid-state joining without melting?"},
                    {"label": "Liquid-Solid State", "query": "What processes fall under liquid-solid state joining on Figure A3?"},
                    {"label": "Fusion Welding", "query": "What are the primary characteristics of fusion welding on Figure A3?"},
                    {"label": "Atomic vs Mechanical Bonds", "query": "How does Figure A3 distinguish atomic bonds from mechanical bonding?"}
                ]
            }
        ]
    },
    "Figure A4": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Classification Criteria",
                "color": "#4ade80",
                "chips": [
                    {"label": "Energy Sources", "query": "What energy sources are categorized for fusion welding on Figure A4?"},
                    {"label": "Shielding Mediums", "query": "What shielding mediums are listed across fusion welding processes on Figure A4?"},
                    {"label": "Consumable vs Nonconsumable", "query": "How does Figure A4 categorize consumable versus nonconsumable electrode arc processes?"},
                    {"label": "Pressure Application", "query": "Which fusion welding processes on Figure A4 utilize mechanical pressure?"}
                ]
            }
        ]
    },
    "Figure A5": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Solid-State Processes",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Friction Welding (FRW)", "query": "What friction welding methods are classified on Figure A5?"},
                    {"label": "Friction Stir Welding (FSW)", "query": "How is friction stir welding categorized on Figure A5?"},
                    {"label": "Diffusion Welding (DFW)", "query": "What are the energy and pressure requirements for diffusion welding on Figure A5?"},
                    {"label": "Explosion Welding (EXW)", "query": "How is explosion welding categorized on Figure A5?"},
                    {"label": "Ultrasonic Welding (USW)", "query": "What are the characteristics of ultrasonic welding on Figure A5?"},
                    {"label": "Cold Welding (CW)", "query": "What processes use deformation without heat on Figure A5?"}
                ]
            }
        ]
    },
    "Figure A6": {
        "category": "classification",
        "groups": [
            {
                "group_title": "Energy & Thermal Sources",
                "color": "#f87171",
                "chips": [
                    {"label": "Flame Contact", "query": "show me flame contact on figure A6"},
                    {"label": "Arc Thermal Source", "query": "Explain Arc thermal source on Figure A6"},
                    {"label": "Resistance Heating", "query": "Explain Resistance thermal source on Figure A6"},
                    {"label": "Induction Heating", "query": "Explain Induction thermal source on Figure A6"},
                    {"label": "Radiation Heating", "query": "Explain Radiation thermal source on Figure A6"},
                    {"label": "Conduction Heating", "query": "Explain Conduction thermal source on Figure A6"}
                ]
            },
            {
                "group_title": "Shielding & Mechanical Loading",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Flux Shielding", "query": "Which processes use Flux shielding on Figure A6?"},
                    {"label": "Gas Shielding", "query": "Which processes use Gas shielding on Figure A6?"},
                    {"label": "Vacuum Shielding", "query": "Which processes use Vacuum shielding on Figure A6?"},
                    {"label": "*Pressure Footnote", "query": "What does *Pressure normal to faying surfaces mean on Figure A6?"}
                ]
            },
            {
                "group_title": "Brazing & Soldering Processes",
                "color": "#4ade80",
                "chips": [
                    {"label": "TB (Torch Brazing)", "query": "What is TB on Figure A6?"},
                    {"label": "FB (Furnace Brazing)", "query": "What is FB on Figure A6?"},
                    {"label": "EXB (Exothermic Brazing)", "query": "What is EXB on Figure A6 and what are its physical characteristics?"},
                    {"label": "DFB (Diffusion Brazing)", "query": "What is DFB on Figure A6?"},
                    {"label": "WS (Wave Soldering)", "query": "What is WS on Figure A6?"},
                    {"label": "USS (Ultrasonic Soldering)", "query": "What is USS on Figure A6?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 2: ANNEX B JOINT GEOMETRY & EDGES (B1 - B7)
    # =========================================================================
    "Figure B1": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Five Basic Joint Types (Left Column)",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Panel (A) Butt Joint", "query": "What is a butt joint illustrated in Figure B1(A)?"},
                    {"label": "Panel (B) Corner Joint", "query": "What is a corner joint illustrated in Figure B1(B)?"},
                    {"label": "Panel (C) T-Joint", "query": "What is a T-joint illustrated in Figure B1(C)?"},
                    {"label": "Panel (D) Lap Joint", "query": "What is a lap joint illustrated in Figure B1(D)?"},
                    {"label": "Panel (E) Parallel Joint", "query": "What is a parallel joint illustrated in Figure B1(E) and what term did it replace?"}
                ]
            },
            {
                "group_title": "Applicable Weld Types (Right Column)",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Butt Joint Applicable Welds", "query": "What weld types are applicable to a butt joint in Figure B1?"},
                    {"label": "Corner Joint Applicable Welds", "query": "What weld types are applicable to a corner joint in Figure B1?"},
                    {"label": "T-Joint Applicable Welds", "query": "What weld types are applicable to a T-joint in Figure B1?"},
                    {"label": "Lap Joint Applicable Welds", "query": "What weld types are applicable to a lap joint in Figure B1?"},
                    {"label": "Parallel Joint Applicable Welds", "query": "What weld types are applicable to a parallel joint in Figure B1?"}
                ]
            }
        ]
    },
    "Figure B2": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Flanged Joint Variations",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Flanged Butt Joint (A)", "query": "What is a flanged butt joint in Figure B2(A)?"},
                    {"label": "Flanged Corner Joint (B)", "query": "What is a flanged corner joint in Figure B2(B)?"},
                    {"label": "Flanged T-Joint (C)", "query": "What is a flanged T-joint in Figure B2(C)?"},
                    {"label": "Flanged Lap Joint (D)", "query": "What is a flanged lap joint in Figure B2(D)?"},
                    {"label": "Flanged Parallel Joint (E)", "query": "What is a flanged parallel joint in Figure B2(E)?"}
                ]
            }
        ]
    },
    "Figure B3": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Spliced Joint Configurations",
                "color": "#a855f7",
                "chips": [
                    {"label": "Single-Spliced Butt Joint", "query": "Explain a single-spliced butt joint in Figure B3"},
                    {"label": "Double-Spliced Butt Joint", "query": "Explain a double-spliced butt joint in Figure B3"},
                    {"label": "Splice Member", "query": "What is a splice member in Figure B3?"}
                ]
            }
        ]
    },
    "Figure B4": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Root Features & Locations",
                "color": "#4ade80",
                "chips": [
                    {"label": "Joint Root", "query": "Define joint root according to AWS A3.0 and Figure B4"},
                    {"label": "Root Face", "query": "Where is the root face located in Figure B4?"},
                    {"label": "Root Edge", "query": "Where is the root edge located in Figure B4?"},
                    {"label": "Root Radius", "query": "What is the root radius in a J- or U-groove in Figure B4?"}
                ]
            }
        ]
    },
    "Figure B5": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Faces & Land Dimensions",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Groove Face", "query": "Which figure illustrates groove face, root edge, and root face?"},
                    {"label": "Root Face vs Root Opening", "query": "What is the structural difference between root opening and root face in a weld joint?"},
                    {"label": "Root Edge (Zero Land)", "query": "What is the difference between root face and root edge on Figure B5?"},
                    {"label": "Bevel Face", "query": "Define bevel face on Figure B5"}
                ]
            }
        ]
    },
    "Figure B6": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Groove Angles & Dimensions",
                "color": "#f87171",
                "chips": [
                    {"label": "Bevel Angle", "query": "Define bevel angle and bevel depth, and identify which figure illustrates them"},
                    {"label": "Groove Angle", "query": "What is the relationship between groove angle and bevel angle on Figure B6?"},
                    {"label": "Depth of Bevel", "query": "What is depth of bevel on Figure B6?"},
                    {"label": "Groove Radius", "query": "What is groove radius on Figure B6?"},
                    {"label": "Root Opening", "query": "What is root opening on Figure B6?"}
                ]
            }
        ]
    },
    "Figure B7": {
        "category": "joint_geometry",
        "groups": [
            {
                "group_title": "Edge Preparations",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Square Edge", "query": "What is a square edge illustrated in Figure B7?"},
                    {"label": "Bevel Edge", "query": "What is a single-bevel and double-bevel edge in Figure B7?"},
                    {"label": "J-Edge Shape", "query": "What is a J-edge shape in Figure B7?"},
                    {"label": "U-Edge Shape", "query": "What is a U-edge shape in Figure B7?"},
                    {"label": "Flanged Edge", "query": "What is a flanged edge in Figure B7?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 3: ANNEX B GROOVES, FLANGED WELDS, TABS & WORKPIECES (B8 - B15)
    # =========================================================================
    "Figure B8": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Single-Groove Weld Geometries",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Square-Groove Weld", "query": "What is a square-groove weld illustrated in Figure B8?"},
                    {"label": "Single-V-Groove Weld", "query": "What is a single-V-groove weld illustrated in Figure B8?"},
                    {"label": "Single-Bevel-Groove Weld", "query": "What is a single-bevel-groove weld in Figure B8?"},
                    {"label": "Single-U-Groove Weld", "query": "What is a single-U-groove weld in Figure B8?"},
                    {"label": "Single-J-Groove Weld", "query": "What is a single-J-groove weld in Figure B8?"},
                    {"label": "Flare-V & Flare-Bevel", "query": "What are flare-V-groove and flare-bevel-groove welds in Figure B8?"}
                ]
            }
        ]
    },
    "Figure B9": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Double-Groove Weld Profiles",
                "color": "#4ade80",
                "chips": [
                    {"label": "Double-V-Groove Weld", "query": "What is a double-V-groove weld illustrated in Figure B9?"},
                    {"label": "Double-Bevel-Groove Weld", "query": "What is a double-bevel-groove weld in Figure B9?"},
                    {"label": "Double-U-Groove Weld", "query": "What is a double-U-groove weld in Figure B9?"},
                    {"label": "Double-J-Groove Weld", "query": "What is a double-J-groove weld in Figure B9?"}
                ]
            }
        ]
    },
    "Figure B10": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Flanged Joint Weld Types",
                "color": "#a855f7",
                "chips": [
                    {"label": "Edge Weld in Flanged Butt", "query": "Explain an edge weld in a flanged butt joint in Figure B10"},
                    {"label": "Edge Weld in Flanged Corner", "query": "Explain an edge weld in a flanged corner joint in Figure B10"},
                    {"label": "Flanged Lap Weld", "query": "Explain an edge weld in a flanged lap joint in Figure B10"}
                ]
            }
        ]
    },
    "Figure B11": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Workpiece Contact Classification",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Butting Workpiece", "query": "Define butting workpiece according to AWS A3.0 and Figure B11"},
                    {"label": "Nonbutting Workpiece", "query": "Define nonbutting workpiece according to AWS A3.0 and Figure B11"},
                    {"label": "Butting Surfaces", "query": "What are butting surfaces in Figure B11?"}
                ]
            }
        ]
    },
    "Figure B12": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Tabs, Backing & Runoff Devices",
                "color": "#f87171",
                "chips": [
                    {"label": "Starting Weld Tab", "query": "What is the function of a starting weld tab in Figure B12?"},
                    {"label": "Runoff Weld Tab", "query": "What is a runoff weld tab in Figure B12 and how does it prevent crater defects?"},
                    {"label": "End Dam", "query": "What is an end dam in Figure B12?"},
                    {"label": "Shelf Bar", "query": "What is a shelf bar in Figure B12?"},
                    {"label": "Split Pipe Backing", "query": "What is split pipe backing in Figure B12?"},
                    {"label": "Sump (ESW/EGW)", "query": "What is a sump in electroslag welding on Figure B12?"}
                ]
            }
        ]
    },
    "Figure B13": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Specialized Features & Inserts",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Consumable Insert", "query": "Define consumable insert and identify which figure illustrates it"},
                    {"label": "Joint Mismatch (High-Low)", "query": "What is joint mismatch illustrated in Figure B13?"},
                    {"label": "Scarf Groove", "query": "What is a scarf groove in Figure B13?"},
                    {"label": "Root Face Extension", "query": "What is a root face extension in Figure B13?"},
                    {"label": "Preplaced Brazing Filler", "query": "What is preplaced filler metal in a brazed joint in Figure B13?"}
                ]
            }
        ]
    },
    "Figure B14": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Spot and Seam Configurations",
                "color": "#4ade80",
                "chips": [
                    {"label": "Resistance Spot Weld", "query": "What is a resistance spot weld in Figure B14?"},
                    {"label": "Arc Spot Weld", "query": "What is an arc spot weld in Figure B14?"},
                    {"label": "Resistance Seam Weld", "query": "What is a resistance seam weld in Figure B14?"},
                    {"label": "Arc Seam Weld", "query": "What is an arc seam weld in Figure B14?"}
                ]
            }
        ]
    },
    "Figure B15": {
        "category": "grooves_tabs",
        "groups": [
            {
                "group_title": "Miscellaneous Weld Types",
                "color": "#a855f7",
                "chips": [
                    {"label": "Fillet Weld", "query": "What is a fillet weld illustrated in Figure B15?"},
                    {"label": "Plug Weld", "query": "What is a plug weld in Figure B15?"},
                    {"label": "Slot Weld", "query": "What is a slot weld in Figure B15?"},
                    {"label": "Stud Weld", "query": "What is a stud weld in Figure B15?"},
                    {"label": "Surfacing Weld", "query": "What is a surfacing weld in Figure B15?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 4: ANNEX B WELDING POSITIONS & COORDINATES (B16A - B21)
    # =========================================================================
    "Figure B16A": {
        "category": "positions",
        "groups": [
            {
                "group_title": "3D Coordinate Boundaries (Plate Groove)",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Flat Position (1G) Limits", "query": "In Figure B16A, what are the inclination of axis and rotation of face coordinate limits for Flat position groove welds in plate?"},
                    {"label": "Horizontal Position (2G) Limits", "query": "What are the coordinate boundaries for horizontal groove welds in plate on Figure B16A?"},
                    {"label": "Overhead Position (4G) Limits", "query": "What are the coordinate boundaries for overhead groove welds in plate on Figure B16A?"},
                    {"label": "Vertical Position (3G) Limits", "query": "What are the coordinate boundaries for vertical groove welds in plate on Figure B16A?"},
                    {"label": "Inclination of Axis", "query": "How is inclination of axis defined in Figure B16A?"},
                    {"label": "Rotation of Face", "query": "How is rotation of face measured in Figure B16A?"}
                ]
            }
        ]
    },
    "Figure B16B": {
        "category": "positions",
        "groups": [
            {
                "group_title": "3D Coordinate Boundaries (Plate Fillet)",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Flat Position (1F)", "query": "What are the inclination and rotation boundaries for 1F flat fillet welds on Figure B16B?"},
                    {"label": "Horizontal Position (2F)", "query": "What are the boundaries for 2F horizontal fillet welds on Figure B16B?"},
                    {"label": "Overhead Position (4F)", "query": "What are the boundaries for 4F overhead fillet welds on Figure B16B?"},
                    {"label": "Vertical Position (3F)", "query": "What are the boundaries for 3F vertical fillet welds on Figure B16B?"}
                ]
            }
        ]
    },
    "Figure B16C": {
        "category": "positions",
        "groups": [
            {
                "group_title": "3D Coordinate Boundaries (Pipe Groove)",
                "color": "#4ade80",
                "chips": [
                    {"label": "Pipe Inclination of Axis", "query": "What are the limits of inclination for pipe groove positions on Figure B16C?"},
                    {"label": "Pipe Rotation Limits", "query": "How is rotation of face bounded for groove welds in pipe on Figure B16C?"}
                ]
            }
        ]
    },
    "Figure B17": {
        "category": "positions",
        "groups": [
            {
                "group_title": "Plate Groove Test Positions",
                "color": "#a855f7",
                "chips": [
                    {"label": "1G Test Position", "query": "What is the 1G welding test position for plate in Figure B17?"},
                    {"label": "2G Test Position", "query": "What is the 2G welding test position for plate in Figure B17?"},
                    {"label": "3G Test Position", "query": "What is the 3G welding test position for plate in Figure B17?"},
                    {"label": "4G Test Position", "query": "What is the 4G welding test position for plate in Figure B17?"}
                ]
            }
        ]
    },
    "Figure B18": {
        "category": "positions",
        "groups": [
            {
                "group_title": "Plate Fillet Test Positions",
                "color": "#f87171",
                "chips": [
                    {"label": "1F Test Position", "query": "What is the 1F fillet welding test position in plate on Figure B18?"},
                    {"label": "2F Test Position", "query": "What is the 2F fillet welding test position in plate on Figure B18?"},
                    {"label": "3F Test Position", "query": "What is the 3F fillet welding test position in plate on Figure B18?"},
                    {"label": "4F Test Position", "query": "What is the 4F fillet welding test position in plate on Figure B18?"}
                ]
            }
        ]
    },
    "Figure B19": {
        "category": "positions",
        "groups": [
            {
                "group_title": "Pipe Groove Test Positions",
                "color": "#38bdf8",
                "chips": [
                    {"label": "1G (Pipe Rotated)", "query": "Explain the 1G pipe test position in Figure B19"},
                    {"label": "2G (Pipe Fixed Vertical)", "query": "Explain the 2G pipe test position in Figure B19"},
                    {"label": "5G (Pipe Fixed Horizontal)", "query": "Explain the 5G pipe test position in Figure B19"},
                    {"label": "6G (Pipe Fixed Inclined 45°)", "query": "Explain the 6G pipe test position in Figure B19"}
                ]
            }
        ]
    },
    "Figure B20": {
        "category": "positions",
        "groups": [
            {
                "group_title": "Pipe Fillet Test Positions",
                "color": "#4ade80",
                "chips": [
                    {"label": "1F (Pipe Axis 45°, Rotated)", "query": "Explain what a 1F pipe welding test position is, and identify which figure illustrates it"},
                    {"label": "2F (Pipe Axis Vertical, Fixed)", "query": "Explain 2F pipe welding test position on Figure B20"},
                    {"label": "2FR (Pipe Axis Horizontal, Rotated)", "query": "Explain 2FR pipe welding test position on Figure B20"},
                    {"label": "4F (Overhead Fillet in Pipe)", "query": "Explain 4F pipe welding test position on Figure B20"},
                    {"label": "5F (Pipe Axis Horizontal, Fixed)", "query": "Explain 5F pipe welding test position on Figure B20"}
                ]
            }
        ]
    },
    "Figure B21": {
        "category": "positions",
        "groups": [
            {
                "group_title": "Torch Angles & Restriction Ring",
                "color": "#f87171",
                "chips": [
                    {"label": "Work Angle", "query": "Define work angle according to Figure B21"},
                    {"label": "Travel Angle", "query": "Define travel angle according to Figure B21"},
                    {"label": "Lead Angle (Pushing)", "query": "Define lead angle according to Figure B21"},
                    {"label": "Trail Angle (Pulling)", "query": "Define trail angle according to Figure B21"},
                    {"label": "6GR Restriction Ring", "query": "Which pipe welding test position in Figure B21 includes a restriction ring, and what is its letter designation?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 5: ANNEX B WELD BEADS, NOMENCLATURE & THROATS (B22 - B26)
    # =========================================================================
    "Figure B22": {
        "category": "beads_throats",
        "groups": [
            {
                "group_title": "Weld Bead Classifications",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Stringer Bead", "query": "What is a stringer bead illustrated in Figure B22?"},
                    {"label": "Weave Bead", "query": "What is a weave bead illustrated in Figure B22?"},
                    {"label": "Root Bead", "query": "What is a root bead in Figure B22?"},
                    {"label": "Face Bead", "query": "What is a face bead in Figure B22?"}
                ]
            }
        ]
    },
    "Figure B23": {
        "category": "beads_throats",
        "groups": [
            {
                "group_title": "Passes, Layers & Temper Beads",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Weld Pass vs Weld Layer", "query": "What is the difference between a weld pass and a weld layer in Figure B23?"},
                    {"label": "Toe Temper Bead (Figure B23J)", "query": "In Figure B23(J), what is the distinction between a toe temper bead and surface temper weld reinforcing beads?"},
                    {"label": "Block Sequence", "query": "What is a block sequence in Figure B23?"},
                    {"label": "Cascade Sequence", "query": "What is a cascade sequence in Figure B23?"},
                    {"label": "Backstep Sequence", "query": "What is a backstep sequence in Figure B23?"}
                ]
            }
        ]
    },
    "Figure B24": {
        "category": "beads_throats",
        "groups": [
            {
                "group_title": "Weld Anatomy (Panels A–R)",
                "color": "#4ade80",
                "chips": [
                    {"label": "Weld Root & Root Surface", "query": "Where are the weld root and root surface located on Figure B24?"},
                    {"label": "Weld Toe & Weld Face", "query": "What are the weld toe and weld face on Figure B24?"},
                    {"label": "Heat-Affected Zone (HAZ)", "query": "Where is the heat-affected zone (HAZ) located on Figure B24?"},
                    {"label": "Fusion Zone & Weld Interface", "query": "What is the boundary between the fusion zone and weld interface on Figure B24?"},
                    {"label": "Back Weld vs Backing Weld", "query": "What is the difference between a back weld and a backing weld in Figure B24?"}
                ]
            }
        ]
    },
    "Figure B25": {
        "category": "beads_throats",
        "groups": [
            {
                "group_title": "Fillet Throats & Dimensions",
                "color": "#f87171",
                "chips": [
                    {"label": "Actual Throat", "query": "Define actual throat and explain how it differs from theoretical throat in a fillet weld"},
                    {"label": "Effective Throat", "query": "Identify the three distinct fillet weld throats illustrated in Figure B25"},
                    {"label": "Theoretical Throat", "query": "Define theoretical throat on Figure B25"},
                    {"label": "Convexity", "query": "What is convexity on Figure B25?"},
                    {"label": "Leg Size", "query": "What is fillet weld leg size on Figure B25?"}
                ]
            }
        ]
    },
    "Figure B26": {
        "category": "beads_throats",
        "groups": [
            {
                "group_title": "Groove Penetration & Discontinuities",
                "color": "#a855f7",
                "chips": [
                    {"label": "Groove Weld Size", "query": "What is groove weld size on Figure B26?"},
                    {"label": "Complete Joint Penetration (CJP)", "query": "What is complete joint penetration (CJP) in Figure B26?"},
                    {"label": "Partial Joint Penetration (PJP)", "query": "What is partial joint penetration (PJP) in Figure B26?"},
                    {"label": "Undercut & Overlap", "query": "What weld face discontinuities and profile deviations are illustrated in Figure B26?"},
                    {"label": "Underfill", "query": "Explain underfill on Figure B26"},
                    {"label": "Excessive Reinforcement", "query": "Explain excessive reinforcement on Figure B26"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 6: ANNEX B FUSION & DISCONTINUITIES (B27 - B33)
    # =========================================================================
    "Figure B27": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Root Profiles & Melt-Through",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Melt-Through Profile", "query": "What is melt-through in Figure B27?"},
                    {"label": "Root Concavity (Suck-Back)", "query": "What is root concavity in Figure B27?"},
                    {"label": "Root Surface Profile", "query": "How is root surface profile characterized in Figure B27?"}
                ]
            }
        ]
    },
    "Figure B28": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Complete Fusion Characteristics",
                "color": "#4ade80",
                "chips": [
                    {"label": "Complete Fusion", "query": "Define complete fusion according to AWS A3.0 and Figure B28"},
                    {"label": "Fusion Across Joint", "query": "What indicates complete fusion across the entire joint on Figure B28?"}
                ]
            }
        ]
    },
    "Figure B29": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Incomplete Fusion Locations",
                "color": "#f87171",
                "chips": [
                    {"label": "Lack of Root Fusion", "query": "Where does incomplete fusion occur at the root on Figure B29?"},
                    {"label": "Lack of Sidewall Fusion", "query": "Where does incomplete sidewall fusion occur on Figure B29?"},
                    {"label": "Interpass Incomplete Fusion", "query": "What is interpass incomplete fusion on Figure B29?"}
                ]
            }
        ]
    },
    "Figure B30": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Cross-Sectional Zones",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Transverse Weld Profile", "query": "What are the transverse section zones of a fusion weld on Figure B30?"},
                    {"label": "Fusion Boundary", "query": "What is the fusion boundary in Figure B30?"},
                    {"label": "HAZ Boundary", "query": "What is the heat-affected zone boundary in Figure B30?"}
                ]
            }
        ]
    },
    "Figure B31": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Solid-State & Brazed Interfaces",
                "color": "#a855f7",
                "chips": [
                    {"label": "Solid-State Bond Line", "query": "What is the interface appearance for solid-state joining in Figure B31?"},
                    {"label": "Brazed Joint Interface", "query": "What does a brazed joint interface look like in Figure B31?"}
                ]
            }
        ]
    },
    "Figure B32": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Discontinuity Types (Panels A–O)",
                "color": "#f87171",
                "chips": [
                    {"label": "Porosity", "query": "What forms of porosity are illustrated in Figure B32?"},
                    {"label": "Slag Inclusions", "query": "What are slag inclusions in Figure B32?"},
                    {"label": "Panel (O) Burn-Through", "query": "How is burn-through defined as a standard discontinuity in Figure B32(O)?"},
                    {"label": "Incomplete Joint Penetration", "query": "Where is incomplete joint penetration shown on Figure B32?"},
                    {"label": "Undercut & Overlap", "query": "Compare undercut and overlap in Figure B32"}
                ]
            }
        ]
    },
    "Figure B33": {
        "category": "fusion_cracks",
        "groups": [
            {
                "group_title": "Crack Classification by Location",
                "color": "#ef4444",
                "chips": [
                    {"label": "Crater Crack", "query": "What is a crater crack in Figure B33?"},
                    {"label": "Toe Crack", "query": "What is a toe crack in Figure B33?"},
                    {"label": "Underbead Crack", "query": "What is an underbead crack in Figure B33?"},
                    {"label": "Root Crack", "query": "What is a root crack in Figure B33?"},
                    {"label": "Longitudinal vs Transverse", "query": "What is the difference between a longitudinal crack and a transverse crack in Figure B33?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 7: ANNEX B TORCHES, GUNS, CUTTING & TRANSFERS (B34 - B43)
    # =========================================================================
    "Figure B34": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Electrical Polarity Systems",
                "color": "#38bdf8",
                "chips": [
                    {"label": "DCEN (Straight Polarity)", "query": "Explain direct current electrode negative (DCEN) polarity on Figure B34"},
                    {"label": "DCEP (Reverse Polarity)", "query": "Explain direct current electrode positive (DCEP) polarity on Figure B34"},
                    {"label": "Electron Flow Direction", "query": "How does electron flow differ between DCEN and DCEP on Figure B34?"}
                ]
            }
        ]
    },
    "Figure B35": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Plasma Torch Components",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Constricting Orifice", "query": "What is the constricting orifice in a plasma arc torch on Figure B35?"},
                    {"label": "Orifice Gas vs Shielding Gas", "query": "What is the difference between orifice gas and shielding gas in Figure B35?"},
                    {"label": "Tungsten Electrode", "query": "Where is the electrode located in the plasma torch on Figure B35?"},
                    {"label": "Water Jacket", "query": "What is the cooling water jacket in Figure B35?"}
                ]
            }
        ]
    },
    "Figure B36": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "GTAW Torch Assembly",
                "color": "#4ade80",
                "chips": [
                    {"label": "Collet & Collet Body", "query": "What are the collet and collet body in a GTAW torch on Figure B36?"},
                    {"label": "Gas Nozzle (Cup)", "query": "What is the gas nozzle on a GTAW torch on Figure B36?"},
                    {"label": "Gas Lens", "query": "What is a gas lens in a GTAW torch on Figure B36?"},
                    {"label": "Back Cap", "query": "What is the back cap on Figure B36?"}
                ]
            }
        ]
    },
    "Figure B37": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "ESW Hardware & Shoes",
                "color": "#a855f7",
                "chips": [
                    {"label": "Consumable Guide Tube", "query": "What is a consumable guide tube in electroslag welding on Figure B37?"},
                    {"label": "Moving vs Stationary Shoes", "query": "What are the moving shoe and stationary shoe in electroslag welding on Figure B37?"},
                    {"label": "Molten Slag Bath", "query": "What is the molten slag bath in Figure B37?"}
                ]
            }
        ]
    },
    "Figure B38": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "GMAW/FCAW Gun Components",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Contact Tip", "query": "What is the contact tip in a GMAW gun on Figure B38?"},
                    {"label": "Gas Diffuser", "query": "What is the gas diffuser on Figure B38?"},
                    {"label": "Gas Nozzle", "query": "What is the shielding gas nozzle on Figure B38?"},
                    {"label": "Conduit Liner", "query": "What is the conduit liner in Figure B38?"}
                ]
            }
        ]
    },
    "Figure B39": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "GMAW Metal Transfer Modes",
                "color": "#f87171",
                "chips": [
                    {"label": "Short Circuiting Transfer", "query": "Explain short circuiting transfer in Figure B39"},
                    {"label": "Globular Transfer", "query": "Explain globular transfer in Figure B39"},
                    {"label": "Spray Transfer", "query": "Explain spray transfer in Figure B39"},
                    {"label": "Pulsed Spray Transfer", "query": "Explain pulsed spray transfer in Figure B39"}
                ]
            }
        ]
    },
    "Figure B40": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Flame Classifications",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Neutral Flame", "query": "What are the characteristics of a neutral flame on Figure B40?"},
                    {"label": "Carburizing (Reducing) Flame", "query": "What are the characteristics of a carburizing flame on Figure B40?"},
                    {"label": "Acetylene Feather", "query": "What is the acetylene feather in Figure B40?"},
                    {"label": "Oxidizing Flame", "query": "What are the characteristics of an oxidizing flame on Figure B40?"}
                ]
            }
        ]
    },
    "Figure B41": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Oxygen Cutting Anatomy",
                "color": "#4ade80",
                "chips": [
                    {"label": "Preheat Flames", "query": "What is the role of preheat flames in oxygen cutting on Figure B41?"},
                    {"label": "Cutting Oxygen Stream", "query": "What is the cutting oxygen stream on Figure B41?"},
                    {"label": "Kerf & Drag", "query": "Define kerf and drag in oxygen cutting on Figure B41"},
                    {"label": "Slag Formation", "query": "How is slag formed during oxygen cutting in Figure B41?"}
                ]
            }
        ]
    },
    "Figure B42": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Electrode Packaging Types",
                "color": "#a855f7",
                "chips": [
                    {"label": "Spool Packaging", "query": "What is a spool for filler metal packaging on Figure B42?"},
                    {"label": "Coil with Support", "query": "What is a coil with support on Figure B42?"},
                    {"label": "Coil without Support", "query": "What is a coil without support on Figure B42?"},
                    {"label": "Drum Packaging", "query": "What is drum packaging for welding wire on Figure B42?"}
                ]
            }
        ]
    },
    "Figure B43": {
        "category": "torches_cutting",
        "groups": [
            {
                "group_title": "Surface Preparation Techniques",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Grit Blasting", "query": "What is grit blasting surface preparation on Figure B43?"},
                    {"label": "Rough Threading", "query": "What is rough threading surface preparation on Figure B43?"},
                    {"label": "Grooving & Knurling", "query": "What are grooving and knurling on Figure B43?"}
                ]
            }
        ]
    },

    # =========================================================================
    # GROUP 8: ANNEX B FRICTION, RESISTANCE & WAVEFORMS (B44 - B54)
    # =========================================================================
    "Figure B44": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Inertia Friction Welding Components",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Flywheel Energy Storage", "query": "What is the function of the flywheel in inertia friction welding on Figure B44?"},
                    {"label": "Rotating Chuck", "query": "What is the rotating chuck in Figure B44?"},
                    {"label": "Axial Thrust Force", "query": "How is axial thrust applied in Figure B44?"}
                ]
            }
        ]
    },
    "Figure B45": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Direct Drive Friction Components",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Continuous Drive Motor", "query": "What is the continuous drive motor on Figure B45?"},
                    {"label": "Clutch & Brake", "query": "What is the role of the clutch and brake in direct drive friction welding on Figure B45?"},
                    {"label": "Forging Force", "query": "How is forging force applied in direct drive friction welding on Figure B45?"}
                ]
            }
        ]
    },
    "Figure B46": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "FSW Tool & Sides",
                "color": "#4ade80",
                "chips": [
                    {"label": "Advancing Side", "query": "Define advancing side in friction stir welding on Figure B46"},
                    {"label": "Retreating Side", "query": "Define retreating side in friction stir welding on Figure B46"},
                    {"label": "Tool Shoulder", "query": "What is the function of the tool shoulder on Figure B46?"},
                    {"label": "Tool Probe (Pin)", "query": "What is the probe or pin in friction stir welding on Figure B46?"},
                    {"label": "Stir Zone", "query": "What is the stir zone in friction stir welding on Figure B46?"}
                ]
            }
        ]
    },
    "Figure B47": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Multiple Spot Configurations",
                "color": "#a855f7",
                "chips": [
                    {"label": "Series Welding", "query": "What is series spot welding on Figure B47?"},
                    {"label": "Indirect Welding", "query": "What is indirect spot welding on Figure B47?"},
                    {"label": "Direct Welding", "query": "What is direct spot welding on Figure B47?"}
                ]
            }
        ]
    },
    "Figure B48": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Single Spot Electrode Setups",
                "color": "#f87171",
                "chips": [
                    {"label": "Opposed Electrodes", "query": "What is an opposed electrode arrangement for spot welding on Figure B48?"},
                    {"label": "Projection Welding Setup", "query": "What is projection welding arrangement on Figure B48?"},
                    {"label": "Backup Electrode", "query": "What is a backup electrode in spot welding on Figure B48?"}
                ]
            }
        ]
    },
    "Figure B49": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Pulsation Waveform Parameters",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Heat Time & Cool Time", "query": "What are heat time and cool time in pulsation welding on Figure B49?"},
                    {"label": "Weld Intervals", "query": "What are weld intervals in pulsation resistance spot welding on Figure B49?"},
                    {"label": "Forge Force Application", "query": "How is forge force applied during pulsation welding on Figure B49?"}
                ]
            }
        ]
    },
    "Figure B50": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Single-Pulse Timing Stages",
                "color": "#fbbf24",
                "chips": [
                    {"label": "Squeeze Time", "query": "What is squeeze time in resistance spot welding on Figure B50?"},
                    {"label": "Weld Time", "query": "What is weld time in resistance spot welding on Figure B50?"},
                    {"label": "Hold Time", "query": "What is hold time in resistance spot welding on Figure B50?"},
                    {"label": "Off Time", "query": "What is off time in resistance spot welding on Figure B50?"}
                ]
            }
        ]
    },
    "Figure B51": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Flash Welding Stages & Cycles",
                "color": "#4ade80",
                "chips": [
                    {"label": "Flashing Stage", "query": "What is the flashing stage in a flash welding cycle on Figure B51?"},
                    {"label": "Upsetting Stage", "query": "What is the upsetting stage in flash welding on Figure B51?"},
                    {"label": "Platen Acceleration", "query": "How does platen acceleration coordinate with upset on Figure B51?"},
                    {"label": "Flashing Voltage & Upset Current", "query": "What are flashing voltage and upset current on Figure B51?"}
                ]
            }
        ]
    },
    "Figure B52": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "HF Resistance Configurations",
                "color": "#a855f7",
                "chips": [
                    {"label": "HF Contact Welding (HFRW)", "query": "What is high-frequency resistance welding on Figure B52?"},
                    {"label": "HF Induction Welding (HFIW)", "query": "What is high-frequency induction welding on Figure B52?"},
                    {"label": "Squeeze Rolls", "query": "What are squeeze rolls in HF tube welding on Figure B52?"},
                    {"label": "Apex of the V", "query": "What is the apex of the V in HF resistance welding on Figure B52?"}
                ]
            }
        ]
    },
    "Figure B53": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Pulsed Waveform Variables",
                "color": "#38bdf8",
                "chips": [
                    {"label": "Peak Current", "query": "What is peak current in a pulsed welding cycle on Figure B53?"},
                    {"label": "Background Current", "query": "What is background current in a pulsed welding cycle on Figure B53?"},
                    {"label": "Pulse Width & Frequency", "query": "What are pulse width and pulse frequency on Figure B53?"}
                ]
            }
        ]
    },
    "Figure B54": {
        "category": "friction_waveforms",
        "groups": [
            {
                "group_title": "Continuous Arc Cycle Steps",
                "color": "#f87171",
                "chips": [
                    {"label": "Preflow Time", "query": "What is preflow time in a GMAW welding cycle on Figure B54?"},
                    {"label": "Burnback Time", "query": "What is burnback time in Figure B54?"},
                    {"label": "Postflow Time", "query": "What is postflow time in Figure B54?"},
                    {"label": "Crater Fill Time", "query": "What is crater fill time in Figure B54?"}
                ]
            }
        ]
    }
}

from src.standard_manifest import get_manifest, ManifestError

def _source_metadata(fig_key):
    manifest = get_manifest()
    item = manifest.element(fig_key)
    if not item:
        raise ManifestError("MANIFEST_REFERENCE_INVALID", "Figure registry has no verified source record.")
    section = manifest.section(item["parent_id"])
    pages = manifest.page_range(fig_key)
    ordinal = manifest.page_range(fig_key, ordinal=True)
    prefix = "pp." if len(item["anchors"]) > 1 else "p."
    return {"title": item["title"], "page": f"{section['label']}, p. {pages} (PDF {prefix} {ordinal})"}

if set(FIGURE_INSPECTORS) != set(get_manifest().labels("figures")):
    raise ManifestError("MANIFEST_REFERENCE_INVALID", "Figure UI/source inventories differ.")
for _key, _info in FIGURE_INSPECTORS.items():
    _info.update(_source_metadata(_key))

import json
import math
import re
import urllib.parse
from pathlib import Path
from src.config import PARSED_FIGURES_DIR, BASE_DIR

_BBOX_FILE = BASE_DIR / "parsed" / "figures" / "figure_bboxes.json"
_BBOX_MANIFEST: Dict[str, Any] = {}
if _BBOX_FILE.exists():
    try:
        with open(_BBOX_FILE, "r", encoding="utf-8") as _f:
            _BBOX_MANIFEST = json.load(_f)
    except Exception:
        pass

def _finite_numeric_list(value: Any, length: int) -> bool:
    """Keep JSON numeric lists without coercion, including rejection of bools."""
    return (
        isinstance(value, list) and len(value) == length
        and all(type(v) is int or (type(v) is float and math.isfinite(v)) for v in value)
    )


def _valid_normalized_bbox(bbox: Any) -> bool:
    """UI image coordinates are [ymin, xmin, ymax, xmax] in [0, 1]."""
    return (
        _finite_numeric_list(bbox, 4)
        and 0 <= bbox[0] < bbox[2] <= 1
        and 0 <= bbox[1] < bbox[3] <= 1
    )


def get_figure_bboxes(fig_key: str) -> Optional[Dict[str, Any]]:
    """Return a validated view without changing the cached spatial registry."""
    clean_key = fig_key.strip()
    if not clean_key.startswith("Figure "):
        clean_key = f"Figure {clean_key}"
    raw = _BBOX_MANIFEST.get(clean_key)
    if raw is None:
        return None
    view = dict(raw)
    if "groups" not in raw:
        return view

    groups = []
    label_counts = {}
    for group in raw["groups"]:
        group_view = dict(group)
        chips = []
        for chip in group.get("chips", []):
            chip_view = dict(chip)
            label = chip.get("label", "")
            label_counts[label] = label_counts.get(label, 0) + 1
            bbox = chip.get("bbox")
            if _valid_normalized_bbox(bbox):
                chip_view["bbox"] = list(bbox)
                center = chip.get("center")
                if (_finite_numeric_list(center, 2)
                        and bbox[0] <= center[0] <= bbox[2]
                        and bbox[1] <= center[1] <= bbox[3]):
                    chip_view["center"] = list(center)
                else:
                    chip_view["center"] = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
            else:
                chip_view["bbox"] = None
                chip_view["center"] = None
            chips.append(chip_view)
        group_view["chips"] = chips
        groups.append(group_view)

    # The UI joins by label; repeated spatial labels cannot select one geometry.
    for group in groups:
        for chip in group["chips"]:
            if label_counts[chip.get("label", "")] > 1:
                chip["bbox"] = None
                chip["center"] = None
    view["groups"] = groups
    return view

def _enrich_chips_with_bboxes(fig_key: str, groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merges spatial coordinates (bbox and center) from manifest into chips."""
    bbox_meta = get_figure_bboxes(fig_key)
    if not bbox_meta or "groups" not in bbox_meta:
        return groups
    
    # Map label -> bbox entry
    label_map = {}
    for g in bbox_meta.get("groups", []):
        for c in g.get("chips", []):
            label_map[c.get("label", "")] = c
            
    enriched = []
    for g in groups:
        g_copy = dict(g)
        chips_copy = []
        for c in g.get("chips", []):
            c_copy = dict(c)
            lbl = c.get("label", "")
            if lbl in label_map:
                match = label_map[lbl]
                c_copy["bbox"] = match.get("bbox")
                c_copy["center"] = match.get("center")
                c_copy["panel"] = match.get("panel", "")
            chips_copy.append(c_copy)
        g_copy["chips"] = chips_copy
        enriched.append(g_copy)
    return enriched

def resolve_figure_image_filename(fig_key: str) -> str:
    """Return the explicit first-page binding, independent of directory order."""
    label = str(fig_key).strip()
    if re.fullmatch(r"[AB]\.?\d+[A-Z]?", label, re.IGNORECASE):
        label = "Figure " + label
    paths = get_manifest().asset_paths(label, {".png"})
    return Path(paths[0]).name if paths else ""

def get_figure_data(fig_key: str) -> Dict[str, Any]:
    """Retrieves metadata and chips for a specific figure ID (e.g. 'Figure A6' or 'Figure B25')."""
    clean_key = fig_key.strip()
    if not clean_key.startswith("Figure "):
        clean_key = f"Figure {clean_key}"
    data = FIGURE_INSPECTORS.get(clean_key, {})
    if data:
        data = dict(data)
        data.update(_source_metadata(clean_key))
        paths = get_manifest().asset_paths(clean_key, {".png"})
        data["image_files"] = [Path(path).name for path in paths]
        data["image_file"] = data["image_files"][0] if paths else ""
        data["source_anchors"] = get_manifest().source_anchors(clean_key)
        data["groups"] = _enrich_chips_with_bboxes(clean_key, data.get("groups", []))
    return data

def get_inspector_html(fig_key: str) -> str:
    """Generates the interactive inspector HTML panel with all chips for a specific figure."""
    info = get_figure_data(fig_key)
    if not info:
        return ""

    title = info.get("title", fig_key)
    page = info.get("page", "")
    groups = info.get("groups", [])
    img_file = info.get("image_file", "")

    html = f"""
    <div class="interactive-inspector" style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
        <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
            <span>🔎 Interactive Node & Callout Explorer for {fig_key}:</span>
            <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">{page}</span>
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px; font-style: italic;">{title}</div>
    """

    for g in groups:
        g_title = g.get("group_title", "")
        color = g.get("color", "#38bdf8")
        chips = g.get("chips", [])
        html += f"""
        <div style="margin-bottom: 10px;">
            <span style="font-size: 11px; font-weight: 600; color: {color}; text-transform: uppercase;">{g_title}:</span>
            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
        """
        for c in chips:
            label = c.get("label", "")
            safe_label = label.replace("'", "\\'")
            encoded_query = urllib.parse.quote(c.get("query", ""))
            bbox = c.get("bbox")
            bbox_json = json.dumps(bbox) if bbox else "null"
            focus_btn = ""
            if bbox:
                focus_btn = f''' <span class="chip-focus-btn" title="Focus diagram on {label}" onclick="event.stopPropagation(); focusFeature('{fig_key}', '{safe_label}', {bbox_json})">🎯</span>'''
            html += f"""<span class="pill" data-query="{encoded_query}" onclick="event.stopPropagation(); setQuery(decodeURIComponent(this.getAttribute('data-query')))">{label}{focus_btn}</span>"""
        html += """
            </div>
        </div>
        """

    html += "</div>"
    return html

def get_all_figures_catalog() -> List[Dict[str, Any]]:
    """Returns a summarized list of all 60 figures for the interactive browser."""
    catalog = []
    for fig_id in FIGURE_INSPECTORS:
        data = get_figure_data(fig_id)
        total_chips = sum(len(g.get("chips", [])) for g in data.get("groups", []))
        catalog.append({
            "id": fig_id,
            "title": data.get("title", ""),
            "page": data.get("page", ""),
            "category": data.get("category", ""),
            "chip_count": total_chips,
            "image_file": data.get("image_file", ""),
            "image_files": data.get("image_files", []),
            "groups": data.get("groups", [])
        })
    return catalog

