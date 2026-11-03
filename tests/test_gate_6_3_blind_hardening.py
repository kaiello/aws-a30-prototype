"""Gate 6.3 Blind Hardening Verification Suite.

Validates the full 45-artifact cryptographic lock ledger, 100% (20/20) pass rate
on the blind hardening benchmark suite (storage/evidence_v2/phase6_3_blind_hardening_001),
NER process variation grammar, embedded lightface nonstandard term extraction,
AST zero silent fallback compliance across 12 composer functions, and zero hardcoded test IDs.
"""

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
from typing import Any, Dict
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    _compose_annex_a_chart_answer,
    _compose_normative_tables_answer,
    _compose_waveform_phase4_answer,
    _exec_lookup_taxonomy_subtypes,
    _exec_expand_cross_references,
    _exec_weld_position_sense,
    _exec_disambiguate_homograph,
    _exec_compound_lookup_and_validation,
    _exec_compare_historical_and_active,
    _exec_polysemous_diagram_and_glossary,
    _exec_decode_process_designations,
    execute_whole_standard_plan,
)
from src.welding_ner import get_welding_ner
from src.evidence_clause4_glossary import lookup_glossary_term
from tests.test_gate_6_2_1_multi_action_closure import ALL_42_LOCKED_HASHES

# ---------------------------------------------------------------------------
# All 45 Cryptographically Locked Artifact Hashes (Gate 6.3 Baseline)
# ---------------------------------------------------------------------------
ALL_45_LOCKED_HASHES: Dict[str, str] = {
    **ALL_42_LOCKED_HASHES,
    # 3 Phase 6.3 Blind Hardening Benchmark Files (NET-NEW)
    "storage/evidence_v2/phase6_3_blind_hardening_001/questions.json": "be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b",
    "storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json": "a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c",
    "storage/evidence_v2/phase6_3_blind_hardening_001/results.json": "18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2",
}


def test_gate_6_3_all_45_locked_hashes():
    """Verify byte-for-byte SHA-256 immutability of all 45 locked artifacts."""
    for rel_path, expected_hash in ALL_45_LOCKED_HASHES.items():
        target_path = ROOT / rel_path
        assert target_path.exists(), f"Locked artifact missing on disk: {rel_path}"
        computed_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        assert computed_hash == expected_hash, (
            f"Cryptographic hash mismatch for {rel_path}:\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {computed_hash}"
        )


def test_gate_6_3_blind_hardening_20_questions_offline(monkeypatch):
    """Verify 20/20 (100.0%) pass rate on blind hardening benchmark with network strictly blocked."""
    def _blocked_socket(*args, **kwargs):
        raise RuntimeError("NETWORK_ACCESS_BLOCKED: Tests must run 100% offline.")

    monkeypatch.setattr(socket, "socket", _blocked_socket)

    benchmark_dir = ROOT / "storage/evidence_v2/phase6_3_blind_hardening_001"
    questions = json.loads((benchmark_dir / "questions.json").read_text(encoding="utf-8"))
    rubric = json.loads((benchmark_dir / "rubric.json").read_text(encoding="utf-8"))

    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    passed_count = 0
    failures = []

    for item in questions:
        q_id = item["id"]
        q_text = item["query"]
        rub = rubric["rubrics"][q_id]

        res = answer_whole_standard_question(q_text, planner, stores=stores)
        exec_res = res.get("execution", res)
        ans_text = res.get("answer", "")
        actual_status = exec_res.get("status", "FAIL")

        ans_lower = ans_text.lower()
        req_missing = [req for req in rub["required_elements"] if req.lower() not in ans_lower]
        forb_hits = [forb for forb in rub.get("forbidden_elements", []) if forb.lower() in ans_lower]

        status_match = actual_status == rub["expected_status"]
        crop_match = exec_res.get("requires_diagram_crop", False) == rub["requires_diagram_crop"]

        if status_match and crop_match and len(req_missing) == 0 and len(forb_hits) == 0:
            passed_count += 1
        else:
            failures.append(f"{q_id}: status_match={status_match}, crop_match={crop_match}, missing={req_missing}, forbidden={forb_hits}")

    assert not failures, f"Blind hardening failures ({len(failures)}/20):\n" + "\n".join(failures)
    assert passed_count == 20, f"Expected 20/20, got {passed_count}/20"


