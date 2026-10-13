# NavyWeld multimodal RAG lessons learned

## Purpose and main takeaways

Prepared 12 October 2026. Status: retrospective and advisory draft for review. This document summarizes observed project outcomes, explains what they do and do not establish, and proposes practices for future multimodal retrieval-augmented generation work. It does not authorize implementation, a framework adoption, a new paid service, source uploads, or changes to the active migration criteria.

The central lesson is to keep the source-to-answer chain inspectable. A preserved file, a successful model call, a retrieved page, a populated graph, a passing test suite, and a cited answer are different accomplishments. Each can succeed while the next stage fails. The project repeatedly benefited from separating those stages, and repeatedly lost clarity when one kind of evidence was treated as proof of another.

The strongest forward direction is a smaller amount of project-specific code around a reusable framework, with NavyWeld retaining ownership of evidence identity, ontology, qualifiers, revisions, and evaluation. The framework should earn its place by reducing the work needed to deliver a faithful answer and maintain the system. Neither the number of integrations nor the size of a graph is a useful goal by itself.

### Major takeaways

1. Evaluate retrieval and reading independently. Correctly finding the page does not establish that the model understood it.
2. Validate the scorer before trusting the score. The MAGE comparison showed that evidence-ID presence and passing tests can coexist with unsupported answers.
3. Preserve exact evidence and qualifying conditions. Page-level citations and schema-valid objects can still omit the detail that makes a claim true.
4. Compare one decision surface at a time. The earlier 26-option portfolio is a research map, not a requirement to run every option.
5. Treat unavailable candidates as unavailable. Runtime, authorization, and adapter failures do not establish model quality.
6. Reuse frameworks for ordinary plumbing. Retain the small domain and evidence layer that generic systems cannot be assumed to preserve.
7. Separate preservation, reproducibility, answer quality, and operation. The migration and the AWS A3.0 product have related assets but different completion evidence.
8. Match assurance to the stage. A POC needs trustworthy evidence and a bounded conclusion; a production release needs additional operating and security proof.
9. Make handoffs shorter and stronger. A current manifest, exact target, durable artifact, and explicit next decision are more useful than repeated broad reviews.
10. Diagnose the observed failure. Long histories and inconsistent handoffs do not, by themselves, prove “context rot” or a model-capacity problem.

### Evidence labels

**Observed** refers to an outcome reported in the cited owner review or dated project handoff. The work was not independently rerun for this retrospective. **Interpretation** explains a plausible lesson supported by the evidence without claiming unique causality. **Recommended practice** proposes future behavior. **Open question** marks a point the record cannot settle.

The experiments cover different source populations and stages. MIL-STD-1689A Figures 1–5, Figures 1–33, AWS Annex A, AWS Annex B, legacy 9, and Fresh 9 must remain distinct. Results from one are not accuracy estimates for the others.

## 1 Measure the whole path without collapsing its stages

### The stages that need separate evidence

| Stage | Question to answer | Typical false reassurance |
|---|---|---|
| Source preservation | Are the intended bytes, revisions, identities, and required supporting files retained? | A directory exists or a clone completed |
| Parsing | Was the relevant text, layout, table structure, or visual content recovered? | Parser returned valid JSON |
| Canonicalization | Did identity, source location, units, scope, and qualifiers survive? | Schema validation passed |
| Retrieval | Was the complete supporting evidence available within the budget? | A relevant page appeared somewhere in top-k |
| Reading and reasoning | Was that evidence interpreted correctly for the question? | A larger model was used |
| Answer construction | Does every material claim follow from the authorized evidence? | The answer sounds fluent and contains a citation |
| Evaluation | Does the rubric detect the mistakes that matter? | The test suite is green |
| Operation | Can another operator update, debug, and recover the system? | The demo worked once |

The practical benefit of this separation is faster diagnosis. If gold evidence is supplied and the answer is still wrong, another retrieval experiment is unlikely to be the immediate fix. If the answer is correct with gold evidence but the relevant footnote never reaches the reader, the problem is evidence assembly. If a citation points to the wrong revision, the issue may be the identity and filtering contract even when the language model behaved reasonably.

### Observed retrieval and reader separation

In the corrected September MIL-STD Figures 1–33 review, fused retrieval reached R@3 and R@5 of 1.0, yet 27 of 35 reviewed reader cases failed after correct retrieval. The evaluated readers scored 39/74, 41/74, and 42/74 across the reviewed 3B, 7B, and 8B options. The 3B path was retained because the larger readers did not meet the material-gain criterion. These are the recorded review populations; the different denominators should not be silently combined. [Corrected retrieval and reader review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=cc387d80-e496-4fc4-b640-487515ccd055)

