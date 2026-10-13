"""
query.py: Multimodal NLQ Engine for AWS A3.0M/A3.0:2020.
Combines LightRAG dual-level graph retrieval with local image/table resolution.
"""

import os
import sys
import re
import asyncio
import argparse
from pathlib import Path
from lightrag import QueryParam

from src.config import (
    STORAGE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    DEFAULT_ENGINE
)
from src.indexer import get_rag_instance
from src.citation_checker import extract_citations

TABLE_COMPANION_FIGURES = {
    "Table A1": ["Figure A1", "Figure A4"],
    "Table A2": ["Figure A1", "Figure A2"],
    "Table A3": ["Figure A1"],
    "Table A4": ["Figure A1"],
    "Table A5": ["Figure A2", "Figure A5", "Figure A6"],
}

def resolve_multimodal_assets(text: str):
    """Finds referenced figures or tables and resolves them to local disk paths."""
    resolved_figures = []
    
    # 1. Match both Annex A figures (Figure A1-A6) and Annex B figures (Figure B1-B97)
    fig_matches = re.findall(r'Figure\s+([AB]\d+[A-Z]?)', text, re.IGNORECASE)
    
    # 2. Match Table mentions
    table_matches = re.findall(r'Table\s+(A\d+)', text, re.IGNORECASE)
    
    # Automatically include companion Annex A classification charts for any cited table
    all_target_figures = set(fig_matches)
    for t_num in set(table_matches):
        t_key = f"Table {t_num.upper()}"
        if t_key in TABLE_COMPANION_FIGURES:
            for companion in TABLE_COMPANION_FIGURES[t_key]:
                all_target_figures.add(companion.replace("Figure ", ""))

    for fig_num in sorted(all_target_figures):
        clean_num = fig_num.upper()
        matching_pngs = list(PARSED_FIGURES_DIR.glob(f"Figure_{clean_num}_*.png"))
        if matching_pngs:
            resolved_figures.append({
                "figure_id": f"Figure {clean_num}",
                "image_path": str(matching_pngs[0])
            })
            
    resolved_tables = []
    for t_num in set(table_matches):
        clean_t = t_num.lower()
        t_file = PARSED_TABLES_DIR / f"table_{clean_t}.md"
        t_images = list(PARSED_TABLES_DIR.glob(f"Table_{clean_t.upper()}_*.png"))
        if t_file.exists():
            resolved_tables.append({
                "table_id": f"Table {t_num.upper()}",
                "table_path": str(t_file),
                "image_paths": [str(img) for img in t_images]
            })
            
    return resolved_figures, resolved_tables

async def async_query(query_str: str, mode: str = "mix", engine: str = DEFAULT_ENGINE) -> dict:
    if engine.lower() == "gemini" and not GEMINI_API_KEY:
        return {
            "query": query_str,
            "answer": "[ERROR: GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env.]",
            "citations": {},
            "resolved_figures": [],
            "resolved_tables": []
        }
    elif engine.lower() != "gemini" and not DEEPSEEK_API_KEY:
        return {
            "query": query_str,
            "answer": "[ERROR: DEEPSEEK_API_KEY not configured. Set DEEPSEEK_API_KEY in .env.]",
            "citations": {},
            "resolved_figures": [],
            "resolved_tables": []
        }

    rag = get_rag_instance(working_dir=STORAGE_DIR, engine=engine)
    await rag.initialize_storages()
    
    param = QueryParam(
        mode=mode,
        top_k=40,
        chunk_top_k=20,
        enable_rerank=False
    )
    
    response = await rag.aquery(query_str, param=param)
    citations = extract_citations(response)
    figures, tables = resolve_multimodal_assets(response)
    
    return {
        "query": query_str,
        "answer": response,
        "citations": citations,
        "resolved_figures": figures,
        "resolved_tables": tables
    }

def run_query(query_str: str, mode: str = "mix", engine: str = DEFAULT_ENGINE) -> dict:
    return asyncio.run(async_query(query_str, mode=mode, engine=engine))

def main():
    parser = argparse.ArgumentParser(description="Query AWS A3.0 Multimodal Knowledge Base")
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--mode", type=str, default="mix", choices=["mix", "local", "global", "naive"], help="Retrieval mode")
    parser.add_argument("--engine", type=str, default=DEFAULT_ENGINE, choices=["deepseek", "gemini"], help="LLM inference engine")
    args = parser.parse_args()

    result = run_query(args.query, mode=args.mode, engine=args.engine)
    
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
