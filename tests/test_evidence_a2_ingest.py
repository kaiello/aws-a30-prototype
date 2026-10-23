"""Synthetic adapter boundaries; no licensed labels or answer keys."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

import numpy as np
import pytest

from src.evidence_a2 import (_chart_closure, _heading_rows, _line_interval, _literal, _page_region,
    _physical_connectors, _pixel_box, _private, _row_fields, _uncovered_text_bands, run_questions)
from test_evidence_a1_graph_qa import toy_graph, no_network


def test_coordinate_mapping_keeps_page_scope():
    geometry = {"dpi":144,"pixel_origin":[20,40],"page_size":[100,200]}
    box = _pixel_box([20,30,40,50],geometry)
    assert box==[20,20,40,40]
    assert _page_region(box,geometry)==[.15,.2,.25,.4]


def test_native_line_contacts_stop_at_intervening_box():
    geometry = {"dpi":72,"pixel_origin":[0,0],"page_size":[100,100],
        "lines":[{"pdf_endpoints":[[5,50],[95,50]],"drawing_ordinal":2,"item_index":0}]}
    ink = np.zeros((100,100),dtype=np.uint8)
    ink[49:52,5:96] = 255
    records = _physical_connectors(geometry,{"left":[0,40,20,20],"middle":[40,40,20,20],
        "right":[80,40,20,20]},ink)
    pairs = {tuple(record["end_ids"]) for record in records if record["verified"]}
    assert pairs=={("left","middle"),("middle","right")}
    assert all(record["ink_coverage"]==1.0 for record in records)
    assert all(record["direction"]=="undirected" for record in records)
    assert _line_interval([[0,0],[100,0]],[20,20,20,20]) is None


def test_native_line_without_visible_pixels_not_accepted():
    geometry = {"dpi":72,"pixel_origin":[0,0],"page_size":[100,100],
        "lines":[{"pdf_endpoints":[[5,50],[95,50]],"drawing_ordinal":0,"item_index":0}]}
    records = _physical_connectors(geometry,{"left":[0,40,20,20],"right":[80,40,20,20]},
                                   np.zeros((100,100),dtype=np.uint8))
    assert len(records)==1 and not records[0]["verified"]


def test_heading_rows_and_codes_preserve_printed_hyphens():
    rows = [{"text":"FIRST GROUP (FG)"},{"text":"a short label FG-A"}]
    assert _heading_rows(rows)==rows[:1]
    assert _literal("FG-A")!=_literal("FGA")


def test_punctuation_noise_does_not_destroy_observed_code_column():
    row = {"text":"ordinary label © XX-A","words":[
        {"text":"ordinary","pixel_bbox":[5,20,40,10]},
        {"text":"label","pixel_bbox":[50,20,25,10]},
        {"text":"©","pixel_bbox":[155,20,10,10]},
        {"text":"XX-A","pixel_bbox":[170,20,25,10]}]}
    assert _row_fields(row,[0,0,200,100])[:2]==("ordinary label","XX-A")
    assert row["words"][2]["text"]=="©" and row["text"]=="ordinary label © XX-A"
    crowded = {"text":"ordinary longlabel YY-A","words":[
        {"text":"ordinary","pixel_bbox":[5,20,40,20]},
        {"text":"longlabel","pixel_bbox":[50,20,115,20]},
        {"text":"YY-A","pixel_bbox":[170,20,25,20]}]}
    assert _row_fields(crowded,[0,0,200,100],170)[:2]==("ordinary longlabel","YY-A")
    assert _row_fields(crowded,[0,0,200,100],125)[1] is None


def test_unobserved_ink_row_prevents_completeness():
    ink = np.zeros((100,150),dtype=np.uint8)
    ink[20:29,20:30] = 255
    ink[55:65,20:30] = 255
    missing = _uncovered_text_bands(ink,[0,0,150,100],[{"pixel_bbox":[18,18,40,14]}])
    assert missing==[[55,65]]


def test_private_output_and_gold_input_are_rejected(tmp_path):
    root = tmp_path.resolve()
    (root/"storage/evidence_v2").mkdir(parents=True)
    assert _private(root,"storage/evidence_v2/run/result.json").is_relative_to(root)
    with pytest.raises(ValueError,match="PRIVATE_PATH_INVALID"):
        _private(root,"outside.json")
    payload = {"schema_version":"a2-development-cq-1.0","source_element":"Figure A2",
               "questions":[{"id":"one","query":"ordinary question","expected":"hidden"}]}
    with pytest.raises(ValueError,match="QUESTION_ITEM_INVALID"):
        run_questions(root,"not-read.json",payload)


def test_unassigned_words_and_same_line_missing_ink_block_chart_closure():
    ink = np.zeros((100,150),dtype=np.uint8)
    ink[30:40,20:30] = 255
    ink[30:40,65:75] = 255
    word = {"tsv_row_index":1,"pixel_bbox":[20,30,10,10]}
    row = {"words":[word],"pixel_bbox":[20,30,10,10]}
    group = {"box":[5,5,100,80],"rows":[row],"headers":[]}
    receipt = _chart_closure(ink,[group],[word],[])
    assert not receipt["complete"] and receipt["unexplained_ink_components"]
    receipt = _chart_closure(np.zeros_like(ink),[group],[word,{"tsv_row_index":2,"pixel_bbox":[120,30,10,10]}],[])
    assert not receipt["complete"] and receipt["orphan_or_duplicate_word_ids"]==[2]


def test_heading_gap_does_not_hide_unobserved_word_ink():
    ink = np.zeros((100,150),dtype=np.uint8)
    ink[20:30,20:30] = 255
    ink[20:30,90:100] = 255
    ink[20:30,55:65] = 255  # A missed internal heading word.
    words = [{"tsv_row_index":i,"pixel_bbox":[x,20,10,10]} for i,x in enumerate([20,90])]
    row = {"words":words,"pixel_bbox":[20,20,80,10]}
    group = {"box":[5,5,120,80],"rows":[row],"headers":[row]}
    receipt = _chart_closure(ink,[group],words,[])
    assert not receipt["complete"] and receipt["unexplained_ink_components"]


def candidate_observation_fixture(root, toy_graph):
    """Original toy source bytes and a candidate receipt, never licensed content."""
    from src.evidence_a1 import bind_chart_graph_evidence
    from src.evidence_a2 import _digest
    digest = lambda value: hashlib.sha256(value).hexdigest()
    directory = root / "storage/evidence_v2/visual"
    directory.mkdir(parents=True)
    import fitz
    document = fitz.open()
    for _ in range(89):
        document.new_page(width=100, height=100)
    page = document[88]
    page.draw_line((10, 25), (80, 25), color=(0, 0, 0), width=2)
    document.save(directory / "document.pdf")
    page_image = page.get_pixmap(alpha=False).tobytes("png")
    crop_image = page.get_pixmap(clip=fitz.Rect(5, 5, 95, 90), alpha=False).tobytes("png")
    clip_image = page.get_pixmap(matrix=fitz.Matrix(8, 8),
                                clip=fitz.Rect(8, 8, 85, 45), alpha=False)
    (directory / "page.png").write_bytes(page_image)
    (directory / "crop.png").write_bytes(crop_image)
    pdf_hash = digest((directory / "document.pdf").read_bytes())
    edition = "fixture:visual@1"
    source_id = "source:" + _digest([edition, pdf_hash])
    locator = {"element_id": "Figure A2", "canonical_element_id": "figure:figure_a2",
        "source_identity_id": source_id, "pdf_index": 88, "printed_page": "76", "order": 0,
        "region_scope": "figure_region", "region": [.05, .05, .9, .95]}
    parent = {"edition_id": edition, "source_identity_id": source_id, "locator": locator,
              "asset_sha256": digest(page_image)}
    raw = deepcopy(toy_graph)
    raw["extraction_provenance"] = {"method": "vision", "engine": "toy", "version": "1",
        "input_asset_sha256": digest(crop_image), "uncertainty": "unreviewed_model_observation",
        "parent_source": parent}
    graph = bind_chart_graph_evidence(raw, edition, source_id, locator, digest(crop_image))
    observations = []
    for i, edge in enumerate(e for e in graph["edges"] if e["type"] == "CHART_CONNECTOR"):
        path = directory / f"clip_{i}.png"
        path.write_bytes(clip_image.tobytes("png"))
        observations.append({"matched_existing_edge_id": edge["id"],
            "existing_evidence_id": edge["evidence"]["evidence_id"],
            "existing_region_normalized_ymin_xmin_ymax_xmax": edge["region"],
            "clip_region_normalized_ymin_xmin_ymax_xmax": [.08, .08, .45, .85],
            "clip_pdf_points_xyxy": [8, 8, 85, 45], "render_scale": 8, "render_dpi": 576,
            "render_width_height_pixels": [clip_image.width, clip_image.height],
            "endpoint_node_ids": [edge["from"], edge["to"]],
            "render_relpath": path.name, "render_sha256": digest(path.read_bytes())})
    relative = lambda name: (directory / name).relative_to(root).as_posix()
    source = {"edition_id": edition, "source_identity_id": source_id, **locator,
        "pdf_relpath": relative("document.pdf"), "pdf_sha256": pdf_hash,
        "figure_region_normalized_ymin_xmin_ymax_xmax": locator["region"],
        "full_page_image_relpath": relative("page.png"), "full_page_image_sha256": digest(page_image),
        "retained_full_figure_crop_relpath": relative("crop.png"),
        "retained_full_figure_crop_sha256": digest(crop_image)}
    receipt = {"schema_version": "a2-whole-figure-connector-source-observation-1.0",
        "verification_state": "CANDIDATE_AI_VISUAL_OBSERVATION", "source": source,
        "inspection_method": {"human_inspection_or_approval": False, "owner_review_decision": None},
        "coverage": {"whole_A2_crop_visually_inspected": True,
            "visible_connection_count": len(observations), "matched_existing_connector_records": len(observations),
            "endpoint_contact_count": 2*len(observations), "endpoint_contacts_visually_inspected": 2*len(observations)},
        "source_observations": {"observation_text": "The inspected toy connectors show no visible pointer tips."},
        "connector_observations": observations}
    inventory = directory / "geometry.json"
    inventory.write_text(json.dumps({"segments": observations}), encoding="utf-8")
    receipt.update(geometry_inventory_relpath=inventory.name,
                   geometry_inventory_sha256=digest(inventory.read_bytes()))
    path = directory / "observation.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return graph, path, receipt


def test_candidate_visual_observation_is_source_bound_and_never_admitted(tmp_path, toy_graph):
    from src.evidence_a2 import load_candidate_source_observation, _attach_candidate_source_observation
    graph, path, receipt = candidate_observation_fixture(tmp_path, toy_graph)
    before = deepcopy(graph)
    evidence = load_candidate_source_observation(tmp_path, graph, path)
    assert evidence.verification == "candidate" and evidence.kind == "figure_region"
    assert evidence.content["knowledge_eligible"] is False
    answer = {"answer": "Existing qualified answer.", "operations": [
        {"kind": "epistemic_limits", "query_layer": "evidence", "answer_outcome": "graph_answer",
         "execution_status": "executed", "graph_executed": True}],
        "claims": [], "record_evidence_catalog": [], "semantic_completeness": {"status": "UNASSESSED"}}
    attached = _attach_candidate_source_observation(answer, evidence, query_layer="auto")
    assert receipt["source_observations"]["observation_text"] in attached["answer"]
    assert "candidate" in attached["answer"].lower() and evidence.evidence_id in attached["answer"]
    assert attached["candidate_claims"][0]["knowledge_eligible"] is False
    assert attached["claims"] == [] and attached["record_evidence_catalog"] == []
    assert attached["semantic_completeness"] == {"status": "UNASSESSED"}
    assert graph == before
    assert _attach_candidate_source_observation(answer, None, query_layer="auto") == answer


@pytest.mark.parametrize("change", ["source", "page", "state", "human", "owner", "edge", "region", "clip"])
def test_candidate_observation_rejects_tampered_source_or_authority(tmp_path, toy_graph, change):
    from src.evidence_a2 import load_candidate_source_observation
    graph, path, receipt = candidate_observation_fixture(tmp_path, toy_graph)
    if change == "source": receipt["source"]["pdf_sha256"] = "0" * 64
    if change == "page": receipt["source"]["pdf_index"] = 1
    if change == "state": receipt["verification_state"] = "ACCEPTED"
    if change == "human": receipt["inspection_method"]["human_inspection_or_approval"] = True
    if change == "owner": receipt["inspection_method"]["owner_review_decision"] = "approved"
    if change == "edge": receipt["connector_observations"][0]["existing_evidence_id"] = "invented"
    if change == "region": receipt["connector_observations"][0]["clip_region_normalized_ymin_xmin_ymax_xmax"] = [0, 0, 1, 1]
    if change == "clip": receipt["connector_observations"][0]["render_relpath"] = "../../outside.png"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="A2_(SOURCE_OBSERVATION|PRIVATE)"):
        load_candidate_source_observation(tmp_path, graph, path)


def test_candidate_observation_cannot_change_knowledge_or_literal_only_answers(tmp_path, toy_graph):
    from src.evidence_a2 import load_candidate_source_observation, _attach_candidate_source_observation
    graph, path, _ = candidate_observation_fixture(tmp_path, toy_graph)
    evidence = load_candidate_source_observation(tmp_path, graph, path)
    knowledge = {"answer": "Accepted answer.", "operations": [
        {"kind": "epistemic_limits", "query_layer": "knowledge", "answer_outcome": "graph_answer"}]}
    assert _attach_candidate_source_observation(knowledge, evidence, query_layer="knowledge") == knowledge
    literal = {"answer": "Toy code.", "operations": [{"kind": "designation", "query_layer": "evidence",
        "answer_outcome": "graph_answer", "execution_status": "executed", "graph_executed": True}]}
    attached = _attach_candidate_source_observation(literal, evidence, query_layer="auto")
    assert attached["answer"] == literal["answer"] and attached["candidate_claims"] == []


def test_candidate_clip_cannot_be_replaced_by_self_consistent_unrelated_image(tmp_path, toy_graph):
    import fitz
    from src.evidence_a2 import load_candidate_source_observation
    graph, path, receipt = candidate_observation_fixture(tmp_path, toy_graph)
    item = receipt["connector_observations"][0]
    width, height = item["render_width_height_pixels"]
    blank = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
    blank.clear_with(255)
    clip = path.parent / item["render_relpath"]
    clip.write_bytes(blank.tobytes("png"))
    item["render_sha256"] = hashlib.sha256(clip.read_bytes()).hexdigest()
    inventory = path.parent / receipt["geometry_inventory_relpath"]
    inventory.write_text(json.dumps({"segments": receipt["connector_observations"]}), encoding="utf-8")
    receipt["geometry_inventory_sha256"] = hashlib.sha256(inventory.read_bytes()).hexdigest()
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="A2_SOURCE_OBSERVATION_CLIP"):
        load_candidate_source_observation(tmp_path, graph, path)
