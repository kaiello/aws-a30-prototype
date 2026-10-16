"""Complete references/assets using synthetic metadata; no PDF/models/stores."""
import hashlib
from pathlib import Path
import re

import pytest

import src.standard_manifest as reader
from src.standard_manifest import extract_reference_records


class SyntheticManifest:
    def __init__(self, *, panel_alias=False):
        self.names = {"figures": ["Figure A1", "Figure B1", "Figure B2", "Figure B3", "Figure B6",
                                   "Figure B14", "Figure B14A", "Figure B15", "Figure B16A",
                                   "Figure B16B", "Figure B16C", "Figure B17", "Figure B54"],
                      "tables": ["Table D1", "Table D2", "Table D3"],
                      "sections": ["Clause 4", "Annex A"]}
        self.panel_alias = panel_alias
        self.document = {"id": "doc:synthetic", "sha256": "a" * 64,
                         "pages": [{"pdf_index": index, "printed_label": label} for index, label in
                                   enumerate([None, "ii", "7", "8", "9", "87", "88", "89"])]}

    def labels(self, kind):
        return tuple(self.names[kind])

    def resolve(self, value):
        key = " ".join(str(value).split()).casefold()
        key = re.sub(r"^fig\.? ", "figure ", key)
        key = re.sub(r"(?<=[abd])\.(?=\d)", "", key)
        if key == "figure b14(a)" and self.panel_alias:
            key = "figure b14a"
        if key == "figure b16":
            labels = ["Figure B16A", "Figure B16B", "Figure B16C"]
            return {"status": "group", "labels": labels, "target_ids": [self.identity(label) for label in labels]}
        for label in sum(self.names.values(), []):
            if label.casefold() == key:
                return {"status": "exact", "labels": [label], "target_ids": [self.identity(label)]}
        return {"status": "unknown", "labels": [], "target_ids": []}

    @staticmethod
    def identity(label):
        kind = "figure" if label.startswith("Figure") else "table" if label.startswith("Table") else "clause"
        return kind + ":" + label.casefold().replace(" ", "_")


@pytest.fixture
def manifest():
    return SyntheticManifest()


def assert_span(text, record):
    assert record["raw"] == text[record["start"]:record["end"]]
    assert record["span_space"] == "half_open_unicode_characters"


def test_complete_records_retain_occurrence_order_and_unicode_character_spans(manifest):
    text = "🔎 Figure B2 supports this; Table D1 follows. Figure B2 repeats; Figure B1 ends."
    records = extract_reference_records(text, manifest=manifest)
    assert [record["raw"] for record in records] == ["Figure B2", "Table D1", "Figure B2", "Figure B1"]
    assert [record["order"] for record in records] == list(range(4))
    assert records[0]["start"] == 2
    assert [record["kind"] for record in records] == ["figure", "table", "figure", "figure"]
    for record in records:
        assert_span(text, record)
        assert record["resolution"]["status"] == "exact"


def test_range_remains_one_complete_record_with_all_ordered_members(manifest):
    text = "Use Figures B1–B3, then stop."
    records = extract_reference_records(text, manifest=manifest)
    assert len(records) == 1
    record = records[0]
    assert record["raw"] == "Figures B1–B3"
    assert record["requested_label"] == "Figure B1–B3"
    assert record["resolution"] == {"status": "exact", "labels": ["Figure B1", "Figure B2", "Figure B3"],
                                     "target_ids": ["figure:figure_b1", "figure:figure_b2", "figure:figure_b3"]}
    assert_span(text, record)


def test_single_element_labels_are_canonical_while_full_requests_survive(manifest):
    records=extract_reference_records('Fig.B.16C; Figure B14(Z)',manifest=manifest)
    assert [r['requested_label'] for r in records]==['Figure B16C','Figure B14']
    assert records[1]['raw']=='Figure B14(Z)' and records[1]['qualifiers']['panel']=='(Z)'
    assert records[1]['resolution']['status']=='unsupported_qualifier'
    alias=extract_reference_records('Figure B14(A)',manifest=SyntheticManifest(panel_alias=True))[0]
    assert alias['requested_label']=='Figure B14A' and alias['raw']=='Figure B14(A)'
    grouped=extract_reference_records('Figures B14(Z), B1',manifest=manifest)[0]
    assert grouped['raw']=='Figures B14(Z), B1'
    assert 'B14(Z)' in grouped['requested_label'] and 'B1' in grouped['requested_label']


