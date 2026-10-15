# Declarative manifest implementation receipt

Date: 2026-10-15. Branch: `plan/declarative-manifest-20261015`. Base: `89f4a529b05509d8dc45e439c858347abb2cf469`. Implementation and validation were completed on this branch; the owner-approved pull request records publication and merge state. The owner authorized implementation of [the bounded plan](declarative_manifest_plan.md). No model/provider calls, ingestion, store update, external database, new service, framework integration, commit, push or PR was performed.

## Delivered behavior and source proof

`config/aws_a30_2020_manifest.json` is the editable source-location authority; `src/standard_manifest.py` provides strict standard-library validation and copied read views. Runtime lookup checks the canonical metadata receipt, actual local PDF digest, page bounds, ordered continuations, references, proof states and contained relative paths. Verified assets are byte-checked when resolved. Invalid/missing/stale inputs fail explicitly rather than reusing a stale successful load. Exact aliases inherit their targets' verification state. A B16 group is not an exact source caption.

The licensed local PDF stays in place: 3,377,668 bytes, 190 pages, SHA-256 `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`. The canonical metadata SHA-256 is `144b08462a42442e0fa5b652e2dd2ef32ba890bbc1efd2b7ccdaddf10c778466`; the companion receipt records verifier, timestamp and PyMuPDF 1.26.5. No source paragraphs, renders or source bytes were added to the manifest/receipt.

Inventory: 10 sections, 62 figures, 11 tables. Figure anchors cover 86 figure-page bindings; 13 figures and five tables have multiple source pages. All 94 declared PNG bindings were compared locally against the relevant 180-DPI source-page renders using decoded RGB dimensions and pixel samples: 94 match, including shared-page and suffix figures. No images were regenerated on disk. This verifies render/page binding, not figure-region segmentation or diagram understanding. All region fields remain null. Table Markdown stays candidate content; table cells/footnotes were not certified.

## Consumer inventory

| Files | Result |
|---|---|
| `src/standard_manifest.py`, two `config/aws_a30_2020_manifest*.json` files | Source-bound inventory, strict loader, receipt/cache checks, exact/group/unknown/unverified resolution, safe ordered assets and compatibility projections. |
| `src/citation_checker.py` | Valid inventory from manifest; complete IDs rather than prefix matches; canonical source anchors; unknown/group diagnostics; suffix/D-table claim anchors; prose is not an ID. Citation presence is still not entailment. |
| `src/pre_retrieval.py` | Same existing valid singular enrichment grammar, now checked against canonical IDs. Acronyms and retrieval algorithm stay unchanged. Plural asset/citation support does not silently broaden retrieval expansion. |
| `src/figure_inspectors.py` | Titles/pages projected from manifest; existing categories/chips/queries/bboxes retained; B6 primary is p99; ordered `image_files` and source anchors are additive. Bare B6/b6 helper input remains supported. |
| `src/query.py` | Existing primary asset fields preserved; all available continuation PNGs returned; B16 expands to three explicitly grouped figures; nine UI companions retain candidate relationship status; absent table exports are not invented. |
| `src/config.py`, `src/extract.py` | Correct source indices and source-derived page/table metadata for future extraction; Annex B bounded at index169. Extraction was not run and existing chunk IDs/artifacts stay unchanged. |
| `src/build_dual_graph.py` | Future document/section/table metadata projects from manifest, including A4/A5 and source digest. Graph projection was not run. |
| `src/answer_routes.py` | Cached figure/table pages and filenames cannot override source metadata. Full cached tokens are preserved; unknown/group evidence cannot satisfy location grounding. Candidate text asset status remains explicit. |
| Five `tests/test_manifest_*.py`/`test_standard_manifest.py` files, retrieval baseline fixture, guarded runner | Bounded regression and compatibility evidence described below. |

No dependency change or OpenMetadata/service was introduced. Existing SQLite remains in place. No permanent legacy flag was retained after adapter fixtures passed; rollback is the complete small adapter change set, not removal of the JSON or a data rebuild. The plan records this refinement explicitly.

