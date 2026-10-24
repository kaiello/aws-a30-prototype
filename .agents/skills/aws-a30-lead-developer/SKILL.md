---
name: aws-a30-lead-developer
description: Master lead-developer workflow for the AWS A3.0M/A3.0:2020 Multimodal RAG and Epistemic Knowledge System (aws-a30-prototype). Use whenever planning, debugging, extending ingestion, modifying the planner/compiler contract, running preflight checks, or evaluating QA runs.
---
# AWS A3.0 Lead Developer Skill

Follow this workflow as the lead developing agent for `aws-a30-prototype` to maintain strict epistemic separation, triple-coordinate source provenance, and zero-regression engineering discipline.

## When to Use

- Starting any development task on `aws-a30-prototype`
- Diagnosing a failed or partial natural-language question (NLQ) answer
- Modifying planner schemas, lowering adapters, compilers, or graph executors
- Expanding source ingestion to new figures, tables, or glossary clauses
- Preparing branch handoffs or evaluation reports

## Core Epistemic Rules

1. Keep the Evidence Graph and Knowledge Graph separate:
   - Store literal observations (text spans, boxes, `ENCLOSES_ROW`, undirected `CHART_CONNECTOR`, `INDENTED_UNDER`, and VLM observations with `knowledge_eligible=false`) in the Evidence Graph.
   - Store admitted assertions (`CHART_MEMBER_OF`, `CHART_CONNECTED`, and dual-provenance `IS_A_PROCESS_VARIATION_OF`) in the Knowledge Graph.
   - Never promote layout indentation (`CANDIDATE_LAYOUT_PARENT`) to an accepted `IS_A` subtype without explicit Clause 4 Glossary genus-differentia text and Table A1 corroboration.

2. Bind every source locator using all three page conventions:
   - 0-based `pdf_index` (e.g., Figure A1 = 87, Figure A2 = 88)
   - 1-based `viewer_page` (e.g., Figure A1 = 88, Figure A2 = 89)
   - Printed `page_number` (e.g., Figure A1 = 75, Figure A2 = 76)
   - Normalized `[ymin, xmin, ymax, xmax]` crop coordinates and SHA-256 hashes where applicable

3. Diagnose failures using the 6-layer trace order before writing code:
   - Layer 1: Source manifest and crop/page binding
   - Layer 2: Evidence Graph observations and Knowledge Graph admission status
   - Layer 3: Identity Dictionary resolution, acronym mapping, and sense delimiters
   - Layer 4: Planner sub-question decomposition and action selection
   - Layer 5: Lowering adapter and compiler validation (`src/evidence_chart_question_plan.py` -> `src/evidence_chart_llm_plan.py`)
   - Layer 6: Deterministic answer composition and per-part coverage reporting

4. Enforce strict stop conditions:
   - Never rebuild OCR when the required label or edge already exists in the store and the failure occurred at Layers 3-6.
   - Never run an unapproved live LLM inference loop; run offline real-entry preflight first.
   - Never overwrite historical run receipts, saved raw model outputs, or merged `main` (`71088cebc9eb3b2556d7bbe73a23a451e645e3b9`).

## Step-by-Step Workflow

1. Check repository and baseline integrity:
   - Inspect `git status` and current branch (`feat/planner-contract-preflight` or `feat/a1-a2-relationship-readiness`).
   - Verify source PDF hash (`205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`) and A2 crop hash (`e792b09ccb9896e9dc1eb908883bcf876bb790ef19150a8d226f2e7e6b2ec908`) remain intact.

2. Localize the target defect or feature to its exact architectural layer:
   - Query the SQLite store and Identity Dictionary first to confirm whether required entities and assertions already exist.
   - If the data exists, restrict edits to the planner contract, lowering adapter, compiler, or answer composer.

3. Validate offline before any model call:
   - Run focused unit tests (`pytest`) for all touched modules.
   - Run `python -m src.evidence_chart_preflight` on both `A1` and `A2` using representative payloads (including nonempty `part.reason` strings and compound questions).
   - If saved model outputs exist for the target interface, run one offline unchanged-output replay through `LocalQuestionPlanner.__call__` with network blocked.

4. Report separated metrics in every receipt and handoff:
   - Report structural schema validity, compiler acceptance, executed graph operations, content grade, delivery grade (per requested part), and provenance audit separately.

## Gotchas

- Passing software unit tests (e.g., 398 or 416 checks) proves code invariants, not domain answer accuracy.
- A manual action check with `reason=""` does not prove that live LLM output with nonempty `part.reason` will survive the compiler.
- Executing all operations in an incomplete plan is a question-completeness failure, not a pass.
