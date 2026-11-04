"""Evaluation runner for Gate 6.6: Phase 4 Reader Qualification with Gold Evidence & Diagnostic Separation.

Evaluates 24 benchmark queries across 4 tracks:
- Track 1 (`gold_arm_a`): Coarse Locator Only (`GOLD_ARM_A_COARSE_LOCATOR`)
- Track 2 (`gold_arm_b`): 300-DPI Crop + Primary Caption (`GOLD_ARM_B_CROP_AND_CAPTION`)
- Track 3 (`gold_arm_c`): Complete Functional Evidence Bundle (`GOLD_ARM_C_COMPLETE_GOLD_EVIDENCE`)
- Track 4 (`retrieved_whole_standard`): Live End-to-End Whole-Standard Retrieval + Reader

Classifies every query evaluation into the 5-class failure taxonomy (+ PASS_SUPPORTED) and produces
`gold_packets.json` and `results.json` when explicitly invoked with `--write`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)
from src.reader_qualification import (
    build_gold_evidence_packet,
    classify_diagnostic_outcome,
    compose_from_gold_arm,
    prepare_reader_evidence_arm,
)


def _score_single_response(
    qid: str,
    query: str,
    category: str,
    slice_name: str,
    rubric: Dict[str, Any],
    resp: Dict[str, Any],
    track: str,
    root: Path,
    ingested_pdf_pages: set[int],
    excluded_pdf_pages: set[int],
    gold_arm_c_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate a single response against the 5 provenance gates and classify its diagnostic outcome."""
    execution = resp.get("execution") or {}
    status = execution.get("status")
    answer = resp.get("answer") or ""

    exp_status = rubric["expected_status"]
    status_match = (status == exp_status)
    is_refusal_expected = exp_status in {"ABSTAIN_OUT_OF_SCOPE", "REFUSAL_OUT_OF_SCOPE", "REFUSAL_OUT_OF_RANGE"}

    # 1. Content Gate
    req_missing = [req for req in rubric["required_elements"] if req.lower() not in answer.lower()]
    forb_hit = [forb for forb in rubric["forbidden_elements"] if forb.lower() in answer.lower()]
    content_ok = status_match and (len(req_missing) == 0) and (len(forb_hit) == 0)

    # 2. Coordinate Formula Gate
    p_page = resp.get("printed_page")
    p_pdf = resp.get("pdf_index")
    if is_refusal_expected:
        coord_ok = (p_page is None and p_pdf is None)
    else:
        coord_ok = (
            isinstance(p_page, int)
            and isinstance(p_pdf, int)
            and (p_pdf - p_page == 12)
            and (p_pdf in ingested_pdf_pages)
            and (p_pdf not in excluded_pdf_pages)
        )

    # 3. Crop-to-Locator Identity & Page Gate
    crop_path = resp.get("crop_path")
    act_req_crop = bool(resp.get("requires_diagram_crop"))
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

    # 4. Body-to-Metadata Consistency Gate
    body_p_matches = [int(m) for m in re.findall(r"(?:printed\s+p\.?| p\.)\s*(\d+)", answer, re.IGNORECASE)]
    body_pdf_matches = [int(m) for m in re.findall(r"PDF\s+(?:index\s+)?(\d+)", answer, re.IGNORECASE)]
    prov_pdf_matches = [int(m) for m in re.findall(r"obs:pdf:(\d+):", " ".join(execution.get("normative_provenance") or []))]

    body_meta_ok = True
    if not is_refusal_expected:
        if body_p_matches and p_page not in body_p_matches:
            if not (prov_pdf_matches and p_pdf in prov_pdf_matches):
                elem_spans = {
                    "table_a1": range(69, 72),
                    "figure_b23": range(114, 117),
                    "annex_c": range(159, 165),
                    "table_a3": range(72, 74),
                }
                loc_key = str(resp.get("evidence_locator") or execution.get("evidence_locator") or "").split(":")[0]
                span = elem_spans.get(loc_key)
                if not (span and p_page in span and any(bp in span for bp in body_p_matches)):
                    body_meta_ok = False
        if body_pdf_matches and p_pdf not in body_pdf_matches:
            if not (prov_pdf_matches and p_pdf in prov_pdf_matches):
                body_meta_ok = False
        if not body_p_matches and not body_pdf_matches and prov_pdf_matches:
            if p_pdf not in prov_pdf_matches:
                body_meta_ok = False

    # 5. Overall Strict Pass Gate
    test_passed = content_ok and crop_match and coord_ok and body_meta_ok

    record: Dict[str, Any] = {
        "id": qid,
        "track": track,
        "category": category,
        "slice_name": slice_name,
        "query": query,
        "passed": test_passed,
        "content_ok": content_ok,
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
        "evidence_locator": resp.get("evidence_locator") or execution.get("evidence_locator"),
        "answer_preview": answer[:160] + "..." if len(answer) > 160 else answer,
    }
    record["diagnostic_class"] = classify_diagnostic_outcome(
        record,
        gold_arm_c_record=gold_arm_c_record,
        store_integrity_ok=True,
    )
    return record


