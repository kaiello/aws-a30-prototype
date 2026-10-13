"""
query.py: Multimodal NLQ Engine for AWS A3.0M/A3.0:2020.
Combines LightRAG dual-level graph retrieval with local image/table resolution.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from lightrag import QueryParam

from src.config import (
    STORAGE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR,
    GEMINI_API_KEY
)
from src.indexer import get_rag_instance
from src.citation_checker import extract_citations

def resolve_multimodal_assets(text: str):
    """Finds referenced figures or tables and resolves them to local disk paths."""
    resolved_figures = []
    fig_matches = re.findall(r'Figure\s+(B\d+)', text, re.IGNORECASE)
    for fig_num in set(fig_matches):
        clean_num = fig_num.upper()
        # Search for corresponding PNG in parsed/figures
        matching_pngs = list(PARSED_FIGURES_DIR.glob(f"Figure_{clean_num}_*.png"))
        if matching_pngs:
            resolved_figures.append({
                "figure_id": f"Figure {clean_num}",
                "image_path": str(matching_pngs[0])
            })
            
    resolved_tables = []
    table_matches = re.findall(r'Table\s+(A\d+)', text, re.IGNORECASE)
    for t_num in set(table_matches):
        clean_t = t_num.lower()
        t_file = PARSED_TABLES_DIR / f"table_{clean_t}.md"
        if t_file.exists():
            resolved_tables.append({
                "table_id": f"Table {t_num.upper()}",
                "table_path": str(t_file)
            })
            
    return resolved_figures, resolved_tables

def run_query(query_str: str, mode: str = "mix") -> dict:
    if not GEMINI_API_KEY:
        return {
            "query": query_str,
            "answer": "[SIMULATED / OFFLINE MODE: GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env to run live query.]",
            "citations": {},
            "resolved_figures": [],
            "resolved_tables": []
        }

    rag = get_rag_instance(working_dir=STORAGE_DIR)
    param = QueryParam(mode=mode, top_k=40, chunk_top_k=20)
    
    response = rag.query(query_str, param=param)
    citations = extract_citations(response)
    figures, tables = resolve_multimodal_assets(response)
    
    return {
        "query": query_str,
        "answer": response,
        "citations": citations,
        "resolved_figures": figures,
        "resolved_tables": tables
    }

def main():
    parser = argparse.ArgumentParser(description="Query AWS A3.0 Multimodal Knowledge Base")
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--mode", type=str, default="mix", choices=["mix", "local", "global", "naive"], help="Retrieval mode")
    args = parser.parse_args()

    result = run_query(args.query, mode=args.mode)
    
    print("\n" + "="*70)
    print(f"QUERY: {result['query']}")
    print("="*70)
    print(f"\nANSWER:\n{result['answer']}\n")
    
    if result["citations"]:
        print("CITATIONS AUDIT:")
        for k, v in result["citations"].items():
            if v:
                print(f"  {k}: {v}")
                
    if result["resolved_figures"]:
        print("\nRESOLVED FIGURE ASSETS:")
        for fig in result["resolved_figures"]:
            print(f"  {fig['figure_id']} -> {fig['image_path']}")
            
    if result["resolved_tables"]:
        print("\nRESOLVED TABLE ASSETS:")
        for tbl in result["resolved_tables"]:
            print(f"  {tbl['table_id']} -> {tbl['table_path']}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
