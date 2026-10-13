"""
extract_annex_d_modifications.py: Ingestion of AWS A3.0M/A3.0:2020 Annex D
(Modifications to A3.0M/A3.0:2020 from A3.0M/A3.0:2010), Tables D1 through D6,
and Annex E & F (Terminology from Other Sources & Official Interpretation Procedures).

Ensures that any question regarding standards evolution, new terms added in the 2020 edition,
modified definitions, shifted nonstandard terms, deleted chemistry terms, or official inquiry procedures
is completely answerable with exact citations.
"""

import asyncio
from pathlib import Path
from src.config import STORAGE_DIR
from src.indexer import get_rag_instance

ANNEX_D_MODIFICATIONS_CHUNKS = [
    {
        "chunk_id": "annex_d_modifications_tables_d1_through_d6",
        "content": (
            "[AWS A3.0:2020 Annex D - Modifications to A3.0M/A3.0:2020 from 2010 Edition (Tables D1-D6)]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex D (Informative) - Modifications (Printed Pages 165-170, PDF Pages 177-182)\n"
            "\n"
            "1. TABLE D1: NEW TERMS AND DEFINITIONS ADDED IN 2020 EDITION (p. 165-166, PDF p. 177-178):\n"
            "Over 120 new standard terms and definitions added to the 13th edition, including:\n"
            "- Waveform & Power: 'waveform-controlled welding, arc welding', 'average instantaneous power (AIP)', "
            "'total instantaneous energy (TIE)', 'arc energy (E)', 'welding waveform'.\n"
            "- Additive Manufacturing: 'additive manufacturing' introduced as a standard term.\n"
            "- Positions & Couplings: '2F, pipe', '3F, pipe', '3G, pipe', '4G, pipe', 'orbital welding', 'out-of-position welding'.\n"
            "- Friction Stir & Beam Welding: 'advancing side, friction stir welding', 'retreating side, friction stir welding', "
            "'advancing side, high energy beam welding', 'retreating side, high energy beam welding'.\n"
            "- Temper Bead Terminology: 'temper bead', 'temper bead sequence', 'temper pass', 'toe temper bead', 'toe temper pass'.\n"
            "- Geometry & Joints: 'parallel joint', 'butting workpiece', 'nonbutting workpiece', 'end dam', 'shelf bar', "
            "'sump, ESW and EGW', 'bevel depth', 'groove depth', 'fusion depth', 'reentrant angle', 'toe reentrant angle', 'bead reentrant angle'.\n"
            "- Qualification & Governance: 'performance qualification', 'PQTR', 'performance qualification variable', "
            "'welding procedure qualification variable', 'welder performance qualification variable', 'qualification authority', "
            "'qualified brazer', 'qualified solderer', 'qualified welder'.\n"
            "- Plastic Welding: 'electrofusion welding (EFW), thermoplastics', 'hot gas welding (HGW), thermoplastics', "
            "'infrared welding (IRW), thermoplastics', 'vibration welding (VW), plastics', 'spin welding (SPW), plastics'.\n"
            "\n"
            "2. TABLE D2: MODIFIED TERMS AND DEFINITIONS IN 2020 EDITION (p. 167-168, PDF p. 179-180):\n"
            "Over 120 existing terms updated or refined, including:\n"
            "- 'joint type': Definition modified to: 'A weld joint classification based on the relative orientation of the members being joined. "
            "The five basic joint types are the butt, corner, lap, parallel, and T-joints.'\n"
            "- 'parallel joint': Substituted for 'edge joint'.\n"
            "- 'effective throat' & 'theoretical throat': Definitions updated for geometric precision.\n"
            "- 'autogenous weld', 'defect', 'linear indication', 'rounded indication', 'nondestructive examination (NDE)', "
            "'1G', '2FR', '2G, pipe', '4F, pipe', '6G, pipe', '6GR, pipe', 'pulsed gas metal arc welding (GMAW-P)', "
            "'pulsed gas tungsten arc welding (GTAW-P)', 'short circuiting transfer, GMAW', 'underfill', 'weldability'.\n"
            "\n"
            "3. TABLE D3: TERMS/DEFINITIONS WITH EDITORIAL REVISIONS (p. 169, PDF p. 181):\n"
            "Terms updated with minor wording or cross-reference formatting, including:\n"
            "- '5F, pipe', 'bevel angle', 'bevel face', 'bevel radius', 'burn-through', 'corner joint', "
            "'diffusion brazing (DFB)', 'double-bevel groove', 'flare-V-groove weld', 'flash welding (FW)', "
            "'flow brazing (FLB)', 'groove angle', 'machine welding', 'scarf groove', 'single-J groove', "
            "'square-groove weld', 'thermal spraying (THSP)', 'wash pass', 'wave soldering (WS)', 'work angle'.\n"
            "\n"
            "4. TABLE D4: TERMS REVISED FROM STANDARD TO NONSTANDARD (p. 170, PDF p. 182):\n"
            "The following terms were downgraded from standard to nonstandard in the 2020 edition:\n"
            "- 'cored solder' (Nonstandard; standard is flux cored soldering filler metal).\n"
            "- 'penetration-enhancing flux, gas tungsten arc welding' (Nonstandard; standard is penetration-enhancing compound).\n"
            "- 'multiple impulse welding' (Nonstandard; standard is pulsation welding, resistance welding).\n"
            "\n"
            "5. TABLE D5: TERMS REVISED FROM NONSTANDARD TO STANDARD (p. 170, PDF p. 182):\n"
            "The following terms were upgraded from nonstandard to standard in the 2020 edition:\n"
            "- 'air cap' (Standardized for thermal spraying).\n"
            "- 'machine welding' (Standardized; defined as welding with equipment that has controls that can be adjusted by the operator).\n"
            "- 'nondestructive evaluation' (Standardized as a synonym pointing to nondestructive examination).\n"
            "- 'nondestructive inspection (NDI)' (Standardized as a synonym pointing to nondestructive examination).\n"
            "- 'nondestructive testing (NDT)' (Standardized as a synonym pointing to nondestructive examination).\n"
            "- 'pulsation welding, resistance welding' (Standardized for resistance welding).\n"
            "\n"
            "6. TABLE D6: DELETED TERMS IN 2020 EDITION (p. 170, PDF p. 182):\n"
            "29 terms completely deleted from the standard, including obsolete physical science entries and redundant terms:\n"
            "- Deleted Chemistry & Physical Science Terms: 'covalent bond', 'ionic bond', 'metal', 'differential thermal expansion'.\n"
            "- Deleted Redundant Process & Electrical Terms: 'automatic arc welding current', 'automatic arc welding downslope time', "
            "'automatic arc welding upslope time', 'brazed joint', 'brittle nugget', 'carbon arc brazing', 'direct welding, resistance welding', "
            "'electroslag welding electrode', 'fill weld', 'forge-delay time, resistance welding', 'full fillet weld', 'incomplete bond', "
            "'indirect welding, resistance welding', 'parallel welding', 'pulse, resistance welding', 'random intermittent welds', "
            "'reaction stress', 'resistance welding current', 'resistance welding downslope time', 'resistance welding time', "
            "'resistance welding upslope time', 'selective block sequence', 'series welding', 'weld time', 'welder registration'.\n"
        )
    },
    {
        "chunk_id": "annex_e_and_f_sources_and_interpretation_procedures",
        "content": (
            "[AWS A3.0:2020 Annex E & Annex F - External ISO Sources & Official Interpretation Procedures]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annexes: Annex E (Informative) & Annex F (Informative) (Printed Pages 171-174, PDF Pages 183-186)\n"
            "\n"
            "1. ANNEX E: TERMINOLOGY FROM OTHER SOURCES (p. 171, PDF p. 183):\n"
            "Lists corresponding international standards for welding terminology:\n"
            "- ISO Standards: ISO 857-1 (Metal welding processes), ISO 857-2 (Soldering and brazing), ISO 15296 (Gas welding equipment), "
            "ISO 17659 (Multilingual terms for welded joints with illustrations), ISO 17677-1 (Resistance welding), "
            "ISO/TR 25901 (Welding and related processes vocabulary), ISO 25239-1 (Friction stir welding aluminum vocabulary).\n"
            "- IIW Documents: Multilingual collection of terms (MCT): Part 1 (General terms), Part 2 (Gas welding), "
            "Part 5 (Thermal cutting), Part 6 (Hot spraying), Part 7 (Brazing, soldering, braze welding), Part 9 (Special processes).\n"
            "\n"
            "2. ANNEX F: REQUESTING AN OFFICIAL INTERPRETATION ON AN AWS STANDARD (p. 173-174, PDF p. 185-186):\n"
            "Requirements for Submitting Inquiries to AWS Technical Committees:\n"
            "- F3.1 Submission: Sent electronically to standards@aws.org or mailed to Managing Director, Standards Development, "
            "American Welding Society, 8669 NW 36 St, # 130, Miami, FL 33166.\n"
            "- F3.3 Scope: Each inquiry shall address ONE single provision of the standard unless two provisions are interrelated. "
            "Must state edition (e.g. A3.0M/A3.0:2020).\n"
            "- F3.4 Question Format: All requests MUST be stated in the form of a question that can be answered 'yes' or 'no'. "
            "Sketches, figures, paragraphs, and tables must be cited.\n"
            "- F3.5 Proposed Answer: The inquirer MUST provide proposed answer(s) to their own question(s).\n"
            "- F4 & F5 Official AWS Policy: All interpretations are approved by the technical committee, published in the Welding Journal, "
            "and posted on the AWS website. Telephone inquiries cannot receive official interpretations.\n"
        )
    },
    {
        "chunk_id": "annex_f_official_interpretation_procedures_dedicated",
        "content": (
            "[AWS A3.0:2020 Annex F - Requesting an Official Interpretation on an AWS Standard]\n"
            "Document: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions\n"
            "Annex: Annex F (Informative) - Guidelines for Requesting an Official Interpretation on an AWS Standard (Printed Pages 173-174, PDF Pages 185-186)\n"
            "Heading: Annex F Official Inquiry Procedures and Format Requirements (Clauses F1 through F5)\n"
            "\n"
            "REQUIRED FORMAT AND SUBMISSION PROCEDURES FOR REQUESTING AN OFFICIAL INTERPRETATION (Annex F):\n"
            "1. Submission Procedures (Clause F3.1):\n"
            "All inquiries requesting an official interpretation on an AWS standard must be submitted in writing to the American Welding Society.\n"
            "- Electronic Submissions: Inquiries can be submitted electronically by emailing standards@aws.org.\n"
            "- Written/Postal Submissions: Inquiries may be addressed to: American Welding Society, Attention: Managing Director, Standards Development, 8669 NW 36 St, # 130, Miami, FL 33166.\n"
            "- Telephone inquiries cannot receive an official interpretation. Only written inquiries received by AWS receive official interpretations.\n"
            "\n"
            "2. Required Question Format (Clause F3.4):\n"
            "All requests for interpretation MUST be stated in the form of a specific question that can be answered with a simple 'yes' or 'no'. "
            "The question must cite the applicable edition, paragraph(s), figure(s), table(s), or sketch(es) from the standard.\n"
            "\n"
            "3. Inquirer's Proposed Answer (Clause F3.5):\n"
            "The inquirer MUST provide a proposed answer (or answers) to their own question(s) at the time of submission.\n"
            "\n"
            "4. Scope of Provision and Limitations (Clause F3.2 and Clause F3.3):\n"
            "Each inquiry shall address ONE single provision of the standard, unless two or more provisions are interrelated. "
            "General questions or requests for consulting services will be returned without interpretation.\n"
            "\n"
            "5. Committee Approval and Publication (Clause F4 and Clause F5):\n"
            "Interpretations are formulated and approved by the responsible AWS technical committee. "
            "Official interpretations are published in the Welding Journal and posted on the official AWS website."
        )
    }
]

async def main():
    print(f"Connecting to LightRAG storage at {STORAGE_DIR}...")
    rag = get_rag_instance(working_dir=STORAGE_DIR)
    await rag.initialize_storages()

    texts = [item["content"] for item in ANNEX_D_MODIFICATIONS_CHUNKS]
    ids = [item["chunk_id"] for item in ANNEX_D_MODIFICATIONS_CHUNKS]

    print(f"Ingesting {len(texts)} Annex D, E, and F chunks into LightRAG...")
    await rag.ainsert(texts, ids=ids)
    print("Ingestion complete! All Annex D revision tables (D1-D6) and Annex E/F procedures are indexed.")

if __name__ == "__main__":
    asyncio.run(main())
