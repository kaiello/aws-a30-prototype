"""Evaluation runner for Gate 6.3: Blind Hardening Benchmark.

Evaluates 20 blind hardening queries across 5 distinct slices against answer_whole_standard_question:
- Slice 1: Nonstandard shop terms with embedded lightface redirects (ground clamp, ground lead, welding ground, silver soldering)
- Slice 2: Process variations vs normative Table A4 compound suffixes (GMAW-S, GTAW-P, PAW)
- Slice 3: Historical process designations and classifications (BB, CAW-S, bronze welding vs brazing, heliarc)
- Slice 4: Spatial callout diagram queries (Butt joint, Scarf joint, T-joint panel (E))
- Slice 5: Homographs, compound rules, and nonstandard terminology (AB, Table A4 suffixes, burning, puddle, stick welding, mig welding)

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


class DeterministicFixtureAdapter:
    """Adapter to load quarantined synthetic planner fixtures for benchmark verification."""
    def __init__(self, fixtures_dir: Path):
        self.fixtures_dir = fixtures_dir

    def plan_with_semantic_expansion(self, question_text: str, req_dir: Optional[Path] = None, stores: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.plan_whole_standard_question(question_text, req_dir=req_dir, stores=stores)

    def plan_whole_standard_question(self, question_text: str, req_dir: Optional[Path] = None, stores: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from src.deepseek_v41_adapter import DeepSeekV41Config, DeepSeekV41PlannerAdapter
        adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"))
        key = adapter.compute_replay_key(adapter.build_whole_standard_prompt(question_text))
        fixture_p = self.fixtures_dir / f"{key}.json"
        if not fixture_p.exists():
            raise ValueError(f"INSUFFICIENT_EVIDENCE: Missing fixture for key {key} at {fixture_p}")
        data = json.loads(fixture_p.read_text(encoding="utf-8"))
        return data.get("parsed_plan", {})


def evaluate_blind_hardening_benchmark(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    write_results: bool = True,
    use_replay_cassettes: bool = False,
    strict_replay: bool = False,
    use_fixtures: bool = False,
) -> Dict[str, Any]:
    """Execute Gate 6.3 20-query blind hardening benchmark with transparent replay accounting."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = (root / "storage/evidence_v2/phase6_3_blind_hardening_001").resolve()
    else:
        output_dir = Path(output_dir).resolve()

    q_file = output_dir / "questions.json"
    r_file = output_dir / "rubric.json"

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubric_data = json.loads(r_file.read_text(encoding="utf-8"))
    rubrics = rubric_data["rubrics"]

    stores = get_whole_standard_stores(root)
    planner = DeterministicQuestionPlanner(root)

    replay_adapter = None
    if use_replay_cassettes:
        from src.deepseek_v41_adapter import DeepSeekV41Config, DeepSeekV41PlannerAdapter
        replay_adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"), root=root)

    fixtures_dir = root / "storage/model_replays/deterministic_planner_fixtures"

    results = []
    passed_count = 0
    replayed_model_count = 0
    synthetic_fixtures_count = 0
    deterministic_fallbacks_count = 0

    for item in questions:
        qid = item["id"]
        query = item["query"]
        category = item["category"]
        slice_name = item.get("slice_name", category)
        rubric = rubrics[qid]

        item_planner = planner
        planner_source = "deterministic_planner"
        if use_replay_cassettes and replay_adapter:
            key = replay_adapter.compute_replay_key(replay_adapter.build_whole_standard_prompt(query))
            model_cassette_p = replay_adapter.replay_dir / f"{key}.json"
            fixture_p = fixtures_dir / f"{key}.json"

            if model_cassette_p.exists():
                item_planner = replay_adapter
                planner_source = "deepseek_v4_1_replay_cassette"
                replayed_model_count += 1
            elif use_fixtures and fixture_p.exists():
                # Quarantined fixture
                item_planner = DeterministicFixtureAdapter(fixtures_dir)
                planner_source = "synthetic_planner_fixture"
                synthetic_fixtures_count += 1
            else:
                if strict_replay:
                    raise RuntimeError(f"Strict replay failure: no genuine model replay cassette found for query {qid} ({key})")
                deterministic_fallbacks_count += 1
        else:
            deterministic_fallbacks_count += 1

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
            "passed": test_passed,
            "status_match": status_match,
            "crop_match": crop_match,
            "actual_status": status,
            "expected_status": exp_status,
            "requires_diagram_crop": act_req_crop,
            "expected_requires_diagram_crop": exp_req_crop,
            "required_elements_missing": req_missing,
            "forbidden_elements_hit": forb_hit,
            "answer_preview": answer[:160] + "..." if len(answer) > 160 else answer,
            "primary_target": rubric.get("primary_target"),
            "evidence_locator": execution.get("evidence_locator"),
            "planner_source": planner_source,
        })

    summary = {
        "gate": "Gate 6.3",
        "benchmark": "phase6_3_blind_hardening_001",
        "total_queries": len(questions),
        "passed": passed_count,
        "failed": len(questions) - passed_count,
        "pass_rate": round(passed_count / len(questions) * 100, 2),
        "model_replays_count": replayed_model_count,
        "synthetic_fixtures_count": synthetic_fixtures_count,
        "deterministic_fallbacks_count": deterministic_fallbacks_count,
        "results": results,
    }

    if write_results:
        res_file = output_dir / "results.json"
        res_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gate 6.3 Blind Hardening Benchmark Evaluation")
    parser.add_argument("--benchmark-dir", type=str, default=None, help="Path to benchmark directory")
    parser.add_argument("--use-replay-cassettes", action="store_true", help="Use offline DeepSeek-V4.1 replay cassettes for matching queries")
    parser.add_argument("--strict-replay", action="store_true", help="Fail if any query cannot be served by a genuine model replay cassette")
    parser.add_argument("--use-fixtures", action="store_true", help="Allow fallback to quarantined synthetic planner fixtures")
    parser.add_argument("--no-write", action="store_true", help="Do not overwrite results.json")
    args = parser.parse_args()

    bench_dir = Path(args.benchmark_dir) if args.benchmark_dir else None
    summary = evaluate_blind_hardening_benchmark(
        output_dir=bench_dir,
        write_results=not args.no_write,
        use_replay_cassettes=args.use_replay_cassettes,
        strict_replay=args.strict_replay,
        use_fixtures=args.use_fixtures,
    )
    print(f"Gate 6.3 Blind Hardening Benchmark: {summary['passed']}/{summary['total_queries']} passed ({summary['pass_rate']}%)")
    print(f"  Model Replays: {summary['model_replays_count']} | Synthetic Fixtures: {summary['synthetic_fixtures_count']} | Deterministic Fallbacks: {summary['deterministic_fallbacks_count']}")
    if summary["failed"] > 0:
        sys.exit(1)
