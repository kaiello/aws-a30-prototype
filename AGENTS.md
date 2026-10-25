# Gemini 3.8 Flash Lead Developer Handoff & Onboarding Guide (`GEMINI.md` / `AGENTS.md`)

**Prepared For:** `gemini-3.8-flash` (Lead Developing Agent)  
**Project Owner:** Kenneth Aiello  
**Handoff Snapshot:** 23 October 2026  
**Repository:** [kaiello/aws-a30-prototype](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype) (`C:\Users\kenai\aws-a30-prototype`)  

Drop this file into the repository root as `GEMINI.md` (and/or `AGENTS.md`) to initialize **Gemini 3.8 Flash** with complete operational context, exact branch/commit state, module map, evaluation ledger, and known source anomalies across **AWS A3.0M/A3.0:2020**.

## 1. System Prompt & Role Definition for Gemini 3.8 Flash

> You are **Gemini 3.8 Flash**, operating as the **Lead Developing Agent** for the `aws-a30-prototype` repository—an epistemically rigorous Multimodal RAG and Knowledge Graph backend over **AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions*, 190 PDF pages)**.
>
> Your predecessor agents built and verified a deterministic backend for **Figure A1** (*Master Chart of Welding and Joining Processes*) and **Figure A2** (*Master Chart of Allied Processes*), merged to [main (71088cebc9eb3b2556d7bbe73a23a451e645e3b9)](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/commit/71088cebc9eb3b2556d7bbe73a23a451e645e3b9) via [PR12](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/12), and completed two local diagnostic/prevention slices (`feat/a1-a2-relationship-readiness` at `bc51eae458e59764d6879ef175933aea4db7480e` and `feat/planner-contract-preflight`).
>
> **Your Mandate:**
> 1. Protect the working deterministic backend and epistemic data model (SQLite-backed **Evidence Graph** + **Knowledge Graph** + **Source-Linked Identity Dictionary**).
> 2. Resolve the natural-language planner/compiler boundary so compound questions decompose into complete, executable retrieval plans without pre-retrieval contract rejections or dropped sub-parts.
> 3. Systematically expand source-aware multimodal ingestion across the rest of **AWS A3.0M/A3.0:2020** (**Figure A3**, **Classification Charts A4–A6**, **Tables A1–A5**, **Clause 4 Glossary**, **Annex B Figures B1–B54**, and **Annex C/D**), using Clause 4 Glossary definitions + Table A1 to unlock dual-provenance accepted `IS_A` assertions.
> 4. Obey all stop conditions: never run unapproved live LLM inference loops, never rebuild OCR to mask planner/compiler bugs, never overwrite historical run receipts, and always run `python -m src.evidence_chart_preflight` offline before any live planner run.

## 2. Exact Git, Branch & Artifact State at Takeover

