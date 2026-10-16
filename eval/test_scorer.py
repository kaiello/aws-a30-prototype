"""
test_scorer.py: Automated benchmark evaluation harness for AWS A3.0 prototype.
Evaluates the existing gold benchmark and reports legacy heuristics and route
diagnostics. Route diagnostics do not measure claim truth or evidence completeness:
- Document@1 (Standard Disambiguation & Scope Boundary Enforcement)
- Answer@1 (Primary Answer Accuracy)
- Legacy route recall, completeness and epistemic diagnostic fields (nullable)
"""

import sys
import json
import argparse
import datetime
import math
from numbers import Real
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import BENCHMARK_FILE, BASE_DIR, DEFAULT_ENGINE, DEEPSEEK_MODEL, GEMINI_MODEL, EMBEDDING_MODEL
from src.query import run_query
from src.citation_checker import verify_response
from src.answer_routes import resolve_answer_route


def _finite_metric(value):
    """Return a JSON-safe real number, preserving zero and excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _aggregate_legacy_metric(values):
    """Report an assessed-only mean with the full query denominator visible."""
    values = list(values)
    assessed = [number for value in values
                if (number := _finite_metric(value)) is not None]
    count = len(assessed)
    mean = math.fsum(value / count for value in assessed) if count else None
    return {"value": mean, "assessed_count": count, "total_count": len(values)}


def _format_metric(value, *, precision=2, percent=False):
    number = _finite_metric(value)
    if number is None:
        return "unassessed"
    return f"{number * 100 if percent else number:.{precision}f}{'%' if percent else ''}"


def _legacy_route_metrics(route):
    """A compatibility False is unmeasured when route recall is unassessed."""
    recall = _finite_metric(route.evidence_recall_score)
    completeness = (float(route.all_evidence_recovered)
                    if recall is not None and isinstance(route.all_evidence_recovered, bool)
                    else None)
    return {"evidence_recall": recall,
            "epistemic_score": _finite_metric(route.epistemic_score),
            "all_evidence": completeness}


def run_evaluation(
    benchmark_path: Path = BENCHMARK_FILE,
    mode: str = "mix",
    engine: str = DEFAULT_ENGINE,
    report_filename: str = "card08_benchmark_report.md",
    receipt_filename: str = "run_receipt_card08.json"
):
    if not benchmark_path.exists():
        print(f"Benchmark file not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print(f"\n========================================================")
    print(f"AWS A3.0 Grounded Evaluation: {len(benchmark)} Queries")
    print(f"Engine: {engine.upper()} | Mode: {mode}")
    print("Legacy benchmark heuristics and route diagnostics (not claim-truth assessment)")
    print(f"========================================================\n")
    
    results = []
    modality_counts = {}
    modality_passes = {}

    # Existing answer heuristics retain their full benchmark denominators.
    doc_at_1_passes = 0
    ans_at_1_passes = 0
    legacy_route_values = {"evidence_recall": [], "all_evidence": [], "epistemic_score": []}
    
    for item in benchmark:
        q_id = item["id"]
        modality = item["modality"]
        query = item["query"]
        
        modality_counts[modality] = modality_counts.get(modality, 0) + 1
        
        print(f"[{q_id}] ({modality.upper()}) {query}")
        query_res = run_query(query, mode=mode, engine=engine)
        ans = query_res["answer"]
        
        verification = verify_response(item, ans)
        is_pass = verification["pass"]

        # Resolve legacy navigation diagnostics; these do not assess answer truth.
        answer_route = resolve_answer_route(query, ans)
        route_metrics = _legacy_route_metrics(answer_route)
        for name, values in legacy_route_values.items():
            values.append(route_metrics[name])
        
        # Document@1: Correct standard cited or clean abstention
        doc_pass = False
        if modality == "abstention":
            doc_pass = verification["pass"] and ("out of scope" in ans.lower() or "not defined in aws a3.0" in ans.lower())
        else:
            doc_pass = verification["pass"] and ("clause" in ans.lower() or "table" in ans.lower() or "figure" in ans.lower())
        if doc_pass:
            doc_at_1_passes += 1

        # Answer@1: Primary answer pass
        if is_pass:
            ans_at_1_passes += 1

        if is_pass:
            modality_passes[modality] = modality_passes.get(modality, 0) + 1
            print(f"  -> PASS: {verification['reason']}")
            print(f"     [Legacy Route Diagnostic] Status: {answer_route.status} | Evidence: {len(answer_route.evidence_group)} items | Recall: {_format_metric(route_metrics['evidence_recall'])}")
        else:
            print(f"  -> FAIL: {verification['reason']}")
            
        results.append({
            "item": item,
            "query_result": query_res,
            "verification": verification,
            "answer_route": answer_route.to_dict(),
            "context_metrics": {
                "document_at_1": doc_pass,
                "answer_at_1": is_pass,
                "evidence_recall": route_metrics["evidence_recall"],
                "all_evidence": answer_route.all_evidence_recovered,
                "all_evidence_diagnostic": route_metrics["all_evidence"],
                "epistemic_score": route_metrics["epistemic_score"]
            }
        })
        print("-" * 60)

    # Summarize results
    total = len(benchmark)
    passed = sum(1 for r in results if r["verification"]["pass"])
    pass_rate = (passed / total) * 100 if total > 0 else 0

    doc_at_1_pct = (doc_at_1_passes / total) * 100 if total > 0 else 0
    ans_at_1_pct = (ans_at_1_passes / total) * 100 if total > 0 else 0
    legacy_metrics = {name: _aggregate_legacy_metric(values)
                      for name, values in legacy_route_values.items()}
    avg_evidence_recall = legacy_metrics["evidence_recall"]["value"]
    avg_all_evidence = legacy_metrics["all_evidence"]["value"]
    avg_epistemic_score = legacy_metrics["epistemic_score"]["value"]
    avg_evidence_recall_pct = avg_evidence_recall * 100 if avg_evidence_recall is not None else None
    all_evidence_pct = avg_all_evidence * 100 if avg_all_evidence is not None else None
    all_evidence_passes = sum(value == 1.0 for value in legacy_route_values["all_evidence"])
    
    active_model = GEMINI_MODEL if engine.lower() == "gemini" else DEEPSEEK_MODEL

    report_lines = [
        f"# AWS A3.0 Prototype Legacy Benchmark Report (Card 08)\n",
        f"**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Inference Engine:** {engine.upper()} (`{active_model}`)",
        f"**Retrieval Mode:** {mode}",
        f"**Total Queries Evaluated:** {total}",
        f"**Total Passed:** {passed} / {total} ({pass_rate:.1f}%)\n",
        "## Legacy Heuristics and Route Diagnostics\n",
        "Document@1 and Answer@1 retain the existing content heuristics. Route diagnostics below do not measure claim truth or evidence completeness. Their means include assessed values only; assessed counts retain the full query denominator. Unassessed values are not measured zeroes.\n",
        "| Legacy Metric / Diagnostic | Total | Passed / Assessed | Rate / Assessed-only Mean | Interpretation |",
        "|---|:---:|:---:|:---:|---|",
        f"| **Document@1** | {total} | {doc_at_1_passes} | **{doc_at_1_pct:.1f}%** | Document Disambiguation & Strict Scope Boundaries |",
        f"| **Answer@1** | {total} | {ans_at_1_passes} | **{ans_at_1_pct:.1f}%** | Primary Answer-Bearing Chunk Retrieval |",
        f"| **Legacy route recall diagnostic** | {total} | {legacy_metrics['evidence_recall']['assessed_count']} / {total} assessed | **{_format_metric(avg_evidence_recall, precision=1, percent=True)}** | Legacy route value; not measured evidence recall |",
        f"| **Legacy route completeness diagnostic** | {total} | {legacy_metrics['all_evidence']['assessed_count']} / {total} assessed; {all_evidence_passes} true | **{_format_metric(avg_all_evidence, precision=1, percent=True)}** | Compatibility flags alone do not establish completeness |",
        f"| **Legacy route epistemic diagnostic** | {total} | {legacy_metrics['epistemic_score']['assessed_count']} / {total} assessed | **{_format_metric(avg_epistemic_score, precision=3)}** | Legacy route value; not a claim-truth score |\n",
        "## Performance by Modality\n",
        "| Modality | Tested | Passed | Pass Rate |",
        "|---|:---:|:---:|:---:|"
    ]
    
    for mod, count in modality_counts.items():
        p = modality_passes.get(mod, 0)
        pct = (p / count) * 100 if count > 0 else 0
        report_lines.append(f"| {mod.capitalize()} | {count} | {p} | {pct:.1f}% |")

    report_lines.append("\n## Detailed Query Results & Answer Route Manifest\n")
    report_lines.append("| ID | Modality | Result | Doc@1 | Ans@1 | Legacy Recall Diagnostic | Evidence Items | Citations Found |")
    report_lines.append("|---|---|:---:|:---:|:---:|:---:|---|---|")
    
    for r in results:
        it = r["item"]
        v = r["verification"]
        cm = r["context_metrics"]
        ar = r["answer_route"]
        status = "✅ PASS" if v["pass"] else "❌ FAIL"
        doc_s = "✅" if cm["document_at_1"] else "❌"
        ans_s = "✅" if cm["answer_at_1"] else "❌"
        ev_items_summary = f"{len(ar.get('evidence_group', []))} items"
        cits = ", ".join(v["citations"]["figures"] + v["citations"]["tables"] + v["citations"]["clauses"]) or "None"
        report_lines.append(f"| {it['id']} | {it['modality']} | {status} | {doc_s} | {ans_s} | {_format_metric(cm['evidence_recall'])} | {ev_items_summary} | {cits} |")

    report_md = "\n".join(report_lines)
    report_file = BASE_DIR / "eval" / report_filename
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"\n========================================================")
    print(f"Evaluation complete! Report written to {report_file}")
    print(f"Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
    print(f"Legacy Document@1 heuristic: {doc_at_1_pct:.1f}%")
    print(f"Legacy Answer@1 heuristic: {ans_at_1_pct:.1f}%")
    for name, aggregate in legacy_metrics.items():
        display = _format_metric(aggregate['value'], precision=3 if name == 'epistemic_score' else 1,
                                 percent=name != 'epistemic_score')
        print(f"Legacy route {name} diagnostic: {display} ({aggregate['assessed_count']}/{total} assessed; not claim truth)")
    print(f"========================================================\n")

    # Generate run receipt
    try:
        import subprocess
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_hash = "unknown"

    graph_file = BASE_DIR / "storage" / "dual_layer_knowledge_graph.graphml"
    node_count = 0
    edge_count = 0
    if graph_file.exists():
        try:
            import networkx as nx
            G = nx.read_graphml(graph_file)
            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()
        except Exception:
            pass

    receipt = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "document": "AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions",
        "commit_hash": commit_hash,
        "llm_engine": engine,
        "llm_model": active_model,
        "embedding_model": "BAAI/bge-large-en-v1.5 (1024-dim, Contextualized)",
        "graph_nodes": node_count,
        "graph_edges": edge_count,
        "context_bench_metrics": {
            "document_at_1_pct": round(doc_at_1_pct, 2),
            "answer_at_1_pct": round(ans_at_1_pct, 2),
            "evidence_recall_pct": round(avg_evidence_recall_pct, 2) if avg_evidence_recall_pct is not None else None,
            "all_evidence_pct": round(all_evidence_pct, 2) if all_evidence_pct is not None else None,
            "epistemic_provenance_score": round(avg_epistemic_score, 3) if avg_epistemic_score is not None else None,
            "route_metric_scope": "legacy_route_diagnostics_not_claim_truth"
        },
        "legacy_route_diagnostics": {
            "scope": "legacy_route_diagnostics_not_claim_truth",
            "aggregation": "assessed_only_mean",
            **legacy_metrics
        },
        "benchmark_summary": {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate_pct": round(pass_rate, 2),
            "modality_breakdown": {
                mod: f"{modality_passes.get(mod, 0)}/{modality_counts.get(mod, 0)}"
                for mod in modality_counts
            }
        }
    }
    receipt_file = BASE_DIR / "eval" / receipt_filename
    with open(receipt_file, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
    print(f"Run receipt written to {receipt_file}\n")
    return pass_rate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AWS A3.0 Prototype legacy heuristics and route diagnostics")
    parser.add_argument("--mode", type=str, default="mix", help="LightRAG query mode")
    parser.add_argument("--engine", type=str, default=DEFAULT_ENGINE, choices=["deepseek", "gemini"], help="LLM inference engine")
    parser.add_argument("--report", type=str, default="card08_benchmark_report.md", help="Report filename")
    parser.add_argument("--receipt", type=str, default="run_receipt_card08.json", help="Receipt filename")
    args = parser.parse_args()
    
    run_evaluation(
        mode=args.mode,
        engine=args.engine,
        report_filename=args.report,
        receipt_filename=args.receipt
    )
