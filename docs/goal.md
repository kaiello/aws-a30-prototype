# AWS A3.0M/A3.0:2020 Multimodal RAG — End Goal & Production System Architecture (`goal.md`)

**Target Standard:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Coordinate Formula:** $\text{printed\_page} = \text{pdf\_index} - 12 = \text{viewer\_page} - 13$ (for main text & annexes starting at Clause 1, printed p. 1 = PDF index 13)  
**Production Release Tag:** `v1.6.4.1-provenance-integrity` (merged on `main`)  
**Repository:** `https://github.com/kaiello/aws-a30-prototype`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)  
**Full Regression Test Suite:** `1,514 passed, 8 skipped, 0 failures, 0 warnings`  

---

## 1. What the End Product Is

The end product is a **hardened, source-grounded multimodal Question-Answering (QA) and Reference System with explicit abstention** for the complete `AWS A3.0M/A3.0:2020` standard. Instead of a conventional vector-chunk RAG chatbot that guesses answers from fragmented text snippets, this system transforms every word, normative table, decision tree, spatial callout diagram, and cycle waveform in the 190-page PDF into a **cryptographically locked, cross-linked Knowledge Graph**.

When an engineer, welding inspector, researcher, or autonomous AI agent asks a question—whether phrased using formal standard terminology, shop-floor slang, historical nomenclature, process abbreviations, or ID-free natural language—the system delivers:

1. **A 100% Store-Backed, Zero-Fallback Answer:** Every fact, taxonomy path, table designation, and diagram interval is composed directly from locked canonical JSON/SQLite stores. If a required field is missing or corrupted, the system strictly raises or returns `INSUFFICIENT_EVIDENCE` rather than emitting fallback prose (enforced by AST static analysis banning `.get(key, "literal")` fallbacks and 7-target store mutation degradation tests).
2. **Exact Triple-Coordinate & Visual Provenance:** Every response cites the exact **Printed Page Number**, **PDF Page Index**, and **300-DPI Isolated Diagram Crop (PNG with locked SHA-256 digest)** so a human reviewer can verify primary source evidence in seconds.
3. **Multi-Layer Epistemic Transparency (`ACCEPTED` vs. `CANDIDATE` vs. `IS_A` vs. `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`):**
   - `ACCEPTED`: Facts physically corroborated by PDF vector geometry, explicit table cells, or Clause 4 boldface definitions.
   - `CANDIDATE`: Visually implied layout relationships (such as uncorroborated table row indentations or candidate VLM visual detections, retained strictly with `knowledge_eligible=False`).
   - `IS_A_PROCESS_VARIATION_OF`: Promoted taxonomy edges (`35` promoted, `83` retained as `CANDIDATE`) requiring dual-provenance corroboration across both `Table A1` and `Clause 4` genus-differentia definitions.
   - `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`: Strict quarantine of all LLM/VLM reasoning traces and chain-of-thought tokens, ensuring model-generated reasons never enter final answers or normative citations.
4. **Deterministic Semantic Query Expansion & ID-Free NLQ Understanding (Gate 5.5):**
   - Users do **not** need to know figure numbers (`Figure A5`, `Figure B49`), table numbers (`Table A4`), or exact headword orthography.
   - An offline, store-derived **Semantic Expansion Engine ([`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py))** automatically resolves process abbreviations (`SMAW`, `GTAW-P`, `FCAW-S`, `CW`, `AB`), Annex C nonstandard shop terms (*"stick electrode"*, *"button weld"*), Annex D historical terms (*"heliarc"*, *"atomic hydrogen welding"*, *"forge welding"*), morphological inflections (*"kerfs"* $\rightarrow$ *"kerf"*, *"undercutting"* $\rightarrow$ *"undercut"*), and conceptual figure/table signatures into a verifiable `semantic_expansion_trace`.
   - Verified on a frozen 15-question benchmark ([`storage/evidence_v2/phase5_5_nlq_001/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase5_5_nlq_001/)) achieving **15 / 15 (100.0%)** pass rate across all 5 architectural slices (`G55-NLQ01` through `G55-NLQ15`).
5. **DeepSeek-V4.1-Flash-1017 Planner & Multimodal VLM Integration (Gate 5.4):**
   - Integrates `deepseek-ai/DeepSeek-V4.1-Flash-1017` at Layer 4 (Question Planning & Multi-Hop Decomposition) and Layer 1/2 (Candidate Visual Verification Stub) via [`src/deepseek_v41_adapter.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/deepseek_v41_adapter.py).
   - Operates with **0 network calls** in automated testing and preflight by utilizing 8 content-addressed replay cassettes in [`storage/model_replays/deepseek_v4_1_flash_1017/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/model_replays/deepseek_v4_1_flash_1017/).
   - Enforces strict epistemic quarantine: every `part.reason` emitted by the model is tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE` and lowered to `PLANNED_REASON` (`""`) in internal wire plans.
6. **Adversarial & Scope-Boundary Robustness with Explicit Abstention (Gate 5):**
   - Out-of-range coordinates (e.g., `Figure A7`, `Figure B55`, `Table A6`) are deterministically rejected with `REFUSAL_OUT_OF_RANGE`.
   - Taxonomic false premises (e.g., claiming `SMAW` is a Solid-State Welding process) are refuted with exact chart provenance (`CONTRADICTION_REFUTED`).
   - Unstandardized or fabricated terms (e.g., *"hyper-flux welding"*, *"cryo-ionic brazing"*) return `NOT_IN_STANDARD`.
   - Out-of-scope engineering queries (e.g., filler metal tensile/yield strength values, Charpy impact toughness, preheat schedules, or external ASME/AWS D1.1 construction codes) are cleanly refused with `REFUSAL_OUT_OF_SCOPE` via a generalized structural classifier (`HK-5-1`).
7. **Two Operating Speeds:**
   - **Offline Deterministic Route (`DeterministicQuestionPlanner` + `SemanticNLQExpander`):** Answers structured, paraphrased, and multi-hop natural language queries with measured low latency ($p_{50}: 55.5\text{ ms}$, $p_{95}: 70.2\text{ ms}$ per [`storage/manifests/latency_benchmark.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/manifests/latency_benchmark.json)) and no per-query external API charge under socket-guarded zero network access (`CLEAR_WHOLE_STANDARD_CONTRACT`).
   - **DeepSeek-V4.1 Planner Route (`DeepSeekV41PlannerAdapter`):** Translates complex, open-ended conversational questions into schema-constrained AST lookup plans (`temperature=0`, `0` retries) executed against the same immutable stores under full epistemic quarantine (`CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`).

---

## 2. How Multimodal Ingestion & Runtime Retrieval Work

### Stage 1: Pre-Computed Multimodal Knowledge Graph (Locked Canonical Stores)

The 190-page standard is partitioned into **4 Visual Archetypes** plus the **Clause 4 / Annex C / Annex D Lexical & Taxonomic Stores**:

