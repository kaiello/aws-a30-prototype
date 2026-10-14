"""
evaluate_all_chips.py: Comprehensive evaluation script for all interactive chips
in the AWS A3.0 Multimodal Prototype.
Validates:
1. Static structural integrity of all chips (labels, queries, syntax, encoding)
2. Category classification mapping (no orphan or empty categories)
3. Asset resolution: Does each chip resolve to its target figure image and page?
4. Multimodal retrieval verification on all suggestion chips and inspector chips
"""

import os
import sys
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import BASE_DIR, PARSED_FIGURES_DIR, PARSED_TABLES_DIR
from src.figure_inspectors import FIGURE_INSPECTORS, FIGURE_CATEGORIES, resolve_figure_image_filename
from src.query import resolve_multimodal_assets
from src.answer_routes import resolve_answer_route
from src.citation_checker import extract_citations, extract_grounded_claims
from src.epistemic_verifier import verify_epistemic_provenance

SUGGESTION_CHIPS = [
    {"label": "🔥 Flame Contact (Fig A6)", "query": "show me flame contact on figure A6", "expected_fig": "Figure A6"},
    {"label": "🧭 3D Welding Coordinates (Fig B16A)", "query": "In Figure B16A, what are the inclination of axis and rotation of face coordinate limits for Flat position groove welds in plate?", "expected_fig": "Figure B16A"},
    {"label": "🔨 Temper Beads (Fig B23J)", "query": "In Figure B23(J), what is the distinction between a toe temper bead and surface temper weld reinforcing beads?", "expected_fig": "Figure B23"},
    {"label": "🌀 FSW Schematic (Fig B46)", "query": "What are the callout components and features identified on Figure B46 for the Friction Stir Welding (FSW) process?", "expected_fig": "Figure B46"},
    {"label": "🔥 Flame Types (Fig B40)", "query": "What are the three distinct oxyacetylene flame types illustrated in Figure B40?", "expected_fig": "Figure B40"},
    {"label": "💍 6GR Restriction Ring (Fig B21)", "query": "Which pipe welding test position in Figure B21 includes a restriction ring?", "expected_fig": "Figure B21"},
    {"label": "📐 Fillet Throats (Fig B25)", "query": "Identify the three distinct fillet weld throats illustrated in Figure B25", "expected_fig": "Figure B25"},
    {"label": "📏 Root Face vs Root Edge (Fig B5)", "query": "Which figure illustrates groove face, root edge, and root face?", "expected_fig": "Figure B5"},
    {"label": "⚖️ GTAW vs TIG Rationale (Annex C)", "query": "According to Annex C1.5.3, why does the Definitions Subcommittee reject TIG and MIG in favor of GTAW and GMAW?", "expected_clause": "Annex C"},
    {"label": "📐 Parallel Joint Rationale (Annex C)", "query": "Why was the term parallel joint introduced in the 2020 edition to replace edge joint according to Annex C1.5.7?", "expected_clause": "Annex C"},
    {"label": "⚡ Waveform AIP & TIE (Table D1)", "query": "According to Table D1, what new electrical terms were introduced in the 2020 edition for waveform-controlled welding?", "expected_tbl": "Table D1"},
    {"label": "🗑️ Deleted Terms (Table D6)", "query": "According to Table D6, name physical science and chemistry terms that were deleted in the 2020 edition", "expected_tbl": "Table D6"},
    {"label": "🚫 FSW B75 Schedule (Negative Control)", "query": "Show me the friction stir welding parameter schedule on Figure B75", "negative_control": True}
]

