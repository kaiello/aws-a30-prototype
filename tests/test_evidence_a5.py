"""Focused unit tests for Figure A5 (Solid-State Welding Classification Chart) source-aware ingestion and deterministic QA."""
import json
from pathlib import Path
import pytest

from src.evidence_a5 import (
    ELEMENT,
    TITLE,
    PDF_INDEX,
    PRINTED_PAGE,
    REGION,
    CROP_SHA256,
    SPEC_A5,
    run_questions,
    answer_a5_query,
)
from src.archetype_decision_tree import authenticate_source, build_decision_tree_graph

ROOT = Path(__file__).resolve().parents[1]


def test_a5_source_and_crop():
    source, geometry, image_bytes = authenticate_source(ROOT, SPEC_A5)
    assert source["edition_id"] == "AWS_A3.0_2020@2020"
    assert source["locator"]["element_id"] == ELEMENT
    assert source["locator"]["pdf_index"] == PDF_INDEX
    assert source["locator"]["printed_page"] == PRINTED_PAGE
    assert source["locator"]["region"] == REGION
    assert source["crop_sha256"] == CROP_SHA256
    assert "Figure A5" in geometry["caption"]
    assert "Solid-State Welding Classification Chart" in geometry["caption"]
    assert "CW" in geometry["native_text_inside_region"]
    assert "USW" in geometry["native_text_inside_region"]
    assert "DFW" in geometry["native_text_inside_region"]


def test_a5_graph_structure():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A5)
    graph = build_decision_tree_graph(source, geometry, SPEC_A5)
    assert graph["schema_version"] == "a1-geometry-1.0"
    assert graph["root_id"] == "a5node:solid_state_welding_root"
    assert len(graph["nodes"]) == 68
    assert len(graph["edges"]) == 66

    # Epistemic checks: dual-layer verification and 0 IS_A promotions
    edge_types = {e["type"] for e in graph["edges"]}
    assert "IS_A" not in edge_types
    assert "IS_A_PROCESS_VARIATION_OF" not in edge_types
    assert edge_types.issubset({"CHART_CONNECTOR", "ENCLOSES_ROW", "INDENTED_UNDER"})

    assert graph["edge_qualifications"]["CHART_CONNECTOR"]["verification"] == "source_bound"
    assert graph["edge_qualifications"]["ENCLOSES_ROW"]["verification"] == "source_bound"
    assert graph["edge_qualifications"]["INDENTED_UNDER"]["verification"] == "candidate"
    assert all(n["evidence"]["verification"] == "source_bound" for n in graph["nodes"])
    assert all(
        e["evidence"]["verification"] == "source_bound"
        for e in graph["edges"]
        if e["type"] in ("CHART_CONNECTOR", "ENCLOSES_ROW")
    )


def test_a5_characteristic_tree_and_multi_branch():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A5)
    graph = build_decision_tree_graph(source, geometry, SPEC_A5)
    nodes = {n["id"]: n for n in graph["nodes"]}

    # Energy sources (3: Electrical, Chemical, Mechanical)
    assert "a5node:energy_electrical" in nodes
    assert "a5node:energy_chemical" in nodes
    assert "a5node:energy_mechanical" in nodes

    # Thermal sources
    assert "a5node:thermal_elec_radiation" in nodes
    assert "a5node:thermal_elec_induction" in nodes
    assert "a5node:thermal_elec_resistance" in nodes
    assert "a5node:thermal_chem_flame" in nodes
    assert "a5node:thermal_chem_radiation" in nodes
    assert "a5node:thermal_chem_explosion" in nodes
    assert "a5node:thermal_mech_friction" in nodes

    # Multi-branch processes
    hpw_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "HPW"]
    assert len(hpw_nodes) == 2  # Gas and Vacuum
    dfw_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "DFW"]
    assert len(dfw_nodes) == 3  # Elec Gas, Elec Vac, Chem Gas
    fow_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "FOW"]
    assert len(fow_nodes) == 2  # Elec and Chem
    row_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "ROW"]
    assert len(row_nodes) == 2  # Elec and Chem
    cew_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "CEW"]
    assert len(cew_nodes) == 2  # Elec and Chem
    iw_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "IW"]
    assert len(iw_nodes) == 2  # Gas and Vacuum


