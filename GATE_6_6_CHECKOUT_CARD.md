# Gate 6.6 Checkout & Closeout Card: Phase 4 Reader Qualification with Gold Evidence, Retrieval-vs-Reader Diagnostic Separation & Replay Coverage Ledger

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `6ce50e0` (`v1.6.5.1-closeout-hygiene` / `v1.6.5-unified-provenance-and-path`)  
**Target Branch:** `feat/gate-6-6-reader-qualification` $\rightarrow$ `main`  
**Release Tag:** `v1.6.6-reader-qualification`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Executive Summary & Verification Ledger

Gate 6.6 executes **Phase 4 (Reader Qualification with Gold Evidence — Bakeoff #16)** from [AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md), isolating reader/composer performance from retrieval and routing across 3 controlled gold-evidence arms, establishing a deterministic 5-class failure taxonomy, and auditing genuine vs. quarantined offline model replay coverage:

1. **Authoritative Gold-Evidence Packet Builder & 3-Arm Reader Qualification ([reader_qualification.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/reader_qualification.py)):**
   - Implemented [`build_gold_evidence_packet`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/reader_qualification.py#L104-L151), [`prepare_reader_evidence_arm`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/reader_qualification.py#L154-L218), and [`compose_from_gold_arm`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/reader_qualification.py#L221-L255) across three controlled gold-evidence budgets:
     - **Arm A (`GOLD_ARM_A_COARSE_LOCATOR`):** Top-level locator and first-clause summary only (`requires_diagram_crop=False, crop_path=None`) $\rightarrow$ **2 / 24 (`8.33%`)**.
     - **Arm B (`GOLD_ARM_B_CROP_AND_CAPTION`):** Verified 300-DPI crop + primary caption/table summary (omitting deep schematic key callouts, measurement footnotes, and multi-hop Clause 4 `See also` chains) $\rightarrow$ **15 / 24 (`62.50%`)**.
     - **Arm C (`GOLD_ARM_C_COMPLETE_GOLD_EVIDENCE`):** Complete functional evidence bundle joining 300-DPI figure crop, numbered schematic key callout items, general measurement notes, and cross-referenced Clause 4 / Annex C / Annex D definitions $\rightarrow$ **24 / 24 (`100.00%`)**.
     - **Live Retrieved Track (`retrieved_whole_standard`):** End-to-end `DeterministicQuestionPlanner` + [`answer_whole_standard_question`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py) $\rightarrow$ **24 / 24 (`100.00%`)**, proving `0.0%` retrieval-vs-reader delta on the repaired whole-standard baseline.
2. **Deterministic 5-Class Failure Taxonomy ([`classify_diagnostic_outcome`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/reader_qualification.py#L258-L315)):**
   - Separates every evaluated query into `PASS_SUPPORTED` or one of the 5 diagnostic failure classes: `EXTRACTION_FAILURE`, `RETRIEVAL_FAILURE`, `READER_INTERPRETATION_FAILURE`, `EVIDENCE_BINDING_OR_PROVENANCE_FAILURE`, and `ABSTENTION_FAILURE`.
3. **24-Query Reader Qualification Benchmark ([run_phase6_6_reader_qualification.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_6_reader_qualification.py)):**
   - Evaluates the 20 Gate 6.3 blind hardening queries (`G63-BLIND01`–`G63-BLIND20`) plus 4 diagnostic controls (`G66-DIAG01` Out-of-Scope Abstention, `G66-DIAG02` Invalid Compound Suffix Rejection, `G66-DIAG03` Obsolete Process Refutation, and `G66-DIAG04` Multi-Panel Spatial Callout & Waveform Binding) across all 4 tracks with default `write_results: bool = False`.
4. **Honest Replay Coverage Audit Ledger ([audit_replay_coverage.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/scripts/audit_replay_coverage.py) & [replay_coverage_manifest.json](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/manifests/replay_coverage_manifest.json)):**
   - Audits all 14 genuine `DeepSeek-V4.1` replay cassettes (`storage/model_replays/deepseek_v4_1_flash_1017/`) against the 6 quarantined synthetic planner fixtures (`storage/model_replays/deterministic_planner_fixtures/`) across every benchmark suite (`phase5_5_nlq_001` through `phase6_6_reader_qualification_001`).
5. **CLI & Application Diagnostic Parity ([evidence_whole_standard_cli.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_whole_standard_cli.py) & [query.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/query.py)):**
   - Added `--qualify-reader <query>` and `--replay-audit` to [evidence_whole_standard_cli.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_whole_standard_cli.py) and `diagnostic_track` (`gold_arm_a`, `gold_arm_b`, `gold_arm_c`, `retrieved_whole_standard`) to [`async_query`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/query.py#L219-L315) and [`run_query`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/query.py#L453-L480).

---

## 2. Gate 6.6 24-Query Reader Qualification Results Across 4 Tracks

| QID | Category | Printed Page / PDF Index | Evidence Locator | Arm A (Coarse) | Arm B (Crop+Caption) | Arm C (Full Gold) | Retrieved (Live) |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `G63-BLIND01` | `clause4_visual_linkage` | 6 / 18 | `clause4:term:acetylene feather` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND02` | `clause4_definition_with_see_also` | 69 / 81 | `table_a1:process_letter_designations` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND03` | `welding_position_tabulations` | 103 / 115 | `figure_b16b:diagram_details` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND04` | `reverse_figure_lookup` | 112 / 124 | `figure_b21:diagram_details` | FAIL (`BINDING_PROV`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND05` | `joint_type_applicable_welds` | 82 / 94 | `figure_b1:diagram_details` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND06` | `classification_chart_energy_sources` | 79 / 91 | `figure_a6:brazing_and_soldering` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND07` | `letter_designation_decoding` | 70 / 82 | `table_a1:process_letter_designations` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND08` | `process_group_listing` | 78 / 90 | `figure_a5:solid_state_welding` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND09` | `obsolete_process_verification` | 74 / 86 | `table_a5:obsolete_processes` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND10` | `process_variation_subtyping` | 70 / 82 | `table_a1:process_letter_designations` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND11` | `sequence_nomenclature_cluster` | 114 / 126 | `figure_b23:diagram_details` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND12` | `throat_dimension_cluster` | 127 / 139 | `figure_b26:diagram_details` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND13` | `fsw_schematic_and_key` | 150 / 162 | `figure_b46:schematic_key` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND14` | `temper_bead_nomenclature` | 116 / 128 | `figure_b23:panel_j` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND15` | `reentrant_angle_discontinuity_cluster` | 136 / 148 | `figure_b32:diagram_details` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND16` | `application_mode_suffixes_and_rules` | 74 / 86 | `table_a4:suffix:-AU` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND17` | `process_family_pressure_ranges` | 70 / 82 | `table_a1:process_letter_designations` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND18` | `safety_exceptions_and_incorrect_terms` | 140 / 152 | `figure_b34:diagram_details` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND19` | `annex_c_and_d_normative_revisions` | 159 / 171 | `annex_c:decision:C1.5.6` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND20` | `waveform_cycle_interval_analysis` | 153 / 165 | `figure_b49:interval:upslope` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G66-DIAG01` | `abstention_control` | `None` / `None` | `None` | **PASS** | **PASS** | **PASS** | **PASS** |
| `G66-DIAG02` | `invalid_compound_suffix_control` | 69 / 81 | `table_a1:process_letter_designations` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G66-DIAG03` | `obsolete_process_refutation_control` | 74 / 86 | `table_a5:obsolete_processes` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G66-DIAG04` | `waveform_spatial_callout_control` | 157 / 169 | `figure_b53:interval:upslope_and_downslope` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |

---

## 3. Offline Replay Coverage Audit Ledger

| Benchmark Suite | Total Queries | Genuine `DeepSeek-V4.1` Replays | Quarantined Synthetic Fixtures | Deterministic Planner Fallbacks |
| :--- | :---: | :---: | :---: | :---: |
| `phase5_5_nlq_001` | 15 | 3 | 0 | 12 |
| `phase6_ner_routing_001` | 20 | 1 | 0 | 19 |
| `phase6_1_semantic_graph_001` | 15 | 3 | 0 | 12 |
| `phase6_2_generalization_holdout_001` | 20 | 2 | 0 | 18 |
| `phase6_3_blind_hardening_001` | 20 | 0 | 6 | 14 |
| `phase6_6_reader_qualification_001` | 24 | 0 | 6 | 18 |

- **Total Genuine `DeepSeek-V4.1` Replay Cassettes on Disk:** `14` (`storage/model_replays/deepseek_v4_1_flash_1017/`, including 5 Phase 5 Annex A chart-planning replays + 9 whole-standard NLQ replays).
- **Total Quarantined Synthetic Planner Fixtures on Disk:** `6` (`storage/model_replays/deterministic_planner_fixtures/`).

---

## 4. Cryptographic Lock Ledger (All 54 Locked Artifacts)

| Index | Rel Path | SHA-256 Digest | Status |
| :---: | :--- | :--- | :---: |
| 1–51 | Prior Gate 6.0–6.5.1 Locked Artifacts (`ALL_51_LOCKED_HASHES`) | Verified byte-for-byte identical | MATCH |
| 52 | `storage/evidence_v2/phase6_6_reader_qualification_001/questions.json` | `37fb22ce12235042e2a8f84aabca2011a45d81ebdf34cc764b9e0a1ffcc7ea2d` | MATCH |
| 53 | `storage/evidence_v2/phase6_6_reader_qualification_001/gold_packets.json` | `030834a2abd05322248f77e8a8811ded57b400e4760b7091259d5b0415fd5386` | MATCH |
| 54 | `storage/evidence_v2/phase6_6_reader_qualification_001/results.json` | `8c9d29b039e069c075fb9046a116322d328256008d3ca4115bb8d69ffddbd20a` | MATCH |
