"""Tier 1 Exhaustive Property Tests & Tier 2 AST QA Composer Closure Tests for Archetype 3.

Covers Annex B Figures B1–B6 (printed pp. 82–89, PDF indices 94–101).
Mandatory rules:
- 0 live LLM calls.
- 0 hardcoded question IDs or canned answer strings.
- 100% property verification of panels, callouts, welds, continuations, joins, and anomalies.
"""
from pathlib import Path
import json
import pytest

from src.archetype_spatial_callout import (
    ANNEX_B_SPECS,
    compose_spatial_callout_answer,
)


@pytest.fixture(scope="module")
def annex_b_dir():
    root = Path(__file__).resolve().parents[1]
    return root / "storage" / "evidence_v2" / "annex_b_archetype3_001"


@pytest.fixture(scope="module")
def figure_stores(annex_b_dir):
    figure_files = {
        "Figure B1": "b1_joint_types_store.json",
        "Figure B2": "b2_flanged_joints_store.json",
        "Figure B3": "b3_spliced_butt_joints_store.json",
        "Figure B4": "b4_joint_root_store.json",
        "Figure B5": "b5_groove_face_store.json",
        "Figure B6": "b6_multi_page_store.json",
    }
    stores = {}
    for fig_id, fname in figure_files.items():
        fpath = annex_b_dir / fname
        assert fpath.exists(), f"Store file missing: {fpath}"
        stores[fig_id] = json.loads(fpath.read_text(encoding="utf-8"))
    return stores


@pytest.fixture(scope="module")
def unified_manifest(annex_b_dir):
    upath = annex_b_dir / "annex_b_archetype3_unified_store.json"
    assert upath.exists(), f"Unified store missing: {upath}"
    return json.loads(upath.read_text(encoding="utf-8"))


# ===========================================================================
# Tier 1 Exhaustive Property Tests
# ===========================================================================

def test_crop_manifests_and_sha256(figure_stores, annex_b_dir):
    """Verify all 8 page crops are rendered at 300 DPI with valid SHA-256 hashes."""
    crops_dir = annex_b_dir / "crops"
    assert crops_dir.is_dir(), "Crops directory missing"

    total_crops = 0
    for fig_id, store in figure_stores.items():
        manifests = store["crop_manifests"]
        assert len(manifests) == store["metrics"]["total_pages"]
        for cm in manifests:
            total_crops += 1
            assert cm["dpi"] == 300
            assert cm["width_px"] == 2126
            assert cm["height_px"] == 2897
            assert len(cm["sha256"]) == 64
            crop_file = Path(cm["crop_path"])
            assert crop_file.exists(), f"Crop PNG missing on disk: {crop_file}"
            assert crop_file.stat().st_size == cm["size_bytes"]

    assert total_crops == 8, f"Expected 8 crops across B1-B6, found {total_crops}"


def test_figure_b1_subpanels_and_applicable_welds(figure_stores):
    """Verify Figure B1 has exactly 5 basic joint panels and 55 applicable weld pairings."""
    b1 = figure_stores["Figure B1"]
    assert b1["official_title"] == "Joint Types"
    assert len(b1["sub_panels"]) == 5

    panels = [sp["letter"] for sp in b1["sub_panels"]]
    assert panels == ["(A)", "(B)", "(C)", "(D)", "(E)"]

    welds_map = b1["applicable_welds_by_joint"]
    assert len(welds_map) == 5

    # Check weld counts per joint
    assert len(welds_map["BUTT JOINT"]) == 8
    assert len(welds_map["CORNER JOINT"]) == 14
    assert len(welds_map["T-JOINT"]) == 11
    assert len(welds_map["LAP JOINT"]) == 10
    assert len(welds_map["PARALLEL JOINT"]) == 12

    total_welds = sum(len(ws) for ws in welds_map.values())
    assert total_welds == 55
    assert b1["metrics"]["total_applicable_weld_edges"] == 55

    # Normative specific checks
    assert "BRAZE" in welds_map["BUTT JOINT"]
    assert "BRAZE" in welds_map["CORNER JOINT"]
    assert "BRAZE" in welds_map["T-JOINT"]
    assert "BRAZE" in welds_map["LAP JOINT"]
    assert "BRAZE" in welds_map["PARALLEL JOINT"]
    assert "EDGE" in welds_map["PARALLEL JOINT"], "Edge weld must be applicable to parallel joint"
    assert "SQUARE GROOVE" in welds_map["BUTT JOINT"], "Square groove in panel (A) lacks hyphen in source"


