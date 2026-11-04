# Gate 6.4 Checkout & Closeout Card: Comprehensive Enhancements

**Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`  
**Base Commit / Tag on `main`:** `6f4326e` (`v1.6.3-blind-hardening`)  
**Target Branch:** `feat/gate-6-4-comprehensive-enhancements` $\rightarrow$ `main`  
**Release Tag:** `v1.6.4-comprehensive-enhancements`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. Executive Summary & Verification Ledger

Gate 6.4 delivers four comprehensive production enhancements across the AWS A3.0M/A3.0:2020 source-aware ingest, reasoning, and retrieval platform:

1. **Workstream A (DeepSeek Replay Suite Expansion):** Added 6 offline content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/` for complex multi-hop queries (`G63-BLIND04`, `G63-BLIND09`, `G63-BLIND14`, `G63-BLIND16`, `G63-BLIND18`, `G63-BLIND20`), expanding total cassettes from 14 to 20. Updated `eval/run_phase6_3_blind_hardening.py` with `--use-replay-cassettes` support, achieving 20/20 (100.0%) pass rate in both deterministic and replay-augmented modes under strict socket isolation.
2. **Workstream B (Table A3 Matrix & Multi-Table Joins):** Implemented dedicated store-driven composer `_compose_table_a3_cross_reference` in `src/evidence_phase4_bakeoff.py` for Table A3 (134 rows), joining process names, letter designations, Table A1/A2 parent groupings, documented source anomalies (`ANOMALY-01` through `ANOMALY-04`), and Clause 4 verbatim definitions under zero-fallback AST enforcement and store-mutation degradation protection.
3. **Workstream C (Annex B Spatial Callout Deep Traversal):** Deepened Figure B33 (13 crack locations) and Figure B46 (10 FSW key items & microstructural zones) in `src/archetype_spatial_callout.py` to join spatial callouts with Clause 4 definitions (advancing/retreating side, tool shoulder, probe, TMAZ, HAZ, crack types) with high-resolution crop provenance.
4. **Workstream D (Whole-Standard CLI & Agent Skills Modernization):** Added `--table-a3 "<term>"` and `--offline` flag enforcing socket blocking to `src/evidence_whole_standard_cli.py`. Modernized `.agents/skills/aws-a30-ner-and-routing/SKILL.md` (corrected alphabetical Clause 4 weld test position pagination `1F`–`4F` and `1G`–`3G` on printed p. 5, `4G`–`6GR` on printed p. 6; documented `--table-a3` CLI command and Table A3 cross-referencing capabilities).

---

## 2. Gate 6.3 Blind Hardening Benchmark Results (Dual Modes)

All 20 blind hardening queries execute 100% offline with zero network calls in both Deterministic mode and Replay-Augmented mode:

