"""Pure synthetic evaluation contracts: no models, services or real stores."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "eval" / "terminology_live_evaluation.py"
SPEC = importlib.util.spec_from_file_location("terminology_evaluation_under_test", MODULE_PATH)
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def descriptor(identifier="chunk-a", excerpt="Reviewed synthetic alpha."):
    content = "Synthetic heading\n" + excerpt + "\nOther existing chunk text."
    return {"id": identifier, "full_doc_id": "source:" + identifier, "content": excerpt,
            "excerpt_sha256": sha(excerpt), "content_sha256": sha(content),
            "verification_state": "verified", "source_anchors": [{
                "document_id": "doc:synthetic", "source_sha256": "a" * 64,
                "section_id": "clause:synthetic", "pdf_index": 25, "printed_label": "13"}]}


def hit(identifier="chunk-a", excerpt="Reviewed synthetic alpha.", score=0.5):
    return {"id": identifier, "full_doc_id": "source:" + identifier,
            "content": "Synthetic heading\n" + excerpt + "\nOther existing chunk text.",
            "score": score, "rrf_score": 0.02, "cross_encoder_score": score}


def member(value=None):
    return deepcopy(value or descriptor("chunk-b", "Reviewed synthetic beta."))


def qrels():
    positive = {"id": "P01", "query": "A synthetic two-target question", "stratum": "positive",
                "expected_policy": "answer", "expected_activation": True,
                "grade_answers": True,
                "expected_targets": ["onto:alpha", "onto:beta"],
                "required_groups": [{"id": "alpha", "chunk_ids": ["chunk-a"]},
                                    {"id": "beta", "chunk_ids": ["chunk-b"]}],
                "required_claims": [{"id": "claim:one", "statement": "GOLD_ONLY_SENTINEL", "source_ref": "local-review"}]}
    return {"schema_version": 1, "suite_id": "synthetic-v1", "answer_top_k": 5,
            "evidence": [descriptor(), descriptor("chunk-b", "Reviewed synthetic beta.")],
            "cases": [positive] + [{"id": f"U{index:02}", "query": f"Unrelated query {index}",
                                     "stratum": "unrelated", "expected_policy": "unchanged",
                                     "grade_answers": False, "required_groups": []} for index in range(1, 11)]}


def capture_report(label="before"):
    data = qrels()
    return {"kind": "terminology-live-capture", "label": label,
            "qrels_sha256": "a" * 64, "qrels": data,
            "qrels_snapshot_sha256": sha(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                                     separators=(",", ":"), allow_nan=False)),
            "rows": [{"id": case["id"], "query": case["query"], "hits": [hit()], "gate": None}
                     for case in data["cases"]],
            "stores_unchanged": True, "code_unchanged": True,
            "code_fingerprints": {"eval/terminology_live_evaluation.py": "e" * 64},
            "corpus_fingerprints": {"synthetic-store": "b" * 64},
            "prompt_spec_sha256": "c" * 64,
            "model_settings": {"embedding_model": "synthetic", "reranker": "synthetic"},
            "package_versions": {"synthetic": "1"}}


def test_qrels_validation_preserves_input_and_requires_ten_unrelated_controls():
    data = qrels()
    before = deepcopy(data)
    assert evaluation.validate_qrels(data) == data
    assert data == before
    data["cases"].pop()
    with pytest.raises(ValueError, match="unrelated"):
        evaluation.validate_qrels(data)


@pytest.mark.parametrize("problem", ["duplicate_id", "unknown_chunk", "bad_excerpt_hash", "invalid_anchor", "bad_expected_activation"])
def test_qrels_reject_invalid_or_unreviewed_bindings(problem):
    data = qrels()
    if problem == "duplicate_id":
        data["cases"][1]["id"] = "P01"
    elif problem == "unknown_chunk":
        data["cases"][0]["required_groups"][0]["chunk_ids"] = ["not-reviewed"]
    elif problem == "bad_excerpt_hash":
        data["evidence"][0]["excerpt_sha256"] = "b" * 64
    elif problem == "invalid_anchor":
        data["evidence"][0]["source_anchors"][0]["pdf_index"] = True
    else:
        data["cases"][0]["expected_activation"] = "true"
    with pytest.raises(ValueError):
        evaluation.validate_qrels(data)


def test_base_hit_requires_exact_id_whole_content_hash_and_literal_excerpt():
    descriptors = qrels()["evidence"]
    assert evaluation.evidence_ids(hit(), descriptors) == ["chunk-a"]
    altered = hit()
    altered["content"] += " changed"
    assert evaluation.evidence_ids(altered, descriptors) == []
    assert evaluation.evidence_ids({"id": "chunk-a"}, descriptors) == []


def test_bundle_members_are_validated_against_independent_reviewed_excerpts():
    bundled = hit()
    bundled["bundle"] = {"supporting_evidence": [member()]}
    assert evaluation.evidence_ids(bundled, qrels()["evidence"]) == ["chunk-a", "chunk-b"]
    assert evaluation.evidence_ids(bundled, qrels()["evidence"], include_bundle=False) == ["chunk-a"]


@pytest.mark.parametrize("problem", ["id_only", "empty", "unverified", "hash", "whole_hash", "anchor", "wrong_excerpt", "prefix", "suffix"])
def test_invalid_member_ids_never_count_as_evidence(problem):
    candidate = member()
    if problem == "id_only":
        candidate = {"id": "chunk-b"}
    elif problem == "empty":
        candidate["content"] = ""
    elif problem == "unverified":
        candidate["verification_state"] = "candidate"
    elif problem == "hash":
        candidate["excerpt_sha256"] = "f" * 64
    elif problem == "whole_hash":
        candidate["content_sha256"] = "f" * 64
    elif problem == "anchor":
        candidate["source_anchors"][0]["printed_label"] = "999"
    elif problem == "wrong_excerpt":
        candidate["content"] = "Different unreviewed excerpt."
        candidate["excerpt_sha256"] = sha(candidate["content"])
    else:
        candidate["content"] = ("Unsupported prefix. " + candidate["content"] if problem == "prefix"
                                else candidate["content"] + " Unsupported suffix.")
        candidate["excerpt_sha256"] = sha(candidate["content"])
    bundled = {"id": "distractor", "content": "Not relevant.", "bundle": {"supporting_evidence": [candidate]}}
    assert evaluation.evidence_ids(bundled, qrels()["evidence"]) == []


def test_registry_input_field_does_not_substitute_for_runtime_supporting_evidence():
    candidate = {"id": "distractor", "content": "Not relevant.", "bundle": {"evidence_members": [member()]}}
    assert evaluation.evidence_ids(candidate, qrels()["evidence"]) == []


def test_standalone_runtime_bundle_requires_marker_and_exact_reviewed_members():
    candidate = {"id": "terminology:synthetic", "supporting_evidence": [member()]}
    assert evaluation.evidence_ids(candidate, qrels()["evidence"]) == []
    candidate["evidence_type"] = "terminology_mapping"
    assert evaluation.evidence_ids(candidate, qrels()["evidence"]) == ["chunk-b"]
    prompt = evaluation.render_prompt("Synthetic query", [candidate], qrels()["evidence"])
    assert "Reviewed synthetic beta." in prompt


def test_answer_context_does_not_filter_actual_members_using_qrel_relevance():
    actual = member()
    actual["content"] = "Runtime-verified synthetic evidence absent from qrels."
    actual["excerpt_sha256"] = sha(actual["content"])
    candidate = {"id": "terminology:synthetic", "evidence_type": "terminology_mapping",
                 "supporting_evidence": [actual]}
    assert evaluation.evidence_ids(candidate, qrels()["evidence"]) == []
    assert actual["content"] in evaluation.render_prompt("Synthetic query", [candidate], qrels()["evidence"])


def test_primary_metrics_do_not_credit_correct_id_with_changed_content():
    data = qrels()
    changed = hit()
    changed["content"] += " altered"
    scored = evaluation.score_retrieval(data["cases"], [{"id": "P01", "hits": [changed]}], data["evidence"])
    assert scored["at_1"]["primary_chunk_hits"] == 0


def test_activation_and_target_checks_count_wrong_unreviewed_activation():
    cases = [{"id": "B", "expected_activation": False, "expected_targets": [],
              "forbidden_target_ids": ["onto:wrong"], "expected_policy": "no_supported_mapping"}]
    rows = [{"id": "B", "hits": [{"evidence_type": "terminology_mapping",
                                    "terminology_resolution": {"target_ids": ["onto:wrong"]}}]}]
    scored = evaluation.score_policies(cases, rows)
    assert scored["activation_checks"] == 1
    assert scored["activation_passes"] == 0
    assert scored["target_checks"] == 1
    assert scored["target_passes"] == 0
    assert scored["forbidden_target_violations"] == 1


def test_parity_does_not_pass_two_failed_empty_captures():
    report = capture_report()
    for row in report["rows"]:
        row.update(hits=[], error={"type": "RuntimeError"})
    after = deepcopy(report)
    after["label"] = "after"
    result = evaluation.compare_captures(report, after)
    assert result["unrelated_exact_rank_score_parity"] is False
    assert result["captures_error_free"] is False


def test_and_of_or_groups_distinguish_primary_rank_and_bundle_unit():
    data = qrels()
    candidate = hit()
    candidate["bundle"] = {"supporting_evidence": [member()]}
    scored = evaluation.score_retrieval(data["cases"], [{"id": "P01", "hits": [candidate]}],
                                        data["evidence"])
    assert scored["graded_cases"] == 1
    assert scored["at_1"]["primary_chunk_hits"] == 1
    assert scored["at_1"]["bundle_hits"] == 1
    assert scored["at_1"]["complete_bundle_evidence"] == 1
    assert scored["at_1"]["recovered_groups"] == 2
    assert scored["at_1"]["required_groups"] == 2
    assert scored["metric_unit"] == "ranked base chunks; bundle-at-K includes validated supporting excerpts"


def test_same_chunk_wrong_sense_excerpt_does_not_satisfy_required_hash():
    alpha = "Reviewed synthetic standard sense."
    beta = "Reviewed synthetic conditional sense."
    whole = alpha + "\n" + beta
    first, second = descriptor("shared-page", alpha), descriptor("shared-page", beta)
    first["content_sha256"] = second["content_sha256"] = sha(whole)
    group = {"id": "conditional", "chunk_ids": ["shared-page"],
             "required_excerpt_sha256s": [sha(beta)]}
    cases = [{"id": "sense", "stratum": "positive", "required_groups": [group]}]
    wrong = {"id": "distractor", "bundle": {"supporting_evidence": [member(first)]}}
    scores = evaluation.score_retrieval(cases, [{"id": "sense", "hits": [wrong]}], [first, second])
    assert scores["at_1"]["bundle_hits"] == 0
    assert scores["at_1"]["complete_bundle_evidence"] == 0
    base = {"id": "shared-page", "content": whole}
    scores = evaluation.score_retrieval(cases, [{"id": "sense", "hits": [base]}], [first, second])
    assert scores["at_1"]["complete_bundle_evidence"] == 1


def test_missing_evidence_and_gate_failures_remain_in_the_positive_denominator():
    data = qrels()
    scored = evaluation.score_retrieval(data["cases"], [{"id": "P01", "hits": [], "gate": {"status": "TRUTHFUL_ABSTENTION"}}],
                                        data["evidence"])
    assert scored["graded_cases"] == 1
    assert scored["at_10"]["complete_bundle_evidence"] == 0
    assert scored["at_10"]["required_groups"] == 2


def test_negative_cases_do_not_receive_vacuous_completeness():
    cases = [{"id": "N01", "query": "Out of scope synthetic query", "stratum": "negative",
              "expected_policy": "abstain", "required_groups": []}]
    scored = evaluation.score_retrieval(cases, [{"id": "N01", "hits": [], "gate": {"status": "TRUTHFUL_ABSTENTION"}}], [])
    assert scored["graded_cases"] == 0
    assert scored["at_10"]["complete_bundle_evidence"] == 0
    assert scored["at_10"]["complete_rate"] is None


def test_capture_calls_real_boundaries_once_per_ungated_case_without_query_changes():
    calls = []
    cases = [{"id": "P", "query": "Keep this exact question"}, {"id": "N", "query": "Skip this query"}]
    def retrieve(query, top_k):
        calls.append((query, top_k))
        return [hit()]
    rows = evaluation.capture_cases(cases, retrieve, lambda query: {"status": "TRUTHFUL_ABSTENTION"} if query.startswith("Skip") else None)
    assert calls == [("Keep this exact question", 10)]
    assert rows[1]["hits"] == []
    assert rows[1]["gate"]["status"] == "TRUTHFUL_ABSTENTION"


def test_frozen_prompt_uses_captured_evidence_without_gold_claim_or_policy_leakage():
    data = qrels()
    prompt = evaluation.render_prompt(data["cases"][0]["query"], [hit()], data["evidence"], top_k=5)
    assert "Reviewed synthetic alpha." in prompt
    assert "GOLD_ONLY_SENTINEL" not in prompt
    assert "expected_policy" not in prompt
    assert evaluation.render_prompt(data["cases"][0]["query"], [hit()], data["evidence"], top_k=5) == prompt


def test_answer_plan_separates_gate_answers_and_only_predeclared_model_cases():
    cases = [
        {"id": "P", "stratum": "positive", "grade_answers": True},
        {"id": "A", "stratum": "ambiguous", "grade_answers": True},
        {"id": "B", "stratum": "negative", "grade_answers": False, "expected_policy": "no_supported_mapping"},
        {"id": "N", "stratum": "negative", "grade_answers": False},
        {"id": "U", "stratum": "unrelated", "grade_answers": False},
    ]
    rows = [{"id": case["id"], "gate": {"answer": "Deterministic scope answer"} if case["id"] == "N" else None}
            for case in cases]
    jobs = evaluation.plan_answer_jobs(cases, rows)
    assert [(job["id"], job["kind"]) for job in jobs] == [("P", "model"), ("A", "model"), ("N", "gate")]


def test_comparison_checks_unrelated_exact_rank_and_score_parity_separately_from_bundles():
    before = capture_report()
    after = deepcopy(before)
    after["label"] = "after"
    after["rows"][1]["hits"][0]["bundle"] = {"supporting_evidence": [member()]}
    result = evaluation.compare_captures(before, after)
    assert result["unrelated_exact_rank_score_parity"] is True
    after["rows"][1]["hits"][0]["cross_encoder_score"] = 0.500001
    assert evaluation.compare_captures(before, after)["unrelated_exact_rank_score_parity"] is False
    after["qrels_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="qrels"):
        evaluation.compare_captures(before, after)


@pytest.mark.parametrize("problem", ["kind", "before_label", "after_label", "missing_stores",
                                    "false_stores", "missing_code", "false_code", "qrels_mismatch",
                                    "missing_case", "duplicate_case", "unknown_case", "wrong_query"])
def test_comparison_rejects_incomplete_or_incompatible_capture_receipts(problem):
    before, after = capture_report(), capture_report("after")
    if problem == "kind":
        after["kind"] = "answers"
    elif problem == "before_label":
        before["label"] = "after"
    elif problem == "after_label":
        after["label"] = "before"
    elif problem == "missing_stores":
        del after["stores_unchanged"]
    elif problem == "false_stores":
        after["stores_unchanged"] = False
    elif problem == "missing_code":
        del after["code_unchanged"]
    elif problem == "false_code":
        after["code_unchanged"] = False
    elif problem == "qrels_mismatch":
        after["qrels"]["cases"][0]["query"] = "A changed frozen question"
    elif problem == "missing_case":
        after["rows"].pop(0)
    elif problem == "duplicate_case":
        after["rows"].append(deepcopy(after["rows"][0]))
    elif problem == "unknown_case":
        after["rows"].append({"id": "UNKNOWN", "query": "Unknown", "hits": []})
    else:
        after["rows"][0]["query"] = "The wrong actual query"
    with pytest.raises(ValueError):
        evaluation.compare_captures(before, after)


def test_comparison_rejects_different_qrels_even_with_recomputed_snapshot():
    before, after = capture_report(), capture_report("after")
    after["qrels"]["cases"][0]["query"] = "A changed frozen question"
    after["rows"][0]["query"] = "A changed frozen question"
    after["qrels_snapshot_sha256"] = sha(json.dumps(after["qrels"], ensure_ascii=False, sort_keys=True,
                                                     separators=(",", ":"), allow_nan=False))
    with pytest.raises(ValueError, match="qrels"):
        evaluation.compare_captures(before, after)


def test_comparison_requires_same_recorded_evaluator_source_fingerprint():
    before, after = capture_report(), capture_report("after")
    after["code_fingerprints"]["eval/terminology_live_evaluation.py"] = "f" * 64
    with pytest.raises(ValueError, match="evaluator"):
        evaluation.compare_captures(before, after)


def test_answers_reject_incomplete_capture_before_creating_output_or_runtime(monkeypatch, tmp_path):
    report = capture_report()
    report["prompt_spec_sha256"] = sha(json.dumps({"prompt": evaluation.PROMPT,
        "options": evaluation.OPTIONS, "top_k": report["qrels"]["answer_top_k"]},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    report["rows"].pop(0)
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    def forbidden(*args, **kwargs):
        pytest.fail("Incomplete capture reached output or runtime")
    monkeypatch.setattr(evaluation, "prepare_output", forbidden)
    monkeypatch.setattr(evaluation, "runtime_guard", forbidden)
    with pytest.raises(ValueError, match="capture"):
        evaluation.generate_answers(path, tmp_path / "fresh-output")


@pytest.mark.parametrize("gate", [{}, {"status": "ANSWER"}, {"status": "TRUTHFUL_ABSTENTION"}])
def test_abstention_policy_requires_explicit_actual_gate_status(gate):
    cases = [{"id": "N", "expected_policy": "abstain"}]
    scored = evaluation.score_policies(cases, [{"id": "N", "hits": [], "gate": gate}])
    assert scored["abstention_passes"] == int(gate.get("status") == "TRUTHFUL_ABSTENTION")


def test_evidence_or_group_accepts_either_reviewed_chunk_and_requires_every_and_group():
    data = qrels()
    cases = [{"id": "OR", "stratum": "positive", "required_groups": [
        {"id": "alternative", "chunk_ids": ["chunk-a", "chunk-b"]},
        {"id": "also-required", "chunk_ids": ["chunk-a"]}]}]
    scored = evaluation.score_retrieval(cases, [{"id": "OR", "hits": [hit("chunk-b", "Reviewed synthetic beta.")]}],
                                        data["evidence"])
    assert scored["at_1"]["recovered_groups"] == 1
    assert scored["at_1"]["complete_bundle_evidence"] == 0
    scored = evaluation.score_retrieval(cases, [{"id": "OR", "hits": [hit()]}], data["evidence"])
    assert scored["at_1"]["complete_bundle_evidence"] == 1


@pytest.mark.parametrize("address,allowed", [(("127.0.0.1", 11434), True), (("::1", 11434), True),
                                            (("8.8.8.8", 443), False), (("api.example.com", 443), False)])
def test_network_boundary_accepts_only_literal_loopback(address, allowed):
    assert evaluation.is_loopback_address(address) is allowed


def test_outputs_must_be_fresh_and_outside_the_repository(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="fresh"):
        evaluation.prepare_output(existing)
    with pytest.raises(ValueError, match="outside"):
        evaluation.prepare_output(evaluation.ROOT / "forbidden-output")