| Structural Slice | AWS A3.0M/A3.0:2020 Scope | Printed Pages (PDF Indices) | What Is Extracted & Verified |
| :--- | :--- | :--- | :--- |
| **Archetype 1: Box Indentation Charts** | `Figures A1, A2, A3` | pp. 75–76 (PDF 87–88) | Enclosing boxes, physical vector connectors, candidate row indentations, footnotes, and explicit cross-chart pointers (`See Figure A4/A5/A6`). |
| **Archetype 2: Characteristic Decision Trees** | `Figures A4, A5, A6` | pp. 77–79 (PDF 89–91) | 5-column characteristic classification trees (`Energy Source` $\rightarrow$ `Thermal Source` $\rightarrow$ `Loading` $\rightarrow$ `Shielding/Flux` $\rightarrow$ `Process`), `96` numbered process circles, `59` bottom legend rows, and multi-branch process paths. |
| **Normative Process Tables** | `Tables A1–A5` | pp. 69–74 (PDF 81–86) | `138` Table A1 rows, `133` Table A2 rows, `134` Table A3 matrix rows, `6` Table A4 adaptive/mechanized/automatic/robotic/manual letter suffixes, and `13` Table A5 obsolete designations, plus 4 documented source anomalies (including `AB` = arc brazing vs. adhesive bonding). |
| **Clause 4 Glossary & Dual-Provenance `IS_A`** | `Clause 4` + `Annex C` + `Annex D` | pp. 5–67, 159–170 (PDF 17–79, 171–182) | `1,607` glossary entries (`1,345` standard boldface, `262` nonstandard lightface), `311` `NONSTANDARD_SYNONYM_OF` edges, `378` underline & `458` margin-bar 2020 revision markers, `21` Annex C clauses (`8` editorial decisions), `491` Annex D historical rows across Tables D1–D6 (rectifying an uncalibrated historical claim of 591), and `35` dual-provenance `IS_A_PROCESS_VARIATION_OF` promotions. |
| **Archetype 3: Spatial Callout Diagrams** | `Figures B1–B43, B46–B48, B52` (`49` figure units) | pp. 82–147, 151–152, 156 (PDF 94–159, 163–164, 168) | Multi-panel weld joint/groove/crack/position drawings (`80` high-res 300-DPI crops), sub-panels `(A)–(G)`, arrow/leader-line callouts, numbered key legends (e.g., `B33` 1–13 crack keys, `B46` 1–10 FSW keys), and multi-page continuations (`B6`, `B8`, `B17`, `B19`, `B20`, `B22`). |
| **Archetype 4: Cycle & Waveform Plots** | `Figures B44–B45, B49–B51, B53–B54` (`7` figure units) | pp. 148–150, 153–155, 157 (PDF 160–162, 165–167, 169) | Temporal cycle sequences (`SQUEEZE` $\rightarrow$ `WELD` $\rightarrow$ `HOLD` $\rightarrow$ `OFF`, upslope/downslope, pulsed spray waveforms) and physical trace relationships (`CURRENT`, `FORCE`, `VOLTAGE` vs. `TIME`). |

---

### Stage 2: 5-Step Runtime NLQ & Multi-Hop Execution Pipeline

When a user submits a natural language question at runtime, the system executes a deterministic 5-step pipeline:

```
[Raw User Query (Text / NLQ / Synonyms / Acronyms)]
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 1. Store-Derived Semantic Expander                     │
│    - Morphological normalization (kerfs -> kerf)       │
│    - Annex C nonstandard & Annex D historical pivots   │
│    - Tables A1/A4/A5 abbreviation expansion            │
│    - ID-free Figure / Table conceptual signature match │
│    - Output: SemanticExpansionTrace                    │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 2. Question Planner (Deterministic / DeepSeek-V4.1)   │
│    - Boundary screening (Figure > A6, Figure > B54)    │
│    - Structural out-of-scope classifier (HK-5-1)      │
│    - Epistemic Quarantine (part.reason -> UNVERIFIED)  │
│    - Schema-constrained JSON operation plan            │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 3. AST Plan Compiler & Schema Guardrails               │
│    - Lowers to internal wire operations (PLANNED_REASON│
│    - Validates actions, targets, and bindings          │
│    - Asserts 0 blocked actions, operations >= 1        │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 4. Multi-Hop Cross-Store Graph Executor                │
│    - Traverses Clause 4, Tables A1-A5, Figures A1-A6,  │
│      Figures B1-B54 via deterministic store access     │
│    - Chains intermediate hops into hop_trace           │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 5. Zero-Fallback Deterministic Answer Composer         │
│    - Assembles final answer strictly from store fields │
│    - Attaches triple-coordinates (Printed Page, PDF    │
│      Index, 300-DPI PNG Crop SHA-256 Digest)           │
│    - Returns structured answer receipt                 │
└────────────────────────────────────────────────────────┘
```

---

## 3. Cryptographic Immutability Ledger (45 Locked Repository Artifacts)

