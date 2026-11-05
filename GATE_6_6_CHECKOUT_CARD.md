# Gate 6.6 Checkout Card: Diagnostic Prototype and Replay Coverage Ledger

**Correction for Gate 6.7 review:** This card records a deterministic diagnostic prototype. Its historical scores do not independently qualify a reader, establish source-supported answer accuracy, or measure a retrieval-versus-reader delta. `PASS_SUPPORTED` in the stored results is the legacy scorer label. The source/results/replay receipts are preserved; only this reporting is corrected. See [Gate 6.7](GATE_6_7_INDEPENDENT_EVALUATION_CARD.md) for the replacement evaluation.

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `6ce50e0` (`v1.6.5.1-closeout-hygiene` / `v1.6.5-unified-provenance-and-path`)  
**Target Branch:** `feat/gate-6-6-reader-qualification` $\rightarrow$ `main`  
**Release Tag:** `v1.6.6-reader-qualification`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Corrected Executive Summary and Recorded Verification

`src/reader_qualification.py` builds its gold packet from the completed answer returned by `answer_whole_standard_question`. Arms A/B contain answer fragments selected partly by question keywords; arm C contains the complete generated answer. `compose_from_gold_arm` copies the supplied text into the response. The retrieved track calls the same engine with `DeterministicQuestionPlanner`. This is a deterministic answer-fragment diagnostic, with no fresh candidate-reader or DeepSeek invocation in the evaluator.

The preserved `results.json` records Arm A **2/24 (8.33%)**, Arm B **15/24 (62.50%)**, Arm C **24/24 (100%)**, and deterministic retrieved track **24/24 (100%)**. These are legacy harness scores. The numeric zero delta is circular; it does not isolate retrieval from reader interpretation. The 24 cases include 20 previously exposed Gate 6.3 cases and four diagnostic controls, so they remain development/regression material.

The scorer checks required/forbidden text and structural provenance metadata. A bounded adversarial check using negated required facts and an unrelated but structurally valid Table A1 citation still returns `PASS_SUPPORTED`. Consequently, passing these checks does not establish claim-level support or citation relevance.

Useful delivered work remains available: the diagnostic interfaces and taxonomy scaffolding; replay coverage accounting separating 14 genuine DeepSeek cassettes from six quarantined synthetic fixtures; CLI/application diagnostic paths; and the historical 54-artifact lock ledger. This correction does not invalidate replay quarantine or source-store integrity. Previously recorded software checks are historical verification evidence, not independent answer-quality adjudication.

The matrix below is reconciled to stored case records: `G63-BLIND13` passes recorded arms A/B and `G63-BLIND15` passes recorded arm B. No historical JSON receipt has been rewritten.

---

## 2. Recorded Gate 6.6 Diagnostic Results Across Four Tracks


