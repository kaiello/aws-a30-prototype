# Project Gate Checkout Card: Gate 6.1 (Polysemous Welding NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion)

**Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions*, 190 PDF pages)  
**Gate ID:** `Gate 6.1` (Polysemous Welding NER, 3-Tier Compound Grammar & Store-Compiled Semantic Graph Expansion)  
**Release Tag:** `v1.6.1-ner-semantic-graph`  
**Base Lineage:** `v1.6.0-ner-routing-skills` (`6110430`) $\rightarrow$ `feat/gate-6-1-ner-semantic-graph-expansion` $\rightarrow$ `main`  
**Audit Bundle:** [`GATE_6_FULL_AUDIT_BUNDLE.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_FULL_AUDIT_BUNDLE.md) & [`storage/gate_reviews/GATE_6_FULL_AUDIT_BUNDLE.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/gate_reviews/GATE_6_FULL_AUDIT_BUNDLE.md) (rebuilt via `python -B scripts/build_gate_6_bundle.py`)  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)  
**Working Tree Status:** `CLEAN` (`34/34` cryptographic hashes locked and verified)  
**Full Regression Test Suite:** `1,482 passed, 8 skipped, 0 failures, 0 warnings`  
**Author / Lead Developer:** Autonomous RAG Engineering Lead  
**Auditor / Reviewer:** Principal Reviewer & Systems Architect  
**Submission & Verification Date:** November 1, 2026  
**Final Closeout Disposition:** `APPROVED_CLOSED_OUT_AND_DEPLOYED`  

---

## 1. Executive Summary & Milestone Deliverables

This checkout card formalizes the forensic audit, implementation, and final production closeout of **Gate 6.1**, extending the deterministic NER and semantic routing architecture over the frozen 190-page `AWS A3.0M/A3.0:2020` multimodal standard.

### Deliverables Completed & Verified:

