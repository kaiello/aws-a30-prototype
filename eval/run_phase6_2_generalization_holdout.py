"""Evaluation runner for Gate 6.2: Store-Driven Composition & Generalization Holdout Benchmark.

Evaluates 20 unseen queries across 5 distinct slices against answer_whole_standard_question:
- Slice 1: Unseen IS_A Process Variation Families (GMAW, OFC, SAW, RSEW)
- Slice 2: Unseen Clause 4 See / See also Graph Neighborhoods (backfire, bend test, agglomerated flux, base metal zone)
- Slice 3: Unseen Weld Test Positions & Unqualified Dual-Sense Disambiguation (5G, 3G, 4F, AB + 2G)
- Slice 4: Unseen Polysemous Callouts, Obsolete Comparisons & 3-Tier Validation (bevel/groove/root face, backing shoe, FOW vs FSW, OFC-P-ME / GMAW-X-SA / GTAW-AU-MA)
- Slice 5: Unseen DeepSeek-V4.1 Multi-Operation Replay Cassettes & Boundary Guards (GMAW-P-SA + B54, FOW vs FSW + A5, braze multi-POS, EBW-AU-SA + A7)

Asserts 100% PASS rate with strict modality-appropriate conditional crop provenance.
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


def evaluate_generalization_holdout_benchmark(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    write_results: bool = False,
    use_replay_for_slice5: bool = False,
) -> Dict[str, Any]:
    """Execute Gate 6.2 20-query store-driven composition and generalization holdout benchmark."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = (root / "storage/evidence_v2/phase6_2_generalization_holdout_001").resolve()
    else:
        output_dir = Path(output_dir).resolve()

    q_file = output_dir / "questions.json"
    r_file = output_dir / "rubric.json"

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubric_data = json.loads(r_file.read_text(encoding="utf-8"))
    rubrics = rubric_data["rubrics"]

    stores = get_whole_standard_stores(root)
    deterministic_planner = DeterministicQuestionPlanner(root)

    replay_adapter = None
    if use_replay_for_slice5:
        from src.deepseek_v41_adapter import DeepSeekV41Config, DeepSeekV41PlannerAdapter
        replay_adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"), root=root)

    results = []
    passed_count = 0

    for item in questions:
        qid = item["id"]
        query = item["query"]
        category = item["category"]
        slice_name = item.get("slice_name", category)
        rubric = rubrics[qid]

        item_planner = deterministic_planner
        if use_replay_for_slice5 and replay_adapter:
            key = replay_adapter.compute_replay_key(replay_adapter.build_whole_standard_prompt(query))
            if (replay_adapter.replay_dir / f"{key}.json").exists():
                item_planner = replay_adapter

        resp = answer_whole_standard_question(query, item_planner, stores=stores)
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

        # Check conditional diagram crop requirement
        exp_req_crop = rubric.get("requires_diagram_crop")
        act_req_crop = resp.get("requires_diagram_crop")
        crop_match = (exp_req_crop is None) or (act_req_crop == exp_req_crop)

        test_passed = status_match and (len(req_missing) == 0) and (len(forb_hit) == 0) and crop_match
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
            "requires_diagram_crop": act_req_crop,
            "expected_requires_diagram_crop": exp_req_crop,
            "crop_match": crop_match,
            "crop_path": resp.get("crop_path"),
            "printed_page": resp.get("printed_page"),
            "pdf_index": resp.get("pdf_index"),
            "evidence_locator": resp.get("evidence_locator"),
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
        "version": "phase6_2_generalization_holdout_results_v1.0",
        "benchmark_name": "Gate 6.2 Store-Driven Composition & Generalization Holdout Benchmark",
        "total_questions": total_q,
        "passed_count": passed_count,
        "pass_rate_percent": pass_rate,
        "gate_status": "PASS" if passed_count == total_q else "FAIL",
        "results": results,
    }

    if write_results:
        res_file = output_dir / "results.json"
        res_bytes = json.dumps(output_payload, indent=2).encode("utf-8")
        res_file.write_bytes(res_bytes)
        res_sha = hashlib.sha256(res_bytes).hexdigest()
        print(f"Gate 6.2 Generalization Holdout Benchmark: {passed_count}/{total_q} passed ({pass_rate:.1f}%)")
        print(f"Results written to: {res_file.resolve().relative_to(root.resolve())} (SHA-256: {res_sha})")
    else:
        print(f"Gate 6.2 Generalization Holdout Benchmark: {passed_count}/{total_q} passed ({pass_rate:.1f}%) [in-memory]")

    return output_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gate 6.2 Generalization Holdout Benchmark")
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root directory")
    parser.add_argument("--benchmark-dir", "--output-dir", dest="output_dir", type=Path, default=None, help="Benchmark directory containing questions.json and rubric.json")
    parser.add_argument("--use-replay-cassettes", action="store_true", help="Use DeepSeek replay adapter for Slice 5 queries")
    parser.add_argument("--no-write", action="store_true", help="Do not write results to disk (dry run)")
    args = parser.parse_args()

    payload = evaluate_generalization_holdout_benchmark(
        root=args.root,
        output_dir=args.output_dir,
        write_results=not args.no_write,
        use_replay_for_slice5=args.use_replay_cassettes,
    )
    sys.exit(0 if payload["gate_status"] == "PASS" else 1)
