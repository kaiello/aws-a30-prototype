"""
extract_annex_c_style_and_decisions.py: Ingestion of AWS A3.0M/A3.0:2020 Annex C
(Principles of A3.0M/A3.0 Style) and the 8 Official Definitions Subcommittee Decisions (C1.5.1 through C1.5.8).

Ensures that any question regarding terminology governance, standard vs nonstandard rationale,
subcommittee rulings (bonding vs welding, GTAW vs TIG, parallel joint vs edge joint, welder vs weldor),
or definition style is directly answerable with verbatim precision and exact printed page citations.
"""

import asyncio
from pathlib import Path
from src.config import STORAGE_DIR
from src.indexer import get_rag_instance

ANNEX_C_STYLE_CHUNKS = [
    {
        "chunk_id": "annex_c_style_rules_and_committee_decisions_c1_c2_v2",
        "content": (
            "[AWS A3.0:2020 Annex C - Principles of A3.0M/A3.0 Style & Official Subcommittee Decisions]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex C (Informative) - Principles of A3.0M/A3.0 Style (Printed Pages 159-164, PDF Pages 171-176)\n"
            "\n"
            "1. TERMINOLOGY SELECTION & CONSTRUCTION PRINCIPLES (Clause C1, p. 159-160):\n"
            "- Standard vs Nonstandard Typography: Standard terms are printed in boldface type when defined or in cross-references; "
            "nonstandard terms are printed in lightface type.\n"
            "- Nonstandard Formula: Nonstandard definitions begin with 'A nonstandard term for...' (if term has no standard use) "
            "or 'A nonstandard term when used for...' (if it has standard meaning in other contexts). "
            "If misuse of a term may endanger personal safety, it is identified as both nonstandard and incorrect (e.g. 'ground lead').\n"
            "- Application Mode Suffixes: Appended to process designations according to Table A4 (e.g., B-AU for automatic brazing, GMAW-S-RO for robotic short circuiting gas metal arc welding).\n"
            "- Obsolete or Seldom Used Process: Alerted by incorporating 'This is an obsolete or seldom used process.' in the definition (summarized in Table A5).\n"
            "\n"
            "2. THE 8 OFFICIAL DEFINITIONS SUBCOMMITTEE DECISIONS (Clause C1.5, p. 160-163):\n"
            "- C1.5.1 'bonding': The Definitions Subcommittee discourages the use of 'bonding' for 'welding.' The term bonding is reserved strictly for joining and allied processes where either an adhesive bond or a mechanical bond is predominant at the interface (adhesive bonding, brazing, soldering, thermal spraying). When an atomic bond between atoms is predominant, the joint is a weld and the process is welding, whether created by fusion or in the solid state.\n"
            "- C1.5.2 'diffusion welding': Consistent with international custom (BS499). Replaces 'diffusion bonding'. The origin of 'diffusion bonding' was an aircraft industry euphemism where welding was avoided because welded structures had an unearned reputation for failure; A3.0 rejects this prejudice.\n"
            "- C1.5.3 'gas tungsten arc welding (GTAW) & gas metal arc welding (GMAW) versus TIG & MIG': GTAW and GMAW are standard; TIG and MIG are nonstandard. The use of 'inert' is inaccurate because modern processes frequently use active gases (e.g. CO2, O2, Ar-H2). Calling it TAG or MAG based on gas mixture creates absurdities where process names change with base metals. Both GTAW and GMAW belong to a coherent, unified letter designation system.\n"
            "- C1.5.4 'welder' versus 'welding machine' versus 'weldor': 'welder' is the person who performs welding. 'welding machine' is the equipment. The alternate spelling 'weldor' was proposed to distinguish them, but is rejected because spoken English pronunciation of welder and weldor is phonetically identical.\n"
            "- C1.5.5 'workpiece': Designated standard term for the part to be welded, brazed, soldered, thermal cut, or sprayed. Webster's Third New International Dictionary defines workpiece specifically as a piece of work in process of manufacture, whereas component, member, or part carry non-manufacturing connotations.\n"
            "- C1.5.6 'nondestructive examination (NDE)': Established in the 2001 edition in consultation with ASME, ASNT, and ASTM. Defined as 'The process of determining acceptability of a material or a component in accordance with established criteria without impairing its future usefulness.' NDE determines 'acceptability' rather than guaranteeing 'suitability for intended purpose'. NDT, NDI, and nondestructive evaluation are standard alternatives that cross-reference NDE.\n"
            "- Annex C1.5.7 'parallel joint' (replaces 'edge joint' in the 2020 edition): Clause C1.5.7 explains why the term 'parallel joint' was introduced in the 2020 edition to replace 'edge joint'. Historically, five basic joint types were recognized (butt, corner, edge, lap, T-joint). All describe relative member orientation except edge joint, which instead described weld location and caused confusion with edge weld. In an effort to correct this irregularity, parallel joint was introduced to describe member orientation: 'A joint type formed by butting, parallel surfaces of one or more workpieces with flush ends.' The five standard basic joint types are now: butt, corner, lap, parallel, and T-joints.\n"
            "- C1.5.8 'deposit': The term deposit and its derivatives are used ONLY in connection with filler metal or surfacing material. Use with weld metal, weld bead, or weld is nonstandard.\n"
            "\n"
            "3. DEFINITION STYLE AND FORMAT REQUIREMENTS (Clause C2, p. 163-164):\n"
            "- Complete in one succinct sentence: Completes with a simple verb such as 'is' or 'means' substituted for the period separating term and definition.\n"
            "- No abbreviations or units: Abbreviations and letter designations are excluded from definitions; units of measurement are not included in definitions.\n"
            "- Parts of Speech Formatting: Verbs are stated in infinitive with comma and italic 'v.' (e.g. 'braze, v. To join materials...'); adjectives with comma and italic 'adj.' (e.g. 'as-welded, adj.'); nouns are stated in singular form; gerunds ending in 'ing' are used where verbs are treated as nouns.\n"
            "- Cross-reference Syntax: Cross-references begin with 'See' for figures/tables, and 'See also' for terms, ordered: figures, tables, then alphabetical terms.\n"
        )
    },
    {
        "chunk_id": "annex_c_clause_c1_5_7_parallel_joint_vs_edge_joint_dedicated",
        "content": (
            "[AWS A3.0:2020 Annex C - Clause C1.5.7 Parallel Joint Replacing Edge Joint]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex C (Informative) - Principles of A3.0M/A3.0 Style, Clause C1.5.7 (Printed Pages 162-163, PDF Pages 174-175)\n"
            "Heading: Annex C1.5.7 and Clause C1.5.7 'parallel joint'\n"
            "\n"
            "DEFINITIONS SUBCOMMITTEE RATIONALE FOR INTRODUCING PARALLEL JOINT TO REPLACE EDGE JOINT (Clause C1.5.7):\n"
            "In the 2020 edition of AWS A3.0M/A3.0, the Definitions Subcommittee introduced the standard term 'parallel joint' to replace 'edge joint'.\n"
            "1. Historical Five Joint Types: Historically, five basic joint types were recognized in welding: butt joint, corner joint, edge joint, lap joint, and T-joint.\n"
            "2. Irregularity of 'Edge Joint': All of the basic joint types described relative member orientation except 'edge joint'. "
            "Instead of describing workpiece orientation, 'edge joint' described the location of the weld on the joint edges. "
            "This caused significant confusion with the term 'edge weld'.\n"
            "3. Correction in 2020 Edition: To eliminate this irregularity, the Definitions Subcommittee introduced 'parallel joint' "
            "so that all five basic joint types strictly describe member orientation. A parallel joint is formally defined as: "
            "'A joint type formed by butting, parallel surfaces of one or more workpieces with flush ends.'\n"
            "4. Current Basic Joint Types: The five basic joint types are butt, corner, lap, parallel, and T-joints. "
            "Edge joint is now a historical/nonstandard synonym replaced by parallel joint."
        )
    }
]

async def main():
    print(f"Connecting to LightRAG storage at {STORAGE_DIR}...")
    rag = get_rag_instance(working_dir=STORAGE_DIR)
    await rag.initialize_storages()

    texts = [item["content"] for item in ANNEX_C_STYLE_CHUNKS]
    ids = [item["chunk_id"] for item in ANNEX_C_STYLE_CHUNKS]

    print(f"Ingesting {len(texts)} Annex C style principles & committee decision chunks...")
    await rag.ainsert(texts, ids=ids)
    print("Ingestion complete! All Annex C style rules and subcommittee decisions are indexed.")

if __name__ == "__main__":
    asyncio.run(main())
