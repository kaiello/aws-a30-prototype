"""One saved response through the public planner and canonical backend, offline.

This checks contract/execution compatibility, never semantic answer correctness or
fresh model performance. Private receipts and source assets are supplied locally.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
from unittest.mock import patch

from src.evidence_a1_cli import write_private_output
from src.evidence_a1_vision import _strict_loads
from src.evidence_chart_contract import CONTRACT_VERSION, CONTRACT_SHA256, QUESTION_INTERFACE, PLANNED_REASON
from src.evidence_chart_local_planner import LocalQuestionPlanner

VERSION = "chart-public-entry-preflight-1.0"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(root, value):
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve(strict=True)


class _SavedResponsePlanner(LocalQuestionPlanner):
    """Reuse inherited __call__/record_result; replace transport and setup only."""
    def __init__(self, root, directory, original):
        self.root, self.directory, self.original = root, directory, original
        self.calls, self.requests, self.structural_block = [], 0, None
        self.enforces_structured_schema = False
        self.metadata = {"model": "NONE", "provider": "OFFLINE_SAVED_RESPONSE"}

    def _generate(self, prompt, schema, directory):
        if self.requests != 1:
            raise ValueError("PREFLIGHT_ONE_RESPONSE_ONLY")
        directory.mkdir(exist_ok=False)
        # New instructions are exercised by code, never sent to a model.
        write_private_output(self.root, directory / "request_not_sent.json",
                             {"prompt": prompt, "schema": schema, "sent_to_model": False})
        return {**deepcopy(self.original), "version": VERSION, "model": "NONE", "digest": None,
                "provider": "OFFLINE_SAVED_RESPONSE", "options": {}, "elapsed_seconds": 0,
                "request_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "model_invocation_count": 0, "external_call_count": 0}


def run_preflight(root, input_path, question_id, receipt_path, output_directory,
                  *, graph_path=None, source_observation_path=None):
    root = Path(root).resolve(strict=True)
    input_path, receipt_path = _path(root, input_path), _path(root, receipt_path)
    payload = _strict_loads(input_path.read_bytes())
    if (not isinstance(payload, dict) or set(payload) != {"schema_version", "source_element", "questions"}
            or not isinstance(payload["questions"], list)
            or any(not isinstance(q, dict) or set(q) != {"id", "query"}
                   or not isinstance(q["id"], str) or not isinstance(q["query"], str)
                   for q in payload["questions"])):
        raise ValueError("PREFLIGHT_EXECUTION_ONLY_QUESTION_INPUT_REQUIRED")
    questions = [q for q in payload["questions"] if q["id"] == question_id]
    if len(questions) != 1 or len({q["id"] for q in payload["questions"]}) != len(payload["questions"]):
        raise ValueError("PREFLIGHT_UNIQUE_EXISTING_QUESTION_REQUIRED")
    source = payload["source_element"]
    if source not in {"Figure A1", "Figure A2", "Figure A3", "Figure A4"} or (source in {"Figure A2", "Figure A3", "Figure A4"} and graph_path is None):
        raise ValueError("PREFLIGHT_SUPPORTED_SOURCE_AND_GRAPH_REQUIRED")
    if source == "Figure A1" and (graph_path is not None or source_observation_path is not None):
        raise ValueError("PREFLIGHT_A1_USES_CANONICAL_SOURCE_ONLY")
    original = _strict_loads(receipt_path.read_bytes())
    if (not isinstance(original, dict) or original.get("error") is not None
            or not isinstance(original.get("raw_output"), str)
            or (original.get("final") or {}).get("finish_reason",
                (original.get("final") or {}).get("done_reason")) != "stop"):
        raise ValueError("PREFLIGHT_ORIGINAL_NATURALLY_COMPLETED_RECEIPT_REQUIRED")
    external = _strict_loads(original["raw_output"])
    if external.get("query") != questions[0]["query"] or external.get("source_element") != source:
        raise ValueError("PREFLIGHT_SAVED_RESPONSE_QUERY_SOURCE_MISMATCH")
    if not any(p.get("status") == "planned" and isinstance(p.get("reason"), str)
               and p["reason"].strip() for p in external.get("parts", [])):
        raise ValueError("PREFLIGHT_NONEMPTY_ORIGINAL_PLANNED_RATIONALE_REQUIRED")
    output = Path(output_directory)
    output = (output if output.is_absolute() else root / output).resolve()
    if output.exists():
        raise ValueError("PREFLIGHT_NEW_PRIVATE_DIRECTORY_REQUIRED")
    write_private_output(root, output / "scope.json", {"version": VERSION, "new_model_calls": 0})
    # Use the existing private writer regardless of nesting depth.
    planner = _SavedResponsePlanner(root, output, original)
    selected = {**payload, "questions": questions}
    bound = {"questions": input_path, "original_receipt": receipt_path}
    if graph_path is not None:
        graph_path = _path(root, graph_path)
        bound["graph"] = graph_path
        registry = graph_path.with_suffix(".registry.db")
        if registry.exists():
            bound["registry"] = registry
    if source_observation_path is not None:
        source_observation_path = _path(root, source_observation_path)
        bound["candidate_source_observation"] = source_observation_path
    hashes = {key: _sha(path) for key, path in bound.items()}
    attempts, result, error = [], None, None

    def blocked(*args, **kwargs):
        attempts.append("BLOCKED_NETWORK_ATTEMPT")
        raise RuntimeError("PREFLIGHT_NETWORK_FORBIDDEN")

    with patch.object(socket, "create_connection", blocked), patch.object(socket.socket, "connect", blocked), \
            patch.object(socket.socket, "connect_ex", blocked):
        try:
            if source == "Figure A4":
                from src.evidence_a4 import run_questions
                backend = run_questions(root, graph_path, selected, question_planner=planner,
                                        source_observation_path=source_observation_path)
                result = backend["answers"][0]["result"]
            elif source == "Figure A3":
                from src.evidence_a3 import run_questions
                backend = run_questions(root, graph_path, selected, question_planner=planner,
                                        source_observation_path=source_observation_path)
                result = backend["answers"][0]["result"]
            elif source == "Figure A2":
                from src.evidence_a2 import run_questions
                backend = run_questions(root, graph_path, selected, question_planner=planner,
                                        source_observation_path=source_observation_path)
                result = backend["answers"][0]["result"]
            else:
                from src.evidence_a1_graph_qa import run_graph_qa
                backend = run_graph_qa(root, selected, question_planner=planner)
                result = backend["answers"][0]
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
    result = result or {}
    plan = result.get("plan", {})
    mappings = plan.get("model_part_metadata", [])
    checks = {"public_entry_called_once": planner.requests == len(planner.calls) == 1,
        "original_plan_exact": plan.get("external_plan") == external,
        "original_actions_exact": plan.get("question_actions") == external.get("actions"),
        "metadata_mapping_complete": len(mappings) == len(external.get("parts", [])) and all(
            m.get("original_reason") == p.get("reason")
            and m.get("internal_reason") == (PLANNED_REASON if p.get("status") == "planned" else p.get("reason"))
            for m, p in zip(mappings, external.get("parts", []))),
        "captured_execution_complete": result.get("execution_coverage", {}).get("status") == "complete",
        "graph_retrieval_executed": any(op.get("graph_executed") is True for op in result.get("operations", [])),
        "source_evidence_delivered": bool(result.get("record_evidence_catalog")),
        "answer_delivered": result.get("answer_outcome") == "graph_answer" and bool(result.get("answer")),
        "inputs_unchanged": hashes == {key: _sha(path) for key, path in bound.items()},
        "offline_only": not attempts and all(c.get("model_invocation_count") == c.get("external_call_count") == 0
                                             for c in planner.calls), "no_backend_error": error is None}
    receipt = {"version": VERSION, "status": "CLEAR_REAL_ENTRY_CONTRACT" if all(checks.values()) else "BLOCKED",
        "question_id": question_id, "source_element": source, "checks": checks, "error": error,
        "contract_version": CONTRACT_VERSION, "contract_sha256": CONTRACT_SHA256,
        "question_instructions": QUESTION_INTERFACE["instruction_version"], "input_sha256": hashes,
        "input_paths": {key: str(path) for key, path in bound.items()},
        "historical_response_model": original.get("response_model", original.get("model")),
        "new_model_calls": 0, "external_calls": 0, "network_attempts": attempts,
        "evidence_kind": "SAVED_ORIGINAL_RESPONSE_PUBLIC_ENTRY_PREFLIGHT",
        "semantic_answer_quality": "UNASSESSED_REQUIRES_INDEPENDENT_SOURCE_REVIEW",
        "model_consumed_current_instructions": False}
    write_private_output(root, output / "actual_answer.json", result)
    write_private_output(root, output / "preflight.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    for name in ("input", "receipt", "output-directory"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--source-observation", type=Path)
    args = parser.parse_args(argv)
    receipt = run_preflight(args.root, args.input, args.question_id, args.receipt, args.output_directory,
                            graph_path=args.graph, source_observation_path=args.source_observation)
    print(json.dumps({key: receipt[key] for key in ("status", "question_id", "new_model_calls", "checks")}))
    return 0 if receipt["status"] == "CLEAR_REAL_ENTRY_CONTRACT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
