# Local v2 evidence-engine receipt — 2026-10-21

**Current first-owner-QA receipt:** [Figure A1 QA 001](evidence_v2_a1_qa_001.md)
preserves the unanswered baseline and separately records 15/15 independently
source-supported deterministic graph-QA DEVELOPMENT answers. Model/provider NONE;
no source graph changes or model evaluation. Stop after this bounded set. The
original step-3 semantic/release acceptance remains incomplete; these results
do not turn historical failures into passes or establish generalization.

**Latest owner stop point: Figure A1 setup, awaiting owner competency questions.**
The [A1 setup receipt](evidence_v2_a1_setup.md) records current structural readiness,
graph retrieval, input schema and limits. No answer-accuracy/model comparison is
authorized to continue now. The five later-approved DeepSeek cases and alternative
local-model trial never started. Earlier source/model results remain historical;
setup readiness does not make the original step-3 semantic acceptance complete.

**Current follow-up:** The capacity blocker below is now resolved; see
[runtime recovery and independent source grades](evidence_v2_runtime_recovery.md).
The original source semantic gate remains failed/incomplete (4/6); runtime
success does not close step 3. Earlier failed executions below are preserved as
historical evidence, not a current claim that the model cannot load.
The [strict unchanged-v1 follow-up](evidence_v2_live_comparison_blocker.md) records
one permitted actual source-composed pair and the exact local-only blocker for
five configured cloud cases. Reader ablation is not substituted for integration.

Steps 1 and 2 are complete locally. Step 3 has a working, tested software slice
and source-backed extraction, but its real visual/model validation is blocked.
Do not label all steps 1–3 complete or infer semantic improvement from mocked
tests. No commits, pushes, publication, merges, branch deletion or existing tag
moves were performed.

## Baseline and scope

Repository origin was verified as `https://github.com/kaiello/aws-a30-prototype.git`.
The checkout was clean on `main` at
`24bac45465bcb5c9ea14663f7a669927d5d2ed00`. The new annotated local `v1.0` tag
points to that commit and documents its limitations; work is on local
`v2/evidence-engine`. `main`, `HEAD` commit and the peeled tag still have the
baseline SHA. The tag denotes an experimental baseline, not production readiness.

Baseline A2/A3 Markdown contained captions only. The main generated-answering
path supplied text to LightRAG; separate VLM extraction and browser image links
did not establish answer-time pixels. Existing reviewed terminology covered
only a bounded set, and prior failed semantic/fresh validation stays failed.

The slice adds no database, UI, external service or framework. The canonical
manifest remains authoritative; existing SQLite is read only, with name-matched
concept IDs explicitly candidate metadata. Indexes are derived. No source,
archive or checkout belonging to archived Navy Weld work was accessed.
The referenced MEIA snapshot could not be fetched through the restricted web
tool. No MEIA code or vendor/business heuristics were copied; only the supplied
typed-route/complete-packet concept was used.

## Implemented path

`src/evidence_v2.py` defines content/edition/locator-bound evidence, explicit
definition/sense, table, visual, comparison, ambiguity and missing routes, and
required evidence closure. Source-bound extraction is separate from reviewed
semantic support. Qualified alias relationships preserve conditions and source
targets; candidate illustration links remain navigation.
Derived SQLite concept links remain qualified candidate relationships outside
the canonical source-ID hash, so index identity changes do not change evidence
IDs. Table selectors match exact known cell phrases/codes and unknown selectors
withhold an answer; label-only browsing retains whole-table extraction.

`src/evidence_sources.py` projects six exact definition/alias entries (`root
face`, `root opening`, `root gap`, `bevel angle`, `back weld`, `backing weld`),
267 native table rows and three ordered B6 page regions plus the required Annex B
applicability-conflict note. Full-page scope is explicit; no certified panel
regions are claimed. Native source text is reproduced before definition
admission. No real multi-sense coverage beyond this source slice is claimed.

