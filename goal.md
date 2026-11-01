# AWS A3.0M/A3.0:2020 Multimodal RAG — End Goal & Production System Architecture (`goal.md`)

**Target Standard:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Coordinate Formula:** $\text{printed\_page} = \text{pdf\_index} - 12 = \text{viewer\_page} - 13$ (for main text & annexes starting at Clause 1, printed p. 1 = PDF index 13)  
**Production Release Merge SHA:** `e31b8e2` (merged on `main`)  
**Repository:** `https://github.com/kaiello/aws-a30-prototype`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)  
**Full Regression Test Suite:** `1,463 passed, 8 skipped, 0 failures, 0 warnings`  

---

## 1. What the End Product Is

The end product is a **hardened, zero-hallucination, multimodal Question-Answering (QA) and Reference System** for the complete `AWS A3.0M/A3.0:2020` standard. Instead of a conventional vector-chunk RAG chatbot that guesses answers from fragmented text snippets, this system transforms every word, normative table, decision tree, spatial callout diagram, and cycle waveform in the 190-page PDF into a **cryptographically locked, cross-linked Knowledge Graph**.

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
6. **Adversarial & Scope-Boundary Immunity (Gate 5):**
   - Out-of-range coordinates (e.g., `Figure A7`, `Figure B55`, `Table A6`) are deterministically rejected with `REFUSAL_OUT_OF_RANGE`.
   - Taxonomic false premises (e.g., claiming `SMAW` is a Solid-State Welding process) are refuted with exact chart provenance (`CONTRADICTION_REFUTED`).
   - Unstandardized or fabricated terms (e.g., *"hyper-flux welding"*, *"cryo-ionic brazing"*) return `NOT_IN_STANDARD`.
   - Out-of-scope engineering queries (e.g., filler metal tensile/yield strength values, Charpy impact toughness, preheat schedules, or external ASME/AWS D1.1 construction codes) are cleanly refused with `REFUSAL_OUT_OF_SCOPE` via a generalized structural classifier (`HK-5-1`).
7. **Two Operating Speeds:**
   - **Offline Deterministic Route (`DeterministicQuestionPlanner` + `SemanticNLQExpander`):** Answers structured, paraphrased, and multi-hop natural language queries in $< 1\text{ ms}$ at $\$0.00$ cost with socket-guarded zero network access (`CLEAR_WHOLE_STANDARD_CONTRACT`).
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
| **Clause 4 Glossary & Dual-Provenance `IS_A`** | `Clause 4` + `Annex C` + `Annex D` | pp. 5–67, 159–170 (PDF 17–79, 171–182) | `1,607` glossary entries (`1,345` standard boldface, `262` nonstandard lightface), `311` `NONSTANDARD_SYNONYM_OF` edges, `378` underline & `458` margin-bar 2020 revision markers, `21` Annex C clauses (`8` editorial decisions), `591` Annex D historical rows, and `35` dual-provenance `IS_A_PROCESS_VARIATION_OF` promotions. |
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

## 3. Cryptographic Immutability Ledger (22 Locked Repository Artifacts)

All operational, evaluation, and semantic expansion code must treat the canonical Phase 0–3 stores, frozen benchmark suites, and offline model replay cassettes as **100% read-only**. [`tests/test_gate_5_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_hardening.py), [`tests/test_gate_5_4_deepseek_adapter.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_4_deepseek_adapter.py), and [`tests/test_gate_5_5_semantic_nlq.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_5_5_semantic_nlq.py) enforce exact SHA-256 verification across all 22 locked files:

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

---

## 4. Core Architectural Invariants & Anti-Drift Rules (Enforced in CI)

1. **Zero Question-ID or Benchmark-Literal Hardcoding:**
   - Operational modules (`src/*.py`) and evaluators (`eval/*.py`) must return `0 matches` for any benchmark question ID pattern:
     ```powershell
     git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+" -- src/ eval/*.py
     ```
   - Operational modules (`src/*.py`) must return `0 matches` for benchmark-specific trap literals:
     ```powershell
     git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/
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
