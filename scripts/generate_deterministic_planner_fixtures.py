"""Generate deterministic planner fixtures for evaluation benchmarking.

These fixtures capture parsed plans from DeterministicQuestionPlanner for
designated benchmark queries. They are stored under
storage/model_replays/deterministic_planner_fixtures/ with:
  model_id: "DeterministicQuestionPlanner"
  epistemic_tag: "SYNTHETIC_PLANNER_FIXTURE_NOT_MODEL_OUTPUT"
  cassette_origin: "synthetic_planner_fixture"

They are explicitly quarantined from storage/model_replays/deepseek_v4_1_flash_1017/
to preserve epistemic boundaries between genuine LLM model replays and
deterministic planner outputs (per Gate 6.4.1 Provenance Integrity remediation).
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.deepseek_v41_adapter import (
    DeepSeekV41Config,
    DeepSeekV41PlannerAdapter,
    normalize_prompt,
)
from src.evidence_phase4_bakeoff import DeterministicQuestionPlanner

EPISTEMIC_TAG = "SYNTHETIC_PLANNER_FIXTURE_NOT_MODEL_OUTPUT"
TARGET_QIDS = [
    "G63-BLIND04",  # Figure B21 reverse lookup
    "G63-BLIND09",  # Table A5 block brazing / CAW-S
    "G63-BLIND14",  # Figure B23(J) temper beads
    "G63-BLIND16",  # Table A4 application modes
    "G63-BLIND18",  # Annex C C2.3 ground clamp/lead
    "G63-BLIND20",  # Figure B49/B50 waveforms
]


def generate_fixtures() -> None:
    adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"), root=ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    out_dir = ROOT / "storage/model_replays/deterministic_planner_fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    q_file = ROOT / "storage/evidence_v2/phase6_3_blind_hardening_001/questions.json"
    questions = json.loads(q_file.read_text(encoding="utf-8"))

    for q in questions:
        qid = q["id"]
        if qid in TARGET_QIDS:
            query_text = q["query"]
            plan = planner.plan_whole_standard_question(query_text)
            prompt = adapter.build_whole_standard_prompt(query_text)
            key = adapter.compute_replay_key(prompt)

            parsed_plan = {
                "target_division": plan.get("target_division"),
                "intent": plan.get("intent"),
                "target_entities": plan.get("target_entities", []),
                "actions": plan.get("actions", []),
                "reason": f"Deterministic planner trace: Captured plan for {q['category']} targeting {plan.get('target_division')}.",
            }

            fixture = {
                "model_id": "DeterministicQuestionPlanner",
                "replay_key": key,
                "normalized_prompt": normalize_prompt(prompt),
                "contract_sha256": adapter.contract_sha256,
                "raw_model_output": json.dumps(parsed_plan),
                "parsed_plan": parsed_plan,
                "epistemic_tag": EPISTEMIC_TAG,
                "cassette_origin": "synthetic_planner_fixture",
            }

            out_file = out_dir / f"{key}.json"
            out_file.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
            print(f"Generated fixture [{qid}] -> {out_file.name}")


if __name__ == "__main__":
    generate_fixtures()
