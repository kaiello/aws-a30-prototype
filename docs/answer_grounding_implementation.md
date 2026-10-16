# Bounded answer grounding implementation (2026-10-16)

Implemented on `fix/answer-grounding-20261015` from `3cb9f095dd06e0b76298bdabef4b3b847bab9eac`. The initial frozen run missed two process-scope qualifications. A subsequent bounded repair passes the same content/citation criteria as a **development result**; the reused holdouts are no longer fresh unseen validation. Real-browser functional checks pass with one retained favicon 404 finding; the strict clean-network assertion fails. The implementation and evaluation below precede the separately authorized repository closeout.

## Development repair after the preserved initial failure

The only runtime repair adds one uniform, explicitly labeled application scope note to successful composed answers and separate `answer_policy_notes` metadata. It states the limit of the supplied reviewed entries without inventing a process rule, source quotation or absence anchor. Factual claims, fact IDs, canonical citations, alternatives, conditions and outcomes are unchanged. The full rendered answer hash includes the note. Four synthetic cases reproduced three missing-note failures and one guard-preservation pass; all 104 affected composer/query/assessment checks then passed. Independent code review cleared the two-file delta (`src/grounded_answer.py`, `tests/test_grounded_answer.py`).

The repair required a second reload of only the verified port-8001 prototype; port 8000 and Ollama retained their original process identities. The unchanged 18 cases were captured again using the same frozen executor, local model identity, transport, case files and rubrics. An independent reviewer revalidated source support and exact bindings. The final capture is explicitly **DEVELOPMENT**, informed by the prior holdout failure category. Implementers did not receive raw holdout text, but this repair cannot count as independent unseen generalization.

| Cohort | Initial strict complete | Repaired development complete | Initial facts | Repaired facts | Repaired complete citations |
|---|---:|---:|---:|---:|---:|
| Original 12 | 11/12 | 12/12 | 31/32 | 32/32 | 12/12 |
| Reused holdout six | 5/6 | 6/6 | 19/20 | 20/20 | 6/6 |

All 18 repaired responses remain composed: 16 extractive and two safe clarifications, with zero runtime errors, zero unsupported/contradicted additions and 58/58 asserted factual bindings valid. The two repaired explanations are explicit evidence-scope policy, not fabricated native source facts. All 27 required source groups remain present. The rubric, denominators, initial failed outputs and initial adjudication hashes were not changed. The exact original 20-file implementation/test snapshot, four original documents and original handoff were preserved before repair. These observations establish bounded source composition, not model-reasoning improvement or full multimodal NLQ readiness.

The later owner authorization resolved the initial browser denial. A fresh isolated installed Chrome profile exercised the original three query flows and one scope control using native input, then loaded the canonical Figure B6 image and printed-page range, verified stale evidence clearing and 62 figure tiles. Four UI submissions passed, with zero JavaScript errors, zero external requests and no horizontal overflow. The strict clean-network assertion remains failed because `GET /favicon.ico` returned 404. This low-impact missing favicon does not affect the observed answer/figure flows; it was not suppressed or fixed in this bounded repair. The first executed browser harness also had an incorrect blank-status expectation, corrected to the existing `Figure inspection` contract; partial attempts are preserved. Private screenshots stayed local. Browser checks use UI mix mode; prior exact HTTP mix/naive/naive acceptance remains separate.

## Runtime behavior

`src/query.py` applies the deterministic scope gate first. For bounded definition/alias intent, `src/grounded_answer.py` projects the existing three-headword reviewed registry into exact source-bound facts, preserves complete alternative and conditional senses, and composes a deterministic answer before provider initialization. Selection requests without application context return clarification while preserving reviewed alternatives. Unsupported intent continues to the existing hybrid/LightRAG generation path. Missing relevant evidence and provider failures have explicit structured outcomes.