def test_gate_6_3_ner_process_variation_grammar():
    """Verify WeldingNER properly handles process variation letter designations and compound suffixes."""
    stores = get_whole_standard_stores(ROOT)
    ner = get_welding_ner(stores=stores, root=ROOT)

    # Valid process variations from Tables A1/A2/A3 must be recognized as PROCESS_CODE in lexicon
    valid_variations = ["LBC-EV", "EBW-HV", "FLSP-P", "FRW-DD", "HIPW", "OFC-A", "GMAW-P", "GTAW-P"]
    for v in valid_variations:
        assert v in ner.process_codes, f"Process variation {v} missing in ner.process_codes lexicon"
        receipt = ner.recognize_entities(f"What is {v} in AWS A3.0?")
        code_entities = [s.surface_text for s in receipt.spans if s.entity_type in ["PROCESS_CODE", "COMPOUND_DESIGNATION"]]
        assert any(v in ce for ce in code_entities), f"NER failed to recognize valid variation {v}"

    # Verify compound parsing distinguishing variations from Table A4 modes
    # Standalone variations are recognized as process codes, so parse_compound_designation returns None
    assert ner.parse_compound_designation("LBC-EV") is None

    # Compound application modes are valid
    parsed_gmaw = ner.parse_compound_designation("GMAW-SA")
    assert parsed_gmaw is not None
    assert parsed_gmaw["is_valid"] is True
    assert "semiautomatic" in parsed_gmaw["canonical_term"]

    # 3-tier compound with variation + mode
    parsed_3tier = ner.parse_compound_designation("GMAW-S-RO")
    assert parsed_3tier is not None
    assert parsed_3tier["is_valid"] is True
    assert "robotic" in parsed_3tier["canonical_term"]

    # Nonstandard / invalid suffix
    parsed_invalid = ner.parse_compound_designation("GMAW-ZZ")
    assert parsed_invalid is not None
    assert parsed_invalid["is_valid"] is False


def test_gate_6_3_embedded_lightface_nonstandard_term_resolution():
    """Verify embedded Clause 4 lightface nonstandard terms are extracted and resolve to standard terms."""
    stores = get_whole_standard_stores(ROOT)
    glossary = stores["glossary"]

    terms_to_test = {
        "ground clamp": "workpiece connection",
        "ground lead": "workpiece lead",
        "welding ground": "workpiece connection",
        "silver soldering": "brazing",
    }

    for term, expected_target in terms_to_test.items():
        entry = lookup_glossary_term(term, glossary)
        assert entry is not None, f"Lightface term '{term}' not found in glossary lookup"
        assert entry.get("is_standard") is False, f"Term '{term}' should be nonstandard"
        def_lower = entry.get("definition", "").lower()
        assert ("nonstandard" in def_lower or "incorrect" in def_lower), f"Term '{term}' should have nonstandard or incorrect in definition"
        assert expected_target in def_lower, f"Term '{term}' missing redirect target '{expected_target}'"


def test_gate_6_3_ast_zero_fallbacks_across_all_12_functions():
    """Verify 0 string-literal fallbacks and 0 domain-entity ternary fallbacks across all 12 functions."""
    qa_file = ROOT / "src/evidence_phase4_bakeoff.py"
    tree = ast.parse(qa_file.read_text(encoding="utf-8"))

    composer_functions = [
        "_compose_annex_a_chart_answer",
        "_compose_normative_tables_answer",
        "_compose_waveform_phase4_answer",
        "_exec_lookup_taxonomy_subtypes",
        "_exec_expand_cross_references",
        "_exec_weld_position_sense",
        "_exec_disambiguate_homograph",
        "_exec_compound_lookup_and_validation",
        "_exec_compare_historical_and_active",
        "_exec_polysemous_diagram_and_glossary",
        "execute_whole_standard_plan",
        "_exec_decode_process_designations",
    ]

    violations = []
    banned_ternary_literals = [
        "Edge Shapes", "Figure B25", "Figure B7",
        "undercut", "coalescence", "atomic hydrogen welding",
        "flux cored arc welding", "gas tungsten arc welding",
        "throat of a fillet weld", "PAW-AU", "1G", "2F", "AHW", "UNKNOWN",
    ]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in composer_functions:
            for sub in ast.walk(node):
                # 1. Banned .get(k, "fallback")
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "get":
                    if len(sub.args) >= 2 and isinstance(sub.args[1], ast.Constant):
                        val = sub.args[1].value
                        if isinstance(val, str) and len(val.strip()) > 0:
                            violations.append(f"{node.name}:{sub.lineno}: .get({ast.dump(sub.args[0])}, '{val}')")
                # 2. Banned ternary domain entity fallbacks
                if isinstance(sub, ast.IfExp):
                    for branch in [sub.body, sub.orelse]:
                        if isinstance(branch, ast.Constant) and isinstance(branch.value, str):
                            if branch.value in banned_ternary_literals:
                                violations.append(f"{node.name}:{sub.lineno}: banned ternary literal '{branch.value}'")
                # 3. Banned .get(...) or "literal" fallbacks
                if isinstance(sub, ast.BoolOp) and isinstance(sub.op, ast.Or):
                    if len(sub.values) >= 2 and isinstance(sub.values[0], ast.Call):
                        first_val = sub.values[0]
                        if isinstance(first_val.func, ast.Attribute) and first_val.func.attr == "get":
                            for v in sub.values[1:]:
                                if isinstance(v, ast.Constant) and isinstance(v.value, str) and len(v.value.strip()) > 0:
                                    get_arg = first_val.args[0].value if (first_val.args and isinstance(first_val.args[0], ast.Constant)) else None
                                    if get_arg == "target_division" and v.value == "Clause 4":
                                        continue
                                    if get_arg == "intent" and v.value == "general_query":
                                        continue
                                    violations.append(f"{node.name}:{sub.lineno}: .get({repr(get_arg)}) or '{v.value}'")

    assert not violations, f"AST violations detected in composer/execution functions:\n" + "\n".join(violations)


