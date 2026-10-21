# Evidence v2 contract (2.0.0)

The executable contract is `src/evidence_v2.py`; serialization uses dataclass
fields and `EvidencePacket.to_dict()`. It is additive to the existing v1 result.
The manifest owns source identities and locations. SQLite is read only and
supplies candidate concept identity links; neither a graph edge nor an index
score grants support. All in-memory lookup structures are derived.

| Record | Required fields and rules |
|---|---|
| Evidence | `evidence_id`, `edition_id`, `kind`, `locator`, `content`, `verification`, `required_ids`, `relationships` |
| Evidence ID | `ev2:` plus SHA256 of compact UTF-8 JSON `["2.0.0",edition_id,kind,locator,content]`, sorted keys, Unicode preserved, non-finite numbers forbidden |
| Edition ID | Canonical manifest document ID plus `@` and verified PDF SHA256; fixture IDs begin `fixture:` |
| Kind | `definition`, `table_row`, `figure_region`, `note` |
| Verification | `source_bound`, `candidate`, `reviewed`, `synthetic`. Synthetic is fixture-only. Source-bound means extraction identity, never semantic review |
| Locator | Canonical `element_id`; PDF zero-based index, printed label, declaration order and geometry/span where available. Printed pages and viewer ordinals are distinct |
| Definition content | `headword`, `sense`, exact `text`, aliases, qualifiers, exceptions, notes. The bounded source projector admits only native chunk spans reproduced in PDF text |
| Table row content | Ordered `headers` and aligned `cells` (list or exact-key dictionary), footnotes, qualifiers, exceptions, notes. Missing/empty required cells withhold the packet. Native cell/header geometry is retained in the source projection |
| Figure content | Caption, `asset_relpath`, SHA256, `image/png`, hash-bound `continuation_orders` and `required_evidence_ids` for required notes. All declared orders and required assets must be present; no inferred panel crop |
| Relationships | Qualified `ALIAS_FOR`, `ILLUSTRATED_BY`, `COMPARES_WITH`, `CONTINUES`, `CANDIDATE_CONCEPT`, `CANDIDATE_REGISTRY`, with `target_id`, `qualification`, `verification`. Candidate concept/registry identities must remain candidate and are outside the source ID hash; relationships do not certify entailment |
| Required closure | `required_ids` and content-bound required IDs. Figure continuation order is independently content-bound, avoiding cyclic evidence IDs. Source adapters derive the complete set from manifest/source, not client selections |
| RoutePlan | `kind`, ordered seed evidence IDs, sense alternatives, diagnostics. Kinds: definition, table, visual, comparison, ambiguity, missing |
| EvidencePacket | `schema_version`, query, route, ordered evidence, missing diagnostics, status: complete, insufficient_evidence, clarification_required |
| Reader output | Existing result keys plus `evidence_version`, `evidence_packet`, claim `evidence_ids`, timings, observed usage and nullable cost |

Definitions/aliases use whole-phrase lookup with exact-headword preference and
explicit ambiguity when a spelling maps to multiple senses/targets. Tables and
figures in this first slice require explicit canonical element labels. A
comparison requires at least two subjects; all their selected evidence and
dependencies survive. No vector or vendor-specific heuristic routing is added.
Table selectors use the longest exact whole cell phrase/code. Label-only
browsing retains the full table; unknown selectors withhold an answer.

The model boundary receives the full packet plus original PNG bytes in declared
order. The existing configured local Ollama adapter translates those image parts
into its final request's `images` array. It disables redirects and environment
proxies and permits only the configured loopback provider. It never reads new
credentials, downloads models, changes endpoints or calls the separate extraction
VLM as evidence of answering. Oversize/corrupt/missing assets withhold the whole
read; no downsampling or partial read occurs.

The native request bounds context to 16,384 tokens and generation to 1,024
tokens at temperature zero. Adjacent image labels carry source locators and
captions. Capacity failures are explicit, and HTTP diagnostics expose numeric
resource limits without raw provider bodies. A valid empty claims list is an
insufficient-evidence abstention that retains observed usage, not a transport
error. See [runtime recovery and semantic limits](evidence_v2_runtime_recovery.md).

Extractive claims retain qualifiers, exceptions, notes and footnotes and receive
`SOURCE_BOUND_EXTRACT` with assessment scope `source_binding_only` and
`semantic_validation=false`. Model claims must have nonempty text and supplied
evidence IDs; unknown bindings reject the response. Valid bindings remain
`UNASSESSED` with `validated=false`: citations and available pixels do not prove
the claim is supported, correct, or a complete answer to the question.

The schema does not certify arbitrary client-authored packets: evidence creation
and packet construction remain server-side. The source adapter verifies the PDF
hash and reproduces the bounded table derivative before admitting its rows.
Future schema changes require an explicit version, migration/projection and
same-input comparison; no persisted v1 store migration occurs here.

## Figure A1 source and graph view

The active setup projects one verified Figure A1 image and the required Annex A
note. It never slices the required continuations from a multipage object.
`source_identity_id` binds edition, canonical manifest element, source anchor and
asset SHA independently of retrieval. `evidence_id` remains the content/view hash:
its value can differ when the graph projection changes; it is not an image-only ID.
The locator also carries `canonical_element_id` and `source_identity_id`.

`chart_graph` uses `a1-geometry-1.0`: edition/region-bound node IDs, native
labels/designations, normalized PDF regions and qualified edges. `ENCLOSES_ROW`
binds paired text/code to a source rectangle; `CHART_CONNECTOR` records physical
undirected adjacency without claiming a printed arrow; `INDENTED_UNDER` remains
a candidate based on layout. These are not reviewed semantic `IS_A` assertions.

Literal full-name/code selection traverses every inbound parent before packet
construction. The packet retains all category/root context, matching process
seeds, all ancestors and edge qualifications, plus a hash/count of the complete
native graph. The complete original image always remains required. Unmatched
text yields `category_context_only`, not a claim of relevance/completeness for an
unnamed requested process. Two literal chart seeds can form a within-image
comparison; external images/pages and unsupported qualifiers defer before reading.

SQLite is opened read only for an exact canonical element-ID candidate join.
Legacy asset aliases and bridge descriptions never supply source facts; edition
and asset proof come from the manifest/PDF SHA. Native graph traversal is in
memory, not a claim that SQL graph traversal or semantic ranking was implemented.
See [setup commands and owner input contract](evidence_v2_a1_setup.md).

## Explicit deterministic A1 graph QA

`src.evidence_a1_cli --graph-qa` calls `src.evidence_a1_graph_qa` version
`a1-graph-qa-1.0`. The ordinary CLI still prepares packets only. This explicit
mode loads the full source graph and validates its single-image packet, then
executes generic descendants, parent-family, abbreviation, designation-expansion
or bounded-membership operations. It records queries, routes, resolved nodes,
direction/seeds/visited nodes/edges/qualifications, source/evidence/edition IDs,
raw answer, support state and latency. Model/provider are NONE, call count zero.

Full-category enumeration requires the full source graph and preserves all
enclosed rows plus candidate indentation, each once. A negative membership
requires a positive unique foreign-category enclosure and full-chart scope;
absence alone abstains. Source-bound chart-layout output retains
`semantic_validation=false`. Independent grading is separate and never changes
the source graph or candidate authority. Read [first QA results and limitations](evidence_v2_a1_qa_001.md),
including the diagnosed multi-process longest-match limitation outside the first
15 owner questions. No automatic further evaluation is authorized.
