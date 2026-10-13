# NavyWeld framework first roadmap

## Purpose and recommendation

Prepared 12 October 2026. Status: speculative planning draft for review. This document proposes a future direction for NavyWeld; it does not authorize a framework adoption, a new runtime, a paid service, repository changes, or a change to the active migration acceptance criteria.

The recommendation is to make a mature framework responsible for ordinary ingestion and retrieval plumbing, while retaining a small NavyWeld-owned layer for the things that make this project valuable: document identity, accepted evidence, reliable anchors, domain ontology, qualifiers, version semantics, questions, evaluations, and release decisions. Compare a small number of coherent stacks against the same narrow vertical slice, choose one primary path, and add components only when a measured failure justifies them.

The long-term objective remains AWS A3.0 multimodal natural-language querying. The practical first demonstration should be much narrower: a person asks a real AWS question, the system retrieves the relevant text and visual or tabular evidence, produces a scoped answer with exact citations, and abstains when the evidence does not support the answer. The system must preserve the source revision and qualifying conditions throughout that path. A polished chat interface, a large graph, or a high retrieval score cannot substitute for that result.

The immediate full-preservation migration from `mb2026` to the new NavyWeld Git context is a separate critical path. Its job is to preserve the project and make identities, handoffs, and evidence inspectable. It should not become an obligation to make every historical experiment production-ready. Conversely, a future framework proposal must not quietly narrow a preservation commitment that is already in force. Any such change is a decision for the project owner.

### What this document provides

- A boundary between reusable framework services and NavyWeld's enduring intellectual assets.
- A proposed end-to-end architecture with stable evidence and evaluation contracts.
- A way to reuse the results of prior bakeoffs without restarting them indiscriminately.
- A finite comparison plan, with hypotheses, inputs, metrics, guardrails, and stopping rules.
- A phased route from a small vertical slice to an operable multimodal NLQ service.
- Decision points for deployment, cost, security, licensing, and optional managed services.

### How to read the status labels

**Recorded project state** means the current project handoff reports the fact. These facts should be traced to the linked project artifacts before becoming an execution baseline. **Verified external capability** means a primary source describes the capability; it does not establish that it works for the NavyWeld corpus. **Proposal** means a suggested design or sequence. **Hypothesis** means a claim a comparison must test. **Unresolved** means the available evidence does not support a conclusion.

All future phases, acceptance thresholds, ownership assignments, and deployment choices in this document are proposals unless explicitly described as existing accepted evidence. No new accuracy result is claimed.

## 1 Current position and boundaries

### The active project context

