# Figure A1 bounded backend bakeoff: safe aggregate results

**Status: BOUNDED_BAKEOFF_FINISHED_WITH_EXPLICIT_BLOCKED_CANDIDATES_NO_ADOPTION.**
This document contains aggregate findings, not source extracts or answer examples.

## Scope and interpretation

- One Figure A1 and the same 31 frozen questions were used throughout.
- Evaluation concerned backend evidence, multihop retrieval, completeness and support; no UI work.
- These exposed development questions are not unseen acceptance or a corpus-wide benchmark.
- The evaluation harness is vendor-neutral and distinct from production orchestration.
- The team reports RapidOCR + Golden Retriever working for specificity, but GR was not run here.
- GR remains an optional adapter, not a tested winner or mandated production foundation.

## Latest independently graded configurations

All model arms used the installed Qwen3-VL 8B model, temperature 0 and seed 42.
Initial reader context was **16,384**; final MMGraph context was **32,768**.
The larger context and different request counts confound attribution to frameworks alone.

| Configuration | PASS | PARTIAL | FAIL | UNASSESSED | Calls shown |
|---|---:|---:|---:|---:|---:|
| C03 existing deterministic A1 reference | 31 | 0 | 0 | 0 | 0 |
| C01 complete image + native-text control | 21 | 5 | 5 | 0 | 31 |
| B06 LlamaIndex routing/retrieval component | 18 | 3 | 10 | 0 | 62 |
| S01 Haystack native-text RAG, corrected overlay | 13 | 5 | 13 | 0 | 32 |
| S02 PageIndex local text/tree component | 11 | 6 | 14 | 0 | 76 |
| B02 MMGraphRAG final 32k run | 11 | 4 | 16 | 0 | 92 |

The latest overlay contains **186 graded slots = 31 questions x six configurations**.
The original five-configuration **155 slots** and all initial raw results are preserved.
Haystack's one-row correction replaces its earlier unassessed result; it adds no question slot.
MMGraph's earlier three index calls and LightRAG's 15 calls are additional to the table.
Total generation calls are **311**; **24 historical calls remain separate**.
ColQwen's one image and 31 query embedding passes are separate from generation counts.

## Capacity corrections and remaining evidence failures

- Initial reader output quota was 2,048; the original LightRAG index quota was 4,096.
- Approved corrections used native `num_predict=-1`, with disclosed context/transport guards.
- Haystack's exact-request replay stopped naturally after 448 generated tokens.
- Its capacity issue resolved, but grading remained FAIL: 10/11 pairs, one omission,
  wrong-family extras and a support error. Its original 13/5/12/1 aggregate is preserved.
- MMGraph's 16k correction exhausted the chosen window, not the model-declared maximum.
- At 32k, MMGraph completed all 31 questions with 7 index and 85 query calls.
- All 92 final-run calls stopped naturally without errors, context shifts or output-cap stops.
- Eighteen questions actually sent A1 pixels to a VLM; thirteen used a text-only graph route.
- Its index audit found 104 nodes/108 edges and 90 codes, but only three exact name nodes
  and misaligned edge context. Natural completion does not establish semantic index validity.
- PageIndex retrieved the native page for every answer, but lost geometry/name-code pairing.
  This was local text extraction, not an OCR experiment; retrieval presence is not support.
- Two whole-image PARTIAL grades retain a frozen rubric requirement not asked explicitly.

## Purpose groups for the same questions

Regrouping changed reporting only, not the questions, gold, execution input or rubric.

| Primary purpose | Questions | MMGraph PASS / PARTIAL / FAIL |
|---|---:|---:|
| Simple lookup / control | 7 | 4 / 0 / 3 |
| Enumeration | 8 | 2 / 2 / 4 |
| Multi-entity / multi-intent | 5 | 5 / 0 / 0 |
| Hierarchy | 7 | 0 / 0 / 7 |
| Source grounding / limits | 4 | 0 / 2 / 2 |

## Complete candidate coverage

A setup hold or index failure is not a failed answer grade or a successful QA test.

| Candidate | Bounded outcome |
|---|---|
| B01 [LightRAG](https://pypi.org/project/lightrag-hku/1.5.7/) / RAG-Anything variant | Both extraction variants failed before graph/QA; 0/31 each, null grades |
| B02 [MMGraphRAG](https://github.com/wanxueyao/MMGraphRAG) | 31/31 final answers graded at 32k; earlier capped runs retained |
| B03 [MegaRAG](https://github.com/AI-Application-and-Integration-Lab/MegaRAG) | Blocked: custom-license and local-setup decision |
| B04 [RAGFlow](https://github.com/infiniflow/ragflow/releases/tag/v1.0.0-rc2) | Blocked: major server-deployment decision |
| B05 [WeKnora](https://github.com/Tencent/WeKnora/releases/tag/v0.8.3) | Blocked: build/service requirements |
| B06 [LlamaIndex](https://pypi.org/project/llama-index-core/0.14.25/) | Tested routing/retrieval component; not a new production stack |
| B07 [Neo4j GraphRAG](https://github.com/neo4j/neo4j-graphrag-python) | Blocked: no verified authorized database instance |
| B08 [Docling/LI/Neo4j combination](https://github.com/docling-project/docling-graph) | Full combination blocked by database/setup requirements |
| B09 [ColQwen](https://huggingface.co/vidore/colqwen2.5-v0.2) + LightRAG | Visual component completed; both full-QA variants blocked by index failure |
| S01 [Haystack](https://pypi.org/project/haystack-ai/3.4.1/) | Tested native-text RAG control, including one capacity correction |
| S02 [PageIndex](https://pypi.org/project/pageindex/0.4.4/) | Tested local text/tree component with native tools |

C02 native-text control is the same S01 arm and is not double-counted.
LightRAG history totals 15 calls: original four, earlier JSON three, then eight cap-correction calls.
The final eight comprised six natural stops and two client repetition stops; both variants failed pre-graph.
The formerly capped chunk completed naturally at 4,540 tokens; later repetition still prevented QA.
No layout-repair pipeline was executed or scored. Shared B01/B09 calls are counted once.
A single known image ranking first cannot establish corpus-level visual retrieval recall.

## Recommendation and next boundary

Retain the existing A1 reference plus the whole-image control; **no production adoption**.
MMGraph's 11 PASS versus whole-image 21 PASS is not a universal framework ranking.
Correct evidence must reach the reader; citations, natural stops and node counts alone do not prove support.
A relationship/multihop phase is **planned, not implemented** by this closeout.
Any future competing-figure recall test, integration or implementation needs its own scope.
The frozen questions, gold, private raw traces and original baselines remain unchanged.

## Git closeout and artifact boundary

The owner authorized a local record commit and a focused approved docs-only PR/merge on a new branch.
Experiment code remains an isolated local record; the separate LightRAG worktree remains isolated.
This publication adds no reusable production code, source assets, raw answers, question texts or private IDs.
Earlier no-commit notes describe historical evaluation scopes; active owner authorization governs closeout.
No new inference, tests, source repair, deployment, GR integration or replacement follows from publication.

## Closeout validation

The clean main publication checkout passed 59 selected existing software checks in 1.29 s
using a workspace temporary directory. This is software validation, not semantic grading;
no model inference or new QA was run for Git closeout.
