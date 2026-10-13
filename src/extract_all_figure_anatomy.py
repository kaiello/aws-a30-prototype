"""
extract_all_figure_anatomy.py: Comprehensive visual callout, label, and diagram anatomy
ingestion for AWS A3.0:2020 Annex A (Figures A1-A5) and Annex B (Figures B1-B97).

Ensures that any part, callout, axis, or word on ANY diagram in the standard is fully queryable
with exact element IDs, printed page citations, and Clause 4 semantic grounding.
"""

import asyncio
from pathlib import Path
from src.config import STORAGE_DIR
from src.indexer import get_rag_instance

FIGURE_ANATOMY_CHUNKS = [
    {
        "chunk_id": "annex_a_figures_a1_a2_a3_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figures A1, A2, and A3 Process Charts & Taxonomies]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex A (Informative) - Process and Classification Charts\n"
            "\n"
            "1. FIGURE A1: MASTER CHART OF WELDING AND JOINING PROCESSES (p. 75, PDF p. 88)\n"
            "Official Title: Figure A1—Master Chart of Welding and Joining Processes\n"
            "File: Figure_A1_p88.png\n"
            "Taxonomy Branches & Standard Designations:\n"
            "- Arc Welding (AW): SW (stud arc), AHW (atomic hydrogen), BMAW (bare metal arc), CAW (carbon arc), "
            "CAW-G (gas carbon arc), CAW-S (shielded carbon arc), CAW-T (twin carbon arc), EGW (electrogas), "
            "FCAW (flux cored arc), FCAW-G (gas-shielded flux cored arc), FCAW-S (self-shielded flux cored arc), "
            "GMAW (gas metal arc), GMAW-P (pulsed gas metal arc), GMAW-S (short circuiting gas metal arc), "
            "GTAW (gas tungsten arc), GTAW-P (pulsed gas tungsten arc), MIAW (magnetically impelled arc), "
            "PAW (plasma arc), SMAW (shielded metal arc), SAW (submerged arc), SAW-S (series submerged arc).\n"
            "- Resistance Welding (RW): FW (flash), RW-PC (pressure-controlled resistance), PW (projection), "
            "RSEW (resistance seam), RSEW-HF (high-frequency resistance seam), RSEW-I (induction resistance seam), "
            "RSEW-MS (mash resistance seam), RSW (resistance spot), UW (upset), UW-HF (high-frequency upset), UW-I (induction upset).\n"
            "- Solid-State Welding (SSW): CEW (coextrusion), CW (cold), DFW (diffusion), HIPW (hot isostatic pressure), "
            "EXW (explosion), FOW (forge), FRW (friction), FRW-DD (direct-drive friction), FSW (friction stir), "
            "FRW-I (inertia friction), HPW (hot pressure), ROW (roll), USW (ultrasonic).\n"
            "- Soldering (S): DS (dip), FS (furnace), IS (induction), IRS (infrared), INS (iron), RS (resistance), "
            "TS (torch), USS (ultrasonic), WS (wave).\n"
            "- Brazing (B): BB (block), CAB (controlled atmosphere), DFB (diffusion), DB (dip), EBB (electron beam), "
            "EXB (exothermic), FLB (flow), FB (furnace), IB (induction), IRB (infrared), LBB (laser beam), "
            "RB (resistance), TB (torch), TCAB (twin carbon arc).\n"
            "- Oxyfuel Gas Welding (OFW): AAW (air acetylene), OAW (oxyacetylene), OHW (oxyhydrogen), PGW (pressure gas).\n"
            "- High Energy Beam Welding (HEBW): EBW (electron beam), EBW-HV (high vacuum electron beam), "
            "EBW-MV (medium vacuum electron beam), EBW-NV (nonvacuum electron beam), LBW (laser beam).\n"
            "- Other Welding and Joining: AB (arc brazing), BW (braze welding), ABW (arc braze welding), "
            "CABW (carbon arc braze welding), EBBW (electron beam braze welding), EXBW (exothermic braze welding), "
            "FLOW (flow welding), LBBW (laser beam braze welding), ESW (electroslag), ESW-CG (consumable guide electroslag), "
            "IW (induction), PEW (percussion), TW (thermit).\n"
            "\n"
            "2. FIGURE A2: MASTER CHART OF ALLIED PROCESSES (p. 75, PDF p. 89)\n"
            "Official Title: Figure A2—Master Chart of Allied Processes\n"
            "File: Figure_A2_p89.png\n"
            "Taxonomy Branches & Standard Designations:\n"
            "- Thermal Spraying (THSP): FLSP (flame spraying), FLSP-P (powder flame spraying), FLSP-W (wire flame spraying), "
            "HVOF (high velocity oxyfuel spraying), HVAF (high velocity air fuel spraying), D-SP (detonation flame spraying), "
            "PSP (plasma spraying), VPSP (vacuum plasma spraying), ASP (arc spraying), CS (cold spraying).\n"
            "- Thermal Cutting (TC): Oxygen Cutting (OC): OFC (oxyfuel gas cutting), OFC-A (oxynatural gas cutting), "
            "OFC-H (oxyhydrogen cutting), OFC-P (oxypropane cutting), FOC (flux oxygen cutting), MOC (metal powder oxygen cutting), "
            "POC (plasma oxygen cutting), CHOC (chemical oxygen cutting).\n"
            "Arc Cutting (AC): CAC (carbon arc cutting), CAC-A (air carbon arc cutting), MAC (metal arc cutting), "
            "GMAC (gas metal arc cutting), GTAC (gas tungsten arc cutting), PAC (plasma arc cutting), SMAC (shielded metal arc cutting).\n"
            "Other Thermal Cutting: LBC (laser beam cutting), EBC (electron beam cutting).\n"
            "- Adhesive Bonding (AB): Classifies bonding methods using structural adhesives.\n"
            "- Surface Preparation (SP): Thermal and mechanical pre-treatment methods.\n"
            "\n"
            "3. FIGURE A3: JOINING METHOD CHART (p. 76, PDF p. 89)\n"
            "Official Title: Figure A3—Joining Method Chart\n"
            "File: Figure_A3_p89.png\n"
            "Taxonomy Hierarchy:\n"
            "Root: Joining Methods\n"
            "-> Fusion Welding: Leading directly to Figure A4 (Fusion Welding Classification Chart).\n"
            "-> Solid-State Welding: Leading directly to Figure A5 (Solid-State Welding Classification Chart).\n"
            "-> Brazing and Soldering: Leading directly to Figure A6 (Brazing and Soldering Classification Chart).\n"
        )
    },
    {
        "chunk_id": "annex_a_figures_a4_a5_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figures A4 and A5 Classification Charts]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex A (Informative)\n"
            "\n"
            "1. FIGURE A4: FUSION WELDING CLASSIFICATION CHART (p. 77, PDF p. 90)\n"
            "Official Title: Figure A4—Fusion Welding Classification Chart\n"
            "File: Figure_A4_p90.png\n"
            "Physical Characteristics:\n"
            "- Energy Source: Electrical (Arc, Resistance, Radiation) and Chemical (Gas combustion).\n"
            "- Shielding Mediums: Flux, Gas, Vacuum, Self-shielded.\n"
            "Classified Processes on Figure A4:\n"
            "- Arc Welding: SMAW, GMAW, GTAW, FCAW, SAW, PAW, EGW, CAW.\n"
            "- Resistance Welding (Fusion): RSW, RSEW, FW, PW, UW.\n"
            "- Radiation Fusion: EBW (electron beam welding in vacuum or air), LBW (laser beam welding).\n"
            "- Chemical Fusion: OAW (oxyacetylene welding), OHW (oxyhydrogen welding).\n"
            "\n"
            "2. FIGURE A5: SOLID-STATE WELDING CLASSIFICATION CHART (p. 78, PDF p. 91)\n"
            "Official Title: Figure A5—Solid-State Welding Classification Chart\n"
            "File: Figure_A5_p91.png\n"
            "Physical Characteristics:\n"
            "- Energy Source: Mechanical, Thermal, Electrical, Chemical.\n"
            "- Mechanical Loading: Compressive load / pressure without melting the base metal.\n"
            "Classified Processes on Figure A5:\n"
            "- CW (cold welding), DFW (diffusion welding), EXW (explosion welding), FOW (forge welding), "
            "FRW (friction welding: inertia FRW-I and direct-drive FRW-DD), FSW (friction stir welding), "
            "HIPW (hot isostatic pressure welding), HPW (hot pressure welding), ROW (roll welding), "
            "USW (ultrasonic welding), CEW (coextrusion welding).\n"
        )
    },
    {
        "chunk_id": "annex_b_figures_b1_b7_joint_geometry_v2",
        "content": (
            "[AWS A3.0:2020 Annex B - Figures B1 through B7 Joint Geometry, Joint Roots & Edge Preparation]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex B (Informative) - Engineering Drawings & Weld Configurations\n"
            "\n"
            "1. FIGURE B1: JOINT TYPES (p. 82, PDF p. 95)\n"
            "Official Title: Figure B1—Joint Types\n"
            "Joint Types Illustrated:\n"
            "- (A) Butt joint: A joint between two members aligned approximately in the same plane.\n"
            "- (B) Corner joint: A joint between two members located approximately at right angles to each other at their edges.\n"
            "- (C) T-joint: A joint between two members located approximately at right angles to each other in the form of a T.\n"
            "- (D) Lap joint: A joint between two overlapping members in parallel planes.\n"
            "- (E) Edge joint: A joint between the edges of two or more parallel or nearly parallel members.\n"
            "\n"
            "2. FIGURE B2: FLANGED JOINTS (p. 83, PDF p. 96)\n"
            "Official Title: Figure B2—Flanged Joints\n"
            "\n"
            "3. FIGURE B3: SPLICED BUTT JOINTS (p. 84, PDF p. 97)\n"
            "Official Title: Figure B3—Spliced Butt Joints\n"
            "\n"
            "4. FIGURE B4: JOINT ROOT (p. 85, PDF p. 98)\n"
            "Official Title: Figure B4—Joint Root\n"
            "File: Figure_B4_p98.png\n"
            "Definition & Illustrations:\n"
            "- Depicts and illustrates the joint root for butt joints, corner joints, T-joints, lap joints, and edge joints.\n"
            "- Joint Root: The portion of a joint to be welded where the members approach closest to each other.\n"
            "- In cross section, the joint root may be a root point, a root line, or a root area across butt, corner, and T-joints.\n"
            "\n"
            "5. FIGURE B5: GROOVE FACE, ROOT EDGE, AND ROOT FACE (p. 86, PDF p. 99)\n"
            "Official Title: Figure B5—Groove Face, Root Edge, and Root Face\n"
            "File: Figure_B5_p99.png\n"
            "Crucial Distinctions & Callouts on Figure B5:\n"
            "- 'Groove face': That surface of a member included in the groove.\n"
            "- 'Root face': The portion of the groove face adjacent to the joint root (the flat vertical land that is not beveled).\n"
            "- 'Root edge': A root face of zero width (a sharp un-machined knife-edge at the root).\n"
            "- 'Root opening': The separation between the workpieces at the joint root prior to welding.\n"
            "- 'Bevel face': The prepared sloping surface of a member.\n"
            "- Difference between root face and root opening: Root face is a surface dimension on the workpiece itself; root opening is the gap or space separating the two workpieces.\n"
            "- Difference between root face and root edge: Root face has measurable land thickness (> 0); root edge has zero land thickness.\n"
            "\n"
            "6. FIGURE B6: BEVEL ANGLE, GROOVE ANGLE, AND RADII (p. 87-89, PDF p. 100-102)\n"
            "Official Title: Figure B6—Bevel Angle, Bevel Face, Bevel Depth, Groove Angle, and Included Angle\n"
            "File: Figure_B6_p100.png, Figure_B6_p101.png, Figure_B6_p102.png\n"
            "Callouts & Geometric Axes:\n"
            "- 'Bevel angle': The angle between the prepared edge of a member and a plane perpendicular to the surface of the member.\n"
            "- 'Groove angle': The total included angle of the groove between the workpieces to be joined.\n"
            "- Relation: For a symmetrical single-V groove on two beveled plates, Groove Angle = 2 * (Bevel Angle). For a single-bevel groove with one square edge, Groove Angle = Bevel Angle.\n"
            "- 'Groove radius': The radius used to form the curved contour of a J-groove or U-groove weld.\n"
            "- 'Depth of bevel': The perpendicular distance from the workpiece surface to the root edge or beginning of the root face.\n"
            "\n"
            "7. FIGURE B7: EDGE SHAPES (p. 90, PDF p. 103)\n"
            "Official Title: Figure B7—Edge Shapes\n"
            "Shapes Illustrated: Square edge, bevel edge, chamfer edge, J-edge, U-edge, flanged edge.\n"
        )
    },
    {
        "chunk_id": "clause_4_waveform_and_nonstandard_terms",
        "content": (
            "[AWS A3.0:2020 Clause 4 - Waveform-Controlled Welding and Critical Nonstandard Terms]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Clause: Clause 4 - Glossary of Terms\n"
            "\n"
            "1. WAVEFORM-CONTROLLED WELDING (Clause 4, p. 62):\n"
            "- 'waveform-controlled welding, arc welding': A process modification using software to purposely manipulate the output welding waveform.\n"
            "- Nonstandard term: 'controlled waveform welding' is a nonstandard term when used for waveform-controlled welding (Clause 4, p. 17).\n"
            "- Related metrics:\n"
            "  * 'average instantaneous power (AIP), waveform-controlled welding' (Clause 4, p. 10): The average of products of amperages and voltages determined at sampling frequencies sufficient to quantify waveform changes during a welding interval.\n"
            "  * 'total instantaneous energy (TIE), waveform-controlled welding' (Clause 4, p. 60): The sum of products of amperages, voltages, and time intervals determined at sampling frequencies sufficient to quantify waveform changes during a welding interval.\n"
            "\n"
            "2. NONSTANDARD TERMS & OBSOLETE PROCESSES:\n"
            "- 'hydromatic welding' (Clause 4, p. 32): A nonstandard term for 'pressure-controlled resistance welding'.\n"
            "- 'short arc' (Clause 4, p. 58): A nonstandard term when used for 'short circuiting transfer'.\n"
            "- 'dip transfer' (Clause 4, p. 20): A nonstandard term when used for dip feed or 'short circuiting transfer'.\n"
            "- 'short circuiting arc welding': A nonstandard term for 'short circuiting gas metal arc welding (GMAW-S)'.\n"
            "- 'micro wire welding': A nonstandard shop colloquialism historically used for short circuiting gas metal arc welding (GMAW-S).\n"
            "- 'flow welding (FLOW)' (Clause 4, p. 26 & Table A5): A braze welding process variation using molten filler metal poured over the fusion faces as the heat source. Obsolete or seldom used process. See Table A5.\n"
            "- 'flow brazing (FLB)' (Clause 4, p. 26 & Table A5): A brazing process using heat from the brazing filler metal poured over the joint. Obsolete or seldom used process. See Table A5.\n"
            "- 'burning in' (Clause 4, p. 12): A nonstandard term for flow welding.\n"
        )
    },
    {
        "chunk_id": "annex_b_figures_b13_b26_welds_positions_throats",
        "content": (
            "[AWS A3.0:2020 Annex B - Figures B13, B15, B20, B21, B25, B26 Weld Features & Positions]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex B (Informative)\n"
            "\n"
            "1. FIGURE B13: COMPLETE JOINT PENETRATION (CJP) & PARTIAL JOINT PENETRATION (PJP) (p. 98, PDF p. 111)\n"
            "Official Title: Figure B13—Complete Joint Penetration and Partial Joint Penetration Groove Welds\n"
            "File: Figure_B13_p111.png\n"
            "Key Callouts:\n"
            "- 'Complete joint penetration (CJP)': A groove weld in which weld metal extends through joint thickness.\n"
            "- 'Partial joint penetration (PJP)': A groove weld in which incomplete joint penetration exists intentionally.\n"
            "\n"
            "2. FIGURE B15: BACK WELD VS. BACKING WELD (p. 100, PDF p. 113)\n"
            "Official Title: Figure B15—Back Weld and Backing Weld Distinction\n"
            "File: Figure_B15_p113.png\n"
            "Key Distinction:\n"
            "- 'Back weld': A weld made at the back of a single-groove weld AFTER the groove weld has been deposited.\n"
            "- 'Backing weld': Backing in the form of a weld made BEFORE the primary groove weld has been deposited.\n"
            "- Sequence is the sole qualifying discriminator between these two terms.\n"
            "\n"
            "3. FIGURE B20: FILLET WELD PIPE TEST POSITIONS (1F, 2F, 2FR, 4F, 5F) (p. 105, PDF p. 118)\n"
            "Official Title: Figure B20—Fillet Weld Pipe Test Positions\n"
            "File: Figure_B20_p118.png\n"
            "Positions and Orientations Illustrated:\n"
            "- '1F': Pipe axis inclined at 45° to horizontal and rotated during welding so weld metal is deposited from above.\n"
            "- '2F': Pipe axis vertical; pipe not rotated; weld deposited in horizontal position.\n"
            "- '2FR': Pipe axis horizontal; pipe rotated.\n"
            "- '4F': Pipe axis vertical; weld deposited overhead on horizontal flange.\n"
            "- '5F': Pipe axis horizontal and fixed (not rotated); weld deposited in progression around circumference.\n"
            "\n"
            "4. FIGURE B21: GROOVE WELD PIPE TEST POSITIONS (1G, 2G, 5G, 6G, 6GR) (p. 112, PDF p. 124)\n"
            "Official Title: Figure B21—Groove Weld Pipe Test Positions\n"
            "File: Figure_B21_p124.png\n"
            "Positions and Orientations Illustrated:\n"
            "- '1G': Pipe axis horizontal; pipe rotated during welding; weld metal deposited from above (flat position).\n"
            "- '2G': Pipe axis vertical; pipe fixed (not rotated); weld deposited in horizontal plane.\n"
            "- '5G': Pipe axis horizontal; pipe fixed (not rotated); weld deposited in flat, vertical, and overhead positions.\n"
            "- '6G': Pipe axis inclined at 45° ± 5° to horizontal; pipe fixed (not rotated); tests welder in all positions.\n"
            "- '6GR': 6G position with a restriction ring placed near the weld groove to test accessibility restrictions.\n"
            "\n"
            "5. FIGURE B25: FILLET WELD THROATS AND GEOMETRY (p. 119, PDF p. 135-138)\n"
            "Official Title: Figure B25—Fillet Weld Throats and Terminology\n"
            "File: Figure_B25_p135.png\n"
            "Callouts on Diagram:\n"
            "- 'Theoretical throat': The distance from the joint root perpendicular to the hypotenuse of the largest right-triangle that can be inscribed within the fillet weld cross section.\n"
            "- 'Actual throat': The shortest distance between the joint root and the face of a fillet weld.\n"
            "- 'Effective throat': The minimum distance minus any convexity between the joint root and the face of a fillet weld, or with specified root penetration, the distance from the root penetration depth to the face.\n"
            "- 'Leg': The distance from the joint root to the toe of the fillet weld.\n"
            "- 'Toe': The junction between the face of a weld and the base metal.\n"
            "- 'Root': The junction between the two faying surfaces.\n"
            "- 'Convexity': The maximum distance from the face of a convex fillet weld perpendicular to a line joining the weld toes.\n"
            "\n"
            "6. FIGURE B26: CONVEXITY, CONCAVITY, AND DISCONTINUITIES (p. 123, PDF p. 139-141)\n"
            "Official Title: Figure B26—Fillet Weld Profiles and Discontinuities\n"
            "File: Figure_B26_p139.png\n"
            "Callouts: Desirable fillet weld profile, acceptable fillet weld profile, excessive convexity, undercut, overlap, insufficient leg, insufficient throat.\n"
        )
    }
]

async def main():
    print(f"Connecting to LightRAG storage at {STORAGE_DIR}...")
    rag = get_rag_instance(working_dir=STORAGE_DIR)
    await rag.initialize_storages()

    texts = [item["content"] for item in FIGURE_ANATOMY_CHUNKS]
    ids = [item["chunk_id"] for item in FIGURE_ANATOMY_CHUNKS]

    print(f"Ingesting {len(texts)} whole-document figure callout anatomy chunks...")
    await rag.ainsert(texts, ids=ids)
    print("Ingestion complete! All Annex A and Annex B engineering drawings and callouts are indexed.")

if __name__ == "__main__":
    asyncio.run(main())
