# Gate 6.7 checkout: Independent Reader and Retrieval Diagnostic

**Disposition:** bounded implementation and local pilot complete; **reader NOT QUALIFIED**.

**Base:** `27ab96ed6b8809b1990d4d32abfd38ea586cf54f` (Gate 6.6).  
**Tested implementation commit:** `f870c1c93f90aad2dfb7a35b6295c121d848e5b2`.  
**Branch:** `feat/gate-6-7-independent-evaluation`. No merge, deployment or release tag.  
**Plan:** [Gate 6.7 card](GATE_6_7_INDEPENDENT_EVALUATION_CARD.md).  
**Case-level evidence:** [safe results report](docs/gate67_observed_results.json).

## What changed

Native PDF text and full-page images replace application-generated answers as reader evidence. Packets have explicit page IDs, all three page coordinates and PDF/text/image hashes. Gold expected claims and statuses remain outside reader inputs. The actual `src.query.run_query(..., evidence_version="whole_standard")` route selects retrieved pages before gold is opened; its prose answer is recorded separately and never supplied to the candidate reader. Both tracks use a fixed two-page budget and the same reader configuration.

The scorer checks offered evidence identity, citation IDs, answer/claim spans and status. Semantic approval requires a named independent human's source and response review, bound to case, packet and response hashes. Negated keyword answers cannot automatically pass. Reviews also cover completeness, qualifiers, citation support and appropriate abstention. Review JSON is an auditable human assertion, not authentication of the reviewer.

Gate 6.6 is now described as a circular diagnostic prototype. Its stored A/B/C/retrieved totals remain 2/15/24/24 out of 24. Three incorrect matrix cells were corrected; historical packets, results and replay provenance were preserved. The historical audit bundle is annotated rather than regenerated.

Selective Drive sync now validates every selected source and destination hash before writing, copies only listed project files, verifies readback, and does not prune or copy through the canonical checkout. Existing default mirror behavior is retained for compatibility; this gate uses the explicit selection mode.

## Observed pilot

Eight newly authored cases were checked directly against the immutable source PDF by an agent. They are **exposed development cases**, not held out. Human source and answer adjudications: **0**. A custodian-held unseen set has not been created or run.

Reader: local Ollama `qwen2.5vl:3b`, digest `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`. Configuration: temperature 0, seed 67, context 16,384 tokens, output limit 1,200 tokens, timeout 180 seconds, full-page images at 120 DPI. Exactly **16 calls attempted and completed**, one per case/track, zero retries, zero paid API calls, zero model downloads. All responses stopped normally; maximum observed prompt tokens 5,341 and output tokens 233. This was a real local vision-reader pilot, not a live DeepSeek planner evaluation.

| Case | Topic | Gold PDF indices | App-selected PDF indices | Gold reader | Retrieved reader |
|---|---|---|---|---|---|
| G67-DEV-01 | Residual-stress qualifiers | 60 | 60 | Structural failure | Structural failure |
| G67-DEV-02 | Active flux and voltage dependency | 18 | 68 | Pending human review | Structural failure |
| G67-DEV-03 | Equal/unequal fillet size | 37 | 36 | Structural failure | Structural failure |
| G67-DEV-04 | Robotic coextrusion code, two tables | 82, 86 | 81, 86 | Structural failure | Structural failure |
| G67-DEV-05 | Figure A3 structure and footnote | 88 | 88 | Structural failure | Structural failure |
| G67-DEV-06 | Figure B46 key mapping | 162 | 162, 19 | Structural failure | Pending human review |
| G67-DEV-07 | Figure B54 qualitative/current limits | 169 | none; app refused | Structural failure | Structural failure |
| G67-DEV-08 | Table A4 cannot provide amperage | 86 | 86 | Structural failure | Structural failure |

The source-page coverage check finds at least one missing gold page in cases 02, 03, 04 and 07. Case 06's fixed budget omits another app-returned page (PDF 60). Coverage can expose a source-selection or citation-metadata problem; it does not establish whether an answer claim is supported.

Across both reader tracks, **14 structural failures and 2 pending reviews** were recorded. Failure instances include 9 claim-span mismatches, 7 unknown citation IDs, 3 missing/invalid claim citations, 5 status mismatches and 4 missing required pages; categories can overlap. These are protocol/evidence checks, not a semantic accuracy score. No answer is certified supported, no quality delta is reported, and the candidate reader is not qualified.

