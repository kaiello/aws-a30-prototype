# Navy Weld value and outcomes assessment

## Purpose and conclusion

Prepared 13 October 2026 for project review. This assessment explains what is valuable in Navy Weld's existing work, what useful results could follow from it, and what would have to be demonstrated before those results could be claimed. It complements the [framework roadmap](navy_weld_framework_roadmap.md) and [multimodal lessons learned](navy_weld_multimodal_lessons_learned.md), which contain the detailed candidate catalog and experimental history.

Navy Weld has created a useful foundation for an evidence-centered welding information system. Its strongest assets are the connection between claims and inspectable source material, the beginnings of a welding semantic model, concrete multimodal experiments, reusable questions and failure cases, and increasingly explicit preservation and reproducibility records. Together, these make it possible to judge a future system by whether it gives a faithful, reviewable answer, rather than by whether it produces plausible prose.

The most valuable next result would be a small, usable AWS A3.0 demonstrator with exact evidence and honest limits. A reusable evidence and ontology layer, a credible framework comparison, and an engineering case study can then emerge from the same work. A broader release or publication is possible, but depends on new performance evidence, reproducibility, and permission to distribute the relevant sources, derived assets, and software.

The recommended investment is to make the existing work easier to use and verify. Preserve distinctive evidence and semantics; use frameworks where they remove ordinary plumbing; repair demonstrated gaps; and retire duplicated implementations only after a replacement has proved itself. Past effort is not a reason to keep every component active.

**Evidence language.** “Recorded evidence” means a dated project receipt or review supports the statement; this assessment did not rerun the experiments. “Interpretation” identifies the value reasonably suggested by that evidence. “Potential outcome” describes something the project could produce but has not yet established. Suggested acceptance measures are proposals, not newly adopted release gates.

## 1 Current position and the owner directed sequence

