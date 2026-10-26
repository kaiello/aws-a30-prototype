"""Build and verify Annex B Archetype 3 stores (Figures B1–B6)."""
from pathlib import Path
import sys

# Ensure repository root is in sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.archetype_spatial_callout import build_annex_b_archetype3_stores


def main() -> int:
    pdf_path = root_dir / "data" / "AWS_A3.0_2020.pdf"
    glossary_store_path = root_dir / "storage" / "evidence_v2" / "clause4_ingest_001" / "glossary_store.json"
    annex_c_d_store_path = root_dir / "storage" / "evidence_v2" / "clause4_ingest_001" / "annex_c_d_store.json"
    output_dir = root_dir / "storage" / "evidence_v2" / "annex_b_archetype3_001"

    print(f"Building Annex B Archetype 3 stores from {pdf_path}...")
    res = build_annex_b_archetype3_stores(pdf_path, glossary_store_path, annex_c_d_store_path, output_dir)

    print("\n=== Ingestion Complete ===")
    manifest = res["unified_manifest"]
    print("Dataset:", manifest["dataset_name"])
    print("Standard:", manifest["standard"])
    print("Figures:", manifest["figures_ingested"])
    print("Metrics:")
    for k, v in manifest["metrics"].items():
        print(f"  {k}: {v}")

    print("\n=== Per-Figure Breakdown ===")
    for fig_id, store in res["figure_stores"].items():
        m = store["metrics"]
        print(f"{fig_id} ({store['official_title']}):")
        print(f"  Pages: {m['total_pages']} | Sub-panels: {m['total_sub_panels']} | Welds: {m['total_applicable_weld_edges']} | Continuations: {m['total_continuation_edges']} | Callouts: {m['total_callout_nodes']}")
        print(f"  Accepted nodes: {m['accepted_nodes_count']} | Candidate: {m['candidate_nodes_count']}")
        print(f"  Cross-clause joins: {m['cross_clause_joins_count']} | Annex C joins: {m['annex_c_joins_count']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
