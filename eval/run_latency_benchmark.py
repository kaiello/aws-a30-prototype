#!/usr/bin/env python3
"""eval/run_latency_benchmark.py

Measured Offline Latency Benchmark for AWS A3.0M/A3.0:2020 RAG System.
Replaces unverified latency claims with empirical microsecond-resolution timing
(using time.perf_counter_ns) across deterministic and DeepSeek-V4.1 offline replay routes.

Output: storage/manifests/latency_benchmark.json
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any, Dict, List
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)
from src.deepseek_v41_adapter import DeepSeekV41PlannerAdapter
from test_evidence_a1_provenance import fixture as a1_fixture
from test_evidence_a1_graph_qa import toy_graph as a2_toy_graph
from test_evidence_a2_core import bind as a2_bind, nested as a2_nested
from src.evidence_a1 import bind_a1_graph_evidence
from src.evidence_a1_graph_qa import answer_graph


def _guard_network(*args, **kwargs):
    raise RuntimeError("Network blocked: offline execution contract violation")


def percentile(data: List[float], p: float) -> float:
    """Compute empirical percentile from data."""
    if not data:
        return 0.0
    k = (len(data) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(data) - 1)
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return round(d0 + d1, 3)


def run_latency_benchmark(
    root: Path = ROOT,
    iterations_per_query: int = 5,
) -> Dict[str, Any]:
    """Execute latency benchmark across offline deterministic and replay routes."""
    stores = get_whole_standard_stores(root)
    det_planner = DeterministicQuestionPlanner(root)
    deepseek_adapter = DeepSeekV41PlannerAdapter(root=root)

    # Load 15 NLQ queries
    nlq_path = root / "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json"
    nlq_items = json.loads(nlq_path.read_text(encoding="utf-8"))

    # Load 10 Adversarial queries
    adv_path = root / "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json"
    adv_items = json.loads(adv_path.read_text(encoding="utf-8"))

    all_det_queries = [item["query"] for item in nlq_items] + [item["query"] for item in adv_items]

    # Warm-up run (ensure stores and expansion graphs are cached)
    _ = answer_whole_standard_question(all_det_queries[0], planner=det_planner, stores=stores)

    # 1. Benchmark Offline Deterministic Route (25 queries x N iterations)
    # -------------------------------------------------------------------------
    det_latencies_ms: List[float] = []
    nlq_latencies_ms: List[float] = []
    adv_latencies_ms: List[float] = []

    with patch("socket.socket", side_effect=_guard_network), \
         patch("socket.create_connection", side_effect=_guard_network):

        for item in nlq_items:
            q = item["query"]
            for _ in range(iterations_per_query):
                t0 = time.perf_counter_ns()
                _ = answer_whole_standard_question(q, planner=det_planner, stores=stores)
                t1 = time.perf_counter_ns()
                elapsed_ms = (t1 - t0) / 1_000_000.0
                det_latencies_ms.append(elapsed_ms)
                nlq_latencies_ms.append(elapsed_ms)

        for item in adv_items:
            q = item["query"]
            for _ in range(iterations_per_query):
                t0 = time.perf_counter_ns()
                _ = answer_whole_standard_question(q, planner=det_planner, stores=stores)
                t1 = time.perf_counter_ns()
                elapsed_ms = (t1 - t0) / 1_000_000.0
                det_latencies_ms.append(elapsed_ms)
                adv_latencies_ms.append(elapsed_ms)

    det_latencies_ms.sort()
    det_stats = {
        "query_count": len(all_det_queries),
        "total_iterations": len(det_latencies_ms),
        "iterations_per_query": iterations_per_query,
        "p50_ms": percentile(det_latencies_ms, 50.0),
        "p95_ms": percentile(det_latencies_ms, 95.0),
        "p99_ms": percentile(det_latencies_ms, 99.0),
        "mean_ms": round(statistics.mean(det_latencies_ms), 3),
        "min_ms": round(min(det_latencies_ms), 3),
        "max_ms": round(max(det_latencies_ms), 3),
        "stdev_ms": round(statistics.stdev(det_latencies_ms), 3) if len(det_latencies_ms) > 1 else 0.0,
    }

    # 2. Benchmark Offline DeepSeek-V4.1 Replay Route (8 locked replay fixtures x N iterations)
    # -------------------------------------------------------------------------
    raw_toy = a2_toy_graph.__wrapped__() if hasattr(a2_toy_graph, "__wrapped__") else a2_toy_graph()
    src_a2 = a2_bind(a2_nested(raw_toy))
    q_a2 = "Give the name, acronym and group for ZZRP in Figure A2."

    g_a1, src_kwargs_a1 = a1_fixture()
    src_a1 = bind_a1_graph_evidence(g_a1, **src_kwargs_a1)
    q_a1 = "Provide all processes under arc welding (aw)- include the process and the acronym."

    deepseek_whole_queries = [
        "What is the definition of shielded metal arc welding in Clause 4, what letter designation is assigned in Table A1, and which figure illustrates arc welding power source waveforms?",
        "Which processes are classified on Figure A7 and Figure B55 in AWS A3.0?",
        "Why is shielded metal arc welding categorized under solid-state welding in AWS A3.0?",
        "Which waveform diagram illustrates upslope and downslope current intervals for pulsed welding cycles?",
        "Is atomic hydrogen welding an active process in the standard or is it obsolete, and what was its letter designation?",
        "What preheat temperature and Charpy impact toughness are specified for structural steel?",
    ]

    replay_latencies_ms: List[float] = []

    with patch("socket.socket", side_effect=_guard_network), \
         patch("socket.create_connection", side_effect=_guard_network):

        # Chart Replay 1 (Figure A2)
        for _ in range(iterations_per_query):
            t0 = time.perf_counter_ns()
            _ = answer_graph(src_a2, q_a2, question_planner=deepseek_adapter)
            t1 = time.perf_counter_ns()
            replay_latencies_ms.append((t1 - t0) / 1_000_000.0)

        # Chart Replay 2 (Figure A1)
        for _ in range(iterations_per_query):
            t0 = time.perf_counter_ns()
            _ = deepseek_adapter(src_a1, q_a1)
            t1 = time.perf_counter_ns()
            replay_latencies_ms.append((t1 - t0) / 1_000_000.0)

        # Whole Standard Replays 3-8
        for q in deepseek_whole_queries:
            for _ in range(iterations_per_query):
                t0 = time.perf_counter_ns()
                _ = answer_whole_standard_question(q, planner=deepseek_adapter, stores=stores)
                t1 = time.perf_counter_ns()
                replay_latencies_ms.append((t1 - t0) / 1_000_000.0)

    replay_latencies_ms.sort()
    replay_stats = {
        "cassettes_count": 8,
        "total_iterations": len(replay_latencies_ms),
        "iterations_per_query": iterations_per_query,
        "p50_ms": percentile(replay_latencies_ms, 50.0),
        "p95_ms": percentile(replay_latencies_ms, 95.0),
        "p99_ms": percentile(replay_latencies_ms, 99.0),
        "mean_ms": round(statistics.mean(replay_latencies_ms), 3),
        "min_ms": round(min(replay_latencies_ms), 3),
        "max_ms": round(max(replay_latencies_ms), 3),
        "stdev_ms": round(statistics.stdev(replay_latencies_ms), 3) if len(replay_latencies_ms) > 1 else 0.0,
    }

    # 3. Assemble Latency Benchmark Payload
    # -------------------------------------------------------------------------
    payload = {
        "schema_version": "1.0.0",
        "standard_title": "AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions",
        "benchmark_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "execution_environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
            "architecture": platform.machine(),
            "timing_primitive": "time.perf_counter_ns",
        },
        "cost_and_replay_qualification": {
            "external_api_charge_per_query_usd": 0.0,
            "cost_qualification": "No per-query external API charge in offline deterministic/replay mode; local compute, storage, and maintenance costs still apply. Live DeepSeek-V4.1 API calls incur normal token/endpoint charges and network latency.",
            "replay_isolation": "100% network-blocked via socket.socket interception during benchmark runs.",
        },
        "routes": {
            "offline_deterministic_route": det_stats,
            "offline_deepseek_replay_route": replay_stats,
        },
    }

    return payload


def main():
    payload = run_latency_benchmark(ROOT)
    output_path = ROOT / "storage/manifests/latency_benchmark.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[OK] Generated Latency Benchmark: {output_path.relative_to(ROOT)}")
    det = payload["routes"]["offline_deterministic_route"]
    rep = payload["routes"]["offline_deepseek_replay_route"]
    print(f"     Deterministic Route ({det['query_count']} queries, {det['total_iterations']} runs):")
    print(f"       p50: {det['p50_ms']} ms | p95: {det['p95_ms']} ms | p99: {det['p99_ms']} ms | mean: {det['mean_ms']} ms")
    print(f"     DeepSeek Replay Route ({rep['cassettes_count']} cassettes, {rep['total_iterations']} runs):")
    print(f"       p50: {rep['p50_ms']} ms | p95: {rep['p95_ms']} ms | p99: {rep['p99_ms']} ms | mean: {rep['mean_ms']} ms")


if __name__ == "__main__":
    main()