All operational, evaluation, and semantic expansion code must treat the canonical Phase 0–3 stores, frozen benchmark suites, offline model replay cassettes, and system manifests as **100% read-only**. [`tests/test_gate_5_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_hardening.py), [`tests/test_gate_5_4_deepseek_adapter.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_4_deepseek_adapter.py), [`tests/test_gate_5_5_semantic_nlq.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_5_semantic_nlq.py), [`tests/test_gate_5_6_epistemic_manifest.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_6_epistemic_manifest.py), [`tests/test_gate_6_0_ner_routing_skills.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_0_ner_routing_skills.py), [`tests/test_gate_6_1_semantic_graph.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_1_semantic_graph.py), [`tests/test_gate_6_2_store_driven_composition.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_2_store_driven_composition.py), [`tests/test_gate_6_2_1_multi_action_closure.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_2_1_multi_action_closure.py), and [`tests/test_gate_6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_3_blind_hardening.py) enforce exact SHA-256 verification across all 45 locked files:

### Part A: 14 Core Repository & Benchmark Artifacts

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Source PDF** | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | `VERIFIED_LOCKED` |
| 2 | **Phase 0 Glossary Store** | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | `VERIFIED_LOCKED` |
| 3 | **Phase 1 Annex C/D Store** | `storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | `VERIFIED_LOCKED` |
| 4 | **Phase 2 `IS_A` Store** | `storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | `VERIFIED_LOCKED` |
| 5 | **Phase 3A Annex B (B1–B6)** | `storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | `VERIFIED_LOCKED` |
| 6 | **Phase 3B Annex B Complete** | `storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | `VERIFIED_LOCKED` |
| 7 | **Phase 3C Archetype 4 Store** | `storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | `VERIFIED_LOCKED` |
| 8 | **Phase 2F Annex A Holdout Rubric** | `storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json` | `70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479` | `VERIFIED_LOCKED` |
| 9 | **Phase 5 Adversarial Qs** | `storage/evidence_v2/phase5_hardening_001/adversarial_questions.json` | `0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9` | `VERIFIED_LOCKED` |
| 10 | **Phase 5 Adversarial Rubric** | `storage/evidence_v2/phase5_hardening_001/rubric.json` | `df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981` | `VERIFIED_LOCKED` |
| 11 | **Phase 5 Adversarial Results** | `storage/evidence_v2/phase5_hardening_001/results.json` | `92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273` | `VERIFIED_LOCKED` |
| 12 | **Phase 5.5 NLQ Questions** | `storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json` | `ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57` | `VERIFIED_LOCKED` |
| 13 | **Phase 5.5 NLQ Rubric** | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b` | `VERIFIED_LOCKED` |
| 14 | **Phase 5.5 NLQ Results** | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74` | `VERIFIED_LOCKED` |

### Part B: 8 DeepSeek-V4.1-Flash-1017 Offline Replay Cassettes

| # | Query Topic / Type | Replay Cassette Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 15 | Gate 5.4 Figure A2 Query | `storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json` | `59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f` | `VERIFIED_LOCKED` |
| 16 | Gate 5.4 Multi-Hop Query | `storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079` | `VERIFIED_LOCKED` |
| 17 | Gate 5.4 Out-of-Range Refusal | `storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d` | `VERIFIED_LOCKED` |
| 18 | Gate 5.4 False Premise Refutation | `storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a` | `VERIFIED_LOCKED` |
| 19 | Gate 5.4 Figure A1 Query | `storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | `VERIFIED_LOCKED` |
| 20 | Gate 5.5 ID-Free Waveform (B53) | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | `VERIFIED_LOCKED` |
| 21 | Gate 5.5 Historical Multi-Hop (AHW) | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | `VERIFIED_LOCKED` |
| 22 | Gate 5.5 Out-of-Scope Refusal | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | `VERIFIED_LOCKED` |

### Part C: 2 Gate 5.6 Manifests (Whole-Standard Coverage & Latency Telemetry)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 23 | **Coverage Manifest** | `storage/manifests/coverage_manifest.json` | `8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e` | `VERIFIED_LOCKED` |
| 24 | **Latency Benchmark** | `storage/manifests/latency_benchmark.json` | `bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c` | `VERIFIED_LOCKED` |

### Part D: 5 Gate 6.0 Artifacts (NER/Routing Benchmark & DeepSeek Replay Cassettes)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 25 | **Gate 6.0 Questions** | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac` | `VERIFIED_LOCKED` |
| 26 | **Gate 6.0 Rubric** | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427` | `VERIFIED_LOCKED` |
| 27 | **Gate 6.0 Results** | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8` | `VERIFIED_LOCKED` |
| 28 | **Gate 6.0 Compound + Chart Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057` | `VERIFIED_LOCKED` |
| 29 | **Gate 6.0 Spatial Callout Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42` | `VERIFIED_LOCKED` |

### Part E: 5 Gate 6.1 Artifacts (Semantic Graph Benchmark & DeepSeek Replay Cassettes)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 30 | **Gate 6.1 Questions** | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7` | `VERIFIED_LOCKED` |
| 31 | **Gate 6.1 Rubric** | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5` | `VERIFIED_LOCKED` |
| 32 | **Gate 6.1 Results** | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf` | `VERIFIED_LOCKED` |
| 33 | **Gate 6.1 FCAW-G-SA Replay** | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432` | `VERIFIED_LOCKED` |
| 34 | **Gate 6.1 PAW-AU Replay** | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993` | `VERIFIED_LOCKED` |

### Part F: 5 Gate 6.2 Artifacts (Generalization Holdout Benchmark & DeepSeek Replay Cassettes)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 35 | **Gate 6.2 Holdout Questions** | `storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | `VERIFIED_LOCKED` |
| 36 | **Gate 6.2 Holdout Rubric** | `storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json` | `bb18c854ee6c590dfa83955939b0c9fd810a4cd633ee6d0f64eaf9f0168fe6c3` | `VERIFIED_LOCKED` |
| 37 | **Gate 6.2 Holdout Results** | `storage/evidence_v2/phase6_2_generalization_holdout_001/results.json` | `dfe96330a00328fdb79d594353be826c6d3ccaa10063b62b0a83e0f560886f60` | `VERIFIED_LOCKED` |
| 38 | **Gate 6.2 GMAW-P-SA Replay** | `storage/model_replays/deepseek_v4_1_flash_1017/7e9982c36d0fcfa591123da74ceb0e7c7da002981d4379693a07eb61d3c40d29.json` | `f8cd0108b311f27868d5b9fa59b9478ff4128492be28d361d7b793f6011bc21f` | `VERIFIED_LOCKED` |
| 39 | **Gate 6.2 FOW vs FSW Replay** | `storage/model_replays/deepseek_v4_1_flash_1017/3d6a2cbb61def68a41a52cdec81712a85cd65f7ed52c2e6505bc280821dacf9a.json` | `cb9ac95d98a5aac82c61f4d2d4b34438b452268f7e0221996fdac9e55edac570` | `VERIFIED_LOCKED` |

### Part G: 3 Gate 6.2.1 Artifacts (Generalization Holdout 002 Benchmark)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 40 | **Gate 6.2.1 Holdout Questions** | `storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | `VERIFIED_LOCKED` |
| 41 | **Gate 6.2.1 Holdout Rubric** | `storage/evidence_v2/phase6_2_generalization_holdout_002/rubric.json` | `e23085ad83f13142a7bc84a1ddc3a89459b72b8c894c966b98d4d9b6587b24c4` | `VERIFIED_LOCKED` |
| 42 | **Gate 6.2.1 Holdout Results** | `storage/evidence_v2/phase6_2_generalization_holdout_002/results.json` | `0d9f8a1bf4a88861ab0c6fa27ec6cf0a88fd8a1f1cc257c02d25433396b53b2b` | `VERIFIED_LOCKED` |

### Part H: 3 Gate 6.3 Artifacts (Blind Hardening 001 Benchmark)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 43 | **Gate 6.3 Blind Hardening Questions** | `storage/evidence_v2/phase6_3_blind_hardening_001/questions.json` | `be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b` | `VERIFIED_LOCKED` |
| 44 | **Gate 6.3 Blind Hardening Rubric** | `storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json` | `a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c` | `VERIFIED_LOCKED` |
| 45 | **Gate 6.3 Blind Hardening Results** | `storage/evidence_v2/phase6_3_blind_hardening_001/results.json` | `18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2` | `VERIFIED_LOCKED` |

### Version-Bound Store Immutability Policy
Cryptographic SHA-256 digests lock each released store version (`*_001`). Verified content corrections or spatial refinements produce a successor version (`*_002`) with a documented migration ledger rather than mutating locked releases in place.

### Machine-Verifiable 190-Page Coverage Manifest
[`storage/manifests/coverage_manifest.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/manifests/coverage_manifest.json) accounts for all 190 PDF pages:
- **162 Ingested Pages:** Clause 4 (PDF 17–79), Tables A1–A5 (PDF 81–86), Figures A1–A6 (PDF 87–91), Annex B Figures B1–B54 (PDF 94–169), Annex C Decisions (PDF 171–176), Annex D Tables D1–D6 (PDF 177–182).
- **28 Excluded Pages:** Front matter and TOC (PDF 1–12), introductory administrative scope (PDF 13–16), section dividers / blank pages (PDF 80, 92–93, 170), and Informative Index / back matter (PDF 183–190).

### Modality-Appropriate Conditional Crop Provenance
Every non-refusal answer includes universal page coordinates (`printed_page`, `pdf_index`) and structured `evidence_locator`. A 300-DPI diagram crop (`crop_path`) is attached with `requires_diagram_crop: True` **when and only when** the answer depends on a visual diagram (`Figures A1–A6` or `Figures B1–B54`). For text-only and tabular lookups (`Clause 4`, `Annex C/D`, `Tables A1–A5`), `requires_diagram_crop: False` is set and spurious diagram crops are omitted.

---

## 4. Core Architectural Invariants & Anti-Drift Rules (Enforced in CI)

1. **Zero Question-ID or Benchmark-Literal Hardcoding:**
   - Operational modules (`src/*.py`) and evaluators (`eval/*.py`) must return `0 matches` for any benchmark question ID pattern:
     ```powershell
     git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+|G61-SEM[0-9]+|G61-[0-9]+|G62-GEN[0-9]+|G62-[0-9]+" -- src/ eval/*.py
     ```
   - Operational modules (`src/*.py`) must return `0 matches` for benchmark-specific trap literals:
     ```powershell
     git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018|OFC-A-MA|FCAW-Z-SA|PAW-AU-ME|GTAW-ZZ|GMAW-P-AU|FCAW-G-SA|GMAW-X-SA|GTAW-AU-MA|EBW-AU-SA" -- src/
     ```
2. **Epistemic Quarantine of Model Traces:**
   - Every `part.reason` emitted by `DeepSeek-V4.1-Flash-1017` is lowered to `PLANNED_REASON` (`""`) in internal wire plans and quarantined in `model_part_metadata` with `authority: "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"`. It never enters final answers or provenance citations.
   - Multimodal visual candidate observations emitted by `DeepSeekV41VisualCandidateVerifier` strictly carry `verification="candidate"` and `knowledge_eligible=False`.
3. **AST Zero Silent Fallback Guarantee:**
   - No composer function may call `.get(key, "non_empty_literal")` to mask missing store data. Missing or corrupted store structures must strictly raise `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
4. **Strict Offline Test & Preflight Isolation:**
   - `answer_whole_standard_question` and `run_deepseek_replay_preflight` execute under `socket.socket` interception (`0` network calls), reading deterministic content-addressed replay fixtures, verifying input immutability, and confirming all canonical store hashes remain untouched (`CLEAR_WHOLE_STANDARD_CONTRACT` / `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`).

---

## 5. Gate 5.5 Benchmark Slices & Deliverables Summary

### Benchmark Slices ([`storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | ID-Free Annex A Chart & Table NLQs | `G55-NLQ01` – `G55-NLQ03` | Table A4, Figure A5, Table A5 (Application Modes, Classification Tree, Obsolete Codes) | `100.0% PASS (3/3)` |
| **Slice 2** | ID-Free Annex B Visual & Waveform NLQs | `G55-NLQ04` – `G55-NLQ06` | Figures B53, B7, B49 (Pulsed cycles, Edge shapes, Resistance spot waveforms) | `100.0% PASS (3/3)` |
| **Slice 3** | Historical, Nonstandard & Abbreviation Semantic Expansion | `G55-NLQ07` – `G55-NLQ09` | Clause 4, Annex C/D, Table A1 (`stick electrode` $\rightarrow$ `covered electrode`, `CW` $\rightarrow$ `cold welding`, `AHW` obsolete) | `100.0% PASS (3/3)` |
| **Slice 4** | Conversational & Morphological Clause 4 + `is_a` NLQs | `G55-NLQ10` – `G55-NLQ12` | Clause 4 glossary + Figures B41, B32 (`kerfs` $\rightarrow$ `kerf`, `undercutting` $\rightarrow$ `undercut`, `coalescence`) | `100.0% PASS (3/3)` |
| **Slice 5** | Natural-Language Adversarial & Out-of-Scope Traps | `G55-NLQ13` – `G55-NLQ15` | Refusal boundaries (`cryo-ionic` $\rightarrow$ `NOT_IN_STANDARD`, preheat/Charpy $\rightarrow$ `REFUSAL_OUT_OF_SCOPE`, SMAW $\rightarrow$ `CONTRADICTION_REFUTED`) | `100.0% PASS (3/3)` |

### Deliverables Checklist

- [x] **Deliverable 1 (`src/semantic_nlq_expander.py`):** Deterministic, store-derived Semantic Expansion Engine mapping process codes (`Tables A1/A2/A4/A5`), nonstandard terms (`Annex C`), historical terms (`Annex D`), morphological variants (`Clause 4`), and inverted `Figure`/`Table` concept signatures (`Annex A` & `Annex B`) with auditable `semantic_expansion_trace` output.
- [x] **Deliverable 2 (ID-Free Routing & Conversational Extractor in `src/evidence_phase4_bakeoff.py`):** ID-free routing to `Figures A1–A6`, `Tables A1–A5`, and `Figures B1–B54`; conversational noun-phrase extraction; generalized out-of-scope refusal logic (`HK-5-1`).
- [x] **Deliverable 3 (DeepSeek-V4.1-Flash-1017 Integration in `src/deepseek_v41_adapter.py`):** Full offline replay integration with `plan_with_semantic_expansion`, epistemic quarantine, and 8 content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/`.
- [x] **Deliverable 4 (Frozen 15-Query Gate 5.5 NLQ Benchmark):** `storage/evidence_v2/phase5_5_nlq_001/{nlq_questions.json, rubric.json, results.json}` and `eval/run_phase5_5_nlq.py`, achieving **15 / 15 (100.0%)** across all 5 NLQ slices (`G55-NLQ01` through `G55-NLQ15`).
- [x] **Deliverable 5 (22/22 Artifact Hash Locks & Full Test Suite):** Lock all 14 core project hashes and all 8 DeepSeek replay hashes in `tests/test_gate_5_4_deepseek_adapter.py` and `tests/test_gate_5_5_semantic_nlq.py`, verifying `0` failures and `0` warnings across all `1,463` repository tests.

---

## 6. Gate 6.0 NER & Multi-Intent Benchmark Slices & Deliverables Summary

### Benchmark Slices ([`storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | Dynamic Compound Process + Mode Designations | `G60-NER01` – `G60-NER04` | Table A1 + Table A4 (`PAW-AU`, `GTAW-ME`, `FCAW-G-SA`, `OFC-A-MA`) | `100.0% PASS (4/4)` |
| **Slice 2** | ID-Free Annex B Spatial Diagram Callouts | `G60-NER05` – `G60-NER08` | Figures B25, B33, B46, B12 (Throat terms, Crack types, FSW zones, Joint backing) | `100.0% PASS (4/4)` |
| **Slice 3** | Homographs & Weld Test Position Disambiguation | `G60-NER09` – `G60-NER12` | Table A1 / Figure A6 (`AB`), Figures B16A–C (`6G`, `2F` positions) | `100.0% PASS (4/4)` |
| **Slice 4** | Multi-Entity Cross-Store Comparative & Multi-Hop | `G60-NER13` – `G60-NER16` | Table A1/A4 + Figure A4, Table A5 vs A1 (`AHW`/`GTAW`), Figure B53 + Clause 4 (`heliarc`), Clause 4 (`braze` POS) | `100.0% PASS (4/4)` |
| **Slice 5** | Suffix Verification, Out-of-Range & Out-of-Scope Boundaries | `G60-NER17` – `G60-NER20` | Invalid suffix (`GTAW-ZZ`), Figure B55 refusal, coined term refusal, WPS parameter refusal | `100.0% PASS (4/4)` |

### Deliverables Checklist

- [x] **Deliverable 1 (`src/welding_ner.py`):** Deterministic Welding Named Entity Recognizer & dynamic compound code parser resolving 11 domain entity categories, character-offset matching, longest-match precedence, and homograph candidate tracking (`AB`).
- [x] **Deliverable 2 (`src/semantic_nlq_expander.py` & `src/evidence_phase4_bakeoff.py`):** Inverted Annex B spatial callout graph (1,115 callout terms), Clause 4 figure backlink graph (265 edges), and multi-intent action planner for cross-store multi-hop queries.
- [x] **Deliverable 3 (`src/evidence_whole_standard_cli.py` & `.agents/skills/`):** Whole-standard CLI entry point (`--ner`, `--route`, `--ask`) and updated skill playbooks replacing legacy Figure A1 limitations.
- [x] **Deliverable 4 (`storage/evidence_v2/phase6_ner_routing_001/` & `eval/run_phase6_ner_routing.py`):** Frozen 20-question Gate 6.0 benchmark scoring **20 / 20 (100.0%)** across compound designations, ID-free callouts, homographs, multi-hop queries, and adversarial boundaries.
- [x] **Deliverable 5 (29/29 Cryptographic Hash Locks & Regression Suite in `tests/test_gate_6_0_ner_routing_skills.py`):** 24 prior locked hashes + 5 Gate 6.0 artifacts cryptographically locked under CI; full regression suite passing at 1,475 passed, 8 skipped, 0 failures, 0 warnings.

---

## 7. Gate 6.1 Polysemous NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion

### Benchmark Slices ([`storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | Polysemous Callout & Definitional Intent Spans | `G61-SEM01` – `G61-SEM03` | Clause 4 + Annex B (`theoretical throat`, `crater crack`, `advancing side`) | `100.0% PASS (3/3)` |
| **Slice 2** | 3-Tier Compound Designation Decompositions | `G61-SEM04` – `G61-SEM06` | Table A1 + Table A4 (`FCAW-G-SA`, `GMAW-P-AU`, `OFC-A-MA` vs `FCAW-Z-SA` / `PAW-AU-ME`) | `100.0% PASS (3/3)` |
| **Slice 3** | Contextual Sense & Qualifier Resolution | `G61-SEM07` – `G61-SEM09` | Figures B17 vs B19 (`1G, plate` vs `1G, pipe`), Table A1 vs Figure A6 (`AB` + `2F`) | `100.0% PASS (3/3)` |
| **Slice 4** | See also & Taxonomy Sibling Expansion | `G61-SEM10` – `G61-SEM12` | Clause 4 cross-references (`throat of a fillet weld`, `FCAW` variations, `travel angle` family) | `100.0% PASS (3/3)` |
| **Slice 5** | CLI `--expand` & Offline Replay Verification | `G61-SEM13` – `G61-SEM15` | Whole-standard CLI JSON expand contract & DeepSeek-V4.1 offline replay cassettes | `100.0% PASS (3/3)` |

### Deliverables Checklist

- [x] **Deliverable 1 (`src/welding_ner.py`):** Extended `WeldingEntitySpan` with `secondary_entity_types`, `linked_clause4_terms`, `linked_figures`, `linked_tables`, and `ambiguous_senses`; dual-role routing for definitional intent queries.
- [x] **Deliverable 2 (`src/welding_ner.py`):** 3-tier compound designation parser `<BASE>[-<VAR>][-<MODE>]` with process variations (`FCAW-G-SA`, `OFC-A-MA`), invalid code detection (`FCAW-Z-SA`, `PAW-AU-ME`), and contextual sense resolution for weld positions (`1G`, `1F`) and homographs (`AB`).
- [x] **Deliverable 3 (`src/semantic_nlq_expander.py`):** Deterministic in-memory `SemanticConceptGraph` tracking `see_also_edges`, `is_a_subtypes`, `sibling_variations`, and diagram co-callouts; bidirectional expansion for throat and angle clusters.
- [x] **Deliverable 4 (`src/evidence_whole_standard_cli.py` & `src/evidence_phase4_bakeoff.py`):** CLI `--expand` flag returning structured neighborhood, NER receipt, and ranked figures; multi-hop execution branch for compound validation, test positions, disambiguation, and see-also cross references.
- [x] **Deliverable 5 (34/34 Cryptographic Hash Locks & Regression Suite in `tests/test_gate_6_1_semantic_graph.py`):** 29 prior locked hashes + 3 Gate 6.1 benchmark files + 2 new DeepSeek-V4.1 replay cassettes locked under CI; full regression suite passing at 1,482 passed, 8 skipped, 0 failures, 0 warnings.

---

## 8. Gate 6.2 Store-Driven Multi-Operation Composition, Zero-Canned-Prose AST Hardening & 20-Query Holdout

### Benchmark Slices ([`storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | Generalized Dynamic Taxonomy Subtypes | `G62-GEN01` – `G62-GEN04` | `is_a_promotion_store.json` + `Table A1` (OFC, SAW, RSEW, GMAW variations) | `100.0% PASS (4/4)` |
| **Slice 2** | Dynamic See-Also Expansion across Unseen Hubs | `G62-GEN05` – `G62-GEN08` | `glossary_store.json` (backfire, welding cycle, defect, joint type cross-references) | `100.0% PASS (4/4)` |
| **Slice 3** | Comprehensive Weld Test Position Disambiguation | `G62-GEN09` – `G62-GEN12` | Clause 4 (p. 5/6) + Figures B16A–C, B17–B20 (3G, 4G, 5G, 3F, 4F plate vs pipe) | `100.0% PASS (4/4)` |
| **Slice 4** | Generalized Cross-Store & Multi-Validation Operations | `G62-GEN13` – `G62-GEN16` | Table A5 / A1 / A2 (`FOW` vs `FSW`, `OFC-P-ME` vs invalid `GMAW-X-SA`, `GTAW-AU-MA`) | `100.0% PASS (4/4)` |
| **Slice 5** | Offline DeepSeek Multi-Hop Replay over Composers | `G62-GEN17` – `G62-GEN20` | `DeepSeek-V4.1-Flash-1017` replay cassettes over 3-tier compound, diagram cycles & FSW | `100.0% PASS (4/4)` |

### Deliverables Checklist

- [x] **Deliverable G62-1 (Store-Driven Multi-Operation Action Composers in `src/evidence_phase4_bakeoff.py`):** 7 atomic, zero-canned-prose composers (`_exec_lookup_taxonomy_subtypes`, `_exec_expand_cross_references`, `_exec_weld_position_sense`, `_exec_disambiguate_homograph`, `_exec_compound_lookup_and_validation`, `_exec_compare_historical_and_active`, `_exec_polysemous_diagram_and_glossary`) reading dynamically from canonical stores.
- [x] **Deliverable G62-2 (Zero-Canned-Prose AST Guard & 12-Target Store Mutation Degradation Suite in `tests/test_gate_6_2_store_driven_composition.py`):** AST guard enforcing zero string literal fallbacks in `.get(key, '...')` across all 10 composers; 12-target store mutation degradation suite proving catastrophic failure (`INSUFFICIENT_EVIDENCE`) when store keys/data are emptied.
- [x] **Deliverable G62-3 (Offline DeepSeek 14-Replay Suite with Epistemic Quarantine):** 14 content-addressed `DeepSeek-V4.1-Flash-1017` replay cassettes executing in `< 1 ms` under socket isolation (`socket.socket` blocked, 0 network calls).
- [x] **Deliverable G62-4 (20-Query Unseen Generalization Holdout Benchmark):** `storage/evidence_v2/phase6_2_generalization_holdout_001/{questions.json, rubric.json, results.json}` and `eval/run_phase6_2_generalization_holdout.py`, achieving **20 / 20 (100.0%)** across all 5 slices (`G62-GEN01` through `G62-GEN20`).
- [x] **Deliverable G62-5 (39/39 Cryptographic Hash Locks & Anti-Drift Zero-Tolerance):** 34 prior locked hashes + 5 Gate 6.2 artifacts cryptographically locked under CI; 0 benchmark question IDs and 0 trap literals in `src/`; full regression suite passing at 100%.

---

## 9. Gate 6.2.1 Multi-Action Composition, Holdout 002 & 42-Hash Closeout

### Benchmark Slices ([`storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | Generalized Dynamic Taxonomy Subtypes | `G62-GEN01` – `G62-GEN04` | `is_a_promotion_store.json` + `Table A1` (OFC, SAW, RSEW, GMAW variations) | `100.0% PASS (4/4)` |
| **Slice 2** | Dynamic See-Also Expansion across Unseen Hubs | `G62-GEN05` – `G62-GEN08` | `glossary_store.json` (backfire, welding cycle, defect, agglomerated flux cross-references) | `100.0% PASS (4/4)` |
| **Slice 3** | Comprehensive Weld Test Position Disambiguation | `G62-GEN09` – `G62-GEN12` | Clause 4 (p. 5/6) + Figures B16A–C, B17–B20 (3G, 4G, 5G, 3F, 4F plate vs pipe) | `100.0% PASS (4/4)` |
| **Slice 4** | Generalized Cross-Store & Multi-Validation Operations | `G62-GEN13` – `G62-GEN16` | Table A5 / A1 / A2 (`FOW` vs `FSW`, `OFC-P-ME` vs invalid `GMAW-X-SA`, `GTAW-AU-MA`) | `100.0% PASS (4/4)` |
| **Slice 5** | Offline DeepSeek Multi-Hop Replay over Composers | `G62-GEN17` – `G62-GEN20` | `DeepSeek-V4.1-Flash-1017` replay cassettes over 3-tier compound, diagram cycles & FSW | `100.0% PASS (4/4)` |

### Deliverables Checklist

- [x] **Deliverable G621-1 (Modular Multi-Action Composition & Zero-Canned-Prose Elimination):** Replaced all remaining legacy template strings in `src/evidence_phase4_bakeoff.py` (`invalid_compound_suffix`, `compound_designation`, `polysemous_callout_and_glossary`, angle clusters, Figure B6/B12/B25/B33/B46) with modular store-driven composability.
- [x] **Deliverable G621-2 (Unweakened `holdout_002` Benchmark):** Established `storage/evidence_v2/phase6_2_generalization_holdout_002/` scoring **20 / 20 (100.0%)** without weakening rubrics or relaxing modality requirements.
- [x] **Deliverable G621-3 (Dynamic Table Derivations in NER & NLQ):** Standardized dynamic Table A1/A2/A3/A4/A5 derivations across `src/welding_ner.py` and `src/semantic_nlq_expander.py`.
- [x] **Deliverable G621-4 (Hardened 12-Target Store Mutation Suite):** Verified mutations 8–12 fail catastrophically through `answer_whole_standard_question` raising `ValueError("INSUFFICIENT_EVIDENCE")`.
- [x] **Deliverable G621-5 (42/42 Cryptographic Hash Locks & Test Suite in `tests/test_gate_6_2_1_multi_action_closure.py`):** 39 prior locked hashes + 3 `phase6_2_generalization_holdout_002` benchmark files locked under CI; full regression suite passing at 1,494 passed, 8 skipped, 0 failures, 0 warnings.

## Gate 6.2.2: Post-6.2.1 Closeout Hygiene, Google Drive 42-Artifact Mirror Parity, Repo Doc Alignment & Post-Merge Audit Bundle (Tagged `v1.6.2.2-closeout-hygiene`)

- [x] **Deliverable G622-1 (Complete 42-Artifact Google Drive Mirror Collection):** Updated `collect_reviewable_files` in `src/sync_drive_mirror.py` to collect all 41 non-PDF locked artifacts, scripts, and benchmark results without omissions.
- [x] **Deliverable G622-2 (Document Hash & Pagination Alignment):** Corrected rows #36 and #37 SHA-256 digests in ledger tables, aligned test count to 1,499 passed, 8 skipped, and fixed Clause 4 weld position pagination.
- [x] **Deliverable G622-3 (AST Zero-Fallback Expansion):** Enforced AST zero-fallback guard on `execute_whole_standard_plan` across `tests/test_gate_5_hardening.py` and `tests/test_gate_6_2_store_driven_composition.py`, eliminating inline fallback strings.
- [x] **Deliverable G622-4 (Evaluator CLI Enhancements & Genus-Scoped Cross-References):** Added `--benchmark-dir` and `--use-replay-cassettes` CLI flags to `eval/run_phase6_2_generalization_holdout.py` and isolated single-subtype cross-reference expansion.
- [x] **Deliverable G622-5 (42/42 Locked Hash Verification & Full Suite Baseline):** Maintained 100% byte-identity across all 42 locked repository artifacts with full test suite passing at 1,499 passed, 8 skipped.

---

## 10. Gate 6.3: Blind Hardening Benchmark, Process Variation Grammar & Embedded Lightface NER

### Benchmark Slices ([`storage/evidence_v2/phase6_3_blind_hardening_001/questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/questions.json))

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | Clause 4 Linked Visual Nomenclature | `G63-BLIND01` | `acetylene feather` definition and Figure B40 reference | `100.0% PASS (1/1)` |
| **Slice 2** | Root Process Definitions & See-Also Expansions | `G63-BLIND02` | `GTAW` definition and Figure B36 reference | `100.0% PASS (1/1)` |
| **Slice 3** | Welding Position Tabulations & Angular Limits | `G63-BLIND03` | Flat fillet weld rotation of face ($150^\circ$ to $210^\circ$) via Figure B16B | `100.0% PASS (1/1)` |
| **Slice 4** | Reverse Figure Concept Search | `G63-BLIND04` | Position of beam, filler material, gun, or torch (Figure B21, p. 112) | `100.0% PASS (1/1)` |
| **Slice 5** | Joint Type to Applicable Weld Taxonomy | `G63-BLIND05` | T-joint applicable weld types via Figure B1(C) | `100.0% PASS (1/1)` |
| **Slice 6** | Annex A Classification Chart Topology | `G63-BLIND06` | Figure A6 Brazing and Soldering top-level energy sources (Chemical, Electrical) | `100.0% PASS (1/1)` |
| **Slice 7** | Multi-Process Designation Decoding & Definitions | `G63-BLIND07` | Decode `FRW`, `RSEW`, and `RSW` from Table A1 and Clause 4 | `100.0% PASS (1/1)` |
| **Slice 8** | Major Process Group Enumeration | `G63-BLIND08` | Solid-State Welding process enumeration via Table A1 and Figure A5 (p. 78) | `100.0% PASS (1/1)` |
| **Slice 9** | Obsolete Process Verification & Status | `G63-BLIND09` | Obsolete status of `BB` (block brazing) and `CAW-S` (shielded carbon arc) via Table A5 | `100.0% PASS (1/1)` |
| **Slice 10** | Process Variation Subtyping & Suffix Grammar | `G63-BLIND10` | Differentiate `FLSP`, `FLSP-P`, and `FLSP-W` via Table A1 and Clause 4 | `100.0% PASS (1/1)` |
| **Slice 11** | Sequence Nomenclature Cluster & Linked Figures | `G63-BLIND11` | Block sequence definition, Figure B23, and linked sequence terms | `100.0% PASS (1/1)` |
| **Slice 12** | Geometric Throat Cluster & Multi-Figure Reference | `G63-BLIND12` | Effective throat definition, Figure B25, and throat terminology cluster | `100.0% PASS (1/1)` |
| **Slice 13** | Figure Schematic Key Enumeration & Directional Senses | `G63-BLIND13` | Figure B46 Friction Stir Welding 10 key items and advancing/retreating side | `100.0% PASS (1/1)` |
| **Slice 14** | Sub-Diagram Measurement Notes & Temper Bead Cluster | `G63-BLIND14` | Figure B23(J) temper beads, distance S measurement, and temper bead definitions | `100.0% PASS (1/1)` |
| **Slice 15** | Angle Cluster & Weld Discontinuity Multi-Diagrams | `G63-BLIND15` | Reentrant angle, bead/toe reentrant angles, Figure B32, and overlap | `100.0% PASS (1/1)` |
| **Slice 16** | Suffix Modifiers, Appending Grammar & Mode Definitions | `G63-BLIND16` | Table A4 application mode suffixes (`-AD`, `-AU`, `-MA`, `-ME`, `-RO`, `-SA`) | `100.0% PASS (1/1)` |
| **Slice 17** | Multi-Family Process Decoding & Vacuum Pressure Limits | `G63-BLIND17` | `LBC` and `EBW` variations, operating pressure ranges, and definitions | `100.0% PASS (1/1)` |
| **Slice 18** | Personal Safety Exception & Nonstandard/Incorrect Terms | `G63-BLIND18` | Nonstandard & incorrect terms (`ground clamp`, `ground lead`), safety exception, Figure B34 | `100.0% PASS (1/1)` |
| **Slice 19** | Edition Revision Decisions & Normative Rationale | `G63-BLIND19` | Annex C C1.5.6/C1.5.7 parallel joint vs edge joint, NDE/NDI/NDT revisions | `100.0% PASS (1/1)` |
| **Slice 20** | Dual Waveform Comparison & 11 Cycle Interval Definitions | `G63-BLIND20` | Figure B49 and B50 resistance spot welding waveforms and 11 cycle intervals | `100.0% PASS (1/1)` |

### Deliverables Checklist

- [x] **Deliverable G63-1 (20-Question Blind Hardening Benchmark Suite):** Established `storage/evidence_v2/phase6_3_blind_hardening_001/{questions.json, rubric.json, results.json}` and `eval/run_phase6_3_blind_hardening.py`, achieving **20 / 20 (100.0%)** pass rate under socket isolation (`0` network calls).
- [x] **Deliverable G63-2 (Process Variation Grammar vs Compound Suffix Bifurcation):** Hardened `WeldingNER` process variations (`ner.process_codes` vs Table A4 compound application modes) avoiding false invalidations on Table A1–A3 variants like `GMAW-S` and `GTAW-P`.
- [x] **Deliverable G63-3 (Embedded Lightface Nonstandard Term Resolution):** Enhanced `SemanticExpander` and `WeldingNER` to extract and resolve multi-word embedded nonstandard terms (`ground clamp`, `ground lead`, `welding ground`, `silver soldering`) directly to standard Clause 4 terms and definitions.
- [x] **Deliverable G63-4 (AST Zero-Fallback Expansion Across 12 Functions):** Extended the AST zero-fallback guard in `tests/test_gate_6_3_blind_hardening.py` across all 12 composer and plan-execution functions (`0` violations).
- [x] **Deliverable G63-5 (45/45 Cryptographic Hash Locks & Drive Mirror Parity):** Added Artifacts #43–#45 to the immutability ledger (`test_gate_6_3_all_45_locked_hashes`), preserved 100% backward compatibility across all legacy test suites, and synchronized with Google Drive mirror.

---

## 11. Gate 6.4: Comprehensive Enhancements (Replay/Fixture Suite, Table A3 Joins, Figures B33/B46 Deep Traversal & Whole-Standard CLI)

### Deliverables Checklist

- [x] **Deliverable G64-1 (Offline Replay & Synthetic Fixture Suite Expansion):** Added 6 content-addressed synthetic planner fixtures (quarantined in `storage/model_replays/deterministic_planner_fixtures/` per Gate 6.4.1 `PROV-6.4-1` alongside the 14 genuine model replays in `storage/model_replays/deepseek_v4_1_flash_1017/`) for `G63-BLIND04`, `G63-BLIND09`, `G63-BLIND14`, `G63-BLIND16`, `G63-BLIND18`, and `G63-BLIND20`. Updated `eval/run_phase6_3_blind_hardening.py` to support `--use-replay-cassettes`, `--strict-replay`, and `--use-fixtures`, verifying **20 / 20 (100.0%)** pass rate under socket isolation.
- [x] **Deliverable G64-2 (Table A3 Matrix & Multi-Table Joins):** Built dedicated store-driven composer `_compose_table_a3_cross_reference` in `src/evidence_phase4_bakeoff.py` for Table A3 (134 letter designations from `AB` to `WS`), dynamically cross-referencing process names, letter designations, Table A1/A2, source anomalies (`ANOMALY-01` through `ANOMALY-04`), and Clause 4 definitions with zero fallback AST compliance and store-mutation degradation tests.
- [x] **Deliverable G64-3 (Annex B Spatial Callout Deep Traversal for Figures B33 & B46):** Deepened Figure B33 (13 crack locations on printed p. 139 / PDF index 151) and Figure B46 (10 FSW key items on printed p. 150 / PDF index 162) in `src/archetype_spatial_callout.py` to join spatial callouts with Clause 4 definitions (`advancing side`, `retreating side`, crack types) and store-verified key labels (`Item 5: Tool Shoulder`, `Item 6: Probe`) with high-res crop provenance.
- [x] **Deliverable G64-4 (Whole-Standard CLI & Agent Skills Modernization):** Added `--table-a3` and `--offline` to `src/evidence_whole_standard_cli.py`, modernizing `.agents/skills/aws-a30-ner-and-routing/SKILL.md` (correct alphabetical weld test position Clause 4 pagination `1F`–`4F` and `1G`–`3G` on printed p. 5, `4G`–`6GR` on printed p. 6; documented Table A3 CLI and capabilities).
- [x] **Deliverable G64-5 (51/51 Cryptographic Hash Locks & Test Suite in `tests/test_gate_6_4_comprehensive_enhancements.py`):** Added Artifacts #46–#51 to the immutability ledger, verified all 51 cryptographic hashes under CI, and scored 7/7 (100%) on `tests/test_gate_6_4_comprehensive_enhancements.py`.

---

## 12. Gate 6.4.1: Provenance Integrity Remediation (Quarantined Synthetic Fixtures, Grounded B46 Labels, Store-Derived Table A3 & Zero Disk Reads)

### Deliverables Checklist

- [x] **Deliverable G641-1 (Synthetic Cassette Quarantine & Honest Replay Accounting - PROV-6.4-1, EVAL-6.4-7):** Quarantined the 6 synthetic fixtures from `storage/model_replays/deepseek_v4_1_flash_1017/` to `storage/model_replays/deterministic_planner_fixtures/` with `model_id: "DeterministicQuestionPlanner"`, `epistemic_tag: "SYNTHETIC_PLANNER_FIXTURE_NOT_MODEL_OUTPUT"`, and `cassette_origin: "synthetic_planner_fixture"`. Committed reproducible generator `scripts/generate_deterministic_planner_fixtures.py`. Updated `eval/run_phase6_3_blind_hardening.py` to support `--use-fixtures` and `--strict-replay`, reporting 14 genuine DeepSeek model replays and 6 quarantined fixtures.
- [x] **Deliverable G641-2 (Grounded Figure B46 Labels & Zero Fabricated Prose - PROV-6.4-2):** Eliminated fabricated Clause 4 definitions for "Tool Shoulder" and "Probe" in `src/archetype_spatial_callout.py`. Emits verified key-item labels from Annex B store and real Clause 4 definitions for `advancing side` and `retreating side`, explicitly noting that tool shoulder and probe have no separate normative definition entries in Clause 4.
- [x] **Deliverable G641-3 (Dynamically Derived Table A3 Range & Word-Boundary Subsumption - PROV-6.4-3, EXEC-6.4-5):** Dynamically derived Table A3 range `AB` (`adhesive bonding`) through `WS` (`wave soldering`), `printed pp. 72–73`, `PDF index 84–85` strictly from `table_a3` store, removing hardcoded `"W"`. Implemented word-boundary matching and subsumption filtering in `_compose_table_a3_cross_reference` so `torch brazing` returns only `TB` and `gas tungsten arc welding` returns only `GTAW`.
- [x] **Deliverable G641-4 (Zero Direct Disk Reads & Structural Intent Routing - EXEC-6.4-4, EXEC-6.4-6):** Eliminated direct `open(...)` calls to `glossary_store.json` in `src/archetype_spatial_callout.py`, utilizing injected stores. Constrained `elements_present` strictly to strings appearing in `answer_text`. Refactored Priority 17b and Priority 22 in `src/evidence_phase4_bakeoff.py` to route on structural intent (`table a1` + primary process grouping) rather than brittle process exclusions.
- [x] **Deliverable G641-5 (Bundle Target Separation, Strengthened AST Guards & Full Regression - HYG-6.4-9, TEST-6.4-8):** Removed Gate 5 targets from `scripts/build_gate_6_bundle.py` and restored genuine Gate 5 bundle (`508,291` bytes). Enforced AST checks on `src/archetype_spatial_callout.py` (0 `open()`, 0 `.read_text()` / `.read_bytes()`, 0 fabricated strings). Regression baseline verified at 1,514 passed, 8 skipped, 0 failures, 0 warnings.

---

## 13. Gate 6.5: Authoritative Provenance Unification, Shared Application Path, Checkout Reconciliation & Independent Claim/Coordinate Evaluator

### Scope & Architectural Summary
Following the forensic architecture assessment (`AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md`), Gate 6.5 executes Phases 1–3 of the strategic modernization:
- **Decision Ledger (D1–D6):**
  - **D1 (Retain Evidence-First Architecture):** ACCEPT. Retain 45 locked stores; reject wholesale OCR or ungrounded similarity retrieval.
  - **D2 (Authoritative Provenance Registry):** ACCEPT. Corrected `ANNEX_A_PAGES` (A1=75/87, A2=76/88, A3=76/88, A4=77/89, A5=78/90, A6=79/91); eliminated overwrite bugs in `_enrich_and_validate_provenance`; prioritized B53 locator over B49 keywords; aligned Table A3 GTAW to p. 73 / PDF 85.
  - **D3 (Shared Execution Path):** ACCEPT. Added `evidence_version="whole_standard"` to `src/query.py` (`async_query`/`run_query`) and `src/web.py` (`/api/query`), unifying CLI, web demo, and evaluator paths under `answer_whole_standard_question`.
  - **D4 (Checkout Card & Question Table Reconciliation):** ACCEPT. Synchronized `GATE_6_4_CHECKOUT_CARD.md`, `ROADMAP.md`, `goal.md`, and `docs/goal.md` with exact 20 questions and 51 locked hashes.
  - **D5 (Independent Provenance & Coordinate Evaluator):** ACCEPT. Upgraded `eval/run_phase6_3_blind_hardening.py` with 5 structural provenance gates (coordinate formula, body-metadata consistency, crop-locator identity, modality/abstention, and granular metric reporting).
  - **D6 (Sequenced Roadmap):** Stage Bakeoff #16 (reader qualification with gold evidence) in Gate 6.6, and Bakeoff #8 (ColQwen2.5/ColPali visual retrieval comparison) in Gate 6.7.

### Deliverables Checklist

- [x] **Deliverable G65-1 (Authoritative Provenance Registry & Zero-Overwrite Contract):** Aligned `ANNEX_A_PAGES` to physical PDF page allocation (`storage/manifests/coverage_manifest.json`), eliminating off-by-one +1 placing Figure A6 on excluded blank divider p. 80 / PDF 92. Guarded composer coordinates in `_enrich_modality_provenance` from keyword overwrites (Table A3 GTAW preserved at 73/85, B53 preserved at 157/169 with `figure_b53:interval:upslope_and_downslope`, Figure B23(J) preserved at 116/128). Fixed Annex B crop resolver regex to avoid prefix overmatching (`figure_b1*.png` matching `figure_b10...`).
- [x] **Deliverable G65-2 (Shared Application, CLI & Evaluator Execution Path):** Integrated `evidence_version="whole_standard"` into `src/query.py` (`async_query` and `run_query`) and `src/web.py` (`/api/query`), forwarding queries directly through `answer_whole_standard_question` and returning unified evidence packets with preserved `planner_source`.
- [x] **Deliverable G65-3 (Independent Provenance, Coordinate & Crop-Identity Evaluator):** Upgraded `eval/run_phase6_3_blind_hardening.py` with 5 mandatory structural provenance gates (Coordinate Formula, Body-to-Metadata Alignment, Crop-to-Locator Identity, Modality/Abstention, and Granular Metric Reporting), scoring 20/20 (100.0%) across all 5 gates.
- [x] **Deliverable G65-4 (Reconcile Stale Checkout Cards & Question Tables):** Corrected Section 2 in `GATE_6_4_CHECKOUT_CARD.md` with exact 20 questions from `questions.json`; updated Section 3 hash table with quarantined fixture metadata; synchronized Section 10 in `ROADMAP.md`, `goal.md`, and `docs/goal.md`; added `CONTINUATION_*.md` glob to `src/sync_drive_mirror.py`.
- [x] **Deliverable G65-5 (Gate 6.5 Verification Suite in `tests/test_gate_6_5_provenance_and_shared_path.py`):** Author comprehensive test suite asserting exact Annex A coordinates, B53/B49 locator dispatch, Table A3 GTAW consistency, shared `/api/query` execution, evaluator rejection of bad provenance, and checkout card cryptographic parity.

---

## 14. Subsequent Roadmap Staging: Gates 6.6 & 6.7

- **Gate 6.6 (Phase 4 — Reader Qualification with Gold Evidence & DeepSeek Cassette Capture):** Supply verified gold source crops/pages directly to candidate multimodal readers (Bakeoff #16), separating extraction/interpretation/binding failure classes, and capture genuine `DeepSeek-V4.1` cassettes for any remaining unrecorded queries in a separate isolated worktree.
- **Gate 6.7 (Phase 5 — Bounded ColQwen2.5 / ColPali Visual Retrieval Comparison):** Compare the repaired deterministic baseline against a pinned ColQwen2.5/ColPali visual page retriever on demonstrated retrieval misses (Bakeoff #8), reporting case-by-case rescues vs. harms under a fixed reader and evidence budget.
