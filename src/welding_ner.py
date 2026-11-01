"""welding_ner.py - Deterministic Named Entity Recognizer & Compound Designation Parser.

AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions.
Compiled 100% offline from the locked _001 canonical stores.
Zero external ML dependencies; zero network calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class WeldingEntitySpan:
    """A deterministic, character-offset typed welding entity span."""

    surface_text: str
    start_char: int
    end_char: int
    entity_type: str
    canonical_term: str
    canonical_id: str
    source_authority: str
    target_division: str
    sub_components: Tuple[Dict[str, Any], ...] = ()
    ambiguity_candidates: Tuple[Dict[str, Any], ...] = ()
    is_valid: bool = True
    abstention_reason: Optional[str] = None
    secondary_entity_types: Tuple[str, ...] = ()
    linked_clause4_terms: Tuple[str, ...] = ()
    linked_figures: Tuple[str, ...] = ()
    linked_tables: Tuple[str, ...] = ()
    ambiguous_senses: Tuple[str, ...] = ()


@dataclass
class WeldingNERReceipt:
    """Receipt summarizing entity recognition over an input query."""

    raw_query: str
    normalized_query: str
    spans: List[WeldingEntitySpan]
    entity_counts_by_type: Dict[str, int]
    has_ambiguities: bool
    target_divisions: List[str]
    inferred_targets: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "spans": [
                {
                    "surface_text": s.surface_text,
                    "start_char": s.start_char,
                    "end_char": s.end_char,
                    "entity_type": s.entity_type,
                    "canonical_term": s.canonical_term,
                    "canonical_id": s.canonical_id,
                    "source_authority": s.source_authority,
                    "target_division": s.target_division,
                    "sub_components": list(s.sub_components),
                    "ambiguity_candidates": list(s.ambiguity_candidates),
                    "is_valid": s.is_valid,
                    "abstention_reason": s.abstention_reason,
                    "secondary_entity_types": list(s.secondary_entity_types),
                    "linked_clause4_terms": list(s.linked_clause4_terms),
                    "linked_figures": list(s.linked_figures),
                    "linked_tables": list(s.linked_tables),
                    "ambiguous_senses": list(s.ambiguous_senses),
                }
                for s in self.spans
            ],
            "entity_counts_by_type": self.entity_counts_by_type,
            "has_ambiguities": self.has_ambiguities,
            "target_divisions": self.target_divisions,
            "inferred_targets": self.inferred_targets,
        }


class WeldingNER:
    """Deterministic Welding Domain NER and Compound Designation Parser."""

    VALID_MODE_SUFFIXES: Dict[str, Dict[str, str]] = {
        "-AD": {"mode": "Adaptive control", "clean": "AD"},
        "-AU": {"mode": "Automatic", "clean": "AU"},
        "-MA": {"mode": "Manual", "clean": "MA"},
        "-ME": {"mode": "Mechanized", "clean": "ME"},
        "-RO": {"mode": "Robotic", "clean": "RO"},
        "-SA": {"mode": "Semiautomatic", "clean": "SA"},
    }

    OUT_OF_RANGE_LOCATORS: Dict[str, Dict[str, str]] = {
        "figure a7": {"division": "annex_a_charts", "reason": "AWS A3.0M/A3.0:2020 Annex A contains only Figures A1 through A6"},
        "figure b55": {"division": "annex_b", "reason": "AWS A3.0M/A3.0:2020 Annex B contains only Figures B1 through B54"},
        "figure b56": {"division": "annex_b", "reason": "AWS A3.0M/A3.0:2020 Annex B contains only Figures B1 through B54"},
        "table a6": {"division": "annex_a_tables", "reason": "AWS A3.0M/A3.0:2020 Annex A contains only Tables A1 through A5"},
        "clause 5": {"division": "clause", "reason": "AWS A3.0M/A3.0:2020 contains Clauses 1 through 4"},
    }

    def __init__(self, stores: Optional[Dict[str, Any]] = None, root: Optional[Path] = None):
        self.root = Path(root or ROOT).resolve()
        self.stores = stores or {}
        self._initialized = False

        # Lexicons
        self.process_codes: Dict[str, Dict[str, Any]] = {}
        self.process_terms: Dict[str, Dict[str, Any]] = {}
        self.nonstandard_terms: Dict[str, Dict[str, Any]] = {}
        self.glossary_terms: Dict[str, Dict[str, Any]] = {}
        self.weld_positions: Dict[str, Dict[str, Any]] = {}
        self.domain_qualifiers: Dict[str, Dict[str, Any]] = {}
        self.diagram_callouts: Dict[str, Dict[str, Any]] = {}
        self.waveform_intervals: Dict[str, Dict[str, Any]] = {}
        self.standard_locators: Dict[str, Dict[str, Any]] = {}

        # Lookups
        self.all_spans_trie: Dict[str, List[Dict[str, Any]]] = {}
        self._key_words: Dict[str, Tuple[str, ...]] = {}
        self.indexed_annex_b_node_count: int = 0
        self.indexed_annex_a_circle_count: int = 0
        self.indexed_clause4_backlink_count: int = 0

    def ensure_initialized(self, stores: Optional[Dict[str, Any]] = None) -> None:
        """Hydrate knowledge stores if not already initialized."""
        if self._initialized and not stores:
            return
        if stores:
            self.stores = stores
        elif not self.stores:
            from src.evidence_phase4_bakeoff import get_whole_standard_stores
            self.stores = get_whole_standard_stores()

        self._build_ner_lexicons()
        self._initialized = True

    def _build_ner_lexicons(self) -> None:
        """Extract typed entities directly from locked stores."""
        glossary = self.stores.get("glossary", {})
        tables = self.stores.get("tables", {})
        annex_c_d = self.stores.get("annex_c_d", {})
        is_a_store = self.stores.get("is_a", {})
        annex_a_graphs = self.stores.get("annex_a_graphs", {})

        # 1. Standard Locators (Figures, Tables, Clauses, Annexes)
        for i in range(1, 7):
            fid = f"Figure A{i}"
            self.standard_locators[fid.lower()] = {
                "canonical_term": fid,
                "canonical_id": f"figure:{fid.lower().replace(' ', '_')}",
                "source_authority": "Annex A",
                "target_division": "annex_a_charts",
                "entity_type": "STANDARD_LOCATOR",
            }
        for i in range(1, 55):
            fid = f"Figure B{i}"
            self.standard_locators[fid.lower()] = {
                "canonical_term": fid,
                "canonical_id": f"figure:{fid.lower().replace(' ', '_')}",
                "source_authority": "Annex B",
                "target_division": "annex_b_spatial" if i <= 43 or (i in [46, 47, 48, 52]) else "annex_b_waveform",
                "entity_type": "STANDARD_LOCATOR",
            }
            # Also subpanel letters e.g. Figure B16A, B16B, B16C, B25(A), etc.
            if i == 16:
                for sub in ["A", "B", "C"]:
                    sid = f"Figure B16{sub}"
                    self.standard_locators[sid.lower()] = {
                        "canonical_term": sid,
                        "canonical_id": f"figure:{sid.lower().replace(' ', '_')}",
                        "source_authority": "Annex B",
                        "target_division": "annex_b_spatial",
                        "entity_type": "STANDARD_LOCATOR",
                    }
        for i in range(1, 6):
            tid = f"Table A{i}"
            self.standard_locators[tid.lower()] = {
                "canonical_term": tid,
                "canonical_id": f"table:{tid.lower().replace(' ', '_')}",
                "source_authority": "Annex A",
                "target_division": "annex_a_tables",
                "entity_type": "STANDARD_LOCATOR",
            }
        for cid in ["Clause 4", "Clause 1", "Clause 2", "Clause 3", "Annex C", "Annex D", "Annex E"]:
            self.standard_locators[cid.lower()] = {
                "canonical_term": cid,
                "canonical_id": f"clause:{cid.lower().replace(' ', '_')}",
                "source_authority": cid,
                "target_division": "clause4_glossary" if "Clause 4" in cid else "annex_c_d" if "Annex" in cid else "clause",
                "entity_type": "STANDARD_LOCATOR",
            }

        # 2. Table A1 & Table A2 Process Codes & Process Terms
        table_a1 = tables.get("table_a1", [])
        for row in table_a1:
            proc = row.get("process", "").strip()
            desig = row.get("designation")
            page = row.get("page", 69)
            if proc:
                p_lower = proc.lower()
                self.process_terms[p_lower] = {
                    "canonical_term": proc,
                    "canonical_id": f"table_a1:proc:{p_lower.replace(' ', '_')}",
                    "source_authority": f"Table A1 (p. {page})",
                    "target_division": "annex_a_tables",
                    "entity_type": "PROCESS_TERM",
                }
            if desig:
                d_upper = desig.upper().strip()
                # Check for known AB collision
                if d_upper == "AB":
                    self.process_codes[d_upper] = {
                        "canonical_term": proc,
                        "canonical_id": f"table_a1:code:{d_upper}",
                        "source_authority": f"Table A1 (p. {page})",
                        "target_division": "annex_a_tables",
                        "entity_type": "PROCESS_CODE",
                        "ambiguity_candidates": (
                            {
                                "canonical_term": "adhesive bonding",
                                "source_authority": f"Table A1 (p. {page}) / Clause 4 (p. 8)",
                                "target_division": "annex_a_tables",
                                "context_hint": "adhesive bonding",
                            },
                            {
                                "canonical_term": "arc brazing",
                                "source_authority": "Figure A6 (p. 79) Legend",
                                "target_division": "annex_a_charts",
                                "context_hint": "brazing / arc",
                            },
                        ),
                    }
                else:
                    self.process_codes[d_upper] = {
                        "canonical_term": proc,
                        "canonical_id": f"table_a1:code:{d_upper}",
                        "source_authority": f"Table A1 (p. {page})",
                        "target_division": "annex_a_tables",
                        "entity_type": "PROCESS_CODE",
                    }

        # Table A5 Obsolete Processes
        table_a5 = tables.get("table_a5", [])
        for row in table_a5:
            proc = row.get("process", "").strip()
            desig = row.get("designation")
            if desig:
                d_upper = desig.upper().strip()
                self.process_codes[d_upper] = {
                    "canonical_term": proc,
                    "canonical_id": f"table_a5:code:{d_upper}",
                    "source_authority": "Table A5 (p. 74)",
                    "target_division": "annex_a_tables",
                    "entity_type": "PROCESS_CODE",
                    "is_obsolete": True,
                }
            if proc:
                p_lower = proc.lower()
                self.nonstandard_terms[p_lower] = {
                    "canonical_term": proc,
                    "canonical_id": f"table_a5:proc:{p_lower.replace(' ', '_')}",
                    "source_authority": "Table A5 (p. 74)",
                    "target_division": "annex_a_tables",
                    "entity_type": "NONSTANDARD_OR_HISTORICAL",
                }

        # Promoted IS-A variants (e.g. GTAW-P, GMAW-S, FCAW-G, FCAW-S)
        promoted = is_a_store.get("promoted_is_a", [])
        for row in promoted:
            cdesig = row.get("child_designation")
            cproc = row.get("child_process")
            if cdesig and cproc:
                c_upper = cdesig.upper().strip()
                self.process_codes[c_upper] = {
                    "canonical_term": cproc,
                    "canonical_id": f"is_a:code:{c_upper}",
                    "source_authority": "Table A1 / IS_A Promotions",
                    "target_division": "annex_a_tables",
                    "entity_type": "PROCESS_CODE",
                }
                self.process_terms[cproc.lower()] = {
                    "canonical_term": cproc,
                    "canonical_id": f"is_a:proc:{cproc.lower().replace(' ', '_')}",
                    "source_authority": "Table A1 / IS_A Promotions",
                    "target_division": "annex_a_tables",
                    "entity_type": "PROCESS_TERM",
                }

        # Figure A2-A6 process circles (96 circles across A4-A6; 130 across A2-A6)
        self.indexed_annex_a_circle_count = 0
        annex_a_graph_map: Dict[str, Dict[str, Any]] = dict(annex_a_graphs)
        a2_graph_path = self.root / "storage/evidence_v2/a2_ingest_001/final_projection/graph.json"
        if "Figure A2" not in annex_a_graph_map and a2_graph_path.exists():
            import json as _json
            annex_a_graph_map["Figure A2"] = _json.loads(a2_graph_path.read_text(encoding="utf-8"))

        annex_a_pages = {"Figure A2": 76, "Figure A3": 77, "Figure A4": 78, "Figure A5": 79, "Figure A6": 79}
        for fig_a_id, fig_a_graph in sorted(annex_a_graph_map.items()):
            p_a = annex_a_pages.get(fig_a_id, 78)
            for node in fig_a_graph.get("nodes", []):
                if node.get("kind") == "process":
                    self.indexed_annex_a_circle_count += 1
                code = node.get("code")
                label = (node.get("label") or node.get("name") or "").strip()
                if code and label:
                    if code == "AB" and "arc brazing" in label.lower():
                        # already tracked as ambiguity candidate above
                        continue
                    if code not in self.process_codes:
                        self.process_codes[code] = {
                            "canonical_term": label,
                            "canonical_id": f"{fig_a_id.lower().replace(' ', '_')}:code:{code}",
                            "source_authority": f"{fig_a_id} (p. {p_a})",
                            "target_division": "annex_a_charts",
                            "entity_type": "PROCESS_CODE",
                        }
                    lbl_clean = re.sub(r"^[A-Z0-9\-]+:\s*", "", label).strip()
                    if lbl_clean and lbl_clean.lower() not in self.process_terms and len(lbl_clean) > 3:
                        self.process_terms[lbl_clean.lower()] = {
                            "canonical_term": lbl_clean,
                            "canonical_id": f"{fig_a_id.lower().replace(' ', '_')}:proc:{lbl_clean.lower().replace(' ', '_')}",
                            "source_authority": f"{fig_a_id} (p. {p_a})",
                            "target_division": "annex_a_charts",
                            "entity_type": "PROCESS_TERM",
                        }

        # 3. Mode Suffixes (Table A4)
        for suf, info in self.VALID_MODE_SUFFIXES.items():
            self.process_codes[suf] = {
                "canonical_term": info["mode"],
                "canonical_id": f"table_a4:suffix:{suf}",
                "source_authority": "Table A4 (p. 74)",
                "target_division": "annex_a_tables",
                "entity_type": "MODE_SUFFIX",
            }

        # 4. Annex C / Annex D Nonstandard & Historical Terms (Table D4 nonstandard & Table D6 deleted)
        annex_d = annex_c_d.get("annex_d", {})
        for tbl_key in ["Table D4", "Table D6"]:
            t_obj = annex_d.get(tbl_key, {})
            p_default = t_obj.get("page", 165)
            for row in t_obj.get("rows", []):
                t_str = row.get("term", "").strip() or row.get("entry", "").strip()
                if not t_str:
                    continue
                t_lower = t_str.lower()
                self.nonstandard_terms[t_lower] = {
                    "canonical_term": t_str,
                    "canonical_id": f"annex_d:{tbl_key.lower().replace(' ', '_')}:{t_lower.replace(' ', '_')}",
                    "source_authority": f"{tbl_key} (p. {row.get('page', p_default)})",
                    "target_division": "annex_c_d",
                    "entity_type": "NONSTANDARD_OR_HISTORICAL",
                }

        # Common colloquial welding slang
        slang_map = {
            "stick electrode": ("covered electrode", "Clause 4 (p. 57) / Annex C"),
            "stick welding": ("shielded metal arc welding", "Clause 4 (p. 57) / Table A1"),
            "stick electrode welding": ("shielded metal arc welding", "Clause 4 (p. 57) / Table A1"),
            "heliarc": ("gas tungsten arc welding", "Clause 4 (p. 32) / Annex C"),
            "heliarc welding": ("gas tungsten arc welding", "Clause 4 (p. 32) / Annex C"),
            "tig": ("gas tungsten arc welding", "Clause 4 (p. 59) / Table A1"),
            "tig welding": ("gas tungsten arc welding", "Clause 4 (p. 59) / Table A1"),
            "mig": ("gas metal arc welding", "Clause 4 (p. 39) / Table A1"),
            "mig welding": ("gas metal arc welding", "Clause 4 (p. 39) / Table A1"),
            "button weld": ("button", "Clause 4 (p. 11) / Annex C"),
            "gas pocket": ("porosity", "Clause 4 (p. 29) / Annex C"),
        }
        for s_term, (canon, auth) in slang_map.items():
            self.nonstandard_terms[s_term] = {
                "canonical_term": canon,
                "canonical_id": f"slang:{s_term.replace(' ', '_')}",
                "source_authority": auth,
                "target_division": "clause4_glossary",
                "entity_type": "NONSTANDARD_OR_HISTORICAL",
            }

        # 5. Clause 4 Glossary Terms (with Multi-POS Ambiguity Candidates & Morphological Inflections)
        self.indexed_clause4_backlink_count = 0
        entries = glossary.get("entries", [])
        std_entries_by_term: Dict[str, List[Dict[str, Any]]] = {}
        for e in entries:
            term = e.get("term", "").strip()
            if not term:
                continue
            term_lower = term.lower()
            status = e.get("term_status", "standard")
            is_std = e.get("is_standard", True)
            page = e.get("printed_page", 17)

            figs = e.get("cross_references", {}).get("figures", [])
            for f_ref in figs:
                if re.search(r"B[0-9]{1,2}[A-C]?", str(f_ref)):
                    self.indexed_clause4_backlink_count += 1

            if status == "nonstandard" or not is_std:
                target = e.get("target_standard_term") or (e.get("preferred_terms", [None])[0] if e.get("preferred_terms") else term)
                self.nonstandard_terms[term_lower] = {
                    "canonical_term": target,
                    "canonical_id": f"clause4:nonstandard:{term_lower.replace(' ', '_')}",
                    "source_authority": f"Clause 4 (p. {page})",
                    "target_division": "clause4_glossary",
                    "entity_type": "NONSTANDARD_OR_HISTORICAL",
                }
            else:
                std_entries_by_term.setdefault(term_lower, []).append(e)

        for term_lower, matching_entries in std_entries_by_term.items():
            primary = matching_entries[0]
            term = primary.get("term", "").strip()
            page = primary.get("printed_page", 17)
            cross_figs: List[str] = []
            for me in matching_entries:
                for cf in me.get("cross_references", {}).get("figures", []):
                    if cf not in cross_figs:
                        cross_figs.append(cf)

            ambig_cands: Tuple[Dict[str, Any], ...] = ()
            if len(matching_entries) > 1:
                ambig_cands = tuple(
                    {
                        "canonical_term": me.get("term", term),
                        "part_of_speech": me.get("part_of_speech"),
                        "domain_qualifier": me.get("domain_delimiter") or me.get("qualifier"),
                        "source_authority": f"Clause 4 (p. {me.get('printed_page', page)})",
                        "target_division": "clause4_glossary",
                    }
                    for me in matching_entries
                )

            self.glossary_terms[term_lower] = {
                "canonical_term": term,
                "canonical_id": f"clause4:term:{term_lower.replace(' ', '_')}",
                "source_authority": f"Clause 4 (p. {page})",
                "target_division": "clause4_glossary",
                "entity_type": "GLOSSARY_TERM",
                "cross_figures": cross_figs,
                "ambiguity_candidates": ambig_cands,
            }

        # Add morphological inflections (plurals, hyphenation variants, gerunds) to glossary_terms
        morph_stopwords = {
            "is", "in", "as", "at", "by", "to", "or", "an", "it", "on", "of", "for", "the",
            "and", "be", "do", "we", "he", "so", "no", "if", "my", "up", "are", "was",
            "were", "has", "had", "how", "what", "which", "who", "whom", "this", "that",
            "means", "terms", "parts", "sides", "types", "lines", "areas", "rates", "times",
        }
        base_headwords = list(self.glossary_terms.items())
        for base_lower, g_meta in base_headwords:
            if len(base_lower) <= 2 or base_lower in morph_stopwords:
                continue
            variants: List[str] = []
            if base_lower.endswith("y") and not base_lower.endswith(("ay", "ey", "oy", "uy")):
                variants.append(base_lower[:-1] + "ies")
            elif base_lower.endswith(("s", "sh", "ch", "x", "z")):
                variants.append(base_lower + "es")
            else:
                variants.append(base_lower + "s")
            if "-" in base_lower:
                variants.append(base_lower.replace("-", " "))
            for var in variants:
                if (
                    var not in self.glossary_terms
                    and var not in self.nonstandard_terms
                    and var not in self.process_terms
                    and var not in morph_stopwords
                ):
                    self.glossary_terms[var] = dict(g_meta)

        domain_inflections = {
            "kerfs": "kerf",
            "undercutting": "undercut",
            "keyholing": "keyhole welding",
            "coalescences": "coalescence",
            "porosities": "porosity",
            "discontinuities": "discontinuity",
            "throat of a fillet weld": "fillet weld throat",
        }
        for infl, base_t in domain_inflections.items():
            if base_t in self.glossary_terms and infl not in self.glossary_terms:
                self.glossary_terms[infl] = dict(self.glossary_terms[base_t])

        # 6. Weld Position Entities & Domain Qualifiers
        position_codes = {
            "1g": ("1G", "flat groove/surfacing weld position"),
            "2g": ("2G", "horizontal groove/surfacing weld position"),
            "3g": ("3G", "vertical groove weld position"),
            "4g": ("4G", "overhead groove weld position"),
            "5g": ("5G", "horizontal fixed pipe groove weld position"),
            "6g": ("6G", "inclined fixed pipe groove weld position"),
            "6gr": ("6GR", "inclined fixed pipe groove weld position with restriction ring"),
            "1f": ("1F", "flat fillet weld position"),
            "2f": ("2F", "horizontal fillet weld position"),
            "2fr": ("2FR", "horizontal rotated pipe fillet weld position"),
            "3f": ("3F", "vertical fillet weld position"),
            "4f": ("4F", "overhead fillet weld position"),
        }
        for code, (canon_code, desc) in position_codes.items():
            self.weld_positions[code] = {
                "canonical_term": f"{canon_code} ({desc})",
                "canonical_id": f"weld_position:{code}",
                "source_authority": "Clause 4 / Figures B16-B20",
                "target_division": "clause4_glossary",
                "entity_type": "WELD_POSITION",
                "ambiguity_candidates": (
                    {"figure": "Figure B16A", "qualifier": "plate groove", "authority": "Figure B16A (p. 106)"},
                    {"figure": "Figure B16B", "qualifier": "plate fillet", "authority": "Figure B16B (p. 107)"},
                    {"figure": "Figure B16C", "qualifier": "pipe groove", "authority": "Figure B16C (p. 108)"},
                ),
            }
        position_phrases = [
            "flat welding position",
            "horizontal fixed position",
            "horizontal welding position",
            "overhead welding position",
            "vertical welding position",
            "inclined position",
        ]
        for pp in position_phrases:
            self.weld_positions[pp] = {
                "canonical_term": pp,
                "canonical_id": f"weld_position:{pp.replace(' ', '_')}",
                "source_authority": "Clause 4",
                "target_division": "clause4_glossary",
                "entity_type": "WELD_POSITION",
            }

        domain_quals = [
            "[pipe]", "[plate]", "[resistance welding]", "[brazing]", "[soldering]", "[thermal spraying]",
            "in pipe", "in plate", "pipe groove", "plate groove", "pipe fillet", "plate fillet",
            "in groove", "in fillet",
        ]
        for dq in domain_quals:
            self.domain_qualifiers[dq.lower()] = {
                "canonical_term": dq,
                "canonical_id": f"domain_qualifier:{dq.lower().replace(' ', '_').strip('[]')}",
                "source_authority": "Clause 4 / Annex B Qualifiers",
                "target_division": "clause4_glossary",
                "entity_type": "DOMAIN_QUALIFIER",
            }

        # 7. Diagram Callouts (Accepted Nodes across Annex B figures)
        annex_b_callouts = {
            # Figure B25
            "theoretical throat": ("Figure B25", "Weld Sizes", 123),
            "effective throat": ("Figure B25", "Weld Sizes", 123),
            "actual throat": ("Figure B25", "Weld Sizes", 123),
            "convex fillet weld size": ("Figure B25", "Weld Sizes", 123),
            "concave fillet weld size": ("Figure B25", "Weld Sizes", 123),
            "groove weld size": ("Figure B25", "Weld Sizes", 123),
            # Figure B33
            "crater crack": ("Figure B33", "Crack Types", 137),
            "face crack": ("Figure B33", "Crack Types", 137),
            "heat-affected zone crack": ("Figure B33", "Crack Types", 137),
            "longitudinal crack": ("Figure B33", "Crack Types", 137),
            "root crack": ("Figure B33", "Crack Types", 137),
            "root surface crack": ("Figure B33", "Crack Types", 137),
            "throat crack": ("Figure B33", "Crack Types", 137),
            "toe crack": ("Figure B33", "Crack Types", 137),
            "underbead crack": ("Figure B33", "Crack Types", 137),
            "transverse crack": ("Figure B33", "Crack Types", 137),
            "lamellar tear": ("Figure B33", "Crack Types", 137),
            # Figure B46
            "advancing side": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "retreating side": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "thermomechanically affected zone": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "tmaz": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "tool shoulder": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "probe": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "weld nugget": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            "exit hole": ("Figure B46", "Schematic of the Friction Stir Welding Process", 154),
            # Figure B12
            "starting weld tab": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "runoff tab": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "runoff weld tab": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "sump": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "split pipe backing": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "end dam": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            "shelf bar": ("Figure B12", "End Dam, Shelf, Split Pipe Backing, Sump, Starting Weld Tab, and Runoff Tab", 101),
            # Figure B7
            "edge shape": ("Figure B7", "Edge Shapes", 92),
            "edge shapes": ("Figure B7", "Edge Shapes", 92),
        }
        for callout_phrase, (fig_id, title, page) in annex_b_callouts.items():
            self.diagram_callouts[callout_phrase] = {
                "canonical_term": callout_phrase,
                "canonical_id": f"{fig_id.lower().replace(' ', '_')}:callout:{callout_phrase.replace(' ', '_')}",
                "figure_id": fig_id,
                "figure_title": title,
                "source_authority": f"Annex B ({fig_id}, p. {page})",
                "target_division": "annex_b_spatial",
                "entity_type": "DIAGRAM_CALLOUT",
            }

        # 8. Waveform Intervals
        waveforms = {
            "upslope": ("Figure B53", "Pulsed Welding Cycle", 163),
            "downslope": ("Figure B53", "Pulsed Welding Cycle", 163),
            "upslope interval": ("Figure B53", "Pulsed Welding Cycle", 163),
            "downslope interval": ("Figure B53", "Pulsed Welding Cycle", 163),
            "upslope and downslope current intervals": ("Figure B53", "Pulsed Welding Cycle", 163),
            "upslope and downslope intervals": ("Figure B53", "Pulsed Welding Cycle", 163),
            "background current": ("Figure B53", "Pulsed Welding Cycle", 163),
            "peak current": ("Figure B53", "Pulsed Welding Cycle", 163),
            "squeeze time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "hold time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "quench time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "temper time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "weld interval": ("Figure B49", "Pulsation Welding Waveform", 158),
            "heat time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "cool time": ("Figure B49", "Pulsation Welding Waveform", 158),
            "crater fill time": ("Figure B54", "Arc Welding Cycle", 164),
            "meltback time": ("Figure B54", "Arc Welding Cycle", 164),
            "postflow time": ("Figure B54", "Arc Welding Cycle", 164),
            "flash time": ("Figure B51", "Flash Welding Cycle", 160),
            "upset time": ("Figure B51", "Flash Welding Cycle", 160),
            "rotational speed": ("Figure B44", "Inertia Friction Welding", 152),
            "friction force": ("Figure B44", "Inertia Friction Welding", 152),
        }
        for w_phrase, (fig_id, title, page) in waveforms.items():
            self.waveform_intervals[w_phrase] = {
                "canonical_term": w_phrase,
                "canonical_id": f"{fig_id.lower().replace(' ', '_')}:interval:{w_phrase.replace(' ', '_')}",
                "figure_id": fig_id,
                "figure_title": title,
                "source_authority": f"Annex B ({fig_id}, p. {page})",
                "target_division": "annex_b_waveform",
                "entity_type": "WAVEFORM_INTERVAL",
            }

        # 9. Full Store-Compiled Annex B Node Inventory (All 1,115 Accepted Nodes Across 56 Figure Stores)
        import json as _json
        self.indexed_annex_b_node_count = 0
        annex_b_dir = self.root / "storage/evidence_v2/annex_b_complete_001"
        generic_callout_noise = {
            "aws a3.0m/a3.0:2020", "annex b", "time", "weld", "welds", "plate", "pipe",
            "joint", "joints", "process", "arrow", "other", "both", "none", "notes", "note",
            "detail", "section", "view", "axis", "force", "speed", "current", "voltage",
            "1g welding", "2g welding", "3g welding", "4g welding", "5g welding", "6g welding",
            "1f welding", "2f welding", "3f welding", "4f welding",
        }
        if annex_b_dir.exists():
            for fig_store_path in sorted(annex_b_dir.glob("figure_b*_store.json")):
                f_data = _json.loads(fig_store_path.read_text(encoding="utf-8"))
                fig_id = f_data.get("figure_id", "").strip()
                title = f_data.get("official_title", "").strip()
                archetype = f_data.get("archetype", "")
                pages_raw = f_data.get("pages", [])
                page = 88
                if pages_raw:
                    first_p = pages_raw[0]
                    if isinstance(first_p, (list, tuple)) and len(first_p) >= 2:
                        page = first_p[1]
                    elif isinstance(first_p, int):
                        page = first_p
                elif f_data.get("provenance", {}).get("printed_page"):
                    page = f_data["provenance"]["printed_page"]

                raw_nodes = f_data.get("nodes") or f_data.get("graph", {}).get("nodes") or {}
                node_list = list(raw_nodes.values()) if isinstance(raw_nodes, dict) else list(raw_nodes)
                self.indexed_annex_b_node_count += len(node_list)

                is_waveform = archetype == "cycle_waveform_plot" or fig_id in {
                    "Figure B44", "Figure B45", "Figure B49", "Figure B50",
                    "Figure B51", "Figure B53", "Figure B54",
                }
                for node in node_list:
                    n_type = node.get("node_type", "")
                    if n_type in ("FIGURE", "TIME_AXIS"):
                        continue
                    raw_lbl = (node.get("name") or node.get("label") or node.get("text") or "").replace("\x08", " ").strip()
                    if not raw_lbl:
                        continue
                    cleaned_lbl = re.sub(r"^(?:\([A-Za-z0-9]+\)|[A-Z]\s+(?=[A-Z][a-z])|\d+[\.\):\-])\s*", "", raw_lbl).strip()
                    cleaned_lower = " ".join(cleaned_lbl.lower().split())
                    if (
                        len(cleaned_lower) < 4
                        or len(cleaned_lower) > 70
                        or cleaned_lower in generic_callout_noise
                        or cleaned_lower.startswith(("aws a3.0", "annex b", "figure b", "see figure"))
                        or not re.search(r"[a-z]{3,}", cleaned_lower)
                    ):
                        continue
                    # Require >= 2 words for auto-extracted store labels to prevent single-word over-tagging
                    if len(cleaned_lower.split()) < 2:
                        continue
                    if is_waveform:
                        if cleaned_lower not in self.waveform_intervals:
                            self.waveform_intervals[cleaned_lower] = {
                                "canonical_term": cleaned_lower,
                                "canonical_id": f"{fig_id.lower().replace(' ', '_')}:interval:{cleaned_lower.replace(' ', '_')}",
                                "figure_id": fig_id,
                                "figure_title": title,
                                "source_authority": f"Annex B ({fig_id}, p. {page})",
                                "target_division": "annex_b_waveform",
                                "entity_type": "WAVEFORM_INTERVAL",
                            }
                    else:
                        if cleaned_lower not in self.diagram_callouts:
                            self.diagram_callouts[cleaned_lower] = {
                                "canonical_term": cleaned_lower,
                                "canonical_id": f"{fig_id.lower().replace(' ', '_')}:callout:{cleaned_lower.replace(' ', '_')}",
                                "figure_id": fig_id,
                                "figure_title": title,
                                "source_authority": f"Annex B ({fig_id}, p. {page})",
                                "target_division": "annex_b_spatial",
                                "entity_type": "DIAGRAM_CALLOUT",
                            }

        # Precompute word-boundary token tuples for O(1) set-membership pre-filtering
        self._key_words = {}
        for lex in (
            self.OUT_OF_RANGE_LOCATORS,
            self.standard_locators,
            self.waveform_intervals,
            self.diagram_callouts,
            self.weld_positions,
            self.domain_qualifiers,
            self.process_codes,
            self.nonstandard_terms,
            self.process_terms,
            self.glossary_terms,
        ):
            for k in lex:
                if k not in self._key_words:
                    self._key_words[k] = tuple(re.findall(r"\w+", k.lower()))

    # -----------------------------------------------------------------------
    # Compound Designation Parsing
    # -----------------------------------------------------------------------

    def parse_compound_designation(self, token: str) -> Optional[Dict[str, Any]]:
        """Parse <BASE_PROCESS>[-<VARIANT>]-<MODE_SUFFIX> per Table A4.
        e.g. PAW-AU, GTAW-ME, FCAW-G-SA, OFC-A-MA, GMAW-P-AU.
        Also detects invalid variants (e.g. FCAW-Z-SA), invalid suffixes (e.g. GTAW-ZZ),
        and conflicting double mode suffixes (e.g. PAW-AU-ME).
        """
        tok_upper = token.upper().strip()
        parts = tok_upper.split("-")
        if len(parts) < 2 or len(parts) > 3:
            return None

        base_cand = parts[0]
        if not re.match(r"^[A-Z]{2,6}$", base_cand):
            return None

        # Check if base_cand is a recognized process code
        base_info = self.process_codes.get(base_cand)
        if not base_info:
            return None

        # -------------------------------------------------------------------
        # 2-Tier Compound: <BASE>-<MODE_SUFFIX> (e.g. PAW-AU, GTAW-ZZ)
        # Suffix must be exactly 2 letters; 1-letter hyphens are process variations (e.g. FCAW-G)
        # -------------------------------------------------------------------
        if len(parts) == 2:
            if len(parts[1]) != 2:
                return None
            suf_cand = f"-{parts[1]}"
            suf_info = self.VALID_MODE_SUFFIXES.get(suf_cand)
            if suf_info:
                canonical_mode = suf_info["mode"]
                canonical_proc = base_info["canonical_term"]
                full_canonical = f"{canonical_mode.lower()} {canonical_proc}"
                return {
                    "is_valid": True,
                    "canonical_term": full_canonical,
                    "canonical_id": f"compound:{tok_upper}",
                    "source_authority": f"{base_info['source_authority']} + Table A4 (p. 74)",
                    "target_division": "annex_a_tables",
                    "sub_components": (
                        {
                            "type": "BASE_PROCESS",
                            "designation": base_cand,
                            "canonical_term": canonical_proc,
                            "source_authority": base_info["source_authority"],
                        },
                        {
                            "type": "APPLICATION_MODE",
                            "suffix": suf_cand,
                            "canonical_term": canonical_mode,
                            "source_authority": "Table A4 (p. 74)",
                        },
                    ),
                    "abstention_reason": None,
                }
            else:
                # Valid base process, but invalid application mode suffix!
                return {
                    "is_valid": False,
                    "canonical_term": base_info["canonical_term"],
                    "canonical_id": f"invalid_compound:{tok_upper}",
                    "source_authority": f"{base_info['source_authority']} + Table A4 (p. 74)",
                    "target_division": "annex_a_tables",
                    "sub_components": (
                        {
                            "type": "BASE_PROCESS",
                            "designation": base_cand,
                            "canonical_term": base_info["canonical_term"],
                            "source_authority": base_info["source_authority"],
                        },
                        {
                            "type": "INVALID_APPLICATION_MODE",
                            "suffix": suf_cand,
                            "canonical_term": f"Unknown application mode suffix '{suf_cand}'",
                            "source_authority": "Table A4 (p. 74)",
                        },
                    ),
                    "abstention_reason": (
                        f"Suffix '{suf_cand}' is not a standardized application mode suffix in AWS A3.0M/A3.0:2020 Table A4. "
                        "Table A4 standardizes exactly six suffixes: -AD (Adaptive control), -AU (Automatic), -MA (Manual), "
                        "-ME (Mechanized), -RO (Robotic), and -SA (Semiautomatic)."
                    ),
                }

        # -------------------------------------------------------------------
        # 3-Tier Compound: <BASE>-<MID>-<SUFFIX> (e.g. FCAW-G-SA, PAW-AU-ME)
        # -------------------------------------------------------------------
        part1_suf = f"-{parts[1]}"
        part2_suf = f"-{parts[2]}"

        # Subcase 1: Conflicting double mode suffixes (e.g. PAW-AU-ME, PAW-AU-MA)
        if part1_suf in self.VALID_MODE_SUFFIXES and part2_suf in self.VALID_MODE_SUFFIXES:
            return {
                "is_valid": False,
                "canonical_term": base_info["canonical_term"],
                "canonical_id": f"invalid_compound:{tok_upper}",
                "source_authority": f"{base_info['source_authority']} + Table A4 (p. 74)",
                "target_division": "annex_a_tables",
                "sub_components": (
                    {
                        "type": "BASE_PROCESS",
                        "designation": base_cand,
                        "canonical_term": base_info["canonical_term"],
                        "source_authority": base_info["source_authority"],
                    },
                    {
                        "type": "CONFLICTING_APPLICATION_MODE",
                        "suffix": part1_suf,
                        "canonical_term": self.VALID_MODE_SUFFIXES[part1_suf]["mode"],
                        "source_authority": "Table A4 (p. 74)",
                    },
                    {
                        "type": "CONFLICTING_APPLICATION_MODE",
                        "suffix": part2_suf,
                        "canonical_term": self.VALID_MODE_SUFFIXES[part2_suf]["mode"],
                        "source_authority": "Table A4 (p. 74)",
                    },
                ),
                "abstention_reason": (
                    f"Conflicting application mode suffixes: '{part1_suf}' and '{part2_suf}' cannot both be appended. "
                    "Table A4 standardizes exactly one application mode suffix per process designation."
                ),
            }

        # Subcase 2: Base + Process Variation + Mode Suffix
        var_code = f"{base_cand}-{parts[1]}"
        var_info = self.process_codes.get(var_code)
        suf_info = self.VALID_MODE_SUFFIXES.get(part2_suf)

        if var_info and suf_info:
            # Valid 3-tier compound!
            canonical_mode = suf_info["mode"]
            canonical_var = var_info["canonical_term"]
            canonical_base = base_info["canonical_term"]
            full_canonical = f"{canonical_mode.lower()} {canonical_var}"
            return {
                "is_valid": True,
                "canonical_term": full_canonical,
                "canonical_id": f"compound:{tok_upper}",
                "source_authority": f"{base_info['source_authority']} + Clause 4 / Table A1 / IS_A Store + Table A4 (p. 74)",
                "target_division": "annex_a_tables",
                "sub_components": (
                    {
                        "type": "BASE_PROCESS",
                        "designation": base_cand,
                        "canonical_term": canonical_base,
                        "source_authority": base_info["source_authority"],
                    },
                    {
                        "type": "PROCESS_VARIATION",
                        "code": var_code,
                        "canonical_term": canonical_var,
                        "source_authority": "Clause 4 / Table A1 / IS_A Store",
                    },
                    {
                        "type": "APPLICATION_MODE",
                        "suffix": part2_suf,
                        "canonical_term": canonical_mode,
                        "source_authority": "Table A4 (p. 74)",
                    },
                ),
                "abstention_reason": None,
            }
        elif not var_info:
            # Base is valid, but intermediate variation is invalid! (e.g. FCAW-Z-SA)
            return {
                "is_valid": False,
                "canonical_term": base_info["canonical_term"],
                "canonical_id": f"invalid_compound:{tok_upper}",
                "source_authority": f"{base_info['source_authority']} + Table A4 (p. 74)",
                "target_division": "annex_a_tables",
                "sub_components": (
                    {
                        "type": "BASE_PROCESS",
                        "designation": base_cand,
                        "canonical_term": base_info["canonical_term"],
                        "source_authority": base_info["source_authority"],
                    },
                    {
                        "type": "INVALID_PROCESS_VARIATION",
                        "code": var_code,
                        "canonical_term": f"Unknown process variation '{var_code}'",
                        "source_authority": "Clause 4 / Table A1 / IS_A Store",
                    },
                    {
                        "type": "APPLICATION_MODE" if suf_info else "INVALID_APPLICATION_MODE",
                        "suffix": part2_suf,
                        "canonical_term": suf_info["mode"] if suf_info else f"Unknown suffix '{part2_suf}'",
                        "source_authority": "Table A4 (p. 74)",
                    },
                ),
                "abstention_reason": f"Process variation '{var_code}' is not a standardized process variation of '{base_cand}' in AWS A3.0M/A3.0:2020.",
            }
        else:
            # Intermediate variation is valid, but mode suffix is invalid!
            return {
                "is_valid": False,
                "canonical_term": var_info["canonical_term"],
                "canonical_id": f"invalid_compound:{tok_upper}",
                "source_authority": f"{var_info['source_authority']} + Table A4 (p. 74)",
                "target_division": "annex_a_tables",
                "sub_components": (
                    {
                        "type": "BASE_PROCESS",
                        "designation": base_cand,
                        "canonical_term": base_info["canonical_term"],
                        "source_authority": base_info["source_authority"],
                    },
                    {
                        "type": "PROCESS_VARIATION",
                        "code": var_code,
                        "canonical_term": var_info["canonical_term"],
                        "source_authority": "Clause 4 / Table A1 / IS_A Store",
                    },
                    {
                        "type": "INVALID_APPLICATION_MODE",
                        "suffix": part2_suf,
                        "canonical_term": f"Unknown application mode suffix '{part2_suf}'",
                        "source_authority": "Table A4 (p. 74)",
                    },
                ),
                "abstention_reason": f"Suffix '{part2_suf}' is not a standardized application mode suffix in AWS A3.0M/A3.0:2020 Table A4.",
            }

    # -----------------------------------------------------------------------
    # Main Recognition Pipeline
    # -----------------------------------------------------------------------

    def recognize_entities(self, query: str) -> WeldingNERReceipt:
        """Run deterministic longest-match entity recognition over query text.
        Returns character-offset typed spans and structured multi-division receipt.
        """
        self.ensure_initialized()
        raw_query = query
        q_len = len(query)
        q_words = set(re.findall(r"\w+", query.lower()))
        kw_map = self._key_words

        # Collect candidate spans: (start, end, span_dict)
        raw_candidates: List[Tuple[int, int, Dict[str, Any]]] = []

        # 1. Out-of-Range Locators
        for loc_str, loc_info in self.OUT_OF_RANGE_LOCATORS.items():
            if not all(w in q_words for w in kw_map.get(loc_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(loc_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": "STANDARD_LOCATOR",
                            "canonical_term": loc_str.title(),
                            "canonical_id": f"locator:out_of_range:{loc_str.replace(' ', '_')}",
                            "source_authority": "AWS A3.0 Scope Boundary",
                            "target_division": loc_info["division"],
                            "is_valid": False,
                            "abstention_reason": loc_info["reason"],
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 2. Standard Locators (Figures, Tables, Clauses)
        for loc_str, loc_info in self.standard_locators.items():
            if not all(w in q_words for w in kw_map.get(loc_str, ())):
                continue
            pattern = r"\b" + re.escape(loc_str) + r"\b"
            for m in re.finditer(pattern, query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": loc_info["entity_type"],
                            "canonical_term": loc_info["canonical_term"],
                            "canonical_id": loc_info["canonical_id"],
                            "source_authority": loc_info["source_authority"],
                            "target_division": loc_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 3. Dynamic Compound Designations (e.g. PAW-AU, GTAW-ME, GTAW-ZZ, FCAW-G-SA, OFC-A-MA, PAW-AU-ME)
        for m in re.finditer(r"\b[A-Za-z]{2,6}(?:-[A-Za-z0-9]{1,4}){1,2}\b", query):
            tok = m.group(0)
            parsed = self.parse_compound_designation(tok)
            if parsed:
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": "COMPOUND_DESIGNATION" if parsed["is_valid"] else "INVALID_COMPOUND_DESIGNATION",
                            "canonical_term": parsed["canonical_term"],
                            "canonical_id": parsed["canonical_id"],
                            "source_authority": parsed["source_authority"],
                            "target_division": parsed["target_division"],
                            "is_valid": parsed["is_valid"],
                            "abstention_reason": parsed["abstention_reason"],
                            "sub_components": parsed["sub_components"],
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 4. Waveform Intervals
        for w_str, w_info in self.waveform_intervals.items():
            if not all(w in q_words for w in kw_map.get(w_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(w_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": w_info["entity_type"],
                            "canonical_term": w_info["canonical_term"],
                            "canonical_id": w_info["canonical_id"],
                            "source_authority": w_info["source_authority"],
                            "target_division": w_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 5. Diagram Callouts
        for c_str, c_info in self.diagram_callouts.items():
            if not all(w in q_words for w in kw_map.get(c_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(c_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": c_info["entity_type"],
                            "canonical_term": c_info["canonical_term"],
                            "canonical_id": c_info["canonical_id"],
                            "source_authority": c_info["source_authority"],
                            "target_division": c_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 6. Weld Positions
        for p_str, p_info in self.weld_positions.items():
            if not all(w in q_words for w in kw_map.get(p_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(p_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": p_info["entity_type"],
                            "canonical_term": p_info["canonical_term"],
                            "canonical_id": p_info["canonical_id"],
                            "source_authority": p_info["source_authority"],
                            "target_division": p_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": p_info.get("ambiguity_candidates", ()),
                        },
                    )
                )

        # 7. Domain Qualifiers
        for q_str, q_info in self.domain_qualifiers.items():
            if not all(w in q_words for w in kw_map.get(q_str, ())):
                continue
            # Support bracketed and unbracketed word boundary
            esc_q = re.escape(q_str)
            pattern = esc_q if q_str.startswith("[") else r"\b" + esc_q + r"\b"
            for m in re.finditer(pattern, query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": q_info["entity_type"],
                            "canonical_term": q_info["canonical_term"],
                            "canonical_id": q_info["canonical_id"],
                            "source_authority": q_info["source_authority"],
                            "target_division": q_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 8. Standalone Process Codes
        for code, c_info in self.process_codes.items():
            if not all(w in q_words for w in kw_map.get(code, ())):
                continue
            # If code is short (2 letters like CW, AB, TB, FB, IB, IS, RS, WS), require word boundary
            for m in re.finditer(r"\b" + re.escape(code) + r"\b", query, flags=re.IGNORECASE if len(code) > 2 else 0):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": c_info["entity_type"],
                            "canonical_term": c_info["canonical_term"],
                            "canonical_id": c_info["canonical_id"],
                            "source_authority": c_info["source_authority"],
                            "target_division": c_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": c_info.get("ambiguity_candidates", ()),
                        },
                    )
                )

        # 9. Nonstandard & Historical Terms
        for ns_str, ns_info in self.nonstandard_terms.items():
            if len(ns_str) <= 2 or not all(w in q_words for w in kw_map.get(ns_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(ns_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": ns_info["entity_type"],
                            "canonical_term": ns_info["canonical_term"],
                            "canonical_id": ns_info["canonical_id"],
                            "source_authority": ns_info["source_authority"],
                            "target_division": ns_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 10. Process Terms (Table A1/A2/IS-A full names)
        for p_str, p_info in self.process_terms.items():
            if len(p_str) <= 3 or not all(w in q_words for w in kw_map.get(p_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(p_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": p_info["entity_type"],
                            "canonical_term": p_info["canonical_term"],
                            "canonical_id": p_info["canonical_id"],
                            "source_authority": p_info["source_authority"],
                            "target_division": p_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": (),
                        },
                    )
                )

        # 11. Glossary Headwords
        stopwords = {
            "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against", "between",
            "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
            "down", "of", "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
            "is", "are", "was", "were", "what", "which", "who", "whom", "this", "that", "these",
            "those", "am", "be", "been", "being", "have", "has", "had", "having", "do", "does",
            "did", "doing", "and", "but", "if", "or", "because", "as", "until", "while",
            "standard", "definition", "definitions", "defined", "meaning", "means", "term",
            "terms", "figure", "figures", "table", "tables", "annex", "clause", "part",
        }
        for g_str, g_info in self.glossary_terms.items():
            if len(g_str) <= 2 or g_str in stopwords or not all(w in q_words for w in kw_map.get(g_str, ())):
                continue
            for m in re.finditer(r"\b" + re.escape(g_str) + r"\b", query, flags=re.IGNORECASE):
                raw_candidates.append(
                    (
                        m.start(),
                        m.end(),
                        {
                            "surface_text": query[m.start():m.end()],
                            "entity_type": g_info["entity_type"],
                            "canonical_term": g_info["canonical_term"],
                            "canonical_id": g_info["canonical_id"],
                            "source_authority": g_info["source_authority"],
                            "target_division": g_info["target_division"],
                            "is_valid": True,
                            "abstention_reason": None,
                            "sub_components": (),
                            "ambiguity_candidates": g_info.get("ambiguity_candidates", ()),
                        },
                    )
                )

        # -------------------------------------------------------------------
        # Non-overlapping longest-match selection
        # -------------------------------------------------------------------
        # Sort candidates by:
        # 1. start_char ascending
        # 2. length descending (end - start)
        # 3. entity priority: STANDARD_LOCATOR > COMPOUND_DESIGNATION > DIAGRAM_CALLOUT / WAVEFORM > WELD_POSITION > NONSTANDARD > PROCESS > GLOSSARY
        priority_map = {
            "STANDARD_LOCATOR": 10,
            "COMPOUND_DESIGNATION": 9,
            "INVALID_COMPOUND_DESIGNATION": 9,
            "DIAGRAM_CALLOUT": 8,
            "WAVEFORM_INTERVAL": 8,
            "WELD_POSITION": 7,
            "DOMAIN_QUALIFIER": 6,
            "NONSTANDARD_OR_HISTORICAL": 5,
            "PROCESS_CODE": 4,
            "MODE_SUFFIX": 4,
            "PROCESS_TERM": 3,
            "GLOSSARY_TERM": 2,
        }

        # Filter out exact duplicates
        unique_cands: List[Tuple[int, int, Dict[str, Any]]] = []
        seen_cand_keys: Set[Tuple[int, int, str]] = set()
        for s, e, d in raw_candidates:
            k = (s, e, d["canonical_id"])
            if k not in seen_cand_keys:
                seen_cand_keys.add(k)
                unique_cands.append((s, e, d))

        unique_cands.sort(
            key=lambda item: (
                item[0],  # start_char asc
                -(item[1] - item[0]),  # length desc
                -priority_map.get(item[2]["entity_type"], 0),  # priority desc
            )
        )

        selected_spans: List[WeldingEntitySpan] = []
        last_end = -1

        pipe_positions = {
            "1g": ("1G, pipe", "Figure B19(A)", "Clause 4 (p. 1) / Figure B19(A)"),
            "2g": ("2G, pipe", "Figure B19(B)", "Clause 4 (p. 1) / Figure B19(B)"),
            "3g": ("3G, pipe", "Figure B19(A)", "Clause 4 (p. 1) / Figure B19(A)"),
            "4g": ("4G, pipe", "Figure B19(A)", "Clause 4 (p. 1) / Figure B19(A)"),
            "5g": ("5G, pipe", "Figure B19(C)", "Clause 4 (p. 1) / Figure B19(C)"),
            "6g": ("6G, pipe", "Figure B19(D)", "Clause 4 (p. 1) / Figure B19(D)"),
            "6gr": ("6GR, pipe", "Figure B19(E)", "Clause 4 (p. 1) / Figure B19(E)"),
            "1f": ("1F, pipe", "Figure B20(A)", "Clause 4 (p. 1) / Figure B20(A)"),
            "2f": ("2F, pipe", "Figure B20(B)", "Clause 4 (p. 1) / Figure B20(B)"),
            "2fr": ("2FR, pipe", "Figure B20(C)", "Clause 4 (p. 1) / Figure B20(C)"),
            "3f": ("3F, pipe", "Figure B20(C)", "Clause 4 (p. 1) / Figure B20(C)"),
            "4f": ("4F, pipe", "Figure B20(D)", "Clause 4 (p. 1) / Figure B20(D)"),
        }
        plate_positions = {
            "1g": ("1G, plate", "Figure B17(A)", "Clause 4 (p. 1) / Figure B17(A)"),
            "2g": ("2G, plate", "Figure B17(B)", "Clause 4 (p. 1) / Figure B17(B)"),
            "3g": ("3G, plate", "Figure B17(C)", "Clause 4 (p. 1) / Figure B17(C)"),
            "4g": ("4G, plate", "Figure B17(D)", "Clause 4 (p. 1) / Figure B17(D)"),
            "1f": ("1F, plate", "Figure B18(A)", "Clause 4 (p. 1) / Figure B18(A)"),
            "2f": ("2F, plate", "Figure B18(B)", "Clause 4 (p. 1) / Figure B18(B)"),
            "3f": ("3F, plate", "Figure B18(C)", "Clause 4 (p. 1) / Figure B18(C)"),
            "4f": ("4F, plate", "Figure B18(D)", "Clause 4 (p. 1) / Figure B18(D)"),
        }

        for s, e, d in unique_cands:
            if s >= last_end:
                # Disambiguation / Context Refinement
                ambig = d.get("ambiguity_candidates", ())
                canon_term = d["canonical_term"]
                canon_id = d["canonical_id"]
                authority = d["source_authority"]
                target_div = d["target_division"]

                sec_types: List[str] = []
                linked_c4: List[str] = []
                linked_figs: List[str] = []
                linked_tbls: List[str] = []
                ambig_senses: List[str] = []

                # Special Disambiguation 1: "AB"
                if d["surface_text"].upper() == "AB":
                    q_lower = query.lower()
                    if any(w in q_lower for w in ["braz", "arc", "figure a6", "a6"]):
                        canon_term = "arc brazing"
                        canon_id = "figure_a6:code:AB"
                        authority = "Figure A6 (p. 79) Legend"
                        target_div = "annex_a_charts"
                        linked_figs.append("Figure A6")
                    elif any(w in q_lower for w in ["adhesive", "bonding", "table a1", "clause 4"]):
                        canon_term = "adhesive bonding"
                        canon_id = "table_a1:code:AB"
                        authority = "Table A1 (p. 69) / Clause 4 (p. 8)"
                        target_div = "annex_a_tables"
                        linked_tbls.append("Table A1")
                    else:
                        ambig_senses.extend(["adhesive bonding", "arc brazing"])
                        linked_tbls.append("Table A1")
                        linked_figs.append("Figure A6")

                # Special Disambiguation 2: Test Positions (1G, 1F, 2G, 2F, 5G, 6G, 6GR)
                elif d["entity_type"] == "WELD_POSITION":
                    q_lower = query.lower()
                    code_lower = d["surface_text"].lower().strip()
                    pipe_words = any(w in q_lower for w in ["pipe", "tube", "circumferential", "rotated", "[pipe]"])
                    plate_words = any(w in q_lower for w in ["plate", "linear", "[plate]"])
                    if code_lower in pipe_positions or code_lower in plate_positions:
                        if pipe_words and not plate_words and code_lower in pipe_positions:
                            c_term, fig, auth = pipe_positions[code_lower]
                            canon_term = c_term
                            authority = auth
                            linked_figs.append(fig)
                            bf = fig.split("(")[0]
                            if bf not in linked_figs:
                                linked_figs.append(bf)
                        elif plate_words and not pipe_words and code_lower in plate_positions:
                            c_term, fig, auth = plate_positions[code_lower]
                            canon_term = c_term
                            authority = auth
                            linked_figs.append(fig)
                            bf = fig.split("(")[0]
                            if bf not in linked_figs:
                                linked_figs.append(bf)
                        else:
                            # Both or Unqualified -> Bind both senses!
                            c_plate = plate_positions.get(code_lower)
                            c_pipe = pipe_positions.get(code_lower)
                            if c_plate and c_pipe:
                                ambig_senses.extend([f"{code_lower.upper()}, plate", f"{code_lower.upper()}, pipe"])
                                for cf in [c_plate[1], c_pipe[1]]:
                                    linked_figs.append(cf)
                                    bf = cf.split("(")[0]
                                    if bf not in linked_figs:
                                        linked_figs.append(bf)
                            elif c_pipe:
                                linked_figs.append(c_pipe[1])
                            elif c_plate:
                                linked_figs.append(c_plate[1])

                # Polysemous Cross-Linking (Callouts <-> Glossary)
                if d["entity_type"] in ["DIAGRAM_CALLOUT", "WAVEFORM_INTERVAL", "PROCESS_TERM", "PROCESS_CODE"]:
                    term_key = d["canonical_term"].lower()
                    surf_key = d["surface_text"].lower()
                    g_meta = self.glossary_terms.get(term_key) or self.glossary_terms.get(surf_key)
                    if g_meta:
                        if "GLOSSARY_TERM" not in sec_types:
                            sec_types.append("GLOSSARY_TERM")
                        g_term = g_meta["canonical_term"]
                        if g_term not in linked_c4:
                            linked_c4.append(g_term)
                        for cf in g_meta.get("cross_figures", []):
                            clean_cf = cf if cf.startswith("Figure") else f"Figure {cf}"
                            if clean_cf not in linked_figs:
                                linked_figs.append(clean_cf)
                    if d.get("figure_id") and d["figure_id"] not in linked_figs:
                        linked_figs.append(d["figure_id"])

                elif d["entity_type"] == "GLOSSARY_TERM":
                    term_key = d["canonical_term"].lower()
                    surf_key = d["surface_text"].lower()
                    c_meta = self.diagram_callouts.get(term_key) or self.diagram_callouts.get(surf_key)
                    w_meta = self.waveform_intervals.get(term_key) or self.waveform_intervals.get(surf_key)
                    if c_meta:
                        if "DIAGRAM_CALLOUT" not in sec_types:
                            sec_types.append("DIAGRAM_CALLOUT")
                        if c_meta.get("figure_id") and c_meta["figure_id"] not in linked_figs:
                            linked_figs.append(c_meta["figure_id"])
                    elif w_meta:
                        if "WAVEFORM_INTERVAL" not in sec_types:
                            sec_types.append("WAVEFORM_INTERVAL")
                        if w_meta.get("figure_id") and w_meta["figure_id"] not in linked_figs:
                            linked_figs.append(w_meta["figure_id"])
                    if d["canonical_term"] not in linked_c4:
                        linked_c4.append(d["canonical_term"])
                    for cf in d.get("cross_figures", []):
                        clean_cf = cf if cf.startswith("Figure") else f"Figure {cf}"
                        if clean_cf not in linked_figs:
                            linked_figs.append(clean_cf)

                # Extract figure from canonical_id if present
                m_fig_id = re.search(r"figure_([ab][0-9]{1,2}[a-z]?)", d["canonical_id"])
                if m_fig_id:
                    fid_str = f"Figure {m_fig_id.group(1).upper()}"
                    if fid_str not in linked_figs:
                        linked_figs.append(fid_str)

                # Extract table from canonical_id if present
                m_tbl_id = re.search(r"table_([a-z][0-9]+)", d["canonical_id"])
                if m_tbl_id:
                    tid_str = f"Table {m_tbl_id.group(1).upper()}"
                    if tid_str not in linked_tbls:
                        linked_tbls.append(tid_str)

                # Extract tables for compound designations
                if d.get("sub_components"):
                    for sc in d["sub_components"]:
                        if sc.get("type") in ["APPLICATION_MODE", "INVALID_APPLICATION_MODE", "CONFLICTING_APPLICATION_MODE"]:
                            if "Table A4" not in linked_tbls:
                                linked_tbls.append("Table A4")
                        if sc.get("type") in ["BASE_PROCESS", "PROCESS_VARIATION"]:
                            if "Table A1" not in linked_tbls:
                                linked_tbls.append("Table A1")

                span = WeldingEntitySpan(
                    surface_text=d["surface_text"],
                    start_char=s,
                    end_char=e,
                    entity_type=d["entity_type"],
                    canonical_term=canon_term,
                    canonical_id=canon_id,
                    source_authority=authority,
                    target_division=target_div,
                    sub_components=d.get("sub_components", ()),
                    ambiguity_candidates=ambig,
                    is_valid=d.get("is_valid", True),
                    abstention_reason=d.get("abstention_reason"),
                    secondary_entity_types=tuple(sec_types),
                    linked_clause4_terms=tuple(linked_c4),
                    linked_figures=tuple(linked_figs),
                    linked_tables=tuple(linked_tbls),
                    ambiguous_senses=tuple(ambig_senses),
                )
                selected_spans.append(span)
                last_end = e

        # Summary Metrics
        entity_counts: Dict[str, int] = {}
        target_divisions_set: Set[str] = set()
        inferred_figures: List[str] = []
        inferred_tables: List[str] = []
        inferred_clause4_terms: List[str] = []
        has_ambiguities = False

        for sp in selected_spans:
            entity_counts[sp.entity_type] = entity_counts.get(sp.entity_type, 0) + 1
            target_divisions_set.add(sp.target_division)
            if sp.ambiguity_candidates or sp.ambiguous_senses:
                has_ambiguities = True

            # Inferred targets from links
            for fig in sp.linked_figures:
                clean_fig = fig.split("(")[0].strip()
                if clean_fig not in inferred_figures:
                    inferred_figures.append(clean_fig)
                if fig not in inferred_figures:
                    inferred_figures.append(fig)

            for tbl in sp.linked_tables:
                if tbl not in inferred_tables:
                    inferred_tables.append(tbl)

            for c4 in sp.linked_clause4_terms:
                if c4 not in inferred_clause4_terms:
                    inferred_clause4_terms.append(c4)

            # Inferred targets from entity type
            if sp.entity_type in ["STANDARD_LOCATOR", "DIAGRAM_CALLOUT", "WAVEFORM_INTERVAL"]:
                m_fig = re.search(r"figure_([ab][0-9]{1,2}[a-z]?)", sp.canonical_id)
                if m_fig:
                    fig_num = m_fig.group(1).upper()
                    f_name = f"Figure {fig_num}"
                    if f_name not in inferred_figures:
                        inferred_figures.append(f_name)

            if sp.entity_type == "STANDARD_LOCATOR" and "table" in sp.canonical_id:
                m_tbl = re.search(r"table_([a-z][0-9]+)", sp.canonical_id)
                if m_tbl:
                    tbl_name = f"Table {m_tbl.group(1).upper()}"
                    if tbl_name not in inferred_tables:
                        inferred_tables.append(tbl_name)

            if sp.entity_type in ["GLOSSARY_TERM", "NONSTANDARD_OR_HISTORICAL", "PROCESS_TERM"]:
                if sp.canonical_term not in inferred_clause4_terms and len(sp.canonical_term.split()) <= 4:
                    inferred_clause4_terms.append(sp.canonical_term)

            # If span is dual-role (e.g. DIAGRAM_CALLOUT with secondary GLOSSARY_TERM), include clause4_glossary
            if "GLOSSARY_TERM" in sp.secondary_entity_types or sp.linked_clause4_terms:
                target_divisions_set.add("clause4_glossary")

        # Definitional intent promotion
        definitional_intent = any(tok in q_words for tok in ["define", "defined", "definition", "definitions", "meaning"]) or "what is" in query.lower() or "how is" in query.lower() or "how are" in query.lower() or "explain" in query.lower()
        if definitional_intent and inferred_clause4_terms:
            target_divisions_set.add("clause4_glossary")

        # Normalized query
        cleaned = re.sub(r"[^\w\s\-]", " ", query)
        normalized_query = " ".join(cleaned.lower().split())

        return WeldingNERReceipt(
            raw_query=raw_query,
            normalized_query=normalized_query,
            spans=selected_spans,
            entity_counts_by_type=entity_counts,
            has_ambiguities=has_ambiguities,
            target_divisions=sorted(list(target_divisions_set)),
            inferred_targets={
                "figures": inferred_figures,
                "tables": inferred_tables,
                "clause4_terms": inferred_clause4_terms,
            },
        )

    def extract(self, query: str) -> WeldingNERReceipt:
        """Standardized NER extraction interface equivalent to recognize_entities."""
        return self.recognize_entities(query)


# Singleton
_NER_INSTANCE: Optional[WeldingNER] = None


def get_welding_ner(stores: Optional[Dict[str, Any]] = None, root: Optional[Path] = None) -> WeldingNER:
    """Return singleton WeldingNER instance, automatically ensuring hydration."""
    global _NER_INSTANCE
    if _NER_INSTANCE is None:
        _NER_INSTANCE = WeldingNER(stores=stores, root=root)
        _NER_INSTANCE.ensure_initialized()
    elif stores:
        _NER_INSTANCE.ensure_initialized(stores)
    return _NER_INSTANCE
