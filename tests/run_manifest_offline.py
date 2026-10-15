"""Run bounded offline regressions. Refuse model, provider and database access.

Usage: python -B tests/run_manifest_offline.py
Dependencies must already be installed. No ingestion or service is started.
"""
import os
import inspect
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import types


def main():
    ROOT = Path(__file__).resolve().parents[1]
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

    def forbidden(*args, **kwargs):
        raise AssertionError("External/model/database access forbidden in manifest checks")

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: False
    sys.modules["dotenv"] = dotenv
    embeddings = types.ModuleType("sentence_transformers")
    embeddings.SentenceTransformer = forbidden
    embeddings.CrossEncoder = forbidden
    sys.modules["sentence_transformers"] = embeddings
    lightrag = types.ModuleType("lightrag")
    lightrag.QueryParam = forbidden
    sys.modules["lightrag"] = lightrag
    indexer = types.ModuleType("src.indexer")
    indexer.get_rag_instance = forbidden
    sys.modules["src.indexer"] = indexer
    sqlite3.connect = forbidden
    original_connect = socket.socket.connect
    def guarded_connect(sock, address):
        caller = inspect.currentframe().f_back
        # Windows asyncio implements its private wakeup socketpair using loopback.
        if (caller.f_code.co_name == "_fallback_socketpair"
                and caller.f_globals.get("__name__") == "socket"
                and address[0] in {"127.0.0.1", "::1"}):
            return original_connect(sock, address)
        return forbidden()
    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = forbidden
    socket.create_connection = forbidden

    import src.pre_retrieval as pre_retrieval
    scratch = Path(tempfile.mkdtemp(prefix="aws-a30-manifest-checks-"))
    pre_retrieval.DUAL_SQLITE_PATH = scratch / "absent.db"

    import pytest
    raise SystemExit(pytest.main([
        "-q", "-p", "no:cacheprovider", "--tb=short", "--basetemp=" + str(scratch),
        "tests/test_security_boundaries.py", "tests/test_pre_retrieval.py",
        "tests/test_query_prerequisites.py",
        "tests/test_figure_bboxes.py",
        "tests/test_hybrid_retrieval.py::test_reciprocal_rank_fusion",
        "tests/test_standard_manifest.py", "tests/test_manifest_citations.py", "tests/test_manifest_assets.py",
        "tests/test_manifest_metadata.py", "tests/test_manifest_retrieval_contract.py",
        "tests/test_terminology_mappings.py",
        "tests/test_terminology_retrieval.py", "tests/test_terminology_evaluation.py",
    ]))


if __name__ == "__main__":
    main()
