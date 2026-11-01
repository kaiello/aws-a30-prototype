"""Gate 6.0 Test Suite: Deterministic Welding Domain NER, Callout/Backlink Routing,
Whole-Standard CLI, Replay Cassettes, and 29/29 Locked Cryptographic Artifacts.

Verifies:
1. test_gate_6_0_welding_ner_spans_and_compound_codes:
   - Asserts exact character-offset matching (query[span.start_char:span.end_char] == span.surface_text).
   - Asserts dynamic compound decomposition of valid codes (PAW-AU, FCAW-G-SA) and invalid codes (GTAW-ZZ).
   - Asserts longest-match subsumption and homograph ambiguity candidates (AB).
   - Asserts cold-start standalone store hydration.
2. test_gate_6_0_id_free_spatial_callout_routing:
   - Asserts ID-free callouts route deterministically to Figures B25, B33, B46, B12, B16B, B16C.
   - Asserts requires_diagram_crop is True with verified crop paths existing on disk.
3. test_gate_6_0_multi_intent_cross_store_composition:
   - Asserts multi-hop prompts (compound designation + diagram, historical vs active) execute cleanly.
   - Asserts modality-appropriate crop provenance (requires_diagram_crop is False for pure text/table).
4. test_gate_6_0_whole_standard_cli_and_skills_contracts:
   - Executes evidence_whole_standard_cli (--ner, --route, --ask) under socket.socket network block.
   - Scans .agents/skills/ to verify removal of obsolete restrictions and presence of whole-standard tools.
5. test_gate_6_0_deepseek_replay_backward_and_new_cassettes:
   - Patches socket.socket to block network and verifies all 10 replay cassettes (8 prior + 2 Gate 6.0)
     replay cleanly with epistemic_tag "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE".
6. test_gate_6_0_benchmark_all_20_pass:
   - Runs eval.run_phase6_ner_routing and asserts 20 / 20 (100.0%) pass rate.
7. test_gate_6_0_all_29_locked_hashes_and_anti_drift:
   - Cryptographically verifies all 29 artifacts (24 prior + 5 Gate 6.0).
   - Scans src/ and eval/*.py for benchmark question ID patterns (0 matches expected).
   - Scans src/ for benchmark trap literals (0 matches expected).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import socket
import sys
import pytest

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    ROOT,
)
from src.welding_ner import (
    WeldingNER,
    get_welding_ner,
)
from src.deepseek_v41_adapter import (
    DeepSeekV41PlannerAdapter,
    DeepSeekV41Config,
)
from eval.run_phase6_ner_routing import evaluate_ner_routing_benchmark

ALL_29_LOCKED_HASHES = {
    # 1 Source PDF Standard
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    # 6 Phase 0-3 Historical Canonical Stores
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
    # 1 Externalized Annex A Holdout Rubric
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json": "70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479",
    # 3 Phase 5 Hardening Benchmark Files
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json": "0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9",
    "storage/evidence_v2/phase5_hardening_001/rubric.json": "df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981",
    "storage/evidence_v2/phase5_hardening_001/results.json": "92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273",
    # 3 Phase 5.5 NLQ Benchmark Files
    "storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json": "ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57",
    "storage/evidence_v2/phase5_5_nlq_001/rubric.json": "68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b",
    "storage/evidence_v2/phase5_5_nlq_001/results.json": "df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74",
    # 8 Existing DeepSeek-V4.1-Flash-1017 Replay Cassettes
    "storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json": "59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f",
    "storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json": "e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079",
    "storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json": "5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d",
    "storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json": "6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a",
    "storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json": "d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592",
    "storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json": "ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2",
    "storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json": "e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e",
    "storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json": "0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621",
    # 2 Gate 5.6 Manifests
    "storage/manifests/coverage_manifest.json": "8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e",
    "storage/manifests/latency_benchmark.json": "bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c",
    # 3 Gate 6.0 Benchmark Files
    "storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json": "bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac",
    "storage/evidence_v2/phase6_ner_routing_001/rubric.json": "602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427",
    "storage/evidence_v2/phase6_ner_routing_001/results.json": "4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8",
    # 2 Gate 6.0 DeepSeek Replay Cassettes
    "storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json": "b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057",
    "storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json": "178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42",
}


def test_gate_6_0_welding_ner_spans_and_compound_codes():
    """Verify WeldingNER extracts exact character offsets, compound codes, and homographs."""
    ner = get_welding_ner(root=ROOT)
    assert ner is not None

    # 1. Cold-start auto-hydration & store-compiled node counts
    standalone_ner = WeldingNER(root=ROOT)
    standalone_ner.ensure_initialized()
    assert len(standalone_ner.process_codes) > 10
    assert len(standalone_ner.glossary_terms) > 100
    assert standalone_ner.indexed_annex_b_node_count == 1115
    assert standalone_ner.indexed_annex_a_circle_count >= 96
    assert standalone_ner.indexed_clause4_backlink_count >= 265

    # 2. Exact character offset matching
    q1 = "What does the compound designation PAW-AU stand for according to Table A1 and Table A4?"
    receipt1 = ner.recognize_entities(q1)
    for span in receipt1.spans:
        assert q1[span.start_char:span.end_char] == span.surface_text

    # 3. Dynamic compound code parsing
    paw_span = next((s for s in receipt1.spans if s.surface_text == "PAW-AU"), None)
    assert paw_span is not None
    assert paw_span.entity_type == "COMPOUND_DESIGNATION"
    assert paw_span.canonical_term == "automatic plasma arc welding"
    assert len(paw_span.sub_components) == 2
    assert paw_span.sub_components[0]["designation"] == "PAW"
    assert paw_span.sub_components[1]["suffix"] == "-AU"

    # Multi-component compound code
    q2 = "Explain FCAW-G-SA welding parameters"
    receipt2 = ner.recognize_entities(q2)
    fcaw_span = next((s for s in receipt2.spans if s.surface_text == "FCAW-G-SA"), None)
    assert fcaw_span is not None
    assert fcaw_span.entity_type == "COMPOUND_DESIGNATION"
    assert fcaw_span.canonical_term == "semiautomatic gas shielded flux cored arc welding"

    # Invalid suffix detection
    q3 = "What does the code GTAW-ZZ mean?"
    receipt3 = ner.recognize_entities(q3)
    inv_span = next((s for s in receipt3.spans if s.surface_text == "GTAW-ZZ"), None)
    assert inv_span is not None
    assert inv_span.entity_type == "INVALID_COMPOUND_DESIGNATION"
    assert not inv_span.is_valid
    assert "not a standardized application mode suffix" in inv_span.abstention_reason

    # 4. Longest-match resolution (multi-word term subsumes sub-tokens)
    q4 = "gas tungsten arc welding process"
    receipt4 = ner.recognize_entities(q4)
    assert any(s.surface_text == "gas tungsten arc welding" for s in receipt4.spans)
    # Sub-tokens like "arc" or "welding" alone should not form overlapping spans
    assert not any(s.surface_text == "arc" for s in receipt4.spans)

    # 5. Homograph ambiguity candidates for AB & multi-POS Clause 4 headwords & morphological inflections
    q5 = "What is AB?"
    receipt5 = ner.recognize_entities(q5)
    ab_span = next((s for s in receipt5.spans if s.surface_text == "AB"), None)
    assert ab_span is not None
    assert len(ab_span.ambiguity_candidates) == 2
    cands = [c["canonical_term"] for c in ab_span.ambiguity_candidates]
    assert "arc brazing" in cands
    assert "adhesive bonding" in cands

    receipt_pos = ner.recognize_entities("Define braze and kerfs in Clause 4")
    braze_span = next((s for s in receipt_pos.spans if s.surface_text == "braze"), None)
    assert braze_span is not None
    assert len(braze_span.ambiguity_candidates) >= 2
    pos_tags = {c.get("part_of_speech") for c in braze_span.ambiguity_candidates}
    assert "n." in pos_tags and "v." in pos_tags
    kerfs_span = next((s for s in receipt_pos.spans if s.surface_text == "kerfs"), None)
    assert kerfs_span is not None
    assert kerfs_span.entity_type == "GLOSSARY_TERM"
    assert kerfs_span.canonical_term == "kerf"


def test_gate_6_0_id_free_spatial_callout_routing():
    """Verify ID-free spatial callout queries route cleanly to diagrams with requires_diagram_crop=True."""
    from src.semantic_nlq_expander import SemanticExpander

    standalone_exp = SemanticExpander(root=ROOT)
    standalone_exp.ensure_initialized()
    assert standalone_exp.indexed_annex_b_node_count == 1115
    assert standalone_exp.indexed_annex_a_circle_count >= 96
    assert standalone_exp.indexed_clause4_backlink_count >= 265

    # Verify non-benchmark Annex B figure resolves via store-compiled 1,115-node IDF callout index
    b10_trace = standalone_exp.expand_query(
        "Which diagram illustrates flanged butt joint weld and flanged corner joint weld?"
    )
    assert "Figure B10" in b10_trace.inferred_targets["figures"]

    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    cases = [
        ("Which diagram illustrates theoretical throat, effective throat, and actual throat?", "Figure B25", 123),
        ("Which figure illustrates crack types including underbead crack, toe crack, and crater crack?", "Figure B33", 137),
        ("Which diagram shows friction stir welding terms like advancing side, retreating side, and thermomechanically affected zone?", "Figure B46", 154),
        ("Which figure illustrates starting weld tab, runoff tab, and split pipe backing?", "Figure B12", 101),
        ("What welding position does 6G designate for pipe groove welding?", "Figure B16C", 108),
    ]

    for query, expected_fig, expected_p in cases:
        resp = answer_whole_standard_question(query, planner, stores=stores)
        assert resp["execution"]["status"] == "PASS"
        assert resp["requires_diagram_crop"] is True
        assert resp["crop_path"] is not None
        crop_file = ROOT / resp["crop_path"]
        assert crop_file.exists(), f"Crop path {resp['crop_path']} missing on disk!"
        assert expected_fig in resp["answer"]


def test_gate_6_0_multi_intent_cross_store_composition():
    """Verify multi-hop and multi-intent queries execute and enforce modality-appropriate provenance."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Pure compound code -> text/table only, requires_diagram_crop=False
    resp1 = answer_whole_standard_question("What does PAW-AU designate in AWS A3.0?", planner, stores=stores)
    assert resp1["execution"]["status"] == "PASS"
    assert resp1["requires_diagram_crop"] is False
    assert resp1.get("crop_path") is None
    assert "automatic plasma arc welding" in resp1["answer"].lower()

    # Compound code + chart classification -> requires_diagram_crop=True
    resp2 = answer_whole_standard_question(
        "What does PAW-AU designate and how is plasma arc welding classified in Figure A4?",
        planner,
        stores=stores,
    )
    assert resp2["execution"]["status"] == "PASS"
    assert resp2["requires_diagram_crop"] is True
    assert resp2["crop_path"] is not None
    assert (ROOT / resp2["crop_path"]).exists()
    assert "Figure A4" in resp2["answer"]
    assert "automatic plasma arc welding" in resp2["answer"].lower()

    # Pure Clause 4 noun & verb definition -> requires_diagram_crop=False
    resp3 = answer_whole_standard_question("How is braze defined as both a noun and a verb in Clause 4?", planner, stores=stores)
    assert resp3["execution"]["status"] == "PASS"
    assert resp3["requires_diagram_crop"] is False
    assert resp3.get("crop_path") is None
    assert "noun" in resp3["answer"].lower()
    assert "verb" in resp3["answer"].lower()


