"""Unit and integration test suite for Annex A Tables A1–A5 (Gate 2E)."""
import json
from pathlib import Path
import pytest

from src.evidence_tables_a1_a5 import (
    SOURCE_PDF_SHA256,
    TABLE_METADATA,
    SOURCE_ANOMALIES,
    authenticate_pdf,
    build_annex_a_tables_store,
    extract_table_a1,
    extract_table_a2,
    extract_table_a3,
    extract_table_a4,
    extract_table_a5,
    parse_application_mode,
    answer_tables_query,
    run_tables_anti_drift_verifier,
    run_tables_evaluation,
)
import fitz

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data/AWS_A3.0_2020.pdf"
STORE_DIR = ROOT / "storage/evidence_v2/annex_a_tables_001"


def test_pdf_authentication():
    """Verify raw PDF matches immutable standard SHA-256."""
    assert authenticate_pdf(PDF_PATH) is True


def test_table_a1_hierarchy_and_epistemic_bounds():
    """Verify Table A1 extraction, 8 major groups, candidate indentation, and IS_A == 0."""
    with fitz.open(PDF_PATH) as doc:
        t1 = extract_table_a1(doc)
    assert len(t1) == 138

    # Verify no uncorroborated IS_A promotions
    for row in t1:
        assert row.get("is_a_promotion") is False

    # Check candidate layout parents exist
    candidate_rows = [r for r in t1 if r.get("parent_process")]
    assert len(candidate_rows) == 118

    # Check USW appears under both plastics welding and solid-state welding
    usw_entries = [r for r in t1 if r.get("designation") == "USW"]
    assert len(usw_entries) == 2
    parents = {r["parent_process"] for r in usw_entries}
    assert "plastics welding" in parents
    assert "solid-state welding" in parents


def test_table_a2_and_a3_row_counts_and_anomalies():
    """Verify Table A2 (133 rows) and Table A3 (134 rows) counts and anomalies."""
    with fitz.open(PDF_PATH) as doc:
        t2 = extract_table_a2(doc)
        t3 = extract_table_a3(doc)

    assert len(t2) == 133
    assert len(t3) == 134

    # Anomaly 1: OC-P typo in Table A2
    ocp_a2 = next(r for r in t2 if r["designation"] == "OC-P")
    ocp_a3 = next(r for r in t3 if r["designation"] == "OC-P")
    assert ocp_a2["process"] == "metal power cutting"
    assert ocp_a3["process"] == "metal powder cutting"

    # Anomaly 2: EW-PC typo in Table A2
    ewpc_a2 = next(r for r in t2 if r["designation"] == "EW-PC")
    rwpc_a3 = next(r for r in t3 if r["designation"] == "RW-PC")
    assert ewpc_a2["process"] == "pressure-controlled resistance welding"
    assert rwpc_a3["process"] == "pressure-controlled resistance welding"

    # Anomaly 3: AHW asymmetry
    ahw_a2 = [r for r in t2 if r["designation"] == "AHW"]
    ahw_a3 = [r for r in t3 if r["designation"] == "AHW"]
    assert len(ahw_a2) == 0
    assert len(ahw_a3) == 1
    assert ahw_a3[0]["process"] == "atomic hydrogen welding"

    # Anomaly 4: AB collision
    ab_a2 = next(r for r in t2 if r["designation"] == "AB")
    ab_a3 = next(r for r in t3 if r["designation"] == "AB")
    assert ab_a2["process"] == "adhesive bonding"
    assert ab_a3["process"] == "adhesive bonding"


def test_table_a4_application_mode_suffixes_and_parsing():
    """Verify Table A4 suffixes, normative note, and code combination parsing."""
    with fitz.open(PDF_PATH) as doc:
        t4 = extract_table_a4(doc)

    assert len(t4["suffixes"]) == 6
    suffixes = {s["suffix"]: s["mode"] for s in t4["suffixes"]}
    assert suffixes["-AD"] == "Adaptive control"
    assert suffixes["-AU"] == "Automatic"
    assert suffixes["-MA"] == "Manual"
    assert suffixes["-ME"] == "Mechanized"
    assert suffixes["-RO"] == "Robotic"
    assert suffixes["-SA"] == "Semiautomatic"

    assert "XXXX-YY" in t4["note"]

    p1 = parse_application_mode("GTAW-MA")
    assert p1["valid"] is True
    assert p1["base_code"] == "GTAW"
    assert p1["suffix"] == "-MA"
    assert p1["application_mode"] == "Manual"

    p2 = parse_application_mode("GMAW-AU")
    assert p2["valid"] is True
    assert p2["base_code"] == "GMAW"
    assert p2["suffix"] == "-AU"
    assert p2["application_mode"] == "Automatic"


def test_table_a5_obsolete_processes():
    """Verify Table A5 obsolete process extraction and firecracker welding designation omission."""
    with fitz.open(PDF_PATH) as doc:
        t5 = extract_table_a5(doc)

    assert len(t5) == 13
    for r in t5:
        assert r["status"] == "obsolete"

    firecracker = next(r for r in t5 if r["process"] == "firecracker welding")
    assert firecracker["designation"] is None


def test_cross_annex_a_figure_joins():
    """Verify Table A1 designations join to Figures A1–A6."""
    with fitz.open(PDF_PATH) as doc:
        t1 = extract_table_a1(doc)

    desigs = {r["designation"] for r in t1 if r["designation"]}
    # Critical processes from Figures A4, A5, A6 must all be present in Table A1
    fig_a4_codes = {"SMAW", "GMAW", "GTAW", "SAW", "PAW", "OAW"}
    fig_a5_codes = {"CW", "DFW", "EXW", "FOW", "FRW", "FSW", "HPW", "USW"}
    fig_a6_codes = {"TB", "FB", "IB", "RB", "DB", "DFB", "WS", "DS", "INS", "USS"}

    for code in fig_a4_codes | fig_a5_codes | fig_a6_codes:
        assert code in desigs, f"Code {code} missing from Table A1"


def test_tables_anti_drift_verifier():
    """Run full 4-check anti-drift loop on Annex A Tables A1–A5."""
    res = run_tables_anti_drift_verifier(ROOT, STORE_DIR, skip_preflight=False)
    assert res["status"] == "PASS"
    assert res["checks"]["check1_geometry_and_title"]["status"] == "PASS"
    assert res["checks"]["check2_epistemic_tier_guard"]["status"] == "PASS"
    assert res["checks"]["check2_epistemic_tier_guard"]["is_a_promotions"] == 0
    assert res["checks"]["check3_table_cross_check"]["status"] == "PASS"
    assert res["checks"]["check4_shared_preflight"]["status"] == "PASS"


def test_deterministic_evaluation_suite():
    """Verify all 15 deterministic questions pass."""
    q_path = STORE_DIR / "evaluation/questions.json"
    out_path = STORE_DIR / "evaluation/answers.json"
    res = run_tables_evaluation(ROOT, STORE_DIR, q_path, out_path)
    assert res["total_questions"] == 15
    assert res["passed"] == 15
    assert res["failed"] == 0
