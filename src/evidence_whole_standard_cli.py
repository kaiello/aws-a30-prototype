"""evidence_whole_standard_cli.py - Canonical Whole-Standard CLI for AWS A3.0M/A3.0:2020.

Deterministic, offline command-line interface supporting:
1. --ner "<query>": Run deterministic Welding Domain Named Entity Recognition.
2. --route "<query>": Run callout/backlink-indexed multi-intent routing and action planning.
3. --expand "<query>": Run store-compiled semantic graph neighborhood expansion.
4. --ask "<query>": Execute full multi-store retrieval, Layer 6 composition, and Gate 5.6 provenance.
5. --planner deterministic|deepseek-replay: Select planner backend (default: deterministic).
6. --json: Output structured JSON receipt.

Zero network calls, 100% offline from locked _001 canonical stores.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent


def run_ner_cli(query: str, as_json: bool = False) -> int:
    """Run Deterministic Welding NER over query."""
    from src.welding_ner import get_welding_ner

    ner = get_welding_ner(root=ROOT)
    receipt = ner.recognize_entities(query)
    data = receipt.to_dict()

    if as_json:
        print(json.dumps(data, indent=2))
    else:
        print(f"=== AWS A3.0M/A3.0:2020 WELDING DOMAIN NER RECEIPT ===")
        print(f"Query: {query}")
        print(f"Normalized: {receipt.normalized_query}")
        print(f"Spans Identified ({len(receipt.spans)}):")
        for s in receipt.spans:
            valid_flag = "VALID" if s.is_valid else f"INVALID ({s.abstention_reason})"
            print(f"  [{s.start_char}:{s.end_char}] '{s.surface_text}' -> {s.entity_type}")
            print(f"      Canonical: {s.canonical_term} ({s.canonical_id})")
            print(f"      Authority: {s.source_authority} [{s.target_division}] ({valid_flag})")
            if s.sub_components:
                print(f"      Sub-Components: {list(s.sub_components)}")
            if s.ambiguity_candidates:
                print(f"      Ambiguity Candidates: {list(s.ambiguity_candidates)}")
        print(f"Entity Counts: {receipt.entity_counts_by_type}")
        print(f"Inferred Targets: {receipt.inferred_targets}")
    return 0


def run_route_cli(query: str, as_json: bool = False, planner_name: str = "deterministic") -> int:
    """Run Callout/Backlink-Indexed Multi-Intent Routing over query."""
    from src.evidence_phase4_bakeoff import DeterministicQuestionPlanner, get_whole_standard_stores
    from src.semantic_nlq_expander import get_semantic_expander

    stores = get_whole_standard_stores(ROOT)
    expander = get_semantic_expander(stores=stores, root=ROOT)
    trace = expander.expand_query(query)

    if planner_name == "deepseek-replay":
        from src.deepseek_v41_adapter import DeepSeekV41PlannerAdapter
        planner = DeepSeekV41PlannerAdapter(root=ROOT)
        plan = planner.plan_whole_standard_question(query, stores=stores)
    else:
        planner = DeterministicQuestionPlanner(root=ROOT)
        plan = planner.plan_whole_standard_question(query)

    data = {
        "query": query,
        "planner": planner_name,
        "target_division": plan.get("target_division"),
        "intent": plan.get("intent"),
        "target_entities": plan.get("target_entities"),
        "inferred_targets": trace.inferred_targets,
        "actions": plan.get("actions"),
        "ner_receipt": trace.ner_receipt,
        "semantic_expansion_trace": plan.get("semantic_expansion_trace"),
        "receipt_metadata": plan.get("receipt_metadata"),
    }

    if as_json:
        print(json.dumps(data, indent=2))
    else:
        print(f"=== AWS A3.0M/A3.0:2020 MULTI-INTENT ROUTER PLAN ===")
        print(f"Query: {query}")
        print(f"Planner: {planner_name}")
        print(f"Target Division: {plan.get('target_division')}")
        print(f"Intent: {plan.get('intent')}")
        print(f"Target Entities: {plan.get('target_entities')}")
        print(f"Planned Actions ({len(plan.get('actions', []))}):")
        for act in plan.get("actions", []):
            print(f"  - Action: {act.get('action_type')} on {act.get('target')} (params: {act.get('parameters')})")
        print(f"Inferred Diagrams: {trace.inferred_targets.get('figures')}")
        print(f"Inferred Tables: {trace.inferred_targets.get('tables')}")
        print(f"Inferred Clause 4: {trace.inferred_targets.get('clause4_terms')}")
    return 0


def run_expand_cli(query: str, as_json: bool = False) -> int:
    """Run Store-Compiled Semantic Graph Neighborhood Expansion over query."""
    from src.semantic_nlq_expander import get_semantic_expander
    from src.welding_ner import get_welding_ner
    from src.evidence_phase4_bakeoff import get_whole_standard_stores

    stores = get_whole_standard_stores(ROOT)
    ner = get_welding_ner(stores=stores, root=ROOT)
    ner_receipt = ner.recognize_entities(query).to_dict()
    expander = get_semantic_expander(stores=stores, root=ROOT)
    neighborhood = expander.expand_semantic_neighborhood(query)

    payload = {
        "query": query,
        "ner_receipt": ner_receipt,
        "concept_graph_neighborhood": neighborhood,
        "ranked_target_figures": neighborhood.get("ranked_target_figures", []),
    }

    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"=== AWS A3.0M/A3.0:2020 SEMANTIC GRAPH EXPANSION RECEIPT ===")
        print(f"Query: {query}")
        print(f"Seed Entities: {neighborhood['seed_entities']}")
        if neighborhood['synonym_pivots']:
            print(f"Synonym Pivots ({len(neighborhood['synonym_pivots'])}):")
            for sp in neighborhood['synonym_pivots']:
                print(f"  - '{sp.get('span')}' -> {sp.get('canonical_term')} [{sp.get('resolution_type')}] ({sp.get('source_authority')})")
        if neighborhood['see_also_neighbors']:
            print(f"See Also Neighbors ({len(neighborhood['see_also_neighbors'])}): {neighborhood['see_also_neighbors']}")
        if neighborhood['taxonomy_subtypes']:
            print(f"Taxonomy Subtypes ({len(neighborhood['taxonomy_subtypes'])}): {neighborhood['taxonomy_subtypes']}")
        if neighborhood['taxonomy_siblings']:
            print(f"Taxonomy Siblings ({len(neighborhood['taxonomy_siblings'])}): {neighborhood['taxonomy_siblings']}")
        if neighborhood['co_diagram_callouts']:
            print(f"Co-Diagram Callouts ({len(neighborhood['co_diagram_callouts'])}): {neighborhood['co_diagram_callouts'][:10]}")
        print(f"Ranked Target Figures: {neighborhood['ranked_target_figures'][:5]}")
    return 0


def run_ask_cli(query: str, as_json: bool = False, planner_name: str = "deterministic") -> int:
    """Execute full Whole-Standard Question Answering."""
    from src.evidence_phase4_bakeoff import answer_whole_standard_question, get_whole_standard_stores

    stores = get_whole_standard_stores(ROOT)
    if planner_name == "deepseek-replay":
        from src.deepseek_v41_adapter import DeepSeekV41PlannerAdapter
        planner = DeepSeekV41PlannerAdapter(root=ROOT)
    else:
        from src.evidence_phase4_bakeoff import DeterministicQuestionPlanner
        planner = DeterministicQuestionPlanner(root=ROOT)

    res = answer_whole_standard_question(query, planner=planner, stores=stores)

    if as_json:
        # Sanitize any non-serializable objects
        print(json.dumps(res, indent=2, default=str))
    else:
        print(f"=== AWS A3.0M/A3.0:2020 QUESTION ANSWERING RECEIPT ===")
        print(f"Question: {query}")
        print(f"Status: {res['execution'].get('status', 'UNKNOWN')}")
        print(f"\nAnswer:\n{res.get('answer', '')}\n")
        print(f"--- Modality-Appropriate Provenance ---")
        print(f"Printed Page: {res.get('printed_page')}")
        print(f"PDF Index: {res.get('pdf_index')}")
        print(f"Evidence Locator: {res.get('evidence_locator')}")
        print(f"Requires Diagram Crop: {res.get('requires_diagram_crop')}")
        if res.get("crop_path"):
            print(f"Crop Asset: {res.get('crop_path')}")
        print(f"Operations Count: {res['execution'].get('operations_count', 0)}")
    return 0


def run_table_a3_cli(term: str, as_json: bool = False) -> int:
    """Query Table A3 cross-reference matrix by designation or process."""
    from src.evidence_phase4_bakeoff import _compose_table_a3_cross_reference, get_whole_standard_stores

    stores = get_whole_standard_stores(ROOT)
    tables_graph = stores.get("tables", {})
    plan = {
        "target_division": "Normative Tables",
        "intent": "table_a3_cross_reference",
        "target_entities": [term],
    }
    res = _compose_table_a3_cross_reference(plan, term, tables_graph, stores=stores)

    if as_json:
        print(json.dumps(res, indent=2))
    else:
        print("=== AWS A3.0M/A3.0:2020 TABLE A3 CROSS-REFERENCE RECEIPT ===")
        print(f"Query: {term}")
        print(f"Status: {res.get('status')}")
        print(f"\nAnswer:\n{res.get('answer', '')}\n")
        print(f"Operations Count: {res.get('operations_count', 0)}")
        print(f"Elements Present: {res.get('elements_present', [])}")
        print(f"Normative Provenance: {res.get('normative_provenance', [])}")
    return 0


def run_qualify_reader_cli(query: str, as_json: bool = False) -> int:
    """Run 3-Arm Gold-Evidence vs Retrieved Reader Qualification on query."""
    from src.evidence_phase4_bakeoff import (
        answer_whole_standard_question,
        get_whole_standard_stores,
        DeterministicQuestionPlanner,
    )
    from src.reader_qualification import (
        build_gold_evidence_packet,
        compose_from_gold_arm,
        prepare_reader_evidence_arm,
    )

    stores = get_whole_standard_stores(ROOT)
    gold_packet = build_gold_evidence_packet(query, stores=stores, root=ROOT)
    arms_out = {}
    for arm_code, track_key in (("A", "gold_arm_a"), ("B", "gold_arm_b"), ("C", "gold_arm_c")):
        arm_pkt = prepare_reader_evidence_arm(gold_packet, arm=arm_code)
        arms_out[track_key] = compose_from_gold_arm(query, arm_pkt, stores=stores)

    planner = DeterministicQuestionPlanner(root=ROOT)
    retrieved_res = answer_whole_standard_question(query, planner=planner, stores=stores)

    payload = {
        "query": query,
        "gold_packet_metadata": {
            "status": gold_packet.get("status"),
            "target_division": gold_packet.get("target_division"),
            "intent": gold_packet.get("intent"),
            "printed_page": gold_packet.get("printed_page"),
            "pdf_index": gold_packet.get("pdf_index"),
            "evidence_locator": gold_packet.get("evidence_locator"),
            "requires_diagram_crop": gold_packet.get("requires_diagram_crop"),
            "crop_path": gold_packet.get("crop_path"),
        },
        "tracks": {
            "gold_arm_a": arms_out["gold_arm_a"],
            "gold_arm_b": arms_out["gold_arm_b"],
            "gold_arm_c": arms_out["gold_arm_c"],
            "retrieved_whole_standard": retrieved_res,
        },
    }

    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print("=== AWS A3.0M/A3.0:2020 READER QUALIFICATION RECEIPT (GATE 6.6) ===")
        print(f"Query: {query}")
        print(f"Locator: {gold_packet.get('evidence_locator')} (p. {gold_packet.get('printed_page')} / PDF {gold_packet.get('pdf_index')})")
        for t_name, t_res in payload["tracks"].items():
            print(f"\n[{t_name}] (requires_crop={t_res.get('requires_diagram_crop')}, crop={t_res.get('crop_path')})")
            print(f"  {t_res.get('answer', '')[:200]}")
    return 0


def run_replay_audit_cli(as_json: bool = False) -> int:
    """Run Offline Replay Coverage Audit across all benchmarks."""
    from src.deepseek_v41_adapter import audit_replay_coverage

    manifest = audit_replay_coverage(root=ROOT, write_manifest=False)
    if as_json:
        print(json.dumps(manifest, indent=2))
    else:
        print("=== AWS A3.0M/A3.0:2020 REPLAY COVERAGE AUDIT (GATE 6.6) ===")
        print(f"Genuine DeepSeek-V4.1 Replays: {manifest['genuine_model_replays_count']}")
        print(f"Quarantined Synthetic Fixtures: {manifest['quarantined_synthetic_fixtures_count']}")
        for b_name, b_stats in manifest["benchmarks"].items():
            print(
                f"  - {b_name}: total={b_stats['total_queries']}, "
                f"genuine={b_stats['genuine_model_replays']}, "
                f"quarantined={b_stats['quarantined_synthetic_fixtures']}, "
                f"deterministic_fallback={b_stats['deterministic_planner_fallbacks']}"
            )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Canonical Whole-Standard CLI for AWS A3.0M/A3.0:2020 (Terms & Definitions)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ner", type=str, help="Run Named Entity Recognition over welding query.")
    group.add_argument("--route", type=str, help="Run multi-intent routing and plan synthesis.")
    group.add_argument("--expand", type=str, help="Run store-compiled semantic graph neighborhood expansion.")
    group.add_argument("--ask", type=str, help="Execute full question answering with provenance.")
    group.add_argument("--table-a3", type=str, help="Query Table A3 cross-reference matrix by designation or process.")
    group.add_argument("--qualify-reader", type=str, help="Run 3-arm gold-evidence vs retrieved reader qualification.")
    group.add_argument("--replay-audit", action="store_true", help="Run offline model replay coverage audit.")

    parser.add_argument(
        "--planner",
        type=str,
        choices=["deterministic", "deepseek-replay"],
        default="deterministic",
        help="Planner backend to use (default: deterministic).",
    )
    parser.add_argument("--json", action="store_true", help="Output result as structured JSON.")
    parser.add_argument("--offline", action="store_true", help="Enforce offline socket blocking.")

    args = parser.parse_args(argv)

    orig_socket = None
    if args.offline:
        import socket
        orig_socket = socket.socket
        class BlockedSocket(orig_socket):
            def __init__(self, *args, **kwargs):
                raise RuntimeError("Network disabled by --offline flag")
        socket.socket = BlockedSocket

    try:
        if args.ner:
            return run_ner_cli(args.ner, as_json=args.json)
        elif args.route:
            return run_route_cli(args.route, as_json=args.json, planner_name=args.planner)
        elif args.expand:
            return run_expand_cli(args.expand, as_json=args.json)
        elif args.ask:
            return run_ask_cli(args.ask, as_json=args.json, planner_name=args.planner)
        elif args.table_a3:
            return run_table_a3_cli(args.table_a3, as_json=args.json)
        elif args.qualify_reader:
            return run_qualify_reader_cli(args.qualify_reader, as_json=args.json)
        elif args.replay_audit:
            return run_replay_audit_cli(as_json=args.json)
        return 0
    finally:
        if orig_socket is not None:
            import socket
            socket.socket = orig_socket


if __name__ == "__main__":
    sys.exit(main())
