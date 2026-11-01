# AWS A3.0M/A3.0:2020 Multimodal RAG Master Roadmap & Cryptographic Invariant Ledger

**Document Purpose:** Living architectural contract, milestone roadmap, and cryptographic provenance ledger for the AWS A3.0M/A3.0:2020 source-aware multimodal graph ingestion and retrieval system.

---

## 1. Project Overview & Gate Status Summary

- **Standard Document:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 190 PDF pages / 162 ingested canonical store pages)
- **Current Test Suite Baseline:** `1,482 passed, 8 skipped, 0 failures, 0 warnings`
- **Active Milestone:** **Gate 6.1 — Polysemous Welding NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion** (`feat/gate-6-1-ner-semantic-graph-expansion` $\rightarrow$ `main`, tagged `v1.6.1-ner-semantic-graph`)
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
| **Gate 5.5** | Unified Final Production Release: Semantic NLQ Expansion, ID-Free Routing, and DeepSeek-V4.1 Integration | `feat/gate-5-5-semantic-nlq` $\rightarrow$ `main` (`e31b8e2`) | `PASSED & MERGED` — Store-derived Semantic Expansion Engine, ID-free `Figure`/`Table` routing, conversational noun-phrase extraction, generalized out-of-scope refusal (`HK-5-1`), 8 locked DeepSeek replay cassettes, 15/15 (100.0%) NLQ benchmark. |
| **Gate 5.6** | Epistemic Claims Calibration, Coverage Manifest, Latency Telemetry & Conditional Visual Provenance | `feat/gate-5-6-epistemic-manifest-calibration` $\rightarrow$ `main` (`dd22331`, `v1.5.6-gate-5-6-calibrated`) | `PASSED & MERGED` — Whole-standard 190-page coverage manifest (`162` ingested, `28` excluded), empirical latency telemetry ($p_{50}: 55.5\text{ ms}$ offline det, $54.0\text{ ms}$ replay), conditional diagram crop requirement, calibrated epistemic claims, 24/24 locked artifacts. |
| **Gate 6.0** | GitOps Branch Reconciliation, Deterministic Welding NER, Callout/Backlink Multi-Intent Router & Whole-Standard Agent Skills | `feat/gate-6-0-ner-routing-skills` $\rightarrow$ `main` (`v1.6.0-ner-routing-skills`) | `PASSED & MERGED` — `origin` pruned `10` $\rightarrow$ `1` clean `main`, character-offset `WeldingNER` (`11` entity types, dynamic `<BASE>-<SUFFIX>` parser, multi-POS/homograph tracking), `1,115`-node Annex B + `96`+ Annex A circle + `492`-edge Clause 4 backlink IDF router, `src.evidence_whole_standard_cli`, modernized `.agents/skills/`, `20/20` (`100.0%`) Gate 6.0 benchmark, `29/29` locked SHA-256 artifacts, `1,475 passed, 8 skipped`. |
| **Gate 6.1** | **Polysemous Welding NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion** | `feat/gate-6-1-ner-semantic-graph-expansion` $\rightarrow$ `main` (`v1.6.1-ner-semantic-graph`) | **`PASSED & READY TO MERGE`** — Character-offset polysemous spans (`secondary_entity_types`, `linked_clause4_terms`, `linked_figures`, `linked_tables`), 3-tier compound grammar `<BASE>[-<VAR>][-<MODE>]` (`FCAW-G-SA`, `OFC-A-MA`, invalid code rejection), in-memory `SemanticConceptGraph` (see-also, IS_A subtypes, sibling variations, co-callouts), whole-standard CLI `--expand`, `15/15` (`100.0%`) Gate 6.1 benchmark, `34/34` locked SHA-256 artifacts, `1,482 passed, 8 skipped`. |

---

## 2. Cryptographic Immutability Ledger (34 Locked Repository Artifacts)

All operational, evaluation, and semantic expansion code must treat the canonical Phase 0–3 stores, frozen benchmark suites, offline model replay cassettes, and system manifests as **100% read-only**. `tests/test_gate_5_hardening.py`, `tests/test_gate_5_4_deepseek_adapter.py`, `tests/test_gate_5_5_semantic_nlq.py`, `tests/test_gate_5_6_epistemic_manifest.py`, `tests/test_gate_6_0_ner_routing_skills.py`, and `tests/test_gate_6_1_semantic_graph.py` enforce exact SHA-256 verification across all 34 locked files:

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

