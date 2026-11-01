# AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Master Roadmap (`ROADMAP.md`)

- **Lead Developing Agent:** `gemini-3.8-flash` (Antigravity Local Execution)
- **Principal Reviewer & Systems Architect:** Principal Audit Loop (`aws-a30-gate-review` & `aws-a30-lead-developer`)
- **Target Standard:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 13th Edition, 190 PDF pages)
- **Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`
- **Repository:** `https://github.com/kaiello/aws-a30-prototype`
- **Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synced via `python -B -m src.sync_drive_mirror`)
- **Current Test Suite Baseline:** `1,449 passed, 8 skipped, 0 failures, 0 warnings` (advancing to `1,455+` in Gate 5.3)
- **Active Milestone:** **Gate 5.3 — Deterministic Store-Derived Semantic Expansion & ID-Free NLQ Hardening** (Final Pre-Merge Extension on `feat/gate-5-production-hardening` $\rightarrow$ `main`)

---

## 1. Master Gate Progression & Checkpoint Ledger (Gates 0 $\rightarrow$ 5.3)

| Phase / Gate | Target Scope & AWS A3.0 Coordinates | Branch / Merge SHA | Status & Key Verification Metrics |
| :--- | :--- | :--- | :--- |
| **Gate 0** | Environment, PDF Lock & Coordinate Formula ($\text{printed} = \text{pdf\_index} - 12$) | `43bde2e5` | `PASSED & MERGED` — Locked 190-page PDF SHA-256 (`205fa58e...`). |
| **Gate 1A** | Archetype 1 Calibration: `Figure A1` (p. 75, PDF 87) & `Figure A2` (p. 76, PDF 88) | `4bc7ab31` | `PASSED & MERGED` — 99 A1 nodes, 127 edges; offline graph & preflight verified. |
| **Gate 1B** | Phase 1 Live LLM Holdout Closeout (`Figures A1 & A2`) | `11aa384b` $\rightarrow$ `main` `2fbaabd8` | `PASSED & MERGED` — 67/67 live planner calls PASS (51/51 A1, 16/16 A2). |
| **Gate 2A** | `Figure A3` — Joining Method Chart (p. 76, PDF 88) | `66317d41` $\rightarrow$ `main` `66937d94` | `PASSED & MERGED` — 11 nodes, 10 edges, 0 cycles, 0 `IS_A`; 114/114 unit tests. |
| **Gate 2B** | `Figure A4` — Fusion Welding Classification Chart (p. 77, PDF 89) | `d1dbf994` $\rightarrow$ `main` `5108cba3` | `PASSED & MERGED` — 66 nodes, 42 edges, 26 process circles, 23 legend rows. |
| **Gate 2C** | `Figure A5` — Solid-State Welding Classification Chart (p. 78, PDF 90) | `6b2d6265` $\rightarrow$ `main` `e080a709` | `PASSED & MERGED` — 68 nodes, 66 edges, 22 process circles, 15 legend rows; CW/USW/EXW verified. |
| **Gate 2D** | `Figure A6` — Brazing and Soldering Classification Chart (p. 79, PDF 91) | `47922e81` $\rightarrow$ `main` `e86157c4` | `PASSED & MERGED` — 104 nodes, 102 edges, 48 process circles, 21 legend rows; `AB` collision logged. |
| **Gate 2E** | Normative `Tables A1–A5` Join & Tier 1/2 Exhaustive Closure (pp. 69–74, PDF 81–86) | `d55eba2` $\rightarrow$ `main` `4bd5d0b` | `PASSED & MERGED` — 138 A1, 133 A2, 134 A3, 6 A4, 13 A5 rows; 564/564 unit tests. |
| **Gate 2F** | Annex A Live LLM Holdout Closeout (`Figures A1–A6` + `Tables A1–A5`) | `7e48e52` $\rightarrow$ `main` `6fa2cde` | `PASSED & MERGED` — 30/30 (100.0%) unseen holdout PASS, 127 executed ops, 0 blocked actions. |
| **Gate 3A** | `Clause 4` Glossary + Dual-Provenance `IS_A` + `Annex C/D` (pp. 5–67, 159–170) | `728ceed` $\rightarrow$ `main` `f9ec225` | `PASSED & MERGED` — 1,607 glossary terms, 311 `NONSTANDARD_SYNONYM_OF`, 35 `IS_A` promoted / 83 retained, 21 Annex C clauses, 591 Annex D rows. |
| **Gate 3B** | Archetype 3 Spatial Callout Calibration: `Figures B1–B6` (pp. 82–89, PDF 94–101) | `d8fb23d` $\rightarrow$ `main` `31d7d65` | `PASSED & MERGED` — 6 figures across 8 pages (34 sub-panels), 55 B1 applicable welds, 86 nodes, 210 edges. |
| **Gate 3C** | Archetype 4 Waveforms (`B44–B45, B49–B51, B53–B54`) + Complete `Annex B` (`B1–B54`) | `937dad7` $\rightarrow$ `main` | `PASSED & MERGED` — 56 figure units across 76 pages, 80/80 300-DPI crops, 1,115 nodes, 1,917 edges, 265/265 Clause 4 figure back-links. |
| **Gate 3D** | Phase 3 Live Holdout Closeout (`Clause 4` + `Annex B` + `Annex C/D` Cross-Modal Suite) | `263bfdb` $\rightarrow$ `main` | `PASSED & MERGED` — 40/40 (100.0%) unseen holdout PASS across 4 balanced 10-question slices (`P3-S1` to `P3-S4`). |
| **Gate 4** | Whole-Standard Production Bakeoff (`Clause 4` + `Annex A/B/C/D`) | `8dff8b6` $\rightarrow$ `main` `42e9658` | `PASSED & MERGED` — 35/35 (100.0%) production bakeoff PASS across all 5 evaluation dimensions; 1,442 unit tests. |
| **Gate 4B** | Multi-Hop Cross-Store Retrieval Stress Test (`2–4` Sequential Store Hops) | `feat/gate-4b-multihop-retrieval-stress-test` | `PASSED` — Chained 2–4 sequential store operations with verified `hop_trace` provenance across stores. |
| **Gate 5.0–5.2** | Production Hardening, AST Zero-Fallback Guard, Adversarial Benchmark & Audit Remediation (`DRIFT-5-1..5-5`) | `e9a5621` (+ `DRIFT-5-1..5-5` fixes on `feat/gate-5-production-hardening`) | `VERIFIED_READY` — 10/10 (`100.0%`) adversarial benchmark (`G5-ADV01..10`), AST zero-fallback guard, 7-target store mutation test, socket-isolated preflight (`CLEAR_WHOLE_STANDARD_CONTRACT`), `1,449 passed, 8 skipped, 0 warnings`. |
| **Gate 5.3** | **Semantic Query Expansion & ID-Free NLQ Hardening (`src/semantic_nlq_expander.py`)** | `feat/gate-5-production-hardening` $\rightarrow$ `main` | **`ACTIVE FINAL GATE`** — Offline store-derived synonym/alias/abbreviation expansion, ID-free `Figure`/`Table` routing, conversational term extraction, generalized out-of-scope boundary classifier, and 15-query NLQ benchmark (`G53-NLQ01..15`). |

