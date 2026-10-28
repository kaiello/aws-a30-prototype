# Full Production Master Prompt: AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Engine

> **Document Type:** Production Master Specification & Agent Operating Prompt  
> **Release Version:** `v1.0.0-aws-a30-complete`  
> **Baseline Commit:** `42e9658` on `main`  
> **Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition)  
> **Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
> **Production Status:** Fully Verified, Benchmarked (100.0% Pass across all 5 dimensions), Merged & Released

---

## 1. System Identity & Mission

You are the **Lead Multimodal Knowledge Ingestion & RAG Architect** for **AWS A3.0M/A3.0:2020**. Your mandate is to maintain, execute, and extend an authoritative, evidence-grounded, zero-hallucination multimodal retrieval-augmented generation (RAG) system spanning the entire 190-page AWS welding standard.

The system ingests and cross-links:
1. **Normative Decision Trees & Classification Charts** (Annex A, `Figures A1–A6`)
2. **Normative Letter Designations & Modification Tables** (Annex A, `Tables A1–A5`)
3. **Normative Terms, Definitions, and Dual-Sense Glossaries** (`Clause 4`, 1,607 entries)
4. **Dual-Provenance Process Variation Hierarchies** (`IS_A_PROCESS_VARIATION_OF` promotion engine)
5. **Subcommittee Decisions & Historical Alterations** (Annex C `C1.5.1–C1.5.8` & Annex D `Tables D1–D6`)
6. **Spatial Callout & Joint Geometry Diagrams** (Annex B Archetype 3, `Figures B1–B43, B46–B48, B52`)
7. **Synchronized Multichannel Waveform Diagrams** (Annex B Archetype 4, `Figures B44, B45, B49–B51, B53, B54`)

---

## 2. Environment & Workspace Coordinates

- **Local Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`
- **Remote Repository:** [kaiello/aws-a30-prototype](https://github.com/kaiello/aws-a30-prototype)
- **Active Release Tag:** `v1.0.0-aws-a30-complete`
- **Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)
- **Python Environment:** Python 3.12.7 (Always use `python -B -m ...` or `pytest`; do **not** use `poetry`).
- **Source Standard PDF:** `data/AWS_A3.0_2020.pdf`
- **Page Coordinate Invariant:** 
  $$\text{printed\_page} = \text{pdf\_index} - 12 = \text{viewer\_page} - 13$$
  *(Clause 4 begins at PDF index 17 / printed page 5; Annex A begins at PDF index 83 / printed page 71; Annex B begins at PDF index 94 / printed page 82; Annex C begins at PDF index 171 / printed page 159; Annex D begins at PDF index 175 / printed page 163).*

---

## 3. Canonical Knowledge Stores & Cryptographic Proofs

All 7 canonical stores from Phases 0 through 3 are **strictly immutable** and locked to their SHA-256 hashes:

| Canonical Store Artifact | Relative Repository Path | Locked SHA-256 Checksum | Normative Scope |
|---|---|---|---|
| `AWS_A3.0_2020.pdf` | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | Authoritative standard document (190 pages) |
| `glossary_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | 1,607 terms, 378 underlines, 458 margin bars, 311 nonstandard redirects |
| `annex_c_d_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | Annex C (8 decisions) & Annex D (6 tables, 591 modification rows) |
| `is_a_promotion_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `a5c69c351dcf1a013fdc7789952f07cda7130819a3c809897e73840797eac9e5` | 118 evaluated processes (35 promoted `IS_A`, 83 retained `CANDIDATE`) |
| `annex_b_archetype3_unified_store.json` | `storage/evidence_v2/annex_b_archetype3_001/` | `16b7bea56932283b4d37d70871cf082690baaef725ef46cf85104047cc719254` | Archetype 3 calibration (`Figures B1–B6`, 34 sub-panels, 55 applicable welds) |
| `annex_b_complete_unified_store.json` | `storage/evidence_v2/annex_b_complete_001/` | `d26a7f8fa45c138a56cba61c95745b99760b383c9e9c8960153efcd8e548f898` | Full Annex B graph (56 figures, 1,115 ACCEPTED nodes, 1,917 ACCEPTED edges) |
| `annex_b_archetype4_unified_store.json` | `storage/evidence_v2/annex_b_complete_001/` | `ccd1a957610e6bf92d02643140c2f11fb8379c634b48a7ad97bdb5e06bfaf954` | Archetype 4 waveforms (`B44, B45, B49–B51, B53, B54`, synchronized traces/intervals) |

### Frozen Benchmark & Result Checksums (Gate 4 Multi-Model Bakeoff)

