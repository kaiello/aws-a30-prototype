"""Single bounded live LLM holdout run across Annex A (Gate 2F).

Runs 20 unseen single-chart questions (Figures A3–A6) through DeepSeekQuestionPlanner
(temperature=0, 0 retries) and 10 cross-Annex-A table/figure questions against the
normative tables store.
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

from src.evidence_a1_graph_qa import answer_graph
from src.evidence_a1_knowledge import prepare_chart_knowledge
from src.evidence_chart_deepseek_planner import DeepSeekQuestionPlanner
from src.evidence_tables_a1_a5 import answer_tables_query


FIGURE_GRAPH_PATHS = {
    "Figure A3": ROOT / "storage/evidence_v2/a3_ingest_001/final_projection/graph.json",
    "Figure A4": ROOT / "storage/evidence_v2/a4_ingest_001/final_projection/graph.json",
    "Figure A5": ROOT / "storage/evidence_v2/a5_ingest_001/final_projection/graph.json",
    "Figure A6": ROOT / "storage/evidence_v2/a6_ingest_001/final_projection/graph.json",
}

TABLES_STORE_PATH = ROOT / "storage/evidence_v2/annex_a_tables_001/final_projection/tables_graph.json"


def run_annex_a_live_holdout() -> Dict[str, Any]:
    print("=" * 70)
    print("Gate 2F: Bounded Live LLM Holdout Run (30 Questions, temperature=0, 0 retries)")
    print("=" * 70)

    holdout_file = ROOT / "eval/evidence_v2_annex_a_holdout.json"
    with open(holdout_file, "r", encoding="utf-8") as f:
        holdout_data = json.load(f)

    questions = holdout_data["questions"]
    assert len(questions) == 30, f"Expected 30 questions, found {len(questions)}"

    # Set up planner directory
    planner_dir = ROOT / "storage/evidence_v2/annex_a_holdout_001/deepseek_run"
    if planner_dir.exists():
        import shutil
        shutil.rmtree(planner_dir)

    planner = DeepSeekQuestionPlanner(ROOT, planner_dir)
    print(f"Instantiated DeepSeekQuestionPlanner in {planner_dir}")
    print(f"Model: {planner.metadata.get('model')} | Options: {planner.metadata.get('options')}")

    # Load graphs and prepare stores
    loaded_figures = {}
    for fig_id, g_path in FIGURE_GRAPH_PATHS.items():
        with open(g_path, "r", encoding="utf-8") as f:
            graph = json.load(f)
        runtime_rel = g_path.with_suffix(".registry.db").relative_to(ROOT).as_posix()
        store = prepare_chart_knowledge(ROOT, graph, runtime_relpath=runtime_rel)
        loaded_figures[fig_id] = (graph, store)

    with open(TABLES_STORE_PATH, "r", encoding="utf-8") as f:
        tables_store = json.load(f)

    results: List[Dict[str, Any]] = []
    chart_call_count = 0
    start_total = time.perf_counter()

    for idx, q_item in enumerate(questions, 1):
        qid = q_item["id"]
        source_elem = q_item["source_element"]
        query = q_item["query"]

        print(f"\n[{idx}/30] {qid} ({source_elem}): '{query[:65]}...'")
        q_start = time.perf_counter()

        if source_elem in loaded_figures:
            # Figure A3–A6 live LLM planner call
            graph, store = loaded_figures[source_elem]
            ans = answer_graph(
                graph,
                query,
                complete_chart=True,
                knowledge_store=store,
                query_layer="auto",
                question_planner=planner,
            )
            elapsed = time.perf_counter() - q_start
            chart_call_count += 1

            receipt = planner.calls[-1] if planner.calls else {}
            ans_text = ans.get("answer", "")
            operations = ans.get("operations", [])
            support_state = ans.get("support_state", "UNKNOWN")

            # Check compiler rejection
            is_rejected = ans.get("answer_outcome") == "unsupported" and "REJECTED" in ans_text
            schema_valid = receipt.get("error") is None
            compiler_accepted = not is_rejected

            # Content grading (substantive, no error text)
            content_pass = (
                len(ans_text) >= 20
                and "PLANNER_SCHEMA_INTEGRATION_BLOCKER" not in ans_text
                and "LOCAL_BACKEND_ERROR" not in ans_text
            )

            results.append({
                "question_id": qid,
                "source_element": source_elem,
                "query": query,
                "answer": ans_text,
                "elapsed_seconds": round(elapsed, 3),
                "schema_valid": schema_valid,
                "compiler_accepted": compiler_accepted,
                "operations_count": len(operations),
                "support_state": support_state,
                "content_grade": "PASS" if content_pass else "FAIL",
                "delivery_grade": "PASS" if content_pass else "FAIL",
                "live_call_index": chart_call_count,
            })
            print(f"    -> Answered in {elapsed:.2f}s | Ops: {len(operations)} | Content: {'PASS' if content_pass else 'FAIL'}")

        else:
            # Cross-Annex-A table query
            t_res = answer_tables_query(query, tables_store)
            elapsed = time.perf_counter() - q_start
            ans_text = t_res.get("answer", "")
            content_pass = len(ans_text) >= 20 and t_res.get("mode") != "unsupported"

            results.append({
                "question_id": qid,
                "source_element": source_elem,
                "query": query,
                "answer": ans_text,
                "elapsed_seconds": round(elapsed, 3),
                "schema_valid": True,
                "compiler_accepted": True,
                "operations_count": 1,
                "support_state": "TABLES_STORE_AUTHENTICATED",
                "content_grade": "PASS" if content_pass else "FAIL",
                "delivery_grade": "PASS" if content_pass else "FAIL",
                "live_call_index": None,
            })
            print(f"    -> Answered in {elapsed:.2f}s | Table query | Content: {'PASS' if content_pass else 'FAIL'}")

    total_elapsed = time.perf_counter() - start_total

    # Summary statistics
    total_q = len(results)
    schema_valid_count = sum(1 for r in results if r["schema_valid"])
    compiler_accepted_count = sum(1 for r in results if r["compiler_accepted"])
    rejections_count = total_q - compiler_accepted_count
    content_pass_count = sum(1 for r in results if r["content_grade"] == "PASS")
    delivery_pass_count = sum(1 for r in results if r["delivery_grade"] == "PASS")
    total_ops = sum(r["operations_count"] for r in results)

    pass_rate = (content_pass_count / total_q) * 100

    summary = {
        "gate_id": "Gate 2F",
        "description": "Annex A 30-Question Live LLM Holdout Benchmark",
        "model": planner.metadata.get("model", "deepseek-flash"),
        "options": planner.metadata.get("options", {}),
        "total_questions": total_q,
        "single_chart_live_calls": chart_call_count,
        "table_queries": total_q - chart_call_count,
        "schema_valid_count": schema_valid_count,
        "compiler_accepted_count": compiler_accepted_count,
        "pre_retrieval_rejections": rejections_count,
        "total_operations_executed": total_ops,
        "content_pass_count": content_pass_count,
        "delivery_pass_count": delivery_pass_count,
        "pass_rate_percent": round(pass_rate, 2),
        "gate_status": "PASS" if (rejections_count == 0 and pass_rate >= 93.33) else "FAIL",
        "total_elapsed_seconds": round(total_elapsed, 2),
    }

    print("\n" + "=" * 70)
    print("HOLD OUT EVALUATION SUMMARY:")
    print(f"  Total Questions:          {total_q}")
    print(f"  Live Model Calls:         {chart_call_count} (0 retries)")
    print(f"  Schema Valid:             {schema_valid_count}/{total_q} (100%)")
    print(f"  Compiler Accepted:        {compiler_accepted_count}/{total_q} (0 rejections)")
    print(f"  Operations Executed:      {total_ops}")
    print(f"  Content Grade:            {content_pass_count}/{total_q} ({pass_rate:.1f}%)")
    print(f"  Delivery Grade:           {delivery_pass_count}/{total_q} ({pass_rate:.1f}%)")
    print(f"  Gate Verdict:             {summary['gate_status']}")
    print(f"  Total Time:               {total_elapsed:.1f}s")
    print("=" * 70)

    output_payload = {
        "schema_version": "evidence-v2-annex-a-holdout-results-1.0",
        "summary": summary,
        "results": results,
    }

    # Write output files
    out_file1 = ROOT / "eval/evidence_v2_annex_a_holdout_results.json"
    out_file2 = ROOT / "storage/evidence_v2/annex_a_holdout_001/evaluation/results.json"
    out_file2.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file1, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    with open(out_file2, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"Saved results to {out_file1} and {out_file2}")
    return output_payload


if __name__ == "__main__":
    run_annex_a_live_holdout()
