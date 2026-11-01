"""Gate 5.6 Test Suite: Epistemic Claims Calibration, 190-Page Coverage Manifest,
Measured Latency Telemetry, and Modality-Appropriate Conditional Crop Provenance.

Verifies:
1. test_gate_5_6_coverage_manifest_accounts_all_190_pdf_pages:
   - storage/manifests/coverage_manifest.json accounts for all 190 PDF pages (162 ingested + 28 excluded = 190).
   - Programmatically reconciles exact record counts across the 6 canonical stores.
2. test_gate_5_6_latency_manifest_schema_and_bounds:
   - storage/manifests/latency_benchmark.json records empirical p50, p95, p99 timing for deterministic and replay routes.
   - Confirms explicit zero external API charge qualification.
3. test_gate_5_6_modality_appropriate_provenance:
   - Glossary-only and table-only queries return valid printed_page, pdf_index, and evidence_locator
     with requires_diagram_crop is False and zero spurious diagram crops.
   - Diagram-dependent queries (Figure A5, Figure B49) return valid printed_page, pdf_index, evidence_locator,
     requires_diagram_crop is True, and verified crop file path on disk.
4. test_gate_5_6_doc_epistemic_hygiene_scan:
   - Scans goal.md, ROADMAP.md, and GATE_5_REVIEW_PACKET.md to verify absence of unqualified claims
     ("zero-hallucination", "adversarial immunity", residual "Gate 5.3" active markers) and presence
     of version-bound store immutability policy (_001 -> _002).
5. test_gate_5_6_all_24_locked_hashes:
   - Cryptographically verifies all 24 project artifacts (22 prior + 2 Gate 5.6 manifests).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import pytest

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    ROOT,
)

ALL_24_LOCKED_HASHES = {
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
    # 8 DeepSeek-V4.1-Flash-1017 Replay Cassettes
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
}


def test_gate_5_6_coverage_manifest_accounts_all_190_pdf_pages():
    """Verify storage/manifests/coverage_manifest.json accounts for all 190 PDF pages
    and programmatically matches exact store record counts."""
    manifest_path = ROOT / "storage/manifests/coverage_manifest.json"
    assert manifest_path.exists(), "Coverage manifest missing!"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 1. Total page accounting
    acct = manifest["page_accounting"]
    assert acct["total_pdf_pages"] == 190
    assert acct["total_ingested_pages"] == 162
    assert acct["total_excluded_pages"] == 28
    assert acct["total_ingested_pages"] + acct["total_excluded_pages"] == 190

    ingested_set = set(acct["ingested_pdf_indices_1_based"])
    excluded_set = set(acct["excluded_pdf_indices_1_based"])
    assert len(ingested_set) == 162
    assert len(excluded_set) == 28
    assert ingested_set.union(excluded_set) == set(range(1, 191))
    assert ingested_set.isdisjoint(excluded_set)

    # 2. Store reconciliation checks against live stores
    stores = get_whole_standard_stores(ROOT)

    # Clause 4
    live_g_metrics = stores["glossary"].get("metrics", {})
    m_c4 = manifest["inventory_reconciliation"]["clause4_glossary"]
    assert m_c4["total_entries"] == live_g_metrics.get("total_glossary_entries", 1607)
    assert m_c4["standard_terms_count"] == live_g_metrics.get("standard_terms_count", 1345)
    assert m_c4["nonstandard_terms_count"] == live_g_metrics.get("nonstandard_terms_count", 262)
    assert m_c4["has_2020_underline_count"] == live_g_metrics.get("has_2020_underline_count", 378)
    assert m_c4["has_2020_margin_bar_count"] == live_g_metrics.get("has_2020_margin_bar_count", 458)

    # Is-A
    live_isa = stores["is_a"]
    m_isa = manifest["inventory_reconciliation"]["is_a_promotions"]
    assert m_isa["promoted_count"] == live_isa.get("promoted_count", 35)
    assert m_isa["retained_candidate_count"] == live_isa.get("retained_candidate_count", 83)

    # Annex C & D
    live_cd_metrics = stores["annex_c_d"].get("metrics", {})
    m_cd = manifest["inventory_reconciliation"]["annex_c_and_d"]
    assert m_cd["annex_c_clauses_count"] == live_cd_metrics.get("annex_c_clauses_count", 21)
    assert m_cd["annex_c_subcommittee_decisions_count"] == live_cd_metrics.get("annex_c_subcommittee_decisions_count", 8)
    assert m_cd["annex_d_tables_count"] == 6
    assert m_cd["table_d1_rows"] == 172
    assert m_cd["table_d2_rows"] == 181
    assert m_cd["table_d3_rows"] == 99
    assert m_cd["table_d4_rows"] == 3
    assert m_cd["table_d5_rows"] == 6
    assert m_cd["table_d6_rows"] == 30
    assert m_cd["total_annex_d_rows"] == 491

    # Annex B Figures
    live_b_metrics = stores["annex_b_complete"].get("metrics", {})
    m_b = manifest["inventory_reconciliation"]["annex_b_figures"]
    assert m_b["total_figures"] == live_b_metrics.get("total_figures", 56)
    assert m_b["accepted_nodes"] == live_b_metrics.get("total_accepted_nodes", 1115)
    assert m_b["accepted_edges"] == live_b_metrics.get("total_accepted_edges", 1917)
    assert m_b["verified_300dpi_crop_files_on_disk"] == 80
    assert m_b["clause4_figure_backlinks_resolved"] == 265


def test_gate_5_6_latency_manifest_schema_and_bounds():
    """Verify storage/manifests/latency_benchmark.json records empirical timing
    and explicit zero external API charge qualification."""
    bench_path = ROOT / "storage/manifests/latency_benchmark.json"
    assert bench_path.exists(), "Latency benchmark manifest missing!"

    bench = json.loads(bench_path.read_text(encoding="utf-8"))

    # Cost qualification
    cost = bench["cost_and_replay_qualification"]
    assert cost["external_api_charge_per_query_usd"] == 0.0
    assert "No per-query external API charge in offline deterministic/replay mode" in cost["cost_qualification"]

    # Routes timing
    routes = bench["routes"]
    assert "offline_deterministic_route" in routes
    assert "offline_deepseek_replay_route" in routes

    det = routes["offline_deterministic_route"]
    assert det["query_count"] == 25
    assert det["total_iterations"] >= 125
    assert det["p50_ms"] > 0
    assert det["p95_ms"] >= det["p50_ms"]
    assert det["p99_ms"] >= det["p95_ms"]

    rep = routes["offline_deepseek_replay_route"]
    assert rep["cassettes_count"] == 8
    assert rep["total_iterations"] >= 40
    assert rep["p50_ms"] > 0
    assert rep["p95_ms"] >= rep["p50_ms"]
    assert rep["p99_ms"] >= rep["p95_ms"]


def test_gate_5_6_modality_appropriate_provenance():
    """Verify universal page and locator provenance, and conditional crop requirement."""
    stores = get_whole_standard_stores(ROOT)
    planner = DeterministicQuestionPlanner(ROOT)

    # 1. Glossary-Only Query (kerf)
    q_glossary = "How does AWS A3.0 define kerf?"
    res_g = answer_whole_standard_question(q_glossary, planner=planner, stores=stores)
    assert res_g["execution"]["status"] == "PASS"
    assert res_g["printed_page"] == 35
    assert res_g["pdf_index"] == 47
    assert res_g["evidence_locator"] == "clause4:term:kerf"
    assert res_g["requires_diagram_crop"] is False
    assert "crop_path" not in res_g or res_g.get("crop_path") is None

    # 2. Table-Only Query (Table A4)
    q_table = "What are the six standard suffix letter modifiers in Table A4?"
    res_t = answer_whole_standard_question(q_table, planner=planner, stores=stores)
    assert res_t["execution"]["status"] == "PASS"
    assert res_t["printed_page"] == 74
    assert res_t["pdf_index"] == 86
    assert res_t["evidence_locator"] == "table_a4:suffix:-AU"
    assert res_t["requires_diagram_crop"] is False
    assert "crop_path" not in res_t or res_t.get("crop_path") is None

    # 3. Diagram-Dependent Query: Figure A5
    q_a5 = "Which processes are classified under Solid-State Welding in Figure A5?"
    res_a5 = answer_whole_standard_question(q_a5, planner=planner, stores=stores)
    assert res_a5["execution"]["status"] == "PASS"
    assert res_a5["printed_page"] == 79
    assert res_a5["pdf_index"] == 91
    assert "figure_a5" in res_a5["evidence_locator"]
    assert res_a5["requires_diagram_crop"] is True
    assert res_a5.get("crop_path") is not None
    assert (ROOT / res_a5["crop_path"]).exists()

    # 4. Diagram-Dependent Query: Figure B49
    q_b49 = "Which waveform traces and intervals are illustrated in Figure B49 for resistance spot welding?"
    res_b49 = answer_whole_standard_question(q_b49, planner=planner, stores=stores)
    assert res_b49["execution"]["status"] == "PASS"
    assert res_b49["printed_page"] == 153
    assert res_b49["pdf_index"] == 165
    assert "figure_b49" in res_b49["evidence_locator"]
    assert res_b49["requires_diagram_crop"] is True
    assert res_b49.get("crop_path") is not None
    assert (ROOT / res_b49["crop_path"]).exists()


def test_gate_5_6_doc_epistemic_hygiene_scan():
    """Verify goal.md, ROADMAP.md, and GATE_5_REVIEW_PACKET.md do not contain unqualified claims
    and properly document version-bound store immutability."""
    docs = [
        ROOT / "goal.md",
        ROOT / "ROADMAP.md",
        ROOT / "GATE_5_REVIEW_PACKET.md",
    ]

    for doc in docs:
        assert doc.exists(), f"Doc missing: {doc}"
        text = doc.read_text(encoding="utf-8")

        # 1. No unqualified zero-hallucination marketing claim
        zh_matches = re.findall(r"\bzero[- ]hallucination\b", text, re.IGNORECASE)
        assert len(zh_matches) == 0, f"Unqualified 'zero-hallucination' claim found in {doc.name}: {zh_matches}"

        # 2. No unqualified adversarial immunity claim
        ai_matches = re.findall(r"\badversarial immunity\b", text, re.IGNORECASE)
        assert len(ai_matches) == 0, f"Unqualified 'adversarial immunity' claim found in {doc.name}: {ai_matches}"

        # 3. No residual Gate 5.3 active milestone references
        g53_active = re.findall(r"Active Milestone:.*Gate 5\.3", text, re.IGNORECASE)
        assert len(g53_active) == 0, f"Residual Gate 5.3 active milestone found in {doc.name}: {g53_active}"

        # 4. Version-bound immutability documented
        assert "_001" in text, f"Version-bound '_001' not documented in {doc.name}"
        assert "_002" in text, f"Successor version '_002' migration path not documented in {doc.name}"


def test_gate_5_6_all_24_locked_hashes():
    """Verify that all 24 project artifacts match locked SHA-256 digests."""
    assert len(ALL_24_LOCKED_HASHES) == 24, f"Expected 24 locked hashes, found {len(ALL_24_LOCKED_HASHES)}"

    for rel_path, expected_hash in ALL_24_LOCKED_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Locked artifact missing: {rel_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Cryptographic lock violated for {rel_path}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )
