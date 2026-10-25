# AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Roadmap (`ROADMAP.md`)

**Lead Developing Agent:** `gemini-3.8-flash`  
**Target Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Repository:** [kaiello/aws-a30-prototype](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype) (`C:\Users\kenai\aws-a30-prototype`)  
**Deployable Stable `main` Baseline:** `47922e810e132a899afdc0213344efb641f07f49` (Merged Gate 2D)  
**Active Development Branch:** `feat/annex-a-tables-join`  
**Gate 0 Checkpoint (PASSED):** `43bde2e53e6c4b3c9cb50fe05a3b160509f0844c` (24 October 2026, 02:55 UTC)  
**Gate 1A Checkpoint (PASSED):** `4bc7ab316a7196eb6277735f952dd51584d386d7` (24 October 2026, 03:45 UTC)  
**Gate 1B Checkpoint (PASSED):** `11aa384b8d0dc2b25e4e7d4d9fd6402f4f663279` (24 October 2026, 12:15 UTC — `A1-QA002-14` verified `OTHER WELDING AND JOINING`)  
**Gate 2A Checkpoint (PASSED):** `66317d41a3644a97bc81521b22880e531b5476ab` (Figure A3 Crop `e8ae06e6...`, Store Digest `afe1be93...`, 10/10 deterministic QA PASS)  
**Gate 2B Checkpoint (PASSED):** `d1dbf9945384a9cfaac89d9e9ad3d679381f5218` (Figure A4 Crop `ef4174d8...`, Store Digest `86bbe0f2...`, 10/10 deterministic QA PASS)  
**Gate 2C Checkpoint (PASSED):** `6b2d6265fd1e581090305f2c03785fc9672552fa` (Figure A5 Crop `cc432ea4...`, Store Digest `73837ea4...`, 10/10 deterministic QA PASS, 4-check anti-drift verified)  
**Gate 2D Checkpoint (PASSED):** `47922e810e132a899afdc0213344efb641f07f49` (Figure A6 Crop `d16a13a7...`, Store Digest `2eaf4065...`, 10/10 deterministic QA PASS, 4-check anti-drift verified)

## 1. Core Methodology: Strict Figure-by-Figure Progression Until Semi-Automated Consistency Is Proven

Rather than batch-ingesting multiple figures at once, this project advances **strictly one figure at a time**. Each figure serves both as a bounded epistemic deliverable and as a testbed to harden a **repeatable, semi-automated 4-stage figure pipeline**:

1. **Stage A — Manifest & Crop Lock:** Bind the single figure's `(figure_id, pdf_index, viewer_page, printed_page, crop_box, archetype_profile)` in the curated manifest, render the isolated crop PNG, and lock its SHA-256 hash so neighboring page material cannot leak in.
2. **Stage B — Text, Labels & Identity First:** Run native PDF text/vector extraction (with bounded OCR fallback where rasterized) and resolve every printed label, designation, legend entry, and footnote against the Source-Linked Identity Dictionary.
3. **Stage C — Relationships & Epistemic Admission Second:** Construct **Evidence Graph** observations (`ENCLOSES_ROW`, `CHART_CONNECTOR`, `INDENTED_UNDER`, column/branch connectors, callout leaders) and admit **Knowledge Graph** assertions (`CHART_MEMBER_OF`, `CHART_CONNECTED`, `CANDIDATE_LAYOUT_PARENT`) while keeping layout indentation and VLM checks (`knowledge_eligible=false`) strictly out of accepted `IS_A` status.
4. **Stage D — Multihop, Deterministic QA & Real-Entry Preflight Last:** Verify path explanations, cross-chart pointers, and source-limit abstentions via deterministic QA (`0` live LLM calls) and `python -B -m src.evidence_chart_preflight`, execute the **4-Check Deterministic Anti-Drift Loop**, then emit a single **Per-Figure Gate Review Packet** (`storage/gate_reviews/gate_<ID>_review_packet.md`) and stop for review.

