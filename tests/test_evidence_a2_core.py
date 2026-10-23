"""Synthetic A2-compatible contracts; no AWS labels, questions or source facts."""
from copy import deepcopy
import hashlib
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from test_evidence_a1_graph_qa import toy_graph, no_network
from src.evidence_a1 import (
    bind_a1_graph_evidence, bind_chart_graph_evidence,
    validate_a1_graph_evidence, validate_chart_graph_evidence,
)
from src.evidence_a1_graph_qa import _GraphView, _graph_index, answer_graph
from src.evidence_a1_planner import _source_context_spans, plan_graph_query


def a2_binding():
    return {
        "edition_id": "fixture:joining@" + "0" * 64,
        "source_identity_id": "source2:toy-a2",
        "locator": {"element_id": "Figure A2", "canonical_element_id": "figure:figure_a2",
            "source_identity_id": "source2:toy-a2", "pdf_index": 88, "printed_page": "76",
            "order": 0, "region_scope": "figure_region", "region": [.05, .05, .9, .95]},
        "asset_sha256": "1" * 64,
    }


def nested(graph):
    result = deepcopy(graph)
    result["nodes"].append({"id": "toy:container", "kind": "category",
        "label": "ASSEMBLY GROUP", "region": [.3, .4, .4, .6]})
    for edge in result["edges"]:
        if edge["type"] == "CHART_CONNECTOR":
            edge["from"] = "toy:container"
    result["edges"].append({"from": result["root_id"], "to": "toy:container",
        "type": "CHART_CONNECTOR", "region": [.1, .1, .4, .6]})
    return result


def bind(graph):
    return bind_chart_graph_evidence(graph, **a2_binding())


def registry(root):
    (root / "storage").mkdir()
    with sqlite3.connect(root / "storage/dual_layer_registry.db") as connection:
        connection.execute("CREATE TABLE untouched(value TEXT)")
        connection.execute("INSERT INTO untouched VALUES ('legacy')")


def test_explicit_chart_binding_accepts_a2_but_a1_interfaces_remain_strict(toy_graph):
    graph = bind(nested(toy_graph))
    receipt = validate_chart_graph_evidence(graph)
    assert receipt["record_evidence_count"] == len(graph["nodes"]) + len(graph["edges"])
    assert all(record["evidence"]["locator"]["element_id"] == "Figure A2"
               for record in graph["nodes"] + graph["edges"])
    with pytest.raises(ValueError, match="RECORD_LOCATOR_INVALID"):
        validate_a1_graph_evidence(graph)
    with pytest.raises(ValueError, match="RECORD_LOCATOR_INVALID"):
        bind_a1_graph_evidence(nested(toy_graph), **a2_binding())


def test_record_regions_cannot_escape_the_selected_figure_crop(toy_graph):
    graph = nested(toy_graph)
    graph["nodes"][0]["region"] = [.01, .1, .2, .4]
    with pytest.raises(ValueError, match="RECORD_OUTSIDE_FIGURE_REGION"):
        bind(graph)


