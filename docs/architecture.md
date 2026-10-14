# System Architecture: AWS A3.0 Multimodal Prototype

This document specifies the technical architecture, data structures, storage layers, graph schema, epistemic verification pipeline, and runtime interfaces for the **AWS A3.0 Standalone Multimodal Prototype**.

---

## 1. System Overview & Data Flow

The system operates on an offline-first, multimodal, and epistemically grounded architecture designed to query and audit **AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions**.

```mermaid
flowchart TB
    subgraph Ingestion ["1. Document Ingestion & Multimodal Extraction"]
        PDF["AWS A3.0 PDF<br/>(190 Pages)"] --> Extractor["Multimodal Extractor<br/>(PyMuPDF + Docling)"]
        Extractor --> Chunks["Text Chunks JSONL<br/>(Clauses 1–4, Annex C & F)"]
        Extractor --> Tables["Structured Markdown Tables<br/>(Annex A Tables A1–A5, Annex D)"]
        Extractor --> Figs["180 DPI High-Res PNGs<br/>(Annex B Figures B1–B54, A1–A6)"]
        Figs --> Chips["Interactive Chip Registry<br/>(267+ Callout Chips in src/figure_inspectors.py)"]
    end

    subgraph DualGraphStorage ["2. Dual-Layer Epistemic Knowledge Graph"]
        direction TB
        subgraph OntologyLayer ["Domain Ontology Layer (2,522 Nodes, 3,254 Edges)"]
            C_Concept[":Concept (e.g., CJP, Root Face)"]
            C_Proc[":Process (e.g., GMAW-P, GTAW)"]
            C_Geom[":JointGeometry (e.g., Bevel Angle)"]
            C_Disc[":Discontinuity (e.g., Undercut)"]
            C_Concept -->|":HAS_GEOMETRY"| C_Geom
            C_Proc -->|":IS_A"| C_Concept
        end

        subgraph Bridges ["5,854 Epistemic Grounding Bridges"]
            B1["[:DEFINED_IN]"]
            B2["[:ILLUSTRATED_BY]"]
            B3["[:TABULATED_IN]"]
            B4["[:JUSTIFIED_BY]"]
            B5["[:HISTORICALLY_RECORDED_IN]"]
        end

        subgraph EvidenceLayer ["Normative Evidence Layer (471 Nodes, 512 Edges)"]
            E_Doc[":Document (AWS A3.0:2020)"]
            E_Clause[":Clause (Clause 4, Annexes A–F)"]
            E_Fig[":Figure (60 Standard Figures)"]
            E_Callout[":Callout (267 Drawing Chips)"]
            E_Table[":Table (Tables A1–A3, D1–D6)"]
            E_Chunk[":TextChunk (164 Grounded Chunks)"]
            E_Doc --> E_Clause
            E_Clause --> E_Fig
            E_Fig --> E_Callout
            E_Clause --> E_Table
            E_Clause --> E_Chunk
        end

        OntologyLayer -.-> Bridges -.-> EvidenceLayer
    end

    subgraph StorageBackends ["3. Storage & Index Substrates"]
        GraphML["GraphML File<br/>storage/dual_layer_knowledge_graph.graphml"]
        SQLiteDB["SQLite FTS5 Registry<br/>storage/dual_layer_registry.db"]
        NanoVDB["NanoVectorDB<br/>storage/vdb_entities.json"]
        KVStore["Local JSON KV Stores<br/>storage/kv_store_*.json"]
    end

    subgraph RuntimeEngine ["4. Query & Verification Core"]
        UserQuery["Natural Language Query"] --> NLQ["Hybrid NLQ Engine<br/>(src/query.py / LightRAG 1.5.7)"]
        NLQ --> LLM["Google Gemini 2.0 Flash<br/>(Reasoning & Synthesis)"]
        LLM --> CandidateAnswer["Candidate Structured Answer"]
        CandidateAnswer --> Verifier["Epistemic Verifier<br/>(src/epistemic_verifier.py)"]
        Verifier --> AuditReport["Epistemic Trace Manifest<br/>(Provenance Score 0.0–1.0)"]
    end

    subgraph Presentation ["5. Presentation & Evaluation"]
        AuditReport --> WebUI["Web Visual Explorer (Port 8000)<br/>(Interactive Chips + Provenance Badges)"]
        AuditReport --> Benchmark["Automated 50-Item Scorer<br/>(eval/test_scorer.py)"]
    end

    Ingestion --> DualGraphStorage
    DualGraphStorage --> StorageBackends
    StorageBackends --> RuntimeEngine
```

---

## 2. The Dual-Layer Epistemic Graph Architecture

