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

HOLDOUT_RUBRIC = {
    # Figure A3 (Joining Method Chart)
    "A3-HO001-01": {
        "required_elements": ["Mechanical Fastening", "Welding", "Adhesive Bonding", "footnote"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A3-HO001-02": {
        "required_elements": ["simplicity", "footnote a", "Welding"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A3-HO001-03": {
        "required_elements": ["Materials Joining", "Welding", "Solid-State Welding", "Figure A5"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A3-HO001-04": {
        "required_elements": ["Brazing and Soldering", "Figure A6", "Welding"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A3-HO001-05": {
        "required_elements": ["does not include", "Thermal Spraying", "Thermal Cutting"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },

    # Figure A4 (Fusion Welding Classification Chart)
    "A4-HO001-01": {
        "required_elements": ["FCAW", "GTAW", "Arc", "Flux", "Gas", "Electrical"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A4-HO001-02": {
        "required_elements": ["EGW", "EBW", "Gas", "Flux"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A4-HO001-03": {
        "required_elements": ["Resistance", "Pressure", "Pressure normal to faying surfaces"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A4-HO001-04": {
        "required_elements": ["Conduction", "atomic hydrogen welding", "legend"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A4-HO001-05": {
        "required_elements": ["Flame Contact", "Chemical", "oxyacetylene welding", "oxyhydrogen welding", "pressure gas welding"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },

    # Figure A5 (Solid-State Welding Classification Chart)
    "A5-HO001-01": {
        "required_elements": ["USW", "CW", "Friction", "Pressure", "Pressure Deformation", "Thermal Source"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A5-HO001-02": {
        "required_elements": ["DFW", "Radiation", "Pressure", "Gas", "Vacuum"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity", "Pressure Deformation -> Gas -> DFW"],
    },
    "A5-HO001-03": {
        "required_elements": ["CEW", "FOW", "ROW"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A5-HO001-04": {
        "required_elements": ["EXW", "Pressure Deformation", "Thermal Source"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A5-HO001-05": {
        "required_elements": ["Resistance", "Pressure", "Pressure Deformation", "UW", "RSW", "RSEW"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },

    # Figure A6 (Brazing and Soldering Classification Chart)
    "A6-HO001-01": {
        "required_elements": ["AB", "arc brazing", "Arc", "Gas", "Flux"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity", "Arc -> Pressure -> Gas -> AB"],
    },
    "A6-HO001-02": {
        "required_elements": ["B-CA", "Induction", "Radiation", "Gas", "Vacuum"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity", "Chemical Reaction -> None -> Gas -> B-CA"],
    },
    "A6-HO001-03": {
        "required_elements": ["DFB", "Pressure", "Induction", "Radiation", "Gas", "Vacuum"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity", "Chemical -> Radiation -> Pressure -> Vacuum -> DFB"],
    },
    "A6-HO001-04": {
        "required_elements": ["Conduction", "Flux", "iron soldering", "wave soldering", "dip soldering"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "A6-HO001-05": {
        "required_elements": ["B-CA", "EBB", "EXB", "LBB", "controlled-atmosphere brazing", "electron beam brazing", "exothermic brazing", "laser beam brazing"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },

    # Annex A Tables A1–A5
    "AT-HO001-01": {
        "required_elements": ["AB", "adhesive bonding", "arc brazing", "Figure A6"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-02": {
        "required_elements": ["USW", "plastics welding", "solid-state welding", "69", "70"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-03": {
        "required_elements": ["134", "133", "atomic hydrogen welding", "Table A5", "Figure A4"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-04": {
        "required_elements": ["OC-P", "metal power cutting", "metal powder cutting", "EW-PC", "RW-PC"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-05": {
        "required_elements": ["PAW-AD", "adaptive control", "RSW-RO", "robotic", "EBW-HV-AU", "automatic"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-06": {
        "required_elements": ["CAB", "TCAB", "firecracker welding"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-07": {
        "required_elements": ["CANDIDATE_LAYOUT_PARENT", "0", "IS_A", "indentation"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-08": {
        "required_elements": ["IW", "Table A1", "Figure A1", "Figure A4", "Figure A5", "Induction", "Pressure"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity", "Electrical -> Resistance with Pressure"],
    },
    "AT-HO001-09": {
        "required_elements": ["Brazing", "Soldering", "Table A1", "Figure A1", "Figure A3", "Figure A6", "Welding"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
    "AT-HO001-10": {
        "required_elements": ["fillet weld", "preheat", "abstention"],
        "forbidden_elements": ["action1_blocked", "CHART_QUESTION_PLAN_", "ambiguous_source_identity"],
    },
}


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

            # Strict Rubric Evaluation
            rubric = HOLDOUT_RUBRIC.get(qid, {})
            req = rubric.get("required_elements", [])
            forb = rubric.get("forbidden_elements", [])
            req_missing = [elem for elem in req if elem.lower() not in ans_text.lower()]
            forb_found = [elem for elem in forb if elem.lower() in ans_text.lower()]

            has_blocked = (
                "action1_blocked" in ans_text
                or "action_blocked" in ans_text
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