## Verification

- Gate 6.7 focused suite: **96 passed** (source packets, adversarial scoring, pinned reader, runner integrity and selective sync).
- Selective sync plus existing closeout compatibility: **27 passed** (22 new tests, 5 existing).
- All **54 locked artifacts** match their expected SHA-256 values, including the source PDF.
- Offline real-entry preflight: `CLEAR_WHOLE_STANDARD_CONTRACT` and `CLEAR_DEEPSEEK_REPLAY_PREFLIGHT`; zero network calls, 7 canonical stores verified, 4 replay contract cases executed. This does not represent fresh model inference.
- Full repository regression: **incomplete**. The optional 1,630-test run was stopped while executing `test_gate_6_4_replay_and_deterministic_20_20` after 1,443.9 CPU seconds. No full-suite pass is claimed. Three nested-Git failures occurred before the isolated checkout was attached to its Git directory; all three then passed in 2.05 seconds. The same three checks passed on the unchanged original baseline in 1.67 seconds.
- Independent code review found packet/receipt tampering and error-denominator gaps; fixes and regression tests are included. No remaining high-priority circularity or source-leakage finding was reported.

The full-suite command used an external temporary directory (existing capture tests require this) and Windows' selector event-loop policy. An earlier attempt used a repository-local temp path and the default Proactor loop; it was stopped after stalled execution. These attempts do not count as a successful regression run. The focused checks and offline preflight are the completed software verification for this bounded gate. Successful focused pytest runs emitted an ignored `pyreadline3` console destructor warning after exit 0.

## Receipts and continuation

The local receipt root is `C:\Users\kenai\Documents\Codex\2026-11-04\task-2\storage\gate67_runs`. `prepared_006` contains application answers, explicit retrieval selections, source packets and packet hashes. `reader_001` contains captured requests, pinned config/runtime, raw responses, parsed outputs and unapproved human-review templates for all 16 calls. `unadjudicated_score_001.json` confirms repeat scoring without human reviews. Failed/incomplete preparation attempts in earlier numbered directories are preserved.

Source PDF, extracted page text/images, raw requests and model answers stay in ignored local storage. New Git/Drive publication includes only reviewed code, tests, cards, configuration and safe metadata/results. No corpus bytes, credentials or unrelated user files are introduced to Git.

Next, an independent human should review the source, expected claims and every raw answer. Copy each template to `human_reviews/<case-id>/<gold|retrieved>.json`, record supported/contradicted/missing/qualifier judgments and dimensions, then run:

```powershell
python -B -m eval.run_phase6_7_independent_evaluation score --prepared storage/gate67_runs/prepared_006 --run storage/gate67_runs/reader_001 --reviews storage/gate67_runs/human_reviews --output storage/gate67_runs/adjudicated_score_001.json
```

Address reader citation/claim/status adherence and the four app-page coverage misses using those judgments. Freeze a new implementation/configuration before an independent custodian authors and seals fresh held-out questions. ColPali/ColQwen remains deferred until adjudicated evidence shows a retrieval deficit with a qualified reader.

## Publication scope

Git target: the existing owner-controlled `https://github.com/kaiello/aws-a30-prototype.git`, feature branch above. GitHub ownership/push permission and the remote base were verified; the repository is public, so newly introduced blobs were reviewed for source/credential exclusion. The implementation was pushed and its remote tip verified as `f870c1c93f90aad2dfb7a35b6295c121d848e5b2`. The checkout document and final test-status metadata are committed afterward; that final branch tip is recorded in the ignored local completion receipt.

Drive target: the existing owner-private [aws-a30-prototype mirror](https://drive.google.com/drive/folders/1bxW458bhsFbDdX-zkBdtIK5WHOSfUJHN), mounted at `G:\My Drive\git_projects\aws-a30-prototype`. Destination files were compared with the unchanged original checkout before selection; unrelated changes must abort the sync. The first 19-file sync passed every local SHA-256 readback, pruned zero files, and the plan was fetched successfully through the Drive connector. A final scoped sync adds this checkout and updates the test-status report. The completion receipt records the final remote tip, selected-file hash readback and connector verification. No merge or deployment is part of this closeout.