A core innovation in this prototype (completed in Card 07) is the complete structural separation of **what concepts mean** (the domain ontology) from **where and how they are proven** (the normative evidence).

### Layer 1: Domain Ontology Layer
Represents abstract welding domain knowledge independently of the document typography:
- **Node Labels**:
  - `:Concept`: Core welding, thermal, or physical concepts (e.g., *Complete Joint Penetration*, *Actual Throat*, *Thermal Gouging*).
  - `:Process`: Specific welding, thermal cutting, spraying, or allied processes (e.g., `GMAW-P`, `GTAW`, `SMAW`, `FOW`).
  - `:JointGeometry`: Edge preparations, angles, and fit-up characteristics (e.g., *Bevel Angle*, *Root Opening*, *Groove Face*).
  - `:Discontinuity`: Imperfections, flaws, and profile deviations (e.g., *Undercut*, *Overlap*, *Porosity*).
  - `:WeldSymbol`: Graphical weld symbol representations and standard signifiers.
  - `:TestPosition`: Standard qualification orientations (e.g., `1G`, `2F`, `5G`, `6GR`).
- **Node Properties**:
  - `name`: Standard canonical term name.
  - `description`: Formal technical explanation.
  - `standard_status`: Categorized as `standard`, `nonstandard` (e.g., deprecated shop slang), or `deprecated`.
  - `layer`: `"ontology"`.
- **Intra-Ontology Semantic Edges**:
  - `[:IS_A]` / `[:SUBPROCESS_OF]`: Process taxonomic hierarchy.
  - `[:HAS_GEOMETRY]`: Joint-to-feature relations.
  - `[:NONSTANDARD_FOR]`: Directed mapping from deprecated slang to normative standard terms (e.g., `short arc` $\to$ `short circuiting transfer`).
  - `[:CONTRASTS_WITH]`: Fine-grained disambiguation (e.g., `root opening` $\leftrightarrow$ `root face`).

### Layer 2: Normative Evidence Layer
Represents the physical, structural hierarchy of **AWS A3.0M/A3.0:2020**:
- **Node Labels**:
  - `:Document`: Master standard root node (`AWS A3.0M/A3.0:2020`).
  - `:Clause`: Formal document sections (Clause 1–4, Annex A–F).
  - `:Figure`: All 60 standard engineering drawings and classification charts.
  - `:Callout`: Specific labeled callout coordinates/chips on technical diagrams.
  - `:Table`: Master process matrices and historical revision tables.
  - `:TextChunk`: Verbatim, location-tagged text segments.
- **Node Properties**:
  - `id` / `figure_id` / `table_id` / `chunk_id`.
  - `printed_page` and `pdf_page`.
  - `image_file` or `text_file` relative paths on disk.
  - `layer`: `"evidence"`.
- **Intra-Evidence Structural Edges**:
  - `[:CONTAINS_CLAUSE]`: `:Document` $\to$ `:Clause`
  - `[:CONTAINS_FIGURE]`: `:Clause` $\to$ `:Figure`
  - `[:CONTAINS_TABLE]`: `:Clause` $\to$ `:Table`
  - `[:CONTAINS_CHUNK]`: `:Clause` $\to$ `:TextChunk`
  - `[:HAS_CALLOUT]`: `:Figure` $\to$ `:Callout`

### Inter-Layer Epistemic Grounding Bridges
These directed, typed edges cross the boundary between Layer 1 and Layer 2, providing verifiable mathematical proof that a technical claim is tethered to standard text or diagrams:
- `[:DEFINED_IN]`: `:Concept` $\to$ `:TextChunk` (cites exact clause, printed page, and quote).
- `[:ILLUSTRATED_BY]`: `:Concept` / `:JointGeometry` $\to$ `:Figure` or `:Callout` (links concept to exact visual callout chip).
- `[:TABULATED_IN]`: `:Process` $\to$ `:Table` (links letter code to process master table row).
- `[:JUSTIFIED_BY]`: `:Concept` $\to$ `:Clause` (links terms to committee rationale in Annex C).
- `[:HISTORICALLY_RECORDED_IN]`: `:Concept` $\to$ `:Table` (links revision history to Annex D tables).

---

## 3. Storage & Registry Implementation

The system deliberately avoids complex database servers (no Neo4j server, no Docker daemons) to maintain zero-cost local reproducibility.

