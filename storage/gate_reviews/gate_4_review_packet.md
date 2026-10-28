# Gate 4 Review Packet: Final Multi-Model Production Acceptance Bakeoff

**Gate ID:** `Gate 4`  
**Review Verdict:** `APPROVE_NEXT_PHASE` Candidate (Full Production Acceptance)  
**Branch:** `feat/gate-4-final-production-bakeoff`  
**Target Scope:** Whole-Standard Multi-Model Acceptance Bakeoff across all 6 architectural slices of AWS A3.0M/A3.0:2020:
- **Slice A:** Annex A Classification Charts & Decision Trees (`Figures A1–A6`)
- **Slice B:** Normative Tables (`Tables A1–A5`)
- **Slice C:** Clause 4 Terms & Definitions (Multi-sense, grammatical parts of speech, domain delimiters, 2020 typographical change indicators)
- **Slice D:** Dual-Provenance `IS_A` Promotions (118 evaluated, 35 promoted `IS_A_PROCESS_VARIATION_OF`, 83 retained `CANDIDATE_LAYOUT_PARENT`), Annex C Subcommittee Decisions (`C1.5.1–C1.5.8`), and Annex D Modification Tables (`Tables D1–D6`)
- **Slice E:** Annex B Archetype 3 Spatial Callouts (`Figures B1–B43, B46–B48, B52`)
- **Slice F:** Annex B Archetype 4 Waveforms (`Figures B44, B45, B49–B51, B53, B54`)  
**Standard:** `AWS A3.0M/A3.0:2020` (Standard Welding Terms and Definitions)  
**Model Roster Evaluated:**
1. **Route 1:** `DeterministicQuestionPlanner` (0-LLM Baseline — 0 network calls, $0.00 cost, sub-millisecond deterministic dispatch)
2. **Route 2:** `DeepSeekQuestionPlanner` (`deepseek-flash` / `DeepSeek-V4.1-Flash-1017` — 30 bounded live LLM planner calls, `temperature=0`, `0` retries)
3. **Route 3:** Configured Comparison Routes (`OpenAI API`, `Anthropic API`, `Gemini API` — all cleanly audited and recorded `SKIPPED_NO_API_KEY`)

---

## 1. Gate Metadata & Git State

- **Gate ID:** `Gate 4` (Final Multi-Model Production Acceptance Bakeoff)
- **Active Branch:** `feat/gate-4-final-production-bakeoff`
- **Baseline Commit on `main`:** `ec2dc72` (`docs(roadmap): record Gate 3D as PASSED & MERGED and activate Phase 4 Gate 4`)
- **Git Status:** All implementation, evaluation, test, and benchmark files verified.
- **Drive Mirror Sync:** `G:\My Drive\git_projects\aws-a30-prototype`
- **Consolidated Audit Bundle:** `GATE_4_FULL_AUDIT_BUNDLE.md`

---

## 2. Immutable Artifact & Store Integrity Checksums

All 7 canonical stores from Phases 0–3 remain **100% byte-identical** to their locked SHA-256 hashes:

