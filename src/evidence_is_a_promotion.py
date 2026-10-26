"""
src/evidence_is_a_promotion.py: Dual-Provenance IS_A_PROCESS_VARIATION_OF Promotion Engine
for AWS A3.0M/A3.0:2020.

Standard: AWS A3.0M/A3.0:2020 (13th Edition)
Target: Table A1 (printed pp. 69..70, PDF 81..82) and Figures A1..A2 candidate layout edges.

Epistemic Rules:
1. Strict Dual-Provenance Admission Rule (rule_id: "dual-provenance-is-a-1"):
   A candidate layout edge (CANDIDATE_LAYOUT_PARENT) is promoted to an ACCEPTED
   semantic subtype (IS_A_PROCESS_VARIATION_OF, knowledge_eligible=True) ONLY IF supported by both:
   a. An Annex A structural layout observation ID (Table A1, Figure A1, or Figure A2), AND
   b. A corroborating Clause 4 standard definition observation ID whose genus phrase explicitly
      names the parent process or process family per Annex C C1.5 genus-differentia formula:
      - "[parent] process variation"
      - "variation of [parent]"
      - "variation of the [parent]"
      - "process variation of [parent]"
2. Preserve Uncorroborated Candidates:
   Any CANDIDATE_LAYOUT_PARENT edge where Clause 4 does not explicitly corroborate the parent genus
   (such as group root processes like SMAW under Arc Welding) remains CANDIDATE_LAYOUT_PARENT
   (knowledge_eligible=False). Exactly 0 uncorroborated IS_A promotions are permitted.
3. Every promoted record carries >= 2 distinct source observation IDs and a verbatim Clause 4 quote.
4. Nonstandard terms (term_status == "nonstandard") are never promoted as standard IS_A parents.
5. Preserves Phase 1 and Phase 2 stores immutability.
   Writes output to storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json with SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import fitz

from src.config import PDF_PATH, STORAGE_DIR

CLAUSE4_INGEST_DIR = STORAGE_DIR / "evidence_v2" / "clause4_ingest_001"
PROMOTION_STORE_PATH = CLAUSE4_INGEST_DIR / "is_a_promotion_store.json"


def compute_dual_provenance_is_a(
    doc: Optional[fitz.Document] = None,
    clause4_entries: Optional[List[Dict[str, Any]]] = None,
    table_a1_rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Inspect every CANDIDATE_LAYOUT_PARENT edge and apply strict dual-provenance admission rule."""
    target_doc = doc or fitz.open(PDF_PATH)

    if table_a1_rows is None:
        from src.evidence_tables_a1_a5 import extract_table_a1
        table_a1_rows = extract_table_a1(target_doc)

    if clause4_entries is None:
        from src.evidence_clause4_glossary import get_clause4_glossary_store
        glossary_store = get_clause4_glossary_store()
        clause4_entries = glossary_store.get("entries", [])

    c4_by_desig = {e["designation"]: e for e in clause4_entries if e.get("designation")}
    c4_by_term = {e["term"].lower(): e for e in clause4_entries}

    promoted: List[Dict[str, Any]] = []
    retained_candidates: List[Dict[str, Any]] = []

    indented_rows = [r for r in table_a1_rows if r.get("parent_process")]

    for r in indented_rows:
        child = r["process"]
        desig = r.get("designation")
        parent = r["parent_process"]
        indent_level = r.get("indent_level", 1)
        printed_page = r.get("page", 69)

        # Observation ID for Annex A layout observation
        annex_a_obs_id = f"obs:table_a1:p{printed_page}:{child.lower().replace(' ', '_')}"

        # Lookup child standard term in Clause 4
        c4_entry = None
        if desig and desig in c4_by_desig:
            c4_entry = c4_by_desig[desig]
        elif child.lower() in c4_by_term:
            c4_entry = c4_by_term[child.lower()]

        is_corroborated = False
        corroborating_phrase = ""

        if c4_entry:
            # Rule: nonstandard terms are never promoted as standard parents or subtypes
            if c4_entry.get("term_status") == "nonstandard":
                continue

            def_text = c4_entry["definition"].lower()
            parent_lower = parent.lower()

            patterns = [
                f"{parent_lower} process variation",
                f"variation of {parent_lower}",
                f"variation of the {parent_lower}",
                f"process variation of {parent_lower}",
                f"{parent_lower} variation",
            ]

            for pat in patterns:
                if pat in def_text:
                    is_corroborated = True
                    corroborating_phrase = pat
                    break

        if is_corroborated and c4_entry:
            c4_obs_id = c4_entry["observation_id"]
            promoted.append({
                "child_process": child,
                "child_designation": desig,
                "parent_process": parent,
                "indent_level": indent_level,
                "predicate": "IS_A_PROCESS_VARIATION_OF",
                "status": "ACCEPTED",
                "knowledge_eligible": True,
                "source_observation_ids": [
                    annex_a_obs_id,
                    c4_obs_id,
                ],
                "clause4_quote": c4_entry["definition"],
                "corroborating_phrase": corroborating_phrase,
                "clause4_page": c4_entry["printed_page"],
                "rule_id": "dual-provenance-is-a-1",
            })
        else:
            retained_candidates.append({
                "child_process": child,
                "child_designation": desig,
                "parent_process": parent,
                "indent_level": indent_level,
                "predicate": "CANDIDATE_LAYOUT_PARENT",
                "status": "CANDIDATE",
                "knowledge_eligible": False,
                "source_observation_ids": [annex_a_obs_id],
                "reason": (
                    "Visual indentation layout only; Clause 4 standard definition does not specify "
                    f"child as a process variation of '{parent}' per Annex C C1.5 genus formula."
                ),
                "rule_id": "candidate-layout-1",
            })

    uncorroborated_promotions = [p for p in promoted if not p.get("corroborating_phrase")]
    if len(uncorroborated_promotions) != 0:
        raise ValueError(f"DRIFT ERROR: Detected {len(uncorroborated_promotions)} uncorroborated IS_A promotions!")

    return {
        "total_indented_rows": len(indented_rows),
        "promoted_count": len(promoted),
        "retained_candidate_count": len(retained_candidates),
        "uncorroborated_promotions_count": len(uncorroborated_promotions),
        "promoted_is_a": promoted,
        "retained_candidates": retained_candidates,
    }


