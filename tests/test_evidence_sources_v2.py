"""Redistributable synthetic checks for the native source extraction boundary."""
from pathlib import Path
from types import SimpleNamespace
import json
import sys

import pytest

from src import evidence_sources as sources


class SyntheticPage:
    rect = SimpleNamespace(width=600, height=800)

    def __init__(self, label, headers, cells, shifted=False):
        self.label, self.headers, self.cells, self.shifted = label, headers, cells, shifted

    def get_text(self, kind):
        assert kind == "dict"
        rows = [(200, 50, self.label), (100, 70, "Invented table title")]
        rows += [(x, 90, text) for x, text in zip((60, 220, 320, 500), self.headers * 2)]
        rows += [(60, 110, self.cells[0]), (220, 115 if self.shifted else 110, self.cells[1])]
        # Footer and license-like account stamp must never become table cells.
        rows += [(300, 750, "9"), (60, 770, "Accessed by account: SYNTHETIC")]
        lines = [{"bbox": (x, y, x + 80, y + 10), "spans": [{"text": text}]} for x, y, text in rows]
        return {"blocks": [{"lines": lines}]}


def test_derived_sqlite_identity_does_not_change_canonical_evidence_id(tmp_path, monkeypatch):
    text = "root face. An original synthetic definition for identity testing."
    (tmp_path / "parsed").mkdir()
    (tmp_path / "parsed/text_chunks.jsonl").write_text(json.dumps({
        "clause": "Clause 4", "pdf_page": 0, "chunk_id": "fixture:chunk", "content": text}), encoding="utf-8")
    class Pdf:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def __getitem__(self, index):
            return SimpleNamespace(get_text=lambda: text)
    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _: Pdf()))
    manifest = SimpleNamespace(document={"pages": [{"printed_label": "1"}]})
    monkeypatch.setattr(sources, "_spine_ids", lambda _: {"root face": "derived:one"})
    first = sources._definitions(tmp_path, manifest, "fixture:source:1", Path("unused"))[0]
    monkeypatch.setattr(sources, "_spine_ids", lambda _: {"root face": "derived:two"})
    second = sources._definitions(tmp_path, manifest, "fixture:source:1", Path("unused"))[0]
    assert first.evidence_id == second.evidence_id
    assert first.locator == second.locator
    assert first.relationships != second.relationships
    assert all(edge["verification"] == "candidate" for edge in first.relationships + second.relationships)


class SyntheticManifest:
    document = {"sha256": "a" * 64}

    def element(self, label):
        return {"title": "Invented test table", "anchors": [
            {"pdf_index": 0 if label == "Table A2" else 1, "printed_label": "1", "order": 0}]}


class SyntheticPdf:
    def __init__(self, shifted=False):
        self.pages = [SyntheticPage("Table A2", ["Process", "Letter Designation"], ["imaginary process", "XYZ"], shifted),
                      SyntheticPage("Table A3", ["Letter Designation", "Process"], ["XYZ", "imaginary process"])]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __getitem__(self, index):
        return self.pages[index]


def _install(monkeypatch, shifted=False):
    monkeypatch.setattr(sources, "_source", lambda _: (SyntheticManifest(), "synthetic@" + "a" * 64, Path("unused.pdf")))
    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _: SyntheticPdf(shifted)))


def test_exact_native_headers_and_cells_survive_without_footer(monkeypatch):
    _install(monkeypatch)
    payload = sources.extract_tables(Path("unused"))
    assert payload["counts"] == {"Table A2": 1, "Table A3": 1}
    forward, reverse = payload["evidence"]
    assert forward["content"]["headers"] == ["Process", "Letter Designation"]
    assert forward["content"]["cells"] == ["imaginary process", "XYZ"]
    assert reverse["content"]["cells"] == ["XYZ", "imaginary process"]
    assert forward["content"]["footnotes"] == []
    assert forward["verification"] == "source_bound"
    assert all("SYNTHETIC" not in repr(item) for item in payload["evidence"])


def test_ambiguous_native_cell_geometry_is_rejected(monkeypatch):
    _install(monkeypatch, shifted=True)
    with pytest.raises(ValueError, match="CELL_GEOMETRY_AMBIGUOUS"):
        sources.extract_tables(Path("unused"))


def test_requested_table_caption_must_exist():
    page = SyntheticPage("Table A8", ["Process", "Letter Designation"], ["imaginary process", "XYZ"])
    with pytest.raises(ValueError, match="CAPTION_AMBIGUOUS"):
        sources._table_lines(page, "Table A2")


@pytest.mark.parametrize("tamper", ["omit", "verification", "cell"])
def test_cache_must_reproduce_complete_native_projection(monkeypatch, tmp_path, tamper):
    _install(monkeypatch)
    payload = sources.extract_tables(tmp_path)
    payload["source_sha256"] = "a" * 64
    if tamper == "omit":
        payload["evidence"].pop()
    elif tamper == "verification":
        payload["evidence"][0]["verification"] = "reviewed"
    else:
        payload["evidence"][0]["content"]["cells"][1] = "MADEUP"
    path = tmp_path / sources.TABLE_CACHE
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    fake = sources._make("fixture:source", "figure_region", {"element_id": "Figure B6", "order": 0}, {"caption": "Synthetic"})
    monkeypatch.setattr(sources, "_definitions", lambda *args: [])
    monkeypatch.setattr(sources, "_figures", lambda *args: [fake])
    with pytest.raises(ValueError, match="CACHE_NOT_REPRODUCIBLE"):
        sources.load_source_evidence(tmp_path)
