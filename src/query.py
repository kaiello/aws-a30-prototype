"""
query.py: Multimodal NLQ Engine for AWS A3.0M/A3.0:2020.
Combines LightRAG dual-level graph retrieval with local image/table resolution.
"""

import os
import sys
import re
import asyncio
import argparse
from typing import Optional
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from lightrag import QueryParam

from src.config import (
    STORAGE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    CUSTOM_API_KEY,
    CUSTOM_BASE_URL,
    CUSTOM_MODEL,
    DEFAULT_ENGINE
)
from src.indexer import get_rag_instance
from src.citation_checker import extract_citations, extract_grounded_claims
from src.epistemic_verifier import verify_epistemic_provenance
from src.answer_routes import resolve_answer_route
from src.pre_retrieval import check_early_abstention, expand_query
from src.hybrid_retriever import ContextualIndexMissingError, hybrid_retrieve

from src.standard_manifest import get_manifest, extract_references

TABLE_COMPANION_FIGURES = get_manifest().companions()

def resolve_multimodal_assets(text: str):
    """Resolve canonical elements and every declared page without glob guesses."""
    manifest = get_manifest()
    references = extract_references(text)
    direct = set(references["figures"])
    groups = {label: entry["text"] for entry in references["unresolved_elements"]
              if entry["status"] == "group" for label in entry["candidates"]}
    targets = direct | set(groups)
    companions = manifest.companions()
    for table in references["tables"]:
        targets.update(companions.get(table, []))
    figures = []
    for label in sorted(targets):
        paths = manifest.asset_paths(label, {".png"})
        if paths:
            record = {"figure_id": label, "image_path": paths[0], "image_paths": paths,
                      "source_anchors": manifest.source_anchors(label)}
            if label in groups and label not in direct:
                record["requested_as_group"] = groups[label]
            if label not in direct and label not in groups:
                record.update(relationship="ui_companion", relationship_verification="candidate")
            figures.append(record)
    tables = []
    for label in references["tables"]:
        markdown = manifest.asset_paths(label, {".md"})
        images = manifest.asset_paths(label, {".png"})
        # Preserve the existing table_path interface; do not invent absent exports.
        if markdown:
            tables.append({"table_id": label, "table_path": markdown[0], "image_paths": images,
                           "source_anchors": manifest.source_anchors(label),
                           "text_asset_verification": "candidate"})
    return figures, tables

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

