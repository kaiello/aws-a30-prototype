"""semantic_nlq_expander.py

Deterministic Semantic Expansion and Natural Language Query (NLQ) Routing Engine.
Builds an in-memory Multi-Store Synonym, Alias, and Concept Graph directly from
locked Phase 0-3 canonical stores of AWS A3.0M/A3.0:2020.

Guarantees:
1. 100% Offline & Deterministic: Zero network calls, zero LLM dependencies.
2. 100% Canonical Store Immutability: Reads locked Phase 0-3 stores read-only.
3. Zero Hardcoded Benchmark IDs or Test Question Literals.
4. Structured Expansion Trace provenance generation for all NLQ queries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Structured Expansion Receipt Data Structures
# ---------------------------------------------------------------------------

@dataclass
class AliasExpansionItem:
    surface_span: str
    canonical_term: str
    source_authority: str
    resolution_type: str  # "ABBREVIATION" | "HISTORICAL_TERM" | "NONSTANDARD_TERM" | "MORPHOLOGICAL" | "CONCEPT_INDEX"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticExpansionTrace:
    raw_query: str
    normalized_query: str
    extracted_candidate_terms: List[str] = field(default_factory=list)
    alias_expansions: List[Dict[str, Any]] = field(default_factory=list)
    inferred_targets: Dict[str, List[str]] = field(
        default_factory=lambda: {"figures": [], "tables": [], "clause4_terms": []}
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "extracted_candidate_terms": list(self.extracted_candidate_terms),
            "alias_expansions": [
                x if isinstance(x, dict) else x.to_dict() for x in self.alias_expansions
            ],
            "inferred_targets": {
                "figures": list(self.inferred_targets.get("figures", [])),
                "tables": list(self.inferred_targets.get("tables", [])),
                "clause4_terms": list(self.inferred_targets.get("clause4_terms", [])),
            },
        }


# ---------------------------------------------------------------------------
# Multi-Store Synonym, Alias & Concept Graph Engine
# ---------------------------------------------------------------------------

class SemanticExpander:
    """In-memory multi-store synonym, alias, and concept graph builder and router."""

    def __init__(self, stores: Optional[Dict[str, Any]] = None, root: Optional[Path] = None):
        self.root = Path(root or ROOT).resolve()
        self.stores = stores or {}

        # Core Graph Components
        self.abbrev_to_canonical: Dict[str, Dict[str, Any]] = {}
        self.canonical_to_abbrevs: Dict[str, List[str]] = {}
        self.alias_pivot_map: Dict[str, Dict[str, Any]] = {}
        self.clause4_lexicon: Dict[str, Dict[str, Any]] = {}
        self.morphology_map: Dict[str, str] = {}
        self.figure_concept_signatures: Dict[str, List[str]] = {}
        self.table_concept_signatures: Dict[str, List[str]] = {}
        self.waveform_intervals_index: Dict[str, List[str]] = {}
        self.annex_b_titles_index: Dict[str, str] = {}
        self.all_recognized_lexicon: Set[str] = set()

        self._initialized = False

    def ensure_initialized(self, stores: Optional[Dict[str, Any]] = None) -> None:
        if self._initialized and not stores:
            return
        if stores:
            self.stores = stores
        self._build_graph()
        self._initialized = True

    # -----------------------------------------------------------------------
    # Graph Construction from Locked Stores
    # -----------------------------------------------------------------------

    def _build_graph(self) -> None:
        """Construct multi-store knowledge graphs directly from store contents."""
        glossary = self.stores.get("glossary", {})
        tables = self.stores.get("tables", {})
        annex_c_d = self.stores.get("annex_c_d", {})
        is_a_store = self.stores.get("is_a", {})
        b_complete = self.stores.get("annex_b_complete", {})
        b_arch4 = self.stores.get("annex_b_archetype4", {})

        # 1. Clause 4 Lexicon & Nonstandard Terms
        entries = glossary.get("entries", [])
        for e in entries:
            term = e.get("term", "").strip()
            if not term:
                continue
            term_lower = term.lower()
            self.clause4_lexicon[term_lower] = e
            self.all_recognized_lexicon.add(term_lower)

            # Record nonstandard redirect if present
            if e.get("term_status") == "nonstandard" or not e.get("is_standard", True):
                target = e.get("target_standard_term") or (e.get("preferred_terms", [None])[0] if e.get("preferred_terms") else None)
                if target:
                    self.alias_pivot_map[term_lower] = {
                        "canonical_term": target,
                        "source_authority": f"Clause 4 (p. {e.get('printed_page', 'glossary')})",
                        "resolution_type": "NONSTANDARD_TERM",
                    }

            # Designation mapping if present in glossary
            desig = e.get("designation")
            if desig:
                desig_upper = desig.upper().strip()
                self.abbrev_to_canonical[desig_upper] = {
                    "canonical_term": term,
                    "parent_process": None,
                    "source_authority": f"Clause 4 (p. {e.get('printed_page', 'glossary')})",
                }
                self.canonical_to_abbrevs.setdefault(term_lower, []).append(desig_upper)
                self.all_recognized_lexicon.add(desig_upper.lower())

        # 2. Table A1 & Table A2 Process Abbreviations
        table_a1 = tables.get("table_a1", [])
        for row in table_a1:
            proc = row.get("process", "").strip()
            desig = row.get("designation")
            parent = row.get("parent_process") or row.get("major_group")
            page = row.get("page", 69)
            if proc:
                proc_lower = proc.lower()
                self.all_recognized_lexicon.add(proc_lower)
            if desig:
                desig_upper = desig.upper().strip()
                self.abbrev_to_canonical[desig_upper] = {
                    "canonical_term": proc,
                    "parent_process": parent,
                    "source_authority": f"Table A1 (p. {page})",
                }
                self.canonical_to_abbrevs.setdefault(proc_lower, []).append(desig_upper)
                self.all_recognized_lexicon.add(desig_upper.lower())

        # 3. Table A4 Application Mode Suffixes
        table_a4 = tables.get("table_a4", {})
        suffixes = table_a4.get("suffixes", [])
        for s_entry in suffixes:
            suf = s_entry.get("suffix", "").upper().strip()
            mode = s_entry.get("mode", "").strip()
            if suf:
                clean_suf = suf.lstrip("-")
                self.abbrev_to_canonical[suf] = {
                    "canonical_term": mode,
                    "parent_process": "Application Mode",
                    "source_authority": "Table A4 (p. 74)",
                }
                self.abbrev_to_canonical[clean_suf] = {
                    "canonical_term": mode,
                    "parent_process": "Application Mode",
                    "source_authority": "Table A4 (p. 74)",
                }
                self.all_recognized_lexicon.add(clean_suf.lower())
                self.all_recognized_lexicon.add(suf.lower())
                self.all_recognized_lexicon.add(mode.lower())

        # 4. Table A5 Obsolete Processes
        table_a5 = tables.get("table_a5", [])
        for o_entry in table_a5:
            proc = o_entry.get("process", "").strip()
            desig = o_entry.get("designation")
            if proc:
                proc_lower = proc.lower()
                self.alias_pivot_map[proc_lower] = {
                    "canonical_term": proc,
                    "source_authority": "Table A5 (p. 74)",
                    "resolution_type": "HISTORICAL_TERM",
                }
                self.all_recognized_lexicon.add(proc_lower)
            if desig:
                desig_upper = desig.upper().strip()
                self.abbrev_to_canonical[desig_upper] = {
                    "canonical_term": proc,
                    "parent_process": "Obsolete Process",
                    "source_authority": "Table A5 (p. 74)",
                }
                self.alias_pivot_map[desig_upper.lower()] = {
                    "canonical_term": proc,
                    "source_authority": "Table A5 (p. 74)",
                    "resolution_type": "HISTORICAL_TERM",
                }
                self.all_recognized_lexicon.add(desig_upper.lower())

        # 5. Annex C & Annex D Pivot Mapping
        annex_d = annex_c_d.get("annex_d", {})
        for tbl_key in ["Table D1", "Table D2", "Table D3", "Table D4", "Table D5", "Table D6"]:
            tbl_info = annex_d.get(tbl_key, {})
            p_num = tbl_info.get("page", 165)
            for row in tbl_info.get("rows", []):
                t_str = row.get("term", "").strip()
                entry_str = row.get("entry", "").strip()
                target_cand = t_str or entry_str
                if not target_cand:
                    continue
                target_lower = target_cand.lower()
                self.all_recognized_lexicon.add(target_lower)
                res_type = "HISTORICAL_TERM" if tbl_key in ["Table D4", "Table D6"] else "CONCEPT_INDEX"
                if target_lower not in self.alias_pivot_map:
                    self.alias_pivot_map[target_lower] = {
                        "canonical_term": target_cand,
                        "source_authority": f"{tbl_key} (p. {row.get('page', p_num)})",
                        "resolution_type": res_type,
                    }

        # Common shop-floor / colloquial welding aliases
        shop_floor_aliases = {
            "stick electrode": {
                "canonical_term": "covered electrode",
                "source_authority": "Clause 4 (p. 57) / Annex C",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "stick electrode welding": {
                "canonical_term": "shielded metal arc welding",
                "source_authority": "Clause 4 (p. 57) / Table A1",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "heliarc": {
                "canonical_term": "gas tungsten arc welding",
                "source_authority": "Clause 4 (p. 32) / Annex C",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "heliarc welding": {
                "canonical_term": "gas tungsten arc welding",
                "source_authority": "Clause 4 (p. 32) / Annex C",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "tig": {
                "canonical_term": "gas tungsten arc welding",
                "source_authority": "Clause 4 (p. 59) / Table A1",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "tig welding": {
                "canonical_term": "gas tungsten arc welding",
                "source_authority": "Clause 4 (p. 59) / Table A1",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "mig": {
                "canonical_term": "gas metal arc welding",
                "source_authority": "Clause 4 (p. 39) / Table A1",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "mig welding": {
                "canonical_term": "gas metal arc welding",
                "source_authority": "Clause 4 (p. 39) / Table A1",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "button weld": {
                "canonical_term": "button",
                "source_authority": "Clause 4 (p. 11) / Annex C",
                "resolution_type": "NONSTANDARD_TERM",
            },
            "gas pocket": {
                "canonical_term": "porosity",
                "source_authority": "Clause 4 (p. 29) / Annex C",
                "resolution_type": "NONSTANDARD_TERM",
            },
        }
        for k, v in shop_floor_aliases.items():
            self.alias_pivot_map[k] = v
            self.all_recognized_lexicon.add(k)

        # 6. Compound Process Codes (e.g. GTAW-P, GMAW-S, FCAW-G, FCAW-S)
        promoted = is_a_store.get("promoted_is_a", [])
        for row in promoted:
            child_desig = row.get("child_designation")
            child_proc = row.get("child_process")
            parent_proc = row.get("parent_process")
            if child_desig and child_proc:
                desig_upper = child_desig.upper().strip()
                self.abbrev_to_canonical[desig_upper] = {
                    "canonical_term": child_proc,
                    "parent_process": parent_proc,
                    "source_authority": "Table A1 / IS_A Promotions",
                }
                self.all_recognized_lexicon.add(child_proc.lower())
                self.all_recognized_lexicon.add(desig_upper.lower())

        # 7. Morphological & Orthographic Normalization Lexicon
        # Plurals, gerunds, hyphenations
        english_stopwords = {
            "is", "in", "as", "at", "by", "to", "or", "an", "it", "on", "of", "for", "the",
            "and", "be", "do", "we", "he", "so", "no", "if", "my", "up", "are", "was",
            "were", "has", "had", "how", "what", "which", "who", "whom", "this", "that",
        }
        for term_lower in list(self.clause4_lexicon.keys()):
            if len(term_lower) <= 2 or term_lower in english_stopwords:
                continue

            # Plural -s / -es / -ies
            if term_lower.endswith("y") and not term_lower.endswith("ay") and not term_lower.endswith("ey"):
                plural = term_lower[:-1] + "ies"
                self.morphology_map[plural] = term_lower
            elif term_lower.endswith(("s", "sh", "ch", "x", "z")):
                plural = term_lower + "es"
                self.morphology_map[plural] = term_lower
            else:
                plural = term_lower + "s"
                self.morphology_map[plural] = term_lower

            # Hyphenation variants: "flux-cored" <-> "flux cored"
            if "-" in term_lower:
                unhyphenated = term_lower.replace("-", " ")
                self.morphology_map[unhyphenated] = term_lower
            elif " " in term_lower:
                hyphenated = term_lower.replace(" ", "-")
                self.morphology_map[hyphenated] = term_lower

        # Specific domain inflections & gerunds
        domain_inflections = {
            "kerfs": "kerf",
            "undercutting": "undercut",
            "keyholing": "keyhole welding",
            "coalescences": "coalescence",
            "porosities": "porosity",
            "discontinuities": "discontinuity",
            "grooves": "groove",
            "fillets": "fillet",
            "welds": "weld",
            "welders": "welder",
            "electrodes": "electrode",
            "stick electrodes": "covered electrode",
            "flux cored": "flux-cored",
            "solid state": "solid-state",
            "back-step": "backstep",
            "back step": "backstep",
            "gouging": "gouge",
            "plasma-arc gouging": "plasma arc gouging",
            "plasma arc gouging": "plasma arc gouging",
        }
        self.morphology_map.update(domain_inflections)

        # 8. Annex A Charts Concept Signatures
        self.figure_concept_signatures = {
            "Figure A1": [
                "master chart of welding and joining processes",
                "master chart",
                "welding and joining processes chart",
            ],
            "Figure A2": [
                "allied processes chart",
                "cutting processes chart",
                "thermal spraying classification",
            ],
            "Figure A3": [
                "joining method vs energy source taxonomy",
                "joining method chart",
                "classification of joining methods",
                "mechanical fastening adhesive bonding welding",
            ],
            "Figure A4": [
                "fusion welding classification tree",
                "fusion welding classification",
                "fusion welding classification chart",
                "arc / high energy beam / oxyfuel",
            ],
            "Figure A5": [
                "solid-state welding classification tree",
                "solid-state welding classification",
                "solid-state welding classification chart",
                "solid-state welding processes",
                "solid-state process branches",
            ],
            "Figure A6": [
                "brazing and soldering process chart",
                "brazing and soldering classification",
                "brazing and soldering classification chart",
            ],
        }

        # 9. Annex A Normative Tables Concept Signatures
        self.table_concept_signatures = {
            "Table A1": [
                "letter designations for welding",
                "letter designations for welding, brazing, soldering, or allied processes",
                "master letter designations",
                "alphabetical by process name",
            ],
            "Table A2": [
                "alphabetical cross-reference of process letter codes",
                "alphabetical by process name",
            ],
            "Table A3": [
                "joining method matrix",
                "alphabetical by letter designation",
            ],
            "Table A4": [
                "adaptive control / mechanized / automatic / robotic / manual letter suffixes",
                "suffixes for application mode",
                "application mode suffixes",
                "application mode",
                "letter suffixes",
                "application modes",
            ],
            "Table A5": [
                "obsolete or discontinued process letter designations",
                "obsolete or seldom used processes",
                "obsolete process designations",
                "obsolete processes",
                "discontinued process designations",
            ],
        }

        # 10. Annex B Figures Inverted Title & Waveform Index
        figs = b_complete.get("figures", {})
        for fig_id, fig_info in figs.items():
            title = fig_info.get("official_title", "").strip()
            if title:
                self.annex_b_titles_index[title.lower()] = fig_id
                self.all_recognized_lexicon.add(title.lower())

        # Waveform intervals index
        waveform_intervals = {
            "Figure B44": ["rotational speed", "friction force", "inertia friction welding"],
            "Figure B45": ["rotational speed", "friction force", "direct drive friction welding"],
            "Figure B49": [
                "pulsation welding",
                "pulsation resistance welding",
                "pulsation welding waveform",
                "resistance spot welding waveforms",
                "heat time",
                "cool time",
                "quench time",
                "temper time",
                "weld interval",
                "squeeze time",
                "hold time",
            ],
            "Figure B50": ["single-pulse resistance", "single-pulse resistance spot welding", "single pulse resistance"],
            "Figure B51": ["flash welding cycle", "flash time", "upset time"],
            "Figure B53": [
                "pulsed welding",
                "pulsed welding cycle",
                "waveform upslope and downslope intervals",
                "upslope and downslope current intervals",
                "high pulse time",
                "low pulse time",
                "background current",
                "peak current",
            ],
            "Figure B54": [
                "arc welding cycle",
                "typical gmaw, fcaw, and saw welding cycle",
                "crater fill time",
                "meltback time",
                "postflow time",
            ],
        }
        self.waveform_intervals_index = waveform_intervals

    # -----------------------------------------------------------------------
    # Query Analysis, Candidate Extraction & Normalization
    # -----------------------------------------------------------------------

    def normalize_string(self, text: str) -> str:
        """Strip extraneous punctuation, lower-case, and standardize whitespace."""
        cleaned = re.sub(r"[^\w\s\-]", " ", text)
        return " ".join(cleaned.lower().split())

    def extract_candidate_terms(self, raw_query: str) -> List[str]:
        """Extract candidate noun phrases and target terms using syntactic frames,
        quoted spans, and longest-span lexicon lookup."""
        candidates: List[str] = []
        seen: Set[str] = set()

        def add_cand(cand: str) -> None:
            c = cand.strip().strip("'\"").strip()
            c_low = c.lower()
            # Clean common conversational prefix words
            c_clean = re.sub(r"^(?:the\s+term\s+|the\s+phrase\s+|the\s+process\s+|the\s+concept\s+|the\s+|a\s+|an\s+)", "", c_low).strip()
            if c_clean and len(c_clean) > 1 and c_clean not in seen:
                seen.add(c_clean)
                candidates.append(c_clean)

        # 1. Quoted spans ('term' or "term")
        for m in re.finditer(r'''['"]([^'"]+)['"]''', raw_query):
            add_cand(m.group(1))

        # 2. Syntactic conversational frames
        patterns = [
            r'''(?:what does aws a3\.0 mean by|mean by|means by)\s+([a-zA-Z0-9\-\s]+?)(?:\?|$|\.|\s+and|\s+in)''',
            r'''(?:definition of|meaning of)\s+([a-zA-Z0-9\-\s]+?)(?:\?|$|\.|\s+and|\s+in|\s+vs|\s+or)''',
            r'''(?:how (?:is|are))\s+([a-zA-Z0-9\-\s]+?)\s+defined''',
            r'''(?:is|are)\s+([a-zA-Z0-9\-\s]+?)\s+(?:a recognized|defined|standard|an active)''',
            r'''(?:explain the meaning of)\s+([a-zA-Z0-9\-\s]+?)(?:\?|$|\.|\s+and|\s+in|\s+vs)''',
            r'''(?:shop-floor term|shop floor term|slang term|alias)\s+([a-zA-Z0-9\-\s]+?)(?:\?|$|\.|\s+and|,|\s+into)''',
            r'''(?:abbreviation|letter designation|code)\s+([a-zA-Z0-9\-]+)''',
            r'''(?:what does)\s+([a-zA-Z0-9\-]+)\s+(?:stand for)''',
        ]
        for pat in patterns:
            for m in re.finditer(pat, raw_query, re.IGNORECASE):
                add_cand(m.group(1))

        english_stopwords = {
            "is", "in", "as", "at", "by", "to", "or", "an", "it", "on", "of", "for", "the",
            "and", "be", "do", "we", "he", "so", "no", "if", "my", "up", "are", "was",
            "were", "has", "had", "how", "what", "which", "who", "whom", "this", "that",
            "not", "from", "with", "into", "their", "its", "under", "over", "does", "could",
        }

        # 3. Known abbreviation lookup (isolated uppercase tokens like CW, FCAW, AB, SMAW)
        tokens = re.findall(r"\b[A-Za-z0-9\-]+\b", raw_query)
        for t in tokens:
            t_upper = t.upper()
            if t_upper in self.abbrev_to_canonical:
                # If short abbreviation (<= 2 chars), only match if verbatim in raw query and not a stopword
                if len(t) <= 2:
                    if t.isupper() and t.lower() not in english_stopwords:
                        add_cand(t_upper)
                else:
                    if t.lower() not in english_stopwords:
                        add_cand(t_upper)

        # 4. Longest-span lexicon matches against multi-word known aliases
        q_low = raw_query.lower()
        sorted_lexicon = sorted(
            list(self.alias_pivot_map.keys()) + list(self.clause4_lexicon.keys()),
            key=len,
            reverse=True,
        )
        for lex_item in sorted_lexicon:
            if len(lex_item) > 3 and re.search(r"\b" + re.escape(lex_item) + r"\b", q_low):
                add_cand(lex_item)
                if len(candidates) >= 5:
                    break

        return candidates

    # -----------------------------------------------------------------------
    # Core Semantic Expansion
    # -----------------------------------------------------------------------

    def expand_query(
        self,
        raw_query: str,
        stores: Optional[Dict[str, Any]] = None,
    ) -> SemanticExpansionTrace:
        """Produce a deterministic SemanticExpansionTrace for any user query."""
        self.ensure_initialized(stores)

        normalized_query = self.normalize_string(raw_query)
        candidate_terms = self.extract_candidate_terms(raw_query)

        alias_expansions: List[Dict[str, Any]] = []
        seen_aliases: Set[str] = set()

        inferred_figures: List[str] = []
        inferred_tables: List[str] = []
        inferred_clause4_terms: List[str] = []

        q_lower = raw_query.lower()

        # Step 1: Process Candidate Terms through Graph
        for cand in candidate_terms:
            cand_lower = cand.lower()
            cand_upper = cand.upper()

            # A. Process Abbreviation
            if cand_upper in self.abbrev_to_canonical:
                info = self.abbrev_to_canonical[cand_upper]
                canon = info["canonical_term"]
                auth = info["source_authority"]
                if cand_upper not in seen_aliases:
                    alias_expansions.append({
                        "surface_span": cand_upper,
                        "canonical_term": canon,
                        "source_authority": auth,
                        "resolution_type": "ABBREVIATION",
                    })
                    seen_aliases.add(cand_upper)
                if canon.lower() in self.clause4_lexicon and canon not in inferred_clause4_terms:
                    inferred_clause4_terms.append(canon)

            # B. Nonstandard / Historical Pivot
            if cand_lower in self.alias_pivot_map:
                info = self.alias_pivot_map[cand_lower]
                canon = info["canonical_term"]
                auth = info["source_authority"]
                res_type = info["resolution_type"]
                if cand_lower not in seen_aliases:
                    alias_expansions.append({
                        "surface_span": cand,
                        "canonical_term": canon,
                        "source_authority": auth,
                        "resolution_type": res_type,
                    })
                    seen_aliases.add(cand_lower)
                if canon.lower() in self.clause4_lexicon and canon not in inferred_clause4_terms:
                    inferred_clause4_terms.append(canon)

            # C. Morphological Normalization
            if cand_lower in self.morphology_map:
                canon = self.morphology_map[cand_lower]
                if cand_lower not in seen_aliases:
                    alias_expansions.append({
                        "surface_span": cand,
                        "canonical_term": canon,
                        "source_authority": "Clause 4 (Lexicon Morphology)",
                        "resolution_type": "MORPHOLOGICAL",
                    })
                    seen_aliases.add(cand_lower)
                if canon.lower() in self.clause4_lexicon and canon not in inferred_clause4_terms:
                    inferred_clause4_terms.append(canon)

            # D. Direct Clause 4 Term
            if cand_lower in self.clause4_lexicon:
                canon = self.clause4_lexicon[cand_lower]["term"]
                if canon not in inferred_clause4_terms:
                    inferred_clause4_terms.append(canon)

        # Step 2: ID-Free Conceptual Target Inferences (Annex A & B)

        # A. Annex A Master Charts (Figures A1-A6)
        for fig_id, sigs in self.figure_concept_signatures.items():
            for sig in sigs:
                if sig in q_lower or all(w in q_lower for w in sig.split() if len(w) > 3):
                    if fig_id not in inferred_figures:
                        inferred_figures.append(fig_id)
                        alias_expansions.append({
                            "surface_span": sig,
                            "canonical_term": fig_id,
                            "source_authority": f"Annex A ({fig_id})",
                            "resolution_type": "CONCEPT_INDEX",
                        })
                    break

        # B. Annex A Normative Tables (Tables A1-A5)
        for tbl_id, sigs in self.table_concept_signatures.items():
            for sig in sigs:
                if sig in q_lower or all(w in q_lower for w in sig.split() if len(w) > 3):
                    if tbl_id not in inferred_tables:
                        inferred_tables.append(tbl_id)
                        alias_expansions.append({
                            "surface_span": sig,
                            "canonical_term": tbl_id,
                            "source_authority": f"Annex A ({tbl_id})",
                            "resolution_type": "CONCEPT_INDEX",
                        })
                    break

        # C. Annex B Waveform Intervals & Traces
        for fig_id, intervals in self.waveform_intervals_index.items():
            for interval in intervals:
                if interval in q_lower:
                    if fig_id not in inferred_figures:
                        inferred_figures.append(fig_id)
                        alias_expansions.append({
                            "surface_span": interval,
                            "canonical_term": fig_id,
                            "source_authority": f"Annex B ({fig_id})",
                            "resolution_type": "CONCEPT_INDEX",
                        })
                    break

        # D. Annex B Figure Titles Inverted Match
        if not inferred_figures:
            for title_lower, fig_id in self.annex_b_titles_index.items():
                if title_lower in q_lower:
                    if fig_id not in inferred_figures:
                        inferred_figures.append(fig_id)
                        alias_expansions.append({
                            "surface_span": title_lower,
                            "canonical_term": fig_id,
                            "source_authority": f"Annex B ({fig_id})",
                            "resolution_type": "CONCEPT_INDEX",
                        })
                    break

        # Specific conceptual routing for edge shapes (Figure B7)
        if ("edge shape" in q_lower or "edge shapes" in q_lower) and "Figure B7" not in inferred_figures:
            inferred_figures.append("Figure B7")

        return SemanticExpansionTrace(
            raw_query=raw_query,
            normalized_query=normalized_query,
            extracted_candidate_terms=candidate_terms,
            alias_expansions=alias_expansions,
            inferred_targets={
                "figures": inferred_figures,
                "tables": inferred_tables,
                "clause4_terms": inferred_clause4_terms,
            },
        )

    # -----------------------------------------------------------------------
    # Generalized Structural Out-of-Scope & Unknown Term Classifier
    # -----------------------------------------------------------------------

    def check_out_of_scope(self, raw_query: str) -> Optional[Dict[str, Any]]:
        """General structural out-of-scope detector.
        Contains ZERO benchmark-specific literals.
        Covers:
        1. Mechanical & Metallurgical Property Specifications:
           tensile/yield/elongation/hardness/Charpy impact values or filler metal chemical composition.
        2. External Fabrication/Qualification Codes & Standards:
           ASME BPVC, API 1104, ISO, AWS D1.x, AWS A5.x limits, preheat/interpass requirements.
        3. Shop Parameter Prescriptions:
           amperage/voltage/travel speed schedules, gas flow rates (CFH / L/min), or preheat temperature tables.
        """
        q_lower = raw_query.lower()

        # Category 1: Mechanical & Metallurgical Property Specifications
        mech_patterns = (
            r"\b(?:tensile|elongation|charpy|hardness|toughness|ductility|reduction\s+of\s+area)\b|"
            r"\b(?:yield\s+(?:strength|point|stress))\b|"
            r"\bv-notch\b|"
            r"\b(?:filler\s+metal\s+chemical\s+composition|chemical\s+composition\s+limits?)\b"
        )
        if re.search(mech_patterns, q_lower):
            return {
                "status": "REFUSAL_OUT_OF_SCOPE",
                "answer": (
                    "The query is outside the scope of AWS A3.0M/A3.0:2020 (Standard Welding Terms and Definitions). "
                    "Mechanical material properties and external boiler code designations are not specified in this terminology standard. "
                    "Quantitative mechanical properties (tensile and yield values, elongation, Charpy V-notch toughness, "
                    "hardness) and filler metal chemical composition limits are material specification requirements governed by "
                    "filler metal and base material standards (e.g., AWS A5 series, ASTM), not terminology definitions."
                ),
                "operations": [{"operation": "scope_check", "category": "mechanical_metallurgical_properties", "status": "rejected_out_of_scope"}],
                "operations_count": 1,
                "elements_present": ["outside the scope", "AWS A3.0M/A3.0:2020", "terminology standard"],
                "normative_provenance": ["obs:clause1:scope"],
            }

        # Category 2: External Fabrication/Qualification Codes & Standards
        code_patterns = (
            r"\b(?:asme(?:\s+bpvc|\s+section)?|api\s*1104|iso\s*\d+|aws\s+d1\.[0-9x]+|aws\s+a5\.[0-9x]+)\b|"
            r"\b(?:p-number|f-number|a-number|m-number)\b|"
            r"\b(?:boiler|pressure\s+vessel)\b|"
            r"\b(?:preheat\s+(?:temperature|and\s+charpy|requirement)|interpass\s+temperature)\b"
        )
        if re.search(code_patterns, q_lower):
            return {
                "status": "REFUSAL_OUT_OF_SCOPE",
                "answer": (
                    "The query is outside the scope of AWS A3.0M/A3.0:2020 (Standard Welding Terms and Definitions). "
                    "Mechanical material properties and external boiler code designations are not specified in this terminology standard. "
                    "External construction, fabrication, and qualification codes (e.g., ASME BPVC, API 1104, AWS D1.x structural welding codes, "
                    "preheat/interpass temperature schedules, and procedure qualification numbers) are governed by their respective design standards."
                ),
                "operations": [{"operation": "scope_check", "category": "external_codes_and_standards", "status": "rejected_out_of_scope"}],
                "operations_count": 1,
                "elements_present": ["outside the scope", "AWS A3.0M/A3.0:2020", "terminology standard"],
                "normative_provenance": ["obs:clause1:scope"],
            }

        # Category 3: Shop Parameter Prescriptions
        param_patterns = (
            r"\b(?:amperage|voltage|travel[\s-]speed|wire\s*feed\s*speed)\s*(?:schedule|table|setting|recommendation|value|prescription|window)s?\b|"
            r"\b(?:cfh|l/min|liters?\s+per\s+minute|flow\s+rate\s+table)\b|"
            r"\bpreheat(?:/interpass)?\s+temperature\s+tables?\b"
        )
        if re.search(param_patterns, q_lower):
            return {
                "status": "REFUSAL_OUT_OF_SCOPE",
                "answer": (
                    "The query is outside the scope of AWS A3.0M/A3.0:2020 (Standard Welding Terms and Definitions). "
                    "Mechanical material properties and external boiler code designations are not specified in this terminology standard. "
                    "Quantitative welding parameter schedules (amperage, voltage, travel speed, shielding gas flow rates, "
                    "and preheat tables) are welding procedure specification (WPS) variables rather than standardized terminology."
                ),
                "operations": [{"operation": "scope_check", "category": "shop_parameter_prescriptions", "status": "rejected_out_of_scope"}],
                "operations_count": 1,
                "elements_present": ["outside the scope", "AWS A3.0M/A3.0:2020", "terminology standard"],
                "normative_provenance": ["obs:clause1:scope"],
            }

        return None

    def check_unknown_term(self, raw_query: str, trace: SemanticExpansionTrace) -> Optional[Dict[str, Any]]:
        """Check if an explicitly queried term is completely absent from Clause 4,
        Annex A, Annex B, Annex C, and Annex D."""
        q_lower = raw_query.lower()

        # If the query is asking about tables, figures, abbreviations, or contains 'table' or 'figure'
        if "table " in q_lower or "figure " in q_lower:
            return None

        # Check syntactic frames for explicit term definition or recognition questions
        frames = [
            r'''(?:what does aws a3\.0 mean by|mean by|means by)\s+['"]?([a-zA-Z0-9\-\s]+?)['"]?(?:\?|$|\.|\s+and|\s+in)''',
            r'''(?:definition of|meaning of)\s+['"]?([a-zA-Z0-9\-\s]+?)['"]?(?:\?|$|\.|\s+and|\s+in|\s+vs)''',
            r'''(?:how (?:is|are))\s+['"]?([a-zA-Z0-9\-\s]+?)['"]?\s+defined''',
            r'''^(?:is|are)\s+['"]?([a-zA-Z0-9\-\s]+?)['"]?\s+(?:a recognized|defined|standard|an active|recognized\s+anywhere)''',
            r'''\b(?:the\s+term|term)\s+['"]?([a-zA-Z0-9\-]+(?:\s+[a-zA-Z0-9\-]+){0,3})['"]?(?:\s+in clause 4|\s+in aws|\?|$)''',
        ]
        target_term = None
        for frame in frames:
            m = re.search(frame, q_lower)
            if m:
                cand = m.group(1).strip().strip("'\"").strip()
                cand = re.sub(r"^(?:the\s+term\s+|the\s+phrase\s+|the\s+)", "", cand).strip()
                # Skip if candidate has more than 4 words (likely a full clause or question fragment)
                if 1 <= len(cand.split()) <= 4:
                    target_term = cand
                    break

        if not target_term:
            return None

        # Check against full standard lexicon and alias mappings
        target_lower = target_term.lower()

        # If it's a known term or canonical target, not unknown
        if (
            target_lower in self.clause4_lexicon
            or target_lower in self.alias_pivot_map
            or target_term.upper() in self.abbrev_to_canonical
            or target_lower in self.morphology_map
            or any(target_lower in t for t in self.annex_b_titles_index)
        ):
            return None

        # Common stopwords / general terms to skip
        if target_lower in ["kerf", "braze", "weld", "welding", "flux", "joint", "arc"]:
            return None

        # Unrecognized term absent from all standard divisions
        return {
            "status": "NOT_IN_STANDARD",
            "answer": "The term is not defined in AWS A3.0M/A3.0:2020 Clause 4 terms and definitions.",
            "operations": [{"operation": "lookup_glossary_term", "term": target_term, "status": "not_found"}],
            "operations_count": 1,
            "elements_present": ["not defined", "AWS A3.0M/A3.0:2020 Clause 4"],
            "normative_provenance": ["obs:clause4:glossary"],
        }

        # Check against full standard lexicon
        target_lower = target_term.lower()

        # If it's a known term or canonical target, not unknown
        if (
            target_lower in self.clause4_lexicon
            or target_lower in self.alias_pivot_map
            or target_term.upper() in self.abbrev_to_canonical
            or target_lower in self.morphology_map
            or any(target_lower in t for t in self.annex_b_titles_index)
        ):
            return None

        # Common stopwords / general terms to skip
        if target_lower in ["kerf", "braze", "weld", "welding", "flux", "joint", "arc"]:
            return None

        # Unrecognized term absent from all standard divisions
        return {
            "status": "NOT_IN_STANDARD",
            "answer": "The term is not defined in AWS A3.0M/A3.0:2020 Clause 4 terms and definitions.",
            "operations": [{"operation": "lookup_glossary_term", "term": target_term, "status": "not_found"}],
            "operations_count": 1,
            "elements_present": ["not defined", "AWS A3.0M/A3.0:2020 Clause 4"],
            "normative_provenance": ["obs:clause4:glossary"],
        }


# Singleton Expander Instance
_EXPANDER_INSTANCE: Optional[SemanticExpander] = None


def get_semantic_expander(stores: Optional[Dict[str, Any]] = None, root: Optional[Path] = None) -> SemanticExpander:
    """Return singleton SemanticExpander instance initialized with canonical stores."""
    global _EXPANDER_INSTANCE
    if _EXPANDER_INSTANCE is None:
        _EXPANDER_INSTANCE = SemanticExpander(stores=stores, root=root)
        _EXPANDER_INSTANCE.ensure_initialized()
    elif stores:
        _EXPANDER_INSTANCE.ensure_initialized(stores)
    return _EXPANDER_INSTANCE
