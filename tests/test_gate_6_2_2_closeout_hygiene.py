"""Gate 6.2.2 Test Suite: Closeout Hygiene, Google Drive 42-Artifact Mirror Parity & Doc Parity.

Verifies:
1. Complete reviewable file collection in sync_drive_mirror.py (all 41 non-PDF locked artifacts + scripts).
2. Clean genus-scoped cross-reference expansion (isolated single-subtype cross-references without parent leakage).
3. 20/20 PASS on both holdout_001 and holdout_002 across deterministic and Slice 5 replay execution modes.
4. Store-driven compound_designation_and_historical degradation on store mutation.
5. In-repo docs and checkout cards hash parity and pagination accuracy.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    _exec_expand_cross_references,
)
from src.sync_drive_mirror import collect_reviewable_files
from eval.run_phase6_2_generalization_holdout import evaluate_generalization_holdout_benchmark
from tests.test_gate_6_2_1_multi_action_closure import ALL_42_LOCKED_HASHES


def test_gate_6_2_2_sync_drive_mirror_collects_all_locked_review_artifacts():
    """Verify collect_reviewable_files captures all 41 non-PDF locked artifacts and scripts."""
    collected = collect_reviewable_files(ROOT)
    rel_collected = {p.relative_to(ROOT).as_posix() for p in collected}

    # All non-PDF locked artifacts must be present
    missing_locked = []
    for rel_path in ALL_42_LOCKED_HASHES:
        if rel_path.endswith(".pdf"):
            continue
        if rel_path not in rel_collected:
            missing_locked.append(rel_path)

    assert not missing_locked, f"collect_reviewable_files missed locked artifacts: {missing_locked}"

    # Verify key scripts are collected
    assert "scripts/build_gate_6_bundle.py" in rel_collected
    assert "storage/manifests/coverage_manifest.json" in rel_collected
    assert "storage/manifests/latency_benchmark.json" in rel_collected
    assert "storage/evidence_v2/phase6_2_generalization_holdout_002/results.json" in rel_collected


def test_gate_6_2_2_single_subtype_cross_reference_isolation():
    """Verify single-subtype query returns only its direct cross-references without parent leakage."""
    stores = get_whole_standard_stores(ROOT)

    # 1. Single subtype query: bonded flux
    res_bonded = _exec_expand_cross_references(
        "bonded flux",
        "In Clause 4, what related terms are cross-referenced from bonded flux?",
        stores=stores,
    )
    assert res_bonded["status"] == "PASS"
    elements = res_bonded["elements_present"]
    # Must contain agglomerated flux and fused flux
    assert "agglomerated flux" in elements
    assert "fused flux" in elements
    # Must NOT leak general flux see-alsos (brazing flux, soldering flux, welding flux)
    assert "brazing flux" not in elements
    assert "soldering flux" not in elements
    assert "welding flux" not in elements

    # 2. Query asking for genus category: what flux terms are cross-referenced from agglomerated flux
    res_agglom = _exec_expand_cross_references(
        "agglomerated flux",
        "In Clause 4 of AWS A3.0, what flux terms are cross-referenced from agglomerated flux?",
        stores=stores,
    )
    assert res_agglom["status"] == "PASS"
    elements_agglom = res_agglom["elements_present"]
    # Must contain both direct (bonded flux, fused flux) and genus flux (flux, brazing flux, etc.)
    assert "agglomerated flux" in elements_agglom
    assert "bonded flux" in elements_agglom
    assert "fused flux" in elements_agglom
    assert "flux" in elements_agglom
    assert "brazing flux" in elements_agglom


def test_gate_6_2_2_both_holdout_benchmarks_pass_in_both_modes(monkeypatch):
    """Verify holdout_001 and holdout_002 achieve 20/20 PASS across deterministic and replay modes."""
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls blocked during holdout evaluation")
    monkeypatch.setattr(socket, "socket", block_socket)

    d1 = ROOT / "storage/evidence_v2/phase6_2_generalization_holdout_001"
    d2 = ROOT / "storage/evidence_v2/phase6_2_generalization_holdout_002"

    # Holdout 001: deterministic mode
    res_h1_det = evaluate_generalization_holdout_benchmark(root=ROOT, output_dir=d1, write_results=False, use_replay_for_slice5=False)
    assert res_h1_det["passed_count"] == 20
    assert res_h1_det["gate_status"] == "PASS"

    # Holdout 002: deterministic mode
    res_h2_det = evaluate_generalization_holdout_benchmark(root=ROOT, output_dir=d2, write_results=False, use_replay_for_slice5=False)
    assert res_h2_det["passed_count"] == 20
    assert res_h2_det["gate_status"] == "PASS"

    # Holdout 002: replay mode for Slice 5
    res_h2_rep = evaluate_generalization_holdout_benchmark(root=ROOT, output_dir=d2, write_results=False, use_replay_for_slice5=True)
    assert res_h2_rep["passed_count"] == 20
    assert res_h2_rep["gate_status"] == "PASS"


def test_gate_6_2_2_compound_and_historical_store_driven_mutation():
    """Verify compound_designation_and_historical delegates to live stores and raises on mutation."""
    base_stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # 1. Normal execution
    query = "How does obsolete atomic hydrogen welding compare to active GMAW-P-SA in AWS A3.0?"
    res = answer_whole_standard_question(query, planner, stores=base_stores)
    assert res["execution"]["status"] == "PASS"
    assert "atomic hydrogen welding" in res["execution"]["elements_present"]
    assert "GMAW-P-SA" in res["execution"]["elements_present"]
    assert "Table A5" in res["execution"]["elements_present"]
    assert "Table A1" in res["execution"]["elements_present"]
    assert "Table A4" in res["execution"]["elements_present"]

    # 2. Mutation: Table A5 empty
    mut_a5 = copy.deepcopy(base_stores)
    mut_a5["tables"]["table_a5"] = []
    # If not in Table A5, it falls back to Clause 4 glossary. If glossary is also emptied:
    mut_a5["glossary"]["entries"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(query, planner, stores=mut_a5)

    # 3. Mutation: Table A1 empty
    mut_a1 = copy.deepcopy(base_stores)
    mut_a1["tables"]["table_a1"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(query, planner, stores=mut_a1)

    # 4. Mutation: Table A4 suffixes empty
    mut_a4 = copy.deepcopy(base_stores)
    mut_a4["tables"]["table_a4"]["suffixes"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question(query, planner, stores=mut_a4)


def test_gate_6_2_2_docs_and_checkout_cards_hash_and_version_parity():
    """Verify documentation and checkout cards maintain exact hash and pagination parity."""
    # 1. Check GATE_6_2_CHECKOUT_CARD.md
    c62_text = (ROOT / "GATE_6_2_CHECKOUT_CARD.md").read_text(encoding="utf-8")
    assert "(p. 5 for groove, p. 6 for fillet)" not in c62_text
    assert "alphabetical order: `1F`–`4F` and `1G`–`3G` on printed p. 5" in c62_text or "alphabetical order: 1F–4F and 1G–3G on printed p. 5" in c62_text

    # 2. Check holdout_001 hashes in GATE_6_2_1_CHECKOUT_CARD.md
    c621_text = (ROOT / "GATE_6_2_1_CHECKOUT_CARD.md").read_text(encoding="utf-8")
    expected_h36 = ALL_42_LOCKED_HASHES["storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json"]
    expected_h37 = ALL_42_LOCKED_HASHES["storage/evidence_v2/phase6_2_generalization_holdout_001/results.json"]
    assert expected_h36 in c621_text
    assert expected_h37 in c621_text

    # 3. Check goal.md and docs/goal.md
    goal_text = (ROOT / "goal.md").read_text(encoding="utf-8")
    docs_goal_text = (ROOT / "docs/goal.md").read_text(encoding="utf-8")
    assert "v1.6.1-ner-semantic-graph" not in goal_text
    assert "v1.6.1-ner-semantic-graph" not in docs_goal_text
    assert any(tag in goal_text for tag in ["v1.6.2.1-multi-action-closure", "v1.6.2.2-closeout-hygiene", "v1.6.3-blind-hardening"])
    assert any(tag in docs_goal_text for tag in ["v1.6.2.1-multi-action-closure", "v1.6.2.2-closeout-hygiene", "v1.6.3-blind-hardening"])
