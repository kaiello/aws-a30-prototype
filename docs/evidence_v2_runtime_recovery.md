# Local reader recovery and independent source comparison — 2026-10-21

**Historical runtime/semantic evidence; current work is setup only.** Follow
[Figure A1 setup readiness](evidence_v2_a1_setup.md). The five subsequently approved
DeepSeek cases and one alternative-model trial did not start before the owner
stopped evaluations. No inference is pending. Keep all failures below preserved;
they are not A1 competency-question results and must not trigger a replay.

**Strict pipeline follow-up:** One identical-input actual provider-free v1/v2
pair now ran. Five unchanged v1 generation inputs are explicitly blocked by the
configured DeepSeek cloud provider under the continuing local-only scope.
This is separate from the completed reader ablation below. See the
[exact blocker, executed pair and installed-model recommendation](evidence_v2_live_comparison_blocker.md).
No additional vision-model trial ran in that follow-up.

The runtime blocker is resolved. The bounded software implementation is concrete
and reviewable, but the original semantic gate is **not complete**. Keep all
changes local on `v2/evidence-engine`; `main` and local `v1.0` still point to
`24bac45465bcb5c9ea14663f7a669927d5d2ed00`. No commit, push, merge, publication,
branch deletion or tag movement was performed. V1 remains the default.

## Diagnosis and correction

The existing Ollama 0.40.4 listener was inspected without changing its settings.
Its startup log advertised `OLLAMA_CONTEXT_LENGTH=262144` and one parallel
sequence. That request context attempted a **28,991,029,248-byte** CPU KV-cache
allocation after projector offload retry and failed. At diagnosis there were no
loaded Ollama models; the 16 GiB GPU had approximately 11.6 GiB free. The failure
was not attributable to another loaded Ollama model. Other GPU users and
unrelated services were left alone.

The request-level **8192** override did reach the runner. Logs show
`n_ctx=8192` and a **1152 MiB** CUDA KV buffer, followed by rejection of a complete
**13279-token** input as larger than the context. The origin log recorded the
capacity rejection with no truncation. Earlier client receipts recorded HTTP
500; retain those receipts rather than claiming that the override was ignored.

The native request now uses **16384 context tokens**, **1024 output tokens**,
temperature **0**, and the same installed local model. A complete source-backed
crossmodal request succeeded with **13550 input / 839 output tokens** and all
three original PNGs. Loaded-model metadata corroborated context 16384 and
7,995,612,200 bytes of model VRAM. No images were resized, cropped or dropped.
No persistent setting, service, credentials, provider destination or model
installation changed.

Exact model: `qwen3-vl:8b-instruct`, installed before this task; manifest digest
`0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319`.
The digest was recorded from installed and loaded metadata after the experiment,
not as an independent per-call resolved digest capture.

## Recoverable software defects

- Route seed membership is normalized independently of source/continuation
  order. A fresh multi-definition packet no longer fails its own integrity
  check solely because the input inventory had a different insertion order.
- Safe HTTP diagnostics expose only recognized numeric context/allocation
  capacities or HTTP status, never raw provider bodies, reasons or private paths.
- A valid empty `claims` array is an insufficient-evidence abstention with
  observed usage/cost retained. Its original wrapper-error receipt was preserved
  and reprocessed offline; no model call was repeated for that repair.
- Uppercase table codes are matched case-sensitively inside prose. The word
  `is` no longer selects code `IS` for an unknown process. The original failed
  negative remains failed; its exposed **DEVELOPMENT** replay now withholds with
  zero claims. The paired known-code lookup remains two exact rows.
- Each original pixel payload has an adjacent source locator/caption. Generic
  reader instructions request complete panel coverage and distinguish drawn
  leaders from labels. Tests verify metadata adjacency and byte/order retention.
  This formatting change did not repair the exposed multipage semantic failure.

Each correction has a failing reproduction and passing software regression.