| QID | Benchmark Query Text | Status | Page / PDF | Evidence Locator | Crop Path | Arm A (Coarse) | Arm B (Crop+Caption) | Arm C (Full Gold) | Retrieved (Deterministic) |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| `G63-BLIND01` | What is acetylene feather? | PASS | 6 / 18 | `clause4:term:acetylene feather` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND02` | Define GTAW? | PASS | 69 / 81 | `table_a1:process_letter_designations` | `None` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND03` | What is the Rotation of Face for Flat Fillet Weld? | PASS | 103 / 115 | `figure_b16b:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b16b_p103_crop_300.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND04` | What figure shows the position of beam, filler material, gun or torch? | PASS | 112 / 124 | `figure_b21:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b21_p112_crop_300.png` | FAIL (`BINDING_PROV`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND05` | What are the applicable weld types for a T-Joint? | PASS | 82 / 94 | `figure_b1:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b1_p82_crop_300.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND06` | How many different energy sources are there in Brazing and Soldering? | PASS | 79 / 91 | `figure_a6:brazing_and_soldering` | `storage/evidence_v2/a6_ingest_001/a6_crop_300.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND07` | What is FRW, RSEW, and RSW? | PASS | 70 / 82 | `table_a1:process_letter_designations` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND08` | List all the Solid State Welding Processes | PASS | 78 / 90 | `figure_a5:solid_state_welding` | `storage/evidence_v2/a5_ingest_001/a5_crop_300.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND09` | Is block Brazing and Shielded carbon arc welding Obsolete processes? | PASS | 74 / 86 | `table_a5:obsolete_processes` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND10` | What is the difference between FLSP, FLSP-P, and FLSP-W? | PASS | 70 / 82 | `table_a1:process_letter_designations` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND11` | What is a block sequence, what figure illustrates it, and how does AWS A3.0 define and distinguish all of its cross-referenced sequence terms? | PASS | 114 / 126 | `figure_b23:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b23_p114_crop_300.png` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND12` | Define effective throat (including how it is determined when a fillet weld is combined with a partial joint penetration groove weld), identify the figures that illustrate it, and provide the definitions of its cross-referenced throat terms. | PASS | 127 / 139 | `figure_b26:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b26_p127_crop_300.png` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND13` | Which figure in AWS A3.0 shows the schematic of the Friction Stir Welding process, what are the 10 numbered items in its Key, and how does the standard define the advancing side versus the retreating side of the weld? | PASS | 150 / 162 | `figure_b46:schematic_key` | `None` | **PASS** | **PASS** | **PASS** | **PASS** |
| `G63-BLIND14` | Which figure and sub-diagram illustrate the placement of temper beads and toe temper beads in groove, fillet, and overlay welds, how is the distance S measured according to the figure's notes, what approximate offset dimension is specified for the first layer temper beads, and how does Clause 4 define temper pass, temper bead, temper bead sequence, toe temper pass, and toe temper bead? | PASS | 116 / 128 | `figure_b23:panel_j` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b23_p116_crop_300.png` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND15` | How does AWS A3.0 define reentrant angle, bead reentrant angle, and toe reentrant angle, which figure sub-diagrams illustrate them, and what angular condition at the weld toe, weld root, or weld bead toe defines overlap in fusion welding? | PASS | 136 / 148 | `figure_b32:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b32_p136_crop_300.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G63-BLIND16` | List all six application modes and their letter designation suffixes from Table A4, explain the rule and format for appending them to a process or process variation designation, and give the Clause 4 definitions that distinguish the six application modes. | PASS | 74 / 86 | `table_a4:suffix:-AU` | `None` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND17` | Decode the letter designations LBC, LBC-A, LBC-EV, LBC-IG, LBC-O and EBW, EBW-HV, EBW-MV, EBW-NV from Annex A (Tables A1–A3), and state how Clause 4 defines each variation, including the exact operating pressure ranges in pascals and torr for the electron beam welding variations. | PASS | 70 / 82 | `table_a1:process_letter_designations` | `None` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND18` | According to the Foreword and Annex C, under what specific exception does AWS A3.0 classify a term as both "nonstandard and incorrect"? Identify the electrical circuit terms in Clause 4 that carry this "nonstandard and incorrect" designation, and provide the definitions of the standard terms that must be used instead (including the safety distinction with ground connection in Figure B34). | PASS | 140 / 152 | `figure_b34:diagram_details` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b34_p140_crop_300.png` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND19` | Explain two major terminology revisions documented in Annex C (Clauses C1.5.6 and C1.5.7) and Annex D of AWS A3.0:2020: (1) Why was parallel joint introduced to replace edge joint among the five basic joint types, and how are both terms defined in Clause 4? (2) How did the 13th edition change the status of nondestructive evaluation, nondestructive inspection (NDI), and nondestructive testing (NDT) relative to nondestructive examination (NDE), and why was the definition of nondestructive examination (NDE) itself modified? | PASS | 159 / 171 | `annex_c:decision:C1.5.6` | `None` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G63-BLIND20` | Compare the resistance spot welding waveforms in Figure B49 (Pulsation Welding Waveform) and Figure B50 (Single-Pulse Resistance Spot Welding Waveform): how does Clause 4 distinguish weld time, resistance welding from weld interval, resistance welding, and cool time, resistance welding from quench time, resistance welding? Additionally, define the sequential cycle intervals shown across Figures B49 and B50: squeeze time, preweld interval, preheat time, upslope time, pulse time, downslope time, temper time, hold time, postweld interval, forge-delay time, and off time. | PASS | 153 / 165 | `figure_b49:interval:upslope` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b49_300dpi.png` | FAIL (`READER_INTERP`) | FAIL (`READER_INTERP`) | **PASS** | **PASS** |
| `G66-DIAG01` | What is the minimum preheat temperature in degrees Fahrenheit for 2-inch ASTM A514 plate in AWS D1.1 Table 5.8? | REFUSAL_OUT_OF_SCOPE | `None` / `None` | `None` | `None` | **PASS** | **PASS** | **PASS** | **PASS** |
| `G66-DIAG02` | What does the designation GMAW-X-AU stand for in AWS A3.0? | NOT_IN_STANDARD | 69 / 81 | `table_a1:process_letter_designations` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G66-DIAG03` | Is atomic hydrogen welding (AHW) an obsolete process in Table A5 or an active process in Table A1? | PASS | 74 / 86 | `table_a5:obsolete_processes` | `None` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |
| `G66-DIAG04` | In Figure B53, what welding cycle traces illustrate upslope and downslope intervals? | PASS | 157 / 169 | `figure_b53:interval:upslope_and_downslope` | `storage/evidence_v2/annex_b_complete_001/crops/figure_b53_300dpi.png` | FAIL (`READER_INTERP`) | **PASS** | **PASS** | **PASS** |

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
| 52 | `storage/evidence_v2/phase6_6_reader_qualification_001/questions.json` | `37fb22ce12235042e2a8f84aabca2011a45d81ebdf34cc764b9e0a1ffcc7ea2d` | MATCH |
| 53 | `storage/evidence_v2/phase6_6_reader_qualification_001/gold_packets.json` | `030834a2abd05322248f77e8a8811ded57b400e4760b7091259d5b0415fd5386` | MATCH |
| 54 | `storage/evidence_v2/phase6_6_reader_qualification_001/results.json` | `8c9d29b039e069c075fb9046a116322d328256008d3ca4115bb8d69ffddbd20a` | MATCH |

---

## 5. Architectural Enhancements & Verification Summary

1. **Recorded Answer-Fragment Progression:** Arm A (`8.33%`), Arm B (`62.50%`), and Arm C (`100.00%`) are scores from answer-derived inputs. They do not establish the evidence budget a reader requires or isolate reader capability from retrieval.
2. **Diagnostic Failure Separation:** Deterministically classifies outcomes into `PASS_SUPPORTED`, `EXTRACTION_FAILURE`, `RETRIEVAL_FAILURE`, `READER_INTERPRETATION_FAILURE`, `EVIDENCE_BINDING_OR_PROVENANCE_FAILURE`, and `ABSTENTION_FAILURE`.
3. **Honest Offline Replay Accounting:** Separates the 14 genuine `DeepSeek-V4.1` replay cassettes from the 6 quarantined synthetic planner fixtures across all benchmark suites in `storage/manifests/replay_coverage_manifest.json`.
4. **Offline Socket-Isolated Test Suite:** Verified `27/27` tests passing across `test_gate_6_6_reader_qualification.py`, `test_gate_6_5_provenance_and_shared_path.py`, `test_gate_6_4_comprehensive_enhancements.py`, and `test_gate_6_3_blind_hardening.py` with all 54 cryptographic locks intact.
