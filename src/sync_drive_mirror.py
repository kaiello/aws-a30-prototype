r"""Synchronize reviewed codebase and gate verification artifacts to Google Drive mirror.

Destination: G:\My Drive\git_projects\aws-a30-prototype
Excludes:
- .git/ repository files (prevents Google Drive file-locking)
- Active SQLite journals and databases (*.db, *.db-wal, *.db-shm)
- Python cache files (__pycache__/, *.pyc)
- Historical raw request receipts (request_*, etc.)
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_TARGET = Path(r"G:\My Drive\git_projects\aws-a30-prototype")
CANONICAL_PROTOTYPE = Path(r"C:\Users\kenai\aws-a30-prototype")


def _run_git(args: List[str], cwd: Path) -> str:
    """Execute a git command and return stripped stdout or error message."""
    try:
        res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else f"ERROR ({res.returncode}): {res.stderr.strip()}"
    except Exception as exc:
        return f"EXCEPTION: {exc}"


def generate_git_state_summary(repo_dir: Path) -> str:
    """Generate git state summary for reviewer inspection without copying .git/."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "AWS A3.0 Prototype — Git State Summary",
        f"Generated: {now_utc}",
        f"Repository Path: {repo_dir}",
        "",
        "=== git status --short ===",
        _run_git(["status", "--short"], repo_dir),
        "",
        "=== git branch -vv ===",
        _run_git(["branch", "-vv"], repo_dir),
        "",
        "=== git log -n 10 --oneline ===",
        _run_git(["log", "-n", "10", "--oneline"], repo_dir),
        "",
        "=== git diff --stat main..HEAD ===",
        _run_git(["diff", "--stat", "main..HEAD"], repo_dir),
        "",
    ]
    return "\n".join(lines)


