"""
contextual_indexer.py: Long-Context Contextualized Embedding Engine.

Adopts Perplexity Research & Turbopuffer's "Beyond the Gold Passage" principle:
Transforms isolated text chunks into contextualized representations conditioned on
parent document identity, clause applicability, and cross-reference topology,
then encodes them using the high-capacity BAAI/bge-large-en-v1.5 (1024-dimensional)
embedding model offline.

Generates:
- storage/vdb_chunks_contextual.json (1024-dim contextual vector store)
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import STORAGE_DIR, PARSED_FIGURES_DIR, PARSED_TABLES_DIR

CHUNKS_KV_PATH = STORAGE_DIR / "kv_store_text_chunks.json"
CONTEXTUAL_VDB_PATH = STORAGE_DIR / "vdb_chunks_contextual.json"
DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"

CONTEXT_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
CONTEXT_EMBEDDING_DIM = 1024

_context_model = None

def get_context_model():
    global _context_model
    if _context_model is None:
        print(f"Loading long-context embedding model: {CONTEXT_EMBEDDING_MODEL} (1024-dim)...")
        _context_model = SentenceTransformer(CONTEXT_EMBEDDING_MODEL)
    return _context_model

def get_clause_context_header(full_doc_id: str) -> str:
    """Returns the normative clause hierarchy and scope for a given chunk."""
    doc_lower = full_doc_id.lower()
    if "clause_4" in doc_lower or "p" in doc_lower and "annex" not in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Clause 4 Glossary | "
            "SCOPE: Normative definitions of welding, cutting, brazing, and allied processes, joint geometries, and discontinuities."
        )
    elif "annex_a" in doc_lower or "table_a" in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Annex A Process Classification Charts & Tables A1-A5 | "
            "SCOPE: Official letter designations, energy sources, shielding methods, and process hierarchies."
        )
    elif "annex_b" in doc_lower or "figure_b" in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Annex B Engineering Figures B1-B54 | "
            "SCOPE: Visual diagrams of joint configurations, weld test positions, fillet weld throats, and groove anatomy."
        )
    elif "annex_c" in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Annex C Committee Style Guidelines & Rationale | "
            "SCOPE: Historical consensus rationale (e.g. edge joints vs parallel joints) and naming rules."
        )
    elif "annex_d" in doc_lower or "table_d" in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Annex D Summary of 2020 Modifications | "
            "SCOPE: Revision tracking of new terms (Table D1), altered terms, and deleted/deprecated terms (Table D6)."
        )
    elif "annex_f" in doc_lower:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Annex F Official Technical Inquiries | "
            "SCOPE: Procedures for obtaining formal committee rulings."
        )
    else:
        return (
            "DOCUMENT: AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions | "
            "SECTION: Clauses 1-3 General Requirements & Preamble."
        )

def sync_sqlite_chunks_fts(chunks: List[Dict[str, Any]]):
    """Synchronizes all chunks into an FTS5 virtual table for high-speed BM25 sparse search."""
    if not DUAL_SQLITE_PATH.exists():
        return
    print(f"Synchronizing {len(chunks)} chunks into SQLite FTS5 virtual table 'chunks_fts'...")
    conn = sqlite3.connect(DUAL_SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS chunks_fts")
    cur.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id, full_doc_id, content, section, header)")
    for c in chunks:
        doc_id = c["full_doc_id"]
        section = doc_id.split("_")[0] if "_" in doc_id else "general"
        header = c["contextual_text"].split("\n\nCONTENT:\n")[0]
        cur.execute(
            "INSERT INTO chunks_fts(chunk_id, full_doc_id, content, section, header) VALUES (?, ?, ?, ?, ?)",
            (c["chunk_id"], doc_id, c["raw_content"], section, header)
        )
    conn.commit()
    conn.close()
    print(f"Successfully populated 'chunks_fts' ({len(chunks)} rows) in {DUAL_SQLITE_PATH}.")

def build_contextual_chunks() -> List[Dict[str, Any]]:
    """Enriches raw text, table, and figure chunks with structural hierarchy and cross-reference context."""
    contextual_chunks = []
    seen_ids = set()

    # 1. Existing text & table chunks from kv_store
    if CHUNKS_KV_PATH.exists():
        with open(CHUNKS_KV_PATH, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        for chunk_id, info in chunks_data.items():
            doc_ref = info.get("full_doc_id", "")
            raw_content = info.get("content", "")
            clause_header = get_clause_context_header(doc_ref)
            
            term_matches = []
            for line in raw_content.split("\n"):
                line = line.strip()
                if line and not line.startswith("[") and not line.startswith("#"):
                    parts = line.split(". ")
                    if len(parts) > 1 and len(parts[0]) < 60:
                        term_matches.append(parts[0])

            terms_summary = f"KEY DEFINITIONS IN CHUNK: {', '.join(term_matches[:6])}" if term_matches else ""
            contextual_text = f"{clause_header}\n{terms_summary}\n\nCONTENT:\n{raw_content}"

            contextual_chunks.append({
                "chunk_id": chunk_id,
                "full_doc_id": doc_ref,
                "raw_content": raw_content,
                "contextual_text": contextual_text
            })
            seen_ids.add(chunk_id)

    # 2. Add all Annex B figure chunks (including Figures B24 to B54)
    annex_b_jsonl = PARSED_FIGURES_DIR / "annex_b_figures.jsonl"
    if annex_b_jsonl.exists():
        f_added = 0
        with open(annex_b_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                cid = data["chunk_id"]
                if cid not in seen_ids:
                    content = data["content"]
                    clause_header = get_clause_context_header(cid)
                    contextual_chunks.append({
                        "chunk_id": cid,
                        "full_doc_id": cid,
                        "raw_content": content,
                        "contextual_text": f"{clause_header}\n\nCONTENT:\n{content}"
                    })
                    seen_ids.add(cid)
                    f_added += 1
        print(f"Added {f_added} additional Annex B figure chunks to contextual corpus.")

    # 3. Add all Annex A table chunks
    annex_a_jsonl = PARSED_TABLES_DIR / "annex_a_tables.jsonl"
    if annex_a_jsonl.exists():
        t_added = 0
        with open(annex_a_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                cid = data["chunk_id"]
                if cid not in seen_ids:
                    content = data["content"]
                    clause_header = get_clause_context_header(cid)
                    contextual_chunks.append({
                        "chunk_id": cid,
                        "full_doc_id": cid,
                        "raw_content": content,
                        "contextual_text": f"{clause_header}\n\nCONTENT:\n{content}"
                    })
                    seen_ids.add(cid)
                    t_added += 1
        if t_added:
            print(f"Added {t_added} additional Annex A table chunks to contextual corpus.")

    return contextual_chunks

def index_contextual_chunks(force: bool = False):
    """Encodes all contextualized chunks into 1024-dim vectors and saves to JSON, syncing SQLite FTS5."""
    if CONTEXTUAL_VDB_PATH.exists() and not force:
        print(f"Contextual vector store already exists at {CONTEXTUAL_VDB_PATH}. Use --force to rebuild.")
        return

    chunks = build_contextual_chunks()
    print(f"Loaded {len(chunks)} total chunks for contextual encoding...")

    model = get_context_model()

    texts_to_embed = [c["contextual_text"] for c in chunks]
    print(f"Encoding {len(texts_to_embed)} chunks with {CONTEXT_EMBEDDING_MODEL} (batch size 16)...")
    
    embeddings = model.encode(texts_to_embed, batch_size=16, show_progress_bar=True, normalize_embeddings=True)

    records = []
    for i, c in enumerate(chunks):
        records.append({
            "id": c["chunk_id"],
            "full_doc_id": c["full_doc_id"],
            "vector": embeddings[i].tolist(),
            "content": c["raw_content"],
            "context_header": c["contextual_text"].split("\n\nCONTENT:\n")[0]
        })

    output_payload = {
        "model": CONTEXT_EMBEDDING_MODEL,
        "embedding_dim": CONTEXT_EMBEDDING_DIM,
        "total_chunks": len(records),
        "data": records
    }

    CONTEXTUAL_VDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXTUAL_VDB_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f)

    print(f"Successfully saved {len(records)} contextual vectors to {CONTEXTUAL_VDB_PATH}")
    
    # Synchronize SQLite FTS5
    sync_sqlite_chunks_fts(chunks)

def search_contextual_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Performs cosine similarity search against contextual chunk embeddings."""
    if not CONTEXTUAL_VDB_PATH.exists():
        index_contextual_chunks(force=False)

    with open(CONTEXTUAL_VDB_PATH, "r", encoding="utf-8") as f:
        vdb = json.load(f)

    model = get_context_model()
    # BGE models benefit from instruction prefix for queries
    query_text = f"Represent this sentence for searching relevant passages: {query}"
    q_vec = model.encode([query_text], normalize_embeddings=True)[0]

    results = []
    for item in vdb["data"]:
        c_vec = np.array(item["vector"], dtype=np.float32)
        score = float(np.dot(q_vec, c_vec))
        results.append({
            "id": item["id"],
            "full_doc_id": item["full_doc_id"],
            "score": round(score, 4),
            "content": item["content"],
            "context_header": item.get("context_header", "")
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contextual chunk indexing with long-context model")
    parser.add_argument("--force", action="store_true", help="Force re-indexing of contextual vectors")
    parser.add_argument("--search", type=str, help="Execute a test query against contextual vectors")
    args = parser.parse_args()

    if args.search:
        hits = search_contextual_chunks(args.search, top_k=3)
        print(f"\nTop hits for: '{args.search}'")
        for h in hits:
            print(f"[{h['score']}] {h['id']} ({h['full_doc_id']}):\n{h['context_header']}\n{h['content'][:140]}...\n")
    else:
        index_contextual_chunks(force=args.force)