async def async_query(
    query_str: str,
    mode: str = "mix",
    engine: str = DEFAULT_ENGINE,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None
) -> dict:
    engine_lower = (engine or DEFAULT_ENGINE).lower()
    
    if engine_lower == "gemini":
        key = api_key or GEMINI_API_KEY
        if not key:
            return {
                "query": query_str,
                "answer": "[ERROR: GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env, supply via --api-key, or enter in Web UI settings.]",
                "citations": {},
                "grounded_claims": [],
                "resolved_figures": [],
                "resolved_tables": [],
                "see_also": []
            }
    elif engine_lower in ["custom", "openai"]:
        key = api_key or CUSTOM_API_KEY
        if not key:
            return {
                "query": query_str,
                "answer": "[ERROR: Custom API Key not configured. Supply via --api-key, CUSTOM_API_KEY in .env, or enter in Web UI settings.]",
                "citations": {},
                "grounded_claims": [],
                "resolved_figures": [],
                "resolved_tables": [],
                "see_also": []
            }
    else:
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            return {
                "query": query_str,
                "answer": "[ERROR: DEEPSEEK_API_KEY not configured. Set DEEPSEEK_API_KEY in .env, supply via --api-key, or enter in Web UI settings.]",
                "citations": {},
                "grounded_claims": [],
                "resolved_figures": [],
                "resolved_tables": [],
                "see_also": []
            }

    # 0. Deterministic early abstention for out-of-scope negative controls
    early_abstain = check_early_abstention(query_str)
    if early_abstain:
        figures, tables = resolve_multimodal_assets(query_str)
        answer_route = resolve_answer_route(query_str, early_abstain["answer"])
        return {
            "query": query_str,
            "answer": early_abstain["answer"],
            "citations": {"out_of_scope": True},
            "grounded_claims": [],
            "resolved_figures": figures,
            "resolved_tables": tables,
            "see_also": [],
            "epistemic_trace": {"provenance_score": 1.0, "status": "TRUTHFUL_ABSTENTION"},
            "answer_route": answer_route.to_dict(),
            "retrieved_evidence": []
        }

    # 1. Two-stage hybrid retrieval (FTS5 BM25 + BGE-large dense + RRF + Cross-Encoder)
    try:
        hybrid_evidence = hybrid_retrieve(query_str, top_k=5)
    except ContextualIndexMissingError:
        return {
            "query": query_str,
            "answer": "",
            "error": (
                "Required local retrieval index is missing. Restore a compatible "
                "storage/vdb_chunks_contextual.json from a trusted backup, or ask the "
                "project maintainer to provision it before retrying. No answer was generated."
            ),
            "error_code": "RETRIEVAL_INDEX_MISSING",
            "citations": {},
            "grounded_claims": [],
            "resolved_figures": [],
            "resolved_tables": [],
            "see_also": [],
            "retrieved_evidence": []
        }

    try:
        rag = get_rag_instance(
            working_dir=STORAGE_DIR,
            engine=engine,
            api_key=key,
            model_name=model_name,
            base_url=base_url
        )
        await rag.initialize_storages()
        
        param = QueryParam(
            mode=mode,
            top_k=40,
            chunk_top_k=20,
            enable_rerank=False
        )
        
        evidence_blocks = []
        for c in hybrid_evidence:
            c_id = c.get("full_doc_id") or c.get("id", "")
            evidence_blocks.append(f"[{c_id}]\n{c.get('content', '')}")
        evidence_text = "\n\n".join(evidence_blocks)

        augmented_prompt = (
            f"{query_str}\n\n"
            f"[PRIMARY NORMATIVE EVIDENCE CONTEXT FROM AWS A3.0M/A3.0:2020]:\n"
            f"{evidence_text}\n\n"
            f"Answer the query authoritatively using the normative definitions, tables, or figures above. "
            f"Always cite the exact Clause number, Annex, Table, or Figure."
        )

        response = await rag.aquery(augmented_prompt, param=param)
        if response is None:
            raise RuntimeError("LLM returned no response. Please verify your API key, model name, and network connection.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        if hybrid_evidence:
            top_chunk = hybrid_evidence[0]
            top_content = top_chunk.get("content", "").strip()
            top_id = top_chunk.get("full_doc_id") or top_chunk.get("id", "")
            response = (
                f"[Normative Extract from {top_id}]:\n\n"
                f"{top_content}\n\n"
                f"(Synthesized via local hybrid retrieval; upstream LLM unavailable: {str(e)[:120]})"
            )
        else:
            return {
                "query": query_str,
                "answer": f"[ERROR: Query execution failed: {str(e)}]",
                "error": str(e),
                "citations": {},
                "grounded_claims": [],
                "resolved_figures": [],
                "resolved_tables": [],
                "see_also": [],
                "retrieved_evidence": hybrid_evidence
            }

    citations = extract_citations(response)
    grounded_claims = extract_grounded_claims(response)
    combined_asset_text = f"{query_str}\n{response}\n" + " ".join([c.get("content", "") for c in hybrid_evidence[:3]])
    figures, tables = resolve_multimodal_assets(combined_asset_text)
    see_also = extract_see_also_terms(response)
    epistemic_trace = verify_epistemic_provenance(query_str, response)
    answer_route = resolve_answer_route(query_str, response)
    
    return {
        "query": query_str,
        "answer": response,
        "citations": citations,
        "grounded_claims": grounded_claims,
        "resolved_figures": figures,
        "resolved_tables": tables,
        "see_also": see_also,
        "epistemic_trace": epistemic_trace,
        "answer_route": answer_route.to_dict(),
        "retrieved_evidence": hybrid_evidence
    }

import threading

_QUERY_LOOP = None
_QUERY_THREAD = None

def get_query_event_loop() -> asyncio.AbstractEventLoop:
    global _QUERY_LOOP, _QUERY_THREAD
    if _QUERY_LOOP is None or _QUERY_LOOP.is_closed():
        _QUERY_LOOP = asyncio.new_event_loop()
        def _runner(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        _QUERY_THREAD = threading.Thread(target=_runner, args=(_QUERY_LOOP,), daemon=True, name="LightRAGEventLoop")
        _QUERY_THREAD.start()
    return _QUERY_LOOP

def run_query(
    query_str: str,
    mode: str = "mix",
    engine: str = DEFAULT_ENGINE,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None
) -> dict:
    """Thread-safe synchronous query executor using a persistent dedicated event loop."""
    loop = get_query_event_loop()
    future = asyncio.run_coroutine_threadsafe(
        async_query(
            query_str,
            mode=mode,
            engine=engine,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        ),
        loop
    )
    return future.result()

def main():
    parser = argparse.ArgumentParser(description="Query AWS A3.0 Multimodal Knowledge Base")
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--mode", type=str, default="mix", choices=["mix", "local", "global", "naive"], help="Retrieval mode")
    parser.add_argument("--engine", type=str, default=DEFAULT_ENGINE, choices=["deepseek", "gemini", "custom", "openai"], help="LLM inference engine")
    parser.add_argument("--api-key", type=str, default=None, help="Custom API key (overrides .env)")
    parser.add_argument("--model", type=str, default=None, help="Custom model name (e.g. gpt-4o, gemini-2.0-flash, deepseek-chat)")
    parser.add_argument("--base-url", type=str, default=None, help="Custom base URL (for OpenAI, Ollama, Groq, etc.)")
    args = parser.parse_args()

    result = run_query(
        args.query,
        mode=args.mode,
        engine=args.engine,
        api_key=args.api_key,
        model_name=args.model,
        base_url=args.base_url
    )

    if result.get("error_code") == "RETRIEVAL_INDEX_MISSING":
        print(f"ERROR: {result['error']}", file=sys.stderr)
        raise SystemExit(1)
    
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

    if result.get("answer_route"):
        ar = result["answer_route"]
        print(f"\nANSWER ROUTE BUNDLE: Status={ar['status']} | Recall={ar['evidence_recall_score']} | Epistemic={ar['epistemic_score']}")
        print(f"  Concept: {ar.get('concept_name')} ({ar.get('concept_type')})")
        print(f"  Supporting Evidence ({len(ar.get('evidence_group', []))} items):")
        for ev in ar.get("evidence_group", [])[:6]:
            print(f"    - [{ev['evidence_type'].upper()}] {ev['element_id']}: {ev['title']} (Chips: {len(ev.get('callout_chips', []))})")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
