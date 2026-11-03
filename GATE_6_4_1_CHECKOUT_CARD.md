# Gate 6.4.1 Checkout & Closeout Card: Provenance Integrity Remediation

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `8f8616e` (`v1.6.4-comprehensive-enhancements`)  
**Target Branch:** `fix/gate-6-4-1-provenance-integrity` $\rightarrow$ `main`  
**Release Tag:** `v1.6.4.1-provenance-integrity`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Executive Summary & Forensic Audit Remediation

Following the release of Gate 6.4 (`v1.6.4`), an immediate forensic audit identified 9 integrity and hygiene findings (3 provenance defects, 3 execution drifts, 1 evaluation accounting drift, 1 test coverage drift, and 1 bundle hygiene drift). Gate 6.4.1 completely remediates all 9 findings under the project's non-negotiable principle: **all emitted platform content must be rigorously grounded in verified source evidence with uncompromised provenance.**

### Remediation Ledger (All 9 Findings Resolved)

| Finding ID | Severity | Description | Remediation Implemented in Gate 6.4.1 |
| :--- | :---: | :--- | :--- |
| **`PROV-6.4-1`** | 🔴 Critical | 6 synthetic cassettes mislabeled as DeepSeek model outputs | Quarantined from `storage/model_replays/deepseek_v4_1_flash_1017/` to `storage/model_replays/deterministic_planner_fixtures/` with `model_id: "DeterministicQuestionPlanner"`, `epistemic_tag: "SYNTHETIC_PLANNER_FIXTURE_NOT_MODEL_OUTPUT"`, and `cassette_origin: "synthetic_planner_fixture"`. Committed reproducible generator `scripts/generate_deterministic_planner_fixtures.py`. Accurate accounting: exactly 14 genuine DeepSeek cassettes locked. |
| **`PROV-6.4-2`** | 🔴 Critical | Fabricated Clause 4 definitions for Figure B46 "Tool Shoulder" and "Probe" | Removed all fabricated definition strings in `src/archetype_spatial_callout.py`. Emitted verified Figure B46 key-item labels from Annex B store and real Clause 4 definitions for `advancing side` and `retreating side`. Explicitly and truthfully notes that `tool shoulder`, `probe`, `TMAZ`, and `stir zone` have no separate normative definition entries in Clause 4. |
| **`PROV-6.4-3`** | 🟠 High | Table A3 summary hardcoded false range "AB through W" | In `_compose_table_a3_cross_reference` (`src/evidence_phase4_bakeoff.py`), dynamically derived the first designation (`AB`), first process (`adhesive bonding`), last designation (`WS`), last process (`wave soldering`), page range (`printed pp. 72–73`), and PDF range (`PDF index 84–85`) strictly from `table_a3` store. Removed literal `"W"` from `elements_present`. |
| **`EXEC-6.4-4`** | 🟠 High | Direct disk reads (`open(...)`) in spatial callout composer | Eliminated direct `open(...)` calls to `glossary_store.json` in `src/archetype_spatial_callout.py`. Strictly uses injected stores. Constrained `elements_present` to a strict subset of strings genuinely appearing in `answer_text`. Handled "See Figure B33" cross-references transparently. |
| **`EXEC-6.4-5`** | 🟡 Medium | Substring over-matching in Table A3 cross-referencing | Implemented word-boundary regex matching (`re.search(rf"\b{re.escape(proc_lower)}\b", q_lower)`) and strict subsumption filtering: if row A's process is a substring of matched row B's process, row A is suppressed unless explicitly designated. "torch brazing" now returns only `TB` (not `B`), and "gas tungsten arc welding" returns only `GTAW` (not `AW`). |
| **`EXEC-6.4-6`** | 🟡 Medium | Brittle repeated keyword exclusion lists (`"magnetic pulse"`, `"mpw"`) | Refactored Priority 17b, Priority 22, and `_compose_normative_tables_answer` in `src/evidence_phase4_bakeoff.py` to route based on structural intent rather than hardcoded process names. Queries specifically targeting Table A1 primary process classifications route to Table A1 without polluting Table A3 logic. |
| **`EVAL-6.4-7`** | 🟡 Medium | Silent fallback and non-transparent replay accounting | Updated `eval/run_phase6_3_blind_hardening.py` to record `planner_source` per query and report exact counts for `model_replays_count`, `synthetic_fixtures_count`, and `deterministic_fallbacks_count`. Added `--strict-replay` flag that fails if any query lacks a genuine model replay cassette. Added `--use-fixtures` flag for synthetic fixture testing. |
| **`TEST-6.4-8`** | 🟡 Medium | Missing AST checks for direct disk reads and definition prose in spatial callers | Expanded `test_gate_6_4_ast_zero_fallbacks_across_all_13_functions` in `tests/test_gate_6_4_comprehensive_enhancements.py` to inspect `src/archetype_spatial_callout.py`, asserting 0 `open()` calls, 0 `.read_text()` / `.read_bytes()` calls, and 0 fabricated definition strings. Added property assertion that `elements_present` $\subseteq$ `answer_text`. |
| **`HYG-6.4-9`** | ⚪ Low | `build_gate_6_bundle.py` overwriting Gate 5 audit bundles | Removed Gate 5 targets from `scripts/build_gate_6_bundle.py`. Restored genuine Gate 5 audit bundle (508,291 bytes) via `scripts/build_gate_5_bundle.py`. Gate 6 bundle now exclusively generates Gate 6 bundle targets. |

