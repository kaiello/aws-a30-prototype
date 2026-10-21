# Unchanged v1 integration comparison: executed scope and exact blocker

**Historical comparison record; superseded stopping point is A1 setup only.**
The owner later approved the five existing DeepSeek cases and one local trial,
then selected A1 and stopped evaluations pending owner competency questions.
None of those new calls started; none is pending. The old permission blocker
below describes its historical stage, not an unanswered approval request now.
No new A1 source is covered by the old five-case DeepSeek scope. The interrupted
local A1 hybrid observation has no completed ranked-result receipt and no
generation; it was not retried. See [current A1 setup](evidence_v2_a1_setup.md).

This follow-up uses the same frozen six source inputs. It does not substitute a
reader ablation for an unchanged v1 pipeline comparison. No cloud generation,
alternate-model trial, credential change, provider reconfiguration, model install,
service restart, commit or push was performed. V1 defaults and `main` are unchanged.

## Actual integration pair executed

One frozen alias/term-status question is eligible for v1's existing reviewed
source composer. Actual `query.run_query` executed both its default v1 path and
current v2 extractive path on that identical input. No retrieval, synthesis or
answer was replaced with a fake implementation. A fail-closed provider-factory
guard was installed for the check and remained **unreached: zero attempts**.

| Actual path | Result | Claims | Observed local wall time |
|---|---|---:|---:|
| Unchanged v1 reviewed composer | extractive / composed | 2 | 125.485 ms |
| Current v2 source-bound reader | composed / extractive | 2 | 536.326 ms |

Independent checking against the unchanged private source rubric passed both:
**2/2 facts correct, 2/2 source-supported and 2/2 correctly bound** per path,
with no unsupported extras or contradictions. This is parity on one case,
not evidence of v2 superiority. Timings exclude interpreter/import startup.

These are source-composed responses, not live model generations. One observation
does not establish a performance distribution or quality superiority. Detailed
private answers remain under ignored `storage/evidence_v2/`; the source-safe
[integration preflight](../eval/evidence_v2_integration_preflight.json) retains
execution status without licensed answer content.

## Five remaining inputs: why unchanged live generation cannot run locally

Actual provider-free v1 gates were evaluated for all six unchanged frozen
inputs. Five require model generation; they do not enter the reviewed composer
or a deterministic scope answer. Their normal unchanged v1 provider is:

- `DEFAULT_ENGINE=deepseek`.
- Configured root `https://api.deepseek.com`, model `deepseek-chat`.
- Existing key is configured; its value was neither shown nor changed.
- Gemini and Custom/OpenAI alternatives have no configured keys, and their
  configured roots are also cloud endpoints.

`src/query.py` selects this configured engine/key; `src/indexer.py` binds that
root/model and sends the generation request. This is v1's normal provider, not a
fallback. The continuing **local-only restriction** excludes those five outbound
generation actions. They were **not attempted**, not rejected by a provider/tool,
and are not pending. No API charge or latency for those unexecuted calls exists.

A read-only preflight exercised `validate_model_endpoint`: requesting the
existing local `http://localhost:11434/v1` against either the configured DeepSeek
or Custom/OpenAI root is rejected by the server endpoint allowlist. Silently
redirecting v1 would change its baseline configuration and invalidate the
requested unchanged comparison.

This is not a missing-index/dependency failure. The local contextual index is
present (266 rows), as is the native index (164 rows), with finite numeric
1024-dimensional vectors. SQLite and required tables are present; LightRAG
1.5.7 and the guarded native-reader source contract match. Manifest/source and
reviewed registry fingerprints validate. No index rebuild or re-embedding was
performed.

The smallest decision needed to complete the **unchanged** live comparison is
whether to authorize **five bounded requests to the existing DeepSeek endpoint**,
which would send their retrieved source context outside the computer. No new
credentials are needed. If local-only must remain absolute, unchanged baseline
generation cannot be compared: a separately approved, explicitly labeled local
v1 configuration would be a different experiment.

## Concrete one-model trial recommendation — not executed

Recommend the already-installed **`qwen2.5vl:7b`**, Q4_K_M, 8.3B parameters,
completion and vision capabilities, no remote backing. Installed manifest digest:
`5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.

The installed weights occupy **5,969,245,856 bytes (5.56 GiB)**. Metadata reports
28 layers and four KV heads; using a 128-dimensional head and F16 KV, context
16384 requires approximately **0.875 GiB KV**. Allow an estimated **7–10 GiB
total** for weights, KV, vision projector and runtime buffers. This is an
estimate, not a measured trial. The 16 GiB GPU currently has about 11.6 GiB free,
with no loaded Ollama model, so the bounded configuration has plausible headroom.
Do not run at its 128000-token model maximum. Different tokenization/image-token
allocation must be checked; preserve every required original image and reject
capacity failures without truncation.

Proposed budget: **one** exposed multipage question, unchanged prompt and frozen
rubric, all three original PNGs, temperature 0, context 16384, output limit 1024.
Record actual memory/tokens/time, then independently grade coverage, page
bindings and visual details. It must be labeled **DEVELOPMENT**, never a fresh
holdout or replacement for the failed original/replay.

This is a distinct trained checkpoint with general visual question-answering
capability. It offers a useful diagnostic alternative to qwen3's observed
semantic errors, not a guaranteed repair. It retains more capacity than the
installed 3B variant and needs less memory than the 9.6 GB Gemma weights. OCR-only
specialists prioritize text extraction, making them less suitable for this
general panel/geometry reasoning probe; the cloud-backed model is excluded by
scope. No alternate model has been loaded or invoked.
