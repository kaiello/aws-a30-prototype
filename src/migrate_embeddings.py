"""
migrate_embeddings.py: Offline migration utility to re-encode LightRAG vector stores
with BAAI/bge-large-en-v1.5 (1024-dim) with zero external LLM API calls.
Ensures NanoVectorDB base64 matrix compatibility.
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import sys
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
from sentence_transformers import SentenceTransformer
from nano_vectordb.dbs import array_to_buffer_string, NanoVectorDB
from src.config import STORAGE_DIR, EMBEDDING_MODEL, EMBEDDING_DIM

VDB_CHUNKS_PATH = STORAGE_DIR / "vdb_chunks.json"
VDB_ENTITIES_PATH = STORAGE_DIR / "vdb_entities.json"
VDB_RELATIONS_PATH = STORAGE_DIR / "vdb_relationships.json"

def get_bge_model():
    print(f"Loading {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})...")
    return SentenceTransformer(EMBEDDING_MODEL)

def migrate_vdb_file(file_path: Path, model: SentenceTransformer, text_key: str = "content", batch_size: int = 64):
    if not file_path.exists():
        print(f"File {file_path} does not exist, skipping.")
        return

    print(f"\nProcessing {file_path.name}...")
    bak_path = file_path.with_name(f"{file_path.stem}_384.json.bak")
    source_path = bak_path if bak_path.exists() else file_path

    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create backup if not exists
    if not bak_path.exists():
        print(f"Creating backup: {bak_path.name}")
        with open(bak_path, "w", encoding="utf-8") as f_bak:
            json.dump(data, f_bak)

    records = data.get("data", [])
    print(f"Total records to encode: {len(records)} from {source_path.name}")

    texts = [r.get(text_key, "") for r in records]
    t0 = time.time()
    print(f"Encoding {len(texts)} items with {EMBEDDING_MODEL} in batches of {batch_size}...")

    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embs = model.encode(batch_texts, normalize_embeddings=True, show_progress_bar=False)
        all_vectors.append(batch_embs)
        if (i // batch_size + 1) % 10 == 0 or (i + batch_size >= len(texts)):
            print(f"  Encoded {min(i + batch_size, len(texts))}/{len(texts)} records...")

    matrix = np.vstack(all_vectors).astype(np.float32)
    elapsed = time.time() - t0
    print(f"Encoding complete in {elapsed:.1f}s. Matrix shape: {matrix.shape}")

    # Update records
    for i, r in enumerate(records):
        r["vector"] = matrix[i].tolist()

    data["embedding_dim"] = EMBEDDING_DIM
    # Crucial: NanoVectorDB requires matrix as base64 encoded buffer string
    data["matrix"] = array_to_buffer_string(matrix)

    # Save upgraded 1024-dim JSON
    print(f"Saving upgraded {EMBEDDING_DIM}-dim file to {file_path}...")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # Verification: Ensure NanoVectorDB can load the file without error
    try:
        client = NanoVectorDB(EMBEDDING_DIM, storage_file=str(file_path))
        print(f"Verification: NanoVectorDB successfully loaded {file_path.name} ({len(records)} vectors, dim={EMBEDDING_DIM}).")
    except Exception as e:
        print(f"ERROR: NanoVectorDB failed to load {file_path.name}: {e}")
        raise

def main():
    print("=" * 60)
    print(f"LightRAG Vector Store Migration to BGE-Large (1024-dim)")
    print("=" * 60)
    model = get_bge_model()
    migrate_vdb_file(VDB_CHUNKS_PATH, model, text_key="content")
    migrate_vdb_file(VDB_ENTITIES_PATH, model, text_key="content")
    migrate_vdb_file(VDB_RELATIONS_PATH, model, text_key="content")
    print("\nMigration complete! All LightRAG vector stores are now 1024-dim and base64-verified.")

if __name__ == "__main__":
    main()
