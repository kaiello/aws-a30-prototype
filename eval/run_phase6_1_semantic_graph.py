"""Evaluation runner for Gate 6.1: Polysemous Welding NER, 3-Tier Grammar & Semantic Graph Benchmark.

Evaluates 15 queries across 5 distinct slices against answer_whole_standard_question:
- Slice 1: Polysemous Callout + Glossary Dual-Routing
- Slice 2: 3-Tier Compound Designations & Invalid Variant Rejection
- Slice 3: Contextual Position & Homograph Sense Disambiguation
- Slice 4: See also & Taxonomy Sibling Expansion
- Slice 5: DeepSeek Replay Multi-Hop over Semantic Neighborhoods

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


def evaluate_semantic_graph_benchmark(
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    write_results: bool = False,
) -> Dict[str, Any]:
    """Execute Gate 6.1 15-query NER, 3-tier grammar and semantic graph benchmark."""
    if root is None:
        root = ROOT
    if output_dir is None:
        output_dir = root / "storage/evidence_v2/phase6_1_semantic_graph_001"

    q_file = output_dir / "ner_routing_questions.json"
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
        "version": "phase6_1_semantic_graph_results_v1.0",
        "benchmark_name": "Gate 6.1 Polysemous Welding NER, 3-Tier Grammar & Semantic Graph Benchmark",
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
        print(f"Gate 6.1 Semantic Graph Benchmark: {passed_count}/{total_q} passed ({pass_rate:.1f}%)")
        print(f"Results written to: {res_file.relative_to(root)} (SHA-256: {res_sha})")
    else:
        print(f"Gate 6.1 Semantic Graph Benchmark: {passed_count}/{total_q} passed ({pass_rate:.1f}%) [in-memory]")

    return output_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gate 6.1 Semantic Graph Benchmark")
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root directory")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory for benchmark")
    parser.add_argument("--no-write", action="store_true", help="Do not write results to disk (dry run)")
    args = parser.parse_args()

    payload = evaluate_semantic_graph_benchmark(root=args.root, output_dir=args.output_dir, write_results=not args.no_write)
    sys.exit(0 if payload["gate_status"] == "PASS" else 1)