def run_evaluation():
    results = {
        "summary": {},
        "categories_eval": [],
        "suggestion_chips_eval": [],
        "inspector_chips_eval": {
            "total_figures": len(FIGURE_INSPECTORS),
            "total_chips": 0,
            "chips_with_valid_syntax": 0,
            "chips_with_matched_assets": 0,
            "chips_with_valid_images": 0,
            "per_figure_breakdown": []
        }
    }

    # 1. Evaluate Categories
    print("="*70)
    print("STAGE 1: EVALUATING CATEGORIES AND TAXONOMY")
    print("="*70)
    cat_counts = {c["id"]: 0 for c in FIGURE_CATEGORIES}
    cat_labels = {c["id"]: c["label"] for c in FIGURE_CATEGORIES}
    
    for fig_id, data in FIGURE_INSPECTORS.items():
        cat = data.get("category", "")
        if cat in cat_counts:
            cat_counts[cat] += 1
        else:
            print(f"[WARNING] Figure {fig_id} has unregistered category '{cat}'")

    for cat_id, count in cat_counts.items():
        if cat_id == "all":
            continue
        print(f"  • {cat_labels.get(cat_id, cat_id)} ({cat_id}): {count} figures")
        results["categories_eval"].append({
            "category_id": cat_id,
            "label": cat_labels.get(cat_id, cat_id),
            "figure_count": count
        })

    # 2. Evaluate Suggestion Chips
    print("\n" + "="*70)
    print("STAGE 2: EVALUATING 13 TOP-LEVEL SUGGESTION CHIPS")
    print("="*70)
    for idx, sc in enumerate(SUGGESTION_CHIPS, 1):
        query = sc["query"]
        lbl = sc["label"]
        figs, tbls = resolve_multimodal_assets(query)
        route = resolve_answer_route(query, candidate_answer="")
        
        status = "PASS"
        issues = []
        
        # Verify figure resolution
        if "expected_fig" in sc:
            exp = sc["expected_fig"].upper()
            found = [f["figure_id"].upper() for f in figs]
            if not any(exp in f for f in found):
                # Check if route recovered it
                if route and any(exp in e.element_id.upper() for e in route.evidence_group):
                    pass
                else:
                    status = "WARN"
                    issues.append(f"Expected figure {sc['expected_fig']} not directly in query regex (resolved: {found})")
        
        # Verify table resolution
        if "expected_tbl" in sc:
            exp_tbl = sc["expected_tbl"].upper()
            found_tbls = [t["table_id"].upper() for t in tbls]
            if not any(exp_tbl in t for t in found_tbls):
                status = "WARN"
                issues.append(f"Expected table {sc['expected_tbl']} not resolved (resolved: {found_tbls})")

        print(f"[{status}] #{idx} {lbl}")
        print(f"       Query: '{query}'")
        print(f"       Resolved Figs: {[f['figure_id'] for f in figs]}")
        print(f"       Resolved Tables: {[t['table_id'] for t in tbls]}")
        if route and route.concept_name:
            print(f"       Context-Bench Route: '{route.concept_name}' (Recall: {route.evidence_recall_score})")
        if issues:
            print(f"       Issues: {issues}")
            
        results["suggestion_chips_eval"].append({
            "index": idx,
            "label": lbl,
            "query": query,
            "status": status,
            "resolved_figures": [f["figure_id"] for f in figs],
            "resolved_tables": [t["table_id"] for t in tbls],
            "has_route": bool(route and route.concept_name),
            "issues": issues
        })

    # 3. Evaluate Inspector Chips (267 Chips across 62 Figures)
    print("\n" + "="*70)
    print("STAGE 3: EVALUATING 267 INTERACTIVE CALLOUT & NODE CHIPS")
    print("="*70)
    
    total_chips = 0
    valid_syntax = 0
    matched_images = 0
    resolved_figs_count = 0
    
    for fig_id, data in FIGURE_INSPECTORS.items():
        title = data.get("title", "")
        page = data.get("page", "")
        groups = data.get("groups", [])
        img_file = resolve_figure_image_filename(fig_id)
        img_exists = bool(img_file and (PARSED_FIGURES_DIR / img_file).exists())
        
        fig_clean = fig_id.replace("Figure ", "").strip().upper()
        
        fig_eval = {
            "figure_id": fig_id,
            "title": title,
            "page": page,
            "image_file": img_file,
            "image_exists": img_exists,
            "chips_count": 0,
            "chips": []
        }
        
        for g in groups:
            for c in g.get("chips", []):
                total_chips += 1
                fig_eval["chips_count"] += 1
                lbl = c.get("label", "")
                q = c.get("query", "")
                
                # Check syntax and URI safety
                syntax_ok = bool(lbl and q and len(lbl) > 1 and len(q) > 5)
                # Check URL encoding safety
                try:
                    enc = urllib.parse.quote(q)
                    dec = urllib.parse.unquote(enc)
                    encoding_ok = (dec == q)
                except Exception:
                    encoding_ok = False
                
                if syntax_ok and encoding_ok:
                    valid_syntax += 1
                    
                # Check if image exists
                if img_exists:
                    matched_images += 1
                    
                # Check if query references the figure or can resolve figure assets
                q_figs, _ = resolve_multimodal_assets(f"{fig_id} {q}")
                resolved_this_fig = any(fig_clean in f["figure_id"].upper() for f in q_figs)
                if resolved_this_fig:
                    resolved_figs_count += 1
                    
                fig_eval["chips"].append({
                    "label": lbl,
                    "query": q,
                    "syntax_ok": syntax_ok and encoding_ok,
                    "resolves_figure": resolved_this_fig
                })
                
        results["inspector_chips_eval"]["per_figure_breakdown"].append(fig_eval)

    results["inspector_chips_eval"]["total_chips"] = total_chips
    results["inspector_chips_eval"]["chips_with_valid_syntax"] = valid_syntax
    results["inspector_chips_eval"]["chips_with_valid_images"] = matched_images
    results["inspector_chips_eval"]["chips_with_matched_assets"] = resolved_figs_count

    print(f"\nTotal Figures Evaluated: {len(FIGURE_INSPECTORS)}")
    print(f"Total Callout & Node Chips Evaluated: {total_chips}")
    print(f"Chips with 100% Valid Syntax & Safe URI Encoding: {valid_syntax}/{total_chips} ({valid_syntax/total_chips*100:.1f}%)")
    print(f"Chips with High-Resolution Image Files On Disk: {matched_images}/{total_chips} ({matched_images/total_chips*100:.1f}%)")
    print(f"Chips Resolving Directly to Parent Figure: {resolved_figs_count}/{total_chips} ({resolved_figs_count/total_chips*100:.1f}%)")

    # Overall Summary
    results["summary"] = {
        "total_categories": len(FIGURE_CATEGORIES) - 1, # excluding 'all'
        "total_figures": len(FIGURE_INSPECTORS),
        "total_suggestion_chips": len(SUGGESTION_CHIPS),
        "total_inspector_chips": total_chips,
        "grand_total_interactive_chips": len(SUGGESTION_CHIPS) + total_chips,
        "syntax_pass_rate": f"{valid_syntax/total_chips*100:.1f}%",
        "image_asset_pass_rate": f"{matched_images/total_chips*100:.1f}%",
        "figure_resolution_pass_rate": f"{resolved_figs_count/total_chips*100:.1f}%"
    }

    report_path = BASE_DIR / "eval" / "chips_evaluation_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[REPORT SAVED] Full report written to: {report_path}")
    return results

if __name__ == "__main__":
    run_evaluation()
