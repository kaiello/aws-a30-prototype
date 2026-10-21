---
name: evidence-graph-routing
description: Route graph questions through the existing typed planning and traversal core, preserving selected evidence and relationship qualifications. Use for designation lookup, membership, children, descendants, comparison or ambiguous graph selectors; use evidence-graph-qa for an owner-question batch through the source-bound A1 CLI.
---

# Evidence Graph Routing

Use the existing `src.evidence_a1_graph_qa.answer_graph` core from the target
repository. Inspect its plan and actual traversal; do not create another router,
wrapper, database or framework. For a caller-supplied compatible geometry graph:

```python
from src.evidence_a1_graph_qa import answer_graph
result = answer_graph(graph, query, complete_chart=False)
```

Caller-supplied graph JSON does not authenticate source or edition. Set
`complete_chart=True` only when full applicable chart coverage is established.
Source-bound owner questions use the canonical CLI through $evidence-graph-qa;
the only implemented source adapter is Figure A1.

Retain all independently requested subjects. Missing/ambiguous selectors must
remain explicit; direct children and recursive descendants are different
operations. Preserve selected nodes, edges, paths and qualifications in the
answer trace. Printed enclosure is chart membership, while indentation remains
candidate layout, not reviewed semantic subtype. A negative needs complete-chart
scope and positive evidence elsewhere; missing retrieval is not proof of absence.

Do not hardcode question answers or repair source facts to fit expected grades.
Keep source-derived results local and preserve prior failures. Run only the
requested bounded operation, then report unsupported capabilities or remaining
failures. This project-discoverable instruction skill does not add automatic
backend skill loading. No model, UI, global configuration or Git publication work
is implied.