The recorded control versions are Goal V10, Instructions V8, Card V13, and Runbook V5. The current Git context includes [NavyWeld pull request 5](https://github.com/kaiello/navy-weld/pull/5), with `main` recorded at `ddb5c9f911c6f1a93810a1342bcfbf997e7593ea`. These identifiers are a dated reference point for the roadmap, rather than a claim that a moving branch will remain at that commit.

The accepted preservation evidence has separate scopes: the four-part backup/restore evidence covers a 14.058 GB, 274,129-file backup inventory, with declared control-related differences in restored byte counts; an additional preservation copy covers 42.34 GB, 339,766 files, and 152 roots and was independently accepted. The record also includes 33 revision-tree inventories and 87 Fresh 9 files. These are separate evidence populations, not one combined backup count. A later construction report at 16:43 recorded 7,422 files, 602 directories, and zero mismatches for the declared Git pair. Independent review of that construction was still pending in the supplied handoff. Git discovery versus compiler behavior, a missing Windows lock, and resource bindings were still unproved. A count or byte comparison alone cannot establish those missing forms of reproducibility. [12 October coordination handoff](https://chatgpt.com/c/01a11bc1-eeb3-7260-8ba7-1c1688a46038)

The legacy nine-document corpus and Fresh 9 remain separate corpus identities. They must not be merged by convenience, by similar filenames, or by a framework's default collection behavior. Corpus membership, revision, extraction configuration, and acceptance state belong in every run manifest.

### What existing results establish

The historical FULL result of 95/2,285 is a separate result population from the AWS baseline of 6/6 questions, 7/7 parts, and 213 controls. Neither denominator should be used to imply performance on the other population. The accepted A2/A3 overlay contains 8 nodes and 4 edges. The record of 19 reviewed claims and 3 provisional claims is a review inventory, not automatic admission of every claim to the runtime evidence set.

These results are useful assets. They provide regression questions, examples of source conditions, traces, and known failure modes. They do not yet demonstrate new AWS A3.0 multimodal answer accuracy, complete framework compatibility, or production readiness.

### Four separate acceptance questions

| Question | Evidence needed | What does not answer it |
|---|---|---|
| Was the project preserved? | Declared source and destination inventories, byte or content checks, exclusions, restore evidence, revision and identity mapping | A new framework demo |
| Can the preserved project be understood and reproduced? | Resolved entry points, resource bindings, dependency and platform facts, inspectable handoffs | File counts alone |
| Does a proposed stack answer the target questions faithfully? | Frozen questions, accepted evidence, source-level answer review, negative controls | A preserved repository or attractive UI |
| Is that stack worth operating? | Measured maintenance effort, cost, latency, update behavior, security and recovery | An isolated answer-quality win |

Keep these questions explicit in reviews. Each has its own evidence and owner. A result may satisfy one while leaving the others open.

## 2 The framework first principle

### Put commodity work behind a replaceable boundary

NavyWeld should prefer established components for file intake, parsing orchestration, chunk or element indexing, embedding calls, job retries, vector and lexical search, query orchestration, tracing, and a basic review interface. The benefit is reduced custom code and fewer infrastructure decisions. It is real only if the chosen stack also reduces the work needed to upgrade, debug, explain, and recover the system.

The framework should not own the only copy of document identity, evidence status, question definitions, source-to-answer lineage, or release decisions. Those records need explicit exports or project-owned representations. If swapping a framework requires recovering the meaning of previously accepted evidence from opaque internal storage, the ownership boundary has failed.

A single primary framework is the preferred end state for the first deliverable. Supporting components can fill demonstrated gaps, but they should have bounded jobs. For example, an OCR fallback may process a known class of scanned pages, and a visual retriever may add a page-level candidate lane. Neither should become a second complete orchestration stack by accident.

### Retain the domain and evidence layer

The durable NavyWeld layer should contain:

1. **Source identity.** Corpus, document, revision, content hash, source location, and permitted use.
2. **Evidence identity.** Stable evidence IDs tied to a specific source revision and exact location, including text spans, page regions, tables, figures, and relationships.
3. **Acceptance state.** Reviewed, accepted, provisional, superseded, rejected, or unreviewed status, with the relevant decision and reviewer record where available.
4. **Domain semantics.** Welding concepts, identifiers, relationships, units, applicability, exceptions, and version-dependent meaning.
5. **Answer requirements.** The actual questions, expected scope, required evidence, qualifying conditions, and acceptable abstentions.
6. **Evaluation and release evidence.** Frozen inputs, run manifests, baseline outputs, adjudications, regression results, and decision records.

This layer should be small enough to understand. It does not need to become a general-purpose knowledge platform before it can support useful answers. Its purpose is to preserve the distinctions that generic retrieval systems otherwise tend to blur.

### What to keep custom only when necessary

Custom code is justified where the project has a concrete requirement that the selected framework cannot satisfy through supported extension points. Likely examples include a canonical evidence adapter, a version-aware applicability filter, a claim-level citation validator, and the project-specific evaluation harness. Each custom component should name the failure it prevents and have a direct test for that failure.

Avoid custom reimplementations of generic queues, vector stores, model clients, UI frameworks, or agent schedulers unless the comparison demonstrates a material reason. An extra abstraction layer also carries a cost. “Replaceable” should mean a tested input/output contract and export path, rather than an elaborate universal framework wrapper.

## 3 Proposed architecture

### End to end flow

The proposed logical path is:

`Source registry → parsing and layout → canonical evidence → retrieval → scoped domain relations → answer construction → citation and abstention checks → evaluation and review`

This describes responsibilities, not a mandatory number of services. An initial implementation may run as one application with a small number of stores. Splitting each responsibility into a separate service would add operational work before scale or security requirements justify it.

The two control inputs are the corpus manifest and the evaluation manifest. The two reviewable outputs are the answer with its evidence trail and the run report. A run should be reproducible from these records without relying on an unrecorded conversation state.

### Source registry and immutable originals

The original document is retained independently of parser output. Each source revision has a stable identifier and content digest. The registry records whether the source belongs to legacy 9, Fresh 9, or a later explicitly declared corpus. It also records the page numbering convention because PDF page index, printed page number, and section number may disagree.

A reparse creates a new extraction version linked to the same source revision. A revised source creates a new source revision. Neither operation silently overwrites accepted evidence. A migration mapping relates old paths or IDs to their current locations so that an accepted citation can remain resolvable after files move.

For large binary assets, Git can hold the manifest and approved reference while the actual asset remains in the authorized storage appropriate to it. The storage decision must preserve recovery, access control, and citation resolution. This roadmap does not authorize a new asset upload or storage migration.

### Parsing and layout

Use one default parser path for the selected corpus slice. Capture reading order, page layout, tables, images, and text rather than flattening everything to a single undifferentiated string. Where the parser cannot recover a relevant element, mark the gap so retrieval and answer construction do not treat an empty extraction as proof of absence.

A parser adapter should preserve the parser's raw result alongside the normalized result. Record parser version, model or OCR version, rendering settings, language assumptions, and known loss of structure. OCR confidence or model confidence is a signal for review, not a substitute for source verification.

The initial fallback policy should be explicit and narrow. For example, invoke the alternative OCR or layout parser only on pages classified as unreadable or structurally suspect by a recorded rule. Running every parser on every document and then reconciling the union would create an expensive second project.

### Canonical evidence

Canonical evidence is the boundary between extraction technology and domain truth. A framework may create a chunk, caption, graph edge, or extracted relation, but that object remains a candidate until it is linked to its source and assigned the appropriate status.

A proposed minimal evidence record includes:

| Field group | Required meaning |
|---|---|
| Identity | Evidence ID, source document ID, source revision, corpus ID, extraction version |
| Location | PDF page index, printed page or section when present, bounding region or text span, element ID |
| Content | Exact extracted text or structured values, element type, asset reference, normalized representation |
| Lineage | Parser and configuration, source hash, transform history, parent evidence IDs, asserted versus derived status |
| Domain context | Relevant concept IDs, units, scope, applicability conditions, exceptions, revision semantics |
| Review | Acceptance status, decision reference, review date where available, supersession link; extraction confidence and source authority recorded separately |
| Use constraints | Permitted corpus scope, sensitivity or access label where applicable, known extraction limitations |

This is a proposed logical contract, not a schema migration to run now. The first version should implement only fields that are needed for the chosen slice and source integrity, while preserving the ability to add richer relationships later.

Tables require more than a page citation. A usable record should preserve headers, row and column coordinates, merged-cell meaning, units, and footnotes when those determine the answer. A figure may need a region, caption, legend, and associated text. A visual retriever that finds the right page is valuable, but it has not yet established which value or condition on that page supports the answer.

### Retrieval and evidence assembly

Start with a strong, inspectable retrieval baseline. It should support exact terms and identifiers, semantic paraphrases, and explicit filters for corpus and revision. Add a visual retrieval lane only when target questions require evidence that the text or structure path misses.

The retrieval interface returns candidate evidence IDs, scores meaningful within that retrieval method, and source locations. It should never return anonymous text that has lost its revision. If scores from different retrievers are fused, the fusion rule and candidate budgets must be recorded. Raw scores from different systems cannot be assumed to be comparable.

Reranking and evidence assembly should consider whether the retrieved material includes the relevant qualifier, table header, exception, or linked definition. A candidate that contains an attractive answer phrase but omits the applicability condition may be worse than a lower-ranked, complete evidence group.

Retrieval success is evaluated at the evidence needed to answer the question. Page recall, element recall, and complete-evidence-group recall are distinct measurements. The correct page alone may still leave the system unable to answer a table or figure question safely.

### Domain relations

Use domain relationships where they answer a concrete question, such as resolving a concept's definition, following an explicit cross-reference, distinguishing an exception from a general rule, or identifying which revision a requirement applies to. Accepted relations should retain their source evidence and any direction or qualifier.

Keep model-extracted relations separate from accepted relations. A relation inferred by a framework is useful as a retrieval hint or review candidate, but must not acquire the authority of the accepted ontology merely because it is stored in a graph database. Preserve provisional status in exports and in the answer path.

The first graph should be intentionally small. Expand from the accepted overlay and demonstrated question needs rather than from a goal of maximizing nodes and edges. A smaller graph with inspectable evidence can be more useful than a large graph that conflates mention, inference, and accepted meaning.

### Answer construction and abstention

An answer should state the applicable corpus and revision when the question could otherwise be ambiguous. It should cite the evidence for each material claim and retain units, conditions, exceptions, and uncertainty. If the answer depends on a table, it should be possible for a reviewer to find the relevant cells and their footnotes.

Before finalizing, check whether the cited evidence supports the actual wording. A citation attached to a paragraph is insufficient if the paragraph adds an unsupported qualification or drops a necessary one. Separate answer generation from evidence validation even if the same framework orchestrates both steps.

Use explicit answer outcomes: supported answer; supported answer with a scope qualification; clarification needed; insufficient evidence; conflicting sources; or unsupported question. The wording can remain natural. The point is that uncertainty should produce a predictable behavior rather than an improvised guess.

Abstention is part of the product. A negative control is successful when the system refuses to infer a value that the authorized corpus does not establish. At the same time, an overly cautious system that refuses clearly answerable questions is not useful. Measure both unsupported answering and unnecessary abstention.

### Evaluation and review

Keep evaluation outside the framework's private scoring system. Store the questions, evidence references, expected constraints, and adjudications in a project-controlled form. Framework-native dashboards may be useful views, but they must not become the only durable record.

Each run records the exact source and corpus revisions, extraction settings, index configuration, framework version, model identifiers, prompts, retrieval budgets, answer outputs, latency, and measured cost inputs. Where a provider does not expose a fully reproducible model revision, record that limitation rather than implying deterministic replay.

Evaluation should distinguish source preservation, parsing, retrieval, reasoning over the evidence, answer correctness, citations, abstention, and operation. A single aggregate score hides the reason a stack succeeds or fails and makes a later regression harder to diagnose.

## 4 Reusing the historical work

### Preserve the evidence before deciding what to rebuild

Every historical component should receive one disposition after its evidence is reviewed: retain as an active component, wrap behind the new contract, retain as a reference or benchmark, archive as a superseded experiment, or reopen for a specific unresolved hypothesis. A preserved experiment can be valuable even when it is never deployed again.

The migration inventory and the framework roadmap should share identities and references, but not the same completion criterion. Full preservation asks whether the historical asset survives with sufficient context. Product selection asks whether the asset earns a place in the forward architecture.

### A proposed historical evidence ledger

For each earlier bakeoff or integration, capture the original question, exact implementation, inputs, corpus, versions, configuration, output artifacts, metrics, failure observations, and decision at the time. Include whether that decision was provisional or accepted. Do not reconstruct missing performance numbers from memory or nearby experiments.

The ledger should answer five practical questions:

1. What did the experiment actually test?
2. Which source population and question set did it cover?
3. Which result can be reused without running it again?
4. What changed that could invalidate that result?
5. Which single unresolved decision, if any, justifies a new test?

When an old result is relevant but not comparable, preserve the finding as a hypothesis or design constraint. For example, evidence that visual retrieval helped one set of scanned pages justifies testing a visual lane on analogous Fresh 9 pages; it does not establish the same gain on every AWS question.

### Conditions for rerunning an experiment

Rerun only when a material factor changed or the old run cannot answer a current decision. Material factors include corpus revision, question population, parser or model revision, resource constraints, privacy boundary, or a defect in the earlier test. A new framework release by itself is not an automatic reason to restart the entire evaluation history.

One baseline replay may be needed to establish that the harness is functioning. After that, targeted regression tests should be preferred over repeated full checks. Record the reason for each rerun and the decision it is intended to inform. Stop when that decision has enough evidence.

## 5 Open source options and integration roles

The options below were checked against primary project or provider documentation on 12 October 2026. Capabilities describe available mechanisms, not measured NavyWeld performance. License descriptions concern the named code or weights only; optional models, databases, parsers, and hosted services need their own review. Candidate names alone are not adoption recommendations.

### Choose among roles before choosing products

| Role | Leading options to consider | Proposed disposition |
|---|---|---|
| Coherent multimodal retrieval stack | LightRAG with integrated RAG-Anything; RAGFlow | Compare one or two complete paths, rather than assembling both |
| Evidence and knowledge application | Utopia | High-value architecture-fit experiment, especially for review and temporal facts |
| Document parsing | Docling; PaddleOCR PP-StructureV3; PaddleOCR-VL | Default plus a bounded challenge on difficult pages |
| Typed extraction | Docling Graph; selected KAPipe components; minimal schema extraction | Compare on accepted relations and qualifiers, with a fixed parser |
| Graph retrieval or reasoning | AWS GraphRAG Toolkit; KAG; Neo4j GraphRAG | Defer until relational hard cases justify the added system |
| Visual retrieval | Existing ColPali/ColQwen lineage; later NeoMME or other qualified challengers | Preserve the baseline; reopen only the failure-specific comparison |
| Typed routing or support decisions | Hosted Jev; self-hosted CLM; current deterministic or LLM rules | Optional shadow experiment behind one interchangeable interface |
| Engineering coordination | OpenRig and any existing code-navigation tools | Separate development tooling; no NLQ runtime dependency |
| Interchange and cross-project discovery | Vault-LD, OKF, DDF, Caesar, Graphify | Historical reference or deferred experiment pending identity and need checks |

### Utopia

Utopia is a particularly relevant reuse hypothesis because its application already addresses editable ontology, evidence-backed facts, review, and temporal queries. Its repository describes a Rust application with PostgreSQL, Tantivy and pgvector retrieval, reversible entity merges, citations, and append-only decision history. It is Apache-2.0 and an early application release, rather than an embeddable library. Scanned or image inputs require additional parsing or vision dependencies. These facts make it worth a bounded architecture-fit test, not an immediate replacement. [Utopia project](https://github.com/deeplethe/utopia)

Its MCP interface has scoped tools for document search, entity facts, and valid-time or knowledge-time queries. Search excerpts and full-document responses have documented limits, and historical search may have incomplete recall. An adapter must therefore verify that the necessary evidence remains retrievable, particularly for long qualifiers or linked table notes. [Utopia MCP documentation](https://github.com/deeplethe/utopia/blob/main/web/src/docs/mcp.md)

Its current maturity also matters: forward-only schema migrations and roadmap items for SSO, backup/restore commands, and larger-scale benchmarking should be reviewed before any production adoption. Do not assume those operating controls are already available. [Utopia project roadmap](https://github.com/deeplethe/utopia)

The proposed seam is an isolated Utopia base populated from a small, approved canonical evidence export. Test round-trip fidelity, temporal distinctions, qualifier retention, contradiction handling, entity linking, citation resolution, and review effort. Passage-level citations must be mapped back to NavyWeld's exact page, region, or cell anchors. The test should show a material reduction in custom work or a measured capability gain before a broader replacement is considered.

Operationally, account for both database and file/index persistence. The current Compose example pins a release candidate and PostgreSQL with pgvector; deployment details should be pinned and reviewed independently of the moving main branch. Security guidance calls for source-level read-only access and least privilege. [Compose configuration](https://raw.githubusercontent.com/deeplethe/utopia/main/docker-compose.yml), [security guidance](https://github.com/deeplethe/utopia/blob/main/SECURITY.md)

### LightRAG with RAG Anything

Treat LightRAG and RAG-Anything as one combined candidate in the current landscape. LightRAG's current documentation describes native RAG-Anything integration with multimodal parsing, graph and vector retrieval, query modes, contexts, and citations. Parser and model choices remain configuration decisions. Both repositories use MIT licenses. Default lightweight stores are suitable for small tests; a production storage choice still needs justification. [LightRAG](https://github.com/HKUDS/LightRAG), [RAG-Anything](https://github.com/HKUDS/RAG-Anything)

The hypothesis is that linked text, table, and figure representations improve the difficult multimodal questions while reducing orchestration code. The critical unknown is whether the combined path preserves exact evidence anchors and qualifiers. A generated graph and a citation feature do not establish either. Compare it with the existing hybrid path under matched evidence and answer budgets before crediting graph complexity.

### RAGFlow

RAGFlow is a plausible integrated analyst baseline because it combines ingestion, DeepDoc parsing, retrieval, and a user-facing workflow. Its Apache-2.0 repository documents a multi-service deployment and separately configured models. Current main references a release candidate, so a trial should pin a reviewed release. [RAGFlow](https://github.com/infiniflow/ragflow)

Its proposed role is to test how much of the practical analyst workflow can be reused. Measure time to ingest, inspect failures, review citations, update documents, and recover state. Treat its domain-relation fidelity as unknown. It should be an alternative integrated path, not an additional permanent layer on top of LightRAG and Utopia.

### Docling and Docling Graph

Docling provides structured parsing, layout and table handling, OCR, and a document representation with JSON export. Docling Graph adds schema-guided extraction into validated objects and directed graph output, with documented provenance and grounding mechanisms. Both code projects use MIT licenses. They are components that could support a thin NavyWeld adapter, rather than a complete NLQ application. [Docling](https://github.com/docling-project/docling), [Docling Graph](https://github.com/docling-project/docling-graph)

The prior Docling parser result and the unexecuted Docling Graph arm must remain separate. A future Docling Graph test asks whether a typed schema can retain relationships, units, qualifiers, and source grounding with less project-specific code. Schema validation checks shape; domain correctness still requires source review. Test footnote attachment and precise supporting cells explicitly.

### PaddleOCR

PaddleOCR's Apache-2.0 project offers PP-StructureV3 and the PaddleOCR-VL path as different document-processing options. Current documentation distinguishes PP-StructureV3's finer coordinates, including text and table-cell coordinates, from the visual-language series. [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)

Compare these only if the chosen default parser misses important layout or evidence. Use the same difficult pages and normalized evidence contract. The earlier unavailable PaddleOCR-VL run was a runtime result, not a quality rejection. A later trial needs a supported, authorized environment before it can make comparative quality claims.

### KAPipe

KAPipe is an Apache-2.0 research toolkit with entity, relation, proposition, graph, retrieval, and QA components. Its documentation explicitly emphasizes research and warns of breaking changes. Its dependency footprint is broad, so isolate any experiment and inspect the exact models and licenses it invokes. [KAPipe](https://github.com/norikinishida/kapipe), [dependency specification](https://raw.githubusercontent.com/norikinishida/kapipe/main/pyproject.toml)

The most useful experiment is one component, such as proposition extraction or template-based evidence reporting, behind the canonical evidence adapter. Its associated research supports investigating extraction quality and grouping granularity, but those are findings on the paper's benchmarks. They provide no NavyWeld accuracy claim. [KAPipe research paper](https://aclanthology.org/2026.tacl-1.29/)

### Graph retrieval and reasoning alternatives

AWS GraphRAG Toolkit provides distinct lexical-graph and bring-your-own-knowledge-graph paths. Its Apache-2.0 toolkit supports multiple graph and vector stores; it is not inherently a Neptune-only deployment. Use it as a challenger only when retrieving over the retained graph or source statements solves a demonstrated problem. It does not remove the need for document parsing and evidence grounding. [AWS GraphRAG Toolkit](https://github.com/awslabs/graphrag-toolkit), [toolkit documentation](https://awslabs.github.io/graphrag-toolkit/)

OpenSPG KAG combines schema-constrained construction, knowledge and chunk indexing, conceptual alignment, and guided hybrid reasoning. Its Apache-2.0 implementation carries an engine and ontology commitment. Its best prospective role is a narrow challenge involving typed constraints, calculations, or genuinely relational questions. [KAG](https://github.com/OpenSPG/KAG)

Neo4j GraphRAG's KG Builder supports schemas, entity resolution, and graph construction, but its documentation marks the builder experimental. The library and database have separate licensing considerations. Consider it if Neo4j-backed typed graph queries are an actual requirement; a compelling graph display alone is insufficient. [KG Builder documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html), [library license](https://github.com/neo4j/neo4j-graphrag-python/blob/main/LICENSE.txt)

Do not run all three as a default graph bakeoff. First demonstrate the failure that graph structure is expected to fix, then choose the one closest to that requirement.

### Jev and CLM

Jev belongs in an optional decision-provider comparison, rather than the framework or multimodal reader comparison. The official TypeSafe API accepts text or JSON state with typed questions and returns choices or distributions. Jevai.org identifies itself as a community hub; official model and API claims should come from TypeSafe. [Official introduction](https://docs.typesafe.ai/introduction), [model documentation](https://docs.typesafe.ai/models), [community site](https://www.jevai.org/)

Candidate uses include choosing a query route, ranking passage usefulness, or checking support for an already formed claim. Keep exact arithmetic, units, dates, authorization, and admission decisions in deterministic or explicitly reviewed paths. The provider documents option-order and other sensitivity risks; a returned confidence value is not independent evidence of correctness. The citation cookbook combines literal quote checks with semantic support checks. [Model limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [confidence documentation](https://docs.typesafe.ai/confidence), [citation cookbook](https://docs.typesafe.ai/cookbooks/citation_check)

CLM is an Apache-2.0 self-hostable research alternative for the same decision interface. Its documented implementation uses a frozen encoder with learned heads and a GPU-backed serving path. The model card makes the candidate-set dependence of its probabilities important. Native multimodal support is not established as a current capability. [CLM repository](https://github.com/Contrastive-LM/CLM), [CLM model card](https://huggingface.co/Contrastive-LM/CLM-v0.1-8B)

A proposed screening test would use approximately 150 to 300 human-labeled atomic decisions, with a document-disjoint holdout, and compare existing rules, the current LLM gate, and at most one of Jev or CLM initially. Measure false support, false rejection, calibration, selective risk, option-order robustness, latency, and total cost including fallback. This sample is a screening experiment, not certification of a low error rate. Zero observed false accepts would still carry uncertainty.

Keep the test shadow-only. Do not send corpus snippets to Jev without approval of external processing; enterprise retention terms require a separate check. CLM avoids that particular transmission when fully self-hosted, but GPU and operational cost may outweigh its benefit at small volume. Neither component should decide that a provisional domain claim is accepted. [TypeSafe enterprise information](https://typesafe.ai/enterprise)

### OpenRig and other engineering tools

OpenRig is development coordination tooling: a local daemon and persistent work queues around coding harnesses. Its Apache-2.0 project and architecture describe a role in coordinating engineering work, not document retrieval or domain ontology. Security guidance expects a trusted machine or private network and includes executable hooks and workspace configuration in its installation behavior. [OpenRig](https://github.com/mvschwarz/openrig), [architecture](https://github.com/mvschwarz/openrig/blob/main/ARCHITECTURE.md), [security](https://github.com/mvschwarz/openrig/blob/main/SECURITY.md)

If considered later, compare it against the existing workflow on a matched, low-risk adapter change and independent QA. Measure cycle time, defects, human interventions, and model cost. Agent count is not a success metric. This optional development experiment should not delay the first source-to-answer path.

### A proposed first shortlist

Use the existing supported hybrid path as the reference. Start with a brief Utopia contract-fit check because its evidence, review, and temporal model align with the enduring requirements. If it can round-trip the minimum evidence safely, it can be one primary challenger. LightRAG with RAG-Anything is the strongest contrasting multimodal integration hypothesis. RAGFlow is a reserve challenger when an integrated analyst workflow matters more than temporal knowledge management, or when one of the first candidates fails the basic contract-fit check.

This is a recommended order for review, not a mandate to install three new stacks. Docling, Docling Graph, PaddleOCR, and KAPipe remain component choices within controlled experiments. Jev, CLM, graph engines, and OpenRig stay deferred unless the earlier phases reveal the failure they could address.

## 6 The first vertical slice

### Proposed outcome

Choose one narrow AWS topic represented in the accepted material and a small set of real user questions that require more than keyword lookup. The slice should include a text definition or rule, a table with meaningful headings or footnotes, a visual or diagram question if the selected sources contain one, a cross-reference or qualifying condition, a revision-sensitive question, and at least one deliberate insufficient-evidence case.

The selection should be driven by available accepted evidence rather than by a framework's best demo. If an expected modality is absent from the selected topic, say so and select another bounded source set rather than inventing a multimodal claim.

### Proposed test set

A practical first slice is approximately 12 to 20 questions, subject to an evidence review before freezing. This is a suggested planning scale, not an approved acceptance threshold or a statistically representative estimate of whole-corpus accuracy. It is large enough to expose different failure types and small enough for careful manual review.

Use a development subset for diagnosing adapters and a held-out subset for the final comparison. Keep at least one qualifier, version, and negative-control challenge out of development. The same questions and gold evidence should be used across candidates. Any question removed or changed after seeing results needs a recorded reason and a rerun of the affected comparisons.

The first slice should reuse eligible AWS baseline questions and accepted source anchors where possible. Newly authored questions should be marked as new and reviewed for answerability. Do not fold the historical FULL denominator into this slice or present an outcome as an improvement against an incomparable baseline.

### What success would look like

A reviewer can follow an answer from each material claim to the exact source revision and relevant evidence. The system retains the condition or exception that makes the answer true. It can distinguish source conflict from missing evidence, abstain on unsupported questions, and recover from a parse or indexing failure without losing source identity.

The chosen stack can be rebuilt from a documented manifest, and a second reviewer can reproduce the evaluation procedure. The maintenance work is understandable enough that the project can own it after the initial experiment. These are proposed success conditions; the project owner should approve the actual release gate before work begins.

## 7 A finite comparison program

### Comparison discipline

Begin with one reference path and no more than two primary challengers. Keep parser, retriever, graph, and managed-service comparisons separate unless the decision genuinely concerns an integrated stack. Changing every component at once can produce a useful product comparison, but it cannot identify which component caused the difference.

Freeze the corpus, source revisions, question set, evidence set, model budget, and evaluation rules before the held-out run. Record unavoidable differences, such as a framework-mandated parser. Keep model choices aligned where supported. If two stacks require different models, report the result as an end-to-end stack comparison rather than a pure framework effect.

Use a single declared tuning round per candidate for the first selection decision. Additional work is justified only by a specific, bounded fix with a credible benefit. If a candidate requires extensive custom plumbing to enter the comparison, that effort counts against its maintainability advantage.

### Proposed comparison matrix

| Test | Hypothesis | Fixed inputs | Primary measures | Guardrail and stop rule |
|---|---|---|---|---|
| Framework baseline | A coherent framework can replace custom plumbing without losing evidence control | Same slice, source registry, accepted anchors, comparable model budget | Supported answers, complete citations, setup and repair effort | Stop a candidate if it cannot export source lineage or preserve revision separation |
| Parser challenge | A better layout path recovers evidence the default path loses | Same difficult pages and human-reviewed element references | Table structure, reading order, region accuracy, qualifier retention | Stop after the declared challenge set; no corpus-wide reparse without demonstrated benefit |
| Visual retrieval challenge | A visual lane adds useful candidates for figure or table questions | Same queries, candidate budget, page set | Needed-evidence recall, marginal latency and cost, citation resolvability | Retain only if benefit survives answer-level review and operational limits |
| Relation challenge | A scoped graph improves questions requiring explicit relationships | Same relation-dependent questions and accepted relation references | Complete evidence, relation precision, unsupported relation use | Stop if inferred edges are presented as accepted evidence or provenance is lost |
| Answer validation challenge | Claim checks reduce unsupported answers without excessive refusal | Same retrieval output and answer constraints | Unsupported claims, qualifier omission, false abstention | Reject any apparent gain driven by refusing the answerable set |
| Operations challenge | The candidate is simpler to maintain across updates and failures | Same reindex, update, failure, and recovery scenarios | Operator steps, recovery integrity, elapsed time, resource use | Stop if recovery relies on undocumented state or unbounded manual repair |
| Managed path challenge | A managed service offers a worthwhile operations tradeoff | Same approved corpus slice and evaluation package | Quality, total cost inputs, access controls, export and update behavior | Run only after data, spend, account, and service scope are approved |

The matrix is a planning template. It does not commit to running every row. Select only tests that can change the first architecture decision. Optional rows stay deferred until a concrete failure or operating need makes them relevant.

### Metrics and adjudication

Report question-level outcomes and the reasons for failure before summarizing them. For each answer, review factual support, coverage of the requested question, preservation of qualifiers and units, source revision correctness, citation precision, and appropriate abstention. Retrieval and parsing scores explain an answer result; they do not replace it.

Suggested measures include:

- **Evidence recall.** Whether all evidence necessary for an answer was available within the candidate budget.
- **Citation validity.** Whether the cited source and location exist and support the associated claim.
- **Qualifier preservation.** Whether the conditions, exceptions, units, and scope required by the source survive into the answer.
- **Unsupported claim rate.** The proportion of reviewed material claims lacking support in the authorized evidence.
- **Answerability behavior.** Supported answers on answerable questions, appropriate abstentions on unanswerable questions, and false abstentions.
- **Revision and corpus isolation.** Whether the answer uses the requested source population and avoids silent cross-revision substitution.
- **Operational effort.** Hands-on setup, diagnosis, upgrade, update, reindex, and recovery work, recorded alongside elapsed time.
- **Resource use.** Parsing and indexing compute, model usage, storage, peak memory, and observed query latency.

The initial sample is intentionally small. Avoid decimal-heavy rankings, unsupported statistical claims, or weighted scores that disguise a critical integrity failure. A critical source or citation error may disqualify a stack regardless of its aggregate score. Approve the critical-error definitions before looking at held-out results.

Use human review for material source and qualifier judgments. Automated checks can verify IDs, revision filters, citation locations, and schema constraints. A model-based judge may assist triage, but its judgment should not become the sole authority for domain acceptance.

### Decision rule

Prefer the simplest candidate that meets the approved evidence and answer requirements. A small quality advantage may not justify a large maintenance burden; conversely, lower setup effort cannot excuse incorrect citations or version mixing. If no candidate meets the gate, narrow the supported product scope or repair one bounded failure, then repeat only the affected evaluation. Do not choose a winner merely to finish the comparison.

## 8 Roadmap phases and decision gates

### Phase 0 Complete the active preservation handoff

**Purpose.** Finish the existing migration acceptance process on its current terms, including independent review and unresolved identity, discovery, dependency, and resource-binding questions.

**Outputs.** A reviewable source-to-destination mapping, preservation report, explicit exceptions, resolved or documented blockers, and a clear description of what has and has not been reproduced.

**Gate.** The authorized migration reviewer accepts the relevant preservation scope or records a decision on outstanding exceptions. This roadmap does not change that gate. Framework planning and read-only evidence inventory can proceed in parallel, but they should not compete for the migration's active execution capacity.

### Phase 1 Consolidate the reusable evidence

**Purpose.** Establish what the project already knows and which assets should travel into the new stack.

**Outputs.** Corpus and revision manifests; a historical bakeoff ledger; accepted evidence and ontology exports; a mapping of old IDs to current references; and a disposition for each relevant historical component. Include the provenance of each result and preserve separate test populations.

**Gate.** The project owner can identify the current baseline, the remaining unknowns, and the evidence available for the first slice without interpreting contradictory handoffs. Missing evidence remains an explicit gap rather than a guessed result.

### Phase 2 Define the evidence contract and freeze the slice

**Purpose.** Make the minimum project-specific requirements testable before choosing a framework.

**Outputs.** The minimal canonical evidence contract, question and gold-evidence manifests, critical-error definitions, a development/held-out split, and an approved comparison budget. The contract should cover source revision, anchors, status, qualifiers, and transform lineage.

**Gate.** At least one independent reviewer can locate every gold evidence item and understand the expected answer or abstention. The owner approves the proposed slice and decision criteria. Nothing requires a full ontology rewrite at this stage.

### Phase 3 Compare coherent framework paths

**Purpose.** Determine whether a framework can carry the whole narrow path with less custom work.

**Outputs.** A reference run, at most two challenger runs, an adapter inventory, a failure ledger, operational observations, and a recommendation with reasons. Record which work was framework configuration, supported extension, or custom code.

**Gate.** Choose one primary stack, retain the baseline temporarily if it remains the best supported path, or explicitly defer the decision because no candidate passes. Selection requires answer evidence and an operating-cost view, not feature counts.

### Phase 4 Add only the component that closes the observed gap

**Purpose.** Address the leading demonstrated limitation in the selected path, such as layout extraction, visual retrieval, or explicit relation retrieval.

**Outputs.** One bounded adapter or component experiment at a time, measured against the unchanged slice and a targeted challenge set. Reuse earlier bakeoff evidence before doing new work.

**Gate.** Keep the component only if it supplies an answer-level benefit or necessary reliability improvement that justifies its maintenance and resource cost. If the base stack already meets the approved gate, this phase can be skipped.

### Phase 5 Establish the narrow product baseline

**Purpose.** Turn the selected slice into a supported, repeatable service or application suitable for the approved users and data boundary.

**Outputs.** A reproducible build and run manifest, ingestion and update procedure, source and citation resolver, reviewed answers, observability, failure recovery, access controls, and a concise operator guide. The exact hosting destination remains a separate decision.

**Gate.** A second operator can ingest an approved update, run the evaluation, inspect a failure, and recover the service without reconstructing undocumented state. The release clearly states its supported corpus, question scope, and limitations.

### Phase 6 Expand toward the full AWS multimodal goal

**Purpose.** Extend coverage in controlled increments while preserving the original evidence standard.

**Outputs.** Additional question families, corpus or revision coverage, modality support, and domain relationships, each with new evidence and regression tests. Measure gains and regressions separately by question type and source population.

**Gate.** Every expansion has a named user need, accepted evidence, a bounded evaluation, and an operational budget. Broader coverage is earned through measured results. It is not inferred from the presence of a multimodal model or graph feature.

### Indicative effort and ownership

No calendar dates or delivery commitments are assigned here. The phases depend on the unresolved migration review, the actual corpus quality, available hardware and service accounts, and the amount of reusable evaluation evidence. Estimate effort after Phase 1 and after the slice is frozen.

Proposed roles are a project owner for scope and spending decisions, a domain reviewer for evidence and qualifying conditions, an implementation owner for adapters and runtime behavior, and an independent reviewer for selection and release evidence. One person may fill several roles, but the held-out answer review should not rely solely on the person who tuned the candidate.

## 9 Data ownership and the single source of truth

### Git

Git should carry versioned implementation, schemas or contracts, approved configuration templates, corpus manifests, evaluation definitions, decision records, and references to large evidence artifacts. Use commits and tags to identify the exact material behind an evaluation or release. Keep credentials and sensitive runtime configuration outside the repository.

Git need not contain every large binary or every transient index. It must contain enough durable metadata to resolve the source, identify the correct revision, rebuild derived state where feasible, and understand the provenance of the reported result.

### Project documentation and Space

A project page or Space can provide the human-readable overview, active decisions, current links, and review notes. It should point to the relevant committed definitions and accepted evidence rather than independently redefining them. A page summary is useful for navigation; it should not become an unversioned competing source of executable truth.

This roadmap is an advisory planning artifact, including when it is published to the approved Git and Space documentation locations. Publication does not create executable work cards, adopt the proposals, or supersede the current project instructions.

### Runtime

The runtime holds operational stores such as parsed artifacts, indexes, caches, graph projections, job state, and traces. These are derived or operational records with clear retention and rebuild rules. A runtime record that becomes accepted evidence must be promoted through a defined review path into a durable, source-linked record.

The important invariant is that the same question run can be traced across Git definitions, source assets, framework output, and the final answer. Avoid duplicate identifiers with unclear ownership. When a framework requires its own IDs, keep an explicit mapping to the canonical NavyWeld IDs.

## 10 Maintainability and operating cost

### Measure the cost of ownership

A framework can reduce initial build time while increasing the cost of debugging or upgrades. Record both. The operational review should include installation and configuration steps, supported extension points, dependency count, upgrade behavior, breaking schema changes, data export, index rebuild requirements, and recovery after partial ingestion.

Prefer a version-pinned, reproducible deployment over an unspecified “latest” installation. Keep the model and parser assumptions explicit. A large collection of optional integrations is not automatically a flexible architecture; every active integration adds another compatibility and security surface.

### Cost model

No credible project-specific total cost is available yet. Measure actual workload inputs before estimating monthly spend. At minimum, separate one-time ingestion or reindex costs from recurring storage, serving, model calls, and operational support.

The proposed cost worksheet should capture source pages and asset sizes; parsing and OCR throughput; embedding and reranking usage; model input and output usage; GPU or CPU time; index and graph storage; query volume; concurrent users; retention; and expected reprocessing frequency. Include the cost of failed jobs and revisions, not only a successful first import.

For managed services, include data transfer, region, minimum capacity or provisioned resources, service-specific model charges, and any always-on components. Compare total operating effort as well as provider charges. A free software license does not make a system free to operate.

### Performance targets

Choose latency, concurrency, freshness, and availability targets from the intended user workflow. An analyst review tool may tolerate a slower, well-grounded answer; an interactive production application may need tighter bounds. Do not impose a high-availability deployment on the first slice without a requirement.

Report latency distributions only when the sample supports them, and separate cold-start, retrieval, model generation, and validation time. Keep the time to ingest an update and the time to recover a failed job visible, since they often dominate the practical usefulness of a small system.

## 11 Security licensing and data handling

### Bound the data flow

Before sending source documents, page images, embeddings, or traces to a third-party model or managed service, identify the exact data, provider, account, region, retention behavior, and purpose. An architectural recommendation is not authorization to transmit the corpus. Some service choices may require new permissions, spending approval, or account agreements.

Keep access controls attached to the source and enforce them before retrieval as well as at the user interface. A citation should not reveal the contents or location of a source the requesting user cannot access. Derived embeddings and graph records can also expose information and belong in the data-handling review.

### Treat source content as data

Documents may contain text that resembles instructions to the application. Parsing, retrieval, and model prompts should treat that text as source evidence, not as authority to change tools, access controls, system behavior, or evaluation rules. Test a bounded prompt-injection example as part of the security review if the runtime will use model tools or external actions.

The first NLQ product should have a read-only answer scope unless a later decision explicitly adds actions. Retrieval of engineering or domain evidence does not require an autonomous agent that can modify repositories, send messages, or provision resources.

### Review the whole license chain

Check the selected framework license, model weights, OCR models, embedding and reranking models, connectors, bundled components, and any hosted-service terms. Repository licensing and model-use rights are separate questions. The roadmap should not assume that an open repository permits every deployment or redistribution scenario.

Record the exact release or commit and the license evidence used for the decision. Do not turn a current README badge into a permanent compliance conclusion. Source-document copyright and contractual use restrictions are also distinct from software licensing.

### Minimum operational controls

Use least-privilege service access, managed secrets, bounded logs, explicit retention, dependency review, and a tested backup and restore path appropriate to the chosen deployment. Log enough for evidence debugging without unnecessarily retaining full sensitive prompts or documents. A deployment choice should include a practical rollback plan and the ability to disable an unsafe ingestion or answer path.

## 12 Optional managed deployment paths

AWS, Google Cloud, and Databricks are possible later deployment or comparison choices. They are not approved purchases, new accounts, or new data destinations under this plan. Here, AWS A3.0 refers to the welding standard and domain objective; it does not by itself select Amazon Web Services infrastructure or authorize use of a cloud service.

Evaluate a managed path only when it addresses a real operating requirement: identity integration, network controls, scale, existing platform alignment, reduced maintenance, or a necessary service capability. Use the same evidence contract and evaluation slice so that a managed result can be compared meaningfully with the selected self-managed path.

The main questions are whether the service exposes precise source locations, preserves revision and access boundaries, supports the needed modalities and qualifying conditions, permits export of project-owned evidence and evaluation records, and has a cost profile compatible with actual usage. If service internals are opaque, state which claims can be verified externally and which remain provider-dependent.

Avoid a three-cloud exercise in the first selection round. Choose at most one managed challenger after the project owner identifies a credible destination and approves the data and budget scope. Defer the others as documented options.

### Specific managed options

**Amazon Bedrock Knowledge Bases and Bedrock Data Automation.** These are managed services distinct from the open-source GraphRAG Toolkit. Data Automation's conversion of multimedia to textual representations and native multimodal embedding retrieval are different experiments. Current API documentation describes parser fallback behavior; test whether fallback makes lost visual evidence visible rather than silently returning a text-only result. [Multimodal retrieval](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-multimodal.html), [prerequisites](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-multimodal-prerequisites.html), [parsing configuration](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_ParsingConfiguration.html)

**Google Cloud search and RAG with Document AI.** Separate the search application, ingestion/retrieval engine, and layout parser. Layout-aware chunks may help tables and lists, but they do not supply the welding ontology. Product names and integration limits are changing; review the selected endpoint, version, region, import limits, and data controls before a trial. [Layout parser integration](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/layout-parser-integration), [document parsing and chunking](https://docs.cloud.google.com/generative-ai-app-builder/docs/parse-chunk-documents)

**Databricks intelligent document processing.** Managed parsing can return structured elements, page identities, and bounding boxes; schema-based extraction is a separate step. This is a plausible challenger if the authorized documents already belong in the relevant Lakehouse environment. Provider-managed parser revisions, runtime and region prerequisites, and format-specific limits need explicit qualification. [Document parsing function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document), [extraction function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract), [document parsing workflow](https://docs.databricks.com/aws/en/agents/agent-bricks/document-parsing)

## 13 Engineering knowledge remains a separate system

Code and engineering knowledge can help an implementation owner find entry points, understand dependencies, map a feature to files, inspect a change, and preserve handoff context. Those are useful functions for the migration and future maintenance. They have a different authority model from AWS domain evidence.

Use separate namespaces and contracts for repository symbols, dependency graphs, runtime traces, design notes, and domain claims. An engineering graph can state where code implements a citation resolver. It cannot establish that a welding statement is correct. Likewise, a domain relation should not be interpreted as a software dependency.

If a historical engineering integration is retained, give it a bounded role such as read-only code navigation, change-impact analysis, or handoff indexing. Test it on that role. Do not let an attractive code graph enlarge the multimodal NLQ critical path or create a second general-purpose orchestrator.

## 14 Risks and the decisions they require

| Risk | Consequence | Proposed response | Decision needed |
|---|---|---|---|
| Preservation and modernization become one task | Migration never closes; every old component becomes mandatory | Keep separate gates and component dispositions | Confirm the boundary without changing existing migration commitments |
| Evidence anchors are lost in framework conversion | Answers cannot be verified or compared across runs | Canonical IDs and source-location adapters before broad ingestion | Approve the minimum evidence contract |
| Legacy 9 and Fresh 9 are silently combined | Results and revision semantics become misleading | Separate corpus manifests and mandatory run filters | Confirm the slice's source population |
| Inferred graph edges become accepted facts | Unsupported reasoning appears authoritative | Separate candidate, provisional, and accepted relations | Define relation promotion authority |
| Quality gains come from changed test conditions | Comparison is not trustworthy | Freeze inputs and disclose stack differences | Approve the comparison protocol |
| Framework sprawl replaces custom-code sprawl | Upgrades and recovery become harder | One primary framework and justified supporting components | Select the primary path and explicit deferrals |
| A model judge becomes the only domain reviewer | Qualifier or unit errors pass unnoticed | Human adjudication of material source claims | Name a review role |
| Cloud or model use changes the data boundary | Unapproved disclosure or cost | Review data, recipient, account, terms, and budget first | Approve any specific service trial separately |
| Old results are treated as new accuracy | Product claims exceed evidence | Preserve populations, dates, manifests, and denominators | Approve how results will be reported |
| No one owns updates and recovery | A successful demo becomes an unreliable service | Second-operator exercise and documented procedures | Assign operating responsibility before release |

## 15 Decisions for the project owner

The next useful decisions are deliberately few:

1. **Approve or amend the architecture boundary.** Should frameworks own ordinary plumbing while NavyWeld retains canonical evidence, ontology, version semantics, questions, and evaluations?
2. **Choose the first slice.** Which AWS topic and source population should supply the first reviewable multimodal path?
3. **Approve a finite comparison.** Which reference path and at most two primary challengers deserve the first test budget?
4. **Set the critical integrity failures.** Which source, citation, qualifier, and version errors are automatic failures for the narrow product?
5. **Choose an initial operating context.** Keep the approved current environment, or separately authorize a bounded managed-service challenger with explicit data and spending scope.
6. **Decide the later migration relationship.** After current preservation evidence is reviewed, determine whether any future exit criteria should change. This is a new decision, not an implication of the framework-first proposal.

A reasonable initial approval would authorize only Phases 1 and 2 as planning and evidence consolidation, then require a concrete comparison plan before implementation or paid trials. The active migration remains governed by its existing instructions.

## 16 What should remain out of scope

For the first framework selection, defer universal multi-agent orchestration, a large automatically populated domain graph, simultaneous support for every parser and retriever, broad corpus expansion, three-cloud deployment, a full UI redesign, and rehabilitation of every historical integration. They may become useful later, but each needs a specific question or operating requirement.

Also defer unsupported claims of whole-corpus accuracy, automatic admission of provisional claims, silent rewriting of evidence IDs, and automatic ingestion of every preserved file. Preservation is broader than runtime eligibility. A file can be retained for history while remaining excluded from the answer corpus.

This document does not authorize executable cards, software changes, service launches, installations, or acceptance of a framework or provider. Its publication to the approved documentation locations is a review step. It provides a direction and the evidence needed for the next decision.

## 17 Recommended first review agenda

Use the first review to settle the shape of the work rather than to pick software by reputation.

- Confirm the current migration evidence and remaining independent-review questions.
- Confirm that preservation does not imply future deployment of every historical component.
- Review the historical evidence ledger and identify the reusable baseline.
- Select the topic, corpus, and question families for the narrow slice.
- Agree on the canonical evidence fields and critical integrity failures.
- Choose the small comparison roster and the information needed to estimate effort.
- Record deferrals so that optional integrations do not reappear as implicit requirements.

The useful result of that review is a short set of decisions and a bounded evidence-gathering plan. The next implementation step should then be obvious: prove one source-to-answer path with reliable citations, using the smallest maintainable stack that can do it.

## 18 Historical results and their reusable meaning

The following register is drawn from the owner's saved project review history. It is a historical evidence summary, not an independent rerun or a claim about the present implementation. The links are private owner references and may require the owner's account. No source-document payloads or licensed excerpts are embedded here.

### Executed work

| Historical record | Observed result | Reusable implication |
|---|---|---|
| 28 August MIL-STD-1689A Figures 1 to 5 | Docling 2.62/Heron, Tesseract 5.5 and MiniLM ran. Native evidence support 0.5333; Docling 0.3333; OCR 0.7667. BM25 R@1 0.90; dense 0.70; lexical plus dense 0.9333. OCR answer correctness 0.667 versus native 0.567 | A small development result supports keeping the strong native/OCR baseline. It does not settle parsing on AWS or Fresh 9 |
| 1 September corrected MIL-STD Figures 1 to 33 | Equal-weight fusion of frozen text/OCR/ColPali/ColQwen ranks: R@1 0.824324, R@3 and R@5 1.0, MRR 0.903153; 4 rescues and 8 harms | Fusion was classified harmful under that review. These are fusion metrics, not individual retriever scores |
| Same reader review | 27 of 35 reader cases failed after correct retrieval. Readers scored 39/74, 41/74 and 42/74 across the reviewed 3B, 7B and 8B options; 3B retained | More reader capacity did not satisfy the material-gain criterion. Diagnose reading and support separately from retrieval |
| 2 September native geometry extraction | 33 high-resolution assets, 99 regions, 1,723 observations; zero true line/path/curve drawing primitives from the scan-image-plus-text source; zero reader calls | Asset extraction and geometric observations are useful artifacts, not semantic accuracy results |
| 3 September specialist readers | North Micro and LFM2.5-VL processed the declared 33-figure/99-region scope; neither passed promotion. PaddleOCR-VL was unavailable after six attempts | No general quality verdict follows from a runtime-unavailable candidate |
| 3 September raster topology | On 10 gold figures, 40 nodes and 30 edges, T0 node/edge F1 0.1893/0.1348; T1 0.0545/0.0769. Unsupported-edge rates 0.8983 and 0.9091; no promotions | Keep geometry and semantic relations separate. The later retrieval/QA pivot should not inherit topology labeling as a new gate |
| 25 September AWS Annex A development integration | MiniLM 619 persisted text vectors and six ColPali A1–A6 crops were reported integrated and live. Separate A/B query exercises retained truthful partial and out-of-scope outcomes; 6/6 bounding-box cases passed | Preserve the accepted substrate and its scoped evidence. This is a development integration, not whole-corpus or production acceptance |

Sources: [28 August parser and OCR review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=06286b13-a355-408f-8888-1344cd3fed56), [1 September corrected retrieval and reader review](https://chatgpt.com/c/6a8f2ff8-2b50-83ea-ad9b-663fd320dcde?messageId=cc387d80-e496-4fc4-b640-487515ccd055), [native geometry record](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=2a326a8f-e374-466a-9c62-42e4c0956ac1), [specialist reader review](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=d5a5f7ff-022e-42ca-8c40-1b174d8f524f), [topology review](https://chatgpt.com/c/6a961f6a-5384-83ea-ad7f-2ff6841bec5b?messageId=934f39ac-5b36-426f-ae9d-9d9877384f7b), [Annex A owner execution report](https://chatgpt.com/c/6ab2874a-ca9c-83ea-a7eb-959b76dbd0d1?messageId=d976f6bc-285c-47da-9e73-139620c0bf0c)

The RRF metrics are reproduced as reported in the corrected review. Their denominator must not be inferred from the separately reported 104-question inventory, and they are not recomputed here. The reader populations and their denominators are separate.

### Invalidated and blocked comparisons

The September C1/C2 MAGE comparison was invalidated because its scorer treated PASS plus any evidence identifier as sufficient. The review found 15 C1 and 11 C2 wrong or incomplete answers counted as passes. The subsequent C1R review also exposed unsupported prose passing its checks. The reported original comparison scores must not be reused as accepted accuracy. MAGE's incremental value remains inconclusive, and the historical record does not establish an approved integration. This invalidation does not erase the separate accepted MiniLM/ColPali retrieval substrate. [C1/C2 invalidation](https://chatgpt.com/c/6ab6cd66-dbc4-83ea-aa6c-e46ba398ef93?messageId=01dc2fb3-8401-483d-bd4a-72dc393e719d), [C1R review](https://chatgpt.com/c/6ab82ed2-6f78-83ea-a62f-8f1154acd455?messageId=f08c584c-9ae4-4954-a96e-57ca5649c0eb)

The later Annex B extraction menu included minimal schema extraction, Docling Graph, and KAPipe. The reported actual status was A0 executed, A1 blocked by source-route authorization, A2 blocked by unavailable Docling Graph dependencies, and A3 blocked by the missing KAPipe adapter. These statuses are evidence about trial readiness, not comparative extraction quality. [Extraction menu](https://chatgpt.com/c/6abbd5f9-222c-83e9-b89b-96627cda82ad?messageId=86339d57-c4cd-4bfd-a20d-61da41a04025), [actual arm status](https://chatgpt.com/c/6abd15bb-99d4-83ea-a8d2-7eb431bf7af9?messageId=0e5d10ee-d034-4a18-821f-661eb7eb8a55)

### Research candidates with no established NavyWeld result

| Historical idea | Proposed failure to investigate | Disposition for this roadmap |
|---|---|---|
| NativeScope-style scope then rank | Relevant evidence is missed after a section or figure anchor is known | Small scoped-versus-unscoped test, with fallback for ambiguous or cross-section queries |
| Functional evidence groups | Definition, rule, figure, table and notes are split apart | Test grouping of existing evidence IDs before changing embeddings or adding a graph store |
| Trident-inspired modality diagnosis | Modality or fusion bias displaces the useful visual candidate | Audit current routes and fusion first; no training commitment |
| Elastic VDR teacher signals | Readable evidence is consistently misranked | Training deferred until a stable labeled failure set and budget justify it |
| NeoMME | A cheaper visual retriever might match the accepted path | Preserve as a bounded challenger; no completed NavyWeld result established |
| Qwen3-VL embedding and reranker; Gemini embedding; Nova multimodal embeddings | Portable dense retrieval and optional visual reranking | Separate provider indexes with shared canonical IDs; new data-route approval where needed |
| Mistral Large 4 reader idea | Fixed selected visual evidence is still read incorrectly | Historical proposed reader test only; current availability not independently established here |
| EmbeddingGemma 2 briefing | Compact cross-modal retrieval | Historical briefing only; identity, availability and performance claims require new verification |
| LangExtract | Text-span grounding | Possible bounded extraction component; no blanket multimodal role |
| PAGE-RAG or MAGE | Evidence navigation or retrieval policy | Deferred; MAGE needs a valid scorer and fixed-evidence baseline before any reopened claim |

These are recorded historical ideas. Their paper metrics and announcement claims are deliberately not imported as project results or current product specifications. Sources: [October retrieval research](https://chatgpt.com/c/6ac7925e-3490-83e9-9079-a3ab3d243e98?messageId=2301cf74-ac1e-5271-8082-7836f9dafd26), [functional evidence and teacher-signal discussion](https://chatgpt.com/c/6ac7925e-3490-83e9-9079-a3ab3d243e98?messageId=a451d235-5e5e-5fe4-a448-79e88072aa40), [embedding research briefing](https://chatgpt.com/c/6aba7db4-8904-83ea-ab42-1dc6d518aa38?messageId=cb37346c-9119-466a-929d-dd7e4411806e), [NeoMME planning](https://chatgpt.com/c/6a9f5b32-e62c-83ea-9041-b7f914b1544a?messageId=b8eb5fbc-33ad-4998-8666-62cc8b0dc91d), [portable embedding comparison proposal](https://chatgpt.com/c/6ab56c9d-57e4-83ea-9f65-39d3b8e3efcd?messageId=2bbc559d-6099-4dca-b4f5-0745a4332638)

### Knowledge infrastructure and interchange

Caesar was proposed for cross-project mechanism discovery and hypotheses. Vault-LD and OKF were proposed for a small identity, predicate, and provenance round trip. DDF was excluded from the earlier POC and retained as a possible federation or source adapter. Graphify and DDF were not acquired in the cited preparation review. Passing preparation tests did not establish model execution, retrieval, or graph integration.

Keep these ideas in the historical inventory. If interchange becomes necessary, test a small round trip for IDs, predicates, qualifiers, provenance, and loss reporting. If cross-project discovery becomes a real user need, evaluate it separately from the AWS answer path. Neighboring ontology-workbench or MEIA plans do not establish NavyWeld adoption. [Caesar proposal](https://chatgpt.com/c/6a770fca-df14-83ea-9328-41fcb16215b4?messageId=d420da2b-81a2-4c20-8e81-f88d9e0e7ced), [interchange and DDF scope](https://chatgpt.com/c/6a770fca-df14-83ea-9328-41fcb16215b4?messageId=f8aa1293-6511-4e19-93f1-f012266b83b3), [preparation review](https://chatgpt.com/c/6a74f5ed-5bdc-83ea-9ee7-06f8efc231ea?messageId=5ddd4cb0-0f84-4197-ad8e-b738828e48d2)

## 19 The earlier 26 option portfolio

The 26-item portfolio is preserved below as a map of decision surfaces. It was a proposal, not evidence that 26 trials ran, and it does not become 26 active tasks under this roadmap. Each item should be reopened only if it can change an identified decision. [Original portfolio](https://chatgpt.com/c/6a770fca-df14-83ea-9328-41fcb16215b4?messageId=f5ed7147-4229-4e98-87bf-707c7a463054)

1. Native extraction versus OCR or VLM extraction.
2. Specialist visual extractors.
3. OCR versus VLM versus their combination.
4. Page, crop, or region representations of figures.
5. Whole-table, row, cell, or cell-plus-footnote representations.
6. BM25, dense, or late-interaction text retrieval.
7. Flat chunks versus the source's native hierarchy.
8. ColPali and ColQwen visual retrieval.
9. RAG-Anything versus vector, lexical, or no-corpus-graph paths.
10. Global versus corpus-graph document routing.
11. Fixed page or element retrieval versus MAGE.
12. MAGE edge-family ablations.
13. MAGE action ablations.
14. MAGE budget frontier.
15. Offline processing everywhere versus on-demand visual inspection.
16. Reader performance on fixed gold evidence.
17. Rule, LLM, or hybrid entity extraction.
18. Generic versus typed relation extraction.
19. String, embedding, or LLM entity resolution.
20. Direct graph insertion versus validated claim promotion.
21. Graph contribution ablations.
22. All available graphs versus a minimal router.
23. RAG-Anything alone, MAGE on a known document, or a composed route.
24. Internal, OKF, or Vault-LD interchange.
25. Similarity, corpus graph, Caesar-style analogy, or random cross-project discovery.
26. Manual, single-agent, or multi-agent improvement workflows.

The forward sequence collapses this large portfolio into four decisions: can the evidence be parsed and anchored; can it be retrieved as a complete group; can it be read and answered faithfully; and can the chosen path be operated with less custom work? Fine-grained ablations are useful only when one of these decisions remains unresolved.

## 20 Evidence limits and document maintenance

Project facts in the opening sections come from the dated project handoff supplied for this planning task, including the control versions, pull request, commit, preservation figures, baseline populations, and accepted overlay counts. They are not newly rerun measurements. Historical sources are linked beside the findings they support. External capability sources were reviewed on 12 October 2026; versions, pricing, product names, licenses, and availability can change.

The companion document, `navy_weld_multimodal_lessons_learned.md`, explains the failure patterns and practices that should shape future multimodal RAG work. These two documents are advisory artifacts. Publishing them for review does not adopt their proposals or modify the active execution cards.

When a proposal is accepted, record the decision separately and update the relevant control artifact through the approved workflow. When a capability or historical claim is corrected, keep the correction and its source visible. The goal is a small, reliable set of project decisions supported by inspectable evidence, rather than an ever-growing list of possible integrations.

