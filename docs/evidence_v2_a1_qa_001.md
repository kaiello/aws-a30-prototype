# Figure A1 owner QA 001 - 2026-10-21

The first bounded owner set is complete. **15/15 PASS**, 0 FAIL, 0 UNASSESSED,
after adding an explicit generic deterministic graph-QA harness. The original
prepared-backend baseline remains **0/15 completed**, all `V2_READER_REQUIRED`.
These are separate phases. The new result is DEVELOPMENT on the same exposed
questions, not an unseen holdout, an LLM benchmark or original-step-3 release
acceptance. No source facts, graph relationships or database rows were repaired.

## Harness, model and reproduction

- Canonical CLI: `src/evidence_a1_cli.py --graph-qa`.
- Engine: `src/evidence_a1_graph_qa.py`, **a1-graph-qa-1.0**.
- Model **NONE**, provider **NONE**, model/external invocation count **0**.
  Generation/context configuration is not applicable. Python 3.12.7 and
  PyMuPDF 1.26.5 were used; no dependency/model was installed.
- Source: only Figure A1, printed page 75, PDF index 87 / ordinal 88, original
  `parsed/figures/Figure_A1_p88.png` plus its required Annex A note.

```powershell
python -B -m src.evidence_a1_cli --input eval/evidence_v2_a1_owner_cqs.json --graph-qa --output storage/evidence_v2/a1_qa_reproduction.json
```

The recorded run called the canonical CLI through a network/subprocess-denying
wrapper. Raw stdout, exact command, versions, code hashes and zero blocked
attempts are in ignored `storage/evidence_v2/a1_qa_run_001/graph_qa_execution.json`.
No replay is needed now. Any separately authorized reproduction needs a fresh
private output path; exclusive creation prevents replacing receipts.

The execution dataset has 15 stable IDs and retains the owner's wording.
Only the supplied trailing “No” on the last two prompts was stripped, with the
original lines/verdicts retained in private grading metadata. No gold entered
retrieval, graph updates, answer code or prompts. Grading data stayed outside
execution; independent source expectations were sealed before nonempty outputs.

## Baseline, implemented operations and source identity

Before changing QA code, the full source graph, source/image/edition identities,
implementation files and protected stores were frozen in ignored
`storage/evidence_v2/a1_qa_run_001/`. Actual default v2/extractive queries and the
canonical packet CLI produced no asserted answers. For list questions 1-8 the
derived graph view held only root/category context, with no process rows. For
questions 9-15 the target rows were retrieved, but there was no deterministic
answer operation. The baseline made no model calls and asserted no false facts.

The added harness resolves category/process/code selectors and actually
traverses graph edges before formatting answers. Enumeration traverses outward;
lookup traverses inward. “All processes under” includes every enclosed row,
including indented descendants and intermediate parent rows, once in source
order. All 29 indentation links remain candidate layout, not reviewed `IS_A`.
Negative answers require positive placement in another named category plus the
complete chart; missing edges alone never establish a negative.

The source graph remains **99 nodes / 127 edges**, SHA256
`6476c898439108dbeaf7b92f0be3946a3e0d3538d5c15afb860d1cf0e02cc4d2`.
Source identity is
`source2:106f7a480d00ced054c58bede817a6055f8f6f165c195eb219a89f31b7dfcc68`.
Protected manifest/PDF/PNG, SQLite, source graph and contextual index hashes
match the pre-change freeze. No ingestion, ontology or edition-join correction
was needed for these questions. The shorter category phrase in CQ015 uses a
qualified unique token-subsequence interpretation, not a new source alias.

## Independent source results

Reviewers checked the actual saved answer strings and row objects against the
original PDF/image, including label/code pairing, parent layout, regions,
source/edition binding and both complete-chart negative proofs. Valid IDs were
not treated as proof of support. Runtime `semantic_validation=false` and
candidate states remain unchanged; independent grades are separate artifacts.

| ID suffix | Operation | Returned rows | Grade |
|---|---|---:|---|
| 001 | category enumeration | 21 | PASS |
| 002 | category enumeration | 9 | PASS |
| 003 | category enumeration | 4 | PASS |
| 004 | category enumeration | 11 | PASS |
| 005 | category enumeration | 14 | PASS |
| 006 | category enumeration | 5 | PASS |
| 007 | category enumeration | 13 | PASS |
| 008 | category enumeration | 13 | PASS |
| 009 | abbreviation | 1 | PASS |
| 010 | family lookup | 1 | PASS |
| 011 | family lookup | 1 | PASS |
| 012 | designation expansion | 1 | PASS |
| 013 | designation expansion | 1 | PASS |
| 014 | bounded chart membership | 1 | PASS |
| 015 | bounded chart membership | 1 | PASS |

All **90/90** requested list pairs are retrieved, correct and supported, with
zero omissions, extras, duplicates, code mismatches, hierarchy or binding errors.
The seven lookup/membership facts are **7/7** correct and supported. The original
baseline stays failed for completion; no failed answer was replaced in place.

**160 synthetic software checks passed** in 2.01 s. Eleven independent toy
contracts first failed because the new module was absent, then passed before
owner execution. These checks are not the source accuracy denominator.

The measured command wall time was **374.355 ms**. Engine time was **120.446 ms**:
source projection 89.930, image validation 8.503, QA operations 22.013 ms.
Per-question operations ranged 0.495-5.923 ms. This batch shares source setup;
it is not a matched end-to-end speedup over original per-query execution.
No model tokens or API charge apply; local hardware/energy is not costed.

## Deliverables, limits and stopping point

Full actual answers (all lists), grades and question text are in ignored local
`storage/evidence_v2/a1_qa_run_001/report.md`. Exact raw results and IDs/traversals
are in `graph_qa_raw.json`; source/freeze and all baseline results are retained.
`combined_independent_grade.json` and `grading/` hold separate grading evidence.
Do not publish licensed raw outputs, source graph or private gold.
The source-safe aggregate is `eval/evidence_v2_a1_qa_001_aggregate.json`.

The ordinary CLI remains packet-only; graph QA requires `--graph-qa`.
V1 defaults and ordinary v2/extractive reader behavior are unchanged. No running
server was reloaded, and no generated-answer model or other figure was tested.
Semantic/vector retrieval, formal subtype authority and arbitrary future
page/panel grammar remain outside the result.

A read-only toy audit found one **known generic routing defect outside these
15**: `_resolve_processes` chooses the globally longest literal label and can
silently drop a shorter independent process in a multi-process lookup. Nested
name overlap should still deduplicate, but independent spans need clarification
or explicit multi-entity support. No frozen question is affected. This is the
next repair target; no correction or owner-question replay was made after the
bounded run. Do not generalize these results to multi-process lookup requests.

Stop after this first set. `main`, `HEAD` commit and annotated `v1.0` remain at
`24bac45465bcb5c9ea14663f7a669927d5d2ed00`; local work stays on
`v2/evidence-engine`. Nothing was committed, pushed or merged. Rollback behavior
by selecting v1; do not delete local work or move the baseline tag.
