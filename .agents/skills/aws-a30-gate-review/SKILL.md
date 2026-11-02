---
name: aws-a30-gate-review
description: Gate verification and audit packet workflow for reviewing milestone work on the AWS A3.0M/A3.0:2020 Multimodal RAG system (aws-a30-prototype). Use whenever completing a milestone gate (Gates 0 through 6.2), preparing a review packet for the principal reviewer, or auditing a submitted gate review packet.
---
# AWS A3.0 Gate Review and Audit Skill

Enforce mandatory stop-and-review gates for `aws-a30-prototype` and standardize the exact evidence packet produced and audited at each milestone across `AWS A3.0M/A3.0:2020` (190 PDF pages / 162 ingested canonical store pages).

## When to Use

- Packaging a completed milestone (Gates 0, 1A, 1B, 2, 3, 4, 5, 5.4, 5.5, 5.6, 6.0, 6.1, 6.2) for principal review
- Auditing a Gate Review Packet submitted for a release tag or merge to `main`
- Deciding whether to authorize branch merge, release tagging, or advancement to the next architectural milestone
- Checking that no epistemic rules, source hashes, or anti-hardcoding/anti-drift rules were violated

## The Mandatory Review Gates

1. **Gate 0–4:** Historical foundation gates (Figure A1/A2 preflight, Annex A charts A1–A6, Normative Tables A1–A5, Clause 4 Glossary, Annex B Figures B1–B54, Annexes C/D, and unseen holdout).
2. **Gate 5 (Production Hardening & Multi-Hop Composition):** Zero-regression multi-hop retrieval across all 6 canonical stores, deterministic compiler, and 10/10 adversarial holdout.
3. **Gate 5.4 (DeepSeek-V4.1-Flash-1017 Planner Adapter & Replay Harness):** Schema-bound planner adapter with offline content-addressed replay cache and `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE` epistemic quarantine.
4. **Gate 5.5 (Semantic NLQ Expansion & Natural Language Routing):** Token-level synonyms, historical acronym aliases, concept-based routing, and 15/15 NLQ benchmark.
5. **Gate 5.6 (Epistemic Hygiene, Coverage Manifest & Provenance Calibration):** 190-page coverage manifest, latency benchmarks, conditional crop provenance, and 24/24 cryptographic artifact locks.
6. **Gate 6.0 (Welding NER, Callout/Backlink Routing & Whole-Standard CLI):**
   - Step 0 GitOps pruning: `10` remote branches on `origin` -> `1` canonical `main`.
   - Character-offset Deterministic Welding NER (`src/welding_ner.py`) with 11 entity types and dynamic compound code parser (`<PROCESS>-<SUFFIX>`).
   - Callout & Backlink-Indexed Multi-Intent Router (1,115 spatial nodes, 265 Clause 4 backlinks).
   - Whole-standard CLI (`src.evidence_whole_standard_cli --ner / --route / --ask`).
   - 20-question Gate 6.0 benchmark (`phase6_ner_routing_001`).
   - 29/29 locked SHA-256 artifacts and 1,475+ full regression tests.
7. **Gate 6.1 (Polysemous Welding NER, 3-Tier Grammar & Semantic Graph Expansion):**
   - Character-offset polysemous spans (`secondary_entity_types`, `linked_clause4_terms`, `linked_figures`, `linked_tables`).
   - 3-tier compound grammar `<BASE>[-<VAR>][-<MODE>]` (`FCAW-G-SA`, `OFC-A-MA`, invalid code rejection).
   - In-memory `SemanticConceptGraph` (see-also, IS_A subtypes, sibling variations, co-callouts).
   - Whole-standard CLI `--expand`.
   - 15/15 Gate 6.1 benchmark (`phase6_1_semantic_graph_001`) and 34/34 locked SHA-256 artifacts.
