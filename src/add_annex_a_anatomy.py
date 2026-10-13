"""
add_annex_a_anatomy.py: Ingests granular visual anatomy for Annex A Figures (A1-A6) into LightRAG.
Provides deep visual branch transcriptions for vector diagrams that have no selectable PDF text,
such as Figure A6 ('Flame Contact' -> Chemical -> Flux -> TB torch brazing, TS torch soldering).
"""

import asyncio
from pathlib import Path
from src.config import STORAGE_DIR
from src.indexer import get_rag_instance

ANNEX_A_FIGURE_ANATOMY = [
    {
        "chunk_id": "annex_a_figure_a6_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figure A6: Brazing and Soldering Classification Chart]\n"
            "Official Title: Figure A6—Brazing and Soldering Classification Chart (p. 79, PDF p. 92)\n"
            "File: Figure_A6_p92.png\n"
            "\n"
            "Visual Hierarchy & Branches:\n"
            "Root: Brazing and Soldering (See Figure A3)\n"
            "\n"
            "1. Branch: Chemical\n"
            "   - Sub-branch: Flame Contact\n"
            "     * Medium: Flux\n"
            "     * Processes Designated: TB (torch brazing), TS (torch soldering)\n"
            "     * Explanation: 'Flame Contact' is the heating mode under Chemical energy where heat is applied via direct contact with a flame, using flux as the protective/cleansing medium to perform torch brazing (TB) or torch soldering (TS).\n"
            "   - Sub-branch: Radiation\n"
            "     * Medium: Flux -> Processes: FB (furnace brazing), FS (furnace soldering)\n"
            "     * Medium: Gas -> Processes: FB (furnace brazing), B-CA (controlled-atmosphere brazing), FS (furnace soldering)\n"
            "   - Sub-branch: Conduction\n"
            "     * Medium: Flux -> Processes: EXB (exothermic brazing), WS (wave soldering), DS (dip soldering), INS (iron soldering)\n"
            "\n"
            "2. Branch: Radiation\n"
            "   - Pressure -> Gas -> DFB (diffusion brazing)\n"
            "   - Pressure -> Vacuum -> DFB (diffusion brazing)\n"
            "   - Flux -> FB (furnace brazing), IRB (infrared brazing), IRS (infrared soldering), FS (furnace soldering), EBB (electron beam brazing), LBB (laser beam brazing)\n"
            "   - Vacuum -> FB (furnace brazing), IRB (infrared brazing), EBB (electron beam brazing), LBB (laser beam brazing), B-CA (controlled-atmosphere brazing), FS (furnace soldering)\n"
            "\n"
            "Complete Process Designation Legend for Figure A6:\n"
            "AB = arc brazing, B-CA = controlled-atmosphere brazing, DB = dip brazing, DS = dip soldering, "
            "DFB = diffusion brazing, EBB = electron beam brazing, EXB = exothermic brazing, FB = furnace brazing, "
            "FS = furnace soldering, IB = induction brazing, IS = induction soldering, IRB = infrared brazing, "
            "IRS = infrared soldering, LBB = laser beam brazing, RB = resistance brazing, RS = resistance soldering, "
            "TB = torch brazing, TS = torch soldering, USS = ultrasonic soldering, WS = wave soldering.\n"
        )
    },
    {
        "chunk_id": "annex_a_figure_a1_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figure A1: Master Chart of Welding and Joining Processes]\n"
            "Official Title: Figure A1—Master Chart of Welding and Joining Processes (p. 75, PDF p. 88)\n"
            "File: Figure_A1_p88.png\n"
            "\n"
            "Visual Hierarchy & Branches:\n"
            "Root: Welding and Joining Processes\n"
            "1. Arc Welding (AW): SW, AHW, BMAW, CAW, CAW-G, CAW-S, CAW-T, EGW, FCAW, FCAW-G, FCAW-S, GMAW, GMAW-P, GMAW-S, GTAW, GTAW-P, MIAW, PAW, SMAW, SAW, SAW-S\n"
            "2. Resistance Welding (RW): FW, RW-PC, PW, RSEW, RSEW-HF, RSEW-I, RSEW-MS, RSW, UW, UW-HF, UW-I\n"
            "3. Solid-State Welding (SSW): CEW, CW, DFW, HIPW, EXW, FOW, FRW, FRW-DD, FSW, FRW-I, HPW, ROW, USW\n"
            "4. Soldering (S): DS, FS, IS, IRS, INS, RS, TS, USS, WS\n"
            "5. Oxyfuel Gas Welding (OFW): AAW, OAW, OHW, PGW\n"
            "6. Brazing (B): BB, CAB, DFB, DB, EBB, EXB, FLB, FB, IB, IRB, LBB, RB, TB, TCAB\n"
            "7. High Energy Beam Welding (HEBW): EBW, EBW-HV, EBW-MV, EBW-NV, LBW\n"
            "8. Other Welding and Joining: AB, BW, ABW, CABW, EBBW, EXBW, FLOW, LBBW, ESW, ESW-CG, IW, PEW, TW\n"
        )
    },
    {
        "chunk_id": "annex_a_figure_a4_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figure A4: Fusion Welding Classification Chart]\n"
            "Official Title: Figure A4—Fusion Welding Classification Chart (p. 77, PDF p. 90)\n"
            "File: Figure_A4_p90.png\n"
            "\n"
            "Visual Hierarchy & Branches:\n"
            "Classifies fusion welding processes by energy delivery and shielding mechanism across arc welding, gas welding, and high-energy beam processes.\n"
        )
    },
    {
        "chunk_id": "annex_a_figure_a5_anatomy",
        "content": (
            "[AWS A3.0:2020 Annex A - Figure A5: Solid-State Welding Classification Chart]\n"
            "Official Title: Figure A5—Solid-State Welding Classification Chart (p. 78, PDF p. 91)\n"
            "File: Figure_A5_p91.png\n"
            "\n"
            "Visual Hierarchy & Branches:\n"
            "Classifies solid-state processes: CEW, CW, DFW, EXW, FOW, FRW, FSW, HPW, IW, PGW, ROW, USW, UW.\n"
        )
    }
]

async def main():
    print(f"Connecting to LightRAG storage at {STORAGE_DIR}...")
    rag = get_rag_instance(working_dir=STORAGE_DIR)
    await rag.initialize_storages()
    
    texts = [item["content"] for item in ANNEX_A_FIGURE_ANATOMY]
    ids = [item["chunk_id"] for item in ANNEX_A_FIGURE_ANATOMY]
    
    print(f"Ingesting {len(texts)} granular Annex A visual anatomy chunks (including Figure A6 Flame Contact)...")
    await rag.ainsert(texts, ids=ids)
    print("Ingestion complete! Granular visual diagram trees are now searchable in knowledge graph and vectors.")

if __name__ == "__main__":
    asyncio.run(main())
