# Gate 6.5 Checkout & Closeout Card: Authoritative Provenance Unification, Shared Application-Evaluator Execution Path, Checkout Reconciliation & Independent Claim/Coordinate Evaluator

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `ccd6bba` (`v1.6.4.1-provenance-integrity`)  
**Target Branch:** `feat/gate-6-5-provenance-and-shared-path` $\rightarrow$ `main`  
**Release Tag:** `v1.6.5-unified-provenance-and-path`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Executive Summary & Verification Ledger

Gate 6.5 delivers comprehensive architectural hardening, authoritative provenance unification, and execution consistency across the AWS A3.0M/A3.0:2020 ingest, retrieval, and evaluation subsystem:

1. **Authoritative Annex A Page Mapping & Zero-Overwrite Contract:**
   - Corrected Annex A page registry `ANNEX_A_PAGES` in [evidence_phase4_bakeoff.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py) to exact physical pagination: Figure A1 (p. 75 / PDF 87), Figure A2 (p. 76 / PDF 88), Figure A3 (p. 76 / PDF 88), Figure A4 (p. 77 / PDF 89), Figure A5 (p. 78 / PDF 90), and Figure A6 (p. 79 / PDF 91). Completely eliminates the off-by-one +1 artifact that erroneously placed Figure A6 on excluded blank divider p. 80 / PDF 92.
   - Refactored `_enrich_modality_provenance` to guarantee zero coordinate overwrites: multi-hop, Annex B, Normative Tables, and Clause 4 composers preserve their exact coordinates (e.g. Table A3 GTAW on p. 73 / PDF 85, Figure B53 on 157 / 169, Figure B23 Panel J on 116 / 128).
   - Fixed Figure B1 crop resolution regex (`^figure_b{num_str}(_|\.|$)`) preventing false-positive prefix matching on `figure_b10...`.
   - Updated Figure B23 Panel J (`temper_beads`) to return printed p. 116 / PDF 128 with locator `figure_b23:panel_j`.
2. **Shared Application, Web API & CLI Execution Path:**
   - Unified [query.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/query.py) (`async_query` and `run_query`) and [web.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/web.py) (`/api/query`) to accept `evidence_version in {"whole_standard", "ws"}` and route directly through `answer_whole_standard_question`.
   - Standardized application-level evidence packets and error handling (`INSUFFICIENT_EVIDENCE: 422`, `EXECUTION_FAILED: 500`).
3. **Independent Provenance, Coordinate & Crop-Identity Evaluator:**
   - Upgraded [run_phase6_3_blind_hardening.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_3_blind_hardening.py) with 5 mandatory structural provenance gates: Coordinate Formula (`pdf_index - printed_page == 12` with exclusion verification), Crop-to-Locator Identity, Body-to-Metadata Alignment, Modality/Abstention, and Granular Metric Reporting.
   - Hardened evaluation runner with `write_results: bool = False` default to protect the cryptographic immutability of `results.json` (`18f247c1...`).
4. **Checkout Reconciliation & Documentation Alignment:**
   - Synchronized [GATE_6_4_CHECKOUT_CARD.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_4_CHECKOUT_CARD.md), [ROADMAP.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md), [goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md), and [docs/goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/goal.md) with the exact 20 questions from `questions.json` and all 51 cryptographic locks.
   - Documented Architectural Recommendations (Decision Ledger D1–D6, 5-Phase Sequence, Navy Weld Bakeoff Triggers) in [AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md), [ROADMAP.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md), [goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md), and [docs/goal.md](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/goal.md).
   - Updated [sync_drive_mirror.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/sync_drive_mirror.py) to preserve `CONTINUATION_*.md`.
5. **Rigorous Offline Verification Suite:**
   - Authored [test_gate_6_5_provenance_and_shared_path.py](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_5_provenance_and_shared_path.py) (6/6 passed under strict socket isolation).

---

## 2. Gate 6.3 Blind Hardening Benchmark Results (Exact 20/20 with Evaluator Provenance Gates)

All 20 benchmark queries execute 100% offline with zero network calls, satisfying all 5 evaluator gates (Content, Coordinate Formula, Crop Identity, Body-Metadata Alignment, and Strict Pass):

