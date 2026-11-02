---
name: evidence-graph-routing
description: Route natural-language welding questions through character-offset Welding NER and callout/backlink-indexed multi-intent routing across all 162 ingested pages of AWS A3.0M/A3.0:2020 (Clause 4, Tables A1-A5, Figures A1-A6, Figures B1-B54, Annex C, Annex D).
---

# Evidence Graph Routing

Use the canonical Whole-Standard CLI and routing engine from the target repository:

```bash
# Inspect Named Entity Recognition spans, compound codes, and homographs
python -B -m src.evidence_whole_standard_cli --ner "<query>" --json

# Inspect Multi-Intent Router plan and target division candidates
python -B -m src.evidence_whole_standard_cli --route "<query>" --json

# Inspect 1-hop Semantic Concept Graph neighborhood and diagram ranking
python -B -m src.evidence_whole_standard_cli --expand "<query>" --json
```

Or via the Python API:

```python
from src.evidence_whole_standard_cli import run_route_cli
from src.semantic_nlq_expander import get_semantic_expander
from src.welding_ner import get_welding_ner

ner = get_welding_ner()
receipt = ner.recognize_entities(query)
expander = get_semantic_expander()
neighborhood = expander.expand_semantic_neighborhood(query, max_hops=1)
```

## Routing Capabilities
1. **Deterministic Welding Domain NER (`src/welding_ner.py`):**
   - 11 entity types: `STANDARD_LOCATOR`, `COMPOUND_DESIGNATION`, `INVALID_COMPOUND_DESIGNATION`, `PROCESS_CODE`, `MODE_SUFFIX`, `PROCESS_TERM`, `NONSTANDARD_OR_HISTORICAL`, `WELD_POSITION`, `DOMAIN_QUALIFIER`, `DIAGRAM_CALLOUT`, `WAVEFORM_INTERVAL`, `GLOSSARY_TERM`.
   - Character-offset non-overlapping longest-match tokenization.
   - 3-tier `<BASE>[-<VAR>][-<MODE>]` decomposition (`FCAW-G-SA`, `OFC-A-MA`, `GMAW-P-AU`).
   - Suffix validity verification against Table A4's 6 standard suffixes (`-AD, -AU, -MA, -ME, -RO, -SA`).
   - Contextual sense and qualifier resolution (`AB` Table A1 vs Figure A6; `1G`/`1F` pipe vs plate).
2. **Callout- & Backlink-Indexed Multi-Intent Routing & Semantic Concept Graph:**
   - Inverted index over all 1,115 Annex B spatial callouts, 96 Annex A circles, and 265 Clause 4 figure back-links.
   - Store-compiled `SemanticConceptGraph` tracking `see_also` clusters, `is_a_subtypes`, `sibling_variations`, and co-diagram callout topologies.
   - Deterministic IDF-weighted ranking for ID-free spatial diagram resolution (`Figure B25` weld sizes, `Figure B33` crack types, `Figure B46` FSW zones, `Figure B12` weld tabs/sump, `Figure B7` edge shapes, `Figures B16A-C` test positions).
3. **Legacy Figure A1 Diagnostics:**
   - Single-chart Figure A1 inspection is still accessible via `src.evidence_chart_cli`.
