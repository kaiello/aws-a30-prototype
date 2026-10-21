"""Deterministic graph-QA contracts over an original toy chart, never AWS gold."""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import re
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from src.evidence_v2 import Evidence, evidence_id
from src.evidence_a1 import a1_source_identity_id
from evidence_v2_fixture import png_bytes


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Toy graph QA must not use a provider or network")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def toy_graph():
    def node(identifier, kind, label, code=None):
        value = {"id": identifier, "kind": kind, "label": label,
                 "region": [0.1, 0.1, 0.2, 0.4]}
        if code is not None:
            value["code"] = code
        return value
    def edge(source, target, kind):
        return {"from": source, "to": target, "type": kind,
                "region": [0.1, 0.1, 0.4, 0.8]}
    return {
        "schema_version": "a1-geometry-1.0", "root_id": "toy:root",
        "nodes": [node("toy:root", "root", "Original Toy Material Work"),
                  node("toy:alpha", "category", "ALPHA FAMILY"),
                  node("toy:beta", "category", "BETA FAMILY"),
                  node("toy:ribbon", "process", "Ribbon folding", "ZZR"),
                  node("toy:pulsed", "process", "Ribbon folding pulsed", "ZZRP"),
                  node("toy:foil", "process", "Foil binding", "ZZF"),
                  node("toy:squeeze", "process", "Squeeze joining", "ZZS")],
        "edges": [edge("toy:root", "toy:alpha", "CHART_CONNECTOR"),
                  edge("toy:root", "toy:beta", "CHART_CONNECTOR"),
                  edge("toy:alpha", "toy:ribbon", "ENCLOSES_ROW"),
                  edge("toy:alpha", "toy:pulsed", "ENCLOSES_ROW"),
                  edge("toy:alpha", "toy:foil", "ENCLOSES_ROW"),
                  edge("toy:beta", "toy:squeeze", "ENCLOSES_ROW"),
                  edge("toy:ribbon", "toy:pulsed", "INDENTED_UNDER")],
        "edge_qualifications": {
            "CHART_CONNECTOR": {"verification": "source_bound",
                "qualification": "Physical chart adjacency only; not a directed semantic subtype."},
            "ENCLOSES_ROW": {"verification": "source_bound",
                "qualification": "A row enclosed by this toy category; not a reviewed semantic subtype."},
            "INDENTED_UNDER": {"verification": "candidate",
                "qualification": "Layout candidate only; semantic parentage requires separate review."}},
        "region_space": "normalized_pdf_page_ymin_xmin_ymax_xmax",
        "native_text": "Original toy labels and codes only.",
        "limits": ["Single original toy image; no global process classification claim."]}


def answer(graph, query, **kwargs):
    engine = importlib.import_module("src.evidence_a1_graph_qa")
    return engine.answer_graph(graph, query, **kwargs)


def row_ids(result):
    return [row["id"] for row in result["rows"]]


def has_edge(result, source, target, kind):
    return any(edge["from"] == source and edge["to"] == target and edge["type"] == kind
               for edge in result["trace"]["selected_edges"])


