"""
indexer.py: LightRAG indexing engine for AWS A3.0M/A3.0:2020.
Uses DeepSeek API for entity-relation extraction and local MiniLM for embeddings.
Builds local graph (NetworkX) and vector (NanoVectorDB) stores in ./storage.
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import sys
import json
import asyncio
import argparse
from pathlib import Path
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc

from typing import Optional, Dict, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import (
    STORAGE_DIR,
    PARSED_TEXT_FILE,
    PARSED_TABLES_DIR,
    PARSED_FIGURES_DIR,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    GEMINI_MODEL,
    CUSTOM_API_KEY,
    CUSTOM_BASE_URL,
    CUSTOM_MODEL,
    DEFAULT_ENGINE,
    EMBEDDING_MODEL,
    EMBEDDING_DIM
)

_embed_model = None
_RAG_INSTANCES: Dict[Tuple, LightRAG] = {}

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model

def get_rag_instance(
    working_dir: Path = STORAGE_DIR,
    engine: str = DEFAULT_ENGINE,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None
) -> LightRAG:
    global _RAG_INSTANCES
    working_dir.mkdir(parents=True, exist_ok=True)
    
    engine_lower = (engine or DEFAULT_ENGINE).lower()
    
    if engine_lower == "gemini":
        effective_key = api_key or GEMINI_API_KEY
        if not effective_key:
            raise ValueError("GEMINI_API_KEY is not set! Supply via --api-key, Web UI settings, or .env")
        effective_base_url = base_url or GEMINI_BASE_URL
        effective_model = model_name or GEMINI_MODEL
    elif engine_lower in ["custom", "openai"]:
        effective_key = api_key or CUSTOM_API_KEY
        if not effective_key:
            raise ValueError("Custom API key is not set! Supply via --api-key, Web UI settings, or CUSTOM_API_KEY in .env")
        effective_base_url = base_url or CUSTOM_BASE_URL
        effective_model = model_name or CUSTOM_MODEL
    else:
        effective_key = api_key or DEEPSEEK_API_KEY
        if not effective_key:
            raise ValueError("DEEPSEEK_API_KEY is not set! Supply via --api-key, Web UI settings, or .env")
        effective_base_url = base_url or DEEPSEEK_BASE_URL
        effective_model = model_name or DEEPSEEK_MODEL

    cache_key = (str(working_dir), engine_lower, effective_key, effective_model, effective_base_url)
    if cache_key in _RAG_INSTANCES:
        return _RAG_INSTANCES[cache_key]

    client = AsyncOpenAI(
        api_key=effective_key,
        base_url=effective_base_url,
        timeout=30.0,
        max_retries=2
    )

    async def llm_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history_messages:
            messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})
        
        resp = await client.chat.completions.create(
            model=effective_model,
            messages=messages,
            temperature=0.0
        )
        return resp.choices[0].message.content

    model = get_embed_model()

    async def embed_func(texts):
        return model.encode(texts, normalize_embeddings=True)

    rag = LightRAG(
        working_dir=str(working_dir),
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            func=embed_func,
            model_name=EMBEDDING_MODEL
        ),
        llm_model_name=effective_model
    )
    _RAG_INSTANCES[cache_key] = rag
    return rag

def load_all_chunks(max_figures: int = 0):
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
                if max_figures > 0 and f_count >= max_figures:
                    break
        print(f"Loaded {f_count} figure chunks from {annex_b_jsonl}")

    return chunks

async def async_index(dry_run: bool = False, max_figures: int = 0, limit: int = 0, batch_size: int = 20):
    chunks = load_all_chunks(max_figures=max_figures)
    if limit > 0:
        chunks = chunks[:limit]
    print(f"Total chunks ready for LightRAG ingestion: {len(chunks)}")
    
    if dry_run:
        print("[DRY RUN] Ingestion verified. Zero calls made to external APIs.")
        return

    rag = get_rag_instance()
    await rag.initialize_storages()
    
    total = len(chunks)
    print(f"Starting LightRAG ingestion of {total} chunks using DeepSeek (batch size: {batch_size})...")
    
    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch]
        ids = [c["id"] for c in batch]
        print(f"\nProcessing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} (chunks {i + 1} to {min(i + batch_size, total)})...")
        await rag.ainsert(texts, ids=ids)
        print(f"Batch {i // batch_size + 1} complete and persisted.")

    print("\nAll batches complete! Local graph and vector stores saved to ./storage")

def run_index(dry_run: bool = False, max_figures: int = 0, limit: int = 0, batch_size: int = 20):
    asyncio.run(async_index(dry_run=dry_run, max_figures=max_figures, limit=limit, batch_size=batch_size))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index AWS A3.0 multimodal chunks into LightRAG")
    parser.add_argument("--dry-run", action="store_true", help="Validate chunk loading without calling model APIs")
    parser.add_argument("--max-figures", type=int, default=0, help="Maximum figure chunks to index (0 for all)")
    parser.add_argument("--limit", type=int, default=0, help="Limit total chunks for testing")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for insertion")
    args = parser.parse_args()

    run_index(dry_run=args.dry_run, max_figures=args.max_figures, limit=args.limit, batch_size=args.batch_size)
