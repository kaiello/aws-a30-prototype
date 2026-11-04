# AWS A30 Architecture Assessment and Recommendations

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