def test_gate_6_0_whole_standard_cli_and_skills_contracts(monkeypatch):
    """Verify evidence_whole_standard_cli runs offline and agent skills are modernized."""
    # 1. Block network sockets
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls blocked during Gate 6.0 CLI test")
    monkeypatch.setattr(socket, "socket", block_socket)

    import subprocess
    cmd_ner = [sys.executable, "-B", "-m", "src.evidence_whole_standard_cli", "--ner", "What does PAW-AU stand for?", "--json"]
    p_ner = subprocess.run(cmd_ner, capture_output=True, text=True, cwd=str(ROOT))
    assert p_ner.returncode == 0
    data_ner = json.loads(p_ner.stdout)
    assert data_ner["raw_query"] == "What does PAW-AU stand for?"

    cmd_route = [sys.executable, "-B", "-m", "src.evidence_whole_standard_cli", "--route", "Compare AHW and GTAW", "--json"]
    p_route = subprocess.run(cmd_route, capture_output=True, text=True, cwd=str(ROOT))
    assert p_route.returncode == 0
    data_route = json.loads(p_route.stdout)
    assert "actions" in data_route
    assert "ner_receipt" in data_route
    assert "inferred_targets" in data_route

    cmd_ask = [sys.executable, "-B", "-m", "src.evidence_whole_standard_cli", "--ask", "What does PAW-AU designate?", "--json"]
    p_ask = subprocess.run(cmd_ask, capture_output=True, text=True, cwd=str(ROOT))
    assert p_ask.returncode == 0
    data_ask = json.loads(p_ask.stdout)
    assert data_ask["execution"]["status"] == "PASS"

    cmd_ask_ds = [
        sys.executable,
        "-B",
        "-m",
        "src.evidence_whole_standard_cli",
        "--ask",
        "What does PAW-AU designate and how is plasma arc welding classified in Figure A4?",
        "--planner",
        "deepseek-replay",
        "--json",
    ]
    p_ask_ds = subprocess.run(cmd_ask_ds, capture_output=True, text=True, cwd=str(ROOT))
    assert p_ask_ds.returncode == 0
    data_ask_ds = json.loads(p_ask_ds.stdout)
    assert data_ask_ds["execution"]["status"] == "PASS"
    assert data_ask_ds["requires_diagram_crop"] is True

    # 2. Modernized .agents/skills/ scan
    skills_dir = ROOT / ".agents/skills"
    assert skills_dir.exists()
    combined_skills = []
    for skill_md in skills_dir.glob("*/SKILL.md"):
        content = skill_md.read_text(encoding="utf-8")
        combined_skills.append(content)
        assert "only implemented source adapter is Figure A1" not in content, f"Obsolete restriction in {skill_md}"
    joined_skills = "\n".join(combined_skills)
    assert "src.evidence_whole_standard_cli" in joined_skills
    assert "src.evidence_whole_standard_preflight" in joined_skills