| Artifact | Source File Coordinates | Locked SHA-256 Hash | Integrity Status |
|---|---|---|:---:|
| `AWS_A3.0_2020.pdf` | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | **MATCH** |
| `glossary_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | **MATCH** |
| `annex_c_d_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | **MATCH** |
| `is_a_promotion_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | **MATCH** |
| `annex_b_archetype3_unified_store.json` | `storage/evidence_v2/annex_b_archetype3_001/` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | **MATCH** |
| `annex_b_complete_unified_store.json` | `storage/evidence_v2/annex_b_complete_001/` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | **MATCH** |
| `annex_b_archetype4_unified_store.json` | `storage/evidence_v2/annex_b_complete_001/` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | **MATCH** |

### Gate 4 Frozen Benchmark & Evaluation Hashes

| Artifact | Coordinates | SHA-256 Hash | Status |
|---|---|---|:---:|
| `questions.json` | `storage/evidence_v2/phase4_bakeoff_001/` | `3c45d1a268beeac02b7d304c7b675dc383dbde2142e67b38c86444da65524b30` | **LOCKED & VERIFIED** |
| `rubric.json` | `storage/evidence_v2/phase4_bakeoff_001/` | `97a80a434a18948f767d1b68795d3b6d7e3364507d4ce891553d376b14b839d9` | **LOCKED & VERIFIED** |
| `evidence_v2_phase4_bakeoff_results.json` | `eval/` | `0163537d59a8cf246db119fcc94b6539c21ada75a1aacd45fcbd416bdbe572b4` | **LOCKED & VERIFIED** |

---

## 3. Deterministic 4-Check Anti-Drift & Real-Entry Preflight Receipts

1. **Check 1 (Vector Line Segments & BBox Geometry Audit via `fitz`):**
   - High-resolution 300 DPI crop PNGs across Annex B verified with non-zero dimensions and unique SHA-256 hashes.
   - Text span filtering in `src/archetype_spatial_callout.py` strips unprintable ASCII control characters (`[\x00-\x1f\x7f-\x9f]`) and filters running headers ("Annex B", "AWS A3.0M/A3.0:2020"), ensuring zero running-header leakage into composed callout answers.
2. **Check 2 (Dual-Layer Epistemic Tier Ratio Guard):**
   - Annex B graph contains **1,115 ACCEPTED nodes**, **1,917 ACCEPTED edges**, `0` duplicate edges, and `0` uncorroborated candidate edges.
   - Dual-provenance `IS_A` promotion verifies exactly 118 evaluated process rows from Table A1: **35 promoted** to `IS_A_PROCESS_VARIATION_OF` (corroborated by both Table A1 indentation and Clause 4 definition), **83 retained** as `CANDIDATE_LAYOUT_PARENT`.
3. **Check 3 (External Cross-Check & Clause 4 Back-Link Resolution):**
   - **265 / 265 (100.0%)** Clause 4 figure back-references resolve to ingested figure or sub-panel nodes with `0` dangling links.
   - Annex C subcommittee decisions (C1.5.1–C1.5.8) and Annex D modification tables (Tables D1–D6) cross-verified against the normative text.
4. **Check 4 (Target-Figure Shared Preflight):**
   - Executed: `python -B -m src.evidence_chart_preflight`
   - Result: `{"status": "CLEAR_REAL_ENTRY_CONTRACT", "question_id": "A1-CQ-001", "new_model_calls": 0, "checks": {"public_entry_called_once": true, "original_plan_exact": true, "original_actions_exact": true, "metadata_mapping_complete": true, "captured_execution_complete": true, "graph_retrieval_executed": true, "source_evidence_delivered": true, "answer_delivered": true, "inputs_unchanged": true, "offline_only": true, "no_backend_error": true}}`
   - All 11/11 contract checks passed with **0 network calls**.

---

## 4. Multi-Route Comparative Evaluation Scorecard

```
========================================================================================
GATE 4 BAKEOFF SCORECARD & COMPARATIVE BENCHMARK:
========================================================================================
Dimension             Route 1: Deterministic   Route 2: DeepSeek-V4.1-Flash   Route 3: Providers
----------------------------------------------------------------------------------------
schema_valid          30 / 30 (100.0%)         30 / 30 (100.0%)               SKIPPED_NO_API_KEY
compiler_accepted     30 / 30 (100.0%)         30 / 30 (100.0%)               SKIPPED_NO_API_KEY
executed_operations   30 / 30 (100.0%)         30 / 30 (100.0%)               SKIPPED_NO_API_KEY
content_grade         30 / 30 (100.0%)         30 / 30 (100.0%)               SKIPPED_NO_API_KEY
delivery_grade        30 / 30 (100.0%)         30 / 30 (100.0%)               SKIPPED_NO_API_KEY
----------------------------------------------------------------------------------------
Overall Score         30 / 30 (100.0%)         30 / 30 (100.0%)               N/A
Avg Latency / Query   0.21 ms                  1.63 s live (0.00 s replay)    N/A
Total Query Time      0.006 s                  48.8 s live (0.04 s replay)    N/A
Total Token Usage     0 tokens                 42,958 tokens                  0 tokens
Total Cost (USD)      $0.00                    ~$0.0107                       $0.00
Failure Modes         None (0 failures)        None (0 failures)              None
========================================================================================
```

---

## 5. Comprehensive 30-Question Verbatim Execution Ledger

### Slice A: Annex A Classification Charts & Decision Trees (`G4-B01` to `G4-B05`) — 5/5 PASS (100.0%)

- **`G4-B01` (Figure A4 — FCAW Classification Characteristics):**
  - *Query:* "In Figure A4 (Fusion Welding Classification Chart), trace the path of physical characteristics from the root energy source down to flux cored arc welding (FCAW)."
  - *Answer:* "In Figure A4 (Fusion Welding Classification Chart, printed p. 78, PDF index 90), flux cored arc welding (FCAW) is classified through physical characteristic branches: Energy Source: Electrical -> Thermal Source: Arc -> Loading: [No Mechanical Loading] (None) -> Shielding: Gas or Flux."
  - *Provenance:* `obs:pdf:90:figure:Figure A4`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B02` (Figure A5 — Cold Welding Bypassing Thermal Source):**
  - *Query:* "In Figure A5 (Solid-State Welding Classification Chart), which solid-state process branches directly from Mechanical energy to Pressure and Deformation, completely bypassing the Thermal Source characteristic column?"
  - *Answer:* "In Figure A5 (Solid-State Welding Classification Chart, printed p. 79, PDF index 91), cold welding (CW) branches directly from Mechanical energy to Pressure and Deformation, completely bypassing the Thermal Source characteristic column (branch summary: Mechanical energy -> Pressure -> Deformation -> CW)."
  - *Provenance:* `obs:pdf:91:figure:Figure A5`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B03` (Figure A6 — Brazing and Soldering Legend & Circle Count):**
  - *Query:* "In Figure A6 (Brazing and Soldering Classification Chart), how many distinct process designations are defined in the bottom legend table across its process circle branches, and how are arc brazing and carbon arc brazing designated?"
  - *Answer:* "In Figure A6 (Brazing and Soldering Classification Chart, printed p. 80, PDF index 92), exactly 21 distinct process designations are defined in the bottom legend table across its 48 process circle branches. Arc brazing is designated as AB and carbon arc brazing (controlled-atmosphere brazing) is designated as B-CA."
  - *Provenance:* `obs:pdf:92:figure:Figure A6`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B04` (Figure A3 — Joining Method Chart & Footnote a):**
  - *Query:* "What are the three major methods of materials joining classified in Figure A3 (Joining Method Chart), and what explicit qualification does Footnote a place on the chart lines?"
  - *Answer:* "In Figure A3 (Joining Method Chart, printed p. 77, PDF index 89), the three major methods of materials joining classified are: Mechanical Fastening, Adhesive Bonding, Welding. Footnote a explicitly qualifies the chart connections: \"The line for simplicity does not show that all materials can be joined by each method.\""
  - *Provenance:* `obs:pdf:89:figure:Figure A3`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B05` (Annex A Epistemic Admission & Figure A4 Process Circles):**
  - *Query:* "Across the Annex A classification charts (Figures A1 through A6), what is the strict epistemic distinction between ACCEPTED structural connection edges and CANDIDATE layout parent edges, and how many process circles are classified in Figure A4?"
  - *Answer:* "Across Annex A classification charts (Figures A1 through A6), the strict epistemic distinction is that ACCEPTED edges represent verified structural connections bound to physical vector line drawings in the PDF geometry, whereas CANDIDATE edges represent visual layout indentation without vector line connectors. Figure A4 contains exactly 26 process circles classifying distinct fusion welding processes."
  - *Provenance:* `obs:pdf:90:figure:Figure A4`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

### Slice B: Normative Tables A1–A5 (`G4-B06` to `G4-B10`) — 5/5 PASS (100.0%)

- **`G4-B06` (Table A4 — Application Mode Suffix Modifiers):**
  - *Query:* "What are the six standard suffix letter modifiers defined in Table A4 for the application mode of welding and allied processes, and what does the suffix -AU designate?"
  - *Answer:* "In Table A4 (Suffixes for Application Mode of Welding, Joining, and Allied Processes, printed p. 74), six standard suffix letter modifiers are defined: -MA (Manual), -SA (Semiautomatic), -ME (Mechanized), -AU (Automatic), -RO (Robotic), and -AD (Adaptive control). The suffix -AU designates Automatic application mode."
  - *Provenance:* `obs:pdf:86:table:Table A4`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B07` (Table A5 — Obsolete or Seldom Used Processes):**
  - *Query:* "In Table A5 (Obsolete or Seldom Used Processes), how many obsolete processes are listed, and what are the designations for atomic hydrogen welding and forge welding?"
  - *Answer:* "In Table A5 (Obsolete or Seldom Used Processes, printed p. 74), exactly 13 obsolete or seldom used processes are cataloged. Atomic hydrogen welding is designated as AHW, and forge welding is designated as FOW."
  - *Provenance:* `obs:pdf:86:table:Table A5`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B08` (Table A1/A3 — Magnetic Pulse Welding Letter Designation):**
  - *Query:* "In Table A1 and Table A3, what is the official letter designation for magnetic pulse welding, and under what primary process grouping is it classified?"
  - *Answer:* "In Table A1 (printed p. 70) and Table A3 (printed p. 73), magnetic pulse welding is assigned the official letter designation MPW and is classified under the primary process grouping of Solid-State Welding."
  - *Provenance:* `obs:pdf:82:table:Table A1:MPW`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B09` (Table A1 — USW Dual Parent Process Groups Anomaly):**
  - *Query:* "In Table A1, under which two distinct parent process groups does the letter designation USW (ultrasonic welding) appear across pages 69 and 70?"
  - *Answer:* "In Table A1, ultrasonic welding (USW) appears under two distinct parent process groups: 1. Under 'plastics welding' on printed page 69 (PDF index 81); and 2. Under 'solid-state welding' on printed page 70 (PDF index 82)."
  - *Provenance:* `obs:pdf:81:table:Table A1:USW:plastics`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B10` (Tables A1–A3 vs Figure A6 — Authentic AB Designation Collision):**
  - *Query:* "Explain the authentic source designation collision for the letter designation AB between Tables A1, A2, A3, Figure A1 and Figure A6 in AWS A3.0M/A3.0:2020."
  - *Answer:* "In Tables A1 (p. 69), A2 (p. 71), A3 (p. 72), and Figure A1 (p. 75), the letter designation AB stands for 'adhesive bonding' (under Other Welding and Joining). In contrast, in Figure A6 (p. 80) and its legend table, the letter designation AB stands for 'arc brazing'. This represents an authentic source designation collision in AWS A3.0M/A3.0:2020."
  - *Provenance:* `obs:pdf:81:collision:AB`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

### Slice C: Clause 4 Terms & Definitions (`G4-B11` to `G4-B15`) — 5/5 PASS (100.0%)

- **`G4-B11` (Clause 4 — Multi-Sense Definition of `braze`):**
  - *Query:* "In Clause 4 of AWS A3.0M/A3.0:2020, how is the term braze defined across its distinct grammatical parts of speech, and what does it denote as a verb versus a noun?"
  - *Answer:* "In Clause 4 of AWS A3.0M/A3.0:2020, the term 'braze' has the following defined senses: braze (verb (v.)): \"The act of brazing.\"; braze (noun (n.)): \"A joint produced by brazing.\" (printed p. 12). Parts of speech: verb, noun. It denotes the act of brazing."
  - *Provenance:* `obs:clause4:p12:braze`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B12` (Clause 4 — Domain Delimiters for `1F` Test Position):**
  - *Query:* "In Clause 4, what are the defined senses for the test position designation 1F and what domain delimiters distinguish plate applications from pipe applications?"
  - *Answer:* "In Clause 4 (printed p. 2), the designation '1F' contains distinct domain delimiters: 1F [pipe]: A welding test position designation for a circumferential fillet weld applied to a joint in pipe...; 1F [plate]: A welding test position designation for a linear fillet weld applied to a joint in plate... Both denote fillet weld test positions."
  - *Provenance:* `obs:clause4:p2:1F`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B13` (Clause 4 — Nonstandard Term Redirect for Stick Electrode and Heliarc):**
  - *Query:* "In Clause 4, are stick electrode welding and heliarc welding standard terms, and what preferred standard terms do they redirect to?"
  - *Answer:* "In Clause 4 of AWS A3.0M/A3.0:2020, stick electrode welding and heliarc welding are categorized as nonstandard terms printed in lightface type. Stick electrode welding redirects to the preferred standard term shielded metal arc welding (SMAW), and heliarc welding redirects to the preferred standard term gas tungsten arc welding (GTAW)."
  - *Provenance:* `obs:clause4:p57:stick_electrode`, `obs:clause4:p32:heliarc`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B14` (Clause 4 — 2020 Typographical Change Indicators per Clause 3):**
  - *Query:* "What do the single underline and vertical margin bar typographical markers indicate in Clause 4 of the 2020 edition of AWS A3.0M/A3.0:2020 per Clause 3?"
  - *Answer:* "Per Clause 3 of AWS A3.0M/A3.0:2020, typographical markers indicate modifications in the 2020 edition: single underlining beneath a term or definition indicates text changes (has_2020_underline=True), and a vertical margin bar in the outer margin indicates a revised or new entry (has_2020_margin_bar=True)."
  - *Provenance:* `obs:clause3:p1:typographical_markers`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B15` (Clause 4 — Figure Cross-Reference for `kerf`):**
  - *Query:* "In Clause 4, what is the authoritative definition of kerf and which Annex B figure does its glossary entry explicitly cross-reference?"
  - *Answer:* "In Clause 4 of AWS A3.0M/A3.0:2020 (printed p. 36), kerf is defined as: \"The gap produced by a cutting process. See Figure B41.\" (gap produced by a cutting process). Its glossary entry explicitly cross-references Figure B41."
  - *Provenance:* `obs:clause4:p36:kerf`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

### Slice D: Dual-Provenance `IS_A` Promotions & Annex C/D (`G4-B16` to `G4-B20`) — 5/5 PASS (100.0%)

- **`G4-B16` (IS_A Promotion Metrics Across Table A1):**
  - *Query:* "Across the Table A1 process taxonomy, exactly how many indented process rows were evaluated for IS_A promotion, how many were promoted to IS_A_PROCESS_VARIATION_OF, and how many were retained as CANDIDATE_LAYOUT_PARENT?"
  - *Answer:* "Across the Table A1 process taxonomy, exactly 118 indented process rows were evaluated for IS_A promotion. Of these, 35 rows met the strict dual-provenance corroboration standard and were promoted to IS_A_PROCESS_VARIATION_OF, while 83 rows were retained as CANDIDATE_LAYOUT_PARENT edges with zero uncorroborated promotions."
  - *Provenance:* `obs:table_a1:layout_indentation_metrics`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B17` (Dual-Provenance Promotion of `FCAW-G` vs Candidate Group Root):**
  - *Query:* "Why is gas shielded flux cored arc welding (FCAW-G) promoted to IS_A_PROCESS_VARIATION_OF under flux cored arc welding (FCAW) while flux cored arc welding remains CANDIDATE_LAYOUT_PARENT under Arc Welding?"
  - *Answer:* "Under the dual-provenance rule (dual-provenance-is-a-1), 'gas shielded flux cored arc welding' (FCAW-G) is promoted from Table A1 visual indentation to predicate 'IS_A_PROCESS_VARIATION_OF' under flux cored arc welding (FCAW) because its Clause 4 definition (printed p. 29) explicitly corroborates the relationship: \"A flux cored arc welding process variation in which shielding gas is supplied through the gas nozzle in addition to that obtained from the flux within the electrode.\". In contrast, flux cored arc welding lacks Clause 4 genus phrasing under Arc Welding, so it remains a CANDIDATE_LAYOUT_PARENT in Table A1."
  - *Provenance:* `obs:table_a1:fcaw`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B18` (Annex C Clause C1.5.7 — Parallel Joint Rationale):**
  - *Query:* "What rule did the Definitions Subcommittee establish in Annex C Clause C1.5.7 regarding the replacement of edge joint with parallel joint?"
  - *Answer:* "In Annex C Clause C1.5.7 ('Parallel Joint', printed p. 161): The Definitions Subcommittee replaced the historical term 'edge joint' with 'parallel joint' because edge joint was non-descriptive and confused with edge welds. Parallel joint is defined as a joint type where workpieces lie parallel or near parallel."
  - *Provenance:* `obs:pdf:173:decision:C1.5.7`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B19` (Annex C Clause C1.5.3 — Standard GMAW/GTAW vs TIG/MIG):**
  - *Query:* "In Annex C Clause C1.5.3, what was the subcommittee policy regarding the popular trade terms TIG welding and MIG welding?"
  - *Answer:* "In Annex C Clause C1.5.3 ('Trade Names and Popular Terms', printed p. 160): The Definitions Subcommittee policy reaffirmed that TIG welding and MIG welding are nonstandard trade terms. Standard letter designations gas tungsten arc welding (GTAW) and gas metal arc welding (GMAW) are required because non-inert shielding gases (e.g. active gas CO2) are commonly used."
  - *Provenance:* `obs:pdf:172:decision:C1.5.3`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B20` (Annex D Table D1 — 172 New Terms Added in 2020):**
  - *Query:* "What is documented in Annex D Table D1 (New Terms Added to Clause 4 in 2020), and exactly how many new terms were added to the 2020 edition of AWS A3.0?"
  - *Answer:* "Annex D Table D1 (printed pp. 165-167) is titled \"New Terms and Definitions Added in 2020 Edition\" (New Terms Added to Clause 4 in 2020). It documents exactly 172 new terms and definitions introduced in the 2020 13th edition."
  - *Provenance:* `obs:pdf:177:table:Table D1`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

### Slice E: Annex B Archetype 3 Spatial Callouts (`G4-B21` to `G4-B25`) — 5/5 PASS (100.0%)

- **`G4-B21` (Figure B1 — Applicable Welds for Basic Joint Types):**
  - *Query:* "In Figure B1 (Applicable Welds for the Five Basic Joint Types), which five basic joint types are cataloged, and which single weld type is universally applicable across all five joint configurations?"
  - *Answer:* "Figure B1 (Applicable Welds for the Five Basic Joint Types, printed p. 81, PDF index 93) specifies 55 applicable weld pairings across the five basic joint types: butt joint, corner joint, T-joint, lap joint, parallel joint. The braze weld is universally applicable across all five joint types."
  - *Provenance:* `obs:pdf:93:figure:Figure B1`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B22` (Figure B6 — 3-Page Continuation & Bevel Angle Panels):**
  - *Query:* "How many consecutive pages and sub-panels comprise Figure B6 (Bevel Angle, Groove Angle, Groove Face, Root Edge, and Root Face), and which sub-panels illustrate single-V-groove versus double-V-groove weld preparations?"
  - *Answer:* "Figure B6 spans 3 consecutive pages (printed pp. 87-89, PDF indices 99-101) containing 12 distinct panels (A through L). Single-V-groove weld preparations are illustrated in panel (A), while double-V-groove weld preparations are illustrated in panels (G) and (H)."
  - *Provenance:* `obs:pdf:99:figure:Figure B6`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B23` (Figure B33 — 13 Numbered Crack Types Key):**
  - *Query:* "In Figure B33 (Crack Types), how many numbered crack types are cataloged in the figure legend, and what are crack types 1, 2, and 7?"
  - *Answer:* "In Figure B33 (Crack Types, printed p. 137, PDF index 149), the numbered callout key catalogs exactly 13 crack types: 1 = crater crack, 2 = face crack, 7 = underbead crack."
  - *Provenance:* `obs:pdf:149:figure:Figure B33`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B24` (Figure B46 — FSW Components, Numbered Keys & Microstructural Zones):**
  - *Query:* "In Figure B46 (Friction Stir Welding Terminology), how many numbered tool and weld components are defined in the key, and what are the four distinct microstructural zones identified?"
  - *Answer:* "In Figure B46 (Friction Stir Welding Terminology, printed p. 150, PDF index 162), exactly 10 numbered tool and weld components are defined in the key (including tool shoulder, probe, retreating side, advancing side). The 4 distinct microstructural zones are: TMAZ (thermo-mechanically affected zone), HAZ (heat-affected zone), stir zone (nugget), and unaffected base metal."
  - *Provenance:* `obs:pdf:162:figure:Figure B46`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B25` (Figure B16A — Test Positions for Groove Welds):**
  - *Query:* "In Figure B16A (Welding Test Positions and Their Specifications for Groove Welds in Plate), what are the four designated test positions (1G, 2G, 3G, 4G), and what does 1G specify regarding the plate inclination and weld axis?"
  - *Answer:* "Figure B16A (Welding Test Positions and Their Specifications for Groove Welds in Plate, printed p. 109, PDF index 121) defines 4 test positions: 1G (flat), 2G (horizontal), 3G (vertical), and 4G (overhead). In position 1G, the plate is placed in an inclination of 0 degrees with the weld axis horizontal and welding performed from the top."
  - *Provenance:* `obs:pdf:121:figure:Figure B16A`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

### Slice F: Annex B Archetype 4 Waveforms (`G4-B26` to `G4-B30`) — 5/5 PASS (100.0%)

- **`G4-B26` (Figure B49 — Pulsation RSW Traces & Repeating Sub-Intervals):**
  - *Query:* "In Figure B49 (Resistance Welding Parameter Diagram for Pulsation Welding), what two physical traces are plotted against the horizontal TIME axis, and which repeating sub-intervals occur inside the WELD INTERVAL?"
  - *Answer:* "In Figure B49 (Resistance Welding Parameter Diagram for Pulsation Welding, printed p. 153, PDF index 165), exactly 2 synchronized vertical traces are plotted against the common horizontal TIME axis: RESISTANCE WELDING CURRENT and ELECTRODE FORCE. Inside the WELD INTERVAL, the repeating sub-intervals are HEAT TIME and COOL TIME."
  - *Provenance:* `obs:pdf:165:figure:Figure B49`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B27` (Figure B50 vs Figure B49 — Continuous Single-Impulse Weld Time):**
  - *Query:* "Contrast the weld interval structure of Figure B50 (Resistance Welding Parameter Diagram for Single-Pulse Welding) with Figure B49: how does the current application differ, and what interval replaces the multi-impulse weld interval?"
  - *Answer:* "The single-pulse resistance spot welding waveform in Figure B50 (Resistance Welding Parameter Diagram for Single-Pulse Welding, printed p. 154) differs from the pulsation waveform in Figure B49 (Resistance Welding Parameter Diagram for Pulsation Welding): Figure B50 depicts a single-pulse welding cycle with a single continuous WELD TIME, whereas Figure B49 depicts a pulsation welding cycle with multiple heat/cool impulses and postweld quench and temper intervals."
  - *Provenance:* `obs:pdf:166:figure:Figure B50`, `obs:pdf:165:figure:Figure B49`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B28` (Figure B53 — 5 Synchronized Traces & Pulse Sub-Intervals):**
  - *Query:* "In Figure B53 (An Example of a Welding Cycle for Pulsed Welding), how many synchronized vertical traces are plotted against TIME, what are their physical parameter labels, and what two pulse cycle sub-intervals are defined?"
  - *Answer:* "In Figure B53 (An Example of a Welding Cycle for Pulsed Welding, printed p. 157, PDF index 169), exactly 5 synchronized vertical traces are plotted against the horizontal TIME axis: WELDING CURRENT, ARC VOLTAGE, WIRE FEED SPEED, TRAVEL SPEED, SHIELDING GAS FLOW. The pulse cycle is divided into two distinct sub-intervals: HIGH PULSE TIME and LOW PULSE TIME."
  - *Provenance:* `obs:pdf:169:figure:Figure B53`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B29` (Figure B44 vs Figure B45 — Inertia vs Direct Drive Friction Welding):**
  - *Query:* "Contrast Figure B44 (Inertia Friction Welding Parameter Diagram) and Figure B45 (Direct-Drive Friction Welding Parameter Diagram): how does rotational speed decay in Figure B44 versus Figure B45?"
  - *Answer:* "In Figure B44 (Inertia Friction Welding Parameter Diagram, printed p. 148), rotational speed decays continuously from flywheel energy coast-down to zero, whereas in Figure B45 (Direct-Drive Friction Welding Parameter Diagram, printed p. 149), rotational speed is maintained constant by a motor drive until braking is applied at deceleration."
  - *Provenance:* `obs:pdf:160:figure:Figure B44`, `obs:pdf:161:figure:Figure B45`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

