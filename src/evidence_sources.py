"""Bounded, local source projection. No credentials, network, index or store writes.

Only ``--extract-tables`` writes a new versioned derivative; legacy Markdown,
the manifest and SQLite registry remain unchanged. Extraction is source binding,
not semantic review. This module deliberately embeds no licensed excerpts.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from src.evidence_v2 import Evidence, evidence_id
from src.standard_manifest import load_manifest

TABLE_CACHE = Path("storage/evidence_v2/tables.v2.2.json")
TERMS = ("root face", "root opening", "bevel angle", "back weld", "backing weld", "root gap")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _normal(text):
    return " ".join(text.split())


def _source(root):
    manifest = load_manifest(root / "config/aws_a30_2020_manifest.json", root=root)
    document = manifest.document
    pdf_path = root / document["pdf_relpath"]
    if not pdf_path.is_file() or _hash(pdf_path.read_bytes()) != document["sha256"]:
        raise ValueError("EVIDENCE_SOURCE_MISSING_OR_STALE")
    return manifest, document["id"] + "@" + document["sha256"], pdf_path


def _make(edition, kind, locator, content, verification="source_bound", **kwargs):
    return Evidence(evidence_id(edition, kind, locator, content), edition, kind,
                    locator, content, verification, **kwargs)


def _spine_ids(root):
    """Read-only candidate identity links; descriptions never become source facts."""
    path = root / "storage/dual_layer_registry.db"
    if not path.is_file():
        return {}
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        rows = connection.execute(
            "SELECT id, name FROM ontology_nodes WHERE lower(name) IN (" +
            ",".join("?" for _ in TERMS) + ")", TERMS).fetchall()
    return {name.casefold(): identifier for identifier, name in rows}


def _definitions(root, manifest, edition, pdf_path):
    import fitz  # Optional extraction dependency; no model initialization.
    chunks_path = root / "parsed/text_chunks.jsonl"
    if not chunks_path.is_file():
        return []
    spine_ids = _spine_ids(root)
    result = []
    with fitz.open(pdf_path) as pdf:
        for line in chunks_path.read_text(encoding="utf-8").splitlines():
            chunk = json.loads(line)
            page = chunk.get("pdf_page")
            if chunk.get("clause") != "Clause 4" or type(page) is not int:
                continue
            raw = chunk["content"]
            for term in TERMS:
                # A headword has no preceding phrase on its line. Stop at the
                # next full headword; continuation lines are kept verbatim.
                match = re.search(r"(?m)^" + re.escape(term) + r"\.\s+", raw)
                if not match:
                    continue
                tail = raw[match.start():]
                end = re.search(r"\n(?=[a-z0-9][^\n.]{0,100}\.\s)", tail)
                text = tail[:end.start()] if end else tail
                # A bare navigation continuation such as 'root face.' at the
                # end of an unrelated entry is not a new definition.
                if not text.startswith(term + ". "):
                    continue
                native = pdf[page].get_text()
                if _normal(text) not in _normal(native):
                    continue
                start = match.start()
                locator = {"element_id": "Clause 4", "pdf_index": page,
                           "printed_page": manifest.document["pages"][page]["printed_label"],
                           "order": 0, "chunk_id": chunk["chunk_id"],
                           "text_span": [start, start + len(text)],
                           "chunk_sha256": _hash(raw.encode("utf-8"))}
                content = {"headword": term, "sense": "", "aliases": [],
                           "text": text, "qualifiers": [], "exceptions": [], "notes": [],
                           "extraction_method": "native_chunk_exact_pdf_text"}
                if term == "root opening":
                    # Attach the alias only when its complete native entry is
                    # present in the same page; do not infer it from the graph.
                    alias = "root gap. A nonstandard term for root opening."
                    if alias in raw and alias in _normal(native):
                        content["aliases"] = ["root gap"]
                        content["qualifiers"] = [alias]
                links = ()
                if term in spine_ids:
                    links = ({"predicate": "CANDIDATE_CONCEPT", "target_id": spine_ids[term],
                              "qualification": "SQLite name match only; derived identity, no semantic support",
                              "verification": "candidate"},)
                result.append(_make(edition, "definition", locator, content, relationships=links))
    return result


def _section_note(manifest, edition, label):
    section = manifest.section(label)
    locator = {"element_id": label, "pdf_indices": section["qualification_pdf_indices"],
               "order": 0, "metadata_path": "config/aws_a30_2020_manifest.json"}
    content = {"text": section["verification"]["note"],
               "normative_status": section["normative_status"],
               "qualifiers": [], "exceptions": [], "notes": [],
               "assessment_scope": "manifest_applicability_metadata"}
    return _make(edition, "note", locator, content)


def _figures(root, manifest, edition):
    """Exactly the ordered manifest-bound B6 pages, never a filename guess."""
    record = manifest.element("Figure B6")
    note = _section_note(manifest, edition, "Annex B")
    items = []
    for anchor in record["anchors"]:
        order = anchor["order"]
        assets = [a for a in record["assets"] if a["source_anchor_orders"] == [order]
                  and a["relpath"].lower().endswith(".png")]
        if len(assets) != 1:
            raise ValueError("EVIDENCE_FIGURE_ASSET_AMBIGUOUS")
        asset = assets[0]
        locator = {"element_id": "Figure B6", "pdf_index": anchor["pdf_index"],
                   "printed_page": anchor["printed_label"], "order": order,
                   "region": anchor["region"], "region_scope": "full_page"}
        content = {"caption": record["title"], "asset_relpath": asset["relpath"],
                   "asset_sha256": asset["sha256"], "media_type": "image/png",
                   "continuation_orders": [a["order"] for a in record["anchors"]],
                   "required_evidence_ids": [note.evidence_id],
                   "qualifiers": ["Full page; no certified panel crop.",
                                  "Annex B applicability is conflicting in the source manifest."],
                   "exceptions": [], "notes": []}
        # Missing/corrupt bytes remain an explicit requirement; reader validates
        # availability. Do not silently drop a required continuation page.
        items.append(_make(edition, "figure_region", locator, content))
    ids = tuple(item.evidence_id for item in items)
    return [note] + [replace(item, required_ids=tuple(i for i in ids if i != item.evidence_id) +
                            (note.evidence_id,)) for item in items]


def _table_lines(page, label):
    """Return native lines only inside the requested table's caption bounds."""
    lines = [line for block in page.get_text("dict")["blocks"] if "lines" in block
             for line in block["lines"]]
    captions = []
    for line in lines:
        text = "".join(span["text"] for span in line["spans"]).strip()
        if re.fullmatch(r"Table A\d+(?: \(Continued\))?", text):
            captions.append((line["bbox"][1], text))
    starts = [y for y, text in captions if text.startswith(label)]
    if len(starts) != 1:
        raise ValueError("EVIDENCE_TABLE_CAPTION_AMBIGUOUS")
    start = starts[0]
    end = min([y for y, _ in captions if y > start] + [page.rect.height - 60])
    selected = []
    for line in lines:
        box = line["bbox"]
        text = "".join(span["text"] for span in line["spans"]).strip()
        if start < box[1] < end and text:
            selected.append((box, text))
    return selected


