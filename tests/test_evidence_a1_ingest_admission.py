"""Source-method boundary over synthetic records; no OCR/model or AWS gold."""
from copy import deepcopy
import sqlite3

import pytest

from test_evidence_a1_provenance import fixture
from src.evidence_a1 import bind_a1_graph_evidence, validate_a1_graph_evidence
from src.evidence_a1_graph_qa import answer_graph
from src.evidence_a1_knowledge import prepare_a1_knowledge


def raster_fixture():
    graph, original = fixture()
    source = deepcopy(original)
    source["asset_sha256"] = "c" * 64
    source["source_identity_id"] = "source2:raster"
    source["locator"]["source_identity_id"] = source["source_identity_id"]
    graph["extraction_provenance"] = {
        "method": "ocr", "engine": "synthetic-ocr", "version": "test-1",
        "input_asset_sha256": source["asset_sha256"],
        "uncertainty": "unreviewed_model_observation", "parent_source": original}
    return graph, source


def registry(root):
    (root / "storage").mkdir()
    with sqlite3.connect(root / "storage/dual_layer_registry.db") as connection:
        connection.execute("CREATE TABLE preserve_legacy (id TEXT PRIMARY KEY)")


def test_raster_proofs_bind_actual_input_and_original_lineage_as_candidates():
    graph, source = raster_fixture()
    original = deepcopy(graph)
    bound = bind_a1_graph_evidence(graph, **source)
    assert graph == original
    assert all(record["evidence"]["verification"] == "candidate"
               for record in bound["nodes"] + bound["edges"])
    for record in bound["nodes"] + bound["edges"]:
        proof = record["evidence"]
        assert proof["asset_sha256"] == "c" * 64
        assert proof["extraction_provenance"] == graph["extraction_provenance"]
        assert proof["extraction_provenance"]["parent_source"]["asset_sha256"] == "b" * 64
    assert all(item["verification"] == "candidate" for item in bound["edge_qualifications"].values())
    assert validate_a1_graph_evidence(bound, expected_source=source)["record_evidence_count"] == 8


@pytest.mark.parametrize("field,value", [
    ("method", "native"), ("input_asset_sha256", "d" * 64),
    ("uncertainty", "verified"), ("version", ""),
])
def test_invalid_raster_method_or_input_provenance_fails_closed(field, value):
    graph, source = raster_fixture()
    graph["extraction_provenance"][field] = value
    with pytest.raises(ValueError, match="EXTRACTION"):
        bind_a1_graph_evidence(graph, **source)


