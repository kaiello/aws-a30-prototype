"""Same-input lane comparison. Evidence/state metrics are not semantic grades.

The harness executes supplied lane callables; it never substitutes an invented
v1 implementation. Labels and required IDs are held out of both reader inputs.
The included original fixture v2 lane uses a deliberately mocked reader.
"""
from dataclasses import dataclass
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Callable
from types import SimpleNamespace
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class ComparisonCase:
    case_id: str
    query: str
    category: str
    required_evidence_ids: tuple[str, ...] = ()


def _evidence_ids(result):
    """Keep selected evidence distinct from claimed bindings."""
    packet = result.get("evidence_packet", {})
    selected = packet.get("evidence", []) if isinstance(packet, dict) else []
    selected = selected or result.get("retrieved_evidence", [])
    return {item.get("evidence_id", item.get("id")) for item in selected
            if isinstance(item, dict) and item.get("evidence_id", item.get("id"))}


def _execute(lane, case):
    start = time.perf_counter()
    try:
        result = lane(case.query)
        if not isinstance(result, dict):
            raise TypeError("Lane must return a result object")
        elapsed = round((time.perf_counter() - start) * 1000, 3)
        selected = _evidence_ids(result)
        required = set(case.required_evidence_ids)
        assessment = result.get("answer_assessment", {})
        # Do not infer zero usage/cost, zero images or semantic validity from an
        # absent counter. Adapters must explicitly report observed model input.
        metrics = result.get("comparison_observation", {})
        return {
            "execution": "completed", "latency_ms": elapsed,
            "answer_outcome": result.get("answer_outcome"),
            "assessment_status": assessment.get("status"),
            "assessment_validated": assessment.get("validated"),
            "selected_evidence_count": len(selected),
            "required_evidence_count": len(required),
            "required_evidence_recall": round(len(required & selected) / len(required), 4) if required else None,
            "all_required_evidence": required <= selected if required else None,
            "observed_model_image_count": metrics.get("model_image_count"),
            "usage": result.get("usage"),
            "cost": metrics.get("cost"),
            "semantic_correctness": None,
        }
    except Exception as exc:
        return {"execution": "failed", "error_type": type(exc).__name__,
                "latency_ms": round((time.perf_counter() - start) * 1000, 3),
                "semantic_correctness": None}


def compare_cases(cases: list[ComparisonCase], v1: Callable, v2: Callable, *,
                  v1_mode: str, v2_mode: str):
    """Execute each exact query once per lane with no reader access to labels."""
    if v1_mode not in {"provider_free", "software_mocked", "live_model"} or v2_mode not in {
            "provider_free", "software_mocked", "live_model"}:
        raise ValueError("Each lane must explicitly declare its validation mode")
    rows = [{"case_id": case.case_id, "query": case.query, "category": case.category,
             "v1": _execute(v1, case), "v2": _execute(v2, case)} for case in cases]
    return {"schema_version": "1.0.0", "kind": "same_input_software_evidence_comparison",
            "lane_modes": {"v1": v1_mode, "v2": v2_mode},
            "semantic_validation": "unassessed; separate source/model grading required",
            "cost_note": "null means unobserved; fixture reader has no provider call",
            "cases": rows}


def fixture_cases(data):
    """Frozen original toy questions; not the licensed AWS gold benchmark."""
    return [
        ComparisonCase("definition_alias", "Define retaining ring", "definition_alias",
                       (data["collar"].evidence_id,)),
        ComparisonCase("definition_senses", "Define nozzle", "sense_ambiguity"),
        ComparisonCase("table", "Table X1 copper", "structured_table", (data["row"].evidence_id,)),
        ComparisonCase("multipage_figure", "Figure X1", "multipage_figure",
                       tuple(item.evidence_id for item in data["figures"]) + (data["note"].evidence_id,)),
        ComparisonCase("crossmodal", "Compare collar and sleeve in Figure X1", "crossmodal_comparison",
                       (data["collar"].evidence_id, data["sleeve"].evidence_id,
                        *[item.evidence_id for item in data["figures"]], data["note"].evidence_id)),
        ComparisonCase("missing", "Table X9 copper", "missing_evidence"),
    ]


def fixture_v2_lane(store, root):
    from src.evidence_reader import read_packet
    def lane(query):
        packet = store.packet(query)
        observed = {"model_image_count": 0, "cost": {"amount": 0, "currency": "USD", "basis": "no provider call"}}
        def mocked_reader(messages):
            observed["model_image_count"] = sum(
                part.get("type") == "image_url" for message in messages
                if isinstance(message.get("content"), list) for part in message["content"])
            return {"claims": [{"text": "Mock reader exercised the complete synthetic packet.",
                                "evidence_ids": [item.evidence_id for item in packet.evidence]}],
                    "usage": {"mocked": True}}
        result = read_packet(packet, root, generate=mocked_reader)
        result["evidence_packet"] = packet.to_dict()
        result["comparison_observation"] = observed
        return result
    return lane


