# AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Roadmap (`ROADMAP.md`)

**Lead Developing Agent:** `gemini-3.8-flash`  
**Target Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Repository:** [kaiello/aws-a30-prototype](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype) (`C:\Users\kenai\aws-a30-prototype`)  
**Deployable Stable `main` Baseline:** `66317d41a3644a97bc81521b22880e531b5476ab` (Merged Gate 2A)  
**Active Development Branch:** `feat/a4-source-aware-ingest`  
**Gate 0 Checkpoint (PASSED):** `43bde2e53e6c4b3c9cb50fe05a3b160509f0844c` (24 October 2026, 02:55 UTC)  
**Gate 1A Checkpoint (PASSED):** `4bc7ab316a7196eb6277735f952dd51584d386d7` (24 October 2026, 03:45 UTC)  
**Gate 1B Checkpoint (PASSED):** `11aa384b8d0dc2b25e4e7d4d9fd6402f4f663279` (24 October 2026, 12:15 UTC — `A1-QA002-14` verified `OTHER WELDING AND JOINING`)  
**Gate 2A Checkpoint (PASSED):** `66317d41a3644a97bc81521b22880e531b5476ab` (Figure A3 Crop `e8ae06e6...`, Store Digest `afe1be93...`, 10/10 deterministic QA PASS)

## 1. Core Methodology: Strict Figure-by-Figure Progression Until Semi-Automated Consistency Is Proven

Rather than batch-ingesting multiple figures at once, this project advances **strictly one figure at a time**. Each figure serves both as a bounded epistemic deliverable and as a testbed to harden a **repeatable, semi-automated 4-stage figure pipeline**:

1. **Stage A — Manifest & Crop Lock:** Bind the single figure's `(figure_id, pdf_index, viewer_page, printed_page, crop_box, archetype_profile)` in the curated manifest, render the isolated crop PNG, and lock its SHA-256 hash so neighboring page material cannot leak in.
2. **Stage B — Text, Labels & Identity First:** Run native PDF text/vector extraction (with bounded OCR fallback where rasterized) and resolve every printed label, designation, legend entry, and footnote against the Source-Linked Identity Dictionary.
3. **Stage C — Relationships & Epistemic Admission Second:** Construct **Evidence Graph** observations (`ENCLOSES_ROW`, `CHART_CONNECTOR`, `INDENTED_UNDER`, column/branch connectors, callout leaders) and admit **Knowledge Graph** assertions (`CHART_MEMBER_OF`, `CHART_CONNECTED`, `CANDIDATE_LAYOUT_PARENT`) while keeping layout indentation and VLM checks (`knowledge_eligible=false`) strictly out of accepted `IS_A` status.
4. **Stage D — Multihop, Deterministic QA & Real-Entry Preflight Last:** Verify path explanations, cross-chart pointers, and source-limit abstentions via deterministic QA (`0` live LLM calls) and `python -B -m src.evidence_chart_preflight`, then emit a single **Per-Figure Gate Review Packet** (`storage/gate_reviews/gate_<ID>_review_packet.md`) and stop for review.

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
| **Gate 2B** | **`Figure A4` — *Fusion Welding Classification Chart***<br>(First Archetype 2 Calibration Figure) | PDF index 89, viewer p. 90, printed p. 77 | 1. Build the semi-automated **Archetype 2** (`characteristic_decision_tree`) extractor and profile in `src/evidence_chart_contract.json`.<br>2. Extract the 5-column tree (`Energy Source`, `Thermal Source`, `Mechanical Loading` + `*Pressure normal to faying surfaces` footnote, `Shielding`, `Process` circles) and the 23-entry bottom legend table (`CAW` through `TW`), including multi-branch `EGW` and `EBW`.<br>3. Join Figure A3's `Fusion Welding -> See Figure A4` pointer to Figure A4's root.<br>4. Pass 100% of Figure A4 deterministic QA + offline preflight. Stop and emit `gate_2B_review_packet.md`. |
| **Gate 2C** | **`Figure A5` — *Solid-State Welding Classification Chart***<br>(First Test of Semi-Automated Archetype 2 Pipeline) | PDF index 90, viewer p. 91, printed p. 78 | 1. Run the **Archetype 2** semi-automated pipeline from Gate 2B on Figure A5, measuring how much runs without custom code.<br>2. Verify all 5-column paths and the 14-entry bottom legend table (`CEW` through `UW`), preserving multi-branch processes (`HPW`, `DFW`, `FOW`, `ROW`, `CEW`, `IW`).<br>3. Join Figure A3's `Solid-State Welding -> See Figure A5` pointer.<br>4. Pass 100% of Figure A5 deterministic QA + offline preflight. Stop and emit `gate_2C_review_packet.md`. |
| **Gate 2D** | **`Figure A6` — *Brazing and Soldering Classification Chart***<br>(Second Test of Semi-Automated Archetype 2 Pipeline) | PDF index 91, viewer p. 92, printed p. 79 | 1. Run the **Archetype 2** semi-automated pipeline on Figure A6 to confirm repeatable consistency.<br>2. Verify all 5-column paths and the 21-entry bottom legend table, including multi-branch processes (`AB`, `B-CA`, `FB`, `IRB`, `EBB`, `LBB`, `DFB`, `WS`, `DS`, `INS`).<br>3. Explicitly preserve and disambiguate the source anomaly where Figure A6 defines `AB = arc brazing` while Table A1/Figure A1 define `AB = adhesive bonding`.<br>4. Join Figure A3's `Brazing and Soldering -> See Figure A6` pointer. Stop and emit `gate_2D_review_packet.md`. |
| **Gate 2E** | **Normative `Tables A1–A5` Cross-Verification & Join** | PDF indices 81–86, viewer pp. 82–87, printed pp. 69–74 | Bind Tables `A1`–`A5` to the verified `A1`–`A6` figure stores, recording the printed source anomalies (`metal power cutting` for `OC-P` on p. 71; `EW-PC` for `RW-PC` on p. 72; `AHW` asymmetry on p. 72) in the Evidence Graph. Stop and emit `gate_2E_review_packet.md`. |