### The 4-Check Deterministic Anti-Drift Loop (Mandatory Before Any Gate Review Packet)
To ensure long-term architectural stability, source fidelity, and prevent project drift, every figure pipeline must pass four automated deterministic checks before emitting a gate review packet:
1. **Check 1 (PDF Vector & BBox Geometry Audit via `fitz`):** Verifies the exact figure title against the List of Figures (printed p. x, PDF index 10) and page caption, confirms all legend/label text tokens exist in the PDF native text layer, and verifies physical vector line segments connect parent-to-child boxes across the figure crop. Catches topology branch defects (e.g. USW branching from Friction) and title hallucinations.
2. **Check 2 (Dual-Layer Epistemic Tier Ratio Guard):** Queries `graph.registry.db` (`a1k_typed_assertions`) to assert `ACCEPTED > 0` for all literal nodes, legend rows, and verified structural connectors (`CHART_CONNECTOR`, `ENCLOSES_ROW`), restricts `CANDIDATE` to uncorroborated layout indentation (`INDENTED_UNDER`), and verifies `IS_A == 0` strictly in chart-only gates, preventing 100% candidate flattening.
3. **Check 3 (External Table A1–A3 Cross-Check):** Cross-checks all legend designations and full process names against the normative process catalog in Table A3 (printed pp. 72–73, PDF indices 84–85), requiring any difference or omission (e.g., AHW in A4, AB in A6) to be explicitly declared in `spec.source_anomalies`. Breaks the self-authored rubric echo chamber.
4. **Check 4 (Target-Figure Shared Preflight):** Runs `python -B -m src.evidence_chart_preflight --figure <ID>` through the shared planner/compiler pipeline, confirming `CLEAR_REAL_ENTRY_CONTRACT` (11/11 contract checks passed) and `new_model_calls: 0`, preventing isolated per-figure script silos.

### When Do We Accelerate? (The Consistency Criterion)
We remain in **single-figure stop-and-review mode** across `Figure A3` $\rightarrow$ `Figure A4` $\rightarrow$ `Figure A5` $\rightarrow$ `Figure A6` until **two consecutive figures of the same structural archetype** pass Stages A–D on the first pass with **zero custom extractor patches or compiler regressions**. Only after an archetype's semi-automated pipeline proves consistent across consecutive single figures do we batch subsequent figures of that same archetype.

## 2. The 4 Reusable Structural Archetypes (Element/Class Families)

All 66 figures in **AWS A3.0M/A3.0:2020** map to four structural archetypes. As each archetype's first figure is reached, its reusable extraction and retrieval profile is added to `src/evidence_chart_contract.json` and `.agents/skills/`:

| Archetype ID & Name | Target Figures | First Calibration Figure | Second Verification Figure (Consistency Proof) | Key Elements & Epistemic Rules |
|---|---|---|---|---|
| **Archetype 1:**<br>`box_indentation_chart` | **Figures A1, A2, A3**<br>(pp. 75–76) | `Figure A1` (Done) & `Figure A2` (Done) | **`Figure A3`** (*Joining Method Chart*, p. 76 lower crop) | Enclosing boxes, undirected connectors, candidate row indentation, footnote `a`, and explicit cross-chart pointers (`See Figure A4/A5/A6`). |
| **Archetype 2:**<br>`characteristic_decision_tree` | **Figures A4, A5, A6**<br>(pp. 77–79) | **`Figure A4`** (*Fusion Welding Classification Chart*, p. 77) | **`Figure A5`** (p. 78) $\rightarrow$ **`Figure A6`** (p. 79) | 5-column physical characteristic tree (`Energy` $\rightarrow$ `Thermal` $\rightarrow$ `Loading` $\rightarrow$ `Shielding` $\rightarrow$ `Process`), `*Pressure normal to faying surfaces` footnote, bottom legend table, and multi-branch process nodes. |
| **Archetype 3:**<br>`spatial_callout_diagram` | **Figures B1–B43, B46–B48**<br>(pp. 82–147, 150–152) | **`Figure B1`** (*Joint Types*, p. 82) & **`Figure B6`** (pp. 87–89 multi-page) | **`Figure B2`** (p. 83) & **`Figure B7`** (p. 90) | Sub-panels `(A)`–`(R)`, dimension arrows, shaded zones, numbered keys (`B33`, `B46`), applicability tables (`B1`, `B7`, `B16A/B`), and multi-page continuation closure. |
| **Archetype 4:**<br>`cycle_waveform_plot` | **Figures B44–B45, B49–B54**<br>(pp. 148–149, 153–157) | **`Figure B49`** (*Pulsation RSW Waveform*, p. 153) | **`Figure B50`** (*Single-Pulse RSW*, p. 153) $\rightarrow$ **`Figure B53`** (p. 157) | Time-series horizontal axis (`TIME`), synchronized vertical traces (`CURRENT`, `FORCE`, `VOLTAGE`, `SPEED`), and ordered temporal intervals (`squeeze`, `weld`, `hold`, `upslope`, `downslope`). |

