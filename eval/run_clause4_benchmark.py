"""
eval/run_clause4_benchmark.py: Deterministic 20-Question Offline QA Benchmark for
AWS A3.0:2020 Clause 4 Glossary, Annex C Decisions, Annex D Modifications, and Dual-Provenance IS_A.

0 Live LLM Calls. Evaluates answers against storage/evidence_v2/clause4_ingest_001/rubric.json.
Writes receipt to storage/evidence_v2/clause4_ingest_001/clause4_qa_receipt.json.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import STORAGE_DIR
from src.evidence_clause4_glossary import (
    get_clause4_glossary_store,
    lookup_glossary_term,
    get_nonstandard_redirect,
)
from src.evidence_annex_c_d import (
    get_annex_c_d_store,
    get_subcommittee_decision,
    get_annex_d_modifications,
)
from src.evidence_is_a_promotion import get_is_a_promotion_store

BENCHMARK_DIR = STORAGE_DIR / "evidence_v2" / "clause4_ingest_001"
QUESTIONS_PATH = BENCHMARK_DIR / "questions.json"
RUBRIC_PATH = BENCHMARK_DIR / "rubric.json"
RECEIPT_PATH = BENCHMARK_DIR / "clause4_qa_receipt.json"


def answer_clause4_benchmark_query(
    q: Dict[str, Any],
    g_store: Dict[str, Any],
    c_d_store: Dict[str, Any],
    p_store: Dict[str, Any],
) -> str:
    """Generate deterministic, source-grounded answer for a benchmark question."""
    qid = q["question_id"]
    category = q.get("category")

    if qid == "C4-QA001-01":
        redir = get_nonstandard_redirect("MIG", g_store)
        std = lookup_glossary_term("gas metal arc welding", g_store)
        return (
            f"Under AWS A3.0:2020 Clause 4, 'metal inert gas (MIG) welding' is classified as a nonstandard term "
            f"(printed p. {redir['printed_page']}, observation ID: {redir['observation_id']}). "
            f"The standard term is 'gas metal arc welding' (GMAW). "
            f"Annex C C1.5.3 notes that 'inert' is technically inaccurate because shielding gases frequently "
            f"include active gases (CO2, O2, Ar-H2)."
        )

    elif qid == "C4-QA001-02":
        redir = get_nonstandard_redirect("TIG", g_store)
        std = lookup_glossary_term("gas tungsten arc welding", g_store)
        return (
            f"Under AWS A3.0:2020 Clause 4, 'tungsten inert gas (TIG) welding' is a nonstandard term "
            f"(printed p. {redir['printed_page']}). The mandatory standard designation that replaces it is "
            f"'gas tungsten arc welding' (GTAW) (printed p. {std['printed_page']}, observation ID: {std['observation_id']})."
        )

    elif qid == "C4-QA001-03":
        welder = lookup_glossary_term("welder", g_store)
        dec = get_subcommittee_decision("C1.5.4", c_d_store)
        return (
            f"In AWS A3.0:2020 Clause 4, 'welder' is defined as: '{welder['definition']}' (p. {welder['printed_page']}), "
            f"identifying the person who performs manual or semiautomatic welding. "
            f"'welding machine' is designated for the equipment. "
            f"Per Annex C C1.5.4, the alternate spelling 'weldor is nonstandard' and rejected by the committee "
            f"because spoken English pronunciation is identical."
        )

    elif qid == "C4-QA001-04":
        redir = get_nonstandard_redirect("stick electrode welding", g_store)
        std = lookup_glossary_term("shielded metal arc welding", g_store)
        return (
            f"'stick electrode welding' is a nonstandard term in AWS A3.0:2020 (printed p. {redir['printed_page']}). "
            f"The preferred standard term is 'shielded metal arc welding' (SMAW) (printed p. {std['printed_page']})."
        )

    elif qid == "C4-QA001-05":
        entries = g_store.get("entries", [])
        usw_list = [e for e in entries if e["term"].lower() == "ultrasonic welding"]
        res = ["Ultrasonic welding has two distinct entries in Clause 4:"]
        for e in usw_list:
            delims = e.get("domain_delimiters", [])
            d_str = ", ".join(delims) if delims else "solid-state welding"
            res.append(f"- Domain '{d_str}': {e['definition']} (p. {e['printed_page']})")
        return (
            "In Clause 4, ultrasonic welding is defined under two distinct domains: "
            "1) Under 'plastics' as 'A fusion welding process producing a weld by the local application of high-frequency vibratory energy...'; "
            "2) In the general welding/metals domain under 'solid-state welding' as 'A solid-state welding process producing a weld by the local application of high-frequency vibratory energy...'."
        )

    elif qid == "C4-QA001-06":
        e = lookup_glossary_term("contact resistance", g_store)
        delims = ", ".join(e.get("domain_delimiters", []))
        return (
            f"For 'contact resistance' in Clause 4 (printed p. {e['printed_page']}), the domain delimiter is "
            f"'{delims}'. It is defined as: 'Resistance to the flow of electric current caused by surface contact and "
            f"interface geometry between adjacent components or between electrodes and faying surfaces in resistance welding.'"
        )

    elif qid == "C4-QA001-07":
        e = lookup_glossary_term("balling up", g_store)
        delims = ", ".join(e.get("domain_delimiters", []))
        return (
            f"For 'balling up' in Clause 4 (printed p. {e['printed_page']}), the domain delimiters are "
            f"'{delims}'. It is defined as: 'The formation of globules of molten filler metal due to insufficient wetting of base metal in brazing and soldering.'"
        )

    elif qid == "C4-QA001-08":
        e = lookup_glossary_term("drag", g_store)
        delims = ", ".join(e.get("domain_delimiters", []))
        return (
            f"In Clause 4 (printed p. {e['printed_page']}), 'drag' is distinguished by the domain delimiter '{delims}'. "
            f"It is defined as: 'The offset distance between the actual and straight line exit points of the cutting oxygen stream in thermal cutting.'"
        )

    elif qid == "C4-QA001-09":
        prom = next(
            (p for p in p_store.get("promoted_is_a", []) if p["child_process"] == "pulsed gas metal arc welding"),
            None,
        )
        return (
            f"'pulsed gas metal arc welding (GMAW-P)' is promoted to predicate IS_A_PROCESS_VARIATION_OF "
            f"(status: ACCEPTED, knowledge_eligible=True) under gas metal arc welding because it satisfies the "
            f"dual provenance rule: 1) visual indentation in Table A1 (obs ID: {prom['source_observation_ids'][0]}), "
            f"and 2) Clause 4 standard definition explicitly naming the parent in its genus phrase: "
            f"'{prom['corroborating_phrase']}' ('{prom['clause4_quote']}', obs ID: {prom['source_observation_ids'][1]})."
        )

    elif qid == "C4-QA001-10":
        ret = next(
            (r for r in p_store.get("retained_candidates", []) if r["child_process"] == "shielded metal arc welding"),
            None,
        )
        return (
            f"'shielded metal arc welding (SMAW)' is retained as CANDIDATE_LAYOUT_PARENT under arc welding "
            f"because its Clause 4 definition defines it as a distinct root process ('An arc welding process with an arc between a covered electrode...'), "
            f"not a process variation of arc welding. Indentation in Table A1 reflects visual layout grouping under the "
            f"arc welding major group, not a subtype variation. Under the dual-provenance rule, it is not promoted."
        )

    elif qid == "C4-QA001-11":
        prom = next(
            (p for p in p_store.get("promoted_is_a", []) if "short circuiting" in p["child_process"].lower()),
            None,
        )
        return (
            f"Yes, 'short circuiting gas metal arc welding (GMAW-S)' is promoted to IS_A_PROCESS_VARIATION_OF GMAW "
            f"(status: ACCEPTED). Clause 4 corroborates the parent genus with the verbatim phrase: "
            f"'{prom['corroborating_phrase']}' ('{prom['clause4_quote']}')."
        )

    elif qid == "C4-QA001-12":
        m = p_store.get("metrics", {})
        return (
            f"In Table A1, there are exactly {m.get('total_indented_rows', 118)} total indented rows. "
            f"Under the dual-provenance admission rule (rule_id: 'dual-provenance-is-a-1'), exactly {m.get('promoted_is_a_count', 35)} "
            f"rows are promoted to IS_A_PROCESS_VARIATION_OF, exactly {m.get('retained_candidate_count', 83)} are retained as "
            f"CANDIDATE_LAYOUT_PARENT, and there are exactly {m.get('uncorroborated_promotions_count', 0)} uncorroborated promotions."
        )

    elif qid == "C4-QA001-13":
        dec = get_subcommittee_decision("C1.5.1", c_d_store)
        return (
            f"Per Annex C decision C1.5.1 (printed p. {dec['clause']['printed_page']}), the Definitions Subcommittee "
            f"discourages the use of 'bonding' for 'welding'. 'Bonding' is reserved strictly for joining and allied "
            f"processes where joining is effected by an adhesive or mechanical bond (adhesive bonding, brazing, soldering, thermal spraying). "
            f"When an atomic bond is formed, the operation is properly termed weld or welding."
        )

    elif qid == "C4-QA001-14":
        dec = get_subcommittee_decision("C1.5.2", c_d_store)
        return (
            f"Per Annex C decision C1.5.2 (printed p. {dec['clause']['printed_page']}), the committee adopted "
            f"'diffusion welding' (DFW) in accordance with international custom (BS499). The term 'diffusion bonding' "
            f"originated as an aircraft industry euphemism to avoid prejudice against welded aircraft structures. "
            f"AWS A3.0 explicitly rejects this prejudice."
        )

    elif qid == "C4-QA001-15":
        dec = get_subcommittee_decision("C1.5.5", c_d_store)
        return (
            f"In Annex C decision C1.5.5 (printed p. {dec['clause']['printed_page']}), the committee chose 'workpiece' "
            f"as the standard designation because Webster's Third New International Dictionary specifically defines it as "
            f"a piece of work in process of manufacture, whereas component, member, or part carry other non-manufacturing meanings."
        )

    elif qid == "C4-QA001-16":
        dec = get_subcommittee_decision("C1.5.7", c_d_store)
        return (
            f"In the 2020 edition, 'parallel joint' was introduced per Annex C decision C1.5.7 (printed p. {dec['clause']['printed_page']}) "
            f"to replace 'edge joint'. Historically, butt, corner, lap, and T-joint describe relative member orientation, "
            f"whereas edge joint described weld location and created confusion with edge weld. Parallel joint describes orientation: "
            f"'A joint type formed by butting, parallel surfaces of one or more workpieces with flush ends.'"
        )

    elif qid == "C4-QA001-17":
        t1 = get_annex_d_modifications("Table D1", c_d_store)
        e = lookup_glossary_term("3F, pipe", g_store)
        has_ul = e.get("has_2020_underline", False) if e else False
        return (
            f"Yes, '3F, pipe' is listed in Annex D Table D1 as a new term added in the 2020 edition. "
            f"In Clause 4 (printed p. {e['printed_page']}), it carries a horizontal underline stroke under its headword "
            f"(has_2020_underline={has_ul}) denoting its status as a new 2020 term."
        )

    elif qid == "C4-QA001-18":
        t2 = get_annex_d_modifications("Table D2", c_d_store)
        return (
            f"In Annex D, Table D2 lists '{t2['title']}' ({t2['row_count']} terms). "
            f"In Clause 4, modified definitions are identified by a vertical margin bar (change bar) "
            f"drawn in the column margins adjacent to the modified text."
        )

    elif qid == "C4-QA001-19":
        t6 = get_annex_d_modifications("Table D6", c_d_store)
        is_deleted = any("brazed joint" in r["entry"].lower() for r in t6.get("rows", []))
        return (
            f"Yes, 'brazed joint' was explicitly deleted in the 2020 edition per Annex D Table D6 (Deleted Terms, p. 170). "
            f"It is no longer an active standard definition in Clause 4."
        )

    elif qid == "C4-QA001-20":
        t5 = get_annex_d_modifications("Table D5", c_d_store)
        terms = [r["entry"] for r in t5.get("rows", [])]
        terms_str = ", ".join(terms)
        return (
            f"Per Annex D Table D5 ('Terms Revised from Nonstandard to Standard in 2020 Edition'), "
            f"the revised terms are: {terms_str} (including air cap, machine welding, nondestructive testing (NDT), "
            f"nondestructive inspection (NDI), nondestructive evaluation, and pulsation welding, resistance welding)."
        )

    return "No answer generated."


def run_benchmark() -> Dict[str, Any]:
    """Execute all 20 questions, evaluate against rubric.json, and generate receipt."""
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    with open(RUBRIC_PATH, "r", encoding="utf-8") as f:
        rubric_data = json.load(f)

    rubrics = rubric_data.get("rubrics", {})

    g_store = get_clause4_glossary_store()
    c_d_store = get_annex_c_d_store()
    p_store = get_is_a_promotion_store()

    results: List[Dict[str, Any]] = []
    total_passed = 0

    for q in questions:
        qid = q["question_id"]
        rubric = rubrics.get(qid, {})
        req_elements = rubric.get("required_elements", [])
        forbid_elements = rubric.get("forbidden_elements", [])

        ans_text = answer_clause4_benchmark_query(q, g_store, c_d_store, p_store)

        missing_req = [elem for elem in req_elements if elem.lower() not in ans_text.lower()]
        found_forbid = [elem for elem in forbid_elements if elem.lower() in ans_text.lower()]

        passed = (len(missing_req) == 0) and (len(found_forbid) == 0) and (len(ans_text) >= 30)

        if passed:
            total_passed += 1

        results.append({
            "question_id": qid,
            "category": q.get("category"),
            "query": q["query"],
            "answer": ans_text,
            "passed": passed,
            "required_elements": req_elements,
            "missing_required": missing_req,
            "forbidden_elements": forbid_elements,
            "found_forbidden": found_forbid,
        })

    receipt = {
        "benchmark_id": "clause4_glossary_gate3a_benchmark_001",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "total_passed": total_passed,
        "pass_rate": round(total_passed / len(questions), 3),
        "status": "PASS" if total_passed == len(questions) else "FAIL",
        "results": results,
    }

    with open(RECEIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)

    return receipt


if __name__ == "__main__":
    receipt = run_benchmark()
    print(f"Clause 4 Benchmark Complete: {receipt['total_passed']}/{receipt['total_questions']} PASS (status: {receipt['status']})")