Final installed checks: **50 v2 software tests**, **827 guarded legacy Python
tests**, **44 installed native-reader tests** and **68 JavaScript checks** pass.
Final Python syntax and `git diff --check` pass. No browser UI was changed or
existing application service restarted for these checks. These software results
are separate from the failed original semantic gate below.

## Frozen experiment and independent grading

A private rubric was frozen before generation and independently checked against
native PDF text, table cell/header clips and all three source images. It contains
six questions, **13 required positive facts** and one missing-evidence control.
Rubric SHA256:
`073820aeaff0ffead75638a00af168d569e292bf3923de160ad8998a794f36dc`.
Expected facts, rubric labels and scores were never placed in model prompts.
Licensed facts, questions, raw outputs and detailed grades remain private local
files and ignored storage, not redistributable fixtures.

Three definition/alias/table cases and the negative control exercised actual v2
source-bound routes without models. Two visual questions compared identical
queries, complete source text and request options with zero images versus all
three original images. There were **four successful provider responses**, one
of which was a valid empty-claims abstention. The first successful crossmodal
pixel output was reused exactly, not regenerated. This is a **controlled reader
component experiment**, not unchanged v1 hybrid/LightRAG retrieval or a full
live v1/v2 integration comparison.

The [original aggregate](../eval/evidence_v2_source_reader_aggregate.json) is
frozen and separate from all development replays:

| Observation | Strict cases passed | Required facts correct | Required facts source-supported |
|---|---:|---:|---:|
| Original v2 source cases | 4/6 | 11/13 | 10/13 |
| Text-only visual reader | 0/2 | 3/8 | 2/8 |
| Image-bearing visual reader | 1/2 | 6/8 | 5/8 |

The original missing-evidence control failed. Its deterministic routing repair
passes separately as DEVELOPMENT 1/1, with no new model call. No original score
is replaced, rounded upward or relabeled fresh.

The image-bearing crossmodal answer passed **4/4 required facts** with correct
source support and no unsupported material extras. The multipage answer failed:
it omitted a required panel, used the wrong image-page binding for another
claim, and described a visual leader that was not supported. One explicitly
labeled development replay after the generic locator/panel instruction change
still failed the same rubric (**2/4 facts correct; 1/4 source-supported**).
Further model calls stopped. Valid generation and in-packet IDs remain separate
from semantic correctness; application-generated status stays `UNASSESSED`.

## Observed latency and cost

| Frozen reader observation | Prompt/output tokens | Service seconds | Local wall seconds |
|---|---:|---:|---:|
| Multipage text only | 4035 / 8 | 3.177 | 5.332 |
| Multipage with pixels | 12969 / 354 | 9.918 | 12.140 |
| Crossmodal text only | 4616 / 655 | 13.444 | 15.541 |
| Crossmodal with pixels | 13550 / 839 | 39.207 | 41.369 |

The last row includes a cold model load. Cache/load conditions and token counts
differ; this is not a causal latency comparison or SLA. The exposed development
pixel replay used 13270/353 tokens and 30.188 service seconds. Incremental local
API charge was zero; hardware, energy and engineering costs were not measured.

## Scope, acceptance and next decision

The local evidence model, routes, complete-packet transport, source table repair,
provider-free source extracts, actual image answering and reproducible controlled
reader comparisons are implemented. The runtime no longer blocks validation.
Do **not** state that all of steps 1–3 have passed semantic acceptance: the
original multipage answer remains incomplete, and unchanged live v1 integration
comparison is unperformed. Native production multi-sense coverage and unseen
held-out semantic accuracy remain unassessed.

There is no pending inference or permission denial. Further quality work needs
a deliberate bounded route: compare another already-installed vision model, or
build independently reviewed panel/claim support data with fresh holdouts.
Neither a larger context nor more blind retries establishes that quality gate.
No download, global-setting change or cloud fallback is needed to preserve and
review the current result. Rollback is the default v1 interface; keep the local
branch/tag and uncommitted work intact.