def extract_tables(root: Path):
    """Read only the three authorized pages; return a versioned derivative."""
    import fitz
    manifest, edition, pdf_path = _source(root)
    rows, counts = [], {}
    with fitz.open(pdf_path) as pdf:
        for label in ("Table A2", "Table A3"):
            record = manifest.element(label)
            expected = ["Process", "Letter Designation"] if label == "Table A2" else ["Letter Designation", "Process"]
            count = 0
            for anchor in record["anchors"]:
                page = pdf[anchor["pdf_index"]]
                lines = _table_lines(page, label)
                headers = [(box, text) for box, text in lines if text in expected]
                if [text for _, text in headers] != expected * 2:
                    raise ValueError("EVIDENCE_TABLE_HEADERS_UNEXPECTED")
                first_data_y = max(box[3] for box, _ in headers)
                data = [(box, text) for box, text in lines if box[1] >= first_data_y]
                if len(data) % 2:
                    raise ValueError("EVIDENCE_TABLE_CELL_PAIR_INCOMPLETE")
                for i in range(0, len(data), 2):
                    (a, first), (b, second) = data[i:i+2]
                    # Both cells must be on one native row, one in each of the
                    # two physical columns of the left or right table block.
                    if abs(a[1] - b[1]) > 1.0 or not a[0] < b[0]:
                        raise ValueError("EVIDENCE_TABLE_CELL_GEOMETRY_AMBIGUOUS")
                    code = second if label == "Table A2" else first
                    if not re.fullmatch(r"[A-Z]+(?:-[A-Z]+)?", code):
                        raise ValueError("EVIDENCE_TABLE_CODE_UNEXPECTED")
                    region = [a[1]/page.rect.height, a[0]/page.rect.width,
                              max(a[3], b[3])/page.rect.height, b[2]/page.rect.width]
                    def normalized(box):
                        return [box[1]/page.rect.height, box[0]/page.rect.width,
                                box[3]/page.rect.height, box[2]/page.rect.width]
                    header_pair = headers[:2] if a[0] < page.rect.width / 2 else headers[2:]
                    locator = {"element_id": label, "pdf_index": anchor["pdf_index"],
                               "printed_page": anchor["printed_label"], "order": count,
                               "anchor_order": anchor["order"], "row_index": count,
                               "region": {"space": "pdf_page_unrotated", "origin": "top_left",
                                          "coordinate_order": "ymin_xmin_ymax_xmax", "normalized": True,
                                          "bbox": region}}
                    content = {"table_label": label, "title": record["title"],
                               "headers": expected, "cells": [first, second],
                               "cell_regions": [normalized(a), normalized(b)],
                               "header_regions": [normalized(box) for box, _ in header_pair],
                               "footnotes": [], "qualifiers": [], "exceptions": [], "notes": [],
                               "extraction_method": "native_pdf_line_pairs_geometry_v2",
                               "footnote_assessment": "No additional native lines after paired cells in this bounded table."}
                    rows.append(asdict(_make(edition, "table_row", locator, content)))
                    count += 1
            counts[label] = count
    return {"schema_version": "2.0.0", "edition_id": edition,
            "source_sha256": manifest.document["sha256"], "extraction_version": "native-table-pairs-v2.2",
            "counts": counts, "evidence": rows,
            "limits": ["Native text/geometry extraction, not semantic review.",
                       "Source spelling and designation discrepancies are retained verbatim.",
                       "No licensed excerpts or derivative cache may be published."]}


