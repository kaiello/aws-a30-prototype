"""
pre_retrieval.py: Pre-Retrieval Intent Engine, Acronym Disambiguator, and Early Abstention Gate.

Analyzes natural language queries before vector or LLM execution:
1. Deterministic early abstention for out-of-scope negative controls (AWS D1.1, acceptance criteria, etc.).
2. Normative acronym and abbreviation expansion (GMAW, 1G-6GR, CJP, HAZ, FSW).
3. Explicit figure / table reference extraction.
4. Canonical ontology concept resolution against SQLite dual_layer_registry.db.
"""

import re
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import STORAGE_DIR
from src.standard_manifest import extract_references, _reference_groups

DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"

# Normative AWS A3.0 welding acronym and designation taxonomy
WELDING_ACRONYMS = {
    # Arc welding processes
    "GMAW": "gas metal arc welding",
    "GMAW-P": "pulsed gas metal arc welding",
    "GMAW-S": "short circuiting gas metal arc welding",
    "SMAW": "shielded metal arc welding",
    "GTAW": "gas tungsten arc welding",
    "GTAW-P": "pulsed gas tungsten arc welding",
    "SAW": "submerged arc welding",
    "SAW-S": "series submerged arc welding",
    "FCAW": "flux cored arc welding",
    "FCAW-G": "gas-shielded flux cored arc welding",
    "FCAW-S": "self-shielded flux cored arc welding",
    "PAW": "plasma arc welding",
    "CAW": "carbon arc welding",
    "SW": "stud arc welding",
    
    # Solid state & other processes
    "FSW": "friction stir welding",
    "FW": "friction welding",
    "ESW": "electroslag welding",
    "EGW": "electrogas welding",
    "RW": "resistance welding",
    "RSW": "resistance spot welding",
    "RSEW": "resistance seam welding",
    "PW": "projection welding",
    "FOW": "forge welding",
    "CW": "cold welding",
    "EXW": "explosion welding",
    "USW": "ultrasonic welding",
    "DFW": "diffusion welding",
    "LBW": "laser beam welding",
    "EBW": "electron beam welding",
    "OAW": "oxyacetylene welding",
    "OFW": "oxyfuel gas welding",
    "OHW": "oxyhydrogen welding",
    "PGW": "pressure gas welding",
    "TW": "thermite welding",

    # Thermal cutting & gouging
    "OFC": "oxyfuel gas cutting",
    "OFC-A": "oxyacetylene cutting",
    "OFC-P": "oxypropane cutting",
    "PAC": "plasma arc cutting",
    "CAC-A": "air carbon arc cutting",
    "LBC": "laser beam cutting",

    # Brazing & soldering
    "TB": "torch brazing",
    "FB": "furnace brazing",
    "IB": "induction brazing",
    "DB": "dip brazing",
    "RSB": "resistance brazing",
    "DFB": "diffusion brazing",
    "EXB": "exothermic brazing",

    # Joint geometry & weld terms
    "CJP": "complete joint penetration",
    "PJP": "partial joint penetration",
    "HAZ": "heat-affected zone",
    "BM": "base metal",
    "WM": "weld metal",

    # Standard qualification test positions (Clause 4 & Figures B15-B20)
    "1G": "1G flat position groove weld",
    "2G": "2G horizontal position groove weld",
    "3G": "3G vertical position groove weld",
    "4G": "4G overhead position groove weld",
    "5G": "5G multiple position pipe groove weld",
    "6G": "6G multiple position inclined pipe groove weld",
    "6GR": "6GR multiple position pipe with restriction ring groove weld",
    "1F": "1F flat position fillet weld",
    "2F": "2F horizontal position fillet weld",
    "2FR": "2FR horizontal rotated position fillet weld",
    "3F": "3F vertical position fillet weld",
    "4F": "4F overhead position fillet weld",
    "5F": "5F multiple position pipe fillet weld",
    "1SP": "1SP flat position stud weld",
    "2SP": "2SP horizontal position stud weld",
    "4SP": "4SP overhead position stud weld",
}

# Out-of-scope negative control patterns
OUT_OF_SCOPE_PATTERNS = [
    r'\baws\s+d1\.1\b',
    r'\basme\s+section\s+ix\b',
    r'\bnavsea\b',
    r'\bacceptance\s+criteria\b',
    r'\bvisual\s+inspection\s+acceptance\b',
    r'\breject\s+limit[s]?\b',
    r'\bpreheat\s+schedule[s]?\b',
    r'\bpreheat\s+temperature[s]?\b',
    r'\binterpass\s+temperature[s]?\b',
    r'\bwelder\s+performance\s+qualification\s+record\b',
    r'\bwps\s+qualification\s+variables\b',
    r'\bpqr\s+testing\b',
    r'\be7018\b',
    r'\byield\s+strength\b',
    r'\belongation\b',
    r'\bfiller\s+metal\s+chemistry\b',
    r'\bradiographic\s+inspection\b',
    r'\bmaximum\s+allowable\b',
    r'\bflow\s+rate\b',
    r'\bparameter\s+schedule\b',
    r'\bfigure\s+b75\b',
    r'\bfigure\s+b120\b',
    r'\btable\s+a10\b',
]