8. **Gate 6.2 (Store-Driven Multi-Operation Composition, Zero-Canned-Prose AST Hardening & 20-Query Holdout):**
   - 7 atomic store-driven composers (`_exec_lookup_taxonomy_subtypes`, `_exec_expand_cross_references`, `_exec_weld_position_sense`, `_exec_disambiguate_homograph`, `_exec_compound_lookup_and_validation`, `_exec_compare_historical_and_active`, `_exec_polysemous_diagram_and_glossary`).
   - AST Zero-Fallback Guard enforcing zero string literal fallbacks in `.get(key, '...')` across all 10 composers.
   - 12-target store mutation degradation suite in `tests/test_gate_6_2_store_driven_composition.py`.
   - 14 offline DeepSeek-V4.1-Flash-1017 replay cassettes executing in `< 1 ms` under socket isolation (`socket.socket` blocked).
   - 20/20 (100.0%) Gate 6.2 Generalization Holdout Benchmark (`phase6_2_generalization_holdout_001`).
   - 39/39 locked SHA-256 artifacts and full regression test suite passing at 100%.

## Standardized Review Checklist for Gate 6.2

At Gate 6.2, confirm all six verification dimensions:

1. **Git State & GitOps Invariant:**
   - Single canonical branch on `origin` (`origin/main`).
   - Tags anchored: `v1.5.6-gate-5-6-calibrated` at `dd22331`, `v1.6.0-ner-routing-skills` at `6110430`, `v1.6.1-ner-semantic-graph`, and `v1.6.2-store-driven-composition` at Gate 6.2 closeout.
   - Merged feature branch deleted locally and remotely.

2. **Immutable Artifacts and Cryptographic Lock Table (39/39):**
   - Source PDF (`data/AWS_A3.0_2020.pdf`) SHA-256 matching `205fa58e...`.
   - 6 Phase 0–3 canonical stores + 1 Annex A holdout rubric untouched.
   - 3 Phase 5 hardening benchmark files untouched.
   - 3 Phase 5.5 NLQ benchmark files untouched.
   - 8 Gate 5.4/5.5 + 2 Gate 6.0 + 2 Gate 6.1 + 2 Gate 6.2 DeepSeek replay cassettes verified (14 total).
   - 2 Gate 5.6 manifests untouched.
   - 3 Gate 6.0 + 3 Gate 6.1 + 3 Gate 6.2 benchmark files locked.

3. **Deterministic Real-Entry Whole-Standard Preflight:**
   - `python -B -m src.evidence_whole_standard_preflight` returns `CLEAR_WHOLE_STANDARD_CONTRACT` and `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT` with zero network calls (`socket.socket` blocked).

4. **Benchmark & Evaluation Pass Rates:**
   - Gate 6.2 Generalization Holdout benchmark (`eval.run_phase6_2_generalization_holdout`): **20 / 20 (100.0%)**.
   - Gate 6.1 Semantic Graph benchmark (`eval.run_phase6_1_semantic_graph`): **15 / 15 (100.0%)**.
   - Gate 6.0 NER & Routing benchmark (`eval.run_phase6_ner_routing`): **20 / 20 (100.0%)**.
   - Gate 4 Production Bakeoff (`eval/evidence_v2_phase4_bakeoff_results.json`): **30 / 30 (100.0%)**.
   - Gate 5 Hardening benchmark (`eval.run_phase5_hardening`): **10 / 10 (100.0%)**.
   - Full repository pytest suite: **1,482+ passed, 8 skipped, 0 failures, 0 warnings**.

5. **AST Guard & Store Mutation Degradation Suite:**
   - AST guard confirms 0 string literal fallbacks in `.get(k, 'val')` across all 10 composer functions.
   - 12-target store mutation degradation suite passes, confirming immediate `ValueError("INSUFFICIENT_EVIDENCE")` on store corruption.

6. **Epistemic Hygiene & Anti-Drift Scan:**
   - Zero occurrences of benchmark IDs (`QA[0-9]+|...|G62-GEN[0-9]+|G62-[0-9]+`) across `src/` and `eval/*.py`.
   - Zero occurrences of trap literals (`hyper-flux|...|EBW-AU-SA`) in `src/`.
   - DeepSeek traces tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.
   - Modality-appropriate crop provenance strictly enforced.

## Mandatory Google Drive Mirror Step

Before final sign-off:
1. Run `python -B -m src.sync_drive_mirror`.
2. Confirm Google Drive mirror reflects all code, skill docs, manifests, and git summary.
