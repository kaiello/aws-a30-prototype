"""Pure legacy route diagnostic aggregation; no benchmark, model or database."""
import ast
from fractions import Fraction
import json
import math
from numbers import Real
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def helpers():
    # Compile only the pure helpers: importing this legacy runner loads providers.
    source = (ROOT / "eval" / "test_scorer.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"_finite_metric", "_aggregate_legacy_metric", "_format_metric",
             "_legacy_route_metrics"}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {"math": math, "Real": Real}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "test_scorer.py", "exec"), namespace)
    return namespace


def test_all_unassessed_stays_null_with_full_denominator(helpers):
    result = helpers["_aggregate_legacy_metric"]([None, None, None])
    assert result == {"value": None, "assessed_count": 0, "total_count": 3}


def test_empty_run_is_unassessed_not_measured_zero(helpers):
    assert helpers["_aggregate_legacy_metric"]([]) == {
        "value": None, "assessed_count": 0, "total_count": 0}


def test_mixed_assessment_exposes_coverage_without_shrinking_total(helpers):
    result = helpers["_aggregate_legacy_metric"]([None, 0.25, 0.75, None])
    assert result == {"value": 0.5, "assessed_count": 2, "total_count": 4}


def test_valid_zero_is_assessed_and_not_replaced_with_null(helpers):
    result = helpers["_aggregate_legacy_metric"]([None, 0, 0.0])
    assert result == {"value": 0.0, "assessed_count": 2, "total_count": 3}
    assert helpers["_format_metric"](result["value"], precision=1, percent=True) == "0.0%"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"),
                                  True, False, "0.5", "", [], {}, object(), 1j])
def test_invalid_values_never_become_measured_numbers(helpers, value):
    assert helpers["_finite_metric"](value) is None
    assert helpers["_aggregate_legacy_metric"]([None, value]) == {
        "value": None, "assessed_count": 0, "total_count": 2}


def test_finite_real_values_include_fraction_and_normalize_to_json_numbers(helpers):
    assert helpers["_aggregate_legacy_metric"]([Fraction(1, 4), 0.75]) == {
        "value": 0.5, "assessed_count": 2, "total_count": 2}


def test_nonfinite_input_has_strict_json_null_output(helpers):
    result = helpers["_aggregate_legacy_metric"]([None, float("nan"), float("inf")])
    encoded = json.dumps(result, allow_nan=False)
    assert json.loads(encoded) == {
        "value": None, "assessed_count": 0, "total_count": 3}
    assert '"value": null' in encoded


@pytest.mark.parametrize("value", [None, float("nan"), True, "0.5"])
def test_unassessed_display_does_not_claim_zero_percent(helpers, value):
    assert helpers["_format_metric"](value, precision=1, percent=True) == "unassessed"


def test_formatting_preserves_numeric_precision(helpers):
    assert helpers["_format_metric"](0.125, precision=1, percent=True) == "12.5%"
    assert helpers["_format_metric"](0.125, precision=3) == "0.125"


def test_new_false_default_does_not_claim_measured_completeness(helpers):
    route = SimpleNamespace(evidence_recall_score=None, epistemic_score=None,
                            all_evidence_recovered=False)
    assert helpers["_legacy_route_metrics"](route) == {
        "evidence_recall": None, "epistemic_score": None, "all_evidence": None}


@pytest.mark.parametrize("flag,expected", [(True, 1.0), (False, 0.0)])
def test_legacy_measured_completeness_preserves_true_and_false(helpers, flag, expected):
    route = SimpleNamespace(evidence_recall_score=0.0, epistemic_score=0.5,
                            all_evidence_recovered=flag)
    assert helpers["_legacy_route_metrics"](route) == {
        "evidence_recall": 0.0, "epistemic_score": 0.5, "all_evidence": expected}


@pytest.mark.parametrize("flag", [None, 0, 1, "false"])
def test_completeness_requires_explicit_boolean_even_with_measured_recall(helpers, flag):
    route = SimpleNamespace(evidence_recall_score=0.5, epistemic_score=None,
                            all_evidence_recovered=flag)
    assert helpers["_legacy_route_metrics"](route)["all_evidence"] is None


def test_invalid_row_metrics_are_null_and_cannot_poison_receipt(helpers):
    route = SimpleNamespace(evidence_recall_score=float("nan"),
                            epistemic_score=float("inf"), all_evidence_recovered=True)
    row = helpers["_legacy_route_metrics"](route)
    assert row == {"evidence_recall": None, "epistemic_score": None, "all_evidence": None}
    assert json.loads(json.dumps(row, allow_nan=False)) == row