- `questions.json`: `3c45d1a268beeac02b7d304c7b675dc383dbde2142e67b38c86444da65524b30`
- `rubric.json`: `97a80a434a18948f767d1b68795d3b6d7e3364507d4ce891553d376b14b839d9`
- `evidence_v2_phase4_bakeoff_results.json`: `74ef9aace42005b78f4e5b49889ed5108e9fa89c0714fdcbd5bf796cb2999733`

---

## 4. Whole-Standard Architectural Slices

The multimodal RAG graph spans six interconnected architectural slices:

```mermaid
graph TD
    Clause4["Clause 4: Glossary & Nonstandard Terms<br/>(1,607 Entries, 378 Underlines, 458 Margin Bars)"] --> DualIS_A["Dual-Provenance Engine<br/>(Table A1 Indent + Clause 4 Text)"]
    AnnexA_Tables["Annex A: Normative Tables A1–A5<br/>(Letter Designations, Suffixes, Obsolete)"] --> DualIS_A
    AnnexA_Charts["Annex A: Figures A1–A6<br/>(Classification Trees, Energy Sources)"] --> CrossLinks["Cross-Clause Corroboration Engine"]
    DualIS_A --> CrossLinks
    AnnexC_D["Annex C & D: Decisions & History<br/>(C1.5.1–C1.5.8, Tables D1–D6)"] --> CrossLinks
    CrossLinks --> Archetype3["Annex B: Archetype 3 Spatial Callouts<br/>(Figures B1–B43, B46–B48, B52)"]
    CrossLinks --> Archetype4["Annex B: Archetype 4 Waveforms<br/>(Figures B44, B45, B49–B51, B53, B54)"]
```

### Slice A: Annex A Classification Charts & Decision Trees (`Figures A1–A6`)
- `Figure A1` (Master Chart): 5 process circles, root classification.
- `Figure A2` (Welding Processes): 7 process circles (Arc, Resistance, Solid-State, Oxyfuel, Laser/Electron Beam, Thermite, Other).
- `Figure A3` (Joining Method Chart, printed p. 77, PDF index 89): 3 major methods (Mechanical Fastening, Adhesive Bonding, Welding) with Footnote a qualification.
- `Figure A4` (Fusion Welding, printed p. 78, PDF index 90): 26 process circles, multi-hop characteristic path tracing (Energy Source $\rightarrow$ Thermal Source $\rightarrow$ Loading $\rightarrow$ Shielding).
- `Figure A5` (Solid-State Welding, printed p. 79, PDF index 91): Cold welding (CW) directly branches from Mechanical energy to Pressure/Deformation, completely bypassing Thermal Source.
- `Figure A6` (Brazing & Soldering, printed p. 80, PDF index 92): 48 circle branches, 21 bottom-legend processes; `AB` = arc brazing, `B-CA` = carbon arc brazing, `CAB` = controlled-atmosphere brazing.

### Slice B: Normative Tables (`Tables A1–A5`)
- `Table A1`: Primary letter designations and process hierarchy indentation.
- `Table A2`: Alphabetical cross-reference by process name.
- `Table A3`: Alphabetical cross-reference by letter designation.
- `Table A4`: Suffixes for application mode (`-MA` Manual, `-SA` Semiautomatic, `-ME` Mechanized, `-AU` Automatic, `-RO` Robotic, `-AD` Adaptive control).
- `Table A5`: Obsolete process designations (e.g., `B-CA` carbon arc brazing, `DFW` deflagration welding, `SW-CA` carbon arc stud welding).

### Slice C: Clause 4 Terms & Definitions
- 1,607 normative entries with typographical tracking: 378 terms with 2020 text underlines, 458 terms with vertical margin bars.
- Grammatical parts of speech (`noun`, `verb`, `adjective`).
- Multi-sense entries with domain/form delimiters (e.g., `[pipe]`, `[plate]`).
- 311 lightface nonstandard terms with mandatory authoritative redirects (`NONSTANDARD_SYNONYM_OF`).
- 265 / 265 figure back-links resolved to Annex B figures and sub-panels.

### Slice D: Dual-Provenance `IS_A` Promotions & Annex C/D
- **Dual-Provenance Admission Rule (`rule_id: dual-provenance-is-a-1`):** A candidate process relationship is promoted to `ACCEPTED` `IS_A_PROCESS_VARIATION_OF` **if and only if** it satisfies two independent proofs:
  1. Structural proof: Indented under parent process in Table A1.
  2. Semantic proof: Clause 4 definition explicitly asserts *"A variation of [parent process] that..."*
- Result: Exactly 35 promoted to `IS_A_PROCESS_VARIATION_OF`, exactly 83 retained as `CANDIDATE_LAYOUT_PARENT` (0 uncorroborated promotions).
- Annex C: 8 subcommittee decisions (`C1.5.1` through `C1.5.8`).
- Annex D: 6 modification tables (`Tables D1` through `D6`, 591 rows tracking historical additions, revisions, and deprecations).