def test_family_listing_contains_every_enclosed_row_once_including_nested_row(toy_graph):
    original = deepcopy(toy_graph)
    result = answer(toy_graph, "List all processes in ALPHA FAMILY in Figure A1.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert set(row_ids(result)) == {"toy:ribbon", "toy:pulsed", "toy:foil"}
    assert len(row_ids(result)) == len(set(row_ids(result))) == 3
    assert all(row["family_id"] == "toy:alpha" for row in result["rows"])
    assert {row["code"] for row in result["rows"]} == {"ZZR", "ZZRP", "ZZF"}
    assert has_edge(result, "toy:ribbon", "toy:pulsed", "INDENTED_UNDER")
    assert "candidate" in json.dumps(result).lower()
    assert result["semantic_validation"] is False
    assert toy_graph == original


def test_parent_family_lookup_retains_the_candidate_indentation_parent(toy_graph):
    result = answer(toy_graph, "Which family does Ribbon folding pulsed belong to in Figure A1?")
    assert result["answer_outcome"] == "graph_answer"
    selected = next(row for row in result["rows"] if row["id"] == "toy:pulsed")
    assert selected["family_id"] == "toy:alpha"
    assert "toy:ribbon" in selected["indent_parent_ids"]
    assert has_edge(result, "toy:ribbon", "toy:pulsed", "INDENTED_UNDER")
    assert "candidate" in json.dumps(result).lower()
    assert result["semantic_validation"] is False


def test_exact_acronym_expands_to_one_matching_row_without_prefix_collision(toy_graph):
    result = answer(toy_graph, "What does ZZRP stand for in Figure A1?")
    assert result["answer_outcome"] == "graph_answer"
    assert row_ids(result) == ["toy:pulsed"]
    assert result["rows"][0]["label"] == "Ribbon folding pulsed"
    assert result["rows"][0]["code"] == "ZZRP"
    assert "Ribbon folding pulsed" in result["answer"]


def test_exact_name_returns_only_its_printed_code(toy_graph):
    result = answer(toy_graph, "What is the abbreviation for Foil binding in Figure A1?")
    assert result["answer_outcome"] == "graph_answer"
    assert row_ids(result) == ["toy:foil"]
    assert "ZZF" in result["answer"]
    assert result["semantic_validation"] is False


def test_missing_node_does_not_become_a_global_negative_even_with_complete_chart(toy_graph):
    result = answer(toy_graph, "Is Moon stitching in ALPHA FAMILY in Figure A1?", complete_chart=True)
    assert result["answer_outcome"] in {"insufficient_evidence", "clarification_required", "capability_gap"}
    assert result.get("verdict", "not_established") == "not_established"
    assert not result["answer"].strip().lower().startswith("no")
    assert "does not exist" not in result["answer"].lower()
    assert result["semantic_validation"] is False


def test_foreign_positive_enclosure_can_support_only_a_chart_bounded_negative(toy_graph):
    result = answer(toy_graph, "Is Squeeze joining in ALPHA FAMILY in Figure A1?", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert result["verdict"] == "no"
    assert has_edge(result, "toy:beta", "toy:squeeze", "ENCLOSES_ROW")
    assert "BETA FAMILY" in result["answer"]
    assert "Figure A1" in result["answer"] or "chart" in result["answer"].lower()
    assert "never" not in result["answer"].lower()
    assert result["semantic_validation"] is False


def test_partial_graph_cannot_turn_absent_membership_into_a_negative(toy_graph):
    result = answer(toy_graph, "Is Squeeze joining in ALPHA FAMILY in Figure A1?")
    assert result["answer_outcome"] in {"insufficient_evidence", "clarification_required", "capability_gap"}
    assert result.get("verdict", "not_established") == "not_established"


@pytest.mark.parametrize("mutation", ["missing_endpoint", "unqualified_relation", "directed_cycle"])
def test_invalid_graph_structure_fails_closed(toy_graph, mutation):
    graph = deepcopy(toy_graph)
    if mutation == "missing_endpoint":
        graph["edges"][0]["to"] = "toy:missing"
    elif mutation == "unqualified_relation":
        graph["edges"][0]["type"] = "UNREVIEWED_SEMANTIC_IS_A"
    else:
        graph["edges"].append({"from": "toy:pulsed", "to": "toy:ribbon",
                               "type": "INDENTED_UNDER", "region": [0.1, 0.1, 0.4, 0.8]})
    with pytest.raises(ValueError):
        answer(graph, "List all processes in ALPHA FAMILY in Figure A1.", complete_chart=True)


def test_wrapper_preserves_one_image_edition_and_source_binding_without_models(toy_graph, tmp_path, monkeypatch):
    engine = importlib.import_module("src.evidence_a1_graph_qa")
    edition = "fixture:graph-qa:1@" + hashlib.sha256(b"Original toy graph QA edition").hexdigest()
    raw = png_bytes((147, 72, 184))
    path = tmp_path / "assets/toy-a1.png"
    path.parent.mkdir()
    path.write_bytes(raw)
    asset_hash = hashlib.sha256(raw).hexdigest()
    anchor = {"pdf_index": 0, "printed_label": "1", "order": 0, "role": "start", "region": None}
    source_id = a1_source_identity_id(edition, "figure:figure_a1", anchor, asset_hash)
    note_content = {"text": "Original toy chart applies only to the displayed toy image.",
                    "normative_status": "synthetic_scope_only", "notes": [], "qualifiers": [], "exceptions": []}
    note_locator = {"element_id": "Annex A", "order": 0}
    note = Evidence(evidence_id(edition, "note", note_locator, note_content), edition,
                    "note", note_locator, note_content, "synthetic")
    locator = {"element_id": "Figure A1", "canonical_element_id": "figure:figure_a1",
               "source_identity_id": source_id, "pdf_index": 0, "printed_page": "1", "order": 0,
               "region": None, "region_scope": "full_page"}
    content = {"caption": "Original toy chart", "asset_relpath": "assets/toy-a1.png",
               "asset_sha256": asset_hash, "source_identity_id": source_id, "media_type": "image/png",
               "single_image_scope": True, "continuation_orders": [0], "chart_graph": toy_graph,
               "required_evidence_ids": [note.evidence_id], "notes": [], "qualifiers": [], "exceptions": []}
    figure = Evidence(evidence_id(edition, "figure_region", locator, content), edition,
                      "figure_region", locator, content, "synthetic", required_ids=(note.evidence_id,))
    loads = []
    def toy_loader(root, query=None):
        loads.append((root, query))
        return [note, figure]
    monkeypatch.setattr(engine, "load_a1_evidence", toy_loader)
    payload = {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1", "questions": [
        {"id": "toy-list", "query": "List all processes in ALPHA FAMILY in Figure A1."},
        {"id": "toy-code", "query": "What does ZZRP stand for in Figure A1?"}]}
    result = engine.run_graph_qa(tmp_path, payload)
    assert result["model"] == result["provider"] == "NONE"
    assert result["model_invocation_count"] == 0
    assert result["harness_version"]
    assert len(result["answers"]) == 2
    assert loads
    for item, expected in zip(result["answers"], payload["questions"]):
        assert item["id"] == expected["id"] and item["query"] == expected["query"]
        assert item["answer_outcome"] == "graph_answer"
        assert item["source_identity_id"] == source_id
        assert item["edition_id"] == edition
        assert figure.evidence_id in item["evidence_ids"]
        assert re.fullmatch(r"[0-9a-f]{64}", item["graph_sha256"])
        assert item["support_state"] == "SOURCE_BOUND_CHART_LAYOUT"
        assert item["semantic_validation"] is False
    assert result["answers"][0]["graph_sha256"] == result["answers"][1]["graph_sha256"]
    assert path.read_bytes() == raw
