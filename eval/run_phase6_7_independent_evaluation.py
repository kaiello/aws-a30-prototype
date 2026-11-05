"""Bounded independent evaluation. Source-bearing receipts stay local and append-only.

prepare runs the existing app route offline, before building either source packet.
run makes one local reader call per selected case/track, with no retries.
score consumes independently completed human forms without modifying run receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from unittest.mock import patch

from src.independent_reader_evaluation import (
    build_reader_request, capture_application_result, invoke_reader, retrieved_evidence_selection,
    validate_config, write_new_json,
)
from src.independent_reader_scoring import canonical_digest, create_review_template, score_response
from src.independent_source_packets import build_source_packet

ROOT = Path(__file__).resolve().parents[1]
TRACKS = ("gold", "retrieved")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_case_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError("Case IDs must be simple unique filenames")
    return value


def _network_blocked(*args, **kwargs):
    raise RuntimeError("Application evidence preparation must remain offline")


def prepare(suite_path: Path, output: Path, *, root: Path = ROOT) -> dict:
    # Import optional application dependencies before replacing socket types.
    # The actual query execution below remains socket-guarded.
    from src.query import get_query_event_loop
    get_query_event_loop()
    suite = read_json(suite_path)
    ids = [_safe_case_id(case["id"]) for case in suite["cases"]]
    if not ids or len(ids) > 15 or len(set(ids)) != len(ids):
        raise ValueError("Prepare requires 1-15 uniquely identified cases")
    output.mkdir(parents=True, exist_ok=False)
    write_new_json(output / "suite.json", suite)
    records = []
    for case in suite["cases"]:
        directory = output / case["id"]
        directory.mkdir()
        record = {"id": case["id"], "question": case["question"]}
        try:
            # The actual application's evidence selection is frozen before gold is read.
            # Preserve the socket type: Windows Proactor uses isinstance(socket.socket)
            # while servicing its preconnected local wakeup pipe.
            with patch("socket.socket.connect", side_effect=_network_blocked), patch(
                    "socket.socket.connect_ex", side_effect=_network_blocked), patch(
                    "socket.socket.sendto", side_effect=_network_blocked), patch(
                    "socket.create_connection", side_effect=_network_blocked):
                application = capture_application_result(case["question"])
            write_new_json(directory / "application.json", application)
            selection = retrieved_evidence_selection(application, max_pages=2)
            write_new_json(directory / "retrieval_selection.json", selection)
            retrieved = build_source_packet(root, suite["source"], case["question"], selection["evidence"])
            gold = build_source_packet(root, suite["source"], case["question"], case["evidence"])
            write_new_json(directory / "retrieved_packet.json", retrieved)
            write_new_json(directory / "gold_packet.json", gold)
            needed = {e["evidence_id"] for e in gold["evidence"]}
            supplied = {e["evidence_id"] for e in retrieved["evidence"]}
            record.update(status="PREPARED", app_execution_mode="actual_application_deterministic",
                          app_status=(application.get("execution") or {}).get("status"),
                          app_answer_outcome=application.get("answer_outcome"),
                          gold_evidence_ids=sorted(needed), retrieved_evidence_ids=sorted(supplied),
                          missing_gold_page_ids=sorted(needed - supplied),
                          omitted_app_pages=selection["omitted_pages"],
                          packet_sha256s={"gold": canonical_digest(gold), "retrieved": canonical_digest(retrieved)},
                          app_content_adjudication="PENDING_HUMAN_REVIEW")
        except Exception as exc:
            record.update(status="PREPARATION_ERROR", error=f"{type(exc).__name__}: {exc}")
        records.append(record)
        print(f"{case['id']}: {record['status']}", flush=True)
    manifest = {"gate": "6.7", "suite_sha256": canonical_digest(suite), "split": suite["split"],
                "page_budget": 2, "rendering_dpi": 120, "cases": records,
                "source_review": "agent_source_checked_human_pending",
                "qualification_status": "NOT_QUALIFIED", "reader_calls": 0}
    write_new_json(output / "manifest.json", manifest)
    return manifest


def run(prepared: Path, config_path: Path, output: Path, *, limit_cases: int = 8) -> dict:
    if not 1 <= limit_cases <= 15:
        raise ValueError("Run limit must be 1-15 cases")
    config = read_json(config_path)
    validate_config(config)
    suite = read_json(prepared / "suite.json")
    manifest = read_json(prepared / "manifest.json")
    if manifest["suite_sha256"] != canonical_digest(suite):
        raise ValueError("Prepared suite hash mismatch")
    # Validate every selected packet before any model receives source material.
    for row in manifest["cases"][:limit_cases]:
        if row["status"] == "PREPARED":
            for track in TRACKS:
                packet = read_json(prepared / row["id"] / f"{track}_packet.json")
                if canonical_digest(packet) != row["packet_sha256s"][track]:
                    raise ValueError("Prepared packet hash mismatch")
    output.mkdir(parents=True, exist_ok=False)
    write_new_json(output / "config.json", config)
    # Absolute path is local continuation metadata, never included in public summaries.
    write_new_json(output / "inputs.json", {"prepared_directory": str(prepared.resolve()),
                   "manifest_sha256": canonical_digest(manifest), "case_limit": limit_cases})
    cases = {case["id"]: case for case in suite["cases"]}
    outcomes = []
    for row in manifest["cases"][:limit_cases]:
        if row["status"] != "PREPARED":
            outcomes.append({"id": row["id"], "outcome": "PREPARATION_ERROR"})
            continue
        case = cases[row["id"]]
        for track in TRACKS:
            packet = read_json(prepared / case["id"] / f"{track}_packet.json")
            directory = output / case["id"] / track
            result = {"id": case["id"], "track": track}
            try:
                receipt = invoke_reader(packet, config, directory)
                response = receipt["response"]
                result.update(score_response(case, packet, response))
                write_new_json(directory / "review_template.json", create_review_template(case, packet, response))
                result["response_sha256"] = receipt["response_sha256"]
            except Exception as exc:
                result.update(outcome="READER_EXECUTION_ERROR", error=f"{type(exc).__name__}: {exc}")
            raw_path = directory / "raw_response.json"
            raw = read_json(raw_path) if raw_path.exists() else {}
            result.update(inference_attempted=(directory / "attempt.json").exists(),
                          raw_response_received=raw_path.exists(),
                          inference_completed=bool(raw.get("done") and (raw.get("message") or {}).get("content")),
                          response_parsed=(directory / "receipt.json").exists())
            outcomes.append(result)
            print(f"{case['id']} {track}: {result['outcome']}", flush=True)
    summary = {"gate": "6.7", "split": suite["split"], "config_sha256": canonical_digest(config),
               "model": config["model"], "model_digest": config["model_digest"],
               "execution_mode": "local_ollama_reader", "qualification_status": "NOT_QUALIFIED",
               "case_limit": limit_cases, "results": outcomes,
               "outcomes": dict(Counter(row["outcome"] for row in outcomes)),
               "human_reviewed_answers": 0, "reader_accuracy": None,
               "retrieval_vs_reader_quality_delta": None}
    write_new_json(output / "summary.json", summary)
    return summary


def score(prepared: Path, run_dir: Path, reviews: Path, output: Path) -> dict:
    suite = read_json(prepared / "suite.json")
    manifest = read_json(prepared / "manifest.json")
    run_inputs = read_json(run_dir / "inputs.json")
    if (manifest["suite_sha256"] != canonical_digest(suite)
            or run_inputs["manifest_sha256"] != canonical_digest(manifest)):
        raise ValueError("Scoring inputs differ from recorded preparation")
    config = read_json(run_dir / "config.json")
    rows_by_id = {row["id"]: row for row in manifest["cases"]}
    original = read_json(run_dir / "summary.json")
    if original["config_sha256"] != canonical_digest(config):
        raise ValueError("Run configuration hash mismatch")
    run_rows = {(row["id"], row.get("track")): row for row in original["results"]}
    results = [row for row in original["results"] if row.get("track") not in TRACKS]
    for case in suite["cases"]:
        for track in TRACKS:
            receipt_path = run_dir / case["id"] / track / "receipt.json"
            if not receipt_path.exists():
                previous = run_rows.get((case["id"], track))
                if previous is not None:
                    results.append(previous)
                continue
            packet = read_json(prepared / case["id"] / f"{track}_packet.json")
            receipt = read_json(receipt_path)
            directory = receipt_path.parent
            raw = read_json(directory / "raw_response.json")
            request = read_json(directory / "request.json")
            call_config = read_json(directory / "config.json")
            if (canonical_digest(packet) != rows_by_id[case["id"]]["packet_sha256s"][track]
                    or canonical_digest(call_config) != canonical_digest(config)
                    or receipt["packet_sha256"] != canonical_digest(packet)
                    or receipt["config_sha256"] != canonical_digest(config)
                    or receipt["request_sha256"] != canonical_digest(request)
                    or canonical_digest(build_reader_request(packet, config)) != canonical_digest(request)
                    or receipt["raw_response_sha256"] != canonical_digest(raw)
                    or receipt["response_sha256"] != canonical_digest(receipt["response"])
                    or receipt["response_sha256"] != canonical_digest(json.loads(raw["message"]["content"]))):
                raise ValueError("Recorded packet/request/response hash mismatch")
            review_path = reviews / case["id"] / f"{track}.json"
            review = read_json(review_path) if review_path.exists() else None
            results.append({"id": case["id"], "track": track,
                            **score_response(case, packet, receipt["response"], review)})
    summary = {"gate": "6.7", "results": results,
               "outcomes": dict(Counter(row["outcome"] for row in results)),
               "human_reviewed_answers": sum(row.get("semantic_reviewed", False) for row in results),
               "note": "Review JSON records human assertions; provenance is audited, reviewer identity is not authenticated."}
    write_new_json(output, summary)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--suite", type=Path, default=ROOT / "eval/fixtures/gate67_development.json")
    prep.add_argument("--output", type=Path, required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--prepared", type=Path, required=True)
    execute.add_argument("--config", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--limit-cases", type=int, default=8)
    adjudicate = commands.add_parser("score")
    adjudicate.add_argument("--prepared", type=Path, required=True)
    adjudicate.add_argument("--run", type=Path, required=True)
    adjudicate.add_argument("--reviews", type=Path, required=True)
    adjudicate.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.suite, args.output)
    elif args.command == "run":
        result = run(args.prepared, args.config, args.output, limit_cases=args.limit_cases)
    else:
        result = score(args.prepared, args.run, args.reviews, args.output)
    print(json.dumps({key: value for key, value in result.items() if key not in {"cases", "results"}}, indent=2))
    return 1 if any(row.get("outcome") == "READER_EXECUTION_ERROR" or row.get("status") == "PREPARATION_ERROR"
                    for row in result.get("results", result.get("cases", []))) else 0


if __name__ == "__main__":
    raise SystemExit(main())
