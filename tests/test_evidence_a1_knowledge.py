"""Bounded synthetic checks for persisted epistemic admission; no owner QA."""
from copy import deepcopy
import json
import sqlite3

import pytest

from test_evidence_a1_graph_qa_repair import graph, no_external_calls
from src.evidence_a1 import bind_a1_graph_evidence


def bound(graph):
    return bind_a1_graph_evidence(graph, "fixture:joining@" + "0" * 64, "source2:toy", {
        "element_id": "Figure A1", "canonical_element_id": "figure:figure_a1",
        "source_identity_id": "source2:toy", "pdf_index": 0, "printed_page": "1",
        "order": 0, "region_scope": "full_page", "region": None}, "1" * 64)


def root_with_registry(tmp_path):
    (tmp_path / "storage").mkdir()
    with sqlite3.connect(tmp_path / "storage/dual_layer_registry.db") as connection:
        connection.execute("CREATE TABLE legacy_marker(value TEXT)")
        connection.execute("INSERT INTO legacy_marker VALUES ('preserve')")
    return tmp_path


def prepare(tmp_path, graph):
    from src.evidence_a1_knowledge import prepare_a1_knowledge
    root_with_registry(tmp_path)
    return prepare_a1_knowledge(tmp_path, bound(graph))


def test_persisted_layers_admit_literal_facts_but_keep_layout_candidates(tmp_path, graph):
    original = bound(graph)
    store = prepare(tmp_path, graph)
    graph["nodes"][0]["label"] = "Changed caller memory"
    assert store.graph("evidence") == original
    knowledge = store.graph("knowledge")
    assert all(edge["type"] != "INDENTED_UNDER" for edge in knowledge["edges"])
    assert knowledge["accepted_assertions"]
    assert all(item["status"] == "ACCEPTED" for item in knowledge["accepted_assertions"])
    assert len(knowledge["concept_bindings"]) == len(original["nodes"])
    assert store.describe()["assertion_status_counts"]["CANDIDATE"] == 2
    from src.evidence_a1_knowledge import prepare_a1_knowledge
    assert prepare_a1_knowledge(tmp_path, original).graph("evidence") == original
    with sqlite3.connect(tmp_path / "storage/dual_layer_registry.db") as connection:
        assert connection.execute("SELECT value FROM legacy_marker").fetchone() == ("preserve",)


def test_semantic_proposal_cannot_promote_geometry_or_arbitrary_counterproof(tmp_path, graph):
    store = prepare(tmp_path, graph)
    source = store.graph("evidence")
    edge = next(edge for edge in source["edges"] if edge["type"] == "INDENTED_UNDER")
    proposal = store.propose(edge["to"], "IS_A", edge["from"],
                             support_evidence_ids=[edge["evidence"]["evidence_id"]])
    assert proposal["status"] == "CANDIDATE"
    assert "geometry" in proposal["admission_reason"].lower()
    assert not any(item["predicate"] == "IS_A" for item in store.graph("knowledge")["accepted_assertions"])
    with pytest.raises(TypeError):
        store.propose(edge["to"], "IS_A", edge["from"], status="ACCEPTED")
    with pytest.raises(ValueError):
        store.propose(edge["to"], "IS_A", edge["from"],
            support_evidence_ids=[edge["evidence"]["evidence_id"]],
            counter_evidence_ids=[source["nodes"][0]["evidence"]["evidence_id"]])


def test_actual_contrary_designations_dispute_both_functional_assertions(tmp_path, graph):
    duplicate = deepcopy(next(node for node in graph["nodes"] if node["id"] == "toy:ribbon"))
    duplicate.update(id="toy:contrary", code="ZZCONFLICT", region=[0.7, 0.1, 0.74, 0.4])
    graph["nodes"].append(duplicate)
    graph["edges"].append({"from": "toy:alpha", "to": duplicate["id"], "type": "ENCLOSES_ROW", "region": duplicate["region"]})
    store = prepare(tmp_path, graph)
    source = store.graph("evidence")
    selected = [node for node in source["nodes"] if node["id"] in {"toy:ribbon", "toy:contrary"}]
    receipt = store.support_for(record_ids=[node["id"] for node in selected])
    conflicts = [item for item in receipt["assertions"] if item["predicate"] == "PRINTED_DESIGNATION"]
    assert len(conflicts) == 2 and all(item["status"] == "DISPUTED" for item in conflicts)
    assert all(item["counter_evidence_ids"] for item in conflicts)
    assert not any(item["predicate"] == "PRINTED_DESIGNATION" and item["subject_id"] == conflicts[0]["subject_id"]
                   for item in store.graph("knowledge")["accepted_assertions"])


