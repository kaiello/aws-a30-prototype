"""
epistemic_verifier.py: Epistemic Provenance Verification Engine
Verifies that claims and concepts asserted in an answer are strictly grounded
through explicit bridges to the Normative Evidence Layer in the Dual-Layer Graph.
"""

import re
import sqlite3
from typing import Dict, Any, List
from pathlib import Path

from src.config import STORAGE_DIR
from src.citation_checker import check_abstention, extract_citations

DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"

def verify_epistemic_provenance(query: str, answer: str) -> Dict[str, Any]:
    """
    Evaluates candidate query answer against the Dual-Layer Epistemic Graph.
    Verifies that all technical concepts trace to valid Evidence nodes.
    """
    # 1. Check if the model abstained
    if check_abstention(answer):
        return {
            "provenance_score": 1.0,
            "epistemic_status": "TRUTHFUL_ABSTENTION",
            "is_abstention": True,
            "concepts_verified": [],
            "unverified_concepts": [],
            "evidence_summary": {
                "figures": [],
                "clauses": [],
                "tables": []
            },
            "manifest_summary": "Query appropriately abstained; no ungrounded technical claims asserted."
        }

    if not DUAL_SQLITE_PATH.exists():
        return {
            "provenance_score": 0.5,
            "epistemic_status": "UNVERIFIED_DATABASE_MISSING",
            "is_abstention": False,
            "concepts_verified": [],
            "unverified_concepts": []
        }

    conn = sqlite3.connect(DUAL_SQLITE_PATH)
    cur = conn.cursor()

    # 2. Extract technical candidate entities from answer
    # Fetch all ontology concepts mentioned in the text
    cur.execute("SELECT id, name, node_type, standard_status FROM ontology_nodes")
    all_ontology = cur.fetchall()

    lowered_answer = answer.lower()
    matched_concepts = []

    for onto_id, name, node_type, status in all_ontology:
        # Ignore very short or ubiquitous single-word concepts to prevent false positives
        if len(name) < 4 and name.upper() not in ["GTAW", "GMAW", "SMAW", "SAW", "FCAW", "PAW", "ESW", "EGW", "OAW", "OFW", "TB", "FB", "DB", "IB", "1G", "2G", "3G", "4G", "5G", "6G", "6GR", "1F", "2F", "3F", "4F", "5F"]:
            continue
        
        # Word boundary search
        pattern = r'\b' + re.escape(name.lower()) + r'\b'
        if re.search(pattern, lowered_answer):
            matched_concepts.append((onto_id, name, node_type, status))

    # Deduplicate and sort by length descending (prefer specific phrases over single words)
    matched_concepts = sorted(matched_concepts, key=lambda x: len(x[1]), reverse=True)
    selected_concepts = []
    seen_spans = set()
    for item in matched_concepts:
        if item[1].lower() not in seen_spans:
            selected_concepts.append(item)
            seen_spans.add(item[1].lower())

    # Limit to top 15 most prominent technical concepts
    selected_concepts = selected_concepts[:15]

    verified_list = []
    unverified_list = []
    figures_seen = set()
    tables_seen = set()
    clauses_seen = set()

    for onto_id, name, node_type, status in selected_concepts:
        cur.execute("""
            SELECT g.rel_type, g.bridge_type, e.node_type, e.name, e.page, e.image_file
            FROM grounding_bridges g
            JOIN evidence_nodes e ON g.evidence_id = e.id
            WHERE g.ontology_id = ?
        """, (onto_id,))
        bridges = cur.fetchall()

        if bridges:
            ev_items = []
            for rel, btype, enode_type, ename, epage, eimg in bridges:
                ev_items.append({
                    "relation": rel,
                    "bridge_type": btype,
                    "evidence_type": enode_type,
                    "name": ename,
                    "page": epage,
                    "image_file": eimg
                })
                if enode_type == "Figure":
                    fig_match = re.search(r'Figure\s+[AB]\d+[A-Z]?', ename)
                    if fig_match:
                        figures_seen.add(fig_match.group(0))
                elif enode_type == "Table":
                    tbl_match = re.search(r'Table\s+[AD]\d+', ename)
                    if tbl_match:
                        tables_seen.add(tbl_match.group(0))
                elif "clause" in ename.lower() or "annex" in ename.lower():
                    clauses_seen.add(ename)

            verified_list.append({
                "concept": name,
                "node_type": node_type,
                "standard_status": status,
                "evidence_count": len(ev_items),
                "primary_evidence": ev_items[:4]
            })
        else:
            unverified_list.append({
                "concept": name,
                "node_type": node_type,
                "standard_status": status
            })

    conn.close()

    total_checked = len(verified_list) + len(unverified_list)
    score = (len(verified_list) / total_checked) if total_checked > 0 else 1.0

    # Also incorporate direct regex citations from citation_checker
    citations = extract_citations(answer)
    for f in citations.get("figures", []):
        figures_seen.add(f)
    for t in citations.get("tables", []):
        tables_seen.add(t)
    for c in citations.get("clauses", []):
        clauses_seen.add(c)

    status_str = "VERIFIED_GROUNDED" if score >= 0.8 else ("PARTIALLY_GROUNDED" if score >= 0.5 else "UNGROUNDED")

    return {
        "provenance_score": round(score, 3),
        "epistemic_status": status_str,
        "is_abstention": False,
        "total_concepts_evaluated": total_checked,
        "concepts_verified": verified_list,
        "unverified_concepts": unverified_list,
        "evidence_summary": {
            "figures": sorted(list(figures_seen)),
            "tables": sorted(list(tables_seen)),
            "clauses": sorted(list(clauses_seen))
        },
        "manifest_summary": f"{len(verified_list)}/{total_checked} technical concepts anchored with explicit normative evidence bridges."
    }

if __name__ == "__main__":
    test_q = "Define actual throat and explain how it differs from theoretical throat in a fillet weld"
    test_ans = "Actual throat is the shortest distance between the weld root and the face of a fillet weld, as illustrated in Figure B25. In contrast, theoretical throat excludes convexity."
    res = verify_epistemic_provenance(test_q, test_ans)
    import pprint
    pprint.pprint(res)
