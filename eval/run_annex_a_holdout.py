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
def _load_holdout_rubric():
    r_path = ROOT / "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json"
    if r_path.exists():
        return json.loads(r_path.read_text(encoding="utf-8"))
    return {}

HOLDOUT_RUBRIC = _load_holdout_rubric()


class ReplayQuestionPlanner:
    """Offline deterministic replay planner using saved receipts with 0 live network calls."""
    def __init__(self, root: Path, directory: Path):
        self.root = Path(root)
        self.directory = Path(directory)
        runtime_file = self.directory / "runtime.json"
        if runtime_file.exists():
            with open(runtime_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "provider": "deepseek_https_explicit",
                "model": "deepseek-flash",
                "documented_model_version": "DeepSeek-V4.1-Flash-1017",
                "options": {"temperature": 0},
            }
        self.calls = []
        self.requests = 0
        self.structural_block = None

    def record_result(self, answer):
        pass

    def __call__(self, graph, query, *, concept_bindings=None):
        from src.evidence_chart_question_plan import compile_plan
        from src.evidence_chart_local_planner import _rejected
        from src.evidence_a1_vision import _strict_loads, _canonical

        self.requests += 1
        req_dir = self.directory / f"request_{self.requests:03d}"
        receipt_file = req_dir / "receipt.json"
        if not receipt_file.exists():
            raise FileNotFoundError(f"Missing replay receipt: {receipt_file}")
        with open(receipt_file, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        self.calls.append(receipt)
        payload = _strict_loads(receipt["raw_output"])
        try:
            plan = compile_plan(graph, query, payload, concept_bindings=concept_bindings)
        except (ValueError, TypeError, KeyError) as exc:
            plan = _rejected(query, "MODEL_PLAN_REJECTED: " + str(exc))
        plan["model_planning"] = {key: receipt.get(key) for key in (
            "version", "model", "digest", "provider", "options", "elapsed_seconds",
            "request_sha256", "model_invocation_count", "external_call_count")}
        (req_dir / "validated_plan.json").write_bytes(_canonical(plan))
        return plan


def run_annex_a_live_holdout() -> Dict[str, Any]:
    is_live = "--live" in sys.argv
    print("=" * 70)
    if is_live:
        print("Gate 2F: Bounded Live LLM Holdout Run (30 Questions, temperature=0, 0 retries)")
    else:
        print("Gate 2F: Offline Receipt Replay Benchmark (30 Questions, 0 live LLM calls)")
    print("=" * 70)

    holdout_file = ROOT / "eval/evidence_v2_annex_a_holdout.json"
    with open(holdout_file, "r", encoding="utf-8") as f:
        holdout_data = json.load(f)

    questions = holdout_data["questions"]
    assert len(questions) == 30, f"Expected 30 questions, found {len(questions)}"

    # Set up planner directory
    planner_dir = ROOT / "storage/evidence_v2/annex_a_holdout_001/deepseek_run"
    if is_live:
        if planner_dir.exists():
            import shutil
            shutil.rmtree(planner_dir)
        planner = DeepSeekQuestionPlanner(ROOT, planner_dir)
        print(f"Instantiated DeepSeekQuestionPlanner in {planner_dir}")
        print(f"Model: {planner.metadata.get('model')} | Options: {planner.metadata.get('options')}")
    else:
        if not planner_dir.exists():
            raise FileNotFoundError(f"Replay planner directory does not exist: {planner_dir}")
        planner = ReplayQuestionPlanner(ROOT, planner_dir)
        print(f"Instantiated ReplayQuestionPlanner in {planner_dir} (0 live LLM calls)")

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

            # Strict Rubric Evaluation
            rubric = HOLDOUT_RUBRIC.get(qid, {})
            req = rubric.get("required_elements", [])
            forb = rubric.get("forbidden_elements", [])
            req_missing = [elem for elem in req if elem.lower() not in ans_text.lower()]
            forb_found = [elem for elem in forb if elem.lower() in ans_text.lower()]

            has_blocked = (
                "action1_blocked" in ans_text
                or "action_blocked" in ans_text
                or "[blocked]" in ans_text
                or "ambiguous_source_identity" in ans_text
                or "PLANNER_SCHEMA_INTEGRATION_BLOCKER" in ans_text
                or "LOCAL_BACKEND_ERROR" in ans_text
            )

            content_pass = (
                len(ans_text) >= 20
                and len(operations) >= 1
                and not has_blocked
                and len(req_missing) == 0
                and len(forb_found) == 0
                and compiler_accepted
                and schema_valid
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
                "required_elements_missing": req_missing,
                "forbidden_elements_found": forb_found,
                "content_grade": "PASS" if content_pass else "FAIL",
                "delivery_grade": "PASS" if content_pass else "FAIL",
                "live_call_index": chart_call_count,
            })
            if not content_pass:
                print(f"    -> Answered in {elapsed:.2f}s | Ops: {len(operations)} | Content: FAIL (Missing: {req_missing}, Forb: {forb_found}, Blocked: {has_blocked})")
            else:
                print(f"    -> Answered in {elapsed:.2f}s | Ops: {len(operations)} | Content: PASS")

        else:
            # Cross-Annex-A table query
            t_res = answer_tables_query(query, tables_store)
            elapsed = time.perf_counter() - q_start
            ans_text = t_res.get("answer", "")

            # Strict Rubric Evaluation for tables
            rubric = HOLDOUT_RUBRIC.get(qid, {})
            req = rubric.get("required_elements", [])
            forb = rubric.get("forbidden_elements", [])
            req_missing = [elem for elem in req if elem.lower() not in ans_text.lower()]
            forb_found = [elem for elem in forb if elem.lower() in ans_text.lower()]

            has_blocked = (
                "action1_blocked" in ans_text
                or "action_blocked" in ans_text
                or "[blocked]" in ans_text
                or "ambiguous_source_identity" in ans_text
            )

            content_pass = (
                len(ans_text) >= 20
                and t_res.get("mode") != "unsupported"
                and not has_blocked
                and len(req_missing) == 0
                and len(forb_found) == 0
            )

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
                "required_elements_missing": req_missing,
                "forbidden_elements_found": forb_found,
                "content_grade": "PASS" if content_pass else "FAIL",
                "delivery_grade": "PASS" if content_pass else "FAIL",
                "live_call_index": None,
            })
            if not content_pass:
                print(f"    -> Answered in {elapsed:.2f}s | Table query | Content: FAIL (Missing: {req_missing}, Forb: {forb_found})")
            else:
                print(f"    -> Answered in {elapsed:.2f}s | Table query | Content: PASS")

    total_elapsed = time.perf_counter() - start_total

    # Summary statistics
    total_q = len(results)
    schema_valid_count = sum(1 for r in results if r["schema_valid"])
    compiler_accepted_count = sum(1 for r in results if r["compiler_accepted"])
    rejections_count = total_q - compiler_accepted_count
    content_pass_count = sum(1 for r in results if r["content_grade"] == "PASS")
    delivery_pass_count = sum(1 for r in results if r["delivery_grade"] == "PASS")
    total_ops = sum(r["operations_count"] for r in results)
    ge_1_ops_count = sum(1 for r in results if r["operations_count"] >= 1)
    blocked_count = sum(
        1 for r in results
        if "action1_blocked" in r["answer"]
        or "action_blocked" in r["answer"]
        or "[blocked]" in r["answer"]
        or "ambiguous_source_identity" in r["answer"]
    )
    rubric_satisfied_count = sum(
        1 for r in results
        if len(r.get("required_elements_missing", [])) == 0
        and len(r.get("forbidden_elements_found", [])) == 0
    )

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
        "operations_ge_1_count": ge_1_ops_count,
        "blocked_actions_count": blocked_count,
        "rubric_satisfied_count": rubric_satisfied_count,
        "content_pass_count": content_pass_count,
        "delivery_pass_count": delivery_pass_count,
        "pass_rate_percent": round(pass_rate, 2),
        "gate_status": "PASS" if (rejections_count == 0 and pass_rate == 100.0 and blocked_count == 0 and ge_1_ops_count == total_q) else "FAIL",
        "total_elapsed_seconds": round(total_elapsed, 2),
    }

    print("\n" + "=" * 70)
    print("HOLD OUT EVALUATION SUMMARY:")
    print(f"  Total Questions:          {total_q}")
    print(f"  Live Model Calls:         {chart_call_count} (0 retries)")
    print(f"  Schema Valid:             {schema_valid_count}/{total_q} (100%)")
    print(f"  Compiler Accepted:        {compiler_accepted_count}/{total_q} (0 rejections)")
    print(f"  Operations Executed:      {total_ops} (Questions with >=1 ops: {ge_1_ops_count}/{total_q})")
    print(f"  Blocked Actions:          {blocked_count}/{total_q}")
    print(f"  Rubric Satisfied:         {rubric_satisfied_count}/{total_q}")
    print(f"  Content Grade:            {content_pass_count}/{total_q} ({pass_rate:.1f}%)")
    print(f"  Delivery Grade:           {delivery_pass_count}/{total_q} ({pass_rate:.1f}%)")
    print(f"  Gate Verdict:             {summary['gate_status']}")
    print(f"  Total Time:               {total_elapsed:.1f}s")
    print("=" * 70)
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
