"""Small synthetic inspection and private-output regressions; no source gold."""
import fitz
import pytest

from src.evidence_a1_ingest import inspect_page, _new_directory, answer_raster_questions


def test_page_inspection_separates_text_and_structural_signals():
    with fitz.open() as pdf:
        page = pdf.new_page(width=300, height=300)
        page.insert_text((30, 30), "A readable synthetic label")
        page.draw_rect(fitz.Rect(10, 10, 270, 80))
        top = inspect_page(page, [0, 0, .4, 1])
        bottom = inspect_page(page, [.5, 0, 1, 1])
        assert top["text_route"] == "native_text"
        assert top["vector_drawing_count"] == 1
        assert "does not establish" in top["qualification"]
        assert bottom["text_route"] == "local_ocr"
        assert bottom["vector_drawing_count"] == 0


def test_image_only_pdf_is_not_a_native_text_route():
    from PIL import Image
    import io
    data = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(data, format="PNG")
    with fitz.open() as pdf:
        page = pdf.new_page(width=100, height=100)
        page.insert_image(page.rect, stream=data.getvalue())
        status = inspect_page(page)
        assert status["native_character_count"] == 0
        assert status["raster_image_count"] == 1
        assert status["text_route"] == "local_ocr"


def test_inspection_rejects_invalid_region():
    with fitz.open() as pdf:
        page = pdf.new_page()
        for region in ([0, 1, 1, 0], [0, 0, float("nan"), 1], [False, 0, 1, 1]):
            with pytest.raises(ValueError):
                inspect_page(page, region)


def test_private_run_directory_is_exclusive_and_contained(tmp_path):
    target = _new_directory(tmp_path, "storage/evidence_v2/new-run")
    assert target.is_dir()
    with pytest.raises(FileExistsError):
        _new_directory(tmp_path, target)
    with pytest.raises(ValueError):
        _new_directory(tmp_path, tmp_path.parent / "outside")


def test_missing_raster_graph_is_a_setup_blocker_not_qa_failure(tmp_path):
    result = answer_raster_questions(tmp_path, {}, {
        "schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1",
        "questions": [{"id": "toy", "query": "Show the label."}]},
        runtime_relpath="storage/evidence_v2/toy/registry.db")
    assert result["status"] == "NOT_RUN_EXTRACTION_GRAPH_UNAVAILABLE"
    assert result["answers"] == []