def _summarize_track(track_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    passed = sum(1 for r in records if r["passed"])
    content_passed = sum(1 for r in records if r["content_ok"])
    coord_passed = sum(1 for r in records if r["coord_match"])
    crop_passed = sum(1 for r in records if r["crop_match"])
    body_meta_passed = sum(1 for r in records if r["body_meta_match"])

    diag_counts: Dict[str, int] = {}
    for r in records:
        dc = r["diagnostic_class"]
        diag_counts[dc] = diag_counts.get(dc, 0) + 1

    return {
        "track": track_name,
        "total_queries": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total * 100, 2) if total else 0.0,
        "answer_content_accuracy": round(content_passed / total * 100, 2) if total else 0.0,
        "coordinate_provenance_accuracy": round(coord_passed / total * 100, 2) if total else 0.0,
        "crop_locator_consistency": round(crop_passed / total * 100, 2) if total else 0.0,
        "body_metadata_alignment": round(body_meta_passed / total * 100, 2) if total else 0.0,
        "overall_strict_pass_rate": round(passed / total * 100, 2) if total else 0.0,
        "diagnostic_breakdown": diag_counts,
        "results": records,
    }


def evaluate_reader_qualification_benchmark(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    write_results: bool = False,
) -> Dict[str, Any]:
    """Execute Gate 6.6 24-query reader qualification benchmark across 3 gold arms + retrieved track."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = (root / "storage/evidence_v2/phase6_6_reader_qualification_001").resolve()
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

    gold_packets: List[Dict[str, Any]] = []
    arm_a_records: List[Dict[str, Any]] = []
    arm_b_records: List[Dict[str, Any]] = []
    arm_c_records: List[Dict[str, Any]] = []
    retrieved_records: List[Dict[str, Any]] = []

    for item in questions:
        qid = item["id"]
        query = item["query"]
        category = item["category"]
        slice_name = item.get("slice_name", category)
        rubric = rubrics[qid]

        # Build gold packet once per query
        gold_packet = build_gold_evidence_packet(query, stores=stores, root=root)
        gold_packets.append({
            "id": qid,
            "category": category,
            "slice_name": slice_name,
            **gold_packet,
        })

        # Prepare and compose Arm C first so it can serve as the oracle reference for retrieved_whole_standard
        pkt_c = prepare_reader_evidence_arm(gold_packet, arm="C")
        resp_c = compose_from_gold_arm(query, pkt_c, stores=stores)
        rec_c = _score_single_response(
            qid, query, category, slice_name, rubric, resp_c, "gold_arm_c",
            root, ingested_pdf_pages, excluded_pdf_pages
        )
        arm_c_records.append(rec_c)

        # Arm A
        pkt_a = prepare_reader_evidence_arm(gold_packet, arm="A")
        resp_a = compose_from_gold_arm(query, pkt_a, stores=stores)
        rec_a = _score_single_response(
            qid, query, category, slice_name, rubric, resp_a, "gold_arm_a",
            root, ingested_pdf_pages, excluded_pdf_pages, gold_arm_c_record=rec_c
        )
        arm_a_records.append(rec_a)

        # Arm B
        pkt_b = prepare_reader_evidence_arm(gold_packet, arm="B")
        resp_b = compose_from_gold_arm(query, pkt_b, stores=stores)
        rec_b = _score_single_response(
            qid, query, category, slice_name, rubric, resp_b, "gold_arm_b",
            root, ingested_pdf_pages, excluded_pdf_pages, gold_arm_c_record=rec_c
        )
        arm_b_records.append(rec_b)

        # Live Retrieved Whole-Standard Track
        resp_ret = answer_whole_standard_question(query, planner, stores=stores)
        rec_ret = _score_single_response(
            qid, query, category, slice_name, rubric, resp_ret, "retrieved_whole_standard",
            root, ingested_pdf_pages, excluded_pdf_pages, gold_arm_c_record=rec_c
        )
        retrieved_records.append(rec_ret)

    tracks_summary = {
        "gold_arm_a": _summarize_track("gold_arm_a", arm_a_records),
        "gold_arm_b": _summarize_track("gold_arm_b", arm_b_records),
        "gold_arm_c": _summarize_track("gold_arm_c", arm_c_records),
        "retrieved_whole_standard": _summarize_track("retrieved_whole_standard", retrieved_records),
    }

    summary = {
        "gate": "Gate 6.6",
        "benchmark": "phase6_6_reader_qualification_001",
        "total_queries": len(questions),
        "gold_arm_a_pass_rate": tracks_summary["gold_arm_a"]["pass_rate"],
        "gold_arm_b_pass_rate": tracks_summary["gold_arm_b"]["pass_rate"],
        "gold_arm_c_pass_rate": tracks_summary["gold_arm_c"]["pass_rate"],
        "retrieved_whole_standard_pass_rate": tracks_summary["retrieved_whole_standard"]["pass_rate"],
        "retrieval_vs_reader_delta": round(
            tracks_summary["gold_arm_c"]["pass_rate"] - tracks_summary["retrieved_whole_standard"]["pass_rate"], 2
        ),
        "tracks": tracks_summary,
    }

    if write_results:
        gp_file = output_dir / "gold_packets.json"
        gp_file.write_text(json.dumps(gold_packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        res_file = output_dir / "results.json"
        res_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gate 6.6 Phase 4 Reader Qualification Benchmark")
    parser.add_argument("--benchmark-dir", type=str, default=None, help="Path to benchmark directory")
    parser.add_argument("--write", action="store_true", help="Explicitly write gold_packets.json and results.json")
    parser.add_argument("--no-write", action="store_true", help="Do not write gold_packets.json or results.json")
    args = parser.parse_args()

    bench_dir = Path(args.benchmark_dir) if args.benchmark_dir else None
    summary = evaluate_reader_qualification_benchmark(
        output_dir=bench_dir,
        write_results=(args.write and not args.no_write),
    )
    print(f"Gate 6.6 Reader Qualification Benchmark ({summary['total_queries']} queries):")
    for t_key in ("gold_arm_a", "gold_arm_b", "gold_arm_c", "retrieved_whole_standard"):
        t_info = summary["tracks"][t_key]
        print(f"  {t_key:26s}: {t_info['passed']:2d}/{t_info['total_queries']:2d} passed ({t_info['pass_rate']:6.2f}%) | {t_info['diagnostic_breakdown']}")
    if summary["tracks"]["gold_arm_c"]["failed"] > 0 or summary["tracks"]["retrieved_whole_standard"]["failed"] > 0:
        sys.exit(1)