def load_query_evidence(root: Path, query: str) -> list[Evidence]:
    """Choose the isolated A1 image workflow before unrelated projections.

    A bare A1 is deliberately admitted to its identity-ambiguity gate; it is
    never silently interpreted as Annex A or the separate Table A1.
    """
    if re.search(r"(?<!\w)a1(?!\w)", query, re.IGNORECASE):
        from src.evidence_a1 import load_a1_evidence
        return load_a1_evidence(Path(root), query=query)
    return load_source_evidence(root)


def load_source_evidence(root: Path) -> list[Evidence]:
    root = Path(root)
    manifest, edition, pdf_path = _source(root)
    definitions = _definitions(root, manifest, edition, pdf_path)
    figures = _figures(root, manifest, edition)
    by_term = {item.content["headword"]: item for item in definitions}
    figure_start = next(item for item in figures if item.kind == "figure_region" and item.locator["order"] == 0)
    linked = []
    for item in definitions:
        edges, required = list(item.relationships), []
        if item.content["headword"] == "root gap" and "root opening" in by_term:
            # The exact native mapping was separately source-bound above.
            if _normal(item.content["text"]) == "root gap. A nonstandard term for root opening.":
                target = by_term["root opening"].evidence_id
                edges.append({"predicate": "ALIAS_FOR", "target_id": target,
                              "qualification": "nonstandard term for; exact native mapping",
                              "verification": "source_bound"})
                required.append(target)
        if item.content["aliases"] and "root gap" in by_term:
            required.append(by_term["root gap"].evidence_id)
        if re.search(r"\bFigures?\s+B6\b", item.content["text"]):
            edges.append({"predicate": "ILLUSTRATED_BY", "target_id": figure_start.evidence_id,
                          "qualification": "native See reference; navigation only, panel meaning unreviewed",
                          "verification": "candidate"})
        linked.append(replace(item, relationships=tuple(edges), required_ids=tuple(required)))
    result = linked + figures
    cache = root / TABLE_CACHE
    if cache.is_file():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        if (payload.get("schema_version") != "2.0.0" or payload.get("edition_id") != edition
                or payload.get("source_sha256") != manifest.document["sha256"]):
            raise ValueError("EVIDENCE_TABLE_CACHE_STALE")
        # A self-consistent hash is not proof of source support. Reproduce the
        # bounded three-page projection to detect row omission, mutation and
        # forged verification flags before admitting the derivative.
        canonical = extract_tables(root)
        if payload != json.loads(json.dumps(canonical, ensure_ascii=False)):
            raise ValueError("EVIDENCE_TABLE_CACHE_NOT_REPRODUCIBLE")
        for raw in payload["evidence"]:
            item = Evidence(**dict(raw, required_ids=tuple(raw.get("required_ids", ())),
                                   relationships=tuple(raw.get("relationships", ()))))
            if item.evidence_id != evidence_id(item.edition_id, item.kind, item.locator, item.content):
                raise ValueError("EVIDENCE_TABLE_CACHE_ID_MISMATCH")
            result.append(item)
    else:
        for label in ("Table A2", "Table A3"):
            result.append(_make(edition, "table_row", {"element_id": label, "order": 0},
                                {"table_label": label, "headers": [], "cells": [], "footnotes": [],
                                 "text": "Versioned structured extraction is missing; legacy table has no cells.",
                                 "notes": [], "qualifiers": [], "exceptions": [],
                                 "missing_evidence": "structured_table_cells"}, "candidate"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--extract-tables", action="store_true")
    args = parser.parse_args()
    if not args.extract_tables:
        parser.error("Use --extract-tables for the explicit three-page derivative write.")
    target = args.root / TABLE_CACHE
    if target.exists():
        parser.error("Versioned derivative already exists; inspect it instead of overwriting.")
    payload = extract_tables(args.root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(TABLE_CACHE), "counts": payload["counts"],
                      "assessment": "source extraction only; semantic review pending"}))


if __name__ == "__main__":
    main()
