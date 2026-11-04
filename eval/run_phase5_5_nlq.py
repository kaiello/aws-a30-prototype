"""Evaluation runner for Gate 5.5: Semantic Expansion & ID-Free NLQ Hardening.

Runs 15 natural language queries across 5 distinct slices against
answer_whole_standard_question to prove deterministic semantic query expansion,
ID-free routing across Annex A & Annex B, morphological normalization,
and robust out-of-scope / unstandardized term handling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)


def evaluate_nlq_benchmark(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    write_results: bool = False,
) -> Dict[str, Any]:
    """Execute Gate 5.5 15-query NLQ benchmark against public QA entrypoint."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = root / "storage/evidence_v2/phase5_5_nlq_001"

    q_file = output_dir / "nlq_questions.json"
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
        slice_name = item.get("slice_name", category)
        rubric = rubrics[qid]

        resp = answer_whole_standard_question(query, planner, stores=stores)
        plan = resp.get("plan", {})
        execution = resp.get("execution", {})
        status = execution.get("status")
        answer = resp.get("answer", "")
        elements_present = execution.get("elements_present", [])
        trace = plan.get("semantic_expansion_trace", {})

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
            "slice_name": slice_name,
            "query": query,
            "actual_status": status,
            "expected_status": exp_status,
            "status_match": status_match,
            "required_missing": req_missing,
            "forbidden_hits": forb_hit,
            "test_passed": test_passed,
            "answer": answer,
            "elements_present": elements_present,
            "normative_provenance": execution.get("normative_provenance", []),
            "target_division": plan.get("target_division"),
            "intent": plan.get("intent"),
            "semantic_expansion_trace": trace,
        })

    total_q = len(questions)
    pass_rate = (passed_count / total_q) * 100.0 if total_q > 0 else 0.0

    output_payload = {
        "version": "phase5_5_nlq_results_v1.0",
        "benchmark_name": "Gate 5.5 Semantic Expansion & ID-Free NLQ Benchmark",
        "total_queries": total_q,
        "passed": passed_count,
        "failed": total_q - passed_count,
        "pass_rate_percent": pass_rate,
        "results": results,
    }

    results_file = output_dir / "results.json"
    results_json = json.dumps(output_payload, indent=2) + "\n"
    if write_results:
        with open(results_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(results_json)
        sha256 = hashlib.sha256(results_file.read_bytes()).hexdigest()
    else:
        sha256 = hashlib.sha256(results_json.encode("utf-8")).hexdigest()

    output_payload["results_sha256"] = sha256

    return output_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gate 5.5 NLQ Benchmark")
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root directory")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output benchmark directory")
    parser.add_argument("--write-results", action="store_true", help="Write results.json to disk")
    args = parser.parse_args()
    summary = evaluate_nlq_benchmark(root=args.root, output_dir=args.output_dir, write_results=args.write_results)

    payload = evaluate_nlq_benchmark(root=args.root, output_dir=args.output_dir)
    print(f"Gate 5.5 NLQ Benchmark: {payload['passed']}/{payload['total_queries']} passed ({payload['pass_rate_percent']:.1f}%)")
    print(f"Results written to: storage/evidence_v2/phase5_5_nlq_001/results.json (SHA-256: {payload['results_sha256']})")

    if payload["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