def collect_reviewable_files(base_dir: Path) -> List[Path]:
    """Collect all tracked/reviewable artifacts from the repository while skipping large/binary files."""
    collected: List[Path] = []

    # 1. Top-level files and docs
    top_level_candidates = [
        "ROADMAP.md",
        "GEMINI.md",
        "AGENTS.md",
        "pyproject.toml",
        "README.md",
        "goal.md",
        "docs/goal.md",
        "docs/gates.md",
        "docs/roadmap.md",
        "docs/architecture.md",
        "docs/gemini_3_8_flash_gate_review_protocol.md",
        "GATE_6_1_CHECKOUT_CARD.md",
        "GATE_6_FULL_AUDIT_BUNDLE.md",
        "GATE_6_0_CHECKOUT_CARD.md",
        "GATE_6_0_NER_ROUTING_SKILLS_CARD.md",
        "GATE_5_FULL_AUDIT_BUNDLE.md",
        "GATE_4_FULL_AUDIT_BUNDLE.md",
    ]
    for rel in top_level_candidates:
        p = base_dir / rel
        if p.is_file():
            collected.append(p)

    for p in base_dir.glob("GATE_*.md"):
        if p.is_file() and p not in collected:
            collected.append(p)

    for p in base_dir.glob("CONTINUATION_*.md"):
        if p.is_file() and p not in collected:
            collected.append(p)

    # 2. src/ (.py and .json files, excluding __pycache__)
    src_dir = base_dir / "src"
    if src_dir.is_dir():
        for p in src_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json"):
                collected.append(p)

    # 3. tests/ (.py and .json files, excluding __pycache__)
    tests_dir = base_dir / "tests"
    if tests_dir.is_dir():
        for p in tests_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json"):
                collected.append(p)

    # 4. eval/ (.py and .json files, excluding __pycache__)
    eval_dir = base_dir / "eval"
    if eval_dir.is_dir():
        for p in eval_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json", ".md"):
                collected.append(p)

    # 4b. scripts/ (.py, .json, .sh, .bat files, excluding __pycache__)
    scripts_dir = base_dir / "scripts"
    if scripts_dir.is_dir():
        for p in scripts_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json", ".sh", ".bat"):
                collected.append(p)

    # 4c. docs/ (.md, .json, .py files, excluding __pycache__)
    docs_dir = base_dir / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".md", ".json", ".py"):
                collected.append(p)

    # 5. .agents/skills/ (all SKILL.md and skill assets)
    skills_dir = base_dir / ".agents" / "skills"
    if skills_dir.is_dir():
        for p in skills_dir.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                collected.append(p)

    # 6. storage/gate_reviews/ (all review packets)
    gate_dir = base_dir / "storage" / "gate_reviews"
    if gate_dir.is_dir():
        for p in gate_dir.glob("*.md"):
            collected.append(p)

    # 6b. storage/ canonical JSON stores
    storage_root = base_dir / "storage"
    if storage_root.is_dir():
        for p in storage_root.glob("*.json"):
            collected.append(p)

    # 6c. storage/model_replays/ deterministic offline replay cassettes
    replays_dir = base_dir / "storage" / "model_replays"
    if replays_dir.is_dir():
        for p in replays_dir.rglob("*.json"):
            if p.is_file():
                collected.append(p)

    # 6d. storage/manifests/ (coverage and benchmark manifests)
    manifests_dir = base_dir / "storage" / "manifests"
    if manifests_dir.is_dir():
        for p in manifests_dir.rglob("*.json"):
            if p.is_file():
                collected.append(p)

    # 7. storage/evidence_v2/ stores and lightweight review artifacts
    ev_dir = base_dir / "storage" / "evidence_v2"
    if ev_dir.is_dir():
        for p in ev_dir.glob("*.json"):
            collected.append(p)
    if ev_dir.is_dir():
        for ingest_dir in ev_dir.iterdir():
            if not ingest_dir.is_dir():
                continue
            if not re.match(r".*_[0-9]{3}$", ingest_dir.name):
                continue
            for p in ingest_dir.rglob("*"):
                if not p.is_file():
                    continue
                # Skip binary SQLite files and temporary journals
                if any(p.name.endswith(ext) for ext in (".db", ".db-wal", ".db-shm", ".log")):
                    continue
                # Skip raw receipt directories (e.g. 3,500+ historical run receipts)
                if "request_" in p.as_posix() or "raw_" in p.as_posix():
                    continue
                # Include crops, receipts, graphs, and evaluation files
                if (
                    p.name.endswith("_crop_300.png") or p.suffix == ".png"
                    or p.name in (
                        "graph.json", "questions.json", "nlq_questions.json",
                        "ner_routing_questions.json", "adversarial_questions.json",
                        "rubric.json", "results.json", "gold_packets.json",
                        "ingest_receipt.json", "tables_graph.json", "answers.json"
                    )
                    or p.name.endswith("_receipt.json")
                    or p.name.endswith("_store.json")
                ):
                    collected.append(p)

    return sorted(list(set(collected)))


def prune_destination(dest_dir: Path, expected_rel_paths: set[Path]) -> List[Path]:
    """Prune files in managed reviewable areas of dest_dir that are not in expected_rel_paths."""
    dest_dir = Path(dest_dir).resolve()
    if not dest_dir.is_dir():
        return []

    pruned: List[Path] = []
    # Collect candidate files in managed areas of dest_dir
    candidates = collect_reviewable_files(dest_dir)
    for cand in candidates:
        rel = cand.relative_to(dest_dir)
        if rel == Path("git_state_summary.txt"):
            continue
        if rel not in expected_rel_paths:
            try:
                cand.unlink(missing_ok=True)
                pruned.append(rel)
            except Exception:
                pass

    # Also clean legacy uncollected stores if present
    for legacy_rel in [
        Path("storage/clause4_store.json"),
        Path("storage/evidence_v2/clause4_store.json"),
        Path("src/evidence_clause4.py"),
    ]:
        p = dest_dir / legacy_rel
        if p.exists() and legacy_rel not in expected_rel_paths:
            try:
                p.unlink(missing_ok=True)
                pruned.append(legacy_rel)
            except Exception:
                pass

    return sorted(list(set(pruned)))


