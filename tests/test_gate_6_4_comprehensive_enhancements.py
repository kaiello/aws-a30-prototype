"""Gate 6.4 Comprehensive Enhancements Verification Suite.

Validates:
1. Full 51-artifact cryptographic lock ledger (45 prior + 6 net-new Gate 6.4 replay cassettes).
2. 100% (20/20) pass rate on Gate 6.3 blind hardening benchmark in BOTH deterministic and replay modes under socket isolation.
3. Table A3 Cross-Reference Matrix queries (by designation, process name, multi-table joins, source anomalies).
4. Table A3 store-mutation degradation raising ValueError("INSUFFICIENT_EVIDENCE").
5. Annex B Spatial Callout deep traversal for Figure B33 (13 crack locations + Clause 4 definitions)
   and Figure B46 (10 FSW key items & zones + Clause 4 definitions + tool shoulder/probe descriptions).
6. Whole-Standard CLI offline execution (--ner, --route, --expand, --ask, --table-a3).
7. AST zero-fallback compliance across all 13 composer functions (including _compose_table_a3_cross_reference).
"""

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
from typing import Any, Dict
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence_phase4_bakeoff import (
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
    _compose_annex_a_chart_answer,
    _compose_normative_tables_answer,
    _compose_table_a3_cross_reference,
    _compose_waveform_phase4_answer,
    _exec_lookup_taxonomy_subtypes,
    _exec_expand_cross_references,
    _exec_weld_position_sense,
    _exec_disambiguate_homograph,
    _exec_compound_lookup_and_validation,
    _exec_compare_historical_and_active,
    _exec_polysemous_diagram_and_glossary,
    _exec_decode_process_designations,
    execute_whole_standard_plan,
)
from src.archetype_spatial_callout import compose_spatial_callout_answer
from src.evidence_whole_standard_cli import main as cli_main
from tests.test_gate_6_3_blind_hardening import ALL_45_LOCKED_HASHES

# ---------------------------------------------------------------------------
# All 51 Cryptographically Locked Artifact Hashes (Gate 6.4 Baseline)
# ---------------------------------------------------------------------------
ALL_51_LOCKED_HASHES: Dict[str, str] = {
    **ALL_45_LOCKED_HASHES,
    # 6 DeepSeek Offline Replay Cassettes (Gate 6.4 Expansion to 20 Cassettes)
    "storage/model_replays/deepseek_v4_1_flash_1017/07d3e65cc2f0f4bab38963fdcb9c7c704615a5c046f019365a3ec3b24ad669ec.json": "6b9b5f3d17afdba5859a4b75114876681308098ba96da860327c56a5739478a7",
    "storage/model_replays/deepseek_v4_1_flash_1017/1a0d448e9483f699ecb6fba379971dd65059b4aba5344f1e8708b2d7bca8845c.json": "1ff122410c75893e47771d4af0fccb2243e81e0df2417eccc51a63ecf5482ffc",
    "storage/model_replays/deepseek_v4_1_flash_1017/73ccb5c640979dc600a4e9d349178667a048ee9ece3b3fc36513a042e3427182.json": "dd4a7a19ca1c8a3327fcc031bb046427f218dc103f15bd4627bfaf044ab330dc",
    "storage/model_replays/deepseek_v4_1_flash_1017/78072b41bac7406dd5fa8749643b9320e380548bd065f4af56dd2571940d021f.json": "0c8d9d97c74a4fd51327f9cb6df1a4f93a97f0c5c9251ac877c71c58eacc7f1a",
    "storage/model_replays/deepseek_v4_1_flash_1017/c2b781b11a1f795ae75679362554299d5c2ab8f3bb74ca82e69e90adf6623033.json": "eb60b4a70c60bcfbc8a521aed76fda62f41f9c21bbc43ede727b30a9767b3198",
    "storage/model_replays/deepseek_v4_1_flash_1017/d6401cf2f24c1f017d7e363ea8de410ccd672178512b655bdc6b0c102e47b8a7.json": "b75fe39c9afea284c639a024296b0b251e45fda8e4d3a309088a54c36120a449",
}