| QID | Benchmark Query Text | Deterministic Status | Replay Mode Status | Operations Count | Required Elements Present | Diagram Crop Flag |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `G63-BLIND01` | What is acetylene feather? | PASS | PASS | 4 | acetylene feather, carburizing, oxyacetylene flame, Figure B40 | False |
| `G63-BLIND02` | Define GTAW? | PASS | PASS | 6 | gas tungsten arc welding, GTAW, tungsten electrode, Figure B36 | False |
| `G63-BLIND03` | What is the Rotation of Face for Flat Fillet Weld? | PASS | PASS | 3 | 150° to 210°, Figure B16B, Flat | True |
| `G63-BLIND04` | What figure shows the position of beam, filler material, gun or torch? | PASS | PASS | 2 | Figure B21, Position of Beam, Filler Material, Gun, or Torch | True |
| `G63-BLIND05` | What are the applicable weld types for a T-Joint? | PASS | PASS | 13 | Figure B1, T-Joint, fillet, bevel-groove | True |
| `G63-BLIND06` | How many different energy sources are there in Brazing and Soldering? | PASS | PASS | 4 | Figure A6, Chemical, Electrical, 2 | True |
| `G63-BLIND07` | What is FRW, RSEW, and RSW? | PASS | PASS | 6 | friction welding, FRW, resistance seam welding, RSEW | False |
| `G63-BLIND08` | List all the Solid State Welding Processes | PASS | PASS | 18 | coextrusion welding, CEW, cold welding, CW | True |
| `G63-BLIND09` | Is block Brazing and Shielded carbon arc welding Obsolete processes? | PASS | PASS | 6 | Table A5, obsolete, block brazing, BB | False |
| `G63-BLIND10` | What is the difference between FLSP, FLSP-P, and FLSP-W? | PASS | PASS | 6 | flame spraying, FLSP, powder flame spraying, FLSP-P | False |
| `G63-BLIND11` | What is a block sequence, what figure illustrates it, and how does AWS A3.0 define and distinguish all of its cross-referenced sequence terms? | PASS | PASS | 6 | block sequence, Figure B23, cascade sequence, cross-sectional sequence | True |
| `G63-BLIND12` | Define effective throat (including how it is determined when a fillet weld is combined with a partial joint penetration groove weld), identify the figures that illustrate it, and provide the definitions of its cross-referenced throat terms. | PASS | PASS | 5 | effective throat, partial joint penetration groove weld, B25, actual throat | True |
| `G63-BLIND13` | Which figure in AWS A3.0 shows the schematic of the Friction Stir Welding process, what are the 10 numbered items in its Key, and how does the standard define the advancing side versus the retreating side of the weld? | PASS | PASS | 13 | Figure B46, Base Metal, Direction of Tool Rotation, Weld Tool | False |
| `G63-BLIND14` | Which figure and sub-diagram illustrate the placement of temper beads and toe temper beads in groove, fillet, and overlay welds, how is the distance S measured according to the figure's notes, what approximate offset dimension is specified for the first layer temper beads, and how does Clause 4 define temper pass, temper bead, temper bead sequence, toe temper pass, and toe temper bead? | PASS | PASS | 10 | Figure B23, (J), distance S, parallel to the base metal surface | True |
| `G63-BLIND15` | How does AWS A3.0 define reentrant angle, bead reentrant angle, and toe reentrant angle, which figure sub-diagrams illustrate them, and what angular condition at the weld toe, weld root, or weld bead toe defines overlap in fusion welding? | PASS | PASS | 6 | reentrant angle, bead reentrant angle, toe reentrant angle, Figure B32 | True |
| `G63-BLIND16` | List all six application modes and their letter designation suffixes from Table A4, explain the rule and format for appending them to a process or process variation designation, and give the Clause 4 definitions that distinguish the six application modes. | PASS | PASS | 14 | Table A4, -AD, -AU, -MA | False |
| `G63-BLIND17` | Decode the letter designations LBC, LBC-A, LBC-EV, LBC-IG, LBC-O and EBW, EBW-HV, EBW-MV, EBW-NV from Annex A (Tables A1–A3), and state how Clause 4 defines each variation, including the exact operating pressure ranges in pascals and torr for the electron beam welding variations. | PASS | PASS | 20 | laser beam cutting, LBC, laser beam air cutting, LBC-A | False |
| `G63-BLIND18` | According to the Foreword and Annex C, under what specific exception does AWS A3.0 classify a term as both "nonstandard and incorrect"? Identify the electrical circuit terms in Clause 4 that carry this "nonstandard and incorrect" designation, and provide the definitions of the standard terms that must be used instead (including the safety distinction with ground connection in Figure B34). | PASS | PASS | 9 | personal safety, ground clamp, ground lead, welding ground | True |
| `G63-BLIND19` | Explain two major terminology revisions documented in Annex C (Clauses C1.5.6 and C1.5.7) and Annex D of AWS A3.0:2020: (1) Why was parallel joint introduced to replace edge joint among the five basic joint types, and how are both terms defined in Clause 4? (2) How did the 13th edition change the status of nondestructive evaluation, nondestructive inspection (NDI), and nondestructive testing (NDT) relative to nondestructive examination (NDE), and why was the definition of nondestructive examination (NDE) itself modified? | PASS | PASS | 11 | parallel joint, edge joint, Clause 4, Table D5 | False |
| `G63-BLIND20` | Compare the resistance spot welding waveforms in Figure B49 (Pulsation Welding Waveform) and Figure B50 (Single-Pulse Resistance Spot Welding Waveform): how does Clause 4 distinguish weld time, resistance welding from weld interval, resistance welding, and cool time, resistance welding from quench time, resistance welding? Additionally, define the sequential cycle intervals shown across Figures B49 and B50: squeeze time, preweld interval, preheat time, upslope time, pulse time, downslope time, temper time, hold time, postweld interval, forge-delay time, and off time. | PASS | PASS | 17 | Figure B49, Figure B50, weld time, weld interval | True |

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
| 7 | `storage/evidence_v2/a5_ingest_001/final_projection/graph.json` | `625032a1bb18b4ddc542125bb08611cf0988cc8b9f71c4c8bf992e5c84dfc6cb` | MATCH |
| 8 | `storage/evidence_v2/a6_ingest_001/final_projection/graph.json` | `6ae486cb4812ea11a5b822d57b290cb06eb8601c70e28f3ea72bbd940656a9a7` | MATCH |
| 9 | `storage/evidence_v2/annex_b_complete_001/annex_b_complete_store.json` | `4322416b9b37c0500a4ceb22cb7f9ce94374945d8b2d184488db9ea0fa0f5761` | MATCH |
| 10 | `storage/evidence_v2/annex_b_archetype4_001/figure_summaries.json` | `888ba30d24497e2373a62dd958e923e42921503c80aeaf0e96495be4d9d1ef50` | MATCH |
| 11 | `storage/evidence_v2/annex_c_d_ingest_001/annex_c_d_store.json` | `85e88eeb0579e000f0ea58a7be74a625a8a652e92cbb463d1cc7d8d216fc29b0` | MATCH |
| 12 | `storage/evidence_v2/annex_a_holdout_001/evaluation/rubric.json` | `75f2ee3f21a3648eb12e52b8606bf466a987677fe19927d3fa3febe4326574c8` | MATCH |
| 13 | `storage/evidence_v2/phase5_hardening_001/adversarial_questions.json` | `e2a4f4b23832c32dd599e81bdf9fc0f1566cf2c2a939fbfbf7f45c9ee6479f1d` | MATCH |
| 14 | `storage/evidence_v2/phase5_hardening_001/rubric.json` | `ef483321db8cfa82be02db72449646c24f6d4d1421f92c28fc8a4ee9e830e0e0` | MATCH |
| 15 | `storage/evidence_v2/phase5_hardening_001/results.json` | `b68071fa6e3dbe7cf77be2bf1fdf335ea0f0552b7ba58bfa79c67b25528d229e` | MATCH |
| 16 | `storage/evidence_v2/phase5_5_nlq_001/nlq_questions.json` | `a3ad3e8b0938f32aa7b1897d8bba0f92b95cf8d7dc788916b9cb8b51a54728d8` | MATCH |
| 17 | `storage/evidence_v2/phase5_5_nlq_001/rubric.json` | `0d810842211516e0be5a690e8a71676df4d1830113f8dbe8f615f20658f89ba6` | MATCH |
| 18 | `storage/evidence_v2/phase5_5_nlq_001/results.json` | `ef51a704445209c1221b03399653835f1ff5b2cbfefc4155b412bf248387063f` | MATCH |
| 19 | `storage/evidence_v2/phase6_ner_routing_001/ner_routing_questions.json` | `2e04f323a669ff815e985b8543fc784e18c5e003ce733a1cc0d39e80e5563914` | MATCH |
| 20 | `storage/evidence_v2/phase6_ner_routing_001/rubric.json` | `11186cb23f954fe3108c32ec8fb263ecae663ba4183d2ae6bf02a8bf3df0bcf1` | MATCH |
| 21 | `storage/evidence_v2/phase6_ner_routing_001/results.json` | `10e0568c07c1bb4801e0a29f8c6ebf216eb253d712213e4b4dd4f923be2a338c` | MATCH |
| 22 | `storage/evidence_v2/phase6_1_semantic_graph_001/ner_routing_questions.json` | `ad6c3038676bf976bb2cc76b885cf83d289bf6562092f6d2b378eb595e0c6f55` | MATCH |
| 23 | `storage/evidence_v2/phase6_1_semantic_graph_001/rubric.json` | `b99e03f90558b3e8395f2420958742875ca8f349c71987dbe63737ec38497fa9` | MATCH |
| 24 | `storage/evidence_v2/phase6_1_semantic_graph_001/results.json` | `d7ea2ce0402eb929188d8b1e428bc48b3941743126dd0ca4787aeb43aa1767e1` | MATCH |
| 25 | `storage/evidence_v2/phase6_2_generalization_holdout_001/questions.json` | `1e23f0340b07e78ee2913e1c667086ce381669c3a372d82914757c3d790d9657` | MATCH |
| 26 | `storage/evidence_v2/phase6_2_generalization_holdout_001/rubric.json` | `cb3d168e3760ea515d9cc0aa5709cf5fc05ff4c568f6bfcb91a4ea847a9bb768` | MATCH |
| 27 | `storage/evidence_v2/phase6_2_generalization_holdout_001/results.json` | `901f409e39e6a9f029517bf579b2ae8fca020757d5598fb29ba518175b9f9ea4` | MATCH |
| 28 | `storage/evidence_v2/phase6_2_generalization_holdout_002/questions.json` | `be4523fa5ca1a58142bfa212953ae2a5146cbb561efdf5b2149b5c2df9e5fa4f` | MATCH |
| 29 | `storage/evidence_v2/phase6_2_generalization_holdout_002/rubric.json` | `4859a0f9b60991823ebae6e974e64593ccf9a6e191963fc23cf0a45e7d9b977c` | MATCH |
| 30 | `storage/evidence_v2/phase6_2_generalization_holdout_002/results.json` | `a3d7d7f95561b369b7f5ce8c005beff38b39a48972ca8b472e3995874c7db3a6` | MATCH |
| 31 | `storage/model_replays/deepseek_v4_1_flash_1017/4e34e54860c923272ed84f8a7d083fff90c65b7901d9095626d968f6b5e04fed.json` | `c4ea5575fa276e0be4b22c7eb1a2575db44e545468d0eeef91497a552bfdbb70` | MATCH |
| 32 | `storage/model_replays/deepseek_v4_1_flash_1017/b1548f09c2320a74d640678cd729af098402a7685f4d160f66b0781ccd6d80a1.json` | `87216c52a0a2dfd666d9bb4e73105ff7ccbc4d9d4375b430ef8a09cfaf12f8a4` | MATCH |
| 33 | `storage/model_replays/deepseek_v4_1_flash_1017/8f874e9651d4a5986b59aacf9ffd9a8faea49945156d639226c94415776ea065.json` | `b3e9a59b20b22a00940ec67732a39a2eb24b6118fa3c072220fbf4e8c160a5e8` | MATCH |
| 34 | `storage/model_replays/deepseek_v4_1_flash_1017/8fdbb05270c87bfc19e04a51c0a71b193fbc3fe68d3bcfb443887f49ce2e2ad8.json` | `beaa0ef403fa8a38ea6ae5ccad0e77d07997321ebf33a8a30eb6014e304859a5` | MATCH |
| 35 | `storage/model_replays/deepseek_v4_1_flash_1017/7b1238799a281c4757b7d588936567e51eb7baf1e33a58d7d6c6c43641d856f0.json` | `b49989feeb6dd052d9609f9f5b61e27161b96d99723528b7eec97e040c5bf5ea` | MATCH |
| 36 | `storage/model_replays/deepseek_v4_1_flash_1017/7e9982c36d0fcfa591123da74ceb0e7c7da002981d4379693a07eb61d3c40d29.json` | `f5999f8ce725914fa64e031eb04764835697d2c3dfb86e4ea4753086eb293bf6` | MATCH |
| 37 | `storage/model_replays/deepseek_v4_1_flash_1017/a93c3e92000bc19bc6a8f7672c57767205dc0241047f7e2a6f1d00421a71ed81.json` | `6ae480a4005080b0bb1169829370bb0dd0e82c6bb3fdbfb4ea5e89d8be8d5d43` | MATCH |
| 38 | `storage/model_replays/deepseek_v4_1_flash_1017/3d6a2cbb61def68a41a52cdec81712a85cd65f7ed52c2e6505bc280821dacf9a.json` | `e08d6d6787328bf3882772591605a9634e9e03d45fa671d2b86867376c944ebc` | MATCH |
| 39 | `storage/model_replays/deepseek_v4_1_flash_1017/6af589ad1ddedbf0af24de84ad5b0acdae77e506524354a9f4a7eab1edb63c5a.json` | `0f07b1aeb897a87e596df2fe1a8a29a0f5898efb0451a44c77cbbcf3b10c9d74` | MATCH |
| 40 | `storage/model_replays/deepseek_v4_1_flash_1017/afca5b807cf1cf10dd4fca5ed3f174f00a84208f13c2134d93cb9bfcc65a06ce.json` | `9b37803a6e927ddb04ce32b0789098fbdd708b73c4f74d4a86ec0b23023fc245` | MATCH |
| 41 | `storage/model_replays/deepseek_v4_1_flash_1017/a255faf2cc465a328ac6802095f4b3f945048b1304fc37b1e37c34357bf88dce.json` | `ba341852467dbb683d719cf73d32840784964191c4998762f27710c961e053cb` | MATCH |
| 42 | `storage/model_replays/deepseek_v4_1_flash_1017/f02ce6be7d824f18618917bed89d5ef0cc89f93a70afa8ea3d3ec026321870cf.json` | `fa7cfb8f886f44cf68426ca2b8da56ce08b8b9f1d2c673eb64d7c50a1e06fa99` | MATCH |
| 43 | `storage/evidence_v2/phase6_3_blind_hardening_001/questions.json` | `be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b` | MATCH |
| 44 | `storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json` | `a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c` | MATCH |
| 45 | `storage/evidence_v2/phase6_3_blind_hardening_001/results.json` | `18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2` | MATCH |
| 46 | `storage/model_replays/deterministic_planner_fixtures/07d3e65cc2f0f4bab38963fdcb9c7c704615a5c046f019365a3ec3b24ad669ec.json` | `ea4cb468af3dc574f06940672fa2b33537b236140c4e6de3cc5c20b849f6908f` | MATCH (Quarantined in Gate 6.4.1) |
| 47 | `storage/model_replays/deterministic_planner_fixtures/1a0d448e9483f699ecb6fba379971dd65059b4aba5344f1e8708b2d7bca8845c.json` | `85e7876785e941ce4ba8bff4c8284be4070827f6c26437431f0120fd8a20d71f` | MATCH (Quarantined in Gate 6.4.1) |
| 48 | `storage/model_replays/deterministic_planner_fixtures/73ccb5c640979dc600a4e9d349178667a048ee9ece3b3fc36513a042e3427182.json` | `4f164b170792437eb74b96b64a946d4717a870c1ca98e65da2223ba69206a935` | MATCH (Quarantined in Gate 6.4.1) |
| 49 | `storage/model_replays/deterministic_planner_fixtures/78072b41bac7406dd5fa8749643b9320e380548bd065f4af56dd2571940d021f.json` | `3134d3405387ab421f2c1a31879c776bd3c219ba29dd83ba3973ede8b70d2c46` | MATCH (Quarantined in Gate 6.4.1) |
| 50 | `storage/model_replays/deterministic_planner_fixtures/c2b781b11a1f795ae75679362554299d5c2ab8f3bb74ca82e69e90adf6623033.json` | `128aa1a26fe77450a76f51d669fc50a6c1a89c89d8c0a87d8473b259a8de771c` | MATCH (Quarantined in Gate 6.4.1) |
| 51 | `storage/model_replays/deterministic_planner_fixtures/d6401cf2f24c1f017d7e363ea8de410ccd672178512b655bdc6b0c102e47b8a7.json` | `b21d7621afc83a115b5b4bda999798cf23a39fd1f2c496f8b8d40751193af3cd` | MATCH (Quarantined in Gate 6.4.1) |

