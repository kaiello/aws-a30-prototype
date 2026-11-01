---
name: aws-a30-gate-review
description: Gate verification and audit packet workflow for reviewing milestone work on the AWS A3.0M/A3.0:2020 Multimodal RAG system (aws-a30-prototype). Use whenever completing a milestone gate (Gates 0 through 6.0), preparing a review packet for the principal reviewer, or auditing a submitted gate review packet.
---
# AWS A3.0 Gate Review and Audit Skill

Enforce mandatory stop-and-review gates for `aws-a30-prototype` and standardize the exact evidence packet produced and audited at each milestone across `AWS A3.0M/A3.0:2020` (190 PDF pages / 162 ingested canonical store pages).

## When to Use

- Packaging a completed milestone (Gates 0, 1A, 1B, 2, 3, 4, 5, 5.4, 5.5, 5.6, 6.0) for principal review
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

## Standardized Review Checklist for Gate 6.0

At Gate 6.0, confirm all five verification dimensions:

1. **Git State & GitOps Invariant:**
   - Single canonical branch on `origin` (`origin/main`).
   - Tags anchored: `v1.5.6-gate-5-6-calibrated` at `dd22331`, and `v1.6.0-ner-routing-skills` at Gate 6.0 closeout.
   - Merged feature branch deleted locally and remotely.
   - Archive branch `bakeoff/a1-multimodal-hybrid` preserved untouched.

2. **Immutable Artifacts and Cryptographic Lock Table (29/29):**
   - Source PDF (`data/AWS_A3.0_2020.pdf`) SHA-256 matching `205fa58e...`.
   - 6 Phase 0–3 `_001` canonical stores untouched.
   - 1 Annex A holdout rubric untouched.
   - 3 Phase 5 hardening benchmark files untouched.
   - 3 Phase 5.5 NLQ benchmark files untouched.
   - 8 existing Gate 5.4/5.5 DeepSeek replay cassettes untouched + 2 new Gate 6.0 replay cassettes verified.
   - 2 Gate 5.6 coverage and latency manifests untouched.
   - 3 new Gate 6.0 benchmark files (`storage/evidence_v2/phase6_ner_routing_001/{ner_routing_questions.json, rubric.json, results.json}`) locked.

3. **Deterministic Real-Entry Whole-Standard Preflight:**
   - `python -B -m src.evidence_whole_standard_preflight` returns `CLEAR_WHOLE_STANDARD_CONTRACT` and `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT` with zero network calls (`socket.socket` blocked).

4. **Benchmark & Evaluation Pass Rates:**
   - Gate 6.0 NER & Routing benchmark (`eval.run_phase6_ner_routing`): **20 / 20 (100.0%)**.
   - Gate 5.5 NLQ benchmark (`eval.run_phase5_5_nlq`): **15 / 15 (100.0%)**.
   - Gate 5 Hardening benchmark (`eval.run_phase5_hardening`): **10 / 10 (100.0%)**.
   - Annex A Holdout (`eval.run_annex_a_holdout`): **30 / 30 (100.0%)**.
   - Full repository pytest suite: **1,475+ passed, 8 skipped, 0 failures, 0 warnings**.

5. **Epistemic Hygiene & Anti-Drift Scan:**
   - Zero occurrences of benchmark IDs (`QA[0-9]+|...|G60-NER[0-9]+|G60-[0-9]+`) across `src/` and `eval/*.py`.
   - Zero occurrences of trap literals (`hyper-flux|laser-quantum|cryo-ionic|ASME Section IX|yield strength|E7018`) in `src/`.
   - DeepSeek traces tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.
   - Modality-appropriate crop provenance strictly enforced.

## Mandatory Google Drive Mirror Step

Before final sign-off:
1. Run `python -B -m src.sync_drive_mirror`.
2. Confirm Google Drive mirror reflects all code, skill docs, manifests, and git summary.
