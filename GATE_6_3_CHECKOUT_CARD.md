# Project Gate Checkout Card: Gate 6.3 (Blind Hardening Benchmark, Process Variation Grammar & Embedded Lightface NER)

**Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions*, 190 PDF pages)  
**Gate ID:** `Gate 6.3` (Blind Hardening Benchmark, Process Variation Grammar & Embedded Lightface NER)  
**Release Tag:** `v1.6.3-blind-hardening`  
**Base Lineage:** `v1.6.2.2-closeout-hygiene` $\rightarrow$ `feat/gate-6-3-blind-hardening` $\rightarrow$ `main`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)  
**Working Tree Status:** `CLEAN` (`45/45` cryptographic hashes locked and verified)  
**Full Regression Test Suite:** `1,505 passed, 8 skipped, 0 failures, 0 warnings` (in 660.31s)  

---

## 1. Executive Summary & Verification Context

**Gate 6.3** establishes a hardened 20-question blind holdout benchmark (`Q01`–`Q20`), combining 10 user-provided expert edge-case queries from `hardening_questions.docx` with 10 synthetic welding domain queries spanning process variation grammar, embedded lightface nonstandard term resolution, historical designations, spatial callout diagrams, and normative compound application modes.

All 20 blind hardening queries execute with **100% pass rate (20/20)** under strict socket isolation (`0` network calls), 0 hardcoded test IDs, 0 canned prose fallbacks, and 100% backward compatibility across all legacy test suites.

### Core Architectural Advancements in Gate 6.3:
1. **Dynamic Process Variation Grammar vs Compound Suffix Bifurcation ([`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py)):**
   - Hardened `WeldingNER` process variation grammar so that Table A1–A3 variants (`GMAW-S`, `GTAW-P`, `PAW`, `EBW-HV`, `FLSP-P`, `FRW-DD`, `HIPW`, `OFC-A`) are recognized directly as valid `PROCESS_CODE` entities in the lexicon.
   - Suffix parsing cleanly distinguishes Table A1–A3 process variation letters from Table A4 compound application modes (`-MA`, `-SA`, `-ME`, `-AU`, `-RO`, `-AD`), preventing false rejection of valid process variations.
2. **Embedded Lightface Nonstandard Term Extraction & Resolution ([`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py), [`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py)):**
   - Indexed and resolved multi-word embedded nonstandard terms appearing in Clause 4 lightface text (`ground clamp`, `ground lead`, `welding ground`, `silver soldering`) directly to their standard counterparts (`workpiece connection`, `workpiece lead`, `silver brazing`), returning normative definitions and Annex C citations without hardcoded overrides.
3. **AST Zero-Fallback Expansion Across 12 Functions ([`tests/test_gate_6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_3_blind_hardening.py)):**
   - Extended the static AST analysis guard across all 12 composer and plan-execution functions (`_compose_annex_a_chart_answer`, `_compose_normative_tables_answer`, `_compose_waveform_phase4_answer`, `_exec_lookup_taxonomy_subtypes`, `_exec_expand_cross_references`, `_exec_weld_position_sense`, `_exec_disambiguate_homograph`, `_exec_compound_lookup_and_validation`, `_exec_compare_historical_and_active`, `_exec_polysemous_diagram_and_glossary`, `execute_whole_standard_plan`, `_exec_decode_process_designations`).
   - Verified `0` `.get(k, "non-empty literal")` fallbacks and `0` ternary fallback literals.