**Interpretation.** Reader capacity was not the demonstrated bottleneck fix. The evidence supports investigating how the visual material, crops, labels, relations, and qualifying context were supplied and interpreted. It does not establish that all larger models are ineffective or that retrieval no longer matters on other questions.

**Recommended practice.** Maintain two diagnostic tracks: retrieval against the necessary gold evidence, and a reader test with fixed gold evidence. Then evaluate the composed system. Keep the evidence budget and source coverage constant when comparing readers, and keep the reader constant when comparing retrieval. A full-stack comparison can still be useful, but label it as a full-stack result rather than attributing the gain to one component.

## 2 Fusion can damage a good route

The same corrected review reported equal-weight reciprocal-rank fusion across frozen text, OCR, ColPali, and ColQwen ranks: R@1 0.824324, R@3/R@5 1.0, and MRR 0.903153. The review counted 4 rescues and 8 harms and classified the fusion as harmful. These numbers describe the fused system, not the individual performance of ColPali or ColQwen. They are quoted as reported; their denominator must not be inferred from the separately reported 104-question inventory or combined with the reader populations. [Fusion review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=cc387d80-e496-4fc4-b640-487515ccd055)

**Interpretation.** Adding a useful retrieval channel does not guarantee that a naive fusion rule improves the answer path. A strong aggregate top-k result can hide damage to the first candidate or displacement of the evidence a constrained reader actually sees.

**Recommended practice.** Report wins, losses, and unchanged cases against the reference route. Inspect modality mix, duplicate sources, candidate budgets, and rank displacement. Use source-level deduplication where appropriate and record why a candidate was included. Test a router or scoped fallback only after the failure analysis shows what it needs to fix.

Avoid tuning a fusion weight repeatedly on the final holdout. Use a development set, freeze the rule, and report the held-out behavior. If a new route rescues rare hard cases but harms common ones, consider a conditional route with a broad fallback rather than applying it to every query. That conditional policy still needs its own test for false routing.

## 3 Validate evaluation before making product claims

### The invalidated MAGE comparisons

The September C1/C2 comparison used a scorer that effectively accepted PASS plus the presence of an evidence identifier. The owner review found 15 C1 and 11 C2 wrong or incomplete answers counted as passes. A later C1R review found unsupported prose that still passed its checks. The comparison was invalidated; MAGE's incremental value remained inconclusive, and no approved integration followed from those scores. The separate accepted MiniLM/ColPali substrate was not invalidated by this scorer failure. [C1/C2 review](https://chatgpt.com/c/6ab6cd66-dbc4-83ea-aa6c-e46ba398ef93?messageId=01dc2fb3-8401-483d-bd4a-72dc393e719d), [C1R review](https://chatgpt.com/c/6ab82ed2-6f78-83ea-a62f-8f1154acd455?messageId=f08c584c-9ae4-4954-a96e-57ca5649c0eb)

**Major lesson.** A score can be precisely computed and still measure the wrong thing. Trace presence proves that something was logged. Evidence-ID presence proves that an identifier was included. Neither proves that the answer's material claims are supported.

### Build a small adversarial scorer test set first

A future evaluation harness should deliberately include:

- A correct claim with the correct source and qualifier.
- An incorrect claim carrying a valid but irrelevant evidence ID.
- A partly correct answer that omits the exception or applicability condition.
- A correct value with the wrong unit or comparator.
- A supported statement cited to the wrong revision.
- A fabricated extra sentence appended to an otherwise valid answer.
- A claim whose negation changes its meaning.
- An unanswerable question that receives a plausible guess.
- An answerable question that is unnecessarily refused.
- A citation that names the right page but the wrong table cell or figure panel.

These cases should fail or pass for the intended reason before the main comparison is scored. The cases are not a complete certification suite; they are a safeguard against the most obvious mismatch between rubric and goal.

### Separate structural and semantic checks

Structural checks can verify that IDs resolve, sources belong to the approved corpus, revision filters apply, locations exist, and the output schema is valid. Semantic checks ask whether the evidence supports the claim, whether the claim answers the question, and whether conditions, units, and exceptions are retained.

Use human source review for material semantic judgments, especially on the first small slice. A model judge can triage or provide an independent signal, but it needs calibration against human labels and adversarial cases. Agreement between two model judges is not automatically an independent ground truth.

When a scorer is found defective, quarantine the affected results. Preserve the run artifacts and failure examples, identify which conclusions depended on the scorer, and rerun only what is needed with the corrected rubric. Do not keep the original number in a headline with a footnote that quietly withdraws its meaning.

## 4 Evidence identity is a product requirement

### The minimum useful citation

An answer needs more than a document title. Its material claims should resolve to the source revision and relevant location: section, clause, page, text span, figure region, table row or cell, and associated notes as needed. A parser's element ID is helpful, but it may change after a reparse. Keep a mapping to canonical evidence identities and preserve the transformation lineage.

