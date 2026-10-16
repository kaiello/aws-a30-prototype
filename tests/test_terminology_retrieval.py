"""Bounded terminology wiring contracts; injected models/search, no live stores."""
import ast
import asyncio
import hashlib
import json
import time
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def actual_function(path, name, namespace):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    node = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    helpers = [item for item in tree.body if path == "src/query.py" and isinstance(item, ast.FunctionDef) and item.name in {"_query_failure", "_scope_decision", "_reviewed_trace", "_attach_claim_evidence", "_resolve_display_assets", "_reject_unresolved_citations"}]
    exec(compile(ast.Module(body=helpers + [node], type_ignores=[]), path, "exec"), namespace)
    return namespace[name]


def bundle():
    records = [{"mapping_id": "mapping:fixture-a", "preferred_term": "target alpha", "qualification": "when used for"},
               {"mapping_id": "mapping:fixture-b", "preferred_term": "target beta", "qualification": "when used for"}]
    return {"id": "terminology:fixture-entry", "full_doc_id": "terminology:fixture-entry", "evidence_type": "terminology_mapping",
            "content": "Reviewed source: legacy term refers to target alpha or target beta.",
            "mapping_ids": [record["mapping_id"] for record in records], "terminology_mappings": records,
            "source_anchors": [{"source_id": "doc:synthetic", "source_sha256": "a" * 64,
                                "element_id": "clause:synthetic", "pdf_index": 25, "printed_label": "13"}],
            "supporting_evidence": [{"id": "existing_chunk_13", "full_doc_id": "existing_doc_13",
                                     "content": "Reviewed source facts.",
                                     "content_sha256": "b" * 64, "excerpt_sha256": "c" * 64,
                                     "source_anchors": [{"document_id": "doc:synthetic", "source_sha256": "a" * 64,
                                                         "section_id": "clause:synthetic", "pdf_index": 25, "printed_label": "13"}],
                                     "verification_state": "verified"}],
            "terminology_resolution": {"status": "ambiguous_senses", "matched_terms": ["legacy term"],
                                       "preferred_terms": ["target alpha", "target beta"], "target_ids": [],
                                       "source_entry_ids": ["fixture-entry"], "records": records,
                                       "mapping_ids": [record["mapping_id"] for record in records]},
            "selection_method": "reviewed_terminology_lookup"}


def hybrid_namespace(selected, *, missing=False):
    base = [{"id": "base-a", "full_doc_id": "base-document-a", "content": "Synthetic A", "score": .9},
            {"id": "base-b", "full_doc_id": "base-document-b", "content": "Synthetic B", "score": .8}]
    calls = []
    class MissingIndex(FileNotFoundError):
        pass
    def data():
        if missing:
            raise MissingIndex("fixture index missing")
        return {}
    def lookup(query):
        calls.append(query)
        return deepcopy(selected)
    namespace = {"List": list, "Dict": dict, "Any": object,
                 "get_vdb_data": data, "expand_query": lambda query: {"enriched_query": query},
                 "search_fts_chunks": lambda *args, **kwargs: [], "search_dense_chunks": lambda *args, **kwargs: [],
                 "reciprocal_rank_fusion": lambda *args, **kwargs: deepcopy(base),
                 "rerank_candidates": lambda query, candidates, top_k: candidates[:top_k],
                 "get_terminology_evidence": lookup}
    return actual_function("src/hybrid_retriever.py", "hybrid_retrieve", namespace), base, calls, MissingIndex


def test_live_hybrid_includes_all_mapping_targets_in_one_bounded_bundle():
    retrieve, base, calls, _ = hybrid_namespace(bundle())
    result = retrieve("legacy term", top_k=2)
    assert [row["id"] for row in result] == ["terminology:fixture-entry", "base-a"]
    assert [record["preferred_term"] for record in result[0]["terminology_mappings"]] == ["target alpha", "target beta"]
    assert result[1] == base[0]
    assert calls == ["legacy term"]
    assert not any(field in result[0] for field in ("score", "rrf_score", "cross_encoder_score"))


def test_top_one_cannot_drop_second_target_or_ambiguity_metadata():
    retrieve, _, _, _ = hybrid_namespace(bundle())
    result = retrieve("legacy term", top_k=1)
    assert len(result) == 1
    assert result[0]["id"] == "terminology:fixture-entry"
    assert len(result[0]["mapping_ids"]) == 2
    assert result[0]["terminology_resolution"]["status"] == "ambiguous_senses"


def test_unrelated_hybrid_hits_keep_existing_order_scores_and_shape():
    retrieve, base, _, _ = hybrid_namespace(None)
    assert retrieve("unrelated query", top_k=2) == base


