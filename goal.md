# AWS A3.0M/A3.0:2020 Multimodal RAG — End Goal & Production System Architecture (`goal.md`)

**Target Standard:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition, 190 PDF pages)  
**Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
**Coordinate Formula:** $\text{printed\_page} = \text{pdf\_index} - 12 = \text{viewer\_page} - 13$ (for main text & annexes starting at Clause 1, printed p. 1 = PDF index 13)  
**Repository:** `https://github.com/kaiello/aws-a30-prototype`  
**Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype`  

---

## 1. What the End Product Is

The end product is a **hardened, zero-hallucination, multimodal Question-Answering (QA) and Reference System** for the complete `AWS A3.0M/A3.0:2020` standard. Instead of a conventional vector-chunk RAG chatbot that guesses answers from fragmented text snippets, this system transforms every word, normative table, decision tree, spatial callout diagram, and cycle waveform in the 190-page PDF into a **cryptographically locked, cross-linked Knowledge Graph**.

When an engineer, welding inspector, student, or automated agent asks a question—whether phrased using formal standard terminology, shop-floor slang, historical nomenclature, process abbreviations, or ID-free natural language—the system delivers:

1. **A 100% Store-Backed, Zero-Fallback Answer:** Every fact, taxonomy path, table designation, and diagram interval is composed directly from locked canonical JSON/SQLite stores. If a required field is missing or corrupted, the system strictly raises or returns `INSUFFICIENT_EVIDENCE` rather than emitting fallback prose.
2. **Exact Triple-Coordinate & Visual Provenance:** Every response cites the exact **Printed Page Number**, **PDF Page Index**, and **300-DPI Isolated Diagram Crop (PNG with locked SHA-256 digest)** so a human reviewer can verify the primary source in seconds.
3. **Dual-Layer Epistemic Transparency (`ACCEPTED` vs. `CANDIDATE` vs. `IS_A`):**
   - `ACCEPTED`: Facts physically proven by PDF vector geometry, explicit table cells, or Clause 4 boldface definitions.
   - `CANDIDATE`: Visually implied layout relationships (such as uncorroborated table row indentations, retained with `knowledge_eligible=False`).
   - `IS_A_PROCESS_VARIATION_OF`: Strictly promoted taxonomy edges (`35` promoted, `83` retained as `CANDIDATE`) requiring dual-provenance corroboration across both `Table A1` and `Clause 4` genus-differentia definitions.
4. **Deterministic Semantic Query Expansion & ID-Free NLQ Understanding (Gate 5.3):**
   - Users do **not** need to know figure numbers (`Figure A5`, `Figure B49`), table numbers (`Table A4`), or exact headword orthography.
   - An offline, store-derived **Semantic Expansion Engine (`src/semantic_nlq_expander.py`)** automatically resolves process abbreviations (`SMAW`, `GTAW-P`, `FCAW-S`, `CW`, `AB`), Annex C nonstandard shop terms (*"stick electrode"*, *"button weld"*), Annex D historical terms (*"heliarc"*, *"atomic hydrogen welding"*, *"forge welding"*), morphological inflections (*"kerfs"* $\rightarrow$ *"kerf"*), and conceptual figure/table signatures into a verifiable `semantic_expansion_trace`.
5. **Adversarial & Scope-Boundary Immunity (Gate 5):**
   - Out-of-range coordinates (e.g., `Figure A7`, `Figure B55`, `Table A6`) are deterministically rejected with `REFUSAL_OUT_OF_RANGE`.
   - Taxonomic false premises (e.g., claiming `SMAW` is a Solid-State Welding process) are refuted with exact chart provenance (`CONTRADICTION_REFUTED`).
   - Unstandardized or fabricated terms (e.g., *"hyper-flux welding"*, *"cryo-ionic brazing"*) return `NOT_IN_STANDARD`.
   - Out-of-scope engineering queries (e.g., filler metal tensile/yield strength values, Charpy impact toughness, preheat schedules, or external ASME/AWS D1.1 construction codes) are cleanly refused with `REFUSAL_OUT_OF_SCOPE`.
6. **Two Operating Speeds:**
   - **Offline Deterministic Route (`DeterministicQuestionPlanner` + `SemanticNLQExpander`):** Answers structured, paraphrased, and multi-hop natural language queries in $< 1\text{ ms}$ at $\$0.00$ cost with socket-guarded zero network access (`CLEAR_WHOLE_STANDARD_CONTRACT`).
   - **Live LLM Planner Route (`DeepSeekQuestionPlanner` / Multi-Model Bakeoff):** Translates complex, open-ended conversational questions into validated AST lookup plans (`temperature=0`, `0` retries) executed against the same immutable stores.

---

## 2. How Multimodal Ingestion & Runtime Retrieval Work

### Stage 1: Pre-Computed Multimodal Knowledge Graph (Locked Canonical Stores)

The 190-page standard is partitioned into **4 Visual Archetypes** plus the **Clause 4 / Annex C / Annex D Lexical & Taxonomic Stores**:

| Structural Slice | AWS A3.0M/A3.0:2020 Scope | Printed Pages (PDF Indices) | What Is Extracted & Verified |
| :--- | :--- | :--- | :--- |
| **Archetype 1: Box Indentation Charts** | `Figures A1, A2, A3` | pp. 75–76 (PDF 87–88) | Enclosing boxes, physical vector connectors, candidate row indentations, footnotes, and explicit cross-chart pointers (`See Figure A4/A5/A6`). |
| **Archetype 2: Characteristic Decision Trees** | `Figures A4, A5, A6` | pp. 77–79 (PDF 89–91) | 5-column characteristic classification trees (`Energy Source` $\rightarrow$ `Thermal Source` $\rightarrow$ `Loading` $\rightarrow$ `Shielding/Flux` $\rightarrow$ `Process`), `96` numbered process circles, `59` bottom legend rows, and multi-branch process paths. |
| **Normative Process Tables** | `Tables A1–A5` | pp. 69–74 (PDF 81–86) | `138` Table A1 rows, `133` Table A2 rows, `134` Table A3 matrix rows, `6` Table A4 adaptive/mechanized/automatic/robotic/manual letter suffixes, and `13` Table A5 obsolete designations, plus 4 documented source anomalies (including `AB` = arc brazing vs. adhesive bonding). |
| **Clause 4 Glossary & Dual-Provenance `IS_A`** | `Clause 4` + `Annex C` + `Annex D` | pp. 5–67, 159–170 (PDF 17–79, 171–182) | `1,607` glossary entries (`1,345` standard boldface, `262` nonstandard lightface), `311` `NONSTANDARD_SYNONYM_OF` edges, `378` underline & `458` margin-bar 2020 revision markers, `21` Annex C clauses (`8` editorial decisions), `591` Annex D historical rows, and `35` dual-provenance `IS_A_PROCESS_VARIATION_OF` promotions. |
| **Archetype 3: Spatial Callout Diagrams** | `Figures B1–B43, B46–B48, B52` (`49` figure units) | pp. 82–147, 151–152, 156 (PDF 94–159, 163–164, 168) | Multi-panel weld joint/groove/crack/position drawings (`80` high-res 300-DPI crops), sub-panels `(A)–(G)`, arrow/leader-line callouts, numbered key legends (e.g., `B33` 1–13 crack keys, `B46` 1–10 FSW keys), and multi-page continuations (`B6`, `B8`, `B17`, `B19`, `B20`, `B22`). |
| **Archetype 4: Cycle & Waveform Plots** | `Figures B44–B45, B49–B51, B53–B54` (`7` figure units) | pp. 148–150, 153–155, 157 (PDF 160–162, 165–167, 169) | Temporal cycle sequences (`SQUEEZE` $\rightarrow$ `WELD` $\rightarrow$ `HOLD` $\rightarrow$ `OFF`, upslope/downslope, pulsed spray waveforms) and physical trace relationships (`CURRENT`, `FORCE`, `VOLTAGE` vs. `TIME`). |

---

### Stage 2: 5-Step Runtime NLQ & Multi-Hop Execution Pipeline

When a user submits a natural language question at runtime, the system executes a deterministic 5-step pipeline:

$$
\text{Raw NLQ} \longrightarrow \text{[1. Semantic Expander]} \longrightarrow \text{[2. Question Planner]} \longrightarrow \text{[3. AST Plan Compiler]} \longrightarrow \text{[4. Multi-Hop Graph Executor]} \longrightarrow \text{[5. Zero-Fallback Composer]}
$$

1. **Semantic NLQ Expansion (`src/semantic_nlq_expander.py`):**
   - Normalizes morphology, punctuation, and hyphenation across the 1,607 Clause 4 terms.
   - Pivots nonstandard Annex C terms, historical Annex D terms, and Table A1/A2/A4/A5 process/suffix codes to their canonical entities.
   - Resolves ID-free conceptual descriptions (e.g., *"upslope and downslope intervals"*, *"edge shape diagram"*, *"letter suffixes for automatic welding"*) to their exact target `Figure` or `Table` via an in-memory inverted index over titles, callouts, waveform traces, and Clause 4 `See Figure/Table` back-links.
   - Emits an auditable `semantic_expansion_trace`.
2. **Boundary & Intent Planning (`Planner`):**
   - Screens for out-of-range coordinates (`REFUSAL_OUT_OF_RANGE`), out-of-scope fabrication/mechanical code queries (`REFUSAL_OUT_OF_SCOPE`), and unstandardized terms (`NOT_IN_STANDARD`).
   - Emits a structured JSON operation plan targeting 1 to 4 sequential store lookups.
3. **AST Plan Compilation & Guardrails (`Compiler`):**
   - Validates every requested operation against the schema contract, ensuring `operations_count` $\ge 1$ and `0` blocked actions.
4. **Multi-Hop Cross-Store Graph Execution (`Executor`):**
   - Traverses across stores (`Clause 4` $\leftrightarrow$ `Annex C/D` $\leftrightarrow$ `Tables A1–A5` $\leftrightarrow$ `Figures A1–A6` $\leftrightarrow$ `Figures B1–B54`), chaining outputs from Hop $k$ into Hop $k+1$ and recording a complete `hop_trace`.
5. **Zero-Fallback Deterministic Composition (`Composer`):**
   - Assembles the final response strictly from retrieved store fields (enforced by static AST inspection banning `.get(key, "literal")` fallbacks) and attaches printed page numbers, PDF indices, and 300-DPI crop provenance.