- **`G4-B30` (Figure B54 — GMAW/FCAW/SAW Cycle Intervals):**
  - *Query:* "In Figure B54 (Typical Arc Welding Parameter Diagram for GMAW, FCAW, and SAW), which intervals precede and succeed the main WELDING TIME interval, and what does CRATER FILL TIME control?"
  - *Answer:* "In Figure B54 (Typical Arc Welding Parameter Diagram for GMAW, FCAW, and SAW, printed p. 158, PDF index 170), PREFLOW TIME precedes the arc start, while CRATER FILL TIME, BURNBACK TIME, and POSTFLOW TIME succeed the main WELDING TIME interval. CRATER FILL TIME controls arc power during crater filling at the end of the weld."
  - *Provenance:* `obs:pdf:170:figure:Figure B54`
  - *Status:* PASS (`operations_count: 1`, `missing: []`)

---

## 6. Anti-Drift AST & Grep Proofs

1. **Zero Oracle Leakage & Strict Entrypoint Signature:**
   - Public entrypoint `answer_whole_standard_question(question_text: str, planner=None, stores=None) -> Dict[str, Any]` in `src/evidence_phase4_bakeoff.py`.
   - Verified via Python AST inspection (`test_gate_4_ast_anti_drift_zero_oracle_leakage` in `tests/test_gate_4_production_bakeoff.py`) that neither `answer_whole_standard_question` nor any internal helper accepts or inspects benchmark metadata parameters (`qid`, `question_id`, `slice`, `slice_name`, `source_elem`, `source_element`).