Targeted native extraction touched the three authorized A2/A3 PDF pages only:
A2 **133 rows**, A3 **134 rows**. The versioned derivative at ignored
`storage/evidence_v2/tables.v2.2.json` retains headers, individual cell/header
regions, source spelling/designation discrepancies and footnote assessment.
No additional native note lines were found in these bounded tables. The first
v2 derivative is preserved locally. Legacy Markdown, manifest, SQLite, graphs,
vectors and model configuration are unchanged. Cached rows must exactly match
a fresh deterministic bounded projection; omissions and forged source states
fail closed. Missing/stale PDF or derivative is an explicit failure.

`src/evidence_reader.py` consumes complete packets and actual original PNG bytes.
Hash/CRC/path/size/order guards run before inference. Content-bound continuation
orders and required notes prevent stripped dependency tuples from silently
making an incomplete figure readable. Generated claims must reference supplied
IDs and remain `UNASSESSED`; valid citations do not establish entailment.
Extractive claims retain headers, footnotes, qualifiers, exceptions and notes
with `SOURCE_BOUND_EXTRACT` / `source_binding_only` / semantic-validation false.

The existing query/CLI/guarded API use v1 by default. Examples:

```powershell
python -B -m src.query "Define root gap" --evidence-version v2
python -B -m src.query "Table A2 plasma arc welding" --evidence-version v2
python -B -m src.query "Compare root face and root opening in Figure B6" --evidence-version v2 --v2-reader local
```

The existing `/api/query` accepts `evidence_version: "v2"` and optional
`v2_reader: "local"`; invalid option types fail before query work. No browser UI
or existing server process was changed/reloaded. Local inference uses only the
existing configured loopback Ollama and installed `VLM_MODEL`; no new
credentials/destinations or cloud fallback were used. The native request's
`images` array receives every image in order. Runtime options bound output to
1,024 tokens and context initially to 8,192 tokens; the runtime follow-up raised
the per-request context to 16,384 without a global model/server change.
Larger evidence packets need explicit capacity validation;
byte delivery alone does not prove full model attention.

## Verification and comparison

- Existing provider-blocked suite after first integration: **827 passed**.
- Installed LightRAG 1.5.7 reader after integration: **44 passed**.
- Existing JavaScript checks: **68 passed** (4 credential, 22 geometry, 42 UI).
- V2 software checks: **24 core/reader/comparison**, **7 source-adapter**,
  **9 guarded-interface** cases. These are software tests using original
  redistributable fixtures; no licensed gold labels were changed.
- Offline wheel construction passed; **86 installed transitive package pins**
  satisfy **139 active dependency edges**, with no observed version/missing
  conflicts. See [dependency contract](dependency_contract.md).
- `git diff --check`, schema/inventory and final regression results are recorded
  by the final task report. No full ingest/re-embedding or automatic index rebuild
  was run.

The frozen [six-case receipt](../eval/evidence_v2_fixture_comparison.json) uses
identical queries for definitions/aliases, ambiguous senses, structured table,
multipage figure, crossmodal comparison and missing evidence. It executes actual
tagged-v1 query methods via the repository's AST-isolation pattern, with shared
synthetic retrieval and mocked synthesis/diagnostics. V1 receives the entire
shared fixture pool; this deliberately makes no actual-index ranking claim.
V2 emits composed/clarification/composed/generated/generated/insufficient
outcomes; the mocked v1 emits generated in all six. V2's visual and comparison
requests contain **two original PNGs each**; v1 sends a plain text prompt.
Both lanes retain complete required retrieval evidence under this injected pool,
so this is not a retrieval recall improvement claim.

Observed software latency in the final frozen fixture run was v1 **0.225–0.316 ms**
and v2 **0.142–6.897 ms**. No provider was called; mocked cost is zero and model
tokens/semantic correctness are explicitly unassessed. Reproduce with:

```powershell
# Export baseline source to a scratch file without changing the checkout first.
# Then point --v1-query at that saved file.
python -B -m eval.evidence_v2_compare --v1-query <saved-v1-query.py> --output <scratch-receipt.json>
python -B -m pytest -p no:cacheprovider --basetemp <new-scratch-dir> tests/test_evidence_v2.py tests/test_evidence_sources_v2.py tests/test_evidence_v2_interface.py
python -B tests/run_manifest_offline.py
python -B -m pytest -p no:cacheprovider --basetemp <another-new-scratch-dir> tests/test_vector_reader_compat.py
```

