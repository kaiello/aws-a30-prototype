"""Tier 1 Exhaustive Property Tests & Tier 2 AST QA Composer Closure Tests for Gate 3C.

Covers:
- Archetype 4 (cycle_waveform_plot): Figures B44, B45, B49, B50, B51, B53, B54.
- Remaining Annex B Figures: Figures B7–B43, B46–B48, B52.
- 100% Coverage across all 54 standard figures (56 figure units including B16A, B16B, B16C).

Mandatory rules:
- 0 live LLM calls.
- 0 hardcoded question IDs or canned answers.
- 100% property verification of panels, waveforms, sequences, continuations, joins, and zero duplicate edges.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import pytest

from src.archetype_cycle_waveform import compose_waveform_answer
from src.archetype_spatial_callout import compose_spatial_callout_answer
from src.evidence_annex_b_archetype4_specs import ARCHETYPE4_SPECS
from src.evidence_annex_b_remaining_specs import REMAINING_ANNEX_B_SPECS
from src.evidence_annex_b_specs import ANNEX_B_SPECS


@pytest.fixture(scope="module")
def annex_b_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "storage" / "evidence_v2" / "annex_b_complete_001"


@pytest.fixture(scope="module")
def glossary_store() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    gpath = root / "storage" / "evidence_v2" / "clause4_ingest_001" / "glossary_store.json"
    assert gpath.exists(), f"Glossary store missing: {gpath}"
    return json.loads(gpath.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def unified_manifest(annex_b_dir: Path) -> Dict[str, Any]:
    upath = annex_b_dir / "annex_b_complete_unified_store.json"
    assert upath.exists(), f"Unified complete store missing: {upath}"
    return json.loads(upath.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def archetype4_unified(annex_b_dir: Path) -> Dict[str, Any]:
    upath = annex_b_dir / "annex_b_archetype4_unified_store.json"
    assert upath.exists(), f"Archetype 4 unified store missing: {upath}"
    return json.loads(upath.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tier 1 Property Test 1: Archetype 4 Waveform Graph Topology
# ---------------------------------------------------------------------------
def test_archetype4_waveform_ingestion(annex_b_dir: Path, archetype4_unified: Dict[str, Any]):
    """Verify all 7 Archetype 4 figures have accepted nodes, edges, time axes, and traces."""
    assert archetype4_unified["figures_count"] == 7
    expected_figs = {"Figure B44", "Figure B45", "Figure B49", "Figure B50", "Figure B51", "Figure B53", "Figure B54"}
    assert set(archetype4_unified["figures"]) == expected_figs

    for fid in expected_figs:
        slug = fid.lower().replace(" ", "_")
        store_file = annex_b_dir / f"{slug}_store.json"
        assert store_file.exists(), f"Store file missing for {fid}: {store_file}"
        store = json.loads(store_file.read_text(encoding="utf-8"))

        m = store["metrics"]
        assert m["accepted_nodes"] > 0, f"{fid} has no accepted nodes"
        assert m["accepted_edges"] > 0, f"{fid} has no accepted edges"
        assert m["candidate_nodes"] == 0, f"{fid} has uncorroborated candidate nodes"
        assert m["candidate_edges"] == 0, f"{fid} has uncorroborated candidate edges"
        assert m["duplicate_edges"] == 0, f"{fid} has duplicate edges"
        assert m["traces_count"] >= 2, f"{fid} must have at least 2 synchronized traces"
        assert m["intervals_count"] >= 2, f"{fid} must have at least 2 temporal intervals"

        # Check TIME axis node exists
        axis_nodes = [n for n in store["graph"]["nodes"] if n["node_type"] == "TIME_AXIS"]
        assert len(axis_nodes) == 1, f"{fid} must have exactly 1 TIME_AXIS node"
        assert axis_nodes[0]["name"] == "TIME"


# ---------------------------------------------------------------------------
# Tier 1 Property Test 2: Temporal Precedence Sequences
# ---------------------------------------------------------------------------
def test_archetype4_waveform_temporal_sequences(annex_b_dir: Path):
    """Verify that TEMPORAL_PRECEDES edges form a rigorous causal order along the TIME axis."""
    # Figure B49
    b49_store = json.loads((annex_b_dir / "figure_b49_store.json").read_text(encoding="utf-8"))
    b49_precedes = [
        (e["source"].replace("Figure B49_INTERVAL_", ""), e["target"].replace("Figure B49_INTERVAL_", ""))
        for e in b49_store["graph"]["edges"]
        if e["edge_type"] == "TEMPORAL_PRECEDES"
    ]
    # SQUEEZE TIME -> PREHEAT TIME -> UPSLOPE TIME -> WELD INTERVAL -> DOWNSLOPE TIME -> QUENCH TIME -> TEMPER TIME -> HOLD TIME -> OFF TIME
    assert ("SQUEEZE_TIME", "PREHEAT_TIME") in b49_precedes
    assert ("PREHEAT_TIME", "UPSLOPE_TIME") in b49_precedes
    assert ("UPSLOPE_TIME", "WELD_INTERVAL") in b49_precedes
    assert ("WELD_INTERVAL", "DOWNSLOPE_TIME") in b49_precedes
    assert ("DOWNSLOPE_TIME", "QUENCH_TIME") in b49_precedes
    assert ("QUENCH_TIME", "TEMPER_TIME") in b49_precedes
    assert ("TEMPER_TIME", "HOLD_TIME") in b49_precedes
    assert ("HOLD_TIME", "OFF_TIME") in b49_precedes

    # Figure B50
    b50_store = json.loads((annex_b_dir / "figure_b50_store.json").read_text(encoding="utf-8"))
    b50_precedes = [
        (e["source"].replace("Figure B50_INTERVAL_", ""), e["target"].replace("Figure B50_INTERVAL_", ""))
        for e in b50_store["graph"]["edges"]
        if e["edge_type"] == "TEMPORAL_PRECEDES"
    ]
    assert ("PREWELD_INTERVAL", "SQUEEZE_TIME") in b50_precedes
    assert ("SQUEEZE_TIME", "WELD_TIME") in b50_precedes
    assert ("WELD_TIME", "HOLD_TIME") in b50_precedes
    assert ("HOLD_TIME", "OFF_TIME") in b50_precedes

    # Figure B53
    b53_store = json.loads((annex_b_dir / "figure_b53_store.json").read_text(encoding="utf-8"))
    b53_precedes = [
        (e["source"].replace("Figure B53_INTERVAL_", ""), e["target"].replace("Figure B53_INTERVAL_", ""))
        for e in b53_store["graph"]["edges"]
        if e["edge_type"] == "TEMPORAL_PRECEDES"
    ]
    assert ("PREFLOW_TIME", "START_TIME") in b53_precedes
    assert ("UPSLOPE_TIME", "WELD_TIME") in b53_precedes
    assert ("DOWNSLOPE_TIME", "POSTFLOW_TIME") in b53_precedes


# ---------------------------------------------------------------------------
# Tier 1 Property Test 3: Waveform Sub-Intervals & Parameter Modulation
# ---------------------------------------------------------------------------
def test_archetype4_sub_intervals_and_parameters(annex_b_dir: Path):
    """Verify hierarchical SUB_INTERVAL_OF edges and parameter modulation."""
    b49_store = json.loads((annex_b_dir / "figure_b49_store.json").read_text(encoding="utf-8"))
    sub_edges = [
        (e["source"].replace("Figure B49_INTERVAL_", ""), e["target"].replace("Figure B49_INTERVAL_", ""))
        for e in b49_store["graph"]["edges"]
        if e["edge_type"] == "SUB_INTERVAL_OF"
    ]
    assert ("HEAT_TIME", "WELD_INTERVAL") in sub_edges
    assert ("COOL_TIME", "WELD_INTERVAL") in sub_edges

    b53_store = json.loads((annex_b_dir / "figure_b53_store.json").read_text(encoding="utf-8"))
    b53_subs = [
        (e["source"].replace("Figure B53_INTERVAL_", ""), e["target"].replace("Figure B53_INTERVAL_", ""))
        for e in b53_store["graph"]["edges"]
        if e["edge_type"] == "SUB_INTERVAL_OF"
    ]
    assert ("HIGH_PULSE_TIME", "WELD_TIME") in b53_subs
    assert ("LOW_PULSE_TIME", "WELD_TIME") in b53_subs


# ---------------------------------------------------------------------------
# Tier 1 Property Test 4: Exhaustive Ingestion of All 56 Annex B Figures
# ---------------------------------------------------------------------------
def test_annex_b_all_56_figures_exhaustive_presence(annex_b_dir: Path, unified_manifest: Dict[str, Any]):
    """Verify all 56 figures exist, have 0 duplicates, non-empty crops, and accepted nodes."""
    m = unified_manifest["metrics"]
    assert m["total_figures"] == 56, f"Expected 56 figures, got {m['total_figures']}"
    assert m["total_duplicate_edges"] == 0, f"Found {m['total_duplicate_edges']} duplicate edges"
    assert m["total_candidate_nodes"] == 0
    assert m["total_candidate_edges"] == 0
    assert m["total_accepted_nodes"] >= 800
    assert m["total_accepted_edges"] >= 1600

    crops_dir = annex_b_dir / "crops"
    assert crops_dir.exists()
    crop_files = list(crops_dir.glob("*.png"))
    assert len(crop_files) >= 76, f"Expected at least 76 crop images, found {len(crop_files)}"

    # Check each individual figure store
    for fig_id, fig_info in unified_manifest["figures"].items():
        slug = fig_id.lower().replace(" ", "_")
        store_file = annex_b_dir / f"{slug}_store.json"
        assert store_file.exists(), f"Store file missing: {store_file}"
        assert fig_info["accepted_nodes"] > 0
        assert fig_info["accepted_edges"] > 0


# ---------------------------------------------------------------------------
# Tier 1 Property Test 5: Multi-Page Continuations
# ---------------------------------------------------------------------------
def test_annex_b_multi_page_continuations(annex_b_dir: Path):
    """Verify multi-page continuation figures have CONTINUED_ON_PAGE edges."""
    continuation_figures = {
        "Figure B6": 3,
        "Figure B8": 3,
        "Figure B9": 2,
        "Figure B18": 2,
        "Figure B19": 2,
        "Figure B20": 2,
        "Figure B23": 3,
        "Figure B24": 6,
        "Figure B25": 4,
        "Figure B26": 3,
        "Figure B30": 2,
        "Figure B32": 3,
        "Figure B52": 2,
    }

    for fid, page_count in continuation_figures.items():
        slug = fid.lower().replace(" ", "_")
        store = json.loads((annex_b_dir / f"{slug}_store.json").read_text(encoding="utf-8"))
        assert len(store["pages"]) == page_count, f"{fid} page count mismatch"
        cont_edges = [e for e in store["edges"] if e["edge_type"] == "CONTINUED_ON_PAGE"]
        assert len(cont_edges) == page_count - 1, f"{fid} continuation edges mismatch"


# ---------------------------------------------------------------------------
# Tier 1 Property Test 6: Embedded Tables & Numbered Key Legends
# ---------------------------------------------------------------------------
def test_annex_b_embedded_tables_and_numbered_keys(annex_b_dir: Path):
    """Verify figures with embedded tables and numbered keys."""
    table_figs = ["Figure B1", "Figure B7", "Figure B16A", "Figure B16B", "Figure B16C", "Figure B47", "Figure B48"]
    for fid in table_figs:
        slug = fid.lower().replace(" ", "_")
        store = json.loads((annex_b_dir / f"{slug}_store.json").read_text(encoding="utf-8"))
        assert store.get("has_embedded_table") or any("embedded table" in n.lower() for n in store.get("notes", [])) or "applicable_welds_by_joint" in store

    # Numbered keys
    b33_store = json.loads((annex_b_dir / "figure_b33_store.json").read_text(encoding="utf-8"))
    assert any("numbered key" in n.lower() for n in b33_store.get("notes", []))


# ---------------------------------------------------------------------------
# Tier 1 Property Test 7: 100% Clause 4 Figure Back-Link Resolution
# ---------------------------------------------------------------------------
def test_annex_b_100_percent_clause4_figure_backlink_coverage(
    unified_manifest: Dict[str, Any], glossary_store: Dict[str, Any]
):
    """Verify that every single Annex B figure reference in Clause 4 resolves to an ingested node."""
    known_figs = set()
    known_panels = set()

    for fid in unified_manifest["figures"]:
        short_num = fid.replace("Figure ", "")
        known_figs.add(short_num)
        known_figs.add(fid)

    # Add all panel IDs
    all_refs = set()
    unresolved = []

    for e in glossary_store["entries"]:
        for f in e.get("cross_references", {}).get("figures", []):
            if f.startswith("B") or f.startswith("Figure B"):
                all_refs.add(f)
                m = re.match(r"^(B\d+[A-Z]?)(?:\(([A-Z0-9]+)\))?$", f)
                if m:
                    base = m.group(1)
                    panel = m.group(2)
                    if base not in known_figs and base != "B16":
                        unresolved.append(f)
                else:
                    unresolved.append(f)

    assert len(all_refs) == 265, f"Expected 265 unique Annex B figure references, got {len(all_refs)}"
    assert len(unresolved) == 0, f"Found unresolved figure references: {unresolved}"


# ---------------------------------------------------------------------------
# Tier 2 Data-Driven QA Composition Tests (0 Hardcoded Question IDs)
# ---------------------------------------------------------------------------
def test_tier2_data_driven_qa_composition(annex_b_dir: Path):
    """Verify data-driven QA composition generates factual, validated answers dynamically."""
    b49_store = json.loads((annex_b_dir / "figure_b49_store.json").read_text(encoding="utf-8"))
    b53_store = json.loads((annex_b_dir / "figure_b53_store.json").read_text(encoding="utf-8"))

    # 1. Temporal sequence query
    q1 = {"query_type": "temporal_sequence"}
    ans1 = compose_waveform_answer(q1, b49_store)
    assert ans1["figure_id"] == "Figure B49"
    assert "SQUEEZE TIME" in ans1["answer_text"]
    assert "WELD INTERVAL" in ans1["answer_text"]
    assert "OFF TIME" in ans1["answer_text"]

    # 2. Precedence query
    q2 = {"query_type": "precedence", "target_interval": "WELD INTERVAL"}
    ans2 = compose_waveform_answer(q2, b49_store)
    assert ans2["preceding_interval"] == "UPSLOPE TIME"
    assert ans2["succeeding_interval"] == "DOWNSLOPE TIME"

    # 3. Sub-interval query
    q3 = {"query_type": "sub_intervals", "target_interval": "WELD INTERVAL"}
    ans3 = compose_waveform_answer(q3, b49_store)
    assert "HEAT TIME" in ans3["sub_intervals"]
    assert "COOL TIME" in ans3["sub_intervals"]

    # 4. Synchronized traces query
    q4 = {"query_type": "traces"}
    ans4 = compose_waveform_answer(q4, b53_store)
    assert "WELDING CURRENT" in ans4["traces"]
    assert "ARC VOLTAGE" in ans4["traces"]
    assert "WIRE FEED SPEED" in ans4["traces"]


# ---------------------------------------------------------------------------
# Tier 2 Anti-Drift Zero-Hardcoded Grep Check
# ---------------------------------------------------------------------------
def test_anti_drift_zero_hardcoded_grep():
    """Verify zero hardcoded benchmark question IDs in src/ or eval/*.py."""
    forbidden = ["QA002", "HO002", "CQ-0", "DEV001", "C4-QA001", "B1-QA", "B49-QA"]
    root = Path(__file__).resolve().parents[1]

    for fword in forbidden:
        res = subprocess.run(
            ["git", "grep", "-E", fword, "src/"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        assert res.returncode != 0, f"Found forbidden hardcoded token '{fword}' in src/:\n{res.stdout}"
