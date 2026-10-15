# AWS A3.0 Standalone Multimodal Prototype

**Vector reader fix and evaluation (2026-10-15):** The chunk reader now accepts validated existing numeric lists and native encoded vectors, with an exact LightRAG 1.5.7 contract guard. On frozen questions, strict target Hit@10 was 1/28 before and 11/28 after in a fixed-pool component comparison; the separate current hybrid lane reached 23/28. Only 12 targets are mapped in the reader pool. These results and 220 selected Python checks do not establish factual answer accuracy. See [protocol, results and limits](docs/vector_reader_compatibility.md).

A clean-slate, standalone prototype for Natural Language Querying (NLQ) over the full 190-page **AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions**.

This prototype demonstrates multimodal search and retrieval—connecting text definitions, process designation tables, and engineering diagrams with exact source citations and strict abstentions.

**Source metadata update (2026-10-15):** [the verified manifest](config/aws_a30_2020_manifest.json) now supplies canonical locations and explicit existing asset bindings through `src/standard_manifest.py`. Its inventory is 190 PDF pages, 62 figures (including distinct B16A/B/C) and 11 tables (A1-A5, D1-D6). Printed pages and viewer ordinals remain distinct. Annex B's applicability conflict is retained. See the [implementation evidence and limits](docs/declarative_manifest_implementation.md); historical feature/count claims below are not fresh ingestion or answer-quality evidence.

---

## Architecture & Features

```mermaid
flowchart LR
    A["AWS A3.0 PDF<br/>(190 Pages)"] --> B["Multimodal Extractor<br/>(PyMuPDF + Docling)"]
    B --> C1["Clause 4 Glossary<br/>(pp. 18–80)"]
    B --> C2["Annex A Tables A1–A5<br/>(pp. 81–92 Markdown)"]
    B --> C3["Annex B Figures B1–B60+<br/>(pp. 93–185 PNG Renders)"]
    
    C1 --> D["LightRAG 1.5.7 Engine<br/>(Google Gemini Core)"]
    C2 --> D
    C3 --> D
    
    D --> E["Local NetworkX Graph<br/>& NanoVectorDB Stores"]
    E --> F["Multimodal NLQ Engine<br/>(Verified Citations & Image Links)"]
```

1. **Native Multimodal LightRAG 1.5.7**:
   - Resolves the RAG-Anything version wrinkle: RAG-Anything was merged directly upstream into LightRAG v1.5.0 in May 2026. This prototype uses `lightrag-hku==1.5.7` with built-in sidecar and Docling support.
2. **First-Class Google Gemini Inference**:
   - Uses `gemini-2.0-flash` for high-throughput multimodal reasoning, graph entity/relationship extraction, and answer synthesis.
   - Existing contextual retrieval uses local `BAAI/bge-large-en-v1.5` vectors with 1024 dimensions; this manifest change does not re-embed data or change provider settings.
3. **High-Fidelity Vector Figure Rendering**:
   - Existing page renders are bound explicitly to 62 source figures. The 97 historical Annex-B JSONL records are per-page artifacts, including misclassified later pages; they are not 97 distinct diagrams.
4. **Complete Corpus & Environment Isolation**:
   - Pure local file-based storage (`./storage/`) via NetworkX and NanoVectorDB. Zero external database servers (no Neo4j, no Docker required).
5. **Exact Citation & Abstention Harness**:
   - The frozen 50-question benchmark (`eval/gold_benchmark.json`) is unchanged. This change was checked with offline deterministic fixtures, without rerunning model-based answer evaluation.

---

## Repository Structure