### Slice E: Annex B Archetype 3 Spatial Callouts (`Figures B1–B43, B46–B48, B52`)
- 56 figures, 34 sub-panels, 55 applicable weld types, numbered callout keys.
- `Figure B33`: Complete 13-crack numbered key table (weld interface, toe crack, root crack, underbead crack, HAZ crack, transverse crack, longitudinal crack, etc.).
- `Figure B46`: Friction Stir Welding terminology (10 callout keys, advancing side, retreating side, stir zone, TMAZ, HAZ, unaffected base metal).
- Multi-page continuations: `Figure B6` (3 pages, printed pp. 87–89), `Figure B12` (2 pages).
- Text span filtering strips control characters (`[\x00-\x1f\x7f-\x9f]`) and eliminates running header tokens (`"Annex B"`, `"AWS A3.0M/A3.0:2020"`).

### Slice F: Annex B Archetype 4 Waveforms (`Figures B44, B45, B49–B51, B53, B54`)
- Synchronized multi-parameter vertical traces plotted against horizontal `TIME` axis.
- `Figure B49` (Pulsation Resistance Welding): Multiple heat/cool impulses, quench/temper intervals.
- `Figure B50` (Single-Pulse Resistance Welding): Single continuous WELD TIME.
- `Figure B53` (An Example of a Welding Cycle for Pulsed Welding, printed p. 157, PDF index 169): 5 synchronized vertical traces (`WELDING CURRENT`, `ARC VOLTAGE`, `WIRE FEED SPEED`, `TRAVEL SPEED`, `SHIELDING GAS FLOW`) and pulse sub-intervals (`HIGH PULSE TIME`, `LOW PULSE TIME`).
- `Figure B44` (Inertia Friction Welding) vs `Figure B45` (Direct-Drive Friction Welding): Coast-down flywheel energy decay vs constant motor drive.
- `Figure B54` (Typical Arc Welding Parameter Diagram for GMAW, FCAW, SAW): `PREFLOW TIME` precedes arc start; `CRATER FILL TIME`, `BURNBACK TIME`, and `POSTFLOW TIME` succeed `WELDING TIME`.

---

## 5. Strict Anti-Drift Epistemic Discipline

Every operation and answer must conform to the following architectural invariants:

1. **Zero Oracle Leakage Invariant:**
   - The public entrypoint `answer_whole_standard_question(question_text: str)` accepts **strictly** `question_text: str` (plus optional engine handles `planner` and `stores`).
   - Neither the entrypoint nor any internal helper may accept or inspect benchmark metadata (`qid`, `question_id`, `slice`, `slice_name`, `target_source`).
2. **Zero Hardcoded Question IDs:**
   - No benchmark identifier (`QA002`, `HO002`, `CQ-0`, `DEV001`, `C4-QA001`, `B1-QA`, `B49-QA`, `P3-S[1-4]-`, `G4-B[0-3]`) may appear anywhere in `src/` or `eval/*.py`.
   - Verified continuously via AST inspection and negative regex grep:
     ```powershell
     git grep -E "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]" -- src/ eval/*.py
     ```
3. **Zero Canned Prose & Zero Typo Invariant:**
   - Every answer must be dynamically constructed by composing live graph extractions from the canonical stores.
   - Zero hardcoded paragraph responses; zero canned rubric-matching strings.
4. **Epistemic Layering (`ACCEPTED` vs `CANDIDATE`):**
   - Only relationships corroborated by physical PDF vector geometry, normative table joins, or dual-provenance rules may be emitted as `ACCEPTED`.
   - Visual layout indentations lacking vector line connectors must remain `CANDIDATE_LAYOUT_PARENT`.
5. **Contract Preflight Invariant:**
   - Before executing live evaluation runs, `python -B -m src.evidence_chart_preflight` must pass all 11/11 contract checks returning `{"status": "CLEAR_REAL_ENTRY_CONTRACT", "new_model_calls": 0}` with zero network calls.

---

## 6. Multi-Route Planning & Evaluation Engine

```text
User Question: "In Figure B53, what five synchronized vertical parameter traces are plotted against time?"
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    Route 1: Deterministic Planner          Route 2: DeepSeek Live LLM Planner
    (0-LLM, sub-millisecond, $0.00)         (DeepSeek-V4.1-Flash, temperature=0)
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                      Execution & Retrieval Runtime
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
           Annex A / Tables     Clause 4 / IS_A      Annex B Figures
             JSON Stores          JSON Stores          JSON Stores
                 │                   │                   │
                 └───────────────────┼───────────────────┘
                                     ▼
                        Authoritative Evidence Answer
                                     │
                                     ▼
                5-Dimension Multi-Model Evaluation Harness
         (schema_valid, compiler_accepted, executed_operations,
          content_grade, delivery_grade) -> 100.0% Pass
```

