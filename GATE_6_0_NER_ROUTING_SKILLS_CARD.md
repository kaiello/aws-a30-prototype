# Principal Reviewer Directive: Gate 6.0 — GitOps Branch Reconciliation, Deterministic Welding NER, Callout/Backlink Multi-Intent Router & Whole-Standard Agent Skills (`feat/gate-6-0-ner-routing-skills`)

**Standard:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 190 PDF pages / 162 ingested canonical store pages)  
**Base Commit on `main`:** `dd22331` (Gate 5.6 Epistemic & Manifest Calibration; `1,468 passed, 8 skipped, 0 failures, 0 warnings`; `24/24` SHA-256 artifacts locked)  
**Architecture Specification:** `docs/gate_6_0_ner_routing_and_skills_architecture.md`  
**Target Branch:** `feat/gate-6-0-ner-routing-skills` $\rightarrow$ `main` (tagged `v1.6.0-ner-routing-skills`, with post-merge feature branch cleanup)  
**Status:** `AUTHORIZED_FOR_GITOPS_RECONCILIATION_AND_EXECUTION`

---

## 1. Objective & Non-Negotiable Architectural Guardrails

Gate 6.0 elevates natural-language query understanding across `AWS A3.0M/A3.0:2020` from regex/title heuristics to **character-offset Deterministic Welding Domain NER (`src/welding_ner.py`)**, **1,115-node Callout & 265-edge Backlink Multi-Intent Routing**, and **Whole-Standard CLI & `.agents/skills/` Tooling**, preceded by **Step-0 GitOps Branch Hygiene** reconciling all 10 remote branches on `origin` and 17 local branches.

