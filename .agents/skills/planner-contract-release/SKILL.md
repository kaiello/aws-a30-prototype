---
name: planner-contract-release
description: Prepare a bounded AWS A1/A2 planner-contract change or release handoff, including an offline preflight through the public planner entry point before any separately authorized paid batch.
---

# Planner contract release

Keep the goal correct, complete, evidence-backed AWS backend answers for A1/A2,
progressing from text to relationships to multihop. Read the current dispositions
in [goal](../../../docs/goal.md), [plan](../../../docs/aws_a30_standalone_prototype_plan.md)
and [agent guidance](../../../docs/agents.md). Check the proposed change against
that scope; preserve historical outcomes without treating old approvals as new authority.
Do not expand into OCR, admission changes, new questions/figures, UI or a framework.

## Align the runtime boundary

Use [the shared JSON contract](../../../src/evidence_chart_contract.json) for runtime
definitions, instructions and metadata policy. Check that its schema descriptions,
prompt and lowering agree, including planned rationale retained as bounded unverified
trace metadata and unresolved reasons forwarded unchanged. Validate original metadata
before normalization; preserve the original external plan and action/part identities.

Keep executable source/query bindings, typed IDs/roles, budgets, prior-result references,
blocked dependencies and evidence/admission guards explicit in code. These safety
ceilings intentionally overlap JSON; shared definitions reduce drift but cannot prove
agreement. Printed identity, candidate layout, physical paths and accepted semantic
assertions retain their separate authority. Never fill omitted model intent or repair
individual question selections to obtain a passing result.

The runtime loads JSON instructions. This SKILL.md guides development and release
work; it is not a backend instruction registry or a per-question answer source.

## Run one real-entry offline preflight

Use an original saved model receipt containing a nonempty planned-part rationale,
its unchanged existing question JSON and the matching source. Exclude gold from
preflight inputs and model context. Keep original receipts/plans untouched; do not
substitute an invented or manually adapted plan. Write to a new private directory.

From the repository, use the existing public-entry preflight command with real paths:

```text
python -B -m src.evidence_chart_preflight --root <repo> --input <existing-question-json> --question-id <id> --receipt <original-receipt-json> --output-directory <new-private-dir>
```

For A2, supply `--graph <A2-graph-json>` when required and
`--source-observation <A2-optional-candidate-receipt>` only for the matching optional
candidate attachment. Retain its candidate status. Do not add a parallel harness.

Inspect the resulting transport, compilation, retrieval and answer-delivery contract
receipt. A missing or failed preflight blocks a paid batch even when that batch has
otherwise been authorized; stop with the concrete boundary failure. A passing
preflight establishes only this receipt's contract execution, not semantic correctness,
complete answers, generalization or permission to call a model or publish changes.

## Keep evidence and handoff short

Report software checks, manual-action checks, unchanged cached replay and fresh-model
results separately. Record actual failures and source limits; attempted operations,
valid JSON and passing preflight are not answer-quality approval. Preserve raw plans,
questions, source/store bytes and old results; do not expose private evidence in Git.

Finish with the goal, authorized scope, branch/base and contract/instruction versions,
preflight receipt location/outcome, known failures and one next action. State whether
any model actually consumed the instructions. No paid call, retry campaign, commit,
push, merge or deployment follows from invoking this skill; follow current explicit
authorization for those actions.
