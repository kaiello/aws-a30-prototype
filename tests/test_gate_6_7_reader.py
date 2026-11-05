import copy
import json

import pytest

from src.independent_reader_evaluation import (
    build_reader_request, invoke_reader, retrieved_evidence_selection, validate_config,
)


@pytest.fixture
def config():
    return {"base_url": "http://127.0.0.1:11434", "model": "local-vision:fixed",
            "model_digest": "a" * 64, "options": {"temperature": 0, "seed": 67,
            "num_predict": 1200, "num_ctx": 16384}, "timeout_seconds": 180}


@pytest.fixture
def packet():
    return {"question": "Explain the source.", "page_budget": 2, "evidence": [
        {"evidence_id": "aws2020:pdf:20:full", "pdf_index": 20, "viewer_page": 21,
         "printed_page": 8, "text": "Native source words.", "image_base64": "aW1hZ2U=",
         "source_sha256": "b" * 64, "text_sha256": "c" * 64,
         "image_sha256": "d" * 64, "locator": "source page", "crop": None}]}


def test_request_whitelists_source_and_does_not_copy_gold_or_app_answers(config, packet):
    packet.update(expected_status="ANSWERED", answer="SECRET APP ANSWER", claims=["GOLD RUBRIC"])
    request = build_reader_request(packet, config)
    wire = json.dumps(request)
    assert "Native source words." in wire and "aW1hZ2U=" in wire
    assert "SECRET APP ANSWER" not in wire and "GOLD RUBRIC" not in wire
    assert request["stream"] is False and request["options"] == config["options"]


@pytest.mark.parametrize("url", ["https://example.com", "http://localhost.evil:11434",
    "http://user@localhost:11434", "http://127.0.0.1:11434/proxy", "http://[::1]:11434?x=1"])
def test_remote_or_ambiguous_destination_rejected(config, url):
    config["base_url"] = url
    with pytest.raises(ValueError):
        validate_config(config)


def test_model_must_be_pinned_and_local(config):
    config["model_digest"] = "latest"
    with pytest.raises(ValueError):
        validate_config(config)
    config["model_digest"] = "a" * 64
    config["model"] = "kimi:cloud"
    with pytest.raises(ValueError):
        validate_config(config)


def test_reader_verifies_model_before_and_after_and_captures_raw(config, packet, tmp_path):
    calls = []
    def transport(url, payload, timeout):
        calls.append((url, payload))
        if url.endswith("/api/tags"):
            return {"models": [{"name": config["model"], "digest": "a" * 64}]}
        if url.endswith("/api/show"):
            return {"capabilities": ["vision", "completion"]}
        if url.endswith("/api/version"):
            return {"version": "test-server"}
        return {"done": True, "model": config["model"], "message": {"content": json.dumps(
            {"status": "ABSTAIN", "answer": "Insufficient evidence.", "claims": [],
             "abstention_reason": "Insufficient source."})}}
    receipt = invoke_reader(packet, config, tmp_path / "call", transport=transport)
    assert receipt["execution_mode"] == "local_ollama_reader"
    assert (tmp_path / "call" / "request.json").exists()
    assert (tmp_path / "call" / "raw_response.json").exists()
    assert len([c for c in calls if c[0].endswith("/api/chat")]) == 1
    with pytest.raises(FileExistsError):
        invoke_reader(packet, config, tmp_path / "call", transport=transport)


def test_digest_change_blocks_inference(config, packet, tmp_path):
    calls = []
    def transport(url, payload, timeout):
        calls.append(url)
        return {"models": [{"name": config["model"], "digest": "wrong"}]}
    with pytest.raises(ValueError, match="digest"):
        invoke_reader(packet, config, tmp_path / "call", transport=transport)
    assert not any(url.endswith("/api/chat") for url in calls)


def test_retrieval_pages_come_from_app_provenance_only():
    result = {"pdf_index": 60, "normative_provenance": ["obs:pdf:18:term:x", "obs:pdf:37:term:y"],
              "answer": "The GOLD ANSWER says PDF 162", "plan": {"expected_page": 169}}
    selection = retrieved_evidence_selection(result, max_pages=2)
    assert [e["pdf_index"] for e in selection["evidence"]] == [60, 18]
    assert selection["omitted_pages"] == [37]


def test_empty_retrieval_not_repaired_with_gold():
    assert retrieved_evidence_selection({"answer": "PDF index 60"})["evidence"] == []