All Gate 0–5.6 production invariants remain strictly enforced:
1. **Strict Offline Test & Preflight Isolation (`socket.socket` blocked):** All `pytest` suites, `src/evidence_whole_standard_preflight.py`, `src/welding_ner.py`, and `src/evidence_whole_standard_cli.py` MUST execute with `0` network calls and zero heavyweight external NLP/ML downloads (100% compiled in-memory from the locked `_001` JSON stores).
2. **Version-Bound Canonical Store & Replay Immutability (`24/24` Existing Hashes Untouched):**
   - All **24 previously locked SHA-256 digests** (1 PDF + 6 Phase 0–3 `_001` stores + 1 Annex A holdout rubric + 3 Phase 5 adversarial files + 3 Phase 5.5 NLQ files + 8 Gate 5.4/5.5 DeepSeek replay cassettes + 2 Gate 5.6 manifests) MUST remain byte-identical (`.gitattributes` `storage/** -text` preserved).
   - **CRITICAL GATE 5.4 / 5.5 REPLAY COMPATIBILITY:** Do NOT alter `replay_key` computation for existing cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/`. Attach `ner_receipt` and `multi_intent_route` as additive metadata fields, and add new Gate 6.0 replay cassettes as net-new files.
3. **Epistemic Quarantine & Deterministic Layer 6 Composition:** Model reasoning traces (`part.reason`) from `DeepSeek-V4.1-Flash-1017` remain quarantined as `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`. Final answers and explicit abstentions (`INSUFFICIENT_EVIDENCE`, `NOT_IN_STANDARD`, `REFUSAL_OUT_OF_SCOPE`, `REFUSAL_OUT_OF_RANGE`, `CONTRADICTION_REFUTED`) are composed strictly from verified store records.
4. **Gate 5.6 Modality-Appropriate Provenance:** Every non-refusal answer includes `printed_page`, `pdf_index`, and `evidence_locator`. `requires_diagram_crop: True` (with verified `crop_path`) is emitted **if and only if** at least one resolved claim depends on `Figures A1–A6` or `Figures B1–B54`.

---

## 2. Gate 6.0 Implementation Deliverables (`G60-0` through `G60-5`)

### Deliverable `G60-0`: GitOps Branch Reconciliation, Release Tagging & Branch Pruning (`10` `origin` Branches $\rightarrow$ `1` Clean `main`)

Forensic verification (`git fetch --prune origin` and `git branch -r --no-merged main`) confirms that **0 remote branches have unmerged work**—all 9 non-`main` branches on GitHub (`origin`), including the 5 active Gate 3D / 5 / 5.4 / 5.5 / 5.6 branches and 4 older Phase 0 / Gate 3 branches, are **100% ancestors of `main` (`dd22331`)** and must be **deleted after stamping an immutable Gate 5.6 release tag** (do **not** re-merge already-merged branches):

| # | Remote Branch on `origin` | Tip SHA | Status vs. `main` (`dd22331`) | Required GitOps Action |
| :- | :--- | :--- | :--- | :--- |
| 1 | `origin/main` | `dd22331` | Canonical HEAD | **KEEP** & stamp annotated tag `v1.5.6-gate-5-6-calibrated` |
| 2 | `origin/feat/gate-5-6-epistemic-manifest-calibration` | `533f03b` | Merged (`dd22331`) — Active | **DELETE** on `origin` & local |
| 3 | `origin/feat/gate-5-5-semantic-nlq` | `0da90dc` | Merged (`e31b8e2`) — Active | **DELETE** on `origin` & local |
| 4 | `origin/feat/gate-5-production-hardening` | `0da90dc` | Merged (`e31b8e2`) — Active | **DELETE** on `origin` & local |
| 5 | `origin/feat/gate-5-4-deepseek-planner-replay` | `933cb60` | Merged (`e31b8e2`) — Active | **DELETE** on `origin` & local |
| 6 | `origin/feat/gate-3d-phase3-live-holdout` | `e0fd74d` | Merged (`263bfdb`) — Active | **DELETE** on `origin` |
| 7 | `origin/feat/gate-3b-annex-b-archetype3-b1-b6` | `d8fb23d` | Merged — Stale | **DELETE** on `origin` |
| 8 | `origin/feat/gate-3a-clause4-glossary-is-a` | `728ceed` | Merged — Stale | **DELETE** on `origin` |
| 9 | `origin/fix/a1-query-completeness` | `00457fe` | Merged — Stale | **DELETE** on `origin` & local |
| 10 | `origin/plan/helper-hardening-20261015` | `cd7cce5` | Merged — Stale | **DELETE** on `origin` & local |

**Local Branch & Worktree Rules (17 Local Branches):**
1. **Anchor Release Tag First:** Create annotated tag `v1.5.6-gate-5-6-calibrated` at `dd22331` and push to `origin` before deleting any branch.
2. **Delete 9 Merged Remote Branches on `origin`:** Reduce `origin` from 10 branches to 1 canonical branch (`origin/main`).
3. **Delete 10 Merged Non-Worktree Local Branches via Safe `git branch -d` (Never `-D`):**
   - `docs/a1-bakeoff-findings` (`3a79b94`), `feat/a1-a2-relationship-readiness` (`bc51eae`), `feat/a2-source-aware-ingest` (`6d02ee2`), `feat/gate-5-4-deepseek-planner-replay` (`933cb60`), `feat/gate-5-5-semantic-nlq` (`0da90dc`), `feat/gate-5-6-epistemic-manifest-calibration` (`533f03b`), `feat/gate-5-production-hardening` (`0da90dc`), `fix/a1-query-completeness` (`00457fe`), `plan/declarative-manifest-20261015` (`987e583`), `plan/helper-hardening-20261015` (`cd7cce5`).
4. **Preserve Sibling Worktrees Untouched:**
   - Do **NOT** delete or modify the 5 merged sibling worktree branches (`feat/a1-validated-llm-planner`, `feat/a1-faithful-relationships-multihop`, `feat/a1-nlq-planning-completeness`, `feat/a1-source-aware-ingest`, `fix/a1-lightrag-extraction`) checked out in external sibling folders.
   - **STRICT ARCHIVE PRESERVATION:** `bakeoff/a1-multimodal-hybrid` (`b9f7763`, `"chore: preserve bounded Figure A1 bakeoff record"`, checked out in `.../aws-a1-bakeoff`) is an intentionally preserved historical experiment — **DO NOT merge into `main`** and **DO NOT force-delete**.
5. **Post-Gate-6.0 Branch Hygiene:** At Gate 6.0 closeout, after merging `feat/gate-6-0-ner-routing-skills` `--no-ff` into `main` and pushing tag `v1.6.0-ner-routing-skills`, delete `feat/gate-6-0-ner-routing-skills` locally and on `origin` so `origin` remains at **1 clean branch (`main`)**.

---

### Deliverable `G60-1`: Deterministic Welding Domain NER & Compound Designation Parser (`src/welding_ner.py`)

Create `src/welding_ner.py`, a 100% offline, deterministic, character-offset Named Entity Recognizer compiled directly from `get_whole_standard_stores()` (self-hydrating automatically if `stores=None`):

1. **Typed Span & Receipt Schema (`WeldingEntitySpan` & `WeldingNERReceipt`):**
   ```python
   @dataclass(frozen=True)
   class WeldingEntitySpan:
       surface_text: str
       start_char: int
       end_char: int
       entity_type: str  # One of 11 canonical entity types below
       canonical_term: str
       canonical_id: str  # e.g., "table_a1:PAW", "table_a4:-AU", "figure_b25:callout:theoretical_throat", "clause4:term:kerf"
       source_authority: str
       target_division: str  # "clause4_glossary" | "annex_a_tables" | "annex_a_charts" | "annex_b_spatial" | "annex_b_waveform" | "annex_c_d"
       sub_components: Tuple[Dict[str, Any], ...] = ()
       ambiguity_candidates: Tuple[Dict[str, Any], ...] = ()
   ```
2. **11 Required Entity Types:**
   - `STANDARD_LOCATOR` (explicit `Clause 4`, `Table A1`–`A5`, `Figure A1`–`A6`, `Figure B1`–`B54`, `Annex C`, `Annex D`, plus out-of-range detection such as `Figure A7`, `Figure B55`, `Table A6`)
   - `COMPOUND_DESIGNATION` (dynamically parsed `<PROCESS_CODE>-<MODE_SUFFIX>` or `<PROCESS_CODE>-<VARIANT>-<MODE_SUFFIX>` per `Table A4`'s `XXXX-YY` rule, e.g., `PAW-AU`, `GTAW-MA`, `GTAW-ME`, `FCAW-G-SA`, `OFC-A-MA`, `GTAW-P-AU`; also flags invalid mode suffixes on valid base codes such as `GTAW-ZZ` with `entity_type="INVALID_COMPOUND_DESIGNATION"`)
   - `PROCESS_CODE` (`Table A1` active + `Table A5` obsolete + `IS_A` variant designations: `SMAW`, `GTAW`, `GMAW-S`, `FCAW-G`, `PAW`, `FSW`, `CW`, `CAC-A`, `AHW`, `FOW`, ...)
   - `MODE_SUFFIX` (all 6 `Table A4` suffixes: `-AD`, `-AU`, `-MA`, `-ME`, `-RO`, `-SA` when queried standalone)
   - `PROCESS_TERM` (canonical welding/joining/cutting/brazing/soldering/spraying process names across `Clause 4`, `Tables A1–A3`, `Figures A1–A6`)
   - `NONSTANDARD_OR_HISTORICAL` (`Annex C`, `Annex D Tables D1–D6`, and `Clause 4` lightface nonstandard synonyms, e.g., *atomic hydrogen welding*, *heliarc*, *stick electrode*, *gas pocket*, *button weld*)
   - `WELD_POSITION` (`1G`–`6GR`, `1F`–`6F`, *flat welding position*, *horizontal fixed welding position*, *overhead welding position*, ...)
   - `DOMAIN_QUALIFIER` (bracketed or contextual domain qualifiers: `[pipe]`, `[plate]`, `[resistance welding]`, `[brazing]`, `[soldering]`, `[thermal spraying]`, or natural-language `"in pipe"` / `"in plate"` modifiers adjacent to `WELD_POSITION` or polysemous terms)
   - `DIAGRAM_CALLOUT` (accepted spatial callout labels and numbered legend terms across `Figures B1–B52`, e.g., *theoretical throat*, *effective throat*, *actual throat*, *underbead crack*, *toe crack*, *crater crack*, *thermomechanically affected zone*, *advancing side*, *retreating side*, *runoff tab*, *split pipe backing*)
   - `WAVEFORM_INTERVAL` (Archetype 4 waveform traces/intervals across `Figures B44–B45, B49–B51, B53–B54`, e.g., *upslope*, *downslope*, *squeeze time*, *weld interval*, *quench time*, *temper time*, *crater fill time*, *meltback time*)
   - `GLOSSARY_TERM` (boldface `Clause 4` headwords + morphological inflections not covered by a more specific operational class above)
3. **Non-Overlapping Longest-Match Resolution & Homograph Disambiguation:**
   - Implement a word-boundary-aware longest-match trie / token scanner so multi-word spans (*"gas tungsten arc welding"*, *"theoretical throat"*, *"atomic hydrogen welding"*) cleanly subsume shorter sub-tokens (*"arc"*, *"throat"*, *"welding"*) without arbitrary 5-item caps.
   - Populate `ambiguity_candidates` for homographs and multi-entry collisions:
     - `AB` $\rightarrow$ `Table A1` (*arc brazing*, p. 69/78) **and** `Figure A6` / `Clause 4` (*adhesive bonding*), disambiguating when context mentions `"brazing"` vs. `"adhesive"` / `"bonding"` or returning both senses when unqualified.
     - `1G`, `2G`, `5G`, `6G`, `6GR`, `1F`–`4F` $\rightarrow$ link plate groove (`Figure B16A`), plate fillet (`Figure B16B`), and pipe groove (`Figure B16C`) candidates according to `[plate]` vs. `[pipe]` / `"fillet"` vs. `"groove"` qualifiers.
     - Multi-POS `Clause 4` headwords (e.g., `braze` noun & verb) $\rightarrow$ surface all matching `Clause 4` entries.

---

### Deliverable `G60-2`: Callout- & Backlink-Indexed Multi-Intent Router (`src/semantic_nlq_expander.py`, `src/evidence_phase4_bakeoff.py`, `src/deepseek_v41_adapter.py`)

1. **Fix Standalone Store Hydration & Dead Code in `src/semantic_nlq_expander.py`:**
   - If `SemanticExpander.ensure_initialized()` or `get_semantic_expander()` is called with empty `stores`, automatically load canonical stores via `get_whole_standard_stores()` so standalone callers never initialize an empty lexicon.
   - Remove the unreachable duplicate block at lines `856–881` of `src/semantic_nlq_expander.py`.
2. **Full Annex B Spatial Callout (`1,115` Nodes), Annex A Circle (`96` Nodes) & Clause 4 Backlink (`265` Edges) Inverted Index:**
   - Index all accepted spatial callout labels and numbered legend descriptions from `annex_b_complete_unified_store.json`, all 96 process circles in `Figures A1–A6`, and all 265 Clause 4 `"see Figure B..."` back-links.
   - Score ID-free diagram candidates using deterministic **IDF-weighted span specificity** ($w(\text{span}) = \ln(1 + N_{\text{figs}} / \text{df}(\text{span})) \times \text{word\_count}(\text{span})$) so queries mentioning *"theoretical throat, effective throat, and actual throat"* route deterministically to `Figure B25`, *"toe crack, underbead crack, and crater crack"* route to `Figure B33`, *"advancing side, retreating side, and thermomechanically affected zone"* route to `Figure B46`, and *"runoff tab, starting weld tab, and split pipe backing"* route to `Figure B12`.
3. **Multi-Intent Action Plan Generation in `DeterministicQuestionPlanner` (`src/evidence_phase4_bakeoff.py`):**
   - Integrate `WeldingNER` into `SemanticExpander.expand()` and `DeterministicQuestionPlanner.plan_whole_standard_question()`.
   - When a query contains spans targeting **multiple divisions or compound designations** (e.g., `PAW-AU` $\rightarrow$ `Table A1` + `Table A4` + `Clause 4`; or `Annex D` historical process + active `Table A1` designation + `Figure A4`/`B53` diagram), emit an ordered multi-operation plan and compose a unified multi-store answer citing every contributing store's `printed_page`, `pdf_index`, and `evidence_locator`.
   - Enforce Gate 5.6 provenance strictly: `requires_diagram_crop = True` (with verified `crop_path`) iff at least one operation resolves against `Figures A1–A6` or `Figures B1–B54`; `requires_diagram_crop = False` for pure `Table A1 + Table A4` compound code or `Clause 4 + Annex D` text/table multi-hop answers.
   - Preserve 100% pass rates across all existing Gate 3D, Gate 4/4B, Annex A Holdout (`30/30`), Gate 5 Hardening (`10/10`), Gate 5.5 NLQ (`15/15`), and Gate 5.6 tests.
4. **Additive `DeepSeekV41PlannerAdapter` Integration (`src/deepseek_v41_adapter.py`):**
   - Expose `ner_entities` and `multi_intent_targets` in `plan_with_semantic_expansion()` without altering `replay_key` calculation for the 8 existing Gate 5.4/5.5 replay cassettes.
   - Add **2 new offline replay cassettes** in `storage/model_replays/deepseek_v4_1_flash_1017/` covering:
     1. A dynamic compound designation + chart multi-hop query (e.g., `PAW-AU` across `Table A1` + `Table A4` + `Figure A4`),
     2. An ID-free spatial diagram callout + Clause 4 multi-hop query (e.g., `Figure B25` weld throat callouts + `Clause 4` definitions),
     with `part.reason` quarantined as `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.

