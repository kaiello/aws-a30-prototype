"""
answer_routes.py: Answer Route Bundler and Contextual Evidence Resolver.

Adopts Perplexity Research & Turbopuffer's "Beyond the Gold Passage" paradigm:
Resolves a full Answer Route = (Primary Answer Chunk + Supporting Evidence Group)
using the Dual-Layer Epistemic Knowledge Graph.

Retrieves not only the isolated definition chunk, but all supporting figures,
callout chips, table classification matrices, committee style rules, and revision records
required to verify and understand the answer.
"""

import os
import sys
import re
import json
import sqlite3
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import (
    STORAGE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR
)
from src.citation_checker import check_abstention, extract_citations
from src.figure_inspectors import FIGURE_INSPECTORS

DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"

@dataclass
class EvidenceItem:
    evidence_type: str  # "figure", "callout", "table", "clause", "rationale", "chunk"
    element_id: str     # e.g., "Figure B20", "Table A1", "Clause 4, p. 6", "Annex C1.5.7"
    title: str
    page: Optional[str] = None
    file_path: Optional[str] = None
    callout_chips: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnswerRoute:
    query: str
    status: str  # "VERIFIED_GROUNDED", "TRUTHFUL_ABSTENTION", "PARTIALLY_GROUNDED"
    concept_id: Optional[str] = None
    concept_name: Optional[str] = None
    concept_type: Optional[str] = None
    standard_status: Optional[str] = None
    primary_answer: Optional[str] = None
    primary_citation: Optional[str] = None
    evidence_group: List[EvidenceItem] = field(default_factory=list)
    evidence_recall_score: float = 1.0
    all_evidence_recovered: bool = True
    epistemic_score: float = 1.0
    manifest_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

def _clean_term_for_fts(term: str) -> str:
    # Remove symbols that break SQLite FTS syntax
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', term)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    if not tokens:
        return ""
    # Return FTS phrase or AND query
    return " OR ".join(f'"{t}"' for t in tokens if len(t) > 2)

