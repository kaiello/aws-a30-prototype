"""Opt-in A1 source inspection and raster extraction; no default-route changes.

The independent route excludes native facts. An explicit assisted route may use
source-backed literal names/codes only, never reference geometry or relations.
All private outputs use the existing evidence CLI's contained exclusive writer.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import time

from src.evidence_a1 import (a1_source_identity_id, bind_a1_graph_evidence,
                             load_a1_evidence, validate_a1_graph_evidence,
                             _validate_source_binding)
from src.evidence_a1_cli import validate_cqs, write_private_output

INGEST_VERSION = "a1-source-aware-ingest-1.2"


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def source_normalization_dictionary(root):
    """Project the existing source lexicon into vocabulary, not a reference graph.

    Code/label pairs identify only text already observed in raster OCR. Neither
    graph record IDs, source geometry, edges, nor admission status are exposed.
    """
    from src.evidence_a1_lexicon import source_dictionary, LEXICON_VERSION
    figure = next(item for item in load_a1_evidence(root) if item.kind == "figure_region")
    graph = figure.content["chart_graph"]
    entries = {}
    for literal in source_dictionary(graph):
        if literal["method"] not in {"literal_label", "exact_heading_code", "exact_process_code"}:
            continue
        item = entries.setdefault(literal["node_id"], {"kind": literal["kind"]})
        field = "label" if literal["method"] == "literal_label" else "code"
        item[field] = literal["text"]
    binding = graph["source_binding"]
    result = {"schema_version": "a1-normalization-dictionary-1.0",
        "source": {"edition_id": binding["edition_id"],
                   "source_identity_id": binding["source_identity_id"],
                   "asset_sha256": binding["asset_sha256"], "lexicon_version": LEXICON_VERSION},
        "entries": sorted(entries.values(), key=lambda item: (item["kind"], item["label"]))}
    result["content_sha256"] = _sha(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    return result


def _new_directory(root, declared):
    root = Path(root).resolve(strict=True)
    target = Path(declared)
    if not target.is_absolute():
        target = root / target
    allowed = root / "storage/evidence_v2"
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError("Linked private ingest paths are not allowed")
    target = target.resolve()
    if not allowed.resolve().is_relative_to(root) or not target.is_relative_to(allowed.resolve()):
        raise ValueError("Ingest run directory must be under storage/evidence_v2")
    target.mkdir(parents=True, exist_ok=False)
    return target


def inspect_page(page, region=None):
    """Inspect a selected normalized region, without treating text as topology."""
    import fitz
    if region is None:
        region = [0, 0, 1, 1]
    if (not isinstance(region, list) or len(region) != 4 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in region) or not (0 <= region[0] < region[2] <= 1
                                    and 0 <= region[1] < region[3] <= 1)):
        raise ValueError("Invalid normalized inspection region")
    h, w = page.rect.height, page.rect.width
    clip = fitz.Rect(region[1]*w, region[0]*h, region[3]*w, region[2]*h)
    text = page.get_text("text", clip=clip)
    significant = [c for c in text if not c.isspace()]
    usable = sum(c.isprintable() and c != "\ufffd" for c in significant)
    fraction = usable / len(significant) if significant else 0.0
    vectors = [d for d in page.get_drawings() if fitz.Rect(d["rect"]).intersects(clip)]
    native_usable = len(significant) >= 10 and fraction >= 0.98
    return {"region": region, "region_space": "normalized_page_ymin_xmin_ymax_xmax",
            "native_character_count": len(significant), "readable_fraction": fraction,
            "native_text_usable": native_usable, "vector_drawing_count": len(vectors),
            "raster_image_count": len(page.get_images()),
            "text_route": "native_text" if native_usable else "local_ocr",
            "structure_route": "native_vector_candidate" if vectors else "raster_geometry_and_vision",
            "qualification": "Text availability does not establish relationship correctness."}


def prepare_raster_source(root, directory, *, dpi=300):
    """Render one authorized page into a new image-only PDF; retain byte lineage."""
    import fitz
    from src.evidence_sources import _source
    root = Path(root).resolve(strict=True)
    if dpi != 300:
        raise ValueError("This bounded comparison is frozen at 300 DPI")
    directory = _new_directory(root, directory)
    figure = next(item for item in load_a1_evidence(root) if item.kind == "figure_region")
    parent = deepcopy(figure.content["chart_graph"]["source_binding"])
    _, _, pdf_path = _source(root)
    with fitz.open(pdf_path) as pdf:
        page = pdf[parent["locator"]["pdf_index"]]
        native_inspection = inspect_page(page)
        raster = page.get_pixmap(dpi=dpi, alpha=False)
        pixels = raster.tobytes("png")
        raster_pdf = fitz.open()
        raster_pdf.new_page(width=page.rect.width, height=page.rect.height).insert_image(
            page.rect, stream=pixels)
        pdf_bytes = raster_pdf.tobytes(garbage=4, deflate=True)
        raster_pdf.close()
    (directory / "a1_pixels.png").write_bytes(pixels)
    (directory / "a1_image_only.pdf").write_bytes(pdf_bytes)
    with fitz.open(stream=pdf_bytes, filetype="pdf") as check:
        raster_inspection = inspect_page(check[0])
        if raster_inspection["native_character_count"] or raster_inspection["vector_drawing_count"]:
            raise ValueError("Raster source unexpectedly contains native text or vector geometry")
    lineage = {"schema_version": INGEST_VERSION, "parent_source": parent,
               "original_pdf_sha256": _sha(Path(pdf_path).read_bytes()),
               "original_pdf_index": parent["locator"]["pdf_index"], "input_pdf_index": 0,
               "raster_pdf_sha256": _sha(pdf_bytes), "rendered_png_sha256": _sha(pixels),
               "renderer": "PyMuPDF", "renderer_version": version("PyMuPDF"),
               "render_dpi": dpi, "pixel_dimensions": [raster.width, raster.height],
               "native_inspection_reference": native_inspection,
               "raster_inspection": raster_inspection,
               "extraction_input_contract": "Raster extractor receives image-only PDF and source identity metadata only; no native labels, geometry, graph, questions or gold."}
    # Only the parent binding is passed to raster extraction; the reference
    # inspection above is retained in this separate comparison receipt.
    write_private_output(root, directory / "parent_binding.json", parent)
    write_private_output(root, directory / "lineage_receipt.json", lineage)
    return lineage


def _unresolved_connector_tasks(graph):
    """Ask only about absent physical root connections, never semantic subtype."""
    # Compact bootstrap uses a reserved source until an observed root is resolved.
    # Missing layout must not fall back to sending every process/long record ID.
    root_id = graph.get("root_id") or "$root"
    existing = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
    return [{"type": "CHART_CONNECTOR", "from_id": root_id, "to_id": node["id"]}
            for node in graph["nodes"] if node["kind"] == "category"
            and (root_id, node["id"], "CHART_CONNECTOR") not in existing]


def _add_visual_observations(graph, vision, image_bytes, raw_path, provenance, words=()):
    """Apply validated observations as candidates; an incomplete call adds none."""
    from src.evidence_a1_graph_qa import _graph_index
    rejected = []
    if vision.get("status") != "complete":
        return rejected
    raw_hash = _sha(Path(raw_path).read_bytes())
    vision_provenance = dict(provenance, method="vision", engine=vision["config"]["model"],
                             version=vision["config"]["model_digest"])
    proposed_root = vision.get("root_observation")
    if graph.get("root_id") is None and proposed_root is not None:
        by_id = {word["id"]: word for word in words}
        label = " ".join(by_id[word]["text"] for word in proposed_root["word_ids"])
        identifier = "raster:root:" + _sha(json.dumps(
            [_sha(image_bytes), proposed_root["word_ids"], proposed_root["region"]],
            sort_keys=True, separators=(",", ":")).encode())[:20]
        graph["root_id"] = identifier
        graph["nodes"].insert(0, {"id": identifier, "kind": "root", "label": label,
            "region": proposed_root["region"], "observation_ids": proposed_root["word_ids"],
            "origin_artifact_sha256": raw_hash, "extraction_provenance": vision_provenance})
    if graph.get("root_id") is None:
        return rejected
    existing = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
    for proposal in vision.get("proposals", []):
        source = graph["root_id"] if proposal["from_id"] == "$root" else proposal["from_id"]
        key = (source, proposal["to_id"], proposal["type"])
        if key in existing:
            continue
        graph["edges"].append({"from": key[0], "to": key[1], "type": key[2],
            "region": proposal["region"], "observation": proposal["observation"],
            "origin_artifact_sha256": raw_hash, "extraction_provenance": vision_provenance})
        try:
            _graph_index(graph)
        except ValueError as error:
            graph["edges"].pop()
            rejected.append({"proposal": proposal, "reason": str(error)})
            continue
        existing.add(key)
    return rejected


def ingest_raster(root, input_pdf, parent_binding, directory, *, use_vision=False,
                  dictionary_assisted=False):
    """Extract pixels, optionally using source vocabulary without reference topology."""
    import fitz
    from src.evidence_a1_raster import extract_raster_chart
    root = Path(root).resolve(strict=True)
    directory = _new_directory(root, directory)
    started = time.perf_counter()
    parent = json.loads(Path(parent_binding).read_text(encoding="utf-8"))
    _validate_source_binding(parent)
    input_pdf = Path(input_pdf).resolve(strict=True)
    with fitz.open(input_pdf) as pdf:
        if len(pdf) != 1:
            raise ValueError("A1 raster input must have exactly one image-only page")
        inspection = inspect_page(pdf[0])
        if inspection["native_character_count"] or inspection["vector_drawing_count"]:
            raise ValueError("Raster experiment rejects native text/vector extraction inputs")
        image_bytes = pdf[0].get_pixmap(dpi=300, alpha=False).tobytes("png")
    image_path = directory / "extraction_pixels.png"
    image_path.write_bytes(image_bytes)
    dictionary = source_normalization_dictionary(root) if dictionary_assisted else None
    if dictionary is not None:
        if dictionary["source"]["edition_id"] != parent["edition_id"]:
            raise ValueError("Dictionary and raster edition differ")
        write_private_output(root, directory / "normalization_dictionary.json", dictionary)
    extracted = extract_raster_chart(image_path, parent["edition_id"], **(
        {"dictionary": dictionary} if dictionary is not None else {}))
    write_private_output(root, directory / "ocr_extraction.json", extracted)
    result = {"schema_version": INGEST_VERSION,
              "route": "dictionary_assisted_raster_ocr_geometry" if dictionary_assisted else "raster_ocr_geometry",
              "input_pdf_sha256": _sha(input_pdf.read_bytes()), "input_image_sha256": _sha(image_bytes),
              "inspection": inspection, "parent_source": parent, "ocr": extracted,
              "model_calls": 0, "external_calls": 0, "source_authentication": "declared_derivative_lineage_and_consumed_image_hash; no native-fact transfer"}
    if dictionary is not None:
        result.update(dictionary_sha256=dictionary["content_sha256"],
            source_authentication="declared_derivative_lineage_and_consumed_image_hash; native-source vocabulary assistance only",
            dictionary_contract="Observed text normalization only; no reference regions, edges, accepted status or QA/gold.")
    raw_graph = extracted.get("graph")
    if raw_graph is None and dictionary_assisted and use_vision:
        raw_graph = extracted.get("partial_graph")
    if raw_graph is None:
        result.update(status="RASTER_GRAPH_UNAVAILABLE", elapsed_ms=round((time.perf_counter()-started)*1000, 3))
        write_private_output(root, directory / "ingest_result.json", result)
        return result
    raw_graph = deepcopy(raw_graph)
    if dictionary is not None:
        # Included in the bound graph digest and every record proof's graph hash.
        # Keep recognition assistance separate from source extraction authority.
        raw_graph["dictionary_assistance"] = deepcopy(extracted["dictionary_assistance"])
    provenance = {"method": "ocr", "engine": extracted["engine"], "version": extracted["version"],
                  "input_asset_sha256": _sha(image_bytes), "uncertainty": "unreviewed_model_observation",
                  "parent_source": parent}
    raw_graph["extraction_provenance"] = provenance
    if raw_graph.get("root_id") is None:
        raw_graph["bootstrap_words"] = extracted.get("bootstrap_words", [])
    if use_vision:
        from src.evidence_a1_vision import analyze_visual_structure
        # Full 300-DPI pixels plus OCR references need room for complete visual
        # observations. This is a per-request window, not an output-token cap.
        tasks = _unresolved_connector_tasks(raw_graph) if dictionary_assisted else None
        if tasks == []:
            vision = {"status": "not_needed", "callcount": 0, "proposals": [],
                      "unresolved": [], "qualification": "No absent root-category connector tasks."}
        else:
            vision = analyze_visual_structure(image_path, raw_graph,
                raw_output_path=directory / "vision_raw.ndjson", num_ctx=32768,
                **({"tasks": tasks} if tasks is not None else {}))
        result["vision"] = vision
        result["model_calls"] = vision["callcount"]
        result["rejected_vision_proposals"] = _add_visual_observations(raw_graph, vision,
            image_bytes, directory / "vision_raw.ndjson", provenance, extracted.get("bootstrap_words", []))
    if raw_graph.get("root_id") is None:
        result.update(status="RASTER_GRAPH_UNAVAILABLE", elapsed_ms=round((time.perf_counter()-started)*1000, 3))
        write_private_output(root, directory / "ingest_result.json", result)
        return result
    anchor = dict(parent["locator"], printed_label=parent["locator"]["printed_page"], role="start")
    identity = a1_source_identity_id(parent["edition_id"], "figure:figure_a1", anchor, _sha(image_bytes))
    locator = dict(parent["locator"], source_identity_id=identity)
    graph = bind_a1_graph_evidence(raw_graph, parent["edition_id"], identity, locator, _sha(image_bytes))
    result.update(status="CANDIDATE_RASTER_EVIDENCE_EXTRACTED", graph=graph,
                  coverage_established=False, elapsed_ms=round((time.perf_counter()-started)*1000, 3))
    validate_a1_graph_evidence(graph)
    result["record_catalog"] = record_catalog(graph)
    write_private_output(root, directory / "ingest_result.json", result)
    return result


def record_catalog(graph):
    """One record contract for native and unreviewed extraction methods."""
    records = []
    for record in graph["nodes"] + graph["edges"]:
        proof = deepcopy(record["evidence"])
        extraction = proof.get("extraction_provenance")
        if extraction is None:
            extraction = {"method": "native_pdf", "engine": "PyMuPDF",
                          "version": version("PyMuPDF"),
                          "uncertainty": "literal_or_physical_layout_observation_not_semantic_entailment"}
        records.append(dict(proof, extraction=extraction))
    return records


def _retained_file(root, item):
    """Resolve and hash one immutable local source artifact, excluding links."""
    if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
        raise ValueError("RASTER_INTEGRATION_ARTIFACT_INVALID")
    path = Path(item["path"])
    if path.is_absolute():
        raise ValueError("RASTER_INTEGRATION_ARTIFACT_NOT_RELATIVE")
    path = root / path
    if any(part.is_symlink() or getattr(part, "is_junction", lambda: False)()
           for part in (path, *path.parents) if part != root):
        raise ValueError("RASTER_INTEGRATION_LINKED_ARTIFACT")
    path = path.resolve(strict=True)
    if not path.is_relative_to(root / "storage/evidence_v2") or _sha(path.read_bytes()) != item["sha256"]:
        raise ValueError("RASTER_INTEGRATION_SOURCE_CHANGED")
    return path


def _verified_raster_graph(seed, metadata):
    """Canonical overlay: retain raster records, replace only verified stroke anchors."""
    graph = deepcopy(seed["graph"])
    binding = graph["source_binding"]
    for key in ("source_binding", "record_evidence_schema_version", "native_graph_sha256"):
        graph.pop(key, None)
    connectors = {(item["from_id"], item["to_id"]): item
                  for item in metadata["connector_receipt"]["records"]}
    for node in graph["nodes"]:
        node.pop("evidence", None)
    for edge in graph["edges"]:
        edge.pop("evidence", None)
        edge.pop("id", None)
        verified = connectors.get((edge["from"], edge["to"])) if edge["type"] == "CHART_CONNECTOR" else None
        if verified and verified["verified"]:
            edge["prior_extraction_region"] = edge["region"]
            edge["region"] = verified["region"]
            edge["pixel_stroke_evidence"] = deepcopy(verified)
    graph["raster_verification"] = deepcopy(metadata)
    return bind_a1_graph_evidence(graph, **binding)


def validate_raster_integration(root, graph):
    """Recompute source checks and the full derived graph before granting authority.

    A hash/receipt is only a consistency claim. Actual source pixels and retained
    observations are reread; neither native references nor QA data are loaded.
    """
    from src.evidence_a1_strokes import verify_chart_connectors
    from src.evidence_a1_verification import verify_raster_records
    root = Path(root).resolve(strict=True)
    metadata = graph.get("raster_verification")
    if (not isinstance(metadata, dict) or set(metadata) != {
            "schema_version", "artifacts", "receipt", "connector_receipt"}
            or metadata["schema_version"] != "a1-raster-integration-1.0"
            or not isinstance(metadata["artifacts"], dict)
            or set(metadata["artifacts"]) != {"ingest_result", "image"}):
        raise ValueError("RASTER_INTEGRATION_CONTRACT_INVALID")
    seed_path = _retained_file(root, metadata["artifacts"]["ingest_result"])
    image_path = _retained_file(root, metadata["artifacts"]["image"])
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    validate_a1_graph_evidence(seed["graph"])
    if (seed["graph"]["source_binding"]["asset_sha256"] != _sha(image_path.read_bytes())
            or seed["ocr"]["input"]["image_sha256"] != _sha(image_path.read_bytes())
            or seed["ocr"]["input"]["edition_id"] != seed["graph"]["source_binding"]["edition_id"]):
        raise ValueError("RASTER_INTEGRATION_SOURCE_SCOPE_MISMATCH")
    connectors = verify_chart_connectors(image_path, seed["graph"])
    receipt = verify_raster_records(image_path, seed, connectors)
    if metadata["connector_receipt"] != connectors or metadata["receipt"] != receipt:
        raise ValueError("RASTER_INTEGRATION_SOURCE_VERIFICATION_MISMATCH")
    if graph != _verified_raster_graph(seed, metadata):
        raise ValueError("RASTER_INTEGRATION_GRAPH_DIFFERS_FROM_SOURCE")
    return metadata


def integrate_retained_raster(root, cached_result, directory):
    """Verify saved raster observations without invoking extraction or a model."""
    from src.evidence_a1_strokes import verify_chart_connectors
    from src.evidence_a1_verification import verify_raster_records
    root = Path(root).resolve(strict=True)
    source = Path(cached_result).resolve(strict=True)
    source_item = {"path": str(source.relative_to(root)), "sha256": _sha(source.read_bytes())}
    source = _retained_file(root, source_item)
    seed = json.loads(source.read_text(encoding="utf-8"))
    validate_a1_graph_evidence(seed["graph"])
    image = source.parent / "extraction_pixels.png"
    image_item = {"path": str(image.relative_to(root)), "sha256": _sha(image.read_bytes())}
    image = _retained_file(root, image_item)
    if image_item["sha256"] != seed["graph"]["source_binding"]["asset_sha256"]:
        raise ValueError("RASTER_INTEGRATION_INPUT_IMAGE_MISMATCH")
    connectors = verify_chart_connectors(image, seed["graph"])
    receipt = verify_raster_records(image, seed, connectors)
    metadata = {"schema_version": "a1-raster-integration-1.0",
        "artifacts": {"ingest_result": source_item, "image": image_item},
        "receipt": receipt, "connector_receipt": connectors}
    graph = _verified_raster_graph(seed, metadata)
    validate_raster_integration(root, graph)
    directory = _new_directory(root, directory)
    result = {"schema_version": INGEST_VERSION, "status": "RETAINED_RASTER_EVIDENCE_VERIFIED",
        "route": "retained_raster_pixel_ocr_verification", "graph": graph,
        "record_catalog": record_catalog(graph), "source_verification": metadata,
        "model_calls": 0, "ocr_invocations": 0, "external_calls": 0,
        "qualification": "Per-predicate pixel/OCR admission, not blanket model acceptance or semantic subtype review."}
    write_private_output(root, directory / "ingest_result.json", result)
    return result


def resume_raster_structure(root, cached_result, directory):
    """Resolve missing structure from cached OCR, with no OCR/native reread.

    The first failed extraction is immutable. This is a separately recorded
    development continuation, not a rerun of the original scored extraction.
    """
    from src.evidence_a1_raster import rebuild_partial_from_observations
    from src.evidence_a1_vision import analyze_visual_structure
    from src.evidence_a1_graph_qa import _graph_index
    root = Path(root).resolve(strict=True)
    cached_path = Path(cached_result).resolve(strict=True)
    if not cached_path.is_relative_to(root / "storage/evidence_v2"):
        raise ValueError("Cached OCR must be a private local evidence artifact")
    previous = json.loads(cached_path.read_text(encoding="utf-8"))
    if previous.get("status") != "RASTER_GRAPH_UNAVAILABLE" or previous.get("model_calls") != 0:
        raise ValueError("Resume requires a known no-inference OCR setup failure")
    pixels = (cached_path.parent / "extraction_pixels.png").read_bytes()
    if _sha(pixels) != previous["input_image_sha256"]:
        raise ValueError("Cached extraction pixels changed")
    parent = previous["parent_source"]
    _validate_source_binding(parent)
    ocr_input = previous.get("ocr", {}).get("input", {})
    if (ocr_input.get("image_sha256") != _sha(pixels)
            or ocr_input.get("edition_id") != parent["edition_id"]):
        raise ValueError("Cached OCR pixel/edition lineage mismatch")
    projected = rebuild_partial_from_observations(previous["ocr"])
    graph = deepcopy(projected.get("partial_graph"))
    if graph is None:
        raise ValueError("Cached OCR has no usable partial projection")
    directory = _new_directory(root, directory)
    image_path = directory / "extraction_pixels.png"
    image_path.write_bytes(pixels)
    provenance = {"method": "ocr", "engine": projected["engine"], "version": projected["version"],
                  "input_asset_sha256": _sha(pixels), "uncertainty": "unreviewed_model_observation",
                  "parent_source": parent}
    graph.update(extraction_provenance=provenance, bootstrap_words=projected["bootstrap_words"])
    write_private_output(root, directory / "cached_ocr_projection.json", projected)
    vision = analyze_visual_structure(image_path, graph,
        raw_output_path=directory / "vision_raw.ndjson", num_ctx=32768)
    result = {"schema_version": INGEST_VERSION, "route": "cached_raster_ocr_plus_vision_structure",
              "development_continuation_of": str(cached_path.relative_to(root)),
              "cached_result_sha256": _sha(cached_path.read_bytes()), "ocr_reused_without_rerun": True,
              "input_image_sha256": _sha(pixels), "parent_source": parent, "ocr": projected,
              "vision": vision, "model_calls": vision["callcount"], "external_calls": 0,
              "coverage_established": False, "status": "RASTER_GRAPH_UNAVAILABLE"}
    proposed_root = vision.get("root_observation")
    if proposed_root is None:
        write_private_output(root, directory / "ingest_result.json", result)
        return result
    words = {item["id"]: item for item in projected["bootstrap_words"]}
    label = " ".join(words[word]["text"] for word in proposed_root["word_ids"])
    identifier = "raster:root:" + _sha(json.dumps(
        [_sha(pixels), proposed_root["word_ids"], proposed_root["region"]],
        sort_keys=True, separators=(",", ":")).encode())[:20]
    raw_hash = _sha((directory / "vision_raw.ndjson").read_bytes())
    vision_provenance = dict(provenance, method="vision", engine=vision["config"]["model"],
                             version=vision["config"]["model_digest"])
    graph["root_id"] = identifier
    graph["nodes"].insert(0, {"id": identifier, "kind": "root", "label": label,
        "region": proposed_root["region"], "observation_ids": proposed_root["word_ids"],
        "origin_artifact_sha256": raw_hash, "extraction_provenance": vision_provenance})
    existing = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
    for proposal in vision.get("proposals", []):
        source = identifier if proposal["from_id"] == "$root" else proposal["from_id"]
        key = (source, proposal["to_id"], proposal["type"])
        if key in existing:
            continue
        graph["edges"].append({"from": key[0], "to": key[1], "type": key[2],
            "region": proposal["region"], "observation": proposal["observation"],
            "origin_artifact_sha256": raw_hash, "extraction_provenance": vision_provenance})
        try:
            _graph_index(graph)
        except ValueError as error:
            graph["edges"].pop()
            result.setdefault("rejected_vision_proposals", []).append(
                {"proposal": proposal, "reason": str(error)})
            continue
        existing.add(key)
    anchor = dict(parent["locator"], printed_label=parent["locator"]["printed_page"], role="start")
    source_id = a1_source_identity_id(parent["edition_id"], "figure:figure_a1", anchor, _sha(pixels))
    graph = bind_a1_graph_evidence(graph, parent["edition_id"], source_id,
        dict(parent["locator"], source_identity_id=source_id), _sha(pixels))
    result.update(status="CANDIDATE_RASTER_EVIDENCE_EXTRACTED", graph=graph,
                  record_catalog=record_catalog(graph))
    write_private_output(root, directory / "ingest_result.json", result)
    return result


def ingest_source(root, input_pdf, parent_binding, directory, *, use_vision=False,
                  dictionary_assisted=False):
    """Route canonical native A1 or its image-only derivative by actual content.

    An independent raster call reads pixels/identity only. Dictionary assistance
    explicitly projects native-source vocabulary, without transferring topology.
    """
    import fitz
    root = Path(root).resolve(strict=True)
    parent = json.loads(Path(parent_binding).read_text(encoding="utf-8"))
    _validate_source_binding(parent)
    input_pdf = Path(input_pdf).resolve(strict=True)
    document_hash = parent["edition_id"].rsplit("@", 1)[-1]
    is_canonical = _sha(input_pdf.read_bytes()) == document_hash
    with fitz.open(input_pdf) as pdf:
        page_index = parent["locator"]["pdf_index"] if is_canonical else 0
        inspection = inspect_page(pdf[page_index])
    if not is_canonical:
        return ingest_raster(root, input_pdf, parent_binding, directory,
            use_vision=use_vision, dictionary_assisted=dictionary_assisted)
    if dictionary_assisted:
        raise ValueError("Dictionary assistance applies only to a raster derivative")
    if not inspection["native_text_usable"]:
        raise ValueError("Canonical native text is unreadable; raster preparation is required")
    directory = _new_directory(root, directory)
    figure = next(item for item in load_a1_evidence(root) if item.kind == "figure_region")
    graph = figure.content["chart_graph"]
    if graph["source_binding"] != parent:
        raise ValueError("Native source does not match the declared parent binding")
    result = {"schema_version": INGEST_VERSION, "status": "NATIVE_SOURCE_EVIDENCE_EXTRACTED",
              "route": "native_pdf_text_and_vector_geometry", "inspection": inspection,
              "graph": graph, "record_catalog": record_catalog(graph),
              "coverage_established": True, "model_calls": 0, "external_calls": 0,
              "qualification": "The existing validated A1 adapter is the native baseline; source-bound layout is not semantic subtype."}
    write_private_output(root, directory / "ingest_result.json", result)
    return result


def answer_raster_questions(root, ingest_result, payload, *, runtime_relpath):
    """Use the existing graph executor; never promote observations for a score."""
    from src.evidence_a1_graph_qa import answer_graph
    from src.evidence_a1_knowledge import prepare_a1_knowledge
    validate_cqs(payload)
    graph = ingest_result.get("graph")
    if graph is None:
        return {"status": "NOT_RUN_EXTRACTION_GRAPH_UNAVAILABLE", "questions": len(payload["questions"]), "answers": [], "model_calls": 0}
    validate_a1_graph_evidence(graph)
    store = prepare_a1_knowledge(root, graph, runtime_relpath=runtime_relpath)
    source_coverage = graph.get("raster_verification", {}).get("receipt", {}).get("chart_coverage")
    whole_chart_complete = bool(source_coverage and source_coverage["complete"])
    answers = []
    for question in payload["questions"]:
        start = time.perf_counter()
        accepted = answer_graph(graph, question["query"], complete_chart=whole_chart_complete,
                                knowledge_store=store, query_layer="auto")
        observed = answer_graph(graph, question["query"], complete_chart=whole_chart_complete,
                                knowledge_store=store, query_layer="evidence")
        answers.append({"id": question["id"], "query": question["query"], "accepted_auto": accepted,
                        "candidate_evidence": observed, "latency_ms": round((time.perf_counter()-start)*1000, 3)})
    return {"status": "RASTER_OBSERVATION_AND_ADMISSION_VIEWS_EXECUTED", "answers": answers,
            "epistemic_store": store.describe(), "model": "NONE", "model_calls": 0,
            "complete_chart": whole_chart_complete, "source_coverage": source_coverage,
            "qualification": "Evidence observations and accepted assertions are distinct. Raster coverage is recomputed for each inspected source scope; missing extraction cannot prove negatives."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--input-pdf", type=Path)
    parser.add_argument("--parent-binding", type=Path)
    parser.add_argument("--resume-raster", type=Path, help="New continuation from an immutable no-inference OCR failure")
    parser.add_argument("--integrate-raster", type=Path,
                        help="Verify retained OCR/pixels and integrate supported assertions without new extraction/inference")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--vision", action="store_true", help="One opt-in installed local vision extraction call")
    parser.add_argument("--dictionary-assisted", action="store_true",
                        help="Use native-source names/codes to normalize observed OCR; no topology transfer")
    parser.add_argument("--questions", type=Path,
                        help="Run an existing execution-only CQ file after raster extraction, in both admission views")
    args = parser.parse_args(argv)
    payload = None
    if args.questions:
        if args.prepare or args.resume_raster:
            parser.error("--questions applies to a new raster extraction")
        payload = json.loads(args.questions.read_text(encoding="utf-8"))
        validate_cqs(payload)
    if args.prepare:
        if args.input_pdf or args.parent_binding or args.vision or args.resume_raster or args.dictionary_assisted or args.integrate_raster:
            parser.error("--prepare does not accept extraction inputs or inference")
        result = prepare_raster_source(args.root, args.run_dir)
        print(json.dumps({"status": "IMAGE_ONLY_INPUT_PREPARED", "sha256": result["raster_pdf_sha256"]}))
        return
    elif args.integrate_raster:
        if args.input_pdf or args.parent_binding or args.vision or args.resume_raster or args.dictionary_assisted:
            parser.error("--integrate-raster reuses retained artifacts; it accepts no extraction or model options")
        result = integrate_retained_raster(args.root, args.integrate_raster, args.run_dir)
    elif args.resume_raster:
        if args.input_pdf or args.parent_binding or not args.vision or args.dictionary_assisted:
            parser.error("--resume-raster needs --vision and no new extraction inputs")
        result = resume_raster_structure(args.root, args.resume_raster, args.run_dir)
        print(json.dumps({"status": result["status"], "model_calls": result["model_calls"], "ocr_reused": True}))
        return
    else:
        if not args.input_pdf or not args.parent_binding:
            parser.error("raster extraction requires --input-pdf and --parent-binding")
        result = ingest_source(args.root, args.input_pdf, args.parent_binding, args.run_dir,
            use_vision=args.vision, dictionary_assisted=args.dictionary_assisted)
    receipt = {"status": result["status"], "model_calls": result["model_calls"]}
    if payload is not None:
        if result["route"] == "native_pdf_text_and_vector_geometry":
            raise ValueError("Native QA uses the unchanged evidence_a1_cli --graph-qa interface")
        run_dir = Path(args.run_dir)
        if not run_dir.is_absolute():
            run_dir = args.root.resolve() / run_dir
        runtime = str((run_dir / "registry.db").resolve().relative_to(args.root.resolve()))
        qa = answer_raster_questions(args.root, result, payload, runtime_relpath=runtime)
        write_private_output(args.root, run_dir / "qa_answers.json", qa)
        receipt.update(qa_status=qa["status"], qa_questions=len(qa["answers"]))
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
