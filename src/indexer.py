"""
indexer.py: LightRAG indexing engine for AWS A3.0M/A3.0:2020.
Uses Google Gemini for entity-relation extraction and text embeddings.
Builds local graph and vector stores in ./storage.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from lightrag.llm.gemini import gemini_model_complete, gemini_embed

from src.config import (
    STORAGE_DIR,
    PARSED_TEXT_FILE,
    PARSED_TABLES_DIR,
    PARSED_FIGURES_DIR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_EMBED_MODEL
)

def get_rag_instance(working_dir: Path = STORAGE_DIR) -> LightRAG:
    working_dir.mkdir(parents=True, exist_ok=True)
    
    if not GEMINI_API_KEY:
        print("[WARNING] GEMINI_API_KEY is not set in environment or .env!")
        print("Please configure GEMINI_API_KEY to perform indexing.")
    
    # Configure Gemini embedding function (dim=768 for text-embedding-004)
    async def embed_func(texts):
        return await gemini_embed(
            texts,
            model=GEMINI_EMBED_MODEL,
            api_key=GEMINI_API_KEY
        )

    # Configure Gemini LLM function
    async def llm_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        return await gemini_model_complete(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            model=GEMINI_MODEL,
            api_key=GEMINI_API_KEY,
            **kwargs
        )

    rag = LightRAG(
        working_dir=str(working_dir),
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            func=embed_func,
            model_name=GEMINI_EMBED_MODEL
        ),
        llm_model_name=GEMINI_MODEL
    )
    return rag

def load_all_chunks(max_figures: int = 40):
    chunks = []
    
    # 1. Text chunks (Clause 4 & Preamble)
    if PARSED_TEXT_FILE.exists():
        with open(PARSED_TEXT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                chunks.append({
                    "id": data["chunk_id"],
                    "content": data["content"]
                })
        print(f"Loaded {len(chunks)} text chunks from {PARSED_TEXT_FILE}")

    # 2. Table chunks (Annex A)
    annex_a_jsonl = PARSED_TABLES_DIR / "annex_a_tables.jsonl"
    if annex_a_jsonl.exists():
        t_count = 0
        with open(annex_a_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                chunks.append({
                    "id": data["chunk_id"],
                    "content": data["content"]
                })
                t_count += 1
        print(f"Loaded {t_count} table chunks from {annex_a_jsonl}")

    # 3. Figure chunks (Annex B)
    annex_b_jsonl = PARSED_FIGURES_DIR / "annex_b_figures.jsonl"
    if annex_b_jsonl.exists():
        f_count = 0
        with open(annex_b_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                chunks.append({
                    "id": data["chunk_id"],
                    "content": data["content"]
                })
                f_count += 1
                if max_figures and f_count >= max_figures:
                    break
        print(f"Loaded {f_count} figure chunks from {annex_b_jsonl}")

    return chunks

def run_index(dry_run: bool = False, max_figures: int = 40):
    chunks = load_all_chunks(max_figures=max_figures)
    print(f"Total chunks ready for LightRAG ingestion: {len(chunks)}")
    
    if dry_run:
        print("[DRY RUN] Ingestion verified. Zero calls made to external APIs.")
        return

    if not GEMINI_API_KEY:
        print("[ERROR] Cannot run live indexing without GEMINI_API_KEY.")
        sys.exit(1)

    rag = get_rag_instance()
    texts = [c["content"] for c in chunks]
    ids = [c["id"] for c in chunks]
    
    print(f"Starting LightRAG ingestion of {len(texts)} chunks...")
    rag.insert(texts, ids=ids)
    print("Ingestion complete! Local graph and vector stores saved to ./storage")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index AWS A3.0 multimodal chunks into LightRAG")
    parser.add_argument("--dry-run", action="store_true", help="Validate chunk loading without calling model APIs")
    parser.add_argument("--max-figures", type=int, default=40, help="Maximum figure chunks to index")
    args = parser.parse_args()

    run_index(dry_run=args.dry_run, max_figures=args.max_figures)