```mermaid
classDiagram
    class DualLayerKnowledgeGraph {
        +GraphML export: 2,993 nodes, 9,579 edges
        +Layer attribute: ontology vs evidence
        +Fast NetworkX in-memory traversal
    }
    class SQLiteRegistryDB {
        +ontology_terms table (id, name, type, status, layer)
        +evidence_nodes table (id, type, clause, page, file_path)
        +epistemic_bridges table (source, target, bridge_type, properties)
        +ontology_fts (SQLite FTS5 virtual table for instant full-text search)
    }
    class NanoVectorDB {
        +Entity semantic vectors (768-dim)
        +Relationship semantic vectors (768-dim)
        +Text chunk vectors (768-dim)
    }
    class LocalKVStores {
        +kv_store_full_entities.json
        +kv_store_full_relations.json
        +kv_store_text_chunks.json
        +kv_store_llm_response_cache.json
    }

    DualLayerKnowledgeGraph <--> SQLiteRegistryDB : Synchronized Export
    DualLayerKnowledgeGraph <--> LocalKVStores : Built from Chunks
    NanoVectorDB <--> LocalKVStores : Embedding Projections
```

1. **GraphML Substrate** ([`storage/dual_layer_knowledge_graph.graphml`](file:///C:/Users/kenai/aws-a30-prototype/storage/dual_layer_knowledge_graph.graphml)):
   - Total Nodes: **2,993** (2,522 Ontology + 471 Evidence).
   - Total Edges: **9,579** (3,254 Semantic + 512 Structural + 5,854 Epistemic Bridges).
   - Standard format loadable by Gephi, Cytoscape, NetworkX, and iGraph.
2. **SQLite Registry & FTS5** ([`storage/dual_layer_registry.db`](file:///C:/Users/kenai/aws-a30-prototype/storage/dual_layer_registry.db)):
   - Implements native SQLite `FTS5` full-text search index (`ontology_fts`) for sub-millisecond keyword lookup.
   - Foreign-key relational schema enforcing layer integrity and bridge consistency.
3. **NanoVectorDB & Gemini Embeddings**:
   - `storage/vdb_chunks.json`, `storage/vdb_entities.json`, `storage/vdb_relationships.json`.
   - Embeddings generated via Google Gemini `models/text-embedding-004` (768 dimensions).
4. **Local Response & Extraction Cache**:
   - `storage/kv_store_llm_response_cache.json` caches model inference, allowing repeat runs with zero cloud costs.

---

## 4. Multimodal Perception & Asset Pipeline

The PDF stores engineering diagrams as vector drawings inside `/Form` XObjects rather than embedded JPEG/PNG rasters. 

```mermaid
sequenceDiagram
    participant PDF as AWS A3.0 PDF
    participant PyMuPDF as PyMuPDF Extractor
    participant Catalog as Figure Inspector Registry (src/figure_inspectors.py)
    participant Disk as Parsed Assets (parsed/figures/)
    participant UI as Web Visual Explorer

    PDF->>PyMuPDF: Parse page stream & vector /Form XObjects
    PyMuPDF->>Disk: Render 180 DPI high-resolution PNGs
    Catalog->>Disk: Map Figure IDs (A1–A6, B1–B54) to PNG files
    Catalog->>Catalog: Register 267+ Callout Chips with pixel coordinates
    UI->>Catalog: Fetch Figure manifest & Chips on user query
    UI->>Disk: Stream high-res PNG to browser canvas
    UI->>UI: Render interactive clickable chip overlays
```

1. **High-Resolution Vector Rendering**:
   - PyMuPDF renders all 60 standard figures at 180 DPI, producing crisp technical diagrams without loss of legibility on fine line work and weld symbols.
   - Multi-figure PDF pages (e.g., `B16A`, `B16B`, `B16C` on page 113) are segmented into dedicated visual assets.
2. **Interactive Figure Inspector Registry** ([`src/figure_inspectors.py`](file:///C:/Users/kenai/aws-a30-prototype/src/figure_inspectors.py)):
   - Covers 100% of the 60 standard figures across 9 functional categories:
     - `Joint Anatomy & Grooves`: Figures B1–B15.
     - `Weld Positions & Test Fixtures`: Figures B16–B22 (including 1G, 2F, 5G, 6GR ring).
     - `Flange, Fillet & Plug Welds`: Figures B23–B31 (Fillet weld throats, leg sizes).
     - `Edge Welds & Surfacing`: Figures B32–B37.
     - `Resistance & Solid-State Welding`: Figures B38–B44 (Spot, seam, projection, friction stir).
     - `Brazing & Soldering Joints`: Figures B45–B50.
     - `Cutting & Gouging Profiles`: Figures B51–B54.
     - `Master Process Charts & Trees`: Annex A Figures A1–A6.
   - Encodes 267+ interactive callout chips with queries, labels, and semantic categories.

---

## 5. Auditable Epistemic Verifier Engine

The Epistemic Verifier ([`src/epistemic_verifier.py`](file:///C:/Users/kenai/aws-a30-prototype/src/epistemic_verifier.py)) audits candidate answers before or alongside user presentation.

### Verification Algorithm
```python
def verify_answer(query: str, answer_text: str, graph: nx.MultiDiGraph) -> EpistemicAudit:
    # 1. Detect if query is an Out-of-Scope Negative Control
    if is_out_of_scope(query) and indicates_abstention(answer_text):
        return EpistemicAudit(status="TRUTHFUL_ABSTENTION", provenance_score=1.0)
    
    # 2. Extract technical ontology concepts asserted in answer
    concepts = extract_asserted_concepts(answer_text)
    
    # 3. For every concept, traverse the graph for an unbroken bridge to Evidence
    grounded_concepts = []
    unbacked_concepts = []
    for concept in concepts:
        evidence_nodes = [
            v for u, v, d in graph.out_edges(concept, data=True)
            if d.get("bridge_type") in ["DEFINED_IN", "ILLUSTRATED_BY", "TABULATED_IN"]
        ]
        if evidence_nodes:
            grounded_concepts.append((concept, evidence_nodes))
        else:
            unbacked_concepts.append(concept)
            
    # 4. Compute Epistemic Provenance Score
    score = len(grounded_concepts) / len(concepts) if concepts else 1.0
    status = "VERIFIED_GROUNDED" if score >= 0.85 else "PROVISIONAL_PARTIAL"
    
    return EpistemicAudit(
        status=status,
        provenance_score=score,
        grounded=grounded_concepts,
        unbacked=unbacked_concepts
    )
```

---

## 6. Web Visual Explorer Application

The user interface ([`src/web.py`](file:///C:/Users/kenai/aws-a30-prototype/src/web.py)) is a lightweight single-page visual explorer served over HTTP (default port `8000`).

### UI Features:
1. **Interactive NLQ Search Bar**: Pre-loaded with suggestion chips for joint geometries, nonstandard terms, process matrices, and cross-modal queries.
2. **Dual-Layer Epistemic Provenance Panel**:
   - Status badge: `VERIFIED_GROUNDED (100%)` or `TRUTHFUL_ABSTENTION`.
   - Ontology Concept tags tagged by domain type (`:JointGeometry`, `:Process`, `:Discontinuity`).
   - Unbroken Evidence links showing exact `[:DEFINED_IN]` clauses and `[:ILLUSTRATED_BY]` figure numbers.
3. **Interactive Multimodal Diagram Canvas**:
   - Renders the high-resolution vector drawing with smooth zoom and pan controls.
   - Displays clickable **interactive callout chips** beneath the figure, allowing instant drill-down on anatomical features.
4. **Figure & Diagram Directory Drawer**:
   - Expandable side drawer indexing all 60 standard figures across Annex A and Annex B for direct exploration.

---

## 7. Gold Benchmark & Evaluation Subsystem

The automated benchmark harness ([`eval/test_scorer.py`](file:///C:/Users/kenai/aws-a30-prototype/eval/test_scorer.py)) tests the system against [`eval/gold_benchmark.json`](file:///C:/Users/kenai/aws-a30-prototype/eval/gold_benchmark.json):

| Modality Class | Count | Focus Areas Tested | Target Accuracy |
|---|:---:|---|:---:|
| **Text** | 8 | CJP, Adaptive Control, Throat definitions, Thermal gouging, Style rules, Interpretation procedures | 100.0% |
| **Nonstandard** | 5 | Root pass, Burn-through (melt-through), Short arc, Hydromatic welding, Flow welding | 100.0% |
| **Table** | 7 | GMAW-P, SMAW, ASP, Waveform AIP/TIE (Table D1), Cored solder (Table D4), Deleted terms (Table D6) | 100.0% |
| **Figure** | 18 | Figures A6, B4, B5, B6, B12, B16A, B19, B21 (6GR), B23J, B25, B26, B28, B33, B34, B35, B39, B40, B46, B51 | 100.0% |
| **Cross-Modal** | 2 | 1F pipe test position (Fig B20), Bevel angle & depth (Fig B6) | 100.0% |
| **Qualifier** | 2 | Root opening vs root face, Back weld vs backing weld sequence | 100.0% |
| **Abstention** | 8 | ASTM A36 preheat (D1.1), Porosity acceptance limits, E7018 yield strength, Fictitious Fig B120, Table A10 | 100.0% |
| **TOTAL** | **50** | **Comprehensive normative coverage across all 190 pages of AWS A3.0** | **100.0%** |