def test_a5_legend_and_source_anomalies():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A5)
    graph = build_decision_tree_graph(source, geometry, SPEC_A5)

    # 15 Legend table entries
    legend_nodes = [n for n in graph["nodes"] if n.get("subtype") == "legend_row"]
    assert len(legend_nodes) == 15

    # CW direct column hop (skipping Thermal Source) vs USW (via Friction)
    cw_node = next(n for n in graph["nodes"] if n.get("code") == "CW")
    assert "[No Thermal Source Box]" in cw_node["path_summary"]
    assert "Pressure Deformation" in cw_node["path_summary"]

    usw_node = next(n for n in graph["nodes"] if n.get("code") == "USW")
    assert "Friction" in usw_node["path_summary"]
    assert "Pressure" in usw_node["path_summary"]
    assert "[No Thermal Source Box]" not in usw_node["path_summary"]

    frw_node = next(n for n in graph["nodes"] if n.get("code") == "FRW")
    assert "Friction" in frw_node["path_summary"]
    assert "Pressure Deformation" in frw_node["path_summary"]

    exw_node = next(n for n in graph["nodes"] if n.get("code") == "EXW")
    assert "Deformation" in exw_node["path_summary"]

    # Scoped Radiation boxes: two distinct nodes
    rad_nodes = [n for n in graph["nodes"] if n.get("label") == "Radiation"]
    assert len(rad_nodes) == 2
    rad_parents = {n.get("energy_source") for n in rad_nodes}
    assert rad_parents == {"Electrical", "Chemical"}


def test_a5_deterministic_qa():
    graph_path = ROOT / "storage/evidence_v2/a5_ingest_001/final_projection/graph.json"
    questions_path = ROOT / "storage/evidence_v2/a5_ingest_001/evaluation/questions.json"
    rubric_path = ROOT / "storage/evidence_v2/a5_ingest_001/evaluation/rubric.json"
    assert graph_path.is_file()
    assert questions_path.is_file()
    assert rubric_path.is_file()

    payload = json.loads(questions_path.read_text(encoding="utf-8"))
    rubric = json.load(rubric_path.open(encoding="utf-8"))["questions"]
    rubric_map = {r["id"]: r for r in rubric}

    backend = run_questions(ROOT, graph_path, payload)
    assert backend["source_element"] == ELEMENT
    assert len(backend["answers"]) == 10
    assert backend["model_invocations"] == 0
    assert backend["external_calls"] == 0

    for item in backend["answers"]:
        qid = item["question_id"]
        res = item["result"]
        rule = rubric_map[qid]
        assert res["answer_outcome"] in ("graph_answer", "source_limit_abstention")
        assert len(res["answer"]) > 10
        assert len(res["record_evidence_catalog"]) >= 1

        # Content & Delivery Verification
        content_ok = all(elem.casefold() in res["answer"].casefold() for elem in rule["required_elements"])
        assert content_ok, f"{qid} failed content: missing {[e for e in rule['required_elements'] if e.casefold() not in res['answer'].casefold()]}"
        assert res["answer_outcome"] == rule["expected_outcome"], f"{qid} failed delivery outcome"


def test_a5_anti_drift_loop():
    from src.archetype_decision_tree import run_anti_drift_verifier
    receipt = run_anti_drift_verifier(ROOT, SPEC_A5)
    assert receipt["status"] == "PASS"
    assert receipt["element"] == "Figure A5"
    checks = receipt["checks"]
    assert checks["check1_geometry_and_title"]["status"] == "PASS"
    assert checks["check1_geometry_and_title"]["title_verified_in_list_of_figures"] is True
    assert checks["check1_geometry_and_title"]["vector_connectors_verified"] is True
    assert checks["check2_epistemic_tier_guard"]["status"] == "PASS"
    assert checks["check2_epistemic_tier_guard"]["accepted"] == 127
    assert checks["check2_epistemic_tier_guard"]["is_a_promotions"] == 0
    assert checks["check3_table_a3_cross_check"]["status"] == "PASS"
    assert checks["check3_table_a3_cross_check"]["undeclared_mismatches_count"] == 0
    assert checks["check4_shared_preflight"]["status"] == "PASS"
    assert checks["check4_shared_preflight"]["preflight_status"] == "CLEAR_REAL_ENTRY_CONTRACT"
    assert checks["check4_shared_preflight"]["new_model_calls"] == 0

