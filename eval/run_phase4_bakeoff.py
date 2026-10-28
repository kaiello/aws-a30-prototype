"""
eval/run_phase4_bakeoff.py: Whole-Standard Production Acceptance Bakeoff Runner (Gate 4).

Evaluates the 30-question cross-modal benchmark across the authorized Model Roster:
1. Route 1: DeterministicQuestionPlanner (0-LLM Baseline)
2. Route 2: DeepSeekQuestionPlanner (deepseek-flash / DeepSeek-V4.1-Flash-1017)
3. Route 3: Configured Comparison Routes (Checks .env / env for keys; records SKIPPED_NO_API_KEY if absent)

Strict Anti-Drift:
- Evaluates 5 Separated Dimensions (Schema Validity, Compiler Acceptance, Executed Operations, Content Grade, Delivery Grade)
- Zero question IDs or canned answers hardcoded in this script
- Calls public entrypoint answer_whole_standard_question with raw question text only
- Writes results to eval/evidence_v2_phase4_bakeoff_results.json
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    Phase4QuestionPlanner,
    Phase4ReplayPlanner,
    answer_whole_standard_question,
)

BENCHMARK_DIR = ROOT / "storage/evidence_v2/phase4_bakeoff_001"
QUESTIONS_FILE = BENCHMARK_DIR / "questions.json"
RUBRIC_FILE = BENCHMARK_DIR / "rubric.json"
DEEPSEEK_RUN_DIR = BENCHMARK_DIR / "deepseek_run"
RESULTS_FILE = ROOT / "eval/evidence_v2_phase4_bakeoff_results.json"


def evaluate_response(ans_payload: Dict[str, Any], rubric: Dict[str, Any]) -> Dict[str, Any]:
    """Grade an answer payload against rubric required and forbidden elements."""
    ans_text = ans_payload.get("answer", "")
    exec_res = ans_payload.get("execution", {})
    plan = ans_payload.get("plan", {})
    operations = exec_res.get("operations", [])
    receipt_meta = plan.get("receipt_metadata", {})

    req = rubric.get("required_elements", [])
    forb = rubric.get("forbidden_elements", [])

    req_missing = [elem for elem in req if elem.lower() not in ans_text.lower()]
    forb_found = [elem for elem in forb if elem.lower() in ans_text.lower()]

    has_blocked = any(f.lower() in ans_text.lower() for f in forb) or (
        "action1_blocked" in ans_text
        or "action_blocked" in ans_text
        or "[blocked]" in ans_text
        or "ambiguous_source_identity" in ans_text
        or "PLANNER_SCHEMA_INTEGRATION_BLOCKER" in ans_text
        or "LOCAL_BACKEND_ERROR" in ans_text
    )

    schema_valid = receipt_meta.get("error") is None and bool(plan.get("target_division"))
    compiler_accepted = exec_res.get("status") == "PASS"
    executed_ops = len(operations) >= 1

    content_pass = (
        len(ans_text) >= 20
        and executed_ops
        and not has_blocked
        and len(req_missing) == 0
        and len(forb_found) == 0
        and compiler_accepted
        and schema_valid
    )

    delivery_pass = content_pass and len(ans_text) >= 20

    return {
        "schema_valid": schema_valid,
        "compiler_accepted": compiler_accepted,
        "executed_operations": executed_ops,
        "operations_count": len(operations),
        "required_elements_missing": req_missing,
        "forbidden_elements_found": forb_found,
        "has_blocked": has_blocked,
        "content_grade": "PASS" if content_pass else "FAIL",
        "delivery_grade": "PASS" if delivery_pass else "FAIL",
    }


def run_phase4_bakeoff() -> Dict[str, Any]:
    is_live = "--live" in sys.argv
    print("=" * 80)
    print("GATE 4: FINAL MULTI-MODEL PRODUCTION ACCEPTANCE BAKEOFF")
    print(f"Mode: {'LIVE BOUNDED RUN' if is_live else 'OFFLINE DETERMINISTIC / REPLAY'}")
    print("=" * 80)

    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(f"Questions file missing: {QUESTIONS_FILE}")
    if not RUBRIC_FILE.exists():
        raise FileNotFoundError(f"Rubric file missing: {RUBRIC_FILE}")

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(RUBRIC_FILE, "r", encoding="utf-8") as f:
        rubric_data = json.load(f)
    rubrics = rubric_data.get("rubrics", {})

    total_q = len(questions)
    print(f"Loaded {total_q} questions across all 6 whole-standard slices.")

    stores = get_whole_standard_stores(ROOT)

    # -----------------------------------------------------------------------
    # Route 1: DeterministicQuestionPlanner (0-LLM Baseline)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("ROUTE 1: DeterministicQuestionPlanner (0-LLM Baseline — $0.00, 0 Tokens)")
    print("-" * 80)

    route1_planner = DeterministicQuestionPlanner(ROOT)
    route1_results: List[Dict[str, Any]] = []
    r1_start = time.perf_counter()

    for idx, q_item in enumerate(questions, 1):
        raw_qid = q_item["id"]
        query_text = q_item["query"]
        q_rubric = rubrics.get(raw_qid, {})

        t0 = time.perf_counter()
        ans = answer_whole_standard_question(query_text, route1_planner, stores=stores)
        elapsed = time.perf_counter() - t0

        grade = evaluate_response(ans, q_rubric)
        record = {
            "id": raw_qid,
            "query": query_text,
            "answer": ans.get("answer", ""),
            "elapsed_seconds": round(elapsed, 4),
            "operations_count": grade["operations_count"],
            "schema_valid": grade["schema_valid"],
            "compiler_accepted": grade["compiler_accepted"],
            "executed_operations": grade["executed_operations"],
            "required_elements_missing": grade["required_elements_missing"],
            "forbidden_elements_found": grade["forbidden_elements_found"],
            "content_grade": grade["content_grade"],
            "delivery_grade": grade["delivery_grade"],
        }
        route1_results.append(record)
        print(f"[{idx:02d}/{total_q}] {raw_qid} | {elapsed*1000:6.2f} ms | Grade: {grade['content_grade']} | Missing: {grade['required_elements_missing']}")

    r1_total_time = time.perf_counter() - r1_start

    # -----------------------------------------------------------------------
    # Route 2: DeepSeekQuestionPlanner (deepseek-flash / DeepSeek-V4.1-Flash-1017)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("ROUTE 2: DeepSeekQuestionPlanner (deepseek-flash / DeepSeek-V4.1-Flash-1017)")
    print("-" * 80)

    if is_live:
        if DEEPSEEK_RUN_DIR.exists():
            shutil.rmtree(DEEPSEEK_RUN_DIR)
        route2_planner = Phase4QuestionPlanner(ROOT, DEEPSEEK_RUN_DIR)
        print(f"Initialized live Phase4QuestionPlanner in {DEEPSEEK_RUN_DIR}")
    else:
        if not DEEPSEEK_RUN_DIR.exists():
            raise FileNotFoundError(f"DeepSeek run directory missing for replay: {DEEPSEEK_RUN_DIR}")
        route2_planner = Phase4ReplayPlanner(DEEPSEEK_RUN_DIR)
        print(f"Initialized Phase4ReplayPlanner replaying receipts from {DEEPSEEK_RUN_DIR}")

    route2_results: List[Dict[str, Any]] = []
    r2_start = time.perf_counter()

    for idx, q_item in enumerate(questions, 1):
        raw_qid = q_item["id"]
        query_text = q_item["query"]
        q_rubric = rubrics.get(raw_qid, {})

        t0 = time.perf_counter()
        req_dir = DEEPSEEK_RUN_DIR / f"request_{idx:03d}"
        ans = answer_whole_standard_question(query_text, route2_planner, stores=stores, req_dir=req_dir)
        elapsed = time.perf_counter() - t0

        grade = evaluate_response(ans, q_rubric)
        plan_meta = ans.get("plan", {}).get("receipt_metadata", {})
        record = {
            "id": raw_qid,
            "query": query_text,
            "answer": ans.get("answer", ""),
            "elapsed_seconds": round(elapsed, 4),
            "planner_elapsed_seconds": plan_meta.get("elapsed_seconds"),
            "token_usage": plan_meta.get("token_usage"),
            "model": plan_meta.get("model"),
            "operations_count": grade["operations_count"],
            "schema_valid": grade["schema_valid"],
            "compiler_accepted": grade["compiler_accepted"],
            "executed_operations": grade["executed_operations"],
            "required_elements_missing": grade["required_elements_missing"],
            "forbidden_elements_found": grade["forbidden_elements_found"],
            "content_grade": grade["content_grade"],
            "delivery_grade": grade["delivery_grade"],
        }
        route2_results.append(record)
        print(f"[{idx:02d}/{total_q}] {raw_qid} | {elapsed:6.2f} s | Grade: {grade['content_grade']} | Missing: {grade['required_elements_missing']}")

    r2_total_time = time.perf_counter() - r2_start

    # -----------------------------------------------------------------------
    # Route 3: Configured Comparison Routes (OpenAI / Anthropic / Gemini check)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("ROUTE 3: Configured Comparison Routes (Optional Provider Verification)")
    print("-" * 80)

    comparison_routes = {}
    candidate_providers = [
        ("openai", "OPENAI_API_KEY", "GPT-5.6-Terra"),
        ("anthropic", "ANTHROPIC_API_KEY", "Claude-3.7-Sonnet"),
        ("gemini", "GEMINI_API_KEY", "Gemini-3.8-Flash"),
    ]

    for prov_name, env_var, model_name in candidate_providers:
        if os.environ.get(env_var, "").strip():
            comparison_routes[prov_name] = {
                "status": "CONFIGURED",
                "model": model_name,
                "note": f"Provider key {env_var} found."
            }
            print(f"  Provider '{prov_name}': CONFIGURED ({model_name})")
        else:
            comparison_routes[prov_name] = {
                "status": "SKIPPED_NO_API_KEY",
                "model": model_name,
                "note": f"Provider key {env_var} not configured in environment or .env."
            }
            print(f"  Provider '{prov_name}': SKIPPED_NO_API_KEY ({env_var} not set)")

    # -----------------------------------------------------------------------
    # Metrics Aggregation & Receipt Generation
    # -----------------------------------------------------------------------
    r1_pass = sum(1 for r in route1_results if r["content_grade"] == "PASS")
    r2_pass = sum(1 for r in route2_results if r["content_grade"] == "PASS")

    r1_avg_ms = (sum(r["elapsed_seconds"] for r in route1_results) / total_q) * 1000
    r2_avg_s = sum(r["elapsed_seconds"] for r in route2_results) / total_q

    r2_total_tokens = sum(
        (r.get("token_usage", {}) or {}).get("total_tokens", 0) for r in route2_results
    )
    # DeepSeek flash cost: ~$0.14 / 1M input tokens, ~$0.28 / 1M output tokens (approx $0.0002 / 1k tokens)
    r2_est_cost = (r2_total_tokens / 1000.0) * 0.00025

    summary = {
        "benchmark_id": "phase4_bakeoff_001",
        "standard": "AWS A3.0M/A3.0:2020",
        "total_questions": total_q,
        "mode": "live" if is_live else "replay",
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route_scorecard": {
            "route_1_deterministic": {
                "name": "DeterministicQuestionPlanner (0-LLM Baseline)",
                "passed": r1_pass,
                "total": total_q,
                "accuracy_pct": round(r1_pass / total_q * 100.0, 2),
                "total_time_seconds": round(r1_total_time, 3),
                "avg_latency_ms": round(r1_avg_ms, 2),
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            },
            "route_2_deepseek": {
                "name": "DeepSeekQuestionPlanner (deepseek-flash / DeepSeek-V4.1-Flash-1017)",
                "passed": r2_pass,
                "total": total_q,
                "accuracy_pct": round(r2_pass / total_q * 100.0, 2),
                "total_time_seconds": round(r2_total_time, 3),
                "avg_latency_seconds": round(r2_avg_s, 3),
                "total_tokens": r2_total_tokens,
                "estimated_cost_usd": round(r2_est_cost, 4),
            },
            "route_3_comparison_routes": comparison_routes,
        },
        "route_1_results": route1_results,
        "route_2_results": route2_results,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("GATE 4 BAKEOFF SCORECARD SUMMARY")
    print("=" * 80)
    print(f"Route 1 (Deterministic 0-LLM): {r1_pass}/{total_q} ({r1_pass/total_q*100:.1f}%) | Latency: {r1_avg_ms:.2f} ms/query | Cost: $0.00")
    print(f"Route 2 (DeepSeek-V4.1-Flash):  {r2_pass}/{total_q} ({r2_pass/total_q*100:.1f}%) | Latency: {r2_avg_s:.2f} s/query | Tokens: {r2_total_tokens} (~${r2_est_cost:.4f})")
    for prov, info in comparison_routes.items():
        print(f"Route 3 ({prov:10s}): {info['status']} ({info['model']})")
    print("=" * 80)
    print(f"Receipt written to: {RESULTS_FILE}")
    return summary


if __name__ == "__main__":
    run_phase4_bakeoff()
