# Gate 3C Review Packet: Archetype 4 Waveform Calibration (`Figures B49`, `B50`, `B53`) & Complete Annex B Ingestion (`Figures B1–B54`)

**Gate ID:** `Gate 3C`  
**Review Verdict:** `APPROVE_NEXT_PHASE` Candidate (Repaired)  
**Branch:** `feat/gate-3c-annex-b-archetype4-and-remaining`  
**Target Scope:** `Figure B49` $\rightarrow$ `Figure B50` $\rightarrow$ `Figure B53` + Remaining Annex B Figures (`Figures B7–B54`, printed pp. 90–157, PDF indices 102–169)  
**Standard:** `AWS A3.0M/A3.0:2020` (Terms and Definitions)  
**Live LLM Calls:** `0` (100% deterministic offline ingestion, vector parsing, waveform sequencing, high-resolution rendering, and testing)

---

## 1. Executive Summary & Audit Scorecard

Gate 3C completes Phase 3 of the AWS A3.0 knowledge ingestion pipeline:
1. **Archetype 4 (`cycle_waveform_plot`):** Full calibration across `Figure B49`, `Figure B50`, and `Figure B53` (and remaining waveform figures `B44`, `B45`, `B51`, `B54`), binding horizontal `TIME` axes, synchronized traces, sequential temporal intervals (`TEMPORAL_PRECEDES`), hierarchical sub-intervals (`SUB_INTERVAL_OF`), modulated parameters, and live PyMuPDF text span bounding boxes.
2. **Archetype 3 (`spatial_callout_diagram`):** Ingestion of all remaining figures in **Annex B (`Figures B7–B43`, `B46–B48`, `B52`)**, completely eliminating all placeholder strings (`Panel (A)`) in favor of genuine PyMuPDF callouts, completed sub-panel sequences, numbered key legends (`Figure B33` and `Figure B46`), and embedded tables (`Figures B7, B16A, B16B, B16C, B47, B48`).
3. **High-Resolution 300 DPI Raster Crops:** All 80 crop PNGs rendered at genuine page dimensions (`width >= 1000px`, `height >= 800px`, `size >= 10,000` bytes, range: `82,293` to `483,367` bytes) with 80 unique SHA-256 hashes (zero blank squares).
4. **Graph Epistemic Admission:** All **54 standard figures (56 figure units)** across Annex B (printed pp. 82–157, PDF indices 94–169) are admitted with **0 duplicate edges**, **0 uncorroborated candidate entities**, and **100% resolution of all 265 Clause 4 figure back-links**.

| Audit Dimension | Requirement | Gate 3C Result | Status |
|---|---|---|---|
| **1. Archetype 4 Calibration** | Calibrate `B49` $\rightarrow$ `B50` $\rightarrow$ `B53` + `B44, B45, B51, B54` with `TIME` axis, synchronized traces, intervals, and text span bbox bindings | Ingested all 7 waveform figures; extracted 100% vector drawings; verified `TEMPORAL_PRECEDES` order, `SUB_INTERVAL_OF`, and span bbox bindings (`matched_pdf_spans_count`) | **PASS** |
| **2. Complete Annex B Coverage** | Ingest all remaining figures (`B7–B43, B46–B48, B52`), multi-page continuations, embedded tables, and numbered keys | All 56 figures ingested across 76 printed pages; 13 multi-page continuations verified; 80 300 DPI high-res crops on disk | **PASS** |
| **3. High-Resolution Crops** | All crop PNGs must be genuine 300 DPI renders: `width >= 1000`, `height >= 800`, `size >= 10,000` bytes, unique hashes | 80/80 crops verified: `min_size = 82,293` bytes, `max_size = 483,367` bytes, 80 unique SHA-256 hashes | **PASS** |
| **4. Genuine Callouts & Legends** | 0 dummy `Panel (A)` placeholders; completed sequences for B12, B15, B20, B21, B30, B32, B37, B40; B33 crack keys; B46 FSW keys/zones | 0 dummy strings; B33 has 13 crack keys; B46 has 10 keys + zones; B7/B16/B47/B48 have table/circuit callouts; B17 title cleaned | **PASS** |
| **5. Dual-Layer Admission** | `ACCEPTED > 0`, `CANDIDATE == 0`, `0` duplicate edges `(source, target, edge_type, observation_id)` | **1,115 ACCEPTED nodes**, **1,917 ACCEPTED edges**, `0` CANDIDATE, **0 duplicate edges** across all 56 stores | **PASS** |
| **6. Clause 4 Back-Link Coverage** | 100% of Annex B figure references in `glossary_store.json` resolve to an ingested figure or sub-panel node | **265 / 265 unique references resolved (100.0%)**, `0` unresolved references | **PASS** |
| **7. Testing & Anti-Drift** | Tier 1 property tests + Tier 2 AST / dynamic QA composer; full repository pytest suite; preflight check; 0 hardcoded IDs | **10/10** Gate 3C tests PASS; **1,429/1,429** full pytest suite PASS; `CLEAR_REAL_ENTRY_CONTRACT` (11/11); `0` grep matches | **PASS** |

