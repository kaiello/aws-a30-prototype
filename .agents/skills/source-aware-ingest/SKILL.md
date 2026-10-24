---
name: source-aware-ingest
description: Authoritative 4-archetype ingestion skill for AWS A3.0M/A3.0:2020 multimodal figures, tables, and glossary clauses using the standardized 4-stage pipeline (Manifest Lock, Text First, Relationships Second, QA/Preflight Last). Use when ingesting Figures A1-A6, Tables A1-A5, Clause 4 Glossary, Annex B Figures B1-B54, or Annex C/D.
---
# Source-Aware Ingestion Skill (4-Archetype Pipeline)

Ingest all figures, tables, and glossary definitions of `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 13th Edition, 190 PDF pages) using deterministic provenance, the standardized 4-stage pipeline, and explicit source-anomaly preservation.

## When to Use

- Ingesting Annex A classification charts (Figures A1–A6) and normative tables (Tables A1–A5)
- Ingesting Clause 4 Glossary definitions (printed pp. 5–67) and Annex C/D rationale
- Ingesting Annex B engineering diagrams and cycle waveform plots (Figures B1–B54)
- Mapping any new figure to one of the 4 structural archetypes and verifying pipeline consistency

---

## The 4 Reusable Structural Archetypes

All 66 figures in **AWS A3.0M/A3.0:2020** map to four structural archetypes:

| Archetype ID & Profile | Target Figures | Key Structural Features & Epistemic Rules | Calibration Figures |
|---|---|---|---|
| **Archetype 1:**<br>`box_indentation_chart` | **Figures A1, A2, A3**<br>(printed pp. 75–76) | Enclosing category boxes, undirected connector lines, candidate row indentation (`INDENTED_UNDER`), footnotes (`a`), and explicit cross-chart pointers (`See Figure A4/A5/A6`). Layout indentation remains `CANDIDATE_LAYOUT_PARENT` (`knowledge_eligible=false`) until dual Clause 4 + Table A1 proof closure. | `Figure A1` & `Figure A2` (Calibrated)<br>`Figure A3` (Verified) |
| **Archetype 2:**<br>`characteristic_decision_tree` | **Figures A4, A5, A6**<br>(printed pp. 77–79) | 5-column physical characteristic hierarchy (`Energy Source` $\rightarrow$ `Thermal Source` $\rightarrow$ `Mechanical Loading*` $\rightarrow$ `Shielding` $\rightarrow$ `Process`), `*Pressure normal to faying surfaces.` footnote, bottom designation/process legend table, and multi-branch process nodes. Repeated thermal boxes across parents must be scoped to avoid branch merging. | `Figure A4` (Calibrated)<br>`Figure A5` $\rightarrow$ `Figure A6` (Verification) |
| **Archetype 3:**<br>`spatial_callout_diagram` | **Figures B1–B43, B46–B48**<br>(printed pp. 82–147, 150–152) | Sub-panels `(A)`–`(R)`, dimension arrows, cross-hatch/shaded weld zones, numbered reference callout keys (`B33`, `B46`), applicability tables (`B1`, `B7`, `B16A/B`), and multi-page continuation closure (`B6` across pp. 87–89, `B24` across pp. 117–122). Shading/leader inspection is `knowledge_eligible=false`. | `Figure B1` & `Figure B6` (Phase 3 Calibration) |
| **Archetype 4:**<br>`cycle_waveform_plot` | **Figures B44–B45, B49–B54**<br>(printed pp. 148–149, 153–157) | Time-series horizontal axis (`TIME`), synchronized vertical traces (`CURRENT`, `FORCE`, `VOLTAGE`, `SPEED`), ordered temporal intervals (`squeeze`, `weld`, `hold`, `upslope`, `downslope`), and multi-impulse/temper cycle intervals. | `Figure B49` (Phase 3 Calibration) |

---

## Standardized 4-Stage Figure Pipeline

Every figure runs through the same repeatable sequence:

### Stage A — Manifest & Crop Lock
1. Register `(figure_id, pdf_index, viewer_page, printed_page, crop_box, archetype_profile)` in the curated manifest.
2. Bind the authorized source PDF (`AWS A3.0M/A3.0:2020`, SHA-256 `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`).
3. Render the isolated 300 DPI crop PNG, lock its SHA-256 hash, and verify that adjacent page headers/footers/figures cannot leak in.

### Stage B — Text, Footnotes & Legend Table First
1. Extract native PDF text/vector geometry (with bounded OCR fallback where rasterized).
2. Resolve every printed label, designation acronym, footnote, and legend row against the Source-Linked Identity Dictionary.
3. Prevent column x-offsets from being misparsed as hierarchy indentation.

### Stage C — Relationships & Epistemic Admission Second
1. Construct **Evidence Graph** observations (`ENCLOSES_ROW`, `CHART_CONNECTOR`, `INDENTED_UNDER`, column connectors, callout leaders).
2. Construct **Knowledge Graph** assertions (`CHART_MEMBER_OF`, `CHART_CONNECTED`, `CANDIDATE_LAYOUT_PARENT`).
3. **Strict Epistemic Rule:** Keep candidate layout edges and VLM observations (`knowledge_eligible=false`) strictly out of `IS_A`. Promoted `IS_A_PROCESS_VARIATION_OF` edges require dual Clause 4 Glossary genus-differentia text + Table A1 proof closure.
4. Join cross-chart incoming pointers (e.g., `Figure A3 -> See Figure A4/A5/A6`) to the respective classification chart roots.

### Stage D — Multihop, Deterministic QA & Preflight Last
1. Execute deterministic Graph QA benchmark (`0` live LLM calls) covering taxonomy paths, multi-branch processes, source anomalies, and explicit source-limit abstentions.
2. Run offline real-entry preflight: `python -B -m src.evidence_chart_preflight` (requiring 0 network attempts and `CLEAR_REAL_ENTRY_CONTRACT`).
3. Generate the self-contained Gate Review Packet (`storage/gate_reviews/gate_<ID>_review_packet.md`) using `aws-a30-gate-review` and stop.

---

## The Consistency Criterion for Acceleration

Stay in **strict single-figure stop-and-review mode** (`Figure A3` $\rightarrow$ `Figure A4` $\rightarrow$ `Figure A5` $\rightarrow$ `Figure A6`) until **two consecutive figures of the same structural archetype** pass Stages A–D on the first pass with **zero custom extractor patches or compiler regressions**. Only after an archetype's semi-automated pipeline proves consistent across consecutive single figures may subsequent figures of that archetype be batched.

---

## Source Anomalies Catalog (Preserve Authentically)

Discrepancies in `AWS A3.0M/A3.0:2020` must be preserved as literal source evidence; never silently "correct" them:
- **Figure A4 (p. 77):** `AHW` appears as a circle under `Electrical -> Arc -> Gas` but is omitted from the bottom 23-entry legend table. `Conduction` under `Electrical` has no outgoing right-hand branch.
- **Figure A5 (p. 78):** `Mechanical -> [No Thermal Box] -> Pressure Deformation -> [No Shielding] -> CW` skips the Thermal Source column. `Radiation` appears under both `Electrical` and `Chemical` and must be disambiguated.
- **Figure A6 (p. 79):** Defines `AB = arc brazing`, whereas Table A1 (p. 69), Table A2 (p. 71), Table A3 (p. 72), Figure A1 (p. 75), and Clause 4 (p. 7) assign `AB = adhesive bonding`.
- **Table A2 (p. 71):** Prints `metal power cutting` for `OC-P` (canonical: `metal powder cutting`).
- **Table A2 (p. 72):** Prints `EW-PC` for `pressure-controlled resistance welding` (canonical: `RW-PC`).
- **Figure A1 Footer (p. 75):** Embedded chart graphic retains legacy note `A3.1:2010` inside the 2020 edition page.
