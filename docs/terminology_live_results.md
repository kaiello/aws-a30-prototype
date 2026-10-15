# Reviewed terminology in live retrieval

Date: 2026-10-15. Branch: `plan/helper-hardening-20261015`; HEAD remains `fc918433b1ff61ccb405104bbcdb70577f149e09`. Changes remain uncommitted and unpublished. This receipt distinguishes synthetic checks, actual retrieval, fresh local generation and restarted-app requests. Reproduction commands alone are not evidence of a run.

## Implemented scope

The live path adds reviewed terminology evidence for three headwords:

| Headword | Preserved distinction |
|---|---|
| `burn-through weld` | Both reviewed preferred targets remain together. |
| `burn-through` | Its standard sense remains distinct from a conditional nonstandard use. |
| `root gap` | The reviewed single-target mapping retains its source identity. |

The adapter in [terminology_retrieval.py](../src/terminology_retrieval.py) reuses the existing parser and record merger in [terminology_mappings.py](../src/terminology_mappings.py). Scoped ontology bindings are manually reviewed against source entries. Cached global statuses and reversed graph relationships do not establish those bindings or change their meaning.

Selection matches the longest whole headword, with case/whitespace and common Unicode dash normalization. A longer `burn-through weld` mention suppresses the overlapping shorter `burn-through` match. Hyphenated suffixes remain outside the match. The raw query is preserved.

Unqualified `burn-through` produces `ambiguous_senses`, retaining both the standard context and the conditional mapping. `qualified_mapping` requires clear intent in the local clause for that entry. Mixed-term, negated or unclear wording remains ambiguous. Ordinary reviewed mappings use `mapped`. Every mapping keeps its targets, senses, process context and qualification; these statuses do not rewrite a global standard/nonstandard classification.

## Retrieval and generation contract

[hybrid_retriever.py](../src/hybrid_retriever.py) checks the existing contextual-store prerequisite first. Relevant terminology evidence is then validated before query expansion or embedding/reranker loading. Unrelated inputs do not read the terminology registry. A zero result limit skips terminology lookup.

The existing sparse search, dense search, fusion and reranking still produce the base candidates. For a matched query, one complete terminology bundle reserves one final result slot after reranking. Remaining base hits retain their relative order and scores. All selected terminology targets and senses stay in that bundle, including when `top_k=1`. This reservation can displace a base hit; it is an intentional capacity tradeoff that must remain visible in evaluation. Unrelated query outputs retain the existing hit shapes, order and scores. No synonym-search expansion was added.

A terminology bundle has its own deterministic `id` and `full_doc_id`, `evidence_type=terminology_mapping`, and `selection_method=reviewed_terminology_lookup`. It does not invent a cosine, fusion or cross-encoder score. Existing source-entry, mapping, ontology and supporting chunk identities remain explicit in its metadata.

`supporting_evidence` carries existing chunk IDs and parent document IDs, actual supplied excerpts, excerpt/content digest bindings, verified source anchors and support annotations. Anchors distinguish zero-based PDF indices, derived viewer ordinals and printed page labels. Membership is not inferred from an identifier, filename or page mention alone.

[query.py](../src/query.py) supplies the unique bundle identity, full mapping records, supporting excerpts and provenance to generation. Its terminology-specific instructions preserve every target and conditional qualifier and request clarification where senses remain ambiguous. Successful matched responses add `terminology_resolution`; existing response keys remain present, and unrelated responses do not gain that field.

A relevant missing, stale or malformed registry returns `TERMINOLOGY_REGISTRY_INVALID`, an empty answer and empty evidence collections with a source-free recovery message. This failure occurs before retrieval-model or RAG/provider initialization. The existing missing-index prerequisite keeps its own error contract. HTTP status and runtime checks must be recorded in the verification receipt.

## Local evidence and preservation

The reviewed registry is local ignored data at `storage/terminology_registry.json`. It contains licensed excerpts and is not a publication artifact. Keep the registry, private relevance labels, captured prompts, raw answers and their receipts local. This document contains no source excerpts, private fingerprints or generated answers.

