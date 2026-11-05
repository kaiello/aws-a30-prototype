"""Source-native full-page reader packets for the bounded Gate 6.7 diagnostic.

Gold expectations and application answers never enter this module. Packet construction
verifies byte identity and page bindings; it does not adjudicate source semantics.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any

import fitz


_SOURCE_LOCATOR = "AWS A3.0M/A3.0:2020 source page"


def build_source_packet(
    root: Path,
    source: dict,
    question: str,
    evidence: list[dict],
    *,
    max_pages: int = 2,
    dpi: int = 120,
) -> dict[str, Any]:
    """Return verified native text and PNG bytes from full source pages.

    Evidence uses the standard's body-page coordinates (printed = PDF index - 12).
    The caller may supply arbitrary additional metadata; only the explicit source
    fields below reach the reader. Empty evidence preserves the verified source
    identity so missing retrieval can be measured without inventing support.
    """
    if type(max_pages) is not int or max_pages < 1:
        raise ValueError("page budget must be a positive integer")
    if type(dpi) is not int or dpi < 1:
        raise ValueError("rendering dpi must be a positive integer")
    if not isinstance(question, str) or not isinstance(source, dict) or not isinstance(evidence, list):
        raise ValueError("question, source and evidence have invalid types")
    if len(evidence) > max_pages:
        raise ValueError("evidence exceeds the page budget")

    root = Path(root).resolve(strict=True)
    source_path = source.get("path")
    if not isinstance(source_path, str) or not source_path:
        raise ValueError("source path must be relative to the repository root")
    relative_path = Path(source_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("source path must remain inside the repository root")
    try:
        pdf_path = (root / relative_path).resolve(strict=True)
    except OSError as error:
        raise ValueError("source path is unavailable") from error
    if not pdf_path.is_relative_to(root) or not pdf_path.is_file():
        raise ValueError("source path escapes the repository root or is not a file")

    pdf_bytes = pdf_path.read_bytes()
    source_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    if source.get("sha256") != source_sha256:
        raise ValueError("source PDF SHA-256 does not match the pinned source")
    page_count = source.get("page_count")
    if type(page_count) is not int or page_count < 1:
        raise ValueError("source page_count must be a positive integer")

    packet_pages = []
    seen_ids = set()
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if len(document) != page_count:
            raise ValueError("source PDF page count does not match the pinned source")
        for binding in evidence:
            if not isinstance(binding, dict):
                raise ValueError("each evidence binding must be an object")
            index = binding.get("pdf_index")
            if type(index) is not int or not 0 <= index < page_count:
                raise ValueError("evidence PDF index is outside the source")
            if (type(binding.get("viewer_page")) is not int
                    or binding["viewer_page"] != index + 1
                    or type(binding.get("printed_page")) is not int
                    or binding["printed_page"] != index - 12):
                raise ValueError("evidence page coordinates do not match the source")
            evidence_id = binding.get("evidence_id")
            if evidence_id != f"aws2020:pdf:{index}:full":
                raise ValueError("evidence ID does not identify its full source page")
            if evidence_id in seen_ids:
                raise ValueError("duplicate evidence ID")
            seen_ids.add(evidence_id)
            if binding.get("crop") is not None:
                raise ValueError("this milestone accepts full source pages only")

            page = document[index]
            text = page.get_text()
            text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if ("page_text_sha256" in binding
                    and binding["page_text_sha256"] != text_sha256):
                raise ValueError("source page text hash does not match the evidence binding")
            image = page.get_pixmap(dpi=dpi).tobytes("png")
            packet_pages.append({
                "evidence_id": evidence_id,
                "pdf_index": index,
                "viewer_page": index + 1,
                "printed_page": index - 12,
                "locator": _SOURCE_LOCATOR,
                "crop": None,
                "source_sha256": source_sha256,
                "text_sha256": text_sha256,
                "image_sha256": hashlib.sha256(image).hexdigest(),
                "text": text,
                "image_base64": base64.b64encode(image).decode("ascii"),
            })

    return {
        "question": question,
        "source_sha256": source_sha256,
        "source_page_count": page_count,
        "evidence": packet_pages,
        "page_budget": max_pages,
        "rendering_dpi": dpi,
    }