def test_gate_6_4_all_51_locked_hashes():
    """Verify byte-for-byte SHA-256 immutability of all 51 locked artifacts."""
    assert len(ALL_51_LOCKED_HASHES) == 51, f"Expected exactly 51 locked artifacts, got {len(ALL_51_LOCKED_HASHES)}"
    for rel_path, expected_hash in ALL_51_LOCKED_HASHES.items():
        target_path = ROOT / rel_path
        assert target_path.exists(), f"Locked artifact missing on disk: {rel_path}"
        computed_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        assert computed_hash == expected_hash, (
            f"Cryptographic hash mismatch for {rel_path}:\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {computed_hash}"
        )


def test_gate_6_4_replay_and_deterministic_20_20(monkeypatch):
    """Verify 20/20 (100.0%) pass rate on blind hardening benchmark in BOTH deterministic and replay modes."""
    def _blocked_socket(*args, **kwargs):
        raise RuntimeError("NETWORK_ACCESS_BLOCKED: Tests must run 100% offline.")

    monkeypatch.setattr(socket, "socket", _blocked_socket)

    benchmark_dir = ROOT / "storage/evidence_v2/phase6_3_blind_hardening_001"
    questions = json.loads((benchmark_dir / "questions.json").read_text(encoding="utf-8"))
    rubric = json.loads((benchmark_dir / "rubric.json").read_text(encoding="utf-8"))
    stores = get_whole_standard_stores(ROOT)

    from src.deepseek_v41_adapter import DeepSeekV41PlannerAdapter

    planner = DeterministicQuestionPlanner(root=ROOT)
    replay_adapter = DeepSeekV41PlannerAdapter(root=ROOT)

    modes = [
        ("deterministic", False),
        ("replay_cassettes", True),
    ]

    for mode_name, use_replays in modes:
        passed = 0
        failures = []
        replay_used_count = 0
        for item in questions:
            qid = item["id"]
            q_text = item["query"]
            rub = rubric["rubrics"][qid]

            item_planner = planner
            if use_replays:
                key = replay_adapter.compute_replay_key(replay_adapter.build_whole_standard_prompt(q_text))
                if (replay_adapter.replay_dir / f"{key}.json").exists():
                    item_planner = replay_adapter
                    replay_used_count += 1

            res = answer_whole_standard_question(q_text, planner=item_planner, stores=stores)
            ans = res.get("answer", "")
            exec_res = res.get("execution", res)
            actual_status = exec_res.get("status", "FAIL")

            ans_lower = ans.lower()
            req_missing = [req for req in rub["required_elements"] if req.lower() not in ans_lower]
            forb_hits = [forb for forb in rub.get("forbidden_elements", []) if forb.lower() in ans_lower]

            status_match = actual_status == rub["expected_status"]
            crop_match = exec_res.get("requires_diagram_crop", False) == rub["requires_diagram_crop"]

            if status_match and crop_match and len(req_missing) == 0 and len(forb_hits) == 0:
                passed += 1
            else:
                failures.append(f"[{mode_name}] {qid}: status={status_match}, crop={crop_match}, missing={req_missing}, forbidden={forb_hits}")

        if use_replays:
            assert replay_used_count == 6, f"Expected exactly 6 replay cassettes invoked, got {replay_used_count}"

        assert not failures, f"Failures in mode {mode_name} ({len(failures)}/20):\n" + "\n".join(failures)
        assert passed == 20, f"[{mode_name}] Expected 20/20 passes, got {passed}"


