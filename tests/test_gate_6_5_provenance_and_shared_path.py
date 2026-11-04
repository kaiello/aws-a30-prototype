"""tests/test_gate_6_5_provenance_and_shared_path.py - Verification Suite for Gate 6.5.

Enforces:
1. Exact Annex A coordinate mapping (Figures A1-A6 on printed pp. 75, 76, 76, 77, 78, 79; PDF 87, 88, 88, 89, 90, 91; never p. 80 / PDF 92).
2. Figure B53 vs B49 locator precedence and waveform pages (B44=148/160, B45=149/161, B53=157/169 with figure_b53:interval:upslope_and_downslope).
3. Table A3 GTAW body and top-level coordinate consistency (printed p. 73, PDF 85; never overwritten by 72/84).
4. Shared application execution path: /api/query (web.py/query.py), CLI, and answer_whole_standard_question return identical provenance and coordinates.
5. Independent evaluator rejects bad provenance (formula violation, excluded page, crop-locator mismatch, body-vs-metadata conflict).
6. Checkout cards and roadmap match questions.json and cryptographic hash locks.

Strict 100% offline socket isolation enforced.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import re
import socket
import pytest

ROOT = Path(__file__).resolve().parent.parent

from src.evidence_phase4_bakeoff import (
    ANNEX_A_PAGES,
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)
from src.query import run_query
from eval.run_phase6_3_blind_hardening import evaluate_blind_hardening_benchmark


@pytest.fixture(autouse=True)
def enforce_socket_isolation(monkeypatch):
    """Enforce strict offline execution by blocking non-loopback network socket operations."""
    original_connect = socket.socket.connect

    def forbidden(*args, **kwargs):
        raise RuntimeError("NETWORK_ACCESS_BLOCKED: Gate 6.5 tests must execute 100% offline")

    def guarded_connect(sock, address):
        caller = inspect.currentframe().f_back
        # Windows asyncio implements its private wakeup socketpair using loopback.
        if (caller.f_code.co_name == "_fallback_socketpair"
                and caller.f_globals.get("__name__") == "socket"
                and address[0] in {"127.0.0.1", "::1"}):
            return original_connect(sock, address)
        return forbidden()

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def test_gate_6_5_annex_a_exact_page_coordinates():
    """Verify Figures A1-A6 resolve to exact pages and never to excluded divider p. 80 / PDF 92."""
    expected_pages = {
        "Figure A1": {"printed_page": 75, "pdf_index": 87},
        "Figure A2": {"printed_page": 76, "pdf_index": 88},
        "Figure A3": {"printed_page": 76, "pdf_index": 88},
        "Figure A4": {"printed_page": 77, "pdf_index": 89},
        "Figure A5": {"printed_page": 78, "pdf_index": 90},
        "Figure A6": {"printed_page": 79, "pdf_index": 91},
    }

    cov = json.loads((ROOT / "storage/manifests/coverage_manifest.json").read_text(encoding="utf-8"))
    excluded_pages = set(cov["page_accounting"]["excluded_pdf_indices_1_based"])
    ingested_pages = set(cov["page_accounting"]["ingested_pdf_indices_1_based"])

    assert 92 in excluded_pages, "PDF index 92 must be classified as excluded blank section divider"

    for fig_id, exp in expected_pages.items():
        assert ANNEX_A_PAGES[fig_id] == exp, f"{fig_id} mapping mismatch in ANNEX_A_PAGES"
        assert exp["pdf_index"] - exp["printed_page"] == 12, f"{fig_id} formula violation"
        assert exp["pdf_index"] in ingested_pages, f"{fig_id} not in ingested pages"
        assert exp["pdf_index"] not in excluded_pages, f"{fig_id} erroneously in excluded pages"
        assert exp["printed_page"] != 80, f"{fig_id} must never be assigned to divider page 80"
        assert exp["pdf_index"] != 92, f"{fig_id} must never be assigned to divider PDF index 92"

    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Figure A5 cold welding query
    q_a5 = "In Figure A5, which specific process branches directly from Mechanical energy to Pressure and Deformation?"
    res_a5 = answer_whole_standard_question(q_a5, planner=planner, stores=stores)
    assert res_a5["printed_page"] == 78
    assert res_a5["pdf_index"] == 90
    assert res_a5["pdf_index"] != 92

    # Figure A6 energy sources query
    q_a6 = "How many different energy sources are there in Brazing and Soldering in Figure A6?"
    res_a6 = answer_whole_standard_question(q_a6, planner=planner, stores=stores)
    assert res_a6["printed_page"] == 79
    assert res_a6["pdf_index"] == 91
    assert res_a6["pdf_index"] != 92


def test_gate_6_5_b53_b49_and_b44_b45_provenance():
    """Verify Figure B53 vs B49 locator precedence and waveform page numbers."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Query with both upslope and downslope targeting Figure B53
    q_b53 = "In Figure B53, what welding cycle traces illustrate upslope and downslope intervals?"
    res_b53 = answer_whole_standard_question(q_b53, planner=planner, stores=stores)
    assert res_b53["printed_page"] == 157
    assert res_b53["pdf_index"] == 169
    assert res_b53["evidence_locator"] == "figure_b53:interval:upslope_and_downslope"
    assert "figure_b49" not in res_b53["evidence_locator"]
    assert res_b53["requires_diagram_crop"] is True
    assert "figure_b53" in Path(res_b53["crop_path"]).name.lower()

    # Query targeting Figure B44 (printed p. 148 / PDF 160)
    q_b44 = "Which waveform traces and parameters are illustrated in Figure B44 for direct-drive friction welding?"
    res_b44 = answer_whole_standard_question(q_b44, planner=planner, stores=stores)
    assert res_b44["printed_page"] == 148
    assert res_b44["pdf_index"] == 160

    # Query targeting Figure B45 (printed p. 149 / PDF 161)
    q_b45 = "Which waveform traces are illustrated in Figure B45 for inertia friction welding?"
    res_b45 = answer_whole_standard_question(q_b45, planner=planner, stores=stores)
    assert res_b45["printed_page"] == 149
    assert res_b45["pdf_index"] == 161


