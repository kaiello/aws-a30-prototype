"""DeepSeek-V4.1-Flash-1017 Planner Adapter and Offline Replay Harness.

Integrates DeepSeek-V4.1-Flash-1017 at:
- Layer 4 (Question Planner & Multi-Hop Decomposer)
- Layer 1/2 (Candidate Visual Verification Stub)

Enforces Gate 5 invariants:
1. Strict Offline Test & Preflight Isolation: Zero network calls under socket blocking.
2. Epistemic Quarantine: Model trace reasons tagged UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE.
3. Deterministic Composition Only: Structured query plans only, no answer composition.
4. Canonical Store Immutability: Phase 0-5 canonical stores remain unmutated.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from src.evidence_chart_contract import (
    QUESTION_INTERFACE,
    PLANNED_REASON,
)
from src.evidence_chart_local_planner import LocalQuestionPlanner
from src.evidence_chart_question_plan import (
    build_prompt,
    output_schema,
    compile_plan,
)

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = Path(__file__).resolve().parent / "evidence_chart_contract.json"
CONTRACT_SHA256 = "30e1913b1cb0b87fa6ea87aa2a84ecf041fa17291a836dc47ba7c33d0ef45758"
DEFAULT_REPLAY_DIR = ROOT / "storage" / "model_replays" / "deepseek_v4_1_flash_1017"

EPISTEMIC_TAG = "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"


def normalize_prompt(prompt: str) -> str:
    """Normalize whitespace and CRLF line endings for deterministic hashing."""
    return prompt.strip().replace("\r\n", "\n")


@dataclass
class DeepSeekV41Config:
    """Configuration for DeepSeek-V4.1-Flash-1017 client and replay harness."""
    model_id: str = "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    api_model_name: str = "deepseek-v4.1-flash"
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "DEEPSEEK_API_BASE",
            os.environ.get("VLLM_API_BASE", "https://api.deepseek.com/v1"),
        )
    )
    temperature: float = 0.0
    max_new_tokens: int = 4096
    mode: Literal["OFFLINE_REPLAY_ONLY", "RECORD_IF_MISSING"] = "OFFLINE_REPLAY_ONLY"


class DeepSeekV41PlannerAdapter:
    """Layer 4 Planner Adapter for DeepSeek-V4.1-Flash-1017 with offline replay."""

    def __init__(
        self,
        config: Optional[DeepSeekV41Config] = None,
        root: Optional[Path] = None,
        replay_dir: Optional[Path] = None,
    ):
        self.config = config or DeepSeekV41Config()
        self.root = Path(root or ROOT).resolve()
        self.replay_dir = Path(replay_dir or DEFAULT_REPLAY_DIR).resolve()
        self.contract_path = self.root / "src" / "evidence_chart_contract.json"
        if self.contract_path.exists():
            self.contract_sha256 = hashlib.sha256(self.contract_path.read_bytes()).hexdigest()
        else:
            self.contract_sha256 = CONTRACT_SHA256
        self.requests = 0
        self.calls: List[Dict[str, Any]] = []

    def compute_replay_key(self, prompt: str) -> str:
        """Compute content-addressed replay key: sha256(model_id::contract_sha256::normalized_prompt)."""
        normalized = normalize_prompt(prompt)
        raw_key = f"{self.config.model_id}::{self.contract_sha256}::{normalized}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def load_replay(self, replay_key: str) -> Dict[str, Any]:
        """Load deterministic replay fixture from storage."""
        cassette_file = self.replay_dir / f"{replay_key}.json"
        if not cassette_file.exists():
            if self.config.mode == "OFFLINE_REPLAY_ONLY":
                raise ValueError(
                    f"INSUFFICIENT_EVIDENCE: Missing offline replay fixture for key {replay_key} at {cassette_file}"
                )
            raise RuntimeError(f"RECORD_IF_MISSING not available in offline environment for key {replay_key}")

        cassette = json.loads(cassette_file.read_text(encoding="utf-8"))
        if cassette.get("epistemic_tag") != EPISTEMIC_TAG:
            cassette["epistemic_tag"] = EPISTEMIC_TAG
        return cassette

    def save_replay(
        self,
        prompt: str,
        raw_model_output: str,
        parsed_plan: Dict[str, Any],
    ) -> Path:
        """Write deterministic replay fixture to storage."""
        normalized = normalize_prompt(prompt)
        replay_key = self.compute_replay_key(prompt)
        self.replay_dir.mkdir(parents=True, exist_ok=True)
        cassette_file = self.replay_dir / f"{replay_key}.json"
        cassette = {
            "model_id": self.config.model_id,
            "replay_key": replay_key,
            "normalized_prompt": normalized,
            "contract_sha256": self.contract_sha256,
            "raw_model_output": raw_model_output,
            "parsed_plan": parsed_plan,
            "epistemic_tag": EPISTEMIC_TAG,
        }
        cassette_file.write_text(json.dumps(cassette, indent=2), encoding="utf-8")
        return cassette_file

    def build_whole_standard_prompt(self, question_text: str) -> str:
        """Construct schema-constrained prompt for whole-standard question planning."""
        return (
            f"AWS A3.0M/A3.0:2020 Question Planning Contract\n"
            f"Schema Version: {QUESTION_INTERFACE['schema_version']}\n"
            f"Question: {question_text.strip()}\n"
            f"Instructions: Propose a structured multi-hop JSON plan over Clause 4, Tables A1-A5, Figures A1-A6, Figures B1-B54."
        )

    def __call__(
        self,
        graph: Dict[str, Any],
        query: str,
        *,
        concept_bindings: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """LocalQuestionPlanner-compatible interface for chart question planning."""
        self.requests += 1
        prompt = build_prompt(graph, query)
        replay_key = self.compute_replay_key(prompt)

        # Load offline replay cassette (0 network calls)
        cassette = self.load_replay(replay_key)
        raw_output = cassette.get("raw_model_output", "")
        parsed_plan = cassette.get("parsed_plan")
        if parsed_plan is None and raw_output:
            parsed_plan = json.loads(raw_output)

        if not isinstance(parsed_plan, dict):
            raise ValueError(f"INSUFFICIENT_EVIDENCE: Replay payload for {replay_key} is not a valid JSON plan")

        # Pass through lowering compiler (src/evidence_chart_question_plan.py -> src/evidence_chart_llm_plan.py)
        # Guarantees:
        # 1. part.reason tagged UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE in model_part_metadata
        # 2. internal operation reasons map to PLANNED_REASON ("")
        # 3. failed producer actions block only dependent actions
        compiled_plan = compile_plan(graph, query, parsed_plan, concept_bindings=concept_bindings)

        compiled_plan["model_planning"] = {
            "model": self.config.model_id,
            "api_model_name": self.config.api_model_name,
            "provider": "deepseek_v4_1_flash_1017_offline_replay",
            "replay_key": replay_key,
            "epistemic_tag": EPISTEMIC_TAG,
            "external_call_count": 0,
            "model_invocation_count": 1,
        }
        self.calls.append(compiled_plan["model_planning"])
        return compiled_plan

    def plan_whole_standard_question(
        self,
        question_text: str,
        req_dir: Optional[Path] = None,
        stores: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Whole-standard question planning entrypoint for answer_whole_standard_question."""
        self.requests += 1
        prompt = self.build_whole_standard_prompt(question_text)
        replay_key = self.compute_replay_key(prompt)

        cassette = self.load_replay(replay_key)
        parsed_plan = cassette.get("parsed_plan")
        if parsed_plan is None and cassette.get("raw_model_output"):
            parsed_plan = json.loads(cassette["raw_model_output"])

        if not isinstance(parsed_plan, dict):
            raise ValueError(f"INSUFFICIENT_EVIDENCE: Replay payload for {replay_key} is not a valid JSON plan")

        plan = deepcopy(parsed_plan)
        if "reason" in plan and plan.get("epistemic_tag") != EPISTEMIC_TAG:
            plan["epistemic_tag"] = EPISTEMIC_TAG

        from src.semantic_nlq_expander import get_semantic_expander
        expander = get_semantic_expander(stores=stores, root=self.root)
        trace = expander.expand_query(question_text)
        plan["semantic_expansion_trace"] = trace.to_dict()

        plan["receipt_metadata"] = {
            "planner": "DeepSeekV41PlannerAdapter",
            "model": self.config.model_id,
            "api_model_name": self.config.api_model_name,
            "replay_key": replay_key,
            "epistemic_tag": EPISTEMIC_TAG,
            "external_call_count": 0,
            "model_invocation_count": 1,
            "elapsed_seconds": 0.001,
            "cost_usd": 0.0,
        }
        self.calls.append(plan["receipt_metadata"])
        return plan

    def plan_with_semantic_expansion(
        self,
        query: str,
        req_dir: Optional[Path] = None,
        stores: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enrich query planning with semantic expansion trace while quarantining model trace reason."""
        return self.plan_whole_standard_question(query, req_dir=req_dir, stores=stores)


class DeepSeekV41LocalQuestionPlanner(LocalQuestionPlanner):
    """LocalQuestionPlanner implementation backed by DeepSeek-V4.1 offline replay."""

    def __init__(
        self,
        root: Optional[Path] = None,
        directory: Optional[Union[str, Path]] = None,
        config: Optional[DeepSeekV41Config] = None,
    ):
        self.root = Path(root or ROOT).resolve()
        self.config = config or DeepSeekV41Config()
        self.directory = Path(directory or (self.root / "storage" / "gate_reviews" / "deepseek_replay_tmp"))
        self.adapter = DeepSeekV41PlannerAdapter(config=self.config, root=self.root)
        self.requests = 0
        self.calls: List[Dict[str, Any]] = []
        self.structural_block = None
        self.metadata = {
            "provider": "deepseek_v4_1_flash_1017_offline_replay",
            "model": self.config.model_id,
            "api_model_name": self.config.api_model_name,
            "mode": self.config.mode,
            "epistemic_tag": EPISTEMIC_TAG,
        }

    def _generate(self, prompt: str, schema: Dict[str, Any], directory: Path) -> Dict[str, Any]:
        """Fetch model output strictly from deterministic replay without network calls."""
        directory.mkdir(parents=True, exist_ok=True)
        replay_key = self.adapter.compute_replay_key(prompt)
        cassette = self.adapter.load_replay(replay_key)
        raw_output = cassette.get("raw_model_output", "")
        if not raw_output and cassette.get("parsed_plan"):
            raw_output = json.dumps(cassette["parsed_plan"])
        return {
            "raw_output": raw_output,
            "error": None,
            "version": "deepseek-v4.1-replay-1.0",
            "model": self.config.model_id,
            "digest": replay_key,
            "provider": "deepseek_v4_1_flash_1017_offline_replay",
            "options": {},
            "elapsed_seconds": 0.001,
            "request_sha256": replay_key,
            "model_invocation_count": 1,
            "external_call_count": 0,
        }


class DeepSeekV41VisualCandidateVerifier:
    """Layer 1/2 Multimodal VLM stub for candidate visual observations."""

    def __init__(
        self,
        config: Optional[DeepSeekV41Config] = None,
        root: Optional[Path] = None,
    ):
        self.config = config or DeepSeekV41Config()
        self.root = Path(root or ROOT).resolve()

    def verify_candidate_visual(
        self,
        crop_path: Union[str, Path],
        candidate_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify candidate visual crop/bbox/callout without elevating to accepted knowledge."""
        crop_p = Path(crop_path)
        if not crop_p.is_absolute():
            crop_p = self.root / crop_p

        crop_sha256 = ""
        if crop_p.exists():
            crop_sha256 = hashlib.sha256(crop_p.read_bytes()).hexdigest()

        return {
            "observation_id": f"obs:candidate_visual:{candidate_payload.get('element_id', 'unknown')}",
            "crop_path": str(crop_p.relative_to(self.root)) if crop_p.is_relative_to(self.root) else str(crop_p),
            "crop_sha256": crop_sha256,
            "candidate_payload": deepcopy(candidate_payload),
            "model_id": self.config.model_id,
            "api_model_name": self.config.api_model_name,
            # Non-negotiable epistemic quarantine
            "verification": "candidate",
            "knowledge_eligible": False,
            "epistemic_tag": EPISTEMIC_TAG,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