---

## 2. Locked SHA-256 Provenance & File Coordinates

| Artifact | Source Coordinates | SHA-256 Hash |
|---|---|---|
| `annex_b_complete_unified_store.json` | Annex B unified manifest (all 56 figures) | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` |
| `annex_b_archetype4_unified_store.json` | Archetype 4 unified store (7 waveform figures) | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` |
| `figure_b7_store.json` | Printed p. 90, PDF index 102 | `b3272ac824e0fdeea77511428863045176279935f95aab0eef24521ae6a1e685` |
| `figure_b12_store.json` | Printed p. 98, PDF index 110 | `7642ea0382db202be0fd48a2bc961f74f642a188a4c9622fb852cb16d469d822` |
| `figure_b16a_store.json` | Printed p. 102, PDF index 114 | `e11e03e13c21ffb8f4b5bf8d77a569249e118e649b0a536aefd582d15763fc73` |
| `figure_b20_store.json` | Printed pp. 110–111, PDF indices 122–123 | `395ff6a7eef515ff44d95e7f98ecbdc8cd276a3df00bc66215206a43231a5236` |
| `figure_b30_store.json` | Printed pp. 133–134, PDF indices 145–146 | `1a623dce538470141a3d6484f25603503425b3440169ab9a774fac8000506065` |
| `figure_b32_store.json` | Printed pp. 136–138, PDF indices 148–150 | `d0ccd54cfbf3306499fe12bd427f838c1a7ff34d109c1dbdf425de4adbc9586c` |
| `figure_b33_store.json` | Printed p. 139, PDF index 151 | `8781a4c5627d0735432076b3e915e38726364ab83068f525434d78ddf3e88e61` |
| `figure_b46_store.json` | Printed p. 150, PDF index 162 | `67b8c92f6d69da70bb1bfaba3009e9310d0b7cb21d3b44dce7c17295eef4af81` |
| `figure_b47_store.json` | Printed p. 151, PDF index 163 | `0ef48e8c21e6c050f71a15fd46275f8d12afb38e7c3c828c757347e33869c7b0` |
| `figure_b48_store.json` | Printed p. 152, PDF index 164 | `0850d0c6ab36be7f2200334ba42b6c564225363c03e354b76fa25a7e677dd3f8` |
| `figure_b49_store.json` | Printed p. 153, PDF index 165 | `0c7d41cfa4baa66a7f0e0b14167f65a180105bf534d9df2a315470e06925d607` |
| `figure_b50_store.json` | Printed p. 153, PDF index 165 | `61a691fcd85c2142be9843462429c3260d2a759946431a9182a80422d1be90aa` |
| `figure_b53_store.json` | Printed p. 157, PDF index 169 | `b26e91c3c6bfd029f6596a294505c3e1e8e8caed00d5708d25002b0cf452e6fd` |
| `glossary_store.json` | Printed pp. 5–67, PDF indices 17–79 | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` |

---

## 3. Quantitative Scorecard & Metrics

```
Annex B Complete Corpus:
├── Total Figures Ingested: 56 (54 standard figures + B16A, B16B, B16C)
│   ├── Archetype 3 (Spatial Callout / Tabular): 49 figures
│   └── Archetype 4 (Cycle Waveform Plot): 7 figures
├── Total Printed Pages: 76 (printed pp. 82–157, viewer pp. 83–158, PDF indices 94–169)
├── 300 DPI Raster Crop PNGs: 80 files on disk
│   ├── Width: >= 1000 px on all 80 crops (typical: 2287–2295 px)
│   ├── Height: >= 800 px on all 80 crops (typical: 1350–2970 px)
│   ├── File Size: >= 10,000 bytes on all 80 crops (min: 82,293 B, max: 483,367 B)
│   └── Unique SHA-256 Hashes: 80 / 80 unique (0 duplicate hash sets)
├── Vector Drawings / Lines / Curves:
│   └── Figures with > 0 Vector Drawings / Lines / Curves: 56 / 56 (100.0%)
├── Graph Epistemic Admission:
│   ├── ACCEPTED Nodes: 1,115
│   ├── ACCEPTED Edges: 1,917
│   ├── CANDIDATE Nodes: 0
│   ├── CANDIDATE Edges: 0
│   └── Duplicate Edges: 0
└── Cross-Clause Normative Joins:
    ├── Clause 4 Figure References Tested: 265
    ├── Successfully Resolved: 265 (100.0%)
    └── Unresolved: 0 (0.0%)
