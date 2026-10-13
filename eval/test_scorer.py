"""
test_scorer.py: Automated benchmark evaluation harness for AWS A3.0 prototype.
Runs the 12-question gold benchmark, verifies citations, keyword coverage, and abstentions.
"""

import sys
import json
import argparse
from pathlib import Path
from src.config import BENCHMARK_FILE, BASE_DIR
from src.query import run_query
from src.citation_checker import verify_response

def run_evaluation(benchmark_path: Path = BENCHMARK_FILE, mode: str = "mix"):
    if not benchmark_path.exists():
        print(f"Benchmark file not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print(f"\nRunning AWS A3.0 Evaluation on {len(benchmark)} benchmark queries (mode={mode})...\n")
    
    results = []
    modality_counts = {}
    modality_passes = {}
    
    for item in benchmark:
        q_id = item["id"]
        modality = item["modality"]
        query = item["query"]
        
        modality_counts[modality] = modality_counts.get(modality, 0) + 1
        
        print(f"[{q_id}] ({modality.upper()}) {query}")
        query_res = run_query(query, mode=mode)
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
    
    report_lines = [
        "# AWS A3.0 Multimodal Prototype Benchmark Report\n",
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
    report_file = BASE_DIR / "eval" / "benchmark_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"\nEvaluation complete! Report written to {report_file}")
    print(f"Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AWS A3.0 Prototype")
    parser.add_argument("--mode", type=str, default="mix", help="LightRAG query mode")
    args = parser.parse_args()
    
    run_evaluation(mode=args.mode)