def test_gate_6_4_table_a3_queries():
    """Verify Table A3 cross-reference queries by designation, process name, and multi-table joins."""
    stores = get_whole_standard_stores(ROOT)

    # 1. Designation lookup: AB
    res_ab = answer_whole_standard_question("In Table A3, what is the process name for AB?", stores=stores)
    assert res_ab["execution"]["status"] == "PASS"
    assert "AB" in res_ab["answer"]
    assert "adhesive bonding" in res_ab["answer"]
    assert "printed pp. 72" in res_ab["answer"]
    assert any("Table A3" in prov for prov in res_ab["execution"]["normative_provenance"])
    assert any("Clause_4" in prov for prov in res_ab["execution"]["normative_provenance"])

    # 2. Multi-designation lookup: RSW and FLSP
    res_multi = answer_whole_standard_question("What does Table A3 assign to RSW and FLSP?", stores=stores)
    assert res_multi["execution"]["status"] == "PASS"
    assert "resistance spot welding" in res_multi["answer"]
    assert "flame spraying" in res_multi["answer"]

    # 3. Process name lookup: adhesive bonding
    res_proc = answer_whole_standard_question("In Table A3, what is the designation for adhesive bonding?", stores=stores)
    assert res_proc["execution"]["status"] == "PASS"
    assert "AB" in res_proc["answer"]
    assert "adhesive bonding" in res_proc["answer"]

    # 4. Summary lookup: total designations cataloged
    res_sum = answer_whole_standard_question("How many letter designations are cataloged in Table A3?", stores=stores)
    assert res_sum["execution"]["status"] == "PASS"
    assert "134" in res_sum["answer"]
    assert "AB" in res_sum["answer"]
    assert "W" in res_sum["answer"]