The project should distinguish the original source, raw extraction, normalized values, inferred relationships, reviewed claims, and accepted evidence. These objects can share provenance without sharing authority. An extracted relation is a candidate; an accepted relation has a separate review status and decision.

### Qualifiers carry meaning

The source's units, ranges, comparators, applicability conditions, exceptions, negation, footnotes, and revision precedence often determine whether an answer is correct. A generic summary can lose these details while retaining the main noun and value. A graph can make the same mistake by turning a conditional relation into an unconditional edge.

Recommended practice is to treat these features as first-class test targets. For a table, test the selected cell together with its headers, units, and footnotes. For a figure, retain the panel, label, legend, and relevant surrounding text. For a definition, preserve referenced conditions and the revision to which it belongs. The retrieval unit may be a complete evidence group rather than a standalone chunk.

### Revisions and corpus isolation

Keep legacy 9 and Fresh 9 separate. Keep MIL-STD visual experiments separate from AWS Annex A and Annex B. A later reindex must not silently replace a citation to one source revision with the most recent text. If an answer uses multiple revisions, state why and how conflicts were handled.

The historical FULL 95/2,285 record, the separate AWS baseline of 6/6 questions, 7/7 parts and 213 controls, and the accepted A2/A3 overlay of 8 nodes and 4 edges have different scopes. The 19 reviewed and 3 provisional claims are a review inventory, not automatic admission of every item. None of these counts establishes new whole-corpus semantic accuracy. These are dated project-handoff facts as of 12 October 2026.

## 5 Geometry and transport are useful evidence with limited meaning

### Native geometry did not imply semantic structure

The September native-geometry extraction produced 33 high-resolution assets, 99 regions, and 1,723 observations from MIL-STD Figures 1–33, but found zero true line/path/curve PDF drawing primitives in the scan-image-plus-text source. No reader calls were made. The later raster-topology comparison on 10 gold figures, 40 nodes, and 30 edges had low node and edge F1 and roughly 90% unsupported-edge rates in the reported variants. Neither variant was promoted. [Geometry record](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=2a326a8f-e374-466a-9c62-42e4c0956ac1), [topology review](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=934f39ac-5b36-426f-ae9d-9d9877384f7b)

**Interpretation.** Spatial support can help organize and inspect a figure, but it does not establish the domain meaning of a connection. A line-like image feature, a geometric adjacency, and an accepted semantic relation are separate claims. The later retrieval/QA pivot should not inherit a new requirement to label topology merely because those artifacts exist.

### Byte parity did not establish perception quality