def test_figure_b6_multi_page_continuation(figure_stores):
    """Verify Figure B6 spans 3 consecutive continuation pages with 12 sub-panels."""
    b6 = figure_stores["Figure B6"]
    assert len(b6["pages"]) == 3
    assert b6["pages"] == [[99, 87], [100, 88], [101, 89]]
    assert b6["metrics"]["total_continuation_edges"] == 2

    continuation_edges = [e for e in b6["edges"] if e["edge_type"] == "CONTINUED_ON_PAGE"]
    assert len(continuation_edges) == 2
    assert continuation_edges[0]["from_page"] == 87 and continuation_edges[0]["to_page"] == 88
    assert continuation_edges[1]["from_page"] == 88 and continuation_edges[1]["to_page"] == 89

    panels = b6["sub_panels"]
    assert len(panels) == 12
    letters = [p["letter"] for p in panels]
    expected_letters = ["(A)", "(B)", "(C)", "(D)", "(E)", "(F)", "(G)", "(H)", "(I)", "(J)", "(K)", "(L)"]
    assert letters == expected_letters

    # Page bindings
    p87_panels = [p["letter"] for p in panels if p["page_number"] == 87]
    p88_panels = [p["letter"] for p in panels if p["page_number"] == 88]
    p89_panels = [p["letter"] for p in panels if p["page_number"] == 89]
    assert p87_panels == ["(A)", "(B)", "(C)", "(D)"]
    assert p88_panels == ["(E)", "(F)", "(G)", "(H)"]
    assert p89_panels == ["(I)", "(J)", "(K)", "(L)"]

    # Callouts
    callout_texts = set(n["text"] for n in b6["nodes"].values() if n.get("node_type") == "CALLOUT")
    assert "BEVEL ANGLE" in callout_texts
    assert "BEVEL DEPTH" in callout_texts
    assert "GROOVE ANGLE" in callout_texts
    assert "GROOVE DEPTH" in callout_texts
    assert "ROOT OPENING" in callout_texts
    assert "BEVEL RADIUS" in callout_texts
    assert "BEVEL FACE" in callout_texts
    assert "BEVEL DEPTH AND GROOVE DEPTH" in callout_texts
    assert "GROOVE IN SOLID MATERIAL" in callout_texts


def test_figures_b2_through_b5_properties(figure_stores):
    """Verify sub-panels and properties of Figures B2, B3, B4, and B5."""
    # Figure B2: Flanged Joints
    b2 = figure_stores["Figure B2"]
    assert len(b2["sub_panels"]) == 5
    assert b2["sub_panels"][4]["name"] == "FLANGED PARALLEL JOINTS"

    # Figure B3: Spliced Butt Joints
    b3 = figure_stores["Figure B3"]
    assert len(b3["sub_panels"]) == 2
    assert b3["sub_panels"][0]["name"] == "SINGLE-SPLICED BUTT JOINT"
    assert b3["sub_panels"][1]["name"] == "DOUBLE-SPLICED EDGE JOINT WITH FILLER"

    b3_callouts = set(n["text"] for n in b3["nodes"].values() if n.get("node_type") == "CALLOUT")
    assert {"SPLICE MEMBER", "JOINT MEMBER", "FILLER"}.issubset(b3_callouts)

    # Figure B4: Joint Root
    b4 = figure_stores["Figure B4"]
    assert len(b4["sub_panels"]) == 6
    assert any("shading" in n.lower() for n in ANNEX_B_SPECS["Figure B4"].notes)
    b4_callouts = set(n["text"] for n in b4["nodes"].values() if n.get("node_type") == "CALLOUT")
    assert "Joint root denoted by shading." in b4_callouts

    # Figure B5: Groove Face, Root Edge, Root Face
    b5 = figure_stores["Figure B5"]
    assert len(b5["sub_panels"]) == 4
    b5_callouts = set(n["text"] for n in b5["nodes"].values() if n.get("node_type") == "CALLOUT")
    assert {"ROOT FACE AND GROOVE FACE", "GROOVE FACE", "ROOT EDGE"}.issubset(b5_callouts)