| QID | Benchmark Query Text | Status | Printed Page | PDF Index | Evidence Locator | Crop Path | Required Elements Present | Strict Pass |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: |
| `G63-BLIND01` | What is acetylene feather? | PASS | 6 | 18 | `clause4:term:acetylene_feather` | None | acetylene feather, carburizing, oxyacetylene flame, Figure B40 | PASS |
| `G63-BLIND02` | Define GTAW? | PASS | 29 | 41 | `clause4:term:gas_tungsten_arc_welding` | None | gas tungsten arc welding, GTAW, tungsten electrode, Figure B36 | PASS |
| `G63-BLIND03` | What is the Rotation of Face for Flat Fillet Weld? | PASS | 103 | 115 | `figure_b16b:table_details` | `figure_b16b_p103_crop_300.png` | 150° to 210°, Figure B16B, Flat | PASS |
| `G63-BLIND04` | What figure shows the position of beam, filler material, gun or torch? | PASS | 112 | 124 | `figure_b21:diagram_details` | `figure_b21_p112_crop_300.png` | Figure B21, Position of Beam, Filler Material, Gun, or Torch | PASS |
| `G63-BLIND05` | What are the applicable weld types for a T-Joint? | PASS | 82 | 94 | `figure_b1:panel_c_applicable_welds` | `figure_b1_p82_crop_300.png` | Figure B1, T-Joint, fillet, bevel-groove | PASS |
| `G63-BLIND06` | How many different energy sources are there in Brazing and Soldering? | PASS | 79 | 91 | `figure_a6:hierarchy_tree` | `figure_a6_p79_crop_300.png` | Figure A6, Chemical, Electrical, 2 | PASS |
| `G63-BLIND07` | What is FRW, RSEW, and RSW? | PASS | 27 | 39 | `tables_a1_a3:multi_process_decoding` | None | friction welding, FRW, resistance seam welding, RSEW | PASS |
| `G63-BLIND08` | List all the Solid State Welding Processes | PASS | 75 | 87 | `figure_a1:process_family_tree` | `figure_a1_p75_crop_300.png` | coextrusion welding, CEW, cold welding, CW | PASS |
| `G63-BLIND09` | Is block Brazing and Shielded carbon arc welding Obsolete processes? | PASS | 78 | 90 | `table_a5:obsolete_processes` | None | Table A5, obsolete, block brazing, BB | PASS |
| `G63-BLIND10` | What is the difference between FLSP, FLSP-P, and FLSP-W? | PASS | 26 | 38 | `tables_a1_a3:multi_process_decoding` | None | flame spraying, FLSP, powder flame spraying, FLSP-P | PASS |
| `G63-BLIND11` | What is a block sequence, what figure illustrates it, and how does AWS A3.0 define and distinguish all of its cross-referenced sequence terms? | PASS | 114 | 126 | `figure_b23:diagram_details` | `figure_b23_p114_crop_300.png` | block sequence, Figure B23, cascade sequence, cross-sectional sequence | PASS |
| `G63-BLIND12` | Define effective throat (including how it is determined when a fillet weld is combined with a partial joint penetration groove weld), identify the figures that illustrate it, and provide the definitions of its cross-referenced throat terms. | PASS | 120 | 132 | `figure_b25:diagram_details` | `figure_b25_p120_crop_300.png` | effective throat, partial joint penetration groove weld, B25, actual throat | PASS |
| `G63-BLIND13` | Which figure in AWS A3.0 shows the schematic of the Friction Stir Welding process, what are the 10 numbered items in its Key, and how does the standard define the advancing side versus the retreating side of the weld? | PASS | 147 | 159 | `figure_b46:diagram_details` | `figure_b46_p147_crop_300.png` | Figure B46, Base Metal, Direction of Tool Rotation, Weld Tool | PASS |
| `G63-BLIND14` | Which figure and sub-diagram illustrate the placement of temper beads and toe temper beads in groove, fillet, and overlay welds, how is the distance S measured according to the figure's notes, what approximate offset dimension is specified for the first layer temper beads, and how does Clause 4 define temper pass, temper bead, temper bead sequence, toe temper pass, and toe temper bead? | PASS | 116 | 128 | `figure_b23:panel_j` | `figure_b23_p116_crop_300.png` | Figure B23, (J), distance S, parallel to the base metal surface | PASS |
| `G63-BLIND15` | How does AWS A3.0 define reentrant angle, bead reentrant angle, and toe reentrant angle, which figure sub-diagrams illustrate them, and what angular condition at the weld toe, weld root, or weld bead toe defines overlap in fusion welding? | PASS | 133 | 145 | `figure_b32:diagram_details` | `figure_b32_p133_crop_300.png` | reentrant angle, bead reentrant angle, toe reentrant angle, Figure B32 | PASS |
| `G63-BLIND16` | List all six application modes and their letter designation suffixes from Table A4, explain the rule and format for appending them to a process or process variation designation, and give the Clause 4 definitions that distinguish the six application modes. | PASS | 77 | 89 | `table_a4:letter_designation_suffixes` | None | Table A4, -AD, -AU, -MA | PASS |
| `G63-BLIND17` | Decode the letter designations LBC, LBC-A, LBC-EV, LBC-IG, LBC-O and EBW, EBW-HV, EBW-MV, EBW-NV from Annex A (Tables A1–A3), and state how Clause 4 defines each variation, including the exact operating pressure ranges in pascals and torr for the electron beam welding variations. | PASS | 21 | 33 | `tables_a1_a3:multi_process_decoding` | None | laser beam cutting, LBC, laser beam air cutting, LBC-A | PASS |
| `G63-BLIND18` | According to the Foreword and Annex C, under what specific exception does AWS A3.0 classify a term as both "nonstandard and incorrect"? Identify the electrical circuit terms in Clause 4 that carry this "nonstandard and incorrect" designation, and provide the definitions of the standard terms that must be used instead (including the safety distinction with ground connection in Figure B34). | PASS | 137 | 149 | `figure_b34:diagram_details` | `figure_b34_p137_crop_300.png` | personal safety, ground clamp, ground lead, welding ground | PASS |
| `G63-BLIND19` | Explain two major terminology revisions documented in Annex C (Clauses C1.5.6 and C1.5.7) and Annex D of AWS A3.0:2020: (1) Why was parallel joint introduced to replace edge joint among the five basic joint types, and how are both terms defined in Clause 4? (2) How did the 13th edition change the status of nondestructive evaluation, nondestructive inspection (NDI), and nondestructive testing (NDT) relative to nondestructive examination (NDE), and why was the definition of nondestructive examination (NDE) itself modified? | PASS | 159 | 171 | `annex_c_and_d:historical_revisions` | None | parallel joint, edge joint, Clause 4, Table D5 | PASS |
| `G63-BLIND20` | Compare the resistance spot welding waveforms in Figure B49 (Pulsation Welding Waveform) and Figure B50 (Single-Pulse Resistance Spot Welding Waveform): how does Clause 4 distinguish weld time, resistance welding from weld interval, resistance welding, and cool time, resistance welding from quench time, resistance welding? Additionally, define the sequential cycle intervals shown across Figures B49 and B50: squeeze time, preweld interval, preheat time, upslope time, pulse time, downslope time, temper time, hold time, postweld interval, forge-delay time, and off time. | PASS | 153 | 165 | `figures_b49_b50:waveform_comparison` | `figure_b49_p152_crop_300.png` | Figure B49, Figure B50, weld time, weld interval | PASS |