An adjacent two-page LANL/Terrier exercise reported 100% MCP image-byte parity. The subsequent review found scoring contradictions and unproved dynamic-crop claims; its 2/6 perception figure remained provisional. This is useful evidence that a transport path can preserve image bytes, but it is not reliable AWS or Fresh 9 perception evidence. [Transport and perception review](https://chatgpt.com/c/6aa48497-86e0-83ea-a74a-ecc82923f8c9?messageId=de0fa9ec-2dd3-483b-8bb6-f4f64de5c4ef)

**Recommended practice.** Keep transport checks, rendering checks, crop selection, grounding, and semantic reading separate. If the bytes are correct, investigate the next stage. If the crop or rendering is wrong, fix that before evaluating a reader. The successful lower-layer test remains valuable even when the end-to-end result fails.

## 6 A blocked candidate has no comparative quality score

The historical record contains several kinds of non-execution. PaddleOCR-VL was unavailable at the frozen runtime boundary after six attempts. DTRT lacked a usable checkpoint in the reviewed period. PHT-CAD was deferred without runnable code or weights. In the later Annex B extraction comparison, A1 was blocked by source-route authorization, A2 by unavailable Docling Graph dependencies, and A3 by the missing KAPipe adapter. A0 ran. [Specialist review](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=d5a5f7ff-022e-42ca-8c40-1b174d8f524f), [topology review](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=934f39ac-5b36-426f-ae9d-9d9877384f7b), [Annex B status](https://chatgpt.com/c/6abd15bb-99d4-83ea-a8d2-7eb431bf7af9?messageId=0e5d10ee-d034-4a18-821f-661eb7eb8a55)

Use explicit outcomes such as executed, failed quality gate, unavailable, authorization blocked, adapter missing, or inconclusive. Do not rank “unavailable” as though it had a poor answer score. Its installation or operational difficulty may still count against practical suitability, but that is a different measure.

Readiness checks should be short and bounded. Confirm the exact candidate, license, supported platform, model availability, resource requirement, data route, and minimal adapter. If a declared dependency cannot be met, record the blocker and continue with the accepted baseline. An optional challenger should not hold the whole product hostage.

The actual Docling parser trial on five MIL-STD figures must also stay separate from the later unexecuted Docling Graph arm. The narrow parser comparison favored the native/OCR paths under its conditions. It neither rejects every Docling capability nor proves that schema-guided extraction is unnecessary. [Executed parser comparison](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=06286b13-a355-408f-8888-1344cd3fed56)

## 7 Use finite bakeoffs to make a decision

### The historical portfolio was a map

The earlier 26-option portfolio covered extraction, representation, retrieval, graph use, MAGE policies, readers, entity and relation extraction, interchange, cross-project discovery, and improvement workflows. It was a proposed research portfolio, not proof that the components were installed or that all comparisons ran. [Original portfolio](https://chatgpt.com/c/6a770fca-df14-83ea-9328-41fcb16215b4?messageId=f5ed7147-4229-4e98-87bf-707c7a463054)

**Interpretation.** The portfolio captured many legitimate questions, but using the whole list as a delivery plan would make completion depend on an open-ended research program. A framework-first approach should reduce this surface by asking which unknowns actually block the next useful product outcome.

### A complete comparison definition

Every new bakeoff should specify:

1. The decision it will change.
2. A falsifiable hypothesis.
3. The exact source population and revision.
4. Development and held-out questions with reviewed evidence.
5. The component held fixed and the component being changed.
6. Resource, model, and retrieval budgets.
7. Quality metrics and critical integrity failures.
8. Setup, maintenance, latency, and cost observations.
9. A finite tuning allowance and stopping rule.
10. The possible outcomes, including retaining the baseline or finding the comparison inconclusive.

Do not require every experiment to produce a winner. “The baseline remains adequate” and “the test cannot distinguish these candidates” are useful results. A candidate can also win one role and lose another; a better parser does not automatically become the full framework.

### Stop rules prevent repeated checking

Stop a candidate when it cannot preserve critical source identity, loses qualifiers without warning, leaks across corpus boundaries, or requires an unsupported data route. Stop the comparison when the chosen decision has sufficient evidence under the approved gate. Reopen it only after a material change or a newly demonstrated failure.

An unchanged result is not inherently a reason to rerun. Name the new evidence expected from each additional check. If the check has no distinct claim to establish, it is likely duplicating existing assurance.

## 8 Match rigor to the stage

### Proof of concept

A POC should answer a narrow technical question with real evidence. It needs a frozen small corpus, correct provenance, an honest evaluator, a baseline, and explicit limitations. It does not need a universal ontology, every deployment target, every model family, a production UI, or complete rehabilitation of historical components.

The appropriate POC outcome is a bounded claim such as “this parser preserved the required table cells and footnotes on the declared challenge set” or “this framework produced faithful answers for this reviewed slice with fewer custom adapters.” Avoid transforming that into “the system supports the corpus” or “the integration is production-ready.”

### Development baseline

A development baseline adds repeatable ingestion, source and evidence identity, version-pinned configuration, a stable evaluation harness, and reproducible failure cases. It should make the next experiment cheaper and safer. The AWS Annex A report of 619 MiniLM vectors and six ColPali crops is a scoped development integration, with separate live query exercises and truthful partial or out-of-scope outcomes. It was not production authorization. [Annex A execution report](https://chatgpt.com/c/6ab2874a-ca9c-83ea-a7eb-959b76dbd0d1?messageId=d976f6bc-285c-47da-9e73-139620c0bf0c)

### Release candidate and production

A release needs access control, update and deletion behavior, recovery, monitored failures, clear data-handling boundaries, measured resource costs, and an operator who can maintain it. It also needs a declared supported question scope and a way to report uncertainty. Broader claims require broader representative evaluation.

Production rigor should be added when the product is approaching real operational use. It should not be used to indefinitely postpone a narrow research answer. Conversely, a POC label does not excuse unsupported claims, unauthorized source transmission, or a defective scorer.

## 9 Build versus reuse and open source options

### Keep the distinctive layer small

NavyWeld's lasting value is in accepted evidence, source anchors, ontology, qualifiers, version semantics, real questions, and evaluation. Generic orchestration, indexing, model clients, retries, storage integration, and basic interfaces are candidates for reuse. A new custom component should name the concrete failure it prevents and carry a direct test for that failure.

The core contract should survive a framework swap. Keep corpus and document revisions, hashes, precise evidence anchors, entity and term IDs, typed relations, qualifiers, asserted-versus-derived status, and review status in a project-owned form. Extraction confidence and source authority are separate fields. Neither should automatically determine acceptance.

### Open source options by job

| Option | Job it may do | Caution from the current research |
|---|---|---|
| Utopia | Evidence-backed knowledge application with review and temporal facts | Early application rather than drop-in library; verify exact anchor and qualifier round trips |
| LightRAG with RAG-Anything | Combined multimodal graph/vector retrieval path | Treat as one current integrated candidate; citations do not prove source support |
| RAGFlow | Integrated parsing, retrieval, and analyst workflow | Domain semantics still need a NavyWeld contract; operational dependencies remain |
| Docling and Docling Graph | Structured parsing plus schema-guided extraction | Schema validity is not factual validity; parser and graph trials are different |
| PaddleOCR | OCR, layout, and table extraction alternatives | Compare coordinates and difficult-page behavior; prior unavailability was not a quality score |
| KAPipe | Modular extraction, proposition, graph, and retrieval research | Research focus, dependency footprint, and breaking changes argue for a bounded component test |
| AWS GraphRAG Toolkit | Source-statement graphs or retrieval over an existing graph | Requires evidence that graph retrieval adds value; distinct from managed Bedrock |
| OpenSPG KAG | Typed knowledge and guided reasoning | Higher engine and ontology commitment; formal reasoning need should be demonstrated |
| Neo4j GraphRAG | Typed graph construction and retrieval | KG Builder is experimental; database licensing and operation are separate |
| CLM | Self-hosted finite-decision or relevance ranking | Text decision component; GPU serving and candidate-set calibration need measurement |
| OpenRig | Engineering coordination around coding harnesses | Development tooling only; adds no established domain evidence quality |

Primary sources: [Utopia](https://github.com/deeplethe/utopia), [LightRAG](https://github.com/HKUDS/LightRAG), [RAG-Anything](https://github.com/HKUDS/RAG-Anything), [RAGFlow](https://github.com/infiniflow/ragflow), [Docling](https://github.com/docling-project/docling), [Docling Graph](https://github.com/docling-project/docling-graph), [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), [KAPipe](https://github.com/norikinishida/kapipe), [AWS GraphRAG Toolkit](https://github.com/awslabs/graphrag-toolkit), [KAG](https://github.com/OpenSPG/KAG), [Neo4j KG Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html), [CLM](https://github.com/Contrastive-LM/CLM), [OpenRig](https://github.com/mvschwarz/openrig)

The companion roadmap provides the fuller candidate analysis and proposed sequencing. No project-specific quality or cost winner is established by this research.

### Jev is a different type of dependency

Jev is a hosted typed-decision API described in the official TypeSafe documentation. It should not be presented as an open-source framework or a multimodal answer generator. Its potential uses are bounded routing, relevance, or support decisions. Jevai.org is a community hub, while official API and model claims belong to TypeSafe. [Official introduction](https://docs.typesafe.ai/introduction), [model documentation](https://docs.typesafe.ai/models), [community site](https://www.jevai.org/)

A Jev-versus-CLM comparison should use the same atomic decisions, labels, and fallback policy. Keep it shadow-only initially. Measure acceptance of unsupported claims, calibration, option-order stability, and total cost. A small screening set cannot certify a rare-error guarantee. External processing approval is required before sending source-bearing material to a hosted service.

### Code license is only one part of reuse

Check the framework license, model-weight license, bundled parser and OCR models, embedding and reranking models, database terms, connectors, and hosting terms separately. A permissive code repository does not establish unrestricted use of every model it can call. An offline-capable application can still depend on expensive hardware or external inference.

Record the version and license evidence used for the selection. Keep the source-document usage rights separate from software licensing. A project may be allowed to use a framework while lacking authorization to send the licensed corpus to a particular provider.

### The lowest maintenance answer may be a partial adoption

The correct outcome can be retaining the existing hybrid retriever and adopting only a better parser, or using a framework for orchestration while keeping the accepted ontology outside its generated graph. Avoid a binary choice between rebuilding everything and adopting a whole stack unquestioningly.

A reuse decision should include export and rollback tests. Can canonical IDs, qualifiers, review status, and source links survive a round trip? Can the old path still answer the baseline questions after the experiment? If not, the adoption cost is higher than the installation effort suggests.

## 10 Migration lessons from the current preservation work

The incidents in this section come from the 12 October project handoff. They are operational lessons, not a claim that the active migration is complete. Independent review was still pending in the handoff, and Git discovery/compiler behavior, the Windows lock, and resource bindings were not all proved. [Coordination task and dated receipts](https://chatgpt.com/c/01a11bc1-eeb3-7260-8ba7-1c1688a46038)

### Preserve bytes and interpret content as separate steps

The reported encoding investigation validated CP437 against 36 sealed Unicode path components. All 152 unchanged logs passed strict decoding and byte-for-byte re-encoding. That is a successful, scoped interpretation check; it does not require or imply rewriting the original logs. It illustrates a general boundary: preserving a file's bytes and successfully interpreting its text are separate tasks.

Recommended practice is to retain raw bytes, record the attempted encoding and failure, and use a bounded, documented fallback for interpretation when justified. Inventory output should distinguish preserved, decoded, parsed, and reviewed states. It should also distinguish an unreadable text representation from a missing file.

### Symlinks and settings need explicit treatment

The reported Windows recovery initially had 1,183 failed directory-symlink creations with error 1314. The number 1314 is an error code, not another inventory count. A bounded Python probe succeeded without changing security settings; the later receipt reported all 1,183 links recovered and restore links rebound inside the destination. This is a useful example of finding a scoped supported route before proposing a security-setting change.

A plain file count can still miss link targets, platform-specific paths, hidden configuration, and the settings needed to reproduce a tool invocation. A copy may be byte-complete within a declared file population while remaining operationally incomplete.

Record links as links, including their targets and whether the target is inside the preservation scope. Avoid following them indiscriminately into unrelated or unauthorized locations. Record which settings are safe to preserve, which are secret-bearing, and which need reconstruction through an approved process. Do not copy credentials merely because a settings directory contains them.

### Hidden support directories affect reproducibility

The reported missed hidden support directories, including `.ai` and OpenCode/status material, show why a visible-source-only inventory can omit important handoff or tooling context. The lesson is to define inclusion and exclusion rules once, then test the inventory against those rules. It is not a reason to ingest every hidden file into the runtime answer corpus.

Classify hidden content by purpose: source and manifests, tool configuration, workflow state, caches, generated artifacts, and secrets. Preserve relevant safe context within the approved migration scope. Keep unnecessary caches and credential material out of review artifacts. Report exclusions so that another reviewer can understand them.

### Aggregate reporting protects private identifiers

The handoff noted private-identifier disclosure issues. Review reports should normally give counts, classes of issue, and source-safe examples rather than raw member keys, secrets, or unnecessary private paths. A private repository still has an audience; copying data into it changes where that data is retained and reviewed.

Source manifests can reference sensitive material without reproducing it in broadly visible summaries. Keep detailed sensitive evidence only in its authorized location and provide the minimum metadata needed to verify the result. This retrospective deliberately uses aggregate incident descriptions.

### Construction time and preparation time are different

The reported construction produced 7,422 files, 602 directories, and 113,288,504 bytes, approximately 113 MB, in 145 seconds after a much longer preparation period. This timing describes that construction stage, not the total migration or the duration of all required review. It does not prove that preparation was unnecessary.

**Interpretation.** The contrast is a useful prompt to examine coordination, repeated inventories, unclear target definitions, and proof requirements. Some preparation establishes necessary safety and scope. Other work may repeat information without changing a decision. Future retrospectives should measure time spent defining the task, preparing prerequisites, executing, validating, and waiting separately.

### Preservation does not require rehabilitating every component

The source project contains historical experiments, configurations, outputs, and partially working integrations. Full preservation means retaining the authorized material with sufficient identity and context. It does not automatically mean every old component must run in the new product. A future functional rebuild can select components based on their value and current requirements.

This distinction must not be used to weaken the current migration's already agreed criteria without approval. If the criteria need to change, present the exact change, what evidence would be lost or deferred, and the reason. Let the owner decide. Finish the active preservation review on its current terms until such a decision exists.

## 11 Reduce coordination overhead without weakening proof

### Make the handoff a compact contract

A good handoff should contain the current objective, exact target and revision, authorized scope, known facts, unresolved blockers, expected artifact, verification rule, and next decision. Link the durable artifacts instead of copying a long evolving history into every instruction.

The current control versions, repository commit, corpus IDs, and evidence manifests should be easy to find in one dated handoff. When a fact changes, update the authoritative record and point to the change. Avoid parallel summaries that gradually disagree about what is accepted, provisional, or blocked.

### Give every check a distinct claim

Repeated broad checking can make a project look active while leaving the main uncertainty untouched. Before a new check, name its purpose: verifying a byte inventory, finding missing bindings, testing scorer sensitivity, reproducing an answer, or confirming that an external operation finished. Reuse valid earlier evidence for unchanged claims.

Independent review is valuable when it examines the relevant evidence from a genuinely different angle. It loses value when each reviewer merely repeats the previous status or starts a new generalized audit. Ask the reviewer for a decision on a bounded claim and the smallest evidence needed to support or reject it.

### Prefer one coherent adapter over repeated adapter churn

Adapters are necessary, but a succession of partially specified adapters can become a new source of failure. Establish the evidence contract first. For each adapter, test exact identity mapping, location fidelity, qualifier retention, error reporting, and export. Do not keep rewriting the domain contract to match each candidate's preferred output.

When an adapter fails, determine whether the problem is a small implementation defect, a fundamental missing capability, or an unsupported assumption. Fix the first, reject or defer the second, and revise the hypothesis for the third. Avoid turning each failure into another full-stack redesign.

### Agent availability differs from process completion

A free agent slot, a closed agent session, a background shell process, and a completed external job are different states. Capacity management should not be interpreted as proof that work stopped or finished. Record durable job identifiers and artifacts for long-running work, and check the relevant process or service before reporting completion or starting a duplicate run.

Use parallel workers for independent research or review. Use a single owner for dependent state changes and the final integration decision. More agents can help throughput, but overlapping writers or unclear ownership can increase reconciliation work and duplicate effort. Measure the useful output, elapsed time, defects, and human intervention rather than the number of workers.

### Do not diagnose context rot without evidence

The record contains long histories, repeated handoffs, changing versions, and conflicting claims. These conditions can contribute to mistakes, but they do not prove a specific model-memory failure. More concrete explanations may include stale manifests, ambiguous source populations, inadequate scorer tests, unsupported assumptions, missing artifacts, or messages that did not state the exact target.

Treat “context rot” as a hypothesis if it is raised, not as the retrospective's established cause. First improve the external evidence and handoff contract. If inconsistencies persist under controlled conditions, a focused comparison can investigate whether context length or handoff design affects the outcome.

## 12 Keep Git documentation and runtime roles clear

### Git carries versioned definitions

Use Git for code, schema or evidence contracts, configuration templates, evaluation definitions, manifests, and decision records. A run should point to the exact commit or tag that defined it. Large assets can remain in authorized storage with stable references and integrity metadata where that is the approved design.

Do not put secrets, unnecessary private identifiers, or unrestricted source payloads into a repository just to make a handoff self-contained. The same caution applies to source excerpts in issue comments, generated reports, and diagnostic logs.

### Project pages carry the human view

A Space or project page is useful for the current summary, open decisions, review links, and operating guidance. It should point to the versioned definitions rather than silently replacing them. Keep status words consistent: proposed, executed, accepted, provisional, blocked, superseded, or inconclusive.

An advisory roadmap can be published for review without becoming the new execution instruction. When the owner accepts a proposal, record that decision explicitly and update the appropriate active artifact through the approved workflow.

### Runtime carries derived state

Parsed outputs, indexes, graph projections, caches, traces, and jobs need retention and rebuild rules. Distinguish what can be regenerated from what must be backed up because it contains accepted review decisions or irreplaceable operational history. A runtime-generated claim should not become canonical merely because it survived in a database.

The practical test is whether another person can follow a reported answer through source identity, extraction, retrieval, model configuration, validation, and review. A useful trace is a chain of inspectable artifacts, not simply a long execution log.

## 13 Manage security cost and external dependencies early

### Source routing is an explicit boundary

Before external model or managed-service use, identify the source-bearing data, recipient, account, region, purpose, retention, and applicable terms. A user may authorize a project without authorizing every provider reachable through a framework or tool. A working connector is not proof that a particular licensed corpus may be sent through it.

Use least-privilege access and separate the read-only NLQ product from tools that can modify files, provision services, or send messages. Treat instructions found inside retrieved documents as data. A retrieved passage cannot authorize a change to the system or its evaluation rules.

### Count operational cost as well as model cost

Measure ingestion, OCR, embedding, index rebuilds, retrieval, reranking, reader calls, validation, storage, and operator effort. Count failed jobs and updates. A cheap per-token API can still produce an expensive workflow if it requires repeated calls and fallback, while a local model can be costly when its GPU is mostly idle.

Provider price or benchmark latency is a reference point, not a NavyWeld cost estimate. Use the actual corpus, query rate, concurrency, revision frequency, and target environment before making a budget claim. No new paid service, top-up, overage, or cloud provision is authorized by this retrospective.

### Managed services are optional operating choices

Amazon Bedrock, Google Cloud search/RAG with Document AI, and Databricks document processing may reduce some operational work. They still need evidence-fidelity, access-control, update, export, and cost tests. The welding standard AWS A3.0 should not be confused with a commitment to Amazon Web Services infrastructure.

Avoid evaluating all providers at once. If an existing approved platform supplies a strong reason, choose one bounded challenger. If not, the framework hypothesis can be tested without a new managed-service dependency.

## 14 A reusable practice for the next multimodal RAG project

### Before building

- State the user outcome in terms of answerable questions and evidence.
- Name the source population, revisions, use rights, and permitted data routes.
- Inspect a small representative set of text, tables, figures, scans, and notes.
- Establish stable source IDs and preserve originals independently of extraction.
- Define accepted, provisional, inferred, and unsupported states.
- Select a strong simple baseline before adding graphs or agent policies.

### Before comparing

- Freeze the question set and review the expected evidence.
- Separate development from holdout and keep negative controls.
- Test the scorer with deliberate wrong answers and irrelevant citations.
- Pin versions and record model, parser, prompt, and budget differences.
- Make unavailable and authorization-blocked outcomes explicit.
- Agree on stop rules and the decision the experiment will change.

### Before adopting

- Verify canonical IDs, source anchors, qualifiers, and review status through export and reimport.
- Measure answer-level benefit and maintenance burden.
- Test update, deletion, reindex, and recovery behavior.
- Review the full code, model, database, and provider license chain.
- Confirm the data and spending boundaries for the actual deployment.
- Retain a rollback path and the accepted baseline evidence.

### Before releasing

- Have a second operator reproduce the supported path.
- Review material claims against exact sources.
- Test unsupported and conflicting-source questions.
- Document supported scope, limitations, and expected abstentions.
- Verify access control and safe logging.
- Publish a concise run and decision record tied to exact versions.

## 15 Practices to avoid

| Avoid | Why it fails | Prefer |
|---|---|---|
| Treating all candidate names as equivalent frameworks | They solve different layers and carry different dependencies | Select the role first and compare like with like |
| Adding a graph because the source is complex | A graph can encode unsupported or dequalified relations | Add relationships only for a measured question need |
| Using a bigger reader before isolating the failure | Retrieval, cropping, qualifiers, or task design may dominate | Fixed-gold-evidence reader tests |
| Reporting citation presence as answer support | The citation may be irrelevant or incomplete | Claim-level source verification |
| Calling an unavailable trial a quality loss | No quality measurement occurred | Separate readiness and answer-quality outcomes |
| Merging historical populations into one score | Denominators and scope become misleading | Corpus, revision, and question-set manifests |
| Reopening every historical experiment | Research never converges on a product decision | A small shortlist and explicit deferrals |
| Rebuilding generic infrastructure by default | Maintenance accumulates outside the project's distinctive value | Reuse with a tested evidence contract |
| Adopting an entire stack for one useful component | Unneeded services and coupling become permanent | Bounded adapters and partial adoption |
| Rechecking a completed claim without new evidence | Effort grows while uncertainty stays unchanged | A named purpose and stopping condition for each check |
| Using file counts as proof of reproducibility | Links, settings, bindings, and execution assumptions can still be missing | Separate preservation and reproducibility checks |
| Copying private identifiers into review summaries | Review artifacts acquire unnecessary sensitive data | Aggregate metadata and authorized evidence references |
| Equating free software with zero cost | Models, hardware, storage, and operation still cost | Measured total workload cost |
| Treating a roadmap as execution approval | Proposed scope can silently become a commitment | Explicit decisions before implementation |

## 16 What the record still cannot establish

The available evidence does not establish a current best framework for NavyWeld, a new AWS A3.0 multimodal accuracy result, the superiority of any managed provider, or a production-ready replacement architecture. It also does not establish that context rot caused the coordination problems, that every historical component must be restored to operation, or that a graph-based approach is required for the target questions.

It does establish useful failures and reusable assets: scoped parser and OCR outcomes, corrected fusion and reader results, preserved visual assets, invalid scorer examples, an accepted retrieval substrate, reviewed evidence, and a clearer separation of migration and product goals. Those assets should shorten the next decision rather than become a reason to repeat the entire history.

The companion `navy_weld_framework_roadmap.md` turns these lessons into a proposed architecture and phased decision sequence. The next productive step is to choose one narrow AWS question slice, retain the exact evidence contract, and test whether a small framework-based path can answer it faithfully with less custom work.

## 17 Source and status notes

Historical links in this document point to private owner review history and may require the owner's account. They support the reported outcomes and scope corrections; they are not evidence of a fresh rerun. No licensed source excerpts, raw member keys, secrets, or private machine paths are included.

The migration figures and incidents are attributed to the dated 12 October 2026 project handoff. The current recorded controls were Goal V10, Instructions V8, Card V13, and Runbook V5, with [pull request 5](https://github.com/kaiello/navy-weld/pull/5) and `main` recorded at `ddb5c9f911c6f1a93810a1342bcfbf997e7593ea`. The accepted four-part backup/restore evidence covers a 14.058 GB, 274,129-file backup inventory, with declared control-related differences in restored byte counts. A separate, independently accepted preservation copy covers 42.34 GB, 339,766 files, and 152 roots. The 33 revision-tree inventories and 87 Fresh 9 files are additional scoped evidence; they must not be collapsed into either population. The later 7,422-file construction report and zero mismatches for its declared Git pair were still awaiting independent review in the supplied handoff.

External project capabilities were checked on 12 October 2026. They can change, and the presence of a feature in documentation does not establish its correctness on this corpus. All suggested practices, comparisons, thresholds, and future deployments remain proposals for review.

