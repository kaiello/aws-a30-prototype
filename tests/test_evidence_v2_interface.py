"""Version selection through the existing guarded handler; no provider/server."""
import json
import pytest
from test_security_boundaries import web_fixture, request


def test_v1_default_call_options_are_unchanged(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {"query": "Define a weld"})[0] == 200
    assert "evidence_version" not in web_fixture[3][0][1]
    assert "v2_reader" not in web_fixture[3][0][1]


def test_v2_reader_is_explicitly_dispatched(web_fixture):
    assert request(web_fixture, "/api/query", "POST", {
        "query": "Figure B6", "evidence_version": "v2", "v2_reader": "local"})[0] == 200
    assert web_fixture[3][0][1]["evidence_version"] == "v2"
    assert web_fixture[3][0][1]["v2_reader"] == "local"


@pytest.mark.parametrize("key,value", [
    ("evidence_version", "v3"), ("evidence_version", []),
    ("v2_reader", "cloud"), ("v2_reader", {}),
])
def test_invalid_version_options_fail_before_query(web_fixture, key, value):
    assert request(web_fixture, "/api/query", "POST", {"query": "Figure B6", key: value})[0] == 400
    assert not web_fixture[3]


@pytest.mark.parametrize("code,status", [
    ("V2_SOURCE_UNAVAILABLE", 503), ("V2_READER_REQUIRED", 422), ("V2_READER_FAILED", 502),
])
def test_v2_failures_keep_explicit_http_status(web_fixture, monkeypatch, code, status):
    monkeypatch.setattr(web_fixture[0], "run_query", lambda *args, **kwargs: {"error_code": code})
    result = request(web_fixture, "/api/query", "POST", {"query": "Figure B6", "evidence_version": "v2"})
    assert result[0] == status
    assert json.loads(result[2])["error_code"] == code
