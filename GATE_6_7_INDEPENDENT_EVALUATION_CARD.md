# Gate 6.7: Independent Reader and Retrieval Diagnostic

Status: bounded implementation and local reader pilot completed; reader qualification pending independent human adjudication. See `GATE_6_7_CHECKOUT_CARD.md` for results and sync receipts.

This gate replaces the proposed visual retrieval comparison. Gate 6.6 remains an exposed diagnostic prototype: its gold input was an application-generated answer, its composer copied that answer, and its retrieved arm used the same deterministic engine. Its scores cannot qualify a reader or measure a retrieval deficit.

## Bounded implementation plan

1. Freeze historical artifacts. Reconcile the three incorrect Gate 6.6 matrix cells and annotate current roadmap claims. Verify the 54 existing artifact locks and offline real-entry preflight.
2. Build source-native packets from the immutable PDF, with page IDs, three page coordinates, source/text/image hashes, and a fixed two-page budget. Keep expected claims and answer status outside reader inputs. Eight new, directly source-checked cases are exposed development cases; agent source inspection is distinct from human adjudication.
3. Exercise the actual `src.query.run_query(..., evidence_version="whole_standard")` application route. Record its answer and evidence selection separately. Feed only source pages selected by that route to the same configured reader used for gold pages. Never feed the application answer to that reader.
4. Pin an already available local reader's model digest, prompt, options and evidence budget. Capture exact requests and raw outputs locally. No downloads, paid loops, retries, or external source upload. If unavailable, preserve prepared requests and mark model execution blocked.
5. Replace keyword approval with structural checks and human adjudication bound to case, packet and response hashes. Test negation, wrong/irrelevant citations, missing evidence, dropped qualifiers, false abstention and stale reviews. Semantic approval stays pending until a named independent human reviews source and response.
6. Keep held-out work outside development: an independent custodian authors and seals new questions after this implementation is frozen, checks overlap, runs once against a recorded commit/configuration, and reports all outcomes. No unseen benchmark is claimed in this gate.
7. Produce a checkout with exact commits, tests, per-case outcomes, execution mode, source review status and continuation commands. Push only reviewed project changes to a feature branch and sync the same scoped change set into the verified private Drive mirror. Do not merge, deploy, prune, or overwrite unrelated work.

## Acceptance and decision rules

- The reader receives native source text/images, question and evidence IDs, with no expected answer, claim rubric or answer-derived status.
- Gold and retrieved evidence use identical page budgets and reader configuration. App-route evidence is recorded before consulting gold. A page-level retrieval coverage check is diagnostic only; source-page presence does not establish claim support.
- Software checks, app-route execution, model execution, structural validity and human content judgments are reported separately. Missing human judgment cannot produce `PASS_SUPPORTED`.
- ColPali/ColQwen remains deferred. Consider a bounded retrieval comparison only after a reader succeeds on independently adjudicated gold evidence and fails end to end because required source evidence is missing. Reader failures with correct evidence lead to reader/prompt work first.

## Held-out continuation

The eight development questions and all historical cases are exposed. After implementation freeze, a reviewer who did not implement this gate must author a separate private case file and source rubric, record its SHA-256 and the frozen Git commit, and keep it away from developers and model prompt tuning. Check normalized question overlap against exposed sets. Freeze reader config before opening it; run once, preserve every raw response and human judgment, and publish denominator, failures, rescues and harms. On subsequent tuning, retire that set to regression and commission a new one.

## Deliverables

- `src/independent_source_packets.py`: native PDF page text/images and verified evidence identities.
- `src/independent_reader_evaluation.py`: local pinned reader and actual application-route capture.
- `src/independent_reader_scoring.py`: structural and hash-bound human review gates.
- `eval/run_phase6_7_independent_evaluation.py`: bounded preparation/run/score CLI and local append-only receipts.
- `eval/fixtures/gate67_development.json`: eight exposed source-checked development cases, no source passages.
- `GATE_6_7_CHECKOUT_CARD.md`: measured results and exact remaining blockers.

Run packets and model outputs contain copyrighted source material. They remain in ignored local storage and the existing owner-private mirror only when explicitly selected; source PDF, page text, images and credentials are excluded from new Git publication.

The local transport follows the official [Ollama chat](https://docs.ollama.com/api/chat) and [installed-model metadata](https://docs.ollama.com/api/tags) contracts. It verifies the installed digest before and after inference, refuses cloud aliases and redirects, and captures requests and raw outputs. Human review forms record independent human assertions; the JSON field identifying a reviewer is not an authentication mechanism.
