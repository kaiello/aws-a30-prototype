---
name: aws-a30-lead-developer
description: Master lead-developer workflow for the AWS A3.0M/A3.0:2020 Multimodal RAG and Epistemic Knowledge System (aws-a30-prototype). Use whenever planning, debugging, extending ingestion, modifying the planner/compiler contract, running whole-standard preflight checks, or evaluating QA runs.
---
# AWS A3.0 Lead Developer Skill

Follow this workflow as the lead developing agent for `aws-a30-prototype` to maintain strict epistemic separation, triple-coordinate source provenance, version-bound store immutability, and zero-regression engineering discipline across the entire `AWS A3.0M/A3.0:2020` standard (190 PDF pages / 162 ingested canonical store pages).

## When to Use

- Starting any development task on `aws-a30-prototype`
- Diagnosing a failed or partial natural-language question (NLQ) answer across Clause 4, Annexes A, B, C, or D
- Modifying planner schemas, lowering adapters, compilers, semantic expanders, NER, or graph executors
- Expanding source ingestion to new figures, tables, or glossary clauses
- Preparing branch handoffs or gate evaluation reports
- Verifying offline preflight integrity and zero-network execution invariants

## Core Epistemic Rules

1. Keep the Evidence Graph and Knowledge Graph separate:
   - Store literal observations (text spans, boxes, `ENCLOSES_ROW`, undirected `CHART_CONNECTOR`, `INDENTED_UNDER`, and VLM observations with `knowledge_eligible=false`) in the Evidence Graph.
   - Store admitted assertions (`CHART_MEMBER_OF`, `CHART_CONNECTED`, and dual-provenance `IS_A_PROCESS_VARIATION_OF`) in the Knowledge Graph.
   - Never promote layout indentation (`CANDIDATE_LAYOUT_PARENT`) to an accepted `IS_A` subtype without explicit Clause 4 Glossary genus-differentia text and Table A1 corroboration.
   - Quarantine model reasoning traces (`part.reason`) emitted by `DeepSeek-V4.1-Flash-1017` as `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE`.

2. Bind every source locator using all three page conventions:
   - 0-based `pdf_index` (e.g., printed p. 69 = 81, Figure A1 = 87, Figure B25 = 127)
   - 1-based `viewer_page`
   - Printed `page_number`
   - Normalized `[ymin, xmin, ymax, xmax]` crop coordinates and SHA-256 hashes where applicable.
   - Conditional crop provenance: `requires_diagram_crop: True` (with verified `crop_path` on disk) if and only if at least one resolved claim depends on Figures A1–A6 or Figures B1–B54; `requires_diagram_crop: False` for pure text/table multi-hop answers.

3. Diagnose failures using the 6-layer trace order before writing code:
   - Layer 1: Source manifest and crop/page binding
   - Layer 2: Evidence Graph observations and Knowledge Graph admission status
   - Layer 3: Welding NER (`src/welding_ner.py`), semantic expansion, and Identity Dictionary resolution
   - Layer 4: Multi-intent question planner sub-question decomposition and action selection (`src/evidence_phase4_bakeoff.py`)
   - Layer 5: Lowering adapter and compiler validation (`src/evidence_chart_question_plan.py` -> `src/evidence_chart_llm_plan.py`)
   - Layer 6: Deterministic answer composition, explicit abstentions, and per-part coverage reporting

4. Enforce strict stop conditions:
   - Never alter locked SHA-256 canonical store artifacts (`_001` stores remain byte-identical; version upgrades require explicit `_002` stores).
   - Never run an unapproved live LLM inference loop; run offline real-entry preflight (`src.evidence_whole_standard_preflight`) first.
   - Never write hardcoded question IDs or benchmark trap literals inside `src/` or `eval/*.py`.

## Step-by-Step Workflow

1. Check repository and baseline integrity:
   - Inspect `git status` and current branch.
   - Verify source PDF hash (`205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`) and canonical locked hashes in `tests/test_gate_6_0_ner_routing_skills.py` (29 locked artifacts).

2. Localize the target defect or feature to its exact architectural layer:
   - Inspect entity spans with `python -B -m src.evidence_whole_standard_cli --ner "<query>" --json`.
   - Inspect routing decisions with `python -B -m src.evidence_whole_standard_cli --route "<query>" --json`.
   - Restrict edits to the appropriate layer (NER, router, planner, compiler, or composer).

3. Validate offline before any model call:
   - Run focused unit tests (`pytest`).
   - Run `python -B -m src.evidence_whole_standard_preflight` with network blocked.
   - Verify replay cassettes under `storage/model_replays/deepseek_v4_1_flash_1017/` replay cleanly with 0 network calls.

4. Report separated metrics in every receipt and handoff:
   - Report structural schema validity, compiler acceptance, executed graph operations, content grade, delivery grade (per requested part), and provenance audit separately.

## Gotchas

- Passing unit tests verifies code invariants, not domain answer precision or coverage.
- In `src/welding_ner.py`, never add `table_a1:proc:...` terms to `inferred_tables` as locators unless explicitly referencing Table A1.
- In `src/evidence_phase4_bakeoff.py`, Gate 6.0 multi-intent handlers must precede generic division fallbacks in `execute_whole_standard_plan`.
- In AST anti-drift scans, question IDs matching `QA[0-9]+|...|G60-NER[0-9]+` must return 0 matches across `src/` and `eval/*.py`.
