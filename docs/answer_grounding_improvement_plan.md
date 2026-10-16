# Plan: grounded answers, trustworthy citations and bounded multimodal validation

Status: **proposed work only; no implementation or new execution authorized by this document**. Date: 2026-10-16. Baseline: merged `main` at `3cb9f095dd06e0b76298bdabef4b3b847bab9eac` ([PR #3](https://github.com/kaiello/aws-a30-prototype/pull/3)). The production UI remains the delivery surface. Keep the current framework, source inventory, indexes, provider boundaries and established UI layout.

## Measured baseline and limits

| Measure | Existing result |
|---|---|
| Required evidence, same K=1/5/10 | Before 0/1/2 of 12 complete; after 12/12/12 complete bundles, containing all 18 required groups. Base-chunk hits@10 decreased 4/12 to 3/12. |
| Content correctness/completeness | Before 1/12; after 5/12, or 4/12 under the recorded stricter terminology reading. Supported required facts: 10/32 to 23/32. |
| Complete citation support | 0/12 in both phases. After: four partial, four incorrect, four absent citation sets. |
| Actual application requests | Three generated answers: 2/3 materially correct and complete; all three have citation errors. All three nevertheless received provenance 1.0 and `VERIFIED_GROUNDED`. |
| Controls and regressions | Ten unrelated retrieval controls unchanged; eight scope gates and three activation boundaries passed. Post-merge: 392 guarded Python + 44 native-reader + 26 JavaScript checks passed. |
| Timing observations | One mix request about 32.3 s, two naive requests about 12.1/12.0 s, one scope gate about 58 ms. Different routes/cold states and n=1 per question: these are not an SLA or a paired speed comparison. |

The twelve-question comparison used the same questions, 32 required facts, source rubric, installed model digest, prompt specification and settings (local `qwen2.5:3b`, temperature 0, seed 0, output cap 512, context 32768). Its answer lane called the model on captured top-five evidence. It was not a paired full-app/LightRAG evaluation. All generated outputs completed without observed truncation. These small, curated results do not establish corpus-wide accuracy.

Use the existing local receipts rather than rerunning a baseline during planning: primary before/after captures and comparison, final answer adjudication, three-request HTTP adjudication, and Git closeout receipt. See [the source-free results](terminology_live_results.md). Private receipts and evidence remain outside tracked documentation.

## Locate the error before changing a component

| Boundary | Confirmed evidence | Diagnostic distinction and proposed ownership |
|---|---|---|
| Evidence selection | The reviewed bundles now deliver all required facts, but ordinary ranking remains incomplete and the bundle displaces one base hit. | In `hybrid_retriever.py` / `terminology_retrieval.py`, separately record required evidence, IDs, group completeness and qualifiers. Missing facts are a selection/coverage failure; do not repair them with model guesses. |
| Generation/context composition | Outputs conflate full headwords, lose alternatives/conditions, make unsupported additions and contradict their own quotations despite complete reviewed evidence. `query.py` also sends augmented evidence into `rag.aquery`, which can add another context. | Inspect the actual final model input and output through the existing `indexer.py` model seam. Contradictory cached context is a credible contributor, not a proven sole cause. Distinguish input omission/truncation/conflict from an output that violates correct supplied facts. Do not conclude that a larger model alone is the fix. |
| Citation assembly/validation | Wrong printed pages and panel references pass despite valid page/figure names elsewhere in the document. | `citation_checker.py` currently extracts references; valid identity is not claim support. Bind each displayed claim to its actual reviewed evidence and source anchor; render citations server-side. |
| Verification/UI | Graph bridge presence and zero matched concepts can produce a perfect score; the UI also hardcodes verified/100%-traceable wording. | `epistemic_verifier.py`, `answer_routes.py` and `web.py` must distinguish evidence links, assessed claim support, citation validity and execution outcome. A bridge or citation regex is never an entailment test. |

For future runs, capture minimal stage outcomes/timings and input digests through the existing query/model seam. Save full diagnostic prompts only in an explicitly enabled local receipt, never in normal UI/API logs. No new observability service is needed.

## Ordered small increments

Each increment starts with a meaningful synthetic regression and ends with a focused check and independent review. Keep individual changes to roughly two to five files; split a row further if it exceeds that. Do not special-case frozen question strings or place evaluation labels/expected answers in runtime code.

### 1. Make verifier outcomes truthful

**Targets:** `src/epistemic_verifier.py`, `src/answer_routes.py`, a focused verifier test module. Reuse the saved failure patterns with synthetic content.

Separate graph-link coverage from claim/citation support. Zero matched concepts, a generic bridge, any existing page, or an abstention substring cannot establish a correct answer. Require an explicit scope/answer decision before calling an abstention truthful; mixed refusal plus unsupported assertions must not pass. Type/category presence is not measured evidence recall. Keep existing response keys where possible; add explicit assessment states and document changed/deprecated status semantics.

**Gate:** no empty/unmatched/contradictory, wrong-source or mixed-abstention fixture receives a whole-answer verified status. Missing evidence is explicitly unassessed/insufficient. Preserve graph links as navigation, not truth certification. No schema or database migration.

### 2. Reflect those outcomes in the existing production UI

**Targets:** `src/web.py`, a small JavaScript UI regression module, query response tests if an additive field is required.

Replace unconditional verified-citation/100%-traceable text with the assessed outcome. Distinguish an answer, a request for context, insufficient evidence and a generation error. A provider failure or source extract must not appear to be a successful model answer. Retain current query controls, layout, figures/tables, chips, highlights and source navigation. Render evidence/related-term labels with safe DOM text and canonical links; keep diagnostic IDs out of the main user flow.

**Gate:** synthetic UI/API fixtures show every state honestly, treat unsupported/inferred anchors as unverified, resist markup/inline-handler injection, and preserve the current figure/table interactions. Release increments 1 and 2 together so the UI cannot promote a coverage score back into a truth badge.

### 3. Produce a small reviewed fact view with exact citations

**Targets:** `src/terminology_retrieval.py`, `src/citation_checker.py`, focused synthetic tests; reuse `src/standard_manifest.py` without creating a competing inventory.

Project the three reviewed entries into a compact fact view: stable headword/sense, relation kind, all alternative targets, condition/process scope, existing excerpt ID, reviewed entry/span and canonical source anchor. Keep source and target definitions distinct. Preserve each span coordinate space: normalized parser-projection offsets are local text offsets, not raw PDF spans or geometry. Use existing reviewed native-entry boundaries; if any required definition boundary is absent, request a narrow local review instead of inferring it from cached text. Any additive local sidecar curation is a separate proposed data change requiring backup and temporary validation, not authority to rewrite the corpus.

Assemble printed-page/section/figure citations from those bindings, never from model-written page numbers, chunk-name page hints or generic Clause 4 coverage. Validate each claim-to-source pair. An existing but wrong page must fail. Do not silently drop an unknown panel suffix and count its parent figure as proof. Until a panel-specific binding is reviewed, withhold that assertion or cite the supported definition without claiming diagram understanding.

**Gate:** synthetic cases reject wrong existing pages, wrong-sense evidence on the same page, invented panels, missing target-definition anchors, changed source hashes and unsupported claim IDs. All alternatives survive one-result limits. Identity/location checks remain distinct from semantic truth.

### 4. Add a pure bounded answer composer

**Targets:** a small `src/grounded_answer.py` helper and synthetic tests. Reuse the fact view; do not add an agent framework or new model.

For reviewed definition/alias intents, render the supported facts directly with server-assembled citations. Preserve the full headword, every alternative and the standard-versus-conditional distinction. Correct false only/always premises; state when application context cannot select an alternative. Mixed-headword and negated intent must stay local to the relevant term. Missing facts lead to clarification/insufficient evidence. Keep optional explanatory prose outside the verified portion unless its support is established.

**Gate:** tests cover all targets, conditional/process restrictions, standard senses, no/cannot/contractions, Unicode spelling, missing application context, negated mentions of excluded topics, false extra targets and unsupported universal conclusions. Do not grade success by keyword presence or include real licensed definitions in synthetic tests. This is a bounded extractive/template route, not evidence of improved model reasoning.

### 5. Wire the composed answer through the real query path

**Targets:** `src/query.py`, a narrow reusable generation seam in `src/indexer.py` only if necessary, focused query/provider-fixture tests.

Use the validated composer for the reviewed intents. Its facts must not compete with a second unrestricted LightRAG context. Keep other queries on the existing path. If generation is needed for a supported extension, send only the explicitly selected evidence through the existing approved client and validate the output; otherwise retain an unassessed/insufficient status. Preserve endpoint validation, cache/model fingerprints and provenance. Keep the cheap deterministic composer uncached initially; any generation cache must distinguish the new route/source/prompt revision so old incorrect answers cannot replay. Do not clear shared caches. No automatic model-repair loop or silent provider/model substitution. Record `extractive`, `generated`, `clarification`, `abstention` and `error` outcomes separately; use source-free client errors.

**Gate:** fake-provider integration tests inspect the actual input and prove no stale page/status hint or second retrieval overrides the reviewed facts. Timeout, malformed output and incomplete evidence cannot be counted as an answer. The eight scope gates, ten unrelated retrieval controls, three activation boundaries and existing API/asset contracts remain intact. No live call is needed to test this wiring.

### 6. Re-evaluate correctness through the production UI

**Targets:** `eval/terminology_live_evaluation.py` and its tests for separate component/system lanes; narrow UI/browser checks for `src/web.py`. Update source-free results only after completed receipts.

After explicit authorization for bounded local execution, replay the unchanged twelve questions/rubric and original three app cases. Freeze six independently reviewed paraphrase/negative holdouts before viewing outputs. Keep failed, clarified and unanswered cases in their declared denominators. Compare equal retrieval cutoffs and keep the component-generation lane unchanged. A new deterministic answer path must be labeled as such and evaluated as system correctness, not presented as a model-only accuracy gain. Do not quietly change the gold or reinterpret an omitted required fact as a pass.

**Release gate for the bounded terminology answer path:** all 32/32 required facts supported, 12/12 complete answers under the frozen allowed clarification policy, 12/12 complete claim-to-source citation sets, no material unsupported additions or lost qualifiers; all original three full-app answers pass both content and citation review. Six holdouts and existing controls must pass their predeclared policies. Report answer coverage, safe clarification, abstention, errors and sensitivity cases separately. A safe refusal on an answerable case is not full-answer credit. Preserve the 436 selected Python/26 JavaScript baseline, running affected checks after each slice and the selected suite before release. No production-readiness claim follows merely from this small gate.

## Later gated work

### 7. Bounded multimodal validation before expansion

Only after the terminology gates pass, freeze six source-reviewed UI tasks using existing assets: two table questions (including a footnote/qualifier), two diagram questions (requiring a spatial/panel distinction), and two text-plus-visual questions (including multiple required evidence groups). Add a missing/unsupported visual control and a same-page distractor control. Reuse scope/negative controls; do not count them as vacuous complete answers.

**Targets:** existing `src/query.py`, `src/answer_routes.py`, `src/figure_inspectors.py` / `src/standard_manifest.py`, and a small evaluation sidecar/harness. Change extraction or model code only after a demonstrated local failure identifies a need.

Measure evidence identity/content, table cell/footnote fidelity, source pairing, answer facts, and the displayed/clickable asset separately. Use text-only/image-withheld ablations where visual dependence is claimed: showing the right image or answering from labels is not pixel reasoning. If the current runtime cannot consume the required image/table detail, record unsupported capability; do not invent success or switch models. A bounded VLM/model/asset correction would be a separately approved proposal.

**Gate:** 6/6 answerable workflows meet all required facts/groups and source pairing, no fabricated cells/geometry/targets, both negatives handled correctly, and existing UI interactions preserved. Clarification is permitted only by frozen expectations. This small success would still not certify general multimodal or multi-hop completeness. The corrected text route can be released independently; unsupported visual capability blocks the multimodal claim, not honest text-only delivery.

### 8. Measure latency, then remove demonstrated bottlenecks

**Targets:** lightweight timing in `src/query.py`, `src/hybrid_retriever.py`, the existing `src/indexer.py` client seam and `src/web.py`; an external evaluation receipt. Split instrumenting and optimizing into separate small changes.

With correctness fixed, predeclare identical UI routes, models/settings, hardware, timeout and cache policy. Record cold start separately. Choose six workflows that have passed source-backed correctness: the initial set can use text/terminology UI tasks without waiting for visual capability. Measure visual latency separately after its own gate. For those six representative workflows, propose five interleaved baseline/after repetitions: 60 warm full-app requests total, plus a separately bounded cold sample. Record model loading, expansion, sparse/dense retrieval, reranking, optional graph work, generation/validation, and browser-visible completion. Separate cache hits from fresh inference; retain errors/timeouts. Report counts, p50/p95 and ranges with small-sample limits.

Before executing, choose the absolute UI budget with the owner; the existing 12-32 s observations cannot justify one. Propose no more than a 10% paired warm p95 regression, with zero correctness/citation regressions. Do not claim a stable p95 from this small sample. Only then consider eliminating duplicate retrieval/model initialization, repeated registry parsing, or context bloat where traces show a cost. Cache keys must include source/registry, route/prompt, model/settings fingerprints; bypassing stale checks for speed is prohibited. No benchmark run is authorized now.

## Stop conditions and authority

- Stop the affected increment on missing/stale evidence, unresolved source/citation/qualifier contradictions, false scope abstention, incomplete target groups, new unsupported assertions or unrelated regressions. Preserve the failing receipt; do not tune labels, remove cases or loosen scoring.
- Stop before any new model/provider, download, added paid capacity, corpus rebuild/re-embedding, database/graph replacement or unreviewed source expansion. Propose it with evidence and scope; obtain separate authorization. All such changes in this document are proposals only.
- Stop evaluation on source/qrels/model/config drift, truncation, provider errors, unapproved writes, or private-data exposure. Restore only task-owned changes through a reviewed rollback; do not delete owner work or rewrite protected stores. Do not retry generation indefinitely.
- Keep licensed registry/source PDFs, source spans, qrels, screenshots, prompts, answers, caches and backups local/ignored or in the external task workspace. Publish only approved code, synthetic fixtures and source-free aggregates. Preserve hashes and existing security boundaries. Public artifacts must not embed gold facts or private model inputs.
- The current request authorizes planning/documentation only: no implementation, model runs, corpus changes, app restart, branch creation, commit, push or merge. Execution, deployment and any new data/model scope require a subsequent owner instruction. Independent review is required at each acceptance checkpoint.

## Proposed delivery order

First checkpoint: truthful verifier outcomes and UI labels (1-2). Second: fact/citation bindings and bounded composer wired end-to-end (3-5). Third: source-backed UI acceptance (6). Later, separately gated: multimodal capability (7) and speed measurement/optimization (8). Latency work depends on correctness in its measured scope; it need not wait for unsupported multimodal capability. Parallelize synthetic UI/verifier tests or independent source-label review only after their shared response/fact contract is fixed; keep shared query/generation edits under one owner.
