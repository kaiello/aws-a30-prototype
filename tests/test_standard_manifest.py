"""Offline source-location contract; no providers, models or databases."""
import copy
import json
from pathlib import Path

import pytest

from src.standard_manifest import ManifestError, get_manifest, load_manifest
import src.standard_manifest as reader

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config/aws_a30_2020_manifest.json"


def test_inventory_identity_and_immutable_snapshot():
    m = get_manifest()
    assert m.document["id"] == "doc:aws_a30_2020"
    assert m.document["page_count"] == 190
    assert len(m.labels("figures")) == 62
    assert len(m.labels("tables")) == 11
    assert len(m.labels("sections")) == 10
    copy_of_record = m.element("Figure B6")
    copy_of_record["anchors"].clear()
    assert [a["pdf_index"] for a in m.anchors("Figure B6")] == [99, 100, 101]
    assert m.section("Annex B")["normative_status"] == "conflicting"
    assert m.document["pages"][2]["printed_label"] == "ii"
    assert m.document["pages"][1]["printed_label"] is None


@pytest.mark.parametrize("label", ["Figure A7", "Figure B55", "Figure B120", "Table A10", "Table B1", "Figure B1.5", "Figure B1suffix"])
def test_unknown_labels_are_not_truncated(label):
    assert get_manifest().resolve(label)["status"] == "unknown"


def test_group_alias_is_never_an_exact_caption():
    result = get_manifest().resolve("Figure B16")
    assert result["status"] == "group"
    assert result["labels"] == ["Figure B16A", "Figure B16B", "Figure B16C"]
    assert get_manifest().anchors("Figure B16") == []


def test_all_continuations_and_deterministic_assets():
    m = get_manifest()
    assert sum(len(m.anchors(k)) > 1 for k in m.labels("figures")) == 13
    assert sum(len(m.anchors(k)) > 1 for k in m.labels("tables")) == 5
    assert [Path(p).name for p in m.asset_paths("Figure B6", {".png"})] == [
        "Figure_B6_p99.png", "Figure_B6_p100.png", "Figure_B6_p101.png"]
    assert [a["pdf_index"] for a in m.anchors("Table A3")] == [84, 85]
    assert m.element("Table D2")["assets"] == []  # Source location is not an invented asset.


def test_companions_remain_provisional():
    m = get_manifest()
    assert m.companions()["Table A3"] == ["Figure A1"]
    links = [l for l in m.links if l["kind"] == "ui_companion"]
    assert len(links) == 9
    assert all(l["verification"]["state"] == "candidate" for l in links)


@pytest.fixture
def raw():
    return json.loads(PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(unrecognized=True),
    lambda x: x.update(schema_version="9.0.0"),
    lambda x: x["document"]["pages"][0].update(pdf_index=True),
    lambda x: x["figures"][0]["anchors"][0].update(pdf_index=190),
    lambda x: x["figures"][0]["anchors"][0].update(printed_label="999"),
    lambda x: x["figures"].append(copy.deepcopy(x["figures"][0])),
    lambda x: next(f for f in x["figures"] if f["label"] == "Figure B6")["anchors"].reverse(),
    lambda x: x["figures"][0]["assets"][0].update(relpath="../outside.png"),
    lambda x: x["figures"][0]["assets"][0].update(relpath="parsed/figures/a.png:secret"),
    lambda x: x["links"][0].update(to_id="figure:unknown"),
    lambda x: x["links"][0].update(from_id="figure:figure_a1"),
    lambda x: x["legacy_aliases"][0].update(legacy_value="Figure A1"),
    lambda x: x["figures"][0]["anchors"][0]["verification"].update(verifier=None),
])
def test_invalid_records_fail_before_publication(raw, mutation, tmp_path):
    mutation(raw)
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ManifestError) as err:
        load_manifest(path, root=ROOT)
    assert err.value.code == "MANIFEST_INVALID"


def test_stale_source_hash_is_distinct(raw, tmp_path):
    old = raw["document"]["sha256"]
    text = json.dumps(raw).replace(old, "0" * 64)
    path = tmp_path / "stale.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ManifestError) as err:
        load_manifest(path, root=ROOT)
    assert err.value.code == "MANIFEST_SOURCE_MISMATCH"


@pytest.mark.parametrize("text", ['{"schema_version":"1.0.0","schema_version":"1.0.0"}', '{"x":NaN}'])
def test_ambiguous_json_is_invalid(text, tmp_path):
    path = tmp_path / "ambiguous.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ManifestError) as err:
        load_manifest(path, root=ROOT)
    assert err.value.code == "MANIFEST_INVALID"


def test_missing_manifest_is_explicit(tmp_path):
    with pytest.raises(ManifestError) as err:
        load_manifest(tmp_path / "absent.json", root=ROOT)
    assert err.value.code == "MANIFEST_MISSING"


@pytest.mark.parametrize("state", ["candidate", "stale", "rejected"])
def test_exact_alias_cannot_promote_an_unverified_target(raw, tmp_path, state):
    raw['figures'][0]['anchors'][0]['verification'].update(state=state, verifier=None, verified_at_utc=None)
    raw['legacy_aliases'].append({'legacy_value': 'Figure A01', 'namespace': 'display',
                                  'target_ids': [raw['figures'][0]['id']], 'resolution': 'exact'})
    path = tmp_path / 'candidate.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    manifest = load_manifest(path, root=ROOT)
    assert manifest.resolve('Figure A01')['status'] == 'unverified'
    assert manifest.element('Figure A01') is None
    assert manifest.anchors('Figure A01') == []


@pytest.mark.parametrize('receipt', [[], {}, {'schema_version': '9.0.0'}])
def test_invalid_runtime_receipt_is_a_structured_failure(monkeypatch, receipt):
    original_json = reader._json
    monkeypatch.setattr(reader, '_json', lambda path: receipt if path.name.endswith('.receipt.json') else original_json(path))
    reader._cached_manifest.cache_clear()
    try:
        with pytest.raises(ManifestError) as err:
            get_manifest()
        assert err.value.code == 'MANIFEST_INVALID'
    finally:
        reader._cached_manifest.cache_clear()


@pytest.mark.parametrize('missing', [False, True])
def test_asset_byte_change_or_loss_never_returns_a_cached_binding(monkeypatch, missing):
    manifest = get_manifest()
    asset = ROOT / manifest.element('Figure B6')['assets'][0]['relpath']
    original_read = Path.read_bytes
    def read(path):
        if path == asset:
            if missing:
                raise FileNotFoundError('Synthetic missing asset')
            return b'Changed synthetic bytes'
        return original_read(path)
    monkeypatch.setattr(Path, 'read_bytes', read)
    with pytest.raises(ManifestError) as err:
        manifest.asset_paths('Figure B6', {'.png'})
    assert err.value.code == ('MANIFEST_ASSET_MISSING' if missing else 'MANIFEST_ASSET_MISMATCH')


def test_failed_reload_does_not_reuse_a_previously_verified_snapshot(monkeypatch):
    reader._cached_manifest.cache_clear()
    try:
        assert reader._cached_manifest('old', 'old', 'old').element('Figure B6')
        def fail_load():
            raise ManifestError('MANIFEST_SOURCE_MISMATCH', 'Synthetic changed source')
        monkeypatch.setattr(reader, 'load_manifest', fail_load)
        with pytest.raises(ManifestError) as err:
            reader._cached_manifest('new', 'new', 'new')
        assert err.value.code == 'MANIFEST_SOURCE_MISMATCH'
    finally:
        reader._cached_manifest.cache_clear()
