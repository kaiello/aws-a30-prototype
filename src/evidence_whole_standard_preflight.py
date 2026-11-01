"""Preflight contract verification for the Whole-Standard Question Answering Entrypoint.

Exercises answer_whole_standard_question offline, guaranteeing:
- Zero network calls (socket patching enforces strictly local execution)
- Public entrypoint invoked with clean question_text interface
- Planner returns valid, schema-conforming plan
- Execution engine delivers normative provenance and executed operations
- Source stores remain unmutated and verified
- DeepSeek-V4.1-Flash-1017 offline replay harness verified under network isolation
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
from typing import Any, Dict, Optional
from unittest.mock import patch

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)

PREFLIGHT_VERSION = "whole-standard-preflight-1.0"

LOCKED_STORE_HASHES = {
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class NetworkBlockedError(RuntimeError):
    """Raised if any network activity is attempted during offline preflight."""
    pass


def _guard_socket(*args, **kwargs):
    raise NetworkBlockedError("Offline preflight contract violation: network socket activity detected")


def run_whole_standard_preflight(
    root: Optional[Path] = None,
    test_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute preflight verification of answer_whole_standard_question under network isolation."""
    if root is None:
        root = Path(__file__).resolve().parent.parent

    # 1. Verify canonical store SHA-256 hashes before execution
    store_digests = {}
    for rel_path, expected_hash in LOCKED_STORE_HASHES.items():
        full_path = root / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Missing canonical store: {rel_path}")
        actual_hash = _sha(full_path)
        if actual_hash != expected_hash:
            raise ValueError(f"Store hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
        store_digests[rel_path] = actual_hash

    # 2. Load stores locally
    stores = get_whole_standard_stores(root)
    planner = DeterministicQuestionPlanner(root)

    # 3. Default representative query across whole standard
    if test_query is None:
        test_query = (
            "What are the six standard suffix letter modifiers defined in Table A4 "
            "for the application mode of welding and allied processes, and what does the suffix -AU designate?"
        )

    # 4. Execute under strict network block
    with patch("socket.socket", side_effect=_guard_socket), \
         patch("socket.create_connection", side_effect=_guard_socket):
        result = answer_whole_standard_question(test_query, planner, stores=stores)

    # 5. Contract assertions
    if not isinstance(result, dict):
        raise TypeError(f"Contract violation: result is {type(result)}, expected dict")

    execution = result.get("execution")
    if not isinstance(execution, dict):
        raise TypeError("Contract violation: execution block missing or not dict")

    status = execution.get("status")
    if status != "PASS":
        raise ValueError(f"Contract violation: unexpected execution status '{status}'")

    answer = result.get("answer") or execution.get("answer")
    if not answer or not isinstance(answer, str):
        raise ValueError("Contract violation: empty or non-string answer")

    operations = execution.get("operations", [])
    if not operations or not isinstance(operations, list):
        raise ValueError("Contract violation: missing or invalid operations list")

    provenance = execution.get("normative_provenance", [])
    if not provenance or not isinstance(provenance, list):
        raise ValueError("Contract violation: missing or invalid normative_provenance")

    elements = execution.get("elements_present", [])
    if not elements or not isinstance(elements, list):
        raise ValueError("Contract violation: missing elements_present")

    # 6. Verify stores were not mutated in place
    for rel_path, expected_hash in LOCKED_STORE_HASHES.items():
        actual_hash = _sha(root / rel_path)
        if actual_hash != expected_hash:
            raise ValueError(f"Post-execution mutation detected on {rel_path}")

    return {
        "status": "CLEAR_WHOLE_STANDARD_CONTRACT",
        "preflight_version": PREFLIGHT_VERSION,
        "test_query": test_query,
        "operations_count": len(operations),
        "provenance_count": len(provenance),
        "network_calls": 0,
        "canonical_stores_verified": len(store_digests),
    }


def run_deepseek_replay_preflight(
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute preflight verification of DeepSeek-V4.1-Flash-1017 replay harness under network isolation."""
    if root is None:
        root = Path(__file__).resolve().parent.parent

    # 1. Verify canonical store SHA-256 hashes before execution
    store_digests = {}
    for rel_path, expected_hash in LOCKED_STORE_HASHES.items():
        full_path = root / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Missing canonical store: {rel_path}")
        actual_hash = _sha(full_path)
        if actual_hash != expected_hash:
            raise ValueError(f"Store hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
        store_digests[rel_path] = actual_hash

    from src.deepseek_v41_adapter import DeepSeekV41PlannerAdapter, DeepSeekV41LocalQuestionPlanner
    adapter = DeepSeekV41PlannerAdapter(root=root)
    stores = get_whole_standard_stores(root)

    replayed = []

    with patch("socket.socket", side_effect=_guard_socket), \
         patch("socket.create_connection", side_effect=_guard_socket):

        # Replay 1: Whole-Standard Multi-Hop Cross-Store
        q_mh = (
            "What is the definition of shielded metal arc welding in Clause 4, "
            "what letter designation is assigned in Table A1, and which figure illustrates arc welding power source waveforms?"
        )
        plan_mh = adapter.plan_whole_standard_question(q_mh, stores=stores)
        if plan_mh.get("intent") != "cross_store_multihop":
            raise ValueError("DeepSeek replay plan intent mismatch for multi-hop query")
        if plan_mh.get("receipt_metadata", {}).get("epistemic_tag") != "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE":
            raise ValueError("Epistemic quarantine tag missing on whole-standard plan")
        res_mh = answer_whole_standard_question(q_mh, planner=adapter, stores=stores)
        if res_mh.get("execution", {}).get("status") != "PASS":
            raise ValueError("Whole-standard multi-hop execution did not PASS under DeepSeek planner")
        replayed.append("multi_hop_cross_store")

        # Replay 2: Adversarial Out-of-Range Query
        q_oor = "Which processes are classified on Figure A7 and Figure B55 in AWS A3.0?"
        plan_oor = adapter.plan_whole_standard_question(q_oor, stores=stores)
        if plan_oor.get("intent") != "refusal_out_of_range":
            raise ValueError("DeepSeek replay plan intent mismatch for out-of-range query")
        replayed.append("adversarial_out_of_range")

        # Replay 3: Adversarial False-Premise Query
        q_fp = "Why is shielded metal arc welding categorized under solid-state welding in AWS A3.0?"
        plan_fp = adapter.plan_whole_standard_question(q_fp, stores=stores)
        if plan_fp.get("intent") != "refusal_false_premise":
            raise ValueError("DeepSeek replay plan intent mismatch for false-premise query")
        replayed.append("adversarial_false_premise")

        # Replay 4: Figure A2 Chart Planning through LocalQuestionPlanner interface
        tests_dir = root / "tests"
        if str(tests_dir) not in sys.path:
            sys.path.insert(0, str(tests_dir))

        from test_evidence_a1_graph_qa import toy_graph as _toy_fixture
        from test_evidence_a2_core import bind as _bind, nested as _nested

        with tempfile.TemporaryDirectory() as td:
            local_planner = DeepSeekV41LocalQuestionPlanner(root=root, directory=td)
            raw_toy = _toy_fixture.__wrapped__() if hasattr(_toy_fixture, "__wrapped__") else _toy_fixture()
            src_a2 = _bind(_nested(raw_toy))
            q_a2 = "Give the name, acronym and group for ZZRP in Figure A2."
            chart_plan = local_planner(src_a2, q_a2)
            if chart_plan.get("status") != "ready":
                raise ValueError("DeepSeek chart plan status is not ready")
            meta = chart_plan.get("model_part_metadata", [{}])[0]
            if meta.get("authority") != "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE":
                raise ValueError("Model trace authority quarantine failed in chart plan")
            if chart_plan.get("lowered_plan", {}).get("parts", [{}])[0].get("reason") != "":
                raise ValueError("Lowered wire plan reason is not empty")
            replayed.append("chart_figure_a2_local_planner")

    # Verify stores were not mutated in place
    for rel_path, expected_hash in LOCKED_STORE_HASHES.items():
        actual_hash = _sha(root / rel_path)
        if actual_hash != expected_hash:
            raise ValueError(f"Post-execution mutation detected on {rel_path}")

    return {
        "status": "CLEAR_DEEPSEEK_REPLAY_PREFLIGHT",
        "preflight_version": PREFLIGHT_VERSION,
        "adapter_model": adapter.config.model_id,
        "api_model_name": adapter.config.api_model_name,
        "replayed_queries_count": len(replayed),
        "replayed_queries": replayed,
        "network_calls": 0,
        "epistemic_quarantine_verified": True,
        "canonical_stores_verified": len(store_digests),
    }


if __name__ == "__main__":
    res_whole = run_whole_standard_preflight()
    res_ds = run_deepseek_replay_preflight()
    print(json.dumps({
        "whole_standard": res_whole,
        "deepseek_replay": res_ds,
    }, indent=2))
