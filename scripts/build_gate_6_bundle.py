"""Script to generate GATE_6_FULL_AUDIT_BUNDLE.md dynamically for Gate 6.0 / 6.1 review."""
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

FILES = [
    "storage/gate_reviews/gate_5_review_packet.md",
    "storage/gate_reviews/gate_6_0_review_packet.md",
    "storage/manifests/coverage_manifest.json",
    "storage/manifests/latency_benchmark.json",
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json",
    "storage/evidence_v2/phase5_hardening_001/rubric.json",
    "storage/evidence_v2/phase5_hardening_001/results.json",
    "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json",
    "storage/evidence_v2/phase5_5_nlq_001/rubric.json",
    "storage/evidence_v2/phase5_5_nlq_001/results.json",
    "storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json",
    "storage/evidence_v2/phase6_ner_routing_001/rubric.json",
    "storage/evidence_v2/phase6_ner_routing_001/results.json",
    "storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json",
    "storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json",
    "storage/evidence_v2/phase6_1_semantic_graph_001/results.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_001/results.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_002/rubric.json",
    "storage/evidence_v2/phase6_2_generalization_holdout_002/results.json",
    "storage/evidence_v2/phase6_3_blind_hardening_001/questions.json",
    "storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json",
    "storage/evidence_v2/phase6_3_blind_hardening_001/results.json",
    "src/evidence_whole_standard_preflight.py",
    "src/deepseek_v41_adapter.py",
    "src/semantic_nlq_expander.py",
    "src/welding_ner.py",
    "src/evidence_phase4_bakeoff.py",
    "src/evidence_whole_standard_cli.py",
    "eval/run_phase6_ner_routing.py",
    "eval/run_phase6_1_semantic_graph.py",
    "eval/run_phase6_2_generalization_holdout.py",
    "eval/run_phase6_3_blind_hardening.py",
    "tests/test_gate_6_0_ner_routing_skills.py",
    "tests/test_gate_6_1_semantic_graph.py",
    "tests/test_gate_6_2_store_driven_composition.py",
    "tests/test_gate_6_2_1_multi_action_closure.py",
    "tests/test_gate_6_2_2_closeout_hygiene.py",
    "tests/test_gate_6_3_blind_hardening.py",
    "tests/test_gate_6_4_comprehensive_enhancements.py",
    "GATE_6_0_CHECKOUT_CARD.md",
    "GATE_6_1_CHECKOUT_CARD.md",
    "GATE_6_2_CHECKOUT_CARD.md",
    "GATE_6_2_1_CHECKOUT_CARD.md",
    "GATE_6_2_2_CLOSEOUT_HYGIENE_CARD.md",
    "GATE_6_2_2_CHECKOUT_CARD.md",
    "GATE_6_3_CHECKOUT_CARD.md",
    "GATE_6_4_CHECKOUT_CARD.md",
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

    preflight_res = run_whole_standard_preflight(ROOT)
    deepseek_res = run_deepseek_replay_preflight(ROOT)

    from tests.test_gate_6_4_comprehensive_enhancements import ALL_51_LOCKED_HASHES

    replay_cassettes_count = len(list((ROOT / "storage/model_replays/deepseek_v4_1_flash_1017").glob("*.json")))

    header = f"""# Gate 6 Full Production Audit Bundle
Generated at: {timestamp}
Branch: `{branch}`
Commit: `{commit}`
Clean Working Tree: `{is_clean}`

## Preflight Verification
- Whole Standard Preflight Status: `{preflight_res['status']}`
- DeepSeek Replay Preflight Status: `{deepseek_res['status']}`
- DeepSeek Preflight Smoke Queries Replayed: `{deepseek_res.get('replayed_queries_count', 0)}`
- DeepSeek Replay Cassettes Verified on Disk: `{replay_cassettes_count}`

## Cryptographic Locks (All 51 Artifacts)
"""
    for rel_path, expected_hash in ALL_51_LOCKED_HASHES.items():
        p = ROOT / rel_path
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"
        match_str = "MATCH" if actual_hash == expected_hash else "MISMATCH"
        header += f"- `{rel_path}`: `{actual_hash}` ({match_str})\n"

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

    for target in [
        ROOT / "GATE_6_FULL_AUDIT_BUNDLE.md",
        ROOT / "storage" / "gate_reviews" / "GATE_6_FULL_AUDIT_BUNDLE.md",
        ROOT / "GATE_5_FULL_AUDIT_BUNDLE.md",
        ROOT / "storage" / "gate_reviews" / "GATE_5_FULL_AUDIT_BUNDLE.md",
    ]:
        target.write_text(output_text, encoding="utf-8")
        print(f"Generated {target} ({len(output_text.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
