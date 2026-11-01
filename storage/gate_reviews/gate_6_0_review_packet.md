# Project Gate Review Packet: Gate 6.0 (Deterministic Welding Domain NER, Multi-Intent Routing & Whole-Standard Agent Skills)

**Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions*, 190 PDF pages)  
**Gate ID:** `Gate 6.0` (Deterministic Welding NER, Store-Compiled Callout/Backlink Routing, Whole-Standard CLI & Agent Skills)  
**Release Tag:** `v1.6.0-ner-routing-skills` (anchored at `6110430` on branch `main` / `origin/main`)  
**Base Lineage:** `v1.5.6-gate-5-6-calibrated` (`dd22331`) $\rightarrow$ `feat/gate-6-0-ner-routing-skills` (`49e5f0c`) $\rightarrow$ `fix/gate-6-0-audit-remediation` (`d115d85`) $\rightarrow$ `main` (`6110430`)  
**Audit Bundle:** `GATE_5_FULL_AUDIT_BUNDLE.md` & `storage/gate_reviews/GATE_5_FULL_AUDIT_BUNDLE.md` (rebuilt via `python -B scripts/build_gate_5_bundle.py`)  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)  
**Working Tree Status:** `CLEAN` (`29/29` cryptographic hashes locked and verified)  
**Author / Lead Developer:** Autonomous RAG Engineering Lead  
**Auditor / Reviewer:** Principal Reviewer & Systems Architect  
**Submission & Verification Date:** November 1, 2026  
**Final Closeout Disposition:** `APPROVED_CLOSED_OUT_AND_DEPLOYED`  

---

## 1. Executive Summary & Milestone Deliverables

This review packet formalizes the forensic audit, remediation, and final production closeout of **Gate 6.0**, providing the complete semantic extraction, multi-intent routing, and autonomous agent skill layer over the frozen 190-page `AWS A3.0M/A3.0:2020` multimodal standard.

### Deliverables Completed & Verified:

1. **Deterministic Welding Domain NER ([`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py)):**
   - Implemented character-offset deterministic entity recognizer extracting `3,514` surface patterns across 11 typed entity classes (`STANDARD_LOCATOR`, `PROCESS_CODE`, `MODE_SUFFIX`, `PROCESS_TERM`, `COMPOUND_DESIGNATION`, `NONSTANDARD_OR_HISTORICAL`, `GLOSSARY_TERM`, `WELD_POSITION`, `DOMAIN_QUALIFIER`, `DIAGRAM_CALLOUT`, `WAVEFORM_INTERVAL`).
   - Dynamic `<BASE_PROCESS>[-<VARIANT>]-<MODE_SUFFIX>` compound designation parser decomposing multi-code strings (e.g. `PAW-AU`, `FCAW-G-SA`, `OFC-A-MA`) into constituent `Table A1` processes and `Table A4` application mode suffixes with strict invalid suffix detection (e.g. `GTAW-ZZ`).
   - Multi-POS Clause 4 headword ambiguity tracking (e.g., `braze` as noun and verb) and morphological inflections (`kerfs` $\rightarrow$ `kerf`, `undercutting` $\rightarrow$ `undercut`).
   - Optimized with precomputed lowercase alphanumeric word-token tuples for $O(1)$ set-membership pre-filtering, eliminating Python stdlib `re._cache` thrashing (512-entry cache limit) and executing queries in $< 1\text{ ms}$.
   - Self-contained standalone hydration via [`WeldingNER.ensure_initialized()`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py#L118-L130).

2. **Store-Compiled Callout & Backlink Inverted Routing Index ([`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py)):**
   - Automatically ingests all **`1,115` accepted Annex B nodes** (`920` spatial nodes + `195` waveform nodes) across all 56 `figure_b*_store.json` files in `storage/evidence_v2/annex_b_complete_001/`.
   - Indexes **`130` Annex A process circles** across `Figures A2–A6` (`96` process circles across `A4–A6`).
   - Ingests **`492` Clause 4 figure backlink edges** across `352` unique glossary terms (`541` total spatial callout phrases in `callouts_to_figures`).
   - Evaluates multi-term queries using inverse document frequency (IDF) weighted scoring:
     $$w(\text{span}) = \ln\left(1 + \frac{N_{\text{figs}}}{\text{df}(\text{span})}\right) \times \text{word\_count}(\text{span})$$
   - Deterministically routes ID-free callouts to primary diagrams (`Figure B25`, `B33`, `B46`, `B12`, `B16B`, `B16C`, and non-benchmark `Figure B10`).

