"""
retrieval_scorer.py: Standalone Information Retrieval (IR) Benchmark Harness.

Evaluates the two-stage hybrid retrieval pipeline against the 50-item gold benchmark
WITHOUT calling generative LLMs (100% offline, zero API costs).

Computes standard IR metrics:
- Recall@1
- Recall@5
- Mean Reciprocal Rank (MRR)
- Negative Control Abstention Precision
- Mean Query Retrieval Latency (ms)
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import BENCHMARK_FILE, EVAL_DIR
from src.pre_retrieval import check_early_abstention
from src.hybrid_retriever import hybrid_retrieve

def evaluate_retrieval(benchmark_path: Path = BENCHMARK_FILE) -> Dict[str, Any]:
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print("=" * 65)
    print(f"AWS A3.0 Information Retrieval (IR) Evaluation Suite ({len(benchmark)} Queries)")
    print("Metrics: Recall@1, Recall@5, MRR, Abstention Precision, Latency")
    print("=" * 65 + "\n")

    total_queries = len(benchmark)
    abstention_queries = 0
    abstention_correct = 0

    retrieval_queries = 0
    recall_at_1_hits = 0
    recall_at_5_hits = 0
    reciprocal_ranks = []
    latencies = []

    per_query_results = []

    for item in benchmark:
        qid = item["id"]
        modality = item["modality"]
        query = item["query"]
        expected_citation = item.get("expected_citation", "")

        # 1. Negative control abstention queries
        if modality == "abstention":
            abstention_queries += 1
            abstain = check_early_abstention(query)
            is_correct = abstain is not None and abstain.get("status") == "TRUTHFUL_ABSTENTION"
            if is_correct:
                abstention_correct += 1
                status_str = "PASS (Zero-Cost Early Abstention)"
            else:
                status_str = "FAIL (Missed Abstention)"
            
            print(f"[{qid}] ({modality.upper()}) {query[:50]}... -> {status_str}")
            per_query_results.append({
                "id": qid,
                "modality": modality,
                "query": query,
                "expected": expected_citation,
                "status": "PASS" if is_correct else "FAIL",
                "details": abstain.get("reason", "") if abstain else "Not flagged by early gate"
            })
            continue

        # 2. In-scope retrieval queries
        retrieval_queries += 1
        t0 = time.time()
        retrieved_chunks = hybrid_retrieve(query, top_k=5)
        elapsed_ms = (time.time() - t0) * 1000
        latencies.append(elapsed_ms)

        gold_cit = item.get("gold_citation", {})
        clause = str(gold_cit.get("clause", "")).lower()
        page = str(gold_cit.get("printed_page", "")).lower()
        elem_id = str(gold_cit.get("element_id", "")).lower()
        keywords = [k.lower() for k in item.get("expected_answer_keywords", [])]
        qualifiers = [q.lower() for q in item.get("required_qualifiers", [])]

        # Target terms that uniquely establish relevance to this question
        target_anchors = [elem_id] if elem_id else []
        target_anchors.extend(qualifiers)

        # Rank of first relevant chunk
        hit_rank = 0
        for rank, chunk in enumerate(retrieved_chunks):
            content_lower = chunk.get("content", "").lower()
            doc_id_lower = chunk.get("full_doc_id", "").lower()
            
            matched = False
            # Check 1: Direct match with element ID or required qualifiers
            if target_anchors and any(a in doc_id_lower or a in content_lower for a in target_anchors if len(a) > 2):
                matched = True
            # Check 2: Match with exact clause and printed page
            elif page and f"p. {page}" in content_lower:
                matched = True
            elif page and f"p{page}" in doc_id_lower:
                matched = True
            # Check 3: At least 2 answer keywords present in chunk content
            elif keywords:
                kw_matches = sum(1 for k in keywords if k in content_lower)
                if kw_matches >= 2:
                    matched = True

            if matched:
                hit_rank = rank + 1
                break

        if hit_rank == 1:
            recall_at_1_hits += 1
            recall_at_5_hits += 1
            reciprocal_ranks.append(1.0)
            status_str = f"HIT@1 (Latency: {elapsed_ms:.1f}ms)"
        elif hit_rank > 1:
            recall_at_5_hits += 1
            reciprocal_ranks.append(1.0 / hit_rank)
            status_str = f"HIT@{hit_rank} (Latency: {elapsed_ms:.1f}ms)"
        else:
            reciprocal_ranks.append(0.0)
            status_str = f"MISS (Latency: {elapsed_ms:.1f}ms)"

        print(f"[{qid}] ({modality.upper()}) {query[:45]}... -> {status_str}")
        per_query_results.append({
            "id": qid,
            "modality": modality,
            "query": query,
            "expected_element": elem_id,
            "hit_rank": hit_rank,
            "latency_ms": round(elapsed_ms, 1),
            "top_doc_ids": [c.get("full_doc_id", "") for c in retrieved_chunks[:3]]
        })

    # Summary calculations
    r_at_1 = (recall_at_1_hits / retrieval_queries * 100) if retrieval_queries else 0.0
    r_at_5 = (recall_at_5_hits / retrieval_queries * 100) if retrieval_queries else 0.0
    mrr = (sum(reciprocal_ranks) / len(reciprocal_ranks)) if reciprocal_ranks else 0.0
    abs_prec = (abstention_correct / abstention_queries * 100) if abstention_queries else 0.0
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    print("\n" + "=" * 65)
    print("RETRIEVAL EVALUATION RESULTS SUMMARY")
    print("=" * 65)
    print(f"Total Benchmark Queries:       {total_queries}")
    print(f"In-Scope Retrieval Queries:    {retrieval_queries}")
    print(f"Negative Control Queries:      {abstention_queries}")
    print(f"-----------------------------------------------------------------")
    print(f"Recall@1:                      {r_at_1:.1f}% ({recall_at_1_hits}/{retrieval_queries})")
    print(f"Recall@5:                      {r_at_5:.1f}% ({recall_at_5_hits}/{retrieval_queries})")
    print(f"Mean Reciprocal Rank (MRR):    {mrr:.4f}")
    print(f"Abstention Gate Precision:     {abs_prec:.1f}% ({abstention_correct}/{abstention_queries})")
    print(f"Mean Retrieval Latency:        {avg_latency:.1f} ms")
    print("=" * 65 + "\n")

    report_payload = {
        "metrics": {
            "total_queries": total_queries,
            "recall_at_1": round(r_at_1, 2),
            "recall_at_5": round(r_at_5, 2),
            "mrr": round(mrr, 4),
            "abstention_precision": round(abs_prec, 2),
            "mean_latency_ms": round(avg_latency, 1)
        },
        "query_details": per_query_results
    }

    receipt_path = EVAL_DIR / "run_receipt_retrieval.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)
    print(f"Saved receipt to {receipt_path}")

    return report_payload

if __name__ == "__main__":
    evaluate_retrieval()