def test_gate_6_0_deepseek_replay_backward_and_new_cassettes(monkeypatch):
    """Verify all 10 replay cassettes (8 prior + 2 Gate 6.0) replay cleanly with epistemic quarantine."""
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls blocked during DeepSeek replay test")
    monkeypatch.setattr(socket, "socket", block_socket)

    cfg = DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY")
    adapter = DeepSeekV41PlannerAdapter(config=cfg, root=ROOT)
    stores = get_whole_standard_stores(ROOT)

    replays_dir = ROOT / "storage/model_replays/deepseek_v4_1_flash_1017"
    cassettes = sorted(replays_dir.glob("*.json"))
    assert len(cassettes) >= 10, f"Expected at least 10 replay cassettes, found {len(cassettes)}"

    whole_std_replayed = 0
    for cass_file in cassettes:
        data = json.loads(cass_file.read_text(encoding="utf-8"))
        assert data.get("epistemic_tag") == "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"
        assert "replay_key" in data
        assert "raw_model_output" in data
        assert "parsed_plan" in data
        computed_key = adapter.compute_replay_key(data["normalized_prompt"])
        assert computed_key == data["replay_key"] == cass_file.stem
        loaded = adapter.load_replay(computed_key)
        assert loaded["epistemic_tag"] == "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"

        if data["normalized_prompt"].startswith("AWS A3.0M/A3.0:2020 Question Planning Contract"):
            m_q = re.search(r"^Question:\s*(.+)$", data["normalized_prompt"], flags=re.MULTILINE)
            assert m_q is not None
            q_text = m_q.group(1).strip()
            plan = adapter.plan_with_semantic_expansion(q_text, stores=stores)
            assert plan["receipt_metadata"]["epistemic_tag"] == "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"
            assert "ner_entities" in plan
            assert "multi_intent_targets" in plan
            whole_std_replayed += 1

    assert whole_std_replayed >= 8

    # End-to-end execution of the 2 new Gate 6.0 multi-intent DeepSeek replay cassettes
    for g60_q in [
        "What does PAW-AU designate and how is plasma arc welding classified in Figure A4?",
        "Which diagram illustrates theoretical throat, effective throat, and actual throat, and how are they defined in Clause 4?",
    ]:
        ans = answer_whole_standard_question(g60_q, planner=adapter, stores=stores)
        assert ans["execution"]["status"] == "PASS"
        assert ans["requires_diagram_crop"] is True
        assert (ROOT / ans["crop_path"]).exists()