## Bounded results and reproducibility

Run with existing installed dependencies:

```powershell
python -B tests/run_manifest_offline.py
node tests/security_settings.test.js
git diff --check
```

The guarded runner disables plugin autoload, pytest cache, bytecode and dotenv loading; forbids model constructors, provider network access and actual SQLite connections; and uses fresh system-temp fixtures. Its only permitted connect is Python's internal Windows asyncio socketpair wakeup. Tests use injected synthetic rows/candidates. No live retrieval/answer benchmark ran.

Final results: **176 Python tests passed; four JavaScript credential checks passed**. This comprises 89 existing selected offline/security checks and 87 new manifest/compatibility cases. Frozen benchmark questions, scorer thresholds, historical receipts and security implementation files were not changed.

| Acceptance measure | Observed result |
|---|---|
| Eight named previously false/ambiguous exact citations | A7, A14, B16, B55, B64, B97, B120 and Table A10 now produce explicit unresolved/group diagnostics; none is accepted as an exact source element. |
| Valid figure/table labels | 73/73 resolve under existing canonical labels/IDs with ordered source anchors. |
| Continuations | 13/13 multi-page figures and 5/5 multi-page tables retain complete ordered source spans. Existing exports are returned in source order; missing exports remain absent. |
| B6 primary | Changes from legacy continuation p100 to explicit primary `Figure_B6_p99.png`; p100/p101 remain continuation assets. |
| Retrieval contract | Eight pre-adapter valid queries, each with/without simulated reranking: identical enrichment, injected candidate IDs/order/content/raw scores/RRF scores and simulated cross-encoder results; candidate inputs remain unmutated. This is deterministic compatibility, not live semantic recall. |
| API/security | Existing missing-index, HTTP/CLI, origin, credential and asset containment fixtures pass. BGE-large/1024 configuration remains unchanged. |

Independent local static review found five adapter/loader gaps (D lists, bare IDs, alias proof promotion, prose as ID, unresolved route sufficiency). Each was reproduced in a failing fixture and fixed; a second read-only pass found them resolved. Integrator follow-up fixtures also reproduced/fixed cached B1.5/A1.5 prefix promotion and a non-object receipt error. The reviewer did not execute tests, access the PDF, inspect stores or call models/network.

## Limits and remaining milestones

- Historical chunks/JSONL/stores are unchanged: the first glossary page remains in the legacy preamble chunk; 19 later pages remain mislabeled in old Annex-B JSONL. Future metadata corrections do not repair persisted content. Other one-off extraction scripts remain legacy entry points and were not redesigned.
- D1 has candidate Markdown but no declared PNG export; D2-D5 have source anchors and no declared exports; D6 has candidate Markdown. Source presence is distinct from an available parsed asset. A1-A5 have candidate Markdown and verified existing PNG bindings.
- Annex B is `conflicting` because contents index9 says informative and opening index93 says normative. Location verification does not settle applicability. UI companion links, graph semantic bridges, callout geometry and text reading fidelity are not certified by this work.
- The route's existing heuristic status and citation-presence scoring are not a claim-level entailment proof. Text/image model reading, table-cell/footnote integrity, multi-hop adequacy, abstention calibration and live retrieval/answer quality remain separate evaluation milestones.
- Runtime metadata constants are initialized at import. Changing the manifest/receipt requires coordinated deployment and a process restart to refresh all projections. The reader revalidates changed file-stat keys, but this is not a signature or an adversarial tamper monitor; the source/metadata files must stay trusted and access-controlled.
- The local PDF is currently a required runtime fingerprint input. A deployment without it fails explicitly; a metadata-only deployment contract is outside this change.

Read-only SQLite observation: Python links SQLite 3.45.3. The existing registry header uses read/write format bytes `(1,1)` (rollback family), and no `-wal`/`-shm` sidecars were present at inspection. No connection/PRAGMA, WAL enablement, upgrade or concurrency certification occurred. Keep the manifest plus current embedded store architecture; revisit WAL/version safety only if a separately authorized concurrency change needs it.
