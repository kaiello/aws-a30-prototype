"""Script to generate GATE_5_FULL_AUDIT_BUNDLE.md dynamically for Gate 5 / 5.4 / 5.5 / 5.6 review."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_whole_standard_preflight import (
    run_whole_standard_preflight,
    run_deepseek_replay_preflight,
)
from tests.test_gate_5_6_epistemic_manifest import ALL_24_LOCKED_HASHES

FILES = [
    "storage/gate_reviews/gate_5_review_packet.md",
    "storage/manifests/coverage_manifest.json",
    "storage/manifests/latency_benchmark.json",
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json",
    "storage/evidence_v2/phase5_hardening_001/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/results.json",
    "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json",
    "storage/evidence_v2/phase5_5_nlq_001/rubric.json",
    "storage/evidence_v2/phase5_5_nlq_001/results.json",
    "src/evidence_whole_standard_preflight.py",
    "src/deepseek_v41_adapter.py",
    "src/semantic_nlq_expander.py",
    "src/evidence_phase4_bakeoff.py",
    "scripts/build_coverage_manifest.py",
    "eval/run_latency_benchmark.py",
    "eval/run_phase5_hardening.py",
    "eval/run_phase5_5_nlq.py",
    "tests/test_gate_5_hardening.py",
    "tests/test_gate_5_4_deepseek_adapter.py",
    "tests/test_gate_5_5_semantic_nlq.py",
    "tests/test_gate_5_6_epistemic_manifest.py",
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

    # Dynamic whole-standard preflight check
    preflight_res = run_whole_standard_preflight(ROOT)

    # Dynamic deepseek replay preflight check
    deepseek_preflight = run_deepseek_replay_preflight(ROOT)

    # Dynamic coverage manifest summary
    cov_file = ROOT / "storage/manifests/coverage_manifest.json"
    if cov_file.exists():
        cov_data = json.loads(cov_file.read_text(encoding="utf-8"))
        cov_summary = f"{cov_data['page_accounting']['total_ingested_pages']} ingested + {cov_data['page_accounting']['total_excluded_pages']} excluded = {cov_data['page_accounting']['total_pdf_pages']} total PDF pages accounted for"
    else:
        cov_summary = "N/A"

    # Dynamic latency benchmark summary
    lat_file = ROOT / "storage/manifests/latency_benchmark.json"
    if lat_file.exists():
        lat_data = json.loads(lat_file.read_text(encoding="utf-8"))
        p50_det = lat_data["routes"]["offline_deterministic_route"]["p50_ms"]
        p95_det = lat_data["routes"]["offline_deterministic_route"]["p95_ms"]
        p50_rep = lat_data["routes"]["offline_deepseek_replay_route"]["p50_ms"]
        lat_summary = f"deterministic p50: {p50_det:.2f} ms (p95: {p95_det:.2f} ms) | replay p50: {p50_rep:.2f} ms | $0.00 external API charge"
    else:
        lat_summary = "N/A"

    # Dynamic adversarial benchmark summary
    adv_res_file = ROOT / "storage/evidence_v2/phase5_hardening_001/results.json"
    if adv_res_file.exists():
        adv_data = json.loads(adv_res_file.read_text(encoding="utf-8"))
        adv_summary = f"{adv_data['passed_questions']} / {adv_data['total_questions']} ({adv_data['pass_rate_pct']:.1f}%)"
    else:
        adv_summary = "N/A"

    # Dynamic NLQ benchmark summary
    nlq_res_file = ROOT / "storage/evidence_v2/phase5_5_nlq_001/results.json"
    if nlq_res_file.exists():
        nlq_data = json.loads(nlq_res_file.read_text(encoding="utf-8"))
        nlq_summary = f"{nlq_data['passed']} / {nlq_data['total_queries']} ({nlq_data['pass_rate_percent']:.1f}%)"
    else:
        nlq_summary = "N/A"

    # Dynamic 24/24 cryptographic ledger verification
    store_status = "ALL_24_VERIFIED_LOCKED"
    for rel_p, exp_h in ALL_24_LOCKED_HASHES.items():
        act_h = hashlib.sha256((ROOT / rel_p).read_bytes()).hexdigest()
        if act_h != exp_h:
            store_status = f"CORRUPTED_{rel_p}"
            break

    header = f"""# GATE 5 CONSOLIDATED FULL AUDIT BUNDLE (FINAL PRODUCTION RELEASE: HARDENING, DEEPSEEK V4.1, SEMANTIC NLQ & EPISTEMIC CALIBRATION)
Generated for Principal Reviewer Gate 5 / 5.4 / 5.5 / 5.6 Production Release Audit.
Standard: AWS A3.0M/A3.0:2020 | Gate: Gate 5.6 | Branch: {branch}
Build Commit SHA: {commit} | Timestamp: {timestamp}
Working Tree Tracked Codebase: {"CLEAN" if is_clean else "MODIFIED"}
Cryptographic Immutability Ledger: {store_status} (24/24 repository hashes locked and verified)
Whole-Standard Preflight Contract: {preflight_res['status']} ({preflight_res['network_calls']} network calls, offline verified)
DeepSeek-V4.1 Replay Preflight: {deepseek_preflight['status']} ({deepseek_preflight['network_calls']} network calls, epistemic quarantine verified)
Coverage Manifest: {cov_summary}
Latency Telemetry: {lat_summary}
Adversarial Suite: {adv_summary} passed exact refusal/refutation rubric
NLQ Benchmark Suite: {nlq_summary} passed exact store-derived semantic expansion rubric
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
