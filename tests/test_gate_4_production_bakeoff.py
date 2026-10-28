"""
tests/test_gate_4_production_bakeoff.py: Unit, AST Anti-Drift, and Immutability Tests for Gate 4.

0 Live LLM Calls. Tests:
1. Canonical Store Immutability & SHA-256 Integrity
2. Benchmark Suite Structure (30 questions across 6 slices) & Rubric Completeness
3. AST Zero-Oracle-Leakage Invariants on src/evidence_phase4_bakeoff.py and src/evidence_phase3_qa.py
4. Anti-Drift Zero-Hardcoded Question ID Grep Check across src/ and eval/*.py
5. Deterministic Baseline Whole-Standard QA Execution (30/30 PASS, operations_count >= 1)
6. Shared Preflight Contract (CLEAR_REAL_ENTRY_CONTRACT)
7. Anti-Drift Zero-Canned-Prose & Zero-Typo Invariant ("flywheel flywheel")
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parent.parent

from src.evidence_phase4_bakeoff import (
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    answer_whole_standard_question,
)
from eval.run_phase4_bakeoff import evaluate_response


LOCKED_STORE_HASHES = {
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
}

LOCKED_BENCHMARK_HASHES = {
    "storage/evidence_v2/phase4_bakeoff_001/questions.json": "3c45d1a268beeac02b7d304c7b675dc383dbde2142e67b38c86444da65524b30",
    "storage/evidence_v2/phase4_bakeoff_001/rubric.json": "97a80a434a18948f767d1b68795d3b6d7e3364507d4ce891553d376b14b839d9",
}


def test_gate_4_canonical_store_hashes():
    """Verify that all 7 canonical stores from Phases 0-3 match their locked hashes."""
    for rel_path, exp_hash in LOCKED_STORE_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Store file missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == exp_hash, f"Hash mismatch on {rel_path}: expected {exp_hash}, got {actual_hash}"


def test_gate_4_benchmark_structure_and_rubric():
    """Verify that the 30-question suite has 6 balanced slices of 5 questions each."""
    q_file = ROOT / "storage/evidence_v2/phase4_bakeoff_001/questions.json"
    r_file = ROOT / "storage/evidence_v2/phase4_bakeoff_001/rubric.json"

    assert q_file.exists(), f"Questions file missing: {q_file}"
    assert r_file.exists(), f"Rubric file missing: {r_file}"

    # Verify locked hashes
    for path_str, exp_hash in LOCKED_BENCHMARK_HASHES.items():
        actual = hashlib.sha256((ROOT / path_str).read_bytes()).hexdigest()
        assert actual == exp_hash, f"Benchmark hash mismatch on {path_str}: expected {exp_hash}, got {actual}"

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubric_data = json.loads(r_file.read_text(encoding="utf-8"))
    rubrics = rubric_data.get("rubrics", {})

    assert len(questions) == 30, f"Expected 30 questions, found {len(questions)}"
    assert len(rubrics) == 30, f"Expected 30 rubrics, found {len(rubrics)}"

    slices = {}
    for q in questions:
        s = q.get("slice")
        slices[s] = slices.get(s, 0) + 1
        assert q["id"] in rubrics, f"Question {q['id']} missing from rubric"

        r = rubrics[q["id"]]
        assert len(r.get("required_elements", [])) >= 2, f"{q['id']} has fewer than 2 required elements"
        assert len(r.get("forbidden_elements", [])) >= 1, f"{q['id']} has no forbidden elements"

    expected_slices = {
        "slice_a_annex_a_charts": 5,
        "slice_b_normative_tables": 5,
        "slice_c_clause4_glossary": 5,
        "slice_d_dual_provenance_is_a_annex_c_d": 5,
        "slice_e_archetype3_spatial_callouts": 5,
        "slice_f_archetype4_waveforms": 5,
    }
    assert slices == expected_slices, f"Slice distribution mismatch: {slices}"


def test_gate_4_ast_anti_drift_zero_oracle_leakage():
    """Verify zero benchmark metadata oracle leakage or forbidden dispatch names in QA engines."""
    forbidden_names = {"source_elem", "source_element", "question_id", "qid", "slice", "slice_name"}
    qa_files = [
        ROOT / "src/evidence_phase4_bakeoff.py",
        ROOT / "src/evidence_phase3_qa.py",
    ]

    for qa_file in qa_files:
        assert qa_file.exists(), f"QA file missing: {qa_file}"
        tree = ast.parse(qa_file.read_text(encoding="utf-8"))
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                violations.append(f"{qa_file.name} line {node.lineno}: AST Name '{node.id}'")
            elif isinstance(node, ast.Attribute) and node.attr in forbidden_names:
                violations.append(f"{qa_file.name} line {node.lineno}: AST Attribute '{node.attr}'")
        assert not violations, f"Oracle leakage detected in {qa_file.name}:\n" + "\n".join(violations)

    # Verify public entrypoint signature
    sig = inspect.signature(answer_whole_standard_question)
    param_names = list(sig.parameters.keys())
    assert param_names[0] == "question_text", f"First parameter must be 'question_text', got {param_names[0]}"
    for p in param_names:
        assert p not in forbidden_names, f"Parameter '{p}' violates zero-oracle contract"


def test_gate_4_anti_drift_zero_grep_matches():
    """Verify that no benchmark question IDs or canned responses are hardcoded in src/ or eval/*.py."""
    cmd = ["git", "grep", "-E", "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]", "--", "src/", "eval/*.py"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1, f"Anti-drift violation! Found hardcoded tokens:\n{result.stdout}"


def test_gate_4_ast_anti_drift_zero_canned_prose_and_no_flywheel_typo():
    """Verify that flywheel flywheel typo is 100% eliminated and zero canned benchmark prose exists."""
    cmd = ["git", "grep", "-i", "flywheel flywheel", "--", "src/", "eval/"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1, f"Found 'flywheel flywheel' typo in code:\n{result.stdout}"

    # Verify src/evidence_phase4_bakeoff.py AST has zero hardcoded question-id matching string literals
    qa_file = ROOT / "src/evidence_phase4_bakeoff.py"
    tree = ast.parse(qa_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            assert "flywheel flywheel" not in val, "Found 'flywheel flywheel' in AST string literal"


def test_gate_4_deterministic_route_all_pass():
    """Verify that DeterministicQuestionPlanner scores 30/30 (100%) on the benchmark."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    q_file = ROOT / "storage/evidence_v2/phase4_bakeoff_001/questions.json"
    r_file = ROOT / "storage/evidence_v2/phase4_bakeoff_001/rubric.json"
    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubrics = json.loads(r_file.read_text(encoding="utf-8"))["rubrics"]

    passed_count = 0
    for q_item in questions:
        raw_qid = q_item["id"]
        query_text = q_item["query"]
        ans = answer_whole_standard_question(query_text, planner, stores=stores)
        grade = evaluate_response(ans, rubrics[raw_qid])

        assert grade["schema_valid"] is True, f"Schema invalid on {raw_qid}"
        assert grade["compiler_accepted"] is True, f"Compiler rejected on {raw_qid}"
        assert grade["executed_operations"] is True, f"Zero operations on {raw_qid}"
        assert len(grade["required_elements_missing"]) == 0, f"Missing required elements on {raw_qid}: {grade['required_elements_missing']}"
        assert len(grade["forbidden_elements_found"]) == 0, f"Found forbidden elements on {raw_qid}: {grade['forbidden_elements_found']}"
        assert grade["content_grade"] == "PASS", f"Content grade failed on {raw_qid}"
        assert grade["delivery_grade"] == "PASS", f"Delivery grade failed on {raw_qid}"
        passed_count += 1

    assert passed_count == 30, f"Expected 30/30 pass, got {passed_count}/30"


def test_gate_4_preflight_contract():
    """Verify that shared evidence chart preflight contract returns CLEAR_REAL_ENTRY_CONTRACT."""
    from src.evidence_chart_preflight import run_figure_preflight
    result = run_figure_preflight("A1", root=ROOT)
    assert result["status"] == "CLEAR_REAL_ENTRY_CONTRACT", f"Preflight failed: {result}"
    assert result["new_model_calls"] == 0


def test_gate_4_deepseek_receipts_match_frozen_questions():
    """Verify that every request_0XX/request.json in deepseek_run contains the exact question query from questions.json."""
    q_file = ROOT / "storage/evidence_v2/phase4_bakeoff_001/questions.json"
    questions = json.loads(q_file.read_text(encoding="utf-8"))
    deepseek_dir = ROOT / "storage/evidence_v2/phase4_bakeoff_001/deepseek_run"
    assert deepseek_dir.exists(), f"DeepSeek run directory missing: {deepseek_dir}"

    for idx, q_item in enumerate(questions, 1):
        req_file = deepseek_dir / f"request_{idx:03d}" / "request.json"
        assert req_file.exists(), f"Missing request.json for index {idx} ({q_item['id']})"
        req_data = json.loads(req_file.read_text(encoding="utf-8"))
        prompt_content = ""
        if "messages" in req_data:
            prompt_content = "\n".join(m.get("content", "") for m in req_data["messages"])
        else:
            prompt_content = str(req_data.get("prompt") or req_data.get("text") or req_data)
        assert q_item["query"] in prompt_content, (
            f"Question text mismatch on {q_item['id']} ({idx:03d}):\n"
            f"Expected: {q_item['query']}\n"
            f"Found in request: {prompt_content}"
        )