def test_tampering_cross_edition_and_stale_inputs_fail_without_rebuild(tmp_path, graph):
    store = prepare(tmp_path, graph)
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE a1k_source_observations SET payload_json='{}' WHERE record_id='toy:ribbon'")
    with pytest.raises(ValueError, match="A1_KNOWLEDGE_STORE_TAMPERED"):
        store.graph("evidence")
    from src.evidence_a1_knowledge import prepare_a1_knowledge
    wrong = bound(graph)
    wrong["nodes"][0]["evidence"]["edition_id"] = "fixture:other"
    with pytest.raises(ValueError):
        prepare_a1_knowledge(tmp_path, wrong)
    second_root = tmp_path / "other"
    second_root.mkdir()
    root_with_registry(second_root)
    prepare_a1_knowledge(second_root, bound(graph))
    graph["nodes"][0]["label"] += " changed"
    with pytest.raises(ValueError, match="A1_KNOWLEDGE_SOURCE_CHANGED"):
        prepare_a1_knowledge(second_root, bound(graph))


def test_accepted_two_hop_edges_return_complete_persisted_proof_closure(tmp_path, graph):
    store = prepare(tmp_path, graph)
    knowledge = store.graph("knowledge")
    edges = [edge for edge in knowledge["edges"] if (edge["from"], edge["to"]) in {
        ("toy:root", "toy:alpha"), ("toy:alpha", "toy:ribbon")}]
    assert len(edges) == 2
    receipt = store.support_for(record_ids=[edge["id"] for edge in edges])
    assert {item["predicate"] for item in receipt["assertions"]} == {"CHART_CONNECTED", "CHART_MEMBER_OF"}
    assert {item["record_id"] for item in receipt["observations"]} == {
        "toy:root", "toy:alpha", "toy:ribbon", *[edge["id"] for edge in edges]}
    assert receipt["missing_evidence_ids"] == []
    assert receipt["source_authentication"] == "caller_must_authenticate_canonical_source"


def test_candidate_enclosure_observations_are_not_admitted_as_knowledge(tmp_path, graph):
    graph["edge_qualifications"]["ENCLOSES_ROW"]["verification"] = "candidate"
    store = prepare(tmp_path, graph)
    assert store.graph("evidence") == bound(graph)
    knowledge = store.graph("knowledge")
    assert not any(edge["type"] == "ENCLOSES_ROW" for edge in knowledge["edges"])
    assert not any(item["predicate"] == "CHART_MEMBER_OF" for item in knowledge["accepted_assertions"])
    edges = [edge["id"] for edge in store.graph("evidence")["edges"] if edge["type"] == "ENCLOSES_ROW"]
    membership = [item for item in store.support_for(record_ids=edges)["assertions"]
                  if item["predicate"] == "CHART_MEMBER_OF"]
    assert membership and all(item["status"] == "CANDIDATE" for item in membership)


def test_resealed_forged_admission_is_rejected(tmp_path, graph):
    from src.evidence_a1_knowledge import _seal
    store = prepare(tmp_path, graph)
    with sqlite3.connect(store.path) as connection:
        identifier, payload = next((identifier, payload) for identifier, payload in connection.execute(
            "SELECT assertion_id,payload_json FROM a1k_typed_assertions")
            if json.loads(payload)["predicate"] == "CANDIDATE_LAYOUT_PARENT")
        forged = json.loads(payload)
        forged.update(predicate="IS_A", status="ACCEPTED", admission_reason="Invented review", rule_id="invented-review")
        connection.execute("UPDATE a1k_typed_assertions SET payload_json=? WHERE assertion_id=?", (json.dumps(forged), identifier))
        _seal(connection)
    with pytest.raises(ValueError, match="A1_KNOWLEDGE_ADMISSION_INVALID"):
        store.graph("knowledge")
