"""Synthetic figure catalog projection; no registry, assets or provider is read."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalog_fixture(paths):
    tree = ast.parse((ROOT / "src/figure_inspectors.py").read_text(encoding="utf-8"))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in {"get_figure_data", "get_all_figures_catalog"}]

    class Manifest:
        def asset_paths(self, label, suffixes):
            assert label == "Figure X1"
            assert suffixes == {".png"}
            return list(paths)

        def source_anchors(self, label):
            return [{"order": index} for index in range(len(paths))]

    namespace = {"Dict": dict, "Any": object, "List": list, "Path": Path,
                 "FIGURE_INSPECTORS": {"Figure X1": {"groups": [{"chips": [{"label": "synthetic"}]}]}},
                 "get_manifest": lambda: Manifest(),
                 "_source_metadata": lambda label: {"title": "Synthetic continued figure", "page": "Annex X"},
                 "_enrich_chips_with_bboxes": lambda label, groups: groups}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "actual_figure_catalog", "exec"), namespace)
    return namespace["get_all_figures_catalog"]()


def test_catalog_preserves_all_declared_images_in_manifest_order_and_legacy_primary():
    entry, = catalog_fixture(["synthetic/primary.png", "synthetic/third.png", "synthetic/second.png"])
    assert entry["image_files"] == ["primary.png", "third.png", "second.png"]
    assert entry["image_file"] == "primary.png"
    assert entry["id"] == "Figure X1"
    assert entry["chip_count"] == 1


def test_catalog_keeps_explicit_empty_image_collection_without_inventing_primary():
    entry, = catalog_fixture([])
    assert entry["image_files"] == []
    assert entry["image_file"] == ""