def test_dual_layer_epistemic_admission(figure_stores, unified_manifest):
    """Verify strict Dual-Layer Epistemic Admission: ACCEPTED > 0, CANDIDATE == 0."""
    m = unified_manifest["metrics"]
    assert m["candidate_nodes_count"] == 0
    assert m["uncorroborated_promotions_count"] == 0
    assert m["total_accepted_nodes"] == 86
    assert m["total_accepted_edges"] == 210

    for fig_id, store in figure_stores.items():
        assert store["metrics"]["candidate_nodes_count"] == 0
        assert store["metrics"]["accepted_nodes_count"] > 0
        for n in store["nodes"].values():
            assert n["epistemic_status"] == "ACCEPTED"
            assert n["knowledge_eligible"] is True
            assert n["observation_id"].startswith("obs:pdf:")
        for e in store["edges"]:
            assert e["epistemic_status"] == "ACCEPTED"
            assert e["knowledge_eligible"] is True
            assert e["observation_id"].startswith("obs:")


def test_cross_source_normative_joins(figure_stores):
    """Verify normative joins with Clause 4 standard definitions and Annex C decisions."""
    b1 = figure_stores["Figure B1"]
    assert len(b1["cross_clause_joins"]) >= 6
    terms = [cj["term"] for cj in b1["cross_clause_joins"]]
    assert "butt joint" in terms
    assert "parallel joint" in terms

    # Annex C1.5.7 join on B1
    assert len(b1["annex_c_joins"]) == 1
    c157 = b1["annex_c_joins"][0]
    assert c157["clause_id"] == "C1.5.7"
    assert "parallel joint" in c157["text"].lower()

    # B2 joins
    b2 = figure_stores["Figure B2"]
    assert len(b2["cross_clause_joins"]) >= 6
    b2_terms = [cj["term"] for cj in b2["cross_clause_joins"]]
    assert "flanged butt joint" in b2_terms
    assert "parallel joint" in b2_terms


def test_source_anomalies_recorded(figure_stores, unified_manifest):
    """Verify all 7 documented Annex B source anomalies are preserved."""
    assert unified_manifest["metrics"]["total_anomalies"] == 7

    b1_anomalies = {a["anomaly_id"]: a for a in figure_stores["Figure B1"]["source_anomalies"]}
    assert "B1-ANOMALY-01" in b1_anomalies
    assert "B1-ANOMALY-02" in b1_anomalies

    b2_anomalies = {a["anomaly_id"]: a for a in figure_stores["Figure B2"]["source_anomalies"]}
    assert "B2-ANOMALY-01" in b2_anomalies
    assert "B2-ANOMALY-02" in b2_anomalies

    b3_anomalies = {a["anomaly_id"]: a for a in figure_stores["Figure B3"]["source_anomalies"]}
    assert "B3-ANOMALY-01" in b3_anomalies

    b6_anomalies = {a["anomaly_id"]: a for a in figure_stores["Figure B6"]["source_anomalies"]}
    assert "B6-ANOMALY-01" in b6_anomalies
    assert "B6-ANOMALY-02" in b6_anomalies


# ===========================================================================
# Tier 2 Data-Driven QA Composition & AST Closure Tests
# ===========================================================================