def test_missing_index_precedes_terminology_or_model_work():
    retrieve, _, calls, error = hybrid_namespace(bundle(), missing=True)
    with pytest.raises(error):
        retrieve("legacy term")
    assert calls == []


def query_namespace(evidence):
    prompts = []
    class Rag:
        async def initialize_storages(self):
            pass
        async def aquery(self, prompt, param):
            prompts.append(prompt)
            return "Synthetic answer."
    namespace = {"Optional": object, "DEFAULT_ENGINE": "custom", "CUSTOM_API_KEY": "",
                 "GEMINI_API_KEY": "", "DEEPSEEK_API_KEY": "", "STORAGE_DIR": Path("fixture-no-store"),
                 "check_early_abstention": lambda query: None,
                 "get_terminology_evidence": lambda query: None, "compose_grounded_answer": lambda *args: None,
                 "time": time, "hashlib": hashlib,
                 "hybrid_retrieve": lambda *args, **kwargs: deepcopy(evidence),
                 "ContextualIndexMissingError": FileNotFoundError,
                 "get_rag_instance": lambda **kwargs: Rag(), "QueryParam": lambda **kwargs: kwargs,
                 "extract_citations": lambda text: {}, "extract_grounded_claims": lambda text: [],
                 "extract_reference_records": lambda text: [],
                 "qualify_reference_hierarchy": lambda text, mentions: {"mentions": mentions, "diagnostics": []},
                 "resolve_multimodal_assets": lambda text: ([], []), "extract_see_also_terms": lambda text: [],
                 "verify_epistemic_provenance": lambda *args: {},
                 "resolve_answer_route": lambda *args: SimpleNamespace(to_dict=lambda: {}), "json": json}
    # Compile annotations using real Optional; all application boundaries above stay injected.
    from typing import Optional
    from src.terminology_retrieval import TerminologyRegistryError
    namespace["Optional"] = Optional
    namespace["TerminologyRegistryError"] = TerminologyRegistryError
    return actual_function("src/query.py", "async_query", namespace), prompts


def test_generation_receives_unique_mapping_ids_and_qualified_source_provenance():
    selected = bundle()
    query, prompts = query_namespace([selected])
    result = asyncio.run(query("legacy term", engine="custom", api_key="synthetic-unused-key"))
    assert len(prompts) == 1
    for required in [selected["id"], "mapping:fixture-a", "mapping:fixture-b", "when used for", "a" * 64,
                     "existing_chunk_13", "Reviewed source facts."]:
        assert required in prompts[0]
    assert result["retrieved_evidence"] == [selected]
    assert result["terminology_resolution"] == selected["terminology_resolution"]


def test_unrelated_query_generation_keeps_legacy_context_and_no_new_metadata():
    evidence = [{"id": "base-a", "full_doc_id": "legacy-doc", "content": "Synthetic A"}]
    query, prompts = query_namespace(evidence)
    result = asyncio.run(query("unrelated query", engine="custom", api_key="synthetic-unused-key"))
    assert "[legacy-doc]\nSynthetic A" in prompts[0]
    assert "terminology_resolution" not in result
    assert result["retrieved_evidence"] == evidence


