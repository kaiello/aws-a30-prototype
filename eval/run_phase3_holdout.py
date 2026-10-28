"""
eval/run_phase3_holdout.py: Phase 3 Cross-Modal Holdout Benchmark (Gate 3D).

Evaluates 40 cross-modal holdout questions spanning:
- Slice 1: Clause 4 Glossary, Nonstandard Synonyms & Domain Delimiters
- Slice 2: Dual-Provenance IS_A Promotions & Annex C / Annex D
- Slice 3: Annex B Archetype 3 Spatial Callouts (Figures B1–B48, B52)
- Slice 4: Annex B Archetype 4 Waveforms (Figures B44, B45, B49, B50, B51, B53, B54)

Supports:
- --live: Live bounded LLM planner run using DeepSeekQuestionPlanner (40 calls, temperature=0, 0 retries)
- offline (default): Replays saved receipts from storage/evidence_v2/phase3_holdout_001/deepseek_run

Zero question IDs or canned answers hardcoded. Evaluates 5 Separated Dimensions.
Outputs receipt to eval/evidence_v2_phase3_holdout_results.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase3_qa import (
    get_phase3_stores,
    Phase3QuestionPlanner,
    Phase3ReplayPlanner,
    execute_phase3_plan,
    answer_phase3_question,
)

HOLDOUT_DIR = ROOT / "storage/evidence_v2/phase3_holdout_001"
QUESTIONS_FILE = HOLDOUT_DIR / "questions.json"
RUBRIC_FILE = HOLDOUT_DIR / "rubric.json"
PLANNER_DIR = HOLDOUT_DIR / "deepseek_run"
RESULTS_FILE = ROOT / "eval/evidence_v2_phase3_holdout_results.json"


def run_phase3_holdout() -> Dict[str, Any]:
    is_live = "--live" in sys.argv
    print("=" * 75)
    if is_live:
        print("Gate 3D: Bounded Live LLM Holdout Run (40 Questions, temperature=0, 0 retries)")
    else:
        print("Gate 3D: Offline Receipt Replay Benchmark (40 Questions, 0 live LLM calls)")
    print("=" * 75)

    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(f"Questions file missing: {QUESTIONS_FILE}")
    if not RUBRIC_FILE.exists():
        raise FileNotFoundError(f"Rubric file missing: {RUBRIC_FILE}")

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(RUBRIC_FILE, "r", encoding="utf-8") as f:
        rubric_data = json.load(f)

    rubrics = rubric_data.get("rubrics", {})
    assert len(questions) == 40, f"Expected 40 questions, found {len(questions)}"

    stores = get_phase3_stores(ROOT)

    # Initialize planner
    if is_live:
        if PLANNER_DIR.exists():
            import shutil
            shutil.rmtree(PLANNER_DIR)
        planner = Phase3QuestionPlanner(ROOT, PLANNER_DIR)
        print(f"Instantiated DeepSeekQuestionPlanner in {PLANNER_DIR}")
        print(f"Model: {planner.metadata.get('model')} | Options: {planner.metadata.get('options')}")
    else:
        if not PLANNER_DIR.exists():
            raise FileNotFoundError(f"Replay planner directory does not exist: {PLANNER_DIR}")
        planner = Phase3ReplayPlanner(PLANNER_DIR)
        print(f"Instantiated Phase3ReplayPlanner in {PLANNER_DIR} (0 live LLM calls)")

    results: List[Dict[str, Any]] = []
    start_total = time.perf_counter()
    call_index = 0

    schema_valid_count = 0
    compiler_accepted_count = 0
    executed_ops_count = 0
    content_pass_count = 0
    delivery_pass_count = 0

    for idx, q_item in enumerate(questions, 1):
        qid = q_item["id"]
        slice_name = q_item.get("slice", "")
        source_elem = q_item.get("source_element", "")
        query = q_item["query"]

        print(f"\n[{idx}/40] {qid} ({source_elem}): '{query[:65]}...'")
        q_start = time.perf_counter()

        req_dir = PLANNER_DIR / f"request_{idx:03d}"
        qa_result = answer_phase3_question(query, planner=planner, stores=stores, req_dir=req_dir)
        elapsed = time.perf_counter() - q_start
        call_index += 1

        plan = qa_result["plan"]
        exec_res = qa_result["execution"]
        ans_text = qa_result["answer"]

        receipt_meta = plan.get("receipt_metadata", {})
        schema_valid = receipt_meta.get("error") is None
        compiler_accepted = bool(plan.get("actions")) and plan.get("intent") != "rejected"
        operations = exec_res.get("operations", [])
        ops_count = len(operations)

        # Rubric evaluation
        rubric = rubrics.get(qid, {})
        req = rubric.get("required_elements", [])
        forb = rubric.get("forbidden_elements", [])
        req_missing = [elem for elem in req if elem.lower() not in ans_text.lower()]
        forb_found = [elem for elem in forb if elem.lower() in ans_text.lower()]

        has_blocked = (
            "action_blocked" in ans_text
            or "ambiguous_source_identity" in ans_text
            or "CHART_QUESTION_PLAN_" in ans_text
            or "LOCAL_BACKEND_ERROR" in ans_text
        )

        content_pass = (
            len(ans_text) >= 20
            and ops_count >= 1
            and not has_blocked
            and len(req_missing) == 0
            and len(forb_found) == 0
            and compiler_accepted
            and schema_valid
        )
        delivery_pass = content_pass

        if schema_valid:
            schema_valid_count += 1
        if compiler_accepted:
            compiler_accepted_count += 1
        if ops_count >= 1:
            executed_ops_count += 1
        if content_pass:
            content_pass_count += 1
        if delivery_pass:
            delivery_pass_count += 1

        status_str = "PASS" if content_pass else "FAIL"
        print(f"    -> Answered in {elapsed:.2f}s | Ops: {ops_count} | Content: {status_str}")
        if not content_pass:
            print(f"       Missing: {req_missing} | Forbidden: {forb_found}")

        results.append({
            "question_id": qid,
            "slice": slice_name,
            "source_element": source_elem,
            "query": query,
            "answer": ans_text,
            "elapsed_seconds": round(elapsed, 3),
            "schema_valid": schema_valid,
            "compiler_accepted": compiler_accepted,
            "operations_count": ops_count,
            "operations": operations,
            "required_elements_missing": req_missing,
            "forbidden_elements_found": forb_found,
            "content_grade": "PASS" if content_pass else "FAIL",
            "delivery_grade": "PASS" if delivery_pass else "FAIL",
            "live_call_index": call_index,
        })

    total_elapsed = time.perf_counter() - start_total

    summary = {
        "benchmark_id": "phase3_holdout_gate3d_001",
        "mode": "live" if is_live else "replay",
        "total_questions": len(questions),
        "total_elapsed_seconds": round(total_elapsed, 2),
        "five_dimensions": {
            "schema_valid": f"{schema_valid_count} / {len(questions)} ({schema_valid_count/len(questions)*100:.1f}%)",
            "compiler_accepted": f"{compiler_accepted_count} / {len(questions)} ({compiler_accepted_count/len(questions)*100:.1f}%)",
            "executed_operations": f"{executed_ops_count} / {len(questions)} ({executed_ops_count/len(questions)*100:.1f}%)",
            "content_grade": f"{content_pass_count} / {len(questions)} ({content_pass_count/len(questions)*100:.1f}%)",
            "delivery_grade": f"{delivery_pass_count} / {len(questions)} ({delivery_pass_count/len(questions)*100:.1f}%)",
        },
        "results": results,
    }

    RESULTS_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + "=" * 75)
    print("GATE 3D FIVE-DIMENSION SCORECARD:")
    for k, v in summary["five_dimensions"].items():
        print(f"  {k:22s}: {v}")
    print(f"Receipt written to: {RESULTS_FILE}")
    print("=" * 75)

    return summary


if __name__ == "__main__":
    run_phase3_holdout()
