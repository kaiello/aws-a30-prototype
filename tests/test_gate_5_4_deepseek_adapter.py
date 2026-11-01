"""Gate 5.4 Test Suite: DeepSeek-V4.1-Flash-1017 Planner Adapter and Offline Replay Harness.

Verifies:
1. test_deepseek_v41_offline_replay_zero_network: Zero network calls under socket block.
2. test_deepseek_v41_quarantines_model_trace_reason: Model trace reason quarantined as UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE.
3. test_deepseek_v41_missing_replay_raises_insufficient_evidence: Uncached prompts raise INSUFFICIENT_EVIDENCE.
4. test_deepseek_v41_visual_verifier_enforces_candidate_only: Candidate visual observations strictly candidate-only.
5. test_deepseek_v41_canonical_stores_unmutated: All 7 canonical stores remain byte-identical.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import socket
import tempfile
from unittest.mock import patch
import pytest

from test_evidence_chart_llm_plan import source
from test_evidence_a1_graph_qa import toy_graph
from test_evidence_a2_core import bind, nested
from test_evidence_a1_provenance import fixture
from src.evidence_a1 import bind_a1_graph_evidence
from src.evidence_a1_graph_qa import answer_graph
from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    ROOT,
)
from src.evidence_whole_standard_preflight import (
    LOCKED_STORE_HASHES,
    run_deepseek_replay_preflight,
)
from src.deepseek_v41_adapter import (
    DeepSeekV41Config,
    DeepSeekV41PlannerAdapter,
    DeepSeekV41LocalQuestionPlanner,
    DeepSeekV41VisualCandidateVerifier,
    EPISTEMIC_TAG,
)


def _guard_network(*args, **kwargs):
    raise RuntimeError("Network blocked: offline execution contract violation")


@pytest.fixture
def a2_source():
    raw_toy = toy_graph.__wrapped__() if hasattr(toy_graph, "__wrapped__") else toy_graph()
    return bind(nested(raw_toy))


@pytest.fixture
def a1_source():
    g, src_kwargs = fixture()
    return bind_a1_graph_evidence(g, **src_kwargs)


def test_deepseek_v41_offline_replay_zero_network(a2_source, a1_source):
    """Verify DeepSeekV41PlannerAdapter replays plans offline under socket interception."""
    stores = get_whole_standard_stores(ROOT)
    adapter = DeepSeekV41PlannerAdapter(root=ROOT)

    with patch("socket.socket", side_effect=_guard_network), \
         patch("socket.create_connection", side_effect=_guard_network):

        # 1. Figure A2 chart query replay
        q_a2 = "Give the name, acronym and group for ZZRP in Figure A2."
        plan_a2 = adapter(a2_source, q_a2)
        assert plan_a2["status"] == "ready"
        assert plan_a2["model_planning"]["model"] == "deepseek-ai/DeepSeek-V4.1-Flash-1017"
        assert plan_a2["model_planning"]["external_call_count"] == 0

        # Execute through graph composer
        ans_a2 = answer_graph(a2_source, q_a2, question_planner=adapter)
        assert ans_a2["answer_outcome"] == "graph_answer"
        assert "Ribbon folding pulsed" in ans_a2["answer"]

        # 2. Figure A1 chart query replay
        q_a1 = "Provide all processes under arc welding (aw)- include the process and the acronym."
        plan_a1 = adapter(a1_source, q_a1)
        assert plan_a1["status"] == "ready"
        assert plan_a1["model_planning"]["model"] == "deepseek-ai/DeepSeek-V4.1-Flash-1017"

        # 3. Whole-standard multi-hop query replay
        q_mh = (
            "What is the definition of shielded metal arc welding in Clause 4, "
            "what letter designation is assigned in Table A1, and which figure illustrates arc welding power source waveforms?"
        )
        res_mh = answer_whole_standard_question(q_mh, planner=adapter, stores=stores)
        assert res_mh["execution"]["status"] == "PASS"
        assert len(res_mh["execution"]["operations"]) >= 1
        assert len(res_mh["execution"]["normative_provenance"]) >= 1


def test_deepseek_v41_quarantines_model_trace_reason(a2_source):
    """Verify non-empty part.reason traces are quarantined as UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE."""
    adapter = DeepSeekV41PlannerAdapter(root=ROOT)
    q_a2 = "Give the name, acronym and group for ZZRP in Figure A2."

    with patch("socket.socket", side_effect=_guard_network):
        plan = adapter(a2_source, q_a2)

        # Invariant 1: lowered internal wire plan reason is empty (PLANNED_REASON)
        assert plan["lowered_plan"]["parts"][0]["reason"] == ""

        # Invariant 2: original model reason is captured with UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE authority
        part_meta = plan["model_part_metadata"][0]
        assert part_meta["authority"] == EPISTEMIC_TAG
        assert "DeepSeek-V4.1 trace" in part_meta["original_reason"]

        # Invariant 3: composer execution never leaks model trace into answer or evidence provenance
        ans = answer_graph(a2_source, q_a2, question_planner=adapter)
        assert "DeepSeek-V4.1" not in ans["answer"]
        assert "trace" not in ans["answer"].lower()
        evidence_list = str(ans.get("evidence_ids", [])) + str(ans.get("normative_provenance", []))
        assert "DeepSeek" not in evidence_list


def test_deepseek_v41_missing_replay_raises_insufficient_evidence(a2_source):
    """Verify that an uncached query in OFFLINE_REPLAY_ONLY mode strictly raises INSUFFICIENT_EVIDENCE."""
    adapter = DeepSeekV41PlannerAdapter(
        config=DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"),
        root=ROOT,
    )
    novel_query = "What is the unrecorded hypothetical process in Figure A2?"

    with patch("socket.socket", side_effect=_guard_network):
        with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
            adapter(a2_source, novel_query)


def test_deepseek_v41_visual_verifier_enforces_candidate_only():
    """Verify DeepSeekV41VisualCandidateVerifier emits strictly candidate observations."""
    verifier = DeepSeekV41VisualCandidateVerifier(root=ROOT)
    crop_path = ROOT / "parsed" / "figures" / "Figure_A1_p88.png"

    candidate_payload = {
        "element_id": "Figure A1",
        "callout": "Solid-State Welding (SSW)",
        "bbox": [0.12, 0.05, 0.88, 0.22],
    }

    obs = verifier.verify_candidate_visual(crop_path, candidate_payload)

    # Architectural Invariants
    assert obs["verification"] == "candidate", "Must never emit accepted verification"
    assert obs["knowledge_eligible"] is False, "Must never be knowledge-eligible without geometric proof"
    assert obs["epistemic_tag"] == EPISTEMIC_TAG
    assert obs["model_id"] == "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    assert obs["api_model_name"] == "deepseek-v4.1-flash"
    assert obs["crop_sha256"] != "", "Crop SHA-256 must be computed"
    assert obs["observation_id"].startswith("obs:candidate_visual:")


def test_deepseek_v41_local_question_planner_interface(a2_source):
    """Verify DeepSeekV41LocalQuestionPlanner executes through the LocalQuestionPlanner contract."""
    with tempfile.TemporaryDirectory() as td:
        local_planner = DeepSeekV41LocalQuestionPlanner(root=ROOT, directory=td)
        q = "Give the name, acronym and group for ZZRP in Figure A2."

        with patch("socket.socket", side_effect=_guard_network):
            plan = local_planner(a2_source, q)
            assert plan["status"] == "ready"
            assert plan["lowered_plan"]["parts"][0]["reason"] == ""
            assert plan["model_part_metadata"][0]["authority"] == EPISTEMIC_TAG


def test_deepseek_v41_preflight_runner():
    """Verify run_deepseek_replay_preflight passes cleanly."""
    preflight_res = run_deepseek_replay_preflight(root=ROOT)
    assert preflight_res["status"] == "CLEAR_DEEPSEEK_REPLAY_PREFLIGHT"
    assert preflight_res["network_calls"] == 0
    assert preflight_res["epistemic_quarantine_verified"] is True
    assert preflight_res["canonical_stores_verified"] == 7
    assert preflight_res["replayed_queries_count"] >= 4


def test_deepseek_v41_canonical_stores_unmutated():
    """Verify all 7 canonical stores remain byte-identical to locked SHA-256 digests."""
    for rel_path, expected_hash in LOCKED_STORE_HASHES.items():
        full_path = ROOT / rel_path
        assert full_path.exists(), f"Store missing: {rel_path}"
        h = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_hash = h.hexdigest()
        assert actual_hash == expected_hash, f"Canonical store mutated: {rel_path}"


LOCKED_GATE_5_4_REPLAY_HASHES = {
    "storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json": "59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f",
    "storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json": "e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079",
    "storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json": "5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d",
    "storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json": "6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a",
    "storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json": "d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592",
}


def test_deepseek_v41_replay_cassettes_locked():
    """Verify all 5 Gate 5.4 DeepSeek replay cassettes match locked SHA-256 digests."""
    for rel_path, expected_hash in LOCKED_GATE_5_4_REPLAY_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Replay cassette missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Replay cassette mutated: {rel_path}"


def test_deepseek_v41_anti_drift_regex_coverage():
    """Verify anti-drift pattern scans all question ID families including Gate 5.4 and Gate 5.5."""
    import re
    regex_pattern = r"QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+"
    forbidden_literals_re = re.compile(
        r"hyper-flux|laser-quantum|cryo-ionic|ASME\s+Section\s+IX|yield\s+strength|E7018",
        re.IGNORECASE,
    )

    targets = [ROOT / "src/deepseek_v41_adapter.py"]
    violations = []
    for target in targets:
        text = target.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(regex_pattern, line):
                violations.append(f"{target.relative_to(ROOT)}:{i}: {line.strip()}")
            if forbidden_literals_re.search(line):
                violations.append(f"Forbidden literal in {target.relative_to(ROOT)}:{i}: {line.strip()}")

    assert not violations, "Anti-drift or anti-overfitting violations in DeepSeek adapter:\n" + "\n".join(violations)
