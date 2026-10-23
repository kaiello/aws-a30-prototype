"""Opt-in local question planning; no source uploads or model answer generation.

The local transport retains the exact request and streamed response before plan
validation. The source graph, relationships, gold and prior answers are never
model inputs. The validated plan is executed by the existing graph backend.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from src.evidence_a1_vision import (
    APPROVED_VERSION, _canonical, _json_local, _open_local, _strict_loads,
)

VERSION = "chart-local-planner-1.1"
APPROVED_MODEL = "qwen2.5:3b"
APPROVED_DIGEST = "357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b"
OPTIONS = {"num_ctx": 16384, "num_predict": -1, "temperature": 0, "seed": 42}


def _rejected(query, reason):
    return {"query": query, "status": "unsupported", "operations": [],
            "resolved_entities": [], "unresolved_selectors": [], "mentions": [],
            "diagnostics": [reason],
            "requested_parts": [{"id": "intent:rejected", "text": query,
                "span": [0, len(query)], "kind": "unresolved", "subject_ids": [],
                "operation_ids": [], "status": "unsupported", "reason": reason}]}


def _write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(_canonical(value))


def _nonproductive(text):
    """Detect sustained periodic text, including arbitrary sentence lengths."""
    tail = text[-4096:]
    if len(tail) < 1024:
        return False
    if not tail[-1024:].strip():
        return True
    for period in range(1, 513):
        copies = max(4, (1024 + period - 1) // period)
        size = period * copies
        if size <= len(tail) and tail[-size:] == tail[-period:] * copies:
            return True
    return False


def inspect_local():
    """Metadata only; never downloads or loads a model."""
    version = _json_local("/api/version")
    models = _json_local("/api/tags")
    match = [item for item in models.get("models", [])
             if item.get("name") == APPROVED_MODEL and item.get("digest") == APPROVED_DIGEST]
    if version.get("version") != APPROVED_VERSION or len(match) != 1:
        raise ValueError("LOCAL_PLANNER_RUNTIME_OR_MODEL_CHANGED")
    shown = _json_local("/api/show", {"model": APPROVED_MODEL})
    return {"provider": "local_ollama_proxy_not_production", "model": APPROVED_MODEL,
            "digest": APPROVED_DIGEST, "runtime": version,
            "model_info": shown.get("model_info", {}),
            "template_sha256": hashlib.sha256(shown.get("template", "").encode()).hexdigest(),
            "capabilities": shown.get("capabilities", []), "options": dict(OPTIONS),
            "loaded_models": _json_local("/api/ps")}


def generate(prompt, schema, directory):
    """One streamed request, without retries or an artificial output-token cap.

    A finite runtime window still applies. Context exhaustion, incomplete streams,
    socket errors and nonproductive repetition are infrastructure failures, not
    answer-quality judgments. All partial bytes remain available for diagnosis.
    """
    # Byte-level tokenization cannot require more tokens than input UTF-8 bytes.
    # Reserve template/output space conservatively instead of truncating source
    # identities or the question. This is an input fit check, not an output cap.
    if not isinstance(prompt, str) or len(prompt.encode("utf-8")) > OPTIONS["num_ctx"] - 4096:
        raise ValueError("LOCAL_PLANNER_INPUT_EXCEEDS_CONSERVATIVE_CONTEXT_BUDGET")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    request = {"model": APPROVED_MODEL, "prompt": prompt, "format": schema,
               "stream": True, "options": dict(OPTIONS), "keep_alive": "10m"}
    _write(directory / "request.json", request)
    started = time.perf_counter()
    text, thinking, final, error, repeated = "", "", None, None, False
    try:
        with _open_local("/api/generate", request, timeout=180) as response:
            with (directory / "response.ndjson").open("xb") as raw:
                for line in response:
                    raw.write(line)
                    raw.flush()
                    item = _strict_loads(line)
                    if item.get("error"):
                        raise RuntimeError("LOCAL_BACKEND_ERROR: " + str(item["error"]))
                    text += item.get("response", "")
                    thinking += item.get("thinking", "")
                    # Repeated blocks are a resource stop, not a token budget.
                    combined = thinking + text
                    if _nonproductive(combined):
                        repeated = True
                        raise RuntimeError("NONPRODUCTIVE_REPETITION_STOP")
                    if time.perf_counter() - started > 1800:
                        raise TimeoutError("LOCAL_PLANNER_WALL_RESOURCE_STOP")
                    if item.get("done"):
                        final = item
                        break
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
    receipt = {"version": VERSION, "model": APPROVED_MODEL, "digest": APPROVED_DIGEST,
               "provider": "local_ollama_proxy_not_production", "options": dict(OPTIONS),
               "elapsed_seconds": time.perf_counter() - started,
               "request_sha256": hashlib.sha256(_canonical(request)).hexdigest(),
               "raw_output": text, "thinking": thinking, "final": final, "error": error,
               "resource_stop": repeated, "model_invocation_count": 1,
               "external_call_count": 0}
    if not final and error is None:
        receipt["error"] = {"type": "IncompleteStream", "message": "No backend final event"}
    if final and final.get("done_reason") != "stop":
        receipt["error"] = {"type": "GenerationIncomplete",
                            "message": "Backend stop reason: " + str(final.get("done_reason"))}
    _write(directory / "receipt.json", receipt)
    return receipt


class LocalQuestionPlanner:
    """Callable used by both canonical figure backends; dictionary input only."""
    def __init__(self, root, directory):
        from src.evidence_a1_cli import write_private_output
        self.directory = Path(directory)
        if not self.directory.is_absolute():
            self.directory = Path(root) / self.directory
        if self.directory.exists():
            raise ValueError("LOCAL_PLANNER_NEW_PRIVATE_DIRECTORY_REQUIRED")
        write_private_output(root, self.directory / "scope.json", {
            "version": VERSION, "scope": "question_and_source_dictionary_only"})
        self.metadata = inspect_local()
        _write(self.directory / "runtime.json", self.metadata)
        self.calls = []
        self.requests = 0
        self.structural_block = None

    def record_result(self, answer):
        """Preserve each actual backend answer before the next model request."""
        _write(self.directory / f"answer_{self.requests:03d}.json", answer)

    def _generate(self, prompt, schema, directory):
        return generate(prompt, schema, directory)

    def __call__(self, graph, query, *, concept_bindings=None):
        from src.evidence_chart_llm_plan import build_prompt, output_schema, compile_plan
        if getattr(self, "structural_block", None):
            raise RuntimeError("PLANNER_SCHEMA_INTEGRATION_BLOCKER: " + self.structural_block)
        self.requests += 1
        directory = self.directory / f"request_{self.requests:03d}"
        try:
            prompt, schema = build_prompt(graph, query), output_schema(graph)
        except (ValueError, TypeError, KeyError) as exc:
            plan = _rejected(query, "PLANNING_PREFLIGHT_REJECTED: " + str(exc))
            plan["model_planning"] = {"model": self.metadata.get("model", APPROVED_MODEL),
                "provider": self.metadata.get("provider", "local_ollama_proxy_not_production"),
                "model_invocation_count": 0}
            directory.mkdir(exist_ok=False)
            _write(directory / "preflight_rejection.json", plan)
            return plan
        receipt = self._generate(prompt, schema, directory)
        self.calls.append(receipt)
        if receipt["error"]:
            raise RuntimeError("LOCAL_PLAN_INFRASTRUCTURE_FAILURE: " + receipt["error"]["message"])
        try:
            payload = _strict_loads(receipt["raw_output"])
            plan = compile_plan(graph, query, payload, concept_bindings=concept_bindings)
        except (ValueError, TypeError, KeyError) as exc:
            # An invalid envelope never falls back to a guessed answer. Inside
            # a valid batch, the compiler keeps per-operation failures explicit
            # while permitting independently validated operations to execute.
            plan = _rejected(query, "MODEL_PLAN_REJECTED: " + str(exc))
            if getattr(self, "enforces_structured_schema", True) and (
                    isinstance(exc, json.JSONDecodeError) or any(code in str(exc) for code in (
                    "TOP_LEVEL_INVALID", "OPERATION_KEYS_INVALID", "PART_KEYS_INVALID"))):
                # Do not spend a whole cohort repeating a broken transport
                # shape. Preserve this answer, then stop before another call.
                self.structural_block = str(exc)
        plan["model_planning"] = {key: receipt[key] for key in (
            "version", "model", "digest", "provider", "options", "elapsed_seconds",
            "request_sha256", "model_invocation_count", "external_call_count")}
        _write(directory / "validated_plan.json", plan)
        return plan


def create_question_planner(root, directory, provider="ollama"):
    if provider == "ollama":
        return LocalQuestionPlanner(root, directory)
    if provider == "deepseek":
        from src.evidence_chart_deepseek_planner import DeepSeekQuestionPlanner
        return DeepSeekQuestionPlanner(root, directory)
    raise ValueError("PLANNER_PROVIDER_NOT_ALLOWED")
