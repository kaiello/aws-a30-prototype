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
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


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
    ]
    for rel in top_level_candidates:
        p = base_dir / rel
        if p.is_file():
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

    # 7. storage/evidence_v2/ stores and lightweight review artifacts
    ev_dir = base_dir / "storage" / "evidence_v2"
    if ev_dir.is_dir():
        for p in ev_dir.glob("*.json"):
            collected.append(p)
    if ev_dir.is_dir():
        for ingest_dir in ev_dir.glob("*_001"):
            if not ingest_dir.is_dir():
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
                    or p.name in ("graph.json", "questions.json", "rubric.json", "results.json", "ingest_receipt.json", "tables_graph.json", "answers.json")
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize reviewed codebase and gate verification artifacts to Google Drive mirror")
    parser.add_argument("--source", type=Path, default=None, help="Source repository root (default: auto-detected)")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help=f"Target mirror directory (default: {DEFAULT_TARGET})")
    parser.add_argument("--worktree", type=Path, default=None, help="Active git worktree if different from source")
    args = parser.parse_args(argv)

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