---

### Deliverable `G60-3`: Canonical Whole-Standard CLI & Agent Retrieval Skills (`src/evidence_whole_standard_cli.py` + `.agents/skills/`)

1. **Create `src/evidence_whole_standard_cli.py`:**
   - Deterministic, offline-safe CLI entry point supporting:
     - `python -B -m src.evidence_whole_standard_cli --ner "<query>" [--json]` $\rightarrow$ prints `WeldingNERReceipt` (entity spans, char offsets, compound splits, ambiguity candidates).
     - `python -B -m src.evidence_whole_standard_cli --route "<query>" [--json]` $\rightarrow$ prints NER receipt + `SemanticExpansionTrace` + ranked figure/table/division targets + planned store operations.
     - `python -B -m src.evidence_whole_standard_cli --ask "<query>" [--planner deterministic|deepseek-replay] [--json]` $\rightarrow$ executes full retrieval + deterministic Layer 6 answer composition + Gate 5.6 modality-appropriate provenance receipt.
2. **Modernize `.agents/skills/` to Gate 6.0 Whole-Standard Architecture:**
   - Update `.agents/skills/evidence-graph-routing/SKILL.md`: Replace the obsolete *"only implemented source adapter is Figure A1"* restriction with whole-standard `AWS A3.0M/A3.0:2020` routing across all 6 canonical `_001` stores via `src.evidence_whole_standard_cli --route` (retaining `src.evidence_chart_cli` as legacy Figure A1 chart-only diagnostics).
   - Update `.agents/skills/evidence-graph-qa/SKILL.md`: Document whole-standard QA (`src.evidence_whole_standard_cli --ask`), explicit abstention statuses (`NOT_IN_STANDARD`, `REFUSAL_OUT_OF_SCOPE`, `REFUSAL_OUT_OF_RANGE`, `CONTRADICTION_REFUTED`, `INSUFFICIENT_EVIDENCE`), and Gate 5.6 conditional crop provenance.
   - Update `.agents/skills/aws-a30-lead-developer/SKILL.md` and `.agents/skills/aws-a30-gate-review/SKILL.md`: Update baseline references from October 23 (`398` tests, `src.evidence_chart_preflight`) to Gate 6.0 (`1,475+` tests, `src.evidence_whole_standard_preflight`, version-bound `_001` $\rightarrow$ `_002` store immutability, expanded SHA-256 lock table, and full anti-drift regexes).
   - Create `.agents/skills/aws-a30-ner-and-routing/SKILL.md`: Dedicated skill playbook for invoking `src.welding_ner` and `src.evidence_whole_standard_cli --ner / --route` to inspect compound process codes, homograph disambiguation, and ID-free spatial/waveform figure resolution.