Source-backed provider-free checks returned exact extracts for root face, root
gap and Table A2; B6 had all three image pages plus note; the crossmodal packet
had seven evidence objects; missing Table A9 withheld. Projection of all 277
bounded objects took **432.166 ms** in the observed run. This verifies source
binding and packet availability, not real semantic answer correctness.

Final actual `run_query` calls after review fixes returned: root gap composed
two source-bound claims in **553.676 ms**; the exact Table A2 plasma-arc-welding
selector composed one row in **248.373 ms**; an imaginary missing process
withheld with zero claims in **261.004 ms**. These include source projection
and reader execution, exclude interpreter startup, and use no model/provider.
Final installed v2 suite: **40 passed**. Final guarded v1 regressions:
**827 passed**; installed native reader **44 passed**; JavaScript **68 passed**.
Final whitespace and Python syntax checks passed.

## Original live-model blocker and remaining gaps

The actual opt-in `run_query(..., evidence_version="v2", v2_reader="local")`
crossmodal request was attempted against configured `qwen3-vl:8b-instruct` at
the existing local service. It failed closed with HTTP 500 after **22.001 s**.
A bounded diagnostic identified model-startup out-of-memory while allocating a
**28,991,029,248-byte CPU KV cache**. A same-model retry with 8,192-token context
still returned HTTP 500 after **10.085 s**. No claims were returned. These are
failed executions, not permission denials or a pending model response. No token
usage or dollar-cost result was returned; cost remains null, not zero. Raw
licensed packets/answers and local receipts are ignored under
`storage/evidence_v2/`, never redistributable fixtures.

Remaining work is a usable local model/runtime followed by controlled real
v1/v2 source-backed reading and independent semantic grading, including image
details, qualified senses, table fidelity, completeness, latency and local
compute cost. No real source-backed v1/v2 model comparison was completed;
this task did not redirect the existing v1 provider defaults.
No fresh unseen semantic acceptance, whole-corpus coverage, artifact-hashed
clean-install reproducibility or production readiness is established.

## Exact changed files

- Existing documentation: `README.md`, `docs/agents.md`, `docs/goal.md`,
  `docs/architecture.md`, `docs/aws_a30_standalone_prototype_plan.md`.
- New documentation: `docs/evidence_v2_schema.md`,
  `docs/evidence_v2_implementation.md`, `docs/dependency_contract.md`,
  `docs/evidence_v2_runtime_recovery.md`, `docs/evidence_v2_live_comparison_blocker.md`.
- Existing interfaces: `src/query.py`, `src/web.py`.
- New engine: `src/evidence_v2.py`, `src/evidence_reader.py`, `src/evidence_sources.py`.
- New tests/fixtures: `tests/evidence_v2_fixture.py`, `tests/test_evidence_v2.py`,
  `tests/test_evidence_sources_v2.py`, `tests/test_evidence_v2_interface.py`,
  `tests/test_evidence_reader_runtime.py`.
- New comparison: `eval/evidence_v2_compare.py`, `eval/evidence_v2_fixture_comparison.json`,
  `eval/evidence_v2_source_reader_aggregate.json`, `eval/evidence_v2_development_reader_aggregate.json`.
  The follow-up adds `eval/evidence_v2_integration_preflight.json`.
- New package contracts: `pyproject.toml`, `requirements-v1.lock`, `requirements-runtime.lock`.

Licensed local derivatives/failed model receipts under ignored
`storage/evidence_v2/` are separate local outputs, not redistributable changes.

## Rollback

Use the default v1 interface (or `evidence_version="v1"`) and omit the local v2
reader. No persisted v1 schema migration occurred. Leave the local branch and
tag intact, preserve uncommitted work, and do not switch to `main` with this
work in progress. Reversal of file edits can be reviewed against `v1.0` without
deleting the new derivative, changing tags or running destructive Git commands.
