"""
tests/test_dual_provenance_is_a.py: Tier 1 & Tier 2 Exhaustive Property Tests for
Dual-Provenance IS_A Promotion Engine in AWS A3.0M/A3.0:2020.

Validates that:
1. Exactly 35 process variations are promoted to IS_A_PROCESS_VARIATION_OF (ACCEPTED).
2. Exactly 83 candidate layout parents remain CANDIDATE_LAYOUT_PARENT (CANDIDATE).
3. Exactly 0 uncorroborated IS_A promotions occur.
4. Every promoted process variation has dual provenance (Table A1 indentation + Clause 4 definition).
"""

import pytest

from src.evidence_is_a_promotion import (
    get_is_a_promotion_store,
    compute_dual_provenance_is_a,
)
from src.evidence_clause4_glossary import answer_clause4_query


@pytest.fixture(scope="module")
def dual_prov():
    return get_is_a_promotion_store()


def test_dual_provenance_counts(dual_prov):
    """Verify exact counts for promoted vs retained vs uncorroborated."""
    assert dual_prov["total_indented_rows"] == 118
    assert dual_prov["promoted_count"] == 35
    assert dual_prov["retained_candidate_count"] == 83
    assert dual_prov["uncorroborated_promotions_count"] == 0
    assert len(dual_prov["promoted_is_a"]) == 35
    assert len(dual_prov["retained_candidates"]) == 83


def test_exhaustive_promoted_variations_list(dual_prov):
    """Verify all 35 promoted process variations and their parent processes."""
    expected_pairs = {
        ("gas shielded flux cored arc welding", "flux cored arc welding"),
        ("self-shielded flux cored arc welding", "flux cored arc welding"),
        ("pulsed gas metal arc welding", "gas metal arc welding"),
        ("short circuiting gas metal arc welding", "gas metal arc welding"),
        ("pulsed gas tungsten arc welding", "gas tungsten arc welding"),
        ("series submerged arc welding", "submerged arc welding"),
        ("arc braze welding", "braze welding"),
        ("electron beam braze welding", "braze welding"),
        ("exothermic braze welding", "braze welding"),
        ("laser beam braze welding", "braze welding"),
        ("high vacuum electron beam welding", "electron beam welding"),
        ("medium vacuum electron beam welding", "electron beam welding"),
        ("nonvacuum electron beam welding", "electron beam welding"),
        ("pressure-controlled resistance welding", "resistance welding"),
        ("high-frequency seam welding", "resistance seam welding"),
        ("induction seam welding", "resistance seam welding"),
        ("mash seam welding", "resistance seam welding"),
        ("high-frequency upset welding", "upset welding"),
        ("induction upset welding", "upset welding"),
        ("ultrasonic soldering", "soldering"),
        ("hot isostatic pressure welding", "diffusion welding"),
        ("direct drive friction welding", "friction welding"),
        ("friction stir welding", "friction welding"),
        ("inertia friction welding", "friction welding"),
        ("air carbon arc cutting", "carbon arc cutting"),
        ("laser beam air cutting", "laser beam cutting"),
        ("laser beam evaporative cutting", "laser beam cutting"),
        ("laser beam inert gas cutting", "laser beam cutting"),
        ("laser beam oxygen cutting", "laser beam cutting"),
        ("oxyacetylene cutting", "oxyfuel gas cutting"),
        ("oxyhydrogen gas cutting", "oxyfuel gas cutting"),
        ("oxynatural gas cutting", "oxyfuel gas cutting"),
        ("oxypropane cutting", "oxyfuel gas cutting"),
        ("powder flame spraying", "flame spraying"),
        ("wire flame spraying", "flame spraying"),
    }

    actual_pairs = {(p["child_process"], p["parent_process"]) for p in dual_prov["promoted_is_a"]}
    assert actual_pairs == expected_pairs

    # Verify each promoted entry has valid dual provenance metadata
    for p in dual_prov["promoted_is_a"]:
        assert p["status"] == "ACCEPTED"
        assert p["predicate"] == "IS_A_PROCESS_VARIATION_OF"
        assert len(p["dual_provenance"]) == 2
        assert "Table A1" in p["dual_provenance"][0]
        assert "Clause 4" in p["dual_provenance"][1]
        assert len(p["corroborating_phrase"]) > 0
        assert len(p["corroborating_definition"]) > 0


def test_retained_candidates_remain_candidate(dual_prov):
    """Verify group root processes are NOT promoted and remain candidate layout observations."""
    retained = {(r["child_process"], r["parent_process"]) for r in dual_prov["retained_candidates"]}

    # Processes indented under group headers that are independent processes, not variations
    must_remain_candidate = [
        ("shielded metal arc welding", "arc welding"),
        ("gas metal arc welding", "arc welding"),
        ("flux cored arc welding", "arc welding"),
        ("gas tungsten arc welding", "arc welding"),
        ("plasma arc welding", "arc welding"),
        ("torch brazing", "brazing"),
        ("furnace brazing", "brazing"),
        ("induction brazing", "brazing"),
        ("flash welding", "resistance welding"),
        ("resistance spot welding", "resistance welding"),
        ("projection welding", "resistance welding"),
        ("cold welding", "solid-state welding"),
        ("explosion welding", "solid-state welding"),
        ("forge welding", "solid-state welding"),
        ("friction welding", "solid-state welding"),
        ("diffusion welding", "solid-state welding"),
    ]

    for child, parent in must_remain_candidate:
        assert (child, parent) in retained
        # Ensure not in promoted
        assert not any(p["child_process"] == child and p["parent_process"] == parent for p in dual_prov["promoted_is_a"])


def test_zero_uncorroborated_promotions_guard():
    """Verify that calling compute_dual_provenance_is_a enforces 0 uncorroborated promotions."""
    res = compute_dual_provenance_is_a()
    assert res["uncorroborated_promotions_count"] == 0
    assert len(res["promoted_is_a"]) == 35


def test_answer_dual_provenance_qa():
    """Verify natural language queries on dual-provenance promotions."""
    # GMAW-P
    ans = answer_clause4_query("Is GMAW-P a process variation of gas metal arc welding?")
    assert "Dual-Provenance Rule" in ans["answer"]
    assert "pulsed gas metal arc welding" in ans["answer"]
    assert "Table A1" in ans["answer"]
    assert "Clause 4" in ans["answer"]

    # FSW
    ans2 = answer_clause4_query("Is friction stir welding a variation of friction welding?")
    assert "friction stir welding" in ans2["answer"]
    assert "IS_A_PROCESS_VARIATION_OF" in ans2["answer"]

    # Overall count
    ans3 = answer_clause4_query("How many processes are promoted under dual provenance in A3.0?")
    assert "35" in ans3["answer"]
    assert "83" in ans3["answer"]
    assert "0 uncorroborated" in ans3["answer"]
