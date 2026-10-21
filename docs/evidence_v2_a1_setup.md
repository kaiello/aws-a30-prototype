# Figure A1 backend setup - 2026-10-21

**Historical setup checkpoint:** the owner has since supplied 15 CQs. Their
preserved baseline and explicit deterministic graph-QA DEVELOPMENT results are
recorded in [QA 001](evidence_v2_a1_qa_001.md). The current dataset is no longer
empty. The original setup evidence below remains unchanged in scope; it is not
the later QA harness result or a reason to resume additional evaluations.

**READY_FOR_OWNER_COMPETENCY_QUESTIONS.** Setup and structural regressions pass.
The owner CQ dataset is empty. No A1 answer accuracy, semantic quality or model
comparison result is claimed. The current stopping point supersedes the earlier
B6/comparison plan; do not advance to another image or run inference now.

## Selected source and bindings

This unit is **Figure A1 - Master Chart of Welding and Joining Processes**,
canonical manifest ID `figure:figure_a1`, in AWS A3.0M/A3.0:2020. It is one image:

- `parsed/figures/Figure_A1_p88.png`, 1524 x 1973, 411,634 bytes.
- Zero-based PDF index **87**, viewer/PDF ordinal **88**, printed page **75**.
- PNG SHA256 `252c885b609a0855ce557416e6b4bf18d30e18b43a33b586903460e08fd4f83d`.
- Edition ID `doc:aws_a30_2020@205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`.

Table A1 is a different object on printed pages 69-70. Annex A is the parent
section, not an object named A1. Its applicability note is required alongside
the selected figure. No Table A1, A2, B6 or other image is included.

The manifest/PDF hash and validated original image establish source identity.
`source_identity_id` stays stable across graph views. `evidence_id` hashes the
complete selected content/view and can change with graph selection. Node IDs
also bind edition, source text/code and region. Source identity, graph selection,
packet transport and answer support remain separate contracts.

`evidence_a1_registry.py` opens existing SQLite with `mode=ro` and joins the exact
canonical element ID. Its old filename alias does not resolve the actual asset.
SQLite has no edition/hash columns; its bridge rows remain qualified candidates.
They are not copied into source facts. The authoritative edition/asset join is
manifest plus verified PDF/PNG SHA. No database schema, legacy row, graph or
vector store was rewritten. No new database or graph framework was introduced.

## Extraction and implemented retrieval

`evidence_a1.py` reads only the selected native PDF page. Native vector boxes,
row alignment, code columns and text geometry yield **99 nodes**: one root,
eight category boxes and 90 process/designation rows. The **127 edges** are:

| Edge | Count | Meaning |
|---|---:|---|
| `ENCLOSES_ROW` | 90 | Source rectangle encloses paired label/code; source-bound geometry |
| `CHART_CONNECTOR` | 8 | Physical root/category adjacency; no arrow direction inferred |
| `INDENTED_UNDER` | 29 | Layout candidate parent; not a reviewed semantic subtype |

Extraction excludes account/footer text and unrelated page content. Missing or
ambiguous box, row/code or connector geometry fails closed. Legacy merged
A1/A2/A3 summaries contain known incorrect process expansions and are excluded
from this new projection; they remain preserved for diagnosis.

Retrieval is implemented **before the reader**, not attached after text search:

1. Select the longest literal complete process names, case-insensitively, and
   exact case-sensitive designation codes.
2. Traverse every inbound enclosure/indentation parent recursively. Keep all
   candidate parents; do not guess one or truncate with top-k.
3. Retain the root, all category context and connecting edges. Record selected
   seeds/ancestors, qualifications and the full native graph hash/counts.
4. Bind that derived graph view to the canonical evidence and include the
   entire original image plus the required Annex A note.

Unmatched process wording returns `category_context_only`; that is not evidence
that an unnamed process was retrieved. Whole-image availability proves transport,
not that a question is answered. Literal two-subject comparisons within A1 use
their graph seeds. Other elements/pages, unsupported qualifiers, definitions or
acceptance-limit requests defer before reading. Bare A1 requests explicitly
distinguish Figure A1 and Table A1. Canonical reference/page records preserve
printed-page versus explicit PDF-ordinal interpretation.

Deferred modes: A1 semantic/vector ranking, synonym inference, reviewed semantic
subtype traversal, live SQL graph traversal, cross-edition and cross-image work.
The source-derived graph currently traverses in memory; SQLite is an identity
guard/candidate-link source. Owner CQs will show which additional modes, if any,
are needed. Source extraction and graph connectivity are not answer accuracy.

## Commands and owner input

Run from `C:\Users\kenai\aws-a30-prototype` using the existing environment:

```powershell
python -B -m src.evidence_a1_cli
python -B -m src.evidence_a1_cli --input eval/evidence_v2_a1_owner_cqs.json
```

These commands check source/graph/registry/image/packet structure. They never
initialize providers, read provider credentials, call a model or generate an
answer. The checked-in input is deliberately empty:

```json
{
  "schema_version": "a1-owner-cq-1.0",
  "source_element": "Figure A1",
  "questions": []
}
```

Future owner-supplied items have exactly `id` and `query`. IDs are unique,
1-128 characters using letters/digits/underscore/dot/hyphen, starting with a
letter or digit. Queries are nonempty strings up to 16,360 characters; the batch
limit is 100. No expected facts or agent-generated questions belong in this file.
The harness preserves owner text and adds only its declared Figure A1 context.

After the owner supplies questions, place private inputs under ignored storage
and prepare packets with a fresh output filename:

```powershell
python -B -m src.evidence_a1_cli --input storage/evidence_v2/a1_owner_cqs.json --output storage/evidence_v2/a1_owner_packets_001.json
```

This prepares evidence packets only; it still makes zero model calls and does
not score answers. Nonempty batches require private output. Outputs must be new
JSON files inside local `storage/evidence_v2`; linked directories and overwrite
are rejected. Licensed text/graph views/pixels and private receipts stay local.
Console output gives structural metadata and counts, not full graph/source text.

The existing query/CLI and guarded `/api/query` dispatch explicit A1 inputs to
this isolated loader when `evidence_version="v2"`; v1 remains default. Direct API
queries must name Figure A1. Request fields are `query`, `evidence_version:"v2"`
and `v2_reader:"extractive"`. Visual setup returns a complete packet with
`V2_READER_REQUIRED` (HTTP mapping 422) and no asserted answer. The existing
optional `v2_reader:"local"` sends original image bytes to configured Ollama;
it is not exercised or approved for execution under this setup-only stopping
point. No running app was restarted/reloaded; no live HTTP smoke is claimed.
The module CLI uses current checkout code immediately.

## Structural evidence and limits

Contracts: evidence **2.0.0**, A1 graph **a1-geometry-1.0**, owner CQ
**a1-owner-cq-1.0**. Tested existing host: CPython 3.12.7, PyMuPDF 1.26.5 and
pytest 9.0.2. The source-only optional dependency extra is `a1`; no install ran.

- **149 passed** in 1.80 s: v2 model/packet/interface/runtime plus A1 geometry,
  graph paths, editions/IDs, reference/page scope, read-only registry joins,
  private output safety and owner-input validation. Synthetic fixtures only;
  mocked reader checks are software behavior, not semantic evidence.
- **827 passed** in 18.00 s: existing provider/model/database-disabled offline
  regression runner.
- Actual `query.run_query` inventory input `Figure A1` reached the v2 loader,
  selected the nine-node/eight-edge category view, produced a complete two-item
  packet (one original image plus note), then stopped at `V2_READER_REQUIRED`.
  Provider-factory and vision guards recorded **zero attempts**. No answer claim.
- Protected PDF, manifest, original image, parsed chunks, SQLite, graph/vector
  stores and response-cache hashes matched before/after this actual path.
- A complete code-only wheel built offline from a fresh snapshot of all 38
  source and 10 evaluation modules using setuptools 80.9.0/wheel 0.45.1. All A1
  modules are included; no source assets, JSON/JSONL, database or environment
  files are included. SHA256
  `62e4ce7cabc2bf577f58b1b02a4a1cea14c8dee748236e9018f84dd77b94bee4`.
  This checks packaging, not a clean dependency install or a standalone runtime.

Private source-only receipts live under ignored `storage/evidence_v2/`.
Source-safe aggregate: `eval/evidence_v2_a1_setup_aggregate.json`. The earlier
agent-authored private A1 rubric is deferred, not an accepted owner CQ dataset.
There are **zero owner CQs and zero A1 accuracy results**. Model latency/cost and
factual support are unmeasured for A1. Runtime source/render bindings do not
certify semantic parentage or production readiness.

The five later-approved DeepSeek comparison cases and one local qwen2.5vl:7b
trial never started and are not pending. An already-starting local hybrid
observation was interrupted on the setup-only instruction: process exit 1,
no ranked-result receipt, no generation, no retry. Historical B6 results,
original failed rubric and replays remain recorded under their original scope.

## Local state and rollback

Annotated local `v1.0` and `main` preserve baseline
`24bac45465bcb5c9ea14663f7a669927d5d2ed00`; code remains uncommitted on
`v2/evidence-engine`. No commit, push, publication, merge, branch deletion or tag
move occurred. Rollback behavior by omitting the version or selecting v1. Keep
the dirty checkout, tag and local evidence intact. Steps 1-2 were completed
locally; original step-3 semantic/release acceptance remains incomplete. The
latest requested setup stopping point is complete and awaits owner CQs.

## Exact local changed files

The complete local step-1-to-current-setup diff contains 37 paths. Earlier slice
files remain included and are historical where their scope is deferred.

```text
README.md
docs/agents.md
docs/architecture.md
docs/aws_a30_standalone_prototype_plan.md
docs/goal.md
docs/dependency_contract.md
docs/evidence_v2_a1_setup.md
docs/evidence_v2_implementation.md
docs/evidence_v2_live_comparison_blocker.md
docs/evidence_v2_runtime_recovery.md
docs/evidence_v2_schema.md
eval/evidence_v2_a1_owner_cqs.json
eval/evidence_v2_a1_setup_aggregate.json
eval/evidence_v2_compare.py
eval/evidence_v2_development_reader_aggregate.json
eval/evidence_v2_fixture_comparison.json
eval/evidence_v2_integration_preflight.json
eval/evidence_v2_source_reader_aggregate.json
pyproject.toml
requirements-runtime.lock
requirements-v1.lock
src/evidence_a1.py
src/evidence_a1_cli.py
src/evidence_a1_registry.py
src/evidence_reader.py
src/evidence_sources.py
src/evidence_v2.py
src/query.py
src/web.py
tests/evidence_v2_fixture.py
tests/test_evidence_a1_cli.py
tests/test_evidence_a1_scope.py
tests/test_evidence_a1_sources.py
tests/test_evidence_reader_runtime.py
tests/test_evidence_sources_v2.py
tests/test_evidence_v2.py
tests/test_evidence_v2_interface.py
```