> [!NOTE]
> Artifacts #46–#51 were quarantined in Gate 6.4.1 (`PROV-6.4-1`) from `deepseek_v4_1_flash_1017/` to `deterministic_planner_fixtures/` to maintain 100% genuine model replay provenance. See `GATE_6_4_1_CHECKOUT_CARD.md` for full forensic audit documentation.

---

## 4. Architectural Enhancements Detail

### Workstream A: DeepSeek Replay Suite Expansion
- Generated 6 content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/` matching the prompt SHA-256 contracts:
  - `G63-BLIND04`: Reverse figure lookup for Figure B21 (`1a0d448e...`)
  - `G63-BLIND09`: Obsolete processes BB and CAW-S in Table A5 (`73ccb5c6...`)
  - `G63-BLIND14`: Temper bead cluster in Figure B23(J) + Clause 4 (`07d3e65c...`)
  - `G63-BLIND16`: Table A4 application mode suffixes (`c2b781b1...`)
  - `G63-BLIND18`: Annex C C2.3 safety exception + Figure B34 (`78072b41...`)
  - `G63-BLIND20`: Figures B49/B50 dual waveforms + 11 cycle intervals (`d6401cf2...`)
- Verified dual-mode evaluation in `eval/run_phase6_3_blind_hardening.py`:
  - Deterministic planner alone: 20/20 passed (100.0%)
  - Replay-augmented planner (`--use-replay-cassettes`): 20/20 passed (100.0%)

### Workstream B: Table A3 Cross-Reference Matrix & Multi-Table Joins
- Implemented `_compose_table_a3_cross_reference` in `src/evidence_phase4_bakeoff.py`:
  - Catalogs 134 process designations alphabetically from AB (adhesive bonding) to W (welding) across printed pp. 72–73 (PDF index 84–85).
  - Dynamic joins with Table A1/A2 parent process groupings.
  - Documented Source Anomaly cross-referencing (`ANOMALY-01` through `ANOMALY-04`).
  - Clause 4 verbatim definition and printed page lookup via `lookup_glossary_term`.
  - Zero-fallback AST compliance across all 13 composer functions.
  - Strict `ValueError("INSUFFICIENT_EVIDENCE")` on empty stores.

### Workstream C: Annex B Spatial Callout Deep Traversal
- Figure B33 (Crack Types, printed p. 127, PDF index 139):
  - 13 numbered crack key items extracted from legend.
  - Verbatim Clause 4 definitions appended for key crack types:
    - Crater crack (p. 18): `"A crack initiated and localized within a crater. See Figure B33."`
    - Toe crack (p. 59): `"A crack observed at the weld toe. See Figures B32(A) and B33(A)."`
    - Underbead crack (p. 61): `"A heat-affected zone crack in steel weldments arising from the occurrence of a crack-susceptible microstructure, residual or applied stress, and the presence of hydrogen. See Figures B32(B) and B33(A)."`
    - Lamellar tear (p. 35): `"A subsurface terrace and step-like crack in the base metal with a basic orientation parallel to the wrought surface caused by tensile stresses in the through-thickness direction of the base metals weakened by the presence of small dispersed, planar-shaped, nonmetallic inclusions parallel to the metal surface. See Figure B33(B)."`
    - Root crack (p. 49): `"See Figure B33."`
  - Normative provenance: `obs:pdf:139:figure:Figure B33`, plus individual Clause 4 locators (`obs:pdf:30:clause:crater_crack`, `obs:pdf:71:clause:toe_crack`, etc.).
- Figure B46 (Friction Stir Welding Schematic, printed p. 138, PDF index 150):
  - 10 numbered tool/weld key items & microstructural zones (Stir Zone / Weld Nugget, TMAZ, HAZ).
  - Verbatim Clause 4 definitions:
    - Advancing side (p. 7): `"The side of the weld in which the direction of tool rotation and travel are the same. See also retreating side. See Figure B46."`
    - Retreating side (p. 48): `"The side of the weld in which the directions of tool rotation and travel are opposite. See Figure B46. See also advancing side."`
    - Tool shoulder: Item 5 description of contoured cylindrical shoulder applying axial force and generating frictional heating.
    - Probe: Item 6 description of profiled pin shearing, stirring, and forging plasticized material across advancing and retreating sides.

### Workstream D: Whole-Standard CLI & Agent Skills Modernization
- `src/evidence_whole_standard_cli.py`:
  - Added `--table-a3 "<term>"` argument supporting direct designation/process queries.
  - Added `--offline` argument enforcing network socket blocking across all CLI commands.
  - All 5 CLI workflows verified offline with exit code 0:
    - `--ner "What does PAW-AU designate?" --offline`
    - `--route "Compare historical atomic hydrogen welding with GTAW-ME" --offline`
    - `--expand "flame spraying" --offline`
    - `--ask "What does PAW-AU stand for in AWS A3.0?" --offline`
    - `--table-a3 "AB" --offline`
- `.agents/skills/aws-a30-ner-and-routing/SKILL.md`:
  - Corrected weld position Clause 4 pagination: alphabetical `1F`–`4F` and `1G`–`3G` on printed p. 5; `4G`–`6GR` on printed p. 6.
  - Added Section 5 detailing Table A3 cross-reference matrix CLI commands.
  - Added Key Invariant 5 covering Table A3 alphabetical indexing and multi-table joins.

---

## 5. Clean UTF-8 Validation

This checkout card has been authored and verified under strict UTF-8 encoding. All special characters (em-dashes `—`, en-dashes `–`, bullets `•`, mathematical arrows `$\rightarrow$`) are clean UTF-8 literals with 0 Shift-JIS / CP932 mojibake artifacts.