The query/terminology adapter reads the existing reviewed registry and supplies a validated bundle to the pure composer; no second fact registry, corpus rebuild, embedding change, index migration or framework integration was introduced. Exact native source spans, excerpt and whole-chunk hashes, document identity, printed/PDF anchors and fact-to-claim bindings are checked. The additive canonical section label changes content-addressed bundle identifiers; underlying source, chunk and mapping identities are preserved.

Responses distinguish `answer_outcome` (extractive, generated, clarification, abstention, insufficient evidence or error) and `answer_origin` (composed, generated or none). `answer_assessment` binds its status and scope to the exact answer hash. A validated reviewed-fact status means the asserted facts have reviewed source bindings; it does **not** prove the answer covers every part of the question. Graph reachability and numeric link coverage do not establish truth. Unassessed provenance/recall metrics stay nullable, including in the legacy scorer.

The existing UI shows these outcomes and renders evidence text and local source navigation safely. Stale answer evidence is cleared on a pending query, error and direct figure inspection. The layout, figure assets, geometry, provider configuration and model selector defaults are unchanged. Local capture explicitly selected Custom with `qwen2.5:3b`; the UI default does not establish which provider a user has selected.

## Initial frozen source evaluation before development repair

The original 12 questions, 32 required facts and 18 citation groups were preserved. An independent reviewer froze six unseen holdouts (20 facts, nine groups) before implementation/inference. Implementers did not read holdout questions, answers or labels. An independent source reviewer graded the fixed outputs without changing the rubric. Private queries, reviewed excerpts, source material, raw responses and detailed judgments remain outside published source; this document contains aggregate results only.

| Capture | Strict complete answers | Supported required facts | Strict complete answer citations |
|---|---:|---:|---:|
| Original 12, initial actual HTTP system | 11/12 | 31/32 | 11/12 |
| Holdout six, prior actual HTTP system | 1/6 | 13/20 | 0/6 |
| Holdout six, initial actual HTTP system | 5/6 | 19/20 | 5/6 |
| Separate original three HTTP replay | 3/3 | 9/9 | 3/3 |

All 18 initial responses were **composed**: 16 extractive and two clarification outcomes. There were zero execution errors, zero invalid asserted factual bindings (58/58 valid) and no material unsupported or contradicted additions. All 27 required source groups were present. Complete answer-citation coverage remains 16/18 because each omitted proposition also lacks an asserted citation; presence of a source group cannot repair an omitted answer requirement. The two missing facts are explicit acknowledgments of the limits of a process-qualified definition. The two context-selection clarifications passed their frozen safety criteria.

For the initial run, the release gate remains false for both cohorts. The later development repair is reported separately above. Alternative sensitivity judgments are preserved separately rather than weakening the primary rubric. The three HTTP replays preserve their original mix/naive/naive modes and pass all nine facts, four citation groups and eight asserted bindings. A separate scope request passed its deterministic policy check.

The six holdouts have a paired actual-system baseline; the original 12 do not have a matched prior actual-system capture in this phase. Earlier 12-question component-prompt results are a distinct lane. The before/after system capture used identical frozen executor bytes, inputs, local model identity and transport. The deployed comparator validated that six-case pair and explicitly listed the 12 unmatched after cases. These results demonstrate bounded source composition, **not an improvement in LLM reasoning or model-generated accuracy**.

## Retrieval controls and rejected comparison

The unchanged frozen 33-case retrieval suite captured without errors. A separate independent offline audit recomputed its metrics: complete reviewed evidence is 12/12 at rank one, all 18 required evidence groups are present, all eight scope gates pass and both forbidden-target checks pass. All ten unrelated controls have exactly equal IDs, order, full document IDs, raw/RRF/cross-encoder scores and gates across original before, original after and current captures. This phase preserves the prior adapter's retrieval behavior; it establishes no new retrieval gain.

The legacy comparator **rejected** original-to-current comparison because evaluator full-file fingerprints differ. That rejection was preserved. The historical source copy matches the historical receipts; the current source matches the new receipt. The two files are byte-identical after CRLF-to-LF normalization and have identical full-module ASTs, identifying newline representation as the cause of the full-file hash mismatch. Independent audit recomputed the rows independently and cross-checked them with the current pure functions. This separate audit supports the stated observations; it does not convert the rejected comparison into a passing certified run. Evidence retrieval metrics do not establish answer correctness.

