"""Evaluation runner for Gate 5: Production Hardening & Adversarial Invariant Defense.

Runs 10 boundary, adversarial, and out-of-scope queries against
answer_whole_standard_question to prove robust refusal, contradiction refutation,
and non-hallucination.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)


def evaluate_adversarial_suite(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute adversarial suite against public whole-standard QA entrypoint."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = root / "storage/evidence_v2/phase5_hardening_001"

    q_file = output_dir / "adversarial_questions.json"
    r_file = output_dir / "rubric.json"

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubric_data = json.loads(r_file.read_text(encoding="utf-8"))
    rubrics = rubric_data["rubrics"]

    stores = get_whole_standard_stores(root)
    planner = DeterministicQuestionPlanner(root)

    results = []
    passed_count = 0

    for item in questions:
        qid = item["id"]
        query = item["query"]
        category = item["category"]
        rubric = rubrics[qid]

        resp = answer_whole_standard_question(query, planner, stores=stores)
        execution = resp.get("execution", {})
        status = execution.get("status")
        answer = resp.get("answer", "")
        elements_present = execution.get("elements_present", [])

        exp_status = rubric["expected_status"]
        status_match = (status == exp_status)

        # Check required elements
        req_missing = [req for req in rubric["required_elements"] if req.lower() not in answer.lower()]
        # Check forbidden elements
        forb_hit = [forb for forb in rubric["forbidden_elements"] if forb.lower() in answer.lower()]

        test_passed = status_match and (len(req_missing) == 0) and (len(forb_hit) == 0)
        if test_passed:
            passed_count += 1

        results.append({
            "id": qid,
            "category": category,
            "query": query,
            "actual_status": status,
            "expected_status": exp_status,
            "status_match": status_match,
            "required_missing": req_missing,
            "forbidden_hit": forb_hit,
            "passed": test_passed,
            "answer_preview": answer[:120] + "..." if len(answer) > 120 else answer,
        })

    summary = {
        "suite": "Gate 5 Adversarial & Production Hardening",
        "total_questions": len(questions),
        "passed_questions": passed_count,
        "pass_rate_pct": (passed_count / len(questions)) * 100.0,
        "results": results,
    }

    out_file = output_dir / "results.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    res = evaluate_adversarial_suite()
    print(f"Gate 5 Adversarial Suite: {res['passed_questions']} / {res['total_questions']} ({res['pass_rate_pct']:.1f}%) Passed")
