"""Offline reader execution contracts; HTTP and model results are synthetic."""
import base64
import io
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from src.evidence_reader import LocalVisionReader, build_messages, read_packet
from evidence_v2_fixture import fixture


def complete_messages(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Figure X1")
    return packet, data, build_messages(packet, tmp_path)


def reader():
    return LocalVisionReader("http://localhost:11434", "synthetic-installed-model", timeout=7)


def reject_with_http(monkeypatch, payload, *, reason="PRIVATE_PROVIDER_REASON"):
    seen = []

    class RejectingOpener:
        def open(self, request, timeout):
            seen.append((request, timeout))
            raise HTTPError(request.full_url, 500, reason, {},
                            io.BytesIO(json.dumps(payload).encode("utf-8")))

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: RejectingOpener())
    return seen


def test_native_request_has_bounded_context_and_output_budget(tmp_path):
    _, _, messages = complete_messages(tmp_path)
    body = reader().request_body(messages)
    assert body["options"]["num_ctx"] == 16384
    assert body["options"]["num_predict"] == 1024
    assert body["options"]["temperature"] == 0
    assert body["stream"] is False


def test_context_budget_does_not_remove_or_modify_continuation_pixels(tmp_path):
    _, data, messages = complete_messages(tmp_path)
    body = reader().request_body(messages)
    actual = [base64.b64decode(image, validate=True)
              for message in body["messages"] for image in message.get("images", [])]
    originals = [(tmp_path / item.content["asset_relpath"]).read_bytes()
                 for item in data["figures"]]
    assert len(actual) == len(originals) == 2
    assert actual == originals


def test_each_pixel_payload_has_adjacent_source_locator(tmp_path):
    _, data, messages = complete_messages(tmp_path)
    parts = messages[-1]["content"]
    image_positions = [i for i,p in enumerate(parts) if p["type"] == "image_url"]
    for position,item in zip(image_positions,data["figures"]):
        label = parts[position-1]["text"]
        assert item.evidence_id in label
        assert item.locator["element_id"] in label
        assert '"order": ' + str(item.locator["order"]) in label


def test_context_http_failure_retains_token_counts_without_private_body(monkeypatch, tmp_path):
    _, _, messages = complete_messages(tmp_path)
    seen = reject_with_http(monkeypatch, {
        "error": "request (13279 tokens) exceeds available context size (8192 tokens)",
        "private": "PRIVATE_BODY_TOKEN_s3cr3t",
    })
    with pytest.raises(ValueError) as raised:
        reader()(messages)
    diagnostic = str(raised.value)
    assert "13279" in diagnostic and "8192" in diagnostic
    assert "context" in diagnostic.lower()
    assert "PRIVATE" not in diagnostic and "s3cr3t" not in diagnostic
    assert len(seen) == 1
    assert seen[0][1] == 7


def test_unrecognized_http_failure_is_safe_and_does_not_echo_provider_body(monkeypatch, tmp_path):
    _, _, messages = complete_messages(tmp_path)
    reject_with_http(monkeypatch, {
        "error": "PRIVATE_BODY_TOKEN_s3cr3t: backend failed while reading private-file.pdf",
    })
    with pytest.raises(ValueError) as raised:
        reader()(messages)
    diagnostic = str(raised.value)
    assert diagnostic.strip()
    assert "PRIVATE" not in diagnostic and "s3cr3t" not in diagnostic
    assert "private-file.pdf" not in diagnostic


def test_memory_allocation_failure_retains_only_resource_numbers(monkeypatch, tmp_path):
    _, _, messages = complete_messages(tmp_path)
    reject_with_http(monkeypatch, {
        "error": "failed to allocate buffer of size 31457280000 PRIVATE_BODY_TOKEN_s3cr3t",
        "private": "PRIVATE_BODY_TOKEN_s3cr3t",
    })
    with pytest.raises(ValueError) as raised:
        reader()(messages)
    diagnostic = str(raised.value)
    assert "31457280000" in diagnostic
    assert "memory" in diagnostic.lower() or "allocation" in diagnostic.lower()
    assert "PRIVATE" not in diagnostic and "s3cr3t" not in diagnostic


def test_http_context_failure_withholds_answer_and_preserves_safe_diagnostic(monkeypatch, tmp_path):
    packet, _, _ = complete_messages(tmp_path)
    reject_with_http(monkeypatch, {
        "error": "request (13279 tokens) exceeds available context size (8192 tokens)",
        "private": "PRIVATE_BODY_TOKEN_s3cr3t",
    })
    result = read_packet(packet, tmp_path, generate=reader())
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["error_code"] == "V2_READER_FAILED"
    assert result["grounded_claims"] == []
    assert result["answer_assessment"]["semantic_validation"] is False
    answer = result["answer"]
    assert "13279" in answer and "8192" in answer
    assert "PRIVATE" not in answer and "s3cr3t" not in answer


def test_valid_empty_claims_are_abstention_with_observed_usage(tmp_path):
    packet, _, _ = complete_messages(tmp_path)
    result = read_packet(packet, tmp_path, generate=lambda _: {
        "claims": [], "usage": {"prompt_eval_count": 4035, "eval_count": 8}, "cost_usd": 0})
    assert result["answer_outcome"] == "insufficient_evidence"
    assert not result.get("error_code")
    assert result["usage"] == {"prompt_eval_count": 4035, "eval_count": 8}
    assert result["cost_usd"] == 0
    assert result["grounded_claims"] == []
    assert result["answer_assessment"]["semantic_validation"] is False