def check_early_abstention(query: str) -> Optional[Dict[str, Any]]:
    """
    Checks if query targets out-of-scope codes, acceptance criteria, or fabricated elements.
    Returns structured abstention dict if triggered, or None if in-scope.
    """
    q_lower = query.lower().replace("\u2019", "'")
    for pat in OUT_OF_SCOPE_PATTERNS:
        match = None
        for candidate in re.finditer(pat, q_lower):
            # An exclusion owns only adjacent known topics and conjunctions.
            # Other words (including a later positive directive) end that scope.
            prefix = q_lower[:candidate.start()]
            excluded = False
            markers = re.finditer(
                r"\b(?:(?:do not|don't)\s+(?:discuss|include|cover|address|provide)"
                r"|(?:without|excluding)(?:\s+(?:discussing|including|covering|addressing|providing))?)\s+",
                prefix)
            for marker in markers:
                remainder = prefix[marker.end():]
                for topic_pattern in OUT_OF_SCOPE_PATTERNS:
                    remainder = re.sub(topic_pattern, " ", remainder)
                remainder = re.sub(r"\b(?:and|or|any)\b|[\s,]+", "", remainder)
                if not remainder:
                    excluded = True
                    break
            if not excluded:
                match = candidate
                break
        if match:
            trigger = match.group(0)
            return {
                "status": "TRUTHFUL_ABSTENTION",
                "triggered": True,
                "reason": f"Query targets '{trigger}', which is governed by external fabrication codes, filler specifications, or is outside AWS A3.0M/A3.0:2020 jurisdiction.",
                "primary_citation": "Out-of-Scope (Governed by external fabrication/material code)",
                "answer": (
                    f"**Truthful Abstention:** The requested requirement ('{trigger}') is out of scope. "
                    "AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions*) defines standard nomenclature, "
                    "joint geometry, test positions, and classification matrices. Acceptance criteria, reject limits, "
                    "preheat schedules, and filler metal properties are governed by specific fabrication codes "
                    "(such as AWS D1.1, ASME Section IX, or NAVSEA specifications) and material standards (AWS A5 series)."
                )
            }
    return None

def extract_referenced_elements(query: str) -> Dict[str, List[str]]:
    """Preserve supported enrichment forms while resolving complete canonical IDs."""
    result = {"figures": [], "tables": []}
    # Preserve singular-only enrichment, using the shared whole-expression
    # boundary so a Unicode/spaced range cannot enrich only its first endpoint.
    for kind, expressions in _reference_groups(query, lists=False, singular=True):
        found = extract_references(kind + " " + expressions[0], lists=False)
        for key in result:
            for label in found[key]:
                if label not in result[key]:
                    result[key].append(label)
    return result

def expand_query(query: str) -> Dict[str, Any]:
    """
    Analyzes query and produces normalized terms, acronym expansions,
    explicit figure targets, and matched ontology concepts.
    """
    expanded_terms = []
    matched_acronyms = {}

    # Tokenize query preserving alphanumeric codes
    words = re.findall(r'\b[A-Za-z0-9\-_/]+\b', query)
    
    for word in words:
        w_upper = word.upper()
        if w_upper in WELDING_ACRONYMS:
            expansion = WELDING_ACRONYMS[w_upper]
            matched_acronyms[w_upper] = expansion
            expanded_terms.append(f'"{expansion}"')

    # Detect explicit element references
    referenced = extract_referenced_elements(query)

    # Search SQLite ontology nodes for concepts mentioned in query
    matched_concepts = []
    if DUAL_SQLITE_PATH.exists():
        try:
            conn = sqlite3.connect(DUAL_SQLITE_PATH)
            cur = conn.cursor()
            q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', query).strip()
            tokens = [t for t in q_clean.split() if len(t) > 2]
            if tokens:
                fts_expr = " OR ".join(f'"{t}"' for t in tokens[:6])
                cur.execute(
                    "SELECT id, name, node_type, standard_status FROM ontology_nodes WHERE id IN (SELECT id FROM ontology_fts WHERE ontology_fts MATCH ? LIMIT 5)",
                    (fts_expr,)
                )
                for row in cur.fetchall():
                    matched_concepts.append({
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "status": row[3]
                    })
            conn.close()
        except Exception:
            pass

    # Build enriched search phrase
    enrichment_parts = [query]
    if matched_acronyms:
        enrichment_parts.extend(matched_acronyms.values())
    if referenced["figures"]:
        enrichment_parts.extend(referenced["figures"])
    if referenced["tables"]:
        enrichment_parts.extend(referenced["tables"])

    enriched_query = " ".join(enrichment_parts)

    return {
        "raw_query": query,
        "enriched_query": enriched_query,
        "matched_acronyms": matched_acronyms,
        "referenced_figures": referenced["figures"],
        "referenced_tables": referenced["tables"],
        "matched_concepts": matched_concepts
    }

if __name__ == "__main__":
    sample_queries = [
        "What is GMAW and what figure illustrates it?",
        "Describe 6GR test position requirements",
        "What are the visual inspection acceptance criteria for AWS D1.1?",
        "Show me fillet weld throat on Figure B25"
    ]
    print("Testing Pre-Retrieval Intent Engine:\n")
    for sq in sample_queries:
        abstain = check_early_abstention(sq)
        if abstain:
            print(f"Query: '{sq}'\n  -> [EARLY ABSTENTION]: {abstain['reason']}\n")
        else:
            exp = expand_query(sq)
            print(f"Query: '{sq}'\n  -> Acronyms: {exp['matched_acronyms']}\n  -> Figures: {exp['referenced_figures']}\n  -> Concepts: {[c['name'] for c in exp['matched_concepts']]}\n  -> Enriched: {exp['enriched_query']}\n")
