# AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Roadmap (`ROADMAP.md`)

**Lead Developing Agent:** `gemini-3.8-flash`  
**Target Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Repository:** [kaiello/aws-a30-prototype](https://github.com/kaiello/aws-a30-prototype) (`C:\Users\kenai\aws-a30-prototype`)  
**Google Drive Inspection Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synced via `python -B -m src.sync_drive_mirror`)  
**Previous Stable `main` Baseline:** [71088cebc9eb3b2556d7bbe73a23a451e645e3b9](https://github.com/kaiello/aws-a30-prototype/commit/71088cebc9eb3b2556d7bbe73a23a451e645e3b9) ([PR12](https://github.com/kaiello/aws-a30-prototype/pull/12))  
**Gate 0 Checkpoint (PASSED):** `43bde2e53e6c4b3c9cb50fe05a3b160509f0844c` (24 October 2026, 02:55 UTC)  
**Gate 1A Checkpoint (PASSED):** `4bc7ab316a7196eb6277735f952dd51584d386d7` (24 October 2026, 03:45 UTC)  
**Gate 1B Checkpoint (PASSED & MERGED):** `11aa384b8d0dc2b25e4e7d4d9fd6402f4f663279` $\rightarrow$ `main` `2fbaabd8ce83b99480dc5846f48825ba8bb0ca98`  
**Gate 2A Checkpoint (PASSED & MERGED — Figure A3):** `66317d41a3644a97bc81521b22880e531b5476ab` $\rightarrow$ `main` `66937d94cf212eb5db3b9ff41147076d338ce2a1`  
**Gate 2B Checkpoint (PASSED & MERGED — Figure A4):** `d1dbf9945384a9cfaac89d9e9ad3d679381f5218` $\rightarrow$ `main` `5108cba30796cb0b998ef37a9a796548d7285d1a`  
**Gate 2C Checkpoint (PASSED & MERGED — Figure A5):** `6b2d6265fd1e581090305f2c03785fc9672552fa` $\rightarrow$ `main` `e080a7090875c7b3967bbfebffba1f22e8633cb2`  
**Gate 2D Checkpoint (PASSED & MERGED — Figure A6):** `47922e810e132a899afdc0213344efb641f07f49` $\rightarrow$ `main` `e86157c4d380d090d3660830b893dcf04102be1b`  
**Gate 2E Checkpoint (PASSED — Normative Tables A1–A5 & Tier 1/2 Tests):** `d55eba2` (`c554e9c` + `d55eba2`) on `feat/annex-a-tables-join` (Approved to merge into `main`; 3 pre-launch items queued for Gate 2F.1 before live LLM calls)  
**Gate 2F Checkpoint (PASSED & MERGED — Live Annex A Holdout Benchmark):** `c4363c2` $\rightarrow$ `main` `c4363c2` (30/30 holdout PASS, 127 executed ops, 0 blocked actions, 171/171 unit tests)
**Gate 3A Checkpoint (PASSED & MERGED — Clause 4 Glossary, Dual-Provenance IS_A Promotion, Annex C/D Ingestion):** `728ceed` $\rightarrow$ `main` `728ceed` (1,607 glossary entries, 378 underlines, 458 margin bars, 311 nonstandard relationships, 8 Annex C decisions, 591 Annex D rows, 35 promoted IS_A edges, 83 retained candidate edges, 0 uncorroborated, 20/20 benchmark PASS, CLEAR_REAL_ENTRY_CONTRACT)

## 1. Core Methodology, 3-Tier Testing Strategy & Live LLM Cadence

Rather than batch-ingesting multiple figures at once or burning live LLM calls while extraction schemas are still in flux, this project pairs a **repeatable 4-stage figure pipeline** with a **3-Tier Testing & Live LLM Cadence**:

### A. The 4-Stage Figure Pipeline & 4-Check Anti-Drift Loop
1. **Stage A — Manifest & Crop Lock:** Bind `(figure_id, pdf_index, viewer_page, printed_page, crop_box, archetype_profile)` in the curated manifest, render the isolated crop PNG, and lock its SHA-256 hash.
2. **Stage B — Native PDF Text, Vector Geometry & Identity First (Check 1):** Extract native PDF text spans (`page.get_text("dict")`) and vector drawings (`page.get_drawings()`) within the crop box, verify the official title against the *List of Figures* (printed p. x), and verify that physical vector lines connect declared parent and child boxes.
3. **Stage C — Dual-Layer Epistemic Admission & Normative Table Cross-Check (Checks 2 & 3):**
   - **Check 2:** Assert `ACCEPTED > 0` for literal boxes, legend rows, and verified structural connections (`CHART_MEMBER_OF`, `CHART_CONNECTED`), restrict `CANDIDATE` to layout-indentation inferences (`CANDIDATE_LAYOUT_PARENT`) and VLM checks (`knowledge_eligible=false`), and assert `IS_A == 0` in chart-only gates.
   - **Check 3:** Cross-check all figure designations against independent normative `Table A3` (pp. 72–73) so any discrepancy must be explicitly declared in `source_anomalies`.
4. **Stage D — Shared Preflight & Google Drive Mirror Sync (Check 4):** Run `python -B -m src.evidence_chart_preflight --figure <ID>` (`CLEAR_REAL_ENTRY_CONTRACT`, `0` network calls) and mirror all review artifacts via `python -B -m src.sync_drive_mirror`.

### B. 3-Tier Testing Strategy & When Live LLM Calls Happen

To eliminate the gap between **keyword-matched `DEV001` scripts** (`answer_decision_tree_query` in `src/archetype_decision_tree.py`) and **true natural-language planning (`answer_graph`)**, testing is structured across three tiers, with **bounded live LLM runs occurring once at the close of each major phase**:

| Testing Tier | When It Runs | What It Exercises | Why It Matters |
|---|---|---|---|
| **Tier 1: Exhaustive Graph-Property & Path-Completeness Tests (`0` LLM calls)** | Every sub-gate (`Gates 2A–2E`, `3A–3C`) | Iterates programmatically over **100% of nodes, process circles (`26` in A4, `22` in A5, `48` in A6 = `96` circles), legend rows (`23 + 15 + 21 = 59`), and `Table A1–A5` entries (`134`)** to verify that every graph edge path matches its `path_summary`, PDF vector connector, and cross-table join. | Tests every single node and branch in the chart—not just the 10 nodes mentioned in `DEV001`. |
| **Tier 2: Offline AST Plan-Compiler & Rubric-Graded Execution Tests (`0` LLM calls)** | End of each subsystem (`Gate 2E` / `Gate 2F.1` for Annex A; `Gate 3A/3B/3C` for Clause 4 & Annex B) | Compiles and executes structured `chart-question-actions-1.0` plans (using **only model-visible printed labels/codes or `n1..nK` aliases**) through `src/evidence_chart_question_plan.py` $\rightarrow$ `src/evidence_a1_graph_qa.py` (`answer_graph`), grading the composed `answer_graph` output against `rubric.json` (`required_elements`). | Proves the AST compiler and `answer_graph` composer satisfy the full rubric on `A3`–`A6` without falling back to `if/elif` keyword matching or internal `a4node:...` IDs. |
| **Tier 3: Principal-Authored Unseen Holdout + Bounded Live LLM Run (`temperature=0`, `0` retries)** | **Phase-Closing Live Gates Only:**<br>• `Gate 1B` (Done — 67 calls on `A1`+`A2`)<br>• **`Gate 2F.2`** (30 calls on `A3`–`A6` + `Tables A1–A5`)<br>• **`Gate 3D`** (~50 calls on Clause 4 + Annex B `Archetypes 3 & 4`)<br>• **`Gate 4`** (Final multi-model bakeoff) | Runs the live LLM planner (`DeepSeekQuestionPlanner` / `LocalQuestionPlanner`) once against an **external, reviewer-authored unseen benchmark** containing paraphrased queries, 2-part compound questions, ambiguity traps (e.g., `"What does AB stand for?"`, `"Which processes use Radiation?"`), cross-chart/table hops, and out-of-scope abstentions. | Prevents prompt/rubric overfitting while keeping API costs bounded to 3–4 disciplined live checkpoints across the entire project. |

## 2. The 4 Reusable Structural Archetypes (Element/Class Families)

All 66 figures in **AWS A3.0M/A3.0:2020** map to four structural archetypes. As each archetype's first figure is reached, its reusable extraction and retrieval profile is added to `src/evidence_chart_contract.json` and `.agents/skills/`:

| Archetype ID & Name | Target Figures | First Calibration Figure | Second Verification Figure (Consistency Proof) | Key Elements & Epistemic Rules |
|---|---|---|---|---|
| **Archetype 1:**<br>`box_indentation_chart` | **Figures A1, A2, A3**<br>(pp. 75–76) | `Figure A1` (Done) & `Figure A2` (Done) | **`Figure A3`** (Done — `Gate 2A` Passed) | Enclosing boxes, undirected connectors, candidate row indentation, footnote `a`, and explicit cross-chart pointers (`See Figure A4/A5/A6`). |
| **Archetype 2:**<br>`characteristic_decision_tree` | **Figures A4, A5, A6**<br>(pp. 77–79) | **`Figure A4`** (Done — `Gate 2B` Passed) | **`Figure A5`** (Done — `Gate 2C` Passed) $\rightarrow$ **`Figure A6`** (Done — `Gate 2D` Passed) | 5-column physical characteristic tree (`Energy` $\rightarrow$ `Thermal` $\rightarrow$ `Loading` $\rightarrow$ `Shielding` $\rightarrow$ `Process`), `*Pressure normal to faying surfaces` footnote, bottom legend table, and multi-branch process nodes. |
| **Archetype 3:**<br>`spatial_callout_diagram` | **Figures B1–B43, B46–B48**<br>(pp. 82–147, 150–152) | **`Figure B1`** (*Joint Types*, p. 82) & **`Figure B6`** (pp. 87–89 multi-page) | **`Figure B2`** (p. 83) & **`Figure B7`** (p. 90) | Sub-panels `(A)`–`(R)`, dimension arrows, shaded zones, numbered keys (`B33`, `B46`), applicability tables (`B1`, `B7`, `B16A/B`), and multi-page continuation closure. |
| **Archetype 4:**<br>`cycle_waveform_plot` | **Figures B44–B45, B49–B54**<br>(pp. 148–149, 153–157) | **`Figure B49`** (*Pulsation RSW Waveform*, p. 153) | **`Figure B50`** (*Single-Pulse RSW*, p. 153) $\rightarrow$ **`Figure B53`** (p. 157) | Time-series horizontal axis (`TIME`), synchronized vertical traces (`CURRENT`, `FORCE`, `VOLTAGE`, `SPEED`), and ordered temporal intervals (`squeeze`, `weld`, `hold`, `upslope`, `downslope`). |

## 3. Figure-by-Figure Execution Schedule & Gate Checkpoints

### Phase 0 & Phase 1: Figures A1 & A2 Planner Closure (Gates 0, 1A, 1B — COMPLETED)

| Gate | Scope | Status | Key Outcome |
|---|---|---|---|
| **Gate 0** | Offline A1/A2 Preflight & Hygiene Closure | **PASSED (`43bde2e5`)** | `108/108` unit tests; `11/11` A1 & A2 preflights (`0` network calls); `main` untouched at `71088ce`. |
| **Gate 1A** | Offline `001` vs. `004` Diff & Adapter Repair | **PASSED (`4bc7ab31`)** | Resolved 36/49 blocked ops in `004`; all 5 A1 completeness targets (`A1-QA002-10`, `-13`, `-14`, `A1-HO002-01`, `-05`) pass offline. |
| **Gate 1B** | Pre-Launch Closure + 1 Fresh 67-Q Live Run (`A1` + `A2`) | **PASSED & MERGED (`2fbaabd`)** | `67/67` compiled (`0` rejections), `194` executed ops, `51/51` A1 & `16/16` A2 (`A1-QA002-14` confirmed `OTHER WELDING AND JOINING` on disk). |

### Phase 2: Annex A Figure-by-Figure Progression & Live Planner Closure (`Gates 2A–2F`)

| Gate ID | Single Target Figure / Slice | Status & Source Coordinates | Semi-Automated Pipeline Goal & Verification Criteria |
|---|---|---|---|
| **Gate 2A** | **`Figure A3` — *Joining Method Chart*** | **PASSED & MERGED (`66937d94`)**<br>PDF index 88, viewer p. 89, printed p. 76, crop `[0.51, 0.20, 0.86, 0.80]`<br>Crop SHA-256: `e8ae06e6...`<br>Store SHA-256: `afe1be93...` | `11` nodes, `10` edges, `0` cycles, `0` `IS_A` promotions; `10/10` deterministic QA PASS; `114/114` unit tests (`1.98 s`). |
| **Gate 2B** | **`Figure A4` — *Fusion Welding Classification Chart*** | **PASSED & MERGED (`5108cba3`)**<br>PDF index 89, viewer p. 90, printed p. 77, crop `[0.065, 0.085, 0.925, 0.915]`<br>Crop SHA-256: `ef4174d8...`<br>Store SHA-256: `86bbe0f2...` (`149` ACCEPTED / `0` `IS_A`) | Created `src/archetype_decision_tree.py`; `66` nodes, `42` edges, `0` cycles, `0` `IS_A` promotions; `26` process circles (`24` distinct processes), `23` legend rows; `10/10` QA PASS; 4-Check Anti-Drift PASS. |
| **Gate 2C** | **`Figure A5` — *Solid-State Welding Classification Chart*** | **PASSED & MERGED (`e080a709`)**<br>PDF index 90, viewer p. 91, printed p. 78, crop `[0.065, 0.085, 0.925, 0.915]`<br>Crop SHA-256: `cc432ea4...`<br>Store SHA-256: `73837ea4...` (`127` ACCEPTED / `0` `IS_A`) | `src/evidence_a5.py` (`214` lines $\le 250$); `68` nodes, `66` edges; `USW` branches from `Friction -> Pressure -> USW` while only `CW` skips `Thermal Source`; `EXW` preserves `Deformation`; 4-Check Anti-Drift PASS (`126/126` unit tests). |
| **Gate 2D** | **`Figure A6` — *Brazing and Soldering Classification Chart*** | **PASSED & MERGED (`e86157c4`)**<br>PDF index 91, viewer p. 92, printed p. 79, crop `[0.065, 0.085, 0.925, 0.915]`<br>Crop SHA-256: `d16a13a7...`<br>Store SHA-256: `2eaf4065...` (`157` ACCEPTED / `0` `IS_A`) | `src/evidence_a6.py` (`243` lines $\le 250$); `104` nodes, `102` edges (`48` process circles across `21` distinct processes, `21` legend rows with `B-CA`, `EBB`, `EXB`, `LBB` underlined); `AB = arc brazing` vs. `adhesive bonding` collision declared; 4-Check Anti-Drift PASS. |
| **Gate 2E** | **Normative `Tables A1–A5` Join + Tier 1 Exhaustive Property Tests & Tier 2 AST Closure (`0` LLM Calls)** | **PASSED (`d55eba2`)**<br>PDF indices 81–86, viewer pp. 82–87, printed pp. 69–74<br>Tables Store SHA-256: `9d16717a...` (`429` ACCEPTED / `118` CANDIDATE / `4` DISPUTED / `0` `IS_A`) | `Tables A1–A5` ingested (`138` A1 rows, `133` A2 rows, `134` A3 rows, `6` A4 suffixes, `13` A5 obsolete rows); all 4 source anomalies verified; Tier 1 exhaustive suite (`96` circles, `20` multi-branch codes, `59` legend rows) & Tier 2 AST compiler suite (`40/40` compiled) passing (`564/564` unit tests). |
| **Gate 2F** | **Pre-Launch Drift Closure (`2F.1`, `0` LLM Calls) + Bounded 30-Q Unseen Live LLM Holdout Run (`2F.2`, `30` Calls)** | **PASSED & MERGED (`c4363c2`)**<br>Closes Phase 2 (`Figures A1–A6` + `Tables A1–A5`) | Step 2F.1 drift closure and Step 2F.2 30-question live LLM holdout run complete; `30/30` (`100.0%`) PASS, `127` executed operations, `0` blocked actions, `0` uncorroborated `IS_A` promotions; all `171/171` unit & property tests passing; Gate 2F review packet emitted and Google Drive mirror synced. |

### Phase 3: Clause 4 Glossary, Dual-Provenance `IS_A` & Annex B Calibration (`Gates 3A–3D`)

| Gate ID | Target Scope | Source Coordinates (`AWS A3.0M/A3.0:2020`) | Goal & Verification Criteria |
|---|---|---|---|
| **Gate 3A** | **Clause 4 Glossary + Dual-Provenance `IS_A` Promotion** (+ Annex C/D) | **PASSED & MERGED (`728ceed`)**<br>PDF indices 17–79 & 171–182, printed pp. 5–67 & 159–170<br>Locked Hashes:<br>• `glossary_store.json`: `b602af99...`<br>• `annex_c_d_store.json`: `8b5d8faa...`<br>• `is_a_promotion_store.json`: `a5c69c35...` | Ingest Clause 4 definitions (1,607 entries, 378 underlines, 458 margin bars, 311 nonstandard relationships, 134/134 Table A3 coverage, 13/13 Table A5 coverage), Annex C (21 clauses, 8 decisions), Annex D (6 tables, 591 rows), and dual-provenance `IS_A_PROCESS_VARIATION_OF` promotion engine (35 promoted, 83 retained, 0 uncorroborated); 20/20 benchmark PASS; 18/18 unit tests PASS. |
| **Gate 3B** | **Archetype 3 Calibration: `Figure B1` (Single-Page) & `Figure B6` (3-Page Continuation)** | **ACTIVE CURRENT GATE**<br>`B1`: printed p. 82 (PDF index 94)<br>`B6`: printed pp. 87–89 (PDF indices 99–101)<br>`B2`–`B5`: printed pp. 83–86 (PDF indices 95–98) | Build and verify the semi-automated **Archetype 3** (`spatial_callout_diagram`) pipeline on `B1` and `B6` (3-page continuation), then step through `B2`–`B5` until consistent (`0` LLM calls). |
| **Gate 3C** | **Archetype 4 Calibration: `Figure B49` $\rightarrow$ `Figure B50` $\rightarrow$ `Figure B53` + Remaining Annex B** | Printed pp. 153 & 157 (PDF indices 165 & 169) | Build and verify the semi-automated **Archetype 4** (`cycle_waveform_plot`) pipeline on `B49`, `B50`, and `B53`, and complete remaining Annex B figures once consistent (`0` LLM calls). |
| **Gate 3D** | **Tier 3: Bounded Live LLM Run on Clause 4 + Annex B Holdout (~50 Live Calls)** | Whole Standard (`Clause 4` + `Annex A/B/C/D`) | Execute **1 bounded live LLM run** (`temperature=0`, `0` retries) on a reviewer-supplied unseen cross-modal holdout suite (`Clause 4 <-> Annex A <-> Annex B <-> Annex C/D`). |

### Phase 4: Unseen Holdout & AWS Production Acceptance (`Gate 4`)

- Run **one** frozen unseen benchmark comparing the Deterministic Route, `gemini-3.8-flash`, and AWS `GPT 5.6 Terra` / `Luna` across all 5 evaluation dimensions plus latency and cost.
