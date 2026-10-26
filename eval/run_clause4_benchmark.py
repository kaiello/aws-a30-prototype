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
    compose_clause4_answer,
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
    """Generate deterministic, source-grounded answer for a benchmark question using data-driven composer."""
    return compose_clause4_answer(q, g_store, c_d_store, p_store)


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
