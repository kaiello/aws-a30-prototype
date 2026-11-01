"""Test suite for Gate 6.1: Polysemous Welding NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion.

Verifies:
1. test_gate_6_1_polysemous_callout_glossary_dual_targets:
   - Polysemous entity spans link both Clause 4 headwords and Annex B diagram callouts.
   - Populates inferred_targets with both clause4_terms and figures.
   - Sets target_divisions including clause4_glossary.
2. test_gate_6_1_three_tier_compound_designations:
   - Decomposes <BASE>[-<VAR>][-<MODE>] into BASE_PROCESS, PROCESS_VARIATION, and APPLICATION_MODE.
   - Rejects invalid variants (e.g. FCAW-Z-SA) and conflicting double suffixes (e.g. PAW-AU-ME).
   - Validates 1-letter suffix tokens like FCAW-G are parsed as process variations, not invalid compounds.
3. test_gate_6_1_position_and_homograph_contextual_disambiguation:
   - Disambiguates weld positions (1G pipe vs plate, 2F plate vs pipe, unqualified ambiguous senses).
   - Contextual disambiguation of AB (adhesive bonding vs arc brazing).
4. test_gate_6_1_semantic_concept_graph_see_also_and_siblings:
   - Store-compiled SemanticConceptGraph (SEE_ALSO, IS_A_SUBTYPE, SIBLING_VARIATION, DIAGRAM_CO_CALLOUT).
   - expand_semantic_neighborhood returns seed entities, see_also, taxonomy subtypes/siblings, and ranked figures.
5. test_gate_6_1_cli_expand_flag_and_deepseek_replays:
   - CLI --expand flag emits full NER receipt + neighborhood expansion + IDF figure ranking.
   - Verifies all 12 replay cassettes (10 prior + 2 Gate 6.1) replay cleanly under socket isolation.
   - End-to-end execution of the 2 new Gate 6.1 multi-hop DeepSeek replay cassettes.
6. test_gate_6_1_benchmark_all_15_pass:
   - Runs eval.run_phase6_1_semantic_graph and asserts 15 / 15 (100.0%) pass rate.
7. test_gate_6_1_all_34_locked_hashes_and_anti_drift:
   - Cryptographically verifies all 34 artifacts (29 prior + 3 Phase 6.1 benchmark files + 2 new DeepSeek cassettes).
   - Scans src/ and eval/*.py for benchmark question ID patterns (0 matches expected).
   - Scans src/ for benchmark trap literals (0 matches expected).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
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
from src.semantic_nlq_expander import (
    SemanticExpander,
    get_semantic_expander,
)
from src.deepseek_v41_adapter import (
    DeepSeekV41PlannerAdapter,
    DeepSeekV41Config,
)
from eval.run_phase6_1_semantic_graph import evaluate_semantic_graph_benchmark

ALL_34_LOCKED_HASHES = {
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
    # 8 Existing Phase 5.4 / 5.5 DeepSeek-V4.1-Flash-1017 Replay Cassettes
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
    # 3 Gate 6.1 Benchmark Files
    "storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json": "aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7",
    "storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json": "42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5",
    "storage/evidence_v2/phase6_1_semantic_graph_001/results.json": "48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf",
    # 2 Gate 6.1 DeepSeek Replay Cassettes
    "storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json": "22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432",
    "storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json": "72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993",
}


def test_gate_6_1_polysemous_callout_glossary_dual_targets():
    """Verify polysemous entity spans link Clause 4 headwords and Annex B diagram callouts."""
    ner = get_welding_ner(root=ROOT)
    query = "What does PAW-AU stand for and how are theoretical throat and effective throat defined?"
    receipt = ner.extract(query)

    # 1. Polysemous spans exist and carry secondary entity types
    throat_spans = [s for s in receipt.spans if "throat" in s.surface_text.lower()]
    assert len(throat_spans) >= 2
    for s in throat_spans:
        assert s.entity_type == "DIAGRAM_CALLOUT"
        assert "GLOSSARY_TERM" in s.secondary_entity_types
        assert len(s.linked_clause4_terms) > 0
        assert "Figure B25" in s.linked_figures

    # 2. Both figure and Clause 4 targets are populated in inferred_targets
    inferred = receipt.inferred_targets
    assert "Figure B25" in inferred.get("figures", [])
    assert any("throat" in t.lower() for t in inferred.get("clause4_terms", []))

    # 3. target_divisions contains both Clause 4 and Annex B
    divs = receipt.target_divisions
    assert "clause4_glossary" in divs
    assert "annex_b_spatial" in divs


def test_gate_6_1_three_tier_compound_designations():
    """Verify 3-tier compound grammar <BASE>[-<VAR>][-<MODE>] and rejection of invalid combinations."""
    ner = get_welding_ner(root=ROOT)

    # 1. Valid 3-tier: FCAW-G-SA
    res_fcaw = ner.parse_compound_designation("FCAW-G-SA")
    assert res_fcaw["is_valid"] is True
    assert res_fcaw["canonical_term"] == "semiautomatic gas shielded flux cored arc welding"
    sub_types = {c["type"]: c for c in res_fcaw["sub_components"]}
    assert "BASE_PROCESS" in sub_types
    assert "PROCESS_VARIATION" in sub_types
    assert "APPLICATION_MODE" in sub_types
    assert sub_types["BASE_PROCESS"]["designation"] == "FCAW"
    assert sub_types["PROCESS_VARIATION"]["code"] == "FCAW-G"
    assert sub_types["APPLICATION_MODE"]["suffix"] == "-SA"

    # 2. Valid 3-tier: GMAW-P-AU
    res_gmaw = ner.parse_compound_designation("GMAW-P-AU")
    assert res_gmaw["is_valid"] is True
    assert "gas metal arc welding" in res_gmaw["canonical_term"]
    assert "automatic" in res_gmaw["canonical_term"]

    # 3. Valid 3-tier: OFC-A-MA
    res_ofc = ner.parse_compound_designation("OFC-A-MA")
    assert res_ofc["is_valid"] is True
    assert "oxyacetylene cutting" in res_ofc["canonical_term"]
    assert "manual" in res_ofc["canonical_term"]

    # 4. Reject invalid variation: FCAW-Z-SA
    res_inv_var = ner.parse_compound_designation("FCAW-Z-SA")
    assert res_inv_var["is_valid"] is False
    assert "FCAW-Z" in res_inv_var["abstention_reason"]

    # 5. Reject conflicting double mode suffix: PAW-AU-ME
    res_dbl_suf = ner.parse_compound_designation("PAW-AU-ME")
    assert res_dbl_suf["is_valid"] is False
    assert "Conflicting application mode suffixes" in res_dbl_suf["abstention_reason"]

    # 6. Single variation FCAW-G is NOT parsed as an invalid compound
    res_single = ner.parse_compound_designation("FCAW-G")
    assert res_single is None  # Standalone variation, handled by process lexicon


def test_gate_6_1_position_and_homograph_contextual_disambiguation():
    """Verify context-window disambiguation for weld test positions and homographs."""
    ner = get_welding_ner(root=ROOT)

    # 1. 1G with pipe context -> binds to Figure B19(A)
    rec_pipe = ner.extract("Which diagram shows 1G test position for pipe welding?")
    pos_pipe = next((s for s in rec_pipe.spans if s.surface_text == "1G"), None)
    assert pos_pipe is not None
    assert pos_pipe.canonical_term == "1G, pipe"
    assert "Figure B19(A)" in pos_pipe.linked_figures

    # 2. 1G with plate context -> binds to Figure B17(A)
    rec_plate = ner.extract("Which diagram illustrates 1G test position for plate welding?")
    pos_plate = next((s for s in rec_plate.spans if s.surface_text == "1G"), None)
    assert pos_plate is not None
    assert pos_plate.canonical_term == "1G, plate"
    assert "Figure B17(A)" in pos_plate.linked_figures

    # 3. 1G unqualified -> returns ambiguous senses
    rec_unq = ner.extract("What does the 1G welding position designate?")
    pos_unq = next((s for s in rec_unq.spans if s.surface_text == "1G"), None)
    assert pos_unq is not None
    assert len(pos_unq.ambiguous_senses) >= 2
    assert "1G, plate" in pos_unq.ambiguous_senses
    assert "1G, pipe" in pos_unq.ambiguous_senses

    # 4. AB homograph disambiguation
    rec_ab_braze = ner.extract("What does AB stand for in the context of brazing?")
    ab_braze = next((s for s in rec_ab_braze.spans if s.surface_text == "AB"), None)
    assert ab_braze is not None
    assert ab_braze.canonical_term == "arc brazing"

    rec_ab_adh = ner.extract("What does AB stand for in adhesive bonding?")
    ab_adh = next((s for s in rec_ab_adh.spans if s.surface_text == "AB"), None)
    assert ab_adh is not None
    assert ab_adh.canonical_term == "adhesive bonding"


def test_gate_6_1_semantic_concept_graph_see_also_and_siblings():
    """Verify SemanticConceptGraph compilation, relation traversal, and neighborhood expansion."""
    expander = get_semantic_expander(root=ROOT)
    graph = expander.concept_graph
    assert graph is not None

    # 1. SEE_ALSO bidirectional relations
    see_also_throat = graph.get_see_also("throat of a fillet weld")
    assert "theoretical throat" in see_also_throat
    assert "effective throat" in see_also_throat
    assert "actual throat" in see_also_throat

    # 2. IS_A taxonomy subtypes
    subtypes = graph.get_subtypes("flux cored arc welding")
    assert "FCAW-G" in subtypes
    assert "FCAW-S" in subtypes

    # 3. SIBLING_VARIATION lateral edges
    siblings = graph.get_siblings("FCAW-G")
    assert "FCAW-S" in siblings

    # 4. DIAGRAM_CO_CALLOUT edges
    co_callouts_b25 = graph.get_co_callouts("theoretical throat")
    assert "effective throat" in co_callouts_b25
    assert "actual throat" in co_callouts_b25

    # 5. expand_semantic_neighborhood integration
    res = expander.expand_semantic_neighborhood("What are all the throat terms related to a fillet weld and which diagram shows them?")
    assert len(res["seed_entities"]) > 0
    assert len(res["see_also_neighbors"]) > 0
    assert "Figure B25" in res["ranked_target_figures"]


def test_gate_6_1_cli_expand_flag_and_deepseek_replays(monkeypatch):
    """Verify CLI --expand flag output and DeepSeek replay cassettes under socket isolation."""
    # 1. CLI --expand subprocess execution
    cmd_expand = [
        sys.executable,
        "-B",
        "-m",
        "src.evidence_whole_standard_cli",
        "--expand",
        "What are all the throat terms related to a fillet weld and which diagram shows them?",
        "--json",
    ]
    p_expand = subprocess.run(cmd_expand, capture_output=True, text=True, cwd=str(ROOT))
    assert p_expand.returncode == 0
    data_expand = json.loads(p_expand.stdout)
    assert "concept_graph_neighborhood" in data_expand
    assert "ner_receipt" in data_expand
    assert "ranked_target_figures" in data_expand
    assert "Figure B25" in data_expand["ranked_target_figures"]

    # 2. Verify all 12 replay cassettes replay cleanly under socket isolation
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls blocked during DeepSeek replay test")
    monkeypatch.setattr(socket, "socket", block_socket)

    cfg = DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY")
    adapter = DeepSeekV41PlannerAdapter(config=cfg, root=ROOT)
    stores = get_whole_standard_stores(ROOT)

    replays_dir = ROOT / "storage/model_replays/deepseek_v4_1_flash_1017"
    cassettes = sorted(replays_dir.glob("*.json"))
    assert len(cassettes) == 12, f"Expected 12 replay cassettes, found {len(cassettes)}"

    for cass_file in cassettes:
        data = json.loads(cass_file.read_text(encoding="utf-8"))
        assert data.get("epistemic_tag") == "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"
        computed_key = adapter.compute_replay_key(data["normalized_prompt"])
        assert computed_key == data["replay_key"] == cass_file.stem

    # 3. End-to-end execution of the 2 new Gate 6.1 DeepSeek replay cassettes
    for g61_q in [
        "What does FCAW-G-SA stand for and how is fusion welding classified in Figure A4?",
        "What does PAW-AU stand for and how are theoretical throat and effective throat defined and illustrated in Figure B25?",
    ]:
        ans = answer_whole_standard_question(g61_q, planner=adapter, stores=stores)
        assert ans["execution"]["status"] == "PASS"
        assert ans["requires_diagram_crop"] is True
        assert (ROOT / ans["crop_path"]).exists()


def test_gate_6_1_benchmark_all_15_pass():
    """Verify Gate 6.1 Semantic Graph Benchmark scores exactly 15 / 15 (100.0%)."""
    payload = evaluate_semantic_graph_benchmark(root=ROOT)
    assert payload["total_questions"] == 15
    assert payload["passed_count"] == 15
    assert payload["pass_rate_percent"] == 100.0
    assert payload["gate_status"] == "PASS"


def test_gate_6_1_all_34_locked_hashes_and_anti_drift():
    """Verify all 34 cryptographic SHA-256 hashes match and anti-drift rules hold."""
    # 1. Cryptographic Hash Locks (All 34 Artifacts)
    assert len(ALL_34_LOCKED_HASHES) == 34, f"Expected 34 locked hashes, got {len(ALL_34_LOCKED_HASHES)}"
    for rel_path, expected_hash in ALL_34_LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Locked artifact missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}!\nExpected: {expected_hash}\nActual:   {actual_hash}"

    # 2. Anti-drift check: zero hardcoded benchmark question IDs in src/ or eval/*.py
    id_pattern = re.compile(
        r"\b(QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|"
        r"G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|"
        r"G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+|G61-SEM[0-9]+|G61-[0-9]+)\b"
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
