# AWS A3.0 Knowledge Ingestion Pipeline: Handoff to Gate 3D (Clause 4 + Annex B Holdout Benchmark)

We are building an authoritative, multimodal, evidence-grounded knowledge ingestion and RAG pipeline for **AWS A3.0M/A3.0:2020** (*Standard Welding Terms and Definitions*).

---

## 1. Environment & Workspace Coordinates

- **Local Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`
- **Remote Repository:** [kaiello/aws-a30-prototype](https://github.com/kaiello/aws-a30-prototype)
- **Google Drive 1:1 Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)
- **Source Standard PDF:** `data/AWS_A3.0_2020.pdf` (SHA-256: `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`)
- **Current Branch:** `feat/gate-3c-annex-b-archetype4-and-remaining`
- **Current Head Commit:** `6b2a731` (`test(gate-3c): add explicit in-store crop manifest and real callout assertions`)
- **Working Tree:** Clean, pushed to `origin`, 438 files mirrored to Google Drive.
- **Python Runtime:** Python 3.12.7 (use `python -B -m ...` or `pytest`, do NOT use `poetry`). Harmless `posh-git` warning in PowerShell profile can be ignored.

---

## 2. Completed Milestones & Locked Provenance

| Phase / Gate | Scope | Status & Outcome | Locked Hashes / Checkpoints |
|---|---|---|---|
| **Phase 1 (Gates 0, 1A, 1B)** | Offline A1/A2 closure & 67-Q live run | **PASSED & MERGED** | `main` `2fbaabd8...` (67/67 compiled, 194 executed ops) |
| **Phase 2 (Gates 2A–2F)** | Annex A Figures A1–A6 + Tables A1–A5 + 30-Q Live Holdout | **PASSED & MERGED** | `main` `c4363c2` (30/30 holdout PASS, 127 ops, 171/171 tests) |
| **Gate 3A** | Clause 4 Glossary, Dual-Provenance `IS_A`, Annex C/D | **PASSED & MERGED** | `main` `728ceed`<br>• `glossary_store.json`: `e88a2fd4...`<br>• `annex_c_d_store.json`: `8b5d8faa...`<br>• `is_a_promotion_store.json`: `a5c69c35...` |
| **Gate 3B** | Archetype 3 Calibration (`Figure B1` & `Figure B6` 3-page) | **PASSED & MERGED** | `main` `d8fb23d`<br>• `annex_b_archetype3_unified_store.json`: `16b7bea5...`<br>• `b1_joint_types_store.json`: `2fcd7410...`<br>• `b6_multi_page_store.json`: `1a757175...` |
| **Gate 3C** | Archetype 4 Calibration (`B49`, `B50`, `B53`) & Complete Annex B (`B7–B54`) | **REPAIRED & VERIFIED** (Ready to merge)<br>Head commit: `6b2a731` | • `annex_b_complete_unified_store.json`: `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898`<br>• `annex_b_archetype4_unified_store.json`: `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954`<br>• `figure_b33_store.json`: `8781a4c5...`<br>• `figure_b46_store.json`: `67b8c92f...`<br>• `figure_b49_store.json`: `0c7d41cfa4...`<br>• `figure_b50_store.json`: `61a691fc...`<br>• `figure_b53_store.json`: `b26e91c3...` |

### Key Gate 3C Repair Outcomes (Verified Offline — 0 Live LLM Calls)
1. **High-Res Crops & Vectors:** Fixed normalized fraction conversion in `src/archetype_spatial_callout.py`. All 80 crop PNGs are 300 DPI (`width >= 1000px`, `height >= 800px`, `size >= 10,000 bytes`, 80 unique SHA-256 hashes, zero blank squares), with $> 0$ vector drawings on all 56 figures.
2. **Genuine Callouts & Legends:** Replaced dummy strings with live PyMuPDF text blocks. Complete sub-panel sequences extracted; `Figure B33` has 13 crack keys; `Figure B46` has 10 FSW keys + microstructural zones; `B7, B16A-C, B47, B48` have table/circuit labels; `Figure B17` title stripped of trailing dots.
3. **Waveform Bbox Binding:** Live text spans bound to traces, intervals, and parameters in `src/archetype_cycle_waveform.py`. Dynamic multi-figure QA composer updated for all figures `B1` through `B54`.
4. **Metrics:** 56 figures, 1,115 ACCEPTED nodes, 1,917 ACCEPTED edges, 0 duplicate edges, 265 / 265 Clause 4 figure back-links resolved (100.0%).
5. **Testing:** `10/10` Gate 3C tests PASS, `1,429/1,429` full pytest suite PASS, `11/11` preflight clear (`CLEAR_REAL_ENTRY_CONTRACT`), 0 anti-drift regex matches.

---

## 3. Immediate Action Plan

### Step 3C.0: Git Branch Hygiene & Gate 3C Merge to `main` (Mandatory First Step)

1. In `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`, verify clean working tree and switch to `main`:
   ```powershell
   git status
   git checkout main
   git merge feat/gate-3c-annex-b-archetype4-and-remaining --ff-only
   ```
2. Update `ROADMAP.md` to record Gate 3C as `PASSED & MERGED` (`6b2a731`) with locked SHA-256 hashes for `annex_b_complete_unified_store.json`, `annex_b_archetype4_unified_store.json`, `figure_b33_store.json`, `figure_b46_store.json`, `figure_b49_store.json`, `figure_b50_store.json`, and `figure_b53_store.json`.
3. Commit `ROADMAP.md` update to `main`:
   ```powershell
   git add ROADMAP.md
   git commit -m "docs(roadmap): record Gate 3C as PASSED & MERGED"
   git push origin main
   git branch -d feat/gate-3c-annex-b-archetype4-and-remaining
   ```
4. Sync Google Drive mirror:
   ```powershell
   python -B -m src.sync_drive_mirror
   ```

---

### Step 3D: Execute Gate 3D (Clause 4 + Annex B Unseen Holdout Benchmark)

1. Create and switch to branch `feat/gate-3d-clause4-annex-b-holdout`:
   ```powershell
   git checkout -b feat/gate-3d-clause4-annex-b-holdout
   ```
2. **Review Objectives for Gate 3D:**
   - Ingest / author unseen benchmark queries testing:
     - Cross-clause joins between Clause 4 Terms $\leftrightarrow$ Annex B Figures (`Archetype 3` spatial callouts and `Archetype 4` waveforms).
     - Normative status checks (`standard` vs. `nonstandard` terms, `IS_A_PROCESS_VARIATION_OF` promotion corroboration).
     - Spatial callout lookups (weld types, joint types, sub-panels, crack types in B33, FSW zones in B46).
     - Waveform cycle interval sequences (`TEMPORAL_PRECEDES`, `SUB_INTERVAL_OF`, modulated parameters).
   - Ensure `0` live model calls during test setup; follow strict 3-tier testing rules.
   - Run preflight and verify full pytest suite passes before and after holdout evaluation.