## Original verification and retained boundaries

- 570 guarded Python checks passed against actual deployed code.
- 44 actual native vector-reader checks passed separately.
- 40 JavaScript scenarios passed: 14 new answer-grounding, 22 geometry and four settings scenarios. These are synthetic checks, not real-browser acceptance.
- Independent code/deployment review cleared the bounded contracts and verified all 20 implementation/test files against their pre-capture hashes. Independent source grading and retrieval audit are separate from those checks.
- The initial app reload replaced the verified loopback port-8001 prototype. Port 8000 and Ollama retained their process identities. Twelve protected source/store/manifest/registry files and the owner's improvement plan remain byte-identical; the documented query response cache is tracked separately.

The initially blocked installed-Chrome acceptance helper was limited to a fresh task-only profile and localhost-only requests. Automatic approval review rejected it before launch because it treated the original read-only request as governing authorization and reported no later trusted user approval of those side effects. No retry occurred during that initial blocked phase. At that stage browser rendering, console/network behavior and figure navigation were unverified in a real browser; the initial blocker is preserved historically. Later authorization and executed browser outcomes are reported above.

## Follow-up priorities

1. Obtain a fresh independent validation set before claiming unseen generalization from the repaired behavior. Retain both the initial failed run and the repaired development run; never silently change their rubrics or labels.
2. Address the minor missing favicon separately if a zero-failed-network-response browser gate is required. Preserve the current failed assertion and original HTTP/UI mode distinctions.
3. Evaluate unsupported intents and actual generated answers with claim-level citation/abstention grading. Unassessed generation remains unassessed.
4. Treat broader terminology, table-cell/footnote fidelity, diagram-region semantics, cross-modal relations, multi-hop completeness and broader model evaluation as separate milestones. Full multimodal NLQ is still undemonstrated.

## Publication closeout regression check (2026-10-16)

Before publication, the exact repaired implementation passed the full guarded suite: **574 Python checks**, plus **44 actual native vector-reader checks** and **40 JavaScript scenarios**. The Python guards disable dotenv/model initialization and reject database/external socket effects while permitting only the Windows event loop's private wakeup pair. Native tests retain the installed LightRAG reader and synthetic in-memory fixtures. No new accuracy inference, unseen evaluation, corpus write or model/provider call was performed during closeout.

The authorized publication scope is reviewed source, synthetic tests and source-free documentation, including the preserved original improvement plan. Licensed source/registry material, private qrels/prompts/answers, detailed receipts, backups, credentials and runtime stores remain local. PR metadata and Git history record publication SHAs. The original unseen failure and repaired DEVELOPMENT results above remain separate; the favicon 404 remains a non-answer-impacting browser limitation. This bounded grounding change does not establish full multimodal NLQ or general model-reasoning readiness.

## Private evidence inventory

Task-local source-free summaries and hash receipts include `answer-grounding-system-after-adjudication.summary.json`, `answer-grounding-holdout-before-adjudication.summary.json`, `answer-grounding-live-http-adjudication.summary.json`, `answer-grounding-retrieval-independent-audit.json`, `answer-grounding-system-comparison/report.json`, `answer-grounding-implementation-freeze.json` and `answer-grounding-browser-blocker.json`. These names are evidence references, not distributable source data. The first HTTP helper attempt stopped after one response because it mistakenly counted the mutable cache among protected corpus files; its partial output is preserved and excluded from source grading. The corrected replay kept all twelve corpus files protected and passed.

Development evidence additionally includes `answer-grounding-repair-implementation-freeze.json`, `answer-grounding-development-repair-manifest.json`, `answer-grounding-development-repair/report.json`, `answer-grounding-development-repair-adjudication.summary.json`, `answer-grounding-browser-final-result.json` and `answer-grounding-original-failed-implementation/snapshot.json`. The original evidence listed above is preserved and remains the original observation.