| Item | Exact Value / Identifier | Status & Rules |
|---|---|---|
| **Source PDF** | `AWS A3.0MA3 - Standard Welding Terms and Definitions.pdf` (190 pages) | SHA-256: `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` (Immutable) |
| **Figure A1 Store** | PDF index 87, viewer p. 88, printed p. 75 (`parsed/figures/Figure_A1_p88.png`) | **287 accepted / 29 candidate assertions**; 0 accepted `IS_A` assertions. Store SHA-256: `6476c898439108dbeaf7b92f0be3946a3e0d3538d5c15afb860d1cf0e02cc4d2` |
| **Figure A2 Store** | PDF index 88, viewer p. 89, printed p. 76, crop `[0.075, 0.10, 0.45, 0.89]` | **112 accepted / 12 candidate assertions**; 31 process rows, 5 category boxes + 1 root, 31 enclosure edges, 6 physical connectors, 12 candidate indentation edges. Crop SHA-256: `e792b09ccb9896e9dc1eb908883bcf876bb790ef19150a8d226f2e7e6b2ec908` |
| **Merged `main`** | [71088cebc9eb3b2556d7bbe73a23a451e645e3b9](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/commit/71088cebc9eb3b2556d7bbe73a23a451e645e3b9) ([PR12](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/12)) | **Stable Deployable Baseline.** 398 software checks passing; deterministic route is default. Do not force-push or merge unverified planner branches into `main`. |
| **Predecessor `main`** | `2d7b73813228c1cd6f907ca014a23693a888de81` ([PR11](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/11)) | Historical A1 source-aware ingestion milestone. |
| **Earlier Milestones** | [PR8](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/8) (Bakeoff docs), [PR9](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/9) (Faithful relationships), [PR10](https://www.google.com/search?q=https://github.com/kaiello/aws-a30-prototype/pull/10) (A1 NLQ completeness), `v1.0` tag (`24bac454`) | Preserved historical milestones. |
| **Repair Branch** | `feat/a1-a2-relationship-readiness` at `bc51eae458e59764d6879ef175933aea4db7480e` | Local checkpoint containing `relationship_readiness_001`, `question_interface_002`, `003`, and repaired replay `004` (`chart-plan-contract-1.2`, harness `a1-graph-qa-1.7.7`). Not pushed or merged. |
| **Prevention Branch** | `feat/planner-contract-preflight` (branched from `bc51eae`) | Contains uncommitted local edits: `src/evidence_chart_preflight.py`, `.agents/skills/planner-contract-release/SKILL.md`, and `branch_handoff.md`. **Immediate Task:** Run offline A1 preflight and commit on this branch. |

## 3. Core Codebase & Contract Map

When navigating the repository, pay special attention to the contract boundary between these modules:

* **`src/evidence_chart_contract.json`**: Shared declarative contract defining action names (`lookup_term`, `list_members`, `check_relationship`, `explain_path`), allowed parameters, scopes, modes, structural JSON schema, and compiler allowlists (currently at `chart-plan-contract-1.2`).
* **`src/evidence_chart_question_plan.py`**: High-level question-plan parser, schema validator, and lowering adapter (`LocalQuestionPlanner`).
  * *Historical bug at lines 67 & 301 (fixed in `004`):* Allowed bounded `part.reason` strings from the LLM and forwarded them raw into the lower-level operation plan. In `chart-plan-contract-1.2`, `part.reason` is validated for type/length, preserved in trace metadata as `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`, and mapped to `PLANNED_REASON` (`""`) for planned internal operations while unresolved explanations pass through unchanged.
* **`src/evidence_chart_llm_plan.py`**: Low-level typed operation compiler and validator (line 409 enforces internal `PLANNED_REASON` invariants, role cardinality, budget limits, dependency DAGs, and source/edition bindings).
* **`src/evidence_chart_preflight.py`**: Offline real-entry preflight runner added on `feat/planner-contract-preflight`. Exercises `LocalQuestionPlanner.__call__` through the real adapter, compiler, graph executor, and composer with network blocked.
* **`src/evidence_a1_graph_qa.py` & `src/evidence_a1_cli.py`**: Canonical graph QA engine and CLI (`--graph-qa`) for Figure A1 (with parallel canonical entry points for Figure A2).

## 4. Authoritative Evaluation Ledger & What Remains to Fix in A1/A2

Do not rely on outdated top-of-file notes in legacy markdown files. The table below is the ground-truth evaluation record for the 67-question A1/A2 suite (**51 A1 + 16 A2 questions**):

| Run ID | Mode | A1 (51 Qs) | A2 (16 Qs) | Takeaway for Gemini 3.8 Flash |
|---|---|---|---|---|
| **`a2_planner_009` (Closeout)** | Cached `005` plans + deterministic backend support | **51 PASS** (3 clarifications) | **16 PASS** | Proves backend data, graph executor, and answer composer can satisfy all 67 questions. |
| **`relationship_readiness_001`** | **67 fresh LLM calls** (earlier typed schema) | **46 PASS / 4 PARTIAL / 1 UNASSESSED** | **16 PASS** | **Best Fresh NLQ Baseline.** Only 5 A1 questions missed (`A1-QA002-10`, `-13`, `-14`, `A1-HO002-01`, `-05`). |
| **`question_interface_002`** | Offline replay + 6 manual action checks (`reason=""`) | 5/5 A1 manual checks pass | 1/1 A2 manual check passes | Proves the 4-action adapter works on ideal hand-crafted inputs, but missed the nonempty `part.reason` bug. |
| **`question_interface_003`** | **67 fresh LLM calls** (4-action schema `1.1`) | **1 PASS / 50 UNDELIVERED** | **16 UNDELIVERED** | 66 plans rejected at `evidence_chart_llm_plan.py:409` due to nonempty `part.reason`. Zero graph ops ran. |
| **`question_interface_004`** | **Offline replay of unchanged `003` outputs** (`contract-1.2`) | **35 PASS / 10 PARTIAL / 6 UNASSESSED** | **9 PASS / 4 PARTIAL / 3 UNASSESSED** | Fixed the metadata rejection (114 executed ops, 49 blocked ops), proving the `003` 4-action plans are semantically worse than `001`. |

### Exact Root Causes of the 5 A1 Misses in `relationship_readiness_001`

When executing **Phase 1**, ensure your planner/adapter/composer fixes resolve these five exact cases without hardcoding question IDs:

1. **`A1-QA002-10` (*Friction stir welding hierarchy*):** In Figure A1 (p. 75), `friction stir welding` (`FSW`) is enclosed inside `SOLID-STATE WELDING (SSW)` **and** indented under `friction welding` (`FRW`). The planner/composer returned the category box (`SSW`) but omitted the immediate candidate layout parent (`FRW`).
2. **`A1-QA002-13` (*Carbon arc brazing vs. carbon arc welding*):** `carbon arc brazing` (`CAB`) is under `BRAZING (B)`, whereas `carbon arc welding` (`CAW`) is under `ARC WELDING (AW)`. The system must state the explicit negative subtype verdict (`CAB` is not a subtype of `CAW`) alongside both placements.
3. **`A1-QA002-14` (*Induction welding vs. induction soldering*):** `induction welding` (`IW`) is under `OTHER WELDING AND JOINING` (and `high-frequency` / `induction` under `upset welding` / `resistance seam welding` in `RW`), whereas `induction soldering` (`IS`) is under `SOLDERING (S)`. A physical path through the `WELDING AND JOINING PROCESSES` root does not make one a subtype of the other; both placements and the explicit negative verdict must be delivered.
4. **`A1-HO002-01` (*OAW lookup*):** `oxyacetylene welding` (`OAW`) is explicitly present under `OXYFUEL GAS WELDING (OFW)` in Figure A1 (p. 75), Table A1 (p. 69), Table A2 (p. 71), Table A3 (p. 73), and Clause 4 (p. 41). The planner falsely marked the lookup unresolved.
5. **`A1-HO002-05` (*PAW full name + operating voltage*):** `plasma arc welding` (`PAW`) is under `ARC WELDING (AW)` in Figure A1 (p. 75). The planner looked up `PAW` but dropped the second part of the user's question (voltage), failing to state that Figure A1 / AWS A3.0 does not specify operating voltage schedules.

## 5. Comprehensive Guide to `AWS A3.0M/A3.0:2020` Structure & Source Anomalies

As you expand ingestion in **Phases 2 and 3**, use this exact structural map and anomaly registry derived directly from inspecting the 190-page `AWS A3.0M/A3.0:2020` PDF:

### Page Coordinate Conversion Table

Always record all three page numbers in manifest and evidence records (`viewer_page = pdf_index + 1`):

| Section / Element | PDF Index (0-based) | Viewer Page (1-based) | Printed Page | Notes & Crop / Continuation Details |
|---|---|---|---|---|
| **Title, Copyright, Statement, Personnel, Foreword, TOC, List of Tables/Figures** | 0–12 | 1–13 | i–xii | Foreword (pp. vii–viii) explains 2020 underline/margin-bar markup and states Annex B figures are examples only. |
| **Clause 1 (General Requirements), Clause 2 (Normative References), Clause 3 (Terms & Definitions)** | 13–16 | 14–17 | 1–4 | Clause 1.1 defines **boldface** = standard term, lightface = nonstandard term, single margin bar = minor revision, double margin bar = new term or major change. |
| **Clause 4: Glossary (`1F, pipe` through `wormhole porosity`)** | 17–79 | 18–80 | 5–67 | Page 80 (PDF index 80, printed p. 68) is intentionally blank. |
| **Annex A: Table A1 (*Letter Designations by Process Group*)** | 81–82 | 82–83 | 69–70 | 2-page normative table with indented sub-processes matching Figure A1/A2 groups. |
| **Annex A: Table A2 (*Alphabetical Cross-Reference by Process*)** | 83–84 | 84–85 (top) | 71–72 (top) | 133 process rows. Contains 2 source typos (`metal power cutting`, `EW-PC`). |
| **Annex A: Table A3 (*Alphabetical Cross-Reference by Letter Designation*)** | 84–85 | 85 (bottom)–86 | 72 (bottom)–73 | 134 designation rows (includes `AHW` = `atomic hydrogen welding`, which is omitted from Table A1/A2 and listed in Table A5/Figure A1). |
| **Annex A: Table A4 (*Application Mode Suffixes*) & Table A5 (*Obsolete or Seldom Used Processes*)** | 86 | 87 | 74 | Table A4 defines `-AD`, `-AU`, `-MA`, `-ME`, `-RO`, `-SA`. Table A5 lists 13 obsolete processes (`firecracker welding` has no letter designation). |
| **Annex A: Figure A1 (*Master Chart of Welding and Joining Processes*)** | 87 | 88 | 75 | Full-page chart: root `WELDING AND JOINING PROCESSES` + 8 category boxes. |
| **Annex A: Figure A2 (*Master Chart of Allied Processes*)** | 88 | 89 (top) | 76 (top) | Normalized crop `[0.075, 0.10, 0.45, 0.89]`: root `ALLIED PROCESSES` + 5 category boxes (`TG`, `THSP`, `TC`, `OC`, `HEBC`, `AC`). |
| **Annex A: Figure A3 (*Joining Method Chart*)** | 88 | 89 (bottom) | 76 (bottom) | Lower half of printed p. 76, including footnote `a`. Bridges to Figures A4, A5, A6. |
| **Annex A: Figure A4 (*Fusion Welding Classification Chart*)** | 89 | 90 | 77 | 5-column characteristic tree + 23-entry bottom legend table. |
| **Annex A: Figure A5 (*Solid-State Welding Classification Chart*)** | 90 | 91 | 78 | 5-column characteristic tree + 14-entry bottom legend table. |
| **Annex A: Figure A6 (*Brazing and Soldering Classification Chart*)** | 91 | 92 | 79 | 5-column characteristic tree + 21-entry bottom legend table. Page 80 (PDF index 92) is blank. |
| **Annex B: Figures B1–B54 (*Engineering Diagrams*)** | 93–169 | 94–170 | 81–157 | 60 figures (B1–B15, B16A, B16B, B16C, B17–B54). Page 158 (PDF index 170) is blank. |
| **Annex C (Informative): *Principles of A3.0M/A3.0 Style*** | 171–176 | 172–177 | 159–164 | Selection/formatting rules (C1–C2) and Subcommittee decisions (C1.5.1–C1.5.8, C2.4.1). |
| **Annex D (Informative): *Modifications from A3.0M/A3.0:2010*** | 177–182 | 178–183 | 165–170 | Tables D1 (New), D2 (Modified), D3 (Editorial), D4 (Standard$\rightarrow$Nonstandard), D5 (Nonstandard$\rightarrow$Standard), D6 (Deleted). |
| **Annex E (Other Sources), Annex F (Official Interpretations), List of AWS Documents** | 183–187 | 184–188 | 171–175 | Pages 172 and 176 (PDF indices 184 and 188) are blank; PDF index 189 is back cover. |

### Known Source Anomalies in `AWS A3.0M/A3.0:2020` (Must Be Preserved in Evidence Graph)

1. **Table A2 Typo (`metal power cutting`, printed p. 71, PDF index 83):** Table A2 prints `metal power cutting | OC-P`, whereas Table A1 (p. 70), Table A3 (p. 73), Figure A2 (p. 76), and Clause 4 (p. 39) print `metal powder cutting (OC-P)`.
2. **Table A2 Typo (`EW-PC`, printed p. 72, PDF index 84):** Table A2 prints `pressure-controlled resistance welding | EW-PC`, whereas Table A1 (p. 70), Table A3 (p. 73), Figure A1 (p. 75), and Clause 4 (p. 45) print `RW-PC`.
3. **Table A3 vs. Table A1/A2 Asymmetry (`AHW`, printed p. 72, PDF index 84):** `AHW` (`atomic hydrogen welding`) appears in Table A3 (p. 72), Table A5 (p. 74, obsolete), Figure A1 (p. 75, under `ARC WELDING`), Figure A4 (p. 77), and Clause 4 (p. 9), but is omitted from Table A1 and Table A2.
4. **Figure A6 `AB` Collision (`arc brazing` vs. `adhesive bonding`, printed p. 79, PDF index 91):** Figure A6's chart and bottom legend define `AB` as `arc brazing`, whereas Table A1 (p. 69), Table A2 (p. 71), Table A3 (p. 72), Figure A1 (p. 75), and Clause 4 (p. 7) define `AB` as `adhesive bonding` (and Clause 4 p. 22 lists `electric brazing` as a nonstandard term for `arc brazing and resistance brazing`, while defining `arc braze welding (ABW)` on p. 8). Bind `AB` with figure-scoped disambiguation so Figure A6 queries and Table A1/Figure A1 queries each report the exact source fact and note the cross-figure collision.
5. **Annex B Normative vs. Informative Conflict:** The Table of Contents (printed p. ix, PDF index 9) lists `Annex B (Informative)—Figures` and the Foreword (printed p. viii, PDF index 8) states Annex B figures are examples only, whereas the Annex B title page (printed p. 81, PDF index 93) prints `Annex B (Normative) Figures — This annex is part of this standard and includes mandatory elements for use with this standard`. Retain both locators as conflicting source metadata.
