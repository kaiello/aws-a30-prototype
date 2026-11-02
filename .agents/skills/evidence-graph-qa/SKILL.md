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
1. **Store-Driven Zero-Canned-Prose Composers (Gate 6.2):**
   - 7 atomic composers dynamically query store records with 0 string literal fallbacks in `.get()`:
     - `_exec_lookup_taxonomy_subtypes`: queries `is_a_promotion_store.json` and Table A1 for process variations across any parent.
     - `_exec_expand_cross_references`: queries `glossary_store.json` for bidirectional `see_also` and `figures` cross-references.
     - `_exec_weld_position_sense`: queries Clause 4 definitions for all 12 positions (`1G`–`6GR`, `1F`–`4F`), binding to p. 5 (groove) or p. 6 (fillet) and Figures B16–B20.
     - `_exec_disambiguate_homograph`: resolves `AB` across Table A1, Clause 4, and Figure A6 legend.
     - `_exec_compound_lookup_and_validation`: parses 2-tier and 3-tier compound codes, emitting rejection rationale for invalid codes.
     - `_exec_compare_historical_and_active`: dynamically compares obsolete/historical processes (Table A5) with active processes (Table A1).
     - `_exec_polysemous_diagram_and_glossary`: handles dual-target queries requesting both spatial geometry and Clause 4 definition.
2. **Modality-Appropriate Provenance (Gate 5.6):**
   - Every valid answer returns `printed_page`, `pdf_index`, and a structured `evidence_locator` (e.g. `clause4:term:kerf`, `table_a4:suffix:-AU`, `figure_b25:callout:theoretical_throat`).
   - `requires_diagram_crop: True` (with 300-DPI `crop_path`) is attached **if and only if** the claim depends on a visual diagram (`Figures A1–A6` or `Figures B1–B54`). Pure text and tabular queries return `requires_diagram_crop: False` with zero spurious crops.
3. **Explicit Abstention & Refusal Contracts:**
   - Out-of-Range locators (`Figure A7`, `Figure B55`, `Table A6`): `REFUSAL_OUT_OF_RANGE`.
   - External fabrication codes, mechanical property limits, or welding parameter schedules: `REFUSAL_OUT_OF_SCOPE`.
   - Coined or unstandardized terms absent from the standard: `NOT_IN_STANDARD`.
   - False premises contradicting classification trees: `CONTRADICTION_REFUTED`.
4. **Strict Epistemic Quarantine:**
   - When using `DeepSeek-V4.1-Flash-1017` planning, all reasoning traces are tagged `UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE` and final answers are composed strictly from verified store records.
