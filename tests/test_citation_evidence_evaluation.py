"""Synthetic evaluation contracts; no runtime, provider, or source-text imports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "eval/citation_evidence_evaluation.py"
spec = importlib.util.spec_from_file_location("citation_evidence_evaluation", MODULE)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)

H = "a" * 64
OTHER = "b" * 64


def evidence(element="figure:synthetic_a", asset_hash=H, orders=(0,)):
    return {"element_id": element, "label": "Synthetic A", "relationship": "direct",
            "source_anchors": [{"source_id": "doc:synthetic", "source_sha256": H,
                                "element_id": element, "pdf_index": 4,
                                "pdf_page_ordinal": 5, "printed_label": "1"}],
            "asset_status": "complete",
            "assets": [{"sha256": asset_hash, "source_anchor_orders": list(orders),
                        "kind": "image", "verification_state": "verified"}]}


def link(claim_id="c1", element="figure:synthetic_a"):
    return {"claim_id": claim_id,
            "mentions": [{"raw": "Figure A", "start": 5, "end": 13, "order": 0,
                          "span_space": "half_open_unicode_characters",
                          "kind": "figure", "requested_label": "Figure A",
                          "resolution": {"status": "exact", "labels": ["Synthetic A"],
                                         "target_ids": [element]},
                          "qualifiers": {"panel": None, "page": None}}],
            "reference_status": "exact", "binding_status": "matched",
            "asset_status": "complete", "support_status": "UNASSESSED",
            "ordered_evidence": [evidence(element)], "diagnostics": []}


def case(identifier="D01"):
    return {"id": identifier, "pair_id": "P1",
            "runtime_input": {"claims": [{"claim_id": "c1", "claim": "Synthetic claim Figure A"}],
                              "evidence_context": []},
            "expected": {"links": [link()], "required_groups": [["c1"]]}}


def suite(*cases):
    return {"schema_version": 1, "suite_id": "synthetic-contract", "cohort": "DEVELOPMENT",
            "cases": list(cases or (case(),))}


def response(c=None):
    return {"links": copy.deepcopy((c or case())["expected"]["links"]),
            "assessment": {"status": "UNASSESSED", "complete": False},
            "timings_ms": {"total": 1.0}}


def test_exact_declarative_states_pass_without_asserting_truth():
    result = evaluation.check_case(case(), response())
    assert result["passed"] is True
    assert all(result["checks"].values())
    assert result["claim_truth"] == "not_automatically_adjudicated"


@pytest.mark.parametrize('mutation',['valid','unknown','wrong_role','wrong_hash','support_promotion'])
def test_explicit_navigation_allowance_is_exact_optional_and_never_support(mutation):
    c=case();candidate=evidence('figure:optional',OTHER)
    candidate['relationship']='navigation_candidate'
    c['expected']['links'][0]['allowed_navigation']=[candidate]
    observed=response(c);observed['links'][0]['ordered_evidence'].append(copy.deepcopy(candidate))
    if mutation=='unknown':observed['links'][0]['ordered_evidence'][-1]['element_id']='figure:unknown'
    elif mutation=='wrong_role':observed['links'][0]['ordered_evidence'][-1]['relationship']='direct'
    elif mutation=='wrong_hash':observed['links'][0]['ordered_evidence'][-1]['assets'][0]['sha256']=H
    elif mutation=='support_promotion':observed['links'][0]['support_status']='SUPPORTED_REVIEWED_FACTS'
    assert evaluation.check_case(c,observed)['passed'] is (mutation=='valid')
    assert evaluation.check_case(c,response(c))['passed'] is True


@pytest.mark.parametrize("field,value", [
    ("reference_status", "group"), ("binding_status", "mismatched"),
    ("asset_status", "missing"), ("support_status", "SUPPORTED_REVIEWED_FACTS"),
])
def test_four_states_are_independent_and_not_promoted_by_image_existence(field, value):
    observed = response()
    observed["links"][0][field] = value
    result = evaluation.check_case(case(), observed)
    assert result["passed"] is False
    key = {"reference_status": "reference", "binding_status": "binding",
           "asset_status": "assets", "support_status": "support"}[field]
    assert result["checks"][key] is False


@pytest.mark.parametrize("mutation", ["wrong_element", "wrong_document", "wrong_digest", "wrong_page", "wrong_mention", "lost_panel"])
def test_exact_identity_includes_full_mention_and_source_anchor_binding(mutation):
    observed = response()
    item = observed["links"][0]
    if mutation == "wrong_element":
        item["ordered_evidence"][0]["element_id"] = "figure:other_valid"
    elif mutation == "wrong_document":
        item["ordered_evidence"][0]["source_anchors"][0]["source_id"] = "doc:other_valid"
    elif mutation == "wrong_digest":
        item["ordered_evidence"][0]["source_anchors"][0]["source_sha256"] = OTHER
    elif mutation == "wrong_page":
        item["ordered_evidence"][0]["source_anchors"][0]["pdf_index"] = 5
    elif mutation == "wrong_mention":
        item["mentions"][0]["end"] -= 1
    else:
        item["mentions"][0]["qualifiers"]["panel"] = "(Z)"
    assert evaluation.check_case(case(), observed)["checks"]["reference"] is False


def test_explicit_frozen_page_candidates_are_compared_without_page_overlap_inference():
    c = case()
    c["expected"]["links"][0]["mentions"][0]["page_candidates"] = [
        {"pdf_index": 4, "pdf_page_ordinal": 5, "printed_label": "1"}]
    observed = response(c)
    observed["links"][0]["mentions"][0]["page_candidates"][0]["pdf_index"] = 6
    assert evaluation.check_case(c, observed)["checks"]["reference"] is False


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reversed", "wrong_hash", "wrong_anchor_order", "navigation"])
def test_required_assets_are_ordered_hash_and_anchor_tuples(mutation):
    c = case()
    c["expected"]["links"][0]["ordered_evidence"][0]["assets"].append(
        {"sha256": OTHER, "source_anchor_orders": [1, 2], "kind": "image", "verification_state": "verified"})
    observed = response(c)
    item = observed["links"][0]["ordered_evidence"][0]
    if mutation == "missing":
        item["assets"].pop()
    elif mutation == "duplicate":
        item["assets"].append(copy.deepcopy(item["assets"][0]))
    elif mutation == "reversed":
        item["assets"].reverse()
    elif mutation == "wrong_hash":
        item["assets"][0]["sha256"] = OTHER
    elif mutation == "wrong_anchor_order":
        item["assets"][1]["source_anchor_orders"] = [2, 1]
    else:
        item["relationship"] = "navigation_candidate"
    assert evaluation.check_case(c, observed)["checks"]["assets"] is False


def test_shared_file_does_not_collapse_distinct_claims_or_elements():
    c = case()
    c["expected"]["links"].append(link("c2", "table:synthetic_b"))
    c["expected"]["required_groups"] = [["c1"], ["c2"]]
    observed = response(c)
    observed["links"].pop()
    result = evaluation.check_case(c, observed)
    assert result["passed"] is False
    assert result["required_groups"] == {"matched": 1, "declared": 2, "complete": False}


def test_missing_asset_retains_frozen_required_ledger_separate_from_rendered_subset():
    c = case()
    target = c["expected"]["links"][0]
    target["asset_status"] = "missing"
    target["ordered_evidence"][0]["asset_status"] = "missing"
    target["ordered_evidence"][0]["assets"].append(
        {"sha256": OTHER, "source_anchor_orders": [1], "kind": "image", "verification_state": "verified"})
    target["ordered_evidence"][0]["rendered_assets"] = copy.deepcopy(target["ordered_evidence"][0]["assets"][:1])
    observed = response(c)
    item = observed["links"][0]["ordered_evidence"][0]
    item["declared_assets"] = list(reversed(copy.deepcopy(item["assets"])))
    item["assets"].pop()
    assert evaluation.check_case(c, observed)["checks"]["assets"] is True
    item["declared_assets"].pop()
    assert evaluation.check_case(c, observed)["checks"]["assets"] is False


def test_required_evidence_groups_are_and_of_or_without_vacuous_negative_credit():
    c = case()
    c["expected"]["links"].extend([link("c2"), link("c3")])
    c["expected"]["required_groups"] = [["c1", "c2"], ["c3"]]
    observed = response(c)
    observed["links"][0]["binding_status"] = "mismatched"
    assert evaluation.check_case(c, observed)["required_groups"] == {"matched": 2, "declared": 2, "complete": True}
    c["expected"]["required_groups"] = []
    assert evaluation.check_case(c, response(c))["required_groups"] == {"matched": 0, "declared": 0, "complete": None}


@pytest.mark.parametrize("mutation", ["duplicate_case", "unknown_group", "empty_group", "duplicate_claim", "bad_hash", "invalid_order"])
def test_malformed_frozen_labels_fail_before_invocation(mutation):
    data = suite()
    if mutation == "duplicate_case":
        data["cases"].append(copy.deepcopy(data["cases"][0]))
    elif mutation == "unknown_group":
        data["cases"][0]["expected"]["required_groups"] = [["absent"]]
    elif mutation == "empty_group":
        data["cases"][0]["expected"]["required_groups"] = [[]]
    elif mutation == "duplicate_claim":
        data["cases"][0]["expected"]["links"].append(link())
    elif mutation == "bad_hash":
        data["cases"][0]["expected"]["links"][0]["ordered_evidence"][0]["assets"][0]["sha256"] = "bad"
    else:
        data["cases"][0]["expected"]["links"][0]["ordered_evidence"][0]["assets"][0]["source_anchor_orders"] = [True]
    with pytest.raises(ValueError):
        evaluation.validate_cases(data)


def test_expected_labels_never_enter_adapter_and_callback_mutation_cannot_change_freeze():
    data = suite()
    seen = []
    def invoke(payload):
        seen.append(copy.deepcopy(payload))
        payload["claims"][0]["claim"] = "mutated"
        return response()
    report = evaluation.evaluate_cases(data, invoke)
    assert seen == [data["cases"][0]["runtime_input"]]
    assert "expected" not in seen[0]
    assert data["cases"][0]["runtime_input"]["claims"][0]["claim"] == "Synthetic claim Figure A"
    assert report["summary"]["declared_cases"] == 1
    assert report["summary"]["passed_cases"] == 1


def test_errors_omissions_unknown_and_duplicate_rows_cannot_shrink_denominator():
    data = suite(case("D01"), case("D02"), case("D03"))
    calls = []
    def invoke(payload):
        calls.append(payload)
        if len(calls) == 2:
            raise RuntimeError("private detail must not escape")
        return response()
    report = evaluation.evaluate_cases(data, invoke)
    assert report["summary"]["declared_cases"] == 3
    assert report["summary"]["passed_cases"] == 2
    assert report["summary"]["errors"] == 1
    assert "private detail" not in json.dumps(report)
    for rows in (report["rows"][:-1], report["rows"] + [report["rows"][0]],
                 report["rows"] + [{"id": "UNKNOWN"}]):
        with pytest.raises(ValueError):
            evaluation.validate_report({**report, "rows": rows})


def test_explicit_empty_or_malformed_output_is_a_failed_declared_case():
    for observed in (None, {}, {"links": []}, {"links": "bad"}):
        report = evaluation.evaluate_cases(suite(), lambda _: observed)
        assert report["summary"]["declared_cases"] == 1
        assert report["summary"]["passed_cases"] == 0


def test_benchmark_has_five_fresh_factory_cold_and_thirty_warm_calls_per_case():
    factories = []
    def factory():
        calls = []
        factories.append(calls)
        def invoke(payload):
            calls.append(copy.deepcopy(payload))
            return response()
        return invoke
    report = evaluation.benchmark_cases(suite(), factory)
    assert sorted(map(len, factories)) == [1, 1, 1, 1, 1, 30]
    assert report["summary"]["declared_samples"] == 35
    assert report["summary"]["cold_samples"] == 5
    assert report["summary"]["warm_samples"] == 30
    assert report["summary"]["errors"] == 0
    assert report["cache_policy"] == "cold=fresh adapter state; OS filesystem cache uncontrolled; warm=reused adapter per case"


def test_latency_errors_stay_in_denominator_and_missing_stage_is_unavailable():
    def factory():
        def invoke(_):
            raise RuntimeError("private")
        return invoke
    report = evaluation.benchmark_cases(suite(), factory)
    assert len(report["rows"]) == 35
    assert report["summary"]["declared_samples"] == 35
    assert report["summary"]["errors"] == 35
    assert report["case_statistics"][0]["warm"]["successful_samples"] == 0
    assert report["case_statistics"][0]["warm"]["stages_ms"] == {}


def test_latency_uses_nearest_rank_p95_and_reports_sample_limits():
    result = evaluation.latency_statistics([1, 2, 3, 4, 100])
    assert result == {"n": 5, "median": 3, "min": 1, "max": 100, "p95_nearest_rank": 100}
    assert evaluation.latency_statistics([]) is None


def test_receipt_binds_frozen_suite_and_executor_not_production_code_parity():
    report = evaluation.evaluate_cases(suite(), lambda _: response())
    assert len(report["suite_sha256"]) == 64
    assert len(report["evaluator_sha256"]) == 64
    changed = copy.deepcopy(report)
    changed["suite"]["cases"][0]["runtime_input"]["claims"][0]["claim"] = "changed"
    with pytest.raises(ValueError):
        evaluation.validate_report(changed)


def test_receipt_recomputes_adjudication_instead_of_trusting_fabricated_passes():
    report = evaluation.evaluate_cases(suite(), lambda _: response())
    report["rows"][0]["response"]["links"][0]["binding_status"] = "mismatched"
    with pytest.raises(ValueError):
        evaluation.validate_report(report)


def test_missing_asset_must_retain_exact_frozen_healthy_renderable_subset():
    c = case()
    target = c["expected"]["links"][0]
    target["asset_status"] = "missing"
    item = target["ordered_evidence"][0]
    item["asset_status"] = "missing"
    healthy = copy.deepcopy(item["assets"])
    item["assets"].append({"sha256": OTHER, "source_anchor_orders": [1],
                           "kind": "image", "verification_state": "verified"})
    item["rendered_assets"] = healthy
    observed = response(c)
    actual = observed["links"][0]["ordered_evidence"][0]
    actual["declared_assets"] = copy.deepcopy(actual["assets"])
    actual["assets"] = []  # Dropping the healthy primary is an additional failure.
    assert evaluation.check_case(c, observed)["checks"]["assets"] is False


def test_benchmark_warm_wall_excludes_adapter_initialization(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(evaluation.time, "perf_counter", lambda: clock[0])
    def factory():
        clock[0] += 1.0
        def invoke(_):
            clock[0] += .01
            return response()
        return invoke
    report = evaluation.benchmark_cases(suite(), factory)
    cold = [row["wall_ms"] for row in report["rows"] if row["temperature"] == "cold"]
    warm = [row["wall_ms"] for row in report["rows"] if row["temperature"] == "warm"]
    assert cold == pytest.approx([1010.0] * 5)
    assert warm == pytest.approx([10.0] * 30)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "wrong_repetition", "negative_time", "stale_statistics"])
def test_latency_receipt_revalidates_schedule_and_recomputes_statistics(mutation):
    report = evaluation.benchmark_cases(suite(), lambda: lambda _: response())
    if mutation == "missing":
        report["rows"].pop()
    elif mutation == "duplicate":
        report["rows"][1] = copy.deepcopy(report["rows"][0])
    elif mutation == "wrong_repetition":
        report["rows"][0]["repetition"] = 0
    elif mutation == "negative_time":
        report["rows"][0]["wall_ms"] = -1
    else:
        report["case_statistics"][0]["warm"]["successful_samples"] = 0
    with pytest.raises(ValueError):
        evaluation.validate_latency_report(report)


def test_exact_healthy_subset_is_derived_from_frozen_manifest_without_rewriting_labels(tmp_path):
    data = suite()
    target = data["cases"][0]["expected"]["links"][0]
    target["asset_status"] = "missing"
    item = target["ordered_evidence"][0]
    item["asset_status"] = "missing"
    item["assets"].append({"sha256": OTHER, "source_anchor_orders": [1],
                           "kind": "image", "verification_state": "verified"})
    data["cases"][0]["runtime_input"]["fixture"] = {"asset_mutations": [{"relpath": "parsed/missing.png", "mode": "missing"}]}
    manifest = {"figures": [{"id": "figure:synthetic_a", "assets": [
        {"relpath": "parsed/healthy.png", "sha256": H, "source_anchor_orders": [0], "verification": {"state": "verified"}},
        {"relpath": "parsed/missing.png", "sha256": OTHER, "source_anchor_orders": [1], "verification": {"state": "verified"}}]}], "tables": []}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    data["source_fingerprints"] = {"manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    case_path = tmp_path / "cases.json"
    case_path.write_text(json.dumps(data), encoding="utf-8")
    original = case_path.read_bytes()
    projected = evaluation.load_frozen_cases(case_path, manifest_path=manifest_path)
    projected_item = projected["cases"][0]["expected"]["links"][0]["ordered_evidence"][0]
    assert projected_item["rendered_assets"] == [item["assets"][0]]
    assert projected_item["assets"] == item["assets"]
    assert case_path.read_bytes() == original
    manifest_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        evaluation.load_frozen_cases(case_path, manifest_path=manifest_path)


@pytest.mark.parametrize('mode',[None,'missing','corrupt'])
def test_optional_navigation_projection_is_explicit_and_derived_only_from_frozen_inputs(tmp_path,mode):
    data=suite();candidate='figure:optional'
    manifest={'document':{'id':'doc:synthetic','sha256':H},
              'sections':[{'id':'clause:parent','normative_status':'conflicting'}],
              'figures':[{'id':'figure:synthetic_a'},
                         {'id':candidate,'label':'Optional figure','parent_id':'clause:parent',
                          'anchors':[{'pdf_index':5,'printed_label':'2','verification':{'state':'verified'}}],
                          'assets':[{'relpath':'parsed/optional.png','sha256':OTHER,'source_anchor_orders':[0],
                                     'verification':{'state':'verified'}}]}],
              'tables':[],'links':[{'from_id':'figure:synthetic_a','to_id':candidate,'kind':'ui_companion'}]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest),encoding='utf8')
    data['source_fingerprints']={'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if mode:data['cases'][0]['runtime_input']['fixture']={'asset_mutations':[{'relpath':'parsed/optional.png','mode':mode}]}
    cases=tmp_path/'cases.json';cases.write_text(json.dumps(data),encoding='utf8');original=cases.read_bytes()
    strict=evaluation.load_frozen_cases(cases,manifest_path=path) if mode is None else data
    projected=evaluation.load_frozen_cases(cases,manifest_path=path,include_navigation=True)
    assert 'allowed_navigation' not in strict['cases'][0]['expected']['links'][0]
    ledger=projected['cases'][0]['expected']['links'][0]['allowed_navigation']
    assert [item['element_id'] for item in ledger]==[candidate]
    assert ledger[0]['relationship']=='navigation_candidate'
    assert ledger[0]['source_anchors'][0]['normative_status']=='conflicting'
    assert ledger[0]['assets'][0]['sha256']==OTHER
    assert projected['cases'][0]['expected']['links'][0]['ordered_evidence']==data['cases'][0]['expected']['links'][0]['ordered_evidence']
    assert ledger[0]['asset_status']==(mode or 'complete')
    if mode:assert ledger[0]['rendered_assets']==[]
    assert cases.read_bytes()==original and 'adjudication_amendment' in projected