### Part E: 3 Gate 6.1 Benchmark Artifacts (Semantic Graph Benchmark)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 30 | **Gate 6.1 Questions** | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7` | `VERIFIED_LOCKED` |
| 31 | **Gate 6.1 Rubric** | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5` | `VERIFIED_LOCKED` |
| 32 | **Gate 6.1 Results** | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf` | `VERIFIED_LOCKED` |

### Part F: 2 Gate 6.1 DeepSeek Replay Cassettes

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 33 | **Gate 6.1 3-Tier + Fusion Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432` | `VERIFIED_LOCKED` |
| 34 | **Gate 6.1 Compound + Throat Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993` | `VERIFIED_LOCKED` |

### Version-Bound Store Immutability Policy
Cryptographic SHA-256 digests lock each released store version (`*_001`). Verified content corrections or spatial refinements produce a successor version (`*_002`) with a documented migration ledger rather than mutating locked releases in place.

### Machine-Verifiable 190-Page Coverage Manifest
`storage/manifests/coverage_manifest.json` accounts for all 190 PDF pages:
- **162 Ingested Pages:** Clause 4 (PDF 17–79), Tables A1–A5 (PDF 81–86), Figures A1–A6 (PDF 87–91), Annex B Figures B1–B54 (PDF 94–169), Annex C Decisions (PDF 171–176), Annex D Tables D1–D6 (PDF 177–182).
- **28 Excluded Pages:** Front matter and TOC (PDF 1–12), introductory administrative scope (PDF 13–16), section dividers / blank pages (PDF 80, 92–93, 170), and Informative Index / back matter (PDF 183–190).

### Modality-Appropriate Conditional Crop Provenance
Every non-refusal answer includes universal page coordinates (`printed_page`, `pdf_index`) and structured `evidence_locator`. A 300-DPI diagram crop (`crop_path`) is attached with `requires_diagram_crop: True` **when and only when** the answer depends on a visual diagram (`Figures A1–A6` or `Figures B1–B54`). For text-only and tabular lookups (`Clause 4`, `Annex C/D`, `Tables A1–A5`), `requires_diagram_crop: False` is set and spurious diagram crops are omitted.

---

## 3. Core Architectural Invariants & Anti-Drift Rules (Enforced in CI)

1. **Zero Question-ID or Benchmark-Literal Hardcoding (`test_gate_5_anti_drift_source_scan`, `test_gate_5_4_anti_drift_regex_coverage`, `test_gate_5_5_anti_drift_and_anti_overfitting`, & `tests/test_gate_5_6_epistemic_manifest.py`):**
   - Operational modules (`src/*.py`) and evaluators (`eval/*.py`) must return `0 matches` for any benchmark question ID pattern:
     ```powershell
     git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+" -- src/ eval/*.py
     ```
   - Operational modules (`src/*.py`) must return `0 matches` for benchmark-specific trap literals:
     ```powershell
     git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/
     ```
2. **Epistemic Quarantine of Model Traces (`src/deepseek_v41_adapter.py`):**
   - Every `part.reason` emitted by `DeepSeek-V4.1-Flash-1017` is lowered to `PLANNED_REASON` (`""`) in internal wire plans and quarantined in `model_part_metadata` with `authority: "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"`. It never enters final answers or provenance citations.
   - Multimodal visual candidate observations emitted by `DeepSeekV41VisualCandidateVerifier` strictly carry `verification="candidate"` and `knowledge_eligible=False`.