The roadmap and lessons documents were published through [pull request 6](https://github.com/kaiello/navy-weld/pull/6), with the supplied publication handoff identifying `main` at `1f4e2c7674b815759541dd0657838dc9e5ca8e8c`. This is a dated reference, not a claim about where a moving branch will remain.

The latest migration handoff reports that 13 new Git-root discovery checks passed and four Gitlink parent correspondences were resolved. These are meaningful gains in understanding the preserved repository structure. The native business run has not started, and the real profile, resource, and input bindings remain unresolved. Repository discovery does not establish functional reproduction.

The preservation evidence also has distinct populations: the accepted four-part backup/restore record covers a 14.058 GB, 274,129-file backup inventory, with declared control-related differences in restored byte counts. A separate, independently accepted preservation copy covers 42.34 GB, 339,766 files, and 152 roots. The 33 revision-tree inventories and 87 Fresh 9 files are additional scoped evidence. They must not be summed or relabeled as one homogeneous backup or semantic-validation result. [Coordination receipts](https://chatgpt.com/c/01a11bc1-eeb3-7260-8ba7-1c1688a46038)

The owner's directed sequence is:

1. Complete the migration first.
2. Establish a usable AWS baseline.
3. Run a bounded RAG-Anything/LightRAG comparison.
4. Repair demonstrated gaps through the relevant A1/A2/A3 work.
5. Establish simple, reproducible operation.
6. Retire duplication after a replacement is proved.

A separate canonical goal update is underway. This assessment reflects that direction without claiming that its stages are complete or that this document replaces the active controls. In particular, the broader candidate inventory in the roadmap is a reference resource. It does not enlarge the immediate comparison into a simultaneous trial of every framework.

## 2 The work that already has lasting value

### Inspectable evidence and provenance

**Recorded evidence.** The project has treated source identity, anchors, reviewed claims, provisional status, and acceptance boundaries as explicit concerns. It has also exposed cases where apparently successful answers or scores lacked adequate support. This is valuable work even where the candidate system failed, because it clarifies what the system must preserve and what a reviewer must be able to inspect.

**Interpretation.** An evidence trail is the basis for trust, debugging, and controlled improvement. When an answer can be traced to the exact source revision and relevant clause, page, figure region, or table cell, a reviewer can distinguish a source problem from an extraction, retrieval, or reasoning problem. Without that trail, changes are difficult to evaluate and errors become arguments about plausibility.

The reusable asset is the combination of evidence identities, location mappings, review decisions, and tests of their meaning. A citation string by itself has little value if it does not resolve, points to the wrong revision, or supports only part of the claim. Likewise, a preserved page image is useful only when the system can connect the question and answer to the relevant region and context.

**Potential outcome.** This work can become a framework-independent evidence package: a small set of canonical records and adapters that retains source revisions, exact locations, raw and normalized content, transformation lineage, and review status. A future framework would consume or map to that package rather than becoming the only place the evidence's meaning exists.

### A welding semantic foundation

**Recorded evidence.** The recorded accepted A2/A3 overlay contains 8 nodes and 4 edges. The review inventory contains 19 reviewed claims and 3 provisional typed assertions; that inventory does not automatically admit every item into the runtime evidence set. These are bounded starting points, not proof of a complete welding ontology or broad question coverage.

**Interpretation.** The important work is the distinction between a term, a relation, the evidence asserting it, and the conditions under which it applies. Units, comparators, exceptions, negation, footnotes, and revision precedence can determine whether an answer remains faithful to its source. A generic text summary or generated graph can discard these distinctions while appearing coherent.

A small, carefully grounded semantic foundation can therefore be more useful than a much larger automatically generated graph. It can constrain extraction, improve query interpretation, assemble related evidence, and reveal when two statements should not be merged. It can also help maintain stable concept identities when the retrieval framework changes.

**Potential outcome.** The project could produce a compact welding evidence model with a documented vocabulary, allowed relationships, qualifying conditions, provenance, and explicit asserted-versus-derived status. Expansion should follow real questions. It need not attempt to encode the entire domain before supporting a useful AWS demonstrator.

### Experiments that identify where multimodal systems fail

The experimental record has value because it narrows several tempting but unsupported explanations. It shows why retrieval, reading, evidence assembly, and scoring must be measured separately.

| Recorded experiment | Scoped finding | Value for the next decision |
|---|---|---|
| MIL-STD-1689A Figures 1–5 parser/OCR development trial | Native support 0.5333, Docling support 0.3333, OCR support 0.7667 under that narrow comparison | Preserve a strong native/OCR reference; do not assume a newer parser wins every source type |
| Corrected MIL-STD Figures 1–33 fusion review | Reported fused R@3/R@5 of 1.0, with 4 rescues and 8 harms; fusion classified harmful | Inspect rank displacement and answer-level effects rather than adding routes indiscriminately |
| Reader review associated with the corrected visual work | 27 of 35 reader cases failed after correct retrieval; the reviewed 3B, 7B, and 8B readers scored 39/74, 41/74, and 42/74 | Larger readers did not meet the material-gain criterion; isolate reading and evidence presentation before scaling capacity |
| AWS Annex A development integration | 619 persisted MiniLM text vectors and six ColPali A1–A6 crops were reported integrated and live | Retain the scoped substrate and question evidence as a baseline asset; this is not production or whole-corpus acceptance |

Sources: [parser and OCR review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=06286b13-a355-408f-8888-1344cd3fed56), [corrected retrieval and reader review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=cc387d80-e496-4fc4-b640-487515ccd055), [AWS Annex A report](https://chatgpt.com/c/6ab2874a-ca9c-83ea-a7eb-959b76dbd0d1?messageId=d976f6bc-285c-47da-9e73-139620c0bf0c)

These metrics are reproduced as reported. The fusion denominator must not be inferred from the separately reported 104-question inventory or combined with the reader populations. MIL-STD experiments do not establish AWS performance, and neither source population is interchangeable with legacy 9 or Fresh 9.

**Interpretation.** The larger-reader result is a useful limit on one investigated remedy. It does not establish that all larger models are ineffective. The fusion result likewise says that a particular composition harmed the declared comparison; it does not reject multimodal retrieval as a whole. These distinctions let the project pursue targeted fixes instead of repeating broad model shopping.

### A reusable question and failure suite

**Recorded evidence.** The historical FULL 95/2,285 record is separate from the AWS baseline of 6/6 questions, 7/7 parts, and 213 controls. These figures retain their original scopes and cannot be promoted into a new whole-corpus semantic-accuracy claim. The project also has concrete counterexamples showing how an evaluator can miss unsupported or incomplete prose.

The C1/C2 MAGE comparison was invalidated when its scorer accepted PASS plus any evidence identifier and counted 15 C1 and 11 C2 wrong or incomplete answers as passes. The later C1R review also exposed unsupported prose passing checks. MAGE's incremental value remains inconclusive. The useful surviving assets are the counterexamples, traces, questions, and corrected understanding of the evaluation problem, rather than the invalidated scores. [C1/C2 review](https://chatgpt.com/c/6ab6cd66-dbc4-83ea-aa6c-e46ba398ef93?messageId=01dc2fb3-8401-483d-bd4a-72dc393e719d), [C1R review](https://chatgpt.com/c/6ab82ed2-6f78-83ea-a62f-8f1154acd455?messageId=f08c584c-9ae4-4954-a96e-57ca5649c0eb)

**Potential outcome.** A curated regression suite can test answerable questions, incomplete evidence, wrong revisions, missing qualifiers, incorrect units, misleading citations, and truthful abstention. This is a transferable asset: the same questions and evidence can qualify a parser, a framework, a reader, or a future release. It also makes failed experiments productive by converting the failure into a test the next system must face.

### Preservation and reproducibility knowledge

**Recorded evidence.** The migration work has surfaced encoding, symlink, hidden-support-file, repository-discovery, and resource-binding issues. A CP437 investigation validated decoding and byte-for-byte re-encoding of 152 unchanged logs. The reported recovery of 1,183 directory symlinks after Windows error 1314 used a bounded route without changing security settings. These are scoped operational results. The remaining native-run and binding gaps still matter.

**Interpretation.** The project has learned how easily preserved bytes, discoverable repositories, and executable workflows can diverge. That experience is reusable when defining manifests, environment prerequisites, safe diagnostic reports, and second-operator reproduction. It also supports a clear boundary: retaining a historical experiment does not require making it part of the next product.

The value will be realized when these lessons produce a simpler operating procedure. An extensive archive is useful insurance and research context, but it becomes an engineering asset when someone can identify the supported entry point, required inputs, exact versions, and expected result without reconstructing the entire history.

## 3 Concrete outcomes that should come from the work

### A usable AWS demonstrator

**Recommended first outcome.** Provide a narrow workflow in which a user asks a real AWS A3.0 question, receives an answer scoped to the authorized source revision, and can inspect the evidence for each material claim. Include the modalities actually required by the chosen questions. If the selected slice lacks visual or tabular evidence, do not call that slice a demonstrated multimodal capability.

The demonstrator should handle ordinary supported questions as well as ambiguity, missing evidence, and source conflict. Its value is the ability to find and review relevant information with less manual searching, while preserving the conditions that make the answer correct. It should support evidence navigation and analysis; it should not imply independent engineering approval, weld certification, or compliance determination.

The smallest useful interface may be a simple query and evidence view. A broad interface redesign, autonomous agents, or a large graph is unnecessary unless a measured user need requires it. Test whether the workflow is usable by asking a reviewer to complete defined tasks and inspect the cited sources, rather than judging screenshots alone.

### A reusable evidence and ontology layer

**Recommended companion outcome.** Package the distinctive semantics and provenance so they survive a framework change. The package should cover stable source and evidence IDs, revisions, anchors, domain concepts, relationships, qualifying conditions, review status, and export mappings. Original evidence should remain distinguishable from generated interpretations.

This layer could support several future retrieval implementations without duplicating the domain work. Its usefulness should be proved by a small round trip into and out of a selected framework: can the project recover the same identities, source locations, qualifiers, and statuses, and still answer the baseline questions?

The package should remain modest. It is not a mandate for a universal graph platform or a new abstraction around every component. A few explicit schemas, manifests, resolvers, and tests may be sufficient. The measure of success is continuity of evidence and reduced coupling.

### A decision quality framework benchmark

**Owner-directed next comparison.** After the usable AWS baseline exists, compare a bounded RAG-Anything/LightRAG path against it. The comparison should determine whether the framework improves the supported workflow or removes enough custom work to justify adoption. It should not be designed to guarantee that the challenger wins.

Use the same corpus and revision, reviewed questions, evidence requirements, and declared budgets. Preserve a held-out set. Report parsing and retrieval failures separately from reader and citation failures, then report the composed answer result. Record installation, adapter, update, debugging, and recovery effort alongside latency and resource use.

The result could be full adoption for the narrow product, partial adoption of useful components, retention of the existing baseline, or an inconclusive finding with one bounded unresolved question. Each is valuable if it supports a clear decision. The wider OSS inventory, including Utopia, Docling Graph, KAPipe, RAGFlow, and other options, remains available for demonstrated gaps; it need not be activated now.

### A credible engineering case study

**Potential outcome.** The project could document how evidence-grounded multimodal systems fail and how to improve them without conflating transport, parsing, retrieval, reading, scoring, and operation. Its distinctive material includes harmful fusion, limited gains from larger readers in the tested setting, scorer invalidation, the difference between extracted geometry and semantic relations, and preservation-versus-reproduction problems.

A good case study would reconstruct the decisions using artifacts: the hypothesis, source scope, baseline, controlled change, result, counterexample, and subsequent decision. It would also account for effort, including coordination and repeated checking, rather than presenting only model metrics.

This could be useful internally before any public release. Public claims would require careful replication, explicit limitations, appropriate source and software permissions, and separation of original results from later interpretations. The evidence does not establish a specific “context rot” cause, a universal failure of larger models, or general superiority of a particular architecture.

### A controlled release or publication package

**Conditional outcome.** A release could combine the supported demonstrator, a small evidence contract, an evaluation harness, reproducibility instructions, and source-safe examples. A publication could explain the methods and scoped findings. These should follow evidence and permission checks rather than become new prerequisites for finishing the useful internal baseline.

Before distribution, review ownership and licenses for source documents, images and crops, derived datasets, model weights, framework code, and bundled components. Permission to preserve or privately use material does not automatically permit redistribution. Synthetic examples can support public documentation, but must be labeled and cannot stand in for measured performance on the protected corpus.

No public release, external source upload, paid deployment, or expansion of access is authorized by this assessment. Preparing a review document and committing it to the approved repository is separate from those later actions.

## 4 What to retain simplify and retire

### Retain as active foundations

Retain source and revision identities, accepted evidence and its anchors, qualifying conditions, the reviewed semantic model, useful baseline retrieval artifacts, real questions, failure examples, and acceptance decisions. Keep raw extraction alongside normalized representations where the difference matters. Preserve the separation between extracted, inferred, reviewed, provisional, and accepted claims.

Also retain historical artifacts needed to understand or reproduce an important result, including invalidated experiments. Their status should be obvious. A failed run can be an excellent regression asset without remaining an active runtime dependency.

### Simplify the supported path

Choose one supported AWS entry point, one current run manifest, one evaluation contract, and one primary route for ordinary ingestion and retrieval. Use the selected framework for commodity work when it can satisfy the evidence requirements. Keep custom code focused on the source and domain distinctions that actually need it.

Keep project documentation and runtime state in their proper roles. Git should hold versioned definitions, manifests, and decisions. Human-facing review pages should summarize and link to those definitions. Runtime indexes and caches should have explicit rebuild and retention rules. Avoid three independently edited descriptions of the same accepted state.

Simplify handoffs around a target, current revision, authorized scope, unresolved blocker, expected artifact, and verification rule. A new check should establish a named claim. Reuse valid evidence when the inputs and relevant conditions have not changed.

### Retire only after proving replacement

Candidates for eventual retirement include duplicate orchestration, redundant indexes, unused adapters, stale experimental entry points, and competing copies of current status. Retirement should follow demonstrated replacement and a recoverable archive or approved deletion process. It should not discard the evidence needed to interpret old results.

The historical 26-option portfolio should remain a research reference, not a backlog of mandatory implementation tasks. Unavailable or inconclusive candidates can remain deferred. The project does not gain value from keeping every model, graph engine, or agent workflow installed.

The active preservation commitment remains intact. Future runtime eligibility and historical preservation are different decisions. If an agreed migration criterion needs to change, the change requires an explicit owner decision rather than being inferred from a simplification proposal.

## 5 Measures that would demonstrate realized value

The project should approve concrete thresholds before the relevant runs. The measures below make outcomes inspectable without inventing an accuracy target unsupported by the current evidence.

| Outcome | Evidence to collect | Proposed acceptance meaning |
|---|---|---|
| Usable AWS demonstrator | Held-out answers, claim-level review, source-opening checks, task completion observations | Material claims are supported; revisions and qualifiers are correct; unsupported questions receive appropriate limits or abstention |
| Reusable evidence layer | Export/import comparison of IDs, anchors, qualifiers, and statuses | All required fields in the declared test set survive; any unsupported mapping is explicit and blocks the affected use |
| Framework decision | Baseline/challenger results, failure breakdown, effort and resource measurements | A documented decision explains quality and maintenance tradeoffs; adoption is not assumed |
| Reproducible operation | A second operator's run from the pinned manifest, update and recovery exercises | The supported path works without reconstructing undocumented state or relying on the original implementer's memory |
| Simpler engineering | Active dependency and adapter inventory, operator steps, diagnosis time, duplicate paths removed | Less work is needed to operate the supported scope, without loss of accepted evidence or regression coverage |
| Release or publication | Replication package, claim review, license and source-permission inventory | Every distributed asset and public claim has an appropriate evidence and permission basis |

For answer evaluation, track complete supporting-evidence recall, material-claim support, citation validity, qualifier and unit preservation, revision isolation, unsupported answering, and unnecessary abstention. Report results by question family and source population. A single aggregate score can conceal a serious integrity failure.

For practical value, record reviewer task time and rework against a manual or existing baseline, with a clearly described task set. Do not claim time savings or economic return until observed. For cost, separate ingestion, reindexing, storage, model use, serving, and human operation. A framework's license price alone does not determine its cost.

No known unresolved critical evidence error should be hidden inside an average. Conversely, zero observed errors in a small slice does not prove a low population error rate. Report the sample, adverse cases, uncertainty, and supported scope. These measures are intended to support honest release decisions rather than manufacture a headline.

## 6 A short prioritized path to those outcomes

**First, close the migration on its agreed terms.** Use the passed Git-root checks and resolved Gitlink correspondences as completed evidence. Focus remaining work on the real profile/resource/input bindings and the required native run or other agreed closure evidence. Do not restart settled checks without a relevant change.

**Second, make the AWS baseline usable.** Select a small question slice from the authorized AWS material, preserve exact evidence, and run it through one supported entry point. Include negative and qualifier-sensitive cases. Keep legacy 9, Fresh 9, and MIL-STD findings as separate reference evidence.

**Third, compare RAG-Anything/LightRAG within a fixed budget.** Freeze the slice and the evaluation rules, validate the scorer, and allow only a declared tuning round before held-out review. Produce a decision, not an open-ended technology survey.

**Fourth, repair the leading demonstrated gap.** Expand semantic coverage through the A1→A2→A3 sequence according to the questions the usable baseline cannot yet answer. Preserve source identity, qualifiers, and evidence anchors, and subject each addition to ordinary independent admission and answer review. Test the expanded coverage against the baseline and the targeted failure cases. This semantic sequence does not reactivate the historical parser bakeoff arms.

**Fifth, prove simple operation.** Have another operator reproduce the run, ingest an approved update, inspect a failed answer, and perform the relevant recovery. Measure actual effort and resource use. Keep the operating guide short enough to follow.

**Finally, remove proven duplication and package the result.** Retain historical evidence, retire replaced active paths through the approved process, and prepare the internal demonstrator and reusable evaluation package. Consider broader release or publication only after evidence and source permissions support it.

## 7 Overall assessment

Navy Weld's work has value beyond any single parser, reader, or framework. It has produced a clearer definition of faithful multimodal answering, scoped evidence about several failure modes, and the beginnings of reusable domain and evaluation assets. Its value is strongest where the project can show the source, the claim, the qualifying context, the test, and the decision together.

The remaining opportunity is to turn that accumulated knowledge into a smaller supported system. A usable AWS demonstrator would make the work tangible. A portable evidence layer would preserve its distinctive content. A bounded framework comparison would reduce uncertainty about implementation. Reproducible operation would make the result sustainable.

None of those outcomes is established merely by the current archive or review counts. They are achievable directions whose evidence requirements can now be stated much more clearly. The next phase should use that clarity to finish a useful path and reduce unnecessary work.

## Source and status notes

This assessment synthesizes the published roadmap and lessons learned, the linked historical owner reviews, and the migration and owner-direction handoff current at preparation time. Private conversation links may require the owner's account. No experiment, native business run, source upload, or framework adoption was performed for this document.

The existing reviews provide the full historical and candidate references. This document deliberately avoids importing all of their details or treating their broader proposals as the current execution sequence. It contains no licensed source excerpts, secrets, raw private identifiers, or private machine paths. Publication to the approved review location does not itself change active execution controls or authorize public distribution.