def test_normalization_dictionary_exports_literal_vocabulary_without_graph_authority(monkeypatch):
    from types import SimpleNamespace
    import hashlib
    import json
    import src.evidence_a1_ingest as ingest
    graph = {"root_id": "private-root", "nodes": [
        {"id": "private-root", "kind": "root", "label": "OPERATIONS"},
        {"id": "private-group", "kind": "category", "label": "FOLDING (F)"},
        {"id": "private-process", "kind": "process", "label": "Ribbon fold", "code": "RF"}],
        "edges": [{"from": "private-group", "to": "private-process", "type": "ENCLOSES_ROW"}],
        "source_binding": {"edition_id": "edition", "source_identity_id": "source2:test", "asset_sha256": "a" * 64}}
    monkeypatch.setattr(ingest, "load_a1_evidence", lambda root: [
        SimpleNamespace(kind="figure_region", content={"chart_graph": graph})])
    actual = ingest.source_normalization_dictionary("unused")
    assert {item["label"] for item in actual["entries"]} == {"OPERATIONS", "FOLDING", "Ribbon fold"}
    assert all(set(item) <= {"kind", "label", "code"} for item in actual["entries"])
    digest = actual.pop("content_sha256")
    assert digest == hashlib.sha256(json.dumps(actual, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert "private-" not in json.dumps(actual)


def test_compact_vision_tasks_exclude_already_observed_connections():
    from src.evidence_a1_ingest import _unresolved_connector_tasks
    graph = {"root_id": "root", "nodes": [{"id": "root", "kind": "root"},
        {"id": "group1", "kind": "category"}, {"id": "group2", "kind": "category"},
        {"id": "row", "kind": "process"}],
        "edges": [{"from": "root", "to": "group1", "type": "CHART_CONNECTOR"}]}
    assert _unresolved_connector_tasks(graph) == [{"type": "CHART_CONNECTOR", "from_id": "root", "to_id": "group2"}]
    graph["root_id"] = None
    assert _unresolved_connector_tasks(graph) == [
        {"type": "CHART_CONNECTOR", "from_id": "$root", "to_id": "group1"},
        {"type": "CHART_CONNECTOR", "from_id": "$root", "to_id": "group2"}]


def test_incomplete_visual_output_cannot_add_observations(tmp_path):
    from src.evidence_a1_ingest import _add_visual_observations
    graph = {"root_id": None, "nodes": [], "edges": []}
    actual = _add_visual_observations(graph,
        {"status": "incomplete_output", "root_observation": {"word_ids": ["invented"]},
         "proposals": [{"from_id": "invented"}]}, b"pixels", tmp_path / "absent", {})
    assert actual == []
    assert graph == {"root_id": None, "nodes": [], "edges": []}


def test_verified_category_scope_does_not_claim_unverified_whole_chart():
    from src.evidence_a1_graph_qa import _verified_raster_scope
    graph = {"nodes": [{"id": "r", "kind": "root"}, {"id": "c", "kind": "category"},
                       {"id": "p", "kind": "process"}],
             "edges": [{"from": "c", "to": "p", "type": "ENCLOSES_ROW"}],
             "raster_verification": {"receipt": {
                 "coverage": {"c": {"complete": True}},
                 "chart_coverage": {"scope": "toy_chart", "complete": False}}}}
    assert _verified_raster_scope(graph, {"subject_ids": ["c"]})["complete"]
    assert _verified_raster_scope(graph, {"subject_ids": ["p"]})["complete"]
    assert not _verified_raster_scope(graph, {"subject_ids": ["r"]})["complete"]
    assert not _verified_raster_scope(graph, {"subject_ids": ["missing"]})["complete"]


def test_raster_receipt_cannot_authorize_changed_literals_or_source_bytes(tmp_path, monkeypatch):
    """Synthetic validator replay, not image-recognition/answer validation."""
    import hashlib
    import json
    from copy import deepcopy
    import src.evidence_a1_ingest as ingest
    import src.evidence_a1_strokes as strokes
    import src.evidence_a1_verification as verification
    from test_evidence_a1_ingest_admission import raster_fixture
    from src.evidence_a1 import bind_a1_graph_evidence
    raw, binding = raster_fixture()
    pixels = b"synthetic retained pixels"
    digest = hashlib.sha256(pixels).hexdigest()
    binding["asset_sha256"] = digest
    raw["extraction_provenance"]["input_asset_sha256"] = digest
    graph = bind_a1_graph_evidence(raw, **binding)
    directory = tmp_path / "storage/evidence_v2/toy"
    directory.mkdir(parents=True)
    image = directory / "extraction_pixels.png"
    image.write_bytes(pixels)
    seed = {"graph": graph, "ocr": {"input": {"image_sha256": digest, "edition_id": binding["edition_id"]}}}
    source = directory / "ingest_result.json"
    source.write_text(json.dumps(seed), encoding="utf-8")
    connectors = {"records": []}
    receipt = {"image_sha256": digest}
    monkeypatch.setattr(strokes, "verify_chart_connectors", lambda *args: connectors)
    monkeypatch.setattr(verification, "verify_raster_records", lambda *args: receipt)
    metadata = {"schema_version": "a1-raster-integration-1.0",
                "artifacts": {"ingest_result": {"path": str(source.relative_to(tmp_path)),
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
                    "image": {"path": str(image.relative_to(tmp_path)), "sha256": digest}},
                "receipt": receipt, "connector_receipt": connectors}
    current = ingest._verified_raster_graph(seed, metadata)
    assert ingest.validate_raster_integration(tmp_path, current) == metadata
    changed_seed = deepcopy(seed)
    changed_seed["graph"]["nodes"][0]["label"] = "Unobserved replacement label"
    changed = ingest._verified_raster_graph(changed_seed, metadata)
    with pytest.raises(ValueError, match="GRAPH_DIFFERS_FROM_SOURCE"):
        ingest.validate_raster_integration(tmp_path, changed)
    image.write_bytes(b"different source")
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        ingest.validate_raster_integration(tmp_path, current)


@pytest.mark.parametrize("root_resolved", [True, False])
def test_missing_root_continuation_uses_cached_pixels_without_ocr_or_native_input(tmp_path, monkeypatch, root_resolved):
    from copy import deepcopy
    import hashlib
    import json
    from test_evidence_a1_provenance import fixture
    import src.evidence_a1_raster as raster
    import src.evidence_a1_vision as vision
    import src.evidence_a1_ingest as ingest

    graph, binding = fixture()
    root = next(node for node in graph["nodes"] if node["id"] == graph["root_id"])
    partial = deepcopy(graph)
    partial["nodes"] = [n for n in partial["nodes"] if n["id"] != graph["root_id"]]
    partial["edges"] = [e for e in partial["edges"] if e["from"] != graph["root_id"]]
    partial["root_id"] = None
    projected = {"engine": "toy-ocr", "version": "1", "partial_graph": partial,
                 "bootstrap_words": [{"id": "word-root", "text": root["label"], "region": root["region"]}]}
    monkeypatch.setattr(raster, "rebuild_partial_from_observations", lambda cached: projected)
    def forbidden(*args, **kwargs):
        raise AssertionError("OCR/native input must not be reread")
    monkeypatch.setattr(raster, "_run_tesseract", forbidden)
    monkeypatch.setattr(ingest, "load_a1_evidence", forbidden)
    cached_dir = tmp_path / "storage/evidence_v2/first"
    cached_dir.mkdir(parents=True)
    pixels = b"synthetic cached pixels"
    (cached_dir / "extraction_pixels.png").write_bytes(pixels)
    cached = {"status": "RASTER_GRAPH_UNAVAILABLE", "model_calls": 0,
              "ocr": {"input": {"edition_id": binding["edition_id"],
                                "image_sha256": hashlib.sha256(pixels).hexdigest()}},
              "input_image_sha256": hashlib.sha256(pixels).hexdigest(), "parent_source": binding}
    path = cached_dir / "ingest_result.json"
    path.write_text(json.dumps(cached), encoding="utf-8")
    before = path.read_bytes()
    def observe(image, supplied, *, raw_output_path, num_ctx):
        assert Path(image).read_bytes() == pixels
        assert num_ctx == 32768
        Path(raw_output_path).write_bytes(b"synthetic model observation")
        return {"callcount": 1, "root_observation": {
            "word_ids": ["word-root"], "region": root["region"], "observation": "toy pixels"
        } if root_resolved else None, "proposals": [],
            "config": {"model": "toy-model", "model_digest": "toy-digest"}}
    from pathlib import Path
    monkeypatch.setattr(vision, "analyze_visual_structure", observe)
    result = ingest.resume_raster_structure(tmp_path, path, "storage/evidence_v2/continuation")
    assert path.read_bytes() == before
    assert result["ocr_reused_without_rerun"]
    if root_resolved:
        assert all(record["evidence"]["verification"] == "candidate"
                   for record in result["graph"]["nodes"] + result["graph"]["edges"])
    else:
        assert result["status"] == "RASTER_GRAPH_UNAVAILABLE"
        assert "graph" not in result


@pytest.mark.parametrize("field,bad_value", [("image_sha256", "a" * 64), ("edition_id", "other-edition")])
def test_cached_observations_cannot_be_rebound_to_different_pixels_or_edition(tmp_path, monkeypatch, field, bad_value):
    from pathlib import Path
    import hashlib
    import json
    from test_evidence_a1_provenance import fixture
    import src.evidence_a1_raster as raster
    from src.evidence_a1_ingest import resume_raster_structure
    _, binding = fixture()
    pixels = b"cached pixels"
    pixel_hash = hashlib.sha256(pixels).hexdigest()
    cached = {"status": "RASTER_GRAPH_UNAVAILABLE", "model_calls": 0,
              "input_image_sha256": pixel_hash, "parent_source": binding,
              "ocr": {"input": {"image_sha256": pixel_hash, "edition_id": binding["edition_id"]}}}
    cached["ocr"]["input"][field] = bad_value
    directory = tmp_path / "storage/evidence_v2/cached"
    directory.mkdir(parents=True)
    (directory / "extraction_pixels.png").write_bytes(pixels)
    path = directory / "ingest_result.json"
    path.write_text(json.dumps(cached), encoding="utf-8")
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid lineage must fail before projection or inference")
    monkeypatch.setattr(raster, "rebuild_partial_from_observations", forbidden)
    with pytest.raises(ValueError, match="lineage mismatch"):
        resume_raster_structure(tmp_path, path, "storage/evidence_v2/new")
