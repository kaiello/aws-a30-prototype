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
| `G63-BLIND01` | What is acetylene feather? | PASS | 6 | 18 | `clause4:term:acetylene feather` | `None` | acetylene feather, carburizing, oxyacetylene flame, Figure B40 | PASS |
| `G63-BLIND02` | Define GTAW? | PASS | 69 | 81 | `table_a1:process_letter_designations` | `None` | gas tungsten arc welding, GTAW, tungsten electrode, Figure B36 | PASS |
| `G63-BLIND03` | What is the Rotation of Face for Flat Fillet Weld? | PASS | 103 | 115 | `figure_b16b:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b16b_p103_crop_300.png` | 150° to 210°, Figure B16B, Flat | PASS |
| `G63-BLIND04` | What figure shows the position of beam, filler material, gun or torch? | PASS | 112 | 124 | `figure_b21:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b21_p112_crop_300.png` | Figure B21, Position of Beam, Filler Material, Gun, or Torch | PASS |
| `G63-BLIND05` | What are the applicable weld types for a T-Joint? | PASS | 82 | 94 | `figure_b1:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b1_p82_crop_300.png` | Figure B1, T-Joint, fillet, bevel-groove | PASS |
| `G63-BLIND06` | How many different energy sources are there in Brazing and Soldering? | PASS | 79 | 91 | `figure_a6:brazing_and_soldering` | `storage/evidence_v2/a6_ingest_001/a6_crop_300.png` | Figure A6, Chemical, Electrical, 2 | PASS |
| `G63-BLIND07` | What is FRW, RSEW, and RSW? | PASS | 70 | 82 | `table_a1:process_letter_designations` | `None` | friction welding, FRW, resistance seam welding, RSEW | PASS |
| `G63-BLIND08` | List all the Solid State Welding Processes | PASS | 78 | 90 | `figure_a5:solid_state_welding` | `storage/evidence_v2/a5_ingest_001/a5_crop_300.png` | coextrusion welding, CEW, cold welding, CW | PASS |
| `G63-BLIND09` | Is block Brazing and Shielded carbon arc welding Obsolete processes? | PASS | 74 | 86 | `table_a5:obsolete_processes` | `None` | Table A5, obsolete, block brazing, BB | PASS |
| `G63-BLIND10` | What is the difference between FLSP, FLSP-P, and FLSP-W? | PASS | 70 | 82 | `table_a1:process_letter_designations` | `None` | flame spraying, FLSP, powder flame spraying, FLSP-P | PASS |
| `G63-BLIND11` | What is a block sequence, what figure illustrates it, and how does AWS A3.0 define and distinguish all of its cross-referenced sequence terms? | PASS | 114 | 126 | `figure_b23:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b23_p114_crop_300.png` | block sequence, Figure B23, cascade sequence, cross-sectional sequence | PASS |
| `G63-BLIND12` | Define effective throat (including how it is determined when a fillet weld is combined with a partial joint penetration groove weld), identify the figures that illustrate it, and provide the definitions of its cross-referenced throat terms. | PASS | 127 | 139 | `figure_b26:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b26_p127_crop_300.png` | effective throat, partial joint penetration groove weld, B25, actual throat | PASS |
| `G63-BLIND13` | Which figure in AWS A3.0 shows the schematic of the Friction Stir Welding process, what are the 10 numbered items in its Key, and how does the standard define the advancing side versus the retreating side of the weld? | PASS | 150 | 162 | `figure_b46:schematic_key` | `None` | Figure B46, Base Metal, Direction of Tool Rotation, Weld Tool | PASS |
| `G63-BLIND14` | Which figure and sub-diagram illustrate the placement of temper beads and toe temper beads in groove, fillet, and overlay welds, how is the distance S measured according to the figure's notes, what approximate offset dimension is specified for the first layer temper beads, and how does Clause 4 define temper pass, temper bead, temper bead sequence, toe temper pass, and toe temper bead? | PASS | 116 | 128 | `figure_b23:panel_j` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b23_p116_crop_300.png` | Figure B23, (J), distance S, parallel to the base metal surface | PASS |
| `G63-BLIND15` | How does AWS A3.0 define reentrant angle, bead reentrant angle, and toe reentrant angle, which figure sub-diagrams illustrate them, and what angular condition at the weld toe, weld root, or weld bead toe defines overlap in fusion welding? | PASS | 136 | 148 | `figure_b32:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b32_p136_crop_300.png` | reentrant angle, bead reentrant angle, toe reentrant angle, Figure B32 | PASS |
| `G63-BLIND16` | List all six application modes and their letter designation suffixes from Table A4, explain the rule and format for appending them to a process or process variation designation, and give the Clause 4 definitions that distinguish the six application modes. | PASS | 74 | 86 | `table_a4:suffix:-AU` | `None` | Table A4, -AD, -AU, -MA | PASS |
| `G63-BLIND17` | Decode the letter designations LBC, LBC-A, LBC-EV, LBC-IG, LBC-O and EBW, EBW-HV, EBW-MV, EBW-NV from Annex A (Tables A1–A3), and state how Clause 4 defines each variation, including the exact operating pressure ranges in pascals and torr for the electron beam welding variations. | PASS | 70 | 82 | `table_a1:process_letter_designations` | `None` | laser beam cutting, LBC, laser beam air cutting, LBC-A | PASS |
| `G63-BLIND18` | According to the Foreword and Annex C, under what specific exception does AWS A3.0 classify a term as both "nonstandard and incorrect"? Identify the electrical circuit terms in Clause 4 that carry this "nonstandard and incorrect" designation, and provide the definitions of the standard terms that must be used instead (including the safety distinction with ground connection in Figure B34). | PASS | 140 | 152 | `figure_b34:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b34_p140_crop_300.png` | personal safety, ground clamp, ground lead, welding ground | PASS |
| `G63-BLIND19` | Explain two major terminology revisions documented in Annex C (Clauses C1.5.6 and C1.5.7) and Annex D of AWS A3.0:2020: (1) Why was parallel joint introduced to replace edge joint among the five basic joint types, and how are both terms defined in Clause 4? (2) How did the 13th edition change the status of nondestructive evaluation, nondestructive inspection (NDI), and nondestructive testing (NDT) relative to nondestructive examination (NDE), and why was the definition of nondestructive examination (NDE) itself modified? | PASS | 159 | 171 | `annex_c:decision:C1.5.6` | `None` | parallel joint, edge joint, Clause 4, Table D5 | PASS |
| `G63-BLIND20` | Compare the resistance spot welding waveforms in Figure B49 (Pulsation Welding Waveform) and Figure B50 (Single-Pulse Resistance Spot Welding Waveform): how does Clause 4 distinguish weld time, resistance welding from weld interval, resistance welding, and cool time, resistance welding from quench time, resistance welding? Additionally, define the sequential cycle intervals shown across Figures B49 and B50: squeeze time, preweld interval, preheat time, upslope time, pulse time, downslope time, temper time, hold time, postweld interval, forge-delay time, and off time. | PASS | 153 | 165 | `figure_b49:interval:upslope` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b49_300dpi.png` | Figure B49, Figure B50, weld time, weld interval | PASS |

---

## 3. Cryptographic Lock Ledger (All 51 Locked Artifacts)

| Index | Rel Path | SHA-256 Digest | Status |
| :---: | :--- | :--- | :---: |
| 1 | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | MATCH |
| 2 | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | MATCH |
| 3 | `storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | MATCH |
| 4 | `storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | MATCH |
| 5 | `storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | MATCH |
| 6 | `storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | MATCH |
| 7 | `storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | MATCH |
| 8 | `storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json` | `70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479` | MATCH |
| 9 | `storage/evidence_v2/phase5_hardening_001/adversarial_questions.json` | `0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9` | MATCH |
| 10 | `storage/evidence_v2/phase5_hardening_001/rubric.json` | `df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981` | MATCH |
| 11 | `storage/evidence_v2/phase5_hardening_001/results.json` | `92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273` | MATCH |
| 12 | `storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json` | `ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57` | MATCH |
| 13 | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b` | MATCH |
| 14 | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74` | MATCH |
| 15 | `storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json` | `59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f` | MATCH |
| 16 | `storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079` | MATCH |
| 17 | `storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d` | MATCH |
| 18 | `storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a` | MATCH |
| 19 | `storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | MATCH |
| 20 | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | MATCH |
| 21 | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | MATCH |
| 22 | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | MATCH |
| 23 | `storage/manifests/coverage_manifest.json` | `8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e` | MATCH |
| 24 | `storage/manifests/latency_benchmark.json` | `bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c` | MATCH |
| 25 | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac` | MATCH |
| 26 | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427` | MATCH |
| 27 | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8` | MATCH |
| 28 | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057` | MATCH |
| 29 | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42` | MATCH |
| 30 | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7` | MATCH |
| 31 | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5` | MATCH |
| 32 | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf` | MATCH |
| 33 | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432` | MATCH |
| 34 | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993` | MATCH |
| 35 | `storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | MATCH |
| 36 | `storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json` | `bb18c854ee6c590dfa83955939b0c9fd810a4cd633ee6d0f64eaf9f0168fe6c3` | MATCH |
| 37 | `storage/evidence_v2/phase6_2_generalization_holdout_001/results.json` | `dfe96330a00328fdb79d594353be826c6d3ccaa10063b62b0a83e0f560886f60` | MATCH |
| 38 | `storage/model_replays/deepseek_v4_1_flash_1017/7e9982c36d0fcfa591123da74ceb0e7c7da002981d4379693a07eb61d3c40d29.json` | `f8cd0108b311f27868d5b9fa59b9478ff4128492be28d361d7b793f6011bc21f` | MATCH |
| 39 | `storage/model_replays/deepseek_v4_1_flash_1017/3d6a2cbb61def68a41a52cdec81712a85cd65f7ed52c2e6505bc280821dacf9a.json` | `cb9ac95d98a5aac82c61f4d2d4b34438b452268f7e0221996fdac9e55edac570` | MATCH |
| 40 | `storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | MATCH |
| 41 | `storage/evidence_v2/phase6_2_generalization_holdout_002/rubric.json` | `e23085ad83f13142a7bc84a1ddc3a89459b72b8c894c966b98d4d9b6587b24c4` | MATCH |
| 42 | `storage/evidence_v2/phase6_2_generalization_holdout_002/results.json` | `0d9f8a1bf4a88861ab0c6fa27ec6cf0a88fd8a1f1cc257c02d25433396b53b2b` | MATCH |
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
