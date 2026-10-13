"""
comparative_scorer.py: Head-to-Head Comparative Benchmark Harness (DeepSeek vs. Gemini Flash).
Runs the 12-question gold benchmark across both engines, recording:
- Response latency (seconds)
- Exact citation precision (clause, page, figure, table)
- Abstention fidelity on out-of-scope negative controls
- Side-by-side Markdown comparison matrix
"""

import sys
import json
import time
import argparse
from pathlib import Path

from src.config import BENCHMARK_FILE, BASE_DIR, DEEPSEEK_API_KEY, GEMINI_API_KEY
from src.query import run_query
from src.citation_checker import verify_response

def evaluate_engine(engine_name: str, benchmark: list, mode: str = "mix"):
    print(f"\nEvaluating engine: {engine_name.upper()} ({len(benchmark)} queries)...\n")
    results = []
    total_time = 0.0
    
    for item in benchmark:
        q_id = item["id"]
        modality = item["modality"]
        query = item["query"]
        
        t0 = time.time()
        query_res = run_query(query, mode=mode, engine=engine_name)
        elapsed = time.time() - t0
        total_time += elapsed
        
        ans = query_res["answer"]
        verification = verify_response(item, ans)
        status = "PASS" if verification["pass"] else "FAIL"
        
        print(f"[{engine_name}] [{q_id}] ({modality.upper()}) {status} in {elapsed:.2f}s")
        
        results.append({
            "id": q_id,
            "modality": modality,
            "query": query,
            "latency": round(elapsed, 2),
            "pass": verification["pass"],
            "reason": verification["reason"],
            "citations": verification["citations"],
            "answer_snippet": ans[:150].replace("\n", " ") + "..."
        })
        
    avg_latency = total_time / len(benchmark) if benchmark else 0.0
    passed_count = sum(1 for r in results if r["pass"])
    pass_rate = (passed_count / len(benchmark)) * 100 if benchmark else 0.0
    
    return {
        "engine": engine_name,
        "results": results,
        "total_queries": len(benchmark),
        "passed": passed_count,
        "pass_rate_pct": round(pass_rate, 2),
        "avg_latency_sec": round(avg_latency, 2)
    }

def run_comparative_benchmark(benchmark_path: Path = BENCHMARK_FILE, mode: str = "mix"):
    if not benchmark_path.exists():
        print(f"[ERROR] Benchmark file not found at {benchmark_path}")
        sys.exit(1)
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    engines_to_test = []
    if DEEPSEEK_API_KEY:
        engines_to_test.append("deepseek")
    else:
        print("[WARNING] DEEPSEEK_API_KEY not configured. Skipping DeepSeek.")
        
    if GEMINI_API_KEY:
        engines_to_test.append("gemini")
    else:
        print("[NOTE] GEMINI_API_KEY not configured. Set GEMINI_API_KEY to enable Gemini evaluation.")

    if not engines_to_test:
        print("[ERROR] No active model API keys found. Configure .env first.")
        sys.exit(1)

    eval_data = {}
    for engine in engines_to_test:
        eval_data[engine] = evaluate_engine(engine, benchmark, mode=mode)

    # Build Comparative Report Markdown
    lines = [
        "# AWS A3.0 Head-to-Head Comparative Benchmark Report",
        f"**Evaluated Models:** {', '.join(e.upper() for e in engines_to_test)}",
        f"**Benchmark Size:** {len(benchmark)} gold test queries",
        f"**Retrieval Mode:** LightRAG `{mode}`\n",
        "## Executive Summary",
        "| Metric | " + " | ".join(e.upper() for e in engines_to_test) + " |",
        "|---| " + " | ".join(["---"] * len(engines_to_test)) + " |",
        "| **Overall Pass Rate** | " + " | ".join(f"{eval_data[e]['pass_rate_pct']}% ({eval_data[e]['passed']}/{eval_data[e]['total_queries']})" for e in engines_to_test) + " |",
        "| **Average Latency** | " + " | ".join(f"{eval_data[e]['avg_latency_sec']}s" for e in engines_to_test) + " |\n",
        "## Query-by-Query Performance Comparison\n",
        "| ID | Modality | Target Element | " + " | ".join(f"{e.upper()} Result" for e in engines_to_test) + " | " + " | ".join(f"{e.upper()} Latency" for e in engines_to_test) + " |",
        "|---|---|---| " + " | ".join(["---"] * (len(engines_to_test) * 2)) + " |"
    ]

    for item in benchmark:
        q_id = item["id"]
        mod = item["modality"]
        target = item.get("expected_citation_element") or "Abstain"
        
        row_res = []
        row_lat = []
        for e in engines_to_test:
            res_item = next(r for r in eval_data[e]["results"] if r["id"] == q_id)
            row_res.append("✅ PASS" if res_item["pass"] else "❌ FAIL")
            row_lat.append(f"{res_item['latency']}s")
            
        line = f"| {q_id} | {mod} | {target} | " + " | ".join(row_res) + " | " + " | ".join(row_lat) + " |"
        lines.append(line)

    lines.append("\n## Detailed Citations & Reasoning Audit\n")
    for item in benchmark:
        q_id = item["id"]
        lines.append(f"### {q_id}: {item['query']}")
        for e in engines_to_test:
            res_item = next(r for r in eval_data[e]["results"] if r["id"] == q_id)
            status = "✅ PASS" if res_item["pass"] else "❌ FAIL"
            cits = res_item["citations"]
            cit_str = f"Clauses: {cits.get('clauses', [])}, Figures: {cits.get('figures', [])}, Tables: {cits.get('tables', [])}"
            lines.append(f"- **{e.upper()} ({status}, {res_item['latency']}s)**: {res_item['reason']}")
            lines.append(f"  - Citations: {cit_str}")
        lines.append("")

    report_md = "\n".join(lines)
    report_file = BASE_DIR / "eval" / "comparative_report_deepseek_vs_gemini.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nComparative evaluation complete! Report written to {report_file}")

def main():
    parser = argparse.ArgumentParser(description="Head-to-head benchmark evaluation")
    parser.add_argument("--mode", type=str, default="mix", help="LightRAG query mode")
    args = parser.parse_args()

    run_comparative_benchmark(mode=args.mode)

if __name__ == "__main__":
    main()