---

## 2. Cryptographic Immutability Ledger (14 Locked Repository Artifacts)

All operational, evaluation, and semantic expansion code in Gate 5 / Gate 5.3 must treat the canonical Phase 0–3 stores and frozen benchmark suites as **100% read-only**. `tests/test_gate_5_hardening.py` and `tests/test_gate_5_3_semantic_nlq.py` enforce exact SHA-256 verification across all 14 locked files:

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
| 12 | **Phase 5.3 NLQ Questions** | `storage/evidence_v2/phase5_3_nlq_001/nlq_questions.json` | `ce97f7a4628d2df9d8a40b29357325696c8299f8ebca53be562ce593e337a641` | `VERIFIED_LOCKED` |
| 13 | **Phase 5.3 NLQ Rubric** | `storage/evidence_v2/phase5_3_nlq_001/rubric.json` | `824a97cd67faa0ae91cc07cb3d5b4d6d0c8a30c9970566ee2b10fd780c8e60a7` | `VERIFIED_LOCKED` |
| 14 | **Phase 5.3 NLQ Results** | `storage/evidence_v2/phase5_3_nlq_001/results.json` | `7c42dbbe6272f61bcb07e2f17e5cbd89d64d4e8900c21310fcace84c4994fbcd` | `VERIFIED_LOCKED` |

---

## 3. Core Architectural Invariants & Anti-Drift Rules (Enforced in CI)

1. **Zero Question-ID or Benchmark-Literal Hardcoding (`test_gate_5_anti_drift_source_scan` & `test_gate_5_3_anti_drift_and_anti_overfitting`):**
   - Operational modules (`src/*.py`) and evaluators (`eval/*.py`) must return `0 matches` for any benchmark question ID pattern:
     ```powershell
     git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+" -- src/ eval/*.py
     ```
   - Operational modules (`src/*.py`) must return `0 matches` for benchmark-specific trap literals:
     ```powershell
     git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/
     ```
