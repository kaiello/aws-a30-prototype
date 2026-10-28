"""Script to generate GATE_3D_FULL_AUDIT_BUNDLE.md for Gate 3D review."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "storage" / "gate_reviews" / "GATE_3D_FULL_AUDIT_BUNDLE.md"

FILES = [
    "storage/gate_reviews/gate_3D-1_repair_packet.md",
    "storage/gate_reviews/gate_3D_review_packet.md",
    "eval/evidence_v2_phase3_holdout_results.json",
    "storage/evidence_v2/phase3_holdout_001/questions.json",
    "storage/evidence_v2/phase3_holdout_001/rubric.json",
    "src/evidence_phase3_qa.py",
    "eval/run_phase3_holdout.py",
    "tests/test_gate_3d_phase3_holdout.py",
    "src/archetype_spatial_callout.py",
    "src/archetype_cycle_waveform.py",
    "storage/evidence_v2/phase3_holdout_001/deepseek_run/runtime.json",
]

lines = [
    "# GATE 3D CONSOLIDATED FULL AUDIT BUNDLE",
    "Generated for Principal Reviewer whole-standard Phase 3 holdout benchmark audit.",
    "Standard: AWS A3.0M/A3.0:2020 | Gate: 3D | Branch: feat/gate-3d-phase3-live-holdout",
    "Five Separated Dimensions: 40/40 (100.0%) across all 5 dimensions",
    "",
]

for rel_p in FILES:
    p = ROOT / rel_p
    content = p.read_text(encoding="utf-8")
    lines.append(f"=== FILE: {rel_p} ===")
    lines.append("")
    lines.append(content)
    lines.append("")

output_text = "\n".join(lines)
BUNDLE_PATH.write_text(output_text, encoding="utf-8")
print(f"Generated {BUNDLE_PATH} ({len(output_text.encode('utf-8'))} bytes)")
