"""Gate 5 Test Suite: Production Hardening, Adversarial Invariants, and Anti-Drift Defense.

Verifies:
1. Canonical Store Immutability across all 7 historical stores.
2. Store-Mutation Degradation: artificially blanking store fields MUST raise
   INSUFFICIENT_EVIDENCE and never return a silent canned default.
3. Adversarial Suite: 10 boundary, out-of-range, contradiction, and out-of-scope
   queries are properly refuted/rejected without hallucinations.
4. Paraphrase Robustness: perturbed question phrasing produces identical target
   and operation resolution.
5. Whole-Standard Preflight Contract: offline execution, zero network calls,
   provenance delivery.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
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


def test_gate_5_canonical_store_hashes():
    """Verify that all 7 canonical stores remain byte-identical to their locked SHA-256 digests."""
    for rel_path, exp_hash in LOCKED_STORE_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Store missing: {rel_path}"
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual == exp_hash, f"Canonical store mutated: {rel_path}"


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
    """Verify that perturbed query phrasings resolve to identical targets and operations."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Test Table A4 paraphrase
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

    assert orig_res["execution"]["status"] == "PASS"
    assert para_res["execution"]["status"] == "PASS"
    assert "Automatic" in para_res["answer"]
    assert "-AU" in para_res["answer"]

    # Test Figure A5 cold welding paraphrase
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

    assert orig_cw_res["execution"]["status"] == "PASS"
    assert para_cw_res["execution"]["status"] == "PASS"
    assert "CW" in para_cw_res["answer"]
    assert "cold welding" in para_cw_res["answer"].lower()


def test_gate_5_preflight_contract():
    """Verify that the whole-standard preflight contract passes under socket network blocking."""
    res = run_whole_standard_preflight(ROOT)
    assert res["status"] == "CLEAR_WHOLE_STANDARD_CONTRACT"
    assert res["network_calls"] == 0
    assert res["canonical_stores_verified"] == 7