@pytest.mark.parametrize(
    "query_input,expected_elements",
    [
        (
            {"query": "What are the 5 basic joint types in Figure B1?", "figure_id": "Figure B1", "intent": "sub_panels"},
            ["Figure B1", "BUTT JOINT", "CORNER JOINT", "T-JOINT", "LAP JOINT", "PARALLEL JOINT"],
        ),
        (
            {"query": "What welds apply to a butt joint in Figure B1?", "figure_id": "Figure B1", "intent": "applicable_welds"},
            ["Figure B1", "BUTT JOINT", "BEVEL-GROOVE", "BRAZE", "SQUARE GROOVE"],
        ),
        (
            {"query": "What welds apply to a parallel joint in Figure B1?", "figure_id": "Figure B1", "intent": "applicable_welds"},
            ["Figure B1", "PARALLEL JOINT", "EDGE", "BRAZE", "V-GROOVE"],
        ),
        (
            {"query": "How many pages does Figure B6 span and what are its continuation pages?", "figure_id": "Figure B6", "intent": "multi_page_continuation"},
            ["Figure B6", "CONTINUED_ON_PAGE", "(A)", "(L)"],
        ),
        (
            {"query": "What source anomaly exists in Figure B3?", "figure_id": "Figure B3", "intent": "source_anomalies"},
            ["Figure B3", "B3-ANOMALY-01"],
        ),
        (
            {"query": "What callout labels are present in Figure B6?", "figure_id": "Figure B6", "intent": "callouts"},
            ["Figure B6", "GROOVE ANGLE", "GROOVE DEPTH"],
        ),
    ],
)
def test_data_driven_qa_composition(figure_stores, query_input, expected_elements):
    """Verify that compose_spatial_callout_answer satisfies full rubric without hardcoded question IDs."""
    ans = compose_spatial_callout_answer(query_input, figure_stores)
    assert ans["status"] == "PASS"
    assert len(ans["answer_text"]) > 20
    assert len(ans["normative_provenance"]) > 0

    for elem in expected_elements:
        assert elem in ans["elements_present"] or elem in ans["answer_text"], (
            f"Expected element '{elem}' missing from answer: {ans['answer_text']}"
        )


def test_repaired_callouts_duplicates_and_cross_references(figure_stores):
    """Verify Gate 3B repairs: full vocabulary in nodes, 0 duplicate edges, non-empty figures cross-refs."""
    for fig_id, store in figure_stores.items():
        spec = ANNEX_B_SPECS[fig_id]
        callout_texts = set(n["text"] for n in store["nodes"].values() if n.get("node_type") == "CALLOUT")

        # 1. Every item in spec.callout_vocabulary exists in store["nodes"]
        for v in spec.callout_vocabulary:
            assert v in callout_texts, f"{fig_id} missing callout vocabulary '{v}' in nodes"

        # 2. edges contains zero identical (source, target, edge_type, observation_id) duplicates
        edge_keys = [(e["source"], e["target"], e["edge_type"], e.get("observation_id", "")) for e in store["edges"]]
        assert len(edge_keys) == len(set(edge_keys)), f"{fig_id} contains duplicate edges"

        # 3. Joined Clause 4 terms have non-empty cross_references["figures"] back-links
        for cj in store["cross_clause_joins"]:
            term = cj["term"]
            # Terms with expected direct figure citations
            if term in ["butt joint", "parallel joint", "bevel angle", "groove depth", "single-spliced butt joint", "double-spliced butt joint", "joint root", "groove face", "root edge", "root face"]:
                figs = cj["cross_references"].get("figures", [])
                assert len(figs) > 0, f"Clause 4 term '{term}' in {fig_id} has empty cross_references['figures']"
                assert any(f.startswith("B1") or f.startswith("B2") or f.startswith("B3") or f.startswith("B4") or f.startswith("B5") or f.startswith("B6") for f in figs), (
                    f"Clause 4 term '{term}' in {fig_id} lacks Annex B figure backlink: {figs}"
                )
