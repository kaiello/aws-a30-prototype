# Implementation Milestone Card: Gate 6.2.1 — Multi-Action Plan Composition, Polysemous Diagram+Glossary Activation, 12 End-to-End Store Mutations, Dynamic Tables & Holdout-002 Cryptographic Lock

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `5abf96a` (`v1.6.2-store-driven-composition`)  
**Target Branch:** `feat/gate-6-2-1-multi-action-closure`  
**Target Release Tag:** `v1.6.2.1-multi-action-closure`  
**Audit Bundle:** `GATE_6_FULL_AUDIT_BUNDLE.md`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Goal Description & Background

Gate 6.2 locked 39 cryptographic artifacts, passed `1,489 passed, 8 skipped, 0 failed` in full regression, and established store-driven execution for taxonomy subtypes, weld positions, homographs, and compound codes. However, our line-by-line forensic audit identified five critical implementation gaps that require a focused, disciplined remediation card (**Gate 6.2.1**) prior to advancing to Gate 6.3 / Gate 7:

1. **Dead Code & Omitted Query Parts:** `_exec_polysemous_diagram_and_glossary` was implemented at `src/evidence_phase4_bakeoff.py:1650–1701` but never wired into `execute_whole_standard_plan`. Multi-division queries like `G62-GEN13` (omitted `bevel face`), `G62-GEN14` (omitted all Clause 4 definitions for `backing shoe`, `moving shoe`, and `stationary shoe`), `G62-GEN17` (omitted `Figure B54` intervals), and `G62-GEN18` (omitted `FOW`/`FSW` comparison) dropped query halves due to monolithic `if/elif` branching.
2. **Residual Canned Blocks & Planner Ternaries:** Canned prose blocks remained in `execute_whole_standard_plan` (`Figure B6`, `Figure B25`, `Figure B33`, `Figure B46`, `Figure B12`, `angle_cluster`, `compound_designation`, `invalid_compound_suffix`), and `DeterministicQuestionPlanner._plan_cross_store_comparison` used hardcoded ternaries instead of dynamic entity extraction from NER spans.
3. **Bypassed Store Mutations:** Mutations 8–12 in `tests/test_gate_6_2_store_driven_composition.py` called private `_exec_*` helpers rather than `answer_whole_standard_question(..., stores=mut_X)`; Mutation 10 did not blank `5G`; and Mutation 12 passed empty lists rather than mutating `Table A1`/`Table A4`.
4. **Static Hardcoded Tables:** `WeldingNER` hardcoded `pipe_positions` and `plate_positions` (including non-existent `3G`/`4G` pipe senses), and `SemanticNLQExpander` hardcoded a 7-entry `parent_proc_map` instead of dynamically resolving all 22 parent designations from `Table A1` / `glossary_store.json`.
5. **GitOps & Audit Bundle Hygiene:** Remote `origin` is 2 commits behind local `main` with unpushed tags; `GATE_6_2_CHECKOUT_CARD.md` has minor test-count and pagination typographical errors; and named Downloads roadmap files need synchronization.

Under **Option 1**, all 39 existing Gate 0–6.2 locked artifacts (including `phase6_2_generalization_holdout_001`) remain 100% byte-identical. Gate 6.2.1 introduces a strict `phase6_2_generalization_holdout_002` benchmark with unweakened rubrics, closes all 5 gaps, and locks a clean 44-artifact cryptographic ledger.

---

## 2. Master Integration Register Cross-Reference