---

## 2. Benchmark Evaluation Transparency (Gate 6.3 Blind Hardening)

Running `eval/run_phase6_3_blind_hardening.py` across different operational modes produces transparent, verified accounting:

1. **Deterministic Mode (`--no-write`):**
   - Result: **20/20 passed (100.0%)**
   - Accounting: `Model Replays: 0 | Synthetic Fixtures: 0 | Deterministic Fallbacks: 20`
2. **Model Replay Mode (`--no-write --use-replay-cassettes`):**
   - Result: **20/20 passed (100.0%)**
   - Accounting: `Model Replays: 0 | Synthetic Fixtures: 0 | Deterministic Fallbacks: 20` (unmatched queries transparently fall back to deterministic planner)
3. **Fixture-Augmented Mode (`--no-write --use-replay-cassettes --use-fixtures`):**
   - Result: **20/20 passed (100.0%)**
   - Accounting: `Model Replays: 0 | Synthetic Fixtures: 6 | Deterministic Fallbacks: 14`
4. **Strict Model Replay Mode (`--no-write --use-replay-cassettes --strict-replay`):**
   - Result: **Strict replay failure** with `RuntimeError: Strict replay failure: no genuine model replay cassette found for query G63-BLIND01` (truthful failure on unrecorded queries).

---

## 3. Cryptographic Lock Ledger (All 51 Locked Artifacts)

### Immutable Baseline (All 45 Releases Hashes 100% Unchanged)
All 45 baseline hashes match byte-for-byte with zero drift:
- `#1`–`#14`: Phase 4/5/6 Ingestion, Graph, and Table stores.
- `#15`–`#28`: Exactly **14 genuine DeepSeek-V4.1-Flash-1017 replay cassettes** under `storage/model_replays/deepseek_v4_1_flash_1017/`.
- `#29`–`#45`: Evaluation benchmark suites (Gate 5.5, Gate 6.0, Gate 6.1, Gate 6.2, Gate 6.2.1, Gate 6.3).

### Quarantined Synthetic Planner Fixtures (6 Artifacts)
Stored under `storage/model_replays/deterministic_planner_fixtures/` with `epistemic_tag: "SYNTHETIC_PLANNER_FIXTURE_NOT_MODEL_OUTPUT"`:

| Index | Rel Path | SHA-256 Digest | Status |
| :---: | :--- | :--- | :---: |
| 46 | `storage/model_replays/deterministic_planner_fixtures/07d3e65cc2f0f4bab38963fdcb9c7c704615a5c046f019365a3ec3b24ad669ec.json` | `ea4cb468af3dc574f06940672fa2b33537b236140c4e6de3cc5c20b849f6908f` | MATCH |
| 47 | `storage/model_replays/deterministic_planner_fixtures/1a0d448e9483f699ecb6fba379971dd65059b4aba5344f1e8708b2d7bca8845c.json` | `85e7876785e941ce4ba8bff4c8284be4070827f6c26437431f0120fd8a20d71f` | MATCH |
| 48 | `storage/model_replays/deterministic_planner_fixtures/73ccb5c640979dc600a4e9d349178667a048ee9ece3b3fc36513a042e3427182.json` | `4f164b170792437eb74b96b64a946d4717a870c1ca98e65da2223ba69206a935` | MATCH |
| 49 | `storage/model_replays/deterministic_planner_fixtures/78072b41bac7406dd5fa8749643b9320e380548bd065f4af56dd2571940d021f.json` | `3134d3405387ab421f2c1a31879c776bd3c219ba29dd83ba3973ede8b70d2c46` | MATCH |
| 50 | `storage/model_replays/deterministic_planner_fixtures/c2b781b11a1f795ae75679362554299d5c2ab8f3bb74ca82e69e90adf6623033.json` | `128aa1a26fe77450a76f51d669fc50a6c1a89c89d8c0a87d8473b259a8de771c` | MATCH |
| 51 | `storage/model_replays/deterministic_planner_fixtures/d6401cf2f24c1f017d7e363ea8de410ccd672178512b655bdc6b0c102e47b8a7.json` | `b21d7621afc83a115b5b4bda999798cf23a39fd1f2c496f8b8d40751193af3cd` | MATCH |

---

## 4. Verification Sign-off

- **Unit Test Suite:** `tests/test_gate_6_4_comprehensive_enhancements.py` passed 7/7 (100%).
- **Bakeoff Test Suite:** `tests/test_gate_4_production_bakeoff.py` passed 8/8 (100%).
- **Store Composition Suite:** `tests/test_gate_6_2_store_driven_composition.py` passed 7/7 (100%).
- **AST Zero-Fallback & Zero-Disk-Read Guard:** Passed with 0 violations across all 13 composer functions and `compose_spatial_callout_answer`.
- **Offline Integrity:** 100% offline socket isolation verified (`0` network calls).
