---
name: evidence-graph-qa
description: Execute whole-standard deterministic question answering with modality-appropriate provenance (printed page, PDF index, locator, conditional 300-DPI diagram crop) across AWS A3.0M/A3.0:2020.
---

# Evidence Graph QA

Execute natural-language queries against the complete 162-page ingested AWS A3.0M/A3.0:2020 standard via the canonical CLI:

```bash
# Deterministic Question Answering with structured receipt
python -B -m src.evidence_whole_standard_cli --ask "<query>" --json

# Offline DeepSeek-V4.1 Replay Question Answering
python -B -m src.evidence_whole_standard_cli --ask "<query>" --planner deepseek-replay --json
```

Or programmatically in Python:

```python
from src.evidence_phase4_bakeoff import answer_whole_standard_question

result = answer_whole_standard_question(query)
print("Answer:", result["answer"])
print("Printed Page:", result["printed_page"])
print("Evidence Locator:", result["evidence_locator"])
print("Requires Diagram Crop:", result["requires_diagram_crop"])
if result["requires_diagram_crop"]:
    print("Crop Asset:", result["crop_path"])
```

## Production Invariants Enforced
1. **Modality-Appropriate Provenance (Gate 5.6):**
   - Every valid answer returns `printed_page`, `pdf_index`, and a structured `evidence_locator` (e.g. `clause4:term:kerf`, `table_a4:suffix:-AU`, `figure_b25:callout:theoretical_throat`).
   - `requires_diagram_crop: True` (with 300-DPI `crop_path`) is attached **if and only if** the claim depends on a visual diagram (`Figures A1–A6` or `Figures B1–B54`). Pure text and tabular queries return `requires_diagram_crop: False` with zero spurious crops.
2. **Explicit Abstention & Refusal Contracts:**
   - Out-of-Range locators (`Figure A7`, `Figure B55`, `Table A6`): `REFUSAL_OUT_OF_RANGE`.
   - External fabrication codes, mechanical property limits, or welding parameter schedules: `REFUSAL_OUT_OF_SCOPE`.
   - Coined or unstandardized terms absent from the standard: `NOT_IN_STANDARD`.
   - False premises contradicting classification trees: `CONTRADICTION_REFUTED`.
3. **Strict Epistemic Quarantine:**
   - When using `DeepSeek-V4.1-Flash-1017` planning, all reasoning traces are tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE` and final answers are composed strictly from verified store records.
