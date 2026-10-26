"""
test_web_endpoints.py: Comprehensive validation of Web Explorer endpoints,
categories, inspector chips, and NLQ execution.
"""
import urllib.request
import urllib.parse
import json
import time
import socket
import pytest

BASE_URL = "http://localhost:8000"


def _is_server_running(host: str = "localhost", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


SERVER_AVAILABLE = _is_server_running()
pytestmark = pytest.mark.skipif(not SERVER_AVAILABLE, reason="Web Explorer live server not running on localhost:8000")


def test_benchmark_endpoint():
    print("Testing GET /api/benchmark...")
    req = urllib.request.Request(f"{BASE_URL}/api/benchmark")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data) == 50
        print(f"  [PASS] Benchmark endpoint returned {len(data)} gold questions.")

def test_figures_and_categories():
    print("Testing GET /api/figures & Classification Trees...")
    req = urllib.request.Request(f"{BASE_URL}/api/figures")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        categories = {c["id"]: c["label"] for c in data.get("categories", [])}
        assert "classification" in categories, "Category 'classification' missing!"
        print(f"  [PASS] Found categories: {list(categories.keys())}")
        
        classification_figs = [f for f in data.get("figures", []) if f.get("category") == "classification"]
        assert len(classification_figs) >= 6, f"Expected >=6 classification figures, got {len(classification_figs)}"
        fig_ids = [f["id"] for f in classification_figs]
        print(f"  [PASS] Classification Figures ({len(classification_figs)}): {fig_ids}")
        assert "Figure A1" in fig_ids

def test_figure_inspector_a1():
    print("Testing GET /api/figure_inspector for Figure A1...")
    q = urllib.parse.urlencode({"id": "Figure A1"})
    req = urllib.request.Request(f"{BASE_URL}/api/figure_inspector?{q}")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        html = data.get("html", "")
        assert "Major Process Branches" in html
        assert "Solid-State Welding (SSW)" in html
        assert "data-query" in html
        print("  [PASS] Figure A1 inspector HTML contains Major Process Branches and chips.")

def test_nlq_chip_flame_contact():
    print("Testing POST /api/query for 'show me flame contact on figure A6'...")
    payload = json.dumps({
        "query": "show me flame contact on figure A6",
        "engine": "deepseek",
        "mode": "mix"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/query",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "answer" in data and len(data["answer"]) > 20
        assert "citations" in data
        assert "answer_route" in data
        print("  [PASS] NLQ Flame Contact succeeded:")
        print(f"         Answer: {data['answer'][:80]}...")
        print(f"         Citations: {data['citations']}")

def test_nlq_a1_solid_state_welding():
    print("Testing POST /api/query for 'What processes are included under Solid-State Welding on Figure A1?'...")
    payload = json.dumps({
        "query": "What processes are included under Solid-State Welding on Figure A1?",
        "engine": "deepseek",
        "mode": "mix"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/query",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "answer" in data and len(data["answer"]) > 20
        print("  [PASS] NLQ Figure A1 Solid-State Welding succeeded:")
        print(f"         Answer: {data['answer'][:80]}...")

if __name__ == "__main__":
    time.sleep(2)  # Give server a moment
    print("\n--- RUNNING WEB EXPLORER INTEGRATION TESTS ---\n")
    test_benchmark_endpoint()
    test_figures_and_categories()
    test_figure_inspector_a1()
    test_nlq_chip_flame_contact()
    test_nlq_a1_solid_state_welding()
    print("\n[SUCCESS] ALL WEB EXPLORER & NLQ TESTS PASSED!\n")
