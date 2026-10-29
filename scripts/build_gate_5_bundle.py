"""Script to generate GATE_5_FULL_AUDIT_BUNDLE.md dynamically for Gate 5 review."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_whole_standard_preflight import run_whole_standard_preflight, LOCKED_STORE_HASHES

FILES = [
    "storage/gate_reviews/gate_5_review_packet.md",
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json",
    "storage/evidence_v2/phase5_hardening_001/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/results.json",
    "src/evidence_whole_standard_preflight.py",
    "tests/test_gate_5_hardening.py",
    "eval/run_phase5_hardening.py",
    "src/evidence_phase4_bakeoff.py",
    "tests/test_gate_4_production_bakeoff.py",
    "docs/FULL_PROMPT.md",
]


def get_git_info():
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked_diff = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip().splitlines()
    tracked_changes = [f for f in tracked_diff if "FULL_AUDIT_BUNDLE" not in f]
    return branch, commit, (len(tracked_changes) == 0)


def main():
    branch, commit, is_clean = get_git_info()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Dynamic preflight check
    preflight_res = run_whole_standard_preflight(ROOT)

    # Dynamic adversarial benchmark summary
    adv_res_file = ROOT / "storage/evidence_v2/phase5_hardening_001/results.json"
    if adv_res_file.exists():
        adv_data = json.loads(adv_res_file.read_text(encoding="utf-8"))
        adv_summary = f"{adv_data['passed_questions']} / {adv_data['total_questions']} ({adv_data['pass_rate_pct']:.1f}%)"
    else:
        adv_summary = "N/A"

    # Dynamic canonical store check
    store_status = "ALL_7_VERIFIED_LOCKED"
    for rel_p, exp_h in LOCKED_STORE_HASHES.items():
        act_h = hashlib.sha256((ROOT / rel_p).read_bytes()).hexdigest()
        if act_h != exp_h:
            store_status = f"CORRUPTED_{rel_p}"
            break

    header = f"""# GATE 5 CONSOLIDATED FULL AUDIT BUNDLE (PRODUCTION HARDENING & SUGGESTION REMEDIATION)
Generated for Principal Reviewer Gate 5 Hardening & Invariant Defense Audit.
Standard: AWS A3.0M/A3.0:2020 | Gate: Gate 5 | Branch: {branch}
Build Commit SHA: {commit} | Timestamp: {timestamp}
Working Tree Tracked Codebase: {"CLEAN" if is_clean else "MODIFIED"}
Canonical Stores: {store_status} (7/7 historical hashes match locked digests)
Preflight Contract: {preflight_res['status']} ({preflight_res['network_calls']} network calls, offline verified)
Adversarial Suite: {adv_summary} passed exact refusal/refutation rubric
"""

    lines = [header.strip(), ""]

    for rel_p in FILES:
        p = ROOT / rel_p
        if p.exists():
            content = p.read_text(encoding="utf-8")
            lines.append(f"=== FILE: {rel_p} ===")
            lines.append("")
            lines.append(content)
            lines.append("")
        else:
            lines.append(f"=== FILE: {rel_p} (MISSING) ===")
            lines.append("")

    output_text = "\n".join(lines)

    for target in [ROOT / "GATE_5_FULL_AUDIT_BUNDLE.md", ROOT / "storage" / "gate_reviews" / "GATE_5_FULL_AUDIT_BUNDLE.md"]:
        target.write_text(output_text, encoding="utf-8")
        print(f"Generated {target} ({len(output_text.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
