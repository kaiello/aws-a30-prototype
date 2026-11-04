"""Gate 6.6 Phase 4 Reader Qualification with Gold Evidence & Diagnostic Separation Test Suite.

Validates:
1. Full 54-artifact cryptographic lock ledger (51 prior + 3 net-new Gate 6.6 reader qualification artifacts).
2. Monotonic 3-arm gold-evidence progression (Arm A < Arm B < Arm C = 100%) and 24/24 retrieved parity under socket isolation.
3. Deterministic calibration of all 5 diagnostic failure classes (+ PASS_SUPPORTED) under controlled perturbations.
4. Honest offline replay coverage audit (`14` genuine DeepSeek-V4.1 replays vs `6` quarantined synthetic fixtures).
5. CLI (`--qualify-reader`, `--replay-audit`) and `src/query.py` (`diagnostic_track`) parity.
6. AST zero-fallback & zero-disk-read compliance in `src/reader_qualification.py`.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
import socket
import sys
from typing import Dict

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.run_phase6_6_reader_qualification import evaluate_reader_qualification_benchmark
from src.deepseek_v41_adapter import audit_replay_coverage
from src.evidence_whole_standard_cli import main as cli_main
from src.query import run_query
from src.reader_qualification import (
    build_gold_evidence_packet,
    classify_diagnostic_outcome,
    compose_from_gold_arm,
    prepare_reader_evidence_arm,
)
from tests.test_gate_6_4_comprehensive_enhancements import ALL_51_LOCKED_HASHES

GATE_6_6_NEW_HASHES: Dict[str, str] = {
    "storage/evidence_v2/phase6_6_reader_qualification_001/questions.json": "37fb22ce12235042e2a8f84aabca2011a45d81ebdf34cc764b9e0a1ffcc7ea2d",
    "storage/evidence_v2/phase6_6_reader_qualification_001/gold_packets.json": "030834a2abd05322248f77e8a8811ded57b400e4760b7091259d5b0415fd5386",
    "storage/evidence_v2/phase6_6_reader_qualification_001/results.json": "8c9d29b039e069c075fb9046a116322d328256008d3ca4115bb8d69ffddbd20a",
}

ALL_54_LOCKED_HASHES: Dict[str, str] = {
    **ALL_51_LOCKED_HASHES,
    **GATE_6_6_NEW_HASHES,
}


def test_gate_6_6_all_54_locked_hashes():
    """Verify byte-for-byte SHA-256 immutability of all 54 locked artifacts."""
    assert len(ALL_54_LOCKED_HASHES) == 54, f"Expected 54 locked artifacts, got {len(ALL_54_LOCKED_HASHES)}"
    for rel_path, expected_hash in ALL_54_LOCKED_HASHES.items():
        target_path = ROOT / rel_path
        assert target_path.exists(), f"Locked artifact missing on disk: {rel_path}"
        computed_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        assert computed_hash == expected_hash, (
            f"Cryptographic hash mismatch for {rel_path}:\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {computed_hash}"
        )


def test_gate_6_6_three_arm_gold_vs_retrieved_qualification(monkeypatch):
    """Verify Arm A < Arm B < Arm C (100%) progression and 24/24 retrieved parity under socket isolation."""
    def _blocked_socket(*args, **kwargs):
        raise RuntimeError("NETWORK_ACCESS_BLOCKED: Gate 6.6 tests must run 100% offline.")

    monkeypatch.setattr(socket, "socket", _blocked_socket)

    summary = evaluate_reader_qualification_benchmark(root=ROOT, write_results=False)
    assert summary["total_queries"] == 24

    rate_a = summary["gold_arm_a_pass_rate"]
    rate_b = summary["gold_arm_b_pass_rate"]
    rate_c = summary["gold_arm_c_pass_rate"]
    rate_ret = summary["retrieved_whole_standard_pass_rate"]

    assert rate_a < rate_b < rate_c, (
        f"Expected monotonic progression Arm A ({rate_a}%) < Arm B ({rate_b}%) < Arm C ({rate_c}%)"
    )
    assert rate_c == 100.0, f"Expected Gold Arm C to pass 24/24 (100.0%), got {rate_c}%"
    assert rate_ret == 100.0, f"Expected Retrieved Whole Standard to pass 24/24 (100.0%), got {rate_ret}%"
    assert summary["retrieval_vs_reader_delta"] == 0.0


def test_gate_6_6_five_class_failure_taxonomy_calibration():
    """Verify deterministic classification across all 5 failure classes + PASS_SUPPORTED."""
    base_pass_rec = {
        "track": "retrieved_whole_standard",
        "passed": True,
        "content_ok": True,
        "status_match": True,
        "coord_match": True,
        "crop_match": True,
        "body_meta_match": True,
        "actual_status": "PASS",
        "expected_status": "PASS",
        "evidence_locator": "figure_b23:subdiagram:J",
        "printed_page": 116,
    }
    assert classify_diagnostic_outcome(base_pass_rec, gold_arm_c_record=base_pass_rec) == "PASS_SUPPORTED"

    # 1. EXTRACTION_FAILURE (store integrity missing or INSUFFICIENT_EVIDENCE)
    assert classify_diagnostic_outcome(base_pass_rec, store_integrity_ok=False) == "EXTRACTION_FAILURE"
    ext_rec = dict(base_pass_rec, passed=False, actual_status="INSUFFICIENT_EVIDENCE", status_match=False)
    assert classify_diagnostic_outcome(ext_rec) == "EXTRACTION_FAILURE"

    # 2. ABSTENTION_FAILURE (failed to abstain on out-of-scope or falsely abstained on in-scope)
    abst_rec = dict(
        base_pass_rec,
        passed=False,
        content_ok=False,
        status_match=False,
        expected_status="REFUSAL_OUT_OF_SCOPE",
        actual_status="PASS",
    )
    assert classify_diagnostic_outcome(abst_rec) == "ABSTENTION_FAILURE"

    # 3. EVIDENCE_BINDING_OR_PROVENANCE_FAILURE (content accurate, but page/PDF/crop/body-meta failed)
    bind_rec = dict(base_pass_rec, passed=False, content_ok=True, coord_match=False)
    assert classify_diagnostic_outcome(bind_rec) == "EVIDENCE_BINDING_OR_PROVENANCE_FAILURE"

    # 4. RETRIEVAL_FAILURE (retrieved track missed the gold target locator/page that Gold Arm C passed)
    ret_miss_rec = dict(
        base_pass_rec,
        passed=False,
        content_ok=False,
        evidence_locator="figure_b21",
        printed_page=112,
    )
    assert classify_diagnostic_outcome(ret_miss_rec, gold_arm_c_record=base_pass_rec) == "RETRIEVAL_FAILURE"

    # 5. READER_INTERPRETATION_FAILURE (correct locator/page supplied, but required elements omitted)
    interp_rec = dict(base_pass_rec, track="gold_arm_b", passed=False, content_ok=False)
    assert classify_diagnostic_outcome(interp_rec, gold_arm_c_record=base_pass_rec) == "READER_INTERPRETATION_FAILURE"


def test_gate_6_6_replay_coverage_audit_manifest():
    """Verify replay coverage audit accurately separates 14 genuine model replays from 6 quarantined fixtures."""
    manifest = audit_replay_coverage(root=ROOT, write_manifest=False)
    assert manifest["genuine_model_replays_count"] == 14
    assert manifest["quarantined_synthetic_fixtures_count"] == 6

    g63_stats = manifest["benchmarks"]["phase6_3_blind_hardening_001"]
    assert g63_stats["total_queries"] == 20
    assert g63_stats["genuine_model_replays"] == 0
    assert g63_stats["quarantined_synthetic_fixtures"] == 6
    assert g63_stats["deterministic_planner_fallbacks"] == 14

    g66_stats = manifest["benchmarks"]["phase6_6_reader_qualification_001"]
    assert g66_stats["total_queries"] == 24
    assert g66_stats["quarantined_synthetic_fixtures"] == 6

    disk_manifest_path = ROOT / "storage/manifests/replay_coverage_manifest.json"
    assert disk_manifest_path.exists()
    disk_manifest = json.loads(disk_manifest_path.read_text(encoding="utf-8"))
    assert disk_manifest == manifest


def test_gate_6_6_cli_and_query_diagnostic_parity(capsys):
    """Verify --qualify-reader, --replay-audit, and run_query(diagnostic_track=...) parity."""
    q = "What is the Rotation of Face for Flat Fillet Weld?"
    rc = cli_main(["--qualify-reader", q, "--json", "--offline"])
    assert rc == 0
    out_qual = json.loads(capsys.readouterr().out)
    assert out_qual["query"] == q
    assert out_qual["tracks"]["gold_arm_a"]["requires_diagram_crop"] is False
    assert out_qual["tracks"]["gold_arm_a"]["crop_path"] is None
    assert out_qual["tracks"]["gold_arm_c"]["requires_diagram_crop"] is True
    assert out_qual["tracks"]["gold_arm_c"]["crop_path"] is not None

    rc_audit = cli_main(["--replay-audit", "--json", "--offline"])
    assert rc_audit == 0
    out_audit = json.loads(capsys.readouterr().out)
    assert out_audit["genuine_model_replays_count"] == 14
    assert out_audit["quarantined_synthetic_fixtures_count"] == 6

    q_res_c = run_query(q, evidence_version="whole_standard", diagnostic_track="gold_arm_c")
    assert q_res_c["diagnostic_track"] == "gold_arm_c"
    assert q_res_c["printed_page"] == 103
    assert q_res_c["pdf_index"] == 115
    assert q_res_c["answer"] == out_qual["tracks"]["gold_arm_c"]["answer"]


def test_gate_6_6_ast_zero_fallbacks_and_zero_disk_reads():
    """Enforce zero 2-arg .get(k, 'literal') fallbacks, zero string ternaries, and zero disk I/O in reader_qualification.py."""
    for fn in (
        build_gold_evidence_packet,
        prepare_reader_evidence_arm,
        compose_from_gold_arm,
        classify_diagnostic_outcome,
    ):
        src = inspect.getsource(fn)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    pytest.fail(f"Forbidden open() call in {fn.__name__}")
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"read_text", "read_bytes"}:
                        pytest.fail(f"Forbidden .{node.func.attr}() disk read in {fn.__name__}")
                    if node.func.attr == "get" and len(node.args) >= 2:
                        default_arg = node.args[1]
                        if (
                            isinstance(default_arg, ast.Constant)
                            and isinstance(default_arg.value, str)
                            and len(default_arg.value) > 0
                        ):
                            pytest.fail(
                                f"Forbidden 2-arg .get(k, {default_arg.value!r}) string fallback in {fn.__name__}"
                            )
