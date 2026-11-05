"""Gate 6.7 runner integration: independent inputs and immutable execution bindings."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from types import ModuleType
import sys

import pytest

from eval import run_phase6_7_independent_evaluation as runner
from src.independent_reader_evaluation import invoke_reader
from src.independent_reader_scoring import canonical_digest


def dump(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def prepared_run(tmp_path, monkeypatch):
    app_calls = []
    packet_selections = []
    chat_requests = []
    config = {"base_url": "http://127.0.0.1:11434", "model": "test-vision:fixed",
              "model_digest": "a" * 64, "options": {"temperature": 0, "seed": 67,
              "num_predict": 1000, "num_ctx": 4096}, "timeout_seconds": 30}
    binding = {"evidence_id": "aws2020:pdf:13:full", "pdf_index": 13,
               "viewer_page": 14, "printed_page": 1, "crop": None}
    case = {"id": "development-example", "question": "What does the source support?",
            "category": "synthetic", "expected_status": "ANSWERED", "evidence": [binding],
            "claims": [{"claim_id": "fact", "description": "An expected source fact",
                        "evidence_ids": [binding["evidence_id"]], "qualifiers": []}]}
    suite = {"split": "development_exposed", "source": {"path": "synthetic.pdf",
             "sha256": "c" * 64, "page_count": 15}, "cases": [case]}
    suite_path = tmp_path / "suite.json"
    dump(suite_path, suite)
    query_module = ModuleType("src.query")

    def query(question, **kwargs):
        app_calls.append((question, kwargs))
        return {"answer": "SECRET APPLICATION ANSWER", "pdf_index": 14,
                "normative_provenance": [], "execution": {"status": "PASS"}}

    query_module.run_query = query
    query_module.get_query_event_loop = lambda: None
    monkeypatch.setitem(sys.modules, "src.query", query_module)

    def build_packet(root, source, question, evidence, **kwargs):
        packet_selections.append([e["pdf_index"] for e in evidence])
        pages = []
        for item in evidence:
            text = f"Native source page {item['pdf_index']}."
            pages.append({**deepcopy(item), "locator": "AWS A3.0M/A3.0:2020 source page",
                          "source_sha256": source["sha256"], "text": text,
                          "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                          "image_base64": "aW1hZ2U=",
                          "image_sha256": hashlib.sha256(b"image").hexdigest()})
        return {"question": question, "source_sha256": source["sha256"],
                "source_page_count": source["page_count"], "page_budget": 2,
                "rendering_dpi": 120, "evidence": pages}

    monkeypatch.setattr(runner, "build_source_packet", build_packet)

    def transport(url, payload, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": config["model"], "digest": config["model_digest"]}]}
        if url.endswith("/api/show"):
            return {"capabilities": ["vision", "completion"]}
        if url.endswith("/api/version"):
            return {"version": "synthetic"}
        assert url.endswith("/api/chat")
        chat_requests.append(deepcopy(payload))
        metadata = json.loads(payload["messages"][1]["content"].split("\nSOURCE PAGE TEXT:")[0])
        response = {"status": "ANSWERED", "answer": "Source information.", "claims": [
                    {"text": "Source information.", "evidence_ids": [metadata["evidence_id"]]}],
                    "abstention_reason": None}
        return {"model": config["model"], "done": True, "done_reason": "stop", "eval_count": 12,
                "prompt_eval_count": 20, "message": {"role": "assistant", "content": json.dumps(response)}}

    def invoke(packet, supplied_config, directory):
        return invoke_reader(packet, supplied_config, directory, transport=transport)

    monkeypatch.setattr(runner, "invoke_reader", invoke)
    prepared = tmp_path / "prepared"
    manifest = runner.prepare(suite_path, prepared, root=tmp_path)
    config_path = tmp_path / "config.json"
    dump(config_path, config)
    return {"root": tmp_path, "prepared": prepared, "manifest": manifest,
            "app_calls": app_calls, "packet_selections": packet_selections,
            "chat_requests": chat_requests, "config_path": config_path}


def test_prepare_uses_application_selection_before_gold_and_keeps_answers_separate(prepared_run):
    state = prepared_run
    assert state["app_calls"] == [("What does the source support?", {"evidence_version": "whole_standard"})]
    assert state["packet_selections"] == [[14], [13]]
    row = state["manifest"]["cases"][0]
    assert row["missing_gold_page_ids"] == ["aws2020:pdf:13:full"]
    assert state["manifest"]["reader_calls"] == 0
    for track in runner.TRACKS:
        packet = runner.read_json(state["prepared"] / "development-example" / f"{track}_packet.json")
        assert not {"claims", "expected_status", "answer"} & packet.keys()
        assert "SECRET APPLICATION ANSWER" not in json.dumps(packet)


def test_runner_executes_both_tracks_and_cannot_claim_quality_without_review(prepared_run):
    state = prepared_run
    run_dir = state["root"] / "run"
    summary = runner.run(state["prepared"], state["config_path"], run_dir, limit_cases=1)
    assert len(state["chat_requests"]) == 2
    assert summary["reader_accuracy"] is None
    assert summary["retrieval_vs_reader_quality_delta"] is None
    assert summary["qualification_status"] == "NOT_QUALIFIED"
    assert all(row["outcome"] != "PASS_SUPPORTED" for row in summary["results"])
    with pytest.raises(FileExistsError):
        runner.run(state["prepared"], state["config_path"], run_dir, limit_cases=1)


def test_changed_prepared_packet_blocks_all_inference(prepared_run):
    state = prepared_run
    path = state["prepared"] / "development-example" / "gold_packet.json"
    packet = runner.read_json(path)
    packet["evidence"][0]["text"] = "TAMPERED SOURCE OR ANSWER"
    dump(path, packet)
    with pytest.raises(ValueError, match="(?i)packet|digest|hash"):
        runner.run(state["prepared"], state["config_path"], state["root"] / "run", limit_cases=1)
    assert state["chat_requests"] == []


@pytest.mark.parametrize("changed", ["packet", "response", "raw", "request", "config"])
def test_scoring_rejects_changed_execution_inputs_and_outputs(prepared_run, changed):
    state = prepared_run
    run_dir = state["root"] / "run"
    runner.run(state["prepared"], state["config_path"], run_dir, limit_cases=1)
    directory = run_dir / "development-example" / "gold"
    if changed == "packet":
        path = state["prepared"] / "development-example" / "gold_packet.json"
        value = runner.read_json(path)
        value["evidence"][0]["text"] = "Changed source text"
    elif changed == "response":
        path = directory / "receipt.json"
        value = runner.read_json(path)
        value["response"]["answer"] = "Changed answer"
        value["response_sha256"] = canonical_digest(value["response"])
    elif changed == "raw":
        path = directory / "raw_response.json"
        value = runner.read_json(path)
        value["message"]["content"] = "{}"
    elif changed == "request":
        path = directory / "request.json"
        value = runner.read_json(path)
        value["messages"][-1]["content"] = "Changed question"
    else:
        path = directory / "config.json"
        value = runner.read_json(path)
        value["options"]["seed"] += 1
    dump(path, value)
    with pytest.raises(ValueError):
        runner.score(state["prepared"], run_dir, state["root"] / "reviews", state["root"] / "score.json")


def test_execution_failures_remain_in_scoring_denominator(prepared_run, monkeypatch):
    state = prepared_run
    config = runner.read_json(state["config_path"])

    def error_transport(url, payload, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": config["model"], "digest": config["model_digest"]}]}
        if url.endswith("/api/show"):
            return {"capabilities": ["vision"]}
        if url.endswith("/api/version"):
            return {"version": "synthetic"}
        return {"error": "Synthetic model execution unavailable"}

    def unavailable(packet, supplied_config, directory):
        return invoke_reader(packet, supplied_config, directory, transport=error_transport)

    monkeypatch.setattr(runner, "invoke_reader", unavailable)
    run_dir = state["root"] / "failed-run"
    summary = runner.run(state["prepared"], state["config_path"], run_dir, limit_cases=1)
    assert len(summary["results"]) == 2
    assert all(row["inference_attempted"] and row["raw_response_received"] for row in summary["results"])
    assert not any(row["inference_completed"] for row in summary["results"])
    scored = runner.score(state["prepared"], run_dir, state["root"] / "reviews", state["root"] / "score.json")
    assert scored["outcomes"].get("READER_EXECUTION_ERROR") == 2
