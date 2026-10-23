"""Synthetic transport/contract checks; no actual model or semantic validation."""
from copy import deepcopy
import hashlib
import io
import json

import pytest

from src import evidence_a1_vision as vision


def inputs(tmp_path):
    image = tmp_path / "pixels.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic-image-placeholder")
    graph = {"nodes": [
        {"id": "r", "kind": "root", "label": "Root", "region": [0, 0, .1, .2]},
        {"id": "c", "kind": "category", "label": "Category", "region": [.2, .1, .8, .8]},
        {"id": "p", "kind": "process", "label": "Row", "region": [.3, .2, .4, .6]},
        {"id": "q", "kind": "process", "label": "Indented row", "region": [.5, .3, .6, .6]},
    ], "extraction_provenance": {"method": "ocr", "engine": "synthetic", "version": "0",
        "input_asset_sha256": hashlib.sha256(image.read_bytes()).hexdigest()},
        "native_text": "NEVER SEND NATIVE TEXT", "edges": [{"secret": "NEVER SEND EDGES"}]}
    return image, graph


def proposal(**changes):
    return {"from_id": "c", "to_id": "p", "type": "ENCLOSES_ROW",
            "region": [.2, .1, .8, .8], "observation": "The visible rectangle encloses this row.",
            "unclear": False, **changes}


def output(*proposals, **changes):
    return {"complete": True, "proposals": list(proposals), "unresolved": [], **changes}