The adapter validates the document identity against the current source manifest, checks the approved contextual source-file fingerprint, and binds each supporting member to an existing chunk, its content digest, its supplied excerpt and an explicit source anchor. Unknown members, mismatched excerpts, stale sources, incompatible bindings and invalid projections fail explicitly. These checks establish identity and reviewed evidence bindings; they do not independently prove the truth of a generated answer.

Original reviewed entries remain separate from normalized parser projections. Projection spans index local normalized text and are explicitly marked as such; they are not raw PDF text spans, page geometry or certified crop regions. Source and target anchors retain their distinct provenance.

This increment introduces no framework, corpus rebuild, re-embedding, database migration, SQL persistence or graph projection. The adapter reads the existing corpus and the additive local registry. Store/code/runtime-input fingerprint checks in evaluation provide the preservation evidence; final receipt values belong in the verification record.

## Reproduce the bounded evaluation

Use the existing installed environment and approved local model caches. Supply reviewed relevance labels outside the repository and choose a new external output directory for every command. The evaluator refuses reuse of an output directory. It records input/code fingerprints, settings, provenance, errors and timing scope.

A baseline capture must come from the recorded baseline implementation. A `before` label does not turn a capture of the new implementation into baseline evidence. Capture the baseline before adopting the changed code, then use the same reviewed relevance labels for the after capture.

```powershell
python -B -m eval.terminology_live_evaluation capture --qrels "<external reviewed qrels.json>" --label before --output-dir "<new external before directory>"
python -B -m eval.terminology_live_evaluation capture --qrels "<external reviewed qrels.json>" --label after --output-dir "<new external after directory>"
python -B -m eval.terminology_live_evaluation compare --before "<external before directory>/report.json" --after "<external after directory>/report.json" --output-dir "<new external comparison directory>"
```

Optional fresh answers use the captured evidence and the evaluator's fixed prompt/settings with the already installed local `qwen2.5:3b` model:

```powershell
python -B -m eval.terminology_live_evaluation answers --capture "<external before directory>/report.json" --model qwen2.5:3b --output-dir "<new external before answers directory>"
python -B -m eval.terminology_live_evaluation answers --capture "<external after directory>/report.json" --model qwen2.5:3b --output-dir "<new external after answers directory>"
```

Capture exercises the actual hybrid retriever and pre-retrieval gate. The answer phase generates from its captured evidence; it does not itself exercise the complete production LightRAG query/provider path. Production prompt wiring and HTTP/runtime behavior require their own checks. Model/cache provenance, completion state and latency are recorded separately from retrieval metrics. Runtime loading and inference remain bounded local operations; this procedure adds no paid service or package installation.

## Metric units and accuracy limits

Report ranked base-chunk results separately from bundle-at-K coverage. A bundle is one ranked result containing several reviewed supporting excerpts; its members do not become several independently ranked base hits. Credit supporting membership only when the expected source facts were actually supplied with their validated content/excerpt bindings and anchors. Preserve original relevance denominators and disclose missing or uncertain labels.

A target ID hit, a valid source anchor, a correctly activated mapping or a keyword/citation heuristic is not factual answer accuracy. Fresh outputs require source-backed claim adjudication, including all preferred targets, conditional/standard-sense distinctions, qualifiers and citation support. Keep unadjudicated outputs explicitly unadjudicated. A fixed-order run also does not establish a general latency improvement.

The reviewed scope is three headwords. It does not establish corpus-complete terminology, general language disambiguation, diagram understanding, table-cell/footnote fidelity, claim entailment, multi-hop completeness or full multimodal NLQ readiness. Existing broader provenance/scorer heuristics remain subject to their documented limits.

## Verification record

The coordinator fills this record from completed receipts; no pending item is a success claim.