---

### Deliverable `G60-4`: Frozen 20-Question Gate 6.0 NER & Multi-Intent Benchmark (`storage/evidence_v2/phase6_ner_routing_001/` + `eval/run_phase6_ner_routing.py`)

Create `storage/evidence_v2/phase6_ner_routing_001/` (`ner_routing_questions.json`, `rubric.json`, `results.json`) and deterministic evaluator `eval/run_phase6_ner_routing.py` (with zero hardcoded question IDs or benchmark trap literals inside `src/` or `eval/*.py`):

1. **Slice 1 — Dynamic Compound Process + Application Mode Designations (`G60-NER01` to `G60-NER04`):**
   - Queries testing dynamic `<BASE>-<SUFFIX>` decomposition (`PAW-AU`, `GTAW-ME`, `FCAW-G-SA`, `OFC-A-MA`) resolving both `Table A1` base/variant process and `Table A4` application mode suffix (`requires_diagram_crop: False` when no chart is requested).
2. **Slice 2 — ID-Free Annex B Spatial Diagram Callouts (`G60-NER05` to `G60-NER08`):**
   - Queries without `"Figure B..."` targeting interior spatial callouts:
     - *theoretical throat, effective throat, and actual throat* $\rightarrow$ `Figure B25` (`requires_diagram_crop: True`),
     - *toe crack, underbead crack, root crack, and crater crack* $\rightarrow$ `Figure B33` (`requires_diagram_crop: True`),
     - *advancing side, retreating side, tool shoulder, probe, and thermomechanically affected zone* $\rightarrow$ `Figure B46` (`requires_diagram_crop: True`),
     - *starting weld tab, runoff tab, sump, and split pipe backing* $\rightarrow$ `Figure B12` (`requires_diagram_crop: True`).