def fixture_v1_lane(query_path: Path, data):
    """Execute actual v1 orchestration with synthetic boundary injections.

    AST extraction is the same isolation pattern used by existing repository
    query tests. Retrieval supplies the entire shared fixture to avoid inventing
    a ranking comparison. It is an injected retrieval/synthesis experiment, not
    a measurement of the actual v1 indexes, provider, semantic accuracy or cost.
    Heavyweight imports, credentials, SQLite and network are not initialized.
    """
    raw = query_path.read_text(encoding="utf-8")
    captured = []
    class Rag:
        async def initialize_storages(self):
            pass
        async def aquery(self, prompt, param):
            captured.append(prompt)
            return "Mock generated response using supplied toy context."
    class Missing(FileNotFoundError):
        pass
    class Invalid(RuntimeError):
        pass
    def retrieval(*args, **kwargs):
        return [{"id": item.evidence_id, "evidence_id": item.evidence_id,
                 "content": json.dumps(item.to_dict(), ensure_ascii=False)} for item in data["items"]]
    namespace = {
        "Optional": Optional, "DEFAULT_ENGINE": "custom", "CUSTOM_API_KEY": "",
        "DEEPSEEK_API_KEY": "", "GEMINI_API_KEY": "", "STORAGE_DIR": Path("unused"),
        "check_early_abstention": lambda query: None,
        "get_terminology_evidence": lambda query: None,
        "compose_grounded_answer": lambda query, bundle: None,
        "hybrid_retrieve": retrieval, "ContextualIndexMissingError": Missing,
        "TerminologyRegistryError": Invalid, "ManifestError": ValueError,
        "get_rag_instance": lambda **kwargs: Rag(), "QueryParam": lambda **kwargs: kwargs,
        "extract_citations": lambda text: {}, "extract_grounded_claims": lambda text: [],
        "resolve_multimodal_assets": lambda text: ([], []),
        "extract_see_also_terms": lambda text: [],
        "verify_epistemic_provenance": lambda *args, **kwargs: {"epistemic_status": "UNASSESSED"},
        "resolve_answer_route": lambda *args, **kwargs: SimpleNamespace(to_dict=lambda: {"status": "UNASSESSED"}),
        "resolve_claim_evidence": lambda *args, **kwargs: {"links": [], "assessment": {"status": "UNASSESSED"}, "timings_ms": {}},
        "project_reviewed_facts": lambda bundle: None,
        "extract_reference_records": lambda text: [],
        "qualify_reference_hierarchy": lambda text, mentions: {"mentions": [], "diagnostics": []},
        "hashlib": hashlib, "json": json, "time": time,
    }
    names = {"async_query", "_query_failure", "_reviewed_trace", "_scope_decision",
             "_attach_claim_evidence", "_empty_claim_evidence", "_resolve_display_assets", "_reject_unresolved_citations"}
    nodes = [node for node in ast.parse(raw).body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual-v1-query", "exec"), namespace)
    async_query = namespace["async_query"]
    def lane(query):
        captured.clear()
        # Mock async boundaries complete without suspension. Driving this
        # coroutine directly avoids creating a Windows event-loop socketpair in
        # provider-free sandboxes and rejects any unexpected real async I/O.
        coroutine = async_query(query, engine="custom", api_key="synthetic-test-value")
        try:
            coroutine.send(None)
        except StopIteration as completed:
            result = completed.value
        else:
            raise ValueError("Mocked v1 query unexpectedly suspended for I/O")
        finally:
            coroutine.close()
        if len(captured) != 1 or not isinstance(captured[0], str):
            raise ValueError("Expected one actual v1 text generation call")
        # Actual v1 sends the supplied context as a plain text string to aquery.
        result["comparison_observation"] = {"model_image_count": 0,
            "cost": {"amount": 0, "currency": "USD", "basis": "mocked synthesis; no provider call"}}
        result["usage"] = {"mocked": True}
        return result
    lane.source_sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return lane


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--v1-callback", help="Trusted module:function taking query and returning actual v1 result")
    source.add_argument("--v1-query", type=Path, help="Actual src/query.py; AST isolated with injected retrieval and mocked synthesis")
    parser.add_argument("--v1-mode", choices=["provider_free", "software_mocked", "live_model"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "tests"))
    from evidence_v2_fixture import fixture
    # Explicit output parent also works in managed Windows sandboxes whose
    # redirected default TEMP can create a directory but cannot create children.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a30-v2-comparison-", dir=args.output.parent.resolve()) as temporary:
        store, data = fixture(Path(temporary))
        if args.v1_query:
            v1 = fixture_v1_lane(args.v1_query, data)
            v1_mode = "software_mocked"
        else:
            if not args.v1_mode:
                parser.error("--v1-callback requires an explicit --v1-mode")
            module_name, function_name = args.v1_callback.split(":", 1)
            v1 = getattr(importlib.import_module(module_name), function_name)
            v1_mode = args.v1_mode
        receipt = compare_cases(fixture_cases(data), v1, fixture_v2_lane(store, Path(temporary)),
                                v1_mode=v1_mode, v2_mode="software_mocked")
        if args.v1_query:
            receipt["v1_orchestration_source_sha256"] = v1.source_sha256
            receipt["injection_limits"] = ("Actual v1 query methods; complete shared synthetic retrieval pool; "
                "mocked synthesis and diagnostic boundaries. No actual index ranking or provider/semantic score.")
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(receipt['cases'])} same-input cases; semantic correctness remains unassessed.")


if __name__ == "__main__":
    main()
