"""Focused trusted-contract loader checks; no model, backend, source or gold."""
import hashlib
import json

import pytest

from src.evidence_chart_contract import (
    CONTRACT, CONTRACT_PATH, CONTRACT_SHA256, CONTRACT_VERSION, ContractError,
    EMPTY_SUBJECT_SCOPES, INSTRUCTION_VERSION, OPERATION_PROFILES, SCHEMA_VERSION,
    load_contract, planner_instructions,
)


def test_default_contract_identity_and_explicit_scopes():
    assert CONTRACT_SHA256 == hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    assert CONTRACT_VERSION == "chart-plan-contract-1.0"
    assert SCHEMA_VERSION == "chart-llm-plan-1.0"
    assert INSTRUCTION_VERSION == "chart-llm-plan-instructions-1.4"
    assert len(OPERATION_PROFILES) == 15
    chart = OPERATION_PROFILES["chart_layout"]
    assert chart["subjects"] == chart["targets"] == ()
    assert chart["layers"] == ("evidence",)
    assert EMPTY_SUBJECT_SCOPES["chart_layout"] == "chart"
    assert all(EMPTY_SUBJECT_SCOPES[kind] == "source" for kind in
        ("evidence", "epistemic_limits", "operating_information"))
    assert OPERATION_PROFILES["designation"]["subjects"] == ("root", "category", "process")
    assert OPERATION_PROFILES["membership"]["subjects"] == ("process",)
    assert "MODEL_PROPOSED_UNVERIFIED" in planner_instructions()


def test_definitions_are_immutable_and_copies_are_independent():
    with pytest.raises(TypeError):
        CONTRACT.definitions["budgets"]["MAX_OPERATIONS"] = 99
    copy = CONTRACT.as_dict()
    copy["operation_profiles"]["category"]["subjects"].append("category")
    assert OPERATION_PROFILES["category"]["subjects"] == ("process",)


@pytest.mark.parametrize("change", [
    lambda d: d["budgets"].update(MAX_OPERATIONS=True),
    lambda d: d["budgets"].update(MAX_LITERAL_IDS=33),
    lambda d: d["operation_profiles"]["layout_relation"].update(layers=["knowledge"]),
    lambda d: d["operation_profiles"]["category"].update(subjects=["category"]),
    lambda d: d["operation_profiles"]["membership"].update(targets=["process"]),
    lambda d: d["operation_profiles"]["chart_layout"].update(subjects=["root"]),
    lambda d: d["empty_subject_scopes"].update(evidence="chart"),
    lambda d: d["operation_profiles"]["paths"]["produces"].update(sql=["process"]),
    lambda d: d.update(extra="unknown"),
])
def test_unsafe_or_unknown_contract_is_rejected(tmp_path, change):
    value = CONTRACT.as_dict()
    change(value)
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ContractError):
        load_contract(path)


def test_duplicate_json_key_and_oversized_file_fail_closed(tmp_path):
    path = tmp_path / "contract.json"
    path.write_text('{"budgets":{},"budgets":{}}', encoding="utf-8")
    with pytest.raises(ContractError, match="DUPLICATE_KEY"):
        load_contract(path)
    path.write_bytes(b" " * 65537)
    with pytest.raises(ContractError, match="FILE_TOO_LARGE"):
        load_contract(path)
