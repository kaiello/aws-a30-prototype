"""Figure A1 structural setup and owner-CQ packet preparation. Never infers.

Packet outputs contain licensed derivatives and must stay in the ignored local
storage directory. The owner supplies questions; this module ships no CQ labels.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re

from src.evidence_a1 import load_a1_evidence, validate_a1_graph_evidence
from src.evidence_a1_registry import a1_registry_binding
from src.evidence_reader import build_messages
from src.evidence_sources import load_query_evidence
from src.evidence_v2 import EvidenceStore, SCHEMA_VERSION

CQ_SCHEMA = "a1-owner-cq-1.0"


def validate_cqs(payload):
    if (not isinstance(payload, dict) or set(payload) != {"schema_version", "source_element", "questions"}
            or payload["schema_version"] != CQ_SCHEMA or payload["source_element"] != "Figure A1"
            or not isinstance(payload["questions"], list) or len(payload["questions"]) > 100):
        raise ValueError("Invalid A1 owner-CQ document")
    identifiers = set()
    for question in payload["questions"]:
        if (not isinstance(question, dict) or set(question) != {"id", "query"}
                or not isinstance(question["id"], str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", question["id"]) is None
                or question["id"] in identifiers or not isinstance(question["query"], str)
                or not question["query"].strip() or len(question["query"]) > 16360):
            raise ValueError("Invalid or duplicate A1 owner-CQ item")
        identifiers.add(question["id"])
    return payload


def structural_status(root):
    items = load_a1_evidence(root)
    packet = EvidenceStore(items).packet("Figure A1")  # Element inventory, no CQ.
    messages = build_messages(packet, root)  # Validates original bytes; no model.
    images = [base64.b64decode(part["image_url"]["url"].split(",", 1)[1], validate=True)
              for message in messages if isinstance(message.get("content"), list)
              for part in message["content"] if part.get("type") == "image_url"]
    figures = [item for item in packet.evidence if item.kind == "figure_region"]
    if len(figures) != 1 or len(images) != 1:
        raise ValueError("A1_SINGLE_IMAGE_CONTRACT_FAILED")
    figure = figures[0]
    graph = figure.content["chart_graph"]
    record_binding = validate_a1_graph_evidence(graph, expected_source={
        "edition_id": figure.edition_id, "source_identity_id": figure.content["source_identity_id"],
        "asset_sha256": figure.content["asset_sha256"], "locator": figure.locator})
    binding = a1_registry_binding(root)
    return {
        "status": "READY_FOR_OWNER_COMPETENCY_QUESTIONS", "evidence_schema_version": SCHEMA_VERSION,
        "cq_schema_version": CQ_SCHEMA, "graph_schema_version": graph["schema_version"],
        "python_packages": {name: version(name) for name in ("PyMuPDF",)},
        "source": {"element": "Figure A1", "edition_id": figure.edition_id,
                   "locator": figure.locator, "asset_relpath": figure.content["asset_relpath"],
                   "asset_sha256": hashlib.sha256(images[0]).hexdigest(), "image_count": 1,
                   "required_evidence_count": len(packet.evidence)},
        "graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
                  "edge_counts": {kind: sum(e["type"] == kind for e in graph["edges"])
                                  for kind in graph["edge_qualifications"]},
                  "source_bound_extraction": True, "semantic_validation": False},
        "record_binding": record_binding,
        "registry": binding,
        "retrieval_implemented": ["literal_full_process_name_or_case_sensitive_code",
            "all_inbound_enclosure_and_candidate_parent_ancestors", "root_and_all_category_context",
            "complete_single_original_image_and_annex_note",
            "typed_immediate_parents_with_separate_category_enclosure",
            "complete_direct_children_and_recursive_descendants",
            "ordered_common_ancestor_layout_paths_with_explicit_reverse_hops",
            "atomic_observation_record_evidence_bindings"],
        "retrieval_deferred": ["semantic_vector_ranking_for_A1", "synonym_inference",
            "reviewed_semantic_subtype_edges", "other_images_or_figures", "cross_edition_comparison"],
        "owner_cq_count": 0, "answer_accuracy": "PENDING_OWNER_QUESTIONS",
        "model_calls": 0, "external_calls": 0,
    }


def prepare_packets(root, payload):
    validate_cqs(payload)
    packets = []
    for item in payload["questions"]:
        # Source identity is explicit at the document boundary; preserve the
        # owner's exact text separately and add only that declared context.
        query = item["query"]
        contextual_query = query if re.search(r"\bfigure\s+a1\b", query, re.I) else "Figure A1. " + query
        packet = EvidenceStore(load_query_evidence(root, contextual_query)).packet(contextual_query)
        if packet.status == "complete":
            build_messages(packet, root)  # Structural bytes/closure check only.
        packets.append({"id": item["id"], "owner_query": query,
                        "evidence_packet": packet.to_dict(), "answer_accuracy": "NOT_RUN"})
    return {"schema_version": CQ_SCHEMA, "source_element": "Figure A1", "packets": packets,
            "model_calls": 0, "external_calls": 0, "answer_accuracy": "NOT_RUN"}


def write_private_output(root, target, value):
    root = Path(root).resolve(strict=True)
    declared = root / "storage/evidence_v2"
    allowed = declared.resolve()
    requested = Path(target)
    if not requested.is_absolute():
        requested = root / requested
    target = requested.resolve()
    if (not allowed.is_relative_to(root) or not target.is_relative_to(allowed)
            or target.suffix.lower() != ".json"):
        raise ValueError("Output must be a new JSON file under local storage/evidence_v2")

    def reject_links():
        # Resolve containment and reject linked path components independently:
        # an apparently local ignored folder must not redirect private packets.
        for candidate in (declared, requested):
            for part in (candidate, *candidate.parents):
                if part == root:
                    break
                if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
                    raise ValueError("Linked private output paths are not allowed")

    reject_links()
    target.parent.mkdir(parents=True, exist_ok=True)
    reject_links()
    # Exclusive creation also prevents overwriting prior local receipts.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input", type=Path, help="Owner-supplied CQ JSON; an empty questions array is valid")
    parser.add_argument("--output", type=Path, help="New private receipt under root/storage/evidence_v2")
    parser.add_argument("--graph-qa", action="store_true",
                        help="Explicit deterministic graph QA; no language model or external provider")
    parser.add_argument("--query-layer", choices=("auto", "evidence", "knowledge"), default="auto",
                        help="Graph QA: accepted knowledge, direct evidence, or typed automatic selection")
    args = parser.parse_args(argv)
    if args.query_layer != "auto" and not args.graph_qa:
        parser.error("--query-layer requires --graph-qa")
    try:
        status = structural_status(args.root)
        result = {"setup": status}
        if args.input:
            payload = validate_cqs(json.loads(args.input.read_text(encoding="utf-8-sig")))
            if payload["questions"] and not args.output:
                raise ValueError("Nonempty owner questions require a private --output for packets")
            if args.graph_qa:
                from src.evidence_a1_graph_qa import run_graph_qa
                result["owner_cqs"] = run_graph_qa(args.root, payload, query_layer=args.query_layer)
                status["status"] = "OWNER_CQ_GRAPH_QA_EXECUTED"
                status["answer_accuracy"] = "UNASSESSED_GRAPH_QA"
                status["generation_model"] = "NONE"
                status["qa_harness_version"] = result["owner_cqs"]["harness_version"]
                status["epistemic_store"] = result["owner_cqs"]["epistemic_store"]
                status["query_layer"] = args.query_layer
            else:
                result["owner_cqs"] = prepare_packets(args.root, payload)
            status["owner_cq_count"] = len(payload["questions"])
        elif args.graph_qa:
            raise ValueError("--graph-qa requires an owner --input document")
        if args.output:
            write_private_output(args.root, args.output, result)
        # Summary is source-safe; full packets never print to the console.
        summary = dict(status)
        if "registry" in summary:
            registry = dict(summary["registry"])
            registry["candidate_bridge_count"] = len(registry.pop("bridges", []))
            summary["registry"] = registry
        print(json.dumps(summary, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