## 3. Figure-by-Figure Execution Schedule & Gate Checkpoints

### Phase 0 & Phase 1: Figures A1 & A2 Planner Closure (Gates 0, 1A, 1B)

| Gate | Scope | Status | Key Outcome & Next Requirement |
|---|---|---|---|
| **Gate 0** | Offline A1/A2 Preflight & Hygiene Closure | **PASSED (`43bde2e5`)** | `108/108` unit tests; `11/11` A1 & A2 preflights (`0` network calls); `main` untouched at `71088ce`. |
| **Gate 1A** | Offline `001` vs. `004` Diff & Adapter Repair | **PASSED (`4bc7ab31`)** | Resolved 36/49 blocked ops in `004`; all 5 A1 completeness targets (`A1-QA002-10`, `-13`, `-14`, `A1-HO002-01`, `-05`) pass offline. |
| **Gate 1B** | Pre-Launch Closure + 1 Fresh 67-Q Live Run (`A1` + `A2`) | **CONDITIONAL PASS (`11aa384b`)** | `67/67` compiled (`0` rejections), `194` executed ops. **Immediate Pre-Merge Check:** Verify raw disk output for `A1-QA002-14` (`OTHER WELDING AND JOINING` vs. `OXYFUEL GAS WELDING (OFW)`), then fast-forward merge `feat/planner-contract-preflight` to `main` and commit `ROADMAP.md`. |

### Phase 2: Annex A Figure-by-Figure Progression (One Figure per Gate)

Each gate below executes **strictly one figure** (establishing **1. Text/Footnotes $\rightarrow$ 2. Relationships $\rightarrow$ 3. Multihop & Offline Preflight**) with **0 live LLM calls** required during ingestion/deterministic verification:

