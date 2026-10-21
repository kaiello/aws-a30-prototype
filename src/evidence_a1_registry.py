"""Read-only legacy registry identity join; never a source of chart facts."""
from pathlib import Path
import sqlite3


def a1_registry_binding(root):
    path = Path(root) / "storage/dual_layer_registry.db"
    if not path.is_file():
        raise ValueError("A1_REGISTRY_MISSING")
    try:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT id, node_type, image_file FROM evidence_nodes WHERE id=?",
                ("figure:figure_a1",)).fetchone()
            if row is None or row[1] != "Figure":
                raise ValueError("A1_REGISTRY_IDENTITY_MISSING")
            bridges = connection.execute(
                "SELECT ontology_id, rel_type, bridge_type FROM grounding_bridges "
                "WHERE evidence_id=? ORDER BY ontology_id, rel_type, bridge_type",
                (row[0],)).fetchall()
    except sqlite3.Error:
        raise ValueError("A1_REGISTRY_SCHEMA_INVALID") from None
    return {
        "registry_relpath": "storage/dual_layer_registry.db", "open_mode": "ro",
        "canonical_manifest_element_id": row[0], "verification": "candidate",
        "legacy_image_alias": row[2], "asset_resolution": "manifest_only",
        "edition_binding": "manifest_document_id_and_verified_pdf_sha256",
        "registry_has_edition_hash_columns": False,
        "bridges": [{"ontology_id": a, "rel_type": b, "bridge_type": c,
                     "verification": "candidate"} for a, b, c in bridges],
        "qualification": "Exact canonical element-ID identity join only. Legacy SQLite has no "
            "edition/source hash columns; its image alias and bridge descriptions do not "
            "establish asset identity, chart facts or semantic support.",
    }
