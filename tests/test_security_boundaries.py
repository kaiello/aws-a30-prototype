"""Isolated security regressions: no model, database, listener or network calls."""

import asyncio
import importlib.util
import io
import json
import os
import sys
import types
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename, replacements):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, replacements):
        spec.loader.exec_module(module)
    return module


def fake_config(tmp_path):
    cfg = types.ModuleType("src.config")
    for name in ["BASE_DIR", "STORAGE_DIR", "PARSED_FIGURES_DIR", "PARSED_TABLES_DIR"]:
        setattr(cfg, name, tmp_path / name.lower())
        getattr(cfg, name).mkdir()
    cfg.PARSED_TEXT_FILE = tmp_path / "text.jsonl"
    cfg.DEFAULT_ENGINE = "deepseek"
    cfg.EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
    cfg.EMBEDDING_DIM = 1024
    cfg.ALLOWED_WEB_ORIGINS = ()
    for provider, url in [("DEEPSEEK", "https://api.deepseek.com"),
                          ("GEMINI", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                          ("CUSTOM", "http://localhost:11434/v1")]:
        setattr(cfg, provider + "_BASE_URL", url)
        setattr(cfg, provider + "_API_KEY", "fake-server-key")
        setattr(cfg, provider + "_MODEL", "fake-model")
    return cfg


@pytest.fixture
def web_fixture(tmp_path):
    cfg = fake_config(tmp_path)
    (cfg.PARSED_FIGURES_DIR / "Figure_test.png").write_bytes(b"test-image")
    (cfg.PARSED_TABLES_DIR / "table_a1.md").write_text("test-table", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("private-test-value", encoding="utf-8")
    calls = []
    query = types.ModuleType("src.query")

    def run_query(text, **kwargs):
        calls.append((text, kwargs))
        return {"answer": "fake answer", "citations": {}, "resolved_figures": [], "resolved_tables": []}

    query.run_query = run_query
    query.resolve_multimodal_assets = lambda text: ([], [])
    figures = types.ModuleType("src.figure_inspectors")
    figures.FIGURE_INSPECTORS = {}
    figures.FIGURE_CATEGORIES = []
    figures.get_all_figures_catalog = lambda: []
    figures.get_inspector_html = lambda key: ""
    figures.get_figure_data = lambda key: {}
    web = load_module("isolated_web", "web.py", {"src.config": cfg, "src.query": query,
                                                "src.figure_inspectors": figures})
    server = types.SimpleNamespace(server_address=("127.0.0.1", 8000), allowed_origins=())
    if hasattr(web, "AssetStore"):
        server.asset_stores = {"figures": web.AssetStore(cfg.PARSED_FIGURES_DIR, {".png"}),
                               "tables": web.AssetStore(cfg.PARSED_TABLES_DIR, {".png", ".md"})}
    return web, cfg, server, calls


def request(fixture, path, method="GET", body=None, headers=None, extra_headers=()):
    web, _, server, _ = fixture
    handler = web.MultimodalRequestHandler.__new__(web.MultimodalRequestHandler)
    payload = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
    handler.server = server
    handler.client_address = ("127.0.0.1", 12345)
    handler.command = method
    handler.path = path
    handler.requestline = method + " " + path + " HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.close_connection = True
    handler.headers = Message()
    for key, value in {"Host": "localhost:8000", "Content-Type": "application/json",
                       "Content-Length": str(len(payload)), **(headers or {})}.items():
        if value is not None:
            handler.headers[key] = value
    for key, value in extra_headers:
        handler.headers[key] = value
    handler.rfile = io.BytesIO(payload)
    handler.wfile = io.BytesIO()
    handler.log_message = lambda *args: None
    getattr(handler, "do_" + method)()
    raw = handler.wfile.getvalue()
    head, _, data = raw.partition(b"\r\n\r\n")
    return int(head.split(b" ")[1]), head.decode(), data


def test_legitimate_assets_and_query_shape(web_fixture):
    assert request(web_fixture, "/figures/Figure_test.png")[2] == b"test-image"
    assert request(web_fixture, "/tables/table_a1.md")[2] == b"test-table"
    status, _, body = request(web_fixture, "/api/query", "POST", {"query": "Define a weld"})
    assert status == 200
    assert json.loads(body)["answer"] == "fake answer"


@pytest.mark.parametrize("path", [
    "/tables/../secret.txt", "/tables/../../secret.txt", "/figures/../secret.txt",
    "/tables/%2e%2e%2fsecret.txt", "/tables/%252e%252e%255csecret.txt",
    "/tables/..\\secret.txt", "/tables/C:%5csecret.txt", "/tables/table_a1.md:secret",
    "/tables/table_a1.md.", "/tables/table_a1.md%20", "/tables/%00table_a1.md",
    "/tables/%GG", "/tables/newly_added.md",
    "/tables/%2525252525252525252e%2525252525252525252e%2525252525252525252fsecret.txt",
    "/tables/%ff", "/tables/table_a1.md%3Astream", "/tables/%5c%5cserver%5cshare",
])
def test_asset_escape_and_nonallowlisted_names_are_rejected(web_fixture, path):
    _, cfg, _, _ = web_fixture
    (cfg.PARSED_TABLES_DIR / "newly_added.md").write_text("not-in-startup-catalog")
    status, _, data = request(web_fixture, path)
    assert status in (400, 403, 404)
    assert b"private-test-value" not in data
    assert b"not-in-startup-catalog" not in data


def test_allowed_asset_replaced_with_outside_link_is_rejected(web_fixture, tmp_path):
    _, cfg, _, _ = web_fixture
    asset = cfg.PARSED_TABLES_DIR / "table_a1.md"
    asset.unlink()
    # Hardlinks work without Windows developer-mode privileges and must not expose private files.
    os.link(tmp_path / "secret.txt", asset)
    status, _, data = request(web_fixture, "/tables/table_a1.md")
    assert status in (403, 404)
    assert b"private-test-value" not in data


def test_resolved_symlink_or_junction_escape_is_rejected_before_open(web_fixture, tmp_path, monkeypatch):
    _, cfg, _, _ = web_fixture
    asset = cfg.PARSED_TABLES_DIR / "table_a1.md"
    real_resolve = Path.resolve

    def redirected(path, *args, **kwargs):
        return tmp_path / "secret.txt" if path == asset else real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", redirected)
    status, _, data = request(web_fixture, "/tables/table_a1.md")
    assert status in (403, 404)
    assert b"private-test-value" not in data


def test_percent_encoded_approved_basename_remains_supported(web_fixture):
    assert request(web_fixture, "/figures/%46igure_test.png")[2] == b"test-image"


@pytest.mark.parametrize("headers", [
    {"Host": "attacker.example:8000"}, {"Host": "localhost:9000"},
    {"Origin": "https://attacker.example"}, {"Origin": "null"},
    {"Origin": "http://localhost:8000.attacker.example"},
    {"Sec-Fetch-Site": "cross-site"}, {"Content-Type": "text/plain"},
    {"Origin": "http://localhost:9000", "Sec-Fetch-Site": "same-site"},
    {"Transfer-Encoding": "chunked"},
])
def test_untrusted_requests_do_not_reach_query(web_fixture, headers):
    status, _, _ = request(web_fixture, "/api/query", "POST", {"query": "private question"}, headers)
    assert status in (400, 403, 415)
    assert web_fixture[3] == []


def test_same_origin_and_explicit_production_origin_remain_supported(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {"query": "Define a weld"},
                   {"Origin": "http://localhost:8000"})[0] == 200
    web_fixture[2].allowed_origins = ("https://production.example",)
    status, headers, _ = request(web_fixture, "/api/query", "POST", {"query": "Define a weld"},
                                 {"Origin": "https://production.example", "Sec-Fetch-Site": "cross-site"})
    assert status == 200
    assert "Access-Control-Allow-Origin: https://production.example" in headers


@pytest.mark.parametrize("header", [("Host", "attacker.example:8000"),
                                   ("Origin", "https://attacker.example"),
                                   ("Content-Length", "1"), ("Content-Type", "text/plain")])
def test_duplicate_security_headers_are_rejected(web_fixture, header):
    status, _, _ = request(web_fixture, "/api/query", "POST", {"query": "test"}, extra_headers=[header])
    assert status in (400, 403, 415)
    assert web_fixture[3] == []


def test_forwarded_host_does_not_change_local_authority(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {"query": "test"},
                   {"X-Forwarded-Host": "attacker.example", "Forwarded": "host=attacker.example"})[0] == 200


def test_oversized_request_is_rejected_before_read_or_query(web_fixture):
    status, _, _ = request(web_fixture, "/api/query", "POST", {"query": "test"},
                           {"Content-Length": "1000000"})
    assert status == 413
    assert web_fixture[3] == []


def test_missing_content_length_is_rejected(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {"query": "test"}, {"Content-Length": None})[0] == 400
    assert web_fixture[3] == []


@pytest.mark.parametrize("size,status", [(16384, 200), (16385, 400)])
def test_query_character_limit(web_fixture, size, status):
    assert request(web_fixture, "/api/query", "POST", {"query": "a" * size})[0] == status


def test_multibyte_json_length_is_measured_in_bytes(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {"query": "weld \u03b1 \u6f22"})[0] == 200


@pytest.mark.parametrize("engine", ["deepseek", "gemini", "custom", "openai"])
def test_default_engine_endpoints_are_preserved(web_fixture, engine):
    assert request(web_fixture, "/api/query", "POST", {"query": "test", "engine": engine})[0] == 200


def test_approved_production_origin_preflight(web_fixture):
    web_fixture[2].allowed_origins = ("https://production.example",)
    status, headers, _ = request(web_fixture, "/api/query", "OPTIONS", headers={
        "Origin": "https://production.example", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert status == 204
    assert "Access-Control-Allow-Origin: https://production.example" in headers


@pytest.mark.parametrize("url", ["https://attacker.example/v1", "https://api.deepseek.com.attacker.example",
                                "https://api.deepseek.com/other", "https://api.deepseek.com?redirect=x",
                                "https://user@api.deepseek.com", "http://api.deepseek.com"])
def test_request_endpoint_override_rejected_before_retrieval(web_fixture, url):
    status, _, data = request(web_fixture, "/api/query", "POST", {"query": "private question", "base_url": url})
    assert status == 400
    assert web_fixture[3] == []
    assert b"fake-server-key" not in data


def test_matching_endpoint_and_current_defaults_are_preserved(web_fixture):
    status, _, _ = request(web_fixture, "/api/query", "POST", {
        "query": "Define a weld", "engine": "deepseek", "base_url": "https://api.deepseek.com/"})
    assert status == 200
    _, kwargs = web_fixture[3][0]
    assert kwargs["engine"] == "deepseek"
    assert kwargs["api_key"] is None


@pytest.fixture
def indexer_fixture(tmp_path):
    cfg = fake_config(tmp_path)
    clients = []
    model_loads = []
    openai = types.ModuleType("openai")
    openai.AsyncOpenAI = lambda **kw: clients.append(kw) or types.SimpleNamespace()
    embeddings = types.ModuleType("sentence_transformers")
    embeddings.SentenceTransformer = lambda name: model_loads.append(name) or types.SimpleNamespace()
    lightrag = types.ModuleType("lightrag")
    lightrag.LightRAG = lambda **kw: types.SimpleNamespace(**kw)
    utils = types.ModuleType("lightrag.utils")
    utils.EmbeddingFunc = lambda **kw: kw
    httpx = types.ModuleType("httpx")
    httpx.AsyncClient = lambda **kw: types.SimpleNamespace(settings=kw)
    indexer = load_module("isolated_indexer", "indexer.py", {
        "src.config": cfg, "openai": openai, "sentence_transformers": embeddings,
        "lightrag": lightrag, "lightrag.utils": utils, "httpx": httpx})
    return indexer, cfg, clients, model_loads


@pytest.mark.parametrize("engine,url", [("deepseek", "https://attacker.example/v1"),
                                        ("gemini", "https://api.deepseek.com"),
                                        ("custom", "http://127.0.0.1:9999/v1")])
def test_direct_model_client_rejects_unapproved_endpoint_before_model_load(indexer_fixture, engine, url):
    indexer, cfg, clients, models = indexer_fixture
    with pytest.raises(ValueError):
        indexer.get_rag_instance(working_dir=cfg.STORAGE_DIR, engine=engine, base_url=url)
    assert clients == []
    assert models == []


def test_trusted_model_client_preserves_bge_and_blocks_redirects_and_proxies(indexer_fixture):
    indexer, cfg, clients, models = indexer_fixture
    rag = indexer.get_rag_instance(working_dir=cfg.STORAGE_DIR)
    assert models == ["BAAI/bge-large-en-v1.5"]
    assert rag.embedding_func["embedding_dim"] == 1024
    assert clients[0]["api_key"] == "fake-server-key"
    transport = clients[0]["http_client"]
    assert transport.settings["follow_redirects"] is False
    assert transport.settings["trust_env"] is False


@pytest.mark.parametrize("url", ["https://api.deepseek.com/v1/../", "https://api.deepseek.com/%2f",
                                "https://api.deepseek.com\\@attacker.example", "https://api.deepseek.com/#x",
                                "https://api.deepseek.com:bad", " https://api.deepseek.com"])
def test_ambiguous_model_urls_are_rejected(indexer_fixture, url):
    indexer, cfg, clients, models = indexer_fixture
    with pytest.raises(ValueError):
        indexer.get_rag_instance(working_dir=cfg.STORAGE_DIR, base_url=url)
    assert clients == []
    assert models == []


def test_real_sdk_does_not_follow_provider_redirect(tmp_path, monkeypatch):
    """Use the installed SDK with an in-memory transport, never a real socket."""
    import httpx
    import openai

    cfg = fake_config(tmp_path)
    requests = []
    transports = []
    original_client = httpx.AsyncClient

    def respond(request):
        requests.append(request)
        return httpx.Response(307, headers={"Location": "https://unapproved.example/v1/chat/completions"})

    class IsolatedClient(original_client):
        def __init__(self, **kwargs):
            super().__init__(transport=httpx.MockTransport(respond), **kwargs)
            transports.append(self)

    monkeypatch.setattr(httpx, "AsyncClient", IsolatedClient)
    monkeypatch.setenv("HTTPS_PROXY", "http://unapproved.example:3128")
    embedding = types.ModuleType("sentence_transformers")
    embedding.SentenceTransformer = lambda name: object()
    lightrag = types.ModuleType("lightrag")
    lightrag.LightRAG = lambda **kwargs: types.SimpleNamespace(**kwargs)
    utils = types.ModuleType("lightrag.utils")
    utils.EmbeddingFunc = lambda **kwargs: kwargs
    indexer = load_module("isolated_sdk_indexer", "indexer.py", {
        "src.config": cfg, "sentence_transformers": embedding,
        "lightrag": lightrag, "lightrag.utils": utils})

    async def exercise():
        rag = indexer.get_rag_instance(working_dir=cfg.STORAGE_DIR)
        try:
            with pytest.raises(openai.APIStatusError):
                await rag.llm_model_func("test fixture only")
        finally:
            for transport in transports:
                await transport.aclose()

    asyncio.run(exercise())
    assert len(requests) == 1
    assert requests[0].url.host == "api.deepseek.com"
    assert requests[0].headers["authorization"] == "Bearer fake-server-key"
    assert transports[0].follow_redirects is False
    assert transports[0]._trust_env is False