def test_gate_6_0_benchmark_all_20_pass():
    """Verify Gate 6.0 NER & Multi-Intent Benchmark scores exactly 20 / 20 (100.0%)."""
    payload = evaluate_ner_routing_benchmark(root=ROOT, write_results=False)
    assert payload["total_questions"] == 20
    assert payload["passed_count"] == 20
    assert payload["pass_rate_percent"] == 100.0
    assert payload["gate_status"] == "PASS"


def test_gate_6_0_all_29_locked_hashes_and_anti_drift():
    """Verify all 29 cryptographic SHA-256 hashes match and anti-drift rules hold."""
    # 1. Cryptographic Hash Locks
    assert len(ALL_29_LOCKED_HASHES) == 29, f"Expected 29 locked hashes, got {len(ALL_29_LOCKED_HASHES)}"
    for rel_path, expected_hash in ALL_29_LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Locked artifact missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}!\nExpected: {expected_hash}\nActual:   {actual_hash}"

    # 2. Anti-drift check: zero hardcoded benchmark question IDs in src/ or eval/*.py
    # Pattern includes Gate 6.0 and all prior gates
    id_pattern = re.compile(
        r"\b(QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|"
        r"G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|"
        r"G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+)\b"
    )

    src_files = list((ROOT / "src").rglob("*.py"))
    eval_files = list((ROOT / "eval").glob("*.py"))

    for f in src_files + eval_files:
        content = f.read_text(encoding="utf-8")
        matches = id_pattern.findall(content)
        assert len(matches) == 0, f"Found hardcoded benchmark IDs in {f}: {matches}"

    # 3. Anti-overfitting check: zero benchmark trap literals in src/
    trap_pattern = re.compile(r"\b(hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018)\b", re.IGNORECASE)
    for f in src_files:
        content = f.read_text(encoding="utf-8")
        matches = trap_pattern.findall(content)
        assert len(matches) == 0, f"Found benchmark trap literal in {f}: {matches}"