def sync_mirror(
    source_dir: Path,
    target_dir: Path,
    *,
    active_worktree: Optional[Path] = None,
) -> Dict[str, Any]:
    """Mirror reviewable files to target directory and emit git_state_summary.txt."""
    source_dir = Path(source_dir).resolve(strict=True)
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    git_context = Path(active_worktree or source_dir).resolve()

    files = collect_reviewable_files(source_dir)
    expected_rel = {src_file.relative_to(source_dir) for src_file in files}
    pruned_files = prune_destination(target_dir, expected_rel)
    synced_count = 0
    total_bytes = 0

    for src_file in files:
        rel = src_file.relative_to(source_dir)
        dst_file = target_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        synced_count += 1
        total_bytes += dst_file.stat().st_size

    # Also generate git_state_summary.txt directly in the target root
    git_summary = generate_git_state_summary(git_context)
    summary_path = target_dir / "git_state_summary.txt"
    summary_path.write_text(git_summary, encoding="utf-8")

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    receipt = {
        "status": "PASS",
        "timestamp_utc": now_utc,
        "source_directory": str(source_dir),
        "target_directory": str(target_dir),
        "git_context_directory": str(git_context),
        "files_synced": synced_count,
        "files_pruned": len(pruned_files),
        "pruned_list": [str(p) for p in pruned_files],
        "total_bytes": total_bytes,
        "git_state_summary_written": True,
    }
    return receipt



