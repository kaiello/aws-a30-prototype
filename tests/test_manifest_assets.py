"""Exercise actual asset functions without importing model/database entry points."""
import ast
import importlib.util
from pathlib import Path
import re
import sys
import types
from unittest.mock import patch

import pytest
from src.standard_manifest import get_manifest, extract_references

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def figures():
    cfg = types.ModuleType("src.config")
    cfg.BASE_DIR = ROOT
    cfg.PARSED_FIGURES_DIR = ROOT / "parsed/figures"
    spec = importlib.util.spec_from_file_location("manifest_figure_functions", ROOT / "src/figure_inspectors.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"src.config": cfg}):
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def resolve_assets():
    tree = ast.parse((ROOT / "src/query.py").read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "resolve_multimodal_assets")
    ns = {"re": re, "Path": Path, "PARSED_FIGURES_DIR": ROOT / "parsed/figures",
          "PARSED_TABLES_DIR": ROOT / "parsed/tables", "get_manifest": get_manifest,
          "extract_references": extract_references, "TABLE_COMPANION_FIGURES": get_manifest().companions()}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "actual_query_asset_function", "exec"), ns)
    return ns[fn.name]


def test_primary_b6_is_not_a_continuation(figures):
    assert figures.resolve_figure_image_filename("Figure B6") == "Figure_B6_p99.png"


@pytest.mark.parametrize("label", ["B6", "b6", " figure b6 ", "Fig. B.6"])
def test_primary_resolver_retains_supported_shorthand(figures, label):
    assert figures.resolve_figure_image_filename(label) == "Figure_B6_p99.png"


def test_every_figure_retains_all_source_bound_assets(figures):
    manifest = get_manifest()
    for label in manifest.labels("figures"):
        data = figures.get_figure_data(label)
        assert data["image_files"] == [Path(p).name for p in manifest.asset_paths(label, {".png"})]
        assert len(data["image_files"]) == len(manifest.anchors(label))
        assert data["image_file"] == data["image_files"][0]
        assert data["groups"]  # Existing chip registry remains in use.


def test_plural_figures_and_unknown_prefixes(resolve_assets):
    figures, tables = resolve_assets("Figures B.24, B.25, and B.26. Figure B120; Table A10")
    assert [f["figure_id"] for f in figures] == ["Figure B24", "Figure B25", "Figure B26"]
    assert tables == []
    assert len(figures[0]["image_paths"]) == 6
    assert [a["pdf_index"] for a in figures[0]["source_anchors"]] == list(range(129, 135))


def test_b16_group_expands_without_guessing_a_single_member(resolve_assets):
    figures, _ = resolve_assets("Show Figure B16")
    assert [f["figure_id"] for f in figures] == ["Figure B16A", "Figure B16B", "Figure B16C"]
    assert len({f["image_path"] for f in figures}) == 3
    assert all(f["requested_as_group"] == "Figure B16" for f in figures)


def test_table_continuation_paths_and_companion_kind(resolve_assets):
    figures, tables = resolve_assets("Table A3")
    assert [Path(p).name for p in tables[0]["image_paths"]] == ["Table_A2_A3_p85.png", "Table_A3_p86.png"]
    assert [a["printed_label"] for a in tables[0]["source_anchors"]] == ["72", "73"]
    assert [f["figure_id"] for f in figures] == ["Figure A1"]
    assert figures[0]["relationship"] == "ui_companion"
    assert figures[0]["relationship_verification"] == "candidate"


def test_no_asset_is_invented_for_a_source_only_table(resolve_assets):
    assert get_manifest().source_anchors("Table D2")
    table, = resolve_assets("Table D2")[1]
    assert table["table_id"] == "Table D2"
    assert table["table_path"] is None and table["image_paths"] == []
    assert table["assets"] == [] and table["asset_status"] == "source_only"
    assert table["source_anchors"] == get_manifest().source_anchors("Table D2")



def test_range_asset_resolution_retains_existing_ids_and_continuation_order(resolve_assets):
    figures, tables = resolve_assets("Figures B6–B7; Tables D1–D3")
    assert [f["figure_id"] for f in figures] == ["Figure B6", "Figure B7"]
    assert [Path(p).name for p in figures[0]["image_paths"]] == [
        "Figure_B6_p99.png", "Figure_B6_p100.png", "Figure_B6_p101.png"]
    assert [a["element_id"] for a in figures[0]["source_anchors"]] == ["figure:figure_b6"] * 3
    assert [table["table_id"] for table in tables] == ["Table D1", "Table D2", "Table D3"]
    assert {key: tables[0][key] for key in ("table_id", "table_path", "image_paths", "source_anchors", "text_asset_verification")} == {
        "table_id": "Table D1",
        "table_path": str(ROOT / "parsed/tables/table_d1.md"),
        "image_paths": [],
        "source_anchors": get_manifest().source_anchors("Table D1"),
        "text_asset_verification": "candidate",
    }  # D1 keeps its existing candidate export; D2/D3 retain identity only.
    for table in tables[1:]:
        assert table["table_path"] is None and table["image_paths"] == table["assets"] == []
        assert table["asset_status"] == "source_only"
        assert table["source_anchors"] == get_manifest().source_anchors(table["table_id"])


@pytest.mark.parametrize("expression", ["Figures B54–B55", "Figures B15–B17", "Figures B16A–B16C"])
def test_invalid_ranges_do_not_resolve_partial_or_group_assets(resolve_assets, expression):
    assert resolve_assets(expression) == ([], [])
