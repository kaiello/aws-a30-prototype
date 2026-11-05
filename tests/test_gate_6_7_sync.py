"""Gate 6.7 selective mirror updates must preserve unrelated work and detect conflicts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src import sync_drive_mirror as mirror


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry(source: Path, relative: str, expected: bytes | None = None) -> dict:
    return {"path": relative, "source_sha256": _sha((source / relative).read_bytes()),
            "expected_target_sha256": None if expected is None else _sha(expected)}


def _manifest(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "selection.json"
    path.write_text(json.dumps({"files": entries}), encoding="utf-8")
    return path


@pytest.fixture
def roots(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    (source / "src").mkdir(parents=True)
    (source / "docs").mkdir()
    target.mkdir()
    (source / "src/module.py").write_bytes(b"new module\n")
    (source / "docs/report.md").write_bytes(b"new report\n")
    return source, target


def test_selected_copy_preserves_unrelated_files_and_has_no_summary(roots, tmp_path):
    source, target = roots
    unrelated = target / "unrelated.md"
    unrelated.write_bytes(b"keep reviewer changes")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py")])
    receipt = mirror.sync_selected_files(source, target, manifest)
    assert (target / "src/module.py").read_bytes() == b"new module\n"
    assert unrelated.read_bytes() == b"keep reviewer changes"
    assert not (target / "git_state_summary.txt").exists()
    assert not (target / "docs").exists()
    assert receipt["status"] == "PASS" and receipt["files_pruned"] == 0
    assert receipt["files"][0]["target_sha256"] == _sha(b"new module\n")


def test_all_target_conflicts_are_checked_before_any_writes(roots, tmp_path):
    source, target = roots
    (target / "docs").mkdir()
    (target / "docs/report.md").write_bytes(b"independent reviewer edit")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/report.md", b"old report")])
    with pytest.raises(ValueError, match="CONFLICT"):
        mirror.sync_selected_files(source, target, manifest)
    assert not (target / "src").exists()
    assert (target / "docs/report.md").read_bytes() == b"independent reviewer edit"


def test_source_tamper_blocks_every_copy(roots, tmp_path):
    source, target = roots
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/report.md")])
    (source / "docs/report.md").write_bytes(b"changed after review")
    with pytest.raises(ValueError, match="SOURCE_HASH"):
        mirror.sync_selected_files(source, target, manifest)
    assert list(target.iterdir()) == []


def test_expected_existing_hash_allows_update_and_repeat_is_idempotent(roots, tmp_path):
    source, target = roots
    (target / "src").mkdir()
    (target / "src/module.py").write_bytes(b"old module")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py", b"old module")])
    mirror.sync_selected_files(source, target, manifest)
    receipt = mirror.sync_selected_files(source, target, manifest)
    assert receipt["files"][0]["action"] == "unchanged"
    assert (target / "src/module.py").read_bytes() == b"new module\n"


@pytest.mark.parametrize("relative", ["../escape.md", "src/../../escape.md", "C:/escape.md",
    "src\\module.py", ".git/config", ".env", "data/source.json", "parsed/page.md",
    "storage/results.json", "src/credentials.json", "docs/source.pdf"])
def test_unsafe_or_source_paths_rejected_before_any_copy(roots, tmp_path, relative):
    source, target = roots
    bad = {"path": relative, "source_sha256": "0" * 64, "expected_target_sha256": None}
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"), bad])
    with pytest.raises(ValueError, match="PATH"):
        mirror.sync_selected_files(source, target, manifest)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("side", ["source", "target"])
def test_symlink_escape_rejected(roots, tmp_path, side):
    source, target = roots
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "module.py").write_bytes(b"new module\n")
    link = (source if side == "source" else target) / "docs/link"
    link.parent.mkdir(exist_ok=True)
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Host does not permit symlink creation: {exc}")
    if side == "target":
        (source / "docs/link").mkdir()
        (source / "docs/link/module.py").write_bytes(b"new module\n")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/link/module.py")])
    with pytest.raises(ValueError, match="PATH"):
        mirror.sync_selected_files(source, target, manifest)
    assert not (target / "src").exists()
    assert (outside / "module.py").read_bytes() == b"new module\n"


def test_selective_cli_requires_explicit_source_and_target(tmp_path):
    manifest = _manifest(tmp_path, [])
    for args in [["--selection-manifest", str(manifest)],
                 ["--selection-manifest", str(manifest), "--source", str(tmp_path)]]:
        with pytest.raises(SystemExit) as result:
            mirror.main(args)
        assert result.value.code == 2


def test_target_parent_file_is_found_before_any_copy(roots, tmp_path):
    source, target = roots
    (target / "docs").write_bytes(b"not a directory")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/report.md")])
    with pytest.raises(ValueError, match="PATH"):
        mirror.sync_selected_files(source, target, manifest)
    assert not (target / "src").exists()
    assert (target / "docs").read_bytes() == b"not a directory"


def test_internal_symlink_cannot_alias_excluded_source_paths(roots, tmp_path):
    source, target = roots
    (source / "data").mkdir()
    (source / "data/private.txt").write_bytes(b"source text")
    link = source / "docs/alias.md"
    try:
        link.symlink_to(source / "data/private.txt")
    except OSError as exc:
        pytest.skip(f"Host does not permit symlink creation: {exc}")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/alias.md")])
    with pytest.raises(ValueError, match="PATH"):
        mirror.sync_selected_files(source, target, manifest)
    assert list(target.iterdir()) == []


def test_binary_disguised_as_markdown_is_rejected(roots, tmp_path):
    source, target = roots
    (source / "docs/report.md").write_bytes(b"binary\x00payload")
    manifest = _manifest(tmp_path, [_entry(source, "src/module.py"),
                                   _entry(source, "docs/report.md")])
    with pytest.raises(ValueError, match="PATH"):
        mirror.sync_selected_files(source, target, manifest)
    assert list(target.iterdir()) == []


def test_default_cli_still_uses_legacy_sync_with_default_target(roots, monkeypatch):
    source, target = roots
    calls = []
    monkeypatch.setattr(mirror, "sync_mirror", lambda src, dst, **kwargs:
                        calls.append((src, dst)) or {"target_directory": str(dst),
                        "timestamp_utc": "test", "files_synced": 0, "total_bytes": 0,
                        "files_pruned": 0})
    assert mirror.main(["--source", str(source)]) == 0
    assert calls == [(source, mirror.DEFAULT_TARGET)]