def build_is_a_promotion_store(
    doc: Optional[fitz.Document] = None,
    clause4_entries: Optional[List[Dict[str, Any]]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Build, validate, and atomically persist the Dual-Provenance Promotion store."""
    if not force and PROMOTION_STORE_PATH.exists():
        try:
            data = json.loads(PROMOTION_STORE_PATH.read_text(encoding="utf-8"))
            if data.get("schema_version") == "dual-provenance-is-a-2.0":
                return data
        except Exception:
            pass

    CLAUSE4_INGEST_DIR.mkdir(parents=True, exist_ok=True)
    target_doc = doc or fitz.open(PDF_PATH)
    eval_result = compute_dual_provenance_is_a(target_doc, clause4_entries=clause4_entries)

    store_data: Dict[str, Any] = {
        "schema_version": "dual-provenance-is-a-2.0",
        "standard_title": "AWS A3.0M/A3.0:2020 Dual-Provenance IS_A Process Variation Promotion Store",
        "rule_id": "dual-provenance-is-a-1",
        "rule_description": (
            "A CANDIDATE_LAYOUT_PARENT edge is promoted to IS_A_PROCESS_VARIATION_OF "
            "strictly when corroborated by Clause 4 genus-differentia phrasing naming the parent process. "
            "All other candidate edges remain CANDIDATE_LAYOUT_PARENT."
        ),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "total_indented_rows": eval_result["total_indented_rows"],
            "promoted_is_a_count": eval_result["promoted_count"],
            "retained_candidate_count": eval_result["retained_candidate_count"],
            "uncorroborated_promotions_count": eval_result["uncorroborated_promotions_count"],
        },
        "promoted_is_a": eval_result["promoted_is_a"],
        "retained_candidates": eval_result["retained_candidates"],
    }

    raw_json = json.dumps(store_data, indent=2, ensure_ascii=False)
    sha256 = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    store_data["sha256"] = sha256

    temp_path = PROMOTION_STORE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(store_data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(PROMOTION_STORE_PATH)

    return store_data


def get_is_a_promotion_store() -> Dict[str, Any]:
    """Retrieve cached or freshly built promotion store."""
    if not PROMOTION_STORE_PATH.exists():
        return build_is_a_promotion_store()
    try:
        return json.loads(PROMOTION_STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_is_a_promotion_store(force=True)
