# Implementation Milestone Card: Gate 6.2.2 — Post-6.2.1 Closeout Hygiene, Google Drive 42-Artifact Mirror Parity, Repo Doc Alignment & Post-Merge Audit Bundle

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `d67508f` (`v1.6.2.1-multi-action-closure`)  
**Target Branch:** `feat/gate-6-2-2-closeout-hygiene`  
**Target Release Tag:** `v1.6.2.2-closeout-hygiene`  
**Audit Bundle:** [GATE_6_FULL_AUDIT_BUNDLE.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_FULL_AUDIT_BUNDLE.md)  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Goal Description & Background

Forensic review of Gate 6.2.1 (`v1.6.2.1-multi-action-closure` @ `d67508f`) confirmed that the core whole-standard QA engine is sound (`1,494 passed, 8 skipped`, `0` network calls, `42/42` locked SHA-256 digests intact on disk, `12/12` end-to-end store mutations raising `INSUFFICIENT_EVIDENCE`, and `20/20` passing on `phase6_2_generalization_holdout_002`). However, six concrete closeout and hygiene discrepancies remain across mirror synchronization, in-repository documentation, audit bundle metadata, evaluator CLI options, and two minor composer branches:

1. **`MIRROR-DRIFT` ([sync_drive_mirror.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/sync_drive_mirror.py#L145)):** `ev_dir.glob("*_001")` excluded `storage/evidence_v2/phase6_2_generalization_holdout_002/` (`3` locked files) from syncing to Google Drive, and omitted `storage/manifests/` (`2` locked manifests) and `scripts/`.
2. **`REPO-DOC-DRIFT` ([goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md#L6-L9), [docs/goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/goal.md#L6-L9), [ROADMAP.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md)):** In-repository architecture and roadmap documents remained at Gate 6.1 / Gate 6.2 (`1,482 passed`, `39` locked artifacts), causing Google Drive to mirror stale project documentation.
3. **`DOC-HASH-DRIFT` ([GATE_6_2_1_CHECKOUT_CARD.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_2_1_CHECKOUT_CARD.md#L89-L90), [GATE_6_2_CHECKOUT_CARD.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_2_CHECKOUT_CARD.md#L28)):** Artifacts `#36` and `#37` (`holdout_001` rubric and results) listed incorrect SHA-256 digests (`e23085ad...` and `f376f9ef...` instead of `bb18c854...` and `dfe96330...`), and line 28 of `GATE_6_2_CHECKOUT_CARD.md` retained the unfixed `(p. 5 for groove, p. 6 for fillet)` typo.
4. **`BUNDLE-DRIFT` ([build_gate_6_bundle.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/scripts/build_gate_6_bundle.py#L84), [GATE_6_FULL_AUDIT_BUNDLE.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_FULL_AUDIT_BUNDLE.md#L3-L10)):** The bundle was generated pre-merge (recording `feat/gate-6-2-1-multi-action-closure` @ orphaned commit `b9c45f37...`), queried nonexistent key `cassettes_verified` (printing `DeepSeek Replay Cassettes Verified: 0` instead of `14`), and omitted the Gate 6.1–6.2.2 checkout cards.
5. **`EVAL-DRIFT` ([run_phase6_2_generalization_holdout.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_2_generalization_holdout.py#L52)):** Missing `--benchmark-dir` CLI flag alias and optional offline `DeepSeekV41PlannerAdapter` replay execution for Slice 5 replay queries (`G62-GEN17`, `G62-GEN18`).
6. **`CODE-HYGIENE` ([evidence_phase4_bakeoff.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py#L1413-L1435)):** `_exec_expand_cross_references` matched `"flux" in seed_target.lower()`, leaking general `flux` neighbors onto single-subtype queries (e.g., `"bonded flux"`), and `compound_designation_and_historical` (L2063–L2084) retained an inline string template instead of delegating to `_exec_compare_historical_and_active` + `_exec_compound_lookup_and_validation`.

> [!IMPORTANT]
> **Zero Locked-Artifact Mutation:** All **42** existing SHA-256 locked artifacts (`data/AWS_A3.0_2020.pdf`, 7 canonical Phase 0–3 stores, 14 DeepSeek replay cassettes, 2 epistemic manifests, and all frozen `*_001` / `*_002` benchmark sets) MUST remain **100% byte-identical**.

---

## 2. Master Integration Register Cross-Reference

Cross-referenced against [`NAVY_WELD_MASTER_INTEGRATION_AND_BAKEOFF_LIST_2026-10-18.md`](file:///C:/Users/kenai/meia_kg_poc/docs/NAVY_WELD_MASTER_INTEGRATION_AND_BAKEOFF_LIST_2026-10-18.md):

| Candidate ID | Master Register Category | Specific Gate 6.2.2 Application | Status |
| :---: | :--- | :--- | :---: |
| **`R03`** | Retrieval & Context Assembly | **Modular Composer Delegation:** Replace inline `compound_designation_and_historical` prose template with store-driven `_exec_compare_historical_and_active` + `_exec_compound_lookup_and_validation`. | **ACTIVE_CORE** |
| **`R05`** | Retrieval & Context Assembly | **Genus-Scoped Cross-Reference Expansion:** Replace `*flux*` substring coupling with store-driven category-headword detection so single-subtype queries only return their own Clause 4 `See also` edges. | **ACTIVE_CORE** |
| **`S03`** | Semantic Representation | **Dual-Layer Epistemic Firewall:** Verify Slice 5 replay cassettes (`G62-GEN17`, `G62-GEN18`) via `DeepSeekV41PlannerAdapter` in `OFFLINE_REPLAY_ONLY` mode under `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`. | **ACTIVE_CORE** |
| **`U02`** | Consumer Boundary | **Decoupled Evaluation Harness:** Support `--benchmark-dir` and `--use-replay-cassettes` in `eval/run_phase6_2_generalization_holdout.py`. | **ACTIVE_CORE** |
| **`U03`** | Consumer Boundary | **100% Verifiable Receipts & Ledger Accuracy:** Reconcile exact SHA-256 hashes (`#36`, `#37`), replay cassette counts (`14`), and post-merge `main` commit provenance in `GATE_6_FULL_AUDIT_BUNDLE.md`. | **ACTIVE_CORE** |
| **`D01`** | Engineering Workflow | **Phased Verification Gates:** Add `tests/test_gate_6_2_2_closeout_hygiene.py` asserting mirror collection parity across all 41 non-PDF locked artifacts, doc-hash accuracy, and single-subtype cross-reference isolation. | **ACTIVE_CORE** |
| **`D02`** | Engineering Workflow | **Git Audit Trail & Full Mirror Sync:** Clean `--no-ff` merge to `main`, post-merge bundle refresh on `main`, annotated tag `v1.6.2.2-closeout-hygiene`, push to `origin`, and verified 41-artifact Google Drive sync (all locked files except copyrighted `data/AWS_A3.0_2020.pdf` if excluded by policy, or verified against `sync_drive_mirror.py` allowlist). | **ACTIVE_CORE** |
| **`D03`** | Engineering Workflow | **Deterministic Offline Test Protocol:** `socket.socket` blocked across all Gate 6.2.2 tests and replay evaluations (`0` network calls). | **ACTIVE_CORE** |

---

## 3. Mandatory 4-Point Drift Assessment Table

| Drift Dimension | Invariant Rule | Gate 6.2.2 Compliance & Verification | Violation Disposition |
| :--- | :--- | :--- | :---: |
| **1. Infrastructure Drift** | **Zero External Database Daemons** | 100% local Python, JSON stores, and filesystem mirror copy. Zero daemons, Docker containers, or network calls (`socket.socket` blocked). | **PASS / NO DRIFT** |
| **2. Epistemic Drift** | **Strict Non-Equivalence Firewall** | All 14 replay cassettes remain tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`; inline template removed from `compound_designation_and_historical` in favor of live store lookups. | **PASS / NO DRIFT** |
| **3. Retrieval / Modality Drift** | **Fair Multimodal Representation & 100% Citation** | Preserves 100% printed-page, PDF-index, and conditional 300-DPI crop provenance across `holdout_001` (`20/20`) and `holdout_002` (`20/20`) under both deterministic and replay planners. | **PASS / NO DRIFT** |
| **4. Scope / Capacity Drift** | **Single Bounded Challenger Arm** | Strictly bounded to remediating the 6 forensic closeout defects from Gate 6.2.1 with zero schema changes and zero mutation to existing locked artifacts. | **PASS / NO DRIFT** |

---

## 4. Proposed Technical Changes

### Deliverable 1: Google Drive Mirror Complete Artifact Coverage (`MIRROR-DRIFT`)
- **`[MODIFY]`** [sync_drive_mirror.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/sync_drive_mirror.py)
  1. In `collect_reviewable_files`: Replace `ev_dir.glob("*_001")` with `re.match(r".*_[0-9]{3}$", ingest_dir.name)` across `ev_dir.iterdir()` so `phase6_2_generalization_holdout_002` (and any future `*_002`/`*_003` benchmark revisions) are collected automatically.
  2. Collect `storage/manifests/*.json` (`coverage_manifest.json`, `latency_benchmark.json`), `scripts/*.py` (`build_gate_6_bundle.py`, `build_gate_5_bundle.py`), and `ner_routing_questions.json` inside `storage/evidence_v2/*_[0-9]{3}/` (note line 160 currently lists `questions.json` and `nlq_questions.json` but omitted `ner_routing_questions.json`!).

### Deliverable 2: In-Repository & Downloads Documentation Synchronization (`REPO-DOC-DRIFT` & `DOC-HASH-DRIFT`)
- **`[MODIFY]`** [goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md), [docs/goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/goal.md), and [ROADMAP.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md)
  - Synchronize in-repository `goal.md`, `docs/goal.md`, and `ROADMAP.md` with the updated `C:\Users\kenai\Downloads\{goal.md, AWS A3.0M_A3.0_2020 End Goal & Production Architecture.md, AWS A3.0M_A3.0_2020 Multimodal RAG Master Roadmap.md}` at release tag `v1.6.2.2-closeout-hygiene`, `42` locked artifacts, `14` replay cassettes, and exact pytest counts.
- **`[MODIFY]`** [GATE_6_2_CHECKOUT_CARD.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_2_CHECKOUT_CARD.md) & [GATE_6_2_1_CHECKOUT_CARD.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_2_1_CHECKOUT_CARD.md) (plus Downloads roadmap & artifact [gate_6_2_1_checkout_card.md](file:///C:/Users/kenai/.gemini/antigravity-cli/brain/f69978ec-bac4-412d-90db-19c18803aa24/gate_6_2_1_checkout_card.md))
  1. Fix SHA-256 digests for `#36` (`storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json` $\rightarrow$ `bb18c854ee6c590dfa83955939b0c9fd810a4cd633ee6d0f64eaf9f0168fe6c3`) and `#37` (`storage/evidence_v2/phase6_2_generalization_holdout_001/results.json` $\rightarrow$ `dfe96330a00328fdb79d594353be826c6d3ccaa10063b62b0a83e0f560886f60`).
  2. Fix line 28 of `GATE_6_2_CHECKOUT_CARD.md` to state alphabetical Clause 4 pagination (`1F`–`4F` and `1G`–`3G` on printed p. 5; `4G`–`6GR` on printed p. 6).
- **`[NEW]`** `GATE_6_2_2_CLOSEOUT_HYGIENE_CARD.md` & `GATE_6_2_2_CHECKOUT_CARD.md` in repository root.

### Deliverable 3: Audit Bundle Builder Fix & Post-Merge Generation (`BUNDLE-DRIFT`)
- **`[MODIFY]`** [build_gate_6_bundle.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/scripts/build_gate_6_bundle.py)
  1. Verify all `14` content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/*.json` and emit both `DeepSeek Preflight Smoke Queries Replayed: 4` (`deepseek_res['replayed_queries_count']`) and `DeepSeek Replay Cassettes Verified on Disk: 14`.
  2. Add `GATE_6_1_CHECKOUT_CARD.md`, `GATE_6_2_CHECKOUT_CARD.md`, `GATE_6_2_1_CHECKOUT_CARD.md`, `GATE_6_2_2_CHECKOUT_CARD.md`, and `tests/test_gate_6_2_2_closeout_hygiene.py` to `FILES`.
  3. Rebuild `GATE_6_FULL_AUDIT_BUNDLE.md` **post-merge on `main`** so `Branch: main` and `Commit` points to a permanent reachable merge commit on `main`.

### Deliverable 4: Holdout Evaluator CLI & Slice 5 Replay Option (`EVAL-DRIFT`)
- **`[MODIFY]`** [run_phase6_2_generalization_holdout.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_2_generalization_holdout.py)
  1. Add `--benchmark-dir` as a primary CLI flag alongside `--output-dir` (backward-compatible).
  2. Add `use_replay_for_slice5: bool = False` (`--use-replay-cassettes` CLI flag) that routes replay-backed Slice 5 multi-operation queries (`G62-GEN17`, `G62-GEN18`) through `DeepSeekV41PlannerAdapter(DeepSeekV41Config(mode="OFFLINE_REPLAY_ONLY"))` when corresponding replay cassettes exist, verifying `20/20` (`100.0%`) pass under both deterministic and hybrid-replay modes without mutating locked `results.json` (`--no-write` verified in CI).

### Deliverable 5: Clean Genus-Scoped Cross-Reference Expansion & Composer Delegation (`CODE-HYGIENE`)
- **`[MODIFY]`** [evidence_phase4_bakeoff.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py)
  1. In `_exec_expand_cross_references` (L1413–L1441): Remove hardcoded `elif "flux" in seed_target.lower():` and `elif "agglomerated flux" in term_name.lower():`. Replace with general store-driven genus-headword detection: when the query explicitly asks `"what <genus_noun> terms are cross-referenced from <seed_term>"` and `<genus_noun>` is a distinct standalone Clause 4 headword with `cross_references.see_also`, append `<genus_noun>`'s own Clause 4 `See also` neighbors labeled with `<genus_noun>`'s printed page; when a query simply asks for cross-references of a single term (e.g., `"What terms are cross-referenced from bonded flux?"`), return **only** `bonded flux`'s direct `See also` neighbors (`agglomerated flux`, `fused flux`).
  2. In `execute_whole_standard_plan` (`intent == "compound_designation_and_historical"`, L2063–L2084): Replace the inline prose block by delegating directly to `_exec_compound_lookup_and_validation([tok], [], stores=stores)` and store-backed historical lookup from `tables["table_a5"]` / `annex_c_d` / `glossary`, raising `ValueError("INSUFFICIENT_EVIDENCE")` if any store dependency is missing.

### Deliverable 6: Gate 6.2.2 Regression & Closeout Hygiene Test Suite
- **`[NEW]`** `tests/test_gate_6_2_2_closeout_hygiene.py`
  1. `test_gate_6_2_2_sync_drive_mirror_collects_all_locked_review_artifacts`: Asserts `collect_reviewable_files(ROOT)` includes every non-PDF artifact in `ALL_42_LOCKED_HASHES` (`41/41`, including `holdout_002`, `ner_routing_questions.json`, `storage/manifests/*`, and all `14` replay cassettes) plus `scripts/build_gate_6_bundle.py`.
  2. `test_gate_6_2_2_single_subtype_cross_reference_isolation_and_both_holdouts`: Asserts `"In Clause 4, what related terms are cross-referenced from bonded flux?"` returns `agglomerated flux` and `fused flux` **without** leaking `brazing flux` or `soldering flux`, while both `holdout_001` (`20/20`) and `holdout_002` (`20/20`) pass `100.0%` under both `use_replay_for_slice5=False` and `use_replay_for_slice5=True`.
  3. `test_gate_6_2_2_compound_and_historical_store_driven_mutation`: Asserts `compound_designation_and_historical` raises `ValueError("INSUFFICIENT_EVIDENCE")` when `Table A1` or `Table A4` is emptied.
  4. `test_gate_6_2_2_docs_and_checkout_cards_hash_and_version_parity`: Programmatically scans `goal.md`, `docs/goal.md`, `ROADMAP.md`, `GATE_6_2_CHECKOUT_CARD.md`, and `GATE_6_2_1_CHECKOUT_CARD.md` to verify zero stale `v1.6.1` headers, zero `(p. 5 for groove, p. 6 for fillet)` strings, and exact SHA-256 parity with `ALL_42_LOCKED_HASHES` for every hash quoted in checkout tables.

---

## 5. Verification Plan

1. **Gate 6.2.2 Closeout Hygiene Tests:**
   ```powershell
   python -B -m pytest tests/test_gate_6_2_2_closeout_hygiene.py -v
   ```
2. **Holdout-001 & Holdout-002 CLI Verification (Deterministic + Slice 5 Replay Mode):**
   ```powershell
   python -B eval/run_phase6_2_generalization_holdout.py --benchmark-dir storage/evidence_v2/phase6_2_generalization_holdout_001 --no-write
   python -B eval/run_phase6_2_generalization_holdout.py --benchmark-dir storage/evidence_v2/phase6_2_generalization_holdout_002 --use-replay-cassettes --no-write
   ```
3. **Whole-Standard & DeepSeek Replay Preflight:**
   ```powershell
   python -B -m src.evidence_whole_standard_preflight
   ```
4. **Full Repository Regression Suite & Anti-Drift Grep:**
   ```powershell
   python -B -m pytest -q
   git grep -n -E "G4-B[0-9]+|G5-[A-Z]+[0-9]+|G52-[A-Z]+[0-9]+|G521-[A-Z]+[0-9]+|G53-[A-Z]+[0-9]+|G54-[A-Z]+[0-9]+|G60-[A-Z]+[0-9]+|G61-[A-Z]*[0-9]+|G62-[A-Z]*[0-9]+|G621-[A-Z]*[0-9]+|G622-[A-Z]*[0-9]+" -- src/ "eval/*.py"
   ```
5. **Google Drive Mirror Parity Verification:**
   ```powershell
   python -B -m src.sync_drive_mirror
   Test-Path "G:\My Drive\git_projects\aws-a30-prototype\storage\evidence_v2\phase6_2_generalization_holdout_002\results.json"
   Test-Path "G:\My Drive\git_projects\aws-a30-prototype\storage\manifests\coverage_manifest.json"
   ```

---

## 6. Git Synchronization Protocol

1. **Branch Creation & Implementation Commit:**
   ```powershell
   git checkout main
   git checkout -b feat/gate-6-2-2-closeout-hygiene
   git add src/ eval/ scripts/ tests/ docs/ goal.md ROADMAP.md GATE_6_2_CHECKOUT_CARD.md GATE_6_2_1_CHECKOUT_CARD.md GATE_6_2_2_CLOSEOUT_HYGIENE_CARD.md GATE_6_2_2_CHECKOUT_CARD.md
   git commit -m "fix(gate-6.2.2): closeout hygiene, Drive mirror 42-artifact coverage, doc parity & genus-scoped cross-refs"
   ```
2. **Merge to `main` & Post-Merge Audit Bundle Generation on `main`:**
   ```powershell
   git checkout main
   git merge --no-ff feat/gate-6-2-2-closeout-hygiene -m "Merge branch 'feat/gate-6-2-2-closeout-hygiene' (Gate 6.2.2 Closeout Hygiene)"
   git branch -d feat/gate-6-2-2-closeout-hygiene
   python -B scripts/build_gate_6_bundle.py
   git add GATE_6_FULL_AUDIT_BUNDLE.md GATE_5_FULL_AUDIT_BUNDLE.md storage/gate_reviews/GATE_6_FULL_AUDIT_BUNDLE.md storage/gate_reviews/GATE_5_FULL_AUDIT_BUNDLE.md
   git commit -m "docs(gate-6.2.2): rebuild post-merge GATE_6_FULL_AUDIT_BUNDLE on main"
   git tag -a v1.6.2.2-closeout-hygiene -m "Release v1.6.2.2: Post-6.2.1 Closeout Hygiene, Google Drive 42-Artifact Mirror Parity, Repo Doc Alignment & Post-Merge Audit Bundle"
   ```
3. **Remote Publication & Google Drive Mirror Sync:**
   ```powershell
   git push origin main --tags
   python -B -m src.sync_drive_mirror
   ```
