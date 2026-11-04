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
import re
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
    write_results: bool = False,
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

    cov_file = root / "storage/manifests/coverage_manifest.json"
    cov_data = json.loads(cov_file.read_text(encoding="utf-8")) if cov_file.exists() else {}
    ingested_pdf_pages = set(cov_data.get("page_accounting", {}).get("ingested_pdf_indices_1_based", []))
    excluded_pdf_pages = set(cov_data.get("page_accounting", {}).get("excluded_pdf_indices_1_based", []))

    replay_adapter = None
    if use_replay_cassettes:
        from src.deepseek_v41_adapter import DeepSeekV41Config, DeepSeekV41PlannerAdapter
        replay_adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"), root=root)

    fixtures_dir = root / "storage/model_replays/deterministic_planner_fixtures"

    results = []
    passed_count = 0
    content_passed = 0
    coord_passed = 0
    crop_passed = 0
    body_meta_passed = 0
    planner_breakdown = {}
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

        if planner_source not in planner_breakdown:
            planner_breakdown[planner_source] = {"total": 0, "passed": 0}
        planner_breakdown[planner_source]["total"] += 1

        resp = answer_whole_standard_question(query, item_planner, stores=stores)
        plan = resp.get("plan", {})
        execution = resp.get("execution", {})
        status = execution.get("status")
        answer = resp.get("answer", "")
        elements_present = execution.get("elements_present", [])
        trace = plan.get("semantic_expansion_trace", {})

        exp_status = rubric["expected_status"]
        status_match = (status == exp_status)

        # 1. Content check (required/forbidden elements)
        req_missing = [req for req in rubric["required_elements"] if req.lower() not in answer.lower()]
        forb_hit = [forb for forb in rubric["forbidden_elements"] if forb.lower() in answer.lower()]
        content_ok = status_match and (len(req_missing) == 0) and (len(forb_hit) == 0)
        if content_ok:
            content_passed += 1

        # 2. Coordinate Formula Gate
        p_page = resp.get("printed_page")
        p_pdf = resp.get("pdf_index")
        coord_ok = (
            isinstance(p_page, int)
            and isinstance(p_pdf, int)
            and (p_pdf - p_page == 12)
            and (p_pdf in ingested_pdf_pages)
            and (p_pdf not in excluded_pdf_pages)
        )
        if coord_ok:
            coord_passed += 1

        # 3. Crop-to-Locator Identity Gate & Abstention Gate
        crop_path = resp.get("crop_path")
        act_req_crop = resp.get("requires_diagram_crop")
        exp_req_crop = rubric.get("requires_diagram_crop")

        crop_identity_ok = True
        if act_req_crop:
            if not crop_path or not (root / crop_path).exists():
                crop_identity_ok = False
            else:
                loc_str = (resp.get("evidence_locator") or execution.get("evidence_locator") or "").lower()
                crop_name = Path(crop_path).name.lower()
                m_loc = re.search(r"figure_([ab]\d+[a-z]*)", loc_str)
                m_crop = re.search(r"(?:figure_)?([ab]\d+[a-z]*)", crop_name)
                if m_loc and m_crop and m_loc.group(1) != m_crop.group(1):
                    crop_identity_ok = False
                m_crop_page = re.search(r"_p(\d+)(?:_|\.|$)", crop_name)
                if m_crop_page and isinstance(p_page, int) and int(m_crop_page.group(1)) != p_page:
                    crop_identity_ok = False
        else:
            if crop_path is not None:
                crop_identity_ok = False

        crop_match = (exp_req_crop is None) or (act_req_crop == exp_req_crop and crop_identity_ok)
        if crop_match:
            crop_passed += 1

        # 4. Body-to-Metadata Consistency Gate
        body_p_matches = [int(m) for m in re.findall(r"(?:printed\s+p\.?|p\.)\s*(\d+)", answer, re.IGNORECASE)]
        body_pdf_matches = [int(m) for m in re.findall(r"PDF\s+(?:index\s+)?(\d+)", answer, re.IGNORECASE)]
        prov_pdf_matches = [int(m) for m in re.findall(r"obs:pdf:(\d+):", " ".join(execution.get("normative_provenance", [])))]

        body_meta_ok = True
        if exp_status != "ABSTAIN_OUT_OF_SCOPE":
            if body_p_matches and p_page not in body_p_matches:
                if not (prov_pdf_matches and p_pdf in prov_pdf_matches):
                    elem_spans = {
                        "table_a1": range(69, 72),
                        "figure_b23": range(114, 117),
                        "annex_c": range(159, 165),
                        "table_a3": range(72, 74),
                    }
                    loc_key = str(execution.get("evidence_locator", "")).split(":")[0]
                    span = elem_spans.get(loc_key)
                    if not (span and p_page in span and any(bp in span for bp in body_p_matches)):
                        body_meta_ok = False
            if body_pdf_matches and p_pdf not in body_pdf_matches:
                if not (prov_pdf_matches and p_pdf in prov_pdf_matches):
                    body_meta_ok = False
            if not body_p_matches and not body_pdf_matches and prov_pdf_matches:
                if p_pdf not in prov_pdf_matches:
                    body_meta_ok = False
        if body_meta_ok:
            body_meta_passed += 1

        # 5. Overall Strict Pass Gate
        test_passed = content_ok and crop_match and coord_ok and body_meta_ok
        if test_passed:
            passed_count += 1
            planner_breakdown[planner_source]["passed"] += 1

        results.append({
            "id": qid,
            "category": category,
            "slice_name": slice_name,
            "query": query,
            "passed": test_passed,
            "status_match": status_match,
            "crop_match": crop_match,
            "coord_match": coord_ok,
            "body_meta_match": body_meta_ok,
            "actual_status": status,
            "expected_status": exp_status,
            "printed_page": p_page,
            "pdf_index": p_pdf,
            "crop_path": crop_path,
            "requires_diagram_crop": act_req_crop,
            "expected_requires_diagram_crop": exp_req_crop,
            "required_elements_missing": req_missing,
            "forbidden_elements_hit": forb_hit,
            "answer_preview": answer[:160] + "..." if len(answer) > 160 else answer,
            "primary_target": rubric.get("primary_target"),
            "evidence_locator": execution.get("evidence_locator"),
            "planner_source": planner_source,
        })

    total_q = len(questions)
    summary = {
        "gate": "Gate 6.3",
        "benchmark": "phase6_3_blind_hardening_001",
        "total_queries": total_q,
        "passed": passed_count,
        "failed": total_q - passed_count,
        "pass_rate": round(passed_count / total_q * 100, 2),
        "answer_content_accuracy": round(content_passed / total_q * 100, 2),
        "coordinate_provenance_accuracy": round(coord_passed / total_q * 100, 2),
        "crop_locator_consistency": round(crop_passed / total_q * 100, 2),
        "body_metadata_alignment": round(body_meta_passed / total_q * 100, 2),
        "overall_strict_pass_rate": round(passed_count / total_q * 100, 2),
        "planner_breakdown": {
            src: {
                "total": stats["total"],
                "passed": stats["passed"],
                "pass_rate": round(stats["passed"] / stats["total"] * 100, 2) if stats["total"] else 0.0,
            }
            for src, stats in planner_breakdown.items()
        },
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
    parser.add_argument("--write", action="store_true", help="Explicitly overwrite results.json")
    parser.add_argument("--no-write", action="store_true", help="Do not overwrite results.json")
    args = parser.parse_args()

    bench_dir = Path(args.benchmark_dir) if args.benchmark_dir else None
    summary = evaluate_blind_hardening_benchmark(
        output_dir=bench_dir,
        write_results=(args.write and not args.no_write),
        use_replay_cassettes=args.use_replay_cassettes,
        strict_replay=args.strict_replay,
        use_fixtures=args.use_fixtures,
    )
    print(f"Gate 6.3 Blind Hardening Benchmark: {summary['passed']}/{summary['total_queries']} passed ({summary['pass_rate']}%)")
    print(f"  Model Replays: {summary['model_replays_count']} | Synthetic Fixtures: {summary['synthetic_fixtures_count']} | Deterministic Fallbacks: {summary['deterministic_fallbacks_count']}")
    if summary["failed"] > 0:
        sys.exit(1)