def transport(monkeypatch, document, *, terminal=None, fail_after=False, digest=None):
    calls = []
    text = document if isinstance(document, str) else json.dumps(document)
    frames = [{"response": text[:len(text)//2], "done": False},
              {"response": text[len(text)//2:], "done": False}]
    if not fail_after:
        frames.append({"response": "", "done": True, "done_reason": "stop",
                       "prompt_eval_count": 210, "eval_count": 90, **(terminal or {})})
    raw = b"".join(json.dumps(frame).encode() + b"\n" for frame in frames)

    class Broken(io.BytesIO):
        def read1(self, *args):
            line = super().read1(*args)
            if not line:
                raise TimeoutError("synthetic socket timeout")
            return line

    def fake(path, body=None, *, timeout):
        calls.append((path, body, timeout))
        if path == "/api/version":
            return io.BytesIO(json.dumps({"version": "0.40.4"}).encode())
        if path == "/api/tags":
            return io.BytesIO(json.dumps({"models": [{"name": vision.APPROVED_MODEL,
                "digest": digest or vision.APPROVED_DIGEST}]}).encode())
        if path == "/api/show":
            return io.BytesIO(json.dumps({"model_info": {"qwen3vl.context_length": 262144}}).encode())
        if path == "/api/ps":
            return io.BytesIO(json.dumps({"models": [{"name": vision.APPROVED_MODEL,
                "digest": vision.APPROVED_DIGEST, "context_length": 16384}]}).encode())
        assert path == "/api/generate"
        return (Broken if fail_after else io.BytesIO)(raw)

    monkeypatch.setattr(vision, "_open_local", fake)
    return calls, raw


def test_single_stream_preserves_raw_and_candidate_boundary(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    before = deepcopy(graph)
    calls, raw = transport(monkeypatch, output(proposal()))
    path = tmp_path / "private.ndjson"
    result = vision.analyze_visual_structure(image, graph, raw_output_path=path)
    assert result["status"] == "complete"
    assert result["callcount"] == 1
    assert path.read_bytes() == raw
    assert result["proposals"][0]["verification"] == "candidate"
    assert graph == before
    request = next(body for route, body, _ in calls if route == "/api/generate")
    assert request["options"] == {"num_ctx": 16384, "num_predict": -1, "temperature": 0, "seed": 42}
    assert request["stream"] is True
    assert "NEVER SEND" not in request["prompt"]
    assert result["config"]["actual_context_length"] == 16384
    assert result["diagnostics"]["done_reason"] == "stop"
    assert result["diagnostics"]["input_tokens"] == 210
    assert result["diagnostics"]["output_tokens"] == 90
    assert len(result["config"]["prompt_sha256"]) == 64


@pytest.mark.parametrize("document,terminal,status", [
    ("broken JSON", None, "invalid_output"),
    (output(proposal()), {"done_reason": "length"}, "incomplete_output"),
    (output(proposal(), complete=False), None, "incomplete_output"),
    ({"complete": True, "proposals": [proposal()]}, None, "invalid_output"),
])
def test_incomplete_or_invalid_output_keeps_text_without_proposals(tmp_path, monkeypatch, document, terminal, status):
    image, graph = inputs(tmp_path)
    _, raw = transport(monkeypatch, document, terminal=terminal)
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == status
    assert result["proposals"] == []
    assert result["text"]
    assert (tmp_path / "raw").read_bytes() == raw


@pytest.mark.parametrize("bad", [
    proposal(to_id="invented"), proposal(type="IS_A"), proposal(from_id="p"),
    proposal(region=[0, 0, float("nan"), 1]), proposal(region=[0, 0, 0, 1]),
    proposal(unclear=True),
])
def test_rejects_invalid_or_unclear_candidates(tmp_path, monkeypatch, bad):
    image, graph = inputs(tmp_path)
    transport(monkeypatch, output(bad))
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_output"
    assert result["proposals"] == []


def test_duplicate_and_conflicting_parents_are_rejected(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    graph["nodes"].append({"id": "c2", "kind": "category", "label": "Other", "region": [.2, .1, .8, .8]})
    for index, proposals in enumerate(([proposal(), proposal()], [proposal(), proposal(from_id="c2")])):
        transport(monkeypatch, output(*proposals))
        result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / str(index))
        assert result["status"] == "invalid_output"
        assert result["proposals"] == []


def test_timeout_preserves_partial_stream(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    _, raw = transport(monkeypatch, output(proposal()), fail_after=True)
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "timeout"
    assert result["callcount"] == 1
    assert result["proposals"] == []
    assert (tmp_path / "raw").read_bytes() == raw


def test_precheck_digest_failure_makes_no_inference_call(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    calls, _ = transport(monkeypatch, output(), digest="different")
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "precheck_failed"
    assert result["callcount"] == 0
    assert not any(path == "/api/generate" for path, _, _ in calls)


def test_exclusive_raw_path_never_overwrites_or_calls_backend(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    path = tmp_path / "raw"
    path.write_bytes(b"existing evidence")
    calls, _ = transport(monkeypatch, output())
    with pytest.raises(FileExistsError):
        vision.analyze_visual_structure(image, graph, raw_output_path=path)
    assert path.read_bytes() == b"existing evidence"
    assert calls == []


def test_requires_ocr_pixels_and_matching_hash_before_backend(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    graph["extraction_provenance"]["input_asset_sha256"] = "unbound"
    calls, _ = transport(monkeypatch, output())
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_input"
    assert result["callcount"] == 0
    assert calls == []


def test_repetition_guard_does_not_cap_productive_growth():
    block = json.dumps(proposal()) + ","
    assert vision._repeated_nonproductive_suffix(block * 4)
    productive = "".join(json.dumps(proposal(to_id=f"row-{i}")) + "," for i in range(1500))
    assert not vision._repeated_nonproductive_suffix(productive)


def test_repeated_output_is_explicitly_stopped_with_raw_retained(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    block = json.dumps(proposal()) + ","
    _, raw = transport(monkeypatch, block * 4)
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "repetition_stopped"
    assert result["text"] == block * 4
    assert result["proposals"] == []
    # All received bytes are retained, including any buffered terminal frame.
    assert raw.startswith((tmp_path / "raw").read_bytes())


def test_explicit_interruption_preserves_prior_bytes_without_metadata_delay(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    calls, raw = transport(monkeypatch, output(proposal()))
    original = vision._open_local

    class Interrupted(io.BytesIO):
        def read1(self, *args):
            if self.tell():
                raise KeyboardInterrupt
            # Deliberately interrupt in the middle of the first NDJSON frame.
            return super().read1(20)

    def interrupting(path, body=None, *, timeout):
        return Interrupted(raw) if path == "/api/generate" else original(path, body, timeout=timeout)

    monkeypatch.setattr(vision, "_open_local", interrupting)
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "cancelled"
    assert (tmp_path / "raw").read_bytes() == raw[:20]
    assert not any(path == "/api/ps" for path, _, _ in calls)


def test_local_transport_disables_proxies_and_rejects_redirects(monkeypatch):
    captured = {}

    class FakeOpener:
        def open(self, request, *, timeout):
            captured["request"] = request
            return io.BytesIO(b"{}")

    def opener(*handlers):
        captured["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(vision, "build_opener", opener)
    with vision._open_local("/api/version", timeout=1) as response:
        assert response.read() == b"{}"
    assert captured["request"].full_url == "http://127.0.0.1:11434/api/version"
    assert captured["handlers"][0].proxies == {}
    with pytest.raises(ValueError, match="redirect"):
        captured["handlers"][1].redirect_request(None, None, 302, "", {}, "https://external.invalid")
    with pytest.raises(ValueError, match="Unsupported"):
        vision._open_local("https://external.invalid", timeout=1)


def test_strict_json_duplicate_keys_are_rejected(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    transport(monkeypatch, '{"complete":true,"complete":true,"proposals":[],"unresolved":[]}')
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_output"
    assert "Duplicate JSON key" in result["diagnostics"]["issues"][0]


def bootstrap_inputs(tmp_path):
    image, graph = inputs(tmp_path)
    graph["nodes"] = graph["nodes"][1:]
    graph["root_id"] = None
    graph["bootstrap_words"] = [
        {"id": "word-a", "text": "CENTRAL", "region": [.1, .3, .15, .5]},
        {"id": "word-b", "text": "LABEL", "region": [.16, .3, .2, .5]},
    ]
    return image, graph


def root_observation(**changes):
    return {"word_ids": ["word-a", "word-b"], "region": [.09, .29, .21, .51],
            "observation": "These OCR words lie together inside the visible central outline.", **changes}


def test_missing_root_bootstrap_uses_only_existing_ocr_words(tmp_path, monkeypatch):
    image, graph = bootstrap_inputs(tmp_path)
    document = output(proposal(from_id="$root", to_id="c", type="CHART_CONNECTOR"),
                      root_observation=root_observation())
    calls, _ = transport(monkeypatch, document)
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw", num_ctx=32768)
    assert result["status"] == "complete"
    assert result["root_observation"]["label"] == "CENTRAL LABEL"
    assert result["root_observation"]["verification"] == "candidate"
    assert result["proposals"][0]["from_id"] == "$root"
    request = next(body for route, body, _ in calls if route == "/api/generate")
    assert "root_observation" in request["format"]["required"]
    assert "word-a" in request["prompt"] and "CENTRAL" in request["prompt"]
    assert "NEVER SEND" not in request["prompt"]
    assert "root_observation" not in vision.OUTPUT_SCHEMA["properties"]


@pytest.mark.parametrize("bad", [
    root_observation(word_ids=[]), root_observation(word_ids=["word-a", "word-a"]),
    root_observation(word_ids=["invented"]), root_observation(region=[0, 0, .05, .05]),
    root_observation(label="invented label"),
])
def test_root_bootstrap_rejects_unbound_words_regions_and_invented_labels(tmp_path, monkeypatch, bad):
    image, graph = bootstrap_inputs(tmp_path)
    transport(monkeypatch, output(root_observation=bad))
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_output"
    assert result["root_observation"] is None
    assert result["proposals"] == []


def test_unresolved_root_remains_explicit_without_a_fabricated_node(tmp_path, monkeypatch):
    image, graph = bootstrap_inputs(tmp_path)
    unresolved = [{"node_ids": [], "region": [.09, .29, .21, .51],
                   "observation": "The central outline cannot be resolved from these pixels."}]
    transport(monkeypatch, output(root_observation=None, unresolved=unresolved))
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "root_unresolved"
    assert result["root_observation"] is None
    assert result["unresolved"] == unresolved
    assert all(node["kind"] != "root" for node in graph["nodes"])


def test_unresolved_root_cannot_support_special_root_connector(tmp_path, monkeypatch):
    image, graph = bootstrap_inputs(tmp_path)
    unresolved = [{"node_ids": [], "region": [.09, .29, .21, .51], "observation": "Root unresolved."}]
    transport(monkeypatch, output(proposal(from_id="$root", to_id="c", type="CHART_CONNECTOR"),
                                 root_observation=None, unresolved=unresolved))
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_output"
    assert result["proposals"] == []


def test_bootstrap_rejects_existing_node_using_reserved_root_id_before_call(tmp_path, monkeypatch):
    image, graph = bootstrap_inputs(tmp_path)
    graph["nodes"][0]["id"] = "$root"
    calls, _ = transport(monkeypatch, output(root_observation=root_observation()))
    result = vision.analyze_visual_structure(image, graph, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_input"
    assert result["callcount"] == 0
    assert calls == []


def compact_result(**changes):
    return {"task_id": "t1", "visible": True, "region": [0, 0, .8, .8],
            "observation": "A visible physical line connects the root and category outlines.", **changes}


def connector_task(**changes):
    return {"type": "CHART_CONNECTOR", "from_id": "r", "to_id": "c", **changes}


def test_compact_tasks_send_only_required_nodes_and_map_candidates_back(tmp_path, monkeypatch):
    image, graph = inputs(tmp_path)
    before = deepcopy(graph)
    calls, raw = transport(monkeypatch, {"complete": True, "results": [compact_result()]})
    result = vision.analyze_visual_structure(image, graph, tasks=[connector_task()], raw_output_path=tmp_path / "raw")
    assert result["status"] == "complete" and result["callcount"] == 1
    request = next(body for route, body, _ in calls if route == "/api/generate")
    catalog = json.loads(request["prompt"].split("UNRESOLVED_INPUT_JSON:\n", 1)[1])
    assert [node["id"] for node in catalog["nodes"]] == ["n1", "n2"]
    assert [node["label"] for node in catalog["nodes"]] == ["Root", "Category"]
    assert catalog["tasks"] == [{"id": "t1", "type": "CHART_CONNECTOR", "from_id": "n1", "to_id": "n2"}]
    assert "NEVER SEND" not in request["prompt"]
    assert request["format"]["properties"]["results"]["items"]["properties"]["task_id"]["enum"] == ["t1"]
    assert request["options"]["num_predict"] == -1
    assert result["proposals"][0]["from_id"] == "r"
    assert result["proposals"][0]["to_id"] == "c"
    assert result["proposals"][0]["verification"] == "candidate"
    assert result["config"]["input_node_count"] == 2
    assert result["config"]["original_node_count"] == 4
    assert graph == before and (tmp_path / "raw").read_bytes() == raw


@pytest.mark.parametrize("tasks", [
    [], [connector_task(), connector_task()], [connector_task(to_id="missing")],
    [connector_task(from_id="c", to_id="p")], [connector_task(type="IS_A")],
])
def test_bad_compact_tasks_fail_before_backend(tmp_path, monkeypatch, tasks):
    image, graph = inputs(tmp_path)
    calls, _ = transport(monkeypatch, {})
    result = vision.analyze_visual_structure(image, graph, tasks=tasks, raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_input"
    assert result["callcount"] == 0 and calls == []


@pytest.mark.parametrize("results", [
    [], [compact_result(), compact_result()], [compact_result(task_id="invented")],
    [compact_result(visible=1)], [compact_result(type="IS_A")], [compact_result(observation="")],
])
def test_compact_output_must_dispose_every_task_once_without_new_fields(tmp_path, monkeypatch, results):
    image, graph = inputs(tmp_path)
    transport(monkeypatch, {"complete": True, "results": results})
    result = vision.analyze_visual_structure(image, graph, tasks=[connector_task()], raw_output_path=tmp_path / "raw")
    assert result["status"] == "invalid_output"
    assert result["proposals"] == []


@pytest.mark.parametrize("visible", [False, None])
def test_compact_nonpositive_disposition_stays_unresolved_not_negative_fact(tmp_path, monkeypatch, visible):
    image, graph = inputs(tmp_path)
    transport(monkeypatch, {"complete": True, "results": [compact_result(visible=visible)]})
    result = vision.analyze_visual_structure(image, graph, tasks=[connector_task()], raw_output_path=tmp_path / "raw")
    assert result["status"] == "complete"
    assert result["proposals"] == []
    assert result["unresolved"][0]["node_ids"] == ["r", "c"]
    assert result["unresolved"][0]["observation"].startswith("Not established")


def test_compact_missing_root_can_select_previously_assigned_ocr_words(tmp_path, monkeypatch):
    image, graph = bootstrap_inputs(tmp_path)
    # The allowed pool includes words already assigned to a candidate category;
    # assignment does not confer authority to exclude them from root inspection.
    graph["bootstrap_words"][0]["assigned_node_id"] = "c"
    doc = {"complete": True, "results": [compact_result()], "root_observation":
           root_observation(word_ids=["w1", "w2"])}
    calls, _ = transport(monkeypatch, doc)
    result = vision.analyze_visual_structure(image, graph,
        tasks=[connector_task(from_id="$root")], raw_output_path=tmp_path / "raw")
    assert result["status"] == "complete"
    assert result["root_observation"]["word_ids"] == ["word-a", "word-b"]
    assert result["root_observation"]["label"] == "CENTRAL LABEL"
    request = next(body for route, body, _ in calls if route == "/api/generate")
    assert "assigned_node_id" not in request["prompt"]
    assert result["proposals"][0]["from_id"] == "$root"