def sync_selected_files(source: Path, target: Path, manifest: Path) -> Dict[str, Any]:
    """Apply an explicit reviewed selection after validating every source and target.

    No pruning, canonical-repository copy, or git-summary generation occurs here.
    Pre-existing conflicts abort before writes; this is not a filesystem transaction
    against concurrent destination edits or interruptions during the copy phase.
    """
    source = Path(source).resolve(strict=True)
    target = Path(target).resolve()
    if not source.is_dir() or (target.exists() and not target.is_dir()):
        raise ValueError("UNSAFE_PATH: source and target must be directories")
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"files"}:
        raise ValueError("INVALID_MANIFEST: expected a files object")
    entries = data["files"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("INVALID_MANIFEST: files must be a nonempty list")
    digest_pattern = re.compile(r"[0-9a-f]{64}")
    prepared = []
    seen_source, seen_target = set(), set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "path", "source_sha256", "expected_target_sha256"
        }:
            raise ValueError("INVALID_MANIFEST: unexpected file fields")
        relative = entry["path"]
        if not isinstance(relative, str) or not relative or any(c in relative for c in "\\:\x00"):
            raise ValueError("UNSAFE_PATH: require a relative forward-slash path")
        parts = relative.split("/")
        if any(not part or part in {".", ".."} or part.rstrip(" .") != part for part in parts):
            raise ValueError("UNSAFE_PATH: noncanonical relative path")
        rel = Path(relative)
        allowed = (len(parts) == 1 and rel.suffix.lower() == ".md") or (
            parts[0] in {"src", "tests", "docs", "eval"}
            and rel.suffix.lower() in {".py", ".md", ".json"}
        )
        sensitive = any(part.startswith(".") or re.search(
            r"credential|secret|(?:^|[_.-])(?:token|password|api_key)(?:[_.-]|$)", part, re.I
        ) for part in parts)
        if not allowed or sensitive:
            raise ValueError(f"UNSAFE_PATH: excluded project path {relative}")
        expected_source = entry["source_sha256"]
        expected_target = entry["expected_target_sha256"]
        if not isinstance(expected_source, str) or not digest_pattern.fullmatch(expected_source):
            raise ValueError("INVALID_MANIFEST: invalid source hash")
        if expected_target is not None and (
            not isinstance(expected_target, str) or not digest_pattern.fullmatch(expected_target)
        ):
            raise ValueError("INVALID_MANIFEST: invalid target hash")
        src, dst = (source / rel).resolve(), (target / rel).resolve()
        if (not src.is_relative_to(source) or not dst.is_relative_to(target)
                or src != source / rel or dst != target / rel):
            raise ValueError(f"UNSAFE_PATH: symlink or traversal alias {relative}")
        if any(parent.exists() and not parent.is_dir() for parent in dst.parents):
            raise ValueError(f"UNSAFE_PATH: target parent is not a directory {relative}")
        src_key, dst_key = str(src).casefold(), str(dst).casefold()
        if src_key in seen_source or dst_key in seen_target:
            raise ValueError("UNSAFE_PATH: duplicate or aliased selection")
        seen_source.add(src_key)
        seen_target.add(dst_key)
        if not src.is_file() or (dst.exists() and not dst.is_file()):
            raise ValueError(f"UNSAFE_PATH: expected regular file {relative}")
        payload = src.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_source:
            raise ValueError(f"SOURCE_HASH_MISMATCH: {relative}")
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"UNSAFE_PATH: binary content {relative}") from exc
        if b"\x00" in payload:
            raise ValueError(f"UNSAFE_PATH: binary content {relative}")
        actual_target = hashlib.sha256(dst.read_bytes()).hexdigest() if dst.exists() else None
        if actual_target not in {expected_target, expected_source}:
            raise ValueError(f"TARGET_CONFLICT: {relative}")
        prepared.append((relative, dst, payload, expected_source, actual_target))
    files = []
    for relative, dst, payload, digest, previous_digest in prepared:
        action = "unchanged" if previous_digest == digest else "copied"
        if action == "copied":
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(payload)
        target_digest = hashlib.sha256(dst.read_bytes()).hexdigest()
        if target_digest != digest:
            raise ValueError(f"TARGET_VERIFICATION_FAILED: {relative}")
        files.append({"path": relative, "source_sha256": digest,
                      "target_sha256": target_digest, "action": action})
    return {"status": "PASS", "mode": "selected", "source_directory": str(source),
            "target_directory": str(target), "files_synced": len(files),
            "files_pruned": 0, "files": files}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize reviewed codebase and gate verification artifacts to Google Drive mirror")
    parser.add_argument("--source", type=Path, default=None, help="Source repository root (default: auto-detected)")
    parser.add_argument("--target", type=Path, default=None, help=f"Target mirror directory (default: {DEFAULT_TARGET})")
    parser.add_argument("--selection-manifest", type=Path, help="Reviewed paths and source/expected-target SHA-256 hashes; no pruning")
    parser.add_argument("--worktree", type=Path, default=None, help="Active git worktree if different from source")
    args = parser.parse_args(argv)

    if args.selection_manifest is not None:
        if args.source is None or args.target is None:
            parser.error("--selection-manifest requires explicit --source and --target")
        receipt = sync_selected_files(args.source, args.target, args.selection_manifest)
        print(json.dumps(receipt, indent=2))
        return 0
    if args.target is None:
        args.target = DEFAULT_TARGET

    current_root = Path(__file__).resolve().parents[1]
    source_dir = args.source
    worktree_dir = args.worktree or current_root

    if source_dir is None:
        # If CANONICAL_PROTOTYPE exists and differs from current_root, sync current_root -> CANONICAL_PROTOTYPE first
        if CANONICAL_PROTOTYPE.exists() and current_root != CANONICAL_PROTOTYPE:
            # Sync to canonical prototype first to keep it fresh
            review_files = collect_reviewable_files(current_root)
            expected_canonical_rel = {f.relative_to(current_root) for f in review_files}
            prune_destination(CANONICAL_PROTOTYPE, expected_canonical_rel)
            for f in review_files:
                rel = f.relative_to(current_root)
                dst = CANONICAL_PROTOTYPE / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
            source_dir = CANONICAL_PROTOTYPE
        else:
            source_dir = current_root

    receipt = sync_mirror(source_dir, args.target, active_worktree=worktree_dir)
    print(f"Drive Mirror Synced: {receipt['target_directory']} ({receipt['timestamp_utc']})")
    print(f"Files synced: {receipt['files_synced']} ({receipt['total_bytes']:,} bytes)")
    if receipt["files_pruned"] > 0:
        print(f"Files pruned: {receipt['files_pruned']} ({', '.join(receipt['pruned_list'])})")
    print(f"Git state summary written: {args.target / 'git_state_summary.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
