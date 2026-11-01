"""evidence_whole_standard_cli.py - Canonical Whole-Standard CLI for AWS A3.0M/A3.0:2020.

Deterministic, offline command-line interface supporting:
1. --ner "<query>": Run deterministic Welding Domain Named Entity Recognition.
2. --route "<query>": Run callout/backlink-indexed multi-intent routing and action planning.
3. --ask "<query>": Execute full multi-store retrieval, Layer 6 composition, and Gate 5.6 provenance.
4. --planner deterministic|deepseek-replay: Select planner backend (default: deterministic).
5. --json: Output structured JSON receipt.

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
        "actions": plan.get("actions"),
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Canonical Whole-Standard CLI for AWS A3.0M/A3.0:2020 (Terms & Definitions)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ner", type=str, help="Run Named Entity Recognition over welding query.")
    group.add_argument("--route", type=str, help="Run multi-intent routing and plan synthesis.")
    group.add_argument("--ask", type=str, help="Execute full question answering with provenance.")

    parser.add_argument(
        "--planner",
        type=str,
        choices=["deterministic", "deepseek-replay"],
        default="deterministic",
        help="Planner backend to use (default: deterministic).",
    )
    parser.add_argument("--json", action="store_true", help="Output result as structured JSON.")

    args = parser.parse_args(argv)

    if args.ner:
        return run_ner_cli(args.ner, as_json=args.json)
    elif args.route:
        return run_route_cli(args.route, as_json=args.json, planner_name=args.planner)
    elif args.ask:
        return run_ask_cli(args.ask, as_json=args.json, planner_name=args.planner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