---

## 3. Cryptographic Lock Ledger (All 51 Locked Artifacts)

| Index | Rel Path | SHA-256 Digest | Status |
| :---: | :--- | :--- | :---: |
| 1 | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `a16109aa9369666dd934d40e1eebbb2bb8180c4366eec6a938ea5f061e86a7d6` | MATCH |
| 2 | `storage/evidence_v2/clause4_ingest_001/semantic_graph.json` | `f59a0f44358a74e4c2be895c1a72d73f4e2cbb1dc7b293527b134d1bcddf6047` | MATCH |
| 3 | `storage/evidence_v2/clause4_ingest_001/concept_neighborhoods.json` | `b99e74ce9a8ca6114eb31cf5e1cb2f57ef04d2c88f11d17d5e86973e449bf258` | MATCH |
| 4 | `storage/evidence_v2/annex_a_tables_001/final_projection/tables_graph.json` | `75ba75753066986a4220b2241cf13540eb40e53a3390c5fa6ec750a9fc770c66` | MATCH |
| 5 | `storage/evidence_v2/a3_ingest_001/final_projection/graph.json` | `052327092305542ca024b17cf0808a3d53eb8132ca59f8a329d44747ebc7b1ce` | MATCH |
| 6 | `storage/evidence_v2/a4_ingest_001/final_projection/graph.json` | `a5f082e668a6231f2fb8028714dfb079717878fa3e5dcaefab9b2ff639d67761` | MATCH |
| 7 | `storage/evidence_v2/clause4_ingest_001/coverage_report.json` | `8390b14c330df8fe15ba05b822d56d0d297aa1585ee588be452ff37cff9d71c1` | MATCH |
| 8 | `storage/evidence_v2/annex_b_archetype4_001/extracted_figures.json` | `432247fc9ec178b548b29cf329ba6916568dd7ea44d56d946fc1d516ee71bf08` | MATCH |
| 9 | `storage/evidence_v2/annex_b_archetype4_001/coverage_report.json` | `38b438ea233b2a26c483d31b0fc23bf6111be86f2b489a2e3796d744b8bc009d` | MATCH |
| 10 | `storage/evidence_v2/annex_b_complete_001/figures_deep.json` | `c4ce569477e685f02bc0f7f95ee2ca219e9177a5606d5ef664fbbf4fba18d96b` | MATCH |
| 11 | `storage/evidence_v2/annex_b_complete_001/coverage_report.json` | `6ae9f36f86821262d16ea48d8869ecda6378e12eb0f3299c855a90e3aa02c2e5` | MATCH |
| 12 | `storage/evidence_v2/phase5_4_benchmark_001/questions.json` | `26d11b51e06faeebbc16ca9069d8aa1312356c54779a1f23ee71eb4010313cb1` | MATCH |
| 13 | `storage/evidence_v2/phase5_4_benchmark_001/rubric.json` | `a3feaa30616bf8e146ebaf29e34b92b6a7ee7f8841aeef2e32f05a968a3fb70c` | MATCH |
| 14 | `storage/evidence_v2/phase5_4_benchmark_001/results.json` | `c37eb6d95318dbb966779435bfe2ec0df1a52fef9bc7c4fbcf909d3b76cf6ca3` | MATCH |
| 15 | `storage/evidence_v2/phase5_4_benchmark_001/coverage_report.json` | `7be33f548e64c3c3a9f0febe9d3326107386055d28fbdbba4632b49d6851b2d0` | MATCH |
| 16 | `storage/evidence_v2/phase5_5_nlq_001/questions.json` | `100787a71676dfb3e404bf768dff863b1856cf246a482b8faae2df03d7db27d9` | MATCH |
| 17 | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `9b36d654ca98e1f575ee818961726a84dfc29f2dc349b1a03e1a8fa48ea0cf06` | MATCH |
| 18 | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `0d8b4bf6485d43ecbb625925faeb5001fffaeb0cb02a0a2df362cfbb00d0eb37` | MATCH |
| 19 | `storage/evidence_v2/phase5_5_nlq_001/coverage_report.json` | `fbf2a09b30c451630135ff37651c5b8b982186835a26c48f2441dc285090f779` | MATCH |
| 20 | `storage/model_replays/deepseek_v4_1_flash_1017/2338006b509f6e1f0eeb5571694f479bb726914f6d3ce9bc7372cf93325c866d.json` | `c9735d5dfbb7cb834927cbdb6ae59e2b0a1f0a2829b3634032d1645e7e1a3fd2` | MATCH |
| 21 | `storage/model_replays/deepseek_v4_1_flash_1017/303fe0bba8cf4cf80687056093406aa89be6f9df8813bc3220fa820aeb294cf0.json` | `7715fbc5b3fe746a4e21a2eb2491fa9b8cfeb774a385f95d85feea8bbf029e2f` | MATCH |
| 22 | `storage/model_replays/deepseek_v4_1_flash_1017/361e6fa0ae3e2caae8b1b11ca0f4d38c645b23d9a19c72ffbb4792ecf69fb4d7.json` | `e2a4be6cebcce0d783857ca29b87bcfe94db437eeff69094feec7209930f305c` | MATCH |
| 23 | `storage/model_replays/deepseek_v4_1_flash_1017/5ad852fc6368d90cae254ff03975005e81fdfd15024dbdb512e32f796c561ee6.json` | `1cba3fa4c3619ea78f7aa95cc3d1797c2ae2b64d081cc93f932f93ce0dff567b` | MATCH |
| 24 | `storage/model_replays/deepseek_v4_1_flash_1017/63251e604f210515668efbf98a72b67f1396f9a0c28e83344d3ce3d2f9748644.json` | `2f9d6c3826dd7ef0bc2d04a627cbf90c6ca7f3fb8f4803d5262243d67bcffc2a` | MATCH |
| 25 | `storage/model_replays/deepseek_v4_1_flash_1017/746a7be7e39a5e8ff7f740a6b5791771120f2b36c2e71887342674e1e355c325.json` | `5e913076ff7a83d7351c33cbf9ba51fb53641cecfbf603e8ff8fbcbc6be6a894` | MATCH |
| 26 | `storage/model_replays/deepseek_v4_1_flash_1017/a457492c1eb73f155998f45a0b779a5574c8715831969ec56f8f118ee6e1cbce.json` | `37d42cf38f9b9f390efc354707011d1ef8f4d5462cf82c81593ef908aa3eb128` | MATCH |
| 27 | `storage/model_replays/deepseek_v4_1_flash_1017/dc168661685ce09bcae9fa7ff64fa4c3f760aa01cb7da4ea0f69a9b13970b135.json` | `25bc1ca7f88ea2bbd924ae0f6795f9c49ca14b0870932bb45df7df512ea50dd4` | MATCH |
| 28 | `storage/evidence_v2/phase6_0_routing_001/questions.json` | `8c62b4c10be134c449c2d1b09b9f5e3692881cfd8c7c9ec956be8ef131cfa04a` | MATCH |
| 29 | `storage/evidence_v2/phase6_0_routing_001/rubric.json` | `be25633fa3d95efc5861783ae89bb7373f1aee36da97ec7ee0b40eb424bf16aa` | MATCH |
| 30 | `storage/evidence_v2/phase6_0_routing_001/results.json` | `6c107be9c049968470a18e00fc926d2524f2b1d62c589e6ebbebf75c74384ef0` | MATCH |
| 31 | `storage/evidence_v2/phase6_0_routing_001/coverage_report.json` | `7be33f548e64c3c3a9f0febe9d3326107386055d28fbdbba4632b49d6851b2d0` | MATCH |
| 32 | `storage/model_replays/deepseek_v4_1_flash_1017/a35f8b9ec141df90e3c5ec59837943cff66da2084c8a2cfa05d3bca2aa24e16c.json` | `df332f1712a208034db3ddba4a4b130e94119fa9787ffda42dcfd41a76813134` | MATCH |
| 33 | `storage/model_replays/deepseek_v4_1_flash_1017/dfbfa322dd811bc294c7b8f9e0ec80a80e1a1236113b28b264103348ea08cfa3.json` | `1c30386cfb8159d337ee9bf9921e428e12140bbfa6cc37ea92cf4f79cecb4057` | MATCH |
| 34 | `storage/evidence_v2/phase6_1_semantic_001/questions.json` | `5c21ec15525546fe183916dd6732cfd864eebbb78a5e80cb5ee1516eef316270` | MATCH |
| 35 | `storage/evidence_v2/phase6_1_semantic_001/rubric.json` | `d121c6ba4d9fe80ddda17131804b49cb376e8fb2974fa906e57849e896434446` | MATCH |
| 36 | `storage/evidence_v2/phase6_1_semantic_001/results.json` | `15e5898dff0007823f038f4be8d1fc4fb0d4eb0762fa2277d32906b3f7f858d4` | MATCH |
| 37 | `storage/evidence_v2/phase6_1_semantic_001/coverage_report.json` | `7be33f548e64c3c3a9f0febe9d3326107386055d28fbdbba4632b49d6851b2d0` | MATCH |
| 38 | `storage/model_replays/deepseek_v4_1_flash_1017/280cefc8ff1aa16d3fdf6c63da671f65bb51892f392231ffba30ef52424b9dc8.json` | `73bbbfb2cf4861e63412a80695bf7c8e96bf0f4f9104fa282b047535b4c16a62` | MATCH |
| 39 | `storage/model_replays/deepseek_v4_1_flash_1017/a441a13437299a9b3a0cc30594a821dc3a8ce90aa4fa4fc04d7c5ee32dbba909.json` | `b23617be2d129759d54c00d414a3bfec8df60f7e914fcce7bfa5dbf5734bc1e0` | MATCH |
| 40 | `storage/evidence_v2/phase6_2_1_closure_001/questions.json` | `da7c0337b514b872b7fef48ba98b79f8c6eb53e7f917ce5395bf1ce54f3918a9` | MATCH |
| 41 | `storage/evidence_v2/phase6_2_1_closure_001/rubric.json` | `b54be49c065f4d1a100529e846059d040aeb7e8df6ff865feee571d8be8d98d8` | MATCH |
| 42 | `storage/evidence_v2/phase6_2_1_closure_001/results.json` | `f31289196b27e699f0bb3b3394622a61dd079bc0607994680aa4238e55e886df` | MATCH |
| 43 | `storage/evidence_v2/phase6_3_blind_hardening_001/questions.json` | `be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b` | MATCH |
| 44 | `storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json` | `a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c` | MATCH |
| 45 | `storage/evidence_v2/phase6_3_blind_hardening_001/results.json` | `18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2` | MATCH |
| 46 | `storage/model_replays/deterministic_planner_fixtures/07d3e65cc2f0f4bab38963fdcb9c7c704615a5c046f019365a3ec3b24ad669ec.json` | `ea4cb468af3dc574f06940672fa2b33537b236140c4e6de3cc5c20b849f6908f` | MATCH (Quarantined) |
| 47 | `storage/model_replays/deterministic_planner_fixtures/1a0d448e9483f699ecb6fba379971dd65059b4aba5344f1e8708b2d7bca8845c.json` | `85e7876785e941ce4ba8bff4c8284be4070827f6c26437431f0120fd8a20d71f` | MATCH (Quarantined) |
| 48 | `storage/model_replays/deterministic_planner_fixtures/73ccb5c640979dc600a4e9d349178667a048ee9ece3b3fc36513a042e3427182.json` | `4f164b170792437eb74b96b64a946d4717a870c1ca98e65da2223ba69206a935` | MATCH (Quarantined) |
| 49 | `storage/model_replays/deterministic_planner_fixtures/78072b41bac7406dd5fa8749643b9320e380548bd065f4af56dd2571940d021f.json` | `3134d3405387ab421f2c1a31879c776bd3c219ba29dd83ba3973ede8b70d2c46` | MATCH (Quarantined) |
| 50 | `storage/model_replays/deterministic_planner_fixtures/c2b781b11a1f795ae75679362554299d5c2ab8f3bb74ca82e69e90adf6623033.json` | `128aa1a26fe77450a76f51d669fc50a6c1a89c89d8c0a87d8473b259a8de771c` | MATCH (Quarantined) |
| 51 | `storage/model_replays/deterministic_planner_fixtures/d6401cf2f24c1f017d7e363ea8de410ccd672178512b655bdc6b0c102e47b8a7.json` | `b21d7621afc83a115b5b4bda999798cf23a39fd1f2c496f8b8d40751193af3cd` | MATCH (Quarantined) |

> [!NOTE]
> Items #46 through #51 are synthetic deterministic planner fixtures created during Gate 6.4 development and quarantined from genuine DeepSeek-V4.1 model replays per PROV-6.4-1. Artifact `#45` (`storage/evidence_v2/phase6_3_blind_hardening_001/results.json`: `18f247c1...`) remains 100% byte-identical and cryptographically immutable.

---

## 4. Architectural Enhancements Summary

1. **Deterministic Pagination Law:** Enforces `pdf_index - printed_page == 12` uniformly across all standard clauses and annexes, rejecting all out-of-bounds or excluded pages (e.g. PDF index 92).
2. **Composition-Layer Coordinate Protection:** Eliminates downstream overwrite drift by preserving coordinates assigned by specialized composers (`ANNEX_A_PAGES`, `Table A3`, `Figure B53`, `Figure B23 Panel J`).
3. **Application Parity:** Web API (`/api/query`), Python API (`run_query`, `async_query`), and benchmark CLI share identical execution paths, deterministic planners, and store containers.
4. **Independent Provenance Verification:** Benchmark evaluation runner strictly validates coordinate offsets, figure-crop identities, and body-to-metadata alignments, rejecting any ungrounded assertions.
