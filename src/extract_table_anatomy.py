"""
extract_table_anatomy.py: Ingests structured table cell matrices and critical footnotes
for AWS A3.0:2020 Annex A Tables (Tables A1 through A5).

Ensures that any question regarding process letter designations, abbreviations,
cross-references, or table footnotes (such as footnote a, b) is directly answerable.
"""

import asyncio
from pathlib import Path
from src.config import STORAGE_DIR
from src.indexer import get_rag_instance

TABLE_ANATOMY_CHUNKS = [
    {
        "chunk_id": "annex_a_tables_a1_a5_matrices_and_footnotes_v2",
        "content": (
            "[AWS A3.0:2020 Annex A - Tables A1 through A5 Letter Designations, Matrices & Footnotes]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex A (Informative) - Process and Classification Tables (Printed Pages 70-74, PDF Pages 82-87)\n"
            "\n"
            "1. TABLE A1: LETTER DESIGNATIONS OF WELDING, JOINING, AND ALLIED PROCESSES (p. 69-70, PDF p. 82-83)\n"
            "Official Title: Table A1—Letter Designations of Welding, Joining, and Allied Processes\n"
            "Full Process Designation Matrix:\n"
            "- Arc Welding: AHW (atomic hydrogen welding), BMAW (bare metal arc welding), CAW (carbon arc welding), "
            "CAW-G (gas carbon arc welding), CAW-S (shielded carbon arc welding), CAW-T (twin carbon arc welding), "
            "EGW (electrogas welding), FCAW (flux cored arc welding), FCAW-G (gas-shielded flux cored arc welding), "
            "FCAW-S (self-shielded flux cored arc welding), GMAW (gas metal arc welding), GMAW-P (pulsed gas metal arc welding), "
            "GMAW-S (short circuiting gas metal arc welding), GTAW (gas tungsten arc welding), GTAW-P (pulsed gas tungsten arc welding), "
            "MIAW (magnetically impelled arc welding), PAW (plasma arc welding), SMAW (shielded metal arc welding), "
            "SAW (submerged arc welding), SAW-S (series submerged arc welding), SW (stud arc welding).\n"
            "- Resistance Welding: FW (flash welding), RW-PC (pressure-controlled resistance welding), PW (projection welding), "
            "RSEW (resistance seam welding), RSEW-HF (high-frequency resistance seam welding), RSEW-I (induction resistance seam welding), "
            "RSEW-MS (mash resistance seam welding), RSW (resistance spot welding), UW (upset welding), "
            "UW-HF (high-frequency upset welding), UW-I (induction upset welding).\n"
            "- Solid-State Welding: CEW (coextrusion welding), CW (cold welding), DFW (diffusion welding), "
            "HIPW (hot isostatic pressure welding), EXW (explosion welding), FOW (forge welding), FRW (friction welding), "
            "FRW-DD (direct-drive friction welding), FSW (friction stir welding), FRW-I (inertia friction welding), "
            "HPW (hot pressure welding), ROW (roll welding), USW (ultrasonic welding).\n"
            "- Soldering: DS (dip soldering), FS (furnace soldering), IS (induction soldering), IRS (infrared soldering), "
            "INS (iron soldering), RS (resistance soldering), TS (torch soldering), USS (ultrasonic soldering), WS (wave soldering).\n"
            "- Brazing: BB (block brazing), CAB (controlled atmosphere brazing), DFB (diffusion brazing), DB (dip brazing), "
            "EBB (electron beam brazing), EXB (exothermic brazing), FLB (flow brazing), FB (furnace brazing), "
            "IB (induction brazing), IRB (infrared brazing), LBB (laser beam brazing), RB (resistance brazing), "
            "TB (torch brazing), TCAB (twin carbon arc brazing).\n"
            "- Oxyfuel Gas Welding: AAW (air acetylene welding), OAW (oxyacetylene welding), OHW (oxyhydrogen welding), PGW (pressure gas welding).\n"
            "- High Energy Beam Welding: EBW (electron beam welding), EBW-HV (high vacuum electron beam), "
            "EBW-MV (medium vacuum electron beam), EBW-NV (nonvacuum electron beam), LBW (laser beam welding).\n"
            "- Thermal Spraying (Allied): THSP (thermal spraying master acronym), ASP (arc spraying), CS (cold spraying), "
            "FLSP (flame spraying), FLSP-P (powder flame spraying), FLSP-W (wire flame spraying), HVAF (high velocity air fuel spraying), "
            "HVOF (high velocity oxyfuel spraying), PSP (plasma spraying), VPSP (vacuum plasma spraying), D-SP (detonation flame spraying).\n"
            "- Other Welding: AB (arc brazing), BW (braze welding), ABW (arc braze welding), CABW (carbon arc braze welding), "
            "EBBW (electron beam braze welding), EXBW (exothermic braze welding), FLOW (flow welding), "
            "LBBW (laser beam braze welding), ESW (electroslag welding), ESW-CG (consumable guide electroslag welding), "
            "IW (induction welding), PEW (percussion welding), TW (thermit welding).\n"
            "\n"
            "2. TABLE A2: ALPHABETICAL CROSS-REFERENCE TO TABLE A1 BY PROCESS (p. 71-72, PDF p. 84-85)\n"
            "Official Title: Table A2—Alphabetical Cross-Reference to Table A1 by Process\n"
            "Cross-references every process name alphabetically to its Table A1 letter designation (e.g. oxyacetylene welding -> OAW, oxyhydrogen welding -> OHW).\n"
            "\n"
            "3. TABLE A3: ALPHABETICAL CROSS-REFERENCE TO TABLE A1 BY LETTER DESIGNATION (p. 72-73, PDF p. 85-86)\n"
            "Official Title: Table A3—Alphabetical Cross-Reference to Table A1 by Letter Designation\n"
            "Cross-references every letter designation alphabetically A-Z to its standard process name.\n"
            "\n"
            "4. TABLE A4: SUFFIXES FOR APPLICATION MODE OF WELDING, JOINING, AND ALLIED PROCESSES (p. 74, PDF p. 87)\n"
            "Official Title: Table A4—Suffixes for Application Mode of Welding, Joining, and Allied Processes\n"
            "Suffix letter designations:\n"
            "- Adaptive control: -AD\n"
            "- Automatic: -AU\n"
            "- Manual: -MA\n"
            "- Mechanized: -ME\n"
            "- Robotic: -RO\n"
            "- Semiautomatic: -SA\n"
            "Application format: Added to a process designator in format XXXX-YY (e.g., manual gas tungsten arc welding is GTAW-MA).\n"
            "\n"
            "5. TABLE A5: OBSOLETE OR SELDOM USED PROCESSES (p. 74, PDF p. 87)\n"
            "Official Title: Table A5—Obsolete or Seldom Used Processes\n"
            "Lists obsolete or seldom used processes and variations with letter designations:\n"
            "- air acetylene welding: AAW\n"
            "- atomic hydrogen welding: AHW\n"
            "- bare metal arc welding: BMAW\n"
            "- block brazing: BB\n"
            "- carbon arc brazing: CAB\n"
            "- carbon arc braze welding: CABW\n"
            "- firecracker welding (no letter designation)\n"
            "- flow brazing: FLB\n"
            "- flow welding: FLOW\n"
            "- gas carbon arc welding: CAW-G\n"
            "- shielded carbon arc welding: CAW-S\n"
            "- twin carbon arc brazing: TCAB\n"
            "- twin carbon arc welding: CAW-T\n"
        )
    }
]

async def main():
    print(f"Connecting to LightRAG storage at {STORAGE_DIR}...")
    rag = get_rag_instance(working_dir=STORAGE_DIR)
    await rag.initialize_storages()

    texts = [item["content"] for item in TABLE_ANATOMY_CHUNKS]
    ids = [item["chunk_id"] for item in TABLE_ANATOMY_CHUNKS]

    print(f"Ingesting {len(texts)} whole-document table matrices and footnotes...")
    await rag.ainsert(texts, ids=ids)
    print("Ingestion complete! All Annex A tables, cells, designations, and footnotes are indexed.")

if __name__ == "__main__":
    asyncio.run(main())
