# AWS A3.0M/A3.0:2020 Multimodal RAG Master Roadmap & Cryptographic Invariant Ledger

**Document Purpose:** Living architectural contract, milestone roadmap, and cryptographic provenance ledger for the AWS A3.0M/A3.0:2020 source-aware multimodal graph ingestion and retrieval system.

---

## 1. Project Overview & Gate Status Summary

- **Standard Document:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 190 PDF pages)
- **Current Test Suite Baseline:** `1,455+ passed, 8 skipped, 0 failures, 0 warnings`
- **Active Milestone:** **Gate 5.5 — Unified Final Production Gate: Store-Derived Semantic NLQ Expansion, ID-Free Routing, and DeepSeek-V4.1 Integration** (`feat/gate-5-5-semantic-nlq` $\rightarrow$ `main`)
- **Canonical Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`
- **Mirror Destination:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)

### Milestone Progression Register

| Phase / Gate | Milestone Scope & Description | Target Branch / Commit | Review Verdict & Verification Status |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Clause 4 Terms & Definitions (1,607 terms, 61 printed pages) | `feat/gate-3a-clause4-glossary-is-a` | `PASSED & MERGED` — 1,607/1,607 terms parsed; 0 truncation; 100% letter-section coverage. |
| **Phase 1** | Annex C (Nonstandard Terms) & Annex D (Historical Terms) | `feat/gate-3a-clause4-glossary-is-a` | `PASSED & MERGED` — 100% of nonstandard/historical entries indexed with bidirectional pointers. |
| **Phase 2** | `IS_A` Semantic Hierarchy Generation (BFO-Lite) | `feat/gate-3a-clause4-glossary-is-a` | `PASSED & MERGED` — 1,607 taxonomy links verified against printed definitions. |
| **Phase 2F** | Annex A Holdout Evaluation (6 Charts + 5 Tables) | `263bfdb` $\rightarrow$ `main` | `PASSED & MERGED` — 25/25 (100.0%) holdout query PASS across Figures A1–A6 and Tables A1–A5. |
| **Phase 3A** | Annex B Archetype 3 (B1–B6 Joint Types & Grooves) | `feat/gate-3b-annex-b-archetype3-b1-b6` | `PASSED & MERGED` — Spatial callouts, 180 DPI chips, and 100% coordinate provenance verified. |
| **Phase 3B** | Annex B Complete Unified Store (B7–B54) | `263bfdb` $\rightarrow$ `main` | `PASSED & MERGED` — 54 figures indexed with Loud-and-Clear multimodal representations. |
| **Phase 3C** | Annex B Archetype 4 Waveforms (B44–B45, B49–B51, B53–B54) | `263bfdb` $\rightarrow$ `main` | `PASSED & MERGED` — Mathematical parameterization and cycle-interval parsing complete. |
| **Gate 3D** | Phase 3 Live Holdout Closeout (`Clause 4` + `Annex B` + `Annex C/D` Cross-Modal Suite) | `263bfdb` $\rightarrow$ `main` | `PASSED & MERGED` — 40/40 (100.0%) unseen holdout PASS across 4 balanced 10-question slices (`P3-S1` to `P3-S4`). |
| **Gate 4** | Whole-Standard Production Bakeoff (`Clause 4` + `Annex A/B/C/D`) | `8dff8b6` $\rightarrow$ `main` `42e9658` | `PASSED & MERGED` — 35/35 (100.0%) production bakeoff PASS across all 5 evaluation dimensions; 1,442 unit tests. |
| **Gate 4B** | Multi-Hop Cross-Store Retrieval Stress Test (`2–4` Sequential Store Hops) | `feat/gate-4b-multihop-retrieval-stress-test` | `PASSED` — Chained 2–4 sequential store operations with verified `hop_trace` provenance across stores. |
| **Gate 5.0–5.2** | Production Hardening, AST Zero-Fallback Guard, Adversarial Benchmark & Audit Remediation (`DRIFT-5-1..5-5`) | `e9a5621` (+ `DRIFT-5-1..5-5` fixes on `feat/gate-5-production-hardening`) | `VERIFIED_READY` — 10/10 (`100.0%`) adversarial benchmark (`G5-ADV01..10`), AST zero-fallback guard, 7-target store mutation test, socket-isolated preflight (`CLEAR_WHOLE_STANDARD_CONTRACT`), `1,449 passed, 8 skipped, 0 warnings`. |
| **Gate 5.4** | DeepSeek-V4.1-Flash-1017 Planner Adapter & Offline Replay Harness | `feat/gate-5-4-deepseek-planner-replay` | `PASSED` — Layer 4 planner adapter, Layer 1/2 multimodal visual verifier stub, strict epistemic quarantine (`UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`), 5 locked offline replay fixtures (`0` network calls). |
| **Gate 5.5** | **Unified Final Production Release: Semantic NLQ Expansion, ID-Free Routing, and DeepSeek-V4.1 Integration** | `feat/gate-5-5-semantic-nlq` $\rightarrow$ `main` | **`FINAL PRODUCTION RELEASE`** — Offline store-derived synonym/alias/abbreviation expansion, ID-free `Figure`/`Table` routing, conversational term extraction, generalized out-of-scope boundary classifier, 3 new DeepSeek NLQ replay fixtures, and 15-query NLQ benchmark (`G55-NLQ01..15`). |

---

## 2. Cryptographic Immutability Ledger (22 Locked Repository Artifacts)

All operational, evaluation, and semantic expansion code must treat the canonical Phase 0–3 stores, frozen benchmark suites, and offline model replay cassettes as **100% read-only**. `tests/test_gate_5_hardening.py`, `tests/test_gate_5_4_deepseek_adapter.py`, and `tests/test_gate_5_5_semantic_nlq.py` enforce exact SHA-256 verification across all 22 locked files:

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

| # | Query Topic / Type | Replay Key & Cassette File | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 15 | **Gate 5.4 Figure A2 Query** | `33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json` | `59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f` | `VERIFIED_LOCKED` |
| 16 | **Gate 5.4 Multi-Hop Query** | `8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079` | `VERIFIED_LOCKED` |
| 17 | **Gate 5.4 Out-of-Range Rejection** | `a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d` | `VERIFIED_LOCKED` |
| 18 | **Gate 5.4 False Premise Refutation** | `afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a` | `VERIFIED_LOCKED` |
| 19 | **Gate 5.4 Figure A1 Query** | `b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | `VERIFIED_LOCKED` |
| 20 | **Gate 5.5 ID-Free Waveform (B53)** | `6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | `VERIFIED_LOCKED` |
| 21 | **Gate 5.5 Historical Multi-Hop (AHW)** | `8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | `VERIFIED_LOCKED` |
| 22 | **Gate 5.5 Out-of-Scope Refusal** | `f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | `VERIFIED_LOCKED` |

---

## 3. Core Architectural Invariants & Anti-Drift Rules (Enforced in CI)

1. **Zero Question-ID or Benchmark-Literal Hardcoding (`test_gate_5_anti_drift_source_scan`, `test_gate_5_4_anti_drift_regex_coverage`, & `test_gate_5_5_anti_drift_and_anti_overfitting`):**
   - Operational modules (`src/*.py`) and evaluators (`eval/*.py`) must return `0 matches` for any benchmark question ID pattern:
     ```powershell
     git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+" -- src/ eval/*.py
     ```
   - Operational modules (`src/*.py`) must return `0 matches` for benchmark-specific trap literals:
     ```powershell
     git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/
     ```
2. **Epistemic Quarantine of Model Traces (`src/deepseek_v41_adapter.py`):**
   - Every `part.reason` emitted by `DeepSeek-V4.1-Flash-1017` is lowered to `PLANNED_REASON` (`""`) in internal wire plans and quarantined in `model_part_metadata` with `authority: "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"`. It never enters final answers or provenance citations.
   - Multimodal visual candidate observations emitted by `DeepSeekV41VisualCandidateVerifier` strictly carry `verification="candidate"` and `knowledge_eligible=False`.
3. **AST Zero Silent Fallback Guarantee (`test_gate_5_composer_ast_no_silent_string_fallbacks`):**
   - No composer function may call `.get(key, "non_empty_literal")` to mask missing store data. Missing or corrupted store structures must raise `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
4. **Strict Offline Test & Preflight Isolation (`src/evidence_whole_standard_preflight.py`):**
   - `answer_whole_standard_question` and `run_deepseek_replay_preflight` execute under `socket.socket` interception (`0` network calls), reading deterministic content-addressed replay fixtures, verifying input immutability, and confirming all canonical store hashes remain untouched (`CLEAR_WHOLE_STANDARD_CONTRACT` / `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`).

---

## 4. Gate 5.5 Benchmark Slices & Deliverables Checklist

### Gate 5.5 Benchmark Slices (`storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json`)

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | ID-Free Annex A Chart & Table NLQs | `G55-NLQ01` – `G55-NLQ03` | Table A4, Figure A5, Table A5 (Application Modes, Classification Tree, Obsolete Codes) | `100.0% PASS (3/3)` |
| **Slice 2** | ID-Free Annex B Visual & Waveform NLQs | `G55-NLQ04` – `G55-NLQ06` | Figures B53, B7, B49 (Pulsed cycles, Edge shapes, Resistance spot waveforms) | `100.0% PASS (3/3)` |
| **Slice 3** | Historical, Nonstandard & Abbreviation Semantic Expansion | `G55-NLQ07` – `G55-NLQ09` | Clause 4, Annex C/D, Table A1 (`stick electrode` $\rightarrow$ `covered electrode`, `CW` $\rightarrow$ `cold welding`, `AHW` obsolete) | `100.0% PASS (3/3)` |
| **Slice 4** | Conversational & Morphological Clause 4 + `is_a` NLQs | `G55-NLQ10` – `G55-NLQ12` | Clause 4 glossary + Figures B41, B32 (`kerfs` $\rightarrow$ `kerf`, `undercutting` $\rightarrow$ `undercut`, `coalescence`) | `100.0% PASS (3/3)` |
| **Slice 5** | Natural-Language Adversarial & Out-of-Scope Traps | `G55-NLQ13` – `G55-NLQ15` | Refusal boundaries (`cryo-ionic` $\rightarrow$ `NOT_IN_STANDARD`, preheat/Charpy $\rightarrow$ `REFUSAL_OUT_OF_SCOPE`, SMAW $\rightarrow$ `CONTRADICTION_REFUTED`) | `100.0% PASS (3/3)` |

### Gate 5.5 Deliverables Checklist

- [x] **Deliverable 1 (`src/semantic_nlq_expander.py`):** Deterministic, store-derived Semantic Expansion Engine mapping process codes (`Tables A1/A2/A4/A5`), nonstandard terms (`Annex C`), historical terms (`Annex D`), morphological variants (`Clause 4`), and inverted `Figure`/`Table` concept signatures (`Annex A` & `Annex B`) with auditable `semantic_expansion_trace` output.
- [x] **Deliverable 2 (ID-Free Routing & Conversational Extractor in `src/evidence_phase4_bakeoff.py`):** ID-free routing to `Figures A1–A6`, `Tables A1–A5`, and `Figures B1–B54`; conversational noun-phrase extraction; generalized out-of-scope refusal logic (`HK-5-1`).
- [x] **Deliverable 3 (DeepSeek-V4.1-Flash-1017 Integration in `src/deepseek_v41_adapter.py`):** Full offline replay integration with `plan_with_semantic_expansion`, epistemic quarantine, and 8 content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/`.
- [x] **Deliverable 4 (Frozen 15-Query Gate 5.5 NLQ Benchmark):** `storage/evidence_v2/phase5_5_nlq_001/{nlq_questions.json, rubric.json, results.json}` and `eval/run_phase5_5_nlq.py`, achieving **15 / 15 (100.0%)** across all 5 NLQ slices (`G55-NLQ01` through `G55-NLQ15`).
- [x] **Deliverable 5 (22/22 Artifact Hash Locks & Full Test Suite):** Lock all 14 core project hashes and all 8 DeepSeek replay hashes in `tests/test_gate_5_4_deepseek_adapter.py` and `tests/test_gate_5_5_semantic_nlq.py`, verifying `0` failures and `0` warnings across all `1,455+` repository tests.
