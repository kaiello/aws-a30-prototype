"""
src/evidence_annex_c_d.py: Source-Aware Ingestion and Cross-Verification for
AWS A3.0M/A3.0:2020 Annex C (Principles of Style and Committee Decisions) and
Annex D (Summary of Modifications to AWS A3.0:2020 from AWS A3.0:2010).

Standard: AWS A3.0M/A3.0:2020 (13th Edition)
Coordinates:
- Annex C: PDF indices 171..176 (printed pp. 159..164, Clauses C1..C2, Decisions C1.5.1..C1.5.8, C2.4.1)
- Annex D: PDF indices 177..182 (printed pp. 165..170, Tables D1..D6)

Epistemic Rules:
1. Annex C parses normative style rules and all 8 Definitions Subcommittee decisions
   with verbatim quotes, page anchors, and executive takeaways.
2. Annex D parses Tables D1..D6 directly from PDF indices 177..182.
3. Cross-verifies Tables D1..D6 against Clause 4 Glossary Store:
   - Table D1 (New Terms) vs. has_2020_underline
   - Table D2 (Modified Terms) vs. has_2020_margin_bar
   - Table D6 (Deleted Terms) checked for absence as active standard definitions in Clause 4.
4. Outputs persisted to storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json with SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz

from src.config import PDF_PATH, STORAGE_DIR

CLAUSE4_INGEST_DIR = STORAGE_DIR / "evidence_v2" / "clause4_ingest_001"
ANNEX_C_D_STORE_PATH = CLAUSE4_INGEST_DIR / "annex_c_d_store.json"


# ---------------------------------------------------------------------------
# Stage 1: Extraction of Annex C (Principles of Style, C1..C2, pp. 159..164)
# ---------------------------------------------------------------------------

def extract_annex_c_style_and_decisions(doc: fitz.Document) -> Dict[str, Any]:
    """Extract Annex C Principles of Style, Clauses C1..C2, and the 8 Subcommittee Decisions."""
    clause_headers = [
        ("C1", "Selection and Construction of Terminology"),
        ("C1.1", "Incorporated Terms"),
        ("C1.2", "Terms Not Normally Incorporated"),
        ("C1.3", "Method of Presentation"),
        ("C1.4", "Multiple Word Terms"),
        ("C1.5", "Definitions"),
        ("C1.5.1", "bonding"),
        ("C1.5.2", "diffusion welding"),
        ("C1.5.3", "GTAW and GMAW"),
        ("C1.5.4", "welder vs. welding machine"),
        ("C1.5.5", "workpiece"),
        ("C1.5.6", "nondestructive examination"),
        ("C1.5.7", "parallel joint"),
        ("C1.5.8", "deposit"),
        ("C1.6", "Obsolete or Seldom Used Terms"),
        ("C2", "Principles of Style"),
        ("C2.1", "Parts of Speech"),
        ("C2.2", "Cross-References"),
        ("C2.3", "Style of Definitions"),
        ("C2.4", "Terminology Structure"),
        ("C2.4.1", "Delimiters and Typography"),
    ]

    pages_text: Dict[int, Tuple[int, str]] = {}
    for pno in range(171, 177):
        printed_page = pno - 12
        text = doc[pno].get_text()
        pages_text[pno] = (printed_page, text)

    full_annex = "\n".join(f"\n[PAGE {pno} p.{pages_text[pno][0]}]\n" + pages_text[pno][1] for pno in range(171, 177))

    clauses: Dict[str, Any] = {}
    for i, (cid, ctitle) in enumerate(clause_headers):
        m = re.search(r'(?:^|\n)(' + re.escape(cid) + r'[\.\s\u2002]+[^\n]+)', full_annex)
        if m:
            start_pos = m.start(1)
            if i + 1 < len(clause_headers):
                next_cid = clause_headers[i + 1][0]
                m_next = re.search(r'(?:^|\n)(' + re.escape(next_cid) + r'[\.\s\u2002]+[^\n]+)', full_annex[start_pos + 10:])
                end_pos = start_pos + 10 + m_next.start(1) if m_next else len(full_annex)
            else:
                end_pos = len(full_annex)

            clause_content = full_annex[start_pos:end_pos].strip()
            p_match = re.findall(r'\[PAGE\s+(\d+)\s+p\.(\d+)\]', full_annex[:start_pos])
            start_page = int(p_match[-1][1]) if p_match else 159
            start_pdf = int(p_match[-1][0]) if p_match else 171

            clean_text = re.sub(r'\[PAGE\s+\d+\s+p\.\d+\]\n?', '', clause_content)
            clean_text = re.sub(r'AWS A3\.0M/A3\.0:2020\n?', '', clean_text)
            clean_text = re.sub(r'\n\d+\n', '\n', clean_text)
            clean_text = re.sub(r'Accessed by account:[^\n]+\n?', '', clean_text)
            clean_text = re.sub(r'IP address:[^\n]+\n?', '', clean_text)

            clauses[cid] = {
                "clause_id": cid,
                "title": ctitle,
                "printed_page": start_page,
                "pdf_index": start_pdf,
                "text": clean_text.strip(),
            }

    # Curate the 8 decisions with executive takeaway summaries explicitly derived from and quoting clause text
    decisions_summary = {
        "C1.5.1": {
            "topic": "bonding",
            "takeaway": (
                f"Per C1.5.1: 'The Definitions Subcommittee discourages the use of the term \"bonding\" for \"welding.\"' "
                f"The committee reserves bonding for joining processes where 'either an adhesive bond or a mechanical bond is predominant' "
                f"(adhesive bonding, brazing, soldering, thermal spraying). When 'an atomic bond between the atoms at that interface is predominant, "
                f"the resulting joint is called a weld, and the process that produced that joint is called welding.'"
            ),
            "clause": clauses.get("C1.5.1", {}),
        },
        "C1.5.2": {
            "topic": "diffusion welding",
            "takeaway": (
                f"Per C1.5.2: 'Diffusion welding is consistent with international custom' and British Standards Institution (BS499). "
                f"The committee explains that 'diffusion bonding' originated as an 'aircraft industry euphemism' to avoid 'prejudice' against "
                f"welded structures ('aversion to welding'), and concludes that 'diffusion welding, rather than \"diffusion bonding,\" "
                f"is now universally accepted as a part of standard welding terminology.'"
            ),
            "clause": clauses.get("C1.5.2", {}),
        },
        "C1.5.3": {
            "topic": "GTAW & GMAW vs TIG & MIG",
            "takeaway": (
                f"Per C1.5.3: 'The Definitions Subcommittee prefers the terms gas metal arc welding and gas tungsten arc welding', "
                f"rejecting TIG and MIG because 'application of non-inert, i.e., active, gases for arc shielding rendered the term TIG inaccurate' "
                f"(active gases including CO2, O2, Ar-H2), and 'arguments similar to those made in support of GTAW also apply to gas metal arc welding "
                f"(GMAW) versus metal inert gas welding (MIGW).'"
            ),
            "clause": clauses.get("C1.5.3", {}),
        },
        "C1.5.4": {
            "topic": "welder vs welding machine vs weldor",
            "takeaway": (
                f"Per C1.5.4: 'The use of the term welder to indicate the person who does the welding originated in the early days of welding' "
                f"and 'welding machine' indicates the equipment. The alternate spelling 'weldor is nonstandard' and rejected because "
                f"in spoken English pronunciation is phonetically identical."
            ),
            "clause": clauses.get("C1.5.4", {}),
        },
        "C1.5.5": {
            "topic": "workpiece",
            "takeaway": (
                f"Per C1.5.5: 'The use of the term workpiece to indicate the part to be welded, brazed, soldered...' was chosen because "
                f"'Webster\'s Third New International Dictionary specifically defines workpiece as \"a piece of work in process of manufacture\"', "
                f"whereas component, member, or part carry other non-manufacturing definitions."
            ),
            "clause": clauses.get("C1.5.5", {}),
        },
        "C1.5.6": {
            "topic": "nondestructive examination (NDE)",
            "takeaway": (
                f"Per C1.5.6: The committee established 'nondestructive examination (NDE)' as standard to mean 'The process of determining "
                f"acceptability of a material or a component in accordance with established criteria without impairing its future usefulness', "
                f"consulting ASME, ASNT, and ASTM."
            ),
            "clause": clauses.get("C1.5.6", {}),
        },
        "C1.5.7": {
            "topic": "parallel joint (replaces edge joint in 2020 edition)",
            "takeaway": (
                f"Per C1.5.7: In the 2020 edition, 'parallel joint has been introduced as a replacement for edge joint and is defined as \"A joint type formed by butting, "
                f"parallel surfaces of one or more workpieces with flush ends.\"' Historically, five basic joint types were recognized (butt, corner, "
                f"lap, parallel, and T-joints). Edge joint was replaced because it described weld location rather than member orientation."
            ),
            "clause": clauses.get("C1.5.7", {}),
        },
        "C1.5.8": {
            "topic": "deposit",
            "takeaway": (
                f"Per C1.5.8: 'The term deposit or any of its derivatives, is used only in connection with the terms filler metal or surfacing material. "
                f"Use with such terms as weld metal, weld bead, weld, etc., is nonstandard.'"
            ),
            "clause": clauses.get("C1.5.8", {}),
        },
    }

    return {
        "clauses": clauses,
        "subcommittee_decisions": decisions_summary,
        "principles_summary": {
            "standard_typography": "Boldface type for standard terms when defined or in cross-references.",
            "nonstandard_typography": "Lightface type for nonstandard terms; begins with 'A nonstandard term for...' or 'A nonstandard term when used for...'.",
            "application_mode_suffixes": "Appended per Table A4 (e.g. -AD, -AU, -MA, -ME, -RO, -SA).",
            "obsolete_terms_formula": "Alerted by incorporating 'This is an obsolete or seldom used process. See Table A5.'",
            "definition_style": "Complete in one succinct sentence, no abbreviations or units in definitions, parts of speech format (v., adj., n.).",
            "cross_reference_order": "Figures first, then tables, then alphabetical terms.",
        },
    }


# ---------------------------------------------------------------------------
# Stage 2: Extraction of Annex D (Modifications Tables D1..D6, pp. 165..170)
# ---------------------------------------------------------------------------

def extract_annex_d_modifications(doc: fitz.Document) -> Dict[str, Any]:
    """Extract Annex D modifications across Tables D1 through D6 directly from PDF text."""
    raw_tables: Dict[str, List[Dict[str, Any]]] = {f"Table D{i}": [] for i in range(1, 7)}
    current_table: Optional[str] = None

    table_titles = {
        "Table D1": "New Terms and Definitions Added in 2020 Edition",
        "Table D2": "Modified Terms and Definitions in 2020 Edition",
        "Table D3": "Terms/Definitions with Minor Editorial Revisions in 2020 Edition",
        "Table D4": "Terms Revised from Standard to Nonstandard in 2020 Edition",
        "Table D5": "Terms Revised from Nonstandard to Standard in 2020 Edition",
        "Table D6": "Deleted Terms in 2020 Edition",
    }

    known_headers = {
        "New Terms and Definitions",
        "Modified Terms/Definitions",
        "Terms/Definitions with Editorial Revisions",
        "Terms Revised from Standard to Nonstandard",
        "Terms Revised from Nonstandard to Standard",
        "Deleted Terms (Also see New Terms for revisions in delimiters)",
    }

    for pno in range(177, 183):
        printed_page = pno - 12
        text = doc[pno].get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for line in lines:
            if "AWS A3.0M/A3.0:2020" in line or "CLAUSE" in line or line == str(printed_page):
                continue
            if "Annex D (Informative)" in line or "Modifications to A3.0M" in line or "This annex is not" in line:
                continue
            if "Accessed by account:" in line or "IP address:" in line:
                continue
            if line in known_headers:
                continue

            m_tbl = re.match(r'^(Table D[1-6])(?:\s+\(Continued\))?', line)
            if m_tbl:
                current_table = m_tbl.group(1)
                continue

            if current_table:
                # Add row if not a header artifact
                if not line.startswith("Table D") and line != "Annex D":
                    raw_tables[current_table].append({
                        "entry": line,
                        "term": re.sub(r',.*$', '', line).strip(),
                        "full_line": line,
                        "page": printed_page,
                        "pdf_index": pno,
                    })

    tables: Dict[str, Any] = {}
    for tid, rows in raw_tables.items():
        tables[tid] = {
            "table_id": tid,
            "title": table_titles[tid],
            "row_count": len(rows),
            "rows": rows,
            "entries": [r["entry"] for r in rows],
        }

    return tables


# ---------------------------------------------------------------------------
# Stage 3: Cross-Verification of Annex D against Clause 4 Glossary Store
# ---------------------------------------------------------------------------

def cross_verify_annex_d_with_clause4(
    annex_d_tables: Dict[str, Any],
    glossary_store: Dict[str, Any]
) -> Dict[str, Any]:
    """Cross-verify Tables D1..D6 against Clause 4 Glossary Store revision metadata."""
    entries = glossary_store.get("entries", [])
    entry_by_term = {e["term"].lower(): e for e in entries}

    # Cross-check Table D1 (New Terms) vs. has_2020_underline
    d1_rows = annex_d_tables.get("Table D1", {}).get("rows", [])
    d1_matched = 0
    d1_with_underline = 0
    d1_details: List[Dict[str, Any]] = []

    for r in d1_rows:
        t_raw = r["entry"].lower()
        t_base = r["term"].lower()
        e = entry_by_term.get(t_raw) or entry_by_term.get(t_base)
        if not e:
            for k, cand in entry_by_term.items():
                if t_base in k or k in t_base:
                    e = cand
                    break
        has_ul = e.get("has_2020_underline", False) if e else False
        if e:
            d1_matched += 1
            if has_ul:
                d1_with_underline += 1
        d1_details.append({
            "table_d1_term": r["entry"],
            "matched_in_clause4": e is not None,
            "clause4_term": e["term"] if e else None,
            "has_2020_underline": has_ul,
        })

    # Cross-check Table D2 (Modified Terms) vs. has_2020_margin_bar
    d2_rows = annex_d_tables.get("Table D2", {}).get("rows", [])
    d2_matched = 0
    d2_with_margin_bar = 0
    d2_details: List[Dict[str, Any]] = []

    for r in d2_rows:
        t_raw = r["entry"].lower()
        t_base = r["term"].lower()
        e = entry_by_term.get(t_raw) or entry_by_term.get(t_base)
        if not e:
            for k, cand in entry_by_term.items():
                if t_base in k or k in t_base:
                    e = cand
                    break
        has_mb = e.get("has_2020_margin_bar", False) if e else False
        if e:
            d2_matched += 1
            if has_mb:
                d2_with_margin_bar += 1
        d2_details.append({
            "table_d2_term": r["entry"],
            "matched_in_clause4": e is not None,
            "clause4_term": e["term"] if e else None,
            "has_2020_margin_bar": has_mb,
        })

    # Cross-check Table D6 (Deleted Terms) checked for absence in standard definitions
    d6_rows = annex_d_tables.get("Table D6", {}).get("rows", [])
    d6_absent_count = 0
    d6_details: List[Dict[str, Any]] = []

    for r in d6_rows:
        t_raw = r["entry"].lower()
        t_base = r["term"].lower()
        e = entry_by_term.get(t_raw) or entry_by_term.get(t_base)
        # It should NOT exist as an active standard term
        is_active_standard = (e is not None) and (e.get("term_status") == "standard")
        if not is_active_standard:
            d6_absent_count += 1
        d6_details.append({
            "table_d6_deleted_term": r["entry"],
            "active_standard_in_clause4": is_active_standard,
            "status_in_clause4": e.get("term_status") if e else "ABSENT",
        })

    return {
        "table_d1_cross_check": {
            "total_d1_terms": len(d1_rows),
            "matched_in_clause4": d1_matched,
            "with_2020_underline": d1_with_underline,
            "underline_correlation_rate": round(d1_with_underline / max(d1_matched, 1), 3),
        },
        "table_d2_cross_check": {
            "total_d2_terms": len(d2_rows),
            "matched_in_clause4": d2_matched,
            "with_2020_margin_bar": d2_with_margin_bar,
            "margin_bar_correlation_rate": round(d2_with_margin_bar / max(d2_matched, 1), 3),
        },
        "table_d6_cross_check": {
            "total_d6_deleted_terms": len(d6_rows),
            "confirmed_absent_or_nonstandard": d6_absent_count,
            "absence_verification_rate": round(d6_absent_count / max(len(d6_rows), 1), 3),
        },
    }


# ---------------------------------------------------------------------------
# Stage 4: Canonical Store & Persistence
# ---------------------------------------------------------------------------

def build_annex_c_d_store(
    doc: Optional[fitz.Document] = None,
    glossary_store: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Build, cross-verify, and atomically persist Annex C & Annex D store to clause4_ingest_001/annex_c_d_store.json."""
    if not force and ANNEX_C_D_STORE_PATH.exists():
        try:
            data = json.loads(ANNEX_C_D_STORE_PATH.read_text(encoding="utf-8"))
            if data.get("schema_version") == "annex-c-d-2.0":
                return data
        except Exception:
            pass

    CLAUSE4_INGEST_DIR.mkdir(parents=True, exist_ok=True)
    target_pdf = doc or fitz.open(PDF_PATH)

    # Ingest Annex C and Annex D
    annex_c = extract_annex_c_style_and_decisions(target_pdf)
    annex_d = extract_annex_d_modifications(target_pdf)

    # Load glossary store for cross-verification
    if not glossary_store:
        from src.evidence_clause4_glossary import get_clause4_glossary_store
        glossary_store = get_clause4_glossary_store()

    cross_check = cross_verify_annex_d_with_clause4(annex_d, glossary_store)

    store_data: Dict[str, Any] = {
        "schema_version": "annex-c-d-2.0",
        "standard_title": "AWS A3.0M/A3.0:2020 Annex C & Annex D Store",
        "source_coordinates": {
            "annex_c": {"printed_pages": "159-164", "pdf_indices": "171-176"},
            "annex_d": {"printed_pages": "165-170", "pdf_indices": "177-182"},
        },
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "annex_c_clauses_count": len(annex_c["clauses"]),
            "annex_c_subcommittee_decisions_count": len(annex_c["subcommittee_decisions"]),
            "annex_d_tables_count": len(annex_d),
            "table_d1_rows": annex_d["Table D1"]["row_count"],
            "table_d2_rows": annex_d["Table D2"]["row_count"],
            "table_d3_rows": annex_d["Table D3"]["row_count"],
            "table_d4_rows": annex_d["Table D4"]["row_count"],
            "table_d5_rows": annex_d["Table D5"]["row_count"],
            "table_d6_rows": annex_d["Table D6"]["row_count"],
        },
        "cross_verification": cross_check,
        "annex_c": annex_c,
        "annex_d": annex_d,
    }

    raw_json = json.dumps(store_data, indent=2, ensure_ascii=False)
    sha256 = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    store_data["sha256"] = sha256

    temp_path = ANNEX_C_D_STORE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(store_data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(ANNEX_C_D_STORE_PATH)

    return store_data


def get_annex_c_d_store() -> Dict[str, Any]:
    """Retrieve cached or freshly built Annex C & Annex D store."""
    if not ANNEX_C_D_STORE_PATH.exists():
        return build_annex_c_d_store()
    try:
        return json.loads(ANNEX_C_D_STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_annex_c_d_store(force=True)


def get_subcommittee_decision(decision_id: str, store: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve an Annex C subcommittee decision by ID (e.g. C1.5.1..C1.5.8)."""
    st = store or get_annex_c_d_store()
    return st.get("annex_c", {}).get("subcommittee_decisions", {}).get(decision_id.strip().upper())


def get_annex_d_modifications(table_id: str, store: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve an Annex D table by ID (e.g. 'Table D1'..'Table D6')."""
    st = store or get_annex_c_d_store()
    tid = table_id.strip().title()
    if not tid.startswith("Table"):
        tid = f"Table {tid}"
    return st.get("annex_d", {}).get(tid)