def resolve_answer_route(query: str, candidate_answer: str = "") -> AnswerRoute:
    """
    Given a user query and optional candidate answer, resolves the full Answer Route
    by finding the primary concept and traversing epistemic grounding bridges to assemble
    the complete evidence group.
    """
    # 1. Clean abstention handling for out-of-scope negative controls
    text_to_check = candidate_answer or query
    if candidate_answer and check_abstention(candidate_answer):
        return AnswerRoute(
            query=query,
            status="TRUTHFUL_ABSTENTION",
            concept_id="none",
            concept_name="Out-of-Scope Control",
            concept_type="Abstention",
            standard_status="n/a",
            primary_answer=candidate_answer,
            primary_citation="Out-of-Scope (Governed by external fabrication/material code)",
            evidence_group=[],
            evidence_recall_score=1.0,
            all_evidence_recovered=True,
            epistemic_score=1.0,
            manifest_summary="Truthful abstention: Query asks for requirements beyond AWS A3.0M/A3.0:2020 jurisdiction."
        )

    if not DUAL_SQLITE_PATH.exists():
        return AnswerRoute(
            query=query,
            status="PARTIALLY_GROUNDED",
            primary_answer=candidate_answer or "Database not found.",
            manifest_summary="SQLite registry database missing."
        )

    conn = sqlite3.connect(DUAL_SQLITE_PATH)
    cur = conn.cursor()

    # 2. Identify candidate concepts from query and answer
    # Check exact concept matches in SQLite
    combined_text = f"{query} {candidate_answer}".lower()
    
    cur.execute("SELECT id, name, node_type, standard_status, description FROM ontology_nodes")
    all_nodes = cur.fetchall()

    matched_nodes = []
    for nid, name, ntype, status, desc in all_nodes:
        # Check if name is in text
        if len(name) < 4 and name.upper() not in [
            "1G", "2G", "3G", "4G", "5G", "6G", "6GR", "1F", "2F", "3F", "4F", "5F",
            "GTAW", "GMAW", "SMAW", "SAW", "FCAW", "PAW", "ESW", "EGW", "OAW", "OFW", "TB", "FB", "DB", "IB", "FSW"
        ]:
            continue
        pattern = r'\b' + re.escape(name.lower()) + r'\b'
        if re.search(pattern, combined_text):
            matched_nodes.append((nid, name, ntype, status, desc))

    # Prefer matches in query, then longest match
    def score_match(node):
        nid, name, ntype, status, desc = node
        in_query = 100 if name.lower() in query.lower() else 0
        return in_query + len(name)

    matched_nodes.sort(key=score_match, reverse=True)
    primary_node = matched_nodes[0] if matched_nodes else None

    # Fallback to FTS if no exact regex match
    if not primary_node:
        fts_query = _clean_term_for_fts(query)
        if fts_query:
            try:
                cur.execute(
                    "SELECT id, name, node_type, standard_status, description FROM ontology_nodes WHERE id IN (SELECT id FROM ontology_fts WHERE ontology_fts MATCH ? LIMIT 1)",
                    (fts_query,)
                )
                row = cur.fetchone()
                if row:
                    primary_node = row
            except sqlite3.OperationalError:
                pass

    if not primary_node:
        conn.close()
        # Non-matched general question
        return AnswerRoute(
            query=query,
            status="PARTIALLY_GROUNDED",
            primary_answer=candidate_answer,
            epistemic_score=0.7,
            manifest_summary="No specific ontology concept identified; general document match."
        )

    concept_id, concept_name, concept_type, standard_status, description = primary_node

    # 3. Traverse Epistemic Grounding Bridges
    # Find all evidence nodes connected to the primary concept (and closely related concepts)
    concept_ids_to_expand = [concept_id]
    if len(matched_nodes) > 1:
        concept_ids_to_expand.extend([m[0] for m in matched_nodes[1:3]])

    placeholders = ",".join("?" for _ in concept_ids_to_expand)
    cur.execute(f"""
        SELECT g.rel_type, g.bridge_type, e.id, e.node_type, e.name, e.page, e.image_file, e.preview
        FROM grounding_bridges g
        JOIN evidence_nodes e ON g.evidence_id = e.id
        WHERE g.ontology_id IN ({placeholders})
    """, concept_ids_to_expand)
    bridge_rows = cur.fetchall()

    evidence_items: List[EvidenceItem] = []
    seen_evidence_ids = set()

    for rel_type, bridge_type, eid, enode_type, ename, epage, eimg, eprev in bridge_rows:
        if eid in seen_evidence_ids:
            continue
        seen_evidence_ids.add(eid)

        # Figure Evidence
        if enode_type == "Figure":
            fig_match = re.search(r'Figure\s+([AB]\d+[A-Z]?)', ename, re.IGNORECASE)
            fig_key = fig_match.group(0).upper() if fig_match else ename
            
            # Resolve image file
            clean_fig_code = fig_key.replace("Figure ", "").upper()
            matching_pngs = list(PARSED_FIGURES_DIR.glob(f"Figure_{clean_fig_code}_*.png"))
            img_path = str(matching_pngs[0]) if matching_pngs else (eimg or "")

            # Resolve Callout Chips from registry
            callout_chips = []
            if fig_key in FIGURE_INSPECTORS:
                for grp in FIGURE_INSPECTORS[fig_key].get("groups", []):
                    callout_chips.extend(grp.get("chips", []))

            evidence_items.append(EvidenceItem(
                evidence_type="figure",
                element_id=fig_key,
                title=ename,
                page=epage,
                file_path=img_path,
                callout_chips=callout_chips,
                metadata={"bridge_type": bridge_type or rel_type}
            ))

        # Table Evidence
        elif enode_type == "Table":
            tbl_match = re.search(r'Table\s+([AD]\d+)', ename, re.IGNORECASE)
            tbl_key = tbl_match.group(0).upper() if tbl_match else ename
            clean_tbl_code = tbl_key.replace("Table ", "").lower()
            md_path = str(PARSED_TABLES_DIR / f"table_{clean_tbl_code}.md")
            
            evidence_items.append(EvidenceItem(
                evidence_type="table",
                element_id=tbl_key,
                title=ename,
                page=epage,
                file_path=md_path if os.path.exists(md_path) else None,
                metadata={"bridge_type": bridge_type or rel_type}
            ))

        # Clause / Text Chunk Evidence
        elif enode_type in ["TextChunk", "Clause"]:
            evidence_items.append(EvidenceItem(
                evidence_type="clause",
                element_id=eid,
                title=ename,
                page=epage,
                metadata={"preview": eprev, "bridge_type": bridge_type or rel_type}
            ))

    # Also resolve any directly cited figures/tables from candidate answer if not already in graph
    citations = extract_citations(candidate_answer)
    for fig_cite in citations.get("figures", []):
        if fig_cite not in [ev.element_id for ev in evidence_items]:
            clean_fig = fig_cite.replace("Figure ", "").upper()
            matching_pngs = list(PARSED_FIGURES_DIR.glob(f"Figure_{clean_fig}_*.png"))
            chips = []
            if fig_cite in FIGURE_INSPECTORS:
                for grp in FIGURE_INSPECTORS[fig_cite].get("groups", []):
                    chips.extend(grp.get("chips", []))
            evidence_items.append(EvidenceItem(
                evidence_type="figure",
                element_id=fig_cite,
                title=f"{fig_cite} (Cited in Answer)",
                file_path=str(matching_pngs[0]) if matching_pngs else None,
                callout_chips=chips
            ))

    for tbl_cite in citations.get("tables", []):
        if tbl_cite not in [ev.element_id for ev in evidence_items]:
            clean_tbl = tbl_cite.replace("Table ", "").lower()
            md_path = str(PARSED_TABLES_DIR / f"table_{clean_tbl}.md")
            evidence_items.append(EvidenceItem(
                evidence_type="table",
                element_id=tbl_cite,
                title=f"{tbl_cite} (Cited in Answer)",
                file_path=md_path if os.path.exists(md_path) else None
            ))

    conn.close()

    # 4. Determine Primary Citation & Answer
    primary_cite = "Clause 4"
    for ev in evidence_items:
        if ev.evidence_type == "clause" and "clause" in ev.title.lower():
            primary_cite = ev.title
            break

    # 5. Compute Evidence Sufficiency & Recall
    # Check what the query asked for:
    needs_figure = any(k in query.lower() for k in ["diagram", "figure", "show", "orient", "illustrat", "drawing"])
    needs_table = any(k in query.lower() for k in ["table", "letter designation", "process chart", "summary", "group"])
    
    has_figure = any(ev.evidence_type == "figure" for ev in evidence_items)
    has_table = any(ev.evidence_type == "table" for ev in evidence_items)
    has_clause = any(ev.evidence_type == "clause" for ev in evidence_items)

    requirements_met = 1.0
    if needs_figure and not has_figure:
        requirements_met *= 0.5
    if needs_table and not has_table:
        requirements_met *= 0.5

    all_recovered = (not needs_figure or has_figure) and (not needs_table or has_table) and len(evidence_items) > 0
    epistemic_score = 1.0 if all_recovered else (0.8 if len(evidence_items) > 0 else 0.5)

    manifest = f"Resolved Answer Route for '{concept_name}' ({concept_type}): {len(evidence_items)} supporting evidence items recovered."

    return AnswerRoute(
        query=query,
        status="VERIFIED_GROUNDED" if epistemic_score >= 0.8 else "PARTIALLY_GROUNDED",
        concept_id=concept_id,
        concept_name=concept_name,
        concept_type=concept_type,
        standard_status=standard_status,
        primary_answer=candidate_answer or description,
        primary_citation=primary_cite,
        evidence_group=evidence_items,
        evidence_recall_score=round(requirements_met, 3),
        all_evidence_recovered=all_recovered,
        epistemic_score=round(epistemic_score, 3),
        manifest_summary=manifest
    )

if __name__ == "__main__":
    q = "What is a 1F pipe position and show its diagram?"
    ans = "1F pipe position is a welding test position for a circumferential groove weld applied to pipe in which the pipe is inclined 45 deg, illustrated in Figure B20."
    route = resolve_answer_route(q, ans)
    print("Resolved Answer Route:")
    print("Status:", route.status)
    print("Concept:", route.concept_name, f"({route.concept_type})")
    print("Evidence Items:", len(route.evidence_group))
    for ev in route.evidence_group:
        print(f" - [{ev.evidence_type.upper()}] {ev.element_id}: {ev.title} (Chips: {len(ev.callout_chips)})")
