"""
test_scorer.py: Automated benchmark evaluation harness for AWS A3.0 prototype.
Evaluates the 50-question gold benchmark across 7 modalities and computes
Perplexity & Turbopuffer Context-Bench multi-stage contextual retrieval metrics:
- Document@1 (Standard Disambiguation & Scope Boundary Enforcement)
- Answer@1 (Primary Answer Accuracy)
- Evidence Recall@K (Supporting Evidence Completeness)
- All-Evidence@10 (Full Answer Route Bundle Recovery)
- Epistemic Provenance Score (Auditable Grounding Bridges)
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
from src.answer_routes import resolve_answer_route

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
    print(f"Context-Bench: Document@1, Answer@1, Evidence Recall, All-Evidence")
    print(f"========================================================\n")
    
    results = []
    modality_counts = {}
    modality_passes = {}

    # Context-Bench counters
    doc_at_1_passes = 0
    ans_at_1_passes = 0
    evidence_recall_sum = 0.0
    all_evidence_passes = 0
    epistemic_scores_sum = 0.0
    
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

        # Resolve Answer Route & Context-Bench metrics
        answer_route = resolve_answer_route(query, ans)
        
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

        evidence_recall_sum += answer_route.evidence_recall_score
        if answer_route.all_evidence_recovered:
            all_evidence_passes += 1

        epistemic_scores_sum += answer_route.epistemic_score
        
        if is_pass:
            modality_passes[modality] = modality_passes.get(modality, 0) + 1
            print(f"  -> PASS: {verification['reason']}")
            print(f"     [Answer Route] Status: {answer_route.status} | Evidence: {len(answer_route.evidence_group)} items | Recall: {answer_route.evidence_recall_score}")
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
                "evidence_recall": answer_route.evidence_recall_score,
                "all_evidence": answer_route.all_evidence_recovered,
                "epistemic_score": answer_route.epistemic_score
            }
        })
        print("-" * 60)

    # Summarize results
    total = len(benchmark)
    passed = sum(1 for r in results if r["verification"]["pass"])
    pass_rate = (passed / total) * 100 if total > 0 else 0

    doc_at_1_pct = (doc_at_1_passes / total) * 100 if total > 0 else 0
    ans_at_1_pct = (ans_at_1_passes / total) * 100 if total > 0 else 0
    avg_evidence_recall_pct = (evidence_recall_sum / total) * 100 if total > 0 else 0
    all_evidence_pct = (all_evidence_passes / total) * 100 if total > 0 else 0
    avg_epistemic_score = (epistemic_scores_sum / total) if total > 0 else 0
    
    active_model = GEMINI_MODEL if engine.lower() == "gemini" else DEEPSEEK_MODEL

    report_lines = [
        f"# AWS A3.0 Multimodal Prototype Benchmark Report (Card 08 - Answer Routes & Context-Bench)\n",
        f"**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Inference Engine:** {engine.upper()} (`{active_model}`)",
        f"**Retrieval Mode:** {mode}",
        f"**Total Queries Evaluated:** {total}",
        f"**Total Passed:** {passed} / {total} ({pass_rate:.1f}%)\n",
        "## Context-Bench Multi-Stage Retrieval Metrics\n",
        "Adopting the evaluation framework from Perplexity Research & Turbopuffer (*Contextual Embedding: Beyond the Gold Passage*):\n",
        "| Context-Bench Metric | Tested | Passed / Score | Rate | Capability Tested |",
        "|---|:---:|:---:|:---:|---|",
        f"| **Document@1** | {total} | {doc_at_1_passes} | **{doc_at_1_pct:.1f}%** | Document Disambiguation & Strict Scope Boundaries |",
        f"| **Answer@1** | {total} | {ans_at_1_passes} | **{ans_at_1_pct:.1f}%** | Primary Answer-Bearing Chunk Retrieval |",
        f"| **Evidence Recall@K** | {total} | — | **{avg_evidence_recall_pct:.1f}%** | Supporting Evidence Completeness (Figures, Tables, Callouts) |",
        f"| **All-Evidence@10** | {total} | {all_evidence_passes} | **{all_evidence_pct:.1f}%** | Complete Answer Route Bundle Recovery |",
        f"| **Epistemic Provenance Score** | {total} | — | **{avg_epistemic_score:.3f} / 1.000** | Unbroken Bridges to Normative Evidence Nodes |\n",
        "## Performance by Modality\n",
        "| Modality | Tested | Passed | Pass Rate |",
        "|---|:---:|:---:|:---:|"
    ]
    
    for mod, count in modality_counts.items():
        p = modality_passes.get(mod, 0)
        pct = (p / count) * 100 if count > 0 else 0
        report_lines.append(f"| {mod.capitalize()} | {count} | {p} | {pct:.1f}% |")

    report_lines.append("\n## Detailed Query Results & Answer Route Manifest\n")
    report_lines.append("| ID | Modality | Result | Doc@1 | Ans@1 | Evid Recall | Evidence Items | Citations Found |")
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
        report_lines.append(f"| {it['id']} | {it['modality']} | {status} | {doc_s} | {ans_s} | {cm['evidence_recall']:.2f} | {ev_items_summary} | {cits} |")

    report_md = "\n".join(report_lines)
    report_file = BASE_DIR / "eval" / report_filename
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"\n========================================================")
    print(f"Evaluation complete! Report written to {report_file}")
    print(f"Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
    print(f"Context-Bench Document@1: {doc_at_1_pct:.1f}%")
    print(f"Context-Bench Answer@1: {ans_at_1_pct:.1f}%")
    print(f"Context-Bench Evidence Recall: {avg_evidence_recall_pct:.1f}%")
    print(f"Context-Bench All-Evidence: {all_evidence_pct:.1f}%")
    print(f"Average Epistemic Provenance: {avg_epistemic_score:.3f}")
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
            "evidence_recall_pct": round(avg_evidence_recall_pct, 2),
            "all_evidence_pct": round(all_evidence_pct, 2),
            "epistemic_provenance_score": round(avg_epistemic_score, 3)
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
        json.dump(receipt, f, indent=2)
    print(f"Run receipt written to {receipt_file}\n")
    return pass_rate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AWS A3.0 Prototype with Context-Bench Metrics")
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
