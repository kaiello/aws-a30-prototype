---
name: aws-a30-ner-and-routing
description: Dedicated inspection and playbook skill for the AWS A3.0M/A3.0:2020 Welding Domain Named Entity Recognizer (WeldingNER), dynamic compound code parser, callout/backlink multi-intent router, and whole-standard CLI. Use when inspecting entity spans, diagnosing query routing, parsing Table A4 XXXX-YY compound codes, or evaluating ID-free spatial/waveform diagrams.
---
# AWS A3.0 Domain NER and Multi-Intent Routing Skill

This skill provides operational guidance for inspecting, debugging, and testing query entity extraction and routing across `AWS A3.0M/A3.0:2020` using `src/welding_ner.py`, `src/semantic_nlq_expander.py`, and `src/evidence_whole_standard_cli.py`.

## When to Use

- Inspecting how a natural-language query is segmented into domain entities (`STANDARD_LOCATOR`, `COMPOUND_DESIGNATION`, `PROCESS_CODE`, `MODE_SUFFIX`, `PROCESS_TERM`, `NONSTANDARD_OR_HISTORICAL`, `WELD_POSITION`, `DOMAIN_QUALIFIER`, `DIAGRAM_CALLOUT`, `WAVEFORM_INTERVAL`, `GLOSSARY_TERM`)
- Diagnosing why a query routes to specific figures, tables, or glossary entries
- Testing Table A4 compound process designations (`<PROCESS>-<SUFFIX>`, e.g., `PAW-AU`, `GTAW-ME`, `FCAW-G-SA`) or validating invalid suffixes (e.g., `GTAW-ZZ`)
- Testing ID-free spatial callout resolution (e.g., queries mentioning "theoretical throat" resolving to Figure B25)
- Disambiguating homographs (e.g., `AB` as Arc Brazing vs Adhesive Bonding, or `6G` position in pipe vs plate)

## Quick CLI Usage

All CLI commands run 100% offline with zero network calls:

### 1. Named Entity Recognition Inspection
```powershell
python -B -m src.evidence_whole_standard_cli --ner "What does PAW-AU designate and which diagram illustrates theoretical throat?" --json
```
Returns a `WeldingNERReceipt` containing:
- `spans`: List of extracted spans with exact character offsets (`query[start_char:end_char] == surface_text`).
- `sub_components`: For compound codes, breakdowns into base process (`PAW` from Table A1) and mode suffix (`-AU` from Table A4).
- `ambiguity_candidates`: Any polysemous alternatives (e.g., for `AB`).

### 2. Multi-Intent Routing Inspection
```powershell
python -B -m src.evidence_whole_standard_cli --route "Compare historical atomic hydrogen welding with GTAW-ME" --json
```
Returns:
- `ner_receipt`: Entity spans and detected targets.
- `expansion_trace`: Expanded synonyms, acronyms, and IDF-weighted callout ranks.
- `inferred_targets`: Ranked figures, tables, and Clause 4 terms.
- `planned_operations`: Ordered store operations planned by `DeterministicQuestionPlanner`.

### 3. Full Answer Execution & Provenance
```powershell
python -B -m src.evidence_whole_standard_cli --ask "What does PAW-AU stand for in AWS A3.0?" --json
```
Returns:
- Composed answer.
- `provenance`: `printed_page`, `pdf_index`, `evidence_locator`.
- `requires_diagram_crop`: `False` for table/text-only answers; `True` if a diagram was consulted.

## Key Invariants

1. **Table A4 Dynamic Compound Parsing:**
   Valid suffixes are strictly the 6 defined in Table A4: `-AD` (adaptive), `-AU` (automatic), `-MA` (manual), `-ME` (mechanized), `-RO` (robotic), `-SA` (semiautomatic).
   Invalid suffixes (e.g., `-ZZ`) must be tagged `INVALID_COMPOUND_DESIGNATION` with an explicit abstention reason.

2. **Longest-Match Trie Resolution:**
   Multi-word spans (*"gas tungsten arc welding"*, *"theoretical throat"*, *"atomic hydrogen welding"*) cleanly subsume shorter substrings (*"arc"*, *"welding"*).

3. **Locator Protection:**
   In `src/welding_ner.py`, terms like `table_a1:proc:brazing` are entity type `PROCESS_TERM` or `GLOSSARY_TERM`, NOT `STANDARD_LOCATOR`. Only explicit locators (e.g., `Table A1`, `Figure B25`) populate `inferred_tables` or `inferred_figures`.
