"""Synthetic adapter boundaries; no licensed labels or answer keys."""
from pathlib import Path

import numpy as np
import pytest

from src.evidence_a2 import (_chart_closure, _heading_rows, _line_interval, _literal, _page_region,
    _physical_connectors, _pixel_box, _private, _row_fields, _uncovered_text_bands, run_questions)


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
