# Local API security boundaries

Scope: the 2026-10-15 security branch `fix/security-boundaries-20261015`. The owner
prioritized data and credential boundaries while keeping the existing production
UI/API contract. This work does not apply the supplied refactor ZIP, change models,
rebuild indexes, migrate databases, or claim improved NLQ accuracy or latency.

## Approved destinations and credentials

`DEEPSEEK_BASE_URL`, `GEMINI_BASE_URL` and `CUSTOM_BASE_URL` are server-approved API
roots. An omitted request `base_url` uses the selected engine's configured root;
an explicit override must match that root, allowing normal host case, default-port
and trailing-slash equivalence. Other hosts, ports, paths and schemes are rejected
before the web handler invokes retrieval or generation. Client construction repeats
the endpoint check, including for CLI callers. Request API keys and model names
remain supported, but cannot authorize a different destination.

Endpoints require HTTPS except for literal loopback HTTP services configured on
the server. Userinfo, query strings, fragments, encoded delimiters and dot segments
are rejected. The OpenAI-compatible query client disables redirect following and
environment proxy inheritance. This changes deployments that depended on automatic
redirects or `HTTP_PROXY`/`HTTPS_PROXY`; no operating-system/network setting is changed.
There is no new dependency installation: HTTPX is already required by the OpenAI SDK.

Prototype API-key fields stay in page memory and retain their existing request
field names. Valid legacy settings have key fields removed from localStorage before
settings are loaded. Reloading the page clears entered keys; nonsecret model settings
can still be saved. General model-output HTML and demonstrator HTML escaping remain
deferred by owner direction. Their existing XSS risk is not resolved by origin checks.

## Local API compatibility

The listener remains `127.0.0.1`, with the existing port option and JSON success
payload. Host must be the listener or `localhost` at that port. Forwarded-host
headers do not expand authority. Browser origins must match the page origin or an
exact origin listed in the server's comma-separated `A30_ALLOWED_ORIGINS` setting.
No wildcard CORS, persistent session credential or OS/network change is introduced.
Approved separate production UIs receive CORS headers and JSON POST preflight support.

Normal no-Origin JSON CLI requests remain supported. JSON Content-Type and a single
Content-Length are required; chunked query requests are rejected. Bodies are bounded
to 65536 bytes and query text to 16384 characters. Invalid or foreign requests fail
before query execution. This is browser-origin isolation, not authentication against
other processes on the trusted local machine. Do not expose this listener as an
authenticated multi-user service without separate authorization and design.

An absent required contextual vector store returns `RETRIEVAL_INDEX_MISSING`,
HTTP 503 and restoration guidance, with an empty answer/evidence payload. The CLI
prints the error and exits with status 1. The prerequisite is checked before
database reads or model initialization; no rebuild or provider call is attempted.
Corrupt stores and unrelated missing files are not classified as this error.

## Asset reads

PNG figure assets and PNG/Markdown table assets must be present in their respective
startup allowlist. Restart the server after authorized asset additions. Encoded names
are decoded to closure with a bounded depth; path separators, parent/drive paths,
Windows alternate streams, trailing-dot/space aliases and control bytes are rejected.
Every read checks the canonical root, regular-file status, symlink containment,
single-link status and opened-file identity before returning bytes. Rejected paths
receive a generic not-found response. Asset directories remain trusted project data;
these checks do not establish integrity against arbitrary concurrent in-place writes.

## Isolated validation

From this worktree, use a fresh scratch location for each pytest run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=<fresh-workspace-scratch> tests/test_security_boundaries.py
node tests/security_settings.test.js
```

Tests use fake retrieval/model objects, temporary asset fixtures and in-memory HTTP
handlers. An installed-SDK test uses HTTPX MockTransport to prove a provider redirect
does not forward the request. Hardlinks are tested with real temporary files;
symlink/junction escape resolution is simulated for platform-independent coverage.
On Windows the filesystem sandbox may prevent creating the link fixture; run that
isolated fixture with authorized local filesystem access rather than changing OS
security settings. No real model, provider, database, ingestion or listening server
is exercised. These are security regressions, not the paid gold answer benchmark.

Validation on 2026-10-15: 64 Python checks passed, the Node credential-settings test
passed, and all source Python files parsed. An independent source-free review
assessed the boundary contract and coverage; the implementation diff was reviewed
locally by the integrator. No independent source-code review or live NLQ run is claimed.

Git closeout validation also passed 89 isolated Python checks covering the security
suite, pre-retrieval rules, bounding-box registry and pure rank fusion. Model
construction, database connections, dotenv loading and application network access
were blocked; the only socket connection permitted was Windows asyncio's private
wakeup socketpair. The live retrieval and answer benchmarks were not run.
The missing-index regression includes real loader/query paths, CLI failure and
HTTP 503, plus nearby corruption and unrelated-file cases.

The final review compares against the preserved dirty owner-state baseline, rather
than attributing all pre-existing changes from HEAD to this task. The original checkout
was preserved during implementation. The owner subsequently authorized separate
commits for the previous owner changes and security fixes, branch publication,
PR review, and merge/sync/cleanup only when no material blocker remains. The PR
must record any confirmed blocker and the actual closeout result.

## Durable reference context

The owner-supplied Downloads copies were checked against these repository references;
their text matches, with only working-tree newline differences:

- [Framework roadmap](navy_weld_framework_roadmap.md)
- [Multimodal lessons learned](navy_weld_multimodal_lessons_learned.md)
- [Value and outcomes assessment](navy_weld_value_and_outcomes_assessment.md)

Retain project-owned source/evidence identity, exact anchors, qualifiers and review
status. Separate preservation, retrieval, reading, answer support and operational
evidence; a high aggregate score is not a substitute for the right proof. Prefer
bounded comparisons and repair demonstrated failures before adding architecture.
The roadmap remains speculative context, not execution authority. Data/control plane,
harness, ingestion, and retrieval accuracy/speed are the owner's next priorities;
this note does not authorize that broader implementation.
