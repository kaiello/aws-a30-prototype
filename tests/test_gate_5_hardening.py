"""Gate 5 Test Suite: Production Hardening, Adversarial Invariants, and Anti-Drift Defense.

Verifies:
1. Canonical Store Immutability across all 7 historical stores + 3 frozen Phase 5 benchmark files.
2. Anti-Drift Source Scan: regex scan over src/*.py and eval/*.py ensuring zero hardcoded IDs.
3. AST Zero-Fallback Guard: ensures no composer invokes .get(key, default) with non-empty string literals.
4. Store-Mutation Degradation: artificially blanking store fields MUST raise
   INSUFFICIENT_EVIDENCE across Figures A3, A5, A6, Tables A4, A5, Clause 4, and Annex B.
5. Adversarial Suite: 10 boundary, out-of-range, contradiction, and out-of-scope
   queries are properly refuted/rejected without hallucinations.
6. Paraphrase Robustness: perturbed question phrasing produces identical target
   and operation resolution across 5 distinct architectural slices.
7. Whole-Standard Preflight Contract: offline execution, zero network calls,
   provenance delivery.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import pytest
from typing import Any, Dict

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    ROOT,
)
from src.evidence_whole_standard_preflight import (
    run_whole_standard_preflight,
    LOCKED_STORE_HASHES,
)

BENCHMARK_DIR = ROOT / "storage/evidence_v2/phase5_hardening_001"

LOCKED_PHASE5_HASHES = {
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json": "0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9",
    "storage/evidence_v2/phase5_hardening_001/rubric.json": "df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981",
    "storage/evidence_v2/phase5_hardening_001/results.json": "f2c38b4075cca47c1f6333d17f874095cf3ea3271957e445950f5b579753ba2a",
}


def test_gate_5_canonical_store_hashes():
    """Verify that all 7 canonical stores + 3 Phase 5 benchmark files match locked SHA-256 digests."""
    # Check 7 canonical stores
    for rel_path, exp_hash in LOCKED_STORE_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Store missing: {rel_path}"
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual == exp_hash, f"Canonical store mutated: {rel_path}"

    # Check 3 Phase 5 benchmark files
    for rel_path, exp_hash in LOCKED_PHASE5_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Benchmark file missing: {rel_path}"
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual == exp_hash, f"Phase 5 benchmark file mutated: {rel_path}"


def test_gate_5_anti_drift_source_scan():
    """Verify that no benchmark question IDs are hardcoded in src/ or eval/*.py using full wildcard pattern."""
    regex_pattern = r"QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+"

    targets = list((ROOT / "src").rglob("*.py")) + list((ROOT / "eval").glob("*.py"))
    violations = []
    for target in targets:
        text = target.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(regex_pattern, line):
                # allow comment references in test files or self-referential anti-drift strings
                if "test_" in target.name or "regex_pattern" in line:
                    continue
                violations.append(f"{target.relative_to(ROOT)}:{i}: {line.strip()}")

    assert not violations, f"Anti-drift violation! Found hardcoded question IDs:\n" + "\n".join(violations)


def test_gate_5_composer_ast_no_silent_string_fallbacks():
    """Verify via Python AST that composer functions do not use .get(key, default) with non-empty string literals."""
    qa_file = ROOT / "src/evidence_phase4_bakeoff.py"
    tree = ast.parse(qa_file.read_text(encoding="utf-8"))

    composer_functions = [
        "_compose_annex_a_chart_answer",
        "_compose_normative_tables_answer",
        "_compose_waveform_phase4_answer",
    ]

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in composer_functions:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "get":
                    if len(sub.args) >= 2 and isinstance(sub.args[1], ast.Constant):
                        val = sub.args[1].value
                        if isinstance(val, str) and len(val.strip()) > 0:
                            violations.append(f"{node.name}:{sub.lineno}: .get({ast.dump(sub.args[0])}, '{val}')")

    assert not violations, f"Found forbidden string fallbacks in composers:\n" + "\n".join(violations)


def test_gate_5_store_mutation_raises_insufficient_evidence():
    """Verify that composers raise INSUFFICIENT_EVIDENCE when store fields are missing (no silent defaults)."""
    base_stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # 1. Mutate Figure A5: remove path_summary and branch_summary from cold welding node
    mutated_stores_1 = copy.deepcopy(base_stores)
    g5_nodes = mutated_stores_1["annex_a_graphs"]["Figure A5"]["nodes"]
    for n in g5_nodes:
        if n.get("label") == "CW" or n.get("code") == "CW":
            n.pop("path_summary", None)
            n.pop("branch_summary", None)

    q_a5 = (
        "In Figure A5 (Solid-State Welding Classification Chart), which specific process "
        "branches directly from Mechanical energy to Pressure and Deformation while "
        "completely bypassing the Thermal Source characteristic column?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_a5, planner, stores=mutated_stores_1)

    # 2. Mutate Figure A6: remove code from AB / B-CA legend nodes
    mutated_stores_2 = copy.deepcopy(base_stores)
    g6_nodes = mutated_stores_2["annex_a_graphs"]["Figure A6"]["nodes"]
    for n in g6_nodes:
        if n.get("name") in ["arc brazing", "carbon arc brazing"] or n.get("code") in ["AB", "B-CA"]:
            n.pop("code", None)

    q_a6 = (
        "In Figure A6 (Brazing and Soldering Classification Chart), how many distinct process "
        "designations are defined in the bottom legend table across its 48 process circle branches, "
        "and how are arc brazing and carbon arc brazing designated?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_a6, planner, stores=mutated_stores_2)

    # 3. Mutate Table A4: remove -AU suffix entry
    mutated_stores_3 = copy.deepcopy(base_stores)
    t4_suffixes = mutated_stores_3["tables"]["table_a4"]["suffixes"]
    mutated_stores_3["tables"]["table_a4"]["suffixes"] = [
        s for s in t4_suffixes if s.get("suffix") != "-AU"
    ]

    q_t4 = (
        "What are the six standard suffix letter modifiers defined in Table A4 "
        "for the application mode of welding and allied processes, and what does the suffix -AU designate?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_t4, planner, stores=mutated_stores_3)

    # 4. Mutate Clause 4: remove kerf definition
    mutated_stores_4 = copy.deepcopy(base_stores)
    for e in mutated_stores_4["glossary"].get("entries", []):
        if e.get("term") == "kerf":
            e["definition"] = None

    q_kerf = (
        "What is the official definition and figure cross-reference for the term 'kerf' "
        "in Clause 4 of AWS A3.0M/A3.0:2020?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_kerf, planner, stores=mutated_stores_4)

    # 5. Mutate Figure A3: remove Method category nodes
    mutated_stores_5 = copy.deepcopy(base_stores)
    g3 = mutated_stores_5["annex_a_graphs"]["Figure A3"]
    g3["nodes"] = [n for n in g3["nodes"] if not (n.get("kind") == "category" and n.get("column") == "Method")]

    q_a3 = (
        "In Figure A3 (Joining Method Chart), what are the three major methods of materials "
        "joining classified, and what does footnote a state regarding the simplicity of the chart lines?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_a3, planner, stores=mutated_stores_5)

    # 6. Mutate Table A5: corrupt/blank AHW designation
    mutated_stores_6 = copy.deepcopy(base_stores)
    for r in mutated_stores_6["tables"].get("table_a5", []):
        if "atomic hydrogen" in r.get("process", ""):
            r["designation"] = None

    q_t5 = (
        "In Table A5 (Obsolete or Seldom Used Processes), how many obsolete processes are listed, "
        "and what are the designations for atomic hydrogen welding and forge welding?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_t5, planner, stores=mutated_stores_6)

    # 7. Mutate Figure B44/B45: remove official_title from Figure B44 summary
    mutated_stores_7 = copy.deepcopy(base_stores)
    sums = mutated_stores_7["annex_b_archetype4"]["figure_summaries"]
    if "Figure B44" in sums:
        sums["Figure B44"]["official_title"] = None

    q_b44 = (
        "Comparing the friction welding cycle diagrams in Figure B44 and Figure B45, what two "
        "mechanical variables are plotted on the vertical axes against time, and how do their rotational "
        "speed profiles differ during the deceleration phase?"
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(q_b44, planner, stores=mutated_stores_7)


def test_gate_5_adversarial_suite_all_pass():
    """Verify all 10 adversarial and boundary queries pass with exact refusal/refutation status."""
    q_file = BENCHMARK_DIR / "adversarial_questions.json"
    r_file = BENCHMARK_DIR / "rubric.json"
    assert q_file.exists() and r_file.exists()

    questions = json.loads(q_file.read_text(encoding="utf-8"))
    rubrics = json.loads(r_file.read_text(encoding="utf-8"))["rubrics"]

    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    for item in questions:
        qid = item["id"]
        query = item["query"]
        rubric = rubrics[qid]

        res = answer_whole_standard_question(query, planner, stores=stores)
        execution = res.get("execution", {})
        status = execution.get("status")
        answer = res.get("answer", "")

        assert status == rubric["expected_status"], (
            f"[{qid}] Expected status {rubric['expected_status']}, got {status}"
        )

        for req in rubric["required_elements"]:
            assert req.lower() in answer.lower(), (
                f"[{qid}] Missing required element '{req}' in answer: {answer}"
            )

        for forb in rubric["forbidden_elements"]:
            assert forb.lower() not in answer.lower(), (
                f"[{qid}] Forbidden hallucination '{forb}' found in answer: {answer}"
            )


def test_gate_5_paraphrase_robustness():
    """Verify that perturbed query phrasings resolve to identical targets and operations across 5 slices."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Slice 1: Table A4 paraphrase
    orig_q = (
        "What are the six standard suffix letter modifiers defined in Table A4 "
        "for the application mode of welding and allied processes, and what does the suffix -AU designate?"
    )
    para_q = (
        "In Table A4, name the 6 standard suffix modifiers for welding application mode "
        "and explain what -AU stands for."
    )
    orig_res = answer_whole_standard_question(orig_q, planner, stores=stores)
    para_res = answer_whole_standard_question(para_q, planner, stores=stores)
    assert orig_res["execution"]["status"] == "PASS" and para_res["execution"]["status"] == "PASS"
    assert "Automatic" in para_res["answer"] and "-AU" in para_res["answer"]

    # Slice 2: Figure A5 cold welding paraphrase
    orig_cw = (
        "In Figure A5 (Solid-State Welding Classification Chart), which specific process "
        "branches directly from Mechanical energy to Pressure and Deformation while "
        "completely bypassing the Thermal Source characteristic column?"
    )
    para_cw = (
        "Trace the Solid-State Welding chart Figure A5: which process goes straight "
        "from Mechanical to Pressure and Deformation without any thermal source?"
    )
    orig_cw_res = answer_whole_standard_question(orig_cw, planner, stores=stores)
    para_cw_res = answer_whole_standard_question(para_cw, planner, stores=stores)
    assert orig_cw_res["execution"]["status"] == "PASS" and para_cw_res["execution"]["status"] == "PASS"
    assert "CW" in para_cw_res["answer"] and "cold welding" in para_cw_res["answer"].lower()

    # Slice 3: Clause 4 glossary kerf definition query paraphrase
    orig_kerf = (
        "What is the official definition and figure cross-reference for the term 'kerf' "
        "in Clause 4 of AWS A3.0M/A3.0:2020?"
    )
    para_kerf = (
        "In Clause 4, how is kerf defined and which figure does its glossary entry cross-reference?"
    )
    orig_k_res = answer_whole_standard_question(orig_kerf, planner, stores=stores)
    para_k_res = answer_whole_standard_question(para_kerf, planner, stores=stores)
    assert orig_k_res["execution"]["status"] == "PASS" and para_k_res["execution"]["status"] == "PASS"
    assert "cutting process" in para_k_res["answer"].lower() and "Figure B41" in para_k_res["answer"]

    # Slice 4: Annex B waveform sub-intervals query paraphrase (Figure B49)
    orig_b49 = (
        "In Figure B49 (Single-Phase AC Waveform), what are the two vertical parameter traces "
        "plotted against the horizontal TIME axis, and what sub-intervals alternate within the WELD INTERVAL?"
    )
    para_b49 = (
        "According to Figure B49, list the vertical parameter traces plotted against TIME and "
        "name the repeating sub-intervals inside the WELD INTERVAL."
    )
    orig_b49_res = answer_whole_standard_question(orig_b49, planner, stores=stores)
    para_b49_res = answer_whole_standard_question(para_b49, planner, stores=stores)
    assert orig_b49_res["execution"]["status"] == "PASS" and para_b49_res["execution"]["status"] == "PASS"
    assert "HEAT TIME" in para_b49_res["answer"] and "COOL TIME" in para_b49_res["answer"]

    # Slice 5: Annex C/D nonstandard redirect paraphrase (stick electrode)
    orig_stick = (
        "In AWS A3.0M/A3.0:2020, what standard process term is the nonstandard designation 'stick electrode' "
        "redirected to, and in what historical edition or annex is this addressed?"
    )
    para_stick = (
        "Which standard term should be used instead of 'stick electrode', and what is the official letter designation?"
    )
    orig_s_res = answer_whole_standard_question(orig_stick, planner, stores=stores)
    para_s_res = answer_whole_standard_question(para_stick, planner, stores=stores)
    assert orig_s_res["execution"]["status"] == "PASS" and para_s_res["execution"]["status"] == "PASS"
    assert "shielded metal arc welding" in para_s_res["answer"].lower() or "SMAW" in para_s_res["answer"]


def test_gate_5_preflight_contract():
    """Verify that the whole-standard preflight contract passes under socket network blocking."""
    res = run_whole_standard_preflight(ROOT)
    assert res["status"] == "CLEAR_WHOLE_STANDARD_CONTRACT"
    assert res["network_calls"] == 0
    assert res["canonical_stores_verified"] == 7
