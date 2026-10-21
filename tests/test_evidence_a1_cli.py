"""A1 setup contracts over invented SQLite/CQ data; no source or model calls."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import evidence_a1_cli as cli
from src import evidence_a1_registry as registry


def cqs(questions=None):
    return {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1",
            "questions": [] if questions is None else questions}


def question(identifier="synthetic-1", query="Synthetic structural placeholder."):
    return {"id": identifier, "query": query}


def database(tmp_path, *, canonical=True, node_type="Figure", bridges=True):
    path = tmp_path / "storage/dual_layer_registry.db"
    path.parent.mkdir()
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE evidence_nodes (id TEXT PRIMARY KEY, node_type TEXT, image_file TEXT)")
        # A plausible display alias is deliberately not the canonical ID.
        connection.execute("INSERT INTO evidence_nodes VALUES (?, ?, ?)",
                           ("Figure A1", "Figure", "untrusted-display-alias.png"))
        if canonical:
            connection.execute("INSERT INTO evidence_nodes VALUES (?, ?, ?)",
                               ("figure:figure_a1", node_type, "legacy-not-an-asset-binding.png"))
        if bridges:
            connection.execute("CREATE TABLE grounding_bridges (ontology_id TEXT, evidence_id TEXT, rel_type TEXT, bridge_type TEXT)")
            connection.executemany("INSERT INTO grounding_bridges VALUES (?, ?, ?, ?)", [
                ("synthetic:z", "figure:figure_a1", "ILLUSTRATED_BY", "legacy"),
                ("synthetic:a", "figure:figure_a1", "RELATED_TO", "legacy"),
                ("synthetic:unrelated", "figure:figure_b6", "RELATED_TO", "legacy"),
            ])
    return path


def test_registry_uses_exact_canonical_identity_and_read_only_candidate_join(tmp_path, monkeypatch):
    path = database(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    connect = registry.sqlite3.connect
    seen = []

    def observe_connection(target, *args, **kwargs):
        seen.append((target, kwargs.get("uri")))
        return connect(target, *args, **kwargs)

    monkeypatch.setattr(registry.sqlite3, "connect", observe_connection)
    result = registry.a1_registry_binding(tmp_path)
    assert seen == [(path.resolve().as_uri() + "?mode=ro", True)]
    assert result["canonical_manifest_element_id"] == "figure:figure_a1"
    assert result["verification"] == "candidate"
    assert [item["ontology_id"] for item in result["bridges"]] == ["synthetic:a", "synthetic:z"]
    assert all(item["verification"] == "candidate" for item in result["bridges"])
    assert result["legacy_image_alias"] == "legacy-not-an-asset-binding.png"
    assert result["asset_resolution"] == "manifest_only"
    assert result["registry_has_edition_hash_columns"] is False
    assert result["edition_binding"] == "manifest_document_id_and_verified_pdf_sha256"
    assert "no edition/source hash columns" in result["qualification"]
    assert "do not establish" in result["qualification"]
    assert "semantic support" in result["qualification"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert not any(Path(str(path) + suffix).exists() for suffix in ("-journal", "-wal", "-shm"))


def test_registry_missing_database_fails_closed_without_creating_one(tmp_path):
    with pytest.raises(ValueError, match="A1_REGISTRY_MISSING"):
        registry.a1_registry_binding(tmp_path)
    assert not (tmp_path / "storage/dual_layer_registry.db").exists()


@pytest.mark.parametrize("canonical,node_type", [(False, "Figure"), (True, "Table"), (True, None), (True, 7)])
def test_registry_alias_or_wrong_node_type_cannot_supply_a1_identity(tmp_path, canonical, node_type):
    path = database(tmp_path, canonical=canonical, node_type=node_type)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="A1_REGISTRY_IDENTITY_MISSING"):
        registry.a1_registry_binding(tmp_path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("schema", ["missing_evidence_table", "wrong_columns", "missing_bridge_table", "invalid_sqlite"])
def test_invalid_registry_schemas_fail_closed_without_writes(tmp_path, schema):
    if schema == "missing_bridge_table":
        path = database(tmp_path, bridges=False)
    else:
        path = tmp_path / "storage/dual_layer_registry.db"
        path.parent.mkdir()
        if schema == "invalid_sqlite":
            path.write_bytes(b"Original synthetic bytes, not a SQLite database")
        else:
            with sqlite3.connect(path) as connection:
                if schema == "wrong_columns":
                    connection.execute("CREATE TABLE evidence_nodes (id TEXT, wrong_column TEXT)")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="A1_REGISTRY_SCHEMA_INVALID"):
        registry.a1_registry_binding(tmp_path)
    assert path.read_bytes() == before


def test_empty_owner_cq_document_is_valid_and_does_not_prepare_source_packets(tmp_path, monkeypatch):
    payload = cqs()
    original = deepcopy(payload)

    def forbidden(*args, **kwargs):
        pytest.fail("An empty owner-CQ document must not load source or call a reader")

    monkeypatch.setattr(cli, "load_query_evidence", forbidden)
    monkeypatch.setattr(cli, "build_messages", forbidden)
    assert cli.validate_cqs(payload) == original
    prepared = cli.prepare_packets(tmp_path, payload)
    assert payload == original
    assert prepared["packets"] == []
    assert prepared["model_calls"] == prepared["external_calls"] == 0
    assert prepared["answer_accuracy"] == "NOT_RUN"


@pytest.mark.parametrize("payload", [
    None, [], {},
    {"schema_version": "wrong", "source_element": "Figure A1", "questions": []},
    {"schema_version": "a1-owner-cq-1.0", "source_element": "Table A1", "questions": []},
    {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1", "questions": {}},
    {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1", "questions": [], "expected_facts": []},
])
def test_malformed_owner_cq_documents_are_rejected(payload):
    with pytest.raises(ValueError, match="Invalid A1 owner-CQ document"):
        cli.validate_cqs(payload)


@pytest.mark.parametrize("item", [
    None, {}, {"id": "only-id"}, {"query": "Synthetic placeholder"},
    question(""), question("  "), question("../escape"), question("has space"), question("x" * 129),
    question(query=""), question(query=" \n\t"), question(query=None), question(query=7),
    question(query="x" * 16361), dict(question(), expected_facts=[]),
])
def test_malformed_owner_cq_items_are_rejected_before_source_loading(item, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Malformed CQ must fail validation before source loading")

    monkeypatch.setattr(cli, "load_query_evidence", forbidden)
    with pytest.raises(ValueError, match="Invalid or duplicate A1 owner-CQ item"):
        cli.prepare_packets(tmp_path, cqs([item]))


def test_owner_cq_ids_are_unique_and_query_length_is_bounded():
    valid = cqs([question("a" * 128, "x" * 16360)])
    original = deepcopy(valid)
    assert cli.validate_cqs(valid) == original
    assert valid == original
    with pytest.raises(ValueError, match="duplicate"):
        cli.validate_cqs(cqs([question("same-id"), question("same-id", "Another synthetic placeholder.")]))
    assert cli.validate_cqs(cqs([question("synthetic-" + str(i)) for i in range(100)]))
    with pytest.raises(ValueError, match="Invalid A1 owner-CQ document"):
        cli.validate_cqs(cqs([question("synthetic-" + str(i)) for i in range(101)]))


def test_private_output_is_new_json_under_ignored_storage(tmp_path):
    target = tmp_path / "storage/evidence_v2/new/subdir/synthetic.json"
    value = {"synthetic": True, "packets": []}
    cli.write_private_output(tmp_path, target, value)
    assert json.loads(target.read_text(encoding="utf-8")) == value
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        cli.write_private_output(tmp_path, target, {"overwrite": "forbidden"})
    assert target.read_bytes() == before


@pytest.mark.parametrize("relative", [
    "outside.json", "storage/elsewhere.json", "storage/evidence_v2/../escape.json",
    "storage/evidence_v2/private.txt", "storage/evidence_v2/private.json.env",
])
def test_private_output_rejects_other_destinations_and_extensions(tmp_path, relative):
    target = tmp_path / relative
    with pytest.raises(ValueError, match="new JSON file under local storage/evidence_v2"):
        cli.write_private_output(tmp_path, target, {"synthetic": True})
    assert not target.exists()


def test_cli_nonempty_synthetic_inputs_require_private_output(tmp_path, monkeypatch, capsys):
    source = tmp_path / "synthetic-input.json"
    source.write_text(json.dumps(cqs([question(query="SYNTHETIC_PRIVATE_QUERY_MARKER")])), encoding="utf-8")
    monkeypatch.setattr(cli, "structural_status", lambda root: {"owner_cq_count": 0, "model_calls": 0})
    monkeypatch.setattr(cli, "prepare_packets", lambda root, payload: {"packets": [], "model_calls": 0})
    with pytest.raises(SystemExit) as raised:
        cli.main(["--root", str(tmp_path), "--input", str(source)])
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert "require a private --output" in captured.err
    assert "SYNTHETIC_PRIVATE_QUERY_MARKER" not in captured.out + captured.err


def test_owner_dataset_has_only_stable_execution_questions_without_gold():
    payload = json.loads((ROOT / "eval/evidence_v2_a1_owner_cqs.json").read_text(encoding="utf-8"))
    assert cli.validate_cqs(payload) == payload
    assert [q["id"] for q in payload["questions"]] == [f"A1-CQ-{i:03d}" for i in range(1,16)]
    assert all(set(q) == {"id", "query"} for q in payload["questions"])
    assert all(not q["query"].endswith(" No") for q in payload["questions"])


def test_resolved_storage_redirect_cannot_change_private_output_root(tmp_path, monkeypatch):
    declared = tmp_path / "storage/evidence_v2"
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    original = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == declared:
            return outside
        if path == declared / "synthetic.json":
            return outside / "synthetic.json"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="new JSON file under local storage/evidence_v2"):
        cli.write_private_output(tmp_path, declared / "synthetic.json", {"synthetic": True})
    assert not outside.exists()


def test_linked_private_folder_is_rejected_even_when_resolving_inside_root(tmp_path, monkeypatch):
    declared = tmp_path / "storage/evidence_v2"
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == declared or original(path))
    with pytest.raises(ValueError, match="Linked private output"):
        cli.write_private_output(tmp_path, declared / "synthetic.json", {"synthetic": True})
    assert not declared.exists()
