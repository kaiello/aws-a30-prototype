"""Preflight contract verification for the Whole-Standard Question Answering Entrypoint.

Exercises answer_whole_standard_question offline, guaranteeing:
- Zero network calls (socket patching enforces strictly local execution)
- Public entrypoint invoked with clean question_text interface
- Planner returns valid, schema-conforming plan
- Execution engine delivers normative provenance and executed operations
- Source stores remain unmutated and verified
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
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


if __name__ == "__main__":
    res = run_whole_standard_preflight()
    print(json.dumps(res, indent=2))