def test_nested_connectors_preserve_direct_recursive_and_requested_path_direction(toy_graph):
    graph = bind(nested(toy_graph))
    view = _GraphView(graph)
    direct, _ = view.descendants(["toy:container"], direct=True)
    recursive, _ = view.descendants(["toy:container"])
    assert direct == {"toy:container", "toy:alpha", "toy:beta"}
    assert recursive - direct == {"toy:ribbon", "toy:pulsed", "toy:foil", "toy:squeeze"}
    result = answer_graph(graph, "List all processes in ASSEMBLY GROUP in Figure A2.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert {row["id"] for row in result["rows"]} == recursive - direct
    path = view.segment_paths("toy:ribbon", "toy:root")[0]
    assert path["node_ids"] == ["toy:ribbon", "toy:alpha", "toy:container", "toy:root"]
    assert path["direction"] == "child_to_ancestor"
    cyclic = deepcopy(graph)
    cyclic["edges"].append({"from": "toy:alpha", "to": "toy:container",
        "type": "CHART_CONNECTOR", "region": [.1, .1, .4, .6]})
    with pytest.raises(ValueError, match="GRAPH_QA_DIRECTED_CYCLE"):
        _graph_index(cyclic)


def test_source_context_matches_only_the_selected_graph_figure(toy_graph):
    graph = bind(nested(toy_graph))
    context = _source_context_spans("Figure A2. Figure A1.", graph)
    assert [item["text"] for item in context] == ["Figure A2"]
    query = "What is the acronym for Ribbon folding in Figure A2?"
    plan = plan_graph_query(graph, query)
    assert plan["status"] == "ready"
    assert not plan["unresolved_selectors"]
    assert {part["source_element"] for part in plan["source_context"]} == {"Figure A2"}
    foreign = answer_graph(graph, "What is the acronym for Ribbon folding in Figure A1?")
    assert not foreign["operations"]
    assert "source_reference_outside_selected_chart" in foreign["trace"]["diagnostics"]
    answer = answer_graph(graph, "Can Figure A2 provide operating conditions for Ribbon folding?")
    assert "Figure A2 supplies" in answer["answer"]
    assert "Figure A1" not in answer["answer"]


def test_physical_neighbors_include_incoming_and_outgoing_but_not_enclosures(toy_graph):
    graph = bind(nested(toy_graph))
    result = answer_graph(graph, "List physical neighbors of ASSEMBLY GROUP in Figure A2.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert result["route"] == "physical_neighbors"
    assert {row["id"] for row in result["rows"]} == {"toy:root", "toy:alpha", "toy:beta"}
    assert {edge["type"] for edge in result["trace"]["selected_edges"]} == {"CHART_CONNECTOR"}
    assert result["operations"][0]["trace"]["direction"] == "undirected"
    assert "not arrow direction or semantic subtype" in result["answer"]


def test_outer_container_is_distinguished_from_direct_box_without_false_negative(toy_graph):
    source = bind(nested(toy_graph))
    result = answer_graph(source, "Is Ribbon folding under ASSEMBLY GROUP in Figure A2?", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert result["verdict"] == "not_established"
    assert "directly enclosed by ALPHA FAMILY, not directly by ASSEMBLY GROUP" in result["answer"]
    assert "physical chart path" in result["answer"]
    assert "No," not in result["answer"]
    assert not result["trace"].get("negative_proof")
    assert result["paths"][0]["node_ids"] == ["toy:container", "toy:alpha", "toy:ribbon"]
    assert result["paths"][0]["edge_types"] == ["CHART_CONNECTOR", "ENCLOSES_ROW"]
    flat = answer_graph(toy_graph, "Is Ribbon folding in BETA FAMILY?", complete_chart=True)
    assert flat["verdict"] == "no"
    assert "rather than BETA FAMILY" in flat["answer"]


def test_accepted_nested_paths_exclude_candidate_indentation_and_retain_evidence(tmp_path, toy_graph):
    from src.evidence_a1_knowledge import prepare_chart_knowledge
    registry(tmp_path)
    source = bind(nested(toy_graph))
    store = prepare_chart_knowledge(tmp_path, source, runtime_relpath="storage/evidence_v2/a2_test/registry.db")
    result = answer_graph(source, "Show the path from Ribbon folding pulsed to ASSEMBLY GROUP in Figure A2.",
                          knowledge_store=store, query_layer="knowledge", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    path = result["paths"][0]
    assert path["node_ids"] == ["toy:pulsed", "toy:alpha", "toy:container"]
    assert "INDENTED_UNDER" not in path["edge_types"]
    operation = result["operations"][0]
    assert operation["knowledge_paths"][0]["assertion_ids"]
    assert len(operation["knowledge_paths"][0]["steps"]) == 2
    proofs = operation["knowledge_support"]["observations"]
    assert all(item["proof"]["locator"]["element_id"] == "Figure A2" for item in proofs)
    assert not operation["knowledge_support"]["missing_evidence_ids"]
    assert store.describe()["assertion_status_counts"]["CANDIDATE"] == 1


def test_a2_retained_source_verifier_runs_before_any_runtime_admission(tmp_path, toy_graph, monkeypatch):
    from src.evidence_a1_knowledge import prepare_chart_knowledge
    registry(tmp_path)
    directory = tmp_path / "storage/evidence_v2/a2_test"
    directory.mkdir(parents=True)
    artifacts = {}
    for name in ("ingest_result", "image"):
        path = directory / name
        payload = name.encode()
        path.write_bytes(payload)
        artifacts[name] = {"path": path.relative_to(tmp_path).as_posix(),
                           "sha256": hashlib.sha256(payload).hexdigest()}
    raw = nested(toy_graph)
    raw["extraction_provenance"] = {"method": "ocr", "engine": "test-only", "version": "1",
        "input_asset_sha256": "1" * 64, "uncertainty": "unreviewed_model_observation",
        "parent_source": a2_binding()}
    raw["raster_verification"] = {"schema_version": "chart-source-integration-1.0",
        "receipt": {"schema_version": "chart-source-record-verification-1.0",
                    "image_sha256": "1" * 64, "nodes": {}, "enclosures": {}},
        "connector_receipt": {"records": []}, "artifacts": artifacts}
    called = []
    def reject(root, graph):
        called.append(graph["source_binding"]["locator"]["element_id"])
        raise ValueError("test-source-verification-rejected")
    monkeypatch.setitem(sys.modules, "src.evidence_a2", SimpleNamespace(validate_a2_integration=reject))
    with pytest.raises(ValueError, match="test-source-verification-rejected"):
        prepare_chart_knowledge(tmp_path, bind(raw), runtime_relpath="storage/evidence_v2/a2_test/registry.db")
    assert called == ["Figure A2"]
    assert not (directory / "registry.db").exists()
