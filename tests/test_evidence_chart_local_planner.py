"""Focused local-only transport checks; no model calls or AWS source fixtures."""
from contextlib import contextmanager
import json
import pytest

from src import evidence_chart_local_planner as local
from test_evidence_chart_llm_plan import source
from test_evidence_a1_graph_qa import toy_graph


def test_stream_records_unlimited_output_and_natural_stop(tmp_path, monkeypatch):
    captured = {}
    @contextmanager
    def fake_open(path, body, *, timeout):
        captured.update(path=path, body=body)
        yield [b'{"response":"{}","done":false}\n',
               b'{"response":"","done":true,"done_reason":"stop","eval_count":2}\n']
    monkeypatch.setattr(local, "_open_local", fake_open)
    receipt = local.generate("request", {"type": "object"}, tmp_path / "run")
    assert captured["path"] == "/api/generate"
    assert captured["body"]["options"]["num_predict"] == -1
    assert receipt["error"] is None and receipt["raw_output"] == "{}"
    assert (tmp_path / "run/response.ndjson").read_bytes().endswith(b'2}\n')


def test_length_stop_is_infrastructure_failure_and_keeps_raw(tmp_path, monkeypatch):
    @contextmanager
    def fake_open(*args, **kwargs):
        yield [b'{"response":"{","done":true,"done_reason":"length"}\n']
    monkeypatch.setattr(local, "_open_local", fake_open)
    receipt = local.generate("request", {}, tmp_path / "run")
    assert receipt["error"]["type"] == "GenerationIncomplete"
    assert json.loads((tmp_path / "run/receipt.json").read_text())["raw_output"] == "{"


def test_missing_final_event_never_reports_success(tmp_path, monkeypatch):
    @contextmanager
    def fake_open(*args, **kwargs):
        yield [b'{"response":"{}","done":false}\n']
    monkeypatch.setattr(local, "_open_local", fake_open)
    receipt = local.generate("request", {}, tmp_path / "run")
    assert receipt["error"]["type"] == "IncompleteStream"


def test_foreign_scope_abstains_without_call_and_preserves_each_result(tmp_path, source):
    planner = local.LocalQuestionPlanner.__new__(local.LocalQuestionPlanner)
    planner.directory, planner.calls, planner.requests = tmp_path, [], 0
    planner.metadata = {}
    for index in range(1, 3):
        result = planner(source, "Inspect Figure A3.")
        assert not result["operations"] and result["model_planning"]["model_invocation_count"] == 0
        planner.record_result(result)
        assert (tmp_path / f"request_{index:03d}/preflight_rejection.json").exists()
        assert (tmp_path / f"answer_{index:03d}.json").exists()
    assert planner.calls == []


def test_broken_structured_shape_stops_before_another_model_call(tmp_path, source, monkeypatch):
    planner = local.LocalQuestionPlanner.__new__(local.LocalQuestionPlanner)
    planner.directory, planner.calls, planner.requests = tmp_path, [], 0
    planner.structural_block = None
    def malformed(prompt, schema, directory):
        directory.mkdir()
        return {"raw_output": "{}", "error": None, "version": local.VERSION,
                "model": local.APPROVED_MODEL, "digest": local.APPROVED_DIGEST,
                "provider": "local", "options": local.OPTIONS, "elapsed_seconds": 0,
                "request_sha256": "0"*64, "model_invocation_count": 1, "external_call_count": 0}
    monkeypatch.setattr(local, "generate", malformed)
    plan = planner(source, "Inspect Figure A2.")
    assert not plan["operations"] and len(planner.calls) == 1
    planner.record_result(plan)
    with pytest.raises(RuntimeError, match="SCHEMA_INTEGRATION_BLOCKER"):
        planner(source, "Inspect Figure A2.")
    assert len(planner.calls) == 1 and planner.requests == 1


def test_nonproductive_arbitrary_period_is_resource_stop_not_output_budget():
    assert local._nonproductive("An otherwise productive prefix " + "repeat this sentence of arbitrary length. "*90)
    assert local._nonproductive(" "*1300)
    assert not local._nonproductive("".join(f'{{"id":"item{i}","label":"different {i}"}}' for i in range(100)))
