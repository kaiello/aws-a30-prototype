---
name: source-aware-ingest
description: Expand source-aware multimodal extraction across AWS A3.0M/A3.0:2020 figures, tables, and glossary clauses using the staged extraction policy and curated manifest. Use when ingesting Figures A3-A6, Tables A1-A5, Clause 4 Glossary, Annex B Figures B1-B54, or Annex C/D.
---
# Source-Aware Ingestion Skill

Ingest new sections of `AWS A3.0M/A3.0:2020` figure-by-figure and table-by-table with deterministic provenance, staged extraction, and explicit source-anomaly preservation.

## When to Use

- Adding Figure A3 or Classification Charts A4, A5, A6 (printed pp. 76-79)
- Binding Normative Tables A1-A5 (printed pp. 69-74) or Informative Tables D1-D6 (printed pp. 165-170)
- Ingesting Clause 4 Glossary definitions (printed pp. 5-67) and Annex C style/committee rationale (printed pp. 159-164)
- Ingesting Annex B engineering diagrams B1-B54 (printed pp. 81-157)

## Steps

1. Register the target slice in the Curated Manifest first:
   - Bind the authorized PDF (`AWS A3.0M/A3.0:2020`, SHA-256 `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`).
   - Record `pdf_index` (0-based), `viewer_page` (1-based), `printed_page`, normalized crop `[ymin, xmin, ymax, xmax]`, and crop SHA-256 hash so neighboring material (like Figure A3 below Figure A2 on p. 76) cannot contaminate the slice.
   - For multi-page figures (such as Figure B6 across pp. 87-89 or Figure B24 across pp. 117-122), bind all continuation pages as an ordered `complete-packet` sequence.

2. Apply the 3-stage extraction policy in strict priority order:
   - **Stage 1 (Native PDF Text & Vector Geometry):** Extract native text spans, font weights (boldface standard terms vs. lightface nonstandard terms vs. italic domain delimiters), underline/margin-bar 2020 revision markers, and vector box/line primitives directly from the PDF.
   - **Stage 2 (Raster OCR & Dictionary-Assisted Recovery):** Where figure text is rasterized or fragmented, run bounded OCR constrained by the crop box and validate recovered labels against the Table A1-A5 / Clause 4 Identity Dictionary. Prevent column x-offset from being misparsed as hierarchy indentation.
   - **Stage 3 (Targeted VLM Visual Inspection):** Use local VLM inspection only for unresolved visual properties (e.g., arrowhead presence/absence, callout leader targets, weld cross-section shading), recording the observation with model fingerprint, image hash, and `knowledge_eligible=false`.

3. Preserve real source anomalies transparently in the Evidence Graph:
   - Never silently "fix" or hide discrepancies printed in the AWS A3.0:2020 PDF. Record the literal printed string in the Evidence Graph and attach a documented cross-reference to the canonical entity:
     - **Table A2 (printed p. 71, PDF index 83):** Prints `metal power cutting` for `OC-P` (canonical: `metal powder cutting` in Table A1 p. 70, Table A3 p. 73, and Clause 4 p. 39).
     - **Table A2 (printed p. 72, PDF index 84):** Prints `EW-PC` for `pressure-controlled resistance welding` (canonical: `RW-PC` in Table A1 p. 70, Table A3 p. 73, Figure A1 p. 75, and Clause 4 p. 45).
     - **Figure A6 Legend (printed p. 79, PDF index 91):** Lists `AB` as `arc brazing` (and shows `AB` under `Electrical -> Arc -> Flux/Gas` in the chart), whereas Table A1 (p. 69), Table A2 (p. 71), Table A3 (p. 72), Figure A1 (p. 75), and Clause 4 (p. 7) assign `AB` to `adhesive bonding`, and Clause 4 (p. 22) notes `electric brazing. A nonstandard term for arc brazing and resistance brazing`.
     - **Figure A1 Copyright Footer (printed p. 75, PDF index 87):** Embedded chart graphic retains small footer text `A3.1:2010` inside the 2020 edition page.
     - **Annex B Normative Status Conflict:** Table of Contents (printed p. ix, PDF index 9) labels `Annex B (Informative)—Figures`, Foreword (printed p. viii, PDF index 8) states Annex B figures are examples only, while the Annex B divider page (printed p. 81, PDF index 93) prints `Annex B (Normative) Figures — This annex is part of this standard and includes mandatory elements for use with this standard`.

4. Establish each new figure in three sequential gates:
   - **Gate A (Text & Identity):** 100% of printed labels, designations, footnotes, and legend rows resolve in the Identity Dictionary.
   - **Gate B (Single-Hop Relationships):** Enclosure, physical connectors, and candidate indentation edges pass deterministic single-hop QA.
   - **Gate C (Multihop & Cross-Modal Joins):** Path queries and Clause 4 / Table A1 cross-modal joins pass with full epistemic qualification.

## Gotchas

- Never mix nodes from adjacent figures on the same page (such as Figure A2 and Figure A3 on printed p. 76); enforce strict crop boundaries before extraction.
- Never conflate PDF vector line geometry with vector embeddings.
