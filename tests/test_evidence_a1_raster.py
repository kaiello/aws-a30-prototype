"""Source-free raster geometry checks with explicitly mocked OCR TSV.

OpenCV reads real synthetic pixels; the OCR boundary is mocked for deterministic
labels and word coordinates. These checks establish no actual-chart OCR accuracy.
"""
from copy import deepcopy
import hashlib
import json

import cv2
import numpy as np
import pytest

from src import evidence_a1_raster as raster


TSV_HEADER = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"


def _draw_toy_chart(tmp_path, *, second_root=False):
    """Draw original boxes/lines/text and return their mocked OCR word TSV."""
    image = np.full((600, 800, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (40, 50), (340, 290), (0, 0, 0), 2)
    cv2.rectangle(image, (540, 140), (720, 220), (0, 0, 0), 2)
    cv2.line(image, (340, 180), (540, 180), (0, 0, 0), 2)
    rows = [TSV_HEADER]

    def words(text, left, top, block, line):
        for number, word in enumerate(text.split(), 1):
            (width, height), baseline = cv2.getTextSize(
                word, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.putText(image, word, (left, top + height),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
            rows.append("\t".join(map(str, (
                5, 1, block, 1, line, number, left, top, width,
                height + baseline, 95, word))))
            left += width + 8

    words("SAMPLE FAMILY", 65, 70, 1, 1)
    words("Ribbon fold (QXA)", 65, 110, 1, 2)
    words("Pulse fold (QXB)", 90, 150, 1, 3)
    words("Loop fold", 65, 190, 1, 4)
    words("QXC", 280, 190, 1, 4)
    words("TOY CHART", 565, 165, 2, 1)
    if second_root:
        cv2.rectangle(image, (540, 340), (720, 420), (0, 0, 0), 2)
        words("OTHER ROOT", 560, 365, 3, 1)
    path = tmp_path / ("ambiguous-toy.png" if second_root else "toy.png")
    assert cv2.imwrite(str(path), image)
    return path, "\n".join(rows) + "\n"


def test_mocked_ocr_preserves_labels_codes_and_candidate_pixel_geometry(monkeypatch, tmp_path):
    path, mocked_ocr_tsv = _draw_toy_chart(tmp_path)
    monkeypatch.setattr(raster, "_run_tesseract", lambda *args: mocked_ocr_tsv)

    result = raster.extract_raster_chart(path, "fixture:raster-toy")

    assert result["coverage_established"] is False
    assert result["engine"] and result["version"]
    assert result["observations"]
    graph = result["graph"]
    assert graph["schema_version"] == "a1-geometry-1.0"
    assert graph["region_space"] == "normalized_pdf_page_ymin_xmin_ymax_xmax"
    root = next(node for node in graph["nodes"] if node["kind"] == "root")
    category = next(node for node in graph["nodes"] if node["kind"] == "category")
    processes = {node["code"]: node for node in graph["nodes"] if node["kind"] == "process"}
    assert graph["root_id"] == root["id"]
    assert root["label"] == "TOY CHART"
    assert category["label"] == "SAMPLE FAMILY"
    assert {code: node["label"] for code, node in processes.items()} == {
        "QXA": "Ribbon fold", "QXB": "Pulse fold", "QXC": "Loop fold"}
    assert root["region"] == pytest.approx([140 / 600, 540 / 800, 220 / 600, 720 / 800], abs=0.015)
    for record in graph["nodes"] + graph["edges"]:
        ymin, xmin, ymax, xmax = record["region"]
        assert 0 <= ymin < ymax <= 1 and 0 <= xmin < xmax <= 1
    relations = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
    assert (root["id"], category["id"], "CHART_CONNECTOR") in relations
    assert {(category["id"], node["id"], "ENCLOSES_ROW") for node in processes.values()} <= relations
    assert (processes["QXA"]["id"], processes["QXB"]["id"], "INDENTED_UNDER") in relations
    assert {edge["type"] for edge in graph["edges"]} == {
        "CHART_CONNECTOR", "ENCLOSES_ROW", "INDENTED_UNDER"}
    for kind in ("CHART_CONNECTOR", "ENCLOSES_ROW", "INDENTED_UNDER"):
        assert graph["edge_qualifications"][kind]["verification"] == "candidate"
        assert graph["edge_qualifications"][kind]["qualification"]


def test_mocked_ocr_ambiguous_root_is_unresolved_without_fabricated_graph(monkeypatch, tmp_path):
    path, mocked_ocr_tsv = _draw_toy_chart(tmp_path, second_root=True)
    monkeypatch.setattr(raster, "_run_tesseract", lambda *args: mocked_ocr_tsv)

    result = raster.extract_raster_chart(path, "fixture:raster-ambiguous")

    assert result["graph"] is None
    assert result["observations"]
    assert result["diagnostics"]["unresolved_visual_structures"]
    assert result["coverage_established"] is False


def test_mocked_ocr_empty_text_is_unresolved_without_fabricated_root(monkeypatch, tmp_path):
    path, _ = _draw_toy_chart(tmp_path)
    monkeypatch.setattr(raster, "_run_tesseract", lambda *args: TSV_HEADER + "\n")

    result = raster.extract_raster_chart(path, "fixture:raster-empty")

    assert result["graph"] is None
    assert any(item["kind"] == "visual_rectangle" for item in result["observations"])
    assert not any(item["kind"] in {"ocr_word", "ocr_row"} for item in result["observations"])
    assert not any(item.get("text") for item in result["observations"])
    assert result["diagnostics"]["unresolved_visual_structures"]
    assert result["coverage_established"] is False


def test_invalid_image_path_and_unsupported_engine_fail_before_ocr(monkeypatch, tmp_path):
    def unexpected_ocr(*args):
        raise AssertionError("Invalid input must fail before OCR is invoked.")

    monkeypatch.setattr(raster, "_run_tesseract", unexpected_ocr)
    with pytest.raises(FileNotFoundError):
        raster.extract_raster_chart(tmp_path / "missing.png", "fixture:raster-missing")
    path, _ = _draw_toy_chart(tmp_path)
    with pytest.raises(ValueError):
        raster.extract_raster_chart(path, "fixture:raster-engine", ocr_engine="unsupported")


def test_cached_missing_root_projects_candidates_without_ocr_cv_or_input_mutation(monkeypatch):
    edition, image_hash = "fixture:cached-raster", "1"*64
    observations = []

    def observation(identifier, kind, box, **fields):
        x,y,w,h = box
        record = {"id":identifier,"kind":kind,"pixel_bbox":box,"region":[y/600,x/800,(y+h)/600,(x+w)/800],
                  "edition_id":edition,"image_sha256":image_hash,"verification":"candidate",**fields}
        observations.append(record)
        return record

    observation("rectangle:category","visual_rectangle",[40,50,300,240])
    for prefix,text,x,y in [("heading","SAMPLE FAMILY",65,70),("first","Ribbon fold (QXA)",65,110),
                             ("second","Pulse fold (QXB)",90,150)]:
        identifiers = []
        for index,word in enumerate(text.split()):
            identifier = f"word:{prefix}:{index}"
            observation(identifier,"ocr_word",[x+index*65,y,60,20],text=word,confidence=95)
            identifiers.append(identifier)
        observation(f"row:{prefix}","ocr_row",[x,y,len(identifiers)*65-5,20],text=text,confidence=95,
                    word_observation_ids=identifiers)
    observation("word:root:1","ocr_word",[550,150,35,20],text="TOY",confidence=95)
    observation("word:root:2","ocr_word",[590,150,55,20],text="CHART",confidence=95)
    cached = {"graph":None,"input":{"edition_id":edition,"image_sha256":image_hash,"width":800,"height":600},
              "observations":observations,"diagnostics":{"unresolved_visual_structures":[{"kind":"root_box_not_unique"}]},
              "engine":"tesseract+opencv","version":"frozen-extraction-version","coverage_established":False}
    original = deepcopy(cached)

    def forbidden(*args, **kwargs):
        raise AssertionError("Cached projection must not rerun OCR, CV or image metadata commands.")

    for name in ("_run_tesseract","_rectangles","_connector_contacts","_engine_version"):
        monkeypatch.setattr(raster,name,forbidden)
    result = raster.rebuild_partial_from_observations(cached)
    assert cached==original
    assert result["graph"] is None and result["coverage_established"] is False
    graph = result["partial_graph"]
    assert graph["root_id"] is None and not any(node["kind"]=="root" for node in graph["nodes"])
    assert {node["code"]:node["label"] for node in graph["nodes"] if node["kind"]=="process"}=={
        "QXA":"Ribbon fold","QXB":"Pulse fold"}
    assert {edge["type"] for edge in graph["edges"]}=={"ENCLOSES_ROW","INDENTED_UNDER"}
    assert all(item["verification"]=="candidate" for item in [*graph["nodes"],*graph["edges"],*graph["edge_qualifications"].values()])
    assert result["bootstrap_words"]==[{"id":item["id"],"text":item["text"],"region":item["region"]}
                                       for item in observations if item["kind"]=="ocr_word"]
    assert result["projection"]["source_extraction_version"]=="frozen-extraction-version"
    assert result["projection"]["ocr_invocations"]==result["projection"]["cv_invocations"]==0


def _dictionary(entries, edition="fixture:assisted"):
    value = {"schema_version":"a1-normalization-dictionary-1.0", "source":{
        "edition_id":edition,"source_identity_id":"fixture:source", "asset_sha256":"1"*64,
        "lexicon_version":"fixture:lexicon"}, "entries":entries}
    value["content_sha256"] = hashlib.sha256(json.dumps(value,sort_keys=True,
        separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return value


def test_dictionary_matches_observed_pairs_without_filling_missing_or_conflicting_codes():
    entries = [{"kind":"process","label":"Ribbon fold","code":"QXA-I"},
               {"kind":"process","label":"Pulse fold","code":"QXB"}]
    corrected = {"text":"Ribbon fold QXA-|"}
    assert raster._normalize_observed_row(corrected, entries) == entries[0]
    assert corrected["text"] == "Ribbon fold QXA-|"
    assert corrected["normalization"]["method"] == "exact_name_single_code_edit"
    for text in ("Ribbon fold", "Ribbon fold QXB", "Unknown fold QXA-I"):
        row = {"text":text}
        assert raster._normalize_observed_row(row, entries) is None
        assert "normalized_identity" not in row


def test_multiline_root_identity_requires_the_observed_full_label():
    entries = [{"kind":"root","label":"TOY AND SAMPLE PROCESSES"}]
    group = {"rows":[{"text":text} for text in ("TOY","AND","SAMPLE","PROCESSES")]}
    assert raster._assisted_group_identity(group, entries) == entries[0]
    incomplete = {"rows":[{"text":"TOY"},{"text":"AND"},{"text":"SAMPLE"}]}
    assert raster._assisted_group_identity(incomplete, entries) is None


def test_dictionary_assisted_extraction_preserves_raw_ocr_and_never_adds_absent_entries(monkeypatch, tmp_path):
    path, mocked_ocr_tsv = _draw_toy_chart(tmp_path)
    monkeypatch.setattr(raster,"_run_tesseract",lambda *args:mocked_ocr_tsv)
    dictionary = _dictionary([
        {"kind":"root","label":"TOY CHART"},
        {"kind":"category","label":"SAMPLE FAMILY"},
        {"kind":"process","label":"Ribbon fold","code":"QXA"},
        {"kind":"process","label":"Pulse fold","code":"QXB"},
        {"kind":"process","label":"Loop fold","code":"QXC"},
        {"kind":"process","label":"Absent fold","code":"QXD"}])
    result = raster.extract_raster_chart(path,"fixture:assisted",dictionary=dictionary)
    graph = result["graph"]
    assert graph is not None
    assert {node["code"] for node in graph["nodes"] if node["kind"]=="process"} == {"QXA","QXB","QXC"}
    assert result["dictionary_assistance"]["content_sha256"] == dictionary["content_sha256"]
    assert any(item.get("text")=="Ribbon fold (QXA)" for item in result["observations"])
    assert all(record["verification"]=="candidate" for record in graph["nodes"]+graph["edges"])
    assert result["coverage_established"] is False


def test_dictionary_rejects_relationship_or_geometry_fields_before_ocr(monkeypatch, tmp_path):
    path, _ = _draw_toy_chart(tmp_path)
    dictionary = _dictionary([{"kind":"process","label":"Ribbon fold","code":"QXA","parent":"invented"}])
    monkeypatch.setattr(raster,"_run_tesseract",lambda *args:pytest.fail("Invalid dictionary reached OCR"))
    with pytest.raises(ValueError,match="ENTRIES_INVALID"):
        raster.extract_raster_chart(path,"fixture:assisted",dictionary=dictionary)


def test_assisted_border_repair_closes_only_small_raster_corner_gaps():
    image = np.full((600,800,3),255,dtype=np.uint8)
    cv2.line(image,(42,50),(340,50),(0,0,0),1)
    cv2.line(image,(40,52),(40,290),(0,0,0),1)
    cv2.line(image,(340,50),(340,290),(0,0,0),1)
    cv2.line(image,(40,290),(340,290),(0,0,0),1)
    boxes, _ = raster._rectangles(image,repair_border_gaps=True)
    assert any(abs(box[0]-40)<=2 and abs(box[1]-50)<=2 and abs(box[0]+box[2]-341)<=2 and abs(box[1]+box[3]-291)<=2
               for box in boxes)
