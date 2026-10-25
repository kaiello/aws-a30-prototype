"""Tier 2 Offline AST Plan-Compiler Closure Across Figures A3–A6 (Gate 2E).

Verifies that structured chart-question-actions-1.0 plans compile and execute against
A3, A4, A5, and A6 graphs with strictly 0 live LLM calls and 0 compiler rejections for:
1. 5-column characteristic path lookups (paths / parents / category),
2. Multi-branch process enumeration (returning all characteristic branches for processes like EGW, EBW, DFW, B-CA, FB),
3. Scoped category children (Electrical -> Radiation vs. Chemical -> Radiation),
4. Footnote (* and a), legend table, and source-anomaly queries,
5. Cross-chart pointers (Figure A3 <-> Figures A4/A5/A6), and
6. All 40 questions (A3-DEV001-01..10 through A6-DEV001-01..10) compile and pass through answer_graph.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import pytest

from src.evidence_chart_question_plan import compile_plan
from src.evidence_a1_graph_qa import answer_graph, _GraphView

ROOT = Path(__file__).resolve().parent.parent

# Complete dictionary of 40 validated offline question plans
ANNEX_A_QUESTION_PLANS: Dict[str, Dict[str, Any]] = {
    # Figure A3 (Joining Method Chart, p. 76)
    "A3-DEV001-01": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "descendants", "information_fields": [], "scope": "selected"}],
        "reason": "Request for title and figure number."
    },
    "A3-DEV001-02": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for overarching operation in leftmost column."
    },
    "A3-DEV001-03": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for joining methods branching from Materials Joining."
    },
    "A3-DEV001-04": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n3"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for method annotated with footnote marker a."
    },
    "A3-DEV001-05": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["n11"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for footnote a verbatim text."
    },
    "A3-DEV001-06": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n3"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for process categories classified under Welding."
    },
    "A3-DEV001-07": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n5"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for classification chart corresponding to Fusion Welding."
    },
    "A3-DEV001-08": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n6", "n7"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for classification charts for SSW and Brazing/Soldering."
    },
    "A3-DEV001-09": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["n8"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for path from Materials Joining to Figure A4 pointer."
    },
    "A3-DEV001-10": {
        "actions": [{"id": "a1", "kind": "check_relationship", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["source_limits"], "mode": "source_limits", "information_fields": [], "scope": "selected"}],
        "reason": "Request for epistemic boundaries and unclassified processes."
    },

    # Figure A4 (Fusion Welding Classification Chart, p. 77)
    "A4-DEV001-01": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "descendants", "information_fields": [], "scope": "selected"}],
        "reason": "Request for title and figure number."
    },
    "A4-DEV001-02": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 5 physical characteristics columns."
    },
    "A4-DEV001-03": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["n66"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for footnote * verbatim and anchor."
    },
    "A4-DEV001-04": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 2 Energy Sources in leftmost column."
    },
    "A4-DEV001-05": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n2", "n3"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for Thermal Sources under Electrical and Chemical energy."
    },
    "A4-DEV001-06": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["a4node:proc_gmaw"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 5-column characteristic path for GMAW."
    },
    "A4-DEV001-07": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["a4node:proc_egw_gas", "a4node:proc_egw_flux"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for multi-branch processes in Figure A4."
    },
    "A4-DEV001-08": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["a4node:legend_miaw"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for legend table count and underlined MIAW."
    },
    "A4-DEV001-09": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["a4node:thermal_conduction"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for source anomalies regarding AHW and Conduction."
    },
    "A4-DEV001-10": {
        "actions": [{"id": "a1", "kind": "check_relationship", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["source_limits"], "mode": "source_limits", "information_fields": [], "scope": "selected"}],
        "reason": "Request for epistemic boundaries and unclassified processes."
    },

    # Figure A5 (Solid-State Welding Classification Chart, p. 78)
    "A5-DEV001-01": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "descendants", "information_fields": [], "scope": "selected"}],
        "reason": "Request for title and figure number."
    },
    "A5-DEV001-02": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 5 physical characteristics columns."
    },
    "A5-DEV001-03": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["n68"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for footnote * verbatim and anchor."
    },
    "A5-DEV001-04": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 3 Energy Sources in leftmost column."
    },
    "A5-DEV001-05": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n2", "n3", "n4"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for Thermal Sources under Electrical, Chemical, and Mechanical energy."
    },
    "A5-DEV001-06": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["a5node:proc_cw", "a5node:proc_usw"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for classification paths for CW, FRW/FSW, USW."
    },
    "A5-DEV001-07": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["a5node:proc_dfw_chem_gas", "a5node:proc_dfw_elec_gas", "a5node:proc_dfw_elec_vac"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for multi-branch processes in Figure A5 (DFW, HPW, etc.)."
    },
    "A5-DEV001-08": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["a5node:legend_cw"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for legend table count and designations."
    },
    "A5-DEV001-09": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["a5node:thermal_elec_radiation", "a5node:thermal_chem_radiation"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for scoped Radiation boxes under Electrical vs Chemical."
    },
    "A5-DEV001-10": {
        "actions": [{"id": "a1", "kind": "check_relationship", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["source_limits"], "mode": "source_limits", "information_fields": [], "scope": "selected"}],
        "reason": "Request for epistemic boundaries and unclassified processes."
    },

    # Figure A6 (Brazing and Soldering Classification Chart, p. 79)
    "A6-DEV001-01": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "descendants", "information_fields": [], "scope": "selected"}],
        "reason": "Request for title and figure number."
    },
    "A6-DEV001-02": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 5 physical characteristics columns."
    },
    "A6-DEV001-03": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["n104"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for footnote * verbatim and anchor."
    },
    "A6-DEV001-04": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for 2 Energy Sources in leftmost column."
    },
    "A6-DEV001-05": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["n2", "n3"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for Thermal Sources under Electrical and Chemical energy."
    },
    "A6-DEV001-06": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["a6node:legend_ab", "a6node:legend_b_ca"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for source anomalies regarding AB collision and underlined designations."
    },
    "A6-DEV001-07": {
        "actions": [{"id": "a1", "kind": "explain_path", "query_layer": "evidence", "subjects": ["n1"], "targets": ["a6node:proc_bca_ind_gas", "a6node:proc_dfb_ind_gas"], "subjects_from": [], "targets_from": [], "fields": [], "mode": "from_to", "information_fields": [], "scope": "selected"}],
        "reason": "Request for multi-branch processes in Figure A6 (B-CA, DFB, etc.)."
    },
    "A6-DEV001-08": {
        "actions": [{"id": "a1", "kind": "lookup_term", "query_layer": "evidence", "subjects": ["a6node:legend_ab"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "", "information_fields": [], "scope": "selected"}],
        "reason": "Request for legend table count and designations."
    },
    "A6-DEV001-09": {
        "actions": [{"id": "a1", "kind": "list_members", "query_layer": "evidence", "subjects": ["a6node:thermal_elec_radiation", "a6node:thermal_chem_radiation"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["name"], "mode": "direct", "information_fields": [], "scope": "selected"}],
        "reason": "Request for Radiation and Conduction boxes under Electrical vs Chemical."
    },
    "A6-DEV001-10": {
        "actions": [{"id": "a1", "kind": "check_relationship", "query_layer": "evidence", "subjects": ["n1"], "targets": [], "subjects_from": [], "targets_from": [], "fields": ["source_limits"], "mode": "source_limits", "information_fields": [], "scope": "selected"}],
        "reason": "Request for epistemic boundaries and unclassified processes."
    },
}


def _get_figure_bundle(fig_key: str):
    g_path = ROOT / f"storage/evidence_v2/{fig_key}_ingest_001/final_projection/graph.json"
    q_path = ROOT / f"storage/evidence_v2/{fig_key}_ingest_001/evaluation/questions.json"
    g = json.loads(g_path.read_text(encoding="utf-8"))
    q_data = json.loads(q_path.read_text(encoding="utf-8"))
    return g, q_data


def test_offline_plan_compilation_all_40_questions():
    """Verify all 40 questions across Figures A3–A6 compile with exactly 0 rejections."""
    total_compiled = 0
    for fig_key in ["a3", "a4", "a5", "a6"]:
        graph, q_data = _get_figure_bundle(fig_key)
        element = graph["source_binding"]["locator"]["element_id"]

        for q_item in q_data["questions"]:
            qid = q_item["id"]
            query = q_item["query"]
            plan_spec = ANNEX_A_QUESTION_PLANS[qid]

            payload = {
                "schema_version": "chart-question-actions-1.0",
                "source_element": element,
                "query": query,
                "parts": [{
                    "id": "p1",
                    "quote": query,
                    "status": "planned",
                    "action_ids": [a["id"] for a in plan_spec["actions"]],
                    "reason": plan_spec["reason"],
                }],
                "actions": plan_spec["actions"],
            }

            compiled = compile_plan(graph, query, payload)
            assert not compiled.get("action_errors"), (
                f"Compile rejection for {qid}: {compiled.get('action_errors')}"
            )
            assert compiled["status"] in ("ready", "partial", "clarification_required")
            assert len(compiled["operations"]) >= 1
            total_compiled += 1

    assert total_compiled == 40


def test_offline_plan_execution_through_answer_graph():
    """Verify all 40 questions execute through answer_graph with 0 live model calls."""
    total_executed = 0
    for fig_key in ["a3", "a4", "a5", "a6"]:
        graph, q_data = _get_figure_bundle(fig_key)
        element = graph["source_binding"]["locator"]["element_id"]

        for q_item in q_data["questions"]:
            qid = q_item["id"]
            query = q_item["query"]
            plan_spec = ANNEX_A_QUESTION_PLANS[qid]

            payload = {
                "schema_version": "chart-question-actions-1.0",
                "source_element": element,
                "query": query,
                "parts": [{
                    "id": "p1",
                    "quote": query,
                    "status": "planned",
                    "action_ids": [a["id"] for a in plan_spec["actions"]],
                    "reason": plan_spec["reason"],
                }],
                "actions": plan_spec["actions"],
            }

            compiled = compile_plan(graph, query, payload)
            ans = answer_graph(
                graph,
                query,
                complete_chart=True,
                question_planner=lambda gr, qu, **kw: compiled,
            )

            # Assert 0 live model calls
            assert ans.get("model_invocation_count", 0) == 0
            assert ans.get("planning_model_invocation_count", 0) == 0
            assert ans.get("external_call_count", 0) == 0

            # Assert substantive response
            answer_text = ans.get("answer", "")
            assert len(answer_text) >= 10, f"{qid} returned empty answer"
            total_executed += 1

    assert total_executed == 40


def test_characteristic_path_lookups():
    """Verify 5-column characteristic path lookups on Figures A4, A5, and A6."""
    # A4: GMAW
    g4, _ = _get_figure_bundle("a4")
    q4_06 = "In Figure A4, what is the complete 5-column characteristic path for gas metal arc welding (GMAW)?"
    plan4_06 = ANNEX_A_QUESTION_PLANS["A4-DEV001-06"]
    payload4 = {
        "schema_version": "chart-question-actions-1.0",
        "source_element": "Figure A4",
        "query": q4_06,
        "parts": [{"id": "p1", "quote": q4_06, "status": "planned", "action_ids": ["a1"], "reason": plan4_06["reason"]}],
        "actions": plan4_06["actions"],
    }
    c4 = compile_plan(g4, q4_06, payload4)
    ans4 = answer_graph(g4, q4_06, complete_chart=True, question_planner=lambda g, q, **kw: c4)
    assert "Electrical" in ans4["answer"]
    assert "Arc" in ans4["answer"]
    assert "Gas" in ans4["answer"]
    assert "GMAW" in ans4["answer"] or "gas metal arc welding" in ans4["answer"]

    # A5: CW and USW
    g5, _ = _get_figure_bundle("a5")
    q5_06 = "In Figure A5, what are the classification paths for cold welding (CW) versus friction processes (FRW, FSW) and ultrasonic welding (USW), and which process skips the Thermal Source column?"
    plan5_06 = ANNEX_A_QUESTION_PLANS["A5-DEV001-06"]
    payload5 = {
        "schema_version": "chart-question-actions-1.0",
        "source_element": "Figure A5",
        "query": q5_06,
        "parts": [{"id": "p1", "quote": q5_06, "status": "planned", "action_ids": ["a1"], "reason": plan5_06["reason"]}],
        "actions": plan5_06["actions"],
    }
    c5 = compile_plan(g5, q5_06, payload5)
    ans5 = answer_graph(g5, q5_06, complete_chart=True, question_planner=lambda g, q, **kw: c5)
    assert "Mechanical" in ans5["answer"]
    assert "cold welding" in ans5["answer"]
    assert "ultrasonic welding" in ans5["answer"]


def test_multi_branch_process_plan_execution():
    """Verify multi-branch process questions execute and return characteristic paths."""
    # A4: EGW
    g4, _ = _get_figure_bundle("a4")
    q4_07 = "In Figure A4, which processes appear in multiple characteristic branches, and what are their respective branches?"
    plan4_07 = ANNEX_A_QUESTION_PLANS["A4-DEV001-07"]
    payload4 = {
        "schema_version": "chart-question-actions-1.0",
        "source_element": "Figure A4",
        "query": q4_07,
        "parts": [{"id": "p1", "quote": q4_07, "status": "planned", "action_ids": ["a1"], "reason": plan4_07["reason"]}],
        "actions": plan4_07["actions"],
    }
    c4 = compile_plan(g4, q4_07, payload4)
    ans4 = answer_graph(g4, q4_07, complete_chart=True, question_planner=lambda g, q, **kw: c4)
    assert "Gas" in ans4["answer"]
    assert "Flux" in ans4["answer"]
    assert "electrogas welding" in ans4["answer"]


def test_cross_chart_pointers():
    """Verify cross-chart links between Figure A3 and Figures A4, A5, A6."""
    g3, _ = _get_figure_bundle("a3")
    q3_09 = "What is the complete directed taxonomy path in Figure A3 from Materials Joining to the Fusion Welding Classification Chart (Figure A4)?"
    plan3_09 = ANNEX_A_QUESTION_PLANS["A3-DEV001-09"]
    payload3 = {
        "schema_version": "chart-question-actions-1.0",
        "source_element": "Figure A3",
        "query": q3_09,
        "parts": [{"id": "p1", "quote": q3_09, "status": "planned", "action_ids": ["a1"], "reason": plan3_09["reason"]}],
        "actions": plan3_09["actions"],
    }
    c3 = compile_plan(g3, q3_09, payload3)
    ans3 = answer_graph(g3, q3_09, complete_chart=True, question_planner=lambda g, q, **kw: c3)
    assert "MATERIALS JOINING" in ans3["answer"]
    assert "Welding" in ans3["answer"]
    assert "Fusion Welding" in ans3["answer"]
    assert "See Figure A4" in ans3["answer"]
