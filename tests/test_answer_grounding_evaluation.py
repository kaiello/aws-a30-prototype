"""Synthetic system-lane receipts; no application imports, models or services."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "eval" / "answer_grounding_evaluation.py"
SPEC = importlib.util.spec_from_file_location("answer_grounding_evaluation_under_test", MODULE_PATH)
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def settings():
    return {"endpoint": "http://127.0.0.1:8001/api/query",
            "base_url": "http://127.0.0.1:11434/v1", "model_name": "qwen2.5:3b",
            "engine": "custom", "mode": "mix"}


def cases():
    return {"schema_version": 1, "suite_id": "synthetic-system-v1", "cases": [
        {"id": "H01", "query": "A synthetic question", "cohort": "holdout",
         "source_case_id": "synthetic-source-case", "required_facts": ["NEVER_SEND_GOLD"]},
        {"id": "H02", "query": "A second synthetic question", "cohort": "holdout"}]}


def response(outcome="extractive", origin="composed"):
    answer = "A bounded synthetic answer."
    anchor = {"document_id": "doc:synthetic", "source_sha256": "a" * 64,
              "section_id": "section:synthetic", "pdf_index": 2, "printed_label": "iii"}
    return {"query": "A synthetic question", "answer": answer, "answer_outcome": outcome,
            "answer_origin": origin,
            "answer_assessment": {"status": "SUPPORTED_REVIEWED_FACTS", "validated": True,
                                  "answer_sha256": sha(answer), "assessment_scope": "synthetic facts only",
                                  "citation_support": "bound"},
            "grounded_claims": [{"claim_id": "claim:one", "claim": answer, "fact_ids": ["fact:one"],
                                 "source_anchors": [anchor], "source_bindings": [{"excerpt_id": "synthetic"}]}],
            "citations": {"clauses": [], "pages": ["iii"], "figures": [], "tables": [],
                          "source_anchors": [anchor]},
            "timings_ms": {"composition": 0.2}}


def report(phase="before", values=None):
    data = cases()["cases"] if values is None else values
    return {"kind": "answer-grounding-system-capture", "lane": "system", "phase": phase, "transport": "http",
            "settings": settings(), "qrels_fingerprints": {"frozen-qrels": "b" * 64},
            "model_provenance": {"name": evaluation.MODEL, "digest": evaluation.MODEL_DIGEST,
                                 "size": 123, "details": {"format": "gguf"}},
            "evaluator_sha256": "f" * 64, "evaluator_unchanged": True,
            "protected_fingerprints": {"synthetic-store": "c" * 64},
            "code_fingerprints": {"eval/answer_grounding_evaluation.py": "d" * 64},
            "protected_unchanged": True, "code_unchanged": True, "inputs_unchanged": True,
            "cases": deepcopy(data),
            "rows": [{"id": case["id"], "query": case["query"], "case_file_sha256": "e" * 64,
                      "response": response(), "http_status": 200, "attempted": True,
                      "answer_outcome": "extractive", "answer_origin": "composed"} for case in data]}


def test_cases_preserve_extra_private_rubric_without_mutating_or_disclosing_it():
    data = cases()
    before = deepcopy(data)
    assert evaluation.validate_cases(data) == data
    assert data == before
    calls = []
    rows = evaluation.capture_cases(data["cases"], lambda query: calls.append(query) or
                                    {"http_status": 200, "response": response()})
    assert calls == [case["query"] for case in data["cases"]]
    assert "NEVER_SEND_GOLD" not in str(calls)
    assert rows[0]["response"] == response()


@pytest.mark.parametrize("problem", ["duplicate", "empty_query", "bad_id", "empty_cases", "bad_schema"])
def test_cases_reject_malformed_freezes(problem):
    data = cases()
    if problem == "duplicate":
        data["cases"].append(deepcopy(data["cases"][0]))
    elif problem == "empty_query":
        data["cases"][0]["query"] = " "
    elif problem == "bad_id":
        data["cases"][0]["id"] = ["bad"]
    elif problem == "empty_cases":
        data["cases"] = []
    else:
        data["schema_version"] = True
    with pytest.raises(ValueError):
        evaluation.validate_cases(data)


@pytest.mark.parametrize("field,value", [
    ("endpoint", "http://example.com:8001/api/query"),
    ("endpoint", "http://localhost:8001/api/query"),
    ("endpoint", "http://127.0.0.1:8000/api/query"),
    ("endpoint", "http://127.0.0.1:8001/api/query?target=other"),
    ("base_url", "https://api.openai.com/v1"),
    ("base_url", "http://user:password@127.0.0.1:11434/v1"),
    ("engine", "deepseek"), ("model_name", "unapproved-model"), ("mode", "unknown"), ("mode", "hybrid")])
def test_settings_refuse_remote_or_unapproved_provider_substitution(field, value):
    data = settings()
    data[field] = value
    with pytest.raises(ValueError):
        evaluation.validate_settings(data)


def test_server_configuration_must_match_explicit_local_custom_destination():
    configuration = {"custom_configured": True, "custom_base_url": settings()["base_url"],
                     "custom_model": settings()["model_name"], "default_engine": "deepseek"}
    assert evaluation.validate_server_config(configuration, settings()) == configuration
    configuration["custom_base_url"] = "https://example.com/v1"
    with pytest.raises(ValueError):
        evaluation.validate_server_config(configuration, settings())


def test_legacy_response_is_unassessed_and_never_inferred_generated_from_http_success():
    rows = evaluation.capture_cases(cases()["cases"][:1], lambda query: {
        "http_status": 200, "response": {"answer": "An old answer with a citation."}})
    assert rows[0]["answer_origin"] == "legacy_unassessed"
    assert rows[0]["answer_outcome"] == "unassessed"
    summary = evaluation.summarize_rows(rows)
    assert summary["outcomes"]["unassessed"] == 1
    assert summary["model_accuracy"] == "unadjudicated"


def test_composed_and_generated_results_remain_separate_without_truth_scores():
    replies = iter([response(), response("generated", "generated")])
    rows = evaluation.capture_cases(cases()["cases"], lambda query: {"http_status": 200, "response": next(replies)})
    summary = evaluation.summarize_rows(rows)
    assert summary["origins"] == {"composed": 1, "generated": 1}
    assert summary["self_reported_assessments"]["SUPPORTED_REVIEWED_FACTS"] == 2
    assert summary["system_composed_is_model_gain"] is False
    assert summary["model_accuracy"] == "unadjudicated"
    assert rows[0]["reported_claim_bindings"] == response()["grounded_claims"]
    assert rows[0]["reported_canonical_citations"] == response()["citations"]
    assert rows[0]["reported_stage_timings_ms"] == {"composition": 0.2}


def test_http_or_provider_error_stops_further_calls_and_keeps_declared_denominator():
    calls = []
    def invoke(query):
        calls.append(query)
        return {"http_status": 503, "response": {"answer": "", "error_code": "FIXTURE_UNAVAILABLE"}}
    rows = evaluation.capture_cases(cases()["cases"], invoke)
    assert calls == [cases()["cases"][0]["query"]]
    assert rows[0]["answer_outcome"] == "error"
    assert rows[1]["attempted"] is False
    summary = evaluation.summarize_rows(rows)
    assert summary["declared_cases"] == 2
    assert summary["attempted_cases"] == 1
    assert summary["errors"] == 1
    assert summary["not_run"] == 1


def test_reported_assessment_must_bind_the_actual_answer_bytes():
    changed = response()
    changed["answer"] = "A changed answer."
    rows = evaluation.capture_cases(cases()["cases"][:1], lambda query: {"http_status": 200, "response": changed})
    assert rows[0]["assessment_answer_binding_valid"] is False
    assert rows[0]["response"] == changed
    assert evaluation.summarize_rows(rows)["assessment_binding_failures"] == 1


def test_compare_only_actual_identical_common_cases_and_label_unpaired_system_after_cases():
    before = report()
    new_cases = cases()["cases"] + [{"id": "P01", "query": "Original synthetic case", "cohort": "original"}]
    after = report("after", new_cases)
    result = evaluation.compare_reports(before, after)
    assert result["paired_case_ids"] == ["H01", "H02"]
    assert result["system_after_only_case_ids"] == ["P01"]
    assert result["model_only_accuracy_gain"] is False
    assert result["factual_accuracy"] == "unadjudicated"


@pytest.mark.parametrize("problem", ["wrong_lane", "phase", "missing_case", "duplicate_case", "query",
                                    "case_file", "qrels", "store_drift", "code_drift", "input_drift", "protected_files"])
def test_compare_refuses_mismatched_or_drifting_receipts(problem):
    before, after = report(), report("after")
    if problem == "wrong_lane":
        after["lane"] = "component"
    elif problem == "phase":
        after["phase"] = "before"
    elif problem == "missing_case":
        after["rows"].pop()
    elif problem == "duplicate_case":
        after["rows"][1] = deepcopy(after["rows"][0])
    elif problem == "query":
        after["rows"][0]["query"] = "Different actual query"
    elif problem == "case_file":
        after["rows"][0]["case_file_sha256"] = "f" * 64
    elif problem == "qrels":
        after["qrels_fingerprints"]["frozen-qrels"] = "f" * 64
    elif problem == "store_drift":
        after["protected_unchanged"] = False
    elif problem == "code_drift":
        after["code_unchanged"] = False
    elif problem == "input_drift":
        after["inputs_unchanged"] = False
    else:
        after["protected_fingerprints"]["synthetic-store"] = "f" * 64
    with pytest.raises(ValueError):
        evaluation.compare_reports(before, after)


def test_intended_runtime_code_changes_are_recorded_without_requiring_equal_phase_code_hashes():
    before, after = report(), report("after")
    before["code_fingerprints"]["src/query.py"] = "1" * 64
    after["code_fingerprints"]["src/query.py"] = "2" * 64
    assert evaluation.compare_reports(before, after)["paired_case_ids"] == ["H01", "H02"]


@pytest.mark.parametrize("problem", ["missing_transport", "invalid_transport", "transport_pair",
                                    "missing_evaluator_hash", "invalid_evaluator_hash", "evaluator_pair",
                                    "missing_evaluator_unchanged", "false_evaluator_unchanged",
                                    "missing_model_both", "invalid_model_name", "wrong_model_digest", "model_format"])
def test_comparison_requires_same_capture_executor_transport_and_approved_model_provenance(problem):
    before, after = report(), report("after")
    if problem == "missing_transport":
        del after["transport"]
    elif problem == "invalid_transport":
        after["transport"] = "component"
    elif problem == "transport_pair":
        after["transport"] = "inprocess"
    elif problem == "missing_evaluator_hash":
        del after["evaluator_sha256"]
    elif problem == "invalid_evaluator_hash":
        after["evaluator_sha256"] = "invalid"
    elif problem == "evaluator_pair":
        after["evaluator_sha256"] = "1" * 64
    elif problem == "missing_evaluator_unchanged":
        del after["evaluator_unchanged"]
    elif problem == "false_evaluator_unchanged":
        after["evaluator_unchanged"] = False
    elif problem == "missing_model_both":
        del before["model_provenance"]
        del after["model_provenance"]
    elif problem == "invalid_model_name":
        before["model_provenance"]["name"] = after["model_provenance"]["name"] = "unapproved"
    elif problem == "wrong_model_digest":
        before["model_provenance"]["digest"] = after["model_provenance"]["digest"] = "2" * 64
    else:
        before["model_provenance"]["details"]["format"] = after["model_provenance"]["details"]["format"] = "remote"
    with pytest.raises(ValueError):
        evaluation.compare_reports(before, after)


def test_capture_outputs_are_new_external_directories(tmp_path):
    existing = tmp_path / "exists"
    existing.mkdir()
    with pytest.raises(ValueError, match="fresh"):
        evaluation.prepare_output(existing)
    with pytest.raises(ValueError, match="outside"):
        evaluation.prepare_output(evaluation.ROOT / "forbidden")


def test_evaluator_fingerprint_binds_loaded_staged_source_separately_from_repo_root(monkeypatch, tmp_path):
    staged_source = tmp_path / "staged-evaluator.py"
    staged_source.write_text("synthetic evaluator source", encoding="utf-8")
    monkeypatch.setattr(evaluation, "__file__", str(staged_source))
    monkeypatch.setattr(evaluation, "ROOT", tmp_path / "actual-repository")
    assert evaluation.evaluator_fingerprint() == sha("synthetic evaluator source")
