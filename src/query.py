"""
query.py: Multimodal NLQ Engine for AWS A3.0M/A3.0:2020.
Combines LightRAG dual-level graph retrieval with local image/table resolution.
"""

import os
import sys
import re
import asyncio
import argparse
import json
import hashlib
import time
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
from src.terminology_retrieval import TerminologyRegistryError, get_terminology_evidence
from src.grounded_answer import compose_grounded_answer, project_reviewed_facts
from src.evidence_resolution import qualify_reference_hierarchy, resolve_claim_evidence

from src.standard_manifest import ManifestError, get_manifest, extract_references, extract_reference_records

TABLE_COMPANION_FIGURES = get_manifest().companions()

def resolve_multimodal_assets(text: str):
    """Resolve canonical elements and every declared page without glob guesses."""
    manifest = get_manifest()
    def availability(assets):
        states = {asset["status"] for asset in assets}
        return next((state for state in ("corrupt", "missing", "unavailable") if state in states),
                    "complete" if assets else "source_only")
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
        assets = manifest.validated_assets(label, {".png"})
        paths = [asset["path"] for asset in assets if asset["status"] == "complete"]
        record = {"figure_id": label, "image_path": paths[0] if paths else None, "image_paths": paths,
                  "source_anchors": manifest.source_anchors(label),
                  "asset_status": availability(assets), "assets": assets}
        if label in groups and label not in direct:
            record["requested_as_group"] = groups[label]
        if label not in direct and label not in groups:
            record.update(relationship="ui_companion", relationship_verification="candidate")
        figures.append(record)
    tables = []
    for label in references["tables"]:
        assets = manifest.validated_assets(label)
        healthy = [asset for asset in assets if asset["status"] == "complete"]
        markdown = [asset["path"] for asset in healthy if Path(asset["relpath"]).suffix.lower() == ".md"]
        images = [asset["path"] for asset in healthy if Path(asset["relpath"]).suffix.lower() == ".png"]
        # Preserve the existing table_path interface; do not invent absent exports.
        tables.append({"table_id": label, "table_path": markdown[0] if markdown else None,
                       "image_paths": images, "source_anchors": manifest.source_anchors(label),
                       "text_asset_verification": "candidate" if markdown else "unavailable",
                       "asset_status": availability(assets), "assets": assets})
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

def _query_failure(query, code, message, retrieved_evidence=None):
    return {"query": query, "answer": "", "error": message, "error_code": code,
            "answer_outcome": "error", "answer_origin": "none",
            "answer_assessment": {"status": "UNASSESSED", "validated": False,
                                  "citation_support": "unassessed"},
            "citations": {}, "grounded_claims": [], "resolved_figures": [],
            "resolved_tables": [], "see_also": [],
            "retrieved_evidence": retrieved_evidence or [],
            "claim_evidence_links": [],
            "claim_evidence_assessment": {"status": "UNASSESSED", "complete": False,
                "required_fact_ids": [], "observed_fact_ids": [], "diagnostics": ["no_claims_extracted"]}}


def _attach_claim_evidence(result, evidence_context=(), *, reviewed_bundle=None):
    """Attach bounded identity evidence; only the server projects reviewed facts.

    Generated claims have no inferred selection or reviewed authority. Extraction
    may omit prose, so these links never certify complete generated answers.
    """
    claims = result.get("grounded_claims", [])
    assessment = {"status": "UNASSESSED", "complete": False, "required_fact_ids": [],
                  "observed_fact_ids": [], "diagnostics": ["no_claims_extracted"]}
    resolution = {"links": [], "assessment": assessment, "timings_ms": {}}
    if claims:
        try:
            view = project_reviewed_facts(reviewed_bundle) if reviewed_bundle is not None else None
            resolution = resolve_claim_evidence(claims, evidence_context, reviewed_fact_view=view)
        except (ValueError, TypeError, KeyError, RuntimeError, OSError):
            resolution["assessment"] = dict(assessment, diagnostics=["claim_evidence_unavailable"])
    reviewed = result.get("answer_assessment", {}).get("status") == "SUPPORTED_REVIEWED_FACTS"
    if reviewed and not (resolution["assessment"].get("status") == "SUPPORTED_REVIEWED_FACTS"
                         and resolution["assessment"].get("complete") is True):
        # A conflicting badge must not survive a failed source binding, and no
        # model fallback can repair an invalid reviewed extract's authority.
        result = _query_failure(result.get("query", ""), "EVIDENCE_BINDING_FAILED",
            "Reviewed source bindings could not be validated. No answer was returned.")
        resolution = {"links": [], "assessment": dict(assessment, status="INSUFFICIENT_EVIDENCE",
                      diagnostics=["reviewed_claim_evidence_incomplete"]), "timings_ms": resolution["timings_ms"]}
    result["claim_evidence_links"] = resolution["links"]
    result["claim_evidence_assessment"] = resolution["assessment"]
    result.setdefault("timings_ms", {}).update({"claim_evidence_" + key: value
                                               for key, value in resolution["timings_ms"].items()})
    return result