3. **AST Zero Silent Fallback Guarantee (`test_gate_5_composer_ast_no_silent_string_fallbacks`):**
   - No composer function may call `.get(key, "non_empty_literal")` to mask missing store data. Missing or corrupted store structures must strictly raise `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
4. **Strict Offline Test & Preflight Isolation (`src/evidence_whole_standard_preflight.py`):**
   - `answer_whole_standard_question` and `run_deepseek_replay_preflight` execute under `socket.socket` interception (`0` network calls), reading deterministic content-addressed replay fixtures, verifying input immutability, and confirming all canonical store hashes remain untouched (`CLEAR_WHOLE_STANDARD_CONTRACT` / `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`).

---

## 4. Gate 5.6 Deliverables Checklist

- [x] **Deliverable 1 (`scripts/build_coverage_manifest.py` $\rightarrow$ `storage/manifests/coverage_manifest.json`):** Whole-standard coverage manifest accounting for all 190 PDF pages (162 ingested, 28 excluded) and reconciling exact entity counts across all 6 canonical stores.
- [x] **Deliverable 2 (`eval/run_latency_benchmark.py` $\rightarrow$ `storage/manifests/latency_benchmark.json`):** Measured latency benchmark ($p_{50}: 55.5\text{ ms}$, $p_{95}: 70.2\text{ ms}$ deterministic; $p_{50}: 54.0\text{ ms}$, $p_{95}: 67.1\text{ ms}$ replay) with explicit zero external API charge qualification.
- [x] **Deliverable 3 (Modality-Appropriate Provenance in `src/evidence_phase4_bakeoff.py`):** Universal `printed_page`, `pdf_index`, and `evidence_locator`; conditional 300-DPI diagram crop with `requires_diagram_crop: True` for visual diagrams and `requires_diagram_crop: False` (omitting crops) for glossary and tabular lookups.
- [x] **Deliverable 4 (Epistemic Hygiene & Documentation Synchronization):** Replaced marketing language with source-grounded composition, explicit abstention, and measured robustness; documented version-bound store immutability (`*_001` $\rightarrow$ `*_002`); synchronized `goal.md`, `ROADMAP.md`, and review packets.
- [x] **Deliverable 5 (24/24 Cryptographic Hash Locks in `tests/test_gate_5_6_epistemic_manifest.py`):** All 22 prior artifacts plus the 2 new Gate 5.6 manifests cryptographically verified under CI test suite.

---

## 5. Gate 6.0 Deliverables Checklist (Welding Domain NER, Callout/Backlink Routing & Whole-Standard Skills)

- [x] **Deliverable 1 (`src/welding_ner.py`):** Deterministic Welding Domain Named Entity Recognizer & dynamic compound code parser resolving 11 domain entity categories, character-offset matching, longest-match precedence, and homograph candidate tracking (`AB`).
- [x] **Deliverable 2 (`src/semantic_nlq_expander.py` & `src/evidence_phase4_bakeoff.py`):** Inverted Annex B spatial callout graph (1,115 callout terms), Clause 4 figure backlink graph (265 edges), and multi-intent action planner for cross-store multi-hop queries.
- [x] **Deliverable 3 (`src/evidence_whole_standard_cli.py` & `.agents/skills/`):** Whole-standard CLI entry point (`--ner`, `--route`, `--ask`) and updated skill playbooks replacing legacy Figure A1 limitations.
- [x] **Deliverable 4 (`storage/evidence_v2/phase6_ner_routing_001/` & `eval/run_phase6_ner_routing.py`):** Frozen 20-question Gate 6.0 benchmark scoring **20 / 20 (100.0%)** across compound designations, ID-free callouts, homographs, multi-hop queries, and adversarial boundaries.
- [x] **Deliverable 5 (29/29 Cryptographic Hash Locks & Regression Suite in `tests/test_gate_6_0_ner_routing_skills.py`):** 24 prior locked hashes + 5 Gate 6.0 artifacts cryptographically locked under CI; full regression suite passing at 1,475 passed, 8 skipped, 0 failures, 0 warnings.

---

## 6. Gate 6.1 Deliverables Checklist (Polysemous NER, 3-Tier Compound Grammar & Semantic Concept Graph Expansion)

- [x] **Deliverable 1 (`src/welding_ner.py`):** Extended `WeldingEntitySpan` with `secondary_entity_types`, `linked_clause4_terms`, `linked_figures`, `linked_tables`, and `ambiguous_senses`; dual-role routing for definitional intent queries.
- [x] **Deliverable 2 (`src/welding_ner.py`):** 3-tier compound designation parser `<BASE>[-<VAR>][-<MODE>]` with process variations (`FCAW-G-SA`, `OFC-A-MA`), invalid code detection (`FCAW-Z-SA`, `PAW-AU-ME`), and contextual sense resolution for weld positions (`1G`, `1F`) and homographs (`AB`).
- [x] **Deliverable 3 (`src/semantic_nlq_expander.py`):** Deterministic in-memory `SemanticConceptGraph` tracking `see_also_edges`, `is_a_subtypes`, `sibling_variations`, and diagram co-callouts; bidirectional expansion for throat and angle clusters.
- [x] **Deliverable 4 (`src/evidence_whole_standard_cli.py` & `src/evidence_phase4_bakeoff.py`):** CLI `--expand` flag returning structured neighborhood, NER receipt, and ranked figures; multi-hop execution branch for compound validation, test positions, disambiguation, and see-also cross references.
- [x] **Deliverable 5 (34/34 Cryptographic Hash Locks & Regression Suite in `tests/test_gate_6_1_semantic_graph.py`):** 29 prior locked hashes + 3 Gate 6.1 benchmark files + 2 new DeepSeek-V4.1 replay cassettes locked under CI; full regression suite passing at 1,482 passed, 8 skipped, 0 failures, 0 warnings.


