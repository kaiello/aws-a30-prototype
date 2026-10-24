# Planner contract handoff

Goal: correct, complete evidence-backed AWS answers, one slice at a time; text,
then relationships, then multihop. Current scope is A1/A2 backend only.

Branch: `feat/planner-contract-preflight`, starting from local repair checkpoint
`bc51eae458e59764d6879ef175933aea4db7480e`. Main remains
`71088cebc9eb3b2556d7bbe73a23a451e645e3b9`. Nothing has been pushed or merged.

Exactly two serial workstreams: repair004 is completed/reported; this prevention
slice adds one offline public-entry command and one project planning/release skill.
No further inference, semantic repair, OCR, figure expansion or publication is
authorized. Private artifacts remain under ignored `storage/evidence_v2/`.

Contract: `chart-plan-contract-1.2`, SHA256
`d308371fca21a041e0aa0b6a12c894dc47bc3a7d354f8c74e6079655cde4d863`;
question wire1.0/instructions1.1; internal typed wire1.0/instructions1.5;
harness `a1-graph-qa-1.7.7`. Runtime consumes the shared JSON; SKILL.md is developer
guidance, not an automatically loaded backend registry. Explicit safety ceilings,
lowering and source/admission guards remain code; shared JSON cannot rule out drift.

Repair004:67 original fresh003 responses replayed unchanged through the actual
entry/compiler/backend. A1 content35 PASS/10 PARTIAL/6 UNASSESSED; A2 content9 PASS/
4 PARTIAL/3 UNASSESSED. Unanswered factual requests fail delivery; three A1 passes
are proper clarifications.97 focused software checks passed;51 deterministic A1
controls, source/store hashes and1,503 prior artifacts match. No candidate promotion.
One accepted literal lookup, zero accepted-KG path queries; physical paths are not
semantic IS_A transitivity. These cached results do not establish fresh improvement.

Known failures: missing list items/groups/follow-ups, targetless relationship
requests, invalid modes/information fields and failed reference producers. No
question-specific patches or manual action replacement occurred in004. Preserve
all old outputs and grades; do not launch another tuning/replay loop automatically.

Preflight command (one original response, network blocked, no gold):

Figure A2 check:
```powershell
python -B -m src.evidence_chart_preflight --root . --input storage/evidence_v2/a2_ingest_001/evaluation/questions.json --question-id A2-DEV001-01 --receipt storage/evidence_v2/a1_a2_relationship_003/a2_deepseek/request_001/receipt.json --output-directory storage/evidence_v2/<NEW-private-directory> --graph storage/evidence_v2/a2_ingest_001/final_projection_005/graph.json
```

Figure A1 check:
```powershell
python -B -m src.evidence_chart_preflight --root . --input eval/evidence_v2_a1_owner_cqs.json --question-id A1-CQ-001 --receipt storage/evidence_v2/a1_a2_relationship_003/a1_deepseek/request_001/receipt.json --output-directory storage/evidence_v2/planner_contract_preflight_001/a1_source_bound_saved_response
```

Corrected source-bound run with the original nonempty rationale; receipts:
- A2 receipt: `storage/evidence_v2/planner_contract_preflight_001/source_bound_saved_response/preflight.json` (Status `CLEAR_REAL_ENTRY_CONTRACT`).
- A1 receipt: `storage/evidence_v2/planner_contract_preflight_001/a1_source_bound_saved_response/preflight.json` (Status `CLEAR_REAL_ENTRY_CONTRACT`).
Actual original actions retained, metadata mapped, retrieval/evidence/answer delivered; inputs unchanged; new model/API calls 0.
This verifies captured execution only. Semantic answer quality needs independent source inspection. Both A1 and A2 branches of the preflight command are now separately executed and verified offline.
The first one-response check is retained in `actual_saved_response/`; review then
identified a missing optional candidate-input hash, fixed before the source-bound
check. All runs were offline with zero model/API calls. Skill validation passes;
independent review confirms the provenance correction. 108 focused regression checks passed in 2.60s.

Use [.agents/skills/planner-contract-release/SKILL.md](../.agents/skills/planner-contract-release/SKILL.md)
before any separately authorized paid batch/release. Keep software checks, manual
actions, cached replay and fresh model performance separate. Missing/failed
preflight blocks a batch; passing it grants no inference or publication permission.

Next action: review the actual004 answers and decide how to address remaining model
choices. Hold adoption/merge; another paid validation needs explicit approval.
No automatic A3, UI, Navy Weld, Utopia or new framework work.
