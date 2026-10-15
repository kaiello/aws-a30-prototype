# Helper hardening implementation receipt

Historical helper-only receipt. Subsequent authorized live integration, local inference and the port-8001 restart are recorded in [the live terminology results](terminology_live_results.md); the checks and process state below describe the earlier milestone.

Date: 2026-10-15. Branch: `plan/helper-hardening-20261015`. Base HEAD: `fc918433b1ff61ccb405104bbcdb70577f149e09`. The owner's subsequent **start work** instruction authorized implementation of the three increments in [the inspected-folder plan](helper_hardening_plan.md), focused regressions and independent review. Work remains uncommitted and unpublished.

## Implemented contracts

1. **Geometry:** `figure_inspectors.py` returns copied, validated UI geometry. Only finite numeric `[ymin,xmin,ymax,xmax]` lists within `[0,1]`, with positive area, are accepted; booleans and strings are rejected. Valid coordinates survive unchanged. Bad/missing centers on valid boxes become midpoints. Invalid or duplicate-label geometry suppresses focus without discarding chip/query/source metadata. The browser validates before arithmetic, clears invalid focus even before an image loads, and contains only the derived minimum-size highlight rectangle. No cropper or PDF-region certification was added.
2. **Citations:** `standard_manifest.py` owns the shared whole-expression lexer and inventory-bounded numeric figure/table ranges using ASCII/en/em dashes. It preserves canonical IDs, first-seen order, exact per-element anchors, legacy dotted shorthand and existing lists, and adds semicolon lists/latest explicit prefix handling. Unknown, descending, mixed-prefix, malformed, unsupported or B16-group-crossing ranges remain unresolved as whole expressions. Ordinary prose after an ID remains valid. `pre_retrieval.py` uses the same boundaries in singular-only mode; ranges do not broaden enrichment. Printed-page ranges and claim/page pairing remain deferred.
3. **Terminology:** `terminology_mappings.py` exposes `parse_nonstandard_entry`, `merge_mapping_records` and `project_mapping_records`. It accepts supplied bounded entries, reviewed source spans and an injected manifest, preserves one ordered record per target with sense/process/conditional qualification, and requires verified compatible existing ontology IDs. Ambiguous top-level `or` requires explicit target boundaries; parenthesized `or` and hyphenated terms survive. Unknown/ambiguous evidence remains candidate data. New derived mapping IDs include source/sense/context; duplicate evidence is unioned without last-writer loss. Projection operates only on the supplied directed multigraph, preserves existing nodes/legacy edges, uses explicit edge ownership and canonical JSON, and rejects incoming cross-call target conflicts for operator review. Malformed records fail explicitly. `build_dual_graph.py` adds only a lazy opt-in wrapper; the full builder never calls it.

The helpers preserve the current public query/asset interfaces, scalar acronym expansion, existing node/chunk/evidence IDs and retrieval fixture. Existing cached graph rows alone do not meet the helper's reviewed-node contract. No corpus-wide glossary extraction or automatic terminology expansion was activated.

## Verification actually performed

All outputs below were recorded outside the repository in the task directory. Models, provider access and live database access were blocked in the guarded suite. GraphML serialization used a synthetic graph and temporary file only.

| Check | Before implementation / review correction | Final result |
|---|---|---|
| Bbox Python contracts | 33 failed, 14 passed | 47 passed, included below |
| Modal Node contracts | Invalid focus retained; later unloaded-image transition also reproduced red | 17 invalid + 4 valid/edge + 1 unloaded-image transition passed |
| Citation/assets/retrieval contracts | 33 failed, 49 passed initially; later prose regressions 4 failed/83 passed and shorthand regressions 8 failed/87 passed | 95 passed, included below |
| Terminology helper | Missing-module collection error (new feature absence); separate AST-isolated synthetic legacy insertion probe reproduced same-pair overwrite | 37 passed, included below |
| Terminology review regressions | 8 failed/26 passed; final missing-label cases 2 failed/35 passed | All addressed in final 37 |
| Combined guarded Python suite | Existing selected checks plus focused additions | **303 passed** |
| Actual installed native vector reader/picker suite | Existing suite, separate from stubbed runner | **44 passed** |
| Existing Node credential-settings suite | Existing suite | **4 passed** |
| Real isolated Chrome component fixture | Actual modal functions extracted from current `HTML_INDEX`, synthetic local SVG, isolated profile, no app queries | 17 invalid + 4 valid/edge + unloaded-image transition passed; no captured script errors |
| Valid catalog parity against HEAD | Entire current source/asset views, with network/database access blocked | All 62 figures' catalog/data/HTML/spatial outputs value-equal; 272 spatial chips retained |

Thus **347 selected Python checks** and **26 Node scenarios** passed in separate appropriate runs. This is not a claim that all historical tests or the paid gold benchmark were run. All 44 source/test Python files parsed.

One initial asset fixture incorrectly assumed Table D1 had no export. Inspection confirmed its existing candidate Markdown asset; the test was corrected to preserve D1 and assert no invented D2/D3 exports. Production asset behavior was not changed to satisfy that mistaken expectation. Cases already passing are characterization/parity evidence, not newly repaired failures.

Two independent local reviewers examined the scoped code/tests. Their findings led to reproduced regressions and fixes for prose/shorthand range boundaries, immediate focus cleanup, exact entry-span matching, cross-call conflicts, legacy-key ownership, and malformed containers/labels. Both reviewers reported no remaining actionable issue in the reviewed scope. Reviewers did not execute tests; the integrator ran the checks above.

The scratch legacy insertion probe remains a characterization of the unchanged old `key=rel` path. The new opt-in projection avoids that overwrite; this task does not claim to repair or rebuild existing semantic edges through the full builder.

## Preservation and operation

- Eleven protected fingerprints (native/contextual vectors, SQLite registry, text KV, both graph files, bbox registry, manifest/receipt, frozen gold and source PDF) matched the initial task baseline. No registry, PNG, PDF, manifest, gold, live SQLite or vector/graph store was changed.
- Existing security/provider boundaries and vector-reader compatibility code remain byte-identical to baseline. No dependencies, provider settings or framework were added; no model/API calls, ingestion, embedding generation, publication or commits occurred.
- Existing loopback servers on ports 8001 (PID 33292) and 8000 (PID 36636) were preserved. They were not restarted or used for answer queries. The existing process must be separately reloaded to use changed Python/HTML code; this task does not assert the new code is loaded there.
- Terminology persistence/live retrieval integration remains a separate projection/read-contract task. This helper milestone does not establish improved answer accuracy, certified diagram regions, complete terminology, table fidelity, claim entailment or multi-hop completeness.

Selective helper ideas were reimplemented against current contracts; no patch module was overlaid or executed. Owner-supplied folder provenance and member hashes remain in the plan. Original ZIP byte identity and an explicit standalone patch license are not represented as established.

## Reproduce bounded checks in the existing environment

Use fresh temporary locations, not live stores. No package installation is required.

```powershell
python -B tests/run_manifest_offline.py
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest -q -p no:cacheprovider --basetemp '<fresh-task-temp>' tests/test_vector_reader_compat.py
node tests/security_settings.test.js
node tests/bbox_validation.test.js
```

Generic test discovery is outside this check set: historical endpoint tests can query a running service and invoke a model. Browser/catalog parity harnesses, red/green logs, final fingerprints and the machine-readable implementation receipt remain in the external task directory.
