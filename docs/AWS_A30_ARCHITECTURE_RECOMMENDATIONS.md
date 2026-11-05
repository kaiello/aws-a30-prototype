# AWS A30 Architecture Assessment and Recommendations

## Current assessment: November 5, 2026

**Recommendation:** retain the evidence-first foundation, repair evidence admission and application reporting, and evaluate hybrid page discovery plus conditional page-and-region VLM reading. Move away from expanding question-specific answer composers toward a shared, source-native evidence-packet route. A wholesale replacement, a production VLM fallback, and a new retrieval framework are not yet justified.

**Decision status:** findings and recommended direction recorded at the owner's request. This documentation does not implement the proposed system, qualify a reader, or complete the ongoing human review. The November 3 assessment is retained below as history; its old route and provenance findings must not be treated as unchanged current defects.

### Snapshot and verification limits

- Reviewed checkout: `feat/gate-6-7-independent-evaluation`, commit [`9475df7bc75ada23e8ddb8d401bd578bfb25eebb`](https://github.com/kaiello/aws-a30-prototype/tree/9475df7bc75ada23e8ddb8d401bd578bfb25eebb), clean before and after the read-only review. Main at review time: `27ab96ed6b8809b1990d4d32abfd38ea586cf54f`.
- Scope: source extraction, evidence/knowledge stores, NER and planning, retrieval, visual adapters, model interfaces, application routes, configuration, tests, evaluation receipts, and existing bakeoff research. Findings below refer to the reviewed feature snapshot; this documentation-only merge does not merge its Gate 6.7 implementation into main.
- Completed during review: 96 focused Gate 6.7 tests passed in 7.23 seconds; bounded in-memory connector/scorer diagnostics; read-only source, store, asset and saved-receipt checks. The source PDF hash matched `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` (190 pages).
- Not completed: new model inference, dense-index rebuild, browser end-to-end validation, fresh held-out evaluation or full regression. The earlier 1,630-test regression attempt remains incomplete. Hash parity establishes preserved bytes, not correct interpretation.
- Source observations made by agents below are not human adjudication. Ken's ongoing eight-question/16-answer review remains separate and pending; no reviewer judgments are assumed or changed here.

### What is implemented today

| Route or component | Implemented behavior | Current boundary |
| --- | --- | --- |
| V1, browser/API default | Reviewed terminology shortcut; otherwise text hybrid retrieval and LightRAG | Missing contextual dense store blocks hybrid before available BM25; not a page-image reader |
| Explicit whole-standard route | Deterministic dispatch, structured stores, answer composers and provenance | Bypasses hybrid/local vision; model selection does not change its deterministic planner |
| Explicit V2 local reader | Real native image transport to Ollama | Bounded projection: six fixed terms, B6 and A2/A3, plus a separate A1 workflow; no arbitrary-diagram fallback |
| Gate 6.7 reader adapter, feature branch | Source-only inputs, explicit IDs, pinned digest, captured requests/raw outputs | Evaluation component; not yet connected as a general product route or semantically qualified |
| Source/evidence foundation | Source identity, crops, native extraction, tables, typed graphs and replay quarantine | Assurance differs by ingestion adapter; accepted status is not uniformly independently verified |

Route evidence: [`src/query.py:219-329`](https://github.com/kaiello/aws-a30-prototype/blob/9475df7bc75ada23e8ddb8d401bd578bfb25eebb/src/query.py#L219), `src/web.py:1079-1088,1833-1855`, `src/evidence_sources.py:20-21,124-151,236-299`, and `src/independent_reader_evaluation.py:45-76,99-142` in the reviewed snapshot. The browser sends no whole-standard/V2/local-reader selector.

### Findings that change the next milestone

1. **Repair admission before expanding accepted knowledge.** A4-A6 copy manually specified graph nodes and edges (`src/archetype_decision_tree.py:378-425`). Their connector check (`:141-155`) asks whether a native line endpoint lies in a broad rectangle spanning declared nodes; it does not trace the declared connection. An ephemeral invented direct A4 root-to-TW edge still returned a verified connector. This proves a checker weakness, not that every stored edge is wrong. Annex B can insert missing expected callouts as `ACCEPTED`/`knowledge_eligible` before its vocabulary check (`src/archetype_spatial_callout.py:512-575,720-735`). Agent inspection found B46 zone labels and B54 waveform details supplied by specifications but absent as printed source labels. Across seven waveform figures, 63/96 trace/interval/parameter nodes have zero matched native spans yet remain accepted (`src/archetype_cycle_waveform.py:194-246,304-342`). Curated engineering enrichment needs separate attribution and review authority.
2. **Remove automatic semantic-review authority.** [`src/query.py:291-313`](https://github.com/kaiello/aws-a30-prototype/blob/9475df7bc75ada23e8ddb8d401bd578bfb25eebb/src/query.py#L291) maps executor PASS/CONTRADICTION_REFUTED to `SUPPORTED_REVIEWED_FACTS`, `validated=True` and exact citation support on locator presence, bypassing ordinary generated-claim guards. A successful operation and a locator do not establish source entailment or human review. A fallback triggered only by no answer would miss unsupported answers already labelled successful.
3. **Replace expanding special cases with per-part evidence coverage.** The whole-standard planner is priority-ordered semantic/keyword dispatch, with fixed entities and figure mappings (`src/evidence_phase4_bakeoff.py:205-848`). Literal answer narratives remain, for example the temper-bead branch (`:2752-2799`). Some provenance enrichment still supplies page defaults when exact provenance is absent (`:3506-3528`). This is a bounded curated application, not demonstrated general reading. Its primary page/crop fields are insufficient as the sole support representation for compound answers.
4. **Fix lineage and annotation errors separately from OCR.** Clause 4 merges continuation blocks but retains a starting page (`src/evidence_clause4_glossary.py:192-202,340-347`): stored SAW text includes PDF 69 content but records PDF 68 alone. Annex C preserves raw text but adds incorrect manually authored titles and a C1.5.7 takeaway (`src/evidence_annex_c_d.py:45-65,167-174`). A3 declares OCR/vector engine provenance without executing the claimed extraction; its all-candidate status appropriately limits authority (`src/evidence_a3.py:64-133,341-346`). A different OCR engine would not repair these metadata/admission defects.
5. **Repair the existing hybrid route before adding one.** The read-only registry has 266 FTS rows, but the contextual dense store is absent and required before BM25 (`src/hybrid_retriever.py:67-74,203-220`). Rebuilding now would omit glossary text: `src/contextual_indexer.py:115-149` reads a missing KV file instead of available parsed text. Index construction hardcodes BGE/1024 while retrieval accepts a configurable model without validating identity, dimensions or source version (`:37-38`; `src/hybrid_retriever.py:47-50,119-130`). These are availability/compatibility findings, not measured retrieval-quality scores.
6. **Connect and expose real visual reading deliberately.** V2 sends actual image bytes (`src/evidence_reader.py:71-103,227-249`), but whole-standard crop flags do not invoke it. Its storage crops also cannot resolve through the current browser asset mapping: 80 Annex B crop basenames have zero overlap with 111 served parsed figure assets (`src/web.py:837-845,1770-1780,1899-1900`). This is a static route/asset finding; browser end-to-end behavior was not rerun. Reuse the stronger Gate 6.7 pinned adapter rather than adding another independent reader path.
7. **Separate evidence coverage, reader behavior and semantic grading.** The Gate 6.7 scorer requires corpus-level gold pages/status even when the supplied packet is insufficient, penalizing a precise packet-limited abstention. It checks declared claim text occurs in an answer, but not whether extra material assertions are undeclared (`src/independent_reader_scoring.py:79-115`). Exact expected evidence-ID equality (`:176-180`) cannot represent valid alternative support groups. Add complete predicted-claim/citation judgments, AND-of-OR evidence groups, and packet-conditional abstention alongside corpus answerability. Structural validity must remain distinct from semantic support.

Preserve the strongest controls: genuine A1 native geometry (`src/evidence_a1.py:287-309,375-407`), A2 bounded OCR/pixel admission and quarantined AI observations (`src/evidence_a2.py:403-439,532-557,793-800`), native table/anomaly extraction, immutable source identities, and genuine/synthetic replay separation. Zero accepted IS_A assertions in the inspected chart stores does not independently validate their other accepted claims.

### What the evaluation evidence establishes

- Gate 6.7: eight exposed development cases, 16 completed local `qwen2.5vl:3b` calls, digest `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`, temperature 0/seed 67, 16,384 context, 1,200 output limit, 120-DPI full pages and two-page budget. Four application packets miss at least one agent-selected gold page. Outcomes: **14 structural failures, two pending reviews, zero human-adjudicated answers, zero held-out cases**. No semantic accuracy or retrieval-quality delta is established. See the feature-branch [observed results](https://github.com/kaiello/aws-a30-prototype/blob/9475df7bc75ada23e8ddb8d401bd578bfb25eebb/docs/gate67_observed_results.json) and [checkout](https://github.com/kaiello/aws-a30-prototype/blob/9475df7bc75ada23e8ddb8d401bd578bfb25eebb/GATE_6_7_CHECKOUT_CARD.md).
- Gate 6.6's retained answer-derived gold/copy composer is circular (`src/reader_qualification.py:117,225`); 24/24 and zero delta are historical harness outcomes, not independent reader qualification. Existing quarantine/provenance integrity work is not invalidated by this evaluation defect.
- Earlier A1 bakeoff: deterministic reference 31/31, full image-plus-native-text control 21/31, PageIndex component 11/31. These were exposed development questions with differing contexts/call counts, not a universal framework ranking (`docs/a1_bakeoff_results.md:8-35`).
- Earlier source-reader aggregate: 4/6 original cases; paired text-only 0/2 versus pixels 1/2. The unchanged-v1 live comparison remained incomplete (`eval/evidence_v2_source_reader_aggregate.json:5-45`). This supports investigation, not reader qualification.
- Saved earlier provider receipts exist, but phase3/phase4 current result artifacts describe replay, and phase4's optional other-provider branch only checks key availability (`eval/run_phase4_bakeoff.py:227-241`). Do not describe it as an executed multi-provider quality comparison.
- Historical NavyWeld results are advisory on different sources: reader failures despite correct retrieval, fusion rescues alongside more harms, and invalidated scorer-driven claims. They are not current AWS measurements (`docs/navy_weld_multimodal_lessons_learned.md:30-78`).

### Recommended future route and evidence boundaries

1. Bind the question to the authorized edition and decompose it into explicit subquestions. Preserve false-premise, ambiguity and out-of-corpus dispositions.
2. Use reviewed/independently supported deterministic lookups first. Check sufficient evidence and qualifiers **for each subquestion**, not only executor status.
3. Discover missing evidence with exact IDs/metadata, BM25 and a compatible dense text index. Rank pages, then assemble required continuations, tables, legends and notes. Page-level evidence is appropriate; one page is not always a complete evidence group.
4. Assemble one source-native packet with PDF hash/edition, PDF index/viewer/printed identities, text spans, full-page overview, targeted regions, transformations and evidence IDs. Keep answer rubrics and generated answers out of reader input.
5. Invoke the pinned local VLM only for unresolved visual labels/relationships or interpretation that native text cannot support. Supply page plus relevant regions and native text; keep all observations source-linked. A missing answer alone is not a safe trigger.
6. Check every material claim, citation, qualifier and requested part. Return supported parts with explicit limitations; abstain on unresolved parts. Never infer procedure settings or numerical values from unscaled qualitative sketches.
7. Keep VLM observations and unreviewed interpretations in a candidate channel. A separate named review/admission decision can promote supported claims to reviewed knowledge; schema success, image hashes and citations alone cannot perform that promotion.

Existing components above are reusable but disconnected. Per-subquestion sufficiency, general page discovery/assembly, conditional reader orchestration, complete claim checks and consistent review authority are **proposed repairs/extensions**, not implemented capabilities.

### Bounded comparison and decision gates

| Stage | Fixed elements and comparison | Evidence needed to continue |
| --- | --- | --- |
| Development repair | Existing eight cases; complete Ken's source/answer review; repair admission, scorer, provenance and route labels | Independent semantic judgments separate from structural outcomes; no tuning on a new holdout |
| Retrieval only | Current selection vs BM25 vs BM25+dense; no generation; equal page budget | Complete support-group recall, relevance, binding, case-level rescues/harms |
| Gold reader | Same pinned reader/prompt/budget; native text vs images vs both on independently checked gold | Identify presentation/reader errors independently of retrieval |
| Composed alternatives | Deterministic baseline; hybrid selection with fixed reader; conditional VLM on baseline pages; both | Supported-claim precision, completeness, citation relevance, qualifiers and packet-conditional abstention |
| Frozen screening | Freeze code/config/triggers, then independent custodian creates 16-24 private questions | Report all cases/denominators; screening evidence only, not production reliability; retire to regression after tuning |

Start with the installed local model, at most two source pages and one reader inference attempt per query, no automatic retry. Record budget exhaustion. Any larger budget or different model is a separately disclosed comparison. Measure retrieval, rendering, model loading, generation and validation separately, including cold/warm p50/p95, memory, calls/query, index footprint and incremental cost. The 16 saved pilot service durations span 0.78-32.28 seconds, median 3.36; these are not end-to-end SLA measurements. Zero local API charge is not zero compute cost.

Defer ColPali/ColQwen page-image retrieval until reviewed evidence demonstrates necessary pages missed by text/metadata retrieval while the fixed reader succeeds with gold. Image retrieval is not diagram interpretation; retrieval heatmaps are not citations. Use the primary [ColPali paper](https://arxiv.org/abs/2407.01449) and [ColQwen model card](https://huggingface.co/vidore/colqwen2.5-v0.2) for capability/compatibility checks, not AWS performance claims. No model download or migration follows from recording this recommendation.

### Owner decisions and continuation

Ken's ongoing task is domain review of all 16 outputs, including structural failures; engineering owns protocol/admission/index/route repairs. Owner decisions still needed: whether source-grounded but unreviewed interpretations may be user-visible, acceptable latency/cost limits, local-only versus a separately approved external route, and held-out custodian/critical-error criteria. No proposed architecture is implemented by this document. The human-review packet and raw private receipts remain separate from repository publication.

The future-system diagram is an explanatory deliverable for this recommendation, not proof of implementation. Its legend must distinguish existing components, proposed connections/repairs, and evidence/candidate/reviewed authority.

---

## Retained historical assessment: November 3, 2026

The following assessment is retained for decision history. Read its observed defects against its stated older snapshot; the November 5 findings and sequence above control the current recommendation.


Date: November 3, 2026  
Audience: Solution architecture and engineering leads  
Status: Recommendation for owner review, not authorization to execute changes

## Executive recommendation

**Retain the evidence-first architecture. Redirect the next milestone toward one validated end-to-end user workflow before expanding the retrieval stack.** A wholesale pivot to visual RAG, OCR, another graph database, or a new orchestration framework is not justified by the reviewed evidence.

The strongest near-term experiment is **reader qualification using correct source evidence**, followed by a bounded **ColPali or ColQwen visual-retrieval comparison** on demonstrated retrieval misses. Keep source-native retrieval as the baseline and promote a new component only when it improves independently evaluated results without unacceptable regressions.

The architecture has useful foundations: source identity, typed evidence, separation of candidate interpretations from accepted knowledge, deterministic access, and abstention. The immediate weaknesses are inconsistent provenance, different demo and evaluation paths, stale acceptance documentation, and an evaluator that does not establish the full product claim.

The appropriate maturity description is **a promising development system whose end-to-end production acceptance remains unproven**.

## Review scope and evidence limits

The November 3 review inspected the requested goal and Gate 6.4 documents, relevant implementation, the source PDF, evaluation artifacts, and archived Navy Weld bakeoff material. It included bounded read-only diagnostics. No repository files were changed, servers launched, source documents uploaded, or credentials accessed.

The full test suite and live model route were not exercised. Git metadata identified `fix/gate-6-4-1-provenance-integrity` at `8f8616e`, with `main` pointing to the same commit. Worktree resolution prevented verification of checkout cleanliness and whether all disk corrections were committed. Findings describe the inspected snapshot, not a guarantee about subsequent changes.

In this document, **observed findings** refer to that review. **Recommendations, phases, and acceptance criteria** are proposed next steps, not completed work or existing project requirements.

For compact references, `R` denotes:

```text
C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest
```

Primary requested documents:

- `R\docs\goal.md`
- `R\GATE_6_4_CHECKOUT_CARD.md`

## Architectural assessment

### Retain the core design

An engineering reference assistant must distinguish what the source says from what a model infers. The project's distinction between source observations, candidate interpretations, and accepted knowledge is therefore worth preserving. Explicit abstention is also appropriate when evidence is missing, ambiguous, or outside the authorized corpus.

The goal of combining definitions, figures, tables, and relationships remains sound. The system already retrieves meaningful evidence units rather than relying exclusively on arbitrary text chunks. A move marketed as “chunkless” is not automatically an architectural improvement.

### Change the immediate engineering priority

The next milestone should prove that the user-facing application produces supported answers through the same path that is evaluated. Adding another retrieval lane before resolving this gap would increase the number of components without establishing that the delivered system is more reliable.

The required sequence is:

1. Establish correct evidence identity and provenance.
2. Make the user workflow and evaluator exercise the same execution path.
3. Strengthen evaluation and establish an honest baseline.
4. Separate retrieval failure from reader failure.
5. Add or replace components only against a demonstrated failure class.

## Observed findings and implications

### The demo and Gate 6 engine do not share the evaluated query path

`R\src\web.py:1855` invokes `src.query.run_query`. The v1 path uses terminology, hybrid retrieval, and LightRAG; v2 uses `EvidenceStore` and `read_packet` in `R\src\query.py:233`. Neither invokes `answer_whole_standard_question`.

**Implication:** a passing whole-standard benchmark does not certify demo behavior. A shared evidence-packet contract is necessary, but acceptance must also exercise the actual application entry point and routing behavior.

### Passing status does not establish correct provenance

The review found page mapping errors and citation metadata rules that can manufacture or overwrite locators. Relevant locations include `R\src\evidence_phase4_bakeoff.py:50`, `:3478`, `:3569`, and `:3678`.

Specific examples observed:

- Figure A4 response: printed page 78 and PDF locator 90; the source was printed page 77 and PDF index 89.
- Figure A6 response: printed page 80 and PDF locator 92; the source was printed page 79 and PDF index 91.
- A B53 upslope answer used a B53 crop but the locator `figure_b49:interval:upslope`.
- A Table A3/GTAW response had different page identities in its answer body and top-level metadata.

The physical PDF hash matched `goal.md`. Inspection found A2 and A3 sharing PDF index 88, followed by A4, A5, and A6 at indices 89, 90, and 91. PDF indices must be explicitly distinguished from human-facing page numbers in the repaired contract.

**Implication:** citation accuracy is a release property, not a cosmetic presentation issue. A correct answer with a wrong source can mislead an engineering user.

### The benchmark does not establish twenty model replays

The current tests expect zero model replays, six synthetic fixtures, and fourteen deterministic fallbacks in the fixture-enabled configuration (`R\tests\test_gate_6_4_comprehensive_enhancements.py:149`). The fixtures are separately quarantined.

The bounded diagnostic produced:

| Mode | Passing cases | Model replays | Synthetic fixtures | Deterministic answers |
| --- | ---: | ---: | ---: | ---: |
| Deterministic | 20/20 | 0 | 0 | 20 |
| Replay enabled | 20/20 | 0 | 0 | 20 |
| Replay plus fixtures | 20/20 | 0 | 6 | 14 |

**Implication:** these results may demonstrate deterministic regression behavior under the existing evaluator. They do not demonstrate live DeepSeek performance or generalization to unseen questions.

### The acceptance card has drifted from the checkout

Of 51 artifact hashes listed in the Gate 6.4 card, the review found 3 matching current files, 37 differing, and 11 paths absent. Some absences reflect intentional fixture reclassification, so this establishes a stale acceptance record rather than proving data corruption.

The card also associates `G63-BLIND01` with an FCAW-G-SA question, while the current question and result files use that ID for “What is acetylene feather?”

**Implication:** reissue acceptance evidence from the actual frozen checkout. Do not repair the narrative alone while leaving ambiguous artifact identities or question mappings.

### The evaluator is weaker than the product claim

`R\eval\run_phase6_3_blind_hardening.py:127` primarily checks status, required or forbidden substrings, and a crop flag. Those checks do not independently validate every claim, coordinate, or crop's meaning.

**Implication:** a passing score can coexist with unsupported claims or incorrect citations. Also retain the earlier holdout limitation: revising the rubric for already-used questions does not create a fresh unseen test set.

## Navy Weld bakeoff relevance

The likely intended `bakeoff.md` was located at:

```text
C:\Users\kenai\Documents\Codex\2026-10-01\task\successor\docs\archive\research\METATHEOREM_BAKEOFF_MASTER_PLAN.md
```

Line 3 identifies its original filename as `bakeoff.md`. It is an unversioned, 26-comparison research plan. Its inspected SHA-256 is:

```text
6F7BF07847330E7552C9D6BDD6C97A0B61C732C9CC43635F392FBD4A8455293F
```

The V0_2 documentation rebaseline treats it as historical and future research reference, not a current architecture mandate.

| Bakeoff candidate | Recommendation | Decision it should answer |
| --- | --- | --- |
| #16 Reader qualification, lines 828–864 | First experiment | Can the reader answer correctly when supplied the correct source region? |
| #8 ColPali/ColQwen visual retrieval, lines 511–552 | Bounded addition after baseline repair | Does page-image retrieval recover evidence that current retrieval misses? |
| #7 Source-native hierarchy, lines 479–507 | Small targeted comparison | Does hierarchy improve navigation and evidence assembly across sections? |
| #3 OCR/VLM comparison, lines 324–352 | Only for demonstrated extraction failures | Which extractor preserves required labels, text, layout, and associations? |
| #9 RAG-Anything | Defer | Is corpus-wide discovery demonstrably inadequate after simpler repairs? |
| #11–15 MAGE | Defer | Is adaptive retrieval or routing the measured bottleneck? |

Historical Navy Weld evidence argues for caution:

- The extraction closeout recommends `BAKEOFF_PARTIAL__MORE_EVIDENCE_REQUIRED` and preserving A0.
- The local retrospective records 27 of 35 reader cases failing after correct retrieval.
- Equal-weight fusion produced 4 rescues versus 8 harms.
- Historical MAGE scores were invalidated by scorer defects.

These are historical results from their particular evaluations. They are not current AWS performance estimates or proof that any candidate will fail here. They do show why retrieval success, answer correctness, and evaluator validity must be measured separately.

Sources:

- `C:\Users\kenai\Documents\Codex\2026-09-30\navy-annexb-wave1-bakeoff-closeout-v0_1\status\EXTRACTION_BAKEOFF_RESULTS.md:3`
- `R\docs\navy_weld_multimodal_lessons_learned.md:49`, `:57`, and `:69`

## Visual RAG and chunkless OCR are different choices

**Visual page retrieval** embeds page images and retrieves relevant pages or regions. ColPali and ColQwen are candidates for finding diagrams, tables, or visually expressed relationships that text retrieval misses. A separate reader still has to interpret the evidence. Similarity heatmaps are not verified citations.

**Hierarchy-guided retrieval** navigates a document tree rather than relying on conventional vector chunks. PageIndex is an example. It still selects evidence; “chunkless” does not mean all source content is considered on every query. Its value for an alphabetical terminology standard must be tested, not assumed from results on other document types.

**OCR and structured parsing** recover text and document structure. They are ingestion choices, not substitutes for retrieval or answer validation. The sampled A3.0 figure pages contain native text and vector paths, so wholesale OCR replacement is especially difficult to justify. OCR may recover labels without correctly representing arrows, branches, spatial relationships, or normative meaning.

Recommended policy: preserve original pages and usable native text, apply OCR selectively, and retain explicit source bindings through every transformation.

## Proposed implementation sequence and exit criteria

All criteria below are proposed controls for the next work cards. They have not been executed or accepted by the owner.

### Phase 1 Repair provenance and freeze the baseline

Create one authoritative mapping from evidence identity to document hash, edition, PDF index, printed page label, figure or table identifier, crop coordinates, and supporting content. Remove guessed provenance and keyword-driven citation defaults. Preserve candidate interpretations separately from accepted source facts.

**Exit criteria:**

- Every registered evidence object resolves to an existing source and valid page or region.
- All known A3–A6, B53/B49, and Table A3 discrepancies have explicit regression tests.
- No citation is silently generated from an unsupported default.
- A frozen artifact ledger has zero unexplained missing files or hash mismatches; intentional relocations are explicitly recorded.
- Commit, working-tree state, corpus hashes, configuration, and execution modes are recorded together.

### Phase 2 Validate the delivered query path

Make the UI, CLI, and evaluator consume the same evidence-packet schema and intended engine. Retain adapters only where their differences are explicit and tested.

**Exit criteria:**

- The acceptance suite calls the same application route used by the demo.
- Identical queries under identical configuration produce consistent evidence identities and provenance across entry points.
- Live calls, cached model replays, synthetic fixtures, and deterministic answers are separately identified and reported.
- Synthetic success cannot count as live-model acceptance.

### Phase 3 Establish independent evaluation

Freeze development and held-out sets before tuning. Include exact terminology, nonstandard term mappings, multi-part questions, figures, tables, cross-page evidence, qualifiers, negation, unsupported questions, and edition-sensitive distractors. Do not reuse an exposed benchmark under a new rubric and call it unseen.

**Exit criteria:**

- Every evaluated subquestion has an explicit expected evidence set or an explicit unanswerable disposition.
- Report answer correctness, complete evidence-set recall, citation support, citation completeness, and abstention separately.
- Deliberately wrong page references, irrelevant crops, omitted qualifiers, and plausible unsupported answers fail evaluator tests.
- All discovered provenance errors are treated as failures regardless of answer wording.
- Human adjudication resolves substantive disagreements; headline accuracy includes denominators and execution modes.

### Phase 4 Qualify the reader with gold evidence

Supply verified source pages or crops directly. Hold the question, answering model, prompt, and evidence budget constant when comparing readers. Categorize errors as extraction, interpretation, evidence binding, synthesis, or abstention failures.

**Exit criteria:**

- Publish the reader's result for every case, not only an aggregate score.
- Separate gold-evidence performance from retrieved-evidence performance.
- Identify the dominant failure classes before selecting the next component to change.
- Do not claim a retrieval upgrade solves a case the reader fails with correct evidence.

### Phase 5 Run a bounded visual retrieval comparison

Compare the repaired baseline, a pinned ColPali or ColQwen model, and a hybrid on the same frozen corpus and held-out questions. Focus on demonstrated misses, while preserving a representative regression set. Keep the reader and evidence budget constant; also report equal-cost results where feasible.

**Proposed promotion criteria:**

- Demonstrable improvement in evidence recall and supported answer correctness on the target failure class.
- Zero newly introduced critical terminology, qualifier, unit, edition, or provenance errors in the adjudicated release set.
- Rescues and harms reported case by case; an aggregate improvement cannot conceal critical regressions.
- Latency, memory, index size, and cost fall within owner-approved limits established before the run.
- Model revision, processor, library versions, image resolution, prompts, and fusion settings are reproducible.

Numerical performance thresholds and the minimum meaningful gain should be selected after the repaired baseline is measured and before examining held-out candidate results. A small pilot can guide selection but cannot establish broad production reliability.

## Safe parallel work

After the baseline snapshot and evidence contract are fixed, two bounded workstreams can proceed in separate worktrees:

- **Core integrity:** provenance repair, shared query path, artifact reconciliation, and evaluator hardening.
- **Experimental comparison:** frozen corpus adapters and visual-reader/retrieval experiments that consume the agreed evidence contract.

Use separate branches, virtual environments, output directories, and experiment manifests. Treat shared source evidence as read-only. Do not let both workstreams write the same stores, regenerate the same baseline artifacts, or change acceptance questions. A separate clone is usually unnecessary unless storage or tool behavior makes worktree isolation insufficient.

Experimental results should not be merged into the accepted graph or production route until the integrity work and independent evaluation are complete. This parallel plan is a recommendation, not execution authorization.

## Decision triggers for a future pivot

- If correct evidence cannot be retrieved reliably but the reader succeeds with gold evidence, prioritize retrieval changes.
- If the reader fails on gold evidence, prioritize reader selection, evidence presentation, or structured interpretation.
- If native extraction loses required content, run the targeted OCR/parser comparison.
- If cross-section navigation is the measured problem, compare source-native hierarchy.
- If corpus-wide discovery or adaptive routing remains the bottleneck after these controls, revisit RAG-Anything or MAGE with a narrow hypothesis.
- If the current storage cannot satisfy measured access or scale requirements, evaluate a database change separately from the answer-quality problem.

**Recommended owner decision:** authorize a provenance and end-to-end validation milestone, followed by reader qualification and a bounded visual-retrieval bakeoff. Defer whole-stack migration and corpus-wide OCR conversion until a specific measured limitation warrants them.

## External technical references

These sources describe candidate capabilities, not measured performance on this AWS corpus.

- [ColPali paper](https://arxiv.org/abs/2407.01449): image-based document retrieval with late interaction.
- [ColQwen2.5 v0.2 model card](https://huggingface.co/vidore/colqwen2.5-v0.2): model configuration, resolution trade-offs, and version-sensitive query formatting. Review both adapter and backbone license terms before adoption; do not describe the entire stack as MIT based only on the adapters.
- [PageIndex repository](https://github.com/VectifyAI/PageIndex): hierarchy-guided retrieval candidate.
- [Docling document representation](https://docling-project.github.io/docling/concepts/docling_document/): structured text, tables, pictures, hierarchy, and provenance.
- [DeepSeek OCR 2 repository](https://github.com/deepseek-ai/DeepSeek-OCR-2): optional targeted extraction comparison, not a complete retrieval architecture.
- [ViDoRe v3 paper](https://arxiv.org/abs/2601.08620): evaluation dimensions for visual retrieval and fine-grained grounding.

Preserve the project's authorized source edition throughout any comparison. A newer published standard is not permission to silently change the corpus or mix evidence across editions.