```text
aws-a30-prototype/
├── data/
│   └── AWS_A3.0_2020.pdf             # Full 190-page reference specification
├── parsed/
│   ├── text_chunks.jsonl              # 64 extracted glossary text chunks
│   ├── tables/                        # Tables A1–A5 in Markdown
│   └── figures/                       # 97 rendered Annex B figure diagrams + JSON metadata
├── storage/                           # Local LightRAG stores (NetworkX + NanoVectorDB)
├── eval/
│   ├── gold_benchmark.json            # 12 curated multimodal evaluation questions
│   ├── test_scorer.py                 # Automated benchmark scoring harness
│   └── benchmark_report.md            # Generated benchmark evaluation report
├── src/
│   ├── config.py                      # Model endpoints and directory paths
│   ├── extract.py                     # Multimodal PDF extraction pipeline
│   ├── indexer.py                     # LightRAG indexing engine (Gemini)
│   ├── query.py                       # NLQ CLI with asset resolution
│   └── citation_checker.py            # Deterministic citation validation
├── docs/                              # Historical lessons, roadmaps, and plans
│   ├── navy_weld_multimodal_lessons_learned.md
│   ├── navy_weld_framework_roadmap.md
│   ├── navy_weld_value_and_outcomes_assessment.md
│   └── aws_a30_standalone_prototype_plan.md
├── .env.example                       # Environment configuration template
└── README.md
```

---

## Quickstart

### 1. Prerequisites & Environment
Python 3.11+ is recommended. This repository currently has neither `requirements.txt` nor `pyproject.toml`; its historical setup is not a complete reproducible install specification. The reader fix requires the reviewed `lightrag-hku==1.5.7` contract. See [tested package/model versions](docs/vector_reader_compatibility.md) before changing the existing environment.

### 2. Configure Gemini API Key
Copy `.env.example` to `.env` and set your key:
```bash
# In PowerShell:
Add-Content -Path .env -Value "GEMINI_API_KEY=your_actual_key_here"
```

### 3. Extract Multimodal Assets
Extract the text, tables, and render all 97 figure diagrams:
```bash
python -m src.extract
```

### 4. Build the LightRAG Index
Populate local graph and vector indices:
```bash
# Dry run (validates chunks without API calls):
python -m src.indexer --dry-run

# Live indexing with Gemini:
python -m src.indexer
```

### 5. Run Natural Language Queries
Ask questions via the CLI:
```bash
python -m src.query "Explain a 1F pipe position and show its diagram"
python -m src.query "What is the letter designation for gas metal arc welding - pulsed arc?"
```

The system will return:
- Direct technical answer.
- Exact citations (e.g., `Clause 4, p. 5`, `Annex B, Figure B20`, `Table A1`).
- Direct file path links to the resolved figure diagrams or table files.

### 6. Run Automated Benchmark
Execute the 12-question challenge suite:
```bash
python -m eval.test_scorer
```
Outputs a detailed report to `eval/benchmark_report.md`.

---

## Project Documentation
Detailed system specifications, operational rules, and architecture rationale are available in the `docs/` folder:
- [Project Goals & Evaluation Criteria](docs/goal.md)
- [System Architecture & Epistemic Graph Design](docs/architecture.md)
- [Multi-Agent System (MAS) Operating Guidelines](docs/agents.md)
- [Multimodal Lessons Learned](docs/navy_weld_multimodal_lessons_learned.md)
- [Framework Roadmap](docs/navy_weld_framework_roadmap.md)
- [Value and Outcomes Assessment](docs/navy_weld_value_and_outcomes_assessment.md)
- [Technical Implementation Plan](docs/aws_a30_standalone_prototype_plan.md)

## Local API security boundaries

Model API roots are approved through server configuration. Request-level `base_url`
overrides must match the selected engine's configured root. Existing model and
retrieval defaults are preserved. Assets are served from a startup allowlist with
path and link containment checks. A separate production UI can be approved using
`A30_ALLOWED_ORIGINS`; query clients must send JSON with Content-Length.
Browser-entered API keys stay in page memory. See [security boundary notes](docs/security_boundary_notes.md)
for compatibility details, isolated tests and the deliberately deferred HTML risks.

If the required contextual retrieval index is absent, queries return
`RETRIEVAL_INDEX_MISSING` with restoration guidance (HTTP 503; CLI exit 1).
The application does not automatically rebuild the index or generate an answer.