3. **Slice 3 — Homograph, Weld Position & Domain Qualifier Disambiguation (`G60-NER09` to `G60-NER12`):**
   - Unqualified `AB` query surfacing both *arc brazing* (`Table A1`) and *adhesive bonding* (`Figure A6` / `Clause 4`); qualified `AB` brazing query; `6G` / `6GR` pipe groove position (`Figure B16C` + `Clause 4`); `2F` fillet weld position in plate (`Figure B16B` + `Clause 4`).
4. **Slice 4 — Multi-Entity Cross-Store Comparative & Multi-Hop Queries (`G60-NER13` to `G60-NER16`):**
   - Multi-hop queries spanning 2–3 divisions in one prompt (e.g., `PAW-AU` meaning + `Figure A4` fusion welding classification branch; historical *atomic hydrogen welding* in `Annex D` / `Table A5` (`AHW`) vs. active `GTAW` in `Table A1`; *heliarc* nonstandard pivot + pulsed waveform upslope/downslope intervals in `Figure B53`; `Clause 4` multi-POS definition + `IS_A` hierarchy).
5. **Slice 5 — Invalid Compound Suffix, False-Premise & Out-of-Scope NER Boundaries (`G60-NER17` to `G60-NER20`):**
   - Invalid mode suffix on valid process code (e.g., `GTAW-ZZ` $\rightarrow$ identifies `GTAW` as valid `Table A1` designation, explicitly abstains/refutes `-ZZ` as not among `Table A4`'s 6 valid suffixes `-AD, -AU, -MA, -ME, -RO, -SA`); out-of-range locator (`Figure B55` $\rightarrow$ `REFUSAL_OUT_OF_RANGE`); unrecognized coined welding term $\rightarrow$ `NOT_IN_STANDARD`; external code/WPS schedule request $\rightarrow$ `REFUSAL_OUT_OF_SCOPE`.

---

### Deliverable `G60-5`: Gate 6.0 Verification Suite, Expanded SHA-256 Lock Table & Release Sync (`tests/test_gate_6_0_ner_routing_skills.py`)

Create `tests/test_gate_6_0_ner_routing_skills.py` verifying:
1. `test_gate_6_0_welding_ner_spans_and_compound_codes`: Asserts character-offset accuracy (`query[span.start_char:span.end_char] == span.surface_text`), non-overlapping longest-match behavior, dynamic decomposition of `PAW-AU` / `FCAW-G-SA` / `GTAW-ZZ`, standalone cold-start store hydration, and `AB` homograph `ambiguity_candidates`.
2. `test_gate_6_0_id_free_spatial_callout_routing`: Asserts ID-free callout queries resolve `Figure B25`, `Figure B33`, `Figure B46`, `Figure B12`, and `Figures B16A–C` with `requires_diagram_crop is True` and verified crop paths.
3. `test_gate_6_0_multi_intent_cross_store_composition`: Asserts multi-entity prompts execute multiple store operations and return modality-appropriate provenance (`requires_diagram_crop is False` for `Table A1 + Table A4` only; `True` when a diagram is consulted).
4. `test_gate_6_0_whole_standard_cli_and_skills_contracts`: Executes `src.evidence_whole_standard_cli` (`--ner`, `--route`, `--ask --json`) under `socket.socket` network block and scans `.agents/skills/*/SKILL.md` to confirm the obsolete *"only implemented source adapter is Figure A1"* statement is removed and `src.evidence_whole_standard_cli` + `src.evidence_whole_standard_preflight` are documented.
5. `test_gate_6_0_deepseek_replay_backward_and_new_cassettes`: Patches `socket.socket` to block network access and verifies all **8 existing Gate 5.4/5.5 cassettes** plus **2 new Gate 6.0 multi-intent cassettes** (`10` total) replay cleanly with `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.
6. `test_gate_6_0_benchmark_all_20_pass`: Runs `eval.run_phase6_ner_routing` and asserts **20 / 20 (100.0%)** pass rate.
7. `test_gate_6_0_all_29_locked_hashes_and_anti_drift`:
   - Verifies all **24 previously locked SHA-256 hashes** (unchanged) + **3 new `phase6_ner_routing_001` JSON artifacts** + **2 new Gate 6.0 DeepSeek replay cassettes** = **29 / 29 locked SHA-256 artifacts**.
   - Runs AST/regex anti-drift scan across `src/` and `eval/*.py` asserting `0 matches` for all benchmark ID patterns (including `G60-NER[0-9]+` / `G60-[0-9]+`) and `0 matches` in `src/` for benchmark trap literals.

---

## 3. Step-by-Step GitOps, Execution & Release Script for Gemini Antigravity

Execute the following PowerShell commands in order from `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`:

```powershell
# ===========================================================================
# STEP 0 (G60-0): GitOps Branch Audit, Gate 5.6 Release Tag & Branch Pruning
# ===========================================================================
git checkout main
git fetch --prune origin

# Verify 0 unmerged remote branches before pruning (must output nothing)
git branch -r --no-merged main

# 0a. Anchor Gate 5.6 production release at dd22331 with an immutable annotated tag
git tag -a v1.5.6-gate-5-6-calibrated dd22331 -m "v1.5.6: AWS A3.0M/A3.0:2020 Gate 5.6 Epistemic Calibration, 190-Page Coverage Manifest & Latency Telemetry (24/24 locked artifacts)"
git push origin v1.5.6-gate-5-6-calibrated

# 0b. Delete all 9 fully-merged non-main branches on GitHub (origin: 10 branches -> 1 clean 'main')
git push origin --delete `
  feat/gate-5-6-epistemic-manifest-calibration `
  feat/gate-5-5-semantic-nlq `
  feat/gate-5-production-hardening `
  feat/gate-5-4-deepseek-planner-replay `
  feat/gate-3d-phase3-live-holdout `
  feat/gate-3b-annex-b-archetype3-b1-b6 `
  feat/gate-3a-clause4-glossary-is-a `
  fix/a1-query-completeness `
  plan/helper-hardening-20261015

# 0c. Delete all 10 fully-merged non-worktree local branches safely (-d, NEVER -D; preserves bakeoff/a1-multimodal-hybrid archive & sibling worktrees)
git branch -d `
  docs/a1-bakeoff-findings `
  feat/a1-a2-relationship-readiness `
  feat/a2-source-aware-ingest `
  feat/gate-5-4-deepseek-planner-replay `
  feat/gate-5-5-semantic-nlq `
  feat/gate-5-6-epistemic-manifest-calibration `
  feat/gate-5-production-hardening `
  fix/a1-query-completeness `
  plan/declarative-manifest-20261015 `
  plan/helper-hardening-20261015

git fetch --prune origin
git branch -a

# 0d. Create clean Gate 6.0 feature branch from main
git checkout -b feat/gate-6-0-ner-routing-skills

# ===========================================================================
# STEP 1 (G60-1 .. G60-5): Implement NER, Multi-Intent Router, CLI, Skills & Benchmark
# ===========================================================================
# Implement:
#   - src/welding_ner.py
#   - src/semantic_nlq_expander.py (callout/backlink IDF index + standalone hydration + dead-code cleanup)
#   - src/evidence_phase4_bakeoff.py (multi-intent action planner + multi-store composer)
#   - src/deepseek_v41_adapter.py (+ 2 net-new Gate 6.0 replay cassettes)
#   - src/evidence_whole_standard_cli.py + .agents/skills/*/SKILL.md updates
#   - storage/evidence_v2/phase6_ner_routing_001/ + eval/run_phase6_ner_routing.py
#   - tests/test_gate_6_0_ner_routing_skills.py

# ===========================================================================
# STEP 2: Verify CLI Modes, Evaluators & Whole-Standard Preflight (0 Network)
# ===========================================================================
python -B -m src.evidence_whole_standard_cli --ner "What does PAW-AU designate and which diagram illustrates theoretical throat and effective throat?" --json
python -B -m src.evidence_whole_standard_cli --route "Compare historical atomic hydrogen welding with GTAW-ME" --json
python -B -m src.evidence_whole_standard_cli --ask "What does PAW-AU stand for in AWS A3.0?" --json

python -B -m eval.run_phase6_ner_routing
python -B -m eval.run_phase5_hardening
python -B -m eval.run_phase5_5_nlq
python -B -m eval.run_annex_a_holdout
python -B -m src.evidence_whole_standard_preflight

# ===========================================================================
# STEP 3: Anti-Drift & Anti-Overfitting Scans (Expect 0 Matches / Exit Code 1)
# ===========================================================================
git grep -E "QA[0-9]+|HO[0-9]+|CQ-[0-9]+|DEV[0-9]+|C4-QA[0-9]+|B[0-9]+-QA|P3-S[1-4]-|G4-B[0-9]+|G4B-[0-9]+|G5-ADV[0-9]+|G53-NLQ[0-9]+|G54-[0-9]+|G55-NLQ[0-9]+|G56-[0-9]+|G60-NER[0-9]+|G60-[0-9]+" -- src/ eval/*.py
git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/

# ===========================================================================
# STEP 4: Gate 5.x/6.0 Subset & Full Repository Pytest Regression (0 Failures, 0 Warnings)
# ===========================================================================
python -B -m pytest tests/test_gate_5_hardening.py tests/test_gate_5_4_deepseek_adapter.py tests/test_gate_5_5_semantic_nlq.py tests/test_gate_5_6_epistemic_manifest.py tests/test_gate_6_0_ner_routing_skills.py -v
python -B -m pytest --basetemp=C:\Users\kenai\AppData\Local\Temp\pytest_g60 -p no:langsmith -q

# ===========================================================================
# STEP 5: Commit, Refresh Release Docs/Bundles, Merge to main, Tag & Clean Branch
# ===========================================================================
git add -f storage/evidence_v2/phase6_ner_routing_001/*.json
git add -f storage/model_replays/deepseek_v4_1_flash_1017/*.json
git add -A
git commit -m "feat(gate-6.0): add deterministic welding NER, callout/backlink multi-intent router, whole-standard CLI, and updated agent skills"

# Update ROADMAP.md, goal.md, GATE_6_REVIEW_PACKET.md (or release ledger) & rebuild audit bundle
python -B scripts/build_gate_5_bundle.py
git add -A
git commit --allow-empty -m "chore(gate-6.0): refresh release ledger, roadmap, and audit bundle with Gate 6.0 receipts"

# Merge (--no-ff) into main, stamp v1.6.0 tag, push main + tag, and prune merged feature branch
git checkout main
git merge --no-ff feat/gate-6-0-ner-routing-skills -m "Merge branch 'feat/gate-6-0-ner-routing-skills' into main (Gate 6.0 Welding NER, Multi-Intent Routing & Agent Skills)"
git tag -a v1.6.0-ner-routing-skills -m "v1.6.0: AWS A3.0M/A3.0:2020 Welding Domain NER, Callout/Backlink Multi-Intent Router & Whole-Standard Agent Skills (29/29 locked artifacts)"
git push origin main
git push origin v1.6.0-ner-routing-skills

# Delete merged local feature branch (keep origin single-branch clean on 'main')
git branch -d feat/gate-6-0-ner-routing-skills
git branch -a

# Synchronize Google Drive mirror
python -B -m src.sync_drive_mirror
```

---

## 4. Required Closeout Receipts

Upon completion, report:
1. **GitOps Branch & Tag Reconciliation Receipt:** Confirmation of `v1.5.6-gate-5-6-calibrated` and `v1.6.0-ner-routing-skills` tags on `origin`, `origin` pruned from `10` branches $\rightarrow$ `1` branch (`origin/main`), `10` merged local branches deleted, and `bakeoff/a1-multimodal-hybrid` (`b9f7763`) preserved untouched.
2. **Welding NER & Callout Index Inventory:** Count of indexed NER surface patterns across the 11 entity types, indexed Annex B spatial callout phrases (`1,115` nodes), Clause 4 figure back-links (`265` edges), and sample `--ner` / `--route` JSON receipts.
3. **Gate 6.0 Benchmark & Prior Regression Pass Table:** `20 / 20 (100.0%)` on `phase6_ner_routing_001`, `15 / 15` on `phase5_5_nlq_001`, `10 / 10` on `phase5_hardening_001`, `30 / 30` on `annex_a_holdout_001`, and `CLEAR_WHOLE_STANDARD_CONTRACT` + `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT` (`0` network calls).
4. **29 / 29 Cryptographic SHA-256 Lock Table** (`24` unchanged Gate 0–5.6 digests + `5` new Gate 6.0 benchmark/replay artifacts), anti-drift grep output (`0 matches`), full repository pytest pass count (`1,475+ passed, 8 skipped, 0 failures, 0 warnings`), and final `main` merge commit SHA.
