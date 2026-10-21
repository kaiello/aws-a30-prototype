# Figure A1 QA002 - frozen current-harness evaluation

Status: QA002_COMPLETE_WITH_CAPABILITY_FAILURES. 0 PASS, 15 FAIL, 1 PARTIAL, 0 UNASSESSED. One unchanged deterministic graph QA batch; 16 question items; model/provider NONE; zero model/external calls. No repairs or changed-code replays.

Harness `src/evidence_a1_graph_qa.py`, version `a1-graph-qa-1.0`; Python 3.12.7 / PyMuPDF 1.26.5. Canonical command from repository root:

```powershell
python -B -m src.evidence_a1_cli --input eval/evidence_v2_a1_qa_002_cqs.json --graph-qa --output storage/evidence_v2/a1_qa_run_002/graph_qa_raw.json
```

Harness SHA256 `9de8be895341e05157d2ff9ed0a800d733dbe8eea92086577017d54b9841ffd7`; graph `6476c898439108dbeaf7b92f0be3946a3e0d3538d5c15afb860d1cf0e02cc4d2`; input `f462ba11a21f776617abfbd05b93c0716ded133f748c94d65ede279c243c7dfc`; raw output `b21c4781365597d35f468686ec286fd49e16e32f71438373b38cc1d6cb210562`.

Figure A1 only, original single image, PDF index 87 / ordinal 88 / printed 75. Manifest/PDF/image identity and read-only canonical registry join verified. Candidate indentation edges remain candidate; no reviewed semantic subtype edges were added.

Raw outcomes: 10 capability_gap, 5 insufficient_evidence, 1 graph_answer. Unsupported plural/compound operations, false comparison scope gates, process/process-to-category routing mismatch, unsupported direct/path operations, and incomplete answer composition caused the failures. The required observed source rows and links exist. Case 10 retrieves the needed path but returns only broad enclosure membership.

Multi-name cases resolved 0/13 explicit mentions and returned 0/23 requested acronym/category mappings. The previously known shorter-name drop was not reached/reproduced here. A generic failure/abstention is not credited as a source-grounded answer or semantic restraint explanation.

Engine total 103.302 ms; wrapper wall 220.864 ms. This is graph QA, not end-to-end LLM validation. QA001 unchanged; these different questions expose new coverage gaps rather than prove QA001 regression.

Independent source gold was sealed before outputs and never supplied to execution. Full raw/private grading remains in ignored `storage/evidence_v2/a1_qa_run_002/`; redistributable metrics are in `eval/evidence_v2_a1_qa_002_aggregate.json`. Do not publish licensed source/gold. The initial wrapper UTF-8 decode failure happened before any backend question and was corrected only in the wrapper; one actual backend run followed.

Next priorities (not implemented): typed plural/compound operations and all-mention resolution; graph subjects before scope gating; qualified direct/recursive/path operators; answer subtask coverage; explicit source-limit explanations. No graph semantics repair or new DB/framework justified. Stop pending the next repair decision.

Local branch `v2/evidence-engine`; HEAD/main/v1.0 all `24bac45465bcb5c9ea14663f7a669927d5d2ed00`. All 45 frozen files, six protected files and 102 QA001 files unchanged. No commit/push/merge, UI or other-figure work.
