"""Original redistributable toy manual. No AWS source or benchmark labels."""
from dataclasses import replace
import hashlib
from pathlib import Path
import struct
import zlib

from src.evidence_v2 import Evidence, EvidenceStore, evidence_id

EDITION = "fixture:toolcare:1@" + hashlib.sha256(b"Original toolcare fixture edition 1").hexdigest()


def png_bytes(color=(38, 105, 184)):
    """An actual 16x16 RGB PNG, deterministic and dependency-free."""
    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))
    rows = b"".join(b"\0" + bytes(color) * 16 for _ in range(16))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def fixture(root: Path):
    """Return a store whose definitions, row notes and figure pages are independent."""
    def make(kind, locator, content, **kwargs):
        return Evidence(evidence_id(EDITION, kind, locator, content), EDITION,
                        kind, locator, content, "synthetic", **kwargs)

    note = make("note", {"element_id": "Figure X1", "pdf_index": 4, "printed_page": "3", "order": 2},
                {"text": "The fixture drawing is illustrative only; never measure dimensions from it."})
    figure_pages = []
    for order, color in enumerate(((38, 105, 184), (223, 146, 49))):
        relpath = f"assets/figure_x1_{order}.png"
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = png_bytes(color)
        path.write_bytes(raw)
        figure_pages.append(make("figure_region", {
            "element_id": "Figure X1", "pdf_index": 3 + order,
            "printed_page": str(2 + order), "order": order,
            "region": [0.0, 0.0, 1.0, 1.0]}, {
                "caption": "Collar and sleeve installation" + (" (continued)" if order else ""),
                "asset_relpath": relpath, "asset_sha256": hashlib.sha256(raw).hexdigest(),
                "media_type": "image/png", "notes": [], "continuation_orders": [0, 1],
                "required_evidence_ids": [note.evidence_id]}))
    figure_pages[0] = replace(figure_pages[0], required_ids=(figure_pages[1].evidence_id, note.evidence_id))

    collar = make("definition", {"element_id": "Clause 1", "pdf_index": 0, "printed_page": "1", "order": 0}, {
        "headword": "collar", "sense": "retaining", "aliases": ["retaining ring"],
        "text": "A collar is a ring that retains a sleeve.",
        "qualifiers": ["Applicable only to the toy hand sprayer."],
        "exceptions": ["A split ring is excluded."],
        "notes": ["Loosen the collar before removing the sleeve."]})
    sleeve = make("definition", {"element_id": "Clause 1", "pdf_index": 0, "printed_page": "1", "order": 1}, {
        "headword": "sleeve", "sense": "cover", "aliases": [],
        "text": "A sleeve is a removable cover surrounding the tube.",
        "qualifiers": [], "exceptions": [], "notes": []}, relationships=({
            "predicate": "COMPARES_WITH", "target_id": collar.evidence_id,
            "qualification": "Only while the collar is tightened.", "verification": "synthetic"},))
    nozzles = [make("definition", {"element_id": "Clause 2", "pdf_index": 1, "printed_page": "2", "order": i}, {
        "headword": "nozzle", "sense": sense, "aliases": [], "text": text,
        "qualifiers": [qualifier], "exceptions": [], "notes": []}) for i, (sense, text, qualifier) in enumerate([
            ("air", "An air nozzle directs the air stream.", "Used with the dry-air accessory."),
            ("liquid", "A liquid nozzle directs the liquid stream.", "Used with the liquid accessory.")])]
    row = make("table_row", {"element_id": "Table X1", "pdf_index": 2, "printed_page": "2", "order": 0}, {
        "table_label": "Table X1", "headers": ["Material", "Cleaning solution", "Limit"],
        "cells": ["copper", "water", "20 C*"],
        "footnotes": ["* Applies only to an uncoated fixture sample."],
        "qualifiers": ["Toy toolcare guidance only."], "exceptions": ["Never use on energized equipment."],
        "notes": ["Dry after cleaning."]})
    items = [collar, sleeve, *nozzles, row, *figure_pages, note]
    return EvidenceStore(items), {"collar": collar, "sleeve": sleeve, "row": row,
                                 "figures": figure_pages, "note": note, "items": items}