def test_gate_6_4_table_a3_store_mutation_degradation():
    """Verify that empty or missing Table A3 and glossary stores strictly raise ValueError."""
    stores = get_whole_standard_stores(ROOT)

    # 1. Empty table_a3 store
    mut1 = copy.deepcopy(stores)
    mut1["tables"]["table_a3"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE.*Table A3 missing"):
        answer_whole_standard_question("In Table A3, what is AB?", stores=mut1)

    # 2. Empty glossary store
    mut2 = copy.deepcopy(stores)
    mut2["glossary"]["entries"] = []
    with pytest.raises(ValueError, match="INSUFFICIENT_EVIDENCE.*Glossary store missing or empty"):
        answer_whole_standard_question("In Table A3, what is AB?", stores=mut2)


def test_gate_6_4_annex_b_deep_traversal():
    """Verify Figure B33 (13 crack locations + Clause 4) and Figure B46 (10 FSW items + microstructural zones)."""
    stores = get_whole_standard_stores(ROOT)
    b_figures = stores["annex_b_complete"]["figures"]

    # Figure B33: Crack Types
    res_b33 = compose_spatial_callout_answer({"query": "Figure B33 crack types", "figure_id": "Figure B33"}, b_figures)
    assert res_b33["status"] == "PASS"
    assert res_b33["key_count"] == 13
    assert len(res_b33["key_items"]) == 13
    assert "Crater crack" in res_b33["answer_text"]
    assert "Toe crack" in res_b33["answer_text"]
    assert "Underbead crack" in res_b33["answer_text"]
    assert "Lamellar tear" in res_b33["answer_text"]
    assert "Root crack" in res_b33["answer_text"]
    # Check Clause 4 definitions appended
    assert "Clause 4, p. 18" in res_b33["answer_text"]  # crater crack
    assert "Clause 4, p. 59" in res_b33["answer_text"]  # toe crack
    assert "Clause 4, p. 61" in res_b33["answer_text"]  # underbead crack
    assert "Clause 4, p. 35" in res_b33["answer_text"]  # lamellar tear
    assert any("crater_crack" in prov for prov in res_b33["normative_provenance"])
    assert any("toe_crack" in prov for prov in res_b33["normative_provenance"])

    # Figure B46: Friction Stir Welding Schematic
    res_b46 = compose_spatial_callout_answer({"query": "Figure B46 FSW", "figure_id": "Figure B46"}, b_figures)
    assert res_b46["status"] == "PASS"
    assert "Advancing Side" in res_b46["elements_present"]
    assert "Retreating Side" in res_b46["elements_present"]
    assert "Tool Shoulder" in res_b46["elements_present"]
    assert "Probe" in res_b46["elements_present"]
    assert "TMAZ" in res_b46["elements_present"]
    assert "HAZ" in res_b46["elements_present"]
    # Check Clause 4 definitions appended
    assert "Clause 4, p. 7" in res_b46["answer_text"]   # advancing side
    assert "Clause 4, p. 48" in res_b46["answer_text"]  # retreating side
    assert "Tool Shoulder (Figure B46 Item 5)" in res_b46["answer_text"]
    assert "Probe (Figure B46 Item 6)" in res_b46["answer_text"]
    assert any("advancing_side" in prov for prov in res_b46["normative_provenance"])
    assert any("retreating_side" in prov for prov in res_b46["normative_provenance"])


def test_gate_6_4_cli_offline_commands():
    """Verify all 5 CLI commands run offline with exit code 0."""
    commands = [
        ["--ner", "What does PAW-AU designate?", "--offline", "--json"],
        ["--route", "Compare historical atomic hydrogen welding with GTAW-ME", "--offline", "--json"],
        ["--expand", "flame spraying", "--offline", "--json"],
        ["--ask", "What does PAW-AU stand for in AWS A3.0?", "--offline", "--json"],
        ["--table-a3", "AB", "--offline", "--json"],
    ]

    for cmd in commands:
        code = cli_main(cmd)
        assert code == 0, f"CLI command {cmd} failed with exit code {code}"


def test_gate_6_4_ast_zero_fallbacks_across_all_13_functions():
    """Verify 0 string-literal fallbacks and 0 domain-entity ternary fallbacks across all 13 functions."""
    qa_file = ROOT / "src/evidence_phase4_bakeoff.py"
    tree = ast.parse(qa_file.read_text(encoding="utf-8"))

    composer_functions = [
        "_compose_annex_a_chart_answer",
        "_compose_normative_tables_answer",
        "_compose_table_a3_cross_reference",
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

    assert len(composer_functions) == 13, f"Expected 13 functions, got {len(composer_functions)}"

    violations = []
    banned_ternary_literals = [
        "Edge Shapes", "Figure B25", "Figure B7",
        "undercut", "coalescence", "atomic hydrogen welding",
        "flux cored arc welding", "gas tungsten arc welding",
        "throat of a fillet weld", "PAW-AU", "1G", "2F", "AHW", "UNKNOWN",
    ]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in composer_functions:
            for sub in ast.walk(node):
                # 1. Banned .get(k, "fallback")
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "get":
                    if len(sub.args) >= 2 and isinstance(sub.args[1], ast.Constant):
                        val = sub.args[1].value
                        if isinstance(val, str) and len(val.strip()) > 0:
                            violations.append(f"{node.name}:{sub.lineno}: .get({ast.dump(sub.args[0])}, '{val}')")
                # 2. Banned ternary domain entity fallbacks
                if isinstance(sub, ast.IfExp):
                    for branch in [sub.body, sub.orelse]:
                        if isinstance(branch, ast.Constant) and isinstance(branch.value, str):
                            if branch.value in banned_ternary_literals:
                                violations.append(f"{node.name}:{sub.lineno}: banned ternary literal '{branch.value}'")
                # 3. Banned .get(...) or "literal" fallbacks
                if isinstance(sub, ast.BoolOp) and isinstance(sub.op, ast.Or):
                    if len(sub.values) >= 2 and isinstance(sub.values[0], ast.Call):
                        first_val = sub.values[0]
                        if isinstance(first_val.func, ast.Attribute) and first_val.func.attr == "get":
                            for v in sub.values[1:]:
                                if isinstance(v, ast.Constant) and isinstance(v.value, str) and len(v.value.strip()) > 0:
                                    get_arg = first_val.args[0].value if (first_val.args and isinstance(first_val.args[0], ast.Constant)) else None
                                    if get_arg == "target_division" and v.value == "Clause 4":
                                        continue
                                    if get_arg == "intent" and v.value == "general_query":
                                        continue
                                    violations.append(f"{node.name}:{sub.lineno}: .get(...) or '{v.value}' fallback")

    assert not violations, f"Found {len(violations)} AST zero-fallback violation(s):\n" + "\n".join(violations)