class SyntheticManifest:
    document = {"id": "doc:synthetic", "sha256": "a" * 64}
    def resolve(self, label):
        return {"status": "exact" if label == "clause:synthetic" else "unknown"}
    def anchors(self, label):
        return [{"pdf_index": 25, "printed_label": "13"}] if label == "clause:synthetic" else []


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def reviewed_registry(tmp_path):
    rows, entries = [], []
    for term, target_text, name in [("burn-through weld", "target alpha; target beta", "weld"),
                                    ("burn-through", "target conditional", "conditional"),
                                    ("root gap", "target gamma", "gap")]:
        conditional = name == "conditional"
        definition = "A nonstandard term " + ("when used for " if conditional else "for ") + target_text + "."
        projection_text = term + ". " + definition
        original = projection_text + (" Standard sense remains a separate use." if conditional else "")
        anchor = {"section_id": "clause:synthetic", "pdf_index": 25, "printed_label": "13"}
        source = dict(anchor, document_id="doc:synthetic", source_sha256="a" * 64,
                      record_id="projection:" + name, span=[0, len(projection_text)], text=projection_text,
                      verification_state="verified")
        nodes = [{"id": "onto:" + name, "name": term, "sense": "", "process_context": "", "verification_state": "verified"}]
        nodes += [{"id": "onto:" + target.replace(" ", "_"), "name": target, "sense": "",
                   "process_context": "", "verification_state": "verified"} for target in target_text.split("; ")]
        rows.append({"id": "existing:" + name, "full_doc_id": "existing_doc:" + name, "content": original})
        value = {"entry_id": "entry:" + name, "term": term, "sense": "", "process_context": "",
                 "original_entry": dict(anchor, text=original, verification_state="verified"),
                 "parser_entry": {"term": term, "definition": definition, "sense": "", "process_context": "",
                                  "source_id": "onto:" + name, "source": source},
                 "projection": {"kind": "reviewed_parser_projection", "source_entry_id": "entry:" + name,
                                "is_raw_pdf_span": False, "note": "Synthetic local parser projection."},
                 "ontology_bindings": nodes,
                 "evidence_members": [dict(anchor, id="existing:" + name, full_doc_id="existing_doc:" + name,
                                           source_file="storage/vdb_chunks_contextual.json", content_sha256=digest(original),
                                           excerpt=original, excerpt_sha256=digest(original),
                                           supports=["mapping"], verification_state="verified")]}
        if conditional:
            value["standard_sense"] = {"text": "Standard sense remains a separate use.",
                                       "evidence_member_ids": ["existing:" + name]}
        entries.append(value)
    source_path = tmp_path / "storage/vdb_chunks_contextual.json"
    source_path.parent.mkdir()
    source_path.write_text(json.dumps({"data": rows}), encoding="utf-8")
    registry = {"schema_version": "1.0.0", "document_id": "doc:synthetic", "source_sha256": "a" * 64,
                "source_files": [{"relpath": "storage/vdb_chunks_contextual.json",
                                  "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest()}], "entries": entries}
    path = tmp_path / "storage/terminology_registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return tmp_path, path, registry


def lookup_fixture(fixture, query):
    from src.terminology_retrieval import get_terminology_evidence
    root, path, _ = fixture
    return get_terminology_evidence(query, root=root, registry_path=path, manifest=SyntheticManifest())


def test_longest_whole_term_selection_does_not_select_shorter_conditional_sense(reviewed_registry):
    result = lookup_fixture(reviewed_registry, "Define BURN-THROUGH   WELD.")
    resolution = result["terminology_resolution"]
    assert resolution["matched_terms"] == ["burn-through weld"]
    assert resolution["preferred_terms"] == ["target alpha", "target beta"]
    assert resolution["status"] == "mapped"
    assert len(result["mapping_ids"]) == 2
    assert result["supporting_evidence"][0]["id"] == "existing:weld"
    assert result["supporting_evidence"][0]["content"]
    assert result["supporting_evidence"][0]["source_anchors"][0]["printed_label"] == "13"


def test_unqualified_conditional_term_preserves_both_senses_and_qualifier(reviewed_registry):
    result = lookup_fixture(reviewed_registry, "What does burn-through mean?")
    assert result["terminology_resolution"]["status"] == "ambiguous_senses"
    assert "Standard sense remains a separate use." in result["content"]
    assert result["terminology_resolution"]["records"][0]["qualification"] == "when used for"
    assert "target conditional" in result["content"]


def test_explicit_nonstandard_intent_is_qualified_not_global_status_rewrite(reviewed_registry):
    result = lookup_fixture(reviewed_registry, "Explain the nonstandard use of burn-through for target conditional.")
    assert result["terminology_resolution"]["status"] == "qualified_mapping"
    assert result["terminology_resolution"]["records"][0]["qualification"] == "when used for"


def test_unrelated_query_does_not_read_missing_registry_or_match_prefix(tmp_path):
    from src.terminology_retrieval import get_terminology_evidence
    assert get_terminology_evidence("Explain root gapless geometry", root=tmp_path,
                                    registry_path=tmp_path / "missing.json", manifest=SyntheticManifest()) is None


@pytest.mark.parametrize("mutation", ["stale-document", "unknown-member", "wrong-excerpt", "unverified-binding", "raw-span-claim"])
def test_relevant_registry_validation_fails_closed_without_source_content_in_errors(reviewed_registry, mutation):
    from src.terminology_retrieval import TerminologyRegistryError
    _, path, registry = reviewed_registry
    value = registry["entries"][0]
    if mutation == "stale-document":
        registry["source_sha256"] = "b" * 64
    elif mutation == "unknown-member":
        value["evidence_members"][0]["id"] = "invented:missing"
    elif mutation == "wrong-excerpt":
        value["evidence_members"][0]["excerpt"] = "Source facts that were never supplied."
        value["evidence_members"][0]["excerpt_sha256"] = digest(value["evidence_members"][0]["excerpt"])
    elif mutation == "unverified-binding":
        value["ontology_bindings"][0]["verification_state"] = "candidate"
    else:
        value["projection"]["is_raw_pdf_span"] = True
    path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(TerminologyRegistryError) as caught:
        lookup_fixture(reviewed_registry, "burn-through weld")
    assert "target alpha" not in str(caught.value)
    assert "Source facts" not in str(caught.value)


def test_changed_cached_source_hash_rejects_relevant_lookup(reviewed_registry):
    from src.terminology_retrieval import TerminologyRegistryError
    root, _, _ = reviewed_registry
    with (root / "storage/vdb_chunks_contextual.json").open("a", encoding="utf-8") as stream:
        stream.write(" ")
    with pytest.raises(TerminologyRegistryError):
        lookup_fixture(reviewed_registry, "root gap")


@pytest.mark.parametrize("query", ["Define BURN–THROUGH WELD.", "Define burn—through weld.", "Define burn‑through weld."])
def test_unicode_dash_headword_spelling_selects_same_complete_mapping(reviewed_registry, query):
    result = lookup_fixture(reviewed_registry, query)
    assert result["terminology_resolution"]["matched_terms"] == ["burn-through weld"]
    assert result["terminology_resolution"]["preferred_terms"] == ["target alpha", "target beta"]


@pytest.mark.parametrize("query", ["burn-through-welded", "burn–through–welded", "burn‑through‑welded"])
def test_hyphenated_word_suffix_remains_unrelated_without_registry_io(tmp_path, query):
    from src.terminology_retrieval import get_terminology_evidence
    assert get_terminology_evidence(query, root=tmp_path, registry_path=tmp_path / "missing.json",
                                    manifest=SyntheticManifest()) is None


@pytest.mark.parametrize("query", [
    "Explain the standard sense of burn-through and the nonstandard use of root gap",
    "Is burn-through not nonstandard?",
    "Is burn-through standard or nonstandard?",
    "Explain burn-through, not the nonstandard meaning.",
    "Describe burn-through beside target conditionality.",
])
def test_conditional_intent_remains_ambiguous_when_mixed_negated_or_unclear(reviewed_registry, query):
    result = lookup_fixture(reviewed_registry, query)
    assert result["terminology_resolution"]["status"] == "ambiguous_senses"
    assert "Standard sense remains a separate use." in result["content"]
    conditional = next(record for record in result["terminology_resolution"]["records"]
                       if record["nonstandard_term"] == "burn-through")
    assert conditional["qualification"] == "when used for"


def test_invalid_terminology_registry_returns_source_free_error_before_rag_initialization():
    query, prompts = query_namespace([])
    calls = []
    class RegistryFailure(RuntimeError):
        code = "TERMINOLOGY_REGISTRY_INVALID"
    def lookup(*args, **kwargs):
        raise RegistryFailure("Licensed source details must never enter the response.")
    def forbidden(**kwargs):
        calls.append(kwargs)
        pytest.fail("Invalid registry must fail before RAG/model initialization")
    query.__globals__["TerminologyRegistryError"] = RegistryFailure
    query.__globals__["hybrid_retrieve"] = lookup
    query.__globals__["get_rag_instance"] = forbidden
    result = asyncio.run(query("burn-through", engine="custom", api_key="synthetic-unused-key"))
    assert result["error_code"] == "TERMINOLOGY_REGISTRY_INVALID"
    assert result["answer"] == ""
    assert result["retrieved_evidence"] == []
    assert "Licensed source details" not in json.dumps(result)
    assert calls == [] and prompts == []



def test_invalid_registry_precedes_expansion_search_and_embedding_work():
    retrieve, _, _, _ = hybrid_namespace(None)
    work = []
    class RegistryFailure(RuntimeError):
        pass
    def invalid(query):
        raise RegistryFailure("Synthetic registry failure")
    def forbidden(*args, **kwargs):
        work.append("unexpected retrieval work")
        pytest.fail("Registry validation must precede expansion/search/model work")
    retrieve.__globals__["get_terminology_evidence"] = invalid
    for name in ["expand_query", "search_fts_chunks", "search_dense_chunks", "rerank_candidates"]:
        retrieve.__globals__[name] = forbidden
    with pytest.raises(RegistryFailure):
        retrieve("burn-through")
    assert work == []



def test_top_zero_preserves_empty_result_without_terminology_lookup():
    retrieve, _, calls, _ = hybrid_namespace(bundle())
    assert retrieve("burn-through", top_k=0) == []
    assert calls == []


@pytest.mark.parametrize("query", [
    "Explain why burn-through has no nonstandard meaning",
    "Burn-through isn’t nonstandard",
    "burn-through cannot be nonstandard",
])
def test_conditional_intent_preserves_ambiguity_for_additional_negation_forms(reviewed_registry, query):
    result = lookup_fixture(reviewed_registry, query)
    assert result["terminology_resolution"]["status"] == "ambiguous_senses"
    assert "Standard sense remains a separate use." in result["content"]
