"""
src/evidence_clause4_glossary.py: Source-Aware Ingestion and Epistemic Retrieval for
AWS A3.0M/A3.0:2020 Clause 4 (Terms and Definitions).

Standard: AWS A3.0M/A3.0:2020 (13th Edition)
Coordinates: PDF indices 17..79 (printed pp. 5..67)

Epistemic Rules:
1. No hardcoded glossary dicts: native extraction directly from PDF using PyMuPDF.
2. Standard Terms: identified by boldface typography at entry headword (Arial-BoldMT / bold font flags).
   term_status: "standard".
3. Nonstandard Terms: identified by lightface typography at entry start whose definition matches
   "A nonstandard term for ..." or "A nonstandard term when applied to ...".
   term_status: "nonstandard". Preferred terms extracted and linked via NONSTANDARD_SYNONYM_OF.
4. Domain / Application Delimiters: extracted from italicized qualifiers (e.g. *plastics*, *resistance welding*,
   *submerged arc welding*, *brazing*, *soldering*, *pipe*, etc.) into domain_delimiters: list[str].
5. 2020 Revision Markers:
   - has_2020_underline: bool (horizontal underline strokes under headwords from page.get_drawings())
   - has_2020_margin_bar: bool (vertical change bars in page margins from page.get_drawings())
6. Cross-References & Letter Designations:
   - Letter designations e.g. (GMAW), (GTAW), (USW), (DFW), (CW), (EXW)
   - Figures, tables, see-also cross references
7. Hard verification: raises ValueError if len(entries) < 1400 or any of the 27 sentinels are missing.
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
GLOSSARY_STORE_PATH = CLAUSE4_INGEST_DIR / "glossary_store.json"

MANDATORY_SENTINELS = [
    "arc welding",
    "atomic hydrogen welding",
    "brazing",
    "cold welding",
    "coextrusion welding",
    "diffusion welding",
    "diffusion brazing",
    "electron beam welding",
    "explosion welding",
    "faying surface",
    "friction stir welding",
    "fusion welding",
    "gas metal arc welding",
    "hot pressure welding",
    "induction welding",
    "joint",
    "laser beam welding",
    "oxyacetylene welding",
    "plasma arc welding",
    "resistance spot welding",
    "shielded metal arc welding",
    "solid-state welding",
    "submerged arc welding",
    "thermal cutting",
    "thermal spraying",
    "ultrasonic welding",
    "weld",
]

PARTS_OF_SPEECH = {"n.", "v.", "adj.", "n", "v", "adj"}


def _extract_page_drawings(page: fitz.Page) -> Tuple[List[fitz.Rect], List[fitz.Rect]]:
    """Extract vertical margin bars and horizontal underlines from vector drawings."""
    drawings = page.get_drawings()
    margin_bars: List[fitz.Rect] = []
    underlines: List[fitz.Rect] = []

    for d in drawings:
        r = d["rect"]
        # Skip header (<45pt) and footer (>740pt)
        if r.y1 < 45 or r.y0 > 740:
            continue

        # Margin bar: vertical line in left (x < 65) or right (x > 545) margin
        if abs(r.x1 - r.x0) < 2.0 and abs(r.y1 - r.y0) > 4.0:
            if r.x0 < 65.0 or r.x0 > 545.0:
                margin_bars.append(r)

        # Underline: horizontal line under text
        elif abs(r.y1 - r.y0) < 2.0 and abs(r.x1 - r.x0) > 4.0:
            if 60.0 <= r.x0 <= 550.0:
                underlines.append(r)

    return margin_bars, underlines


def extract_clause4_glossary(doc: fitz.Document) -> List[Dict[str, Any]]:
    """Extract all glossary entries from Clause 4 using font styling, text blocks, and vector drawings."""
    raw_blocks_by_entry: List[Dict[str, Any]] = []
    current_entry: Optional[Dict[str, Any]] = None

    # Pre-extract vector drawings for all Clause 4 pages
    drawings_by_page: Dict[int, Tuple[List[fitz.Rect], List[fitz.Rect]]] = {}
    for pno in range(17, 80):
        drawings_by_page[pno] = _extract_page_drawings(doc[pno])

    for pno in range(17, 80):
        printed_page = pno - 12
        page = doc[pno]
        d = page.get_text("dict")

        for b in d.get("blocks", []):
            if "lines" not in b:
                continue
            bbox = b.get("bbox", [0, 0, 0, 0])
            # Filter header (<45pt) and footer (>745pt)
            if bbox[1] < 45 or bbox[3] > 745:
                continue
            # Skip "4. Glossary" title block on page 17
            if pno == 17 and bbox[1] < 170:
                continue

            first_line = b["lines"][0]
            first_span = first_line["spans"][0]
            font = first_span.get("font", "").lower()
            flags = first_span.get("flags", 0)

            # Build full block text
            block_text = ""
            for line in b["lines"]:
                for s in line["spans"]:
                    block_text += s.get("text", "")
                block_text += " "
            block_text = block_text.strip()
            if not block_text:
                continue

            # Standard entries begin with boldface typography (flags 16 or bold in font name)
            is_bold_start = "bold" in font or (flags & 16) or (flags & 4 and "bold" in font)
            # Nonstandard entries begin with lightface typography and contain nonstandard formula
            is_nonstandard_start = not is_bold_start and ("nonstandard term" in block_text[:120].lower())

            if is_bold_start or is_nonstandard_start:
                if current_entry:
                    raw_blocks_by_entry.append(current_entry)
                current_entry = {
                    "start_pdf_page": pno,
                    "start_printed_page": printed_page,
                    "is_standard": is_bold_start,
                    "blocks": [b],
                    "text": block_text,
                }
            else:
                if current_entry:
                    current_entry["blocks"].append(b)
                    current_entry["text"] += " " + block_text

    if current_entry:
        raw_blocks_by_entry.append(current_entry)

    # Process each raw entry into a structured glossary record
    entries: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    for idx, raw in enumerate(raw_blocks_by_entry):
        full_text = raw["text"]
        first_block = raw["blocks"][0]
        start_pno = raw["start_pdf_page"]
        start_printed = raw["start_printed_page"]
        mb_list, ul_list = drawings_by_page.get(start_pno, ([], []))

        # Check 2020 revision markers from drawings
        first_line_bbox = first_block["lines"][0]["bbox"]
        has_underline = any(
            (abs(ul.y0 - first_line_bbox[3]) <= 5.0 or (first_line_bbox[1] - 2 <= ul.y0 <= first_line_bbox[3] + 4))
            and (ul.x1 >= first_line_bbox[0] and ul.x0 <= first_line_bbox[2])
            for ul in ul_list
        )

        all_y0 = min(b["bbox"][1] for b in raw["blocks"])
        all_y1 = max(b["bbox"][3] for b in raw["blocks"])
        has_margin_bar = any(
            mb.y0 <= all_y1 + 4 and mb.y1 >= all_y0 - 4
            for mb in mb_list
        )

        if raw["is_standard"]:
            # Standard Term
            bold_spans: List[str] = []
            italic_spans: List[str] = []
            state = "bold"

            for line in first_block.get("lines", []):
                for s in line.get("spans", []):
                    f_name = s.get("font", "").lower()
                    t_val = s.get("text", "")
                    s_flags = s.get("flags", 0)
                    s_bold = "bold" in f_name or (s_flags & 16) or (s_flags & 4 and "bold" in f_name)
                    s_italic = "italic" in f_name or (s_flags & 2)

                    if state == "bold":
                        if s_bold:
                            bold_spans.append(t_val)
                        elif s_italic and not bold_spans:
                            bold_spans.append(t_val)
                        else:
                            state = "qualifier"
                            if s_italic:
                                italic_spans.append(t_val)
                    elif state == "qualifier":
                        if s_italic:
                            italic_spans.append(t_val)
                        elif t_val.strip() in {",", ".", ";", " "}:
                            pass
                        else:
                            state = "def"

            raw_heading = "".join(bold_spans).strip()
            raw_heading = re.sub(r'[,.\s]+$', '', raw_heading)
            qualifier_str = "".join(italic_spans).strip()
            qualifier_str = re.sub(r'[,.\s]+$', '', qualifier_str)

            # Separate parts of speech and domain delimiters
            part_of_speech: Optional[str] = None
            domain_delimiters: List[str] = []

            if qualifier_str:
                raw_quals = [q.strip() for q in re.split(r'[,;]+', qualifier_str) if q.strip()]
                for q in raw_quals:
                    if q.lower() in PARTS_OF_SPEECH or q.lower() in {"v", "n", "adj"}:
                        part_of_speech = q if q.endswith(".") else f"{q}."
                    else:
                        domain_delimiters.append(q)

            # Extract designation if in parens e.g. "gas metal arc welding (GMAW)"
            m_desig = re.search(r'\(([A-Z0-9\-\s/]+)\)$', raw_heading)
            if m_desig:
                designation = m_desig.group(1).strip()
                term_name = raw_heading[:m_desig.start()].strip()
            else:
                designation = None
                term_name = raw_heading

            # Clean definition text
            prefix_len = len(raw_heading)
            rest = full_text[prefix_len:].strip()
            if rest.startswith(","):
                rest = rest[1:].strip()
            if qualifier_str and rest.startswith(qualifier_str):
                rest = rest[len(qualifier_str):].strip()
            if rest.startswith("."):
                rest = rest[1:].strip()
            definition = re.sub(r'\s+', ' ', rest).strip()

            # Genus-differentia detection per Annex C C1.5
            genus = None
            is_variation = False
            m_var = re.search(r'^(?:An?|The)\s+([A-Za-z\s\-]+?)\s+process variation\b', definition, re.IGNORECASE)
            if m_var:
                genus = m_var.group(1).strip()
                is_variation = True
            else:
                m_var2 = re.search(r'^(?:A|The)\s+variation of\s+([A-Za-z\s\-]+?)(?:\s+in which|\s+producing|\s+performed|\.|$)', definition, re.IGNORECASE)
                if m_var2:
                    genus = m_var2.group(1).strip()
                    is_variation = True

            fig_refs = re.findall(r'Figure\s+([A-Z]\d+(?:\([A-Z0-9]+\))?)', full_text)
            table_refs = re.findall(r'Table\s+([A-Z]\d+)', full_text)
            see_also_refs = re.findall(r'See also\s+([A-Za-z0-9\s,\u2013\-]+?)(?:\.|$)', full_text)

            is_obsolete = "obsolete or seldom used process" in full_text.lower()
            slug = re.sub(r'[^a-z0-9]+', '_', term_name.lower()).strip('_')
            entry_id = f"term:{slug}_{idx:04d}"
            obs_id = f"obs:clause4:p{start_printed}:{slug}"

            entry = {
                "entry_id": entry_id,
                "observation_id": obs_id,
                "term": term_name,
                "raw_heading": raw_heading,
                "designation": designation,
                "term_status": "standard",
                "is_standard": True,
                "definition": definition,
                "part_of_speech": part_of_speech,
                "domain_delimiters": domain_delimiters,
                "has_2020_underline": has_underline,
                "has_2020_margin_bar": has_margin_bar,
                "preferred_terms": [],
                "is_process_variation": is_variation,
                "variation_genus": genus,
                "is_obsolete": is_obsolete,
                "printed_page": start_printed,
                "pdf_index": start_pno,
                "cross_references": {
                    "figures": sorted(list(set(fig_refs))),
                    "tables": sorted(list(set(table_refs))),
                    "see_also": [s.strip() for s in see_also_refs if s.strip()],
                },
                "full_text": full_text,
            }
            entries.append(entry)

        else:
            # Nonstandard Term
            m = re.match(r'^([^.]+?)\.\s*(A nonstandard term.*)$', full_text, re.IGNORECASE)
            if m:
                term = m.group(1).strip()
                qualifier = None
                def_text = m.group(2).strip()
            else:
                m2 = re.match(r'^([^,]+?),\s*([a-z.]+?)\.\s*(A nonstandard term.*)$', full_text, re.IGNORECASE)
                if m2:
                    term = m2.group(1).strip()
                    qualifier = m2.group(2).strip()
                    def_text = m2.group(3).strip()
                else:
                    parts = full_text.split(".", 1)
                    term = parts[0].strip()
                    qualifier = None
                    def_text = parts[1].strip() if len(parts) > 1 else full_text

            # Extract preferred standard target terms from boldface spans
            target_terms: List[str] = []
            for b in raw["blocks"]:
                for line in b.get("lines", []):
                    for s in line.get("spans", []):
                        f_name = s.get("font", "").lower()
                        s_flags = s.get("flags", 0)
                        if "bold" in f_name or (s_flags & 16):
                            cand = s.get("text", "").strip()
                            if cand and cand not in {".", ",", ";", "and", "or"} and cand not in target_terms:
                                target_terms.append(cand)

            # Fallback if no bold spans were present in nonstandard entry text
            if not target_terms:
                m_nonstd = re.search(r'A nonstandard term (?:for|when applied to|when used for)\s+([^.]+)', def_text, re.IGNORECASE)
                if m_nonstd:
                    raw_target = m_nonstd.group(1).strip()
                    raw_target = re.sub(r'^(?:an?|the)\s+', '', raw_target, flags=re.IGNORECASE)
                    target_terms = [raw_target]

            m_desig = re.search(r'\(([A-Z0-9\-\s/]+)\)$', term)
            if m_desig:
                designation = m_desig.group(1).strip()
                term_name = term[:m_desig.start()].strip()
            else:
                designation = None
                term_name = term

            # Separate parts of speech and domain delimiters
            part_of_speech = None
            domain_delimiters = []
            if qualifier:
                if qualifier.lower() in PARTS_OF_SPEECH or qualifier.lower() in {"v", "n", "adj"}:
                    part_of_speech = qualifier if qualifier.endswith(".") else f"{qualifier}."
                else:
                    domain_delimiters.append(qualifier)

            fig_refs = re.findall(r'Figure\s+([A-Z]\d+(?:\([A-Z0-9]+\))?)', full_text)
            table_refs = re.findall(r'Table\s+([A-Z]\d+)', full_text)

            slug = re.sub(r'[^a-z0-9]+', '_', term_name.lower()).strip('_')
            entry_id = f"term:{slug}_{idx:04d}"
            obs_id = f"obs:clause4:p{start_printed}:{slug}"

            entry = {
                "entry_id": entry_id,
                "observation_id": obs_id,
                "term": term_name,
                "raw_heading": term,
                "designation": designation,
                "term_status": "nonstandard",
                "is_standard": False,
                "definition": re.sub(r'\s+', ' ', def_text).strip(),
                "part_of_speech": part_of_speech,
                "domain_delimiters": domain_delimiters,
                "has_2020_underline": has_underline,
                "has_2020_margin_bar": has_margin_bar,
                "preferred_terms": target_terms,
                "target_standard_term": " and ".join(target_terms) if target_terms else None,
                "is_process_variation": False,
                "variation_genus": None,
                "is_obsolete": False,
                "printed_page": start_printed,
                "pdf_index": start_pno,
                "cross_references": {
                    "figures": sorted(list(set(fig_refs))),
                    "tables": sorted(list(set(table_refs))),
                    "see_also": [],
                },
                "full_text": full_text,
            }
            entries.append(entry)

            # Record nonstandard synonym relationship edge
            for pref in target_terms:
                relationships.append({
                    "relationship_id": f"rel:nonstd:{slug}->{re.sub(r'[^a-z0-9]+', '_', pref.lower())}",
                    "source_term": term_name,
                    "target_term": pref,
                    "predicate": "NONSTANDARD_SYNONYM_OF",
                    "observation_id": obs_id,
                    "rule_id": "annex-c1.2-nonstandard",
                    "printed_page": start_printed,
                })

    # Strict Validation Checks
    if len(entries) < 1400:
        raise ValueError(f"DRIFT ERROR: Expected >= 1400 entries in Clause 4, got {len(entries)}")

    terms_lower = {e["term"].lower(): e for e in entries}
    missing_sentinels = [s for s in MANDATORY_SENTINELS if s.lower() not in terms_lower]
    if missing_sentinels:
        raise ValueError(f"DRIFT ERROR: Missing mandatory sentinels in Clause 4: {missing_sentinels}")

    return entries


def build_clause4_glossary_store(doc: Optional[fitz.Document] = None, force: bool = False) -> Dict[str, Any]:
    """Build, validate, and atomically persist the Clause 4 glossary store to clause4_ingest_001/glossary_store.json."""
    if not force and GLOSSARY_STORE_PATH.exists():
        try:
            data = json.loads(GLOSSARY_STORE_PATH.read_text(encoding="utf-8"))
            if data.get("schema_version") == "clause4-glossary-2.0":
                return data
        except Exception:
            pass

    CLAUSE4_INGEST_DIR.mkdir(parents=True, exist_ok=True)
    target_pdf = doc or fitz.open(PDF_PATH)
    entries = extract_clause4_glossary(target_pdf)

    std_count = sum(1 for e in entries if e["term_status"] == "standard")
    nonstd_count = sum(1 for e in entries if e["term_status"] == "nonstandard")
    underlined_count = sum(1 for e in entries if e["has_2020_underline"])
    margin_bar_count = sum(1 for e in entries if e["has_2020_margin_bar"])
    variations_count = sum(1 for e in entries if e.get("is_process_variation"))

    store_data: Dict[str, Any] = {
        "schema_version": "clause4-glossary-2.0",
        "standard_title": "AWS A3.0M/A3.0:2020 Clause 4 Glossary (Terms and Definitions)",
        "source_coordinates": {
            "clause": "Clause 4",
            "printed_pages": "5-67",
            "pdf_indices": "17-79",
        },
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "total_glossary_entries": len(entries),
            "standard_terms_count": std_count,
            "nonstandard_terms_count": nonstd_count,
            "has_2020_underline_count": underlined_count,
            "has_2020_margin_bar_count": margin_bar_count,
            "process_variations_count": variations_count,
            "sentinels_verified_count": len(MANDATORY_SENTINELS),
            "sentinels_total": len(MANDATORY_SENTINELS),
        },
        "sentinels_verified": MANDATORY_SENTINELS,
        "entries": entries,
    }

    # Atomically write store
    raw_json = json.dumps(store_data, indent=2, ensure_ascii=False)
    sha256 = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    store_data["sha256"] = sha256

    temp_path = GLOSSARY_STORE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(store_data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(GLOSSARY_STORE_PATH)

    return store_data


def get_clause4_glossary_store() -> Dict[str, Any]:
    """Retrieve the cached or freshly built Clause 4 glossary store."""
    if not GLOSSARY_STORE_PATH.exists():
        return build_clause4_glossary_store()
    try:
        return json.loads(GLOSSARY_STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_clause4_glossary_store(force=True)


def lookup_glossary_term(query: str, store: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Look up a glossary term by name or designation, supporting domain qualifiers like '3F, pipe'."""
    st = store or get_clause4_glossary_store()
    q_norm = query.strip().lower()
    entries = st.get("entries", [])

    # Qualified term match (e.g. "3F, pipe")
    if "," in query:
        q_term, q_delim = [part.strip().lower() for part in query.split(",", 1)]
        for e in entries:
            if e["term"].lower() == q_term:
                delims = [d.lower() for d in e.get("domain_delimiters", [])]
                if any(q_delim in d or d in q_delim for d in delims):
                    return e

    # Exact term match
    for e in entries:
        if e["term"].lower() == q_norm:
            return e

    # Exact designation match
    q_upper = query.strip().upper()
    for e in entries:
        if e.get("designation") and e["designation"].upper() == q_upper:
            return e

    # Raw heading match
    for e in entries:
        if e.get("raw_heading", "").lower() == q_norm:
            return e

    # Partial match
    for e in entries:
        if q_norm in e["term"].lower():
            return e

    return None


def get_nonstandard_redirect(query: str, store: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Check if query matches a nonstandard term and return preferred standard terms."""
    st = store or get_clause4_glossary_store()
    entry = lookup_glossary_term(query, st)
    if entry and entry.get("term_status") == "nonstandard":
        return {
            "query": query,
            "nonstandard_term": entry["term"],
            "preferred_terms": entry.get("preferred_terms", []),
            "target_standard_term": entry.get("target_standard_term"),
            "definition": entry["definition"],
            "printed_page": entry["printed_page"],
            "observation_id": entry["observation_id"],
        }
    return None