### Phase 3: Clause 4 Glossary, Dual-Provenance `IS_A` & Annex B Figure-by-Figure Calibration

| Gate ID | Target Scope | Source Coordinates (`AWS A3.0M/A3.0:2020`) | Goal & Verification Criteria |
|---|---|---|---|
| **Gate 3A** | **Clause 4 Glossary + Dual-Provenance `IS_A` Promotion** (+ Annex C/D) | PDF indices 17–79 & 171–182, printed pp. 5–67 & 159–170 | Ingest Clause 4 definitions (boldface standard, lightface nonstandard, italic delimiters, `See Figure/Table` links) and promote `CANDIDATE_LAYOUT_PARENT` edges in `A1`/`A2` to accepted `IS_A_PROCESS_VARIATION_OF` **only where** corroborated by Clause 4 genus-differentia text + Table A1. |
| **Gate 3B** | **Archetype 3 Calibration: `Figure B1` (Single-Page) & `Figure B6` (3-Page Continuation)** | `B1`: printed p. 82 (PDF index 94)<br>`B6`: printed pp. 87–89 (PDF indices 99–101) | Build and verify the semi-automated **Archetype 3** (`spatial_callout_diagram`) pipeline on one single-page figure (`B1` with sub-panels `(A)`–`(E)` and `APPLICABLE WELD TYPES` lists) and one multi-page figure (`B6` across 3 pages `(A)`–`(L)`), then step through `B2`, `B3`, `B4`, `B5` one by one until consistent. |
| **Gate 3C** | **Archetype 4 Calibration: `Figure B49` $\rightarrow$ `Figure B50` $\rightarrow$ `Figure B53`** | Printed pp. 153 & 157 (PDF indices 165 & 169) | Build and verify the semi-automated **Archetype 4** (`cycle_waveform_plot`) pipeline on `B49`, test consistency on `B50` and `B53`, and complete remaining Annex B figures once the pipeline runs cleanly without per-figure patches. |

### Phase 4: Unseen Holdout & AWS Production Acceptance (`Gate 4`)

- Once the figure-by-figure and glossary slices are locked, run **one** frozen unseen benchmark comparing the Deterministic Route, `gemini-3.8-flash`, and AWS `GPT 5.6 Terra` / `Luna`.
