"""
tests/test_gate_3d_phase3_holdout.py: Unit and Property Tests for Gate 3D Phase 3 Holdout.

0 Live LLM Calls. Tests:
1. Store Immutability & Checksums
2. Question Suite Structure & Rubric Completeness (40 questions across 4 slices)
3. Offline Data-Driven Plan Execution Engine (operations_count >= 1, zero blocked actions)
4. Anti-Drift & Anti-Hardcoding Invariant (0 forbidden question IDs in src/ or eval/*.py)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

from src.evidence_phase3_qa import get_phase3_stores, execute_phase3_plan


LOCKED_HASHES = {
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
}


def test_gate_3d_store_immutability():
    """Verify that all locked Phase 0–2 and Gate 3A–3C store hashes remain 100% intact."""
    for rel_path, exp_hash in LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Store file missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == exp_hash, f"Hash mismatch on {rel_path}: expected {exp_hash}, got {actual_hash}"


def test_gate_3d_question_suite_structure():
    """Verify that the 40-question holdout suite has 4 balanced slices of 10 questions each."""
    q_file = ROOT / "storage/evidence_v2/phase3_holdout_001/questions.json"
    r_file = ROOT / "storage/evidence_v2/phase3_holdout_001/rubric.json"

    assert q_file.exists(), f"Questions file missing: {q_file}"
    assert r_file.exists(), f"Rubric file missing: {r_file}"

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubric_data = json.loads(r_file.read_text(encoding="utf-8"))
    rubrics = rubric_data.get("rubrics", {})

    assert len(questions) == 40, f"Expected 40 questions, found {len(questions)}"
    assert len(rubrics) == 40, f"Expected 40 rubrics, found {len(rubrics)}"

    slices = {}
    for q in questions:
        s = q.get("slice")
        slices[s] = slices.get(s, 0) + 1
        assert q["id"] in rubrics, f"Question {q['id']} missing from rubric"

        r = rubrics[q["id"]]
        assert len(r.get("required_elements", [])) >= 2, f"{q['id']} has fewer than 2 required elements"
        assert len(r.get("forbidden_elements", [])) >= 1, f"{q['id']} has no forbidden elements"

    expected_slices = {
        "slice_1_clause4_glossary": 10,
        "slice_2_dual_provenance_is_a_annex_c_d": 10,
        "slice_3_archetype3_spatial_callouts": 10,
        "slice_4_archetype4_waveforms": 10,
    }
    assert slices == expected_slices, f"Slice distribution mismatch: {slices}"


def test_gate_3d_offline_data_driven_execution():
    """Verify that execute_phase3_plan executes operations dynamically with operations_count >= 1."""
    stores = get_phase3_stores(ROOT)

    test_cases = [
        # Slice 1: Clause 4 definition lookup
        (
            {"source_element": "Clause 4", "intent": "definition", "target_entities": ["braze"], "actions": [{"action_type": "lookup", "target": "braze"}]},
            "What is the definition of braze?",
            ["act of brazing", "verb", "braze"],
        ),
        # Slice 1: Nonstandard term redirect
        (
            {"source_element": "Clause 4", "intent": "nonstandard_term", "target_entities": ["stick electrode welding"], "actions": [{"action_type": "lookup", "target": "stick electrode welding"}]},
            "Is stick electrode welding a standard term and what is its preferred term?",
            ["nonstandard", "shielded metal arc welding", "SMAW"],
        ),
        # Slice 2: IS_A promotion metrics
        (
            {"source_element": "IS_A Promotion & Annex C/D", "intent": "is_a_promotion_metrics", "target_entities": ["Table A1"], "actions": [{"action_type": "query_metrics", "target": "is_a"}]},
            "How many indented process rows were evaluated for IS_A promotion and how many were promoted?",
            ["118", "35", "83", "IS_A_PROCESS_VARIATION_OF"],
        ),
        # Slice 2: Annex C decision C1.5.1
        (
            {"source_element": "IS_A Promotion & Annex C/D", "intent": "annex_c_decision", "target_entities": ["bonding", "welding", "C1.5.1"], "actions": [{"action_type": "query_decision", "target": "C1.5.1"}]},
            "What rule did the Definitions Subcommittee establish in Clause C1.5.1 regarding bonding vs welding?",
            ["bonding", "welding", "adhesive", "interatomic"],
        ),
        # Slice 3: Figure B1 applicable welds
        (
            {"source_element": "Figure B1", "intent": "applicable_welds", "target_entities": ["Figure B1", "joint types"], "actions": [{"action_type": "query_welds", "target": "Figure B1"}]},
            "What are the five basic joint types shown in Figure B1 and what weld type is applicable to all five?",
            ["Butt Joint", "Corner Joint", "T-Joint", "Lap Joint", "Parallel Joint", "BRAZE"],
        ),
        # Slice 3: Figure B33 crack keys
        (
            {"source_element": "Figure B33", "intent": "crack_keys", "target_entities": ["Figure B33"], "actions": [{"action_type": "query_keys", "target": "Figure B33"}]},
            "In Figure B33 (Crack Types), how many numbered crack key items are in the legend?",
            ["Figure B33", "13", "Crater crack"],
        ),
        # Slice 4: Figure B49 waveforms
        (
            {"source_element": "Figure B49", "intent": "waveform_traces", "target_entities": ["Figure B49"], "actions": [{"action_type": "query_traces", "target": "Figure B49"}]},
            "In Figure B49, what synchronized vertical traces are plotted against the horizontal TIME axis?",
            ["Figure B49", "TIME", "RESISTANCE WELDING CURRENT", "ELECTRODE FORCE"],
        ),
        # Slice 4: Figure B53 waveform cycles
        (
            {"source_element": "Figure B53", "intent": "waveform_traces", "target_entities": ["Figure B53"], "actions": [{"action_type": "query_traces", "target": "Figure B53"}]},
            "In Figure B53, what are the five synchronized vertical traces plotted against time?",
            ["Figure B53", "WELDING CURRENT", "ARC VOLTAGE", "WIRE FEED SPEED", "TRAVEL SPEED", "SHIELDING GAS FLOW"],
        ),
    ]

    for plan, query, expected_tokens in test_cases:
        res = execute_phase3_plan(plan, query, stores=stores)
        assert res["status"] == "PASS"
        assert res["operations_count"] >= 1, f"Zero operations executed for query: {query}"
        ans_text = res["answer"]
        assert len(ans_text) >= 20, f"Answer too short: {ans_text}"
        for token in expected_tokens:
            assert token.lower() in ans_text.lower(), f"Expected token '{token}' missing from answer: {ans_text}"


def test_gate_3d_anti_drift_zero_grep():
    """Verify that no benchmark question IDs or canned responses are hardcoded in src/ or eval/*.py."""
    import re
    pattern = re.compile(r"QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-")
    violations = []
    files_to_check = list((ROOT / "src").rglob("*.py")) + list((ROOT / "eval").glob("*.py"))
    for f in files_to_check:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for idx, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(ROOT)}:{idx}: {line.strip()}")
        except Exception:
            pass
    assert not violations, f"Anti-drift violation! Found hardcoded tokens:\n" + "\n".join(violations)

    cmd = ["git", "grep", "-E", "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-", "--", "src/", "eval/*.py"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1, f"Anti-drift violation! Found hardcoded tokens:\n{result.stdout}"
