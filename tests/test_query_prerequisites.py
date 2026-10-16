"""Missing-index regressions with no models, database, ingestion or provider calls."""
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def complete_without_await(coroutine):
    """This prerequisite must fail before awaiting any downstream model work."""
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    finally:
        coroutine.close()
    pytest.fail("Missing-index handling unexpectedly awaited downstream work")


def load_module(name, filename, replacements):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, replacements):
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def query_modules(tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail("Missing index must not initialize models or run downstream work")

    cfg = types.ModuleType("src.config")
    for name in ["STORAGE_DIR", "PARSED_FIGURES_DIR", "PARSED_TABLES_DIR"]:
        setattr(cfg, name, tmp_path / name.lower())
    cfg.DEFAULT_ENGINE = "deepseek"
    cfg.EMBEDDING_MODEL = cfg.RERANKER_MODEL = "unused-fixture-model"
    cfg.EMBEDDING_DIM = 1024
    cfg.ENABLE_RERANKER = True
    cfg.DEEPSEEK_API_KEY = cfg.GEMINI_API_KEY = cfg.CUSTOM_API_KEY = ""
    cfg.CUSTOM_BASE_URL = "https://unused.example/v1"
    cfg.CUSTOM_MODEL = "unused"
    embeddings = types.ModuleType("sentence_transformers")
    embeddings.SentenceTransformer = embeddings.CrossEncoder = forbidden
    pre = types.ModuleType("src.pre_retrieval")
    pre.check_early_abstention = lambda query: None
    pre.expand_query = forbidden
    hybrid = load_module("isolated_hybrid", "hybrid_retriever.py", {
        "src.config": cfg, "src.pre_retrieval": pre,
        "sentence_transformers": embeddings, "numpy": types.ModuleType("numpy")})
    hybrid.search_fts_chunks = forbidden
    indexer = types.ModuleType("src.indexer")
    indexer.get_rag_instance = forbidden
    lightrag = types.ModuleType("lightrag")
    lightrag.QueryParam = forbidden
    citations = types.ModuleType("src.citation_checker")
    citations.extract_citations = citations.extract_grounded_claims = forbidden
    verifier = types.ModuleType("src.epistemic_verifier")
    verifier.verify_epistemic_provenance = forbidden
    routes = types.ModuleType("src.answer_routes")
    routes.resolve_answer_route = forbidden
    grounded = types.ModuleType("src.grounded_answer")
    grounded.compose_grounded_answer = lambda *args: None
    grounded.project_reviewed_facts = forbidden
    query = load_module("isolated_query", "query.py", {
        "src.config": cfg, "src.pre_retrieval": pre,
        "src.hybrid_retriever": hybrid, "src.indexer": indexer,
        "lightrag": lightrag, "src.citation_checker": citations,
        "src.epistemic_verifier": verifier, "src.answer_routes": routes, "src.grounded_answer": grounded})
    return query, hybrid


def test_missing_store_has_specific_exception(query_modules):
    _, hybrid = query_modules
    with pytest.raises(hybrid.ContextualIndexMissingError):
        hybrid.get_vdb_data()


def test_missing_store_returns_actionable_failure_before_retrieval_or_models(query_modules):
    query, _ = query_modules
    result = complete_without_await(query.async_query("Define a weld bead", api_key="fake-fixture-key"))
    assert result["error_code"] == "RETRIEVAL_INDEX_MISSING"
    assert "storage/vdb_chunks_contextual.json" in result["error"]
    assert "restore" in result["error"].lower()
    assert result["answer"] == ""
    assert result["citations"] == {}
    for key in ["grounded_claims", "retrieved_evidence", "resolved_figures", "resolved_tables", "see_also"]:
        assert result[key] == []
    assert "epistemic_trace" not in result
    assert "answer_route" not in result


def test_unrelated_missing_file_is_not_mislabeled(query_modules, monkeypatch):
    query, _ = query_modules
    def unrelated(*args, **kwargs):
        raise FileNotFoundError("unrelated fixture")
    monkeypatch.setattr(query, "hybrid_retrieve", unrelated)
    with pytest.raises(FileNotFoundError, match="unrelated fixture"):
        complete_without_await(query.async_query("Define a weld bead", api_key="fake-fixture-key"))


def test_corrupt_store_is_not_mislabeled_as_missing(query_modules):
    _, hybrid = query_modules
    hybrid.CONTEXTUAL_VDB_PATH.parent.mkdir()
    hybrid.CONTEXTUAL_VDB_PATH.write_text("{invalid", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        hybrid.get_vdb_data()


def test_cli_reports_missing_index_and_exits_nonzero(query_modules, monkeypatch, capsys):
    query, _ = query_modules
    result = complete_without_await(query.async_query("Define a weld bead", api_key="fake-fixture-key"))
    monkeypatch.setattr(query, "run_query", lambda *args, **kwargs: result)
    monkeypatch.setattr(sys, "argv", ["query.py", "Define a weld bead"])
    with pytest.raises(SystemExit) as stopped:
        query.main()
    assert stopped.value.code == 1
    output = capsys.readouterr()
    assert "storage/vdb_chunks_contextual.json" in output.err
    assert "ANSWER:" not in output.out
