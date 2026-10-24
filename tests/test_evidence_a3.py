"""Focused unit tests for Figure A3 source-aware ingestion and deterministic QA."""
from pathlib import Path
import json
import pytest

from src.evidence_a3 import (
    ELEMENT,
    REGION,
    CROP_SHA256,
    _source,
    build_a3_graph,
    ingest,
    run_questions,
    answer_a3_query,
)

ROOT = Path(__file__).resolve().parents[1]


def test_a3_source_and_crop():
    source, geometry, image_bytes = _source(ROOT)
    assert source["edition_id"] == "AWS_A3.0_2020@2020"
    assert source["locator"]["element_id"] == ELEMENT
    assert source["locator"]["pdf_index"] == 88
    assert source["locator"]["printed_page"] == "76"
    assert source["locator"]["region"] == REGION
    assert source["crop_sha256"] == CROP_SHA256
    assert geometry["caption"] == "Figure A3—Joining Method Chart"
    assert "Weldinga" in geometry["native_text_inside_region"]
    assert "Footnote" not in geometry["caption"]


def test_a3_graph_structure():
    source, geometry, _ = _source(ROOT)
    graph = build_a3_graph(source, geometry)
    assert graph["schema_version"] == "a1-geometry-1.0"
    assert graph["root_id"] == "a3node:materials_joining"
    assert len(graph["nodes"]) == 11
    assert len(graph["edges"]) == 10

    # Epistemic checks
    edge_types = {e["type"] for e in graph["edges"]}
    assert "IS_A" not in edge_types
    assert "IS_A_PROCESS_VARIATION_OF" not in edge_types
    assert edge_types.issubset({"CHART_CONNECTOR", "ENCLOSES_ROW", "INDENTED_UNDER"})

    for qk, qv in graph["edge_qualifications"].items():
        assert qv["verification"] == "candidate"


def test_a3_deterministic_qa():
    graph_path = ROOT / "storage/evidence_v2/a3_ingest_001/final_projection/graph.json"
    questions_path = ROOT / "storage/evidence_v2/a3_ingest_001/evaluation/questions.json"
    assert graph_path.is_file()
    assert questions_path.is_file()

    payload = json.loads(questions_path.read_text(encoding="utf-8"))
    backend = run_questions(ROOT, graph_path, payload)
    assert backend["source_element"] == ELEMENT
    assert len(backend["answers"]) == 10
    assert backend["model_invocations"] == 0
    assert backend["external_calls"] == 0

    for item in backend["answers"]:
        res = item["result"]
        assert res["answer_outcome"] in ("graph_answer", "source_limit_abstention")
        assert len(res["answer"]) > 10
        assert len(res["record_evidence_catalog"]) >= 1
