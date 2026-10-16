"""Private system-query receipts; automatic checks never adjudicate answer truth.

Run only with explicit local execution authority. Frozen cases, rubrics, source
material, raw responses and receipts belong outside published source. Only the
query string enters the application; relevance labels never enter its prompt.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import datetime
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen2.5:3b"
MODEL_DIGEST = "357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b"
PROTECTED = ("storage/vdb_chunks.json", "storage/vdb_chunks_contextual.json",
             "storage/dual_layer_registry.db", "storage/kv_store_text_chunks.json",
             "storage/graph_chunk_entity_relation.graphml", "storage/dual_layer_knowledge_graph.graphml",
             "parsed/figures/figure_bboxes.json", "config/aws_a30_2020_manifest.json",
             "config/aws_a30_2020_manifest.receipt.json", "eval/gold_benchmark.json",
             "data/AWS_A3.0_2020.pdf", "storage/terminology_registry.json")
CACHE = "storage/kv_store_llm_response_cache.json"
CODE = ("eval/answer_grounding_evaluation.py", "src/query.py", "src/indexer.py",
        "src/grounded_answer.py", "src/terminology_retrieval.py", "src/terminology_mappings.py",
        "src/citation_checker.py", "src/epistemic_verifier.py", "src/answer_routes.py",
        "src/hybrid_retriever.py", "src/pre_retrieval.py", "src/standard_manifest.py",
        "src/config.py", "src/security_boundaries.py", "src/web.py")
OUTCOMES = {"extractive", "generated", "clarification", "abstention", "insufficient_evidence", "error"}
ORIGINS = {"composed", "generated", "none"}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_cases(data):
    if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
            or data["schema_version"] != 1 or not _text(data.get("suite_id"))
            or not isinstance(data.get("cases"), list) or not data["cases"]):
        raise ValueError("Invalid frozen system cases")
    seen = set()
    for case in data["cases"]:
        if (not isinstance(case, dict) or not _text(case.get("id")) or case["id"] in seen
                or not _text(case.get("query"))):
            raise ValueError("Invalid or duplicate frozen case ID/query")
        seen.add(case["id"])
    return deepcopy(data)


def validate_settings(settings):
    if not isinstance(settings, dict):
        raise ValueError("Explicit local Custom settings are required")
    if (settings.get("engine") != "custom" or settings.get("model_name") != MODEL
            or settings.get("mode") not in {"mix", "naive", "local", "global"}):
        raise ValueError("Unapproved engine/model/mode")
    expected = {"endpoint": (8001, "/api/query"), "base_url": (11434, "/v1")}
    for key, (port, path) in expected.items():
        value = settings.get(key)
        try:
            parsed = urllib.parse.urlsplit(value)
            valid = (isinstance(value, str) and parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                     and parsed.port == port and parsed.path.rstrip("/") == path
                     and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise ValueError("Only the explicit approved literal-loopback destination is permitted: " + key)
    return deepcopy(settings)


def validate_server_config(configuration, settings):
    validate_settings(settings)
    if (not isinstance(configuration, dict) or configuration.get("custom_configured") is not True
            or configuration.get("custom_model") != settings["model_name"]
            or not isinstance(configuration.get("custom_base_url"), str)
            or configuration["custom_base_url"].rstrip("/") != settings["base_url"].rstrip("/")):
        raise ValueError("Server Custom configuration does not match the approved local settings")
    return deepcopy(configuration)


def _capture_response(row, envelope):
    if not isinstance(envelope, dict) or not isinstance(envelope.get("response"), dict):
        raise ValueError("Malformed system response envelope")
    raw = deepcopy(envelope["response"])
    row.update(response=raw, http_status=envelope.get("http_status"))
    outcome, origin = raw.get("answer_outcome"), raw.get("answer_origin")
    if outcome is not None and outcome not in OUTCOMES or origin is not None and origin not in ORIGINS:
        raise ValueError("Unknown system outcome/origin metadata")
    row["answer_outcome"] = outcome or "unassessed"
    row["answer_origin"] = origin or "legacy_unassessed"
    row["reported_claim_bindings"] = deepcopy(raw.get("grounded_claims", []))
    row["reported_canonical_citations"] = deepcopy(raw.get("citations", {}))
    row["reported_stage_timings_ms"] = deepcopy(raw.get("timings_ms"))
    assessment, answer = raw.get("answer_assessment"), raw.get("answer")
    row["reported_assessment"] = deepcopy(assessment)
    row["assessment_answer_binding_valid"] = None
    if isinstance(assessment, dict) and (assessment.get("validated") is True or "answer_sha256" in assessment):
        row["assessment_answer_binding_valid"] = isinstance(answer, str) and assessment.get("answer_sha256") == _sha(answer)
    if not isinstance(answer, str):
        raise ValueError("System answer must be a string")
    status = row["http_status"]
    if (status is not None and (type(status) is not int or not 200 <= status < 300)
            or raw.get("error") or raw.get("error_code") or outcome == "error"):
        row.update(answer_outcome="error", error={"type": "SystemError", "message": "System returned an error; see private raw response."})


def capture_cases(cases, invoke, on_row=None):
    """Invoke actual query strings once; never pass rubric metadata to the system."""
    rows, halted = [], False
    for case in cases:
        row = {"id": case["id"], "query": case["query"], "attempted": not halted,
               "answer_origin": "none", "answer_outcome": "not_run", "response": None}
        if not halted:
            started = time.perf_counter()
            try:
                _capture_response(row, invoke(case["query"]))
            except Exception as error:
                row.update(answer_outcome="error", error={"type": type(error).__name__,
                           "message": "System request failed; no retry or provider substitution was attempted."})
            row["request_wall_ms"] = (time.perf_counter() - started) * 1000
            if on_row is not None:
                try:
                    on_row(row)
                except Exception as error:
                    row["receipt_error"] = {"type": type(error).__name__, "message": "Capture fingerprint/configuration drift; remaining requests stopped."}
            halted = bool(row.get("error") or row.get("receipt_error"))
        else:
            row["not_run_reason"] = "Stopped after the preceding execution or receipt error"
        rows.append(row)
    return rows


def summarize_rows(rows):
    outcomes = Counter(row.get("answer_outcome", "unassessed") for row in rows)
    origins = Counter(row.get("answer_origin", "legacy_unassessed") for row in rows)
    assessments = Counter(row["reported_assessment"].get("status", "unassessed") for row in rows
                          if isinstance(row.get("reported_assessment"), dict))
    answered = sum(row.get("answer_outcome") in {"extractive", "generated"}
                   and _text((row.get("response") or {}).get("answer")) for row in rows)
    return {"declared_cases": len(rows), "attempted_cases": sum(row.get("attempted") is True for row in rows),
            "outcomes": dict(outcomes), "origins": dict(origins), "errors": outcomes.get("error", 0),
            "receipt_errors": sum(bool(row.get("receipt_error")) for row in rows),
            "not_run": outcomes.get("not_run", 0), "reported_answer_coverage": answered / len(rows) if rows else None,
            "self_reported_assessments": dict(assessments),
            "assessment_binding_failures": sum(row.get("assessment_answer_binding_valid") is False for row in rows),
            "system_composed_is_model_gain": False, "model_accuracy": "unadjudicated",
            "interpretation": "Outcome/binding metadata only; frozen source-fact adjudication is separate"}


def validate_report(report, phase=None):
    if (not isinstance(report, dict) or report.get("kind") != "answer-grounding-system-capture"
            or report.get("lane") != "system" or report.get("phase") not in {"before", "after"}
            or phase is not None and report["phase"] != phase):
        raise ValueError("Invalid system receipt kind/lane/phase")
    validate_settings(report.get("settings"))
    if any(report.get(key) is not True for key in ("protected_unchanged", "code_unchanged", "inputs_unchanged", "evaluator_unchanged")):
        raise ValueError("System capture drift or missing preservation evidence")
    if report.get("transport") not in {"http", "inprocess"} or not _hash(report.get("evaluator_sha256")):
        raise ValueError("Missing/invalid system transport or capture evaluator fingerprint")
    model = report.get("model_provenance")
    if (not isinstance(model, dict) or model.get("name") != MODEL or model.get("digest") != MODEL_DIGEST
            or model.get("remote_host") or model.get("remote_model") or not isinstance(model.get("details"), dict)
            or model["details"].get("format") != "gguf"):
        raise ValueError("Missing/invalid approved local model provenance")
    cases, rows = report.get("cases"), report.get("rows")
    validate_cases({"schema_version": 1, "suite_id": "receipt", "cases": cases})
    expected = {case["id"]: case for case in cases}
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("Incomplete system capture case denominator")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or not _text(row.get("id")) or row["id"] in seen
                or row["id"] not in expected or row.get("query") != expected[row["id"]]["query"]
                or not _hash(row.get("case_file_sha256"))):
            raise ValueError("Invalid system capture duplicate/unknown/frozen case binding")
        seen.add(row["id"])
    for name in ("qrels_fingerprints", "protected_fingerprints", "code_fingerprints"):
        values = report.get(name)
        if not isinstance(values, dict) or not values or not all(value is None or _hash(value) for value in values.values()):
            raise ValueError("Invalid system capture fingerprint namespace: " + name)
    return report


def compare_reports(before, after):
    validate_report(before, "before")
    validate_report(after, "after")
    for key in ("settings", "qrels_fingerprints", "protected_fingerprints", "transport", "evaluator_sha256"):
        if before[key] != after[key]:
            raise ValueError("Incompatible system comparison: " + key)
    if before.get("model_provenance") != after.get("model_provenance"):
        raise ValueError("Incompatible system comparison: local model provenance")
    old, new = ({row["id"]: row for row in value["rows"]} for value in (before, after))
    paired = [identifier for identifier in old if identifier in new]
    if not paired:
        raise ValueError("No actual paired system cases")
    for identifier in paired:
        if any(old[identifier].get(key) != new[identifier].get(key) for key in ("query", "case_file_sha256")):
            raise ValueError("Frozen paired system case changed")
    return {"lane": "system", "paired_case_ids": paired,
            "system_before_only_case_ids": [identifier for identifier in old if identifier not in new],
            "system_after_only_case_ids": [identifier for identifier in new if identifier not in old],
            "paired_before": summarize_rows([old[identifier] for identifier in paired]),
            "paired_after": summarize_rows([new[identifier] for identifier in paired]),
            "all_before": summarize_rows(before["rows"]), "all_after": summarize_rows(after["rows"]),
            "code_fingerprints_before": before["code_fingerprints"], "code_fingerprints_after": after["code_fingerprints"],
            "model_only_accuracy_gain": False, "factual_accuracy": "unadjudicated",
            "interpretation": "Component-model receipts are separate; unmatched system cases have no paired system baseline"}


def prepare_output(path):
    path = Path(path).resolve()
    if path.is_relative_to(ROOT):
        raise ValueError("Output must be outside the repository")
    if path.exists():
        raise ValueError("Output must be a fresh directory")
    path.mkdir(parents=True)
    return path


def _fingerprints(names):
    return {name: _sha((ROOT / name).read_bytes()) if (ROOT / name).is_file() else None for name in names}


def evaluator_fingerprint():
    """The loaded evaluator can be staged outside the evaluated repository."""
    return _sha(Path(__file__).resolve().read_bytes())


def _write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _file_hashes(paths):
    return {str(Path(path).resolve()): _sha(Path(path).read_bytes()) for path in paths}


def _loopback(address):
    try:
        return isinstance(address, tuple) and ipaddress.ip_address(address[0]).is_loopback
    except (ValueError, TypeError, IndexError):
        return False


@contextmanager
def _local_runtime():
    """No DNS/remote sockets; protect existing evidence files in-process."""
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        os.environ[key] = "1"
    sys.dont_write_bytecode = True
    patches = []
    def patch(owner, name, value):
        patches.append((owner, name, getattr(owner, name)))
        setattr(owner, name, value)
    for name in ("connect", "connect_ex", "sendto"):
        original = getattr(socket.socket, name)
        def restricted(instance, *args, _original=original, _name=name, **kwargs):
            if not _loopback(args[-1] if _name == "sendto" else args[0]):
                raise PermissionError("Non-loopback socket forbidden")
            return _original(instance, *args, **kwargs)
        patch(socket.socket, name, restricted)
    original_resolve = socket.getaddrinfo
    def resolve(host, port, *args, **kwargs):
        if not _loopback((host, port)):
            raise PermissionError("Non-loopback name resolution forbidden")
        return original_resolve(host, port, *args, **kwargs)
    patch(socket, "getaddrinfo", resolve)
    registry = (ROOT / "storage/dual_layer_registry.db").resolve()
    original_connect = sqlite3.connect
    def readonly(path, *args, **kwargs):
        if str(path).startswith("file:") or Path(path).resolve() != registry or not registry.is_file():
            raise PermissionError("Only the existing read-only registry is permitted")
        return original_connect(registry.as_uri() + "?mode=ro", uri=True, timeout=15)
    patch(sqlite3, "connect", readonly)
    protected = {(ROOT / path).resolve() for path in PROTECTED}
    for owner in (io, __import__("builtins")):
        original = owner.open
        def guarded(file, mode="r", *args, _original=original, **kwargs):
            if not isinstance(file, int) and any(flag in mode for flag in "wax+") and Path(file).resolve() in protected:
                raise PermissionError("Protected source/index write forbidden")
            return _original(file, mode, *args, **kwargs)
        patch(owner, "open", guarded)
    try:
        yield
    finally:
        for owner, name, original in reversed(patches):
            setattr(owner, name, original)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PermissionError("HTTP redirects forbidden")


def _request(opener, url, timeout, payload=None):
    request = urllib.request.Request(url, data=None if payload is None else _json(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return {"http_status": response.code, "response": json.load(response)}


def _server_config(opener, settings, timeout):
    url = settings["endpoint"].rsplit("/", 1)[0] + "/config_status"
    envelope = _request(opener, url, timeout)
    if envelope["http_status"] != 200:
        raise ValueError("Server configuration preflight failed")
    raw = envelope["response"]
    # Deliberately retain only the known non-secret configuration fields.
    result = {key: raw.get(key) for key in ("custom_configured", "custom_base_url", "custom_model", "default_engine")}
    return validate_server_config(result, settings)


def _model_info(opener, settings, timeout, expected_digest):
    envelope = _request(opener, "http://127.0.0.1:11434/api/tags", timeout)
    if envelope["http_status"] != 200:
        raise ValueError("Local model provenance preflight failed")
    found = next((item for item in envelope["response"].get("models", []) if item.get("name") == MODEL), None)
    if (not found or found.get("digest") != expected_digest or found.get("remote_host") or found.get("remote_model")
            or found.get("details", {}).get("format") != "gguf"):
        raise ValueError("Approved already-installed local model digest/format mismatch")
    return {key: deepcopy(found.get(key)) for key in ("name", "digest", "size", "details")}


def capture(case_files, qrels_files, baseline_file, output_dir, phase, settings, transport="http", timeout=120,
            expected_model_digest=MODEL_DIGEST):
    settings = validate_settings(settings)
    if phase not in {"before", "after"} or transport not in {"http", "inprocess"} or not 1 <= timeout <= 300:
        raise ValueError("Invalid capture phase/transport/timeout")
    if not _hash(expected_model_digest):
        raise ValueError("Explicit approved model digest required")
    case_files, qrels_files = [Path(path).resolve() for path in case_files], [Path(path).resolve() for path in qrels_files]
    if not case_files or not qrels_files or any(path.is_relative_to(ROOT) for path in case_files + qrels_files):
        raise ValueError("Cases and hash-only qrels inputs must be external local files")
    declared, binding, files = [], {}, {}
    for path in case_files:
        raw = path.read_bytes()
        data = validate_cases(json.loads(raw.decode("utf-8")))
        files[str(path)] = _sha(raw)
        for case in data["cases"]:
            if case["id"] in binding:
                raise ValueError("Duplicate case ID across frozen files")
            declared.append(case)
            binding[case["id"]] = _sha(raw)
    baseline = json.loads(Path(baseline_file).read_text(encoding="utf-8"))
    expected = {name: baseline.get("protected_hashes", {}).get(name) for name in PROTECTED}
    protected, code = _fingerprints(PROTECTED), _fingerprints(CODE)
    evaluator_sha256 = evaluator_fingerprint()
    if not all(_hash(value) for value in expected.values()) or protected != expected:
        raise ValueError("Protected source/index baseline mismatch; no requests made")
    input_paths = case_files + qrels_files + [Path(baseline_file).resolve()]
    inputs = _file_hashes(input_paths)
    qrels_hashes = _file_hashes(qrels_files)  # Bytes only: no rubric facts parsed or sent.
    output, cache_before = prepare_output(output_dir), _fingerprints((CACHE,))
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = {"kind": "answer-grounding-system-capture", "lane": "system", "phase": phase, "transport": transport,
              "settings": settings, "cases": deepcopy(declared), "case_file_fingerprints": files,
              "qrels_fingerprints": qrels_hashes, "protected_fingerprints": protected, "code_fingerprints": code,
              "evaluator_sha256": evaluator_sha256,
              "input_fingerprints": inputs, "started_utc": started,
              "truth_status": "unadjudicated; use the unchanged independent frozen source rubric",
              "http_loaded_code_attestation": "Disk fingerprints alone do not attest the running server's loaded code",
              "generation_settings": "Actual application settings; values not exposed by the system are unassessed"}
    checkpoints = []
    with _local_runtime():
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        try:
            configuration = _server_config(opener, settings, min(timeout, 10)) if transport == "http" else None
            model_info = _model_info(opener, settings, min(timeout, 10), expected_model_digest)
            report.update(server_configuration=configuration, model_provenance=model_info)
            if transport == "inprocess":
                os.environ.update(CUSTOM_BASE_URL=settings["base_url"], CUSTOM_MODEL=MODEL, CUSTOM_API_KEY="local-evaluation")
                if str(ROOT) not in sys.path:
                    sys.path.insert(0, str(ROOT))
                from src import config, query
                if (config.CUSTOM_BASE_URL.rstrip("/") != settings["base_url"].rstrip("/")
                        or config.CUSTOM_MODEL != MODEL or Path(query.__file__).resolve() != ROOT / "src/query.py"):
                    raise ValueError("In-process application configuration/path mismatch")
            def invoke(question):
                payload = {"query": question, "engine": "custom", "mode": settings["mode"],
                           "model_name": MODEL, "base_url": settings["base_url"], "api_key": "local-evaluation"}
                if transport == "http":
                    return _request(opener, settings["endpoint"], timeout, payload)
                return {"http_status": None, "response": query.run_query(question, engine="custom", mode=settings["mode"],
                        model_name=MODEL, base_url=settings["base_url"], api_key="local-evaluation")}
            def checkpoint(row):
                row["case_file_sha256"] = binding[row["id"]]
                checkpoint_started = time.perf_counter()
                checks = {"id": row["id"], "protected_unchanged": protected == _fingerprints(PROTECTED),
                          "code_unchanged": code == _fingerprints(CODE) and evaluator_sha256 == evaluator_fingerprint(),
                          "inputs_unchanged": inputs == _file_hashes(input_paths)}
                checkpoints.append(checks)
                row["receipt_check_ms"] = (time.perf_counter() - checkpoint_started) * 1000
                _write(output / ("case-" + str(len(checkpoints)).zfill(3) + ".json"), row)
                print("Captured case " + str(len(checkpoints)), flush=True)
                if not all(value for key, value in checks.items() if key != "id"):
                    raise ValueError("Protected capture drift")
            report["rows"] = capture_cases(declared, invoke, checkpoint)
            if transport == "http" and _server_config(opener, settings, min(timeout, 10)) != configuration:
                raise ValueError("Server configuration changed during capture")
            if _model_info(opener, settings, min(timeout, 10), expected_model_digest) != model_info:
                raise ValueError("Local model provenance changed during capture")
        except Exception as error:
            report["capture_error"] = {"type": type(error).__name__, "message": "System capture/preflight failed; no retry or provider substitution attempted."}
            if "rows" not in report:
                report["rows"] = [{"id": case["id"], "query": case["query"], "attempted": False,
                                   "answer_outcome": "not_run", "answer_origin": "none", "response": None} for case in declared]
    for row in report["rows"]:
        row["case_file_sha256"] = binding[row["id"]]
    report.update(protected_unchanged=protected == _fingerprints(PROTECTED),
                  code_unchanged=code == _fingerprints(CODE) and evaluator_sha256 == evaluator_fingerprint(),
                  evaluator_unchanged=evaluator_sha256 == evaluator_fingerprint(),
                  inputs_unchanged=inputs == _file_hashes(input_paths), checkpoints=checkpoints,
                  cache_fingerprints_before=cache_before, cache_fingerprints_after=_fingerprints((CACHE,)),
                  summary=summarize_rows(report["rows"]), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    _write(output / "report.json", report)
    print(_json({"output": str(output), "summary": report["summary"], "capture_error": bool(report.get("capture_error"))}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("capture")
    run.add_argument("--cases", type=Path, action="append", required=True)
    run.add_argument("--qrels", type=Path, action="append", required=True)
    run.add_argument("--baseline", type=Path, required=True)
    run.add_argument("--phase", choices=("before", "after"), required=True)
    run.add_argument("--transport", choices=("http", "inprocess"), default="http")
    run.add_argument("--endpoint", required=True)
    run.add_argument("--base-url", required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--engine", choices=("custom",), default="custom")
    run.add_argument("--mode", choices=("mix", "naive", "local", "global"), default="mix")
    run.add_argument("--timeout", type=float, default=120)
    run.add_argument("--expected-model-digest", default=MODEL_DIGEST)
    run.add_argument("--output-dir", type=Path, required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--before", type=Path, required=True)
    compare.add_argument("--after", type=Path, required=True)
    compare.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "capture":
        settings = {"endpoint": args.endpoint, "base_url": args.base_url, "model_name": args.model,
                    "engine": args.engine, "mode": args.mode}
        result = capture(args.cases, args.qrels, args.baseline, args.output_dir, args.phase, settings,
                         args.transport, args.timeout, args.expected_model_digest)
        if result.get("capture_error") or not all(result[key] for key in ("protected_unchanged", "code_unchanged", "inputs_unchanged")) or result["summary"]["errors"] or result["summary"]["receipt_errors"]:
            raise SystemExit(1)
    else:
        before, after = (json.loads(path.read_text(encoding="utf-8")) for path in (args.before, args.after))
        output = prepare_output(args.output_dir)
        _write(output / "report.json", compare_reports(before, after))


if __name__ == "__main__":
    main()