def test_plural_list_is_one_record_and_preserves_first_member_order(manifest):
    records = extract_reference_records("Figures B2, B1, and B2", manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == "Figures B2, B1, and B2"
    assert records[0]["resolution"]["labels"] == ["Figure B2", "Figure B1"]


@pytest.mark.parametrize("mention", [
    "Figures B54–B55", "Figures B3–B1", "Figures A1–B3", "Figures B15–B17",
    "Figures B16A–B16C", "Figure B1 to B3", "Figure B1 through Fig.B3", "Figures B1/B3",
])
def test_invalid_whole_range_is_one_unresolved_record_without_endpoint_promotion(mention, manifest):
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert records[0]["resolution"]["status"] != "exact"
    assert_span(mention, records[0])


@pytest.mark.parametrize("mention,panel", [
    ("Figure B14(A)", "(A)"), ("Figure B14(Z)", "(Z)"),
    ("Figure B14 (A)", "(A)"), ("Figure B14(A)–(C)", "(A)–(C)"),
    ("Figure B14(A), (C)", "(A), (C)"), ("Figure B14(A) and (C)", "(A) and (C)"),
    ("Figure B14(A", "(A"),
])
def test_parenthesized_panel_request_is_complete_and_never_exact_parent_support(mention, panel, manifest):
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    record = records[0]
    assert record["raw"] == mention
    assert record["qualifiers"]["panel"] == panel
    assert record["resolution"] == {"status": "unsupported_qualifier", "labels": ["Figure B14"],
                                     "target_ids": ["figure:figure_b14"]}
    assert_span(mention, record)


def test_declared_full_panel_alias_is_resolved_only_as_the_declared_target():
    record = extract_reference_records("Figure B14(A)", manifest=SyntheticManifest(panel_alias=True))[0]
    assert record["requested_label"] == "Figure B14A"
    assert record["qualifiers"]["panel"] == "(A)"
    assert record["resolution"] == {"status": "exact", "labels": ["Figure B14A"],
                                     "target_ids": ["figure:figure_b14a"]}


def test_canonical_caption_suffix_is_distinct_from_panel_and_group(manifest):
    records = extract_reference_records("Figure B16C; Figure B16(C); Figure B16", manifest=manifest)
    assert records[0]["resolution"]["status"] == "exact"
    assert records[0]["resolution"]["labels"] == ["Figure B16C"]
    assert not records[0]["qualifiers"].get("panel")
    assert records[1]["resolution"]["status"] == "unsupported_qualifier"
    assert records[1]["qualifiers"]["panel"] == "(C)"
    assert records[2]["resolution"]["status"] == "group"
    assert records[2]["resolution"]["labels"] == ["Figure B16A", "Figure B16B", "Figure B16C"]


@pytest.mark.parametrize("page", ["p. 8", "page 999", "pp. 87–89", "pages 7-9"])
def test_attached_page_qualifier_is_preserved_without_invented_page_support(page, manifest):
    mention = "Figure B6, " + page
    record = extract_reference_records(mention, manifest=manifest)[0]
    assert record["raw"] == mention
    assert record["qualifiers"]["page"] == page
    assert record["requested_label"] == "Figure B6"
    assert record["resolution"]["labels"] == ["Figure B6"]
    assert_span(mention, record)


def test_panel_and_page_qualifiers_survive_together_before_independent_reference(manifest):
    text = "Figure B14(Z), p. 8; Table D1, page 9."
    records = extract_reference_records(text, manifest=manifest)
    assert [record["raw"] for record in records] == ["Figure B14(Z), p. 8", "Table D1, page 9"]
    assert records[0]["qualifiers"] == {"panel": "(Z)", "page": "p. 8"}
    assert records[0]["resolution"]["status"] == "unsupported_qualifier"
    assert records[1]["resolution"]["status"] == "exact"


def test_prose_after_reference_is_not_consumed_as_range_or_qualifier(manifest):
    text = "Use Figure B1 to explain the weld; the figure shows detail."
    records = extract_reference_records(text, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == "Figure B1"
    assert records[0]["resolution"]["status"] == "exact"


@pytest.mark.parametrize("mention", ["Figure B14(A)", "Figure B14(Z)", "Figure B14(A)–(C)"])
def test_legacy_extraction_fails_closed_for_unsupported_panel_but_keeps_independent_reference(mention, manifest, monkeypatch):
    monkeypatch.setattr(reader, "get_manifest", lambda: manifest)
    result = reader.extract_references(mention + "; Figure B2")
    assert result["figures"] == ["Figure B2"]
    assert result["tables"] == [] and result["clauses"] == []
    assert len(result["unresolved_elements"]) == 1
    assert result["unresolved_elements"][0]["text"] == mention
    assert result["unresolved_elements"][0]["status"] == "unsupported_qualifier"
    assert set(result) == {"figures", "tables", "clauses", "unresolved_elements"}


@pytest.mark.parametrize("mention,labels,indices", [
    ("p. 8", ["8"], [3]), ("page ii", ["ii"], [1]), ("pp. 7–9", ["7", "8", "9"], [2, 3, 4]),
])
def test_standalone_printed_page_records_are_candidates_not_exact_element_support(mention, labels, indices, manifest):
    record = extract_reference_records(mention, manifest=manifest)[0]
    assert record["kind"] == "page"
    assert record["raw"] == mention
    assert record["resolution"] == {"status": "page_only", "labels": [], "target_ids": []}
    assert record["qualifiers"] == {"panel": None, "page": mention}
    assert record["page_candidates"] == [{"pdf_index": index, "pdf_page_ordinal": index + 1, "printed_label": label}
                                         for index, label in zip(indices, labels)]
    assert_span(mention, record)


@pytest.mark.parametrize("mention", ["p. 999", "page iv", "pages 9–7", "pp. 8–999"])
def test_unknown_or_invalid_standalone_page_set_never_returns_partial_candidates(mention, manifest):
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert records[0]["resolution"] == {"status": "unknown", "labels": [], "target_ids": []}
    assert records[0]["page_candidates"] == []


def test_attached_page_qualifier_is_not_emitted_again_as_standalone_record(manifest):
    text = "Annex A, p. 8; p. 9; Figure B6, pp. 87–89"
    records = extract_reference_records(text, manifest=manifest)
    assert [record["raw"] for record in records] == ["Annex A, p. 8", "p. 9", "Figure B6, pp. 87–89"]
    assert [record["order"] for record in records] == [0, 1, 2]
    assert [record["kind"] for record in records] == ["annex", "page", "figure"]


@pytest.mark.parametrize("mention,label", [
    ("Fig.B.16C", "Figure B16C"), ("FigureB3", "Figure B3"),
    ("TableD1", "Table D1"), ("fig.b1", "Figure B1"),
])
def test_complete_records_include_existing_singular_shorthand(mention, label, manifest):
    text = "Use " + mention + "; stop."
    records = extract_reference_records(text, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert records[0]["resolution"] == {"status": "exact", "labels": [label],
                                        "target_ids": [manifest.identity(label)]}
    assert_span(text, records[0])


def test_shorthand_retains_full_unsupported_panel_and_attached_page(manifest):
    mention = "Fig.B.14(Z), p. 8"
    record = extract_reference_records(mention, manifest=manifest)[0]
    assert record["raw"] == mention
    assert record["qualifiers"] == {"panel": "(Z)", "page": "p. 8"}
    assert record["resolution"]["status"] == "unsupported_qualifier"
    assert record["resolution"]["labels"] == ["Figure B14"]


def test_shorthand_unsupported_word_range_never_leaks_an_endpoint_record(manifest):
    mention = "FigureB1 to Fig.B3"
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert records[0]["resolution"]["status"] == "unknown"
    assert records[0]["resolution"]["labels"] == []


def _asset_manifest(tmp_path, states):
    """Shuffled declarations expose canonical anchor order and isolated failures."""
    assets = []
    for order, state in enumerate(states):
        relpath = f"parsed/figures/synthetic_{order}.png"
        expected = f"synthetic asset {order}".encode("ascii")
        path = tmp_path / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        if state != "missing":
            path.write_bytes(b"changed synthetic bytes" if state == "corrupt" else expected)
        assets.append({"relpath": relpath, "sha256": hashlib.sha256(expected).hexdigest(),
                       "source_anchor_orders": [order], "verification": {"state": "verified"}})
    element = {"id": "figure:synthetic", "label": "Figure B6", "assets": list(reversed(assets)),
               "anchors": [{"verification": {"state": "verified"}}]}
    data = {"document": {}, "sections": [], "figures": [element], "tables": [],
            "links": [], "legacy_aliases": []}
    return reader.StandardManifest(data, tmp_path), assets


def _block_synthetic_asset(monkeypatch, path):
    original = Path.read_bytes

    def read_bytes(candidate):
        if candidate == path:
            raise PermissionError("synthetic unavailable asset")
        return original(candidate)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)


@pytest.mark.parametrize("failure,error_code", [
    ("missing", "MANIFEST_ASSET_MISSING"), ("corrupt", "MANIFEST_ASSET_MISMATCH"),
    ("unavailable", "MANIFEST_ASSET_UNAVAILABLE"),
])
def test_validated_assets_preserves_later_healthy_subset_in_canonical_order(tmp_path, monkeypatch, failure, error_code):
    manifest, canonical = _asset_manifest(tmp_path, ["complete", failure, "complete"])
    if failure == "unavailable":
        _block_synthetic_asset(monkeypatch, tmp_path / canonical[1]["relpath"])
    before = manifest.element("Figure B6")
    records = manifest.validated_assets("Figure B6")
    assert [record["status"] for record in records] == ["complete", failure, "complete"]
    assert [record["error_code"] for record in records] == [None, error_code, None]
    for record, declared in zip(records, canonical):
        assert {key: record[key] for key in declared} == declared
        assert record["path"] == str(tmp_path / declared["relpath"])
    assert [record["path"] for record in records if record["status"] == "complete"] == [
        str(tmp_path / canonical[index]["relpath"]) for index in [0, 2]]
    records[0]["source_anchor_orders"].append(99)
    assert manifest.element("Figure B6") == before


@pytest.mark.parametrize("failure,error_code", [
    ("missing", "MANIFEST_ASSET_MISSING"), ("corrupt", "MANIFEST_ASSET_MISMATCH"),
    ("unavailable", "MANIFEST_ASSET_UNAVAILABLE"),
])
def test_legacy_asset_paths_remains_atomic_for_a_partial_set(tmp_path, monkeypatch, failure, error_code):
    manifest, canonical = _asset_manifest(tmp_path, ["complete", failure, "complete"])
    if failure == "unavailable":
        _block_synthetic_asset(monkeypatch, tmp_path / canonical[1]["relpath"])
    with pytest.raises(reader.ManifestError) as caught:
        manifest.asset_paths("Figure B6")
    assert caught.value.code == error_code


def test_validated_assets_and_legacy_paths_keep_complete_anchor_order(tmp_path):
    manifest, canonical = _asset_manifest(tmp_path, ["complete", "complete", "complete"])
    records = manifest.validated_assets("Figure B6", suffixes={".png"})
    paths = [str(tmp_path / asset["relpath"]) for asset in canonical]
    assert [record["path"] for record in records] == paths
    assert all(record["status"] == "complete" and record["error_code"] is None for record in records)
    assert manifest.asset_paths("Figure B6", suffixes={".png"}) == paths
    assert manifest.validated_assets("Figure B6", suffixes={".md"}) == []
    assert manifest.validated_assets("Figure UNKNOWN") == []


def test_legacy_asset_paths_reuses_the_canonical_validation_seam(tmp_path, monkeypatch):
    manifest, _ = _asset_manifest(tmp_path, [])
    calls = []

    def validated(label, suffixes=None):
        calls.append((label, suffixes))
        return [{"path": "canonical-first", "status": "complete", "error_code": None},
                {"path": "canonical-continuation", "status": "complete", "error_code": None}]

    monkeypatch.setattr(manifest, "validated_assets", validated, raising=False)
    assert manifest.asset_paths("Figure B6", suffixes={".png"}) == ["canonical-first", "canonical-continuation"]
    assert calls == [("Figure B6", {".png"})]


@pytest.mark.parametrize("mention,kind", [
    ("Figures B1 through B3", "figures"),
    ("Figures B1 THROUGH 3", "figures"),
    ("Tables D1 through D3", "tables"),
])
def test_bare_through_range_resolves_every_member_in_both_public_parsers(manifest, monkeypatch, mention, kind):
    monkeypatch.setattr(reader, "get_manifest", lambda: manifest)
    labels = [f"Figure B{i}" if kind == "figures" else f"Table D{i}" for i in range(1, 4)]
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert_span(mention, records[0])
    assert records[0]["resolution"] == {"status": "exact", "labels": labels,
                                         "target_ids": [manifest.identity(label) for label in labels]}
    assert reader.extract_references(mention)[kind] == labels


@pytest.mark.parametrize("mention", [
    "Figures B1 through B4", "Figures B3 through B1", "Figures A1 through B3",
    "Figures B14 through B17", "Figures B16A through B16C",
    "Figures B1 through " + "9" * 5000,
])
def test_invalid_through_range_fails_whole_without_endpoint_promotion(manifest, monkeypatch, mention):
    monkeypatch.setattr(reader, "get_manifest", lambda: manifest)
    records = extract_reference_records(mention, manifest=manifest)
    assert len(records) == 1
    assert records[0]["raw"] == mention
    assert records[0]["resolution"]["status"] != "exact"
    assert_span(mention, records[0])
    assert reader.extract_references(mention)["figures"] == []


def test_element_through_support_does_not_change_printed_page_range_grammar(manifest):
    record = extract_reference_records("pp. 7 through 9", manifest=manifest)[0]
    assert record["raw"] == "pp. 7 through 9"
    assert record["resolution"]["status"] == "unknown"
    assert record["page_candidates"] == []