| Evidence | Final record |
|---|---|
| Focused synthetic and existing regression checks | 392 guarded Python checks, plus 44 actual native vector-reader checks, and 26 JavaScript checks passed. The guarded total includes 33 live terminology and 55 evaluator cases; focused totals overlap and must not be added again. |
| Reviewed local registry/source binding checks | Three reviewed entries, five exact excerpt bindings to four existing chunk IDs, and seven scoped ontology bindings. Temporary registry validated against the actual manifest/contextual rows before adding the ignored file. A pre-change backup receipt records that the new registry was absent. |
| Frozen/source-backed retrieval comparison | Both complete 33/33 cases without runtime errors. Twelve graded questions have 18 required evidence groups. Complete evidence at K=1/5/10 improves from 0/1/2 of 12 to 12/12/12. This is bundle evidence completeness. All ten unrelated controls retain exact ranks, scores and gates. All 33 activation/target checks and eight explicit scope gates pass; two forbidden-target checks find no violation. Independent recomputation agrees. |
| Fresh local outputs and independent claim adjudication | Twelve generated answers per phase. Strict factual correctness/completeness improves from 1/12 to 5/12; a disclosed stricter terminology reading gives 4/12 after. Supported frozen required facts improve from 10/32 to 23/32. Neither phase has a completely supported citation set. Three live app answers separately score 2/3 materially correct/complete, with citation errors in all three. |
| Preserved corpus/store/runtime-input fingerprints | All 11 protected existing corpus/store files remain unchanged through captures and live HTTP queries. Existing source/config/security/vector-reader/gold contracts are preserved. The only new evidence data is the ignored reviewed registry. Normal live query response caching is recorded separately. |
| Local application reload and HTTP checks | Verified port-8001 PID 33292 was replaced by PID 5532 on `http://127.0.0.1:8001/`. Port-8000 PID 36636 and Ollama were preserved. Four read-only routes passed, with 62 catalog figures. Three actual generation requests (one `mix`, two `naive`) and one deterministic scope refusal returned HTTP 200 without the upstream-error extract fallback; independent source review finds 2/3 materially correct/complete and citation errors in all three. |

## Evidence interpretation

| K | Before: base-chunk hit / 12 | After: base-chunk hit / 12 | Before: complete reviewed evidence / 12 | After: complete reviewed bundle evidence / 12 |
|---|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 12 |
| 5 | 1 | 1 | 1 | 12 |
| 10 | 4 | 3 | 2 | 12 |

The result establishes complete delivery of the curated evidence for this small reviewed scope. It does not show an improvement to general semantic ranking. Reserving the bundle slot displaces one base hit in the K=10 aggregate. Negative and unrelated cases receive no vacuous evidence-completeness credit.

Both captures use the same frozen source-reviewed suite, evaluator bytes, unchanged corpus fingerprints, cached BGE embedding/reranker revisions, CUDA device and package versions. The source-free independent audit recomputed the evidence bindings and denominators. Preflight failures and an earlier exploratory capture are retained locally and excluded from the primary pair. A UTF-8 fixture rewrite error was caught by digest validation before runtime/model loading, restored from the original freeze and corrected before the primary pair; the original 50-question gold file was not changed.

Fresh local outputs use installed `qwen2.5:3b`, temperature 0, seed 0, 512 maximum output tokens and a shared 32768 context setting. There are 12 generated answers per phase and eight separately retained deterministic gate answers per phase. All 24 generated outputs completed with `stop`; the largest reported prompt has 4372 tokens and the largest output 269, with no observed input/output truncation. These are one fixed-order, single-seed component runs, not confidence intervals or a production-provider benchmark.

The restarted server uses a process-local Custom backend at `http://127.0.0.1:11434/v1` with `qwen2.5:3b`; select **Custom** in the existing UI. The configured default engine and persisted `.env` were not edited. No key is exposed in the receipt. The three actual generation requests took about 32.3, 12.1 and 12.0 seconds; the scope gate took about 58 ms. These four observations are functionality checks, not a latency comparison. All three live generation answers contain citation errors despite the supplied evidence; one also contains term/mapping errors.