def _resolve_display_assets(text):
    """Legacy navigation availability must not preempt claim-level assessment."""
    try:
        return resolve_multimodal_assets(text)
    except (ManifestError, OSError):
        return [], []


def _reject_unresolved_citations(result):
    """Withhold generated assertions with unresolved source identity.

    Full-response parsing also covers prose missed by claim extraction. This
    checks reference identity only; an exact citation never grants support.
    Rejected claim links remain diagnostic records, not asserted facts.
    """
    response = result["answer"]
    try:
        hierarchy = qualify_reference_hierarchy(response, extract_reference_records(response))
        mentions = hierarchy["mentions"]
        diagnostics = list(hierarchy["diagnostics"])
        if any(mention["resolution"]["status"] not in {"exact", "page_only"} for mention in mentions):
            diagnostics.append("unresolved_generated_reference")
    except (ManifestError, OSError):
        mentions, diagnostics = [], ["source_identity_unavailable"]
    if not diagnostics:
        return result
    answer = "The generated response contains a source reference that could not be validated. No generated answer was returned. Clarify the source reference or ask about an exact standard element."
    result.update(answer=answer, answer_outcome="insufficient_evidence", answer_origin="none",
                  grounded_claims=[], see_also=[],
                  answer_assessment={"status": "INSUFFICIENT_EVIDENCE", "validated": False,
                      "citation_support": "invalid", "assessment_scope": "source_identity_only",
                      "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                      "diagnostics": diagnostics},
                  citation_diagnostics={"references": mentions, "diagnostics": diagnostics})
    result["claim_evidence_assessment"].update(answer_withheld=True, complete=False)
    # Graph navigation may contain the rejected text as a compatibility field.
    if isinstance(result.get("answer_route"), dict):
        result["answer_route"]["primary_answer"] = None
    return result


def _scope_decision(answer):
    return {"status": "TRUTHFUL_ABSTENTION", "validated": True,
            "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            "assessment_scope": "deterministic_scope_policy"}


def _reviewed_trace(assessment):
    supported = assessment.get("status") == "SUPPORTED_REVIEWED_FACTS" and assessment.get("validated") is True
    return {"epistemic_status": "SUPPORTED_REVIEWED_FACTS" if supported else "INSUFFICIENT_EVIDENCE",
            "assessment_status": assessment.get("status", "UNASSESSED"),
            "assessment_scope": "reviewed_fact_bindings", "provenance_score": None,
            "graph_link_coverage": None, "is_abstention": False,
            "concepts_verified": [], "unverified_concepts": [],
            "manifest_summary": "Reviewed fact/source bindings assessed; graph connectivity is not an answer-truth score."}


async def async_query(
    query_str: str,
    mode: str = "mix",
    engine: str = DEFAULT_ENGINE,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    evidence_version: str = "v1",
    v2_reader: str = "extractive"
) -> dict:
    started = time.perf_counter()
    if (not isinstance(evidence_version, str) or not isinstance(v2_reader, str)
            or evidence_version not in {"v1", "v2"} or v2_reader not in {"extractive", "local"}):
        raise ValueError("Unsupported evidence version or reader")
    if evidence_version == "v2":
        from src.evidence_sources import load_query_evidence
        from src.evidence_v2 import EvidenceStore
        from src.evidence_reader import LocalVisionReader, read_packet
        from src.config import BASE_DIR, OLLAMA_BASE_URL, VLM_MODEL
        try:
            packet = EvidenceStore(load_query_evidence(BASE_DIR, query_str)).packet(query_str)
            projected = time.perf_counter()
            reader = LocalVisionReader(OLLAMA_BASE_URL, VLM_MODEL) if v2_reader == "local" else None
            result = read_packet(packet, BASE_DIR, generate=reader)
            result["timings_ms"]["source_projection"] = round((projected - started) * 1000, 3)
            result["timings_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
            return result
        except (ValueError, OSError, KeyError, TypeError):
            return _query_failure(query_str, "V2_SOURCE_UNAVAILABLE",
                "Version 2 source evidence is missing, stale or invalid. Restore its matching source and versioned extraction before retrying.")
    # Deterministic scope decisions and reviewed composition require no provider.
    early_abstain = check_early_abstention(query_str)
    if early_abstain:
        answer = early_abstain["answer"]
        decision = _scope_decision(answer)
        figures, tables = _resolve_display_assets(query_str)
        return _attach_claim_evidence({"query": query_str, "answer": answer, "citations": {"out_of_scope": True},
                "grounded_claims": [], "resolved_figures": figures, "resolved_tables": tables,
                "see_also": [], "answer_outcome": "abstention", "answer_origin": "none",
                "answer_assessment": dict(decision, citation_support="not_applicable"),
                "epistemic_trace": verify_epistemic_provenance(query_str, answer, decision=decision),
                "answer_route": resolve_answer_route(query_str, answer, decision=decision).to_dict(),
                "retrieved_evidence": [], "timings_ms": {"total": round((time.perf_counter()-started)*1000, 3)}})

    try:
        reviewed = get_terminology_evidence(query_str)
    except TerminologyRegistryError:
        return _query_failure(query_str, "TERMINOLOGY_REGISTRY_INVALID",
            "Reviewed local terminology evidence is unavailable or stale. Ask the maintainer to restore the reviewed registry and matching sources before retrying. No answer was generated.")
    if reviewed is not None:
        composed = compose_grounded_answer(query_str, reviewed)
        if composed is not None:
            answer = composed.get("answer", "")
            figures, tables = _resolve_display_assets(query_str + "\n" + answer)
            result = dict(composed, query=query_str, resolved_figures=figures, resolved_tables=tables,
                        see_also=[], retrieved_evidence=[reviewed],
                        terminology_resolution=reviewed.get("terminology_resolution", {}),
                        epistemic_trace=_reviewed_trace(composed.get("answer_assessment", {})),
                        timings_ms={})
            result = _attach_claim_evidence(result, [reviewed], reviewed_bundle=reviewed)
            result["timings_ms"]["total"] = round((time.perf_counter()-started)*1000, 3)
            return result

    engine_lower = (engine or DEFAULT_ENGINE).lower()
    key = api_key or (GEMINI_API_KEY if engine_lower == "gemini" else
                     CUSTOM_API_KEY if engine_lower in {"custom", "openai"} else DEEPSEEK_API_KEY)
    if not key:
        return _query_failure(query_str, "MODEL_PROVIDER_UNCONFIGURED",
                              "The selected model provider is not configured. No generated answer is available.")
    try:
        hybrid_evidence = hybrid_retrieve(query_str, top_k=5)
    except ContextualIndexMissingError:
        return _query_failure(query_str, "RETRIEVAL_INDEX_MISSING",
            "Required local retrieval index is missing. Restore a compatible storage/vdb_chunks_contextual.json from a trusted backup, or ask the project maintainer to provision it before retrying. No answer was generated.")
    except TerminologyRegistryError:
        return _query_failure(query_str, "TERMINOLOGY_REGISTRY_INVALID",
            "Reviewed local terminology evidence is unavailable or stale. Ask the maintainer to restore the reviewed registry and matching sources before retrying. No answer was generated.")

    try:
        rag = get_rag_instance(working_dir=STORAGE_DIR, engine=engine, api_key=key,
                               model_name=model_name, base_url=base_url)
        await rag.initialize_storages()
        param = QueryParam(mode=mode, top_k=40, chunk_top_k=20, enable_rerank=False)
        evidence_blocks = []
        for c in hybrid_evidence:
            c_id = c.get("full_doc_id") or c.get("id", "")
            if c.get("evidence_type") == "terminology_mapping":
                c_id = c["id"]
                provenance = {"terminology_resolution": c.get("terminology_resolution"),
                              "supporting_evidence": c.get("supporting_evidence", []),
                              "source_anchors": c.get("source_anchors", [])}
                evidence_blocks.append(f"[{c_id}]\n{c.get('content', '')}\n" + json.dumps(provenance, ensure_ascii=False))
            else:
                evidence_blocks.append(f"[{c_id}]\n{c.get('content', '')}")
        evidence_text = "\n\n".join(evidence_blocks)
        augmented_prompt = (f"{query_str}\n\n[PRIMARY SELECTED EVIDENCE CONTEXT FROM AWS A3.0M/A3.0:2020]:\n"
                            f"{evidence_text}\n\nAnswer only what the supplied evidence supports. "
                            "Retain conditions and uncertainty. Cite the exact supporting source; "
                            "an existing page or element alone does not establish support.")
        if any(c.get("evidence_type") == "terminology_mapping" for c in hybrid_evidence):
            augmented_prompt += ("\nFor reviewed terminology evidence, retain every preferred target and process/sense qualifier. "
                                 "'When used for' is conditional: do not label every use of that spelling nonstandard. "
                                 "For ambiguous_senses explain the supplied standard and conditional senses or request clarification. "
                                 "Cite the supplied source anchors; parser projection spans are local text spans, not PDF geometry.")
        response = await rag.aquery(augmented_prompt, param=param)
        if not isinstance(response, str) or not response.strip():
            raise RuntimeError("No model response")
    except Exception:
        return _query_failure(query_str, "GENERATION_FAILED",
                              "Answer generation is unavailable. No generated answer was returned.")

    citations = extract_citations(response)
    combined_asset_text = f"{query_str}\n{response}\n" + " ".join(c.get("content", "") for c in hybrid_evidence[:3])
    figures, tables = _resolve_display_assets(combined_asset_text)
    result = {"query": query_str, "answer": response, "citations": citations,
              "grounded_claims": extract_grounded_claims(response), "resolved_figures": figures,
              "resolved_tables": tables, "see_also": extract_see_also_terms(response),
              "answer_outcome": "generated", "answer_origin": "generated",
              "answer_assessment": {"status": "UNASSESSED", "validated": False,
                                    "citation_support": "unassessed", "assessment_scope": "none"},
              "epistemic_trace": verify_epistemic_provenance(query_str, response),
              "answer_route": resolve_answer_route(query_str, response).to_dict(),
              "retrieved_evidence": hybrid_evidence,
              "timings_ms": {"total": round((time.perf_counter()-started)*1000, 3)}}
    resolution = next((c["terminology_resolution"] for c in hybrid_evidence if c.get("evidence_type") == "terminology_mapping"), None)
    if resolution is not None:
        result["terminology_resolution"] = resolution
    result = _reject_unresolved_citations(_attach_claim_evidence(result, hybrid_evidence))
    result["timings_ms"]["total"] = round((time.perf_counter()-started)*1000, 3)
    return result

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
    base_url: Optional[str] = None,
    evidence_version: str = "v1",
    v2_reader: str = "extractive"
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
            base_url=base_url,
            evidence_version=evidence_version,
            v2_reader=v2_reader
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
    parser.add_argument("--evidence-version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--v2-reader", choices=["extractive", "local"], default="extractive")
    args = parser.parse_args()

    result = run_query(
        args.query,
        mode=args.mode,
        engine=args.engine,
        api_key=args.api_key,
        model_name=args.model,
        base_url=args.base_url,
        evidence_version=args.evidence_version,
        v2_reader=args.v2_reader
    )

    if result.get("error_code"):
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
