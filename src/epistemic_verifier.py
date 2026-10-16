"""
epistemic_verifier.py: Graph-link navigation and explicit answer assessment.
Stored bridges establish navigation links, not entailment of generated claims.
"""

import hashlib
import re
import sqlite3
from typing import Dict, Any, List
from pathlib import Path

from src.config import STORAGE_DIR
from src.citation_checker import check_abstention, extract_citations

DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"


def _decision_status(answer, decision):
    """Accept only an internal, validated decision bound to this exact answer.

    The caller owns source/fact or scope-policy validation. This function does
    not turn answer wording, graph links or citation identity into that review.
    """
    scopes = {"SUPPORTED_REVIEWED_FACTS": "reviewed_fact_bindings",
              "TRUTHFUL_ABSTENTION": "deterministic_scope_policy"}
    if not isinstance(decision, dict) or decision.get("validated") is not True:
        return None
    status = decision.get("status")
    if not isinstance(status, str) or status not in scopes:
        return None
    if decision.get("assessment_scope") != scopes[status] or not isinstance(answer, str):
        return None
    digest = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    return status if decision.get("answer_sha256") == digest else None


def verify_epistemic_provenance(query: str, answer: str, *, decision=None) -> Dict[str, Any]:
    """
    Report stored evidence links separately from reviewed answer support.

    ``concepts_verified`` is retained as a legacy navigation key: its members
    have graph links, not independently verified claims. Numeric coverage uses
    only matched concepts and is not evidence recall or an answer truth score.
    """
    assessed_status = _decision_status(answer, decision)
    trace = {
        "provenance_score": None,
        "graph_link_coverage": None,
        "epistemic_status": assessed_status or "UNASSESSED",
        "assessment_status": assessed_status or "UNASSESSED",
        "assessment_scope": decision["assessment_scope"] if assessed_status else None,
        "is_abstention": assessed_status == "TRUTHFUL_ABSTENTION",
        "abstention_phrase_detected": False,
        "total_concepts_evaluated": 0,
        "concepts_verified": [],
        "unverified_concepts": [],
        "evidence_summary": {"figures": [], "clauses": [], "tables": []},
        "unresolved_elements": [],
        "manifest_summary": "Answer support has not been assessed."
    }
    if assessed_status:
        trace["manifest_summary"] = "An explicit validated decision applies to this exact answer; graph coverage was not measured."
        return trace

    # A phrase is diagnostic only, including mixed refusal/assertion answers.
    trace["abstention_phrase_detected"] = bool(check_abstention(answer))

    if not DUAL_SQLITE_PATH.exists():
        trace["epistemic_status"] = "INSUFFICIENT_EVIDENCE"
        trace["manifest_summary"] = "Graph navigation database missing; answer support is unassessed."
        return trace

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
    coverage = (len(verified_list) / total_checked) if total_checked > 0 else None

    # Also incorporate direct regex citations from citation_checker
    citations = extract_citations(answer)
    for f in citations.get("figures", []):
        figures_seen.add(f)
    for t in citations.get("tables", []):
        tables_seen.add(t)
    for c in citations.get("clauses", []):
        clauses_seen.add(c)

    unresolved = citations.get("unresolved_elements", [])
    status_str = "INSUFFICIENT_EVIDENCE" if unresolved else "EVIDENCE_LINKS_FOUND" if verified_list else "UNASSESSED"
    trace.update({
        "graph_link_coverage": round(coverage, 3) if coverage is not None else None,
        "epistemic_status": status_str,
        "total_concepts_evaluated": total_checked,
        "concepts_verified": verified_list,
        "unverified_concepts": unverified_list,
        "evidence_summary": {
            "figures": sorted(list(figures_seen)),
            "tables": sorted(list(tables_seen)),
            "clauses": sorted(list(clauses_seen))
        },
        "unresolved_elements": unresolved,
        "manifest_summary": f"{len(verified_list)}/{total_checked} matched concepts have stored evidence links; claim support is unassessed."
    })
    return trace

if __name__ == "__main__":
    test_q = "Define actual throat and explain how it differs from theoretical throat in a fillet weld"
    test_ans = "Actual throat is the shortest distance between the weld root and the face of a fillet weld, as illustrated in Figure B25. In contrast, theoretical throat excludes convexity."
    res = verify_epistemic_provenance(test_q, test_ans)
    import pprint
    pprint.pprint(res)
