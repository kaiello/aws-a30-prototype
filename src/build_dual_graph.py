"""
build_dual_graph.py: Deterministic Projection of AWS A3.0 Knowledge Assets
into a Dual-Layer Epistemic Knowledge Graph.

Decouples:
1. Layer 1: Domain Ontology Layer (:Concept, :Process, :Discontinuity, :JointGeometry)
2. Layer 2: Normative Evidence Layer (:Document, :Clause, :Figure, :Callout, :Table, :TextChunk)
3. Inter-Layer Grounding Bridges ([:DEFINED_IN], [:ILLUSTRATED_BY], [:TABULATED_IN], [:JUSTIFIED_BY])

Executes 100% locally with zero cloud API calls and zero embedding costs.
Exports to:
- GraphML: storage/dual_layer_knowledge_graph.graphml
- SQLite: storage/dual_layer_registry.db (with FTS5 search)
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple
import networkx as nx

from src.config import STORAGE_DIR, PARSED_FIGURES_DIR, PARSED_TABLES_DIR
from src.figure_inspectors import FIGURE_INSPECTORS, FIGURE_CATEGORIES
from src.citation_checker import extract_citations
from src.standard_manifest import get_manifest

GRAPHML_RAW_PATH = STORAGE_DIR / "graph_chunk_entity_relation.graphml"
CHUNKS_KV_PATH = STORAGE_DIR / "kv_store_text_chunks.json"
ENTITIES_KV_PATH = STORAGE_DIR / "kv_store_full_entities.json"
RELATIONS_KV_PATH = STORAGE_DIR / "kv_store_full_relations.json"

DUAL_GRAPHML_PATH = STORAGE_DIR / "dual_layer_knowledge_graph.graphml"
DUAL_SQLITE_PATH = STORAGE_DIR / "dual_layer_registry.db"

# Master document specification
DOCUMENT_META = get_manifest().document_metadata()

STANDARD_CLAUSES = get_manifest().section_metadata()

STANDARD_TABLES = get_manifest().table_metadata()

def slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip()).strip('_').lower()
    return s[:64]

def classify_ontology_entity(name: str, desc: str) -> Tuple[str, str]:
    """
    Classifies an entity into a specific ontology node_type and standard_status.
    Returns: (node_type, standard_status)
    """
    lower_name = name.lower()
    lower_desc = desc.lower()

    # Determine status
    if "nonstandard" in lower_desc or "nonstandard" in lower_name:
        status = "nonstandard"
    elif "deleted in the 2020 edition" in lower_desc or "deprecated" in lower_desc:
        status = "deprecated"
    else:
        status = "standard"

    # Determine technical node_type
    if any(k in lower_name for k in ["welding", "brazing", "soldering", "cutting", "spraying", "gouging", "process"]) or \
       re.search(r'\b[A-Z]{2,6}(-[A-Z0-9]+)?\b', name):
        node_type = "Process"
    elif any(k in lower_name for k in ["crack", "undercut", "underfill", "porosity", "inclusion", "discontinuity", "spatter", "incomplete fusion", "incomplete penetration"]):
        node_type = "Discontinuity"
    elif any(k in lower_name for k in ["angle", "throat", "bevel", "groove", "root", "radius", "land", "face", "opening", "edge"]):
        node_type = "JointGeometry"
    elif any(k in lower_name for k in ["symbol", "tail", "arrow", "weld symbol"]):
        node_type = "WeldSymbol"
    elif any(k in lower_name for k in ["position", "1g", "2g", "3g", "4g", "5g", "6g", "6gr", "1f", "2f", "3f", "4f", "5f"]):
        node_type = "TestPosition"
    else:
        node_type = "Concept"

    return node_type, status

def build_dual_layer_graph() -> nx.MultiDiGraph:
    print("\n" + "="*70)
    print("STARTING DUAL-LAYER EPISTEMIC GRAPH PROJECTION")
    print("="*70)

    G = nx.MultiDiGraph()

    # =========================================================================
    # PART 1: BUILD NORMATIVE EVIDENCE LAYER
    # =========================================================================
    print("\n[1/4] Building Normative Evidence Layer...")

    # 1.1 Master Document Node
    doc_id = DOCUMENT_META["id"]
    G.add_node(
        doc_id,
        layer="evidence",
        node_type="Document",
        title=DOCUMENT_META["title"],
        edition=DOCUMENT_META["edition"],
        publisher=DOCUMENT_META["publisher"],
        total_pages=DOCUMENT_META["total_pages"],
        source_sha256=DOCUMENT_META["source_sha256"],
        name=DOCUMENT_META["title"]
    )

    # 1.2 Clause Nodes
    for cl in STANDARD_CLAUSES:
        cl_id = cl["id"]
        G.add_node(
            cl_id,
            layer="evidence",
            node_type="Clause",
            clause_num=cl["clause_num"],
            title=cl["title"],
            pages=cl["pages"],
            normative_status=cl["normative_status"],
            name=f"{cl['clause_num']}: {cl['title']}"
        )
        G.add_edge(doc_id, cl_id, key="CONTAINS_CLAUSE", rel_type="CONTAINS_CLAUSE", layer="evidence")

    # 1.3 Figure Nodes & Callout Nodes
    for fig_id, fig_info in FIGURE_INSPECTORS.items():
        clean_num = fig_id.replace("Figure ", "").strip()
        fig_node_id = f"figure:{slugify(fig_id)}"
        
        # Decide parent clause (Annex A vs Annex B)
        parent_clause = "clause:annex_a" if clean_num.startswith("A") else "clause:annex_b"

        G.add_node(
            fig_node_id,
            layer="evidence",
            node_type="Figure",
            figure_id=fig_id,
            title=fig_info.get("title", ""),
            page=fig_info.get("page", ""),
            category=fig_info.get("category", ""),
            image_file=Path(get_manifest().asset_paths(fig_id, {".png"})[0]).name,
            name=f"{fig_id} - {fig_info.get('title', '')}"
        )
        G.add_edge(parent_clause, fig_node_id, key="CONTAINS_FIGURE", rel_type="CONTAINS_FIGURE", layer="evidence")

        # Callout Nodes (from interactive chips)
        for g_idx, grp in enumerate(fig_info.get("groups", [])):
            for c_idx, chip in enumerate(grp.get("chips", [])):
                callout_id = f"callout:{slugify(fig_id)}_{slugify(chip['label'])}_{c_idx}"
                G.add_node(
                    callout_id,
                    layer="evidence",
                    node_type="Callout",
                    label=chip["label"],
                    query=chip["query"],
                    figure_id=fig_id,
                    group_title=grp.get("group_title", ""),
                    name=f"{fig_id} Callout: {chip['label']}"
                )
                G.add_edge(fig_node_id, callout_id, key="HAS_CALLOUT", rel_type="HAS_CALLOUT", layer="evidence")

    # 1.4 Table Nodes
    for tbl in STANDARD_TABLES:
        tbl_node_id = tbl["id"]
        G.add_node(
            tbl_node_id,
            layer="evidence",
            node_type="Table",
            table_num=tbl["table_num"],
            title=tbl["title"],
            page=tbl["page"],
            name=f"{tbl['table_num']}: {tbl['title']}"
        )
        G.add_edge(tbl["clause"], tbl_node_id, key="CONTAINS_TABLE", rel_type="CONTAINS_TABLE", layer="evidence")

    # 1.5 Text Chunk Nodes
    chunks_data = {}
    if CHUNKS_KV_PATH.exists():
        with open(CHUNKS_KV_PATH, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

    for chunk_key, c_info in chunks_data.items():
        chunk_node_id = f"chunk:{chunk_key}"
        doc_ref = c_info.get("full_doc_id", "")
        content = c_info.get("content", "")
        
        # Map full_doc_id to parent clause
        parent_clause = "clause:clause_4"
        if "annex_a" in doc_ref:
            parent_clause = "clause:annex_a"
        elif "annex_b" in doc_ref:
            parent_clause = "clause:annex_b"
        elif "annex_c" in doc_ref:
            parent_clause = "clause:annex_c"
        elif "annex_d" in doc_ref:
            parent_clause = "clause:annex_d"
        elif "annex_e" in doc_ref:
            parent_clause = "clause:annex_e"
        elif "annex_f" in doc_ref:
            parent_clause = "clause:annex_f"

        G.add_node(
            chunk_node_id,
            layer="evidence",
            node_type="TextChunk",
            chunk_id=chunk_key,
            full_doc_id=doc_ref,
            char_length=len(content),
            preview=content[:160].replace("\n", " "),
            name=f"Text Chunk: {chunk_key}"
        )
        G.add_edge(parent_clause, chunk_node_id, key="CONTAINS_CHUNK", rel_type="CONTAINS_CHUNK", layer="evidence")

    print(f"Evidence Layer built: {sum(1 for _, d in G.nodes(data=True) if d.get('layer') == 'evidence')} nodes, {sum(1 for _, _, d in G.edges(data=True) if d.get('layer') == 'evidence')} edges.")

    # =========================================================================
    # PART 2: BUILD DOMAIN ONTOLOGY LAYER
    # =========================================================================
    print("\n[2/4] Building Domain Ontology Layer...")

    raw_G = nx.read_graphml(GRAPHML_RAW_PATH)
    print(f"Loaded raw GraphML: {raw_G.number_of_nodes()} nodes, {raw_G.number_of_edges()} edges.")

    # Structural entity filters to avoid duplicating raw document structural nodes in ontology
    structural_keywords = ["figure a", "figure b", "table a", "table d", "clause ", "annex ", "aws a3.0"]

    ontology_nodes_added = 0
    raw_to_onto_map = {}

    for n, d in raw_G.nodes(data=True):
        lower_n = n.strip().lower()
        
        # Skip pure structural nodes (they are in the evidence layer)
        if any(lower_n == kw or (lower_n.startswith(kw) and len(lower_n) < 16) for kw in structural_keywords):
            continue

        desc = d.get("description", "")
        node_type, status = classify_ontology_entity(n, desc)
        onto_id = f"onto:{slugify(n)}"
        raw_to_onto_map[n] = onto_id

        G.add_node(
            onto_id,
            layer="ontology",
            node_type=node_type,
            name=n,
            description=desc,
            standard_status=status,
            raw_entity_type=d.get("entity_type", "concept"),
            source_chunks=d.get("source_id", "")
        )
        ontology_nodes_added += 1

    # Transfer semantic intra-ontology edges
    ontology_edges_added = 0
    for u, v, d in raw_G.edges(data=True):
        if u in raw_to_onto_map and v in raw_to_onto_map:
            u_onto = raw_to_onto_map[u]
            v_onto = raw_to_onto_map[v]
            
            # Infer specific semantic relation
            keywords = d.get("keywords", "").lower()
            desc = d.get("description", "").lower()
            
            if "nonstandard" in desc or "nonstandard" in keywords:
                rel = "NONSTANDARD_FOR"
            elif "subset" in desc or "is a" in desc or "type of" in desc:
                rel = "IS_A"
            elif "geometry" in desc or "angle" in desc or "throat" in desc:
                rel = "HAS_GEOMETRY"
            elif "contrast" in desc or "opposite" in desc or "versus" in desc:
                rel = "CONTRASTS_WITH"
            else:
                rel = "SEMANTIC_RELATION"

            G.add_edge(
                u_onto,
                v_onto,
                key=rel,
                rel_type=rel,
                layer="ontology",
                weight=d.get("weight", 1.0),
                description=d.get("description", "")
            )
            ontology_edges_added += 1

    print(f"Ontology Layer built: {ontology_nodes_added} concept nodes, {ontology_edges_added} semantic edges.")

    # =========================================================================
    # PART 3: ESTABLISH INTER-LAYER EPISTEMIC GROUNDING BRIDGES
    # =========================================================================
    print("\n[3/4] Wiring Inter-Layer Epistemic Grounding Bridges...")

    bridges_added = 0

    # 3.1 Bridge Concept -> TextChunk (DEFINED_IN)
    for onto_id, d in list(G.nodes(data=True)):
        if d.get("layer") != "ontology":
            continue
        
        source_id_str = d.get("source_chunks", "")
        if source_id_str:
            chunks_referenced = [s.strip() for s in source_id_str.split("<SEP>") if s.strip()]
            for ch in chunks_referenced:
                ch_node_id = f"chunk:{ch}"
                if G.has_node(ch_node_id):
                    G.add_edge(
                        onto_id,
                        ch_node_id,
                        key="DEFINED_IN",
                        rel_type="DEFINED_IN",
                        layer="grounding",
                        bridge_type="text_definition"
                    )
                    bridges_added += 1

    # 3.2 Bridge Concept -> Figure & Callouts (ILLUSTRATED_BY)
    # Check raw edges pointing to Figures
    for u, v, d in raw_G.edges(data=True):
        if u in raw_to_onto_map:
            u_onto = raw_to_onto_map[u]
            # Does v point to a figure?
            fig_match = re.search(r'Figure\s+([AB][0-9]{1,2}[A-Z]?)', v, re.IGNORECASE)
            if fig_match:
                fig_num = fig_match.group(1).upper()
                fig_key = f"Figure {fig_num}"
                fig_node_id = f"figure:{slugify(fig_key)}"
                if G.has_node(fig_node_id):
                    G.add_edge(
                        u_onto,
                        fig_node_id,
                        key="ILLUSTRATED_BY",
                        rel_type="ILLUSTRATED_BY",
                        layer="grounding",
                        bridge_type="figure_reference",
                        description=d.get("description", "")
                    )
                    bridges_added += 1

    # Match Callout Labels to Ontology Concepts
    callout_nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("node_type") == "Callout"]
    ontology_lookup = {d.get("name", "").lower(): n for n, d in G.nodes(data=True) if d.get("layer") == "ontology"}

    for c_id, c_data in callout_nodes:
        lbl = c_data.get("label", "").lower()
        # Clean label e.g. "Root Face (Land)" -> "root face"
        clean_lbl = re.sub(r'\(.*?\)', '', lbl).strip()
        
        target_onto = ontology_lookup.get(clean_lbl) or ontology_lookup.get(lbl)
        if target_onto:
            G.add_edge(
                target_onto,
                c_id,
                key="ILLUSTRATED_BY",
                rel_type="ILLUSTRATED_BY",
                layer="grounding",
                bridge_type="diagram_callout"
            )
            bridges_added += 1

    # 3.3 Bridge Concept -> Tables (TABULATED_IN & HISTORICALLY_RECORDED_IN)
    for u, v, d in raw_G.edges(data=True):
        if u in raw_to_onto_map:
            u_onto = raw_to_onto_map[u]
            tbl_match = re.search(r'Table\s+([AD][0-9]{1,2})', v, re.IGNORECASE)
            if tbl_match:
                tbl_num = tbl_match.group(1).upper()
                tbl_key = f"table:table_{tbl_num.lower()}"
                if G.has_node(tbl_key):
                    rel = "HISTORICALLY_RECORDED_IN" if "D" in tbl_num else "TABULATED_IN"
                    G.add_edge(
                        u_onto,
                        tbl_key,
                        key=rel,
                        rel_type=rel,
                        layer="grounding",
                        bridge_type="table_matrix",
                        description=d.get("description", "")
                    )
                    bridges_added += 1

    # 3.4 Bridge Concept -> Annex C Rationale (JUSTIFIED_BY)
    annex_c_node = "clause:annex_c"
    for onto_id, d in G.nodes(data=True):
        if d.get("layer") == "ontology":
            sources = d.get("source_chunks", "")
            if "annex_c" in sources:
                G.add_edge(
                    onto_id,
                    annex_c_node,
                    key="JUSTIFIED_BY",
                    rel_type="JUSTIFIED_BY",
                    layer="grounding",
                    bridge_type="committee_rationale"
                )
                bridges_added += 1

    print(f"Grounding Bridges wired: {bridges_added} inter-layer edges established.")

    # =========================================================================
    # PART 4: EXPORT TO GRAPHML & SQLITE
    # =========================================================================
    print("\n[4/4] Exporting Dual-Layer Knowledge Graph...")

    # Convert complex dict attributes to string for GraphML standard compliance
    export_G = nx.MultiDiGraph()
    for n, d in G.nodes(data=True):
        clean_d = {}
        for k, v in d.items():
            clean_d[k] = str(v) if not isinstance(v, (int, float, str, bool)) else v
        export_G.add_node(n, **clean_d)

    for u, v, k, d in G.edges(keys=True, data=True):
        clean_d = {}
        for ek, ev in d.items():
            clean_d[ek] = str(ev) if not isinstance(ev, (int, float, str, bool)) else ev
        export_G.add_edge(u, v, key=str(k), **clean_d)

    nx.write_graphml(export_G, DUAL_GRAPHML_PATH)
    print(f"Exported GraphML to: {DUAL_GRAPHML_PATH}")

    # Export to SQLite with FTS5
    export_to_sqlite(G, DUAL_SQLITE_PATH)
    print(f"Exported SQLite database to: {DUAL_SQLITE_PATH}")

    print("\n" + "="*70)
    print("DUAL-LAYER PROJECTION COMPLETE!")
    print(f"Total Nodes: {G.number_of_nodes()} (Ontology: {ontology_nodes_added}, Evidence: {G.number_of_nodes() - ontology_nodes_added})")
    print(f"Total Edges: {G.number_of_edges()} (Semantic: {ontology_edges_added}, Evidence: {sum(1 for _, _, d in G.edges(data=True) if d.get('layer') == 'evidence')}, Grounding: {bridges_added})")
    print("="*70 + "\n")

    return G

def export_to_sqlite(G: nx.MultiDiGraph, db_path: Path):
    """Creates a fast, indexed SQLite database for the dual-layer registry."""
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE ontology_nodes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        node_type TEXT NOT NULL,
        standard_status TEXT NOT NULL,
        description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE evidence_nodes (
        id TEXT PRIMARY KEY,
        node_type TEXT NOT NULL,
        name TEXT NOT NULL,
        page TEXT,
        image_file TEXT,
        preview TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE grounding_bridges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ontology_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        rel_type TEXT NOT NULL,
        bridge_type TEXT,
        description TEXT,
        FOREIGN KEY (ontology_id) REFERENCES ontology_nodes(id),
        FOREIGN KEY (evidence_id) REFERENCES evidence_nodes(id)
    );
    """)

    # Populate tables
    for n, d in G.nodes(data=True):
        if d.get("layer") == "ontology":
            cur.execute(
                "INSERT INTO ontology_nodes VALUES (?, ?, ?, ?, ?)",
                (n, d.get("name", ""), d.get("node_type", "Concept"), d.get("standard_status", "standard"), d.get("description", ""))
            )
        elif d.get("layer") == "evidence":
            cur.execute(
                "INSERT INTO evidence_nodes VALUES (?, ?, ?, ?, ?, ?)",
                (n, d.get("node_type", ""), d.get("name", ""), d.get("page", ""), d.get("image_file", ""), d.get("preview", ""))
            )

    for u, v, k, d in G.edges(keys=True, data=True):
        if d.get("layer") == "grounding":
            cur.execute(
                "INSERT INTO grounding_bridges (ontology_id, evidence_id, rel_type, bridge_type, description) VALUES (?, ?, ?, ?, ?)",
                (u, v, d.get("rel_type", "GROUNDED_IN"), d.get("bridge_type", ""), d.get("description", ""))
            )

    # Create FTS5 virtual table for instant full-text search
    cur.execute("""
    CREATE VIRTUAL TABLE ontology_fts USING fts5(
        id,
        name,
        node_type,
        standard_status,
        description
    );
    """)

    cur.execute("""
    INSERT INTO ontology_fts SELECT id, name, node_type, standard_status, description FROM ontology_nodes;
    """)

    # Indices
    cur.execute("CREATE INDEX idx_bridge_onto ON grounding_bridges(ontology_id);")
    cur.execute("CREATE INDEX idx_bridge_evid ON grounding_bridges(evidence_id);")
    cur.execute("CREATE INDEX idx_evid_type ON evidence_nodes(node_type);")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    build_dual_layer_graph()