No framework integration, package installation, model download, ingestion, re-embedding, SQL/graph rebuild, commit, push or merge was performed. No corpus or source material was uploaded. Licensed registry, source-review records, frozen qrels, prompts, raw answers, cache backups and private receipts remain local. The additive registry cannot be published as source code; code/tests/documentation can be reviewed separately. Full production readiness remains blocked by generated-answer and citation failures and the previously documented broader semantic/security gaps.

## Source-backed answer findings

| Measure | Before | After |
|---|---:|---:|
| All required facts correct and complete, no material unsupported additions, qualification preserved | 1/12 | 5/12 |
| Supported frozen required facts | 10/32 | 23/32 |
| Contradicted / omitted frozen required facts | 12 / 10 | 4 / 5 |
| Qualification preserved | 4/12 | 6/12 |
| Completely supported citation set | 0/12 | 0/12 |
| Partial / incorrect / absent citation support | 0 / 6 / 6 | 4 / 4 / 4 |

These judgments are manual source-backed review, not automatic truth scores. One independent reviewer assessed all 24 randomized, phase-masked outputs against the frozen source facts; the coordinator independently reviewed all outputs, reconciled four recorded uncertainties, and revealed phase labels only afterward. Bundle identifiers can indirectly reveal the phase, so this is partial masking rather than an experimentally blinded trial. The scope is three headwords and twelve deliberately challenging questions, not a representative corpus benchmark.

Correctness/completeness in this table excludes citation quality so that citation failures remain explicit. Answers with correct definitions and wrong page references can pass that content measure and fail citation support. No answer passes a combined full-content-and-complete-citation requirement. Omissions, contradictions, unsupported added claims and clarification are recorded separately in the local receipt. No output is counted as a successful clarifying question. The eight deterministic scope outputs per phase remain separate from the twelve generated-answer denominator.

A sensitivity case concerns one after answer calling a condition a defect. Both reviewers accepted that as ordinary description without an explicit acceptance/rejection assertion; interpreting it as the formal technical classification would reduce the after full-content count to 4/12. Another output retains alternatives but omits the required acknowledgment of insufficient application context; it remains incomplete. A third adds a geometry boundary that differs from the native source; it fails strict additional-claim support. These decisions were resolved before phase aggregation.

Failure patterns include dropping a distinguishing headword suffix, conflating a standard sense with a conditional alias, inventing preferred replacements, omitting one requested alternative/definition, and producing incorrect printed page or figure references. The existing retrieved/generated context still includes legacy hints with conflicting labels. The evaluation demonstrates these output failures; it does not establish how much each context or model factor caused them. The correct reviewed bundle is present in every after case, so bundle delivery alone is insufficient to certify generated answers.

The live endpoint checks separately exercise the actual production query path: one default-style `mix` request, two `naive` requests and a scope refusal through the approved Custom endpoint. The source reviewer finds two of the three generated answers materially correct and complete; all three have citation failures, and the weld answer also conflates terms and invents mappings. Those three requests are functionality/source checks, not a fresh paired production benchmark, and their ratios must not be combined with the component evaluation.

## Final status and local receipts

The bounded code/tests/documentation are ready for owner review on the working branch. They are uncommitted and unpublished. The app is running on loopback port8001 with the approved local Custom model available. Autonomous normative answering, full multimodal NLQ and general publication/deployment readiness are not established. Ordered follow-up work is to remove or subordinate contradictory legacy hints in generation context, enforce claim-to-source citation pairing with meaningful abstention, broaden independently reviewed terminology/evidence coverage, and then evaluate actual table/diagram and multi-hop tasks against source-level facts. These are follow-ups, not changes made in this increment.

Completed local receipts live in the task workspace outside the repository: `terminology-primary-before/report.json`, `terminology-primary-after/report.json`, `terminology-primary-comparison/report.json`, `terminology-answer-adjudication-final.json`, `terminology-live-http-adjudication.json`, and `terminology-live-implementation-receipt.json`. Their raw prompts/answers and licensed evidence remain local. Logs include `terminology-full-offline-final.log`, `terminology-native-vector-final.log`, the two JavaScript logs, and the live HTTP/restart receipts. The implementation receipt records final branch/process/file preservation checks without publishing source excerpts.