Cross-referenced against the 49 integration candidates documented in [`docs/NAVY_WELD_MASTER_INTEGRATION_AND_BAKEOFF_LIST_2026-10-18.md`](file:///C:/Users/kenai/meia_kg_poc/docs/NAVY_WELD_MASTER_INTEGRATION_AND_BAKEOFF_LIST_2026-10-18.md):

| Candidate ID | Master Register Category | Specific Gate 6.2.1 Application | Status |
| :---: | :--- | :--- | :---: |
| **`R03`** | Retrieval & Context Assembly | **Functional Context Packets & Multi-Action Assembly:** Modular execution of `plan["actions"]` composing Clause 4 definitions with Annex B spatial callouts and Annex A process charts into a unified fact packet without text starvation. | **ACTIVE_CORE** |
| **`R05`** | Retrieval & Context Assembly | **Graph Neighborhood Expansion:** Longest-span matching in `DeterministicQuestionPlanner` (`agglomerated flux` over `flux`) and dynamic 22-parent process expansion in `SemanticNLQExpander`. | **ACTIVE_CORE** |
| **`S03`** | Semantic Representation | **Dual-Layer Epistemic Firewall:** Replay cassettes quarantined under `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`; 100% of answer facts must derive strictly from immutable canonical stores. | **ACTIVE_CORE** |
| **`O03`** | Serving Optimization | **Headless CLI & Zero-Daemon Execution:** Sub-millisecond store-driven execution without external database daemons or network socket connections. | **ACTIVE_CORE** |
| **`U02`** | Consumer Boundary | **Decoupled Evaluation Harness:** Strict `phase6_2_generalization_holdout_002` benchmark with unweakened rubrics (`bevel face` required, Clause 4 definitions required, `Figure B54` intervals required). | **ACTIVE_CORE** |
| **`U03`** | Consumer Boundary | **100% Verifiable Receipts & Complete Citations:** Exact printed page and normative locator citations for every asserted fact across all 20 holdout queries. | **ACTIVE_CORE** |
| **`D01`** | Engineering Workflow | **Phased Verification Gates:** Rigorous gating requiring `1,489+` unit and regression tests, `20/20` holdout queries passing, and `12/12` end-to-end store mutation degradations. | **ACTIVE_CORE** |
| **`D02`** | Engineering Workflow | **Git Audit Trail & Remote Sync:** Clean branch `feat/gate-6-2-1-multi-action-closure`, `--no-ff` merge to `main`, annotated tag `v1.6.2.1-multi-action-closure`, and full push to `origin` + Google Drive mirror sync. | **ACTIVE_CORE** |
| **`D03`** | Engineering Workflow | **Deterministic Offline Test Protocol:** `socket.socket` strictly blocked across all tests and preflight scripts. | **ACTIVE_CORE** |

---

## 3. Mandatory 4-Point Drift Assessment Table

| Drift Dimension | Invariant Rule | Gate 6.2.1 Compliance & Verification | Violation Disposition |
| :--- | :--- | :--- | :---: |
| **1. Infrastructure Drift** | **Zero External Database Daemons** | All operations use local Python modules, in-memory store indexes, and local JSON files. Zero Neo4j, Milvus, Qdrant, Docker, or external network services. Verified by `socket.socket` blocking in `test_gate_6_2_1_multi_action_closure.py`. | **PASS / NO DRIFT** |
| **2. Epistemic Drift** | **Strict Non-Equivalence Firewall** | Model replay plans tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`. All answers derived directly from canonical stores (`glossary_store.json`, `table_a1`, `table_a4`, `figure_b*_store.json`). Zero canned prose; zero hallucinations. | **PASS / NO DRIFT** |
| **3. Retrieval / Modality Drift** | **Fair Multimodal Representation & 100% Citation** | Polysemous and multi-action queries compose text definitions from Clause 4 and visual/spatial diagram callouts from Annex B without dropping either modality. 100% citation completeness verified against `rubric.json`. | **PASS / NO DRIFT** |
| **4. Scope / Capacity Drift** | **Single Bounded Challenger Arm** | Scope bounded strictly to remediating Gate 6.2 forensic gaps, activating `_exec_polysemous_diagram_and_glossary`, modular multi-action execution, and locking `holdout_002`. No speculative architecture changes or new models. | **PASS / NO DRIFT** |

---

## 4. Proposed Technical Changes

### Deliverable 1: Modular Multi-Action Dispatcher & Wire `_exec_polysemous_diagram_and_glossary` (`EXEC-DRIFT-6.2.1-1` & `PLAN-DRIFT-6.2.1-2`)
- **File:** `src/evidence_phase4_bakeoff.py`
  1. **Activate `_exec_polysemous_diagram_and_glossary`:**
     - In `execute_whole_standard_plan`: When the plan intent is `polysemous_callout_and_glossary`, or when `inferred_targets["figures"]` and `inferred_targets["clause4_terms"]` co-occur with definitional intent, invoke `_exec_polysemous_diagram_and_glossary(query, figure_id, terms, stores)`.
     - In `_exec_polysemous_diagram_and_glossary`: Dynamically retrieve the Clause 4 definitions for all requested terms and the diagram callouts/details for the specified figure from `stores`. Raise `INSUFFICIENT_EVIDENCE` if any requested term or figure is missing or blank in `stores`.
  2. **Modular Multi-Action Composition in `execute_whole_standard_plan`:**
     - When `plan.get("actions")` contains multiple operations (or when a query asks for a compound code + diagram, or historical comparison + classification chart):
       - Execute each planned action independently against `stores` using its dedicated store-driven executor (`_exec_compound_lookup_and_validation`, `_exec_compare_historical_and_active`, `_compose_waveform_phase4_answer`, `_compose_annex_a_chart_answer`, etc.).
       - Compose the resulting answers into a unified, coherent response without dropping any action.
  3. **Eliminate All Remaining Canned Prose Blocks:**
     - Replace static blocks for `Figure B6` (L1941), `Figure B25` (L1956), `Figure B33` (L1972), `Figure B46` (L1987), `Figure B12` (L2003), `angle_cluster` (L2055), `compound_designation` (L1821), and `invalid_compound_suffix` (L1793) with modular store-driven calls.
  4. **Dynamic Entity Extraction in `DeterministicQuestionPlanner._plan_cross_store_comparison`:**
     - Replace hardcoded ternaries (`hist_term = ...`, `act_term = ...`) by extracting compared terms directly from `receipt.spans` (matching `NONSTANDARD_OR_HISTORICAL`, `PROCESS_TERM`, and `BASE_PROCESS`).

### Deliverable 2: End-to-End Store-Mutation Tests (Mutations 8–12) & Live Store Compound Validation (`TEST-DRIFT-6.2.1-3`)
- **Files:** `tests/test_gate_6_2_store_driven_composition.py` (and new `tests/test_gate_6_2_1_multi_action_closure.py`):
  1. Route all 12 mutations through the public entrypoint `answer_whole_standard_question(query, planner, stores=mutated_stores)`.
  2. **Mutation 10:** Blank the `'5G'` definition in `mut_10["glossary"]["entries"]` and query `5G` position (`"How is the 5G welding position defined in Clause 4 and what diagram illustrates it?"`), asserting it raises `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
  3. **Mutation 12:** Blank/remove `GMAW` base process or `GMAW-P` variation from `mut_12["tables"]["table_a1"]` and `-SA` from `mut_12["tables"]["table_a4"]["suffixes"]`, querying `"What does GMAW-P-SA stand for in AWS A3.0?"`.
  4. In `_exec_compound_lookup_and_validation`: Validate the base process against `stores["tables"]["table_a1"]` and application mode suffix against `stores["tables"]["table_a4"]["suffixes"]` directly, ensuring store mutations trigger `INSUFFICIENT_EVIDENCE` immediately without singleton caching masking the change.

### Deliverable 3: Derive Static Tables Dynamically (`NER-DRIFT-6.2.1-4` & `SEM-DRIFT-6.2.1-5`)
- **File:** `src/welding_ner.py`
  - In `_resolve_contextual_senses`: Derive valid position senses (`pipe` vs `plate`) and printed pages dynamically from `glossary_store.json` (eliminating nonexistent `3G`/`4G` pipe senses, and correctly reflecting printed p. 5 and p. 6).
- **File:** `src/semantic_nlq_expander.py`
  - In `_build_concept_graph`: Derive the full 22-entry `parent_proc_map` dynamically by inspecting `is_a_promotion_store.json` and `Table A1`.

### Deliverable 4: Strict `phase6_2_generalization_holdout_002` Benchmark (`BENCH-6.2.1-6`)
- **Directory:** `storage/evidence_v2/phase6_2_generalization_holdout_002/`
  1. Copy 20 questions (`G62-GEN01` through `G62-GEN20`) to `questions.json`.
  2. Restore unweakened rubrics in `rubric.json`:
     - **`G62-GEN13`:** Require `bevel face`, `groove face`, `root face`, and `Figure B6` (remove artificial `groove angle` workaround).
     - **`G62-GEN14`:** Require Clause 4 definitions for `backing shoe`, `moving shoe`, `stationary shoe` and `Figure B37` (remove artificial callout-only workaround).
     - **`G62-GEN17`:** Require `GMAW-P-SA` compound breakdown AND `Figure B54` arc welding cycle intervals.
     - **`G62-GEN18`:** Require `forge welding (FOW)`, `friction stir welding (FSW)`, AND `Figure A5` solid-state welding classification.
     - **`G62-GEN07`:** Require `bonded flux` and `fused flux` (cross-referenced from `agglomerated flux`).
  3. Update `eval/run_phase6_2_generalization_holdout.py` to support `ReplayQuestionPlanner` for replay queries (`G62-GEN17`, `G62-GEN18`, `G62-GEN19`, `G62-GEN20`).
  4. Generate and lock `results.json` for `phase6_2_generalization_holdout_002`. Total locked artifacts: **44**.

### Deliverable 5: GitOps, Documentation, Audit Bundle & Mirror Synchronization (`GITOPS-6.2.1-7`)
- **Files:** `GATE_6_2_CHECKOUT_CARD.md`, `GATE_6_FULL_AUDIT_BUNDLE.md`, `C:\Users\kenai\Downloads\*`
  1. Reconcile `GATE_6_2_CHECKOUT_CARD.md` with exact test counts (`1,489 passed, 8 skipped`) and alphabetical pagination description (`1F`–`4F`, `1G`–`3G` on p. 5; `4G`–`6GR` on p. 6).
  2. Rebuild `GATE_6_FULL_AUDIT_BUNDLE.md` post-merge.
  3. Synchronize named roadmap and goal files in `Downloads/`:
     - `C:\Users\kenai\Downloads\AWS A3.0M_A3.0_2020 End Goal & Production Architecture.md`
     - `C:\Users\kenai\Downloads\AWS A3.0M_A3.0_2020 Multimodal RAG Master Roadmap.md`
     - `C:\Users\kenai\Downloads\goal.md`
  4. Git Publication: Push `main` and all release tags (`v1.6.0-ner-routing-skills`, `v1.6.1-ner-semantic-graph`, `v1.6.2-store-driven-composition`, `v1.6.2.1-multi-action-closure`) to `origin` (`https://github.com/kaiello/aws-a30-prototype.git`).
  5. Run `python -B -m src.sync_drive_mirror` to ensure 100% sync to Google Drive mirror.

---

## 5. Verification Plan

### Test Commands & Exit Gates
1. **Gate 6.2.1 Unit & Contract Tests:**
   ```powershell
   python -B -m pytest tests/test_gate_6_2_1_multi_action_closure.py -v
   ```
   *Expected:* 10/10 PASS, including multi-action composition, polysemous diagram+glossary, all 12 end-to-end store mutations, and dynamic table derivations.

2. **Holdout-002 Benchmark Evaluation:**
   ```powershell
   python -B eval/run_phase6_2_generalization_holdout.py --benchmark-dir storage/evidence_v2/phase6_2_generalization_holdout_002
   ```
   *Expected:* 20/20 PASS (100.0%) against unweakened rubrics.

3. **Whole-Standard Preflight Contract:**
   ```powershell
   python -B -m src.evidence_whole_standard_preflight
   ```
   *Expected:* `CLEAR_WHOLE_STANDARD_CONTRACT` & `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`.

4. **Full Repository Regression Suite:**
   ```powershell
   python -B -m pytest -q
   ```
   *Expected:* `1,495+ passed, 8 skipped, 0 failed, 0 warnings` in `< 350s`.

5. **Static Anti-Drift Scans:**
   ```powershell
   git grep -E "QA[0-9]+|...|G62-GEN[0-9]+|G62-[0-9]+" -- src/ eval/*.py
   ```
   *Expected:* 0 matches (Exit code 1).

---

## 6. Git Synchronization Protocol

1. **Branch Creation:**
   ```powershell
   git checkout main
   git checkout -b feat/gate-6-2-1-multi-action-closure
   ```
2. **Commit Changes:**
   ```powershell
   git add src/ tests/ eval/ storage/evidence_v2/phase6_2_generalization_holdout_002/ docs/ scripts/ GATE_6_2_CHECKOUT_CARD.md GATE_6_2_1_MULTI_ACTION_CLOSURE_CARD.md
   git commit -m "feat(gate-6.2.1): multi-action plan composition, polysemous diagram+glossary activation & holdout-002 lock"
   ```
3. **Merge & Tag on `main`:**
   ```powershell
   git checkout main
   git merge --no-ff feat/gate-6-2-1-multi-action-closure -m "merge(gate-6.2.1): multi-action plan composition & holdout-002 lock"
   git tag -a v1.6.2.1-multi-action-closure -m "Release v1.6.2.1: Multi-Action Plan Composition, Polysemous Diagram+Glossary Activation, 12 End-to-End Store Mutations & Holdout-002 Lock"
   git branch -d feat/gate-6-2-1-multi-action-closure
   ```
4. **Remote Publication & Google Drive Sync:**
   ```powershell
   git push origin main --tags
   python -B -m src.sync_drive_mirror
   ```