| Gate ID | Single Target Figure / Slice | Source Coordinates (`AWS A3.0M/A3.0:2020`) | Semi-Automated Pipeline Goal & Verification Criteria |
|---|---|---|---|
| **Gate 2A** | **`Figure A3` — *Joining Method Chart***<br>(Completes Archetype 1 + Cross-Chart Pointers) | PDF index 88, viewer p. 89, printed p. 76 (**lower crop**, excluding Figure A2 above it) | **PASSED (`66317d4`)**<br>1. Crop SHA-256: `e8ae06e6d69cda2e05a84b5140f595cb4ef9b3b24a965aab0adc31c8efac593e`<br>2. Graph Digest: `afe1be936b078a3a4e65d6c7b8a7c7d22231c59898c91d794648deee033b1f1a`<br>3. 10/10 deterministic QA passed (100%), 0 LLM calls, preflight clear. |
| **Gate 2B** | **`Figure A4` — *Fusion Welding Classification Chart***<br>(First Archetype 2 Calibration Figure) | PDF index 89, viewer p. 90, printed p. 77 | **PASSED (`d1dbf99`)**<br>1. Crop SHA-256: `ef4174d8e8bd73345423b4daf40a76db56907a19bbb4c6dad3472519ee7fb032`<br>2. Graph Digest: `86bbe0f2d858f8513c265f0b3bd729499467b3161057b36a74ca5ef5d2d4b006`<br>3. 10/10 deterministic QA passed (100%), 0 LLM calls, preflight clear, Archetype 2 engine established. |
| **Gate 2C** | **`Figure A5` — *Solid-State Welding Classification Chart***<br>(First Test of Semi-Automated Archetype 2 Pipeline) | PDF index 90, viewer p. 91, printed p. 78 | **PASSED (`6b2d626`)**<br>1. Crop SHA-256: `cc432ea468ffcd6cd3025f0b15c58b2a11a0027a76188698ea4c1809b4957732`<br>2. Graph Digest: `73837ea4a3c90d9b4f3fe473f1faab1ca5cdb16f1c2ca22a3e85a58b81971476`<br>3. 10/10 deterministic QA passed (100%), 4-check anti-drift verified, 0 LLM calls, preflight clear. |
| **Gate 2D** | **`Figure A6` — *Brazing and Soldering Classification Chart***<br>(Second Test of Semi-Automated Archetype 2 Pipeline) | PDF index 91, viewer p. 92, printed p. 79 | **PASSED (`47922e8`)**<br>1. Crop SHA-256: `d16a13a7c839e99e253ad1e4d74e579e76b01f0a297601a3a625206f85773ff8`<br>2. Graph Digest: `2eaf406508d272acbe6640ef9e3a23207c9b146fbeba54536d8c9e2152fb6924`<br>3. 10/10 deterministic QA passed (100%), 4-check anti-drift verified, 0 LLM calls, preflight clear. |
| **Gate 2E** | **Normative `Tables A1–A5` Cross-Verification & Join** | PDF indices 81–86, viewer pp. 82–87, printed pp. 69–74 | Ingest Tables `A1`–`A5` across printed pp. 69–74 (PDF indices 81–86), bind to Figures `A1`–`A6`, preserve candidate indentation (`IS_A == 0`), record all 4 authentic source anomalies (`OC-P`, `EW-PC`/`RW-PC`, `AHW`, `AB`), and pass 15/15 deterministic QA + preflight. Stop and emit `gate_2E_review_packet.md`. |

### Phase 3: Clause 4 Glossary, Dual-Provenance `IS_A` & Annex B Figure-by-Figure Calibration

| Gate ID | Target Scope | Source Coordinates (`AWS A3.0M/A3.0:2020`) | Goal & Verification Criteria |
|---|---|---|---|
| **Gate 3A** | **Clause 4 Glossary + Dual-Provenance `IS_A` Promotion** (+ Annex C/D) | PDF indices 17–79 & 171–182, printed pp. 5–67 & 159–170 | Ingest Clause 4 definitions (boldface standard, lightface nonstandard, italic delimiters, `See Figure/Table` links) and promote `CANDIDATE_LAYOUT_PARENT` edges in `A1`/`A2` to accepted `IS_A_PROCESS_VARIATION_OF` **only where** corroborated by Clause 4 genus-differentia text + Table A1. |
| **Gate 3B** | **Archetype 3 Calibration: `Figure B1` (Single-Page) & `Figure B6` (3-Page Continuation)** | `B1`: printed p. 82 (PDF index 94)<br>`B6`: printed pp. 87–89 (PDF indices 99–101) | Build and verify the semi-automated **Archetype 3** (`spatial_callout_diagram`) pipeline on one single-page figure (`B1` with sub-panels `(A)`–`(E)` and `APPLICABLE WELD TYPES` lists) and one multi-page figure (`B6` across 3 pages `(A)`–`(L)`), then step through `B2`, `B3`, `B4`, `B5` one by one until consistent. |
| **Gate 3C** | **Archetype 4 Calibration: `Figure B49` $\rightarrow$ `Figure B50` $\rightarrow$ `Figure B53`** | Printed pp. 153 & 157 (PDF indices 165 & 169) | Build and verify the semi-automated **Archetype 4** (`cycle_waveform_plot`) pipeline on `B49`, test consistency on `B50` and `B53`, and complete remaining Annex B figures once the pipeline runs cleanly without per-figure patches. |

### Phase 4: Unseen Holdout & AWS Production Acceptance (`Gate 4`)

- Once the figure-by-figure and glossary slices are locked, run **one** frozen unseen benchmark comparing the Deterministic Route, `gemini-3.8-flash`, and AWS `GPT 5.6 Terra` / `Luna`.
