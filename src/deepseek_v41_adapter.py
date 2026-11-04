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
        ner_receipt = trace.ner_receipt or {}
        plan["ner_entities"] = list(ner_receipt.get("spans", []))
        plan["multi_intent_targets"] = {
            "target_divisions": list(ner_receipt.get("target_divisions", [])),
            "inferred_targets": dict(trace.inferred_targets),
            "ner_inferred_targets": dict(ner_receipt.get("inferred_targets", {})),
            "has_ambiguities": bool(ner_receipt.get("has_ambiguities", False)),
        }

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


def audit_replay_coverage(
    root: Optional[Path] = None,
    write_manifest: bool = False,
) -> Dict[str, Any]:
    """Audit genuine DeepSeek-V4.1 replay cassettes vs quarantined synthetic fixtures across benchmarks."""
    resolved_root = Path(root or ROOT).resolve()
    adapter = DeepSeekV41PlannerAdapter(config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"), root=resolved_root)

    replay_dir = resolved_root / "storage" / "model_replays" / "deepseek_v4_1_flash_1017"
    fixtures_dir = resolved_root / "storage" / "model_replays" / "deterministic_planner_fixtures"

    genuine_cassettes: List[Dict[str, Any]] = []
    if replay_dir.exists():
        for p in sorted(replay_dir.glob("*.json")):
            if p.name == "index.json":
                continue
            data = json.loads(p.read_text(encoding="utf-8"))
            if "replay_key" in data:
                genuine_cassettes.append({
                    "replay_key": data["replay_key"],
                    "file": str(p.relative_to(resolved_root)).replace("\\", "/"),
                    "model_id": data.get("model_id"),
                    "epistemic_tag": data.get("epistemic_tag"),
                })

    quarantined_fixtures: List[Dict[str, Any]] = []
    if fixtures_dir.exists():
        for p in sorted(fixtures_dir.glob("*.json")):
            if p.name == "index.json":
                continue
            data = json.loads(p.read_text(encoding="utf-8"))
            if "replay_key" in data:
                quarantined_fixtures.append({
                    "replay_key": data["replay_key"],
                    "file": str(p.relative_to(resolved_root)).replace("\\", "/"),
                    "model_id": data.get("model_id"),
                    "epistemic_tag": data.get("epistemic_tag"),
                })

    genuine_keys = {c["replay_key"] for c in genuine_cassettes}
    fixture_keys = {f["replay_key"] for f in quarantined_fixtures}

    benchmark_specs = [
        ("phase5_5_nlq_001", "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json"),
        ("phase6_ner_routing_001", "storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json"),
        ("phase6_1_semantic_graph_001", "storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json"),
        ("phase6_2_generalization_holdout_001", "storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json"),
        ("phase6_3_blind_hardening_001", "storage/evidence_v2/phase6_3_blind_hardening_001/questions.json"),
        ("phase6_6_reader_qualification_001", "storage/evidence_v2/phase6_6_reader_qualification_001/questions.json"),
    ]

    benchmarks_report: Dict[str, Any] = {}
    for bench_name, rel_q_path in benchmark_specs:
        q_path = resolved_root / rel_q_path
        if not q_path.exists():
            continue
        q_items = json.loads(q_path.read_text(encoding="utf-8"))
        gen_cnt = 0
        fix_cnt = 0
        det_cnt = 0
        query_ledger: List[Dict[str, Any]] = []
        for item in q_items:
            qid = item.get("id")
            q_text = item.get("query") or item.get("question") or ""
            r_key = adapter.compute_replay_key(adapter.build_whole_standard_prompt(q_text))
            if r_key in genuine_keys:
                source_class = "genuine_model_replay"
                gen_cnt += 1
            elif r_key in fixture_keys:
                source_class = "quarantined_synthetic_fixture"
                fix_cnt += 1
            else:
                source_class = "deterministic_planner_fallback"
                det_cnt += 1
            query_ledger.append({
                "id": qid,
                "replay_key": r_key,
                "source_class": source_class,
            })
        benchmarks_report[bench_name] = {
            "questions_file": rel_q_path,
            "total_queries": len(q_items),
            "genuine_model_replays": gen_cnt,
            "quarantined_synthetic_fixtures": fix_cnt,
            "deterministic_planner_fallbacks": det_cnt,
            "queries": query_ledger,
        }

    manifest = {
        "schema_version": "replay_coverage_manifest_v1.0",
        "gate": "Gate 6.6",
        "model_id": adapter.config.model_id,
        "contract_sha256": adapter.contract_sha256,
        "epistemic_tag": EPISTEMIC_TAG,
        "genuine_model_replays_count": len(genuine_cassettes),
        "quarantined_synthetic_fixtures_count": len(quarantined_fixtures),
        "genuine_model_replays": genuine_cassettes,
        "quarantined_synthetic_fixtures": quarantined_fixtures,
        "benchmarks": benchmarks_report,
    }

    if write_manifest:
        out_path = resolved_root / "storage" / "manifests" / "replay_coverage_manifest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return manifest

