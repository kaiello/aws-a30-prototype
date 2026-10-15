# Chunk vector reader compatibility and bounded evaluation — 2026-10-15

## Outcome and scope

The repository now installs an instance-local compatibility reader on `rag.chunks_vdb` in `src/indexer.py`. Existing numeric-list vectors can participate in LightRAG's cosine selection instead of triggering its error fallback. Native encoded vectors remain supported. No ingestion, embedding rebuild, store migration, provider change, site-package patch, or new dependency was performed.

This work is on `plan/declarative-manifest-20261015`, based on commit `89f4a529b05509d8dc45e439c858347abb2cf469`, alongside the existing uncommitted manifest/security work. Implementation and evaluation preceded publication. The owner subsequently approved publishing the reviewed manifest/vector-reader source, tests and documentation to `https://github.com/kaiello/aws-a30-prototype`, merging through required checks, and synchronizing local main. The PR and external closeout receipt record final commit state; PDFs, credentials, caches, databases and runtime answer receipts are excluded from the publication changes.

## Confirmed failure and minimal repair

Installed `lightrag-hku 1.5.7` calls `get_vectors_by_ids` from `pick_by_vector_similarity`. Its Nano reader unconditionally applies Base64 decoding to resident `vector` fields. The existing 164-row `storage/vdb_chunks.json` has numeric lists in those fields. The resulting `TypeError` is caught by the upstream picker, which returns a truncated candidate list without similarity ranking. Thus HTTP success did not establish a successful vector-selection step.

`src/vector_reader_compat.py` adapts only the installed reader method. It preserves native pending-upsert, redo, delete, locking, client reload and lazy embedding behavior. Lists retain their stored precision. Encoded vectors use the native Base64 + zlib + native-endian float16 format. Both paths validate dimensions, numeric types and finite float32-representable values. Encoded input and decompressed output are bounded; malformed framing, padding, trailing data and truncated streams are rejected with non-sensitive errors. Native upstream picker behavior for genuinely malformed data is otherwise unchanged.

The installer is idempotent and binds only the existing chunk-store instance. It requires LightRAG **exactly 1.5.7**, the expected Nano class, and a reviewed executable AST fingerprint of its reader. An unreviewed dependency change raises an explicit error. The upstream method's MIT notice is retained in the adapter. Review the adapter when upgrading; do not bypass its guard or automatically migrate stored data.

## Regression and review evidence

- **44 vector-reader tests passed** against the actual installed Nano class and LightRAG cosine picker: original failure reproduction, both vector formats at production dimension 1024, numeric precision, malformed/bounded decoding, exact ranking, missing/deleted IDs, lazy pending embeddings, redo precedence, idempotence and dependency-source mismatch.
- **176 selected existing/manifest Python checks passed** through `tests/run_manifest_offline.py`; **4 JavaScript security checks passed**. These are separate runs, totaling 220 selected Python checks, not an assertion that every historical test was executed.
- Independent local code review found a missing `asyncio` import in the first adapter draft. A lazy-pending regression reproduced the issue, the import was added, and review found no remaining actionable issue. A separate evaluation audit checked the receipt and its per-question metadata.

An additional actual-factory wiring check constructed the production LightRAG instance against a temporary copy, initialized and finalized its real stores, and read all 164 resident vectors. Source and copied chunk-store hashes remained identical. It made zero provider requests and zero new embeddings; two cache-metadata HTTP attempts during model loading were blocked. The first sandbox attempt lacked the host tokenizer cache, and a subsequent stalled scratch process was bounded and stopped. The successful check used the existing host cache and a 120-second watchdog. This verifies factory/storage wiring, not the complete graph/answer pipeline.

Reproduce the isolated checks using the existing installed environment, with test output and cache directories outside the repository:

```powershell
python -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP/a30-vector-tests" tests/test_vector_reader_compat.py
python -B tests/run_manifest_offline.py
node tests/security_settings.test.js
```

## Frozen-question evaluation

The final audited run was `2026-10-15T18:59:45Z`–`19:00:42Z`. The 50 questions and targets were unchanged: benchmark SHA-256 `67752bd45700aa99cfb9133dcb72c3756209caa4eee0610e648c07cbc38923b9`. Raw receipts are in the task's `vector-evaluation-2/` directory, outside the repository; `report.json`, `summary.json`, `answers.json` and `reader.log` retain separate evidence types.

The paired reader experiment used the **same fixed pool of 164 resident chunks** and the same fresh, locally computed query embedding per question. It exercised the actual upstream cosine picker with the original reader and the fixed reader. It does **not** exercise production graph candidate construction or the entire application answer pipeline. A separate lane exercised the current custom hybrid retriever over its 266 contextual records and read-only SQLite registry, including cross-encoder scores on all 420 returned candidates across 42 positive questions.

| Strict canonical figure/table target metric | Original reader | Fixed reader | Current hybrid, separate lane |
|---|---:|---:|---:|
| Hit@1, out of 28 | 0 | 3 | 9 |
| Hit@5, out of 28 | 1 | 10 | 19 |
| Hit@10, out of 28 | 1 | 11 | 23 |
| MRR@10, denominator 28 | 0.0119 | 0.1839 | 0.4610 |
| Mean component time across 42 positives | 2.61 ms | 90.08 ms | 356.60 ms |

