"""Synthetic one-image scope contracts. No licensed source, service or model."""
import base64
from dataclasses import replace
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from src.evidence_v2 import Evidence, EvidenceStore, evidence_id
from src.evidence_reader import build_messages, read_packet
from evidence_v2_fixture import png_bytes


@pytest.fixture
def a1_source(tmp_path):
    """An original toy chart bound to exactly one image and its scope note."""
    edition = "fixture:a1-scope:1@" + hashlib.sha256(b"Original toy chart edition").hexdigest()

    def make(kind, locator, content, **kwargs):
        return Evidence(evidence_id(edition, kind, locator, content), edition,
                        kind, locator, content, "synthetic", **kwargs)

    note = make("note", {"element_id": "Annex A", "order": 0}, {
        "text": "This original toy chart supports only the labels visible on its one image.",
        "normative_status": "synthetic_scope_only", "qualifiers": [], "notes": [], "exceptions": []})
    original = png_bytes((61, 138, 91))
    path = tmp_path / "assets/a1.png"
    path.parent.mkdir()
    path.write_bytes(original)
    figure = make("figure_region", {
        "element_id": "Figure A1", "pdf_index": 0, "printed_page": "1", "order": 0,
        "region": [0.0, 0.0, 1.0, 1.0], "region_scope": "full_page"}, {
        "caption": "Original toy process classification chart",
        "asset_relpath": "assets/a1.png", "asset_sha256": hashlib.sha256(original).hexdigest(),
        "media_type": "image/png", "single_image_scope": True, "continuation_orders": [0],
        "identity_alternatives": ["Figure A1", "Table A1"],
        "required_evidence_ids": [note.evidence_id],
        "qualifiers": ["Answer only questions about the visible toy chart."],
        "exceptions": [], "notes": []}, required_ids=(note.evidence_id,))
    return EvidenceStore([figure, note]), figure, note, original


def image_payloads(messages):
    return [base64.b64decode(part["image_url"]["url"].split(",", 1)[1], validate=True)
            for message in messages if isinstance(message.get("content"), list)
            for part in message["content"] if part.get("type") == "image_url"]


def test_a1_packet_is_one_image_with_its_required_annex_a_note(a1_source, tmp_path):
    store, figure, note, original = a1_source
    packet = store.packet("Figure A1")
    assert packet.status == "complete"
    assert packet.route.kind == "visual"
    figures = [item for item in packet.evidence if item.kind == "figure_region"]
    assert figures == [figure]
    assert figure.content["single_image_scope"] is True
    assert figure.content["continuation_orders"] == [0]
    assert note.evidence_id in {item.evidence_id for item in packet.evidence}
    assert image_payloads(build_messages(packet, tmp_path)) == [original]


def test_ordinary_chart_question_reaches_reader_with_one_original_image(a1_source, tmp_path):
    store, figure, _, original = a1_source
    packet = store.packet("Which branch labels are visible in Figure A1?")
    seen = []

    def generate(messages):
        seen.append(messages)
        return {"claims": [{"text": "The original toy chart contains a colored field.",
                            "evidence_ids": [figure.evidence_id]}]}

    result = read_packet(packet, tmp_path, generate=generate)
    assert result["answer_outcome"] == "generated"
    assert len(seen) == 1
    assert image_payloads(seen[0]) == [original]
    assert result["answer_assessment"]["semantic_validation"] is False
    assert result["answer_assessment"]["validated"] is False


@pytest.mark.parametrize("query", [
    "Show Table A1.",
    "Compare Figure A1 and Figure B6.",
    "Compare Figure A1 and Figure A2.",
    "What does the next page add to Figure A1?",
    "Summarize all figures starting with Figure A1.",
    "Give the Clause 4 definition associated with Figure A1.",
    "Use Figure A1 and the other pages to give complete requirements.",
    "Figure A1 and B6",
    "Figure A1 and printed page 2",
    "Figure A1 PDF page 2",
    "Figure A1 PDF index 1",
])
def test_external_evidence_requests_stop_before_generation(a1_source, tmp_path, query):
    store, _, _, _ = a1_source
    packet = store.packet(query)
    assert packet.status == "insufficient_evidence"
    assert packet.missing

    def forbidden(_):
        pytest.fail("An A1 scope request requiring external evidence must not call a model")

    result = read_packet(packet, tmp_path, generate=forbidden)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["answer_origin"] == "none"
    assert result["grounded_claims"] == []
    assert result["answer_assessment"]["semantic_validation"] is False


def test_bare_a1_requires_figure_or_table_identity(a1_source):
    packet = a1_source[0].packet("A1")
    assert packet.status == "clarification_required"
    assert {a["headword"] for a in packet.route.alternatives} == {"Figure A1", "Table A1"}


def test_source_printed_and_pdf_locators_are_distinct(a1_source):
    store = a1_source[0]
    for query in ("Figure A1 printed page 1", "Figure A1 PDF page 1", "Figure A1 PDF index 0"):
        assert store.packet(query).status == "complete"


def test_standard_identifier_is_not_a_bare_foreign_figure(a1_source):
    assert a1_source[0].packet("Figure A1 in AWS A3.0:2020").status == "complete"


def test_comparison_uses_graph_subjects_within_one_image(a1_source):
    _, figure, note, _ = a1_source
    content = dict(figure.content, chart_graph={"selection": {"seed_ids": ["toy:a", "toy:b"]}})
    figure = replace(figure, content=content,
                     evidence_id=evidence_id(figure.edition_id, figure.kind, figure.locator, content))
    packet = EvidenceStore([figure, note]).packet("Compare the two toy branches in Figure A1")
    assert packet.route.kind == "comparison"
    assert packet.status == "complete"


def test_a1_dispatch_never_loads_unrelated_tables_or_b6(monkeypatch, tmp_path):
    from src import evidence_a1, evidence_sources
    sentinel = object()
    calls = []
    monkeypatch.setattr(evidence_a1, "load_a1_evidence", lambda root, query: calls.append((root, query)) or sentinel)
    monkeypatch.setattr(evidence_sources, "load_source_evidence", lambda _: pytest.fail("Unrelated corpus was loaded"))
    assert evidence_sources.load_query_evidence(tmp_path, "Figure A1") is sentinel
    assert calls == [(tmp_path, "Figure A1")]


def test_table_a1_never_reuses_the_figure_a1_asset(a1_source, tmp_path):
    store, _, _, _ = a1_source
    packet = store.packet("Table A1")
    assert packet.status == "insufficient_evidence"
    assert packet.evidence == ()
    result = read_packet(packet, tmp_path)
    assert result["resolved_figures"] == []
    assert result["grounded_claims"] == []


def test_single_image_scope_does_not_relax_other_figures_continuation_requirements(a1_source, tmp_path):
    _, figure, note, _ = a1_source
    missing_id = "ev2:" + "f" * 64
    locator = dict(figure.locator, element_id="Figure X2")
    content = dict(figure.content, continuation_orders=[0, 1],
                   required_evidence_ids=[note.evidence_id, missing_id])
    content.pop("single_image_scope")
    incomplete = replace(figure, locator=locator, content=content,
                         evidence_id=evidence_id(figure.edition_id, figure.kind, locator, content),
                         required_ids=(note.evidence_id, missing_id))
    packet = EvidenceStore([incomplete, note]).packet("Figure X2")
    assert packet.status == "insufficient_evidence"
    assert "figure_continuations_incomplete:Figure X2" in packet.missing

    def forbidden(_):
        pytest.fail("An absent required continuation must not be treated as a one-image scope")

    assert read_packet(packet, tmp_path, generate=forbidden)["grounded_claims"] == []
