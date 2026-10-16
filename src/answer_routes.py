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
from src.citation_checker import extract_citations
from src.figure_inspectors import FIGURE_INSPECTORS
from src.standard_manifest import get_manifest
from src.epistemic_verifier import _decision_status

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
    status: str  # Navigation state, or an explicit validated assessment decision.
    concept_id: Optional[str] = None
    concept_name: Optional[str] = None
    concept_type: Optional[str] = None
    standard_status: Optional[str] = None
    primary_answer: Optional[str] = None
    primary_citation: Optional[str] = None
    evidence_group: List[EvidenceItem] = field(default_factory=list)
    evidence_recall_score: Optional[float] = None
    all_evidence_recovered: bool = False
    epistemic_score: Optional[float] = None
    manifest_summary: str = ""
    assessment_status: str = "UNASSESSED"
    assessment_scope: Optional[str] = None
    graph_link_coverage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

def _apply_source_metadata(item):
    """Overlay source locations without changing retrieved candidates or scores."""
    manifest = get_manifest()
    record = manifest.element(item.element_id)
    if not record:
        item.metadata["source_location_verification"] = "legacy_unverified"
        if item.evidence_type in {"figure", "table"}:
            item.page = None
            item.file_path = None
            item.metadata["source_resolution"] = manifest.resolve(item.element_id)
        return
    label = record["label"]
    if item.evidence_type in {"figure", "table"}:
        item.element_id = label
        item.title = record["title"]
        paths = manifest.asset_paths(label, {".png"} if item.evidence_type == "figure" else {".md"})
        item.file_path = paths[0] if paths else None
        binding = next((a for a in record["assets"] if str(manifest.root / a["relpath"]) == item.file_path), None)
        item.metadata["asset_binding_verification"] = binding["verification"]["state"] if binding else "unavailable"
        if item.evidence_type == "figure":
            item.callout_chips = [chip for group in FIGURE_INSPECTORS.get(label, {}).get("groups", []) for chip in group.get("chips", [])]
    item.page = manifest.page_range(label)
    item.metadata["source_anchors"] = manifest.source_anchors(label)
    item.metadata["source_location_verification"] = "verified"


def _clean_term_for_fts(term: str) -> str:
    # Remove symbols that break SQLite FTS syntax
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', term)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    if not tokens:
        return ""
    # Return FTS phrase or AND query
    return " OR ".join(f'"{t}"' for t in tokens if len(t) > 2)

def resolve_answer_route(query: str, candidate_answer: str = "", *, decision=None) -> AnswerRoute:
    """
    Find navigation evidence for matched concepts without certifying claims.

    Recall and answer support are unmeasured here. Only an explicit validated
    decision bound to this exact answer supplies an assessed outcome.
    """
    assessed_status = _decision_status(candidate_answer, decision)
    if assessed_status:
        return AnswerRoute(
            query=query,
            status=assessed_status,
            primary_answer=candidate_answer,
            assessment_status=assessed_status,
            assessment_scope=decision["assessment_scope"],
            manifest_summary="An explicit validated decision applies to this exact answer; evidence recall was not measured."
        )

    if not DUAL_SQLITE_PATH.exists():
        return AnswerRoute(
            query=query,
            status="INSUFFICIENT_EVIDENCE",
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
            status="INSUFFICIENT_EVIDENCE",
            primary_answer=candidate_answer,
            manifest_summary="No specific ontology concept identified; answer support is unassessed."
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
            fig_match = re.search(r'(?<!\w)Figure\s+([A-Za-z0-9][\w./-]*)', ename, re.IGNORECASE)
            fig_key = fig_match.group(0).rstrip(".") if fig_match else ename

            evidence_items.append(EvidenceItem(
                evidence_type="figure",
                element_id=fig_key,
                title=ename,
                page=epage,
                metadata={"bridge_type": bridge_type or rel_type}
            ))

        # Table Evidence
        elif enode_type == "Table":
            tbl_match = re.search(r'(?<!\w)Table\s+([A-Za-z0-9][\w./-]*)', ename, re.IGNORECASE)
            tbl_key = tbl_match.group(0).rstrip(".") if tbl_match else ename
            
            evidence_items.append(EvidenceItem(
                evidence_type="table",
                element_id=tbl_key,
                title=ename,
                page=epage,
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
            evidence_items.append(EvidenceItem(
                evidence_type="figure",
                element_id=fig_cite,
                title=f"{fig_cite} (Cited in Answer)"
            ))

    for tbl_cite in citations.get("tables", []):
        if tbl_cite not in [ev.element_id for ev in evidence_items]:
            evidence_items.append(EvidenceItem(
                evidence_type="table",
                element_id=tbl_cite,
                title=f"{tbl_cite} (Cited in Answer)"
            ))

    conn.close()

    # Persisted graph pages/assets are hints, never source-location authority.
    for evidence_item in evidence_items:
        _apply_source_metadata(evidence_item)

    # 4. Determine Primary Citation & Answer
    primary_cite = "Clause 4"
    for ev in evidence_items:
        if ev.evidence_type == "clause" and "clause" in ev.title.lower():
            primary_cite = ev.title
            break

    # 5. Report navigation availability, not measured recall or claim support.
    needs_figure = any(k in query.lower() for k in ["diagram", "figure", "show", "orient", "illustrat", "drawing"])
    needs_table = any(k in query.lower() for k in ["table", "letter designation", "process chart", "summary", "group"])
    
    has_figure = any(ev.evidence_type == "figure" and ev.metadata.get("source_location_verification") == "verified" for ev in evidence_items)
    has_table = any(ev.evidence_type == "table" and ev.metadata.get("source_location_verification") == "verified" for ev in evidence_items)
    unresolved_source = bool(citations.get("unresolved_elements")) or any(
        ev.evidence_type in {"figure", "table"} and ev.metadata.get("source_location_verification") != "verified"
        for ev in evidence_items)

    navigation_available = (bool(evidence_items) and not unresolved_source
                            and (not needs_figure or has_figure)
                            and (not needs_table or has_table))
    manifest = (f"Graph navigation for '{concept_name}' ({concept_type}): {len(evidence_items)} evidence links. "
                "Claim support is unassessed; evidence recall was not measured.")

    return AnswerRoute(
        query=query,
        status="EVIDENCE_LINKS_FOUND" if navigation_available else "INSUFFICIENT_EVIDENCE",
        concept_id=concept_id,
        concept_name=concept_name,
        concept_type=concept_type,
        standard_status=standard_status,
        primary_answer=candidate_answer or description,
        primary_citation=primary_cite,
        evidence_group=evidence_items,
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