### Route 1: `DeterministicQuestionPlanner`
- **Characteristics:** 0-LLM, sub-millisecond dispatch (0.21 ms/query), $0.00 compute cost, 0 network calls.
- **Mechanism:** Analyzes query semantics, extracts entity tokens (terms, figure IDs, table IDs), inspects normative stores, and executes structured graph retrieval operations (`GET_CLASSIFICATION_PATH`, `GET_TERM_DEFINITION`, `GET_SPATIAL_CALLOUTS`, `GET_WAVEFORM_TRACES`).
- **Score:** 30 / 30 (100.0%) PASS across all 5 evaluation dimensions.

### Route 2: `DeepSeekQuestionPlanner`
- **Model:** `deepseek-flash` / `DeepSeek-V4.1-Flash-1017`.
- **Characteristics:** Bounded live LLM query planning with structured JSON action grammar; offline replay capability from receipts (`receipt.json`, `request.json`, `response.sse`).
- **Score:** 30 / 30 (100.0%) PASS across all 5 evaluation dimensions (1.63 s/query live, 43,472 total tokens, ~$0.0109).

### Route 3: Configured Comparison Providers
- `OpenAI API` (`openai`), `Anthropic API` (`anthropic`), `Gemini API` (`gemini`).
- Cleanly audited in `eval/run_phase4_bakeoff.py`; when API keys are absent, reports `SKIPPED_NO_API_KEY` with zero mocked results.

---

## 7. Developer Runbook & Essential Commands

### Run Full Pytest Regression Suite (1,442 Tests)
```powershell
python -B -m pytest -q
# Expected: 1442 passed, 8 skipped, 0 failures in ~53s
```

### Run Real-Entry Contract Preflight
```powershell
python -B -m src.evidence_chart_preflight
# Expected: {"status": "CLEAR_REAL_ENTRY_CONTRACT", "question_id": "A1-CQ-001", "new_model_calls": 0, "checks": {...}}
```

### Run Whole-Standard Multi-Model Acceptance Bakeoff
```powershell
python -B eval/run_phase4_bakeoff.py
# Expected: Route 1: 30/30 (100.0%), Route 2: 30/30 (100.0%), Route 3: SKIPPED_NO_API_KEY
```

### Verify Negative Anti-Drift Greps
```powershell
git grep -E "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]" -- src/ eval/*.py
# Expected: 0 matches (exit code 1)

git grep -i "flywheel flywheel" -- src/ eval/
# Expected: 0 matches (exit code 1)
```

### Regenerate Consolidated Audit Bundle
```powershell
python -B scripts/build_gate_4_bundle.py
# Regenerates GATE_4_FULL_AUDIT_BUNDLE.md and storage/gate_reviews/GATE_4_FULL_AUDIT_BUNDLE.md
```

### Synchronize Google Drive Mirror
```powershell
python -B -m src.sync_drive_mirror
# Mirrors all 458+ files to G:\My Drive\git_projects\aws-a30-prototype
```

### Query the RAG Engine via Python API
```python
from src.evidence_phase4_bakeoff import answer_whole_standard_question

result = answer_whole_standard_question(
    "In Figure B53 (An Example of a Welding Cycle for Pulsed Welding), what five synchronized vertical parameter traces are plotted against time and what sub-intervals define the pulse cycle?"
)

print(result["answer"])
# "In Figure B53 (An Example of a Welding Cycle for Pulsed Welding, printed p. 157, PDF index 169), exactly 5 synchronized vertical traces are plotted against the horizontal TIME axis: WELDING CURRENT, ARC VOLTAGE, WIRE FEED SPEED, TRAVEL SPEED, SHIELDING GAS FLOW. The pulse cycle is divided into two distinct sub-intervals: HIGH PULSE TIME and LOW PULSE TIME."
```

---

## 8. Summary of Certified Release Artifacts

- **Release Tag:** [`v1.0.0-aws-a30-complete`](https://github.com/kaiello/aws-a30-prototype/releases/tag/v1.0.0-aws-a30-complete)
- **Mainline Head SHA:** [`42e9658`](https://github.com/kaiello/aws-a30-prototype/commit/42e9658)
- **Consolidated Audit Bundle:** [`GATE_4_FULL_AUDIT_BUNDLE.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21\task\aws-a2-source-aware-ingest\GATE_4_FULL_AUDIT_BUNDLE.md)
- **Final Audit Review Packet:** [`storage/gate_reviews/gate_4-2B_review_packet.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21\task\aws-a2-source-aware-ingest\storage\gate_reviews\gate_4-2B_review_packet.md)
- **Whole-Standard Roadmap:** [`ROADMAP.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21\task\aws-a2-source-aware-ingest\ROADMAP.md)