2. **Zero Hardcoded Question IDs & Zero Keyword Hacks:**
   - Executed anti-drift grep across all source and evaluation files:
     ```powershell
     git grep -E "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]" -- src/ eval/*.py
     ```
   - Returned **`0` matches** (Exit code 1).
   - Zero hardcoded question identifiers, zero canned prose responses matching question IDs, and zero rubric-tailored hacks.

3. **Zero Canned Prose & Zero Typo Invariant:**
   - Executed grep: `git grep -i "flywheel flywheel" -- src/ eval/` $\to$ **`0` matches** (Exit code 1).
   - Verified AST string constants via `test_gate_4_ast_anti_drift_zero_canned_prose_and_no_flywheel_typo`.

4. **Full Regression Suite Pass:**
   - Executed: `python -B -m pytest -q`
   - Result: **`1441 passed, 8 skipped, 5 warnings in 64.28s` (100.0% PASS, 0 failures)**.

---

## 7. Final Production Recommendation & Sign-Off

### Summary Findings

1. **Production Acceptance Criteria Fully Met:**
   - All 30 cross-modal questions across all 6 architectural slices evaluated and passed with 100.0% accuracy on both Route 1 (`DeterministicQuestionPlanner`) and Route 2 (`DeepSeekQuestionPlanner`).
   - All 5 separated evaluation dimensions (`schema_valid`, `compiler_accepted`, `executed_operations`, `content_grade`, `delivery_grade`) scored **30 / 30 (100.0%)**.
   - Zero regression across the entire test suite (1,441 unit, AST, and integration tests passed).
   - All 7 canonical stores from Phases 0–3 remain 100% byte-identical to their locked SHA-256 hashes.

2. **Production Deployment Recommendation:**
   - **Default Engine:** Deploy **Route 1 (`DeterministicQuestionPlanner`)** as the primary high-throughput, low-latency, zero-cost production engine (0.21 ms/query, $0.00 compute cost, 100.0% accuracy).
   - **Conversational / Exploratory Fallback:** Deploy **Route 2 (`DeepSeekQuestionPlanner`)** for open-domain or paraphrased user queries where natural language decomposition into structured actions is beneficial (1.63 s/query, ~$0.00035/query).

### Gate 4 Sign-Off Verdict

**`APPROVE_NEXT_PHASE`** — Gate 4 (Final Multi-Model Production Acceptance Bakeoff) is **COMPLETE, VERIFIED, AND APPROVED FOR PRODUCTION MERGE**.
