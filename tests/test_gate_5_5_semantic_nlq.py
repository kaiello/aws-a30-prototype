"""Gate 5.5 Test Suite: Semantic Expansion, ID-Free NLQ Routing, Morphological Normalization,
and DeepSeek-V4.1-Flash-1017 NLQ Integration.

Verifies:
1. Frozen 15-question NLQ Benchmark: 15 / 15 (100.0%) pass rate across all 5 slices.
2. Semantic Expander Unit Contracts: Abbreviation bidirectional mapping, Annex C/D pivot,
   morphological normalization, ID-free target resolution, and SemanticExpansionTrace generation.
3. DeepSeek-V4.1 NLQ Replay Integration: Under strict offline socket blocking, replays ID-free
   waveform query, historical term multi-hop query, and out-of-scope refusal fixtures.
4. Complete 14/14 Cryptographic Lock: Verifies SHA-256 digests for 1 PDF, 6 historical Phase 0-3
   canonical stores, 1 Annex A holdout rubric, 3 Phase 5 hardening files, and 3 Phase 5.5 NLQ benchmark files.
   Also verifies the 3 new Gate 5.5 DeepSeek replay cassettes.
5. Anti-Drift & Anti-Overfitting Source Scans: Ensures zero hardcoded question IDs in src/ or eval/*.py,
   and zero forbidden benchmark literals in src/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from unittest.mock import patch
import pytest
from typing import Any, Dict

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    ROOT,
)
from src.semantic_nlq_expander import (
    get_semantic_expander,
    SemanticExpansionTrace,
)
from src.deepseek_v41_adapter import (
    DeepSeekV41PlannerAdapter,
    EPISTEMIC_TAG,
)
from eval.run_phase5_5_nlq import evaluate_nlq_benchmark

# Complete 14/14 Cryptographic Lock Registry
ALL_14_LOCKED_HASHES = {
    # 1 PDF Standard Source
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    # 6 Phase 0-3 Historical Canonical Stores
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
    # 1 Externalized Annex A Holdout Rubric
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json": "70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479",
    # 3 Phase 5 Hardening Benchmark Files
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json": "0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9",
    "storage/evidence_v2/phase5_hardening_001/rubric.json": "df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981",
    "storage/evidence_v2/phase5_hardening_001/results.json": "92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273",
    # 3 Phase 5.5 NLQ Benchmark Files
    "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json": "ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57",
    "storage/evidence_v2/phase5_5_nlq_001/rubric.json": "68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b",
    "storage/evidence_v2/phase5_5_nlq_001/results.json": "df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74",
}

GATE_5_5_REPLAY_HASHES = {
    "storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json": "ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2",
    "storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json": "e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e",
    "storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json": "0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621",
}


def _guard_network(*args, **kwargs):
    raise RuntimeError("Network blocked: offline execution contract violation")


def test_gate_5_5_nlq_benchmark_all_pass():
    """Verify that Gate 5.5 15-question NLQ benchmark achieves 15 / 15 (100.0%) pass rate."""
    payload = evaluate_nlq_benchmark(root=ROOT)
    assert payload["total_queries"] == 15, f"Expected 15 queries, got {payload['total_queries']}"
    assert payload["passed"] == 15, f"Expected 15 passed, got {payload['passed']}"
    assert payload["failed"] == 0, f"Expected 0 failed, got {payload['failed']}"
    assert payload["pass_rate_percent"] == 100.0, f"Expected 100.0% pass rate, got {payload['pass_rate_percent']}"

    # Verify that each result payload contains a valid SemanticExpansionTrace
    for r in payload["results"]:
        assert r["test_passed"] is True, f"Query {r['id']} failed"
        assert "semantic_expansion_trace" in r, f"Query {r['id']} missing expansion trace"
        trace = r["semantic_expansion_trace"]
        assert "raw_query" in trace
        assert "inferred_targets" in trace


def test_gate_5_5_semantic_expander_contracts():
    """Verify semantic expander contracts: abbreviation mapping, nonstandard/historical pivot,
    morphological normalization, and ID-free conceptual resolution."""
    stores = get_whole_standard_stores(ROOT)
    exp = get_semantic_expander(stores=stores, root=ROOT)

    # 1. Abbreviation Bidirectional Mapping
    trace_cw = exp.expand_query("What does CW stand for and how is it classified?")
    cw_alias = next((a for a in trace_cw.alias_expansions if a["surface_span"] == "CW"), None)
    assert cw_alias is not None, "CW abbreviation not detected"
    assert cw_alias["canonical_term"] == "cold welding"
    assert cw_alias["resolution_type"] == "ABBREVIATION"

    # 2. Nonstandard Term Pivot
    trace_stick = exp.expand_query("What is the preferred standard term for stick electrode?")
    stick_alias = next((a for a in trace_stick.alias_expansions if a["surface_span"] == "stick electrode"), None)
    assert stick_alias is not None, "stick electrode alias not detected"
    assert stick_alias["canonical_term"] == "covered electrode"
    assert stick_alias["resolution_type"] == "NONSTANDARD_TERM"

    # 3. Historical / Obsolete Process Pivot
    trace_ahw = exp.expand_query("Is atomic hydrogen welding an active process in the standard or is it obsolete?")
    ahw_alias = next((a for a in trace_ahw.alias_expansions if a["surface_span"] == "atomic hydrogen welding"), None)
    assert ahw_alias is not None, "atomic hydrogen welding alias not detected"
    assert ahw_alias["resolution_type"] == "HISTORICAL_TERM"

    # 4. Morphological Normalization
    trace_kerfs = exp.expand_query("How are kerfs defined in the standard?")
    kerf_alias = next((a for a in trace_kerfs.alias_expansions if a["surface_span"] == "kerfs"), None)
    assert kerf_alias is not None, "kerfs plural not normalized"
    assert kerf_alias["canonical_term"] == "kerf"
    assert kerf_alias["resolution_type"] == "MORPHOLOGICAL"

    # 5. ID-Free Annex A Table Resolution
    trace_suf = exp.expand_query("What are the standard letter suffixes for mechanized and automatic welding?")
    assert "Table A4" in trace_suf.inferred_targets["tables"], "Table A4 not conceptually inferred"

    # 6. ID-Free Annex B Waveform Resolution
    trace_pulse = exp.expand_query("Which waveform diagram illustrates upslope and downslope current intervals?")
    assert "Figure B53" in trace_pulse.inferred_targets["figures"], "Figure B53 not conceptually inferred"

    # 7. Generalized Out of Scope Detection
    oos_res = exp.check_out_of_scope("What preheat temperature and Charpy impact toughness are specified for structural steel?")
    assert oos_res is not None, "Out-of-scope query not detected"
    assert oos_res["status"] == "REFUSAL_OUT_OF_SCOPE"


def test_gate_5_5_deepseek_v41_nlq_replay_integration():
    """Verify DeepSeekV41PlannerAdapter replays Gate 5.5 NLQ fixtures under strict socket block."""
    stores = get_whole_standard_stores(ROOT)
    adapter = DeepSeekV41PlannerAdapter(root=ROOT)

    with patch("socket.socket", side_effect=_guard_network), \
         patch("socket.create_connection", side_effect=_guard_network):

        # 1. ID-free waveform query replay (Figure B53)
        q1 = "Which waveform diagram illustrates upslope and downslope current intervals for pulsed welding cycles?"
        res1 = answer_whole_standard_question(q1, planner=adapter, stores=stores)
        assert res1["execution"]["status"] == "PASS"
        assert "Figure B53" in res1["answer"]
        assert "UPSLOPE TIME" in res1["answer"]
        assert res1["plan"]["semantic_expansion_trace"] is not None

        # 2. Historical term multi-hop query replay (atomic hydrogen welding)
        q2 = "Is atomic hydrogen welding an active process in the standard or is it obsolete, and what was its letter designation?"
        res2 = answer_whole_standard_question(q2, planner=adapter, stores=stores)
        assert res2["execution"]["status"] == "PASS"
        assert "Table A5" in res2["answer"]
        assert "AHW" in res2["answer"]
        assert "obsolete" in res2["answer"].lower()

        # 3. Conversational out-of-scope refusal replay (mechanical properties)
        q3 = "What preheat temperature and Charpy impact toughness are specified for structural steel?"
        res3 = answer_whole_standard_question(q3, planner=adapter, stores=stores)
        assert res3["execution"]["status"] == "REFUSAL_OUT_OF_SCOPE"
        assert "outside the scope" in res3["answer"].lower()


def test_gate_5_5_all_locked_hashes():
    """Verify that all 14 project artifacts match locked SHA-256 digests."""
    assert len(ALL_14_LOCKED_HASHES) == 14, f"Expected 14 locked hashes, found {len(ALL_14_LOCKED_HASHES)}"

    for rel_path, expected_hash in ALL_14_LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Locked artifact missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Cryptographic lock violated for {rel_path}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )

    # Also verify the 3 Gate 5.5 DeepSeek replay cassettes
    for rel_path, expected_hash in GATE_5_5_REPLAY_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Replay fixture missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Replay hash violated for {rel_path}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )


def test_gate_5_5_anti_drift_and_anti_overfitting():
    """Verify that no benchmark question IDs are hardcoded in src/ or eval/*.py using full wildcard pattern,
    and assert zero forbidden benchmark literals across src/."""
    regex_pattern = r"QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+"
    forbidden_literals_re = re.compile(
        r"hyper-flux|laser-quantum|cryo-ionic|ASME\s+Section\s+IX|yield\s+strength|E7018",
        re.IGNORECASE,
    )

    targets = list((ROOT / "src").rglob("*.py")) + list((ROOT / "eval").glob("*.py"))
    violations = []
    for target in targets:
        text = target.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(regex_pattern, line):
                if "test_" in target.name or "regex_pattern" in line:
                    continue
                violations.append(f"{target.relative_to(ROOT)}:{i}: {line.strip()}")

    assert not violations, (
        f"Anti-drift violation! Found hardcoded question IDs in src/ or eval/*.py:\n"
        + "\n".join(violations)
    )

    # Scan src/ for forbidden benchmark literals
    src_targets = list((ROOT / "src").rglob("*.py"))
    literal_violations = []
    for target in src_targets:
        text = target.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if forbidden_literals_re.search(line):
                literal_violations.append(f"Forbidden literal in {target.relative_to(ROOT)}:{i}: {line.strip()}")

    assert not literal_violations, (
        f"Anti-overfitting violation! Found forbidden benchmark literals in src/:\n"
        + "\n".join(literal_violations)
    )