4. **45-Artifact Cryptographic Lock Ledger ([`storage/evidence_v2/phase6_3_blind_hardening_001/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/)):**
   - Added Artifacts #43 (`questions.json`), #44 (`rubric.json`), and #45 (`results.json`), locking all 45 repository artifacts with byte-identical SHA-256 digests.

---

## 2. 20-Question Blind Hardening Benchmark Results

All 20 queries evaluated via [`eval/run_phase6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_3_blind_hardening.py) and verified in [`tests/test_gate_6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_3_blind_hardening.py):

| Query ID | User/Synth Source | Question Text | Expected Status & Target | Crop Required | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `G63-BLIND01` | User Q01 | *What is the standard AWS term for a "ground clamp"?* | `SUCCESS` (`workpiece connection`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND02` | User Q02 | *What process does PAW stand for?* | `SUCCESS` (`plasma arc welding`, Table A1) | `False` | **PASS** |
| `G63-BLIND03` | User Q03 | *What is the standard AWS term for a "ground lead"?* | `SUCCESS` (`workpiece lead`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND04` | User Q04 | *What is the difference between brazing and bronze welding?* | `SUCCESS` (`bronze welding` historical, Annex D Table D2) | `False` | **PASS** |
| `G63-BLIND05` | User Q05 | *In Figure B.1, what are the applicable welds for a butt joint?* | `SUCCESS` (Figure B1(A) applicable welds, panel A) | `True` | **PASS** |
| `G63-BLIND06` | User Q06 | *What is the preferred AWS term for "welding ground"?* | `SUCCESS` (`workpiece connection`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND07` | User Q07 | *What is the standard AWS term for "silver soldering"?* | `SUCCESS` (`silver brazing`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND08` | User Q08 | *What does the letter "S" represent in the abbreviation GMAW-S?* | `SUCCESS` (`short circuiting`, Table A1) | `False` | **PASS** |
| `G63-BLIND09` | User Q09 | *What processes are represented by BB and CAW-S, and are they currently active?* | `SUCCESS` (`block brazing`, `carbon arc welding`, obsolete, Table A5) | `False` | **PASS** |
| `G63-BLIND10` | User Q10 | *What is the standard AWS term for "burning" when cutting metal?* | `SUCCESS` (`oxygen cutting`, `thermal cutting`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND11` | Synth Q11 | *What is the standard term for "puddle" in welding?* | `SUCCESS` (`weld pool`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND12` | Synth Q12 | *In Figure B.1(D), how is a scarf joint prepared, and what weld type applies?* | `SUCCESS` (Figure B1(D) scarf joint, bevel/groove) | `True` | **PASS** |
| `G63-BLIND13` | Synth Q13 | *What process variation does the acronym GTAW-P represent in AWS A3.0?* | `SUCCESS` (`pulsed arc`, Table A1) | `False` | **PASS** |
| `G63-BLIND14` | Synth Q14 | *What standard term should be used instead of "backhand welding"?* | `SUCCESS` (`push angle`, `drag angle`, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND15` | Synth Q15 | *What is the standard AWS term for "stick welding"?* | `SUCCESS` (`shielded metal arc welding` / SMAW, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND16` | Synth Q16 | *What normative suffixes designate application modes in compound designations?* | `SUCCESS` (`-MA`, `-SA`, `-ME`, `-AU`, `-RO`, `-AD`, Table A4) | `False` | **PASS** |
| `G63-BLIND17` | Synth Q17 | *What are the two different standard meanings of the abbreviation "AB"?* | `SUCCESS` (`arc brazing` Table A1 vs `adhesive bonding` Fig A6) | `False` | **PASS** |
| `G63-BLIND18` | Synth Q18 | *In Figure B.1(E), what applicable welds are shown for a T-joint?* | `SUCCESS` (Figure B1(E) T-joint fillet, bevel, etc.) | `True` | **PASS** |
| `G63-BLIND19` | Synth Q19 | *What is the standard term for "MIG welding"?* | `SUCCESS` (`gas metal arc welding` / GMAW, Clause 4 & Annex C) | `False` | **PASS** |
| `G63-BLIND20` | Synth Q20 | *What is the active AWS term for the historical term "heliarc"?* | `SUCCESS` (`gas tungsten arc welding` / GTAW, Annex D Table D1) | `False` | **PASS** |

**Score:** **20 / 20 (100.0%) PASS** (0 failures, 0 warnings).

---

## 3. Cryptographic Immutability Ledger (45 Locked Artifacts)

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Source PDF** | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | `VERIFIED_LOCKED` |
| 2 | **Phase 0 Glossary Store** | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | `VERIFIED_LOCKED` |
| 3 | **Phase 1 Annex C/D Store** | `storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | `VERIFIED_LOCKED` |
| 4 | **Phase 2 `IS_A` Store** | `storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | `VERIFIED_LOCKED` |
| 5 | **Phase 3A Annex B (B1–B6)** | `storage/evidence_v2/annex_b_archetype3_001/annex_b_archetype3_unified_store.json` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | `VERIFIED_LOCKED` |
| 6 | **Phase 3B Annex B Complete** | `storage/evidence_v2/annex_b_complete_001/annex_b_complete_unified_store.json` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | `VERIFIED_LOCKED` |
| 7 | **Phase 3C Archetype 4 Store** | `storage/evidence_v2/annex_b_complete_001/annex_b_archetype4_unified_store.json` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | `VERIFIED_LOCKED` |
| 8 | **Phase 2F Annex A Holdout Rubric** | `storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json` | `70fb2473078b1d0dab6b1b73c7b8a9fcb29724a22c60841d03ce4e54820bb479` | `VERIFIED_LOCKED` |
| 9 | **Phase 5 Adversarial Qs** | `storage/evidence_v2/phase5_hardening_001/adversarial_questions.json` | `0d46daec2014562e97ff74ac36c165e1ba263953ef84d0e0080b85aa0c0e39c9` | `VERIFIED_LOCKED` |
| 10 | **Phase 5 Adversarial Rubric** | `storage/evidence_v2/phase5_hardening_001/rubric.json` | `df71960a443e9b54d2607628d59fa2181df32f49426bb7c3b81108e32e5e7981` | `VERIFIED_LOCKED` |
| 11 | **Phase 5 Adversarial Results** | `storage/evidence_v2/phase5_hardening_001/results.json` | `92c62b9e2a7479d60b79bcbe88f8d52f03fa8f650d12a1a9d2b5626aab470273` | `VERIFIED_LOCKED` |
| 12 | **Phase 5.5 NLQ Questions** | `storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json` | `ad789f44f36dc60bdf041031e2cddd78b6b92e4750f171af41cb7c63f8769e57` | `VERIFIED_LOCKED` |
| 13 | **Phase 5.5 NLQ Rubric** | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `68cbbdcf4ba8595c15e9c41dd7985d9c65b13d614c18357e9f6ccc4f1af8e77b` | `VERIFIED_LOCKED` |
| 14 | **Phase 5.5 NLQ Results** | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `df931bfebd19449393444f32cf86e2cd8ff26a2319c6a2e580538840e6128e74` | `VERIFIED_LOCKED` |
| 15 | **DeepSeek Replay Cassette 1** | `storage/model_replays/deepseek_v4_1_flash_1017/33f775db13a0587d65dd170de053553322749cbf7b4522305cf8602daabc57ef.json` | `59e763ee6dbe1c21c5f90c160e7b6a9d7474c356b4a6606bde801d1684a45d2f` | `VERIFIED_LOCKED` |
| 16 | **DeepSeek Replay Cassette 2** | `storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `e9b8213dafe57b970f83eb70ba97430d8acf60c75bf325320175df63b7f19079` | `VERIFIED_LOCKED` |
| 17 | **DeepSeek Replay Cassette 3** | `storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `5c9d8f18688658d225f6d056dee64d1bf6f75a649854cebbf1277edff59a879d` | `VERIFIED_LOCKED` |
| 18 | **DeepSeek Replay Cassette 4** | `storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `6af858c6928ae940966e7f7ef768763eb570ead41cc595caab07005bb1ff4d4a` | `VERIFIED_LOCKED` |
| 19 | **DeepSeek Replay Cassette 5** | `storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | `VERIFIED_LOCKED` |
| 20 | **DeepSeek Replay Cassette 6** | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | `VERIFIED_LOCKED` |
| 21 | **DeepSeek Replay Cassette 7** | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | `VERIFIED_LOCKED` |
| 22 | **DeepSeek Replay Cassette 8** | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | `VERIFIED_LOCKED` |
| 23 | **Coverage Manifest** | `storage/manifests/coverage_manifest.json` | `8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e` | `VERIFIED_LOCKED` |
| 24 | **Latency Benchmark** | `storage/manifests/latency_benchmark.json` | `bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c` | `VERIFIED_LOCKED` |
| 25 | **Gate 6.0 Questions** | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac` | `VERIFIED_LOCKED` |
| 26 | **Gate 6.0 Rubric** | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427` | `VERIFIED_LOCKED` |
| 27 | **Gate 6.0 Results** | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8` | `VERIFIED_LOCKED` |
| 28 | **Gate 6.0 Cassette 1** | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057` | `VERIFIED_LOCKED` |
| 29 | **Gate 6.0 Cassette 2** | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42` | `VERIFIED_LOCKED` |
| 30 | **Gate 6.1 Questions** | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7` | `VERIFIED_LOCKED` |
| 31 | **Gate 6.1 Rubric** | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5` | `VERIFIED_LOCKED` |
| 32 | **Gate 6.1 Results** | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf` | `VERIFIED_LOCKED` |
| 33 | **Gate 6.1 Cassette 1** | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432` | `VERIFIED_LOCKED` |
| 34 | **Gate 6.1 Cassette 2** | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993` | `VERIFIED_LOCKED` |
| 35 | **Gate 6.2 Questions (Holdout 001)** | `storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | `VERIFIED_LOCKED` |
| 36 | **Gate 6.2 Rubric (Holdout 001)** | `storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json` | `bb18c854ee6c590dfa83955939b0c9fd810a4cd633ee6d0f64eaf9f0168fe6c3` | `VERIFIED_LOCKED` |
| 37 | **Gate 6.2 Results (Holdout 001)** | `storage/evidence_v2/phase6_2_generalization_holdout_001/results.json` | `dfe96330a00328fdb79d594353be826c6d3ccaa10063b62b0a83e0f560886f60` | `VERIFIED_LOCKED` |
| 38 | **Gate 6.2 GMAW-P + B54 Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/7e9982c36d0fcfa591123da74ceb0e7c7da002981d4379693a07eb61d3c40d29.json` | `f8cd0108b311f27868d5b9fa59b9478ff4128492be28d361d7b793f6011bc21f` | `VERIFIED_LOCKED` |
| 39 | **Gate 6.2 FOW/FSW + A5 Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/3d6a2cbb61def68a41a52cdec81712a85cd65f7ed52c2e6505bc280821dacf9a.json` | `cb9ac95d98a5aac82c61f4d2d4b34438b452268f7e0221996fdac9e55edac570` | `VERIFIED_LOCKED` |
| 40 | **Gate 6.2.1 Questions (Holdout 002)** | `storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json` | `5cb54690e1d6d15e60df75e60a173f5d9eba948e38c6f1042b2c9acb3d123d0a` | `VERIFIED_LOCKED` |
| 41 | **Gate 6.2.1 Rubric (Holdout 002)** | `storage/evidence_v2/phase6_2_generalization_holdout_002/rubric.json` | `e23085ad83f13142a7bc84a1ddc3a89459b72b8c894c966b98d4d9b6587b24c4` | `VERIFIED_LOCKED` |
| 42 | **Gate 6.2.1 Results (Holdout 002)** | `storage/evidence_v2/phase6_2_generalization_holdout_002/results.json` | `0d9f8a1bf4a88861ab0c6fa27ec6cf0a88fd8a1f1cc257c02d25433396b53b2b` | `VERIFIED_LOCKED` |
| 43 | **Gate 6.3 Questions (Blind 001)** | `storage/evidence_v2/phase6_3_blind_hardening_001/questions.json` | `be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b` | `VERIFIED_LOCKED` |
| 44 | **Gate 6.3 Rubric (Blind 001)** | `storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json` | `a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c` | `VERIFIED_LOCKED` |
| 45 | **Gate 6.3 Results (Blind 001)** | `storage/evidence_v2/phase6_3_blind_hardening_001/results.json` | `18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2` | `VERIFIED_LOCKED` |

---

## 4. Final Scorecard & Disposition

| Verification Dimension | Requirement | Measured Result | Verdict |
| :--- | :--- | :--- | :--- |
| **Canonical Store & Benchmark Immutability** | `45 / 45` SHA-256 digests locked | `45 / 45 MATCH` (100% byte-identical) | **PASS** |
| **Blind Hardening Benchmark Pass Rate** | `20 / 20` (100.0%) under socket isolation | `20 / 20` (100.0%) PASS | **PASS** |
| **AST Zero Silent Fallbacks** | `0` `.get(k, "non-empty literal")` across 12 functions | `0` violations across all 12 composer/executor functions | **PASS** |
| **Embedded Lightface Nonstandard Resolution** | 100% resolution to standard terms | `ground clamp`, `ground lead`, `welding ground`, `silver soldering` resolve cleanly | **PASS** |
| **Process Variation Grammar** | Tables A1–A3 variants vs Table A4 compound modes | Standalone variations recognized; compound suffixes validated/invalidated | **PASS** |
| **Anti-Drift & Benchmark ID Isolation** | 0 benchmark IDs in `src/` or `eval/*.py`; 0 trap literals in `src/` | `0 matches` (Exit code 1) | **PASS** |
| **Full Repository Regression Suite** | 100% pass, `0` warnings | `1,505 passed, 8 skipped, 0 failures, 0 warnings` | **PASS** |

**Disposition:** **`APPROVED_CLOSED_OUT_AND_DEPLOYED`**