1. **Polysemous / Multi-Role Entity Spans in [`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py) (`NER-DRIFT-6.1-1`):**
   - Extended [`WeldingEntitySpan`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py#L18-L34) and [`WeldingNERReceipt`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py#L48-L74) serialization with `secondary_entity_types`, `linked_clause4_terms`, `linked_figures`, `linked_tables`, and `ambiguous_senses`.
   - Populated multi-role bindings: when a diagram callout (e.g., `theoretical throat`, `crater crack`) or process variation appears in Clause 4, links both `clause4_terms` and `figures`, ensuring target divisions include both `annex_b_spatial` and `clause4_glossary`.
   - Definitional intent promotion: queries with `define`, `defined`, `definition`, or `what is` promote `clause4_glossary` into planned execution actions alongside diagram callouts.

2. **3-Tier Compound Designation Grammar & Contextual Qualifier Binding in [`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py) (`NER-DRIFT-6.1-2` & `NER-DRIFT-6.1-4`):**
   - Upgraded [`parse_compound_designation()`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py#L734-L860) to decompose 3-tier designations `<BASE>[-<VARIATION>][-<MODE_SUFFIX>]` into constituent `BASE_PROCESS` (`FCAW`), `PROCESS_VARIATION` (`FCAW-G`), and `APPLICATION_MODE` (`-SA`).
   - Strict validation: rejects unstandardized variations (e.g., `FCAW-Z-SA` with `is_valid: False`), conflicting double mode suffixes (e.g., `PAW-AU-ME` with `is_valid: False`), and invalid mode suffixes (`GTAW-ZZ`).
   - Contextual sense disambiguation: binds weld position codes (`1G`, `1F`) based on surrounding tokens (`pipe` $\rightarrow$ `Figure B19(A)` / `Figure B20(A)`; `plate` $\rightarrow$ `Figure B17(A)` / `Figure B18(A)`; unqualified $\rightarrow$ both senses).
   - Homograph resolution: resolves `AB` based on surrounding context (`arc brazing` in `Figure A6` vs `adhesive bonding` in `Table A1`).

3. **Store-Compiled Semantic Concept Graph in [`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py) (`SEM-DRIFT-6.1-3`):**
   - Implemented in-memory [`SemanticConceptGraph`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py#L74-L125) tracking bidirectional `see_also_edges` (e.g., `throat of a fillet weld` $\leftrightarrow$ `theoretical throat`, `effective throat`, `actual throat`), `is_a_subtypes` (`flux cored arc welding` $\rightarrow$ `FCAW-G`, `FCAW-S`), `sibling_variations` (`FCAW-G` $\leftrightarrow$ `FCAW-S`), and diagram co-callouts.
   - Seed entity resolution booster: multi-term queries expand lateral neighborhood edges up to 2 hops.

4. **Whole-Standard Headless CLI `--expand` & Multi-Hop Composition ([`src/evidence_whole_standard_cli.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_whole_standard_cli.py) & [`src/evidence_phase4_bakeoff.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py)):**
   - `--expand "<query>"`: outputs structured JSON containing `query`, `ner_receipt`, `concept_graph_neighborhood`, and `ranked_target_figures`.
   - Multi-hop composition branches added in `execute_whole_standard_plan`:
     - `compound_designation_and_validation` (validates `OFC-A-MA` while refuting `FCAW-Z-SA` and `PAW-AU-ME`).
     - `compound_designation_and_diagram` (`FCAW-G-SA` + `Figure A4`, `PAW-AU` + `Figure B25`).
     - `homograph_and_position_disambiguation` (`AB` + `2F`).
     - `see_also_cross_references` (`throat of a fillet weld`).
     - `taxonomy_subtypes` (`flux cored arc welding` variations).
     - `angle_cluster` (`travel angle` family).

5. **Content-Addressed Gate 6.1 Replay Cassettes ([`storage/model_replays/deepseek_v4_1_flash_1017/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/model_replays/deepseek_v4_1_flash_1017/)):**
   - Created 2 content-addressed replay cassettes conforming to `compute_replay_key(prompt)`:
     - `a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` (`FCAW-G-SA` + `Figure A4`)
     - `b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` (`PAW-AU` + `Figure B25` throats)
   - Total replay cassettes locked in repository: **12**.
   - Verified strict offline execution (`0` network calls) with epistemic quarantine tag `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.

6. **Frozen 15-Query Gate 6.1 Benchmark ([`eval/run_phase6_1_semantic_graph.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_1_semantic_graph.py)):**
   - Executed against [`storage/evidence_v2/phase6_1_semantic_graph_001/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_1_semantic_graph_001/):
     - Slice 1 (Polysemous Callout & Definitional Intent Spans): 3/3 PASS
     - Slice 2 (3-Tier Compound Designation Decompositions): 3/3 PASS
     - Slice 3 (Contextual Sense & Qualifier Resolution): 3/3 PASS
     - Slice 4 (See also & Taxonomy Sibling Expansion): 3/3 PASS
     - Slice 5 (CLI `--expand` & Offline Replay Verification): 3/3 PASS
   - Overall Score: **15 / 15 passed (100.0%)**.

---

## 2. Cryptographic Immutability Ledger (34 Locked Artifacts)

`tests/test_gate_6_1_semantic_graph.py` verifies all 34 locked files match their exact SHA-256 hashes:

| # | Artifact ID | Canonical Repository Path | Locked SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Source PDF** | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | `VERIFIED_LOCKED` |
| 2 | **Phase 0 Glossary Store** | `storage/evidence_v2/clause4_ingest_001/glossary_store.json` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | `VERIFIED_LOCKED` |
| 3 | **Phase 1 Annex C/D Store** | `storage/evidence_v2/clause4_ingest_001/annex_c_d_store.json` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | `VERIFIED_LOCKED` |
| 4 | **Phase 2 IS_A Store** | `storage/evidence_v2/clause4_ingest_001/is_a_promotion_store.json` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | `VERIFIED_LOCKED` |
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
| 15 | **Gate 5.4 Replay Cassette 1** | `storage/model_replays/deepseek_v4_1_flash_1017/2dff4db48f1082c57700e16bc4cbbf9ef956973ba4182f2f71ee5a2be10c0e7b.json` | `83df23573ce7a052e6462744778103c8fcff537b98544c0fb4e226e648c68ff3` | `VERIFIED_LOCKED` |
| 16 | **Gate 5.4 Replay Cassette 2** | `storage/model_replays/deepseek_v4_1_flash_1017/04eeb64f51e06d9d0663ee8f6e2e5ae6c1f1f50a804fa18dbd83e29f3d699e03.json` | `5e807aa6365fec2e4823297a7dff66a4f5d0701064e43b67406a12b4899538fa` | `VERIFIED_LOCKED` |
| 17 | **Gate 5.4 Replay Cassette 3** | `storage/model_replays/deepseek_v4_1_flash_1017/37a44fbc76bb0610f44383a8b251a37c15e47854e4df9df602a8ebba1ae70823.json` | `eb1e427cae88d01d4a8217bb66f6e80b2a59a72cc94ae4a8c90374e2a14e9f90` | `VERIFIED_LOCKED` |
| 18 | **Gate 5.4 Replay Cassette 4** | `storage/model_replays/deepseek_v4_1_flash_1017/6321262d1061730032bbcc9be31215b3a4aeeabf32e921d7b0429f44db6cbfb8.json` | `b38e079fe03126be127c541b6c00326b5278c772b14589d972fc0028a3857e33` | `VERIFIED_LOCKED` |
| 19 | **Gate 5.5 Replay Cassette 1** | `storage/model_replays/deepseek_v4_1_flash_1017/b84e96a090b80d799a7d28127ec9304edd116bcec6976f7f7bf69ae0f4e590ea.json` | `d50b483130b30a268433d8c627a78017fe707f9cd0180e2cba6dacb7c7984592` | `VERIFIED_LOCKED` |
| 20 | **Gate 5.5 Replay Cassette 2** | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `ae0625dacb0a7541955f46d73cb6a85e2234363bc89a7c5771608d71feb069f2` | `VERIFIED_LOCKED` |
| 21 | **Gate 5.5 Replay Cassette 3** | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `e7114838a52b3d965c0c32cd8977f4e1c998bdad0ab07f5987d9b7825ddb134e` | `VERIFIED_LOCKED` |
| 22 | **Gate 5.5 Replay Cassette 4** | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `0513f4d16b5d6f72ae66688414ffce809000cd0e3444a8bea9db8e6ac6420621` | `VERIFIED_LOCKED` |
| 23 | **Coverage Manifest** | `storage/manifests/coverage_manifest.json` | `8fa510a5d4880f88e05fbf3c295992b9c5ae5274c65e46086ad08fee7c2d553e` | `VERIFIED_LOCKED` |
| 24 | **Latency Benchmark** | `storage/manifests/latency_benchmark.json` | `bc4bb0edfd67bbea0d5204a6430ce6be5af508b07f2874a779a0c2bf230c614c` | `VERIFIED_LOCKED` |
| 25 | **Gate 6.0 Questions** | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `bf2fd3b05532cb76a0584cd1d6db8d3f1fe038ba632d539d8be94a4feb4f23ac` | `VERIFIED_LOCKED` |
| 26 | **Gate 6.0 Rubric** | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `602f37e0194a99ee6b3e52c95c1c76d9e57a3950a50ea7a5efd15c336645b427` | `VERIFIED_LOCKED` |
| 27 | **Gate 6.0 Results** | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `4023b5c13b8265f9a6085399e0176644df8119366ccc3ea920c098159f6ef8a8` | `VERIFIED_LOCKED` |
| 28 | **Gate 6.0 Compound + Chart Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `b5c11233c5389651c5ff6730ebb56b51e910042d8aada8f5b9ec7752f2c7d057` | `VERIFIED_LOCKED` |
| 29 | **Gate 6.0 Spatial Callout Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `178e40f106af85fd17e9a949877cf6b0ea3c469516e102efdc017d043635df42` | `VERIFIED_LOCKED` |
| 30 | **Gate 6.1 Questions** | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `aa16b7fcc444ca4c54bed8eb758a35bde3d9e8c3f64afbb7b75b0112ed0f45d7` | `VERIFIED_LOCKED` |
| 31 | **Gate 6.1 Rubric** | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `42e4e8c3d3fa9e7c32b61d1deafa3a5d42a36b72ab0ec2c4465268d3977457d5` | `VERIFIED_LOCKED` |
| 32 | **Gate 6.1 Results** | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `48b4dc84db39dfe0aa68f0e1610bb3fa8e27be546f0294319a11c9af1cafbccf` | `VERIFIED_LOCKED` |
| 33 | **Gate 6.1 3-Tier + Fusion Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `22bcf1de364e9ba87b604da2ee3e817516570d972b858616cd80018c9acbf432` | `VERIFIED_LOCKED` |
| 34 | **Gate 6.1 Compound + Throat Cassette** | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `72f97e7f8aae9bcef96b16d2f55fea24b9c99ae2068fed3dc8cae8a69efc4993` | `VERIFIED_LOCKED` |

---

## 3. Benchmark Verification Results

*Audit Reconciliation Note (Gate 6.2): Table updated to match canonical locked `ner_routing_questions.json` (SHA-256: `aa16b7fc...`) verbatim across all 15 queries.*

| Query ID | Category / Intent | Query Text | Status | Evidence Locator / Modality Provenance |
| :--- | :--- | :--- | :---: | :--- |
| `G61-SEM01` | Polysemous Span | Which diagram illustrates theoretical throat, effective throat, and actual throat, and how are they defined in Clause 4? | `PASS` | `Figure B25` (p. 123) + `Clause 4` (p. 58) |
| `G61-SEM02` | Polysemous Span | Which diagram illustrates root face and groove angle, and how is root face defined in Clause 4? | `PASS` | `Figure B6` (p. 87) + `Clause 4` (p. 50) |
| `G61-SEM03` | Polysemous Span | Which figure illustrates crack types including toe crack and underbead crack, and how is toe crack defined in Clause 4? | `PASS` | `Figure B33` (p. 137) + `Clause 4` |
| `G61-SEM04` | 3-Tier Grammar | What does the compound designation FCAW-G-SA stand for according to Table A1 and Table A4? | `PASS` | `Table A1` (p. 69) + `Table A4` (p. 74) |
| `G61-SEM05` | 3-Tier Grammar | What does the compound code GMAW-P-AU designate in AWS A3.0? | `PASS` | `Table A1` (p. 69) + `Table A4` (p. 74) |
| `G61-SEM06` | 3-Tier Grammar | Explain why OFC-A-MA is a valid designation while FCAW-Z-SA and PAW-AU-ME are rejected in AWS A3.0. | `PASS` | `Table A1` + `Table A4` (Validation Refutation) |
| `G61-SEM07` | Sense Disambiguation | Which diagram illustrates the 1G test position for pipe groove welding, and how is it defined? | `PASS` | `Figure B19(A)` (p. 111) + `Clause 4` (p. 5) |
| `G61-SEM08` | Sense Disambiguation | Which diagram illustrates the 1G test position for plate groove welding, and how is it defined? | `PASS` | `Figure B17(A)` (p. 109) + `Clause 4` (p. 5) |
| `G61-SEM09` | Sense Disambiguation | How are the homograph AB and the position 2F disambiguated in AWS A3.0? | `PASS` | `Table A1` / `Figure A6` (`AB`) + `Figure B18(B)` / `Figure B20` (`2F`) |
| `G61-SEM10` | Semantic Graph | What are all the throat terms cross-referenced from throat of a fillet weld in Clause 4? | `PASS` | `Clause 4` (p. 58) `see_also` neighborhood + `Figure B25` |
| `G61-SEM11` | Semantic Graph | What are the standard process variations under flux cored arc welding (FCAW) in AWS A3.0? | `PASS` | `Table A1` / `IS_A Store` (`FCAW-G`, `FCAW-S`) + `Clause 4` (p. 27) |
| `G61-SEM12` | Semantic Graph | What related welding angle concepts are connected to travel angle in Clause 4? | `PASS` | `Clause 4` (p. 60) (`work angle`, `drag`, `push`) |
| `G61-SEM13` | Offline Replay | What does FCAW-G-SA stand for and how is fusion welding classified in Figure A4? | `PASS` | Replay `a93c3e92...` (`Figure A4`, p. 78 crop) |
| `G61-SEM14` | Offline Replay | What does PAW-AU stand for and how are theoretical throat and effective throat defined and illustrated in Figure B25? | `PASS` | Replay `b1548f09...` (`Figure B25`, p. 123 crop) |
| `G61-SEM15` | Offline Replay | Compare the active process variation FCAW-G with the obsolete process atomic hydrogen welding (AHW) in AWS A3.0. | `PASS` | `Table A1` (p. 69) + `Table A5` (p. 74) + `Clause 4` |

---

## 4. Anti-Drift & Security Verification

All static analysis and anti-overfitting scans passed with zero matches:
- **Zero Hardcoded Benchmark IDs:** `git grep -E "QA[0-9]+|...|G61-SEM[0-9]+" -- src/ eval/*.py` $\rightarrow$ `0 matches` (Exit code 1).
- **Zero Trap String Literals:** `git grep -Ei "hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018" -- src/` $\rightarrow$ `0 matches` (Exit code 1).
- **Zero Network Access:** All tests executed with `socket.socket` blocked.
- **Full Regression Suite:** `1,482 passed, 8 skipped, 0 failures, 0 warnings` in 169.98s.
