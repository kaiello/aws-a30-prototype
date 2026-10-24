---
name: aws-a30-gate-review
description: Gate verification and audit packet workflow for reviewing Gemini 3.8 Flash work on the AWS A3.0M/A3.0:2020 Multimodal RAG system (aws-a30-prototype). Use whenever Gemini 3.8 Flash completes a milestone gate (Gates 0, 1A, 1B, 2, 3, or 4), prepares a review packet for the principal reviewer, or when auditing a submitted gate review packet for approval or rejection.
---
# AWS A3.0 Gate Review and Audit Skill

Enforce mandatory stop-and-review gates for `aws-a30-prototype` and standardize the exact evidence packet produced by Gemini 3.8 Flash and audited by the principal reviewer at each milestone.

## When to Use

- Packaging a completed milestone (Gates 0, 1A, 1B, 2, 3, or 4) for principal review
- Auditing a Gate Review Packet submitted from Gemini 3.8 Flash
- Deciding whether to authorize a live LLM planner run, approve a branch merge to `main`, or advance to the next ingestion phase
- Checking that no epistemic rules, source hashes, or anti-hardcoding rules were violated during development

## The 6 Mandatory Review Gates (When to Check)

Do not micromanage individual unit-test edits inside a phase. Enforce hard stops at these six boundaries:

1. **Gate 0 (Preflight and Hygiene Closure - 0 LLM Calls):**
   - Trigger: Immediately after running the offline A1 branch of `src.evidence_chart_preflight` and committing `feat/planner-contract-preflight`.
   - Required before: Starting Phase 1 code changes.

2. **Gate 1A (Offline Planner Diff and Contract Repair - 0 LLM Calls):**
   - Trigger: After completing the `001` vs `004` deterministic diff, updating the contract or lowering adapter, fixing the 5 A1 completeness patterns (`A1-QA002-10`, `A1-QA002-13`, `A1-QA002-14`, `A1-HO002-01`, `A1-HO002-05`), and running offline preflight plus saved-plan replay.
   - Required before: Authorizing the single fresh 67-question live LLM run.

3. **Gate 1B (Fresh 67-Question A1/A2 Run and Merge Decision - 67 LLM Calls):**
   - Trigger: Immediately after executing the single authorized 67-question live planner pass (51 A1 + 16 A2 questions).
   - Required before: Merging the readiness branch to `main` or starting Phase 2 ingestion.

4. **Gate 2 (Annex A Full Expansion - Figures A3 through A6 and Tables A1 through A5):**
   - Trigger: After ingesting Figure A3, Classification Charts A4 through A6, and joining Tables A1 through A5 into the SQLite Evidence Graph, Knowledge Graph, and Identity Dictionary.
   - Required before: Starting Phase 3 Clause 4 Glossary and Annex B ingestion.

5. **Gate 3 (Clause 4 Glossary, Dual-Provenance `IS_A` Promotion, and Annex B/C/D):**
   - Trigger: After ingesting Clause 4 Glossary, promoting corroborated `CANDIDATE_LAYOUT_PARENT` edges to accepted `IS_A_PROCESS_VARIATION_OF`, and ingesting Annex B Figures B1 through B54 plus Annex C and D.
   - Required before: Running unseen holdout or AWS production model evaluations.

6. **Gate 4 (Unseen Holdout and AWS Production Acceptance):**
   - Trigger: After running the frozen unseen holdout benchmark across the deterministic route, `gemini-3.8-flash`, and AWS `GPT 5.6 Terra` / `Luna`.
   - Required before: Production release sign-off.

## Standardized Output Packet Required from Gemini 3.8 Flash

At every gate, Gemini 3.8 Flash must generate a single self-contained file at `storage/gate_reviews/gate_<ID>_review_packet.md`. Never approve a gate without all seven sections populated:

1. **Gate Metadata and Git State:** Gate ID, branch, HEAD commit SHA, `main` commit SHA (`71088cebc9eb3b2556d7bbe73a23a451e645e3b9`), `git status --short`, and `git diff --stat`.
2. **Immutable Artifact and Store Integrity:** Verification of Source PDF SHA-256 (`205fa58e...`), A1 store SHA-256 (`6476c898...`), A2 crop SHA-256 (`e792b09c...`), and confirmation that prior run receipts remain untouched.
3. **Offline Real-Entry Preflight Receipt:** Exact CLI command and output of `python -m src.evidence_chart_preflight` for both `A1` and `A2` showing `CLEAR_REAL_ENTRY_CONTRACT` and zero network calls.
4. **Separated Five-Dimension Evaluation Scorecard:**
   - Structural JSON Schema Validity (`X / N`)
   - Compiler Acceptance (`X / N` compiled vs pre-retrieval rejected)
   - Graph Operation Execution (`executed` / `source-limited` / `blocked`)
   - Content Grade (`PASS` / `PARTIAL` / `FAIL` / `UNASSESSED`)
   - Delivery Grade per Requested Part (`PASS` / `PARTIAL` / `FAIL`)
5. **Epistemic and Anti-Hardcoding Audit:**
   - Count of accepted vs candidate assertions per slice
   - Confirmation that zero `CANDIDATE_LAYOUT_PARENT` or VLM observations (`knowledge_eligible=false`) were promoted to `IS_A` without dual Clause 4 + Table A1 provenance
   - Confirmation via `grep` / `git diff` that no question IDs (`A1-QA002-*`, `A1-HO002-*`) or hardcoded answer strings were added to `src/`
6. **Per-Item Failure and Regression Ledger:** Exact question IDs, failure layer attribution (Layers 1 through 6), and verbatim composed answers for any partial/failed/repaired items.
7. **Requested Authorization:** The exact single next step requested from the reviewer.