3. **Whole-Standard Headless CLI ([`src/evidence_whole_standard_cli.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_whole_standard_cli.py)):**
   - `--ner "<query>"`: Outputs character-offset spans, entity counts, and inferred multi-division targets.
   - `--route "<query>"`: Emits multi-intent router plans with `ner_receipt` and planned actions.
   - `--ask "<query>"`: Executes question answering under `--planner deterministic` or `--planner deepseek-replay` with modality-appropriate conditional crop provenance (`requires_diagram_crop: True/False`).
   - Full structured JSON formatting via `--json`.

4. **Whole-Standard Agent Skills Suite ([`.agents/skills/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/.agents/skills/)):**
   - Refactored `aws-a30-whole-standard-qa`, `aws-a30-welding-ner`, `aws-a30-diagram-routing`, `aws-a30-lead-developer`, and `aws-a30-gate-review`.
   - Stripped all obsolete "single-figure only" restrictions, directing autonomous agents to whole-standard CLI and Python APIs.

5. **Content-Addressed Gate 6.0 Replay Cassettes ([`storage/model_replays/deepseek_v4_1_flash_1017/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/model_replays/deepseek_v4_1_flash_1017/)):**
   - Created authentic content-addressed replay cassettes conforming to `compute_replay_key(prompt)`:
     - `4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` (`PAW-AU` + `Figure A4`)
     - `7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` (ID-free `Figure B25` throats + `Clause 4`)
   - Verified strict offline execution (`0` network calls) with epistemic quarantine tag `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.

6. **Frozen 20-Query Gate 6.0 Benchmark ([`eval/run_phase6_ner_routing.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_ner_routing.py)):**
   - Executed against [`storage/evidence_v2/phase6_ner_routing_001/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_ner_routing_001/):
     - Slice 1 (Dynamic Compound Codes): 4/4 PASS
     - Slice 2 (ID-Free Annex B Spatial Callouts): 4/4 PASS
     - Slice 3 (Homograph & Position Disambiguation): 4/4 PASS
     - Slice 4 (Multi-Entity Cross-Store Multi-Hop): 4/4 PASS
     - Slice 5 (Invalid Suffix & Out-of-Scope Boundaries): 4/4 PASS
   - Overall Score: **20 / 20 (100.0%) PASS**.

---

## 2. GitOps Branch & Tag Reconciliation Receipt

| GitOps Item | Certified Verification Receipt |
| :--- | :--- |
| **Merged Commit on `main`** | [`6110430c40247a6cbdc74671a39a8fc54cbd185e`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest) |
| **Annotated Release Tag** | `v1.6.0-ner-routing-skills` (`6110430c40247a6cbdc74671a39a8fc54cbd185e`) pushed to `origin` |
| **Prior Release Tag** | `v1.5.6-gate-5-6-calibrated` (`dd2233196742e0cb741e5901085369f75971a7d1`) verified on `origin` |
| **Remote Branches on `origin`** | Exactly **`1` branch** (`refs/heads/main`) verified via `git ls-remote --heads origin` |
| **Local Merged Branches Pruned** | `11` branches safely deleted via `git branch -d` (`feat/gate-6-0-ner-routing-skills`, `fix/gate-6-0-audit-remediation`, and 9 historical feature branches) |
| **Preserved Worktrees** | `bakeoff/a1-multimodal-hybrid` (`b9f7763`) + 5 sibling task worktrees untouched |
| **Google Drive Mirror Sync** | Synced `495` files (`39,359,864` bytes) to `G:\My Drive\git_projects\aws-a30-prototype`, pruned `2` obsolete files, verified `git_state_summary.txt` |

---

## 3. Store-Compiled Welding NER & Spatial Index Inventory

Verified via standalone cold-start hydration test in [`test_gate_6_0_welding_ner_spans_and_compound_codes`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_0_ner_routing_skills.py#L97-L170):

| NER & Search Index Component | Entity Class / Scope | Exact Pattern / Edge Count |
| :--- | :--- | :--- |
| **Glossary Terms & Inflections** | `GLOSSARY_TERM` | `2,670` active standard headwords, multi-POS ambiguity tags (`n.` / `v.`), and morphological variants |
| **Annex B Diagram Callouts** | `DIAGRAM_CALLOUT` | `436` canonical spatial labels compiled from **`1,115` accepted Annex B nodes** across 56 stores |
| **Waveform Intervals & Traces** | `WAVEFORM_INTERVAL` | `90` temporal cycle intervals across 7 Archetype 4 figures (`B44`, `B45`, `B49`, `B50`, `B51`, `B53`, `B54`) |
| **Nonstandard & Historical Terms** | `NONSTANDARD_OR_HISTORICAL` | `312` terms (`Clause 4` nonstandard + `Table A5` obsolete + `Table D4`/`D6` deleted + shop slang) |
| **Process Codes & Mode Suffixes** | `PROCESS_CODE`, `MODE_SUFFIX` | `155` process codes (`Table A1–A5`, `IS_A`, `Figures A2–A6`, `AB` homographs) + 6 Table A4 suffixes |
| **Process Names** | `PROCESS_TERM` | `151` full normative process names |
| **Standard Locators** | `STANDARD_LOCATOR` | `80` in-range and out-of-range boundary locators |
| **Weld Positions** | `WELD_POSITION` | `18` test positions (`1G`–`6GR`, `1F`–`4F`, position phrases) |
| **Domain Qualifiers** | `DOMAIN_QUALIFIER` | `14` qualifiers (`[pipe]`, `[plate]`, `[brazing]`, etc.) |
| **Compound Designation Parser** | `COMPOUND_DESIGNATION` | Dynamic parser covering $155 \times 6$ permutations with sub-component attribution |
| **Total Distinct NER Fast-Lookup Keys** | All 11 Classes | **`3,514` normalized patterns** ($O(1)$ token set pre-filtered) |
| **Annex B Ingested Graph Nodes** | `storage/evidence_v2/annex_b_complete_001/` | **`1,115` accepted nodes** (`920` spatial + `195` waveform) |
| **Annex A Ingested Process Circles** | `Figures A2–A6` | **`130` process circles** (`96` across `Figures A4–A6`) |
| **Clause 4 Figure Backlink Index** | `see Figure B...` | **`492` backlink edges** across `352` unique Clause 4 headwords |
| **Expander Inverted Callout Phrases** | Spatial + Backlink Phrases | **`541` phrases** in `callouts_to_figures` |

---

## 4. Benchmark & Full Regression Performance Ledger

All test executions verified under socket-level network blocking (`socket.socket` patched to raise `RuntimeError("Network blocked")`):

| Evaluation Suite / Benchmark | Target Division / Scope | Result | Network Calls |
| :--- | :--- | :---: | :---: |
| **Gate 6.0 NER & Multi-Intent Benchmark** | `storage/evidence_v2/phase6_ner_routing_001/` | **`20 / 20 (100.0%) PASS`** | `0` |
| **Gate 5.5 Semantic NLQ Benchmark** | `storage/evidence_v2/phase5_5_nlq_001/` | **`15 / 15 (100.0%) PASS`** | `0` |
| **Gate 5 Adversarial Hardening Suite** | `storage/evidence_v2/phase5_hardening_001/` | **`10 / 10 (100.0%) PASS`** | `0` |
| **Annex A Holdout Replay Suite** | `storage/evidence_v2/annex_a_holdout_001/` | **`30 / 30 (100.0%) PASS`** | `0` |
| **Whole-Standard Preflight Runner** | `src.evidence_whole_standard_preflight` | **`CLEAR_WHOLE_STANDARD_CONTRACT`** | `0` |
| **DeepSeek Replay Preflight Runner** | `src.evidence_whole_standard_preflight` | **`CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`** | `0` |
| **Gate 5.x + Gate 6.0 Sub-Suite** | 5 test files (`33` tests) | **`33 / 33 passed in 51.77s`** | `0` |
| **Full Repository Regression Suite** | `pytest --basetemp=... -q` | **`1,475 passed, 8 skipped in 195.47s`** | `0` |
| **Anti-Drift ID Leakage Scan** | `git grep -E "QA[0-9]+|...|G60-[0-9]+"` | **`0 matches (Exit Code 1)`** | N/A |
| **Anti-Overfitting Trap Literal Scan** | `git grep -Ei "hyper-flux|...|E7018"` | **`0 matches (Exit Code 1)`** | N/A |

---

## 5. Cryptographic Immutability Ledger (29 / 29 Locked Artifacts)

Cryptographically verified by [`test_gate_6_0_all_29_locked_hashes_and_anti_drift`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_0_ner_routing_skills.py#L343-L390) on `main` (`6110430`):

| # | Artifact ID / Scope | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Source PDF** | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | `VERIFIED_LOCKED` |
| 2 | **Glossary Store** | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | `VERIFIED_LOCKED` |
| 3 | **Annex C/D Store** | `storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | `VERIFIED_LOCKED` |
| 4 | **`IS_A` Promotion Store** | `storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | `VERIFIED_LOCKED` |
| 5 | **Annex B Archetype 3 (B1–B6)** | `storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | `VERIFIED_LOCKED` |
| 6 | **Annex B Complete** | `storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | `VERIFIED_LOCKED` |
| 7 | **Annex B Archetype 4** | `storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | `VERIFIED_LOCKED` |
| 8 | **Annex A Holdout Rubric** | `storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json` | `70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479` | `VERIFIED_LOCKED` |
| 9 | **Phase 5 Adversarial Qs** | `storage/evidence_v2/phase5_hardening_001/adversarial_questions.json` | `0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9` | `VERIFIED_LOCKED` |
| 10 | **Phase 5 Adversarial Rubric** | `storage/evidence_v2/phase5_hardening_001/rubric.json` | `df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981` | `VERIFIED_LOCKED` |
| 11 | **Phase 5 Adversarial Results** | `storage/evidence_v2/phase5_hardening_001/results.json` | `92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273` | `VERIFIED_LOCKED` |
| 12 | **Phase 5.5 NLQ Questions** | `storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json` | `ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57` | `VERIFIED_LOCKED` |
| 13 | **Phase 5.5 NLQ Rubric** | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b` | `VERIFIED_LOCKED` |
| 14 | **Phase 5.5 NLQ Results** | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74` | `VERIFIED_LOCKED` |
| 15 | **DeepSeek Cassette (Fig A2)** | `storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json` | `59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f` | `VERIFIED_LOCKED` |
| 16 | **DeepSeek Cassette (Multi-Hop)** | `storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079` | `VERIFIED_LOCKED` |
| 17 | **DeepSeek Cassette (Out-of-Range)** | `storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d` | `VERIFIED_LOCKED` |
| 18 | **DeepSeek Cassette (False Premise)** | `storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a` | `VERIFIED_LOCKED` |
| 19 | **DeepSeek Cassette (Fig A1)** | `storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | `VERIFIED_LOCKED` |
| 20 | **DeepSeek Cassette (Waveform B53)** | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | `VERIFIED_LOCKED` |
| 21 | **DeepSeek Cassette (AHW Historical)** | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | `VERIFIED_LOCKED` |
| 22 | **DeepSeek Cassette (Out-of-Scope)** | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | `VERIFIED_LOCKED` |
| 23 | **Coverage Manifest** | `storage/manifests/coverage_manifest.json` | `8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e` | `VERIFIED_LOCKED` |
| 24 | **Latency Benchmark** | `storage/manifests/latency_benchmark.json` | `bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c` | `VERIFIED_LOCKED` |
| 25 | **Gate 6.0 NER/Routing Qs** | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac` | `VERIFIED_LOCKED` |
| 26 | **Gate 6.0 NER/Routing Rubric** | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427` | `VERIFIED_LOCKED` |
| 27 | **Gate 6.0 NER/Routing Results** | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8` | `VERIFIED_LOCKED` |
| 28 | **Gate 6.0 Replay (PAW-AU + A4)** | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057` | `VERIFIED_LOCKED` |
| 29 | **Gate 6.0 Replay (Throat + C4)** | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42` | `VERIFIED_LOCKED` |

---

## 6. Sample Verified CLI Execution Receipts

### A. Named Entity Recognition Receipt (`--ner`)
```powershell
python -B -m src.evidence_whole_standard_cli --ner "What does PAW-AU stand for and how are theoretical throat and effective throat defined?" --json
```
```json
{
  "raw_query": "What does PAW-AU stand for and how are theoretical throat and effective throat defined?",
  "spans": [
    {
      "surface_text": "PAW-AU",
      "start_char": 10,
      "end_char": 16,
      "entity_type": "COMPOUND_DESIGNATION",
      "canonical_term": "automatic plasma arc welding",
      "canonical_id": "compound:PAW-AU",
      "source_authority": "Table A1 (p. 69) + Table A4 (p. 74)",
      "target_division": "annex_a_tables",
      "sub_components": [
        {"type": "BASE_PROCESS", "designation": "PAW", "canonical_term": "plasma arc welding", "source_authority": "Table A1 (p. 69)"},
        {"type": "APPLICATION_MODE", "suffix": "-AU", "canonical_term": "Automatic", "source_authority": "Table A4 (p. 74)"}
      ],
      "is_valid": true
    },
    {
      "surface_text": "theoretical throat",
      "start_char": 43,
      "end_char": 61,
      "entity_type": "DIAGRAM_CALLOUT",
      "canonical_term": "theoretical throat",
      "canonical_id": "figure_b25:callout:theoretical_throat",
      "source_authority": "Annex B (Figure B25, p. 123)",
      "target_division": "annex_b_spatial",
      "is_valid": true
    },
    {
      "surface_text": "effective throat",
      "start_char": 66,
      "end_char": 82,
      "entity_type": "DIAGRAM_CALLOUT",
      "canonical_term": "effective throat",
      "canonical_id": "figure_b25:callout:effective_throat",
      "source_authority": "Annex B (Figure B25, p. 123)",
      "target_division": "annex_b_spatial",
      "is_valid": true
    }
  ],
  "entity_counts_by_type": {"COMPOUND_DESIGNATION": 1, "DIAGRAM_CALLOUT": 2},
  "target_divisions": ["annex_a_tables", "annex_b_spatial"],
  "inferred_targets": {"figures": ["Figure B25"], "tables": [], "clause4_terms": []}
}
```

### B. Multi-Intent Semantic Route Receipt (`--route`)
```powershell
python -B -m src.evidence_whole_standard_cli --route "Compare historical atomic hydrogen welding with GTAW-ME" --json
```
```json
{
  "query": "Compare historical atomic hydrogen welding with GTAW-ME",
  "planner": "deterministic",
  "target_division": "Multi-Division",
  "intent": "compound_designation_and_historical",
  "target_entities": ["atomic hydrogen welding", "GTAW-ME"],
  "actions": [
    {"action_type": "lookup_historical_process", "target": "atomic hydrogen welding", "parameters": {"source_authority": "Table A5 (p. 74)"}},
    {"action_type": "lookup_compound_code", "target": "GTAW-ME", "parameters": {
      "sub_components": [
        {"type": "BASE_PROCESS", "designation": "GTAW", "canonical_term": "gas tungsten arc welding", "source_authority": "Table A1 (p. 69)"},
        {"type": "APPLICATION_MODE", "suffix": "-ME", "canonical_term": "Mechanized", "source_authority": "Table A4 (p. 74)"}
      ]
    }}
  ]
}
```

### C. Question Answering with Diagram Crop (`--ask --planner deepseek-replay`)
```powershell
python -B -m src.evidence_whole_standard_cli --ask "What does PAW-AU designate and how is plasma arc welding classified in Figure A4?" --planner deepseek-replay --json
```
```json
{
  "question": "What does PAW-AU designate and how is plasma arc welding classified in Figure A4?",
  "answer": "In AWS A3.0M/A3.0:2020, PAW-AU designates automatic plasma arc welding (Table A1, p. 69; Table A4, p. 74). In Figure A4 (Fusion Welding Classification, printed p. 78, PDF index 90), plasma arc welding (PAW) branches under Fusion Welding with an Electrical energy source and Arc thermal source.",
  "printed_page": 78,
  "pdf_index": 90,
  "evidence_locator": "figure_a4:fusion_welding",
  "requires_diagram_crop": true,
  "crop_path": "storage/evidence_v2/a4_ingest_001/a4_crop_300.png",
  "execution": {
    "status": "PASS",
    "operations_count": 2,
    "elements_present": ["PAW-AU", "automatic plasma arc welding", "Figure A4", "Fusion Welding", "Arc", "plasma arc welding"],
    "normative_provenance": ["obs:pdf:81:table:Table A1", "obs:pdf:86:table:Table A4", "obs:pdf:90:figure:Figure A4"]
  }
}
```

---

## 7. Review Verdict & Operational Signoff

### Formal Gate Closeout Verdict: **`APPROVED_CLOSED_OUT_AND_DEPLOYED`**

The `AWS A3.0M/A3.0:2020` Multimodal RAG system has completed all milestones for Gate 6.0:
- GitOps integrity verified with a single remote branch (`origin/main`) and annotated tag `v1.6.0-ner-routing-skills`.
- Standalone deterministic Welding Domain NER with 3,514 patterns and dynamic compound designation parsing.
- Whole-standard store-compiled callout/backlink inverted search index with 1,115 Annex B nodes, 130 Annex A circles, and 492 backlink edges.
- All 1,475 repository regression tests passing with 0 failures and 0 warnings under network-isolated test execution.
- All 29 cryptographic SHA-256 digests verified and locked.
- Google Drive mirror and documentation synchronized.

**Operational Clearance:** The system is fully verified, operational, and approved for production use.
