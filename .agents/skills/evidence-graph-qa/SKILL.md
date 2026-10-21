---
name: evidence-graph-qa
description: Run a bounded owner-question graph-QA set through the existing source-bound Figure A1 CLI and keep actual outputs separate from independent grading. Use for backend answer checks over the prepared A1 adapter; unimplemented figures must be rejected rather than treated as A1.
---

# Evidence Graph QA

Before execution, record the existing source/edition/image/graph identities and
harness/input versions plus hashes; retain them with the new output. Use existing
hash tools, not a new wrapper or framework.

Invoke the existing canonical CLI from the target repository; do not create a
wrapper, test framework or new evaluation infrastructure:

```powershell
python -B -m src.evidence_a1_cli --root <repo> --input <cqs> --graph-qa --output <repo>/storage/evidence_v2/<new-run>.json
```

Use the owner's execution-only CQ JSON (`a1-owner-cq-1.0`,
`source_element="Figure A1"`, unique `id`/`query` items). Keep expected answers,
verdicts and rubric notes in separate private grading data, never in execution
input, retrieval, graph updates or answer logic. Use a new ignored output file;
preserve actual prior outputs, gold and failures.

The canonical CLI validates the prepared Figure A1 source/edition/image and
qualified evidence. Other source adapters are unimplemented. The typed graph
operations may be reused on compatible geometry graphs, but that does not prove
other-figure loading or multi-figure operation.

This deterministic path uses model/provider NONE. Answered cases are not semantic
passes: independently assess actual answers and source support, retaining
candidate relationship qualifications and `semantic_validation=false`. Require
complete-chart scope and positive evidence for negatives. Label exposed repairs
as DEVELOPMENT rather than unseen or model validation.

Run only the authorized bounded set once, report results and remaining failures,
and stop. Do not add questions/gold to this skill, change source semantics to fit
an expected answer, or expand checks/infrastructure. This project-discoverable
instruction skill does not add automatic backend loading or runtime `SKILL.md`
consumption. No UI, model/cloud, global configuration or Git publication work is
implied.
