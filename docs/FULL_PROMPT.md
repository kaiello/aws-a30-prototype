# Full Production Master Prompt: AWS A3.0M/A3.0:2020 Figure-by-Figure Multimodal RAG Engine

> **Document Type:** Production Master Specification & Agent Operating Prompt  
> **Release Version:** `v1.0.0-aws-a30-complete` (Hardened in Gate 5)  
> **Standard:** AWS A3.0M/A3.0:2020 (*Standard Welding Terms and Definitions Including Terms for Adhesive Bonding, Brazing, Soldering, Thermal Cutting, and Thermal Spraying*, 13th Edition)  
> **Source PDF SHA-256:** `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`  
> **Verification Status:** Fully Verified against Canonical Stores, Multi-Model Benchmarked (100.0% Pass across all 5 dimensions), Zero Fallbacks, Hardened & Grounded

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
- **Remote Repository:** https://github.com/kaiello/aws-a30-prototype
- **Active Release Tag:** `v1.0.0-aws-a30-complete`
- **Google Drive Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror`)
- **Python Environment:** Python 3.12.7 (Always use `python -B -m ...` or `pytest`; do **not** use `poetry`).
- **Source Standard PDF:** `data/AWS_A3.0_2020.pdf`
- **Verified Page Coordinate Invariant:** 
  $$\text{printed\_page} = \text{pdf\_index} - 12 = \text{viewer\_page} - 13$$
  *(Verified from stores: Clause 4 begins at PDF index 17 / printed page 5; Annex A begins at PDF index 83 / printed page 71; Annex B begins at PDF index 94 / printed page 82; Annex C begins at PDF index 171 / printed page 159; Annex D begins at PDF index 177 / printed page 165).*

---

## 3. Canonical Knowledge Stores & Cryptographic Proofs

All 7 canonical stores from Phases 0 through 3 are **strictly immutable** and locked to their SHA-256 hashes:

| Canonical Store Artifact | Relative Repository Path | Locked SHA-256 Checksum | Normative Scope |
|---|---|---|---|
| `AWS_A3.0_2020.pdf` | `data/AWS_A3.0_2020.pdf` | `205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d` | Authoritative standard document (190 pages) |
| `glossary_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `e88a2fd4b8a0be47d1691cceb495d89ec4d4e25fad7c7d1d1f5e36c46d5b629b` | 1,607 terms, 378 underlines, 458 margin bars, 311 nonstandard redirects |
| `annex_c_d_store.json` | `storage/evidence_v2/clause4_ingest_001/` | `8b5d8faae9c42c27ac20b75f3bb2ac0f804957770b13e295d1926972ede07266` | Annex C (8 decisions, pp. 159–164) & Annex D (6 tables, 591 modification rows, pp. 165–170) |
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

- **Slice A: Annex A Classification Charts & Decision Trees (`Figures A1–A6`):** Multi-hop characteristic path tracing; 5 circles on A1, 7 on A2, 3 major joining methods on A3 with Footnote a, 26 fusion circles on A4, solid-state branching on A5 (CW direct pressure/deformation bypassing thermal source), and 48 circle branches with 21 legend items on A6 (`AB` = arc brazing, `B-CA` = controlled-atmosphere brazing in Figure A6 legend).
- **Slice B: Normative Tables (`Tables A1–A5`):** Letter designations and hierarchy indentation (Table A1), alphabetical lookups (Tables A2 & A3), standard suffix modifiers (Table A4: `-MA`, `-SA`, `-ME`, `-AU`, `-RO`, `-AD`), and obsolete processes (Table A5, e.g. `B-CA` = carbon arc brazing).
- **Slice C: Clause 4 Terms & Definitions:** 1,607 entries, grammatical parts of speech, domain/sense delimiters (`[pipe]`, `[plate]`), 378 underlines, 458 margin bars, 311 lightface nonstandard redirects (`NONSTANDARD_SYNONYM_OF`), and 265 / 265 resolved figure back-links.
- **Slice D: Dual-Provenance `IS_A` Promotions & Annex C/D:** Strict dual-provenance rule (`rule_id: dual-provenance-is-a-1`): promoted only if indented in Table A1 AND defined as *"A variation of [parent]..."* in Clause 4 (35 promoted, 83 retained as candidate); Annex C decisions (`C1.5.1–C1.5.8`) and Annex D historical modifications (`Tables D1–D6`).
- **Slice E: Annex B Archetype 3 Spatial Callouts (`Figures B1–B43, B46–B48, B52`):** Joint types, sub-panels, applicable welds, numbered callout keys (e.g. 13-crack key in B33, 10 FSW keys in B46), multi-page continuations (B6 is 3 pages; B12 is 1 page), and sanitized text spans (control characters and running headers stripped).
- **Slice F: Annex B Archetype 4 Waveforms (`Figures B44, B45, B49–B51, B53, B54`):** Synchronized vertical parameter traces plotted against `TIME`; single-pulse (B50) vs pulsation (B49); 5 synchronized traces and pulse sub-intervals (`HIGH PULSE TIME`, `LOW PULSE TIME`) in B53; coast-down vs motor drive in B44 vs B45; cycle intervals in B54.

---

## 5. Strict Anti-Drift Epistemic Discipline & Zero-Fallback Invariant

1. **Zero Oracle Leakage Invariant:** `answer_whole_standard_question(question_text: str)` accepts only question text (+ optional engine handles). No benchmark metadata (`qid`, `question_id`, `slice`) may be inspected.
2. **Zero Hardcoded Question IDs:** Negative regex grep `QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]` across `src/` and `eval/*.py` must yield 0 matches.
3. **Zero Canned Prose & Zero Silent Fallbacks:** All answers must be dynamically constructed from live graph extractions. If a required field or node is missing from a store, the engine must raise or return `INSUFFICIENT_EVIDENCE` rather than masking data loss with a hardcoded fallback string.
4. **Epistemic Layering:** Only vector/normative corroborated edges may be `ACCEPTED`; layout indentations remain `CANDIDATE`.
5. **Contract Preflight:** `python -B -m src.evidence_chart_preflight` must pass all 11/11 contract checks returning `{"status": "CLEAR_REAL_ENTRY_CONTRACT", "new_model_calls": 0}`.

---

## 6. Multi-Route Planning & Evaluation Engine

- **Route 1 (`DeterministicQuestionPlanner`):** 0-LLM, sub-millisecond dispatch (0.21 ms/query), $0.00 compute cost, 0 network calls, 100.0% accuracy across all 5 dimensions.
- **Route 2 (`DeepSeekQuestionPlanner`):** Bounded live LLM query planner with structured JSON action grammar (`deepseek-flash` / `DeepSeek-V4.1-Flash-1017`), offline replay capability, 100.0% accuracy across all 5 dimensions.
- **Route 3 (Configured Providers):** `OpenAI API`, `Anthropic API`, `Gemini API` — cleanly audited; report `SKIPPED_NO_API_KEY` when keys are unconfigured.

---

## 7. Developer Runbook & Verification Commands

```powershell
# 1. Full Pytest Regression Suite
python -B -m pytest -q

# 2. Real-Entry Contract Preflight
python -B -m src.evidence_chart_preflight

# 3. Whole-Standard Multi-Model Acceptance Bakeoff
python -B eval/run_phase4_bakeoff.py

# 4. Anti-Drift Invariant Grep Check
git grep -E "QA002|HO002|CQ-0|DEV001|C4-QA001|B1-QA|B49-QA|P3-S[1-4]-|G4-B[0-3]" -- src/ eval/*.py

# 5. Synchronize Google Drive Mirror
python -B -m src.sync_drive_mirror
```
