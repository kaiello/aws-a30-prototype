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
from src.citation_checker import extract_citations, extract_grounded_claims

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
    all_target_figures = set()
    
    # 1. Match both Annex A figures (Figure A1-A6) and Annex B figures (Figure B1-B97)
    # Handles: "Figure B25", "Figures B.24, B.25, and B.26", "Figure B.6", etc.
    for block in re.finditer(r'Figure[s]?\s+([AB]?\.?\d+[A-Z]?(?:[,\s]+(?:and\s+)?[AB]?\.?\d+[A-Z]?)*)', text, re.IGNORECASE):
        prefix = 'B' if 'B' in block.group(0).upper() else 'A'
        sub_figs = re.findall(r'([AB])?\.?(\d+[A-Z]?)', block.group(0), re.IGNORECASE)
        for pfx, num in sub_figs:
            final_pfx = pfx.upper() if pfx else prefix
            all_target_figures.add(f"{final_pfx}{num.upper()}")
            
    isolated = re.findall(r'Figure\s+([AB]\d+[A-Z]?)', text, re.IGNORECASE)
    for fig in isolated:
        all_target_figures.add(fig.upper())
    
    # 2. Match Table mentions
    table_matches = re.findall(r'Table\s+(A\d+)', text, re.IGNORECASE)
    
    # Automatically include companion Annex A classification charts for any cited table
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

def extract_see_also_terms(text: str):
    """Extracts 'See also' terms and bulleted subtypes as actionable cross-links."""
    see_also = []
    # Pattern 1: Explicit "See also <term1>, <term2>, ..., and <termN>"
    matches = re.findall(r'See\s+also\s+([^\.]+?)(?:\.|\n|$)', text, re.IGNORECASE)
    for m in matches:
        terms = re.split(r',\s*|\s+and\s+', m)
        for t in terms:
            clean = t.strip().rstrip('.').rstrip(',')
            if clean and not any(x in clean.lower() for x in ['figure', 'table', 'clause', 'aws', '[', ']', 'page', 'p.']):
                see_also.append(clean)
                
    # Pattern 2: Bullet items under "specific types", "such as", "includes"
    bullet_matches = re.findall(r'^\s*[\*\-]\s+(.+)$', text, re.MULTILINE)
    for b in bullet_matches:
        clean = b.strip().rstrip('.').rstrip(',')
        if len(clean) < 60 and not any(x in clean.lower() for x in ['figure', 'table', 'clause', 'aws', '[', ']', 'page', 'p.']):
            see_also.append(clean)
            
    # Deduplicate preserving order
    seen = set()
    result = []
    for item in see_also:
        norm = item.lower()
        if norm not in seen and len(norm) > 2:
            seen.add(norm)
            result.append(item)
    return result

async def async_query(query_str: str, mode: str = "mix", engine: str = DEFAULT_ENGINE) -> dict:
    if engine.lower() == "gemini" and not GEMINI_API_KEY:
        return {
            "query": query_str,
            "answer": "[ERROR: GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env.]",
            "citations": {},
            "grounded_claims": [],
            "resolved_figures": [],
            "resolved_tables": [],
            "see_also": []
        }
    elif engine.lower() != "gemini" and not DEEPSEEK_API_KEY:
        return {
            "query": query_str,
            "answer": "[ERROR: DEEPSEEK_API_KEY not configured. Set DEEPSEEK_API_KEY in .env.]",
            "citations": {},
            "grounded_claims": [],
            "resolved_figures": [],
            "resolved_tables": [],
            "see_also": []
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
    grounded_claims = extract_grounded_claims(response)
    figures, tables = resolve_multimodal_assets(f"{query_str}\n{response}")
    see_also = extract_see_also_terms(response)
    
    return {
        "query": query_str,
        "answer": response,
        "citations": citations,
        "grounded_claims": grounded_claims,
        "resolved_figures": figures,
        "resolved_tables": tables,
        "see_also": see_also
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