All **42 original reader attempts recorded errors and fallback**. All **42 fixed attempts recorded no reader error and matched a NumPy cosine-order oracle**, conditional on the shared decoder; independent byte/list fixtures separately test decoding. The original fallback is fast because it skips successful ranking. Reader timings exclude query embedding/model loading; hybrid timings include its own expansion/search/rerank. Fixed-order, single-pass measurements do not establish an end-to-end latency improvement.

Only **12/28 strict target questions have any canonically mapped candidate in the fixed resident pool**. Sixteen of the fixed reader's 17 misses at K=10 therefore reflect pool/mapping coverage; absence in this crosswalk is not proof that all semantic evidence is absent. The main denominator remains 28. Fourteen positive text-target questions lack independently labeled relevant chunk IDs and are ungraded for strict retrieval. Target-ID hits establish metadata retrieval, not diagram interpretation, full evidence recall or factual support. The current hybrid result is a separate current-state measurement, not a before/after improvement attributable to the reader fix.

The unchanged pre-retrieval gate accepted all 42 positive questions and abstained on all 8 negative controls. This establishes those gate cases only.

## Fresh local answers and remaining accuracy limits

The final run generated paired answers for the predeclared first ten positives (Q01–Q10): **20 fresh local outputs**, with no cached generated response reuse. It used the already installed local Ollama `qwen2.5:3b` model, digest `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`, temperature 0, seed 0, context 8192 and maximum 384 generated tokens. All 20 ended normally. The prompt used only the selected top five text chunks, without images. No cloud inference or new paid service was used. A preliminary protocol run also generated 20 local outputs; its receipts remain separately preserved in `vector-evaluation-1/` and are not pooled into the final metrics.

| Diagnostic on ten answers per lane | Original | Fixed |
|---|---:|---:|
| Existing keyword/qualifier/citation heuristic passes | 3 | 8 |
| Outputs with a parser-recognized citation | 3 | 7 |
| Unknown cited element IDs detected | 0 | 0 |
| Explicit target-ID mentions, six target-bearing questions | 2 | 5 |
| Mean local request time | 751.95 ms | 957.89 ms |

These diagnostic scores are **not factual answer accuracy**. Neither a recognized citation, a target mention, nor the legacy heuristic establishes claim entailment or correct claim-to-page pairing. The existing scorer can award passes without a parser-recognized citation. The frozen gold also contains page/target inconsistencies and incomplete multi-evidence labels; it was not edited to improve scores. No independent technical adjudication of these answers was performed. No 50/50 truth or full multimodal readiness claim follows from this run.

The local embedding model was `BAAI/bge-large-en-v1.5`, dimension 1024, revision `d4aa6901d3a41ba39fb536a557fa166f842b0e09`, device `cuda:0`. Installed packages: `lightrag-hku 1.5.7`, `nano-vectordb 0.0.4.3`, `numpy 2.2.6`, `sentence-transformers 5.1.2`. Embedding weights and reranker were reused locally. The repository still lacks a complete dependency lock/install manifest; the versions above record the tested environment.

A bounded rerun is explicit and writes only to a new external output directory. Omit `--answers-model` for retrieval/gate checks without generation:

```powershell
$env:PYTHONHASHSEED='0'
python -B -u -X utf8 -m eval.vector_compat_evaluation --output-dir '<new absolute directory outside this repository>' --answers-model 'qwen2.5:3b' --answer-limit 10
```

The evaluator rejects a pre-existing output directory, constrains SQLite to read-only, checks required local models, and records source/code/store fingerprints, observed errors, timing scope, model settings and answer provenance. It is a component evaluation tool, not a replacement gold truth scorer.

## Preservation, operation and next evidence

Final-run fingerprints confirmed the native/contextual vector stores, SQLite registry, text KV store, frozen benchmark, manifest/receipt, mapping JSONLs and evaluated code were unchanged during evaluation. Existing model cache writes from earlier unrelated loopback queries were preserved. No rebuild, licensed-PDF/source-extract upload, credential change, additional model destination or new database was introduced by the evaluation.

The identified idle task server on port 8001 was restarted to load the fix; the separate older server on port 8000 was preserved. Post-reload checks passed 114 actual HTTP checks (including 99 unique asset routes) and production metadata checks for 73 valid element IDs plus eight invalid/group cases, without a cloud answer request. The earlier browser directory check passed before the reload; its isolated Chrome debugging endpoint was closed when a refresh was attempted, so it is not fresh post-fix browser evidence. Opening the app in the local Codex panel was queued. See the task handoff for the current PID and URL. Removing the installer call rolls back this code path without altering stored embeddings, but restores the confirmed numeric-list failure.

The next milestones remain coverage/mapping completion for the indexed evidence, independently adjudicated claim/citation and multi-evidence labels, and full production query trials including actual image input and difficult table/diagram questions. These are separate from resolving this vector-reader bug.