def test_vision_relation_override_keeps_its_actual_method_and_same_asset_lineage():
    graph, source = raster_fixture()
    graph["edges"][-1]["extraction_provenance"] = dict(graph["extraction_provenance"],
        method="vision", engine="synthetic-local-vision", version="digest:test")
    graph["edges"][-1]["origin_artifact_sha256"] = "e" * 64
    bound = bind_a1_graph_evidence(graph, **source)
    assert bound["nodes"][0]["evidence"]["extraction_provenance"]["method"] == "ocr"
    vision = bound["edges"][-1]
    assert vision["evidence"]["verification"] == "candidate"
    assert vision["evidence"]["extraction_provenance"]["method"] == "vision"
    assert vision["origin_artifact_sha256"] == "e" * 64
    graph["edges"][-1]["extraction_provenance"]["input_asset_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="EXTRACTION"):
        bind_a1_graph_evidence(graph, **source)


def test_raster_runtime_isolated_and_candidate_facts_cannot_leak_into_knowledge(tmp_path):
    registry(tmp_path)
    native_graph, native_source = fixture()
    native = prepare_a1_knowledge(tmp_path, bind_a1_graph_evidence(native_graph, **native_source))
    preserved = native.path.read_bytes()
    graph, source = raster_fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    raster = prepare_a1_knowledge(tmp_path, bound,
        runtime_relpath="storage/evidence_v2/ingest-test/registry.db")
    assert raster.path != native.path
    assert native.path.read_bytes() == preserved
    assert native.graph("knowledge")["accepted_assertions"]
    assert not raster.graph("knowledge")["accepted_assertions"]
    assert raster.describe()["runtime_relpath"] == "storage/evidence_v2/ingest-test/registry.db"
    assert raster.describe()["assertion_status_counts"]["CANDIDATE"] > 0
    result = answer_graph(bound, "What does ZZP stand for?", complete_chart=True,
                          knowledge_store=raster)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["rows"] == []
    assert all(op["accepted_assertion_ids"] == [] for op in result["operations"])
    assert "Pulsed fold" not in result["answer"]
    assert "requested_identity_not_admitted_to_knowledge" in result["trace"]["diagnostics"]
    assert native.path.read_bytes() == preserved


def test_raster_evidence_answers_are_qualified_and_unproven_exhaustiveness_abstains(tmp_path):
    registry(tmp_path)
    graph, source = raster_fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    store = prepare_a1_knowledge(tmp_path, bound,
        runtime_relpath="storage/evidence_v2/ingest-test/registry.db")
    result = answer_graph(bound, "Show the path from Ribbon fold to ALPHA (AF).",
                          knowledge_store=store, query_layer="evidence")
    assert result["answer_outcome"] == "graph_answer"
    assert "unreviewed" in result["answer"].lower()
    assert result["source_binding_status"] != "canonical_source_and_image_validated"
    assert all(claim["verification"] == "candidate" for claim in result["claims"])
    assert all(op["accepted_assertion_ids"] == [] for op in result["operations"])
    incomplete = answer_graph(bound, "List all descendants of ALPHA (AF).",
                               knowledge_store=store, query_layer="evidence")
    assert incomplete["answer_outcome"] == "insufficient_evidence"
    assert "complete_chart_required" in " ".join(incomplete["trace"]["diagnostics"])


def verified_raster_fixture():
    """Synthetic decision projection, not a claim of pixel recognition accuracy."""
    import json
    graph, source = raster_fixture()
    decisions = {node["id"]: {"label_supported": True,
        "designation_supported": node.get("code") is not None,
        "label_observation_ids": ["toy-word:" + node["id"]],
        "designation_observation_ids": [], "support_node_ids": []}
        for node in graph["nodes"]}
    # A row label can be supported while its designation remains uncertain.
    decisions["toy:child"]["designation_supported"] = False
    enclosures = {json.dumps([edge["from"], edge["to"], edge["type"]], separators=(",", ":")):
        {"verified": True, "from_id": edge["from"], "to_id": edge["to"], "type": edge["type"]}
        for edge in graph["edges"] if edge["type"] == "ENCLOSES_ROW"}
    graph["raster_verification"] = {"schema_version": "a1-raster-integration-1.0",
        "artifacts": {}, "receipt": {"schema_version": "a1-raster-record-verification-1.0",
            "image_sha256": source["asset_sha256"], "nodes": decisions, "enclosures": enclosures},
        "connector_receipt": {"records": [{"from_id": "toy:root", "to_id": "toy:family",
            "verified": True, "direction": "undirected", "polyline": [[.2, .3], [.3, .3]]}]}}
    return graph, source


def test_raster_admission_is_per_literal_field_and_verified_physical_relation():
    from src.evidence_a1_knowledge import _admit
    graph, source = verified_raster_fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    _, concepts, assertions = _admit(bound)
    by_fact = {(item["subject_id"], item["predicate"]): item for item in assertions}
    assert by_fact[(concepts["toy:child"], "PRINTED_LABEL")]["status"] == "ACCEPTED"
    assert by_fact[(concepts["toy:child"], "PRINTED_DESIGNATION")]["status"] == "CANDIDATE"
    assert by_fact[(concepts["toy:child"], "CHART_MEMBER_OF")]["status"] == "ACCEPTED"
    assert by_fact[(concepts["toy:child"], "CANDIDATE_LAYOUT_PARENT")]["status"] == "CANDIDATE"
    accepted = [item for item in assertions if item["status"] == "ACCEPTED"]
    assert all(item["admission_evidence"]["image_sha256"] == source["asset_sha256"] for item in accepted)
    assert all(record["evidence"]["verification"] == "candidate" for record in bound["nodes"] + bound["edges"])
    assert not any(item["predicate"] == "IS_A" and item["status"] == "ACCEPTED" for item in assertions)
    # A missing pixel enclosure decision cannot inherit acceptance from labels.
    graph["raster_verification"]["receipt"]["enclosures"] = {}
    _, _, uncertain = _admit(bind_a1_graph_evidence(graph, **source))
    assert all(item["status"] == "CANDIDATE" for item in uncertain if item["predicate"] == "CHART_MEMBER_OF")


def persisted_verification_fixture(tmp_path):
    import hashlib
    graph, source = verified_raster_fixture()
    directory = tmp_path / "storage/evidence_v2/source"
    directory.mkdir(parents=True)
    image = directory / "pixels.png"
    image.write_bytes(b"synthetic retained image bytes")
    seed = directory / "ingest.json"
    seed.write_text("{}", encoding="utf-8")
    graph["raster_verification"]["artifacts"] = {
        name: {"path": path.relative_to(tmp_path).as_posix(),
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for name, path in (("image", image), ("ingest_result", seed))}
    return bind_a1_graph_evidence(graph, **source), image


def test_public_raster_admission_rejects_unrecomputed_claimed_acceptance(tmp_path, monkeypatch):
    import src.evidence_a1_ingest as ingest
    registry(tmp_path)
    graph, _ = persisted_verification_fixture(tmp_path)
    def reject(root, supplied):
        raise ValueError("SYNTHETIC_PIXEL_REJECTION")
    monkeypatch.setattr(ingest, "validate_raster_integration", reject, raising=False)
    with pytest.raises(ValueError, match="SYNTHETIC_PIXEL_REJECTION"):
        prepare_a1_knowledge(tmp_path, graph, runtime_relpath="storage/evidence_v2/verified/registry.db")
    assert not (tmp_path / "storage/evidence_v2/verified/registry.db").exists()


def test_raster_admission_cache_rechecks_retained_source_bytes_on_reads(tmp_path, monkeypatch):
    import src.evidence_a1_ingest as ingest
    registry(tmp_path)
    graph, image = persisted_verification_fixture(tmp_path)
    calls = []
    monkeypatch.setattr(ingest, "validate_raster_integration", lambda root, supplied: calls.append(True), raising=False)
    store = prepare_a1_knowledge(tmp_path, graph, runtime_relpath="storage/evidence_v2/verified/registry.db")
    assert store.graph("knowledge")["accepted_assertions"]
    count = len(calls)
    store.describe()
    assert len(calls) == count  # Same source/receipt does not rerun pixel work.
    image.write_bytes(b"changed retained source")
    with pytest.raises(ValueError, match="RASTER_SOURCE_CHANGED"):
        store.graph("knowledge")