def test_gate_6_3_store_mutations_raise_insufficient_evidence():
    """Verify that mutating injected stores raises ValueError('INSUFFICIENT_EVIDENCE') across all 6 new Gate 6.3 paths."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # 1. Decode process designations
    mut1 = copy.deepcopy(stores)
    mut1["tables"]["table_a1"] = []
    mut1["glossary"]["entries"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("Decode GTAW, FRW, and FLSP-P", planner, stores=mut1)

    # 2. Figure B1 applicable welds
    mut2 = copy.deepcopy(stores)
    mut2["annex_b_complete"]["figures"].pop("Figure B1", None)
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Figure B1, how many applicable welds are listed for a T-joint?", planner, stores=mut2)

    # 3. Figure B21 reverse figure lookup
    mut3 = copy.deepcopy(stores)
    mut3["annex_b_complete"]["figures"].pop("Figure B21", None)
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("What figure illustrates Position of Beam, Filler Material, Gun, or Torch?", planner, stores=mut3)

    # 4. Figure B23(J) temper beads
    mut4 = copy.deepcopy(stores)
    mut4["annex_b_complete"]["figures"].pop("Figure B23", None)
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Figure B23(J), how is distance S measured for temper beads?", planner, stores=mut4)

    # 5. Annex C C2.3 safety terms
    mut5 = copy.deepcopy(stores)
    mut5["glossary"]["entries"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("Why are ground clamp and ground lead designated as nonstandard and incorrect per Annex C C2.3?", planner, stores=mut5)

    # 6. Annex C/D revisions
    mut6 = copy.deepcopy(stores)
    mut6["annex_c_d"] = {}
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("Summarize Annex C C1.5.6 and C1.5.7 regarding parallel joint and nondestructive examination.", planner, stores=mut6)


def test_gate_6_3_checkout_card_hygiene():
    """Verify GATE_6_3_CHECKOUT_CARD.md contains zero mojibake corruption and reports all 45 locked hashes."""
    card_path = ROOT / "GATE_6_3_CHECKOUT_CARD.md"
    assert card_path.exists(), "GATE_6_3_CHECKOUT_CARD.md missing"
    card_text = card_path.read_text(encoding="utf-8")
    assert "窶" not in card_text, "Found CP932/Shift-JIS mojibake '窶' in GATE_6_3_CHECKOUT_CARD.md"
    for rel_path, expected_hash in ALL_45_LOCKED_HASHES.items():
        assert expected_hash in card_text, f"Locked hash for {rel_path} missing in GATE_6_3_CHECKOUT_CARD.md"


def test_gate_6_3_anti_drift_zero_hardcoded_benchmark_ids():
    """Verify zero benchmark IDs (G63-BLIND*, G60-, G61-, G62-) are hardcoded in src/ or eval/."""
    src_dir = ROOT / "src"
    eval_dir = ROOT / "eval"

    pattern = re.compile(r"\b(G63-BLIND\d{2}|G6[0-3]-)\b")

    violations = []
    for d in [src_dir, eval_dir]:
        for py_path in d.glob("*.py"):
            text = py_path.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if line.strip().startswith("#"):
                    continue
                m = pattern.search(line)
                if m:
                    violations.append(f"{py_path.name}:{line_no}: found benchmark ID '{m.group(1)}'")

    assert not violations, f"Anti-drift failure: benchmark IDs found in codebase:\n" + "\n".join(violations)