def test_gate_6_5_table_a3_gtaw_body_metadata_consistency():
    """Verify Table A3 GTAW returns printed p. 73 / PDF 85 without being overwritten by 72/84."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    q_a3 = "In Table A3, what is the letter designation for gas tungsten arc welding?"
    res_a3 = answer_whole_standard_question(q_a3, planner=planner, stores=stores)

    assert res_a3["printed_page"] == 73
    assert res_a3["pdf_index"] == 85
    assert res_a3["evidence_locator"] == "table_a3:row:GTAW"
    assert "printed p. 73" in res_a3["answer"] or "p. 73" in res_a3["answer"]
    assert "72" not in str(res_a3["printed_page"])


def test_gate_6_5_shared_web_cli_engine_path():
    """Verify /api/query (web/query.py) and answer_whole_standard_question share execution path and return identical provenance."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    test_queries = [
        "How does AWS A3.0 define kerf?",
        "What are the six standard suffix letter modifiers in Table A4?",
        "What are the applicable weld types for a T-Joint?",
        "What figure shows the position of beam, filler material, gun or torch?",
    ]

    for q in test_queries:
        # Engine execution
        ws_res = answer_whole_standard_question(q, planner=planner, stores=stores)

        # Query / Web execution via evidence_version="whole_standard"
        q_res = run_query(q, evidence_version="whole_standard")

        assert q_res["answer"] == ws_res["answer"]
        assert q_res["printed_page"] == ws_res["printed_page"]
        assert q_res["pdf_index"] == ws_res["pdf_index"]
        assert q_res["evidence_locator"] == ws_res["evidence_locator"]
        assert q_res["requires_diagram_crop"] == ws_res["requires_diagram_crop"]
        assert q_res.get("crop_path") == ws_res.get("crop_path")
        assert q_res["normative_provenance"] == ws_res["execution"].get("normative_provenance", [])
        assert q_res["planner_source"] in {"deterministic_planner", "live_deepseek", "deepseek_v4_1_replay_cassette", "synthetic_planner_fixture"}


