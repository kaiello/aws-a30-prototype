"""
hybrid_retriever.py: Two-Stage Hybrid Retrieval Engine with Reciprocal Rank Fusion & Cross-Encoder Reranking.

Adopts Turbopuffer & Perplexity principles:
1. Stage 1 Sparse: SQLite FTS5 BM25 search for exact term and figure citations.
2. Stage 1 Dense: 1024-dim BGE-Large contextual chunk cosine similarity search.
3. Hybrid Fusion: Reciprocal Rank Fusion (RRF, k=60) merging sparse and dense candidate pools.
4. Stage 2 Rerank: Local cross-encoder (BAAI/bge-reranker-base) scoring top candidates down to top-k.
"""

import os
import sys
import re
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sentence_transformers import SentenceTransformer
from src.config import (
    STORAGE_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    RERANKER_MODEL,
    ENABLE_RERANKER
)
from src.pre_retrieval import expand_query

DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"
CONTEXTUAL_VDB_PATH = STORAGE_DIR / "vdb_chunks_contextual.json"

_dense_model = None
_reranker_model = None
_vdb_cache = None


class ContextualIndexMissingError(FileNotFoundError):
    """The required contextual vector store has not been provisioned."""


def get_dense_model():
    global _dense_model
    if _dense_model is None:
        _dense_model = SentenceTransformer(EMBEDDING_MODEL)
    return _dense_model

def get_reranker_model():
    global _reranker_model
    if not ENABLE_RERANKER:
        return None
    if _reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            # Check if model can be loaded locally or from cache
            _reranker_model = CrossEncoder(RERANKER_MODEL)
        except Exception as e:
            print(f"[hybrid_retriever] Cross-encoder unavailable ({str(e)}). Falling back to pure RRF scoring.")
            _reranker_model = False
    return _reranker_model if _reranker_model is not False else None

def get_vdb_data() -> Dict[str, Any]:
    global _vdb_cache
    if _vdb_cache is None:
        if not CONTEXTUAL_VDB_PATH.exists():
            raise ContextualIndexMissingError("Required contextual vector store is missing.")
        with open(CONTEXTUAL_VDB_PATH, "r", encoding="utf-8") as f:
            _vdb_cache = json.load(f)
    return _vdb_cache

def search_fts_chunks(query: str, top_k: int = 30) -> List[Dict[str, Any]]:
    """Performs SQLite FTS5 BM25 search over chunks_fts."""
    if not DUAL_SQLITE_PATH.exists():
        return []

    conn = sqlite3.connect(DUAL_SQLITE_PATH)
    cur = conn.cursor()

    # Clean query for FTS5 syntax
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', query)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    if not tokens:
        conn.close()
        return []

    fts_query = " OR ".join(f'"{t}"' for t in tokens[:12])
    
    results = []
    try:
        cur.execute("""
            SELECT chunk_id, full_doc_id, content, section, header, rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (fts_query, top_k))
        
        for row in cur.fetchall():
            results.append({
                "id": row[0],
                "full_doc_id": row[1],
                "content": row[2],
                "section": row[3],
                "header": row[4],
                "score": float(row[5])
            })
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

    return results

def search_dense_chunks(query: str, top_k: int = 30) -> List[Dict[str, Any]]:
    """Performs 1024-dim cosine similarity search against contextual chunk embeddings."""
    vdb = get_vdb_data()
    model = get_dense_model()

    query_text = f"Represent this sentence for searching relevant passages: {query}"
    q_vec = model.encode([query_text], normalize_embeddings=True)[0]

    scores = []
    for item in vdb["data"]:
        c_vec = np.array(item["vector"], dtype=np.float32)
        score = float(np.dot(q_vec, c_vec))
        scores.append((score, item))

    scores.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, item in scores[:top_k]:
        results.append({
            "id": item["id"],
            "full_doc_id": item["full_doc_id"],
            "content": item["content"],
            "header": item.get("context_header", ""),
            "score": round(score, 4)
        })

    return results

def reciprocal_rank_fusion(
    sparse_hits: List[Dict[str, Any]],
    dense_hits: List[Dict[str, Any]],
    k: int = 60,
    top_candidates: int = 25
) -> List[Dict[str, Any]]:
    """
    Fuses sparse BM25 and dense cosine rankings using Reciprocal Rank Fusion:
    RRF(d) = sum(1 / (k + rank_i(d)))
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for rank, hit in enumerate(sparse_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        if doc_id not in doc_map:
            doc_map[doc_id] = hit

    for rank, hit in enumerate(dense_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        if doc_id not in doc_map:
            doc_map[doc_id] = hit

    ranked_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)
    
    merged = []
    for did in ranked_ids[:top_candidates]:
        item = dict(doc_map[did])
        item["rrf_score"] = round(scores[did], 6)
        merged.append(item)

    return merged

def rerank_candidates(query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Applies cross-encoder pairwise scoring on candidates.
    Falls back gracefully to RRF score if reranker model is not available.
    """
    reranker = get_reranker_model()
    if not reranker or not candidates:
        return candidates[:top_k]

    pairs = [(query, c.get("content", "")) for c in candidates]
    try:
        ce_scores = reranker.predict(pairs)
        for i, c in enumerate(candidates):
            c["cross_encoder_score"] = float(ce_scores[i])
        
        candidates.sort(key=lambda x: x.get("cross_encoder_score", 0.0), reverse=True)
    except Exception as e:
        print(f"[hybrid_retriever] Reranking exception: {e}. Keeping RRF ordering.")

    return candidates[:top_k]

def hybrid_retrieve(query_str: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Full end-to-end two-stage retrieval pipeline:
    Pre-retrieval expansion -> Sparse BM25 + Dense Cosine -> RRF Fusion -> Cross-Encoder Reranking.
    """
    # Check the required store before expansion, database reads or model loading.
    get_vdb_data()

    # 1. Expand query terms and acronyms
    expansion = expand_query(query_str)
    search_query = expansion["enriched_query"]

    # 2. Dual-stage candidate retrieval
    sparse_candidates = search_fts_chunks(search_query, top_k=30)
    dense_candidates = search_dense_chunks(search_query, top_k=30)

    # 3. Reciprocal Rank Fusion
    fused_candidates = reciprocal_rank_fusion(sparse_candidates, dense_candidates, k=60, top_candidates=25)

    # 4. Cross-Encoder Reranking
    final_hits = rerank_candidates(query_str, fused_candidates, top_k=top_k)

    return final_hits

if __name__ == "__main__":
    test_q = "What is the throat of a fillet weld in Figure B25?"
    print(f"Executing Hybrid Retrieval for: '{test_q}'\n")
    results = hybrid_retrieve(test_q, top_k=3)
    for i, r in enumerate(results):
        print(f"Rank {i+1} [{r.get('id')}]: RRF={r.get('rrf_score', 0)} | CE={r.get('cross_encoder_score', 'n/a')}")
        print(f"Doc ID: {r.get('full_doc_id')}")
        print(f"Content Preview: {r.get('content', '')[:140]}...\n")
