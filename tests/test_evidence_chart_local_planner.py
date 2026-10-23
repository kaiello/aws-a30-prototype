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


def test_runtime_loads_question_actions_and_lowers_mocked_response(tmp_path, source, monkeypatch):
    """Transport integration only; no live model or answer-quality claim."""
    from src.evidence_chart_contract import QUESTION_INTERFACE
    from src.evidence_chart_llm_plan import identity_catalog
    captured = {}
    query = "Give the printed name and acronym of the selected entry."
    alias = next(row[0] for row in identity_catalog(source) if row[1] == "process")
    payload = {"schema_version": QUESTION_INTERFACE["schema_version"],
        "source_element": source["source_binding"]["locator"]["element_id"], "query": query,
        "parts": [{"id": "p1", "quote": query, "status": "planned", "action_ids": ["a1"],
            "reason": "Explain which typed lookup this request needs."}],
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence",
            "subjects": [alias], "targets": [], "subjects_from": [], "targets_from": [],
            "fields": ["name", "acronym"], "mode": "", "information_fields": [], "scope": "selected"}]}
    planner = local.LocalQuestionPlanner.__new__(local.LocalQuestionPlanner)
    planner.directory, planner.calls, planner.requests = tmp_path, [], 0
    planner.metadata, planner.structural_block = {}, None
    def mocked(prompt, schema, directory):
        directory.mkdir()
        captured.update(prompt=prompt, schema=schema)
        return {"raw_output": json.dumps(payload), "error": None, "version": local.VERSION,
            "model": "MOCK_NOT_INFERENCE", "digest": None, "provider": "mock",
            "options": local.OPTIONS, "elapsed_seconds": 0, "request_sha256": "0"*64,
            "model_invocation_count": 0, "external_call_count": 0}
    monkeypatch.setattr(planner, "_generate", mocked)
    result = planner(source, query)
    assert "chart-question-actions-instructions-1.1" in captured["prompt"]
    assert "actions" in captured["schema"]["properties"]
    assert "operations" not in captured["schema"]["properties"]
    assert result["external_plan"] == payload
    assert result["lowered_plan"]["parts"][0]["reason"] == ""
    assert result["model_part_metadata"][0]["original_reason"] == payload["parts"][0]["reason"]
    assert result["operations"][0]["kind"] == "designation"
    assert result["model_planning"]["model_invocation_count"] == 0
    assert json.loads((tmp_path / "request_001/validated_plan.json").read_text())["external_plan"] == payload