def test_gate_6_5_evaluator_rejects_bad_provenance(monkeypatch):
    """Prove that injecting invalid coordinates, excluded pages, or mismatched crops fails evaluation."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # 1. Normal run passes 20/20
    normal_summary = evaluate_blind_hardening_benchmark(root=ROOT, write_results=False)
    assert normal_summary["passed"] == 20
    assert normal_summary["pass_rate"] == 100.0
    assert normal_summary["coordinate_provenance_accuracy"] == 100.0
    assert normal_summary["crop_locator_consistency"] == 100.0
    assert normal_summary["body_metadata_alignment"] == 100.0

    # 2. Inject coordinate formula violation (pdf - printed != 12)
    def _bad_coord_engine(*args, **kwargs):
        res = answer_whole_standard_question(*args, **kwargs)
        if "acetylene feather" in args[0].lower():
            res["pdf_index"] = 25  # p=6, pdf=25 => diff=19 != 12
        return res

    monkeypatch.setattr("eval.run_phase6_3_blind_hardening.answer_whole_standard_question", _bad_coord_engine)
    bad_summary1 = evaluate_blind_hardening_benchmark(root=ROOT, write_results=False)
    assert bad_summary1["passed"] == 19
    failed_q1 = next(r for r in bad_summary1["results"] if r["id"] == "G63-BLIND01")
    assert failed_q1["passed"] is False
    assert failed_q1["coord_match"] is False

    # 3. Inject excluded page violation (PDF index 92)
    def _excluded_page_engine(*args, **kwargs):
        res = answer_whole_standard_question(*args, **kwargs)
        if "acetylene feather" in args[0].lower():
            res["printed_page"] = 80
            res["pdf_index"] = 92  # excluded divider page
        return res

    monkeypatch.setattr("eval.run_phase6_3_blind_hardening.answer_whole_standard_question", _excluded_page_engine)
    bad_summary2 = evaluate_blind_hardening_benchmark(root=ROOT, write_results=False)
    assert bad_summary2["passed"] == 19
    failed_q2 = next(r for r in bad_summary2["results"] if r["id"] == "G63-BLIND01")
    assert failed_q2["passed"] is False
    assert failed_q2["coord_match"] is False

    # 4. Inject crop-locator figure mismatch (B53 crop with figure_b49 locator)
    def _crop_mismatch_engine(*args, **kwargs):
        res = answer_whole_standard_question(*args, **kwargs)
        if "position of beam" in args[0].lower():
            res["evidence_locator"] = "figure_b1:diagram_details"  # crop is B21, locator is B1
            if "execution" in res and isinstance(res["execution"], dict):
                res["execution"]["evidence_locator"] = "figure_b1:diagram_details"
        return res

    monkeypatch.setattr("eval.run_phase6_3_blind_hardening.answer_whole_standard_question", _crop_mismatch_engine)
    bad_summary3 = evaluate_blind_hardening_benchmark(root=ROOT, write_results=False)
    assert bad_summary3["passed"] == 19
    failed_q3 = next(r for r in bad_summary3["results"] if r["id"] == "G63-BLIND04")
    assert failed_q3["passed"] is False
    assert failed_q3["crop_match"] is False


def test_gate_6_5_checkout_cards_and_roadmap_match_questions_json():
    """Verify that GATE_6_4_CHECKOUT_CARD.md, ROADMAP.md, and goal.md match questions.json and all 51 hashes."""
    q_file = ROOT / "storage/evidence_v2/phase6_3_blind_hardening_001/questions.json"
    questions = json.loads(q_file.read_text(encoding="utf-8"))

    card_text = (ROOT / "GATE_6_4_CHECKOUT_CARD.md").read_text(encoding="utf-8")
    roadmap_text = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    goal_text = (ROOT / "goal.md").read_text(encoding="utf-8")

    # Verify questions are in checkout card and roadmap
    for item in questions:
        qid = item["id"]
        assert qid in card_text, f"{qid} missing in GATE_6_4_CHECKOUT_CARD.md"
        assert qid in roadmap_text, f"{qid} missing in ROADMAP.md"
        assert qid in goal_text, f"{qid} missing in goal.md"

    # Verify all 51 locked hashes match files on disk
    from tests.test_gate_6_4_comprehensive_enhancements import ALL_51_LOCKED_HASHES
    for rel_path, expected_hash in ALL_51_LOCKED_HASHES.items():
        p = ROOT / rel_path
        assert p.exists(), f"Locked artifact missing on disk: {rel_path}"
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}: actual {actual_hash} != expected {expected_hash}"
