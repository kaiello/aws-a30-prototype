"""Gate 6.2 Test Suite: Store-Driven Multi-Operation Composition, AST Hardening & 20-Query Holdout.

Verifies:
1. Dynamic Taxonomy Subtypes across 5 distinct parent processes from is_a_promotion_store.json.
2. Pure store-compiled See / See also neighborhood expansion across 4 unseen Clause 4 hubs.
3. All 12 weld test positions (1G-6GR, 1F-4F) with exact Clause 4 printed page citations (p. 5 / p. 6) and B16 overview citations.
4. Generalized cross-store historical vs active comparison and 3-tier compound designation validation.
5. AST Zero-Fallback Guard across all 10 composer functions + 12-target store mutation degradation suite.
6. Offline DeepSeek 14-Replay Suite + Gate 6.2 20-Query Generalization Holdout Benchmark (20/20, 100.0%).
7. Cryptographic SHA-256 hash locks for all 39 repository artifacts + expanded anti-drift & forbidden literal scans.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
from typing import Any, Dict
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.deepseek_v41_adapter import (
    DeepSeekV41PlannerAdapter,
    DeepSeekV41Config,
    EPISTEMIC_TAG,
)
from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    _exec_lookup_taxonomy_subtypes,
    _exec_expand_cross_references,
    _exec_weld_position_sense,
    _exec_disambiguate_homograph,
    _exec_compound_lookup_and_validation,
    _exec_compare_historical_and_active,
    _exec_polysemous_diagram_and_glossary,
)
from src.welding_ner import get_welding_ner
from src.semantic_nlq_expander import get_semantic_expander
from eval.run_phase6_2_generalization_holdout import evaluate_generalization_holdout_benchmark
from eval.run_phase6_1_semantic_graph import evaluate_semantic_graph_benchmark
from eval.run_phase6_ner_routing import evaluate_ner_routing_benchmark

# ---------------------------------------------------------------------------
# All 39 Cryptographically Locked Artifact Hashes
# ---------------------------------------------------------------------------
ALL_39_LOCKED_HASHES: Dict[str, str] = {
    # Canonical PDF Source File (Ground Truth Standard)
    "data/AWS_A3.0_2020.pdf": "205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d",
    # 7 Canonical Ingest Stores (Phase 0-3 Immutable Base)
    "storage/evidence_v2/clause4_ingest_001/glossary_store.json": "e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b",
    "storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json": "8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266",
    "storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json": "a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5",
    "storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json": "16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254",
    "storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json": "d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898",
    "storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json": "ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954",
    "storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json": "70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479",
    # 3 Phase 5 Hardening Benchmark Files
    "storage/evidence_v2/phase5_hardening_001/adversarial_questions.json": "0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9",
    "storage/evidence_v2/phase5_hardening_001/rubric.json": "df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981",
    "storage/evidence_v2/phase5_hardening_001/results.json": "92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273",
    # 3 Phase 5.5 NLQ Expansion Benchmark Files
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
    # 2 Gate 5.6 Epistemic Governance Manifests
    "storage/manifests/coverage_manifest.json": "8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e",
    "storage/manifests/latency_benchmark.json": "bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c",
    # 3 Phase 6.0 NER & Routing Benchmark Files
    "storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json": "bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac",
    "storage/evidence_v2/phase6_ner_routing_001/rubric.json": "602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427",
    "storage/evidence_v2/phase6_ner_routing_001/results.json": "4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8",
    # 2 Gate 6.0 DeepSeek Replay Cassettes
    "storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json": "b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057",
    "storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json": "178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42",
    # 3 Phase 6.1 Semantic Graph Benchmark Files
    "storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json": "aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7",
    "storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json": "42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5",
    "storage/evidence_v2/phase6_1_semantic_graph_001/results.json": "48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf",
    # 2 Gate 6.1 DeepSeek Replay Cassettes
    "storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json": "22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432",
    "storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json": "72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993",
    # 3 Phase 6.2 Store-Driven Generalization Holdout Benchmark Files (NET-NEW)
    "storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json": "5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a",
    "storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json": "bb18c854ee6c590dfa83955939b0c9fd810a4cd633ee6d0f64eaf9f0168fe6c3",
    "storage/evidence_v2/phase6_2_generalization_holdout_001/results.json": "dfe96330a00328fdb79d594353be826c6d3ccaa10063b62b0a83e0f560886f60",
    # 2 Gate 6.2 DeepSeek Replay Cassettes (NET-NEW)
    "storage/model_replays/deepseek_v4_1_flash_1017/7e9982c36d0fcfa591123da74ceb0e7c7da002981d4379693a07eb61d3c40d29.json": "f8cd0108b311f27868d5b9fa59b9478ff4128492be28d361d7b793f6011bc21f",
    "storage/model_replays/deepseek_v4_1_flash_1017/3d6a2cbb61def68a41a52cdec81712a85cd65f7ed52c2e6505bc280821dacf9a.json": "cb9ac95d98a5aac82c61f4d2d4b34438b452268f7e0221996fdac9e55edac570",
}


def test_gate_6_2_dynamic_taxonomy_subtypes_across_all_parents():
    """Verify _exec_lookup_taxonomy_subtypes dynamically extracts process variations across 5 distinct parents."""
    stores = get_whole_standard_stores(ROOT)

    parents_to_test = {
        "gas metal arc welding": ["GMAW-P", "GMAW-S"],
        "oxyfuel gas cutting": ["OFC-A", "OFC-H", "OFC-N", "OFC-P"],
        "submerged arc welding": ["SAW-S"],
        "resistance seam welding": ["RSEW-HF", "RSEW-I", "RSEW-MS"],
        "flux cored arc welding": ["FCAW-G", "FCAW-S"],
    }

    for parent, expected_codes in parents_to_test.items():
        res = _exec_lookup_taxonomy_subtypes(parent, stores=stores)
        assert res["status"] == "PASS"
        for code in expected_codes:
            assert code in res["elements_present"], f"Missing variation code {code} for parent {parent}"
            assert code in res["answer"], f"Missing code {code} in answer for parent {parent}"
        assert res["operations_count"] == 1
        assert res["operations"][0]["operation"] == "lookup_process_variations"

    # Nonexistent parent must raise ValueError
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        _exec_lookup_taxonomy_subtypes("nonexistent fantasy welding process", stores=stores)


def test_gate_6_2_dynamic_see_also_across_unseen_hubs():
    """Verify _exec_expand_cross_references extracts pure store-compiled cliques across 4 unseen hubs."""
    stores = get_whole_standard_stores(ROOT)

    hubs_to_test = {
        "backfire": ["flashback", "sustained backfire"],
        "bend test": ["face bend test", "root bend test"],
        "flux": ["brazing flux", "soldering flux", "welding flux"],
        "base metal zone": ["heat-affected zone"],
    }

    for hub, expected_neighbors in hubs_to_test.items():
        res = _exec_expand_cross_references(hub, f"In Clause 4, what is related to {hub}?", stores=stores)
        assert res["status"] == "PASS"
        for n in expected_neighbors:
            assert any(n.lower() in el.lower() for el in res["elements_present"]), f"Missing neighbor {n} for hub {hub}"
        assert res["operations_count"] == 1
        assert res["operations"][0]["operation"] == "expand_cross_references"

    # Nonexistent term must raise ValueError
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        _exec_expand_cross_references("imaginary non-standard terminology", "dummy query", stores=stores)


def test_gate_6_2_all_12_weld_positions_and_accurate_page_citations():
    """Verify all 12 weld test positions have accurate Clause 4 printed page citations (p. 5 or p. 6) and overview figures."""
    stores = get_whole_standard_stores(ROOT)

    p5_positions = ["1G", "2G", "3G", "1F", "2F", "2FR", "3F", "4F"]
    p6_positions = ["4G", "5G", "6G", "6GR"]

    for pos in p5_positions:
        res = _exec_weld_position_sense(pos, None, include_diagram=True, stores=stores)
        assert res["status"] == "PASS"
        assert "Clause 4 (printed p. 5)" in res["answer"], f"Position {pos} should cite printed p. 5"

    for pos in p6_positions:
        res = _exec_weld_position_sense(pos, None, include_diagram=True, stores=stores)
        assert res["status"] == "PASS"
        assert "Clause 4 (printed p. 6)" in res["answer"], f"Position {pos} should cite printed p. 6"

    # Test diagram associations and categorization
    res_5g = _exec_weld_position_sense("5G", "pipe", include_diagram=True, stores=stores)
    assert "Figure B19" in res_5g["answer"]
    assert "Figure B16C" in res_5g["answer"]

    res_3g = _exec_weld_position_sense("3G", "plate", include_diagram=True, stores=stores)
    assert "Figure B17" in res_3g["answer"]
    assert "Figure B16A" in res_3g["answer"]

    # Invalid position code must raise ValueError
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        _exec_weld_position_sense("9Z", None, include_diagram=True, stores=stores)


def test_gate_6_2_generalized_historical_vs_active_and_compound_validation():
    """Verify cross-store comparison and 3-tier compound designation validation."""
    stores = get_whole_standard_stores(ROOT)

    # 1. Historical vs active comparison
    res_comp1 = _exec_compare_historical_and_active("atomic hydrogen welding", "gas tungsten arc welding", stores=stores)
    assert res_comp1["status"] == "PASS"
    assert "Table A5" in res_comp1["elements_present"]
    assert "Table A1" in res_comp1["elements_present"]

    res_comp2 = _exec_compare_historical_and_active("forge welding", "friction stir welding", stores=stores)
    assert res_comp2["status"] == "PASS"
    assert "FOW" in res_comp2["elements_present"]
    assert "FSW" in res_comp2["elements_present"]

    # 2. 3-tier compound designation lookup and validation
    res_val = _exec_compound_lookup_and_validation(
        val_codes=["OFC-P-ME"],
        inv_codes=["GMAW-X-SA", "GTAW-AU-MA"],
        stores=stores,
    )
    assert res_val["status"] == "PASS"
    assert "OFC-P-ME" in res_val["elements_present"]
    assert "GMAW-X-SA" in res_val["elements_present"]
    assert "GTAW-AU-MA" in res_val["elements_present"]
    assert "rejected" in res_val["answer"]


def test_gate_6_2_ast_zero_fallbacks_and_12_target_store_mutations():
    """Verify zero string fallbacks across all 10 composers and verify 12-target store mutation degradation suite."""
    qa_file = ROOT / "src/evidence_phase4_bakeoff.py"
    tree = ast.parse(qa_file.read_text(encoding="utf-8"))

    composer_functions = [
        "_compose_annex_a_chart_answer",
        "_compose_normative_tables_answer",
        "_compose_waveform_phase4_answer",
        "_exec_lookup_taxonomy_subtypes",
        "_exec_expand_cross_references",
        "_exec_weld_position_sense",
        "_exec_disambiguate_homograph",
        "_exec_compound_lookup_and_validation",
        "_exec_compare_historical_and_active",
        "_exec_polysemous_diagram_and_glossary",
        "execute_whole_standard_plan",
        "_exec_decode_process_designations",
    ]

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in composer_functions:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "get":
                    if len(sub.args) >= 2 and isinstance(sub.args[1], ast.Constant):
                        val = sub.args[1].value
                        if isinstance(val, str) and len(val.strip()) > 0:
                            violations.append(f"{node.name}:{sub.lineno}: .get({ast.dump(sub.args[0])}, '{val}')")

    assert not violations, f"Found forbidden string fallbacks in composers:\n" + "\n".join(violations)

    # 12-Target Store Mutation Degradation Suite
    base_stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # Mutation 1: Figure A5 cold welding path/branch summary
    mut_1 = copy.deepcopy(base_stores)
    for n in mut_1["annex_a_graphs"]["Figure A5"]["nodes"]:
        if n.get("label") == "CW" or n.get("code") == "CW":
            n.pop("path_summary", None)
            n.pop("branch_summary", None)
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Figure A5, which specific process branches directly from Mechanical energy?", planner, stores=mut_1)

    # Mutation 2: Figure A6 AB legend code
    mut_2 = copy.deepcopy(base_stores)
    for n in mut_2["annex_a_graphs"]["Figure A6"]["nodes"]:
        if n.get("code") in ["AB", "B-CA"]:
            n.pop("code", None)
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Figure A6, how are arc brazing and carbon arc brazing designated?", planner, stores=mut_2)

    # Mutation 3: Table A4 suffix removal
    mut_3 = copy.deepcopy(base_stores)
    mut_3["tables"]["table_a4"]["suffixes"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("What are the six standard suffix letter modifiers defined in Table A4?", planner, stores=mut_3)

    # Mutation 4: Clause 4 kerf removal
    mut_4 = copy.deepcopy(base_stores)
    for e in mut_4["glossary"].get("entries", []):
        if e.get("term") == "kerf":
            e["definition"] = None
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("What is the official definition for the term 'kerf' in Clause 4?", planner, stores=mut_4)

    # Mutation 5: Figure A3 Method categories
    mut_5 = copy.deepcopy(base_stores)
    mut_5["annex_a_graphs"]["Figure A3"]["nodes"] = [
        n for n in mut_5["annex_a_graphs"]["Figure A3"]["nodes"]
        if not (n.get("kind") == "category" and n.get("column") == "Method")
    ]
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Figure A3, what are the three major methods of materials joining classified?", planner, stores=mut_5)

    # Mutation 6: Table A5 AHW designation
    mut_6 = copy.deepcopy(base_stores)
    for r in mut_6["tables"].get("table_a5", []):
        if "atomic hydrogen" in r.get("process", ""):
            r["designation"] = None
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Table A5, what are the designations for atomic hydrogen welding?", planner, stores=mut_6)

    # Mutation 7: Figure B44 official title
    mut_7 = copy.deepcopy(base_stores)
    if "Figure B44" in mut_7["annex_b_archetype4"]["figure_summaries"]:
        mut_7["annex_b_archetype4"]["figure_summaries"]["Figure B44"]["official_title"] = None
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("Comparing the friction welding cycle diagrams in Figure B44 and Figure B45, what speed profiles differ?", planner, stores=mut_7)

    # Mutation 8: is_a_promotion_store promoted_is_a emptied
    mut_8 = copy.deepcopy(base_stores)
    mut_8["is_a"]["promoted_is_a"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("What process variations branch under gas metal arc welding in AWS A3.0?", planner, stores=mut_8)

    # Mutation 9: glossary entries emptied
    mut_9 = copy.deepcopy(base_stores)
    mut_9["glossary"]["entries"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("In Clause 4, what related terms are cross-referenced from backfire?", planner, stores=mut_9)

    # Mutation 10: position store data blanked
    mut_10 = copy.deepcopy(base_stores)
    for e in mut_10["glossary"].get("entries", []):
        if e.get("term") == "5G":
            e["definition"] = None
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("Which diagram illustrates the 5G test position for pipe groove welding, and how is it defined?", planner, stores=mut_10)

    # Mutation 11: Table A1 active process rows removed
    mut_11 = copy.deepcopy(base_stores)
    mut_11["tables"]["table_a1"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("How does obsolete atomic hydrogen welding compare to active gas tungsten arc welding?", planner, stores=mut_11)

    # Mutation 12: Compound validation with empty Table A1 store
    mut_12 = copy.deepcopy(base_stores)
    mut_12["tables"]["table_a1"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE"):
        answer_whole_standard_question("What does the compound designation GMAW-P-SA stand for according to Table A1 and Table A4?", planner, stores=mut_12)


def test_gate_6_2_deepseek_14_replays_and_20_query_holdout_benchmark(monkeypatch):
    """Verify all 14 DeepSeek replay cassettes replay offline and all benchmark suites achieve 100% PASS."""
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls blocked during DeepSeek replay test")
    monkeypatch.setattr(socket, "socket", block_socket)

    cfg = DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY")
    adapter = DeepSeekV41PlannerAdapter(config=cfg, root=ROOT)
    stores = get_whole_standard_stores(ROOT)

    replays_dir = ROOT / "storage/model_replays/deepseek_v4_1_flash_1017"
    cassettes = sorted(replays_dir.glob("*.json"))
    assert len(cassettes) == 14, f"Expected 14 replay cassettes, found {len(cassettes)}"

    for cass_file in cassettes:
        data = json.loads(cass_file.read_text(encoding="utf-8"))
        assert data.get("epistemic_tag") == EPISTEMIC_TAG
        computed_key = adapter.compute_replay_key(data["normalized_prompt"])
        assert computed_key == data["replay_key"] == cass_file.stem

    # Execute 2 Net-New Gate 6.2 DeepSeek Replay Cassettes
    for g62_q in [
        "What does GMAW-P-SA stand for and how are arc welding cycle intervals illustrated in Figure B54?",
        "How do forge welding (FOW) and friction stir welding (FSW) compare and how is solid-state welding classified in Figure A5?",
    ]:
        ans = answer_whole_standard_question(g62_q, planner=adapter, stores=stores)
        assert ans["execution"]["status"] == "PASS"

    # Verify Gate 6.2 20-Query Holdout Benchmark (100.0%)
    p62 = evaluate_generalization_holdout_benchmark(root=ROOT, write_results=False)
    assert p62["total_questions"] == 20
    assert p62["passed_count"] == 20
    assert p62["pass_rate_percent"] == 100.0
    assert p62["gate_status"] == "PASS"

    # Verify Gate 6.1 Benchmark (15/15)
    p61 = evaluate_semantic_graph_benchmark(root=ROOT, write_results=False)
    assert p61["passed_count"] == 15
    assert p61["gate_status"] == "PASS"

    # Verify Gate 6.0 Benchmark (20/20)
    p60 = evaluate_ner_routing_benchmark(root=ROOT, write_results=False)
    assert p60["passed_count"] == 20
    assert p60["gate_status"] == "PASS"


def test_gate_6_2_all_39_locked_hashes_and_expanded_anti_drift():
    """Verify all 39 cryptographic SHA-256 hashes match and anti-drift rules hold."""
    # 1. Cryptographic Hash Locks (All 39 Artifacts)
    assert len(ALL_39_LOCKED_HASHES) == 39, f"Expected 39 locked hashes, got {len(ALL_39_LOCKED_HASHES)}"
    for rel_path, expected_hash in ALL_39_LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Locked artifact missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}!\nExpected: {expected_hash}\nActual:   {actual_hash}"

    # 2. Anti-drift check: zero hardcoded benchmark question IDs in src/ or eval/*.py
    id_pattern = re.compile(
        r"\b(QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|"
        r"G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|"
        r"G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+|G61-SEM[0-9]+|G61-[0-9]+|G62-GEN[0-9]+|G62-[0-9]+)\b"
    )

    src_files = list((ROOT / "src").rglob("*.py"))
    eval_files = list((ROOT / "eval").glob("*.py"))

    for f in src_files + eval_files:
        content = f.read_text(encoding="utf-8")
        matches = id_pattern.findall(content)
        assert len(matches) == 0, f"Found hardcoded benchmark IDs in {f}: {matches}"

    # 3. Anti-overfitting check: zero benchmark trap literals in src/
    trap_pattern = re.compile(
        r"\b(hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018|"
        r"OFC-A-MA|FCAW-Z-SA|PAW-AU-ME|GTAW-ZZ|GMAW-P-AU|FCAW-G-SA|GMAW-X-SA|GTAW-AU-MA|EBW-AU-SA)\b",
        re.IGNORECASE,
    )
    for f in src_files:
        content = f.read_text(encoding="utf-8")
        matches = trap_pattern.findall(content)
        assert len(matches) == 0, f"Found benchmark trap literal in {f}: {matches}"