2. **AST Zero Silent Fallback Guarantee (`test_gate_5_composer_ast_no_silent_string_fallbacks`):**
   - No composer function may call `.get(key, "non_empty_literal")` to mask missing store data. Missing or corrupted store structures must raise `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
3. **Whole-Standard Offline Preflight Contract (`src/evidence_whole_standard_preflight.py`):**
   - `answer_whole_standard_question` executes under `socket.socket` interception (`0` network calls), verifies input immutability, delivers normative page/crop provenance, and confirms all canonical store hashes remain untouched (`CLEAR_WHOLE_STANDARD_CONTRACT`).

---

## 4. Gate 5.3 Deliverables & Final Production Closeout Checklist

### Gate 5.3 Benchmark Slices (`storage/evidence_v2/phase5_3_nlq_001/nlq_questions.json`)

| Slice | Category / Focus | Query IDs | Target Stores & Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Slice 1** | ID-Free Annex A Chart & Table NLQs | `G53-NLQ01` – `G53-NLQ03` | Table A4, Figure A5, Annex D (Modes, Classification Tree, Obsolete Codes) | `100.0% PASS (3/3)` |
| **Slice 2** | ID-Free Annex B Visual & Waveform NLQs | `G53-NLQ04` – `G53-NLQ06` | Figures B50, B33, B49 (Pulsed cycles, Edge shapes, Resistance spot waveforms) | `100.0% PASS (3/3)` |
| **Slice 3** | Historical, Nonstandard & Abbreviation Semantic Expansion | `G53-NLQ07` – `G53-NLQ09` | Clause 4, Annex C/D, Table A1 (`stick electrode` $\rightarrow$ `covered electrode`, `CW` $\rightarrow$ `cold welding`, `AHW` obsolete) | `100.0% PASS (3/3)` |
| **Slice 4** | Conversational & Morphological Clause 4 + `is_a` NLQs | `G53-NLQ10` – `G53-NLQ12` | Clause 4 glossary + Figure B38 (`kerfs` $\rightarrow$ `kerf`, `undercutting` $\rightarrow$ `undercut`, `coalescence`) | `100.0% PASS (3/3)` |
| **Slice 5** | Natural-Language Adversarial & Out-of-Scope Traps | `G53-NLQ13` – `G53-NLQ15` | Refusal boundaries (`cryo-ionic` $\rightarrow$ `NOT_IN_STANDARD`, preheat/Charpy $\rightarrow$ `OUT_OF_SCOPE`, SMAW $\rightarrow$ `REFUTED`) | `100.0% PASS (3/3)` |

### Gate 5.3 Deliverables Checklist

To complete Gate 5.3 and merge `feat/gate-5-production-hardening` into `main`:

- [x] **Deliverable 1 (`src/semantic_nlq_expander.py`):** Build the deterministic, store-derived Semantic Expansion Engine mapping process codes (`Tables A1/A2/A4/A5`), nonstandard terms (`Annex C`), historical terms (`Annex D`), morphological variants (`Clause 4`), and inverted `Figure`/`Table` concept signatures (`Annex A` & `Annex B`) with auditable `semantic_expansion_trace` output.
- [x] **Deliverable 2 (ID-Free Routing & Conversational Extractor in `src/evidence_phase4_bakeoff.py`):** Enable ID-free routing to `Figures A1–A6`, `Tables A1–A5`, and `Figures B1–B54`; replace `"the term "` prefix stripping with general conversational noun-phrase extraction; generalize out-of-scope refusal logic (`HK-5-1`).
- [x] **Deliverable 3 (Frozen 15-Query Gate 5.3 NLQ Benchmark):** Create `storage/evidence_v2/phase5_3_nlq_001/{nlq_questions.json, rubric.json, results.json}` and `eval/run_phase5_3_nlq.py`, achieving **15 / 15 (100.0%)** across all 5 NLQ slices (`G53-NLQ01` through `G53-NLQ15`).
- [ ] **Deliverable 4 (14/14 Artifact Hash Locks & Full Test Suite):** Lock all 14 SHA-256 hashes in `tests/test_gate_5_3_semantic_nlq.py`, verify `0` failures and `0` warnings across all `1,455+` repository tests, rebuild `GATE_5_FULL_AUDIT_BUNDLE.md` via `python -B scripts/build_gate_5_bundle.py`, merge `--no-ff` to `main`, push to `origin`, and run `python -B -m src.sync_drive_mirror`.
