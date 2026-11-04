"""CLI tool to audit genuine DeepSeek-V4.1 replay coverage vs quarantined synthetic fixtures (Gate 6.6).

Usage:
    python -B scripts/audit_replay_coverage.py --write
    python -B scripts/audit_replay_coverage.py --json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.deepseek_v41_adapter import audit_replay_coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit DeepSeek-V4.1 offline replay coverage across benchmarks")
    parser.add_argument("--write", action="store_true", help="Write storage/manifests/replay_coverage_manifest.json")
    parser.add_argument("--json", action="store_true", help="Print full JSON manifest to stdout")
    parser.add_argument(
        "--record-missing",
        action="store_true",
        help="Record missing genuine replay cassettes via live DeepSeek-V4.1 endpoint (requires DEEPSEEK_API_KEY)",
    )
    args = parser.parse_args()

    if args.record_missing:
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("VLLM_API_KEY")
        if not api_key:
            print(
                "REFUSAL_OFFLINE_ENVIRONMENT: Cannot record live DeepSeek-V4.1 cassettes without DEEPSEEK_API_KEY / VLLM_API_KEY.",
                file=sys.stderr,
            )
            return 2

    manifest = audit_replay_coverage(root=ROOT, write_manifest=args.write)
    if args.json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(
            f"Replay Coverage Audit (Gate 6.6): "
            f"genuine_model_replays={manifest['genuine_model_replays_count']}, "
            f"quarantined_synthetic_fixtures={manifest['quarantined_synthetic_fixtures_count']}"
        )
        for b_name, b_stats in manifest["benchmarks"].items():
            print(
                f"  {b_name:36s}: total={b_stats['total_queries']:2d} | "
                f"genuine={b_stats['genuine_model_replays']:2d} | "
                f"quarantined_fixtures={b_stats['quarantined_synthetic_fixtures']:2d} | "
                f"deterministic_fallback={b_stats['deterministic_planner_fallbacks']:2d}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
