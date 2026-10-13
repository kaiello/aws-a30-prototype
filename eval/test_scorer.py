"""
test_scorer.py: Automated benchmark evaluation harness for AWS A3.0 prototype.
Runs the 30-question gold benchmark, verifies citations, keyword coverage, qualifiers, and abstentions.
"""

import sys
import json
import argparse
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import BENCHMARK_FILE, BASE_DIR, DEFAULT_ENGINE, DEEPSEEK_MODEL, GEMINI_MODEL, EMBEDDING_MODEL
from src.query import run_query
from src.citation_checker import verify_response

def run_evaluation(
    benchmark_path: Path = BENCHMARK_FILE,
    mode: str = "mix",
    engine: str = DEFAULT_ENGINE,
    report_filename: str = "card05_benchmark_report.md",
    receipt_filename: str = "run_receipt_card05.json"
):
    if not benchmark_path.exists():
        print(f"Benchmark file not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print(f"\n========================================================")
    print(f"AWS A3.0 Grounded Evaluation: {len(benchmark)} Queries")
    print(f"Engine: {engine.upper()} | Mode: {mode}")
    print(f"========================================================\n")
    
    results = []
    modality_counts = {}
    modality_passes = {}
    
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
        
        if is_pass:
            modality_passes[modality] = modality_passes.get(modality, 0) + 1
            print(f"  -> PASS: {verification['reason']}")
        else:
            print(f"  -> FAIL: {verification['reason']}")
            
        results.append({
            "item": item,
            "query_result": query_res,
            "verification": verification
        })
        print("-" * 60)

    # Summarize results
    total = len(benchmark)
    passed = sum(1 for r in results if r["verification"]["pass"])
    pass_rate = (passed / total) * 100 if total > 0 else 0
    
    active_model = GEMINI_MODEL if engine.lower() == "gemini" else DEEPSEEK_MODEL

    report_lines = [
        f"# AWS A3.0 Multimodal Prototype Benchmark Report (Card 05 - Whole Document Exhaustive)\n",
        f"**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Inference Engine:** {engine.upper()} (`{active_model}`)",
        f"**Retrieval Mode:** {mode}",
        f"**Total Queries Evaluated:** {total}",
        f"**Total Passed:** {passed} / {total} ({pass_rate:.1f}%)\n",
        "## Performance by Modality\n",
        "| Modality | Tested | Passed | Pass Rate |",
        "|---|---|---|---|"
    ]
    
    for mod, count in modality_counts.items():
        p = modality_passes.get(mod, 0)
        pct = (p / count) * 100 if count > 0 else 0
        report_lines.append(f"| {mod.capitalize()} | {count} | {p} | {pct:.1f}% |")

    report_lines.append("\n## Detailed Query Results\n")
    report_lines.append("| ID | Modality | Result | Citations Found | Notes |")
    report_lines.append("|---|---|---|---|---|")
    
    for r in results:
        it = r["item"]
        v = r["verification"]
        status = "✅ PASS" if v["pass"] else "❌ FAIL"
        cits = ", ".join(v["citations"]["figures"] + v["citations"]["tables"] + v["citations"]["clauses"]) or "None"
        report_lines.append(f"| {it['id']} | {it['modality']} | {status} | {cits} | {v['reason']} |")

    report_md = "\n".join(report_lines)
    report_file = BASE_DIR / "eval" / report_filename
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"\nEvaluation complete! Report written to {report_file}")
    print(f"Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")

    # Generate run receipt
    try:
        import subprocess
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_hash = "unknown"

    graph_file = BASE_DIR / "storage" / "graph_chunk_entity_relation.graphml"
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
        "embedding_model": EMBEDDING_MODEL,
        "graph_nodes": node_count,
        "graph_edges": edge_count,
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
        json.dump(receipt, f, indent=2)
    print(f"Run receipt written to {receipt_file}\n")
    return pass_rate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AWS A3.0 Prototype")
    parser.add_argument("--mode", type=str, default="mix", help="LightRAG query mode")
    parser.add_argument("--engine", type=str, default=DEFAULT_ENGINE, choices=["deepseek", "gemini"], help="LLM inference engine")
    parser.add_argument("--report", type=str, default="card05_benchmark_report.md", help="Report filename")
    parser.add_argument("--receipt", type=str, default="run_receipt_card05.json", help="Receipt filename")
    args = parser.parse_args()
    
    run_evaluation(
        mode=args.mode,
        engine=args.engine,
        report_filename=args.report,
        receipt_filename=args.receipt
    )
