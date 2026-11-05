"""Gate 6.7 source packets use source bytes, never an application answer."""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
from pathlib import Path

import fitz
import pytest

from src.independent_source_packets import build_source_packet


@pytest.fixture
def source_pdf(tmp_path):
    source_path = tmp_path / "source.pdf"
    with fitz.open() as document:
        for index in range(15):
            page = document.new_page(width=240, height=160)
            page.insert_text((20, 35), f"Native source page {index}")
        document.save(source_path)
    source = {
        "path": "source.pdf",
        "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "page_count": 15,
    }
    evidence = [{
        "evidence_id": "aws2020:pdf:13:full",
        "pdf_index": 13,
        "viewer_page": 14,
        "printed_page": 1,
        "crop": None,
        "locator": "HAND-PICKED GOLD HINT",
    }]
    return tmp_path, source, evidence


def test_packet_contains_native_text_image_and_hashes_without_gold_hints(source_pdf):
    root, source, evidence = source_pdf
    source["answer"] = "LEAKED ANSWER"
    evidence[0].update({
        "expected_status": "ANSWERED",
        "claims": [{"description": "LEAKED CLAIM"}],
        "source_adjudication": {"human_checked": True},
        "answer": "LEAKED ANSWER",
    })
    with fitz.open(root / source["path"]) as document:
        native_text = document[13].get_text()
        native_image = document[13].get_pixmap(dpi=120).tobytes("png")
    evidence[0]["page_text_sha256"] = hashlib.sha256(native_text.encode("utf-8")).hexdigest()
    original = deepcopy(evidence)

    packet = build_source_packet(root, source, "Read this source", evidence)

    assert packet["question"] == "Read this source"
    assert packet["page_budget"] == 2
    assert packet["rendering_dpi"] == 120
    assert packet["source_sha256"] == source["sha256"]
    assert packet["source_page_count"] == 15
    page = packet["evidence"][0]
    assert page["text"] == native_text
    assert page["text_sha256"] == hashlib.sha256(native_text.encode("utf-8")).hexdigest()
    assert base64.b64decode(page["image_base64"]) == native_image
    assert page["image_sha256"] == hashlib.sha256(native_image).hexdigest()
    assert page["source_sha256"] == source["sha256"]
    assert page["locator"] == "AWS A3.0M/A3.0:2020 source page"
    assert set(page) == {
        "evidence_id", "pdf_index", "viewer_page", "printed_page", "locator", "crop",
        "source_sha256", "text_sha256", "image_sha256", "text", "image_base64",
    }
    assert "LEAKED" not in str(packet)
    assert "source_adjudication" not in str(packet)
    assert evidence == original


def test_same_source_page_has_same_packet_despite_gold_or_retrieved_hints(source_pdf):
    root, source, evidence = source_pdf
    other = deepcopy(evidence)
    other[0]["locator"] = "UNRELATED APP LOCATOR"
    other[0]["claims"] = ["an answer"]
    assert build_source_packet(root, source, "q", evidence) == build_source_packet(root, source, "q", other)


def test_empty_retrieved_packet_preserves_verified_source_identity(source_pdf):
    root, source, _ = source_pdf
    packet = build_source_packet(root, source, "What is supported?", [])
    assert packet["evidence"] == []
    assert packet["source_sha256"] == source["sha256"]
    assert packet["source_page_count"] == 15


@pytest.mark.parametrize("change", [
    {"evidence_id": "anything-else"},
    {"evidence_id": "aws2020:pdf:14:full"},
    {"viewer_page": 15},
    {"printed_page": 2},
    {"pdf_index": -1},
    {"pdf_index": 15, "viewer_page": 16, "printed_page": 3, "evidence_id": "aws2020:pdf:15:full"},
    {"pdf_index": True},
    {"crop": [0, 0, 1, 1]},
    {"page_text_sha256": "0" * 64},
])
def test_rejects_invalid_source_binding(source_pdf, change):
    root, source, evidence = source_pdf
    evidence[0].update(change)
    with pytest.raises(ValueError):
        build_source_packet(root, source, "q", evidence)


def test_rejects_duplicate_ids_and_exceeded_page_budget(source_pdf):
    root, source, evidence = source_pdf
    with pytest.raises(ValueError, match="duplicate"):
        build_source_packet(root, source, "q", evidence + evidence)
    second = {**evidence[0], "pdf_index": 14, "viewer_page": 15, "printed_page": 2,
              "evidence_id": "aws2020:pdf:14:full"}
    with pytest.raises(ValueError, match="budget"):
        build_source_packet(root, source, "q", evidence + [second], max_pages=1)


@pytest.mark.parametrize("source_change", [
    {"sha256": "0" * 64}, {"page_count": 14}, {"page_count": True},
])
def test_rejects_source_corruption_even_for_empty_evidence(source_pdf, source_change):
    root, source, _ = source_pdf
    source.update(source_change)
    with pytest.raises(ValueError):
        build_source_packet(root, source, "q", [])


def test_rejects_path_traversal_and_absolute_paths(source_pdf):
    root, source, _ = source_pdf
    source["path"] = "../outside.pdf"
    with pytest.raises(ValueError, match="path"):
        build_source_packet(root, source, "q", [])
    source["path"] = str(root / "source.pdf")
    with pytest.raises(ValueError, match="path"):
        build_source_packet(root, source, "q", [])


def test_rejects_symlink_escape(source_pdf):
    root, source, _ = source_pdf
    link = root / "linked.pdf"
    outside = root.parent / "outside-source.pdf"
    outside.write_bytes((root / "source.pdf").read_bytes())
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"Host does not permit symlink creation: {error}")
    source["path"] = "linked.pdf"
    with pytest.raises(ValueError, match="path"):
        build_source_packet(root, source, "q", [])


@pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": True}, {"dpi": 0}, {"dpi": True}])
def test_rejects_invalid_budgets_and_rendering_configuration(source_pdf, options):
    root, source, evidence = source_pdf
    with pytest.raises(ValueError):
        build_source_packet(root, source, "q", evidence, **options)