```

---

## 4. Part 1: Archetype 4 (`cycle_waveform_plot`) Calibration Details

### 1. `Figure B49` — Pulsation Welding Waveform (Resistance Spot Welding)
- **Source Coordinates:** Printed p. 153, PDF index 165 (top partition: `[0.05, 0.05, 0.48, 0.95]`)
- **Metrics:** 41 ACCEPTED nodes, 65 ACCEPTED edges, 0 duplicate edges, 18 joined Clause 4 terms.
- **Horizontal Time Axis:** `TIME` (`TIME_AXIS` node connected to figure root).
- **Synchronized Vertical Traces:**
  1. `RESISTANCE WELDING CURRENT` (Electric Current, Amperes)
  2. `ELECTRODE FORCE` (Force, Newtons / Pounds-force)
- **Sequential Temporal Intervals (`TEMPORAL_PRECEDES`):**
  `SQUEEZE TIME` $\rightarrow$ `PREHEAT TIME` $\rightarrow$ `UPSLOPE TIME` $\rightarrow$ `WELD INTERVAL` $\rightarrow$ `DOWNSLOPE TIME` $\rightarrow$ `QUENCH TIME` $\rightarrow$ `TEMPER TIME` $\rightarrow$ `HOLD TIME` $\rightarrow$ `OFF TIME`.
- **Sub-Intervals (`SUB_INTERVAL_OF`):**
  `HEAT TIME` $\subset$ `WELD INTERVAL` and `COOL TIME` $\subset$ `WELD INTERVAL`.
- **Modulated Parameters:** `PREHEAT CURRENT`, `UPSLOPE CURRENT`, `WELDING CURRENT`, `DOWNSLOPE CURRENT`, `TEMPER CURRENT`.
- **Compound Intervals:** `POSTWELD INTERVAL` (subsumes quench, temper, hold), `FORGE-DELAY TIME`, `WELDING CYCLE`.
- **PyMuPDF Bbox Binding:** Live spans bound with `matched_pdf_spans_count` and `matched_spans` on all traces, intervals, and parameters.

### 2. `Figure B50` — Single-Pulse Resistance Spot Welding Waveform
- **Source Coordinates:** Printed p. 153, PDF index 165 (bottom partition: `[0.48, 0.05, 0.95, 0.95]`)
- **Metrics:** 21 ACCEPTED nodes, 29 ACCEPTED edges, 0 duplicate edges, 9 joined Clause 4 terms.
- **Synchronized Traces:** `RESISTANCE WELDING CURRENT`, `ELECTRODE FORCE`.
- **Sequential Intervals:** `PREWELD INTERVAL` $\rightarrow$ `SQUEEZE TIME` $\rightarrow$ `WELD TIME` $\rightarrow$ `HOLD TIME` $\rightarrow$ `OFF TIME`.
- **Distinction from B49:** Single impulse (no pulsation, no heat/cool pulses, no quench or temper intervals).

### 3. `Figure B53` — An Example of a Welding Cycle for Pulsed Welding
- **Source Coordinates:** Printed p. 157, PDF index 169 (top partition: `[0.05, 0.05, 0.58, 0.95]`)
- **Metrics:** 50 ACCEPTED nodes, 79 ACCEPTED edges, 0 duplicate edges, 21 joined Clause 4 terms.
- **Synchronized Vertical Traces (5 Traces):**
  1. `WELDING CURRENT` (Current, Amperes)
  2. `ARC VOLTAGE` (Voltage, Volts)
  3. `WIRE FEED SPEED` (Speed, IPM / MPM)
  4. `TRAVEL SPEED` (Speed, IPM / MPM)
  5. `SHIELDING GAS FLOW` (Flow, CFH / LPM)
- **Sequential Intervals:** `PREFLOW TIME` $\rightarrow$ `START TIME` $\rightarrow$ `TRAVEL START DELAY TIME` $\rightarrow$ `FILLER METAL START DELAY TIME` $\rightarrow$ `UPSLOPE TIME` $\rightarrow$ `WELD TIME` $\rightarrow$ `TAPER TIME` $\rightarrow$ `TRAVEL STOP DELAY TIME` $\rightarrow$ `FILLER METAL STOP DELAY TIME` $\rightarrow$ `DOWNSLOPE TIME` $\rightarrow$ `POSTFLOW TIME`.
- **Sub-Intervals:** `HIGH PULSE TIME` $\subset$ `WELD TIME` and `LOW PULSE TIME` $\subset$ `WELD TIME`.
- **Parameters:** `HOT START CURRENT`, `INITIAL CURRENT`, `HIGH PULSE CURRENT`, `LOW PULSE CURRENT`, `FINAL TAPER CURRENT`, `FINAL CURRENT`.

### 4. Remaining Archetype 4 Figures
- **`Figure B44` (Inertia Friction Welding, p. 148, PDF 160):** 18 nodes, 28 edges; traces `ROTATIONAL SPEED`, `AXIAL FORCE`, `UPSET`; phases `FRICTION PHASE` $\rightarrow$ `FORGE PHASE`; parameters `FRICTION SPEED`, `FRICTION WELDING FORCE`, `FRICTION UPSET DISTANCE`, `TOTAL UPSET DISTANCE`.
- **`Figure B45` (Direct Drive Friction Welding, p. 149, PDF 161):** 20 nodes, 34 edges; traces `ROTATIONAL SPEED`, `AXIAL FORCE`, `UPSET`; intervals `FRICTION TIME` $\rightarrow$ `FORGE TIME`; parameters `FRICTION SPEED`, `FRICTION WELDING FORCE`, `FORGE FORCE`, `FRICTION UPSET DISTANCE`, `FORGE UPSET DISTANCE`, `TOTAL UPSET DISTANCE`.
- **`Figure B51` (Flash Welding Cycle, p. 154, PDF 166):** 15 nodes, 24 edges; traces `PLATEN POSITION`, `PLATEN VELOCITY`, `FLASHING VOLTAGE`, `UPSET FORCE`; intervals `FLASH TIME` $\rightarrow$ `UPSET TIME` $\rightarrow$ `HOLD TIME`.
- **`Figure B54` (GMAW, FCAW, SAW Cycle, p. 157, PDF 169):** 30 nodes, 47 edges; traces `WELDING CURRENT`, `ARC VOLTAGE`, `WIRE FEED SPEED`, `SHIELDING GAS FLOW`; intervals `PREFLOW TIME` $\rightarrow$ `START TIME` $\rightarrow$ `FILLER METAL START DELAY TIME` $\rightarrow$ `WELD TIME` $\rightarrow$ `CRATER FILL TIME` $\rightarrow$ `MELTBACK TIME` $\rightarrow$ `POSTFLOW TIME`.

---

## 5. Part 2: Remaining Annex B Spatial Callout & Embedded Table Figures

- **Completed Sub-Panel Sequences Verified:**
  - `Figure B7`: 7 sub-panels `(A)` through `(G)` (`Square Edge Shape` .. `Round Edge Shape`)
  - `Figure B12`: 5 sub-panels `(A)` through `(E)` (`End Dam`, `Shelf Bar`, `Split Back Piping`, `Sump`, `Runoff Weld Tab, Starting Weld Tab`)
  - `Figure B15`: 5 sub-panels `(A)` through `(E)` (`Upset Weld`, `Flash Weld`, `Surfacing Weld`, `Slot Weld`, `Plug Weld`)
  - `Figure B20`: 7 sub-panels `(A)` through `(G)` (`1F Rotated` .. `6F Inclined`)
  - `Figure B21`: 4 sub-panels `(A)` through `(D)` (`Travel Angle`, `Work Angle`, `Pipe Weld`, `Push Angle and Drag Angle`)
  - `Figure B30`: 7 sub-panels `(A)` through `(G)` (`CJP`, `PJP`, `Surfacing Weld`, `Resistance Seam Weld / Spot Weld`, `Seam Weld`, `Projection Weld`, `Edge Weld`)
  - `Figure B32`: 15 sub-panels `(A)` through `(O)` (`Toe Crack` .. `Burn-Through`)
  - `Figure B37`: 2 sub-panels `(A)` and `(B)` (`Nonconsumable Guide ESW`, `Consumable Guide ESW`)
  - `Figure B40`: 4 sub-panels `(A)` through `(D)` (`Pure Acetylene Flame`, `Neutral Flame`, `Oxidizing Flame`, `Reducing Flame`)
- **Numbered Key Legends & Specific Callouts:**
  - `Figure B33` (*Crack Types*, p. 139): All 13 crack key legend items extracted as `CALLOUT` and `KEY_LEGEND_ITEM` nodes:
    `1 Crater crack`, `2 Face crack`, `3 Heat-affected zone crack`, `4 Lamellar tear`, `5 Longitudinal crack`, `6 Root crack`, `7 Root surface crack`, `8 Throat crack`, `9 Toe crack`, `10 Transverse crack`, `11 Underbead crack`, `12 Weld interface crack`, `13 Weld metal crack`.
  - `Figure B46` (*Friction Stir Welding*, p. 150): All 10 numbered key items (`1 Base Metal`, `2 Direction of Tool Rotation`, `3 Weld Tool`, `4 Axial Force`, `5 Tool Shoulder`, `6 Probe`, `7 Advancing Side of Weld`, `8 Exit Hole`, `9 Retreating Side of Weld`, `10 Weld Face`) and microstructural zones (`Advancing Side`, `Retreating Side`, `Shoulder`, `Probe`, `Stir Zone / Weld Nugget`, `TMAZ`, `HAZ`).
  - `Figures B7, B16A, B16B, B16C, B47, B48`: All tabular positions (`Flat`, `Horizontal`, `Overhead`, `Vertical`), diagram references (`A`–`E`), angular rotation/inclination limits, and electrical circuit arrangements (`Direct`, `Indirect`, `Series`, `Push-Pull`, `Parallel`) extracted into `nodes`.
- **Title Cleanliness:** Trailing `. . . . . . . 105` completely stripped from `FIGURE_B17_SPEC.official_title` (`'Welding Test Positions and Their Designations for Groove Welds and Surfacing Welds in Plate'`).

---

## 6. Mandatory 4-Check Deterministic Anti-Drift Audit

### Check 1: Genuine PyMuPDF Extraction & Verification
- 56 / 56 figure titles verified against *List of Figures* in `doc[10..11]` via `verify_figure_title_in_list_of_figures` (raises `ValueError` on any mismatch).
- 56 / 56 figure captions verified on all target pages (`doc[94..169]`).
- Vector waveform traces, dimension lines, and arrowheads extracted from `page.get_drawings()` with > 0 vector items on all 56 figures.

### Check 2: Dual-Layer Epistemic Admission & Duplicate Guard
- Total ACCEPTED nodes: `1,115`
- Total ACCEPTED edges: `1,917`
- Total CANDIDATE nodes: `0`
- Total CANDIDATE edges: `0`
- Duplicate edges: `0` (verified by `(source, target, edge_type, observation_id)` uniqueness across all 56 figures).

### Check 3: Cross-Source Normative Join
- 265 / 265 Annex B figure cross-references in `glossary_store.json` (Clause 4) resolve directly to an ingested figure or sub-panel node.

### Check 4: Zero Live Model Calls & Anti-Drift Closure
- `0` live LLM calls executed during Gate 3C ingestion and evaluation.
- `0` hardcoded benchmark question IDs (`QA002`, `HO002`, `CQ-0`, `DEV001`, `C4-QA001`, `B1-QA`, `B49-QA`) in `src/` or `eval/*.py`.
- `CLEAR_REAL_ENTRY_CONTRACT` verified by `python -B -m src.evidence_chart_preflight`.
