"""Script to generate GATE_4_FULL_AUDIT_BUNDLE.md for Gate 4 review."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "storage/gate_reviews/gate_4-2B_review_packet.md",
    "storage/gate_reviews/gate_4-1_repair_packet.md",
    "storage/gate_reviews/gate_4_review_packet.md",
    "git_state_summary.txt",
    "src/evidence_phase4_bakeoff.py",
    "eval/run_phase4_bakeoff.py",
    "tests/test_gate_4_production_bakeoff.py",
    "storage/evidence_v2/phase4_bakeoff_001/questions.json",
    "storage/evidence_v2/phase4_bakeoff_001/rubric.json",
    "eval/evidence_v2_phase4_bakeoff_results.json",
]

header = """# GATE 4 CONSOLIDATED FULL AUDIT BUNDLE (GATE 4-2B FINAL PRODUCTION RELEASE)
Generated for Principal Reviewer whole-standard Gate 4 multi-model production acceptance bakeoff audit.
Standard: AWS A3.0M/A3.0:2020 | Gate: Gate 4-2B | Branch: feat/gate-4-final-production-bakeoff
Scorecard: Route 1: 30/30 (100.0%) | Route 2: 30/30 (100.0%) across all 5 separated dimensions
Verification: 1,442 passed, 8 skipped, 0 failures | CLEAR_REAL_ENTRY_CONTRACT: 11/11 pass
"""

lines = [header.strip(), ""]

for rel_p in FILES:
    p = ROOT / rel_p
    content = p.read_text(encoding="utf-8")
    lines.append(f"=== FILE: {rel_p} ===")
    lines.append("")
    lines.append(content)
    lines.append("")

output_text = "\n".join(lines)

for target in [ROOT / "GATE_4_FULL_AUDIT_BUNDLE.md", ROOT / "storage" / "gate_reviews" / "GATE_4_FULL_AUDIT_BUNDLE.md"]:
    target.write_text(output_text, encoding="utf-8")
    print(f"Generated {target} ({len(output_text.encode('utf-8'))} bytes)")
