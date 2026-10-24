"""Focused unit tests for Figure A4 (Fusion Welding Classification Chart) source-aware ingestion and deterministic QA."""
import json
from pathlib import Path
import pytest

from src.evidence_a4 import (
    ELEMENT,
    TITLE,
    PDF_INDEX,
    PRINTED_PAGE,
    REGION,
    CROP_SHA256,
    SPEC_A4,
    ingest,
    run_questions,
    answer_a4_query,
)
from src.archetype_decision_tree import authenticate_source, build_decision_tree_graph

ROOT = Path(__file__).resolve().parents[1]


def test_a4_source_and_crop():
    source, geometry, image_bytes = authenticate_source(ROOT, SPEC_A4)
    assert source["edition_id"] == "AWS_A3.0_2020@2020"
    assert source["locator"]["element_id"] == ELEMENT
    assert source["locator"]["pdf_index"] == PDF_INDEX
    assert source["locator"]["printed_page"] == PRINTED_PAGE
    assert source["locator"]["region"] == REGION
    assert source["crop_sha256"] == CROP_SHA256
    assert "Figure A4" in geometry["caption"]
    assert "Fusion Welding Classification Chart" in geometry["caption"]
    assert "AHW" in geometry["native_text_inside_region"]
    assert "MIAW" in geometry["native_text_inside_region"]
    assert "CAW" in geometry["native_text_inside_region"]


def test_a4_graph_structure():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A4)
    graph = build_decision_tree_graph(source, geometry, SPEC_A4)
    assert graph["schema_version"] == "a1-geometry-1.0"
    assert graph["root_id"] == "a4node:fusion_welding_root"
    assert len(graph["nodes"]) == 66
    assert len(graph["edges"]) == 42

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


def test_a4_characteristic_tree_and_multi_branch():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A4)
    graph = build_decision_tree_graph(source, geometry, SPEC_A4)
    nodes = {n["id"]: n for n in graph["nodes"]}

    # Energy sources
    assert "a4node:energy_electrical" in nodes
    assert "a4node:energy_chemical" in nodes

    # Thermal sources
    assert "a4node:thermal_arc" in nodes
    assert "a4node:thermal_resistance" in nodes
    assert "a4node:thermal_radiation" in nodes
    assert "a4node:thermal_conduction" in nodes
    assert "a4node:thermal_induction" in nodes
    assert "a4node:thermal_flame_contact" in nodes
    assert "a4node:thermal_solid_reactants" in nodes

    # Multi-branch processes
    egw_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "EGW"]
    assert len(egw_nodes) == 2  # Gas and Flux branches
    ebw_nodes = [n for n in graph["nodes"] if n.get("kind") == "process" and n.get("code") == "EBW"]
    assert len(ebw_nodes) == 2  # Vacuum and No Shielding branches


def test_a4_legend_and_source_anomalies():
    source, geometry, _ = authenticate_source(ROOT, SPEC_A4)
    graph = build_decision_tree_graph(source, geometry, SPEC_A4)

    # 23 Legend table entries
    legend_nodes = [n for n in graph["nodes"] if n.get("subtype") == "legend_row"]
    assert len(legend_nodes) == 23

    # MIAW underline formatting preserved
    miaw_legend = next(n for n in legend_nodes if n.get("code") == "MIAW")
    assert miaw_legend.get("underline") is True

    # AHW source anomaly: present in process circles but omitted from legend
    assert any(n.get("code") == "AHW" for n in graph["nodes"] if n.get("kind") == "process")
    assert not any(n.get("code") == "AHW" for n in legend_nodes)

    # Conduction source anomaly: unconnected leaf
    outgoing = {e["from"] for e in graph["edges"]}
    assert "a4node:thermal_conduction" not in outgoing


def test_a4_deterministic_qa():
    graph_path = ROOT / "storage/evidence_v2/a4_ingest_001/final_projection/graph.json"
    questions_path = ROOT / "storage/evidence_v2/a4_ingest_001/evaluation/questions.json"
    rubric_path = ROOT / "storage/evidence_v2/a4_ingest_001/evaluation/rubric.json"
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
