# AWS A3.0M/A3.0:2020 Multimodal RAG — Continuation Packet & Handoff Guide

**Document Purpose:** Complete, self-contained handoff and technical onboarding packet for the next engineering agent to resume and advance the AWS A3.0M/A3.0:2020 source-aware multimodal graph ingestion and retrieval system.

---

## 1. Executive Summary & Current System Baseline

- **Standard Document:** `AWS A3.0M/A3.0:2020` (*Standard Welding Terms and Definitions*, 190 PDF pages / 162 ingested canonical store pages)
- **Current Production Release Tag:** `v1.6.4.1-provenance-integrity` (on `main`)
- **Working Tree Status:** `CLEAN`, `0` uncommitted files, synchronized with remote `origin/main`
- **Full Regression Test Suite:** **`1,514 passed, 8 skipped, 0 failures, 0 warnings`** (1,522 total tests)
- **Cryptographic Immutability Ledger:** **51 / 51 Locked SHA-256 Artifacts (`MATCH` across 45 baseline + 6 quarantined planner fixtures)**
- **Canonical Repository:** `C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest`
- **GitHub Remote:** [`https://github.com/kaiello/aws-a30-prototype.git`](https://github.com/kaiello/aws-a30-prototype.git) (`origin`)
- **Google Drive 1:1 Mirror:** `G:\My Drive\git_projects\aws-a30-prototype` (synchronized via `python -B -m src.sync_drive_mirror --target "G:\My Drive\git_projects\aws-a30-prototype"`)
- **Python Runtime:** Python 3.12.7 on Windows (PowerShell shell; use `python -B -m ...` or `pytest`). Note: ignore harmless `posh-git` profile warning on command start.

---

## 2. Gate 6.3 Achievements & Key Code Assets

Gate 6.3 established an authoritative 20-question blind holdout benchmark (`Q01`–`Q20`), combining 10 user-provided expert questions with 10 blind examiner questions:

1. **Blind Hardening Benchmark Suite ([`storage/evidence_v2/phase6_3_blind_hardening_001/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/)):**
   - [`questions.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/questions.json): SHA-256 `be8ee997284de16cb367042a09206d77950344b59f14c68f5ba9ac0123141b5b`
   - [`rubric.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/rubric.json): SHA-256 `a575cd1833cd2d041b6359abdadeff71a728430e155d49d8bdf70205e50ff22c`
   - [`results.json`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/phase6_3_blind_hardening_001/results.json): SHA-256 `18f247c1abb8b96d0a52081e0f8fabb32a74dcaced77143bf9ece518cd19c4c2`
   - Score: **20 / 20 (100.0%) PASS** under socket isolation (`socket.socket` monkeypatched to block network access).
2. **Dynamic Process Variation Grammar ([`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py)):**
   - Tables A1–A3 process variations (`GMAW-S`, `GTAW-P`, `PAW`, `EBW-HV`, `FLSP-P`, `FRW-DD`, `HIPW`, `OFC-A`) are now recognized as valid `PROCESS_CODE` entities in the lexicon.
   - Suffix parsing bifurcates process variation letters from Table A4 compound application modes (`-MA`, `-SA`, `-ME`, `-AU`, `-RO`, `-AD`).
3. **Embedded Lightface Nonstandard Term Resolution ([`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py), [`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py), [`src/evidence_clause4_glossary.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_clause4_glossary.py)):**
   - Embedded multi-word lightface terms (`ground clamp`, `ground lead`, `welding ground`, `silver soldering`) resolve to standard terms (`workpiece connection`, `workpiece lead`, `silver brazing`) without hardcoded overrides.
4. **AST Zero-Fallback Expansion Across 12 Functions ([`tests/test_gate_6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_3_blind_hardening.py#L168-L214)):**
   - Scanned all 12 composer/executor functions (`_compose_annex_a_chart_answer`, `_compose_normative_tables_answer`, `_compose_waveform_phase4_answer`, `_exec_lookup_taxonomy_subtypes`, `_exec_expand_cross_references`, `_exec_weld_position_sense`, `_exec_disambiguate_homograph`, `_exec_compound_lookup_and_validation`, `_exec_compare_historical_and_active`, `_exec_polysemous_diagram_and_glossary`, `execute_whole_standard_plan`, `_exec_decode_process_designations`).
   - Verified 0 `.get(k, "non-empty literal")` fallbacks and 0 domain ternary fallbacks.
5. **Evaluation Script:** [`eval/run_phase6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/eval/run_phase6_3_blind_hardening.py) supports `--benchmark-dir` and `--no-write`.
6. **Documentation & Deliverables:**
   - [`GATE_6_3_CHECKOUT_CARD.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_3_CHECKOUT_CARD.md)
   - [`GATE_6_4_CHECKOUT_CARD.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_4_CHECKOUT_CARD.md)
   - [`GATE_6_4_1_CHECKOUT_CARD.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/GATE_6_4_1_CHECKOUT_CARD.md)
   - [`ROADMAP.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md) (updated to baseline 1,514 passed / 1,522 total tests, 51 hashes: 45 baseline + 6 quarantined planner fixtures)
   - [`goal.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md) & [`docs/goal.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/docs/goal.md)
   - Q&A Reports: [`C:\Users\kenai\Downloads\hardening_questions_full_20.docx`](file:///C:/Users/kenai/Downloads/hardening_questions_full_20.docx) and [`.md`](file:///C:/Users/kenai/Downloads/hardening_questions_full_20.md).

---

## 3. Strict Architectural Invariants & Guardrails (DO NOT VIOLATE)

Any subsequent agent modifying this codebase must adhere strictly to these CI-enforced rules:

1. **Zero Benchmark-ID & Trap-Literal Hardcoding (`tests/test_gate_5_hardening.py`, `tests/test_gate_6_3_blind_hardening.py`):**
   - Never write literal benchmark question IDs (`QA*`, `HO*`, `G4-B*`, `G5-ADV*`, `G55-NLQ*`, `G60-*`, `G61-*`, `G62-*`, `G63-*`) into `src/*.py` or `eval/*.py`.
   - Never hardcode trap/refusal strings (`hyper-flux`, `laser-quantum`, `cryo-ionic`, `ASME Section IX`, `yield strength`, `E7018`) in `src/*.py`.
2. **AST Zero Silent Fallbacks:**
   - Never use `.get(key, "canned fallback string")` in composer or executor functions. If store data is missing, raise `ValueError("INSUFFICIENT_EVIDENCE: ...")`.
3. **Cryptographic Immutability of Released Artifacts (`ALL_45_LOCKED_HASHES`):**
   - The 45 locked artifacts in `storage/` and `data/AWS_A3.0_2020.pdf` are **100% read-only**. Never mutate an existing `*_001` store or results file.
4. **Epistemic Quarantine of Model Traces:**
   - Any LLM reasoning or candidate detection (`DeepSeek-V4.1`) must carry `authority: "UNVERIFIED_MODEL_TRACE_NOT_EVIDENCE"` and `knowledge_eligible=False`. It must never enter final normative answers or citations.
5. **Modality-Appropriate Diagram Crops:**
   - Answers must set `requires_diagram_crop: True` and attach a 300-DPI PNG crop **if and only if** the evidence derives from a visual diagram (`Figures A1–A6`, `Figures B1–B54`). Text-only lookups (`Clause 4`, `Tables A1–A5`, `Annex C/D`) must set `requires_diagram_crop: False` and omit crops.
6. **Strict Offline Test & Evaluation Execution:**
   - Automated tests and benchmarks must pass with `socket.socket` completely blocked (`0` network calls).

---

## 4. Candidate Workstreams for Gate 6.4

The next agent should select and execute one of the following high-value workstreams:

### Candidate Workstream A: Offline DeepSeek-V4.1 Replay Suite Expansion for Gate 6.3 Queries
- **Goal:** Expand offline content-addressed replay cassettes in `storage/model_replays/deepseek_v4_1_flash_1017/` to cover complex multi-hop blind hardening queries (e.g., Q04 brazing vs bronze welding, Q09 BB/CAW-S obsolete classifications, Q17 AB homographs), expanding from 14 to 18–20 replay cassettes.
- **Benefits:** Validates Layer 4 planner decomposition over the net-new Gate 6.3 compound and nonstandard paths under strict socket quarantine.

### Candidate Workstream B: Table A3 Process Matrix & Consumable Cross-Store Joins
- **Goal:** Ingest and cross-reference Table A3 (*Alphabetical Cross-Reference to Tables A1, A2, and Figures A4, A5, A6*) with consumable categories (bare electrode, covered electrode, flux, shielding gas) and automated multi-hop traversal.
- **Benefits:** Unlocks questions regarding welding consumables and multi-table matrix lookups.

### Candidate Workstream C: Annex B Spatial Callout Deep Traversal (Figures B33 & B46)
- **Goal:** Enable multi-hop semantic querying over Figure B33 (13 crack locations: toe crack, underbead crack, crater crack, root crack) and Figure B46 (10 FSW weld zones: TMAZ, HAZ, nugget/stir zone) linked with Clause 4 definitions and high-res diagram crops.
- **Benefits:** Fulfills complex welding inspection and defect analysis workflows.

### Candidate Workstream D: Whole-Standard CLI & Agent Skills Enhancement
- **Goal:** Update `.agents/skills/` playbooks and `src/evidence_whole_standard_cli.py` to expose the new Gate 6.3 capabilities (`--ner`, `--route`, `--expand`, `--ask`) with full JSON/Markdown rendering.
- **Benefits:** Empowers external agents and CLI users to interact with the whole-standard knowledge graph.

---

## 5. Step-by-Step Execution Protocol for the Next Agent

When initiating the next workstream, follow this exact sequence:

1. **Verify Workspace State & Baseline:**
   ```powershell
   cd "C:\Users\kenai\Documents\Codex\2026-10-21\task\aws-a2-source-aware-ingest"
   git status
   git describe --tags  # Must show v1.6.3-blind-hardening
   python -m pytest tests/test_gate_6_3_blind_hardening.py
   ```
2. **Create Workstream Branch:**
   ```powershell
   git checkout -b feat/gate-6-4-<workstream-name>
   ```
3. **Execute Implementation & Hardening:**
   - Implement functionality in `src/`.
   - Update or add tests in `tests/test_gate_6_4_*.py`.
   - Ensure AST zero-fallback compliance across all composer functions.
   - Run anti-drift regex check:
     ```powershell
     python -c "
     import re, pathlib
     p = re.compile(r'\b(G6[0-4]-|QA\d+)\b')
     for d in ['src', 'eval']:
         for f in pathlib.Path(d).glob('*.py'):
             m = p.search(f.read_text(encoding='utf-8'))
             if m: print(f'Drift in {f}: {m.group(1)}')
     "
     ```
4. **Execute Full Test Suite:**
   ```powershell
   python -m pytest -q  # Must show 0 failures, 0 warnings
   ```
5. **Update Documentation & Cryptographic Ledger:**
   - Update `ROADMAP.md` (bump baseline, register Gate 6.4, add new locked artifacts).
   - Update `goal.md` and copy to `docs/goal.md`.
   - Author `GATE_6_4_CHECKOUT_CARD.md`.
6. **Commit, Merge & Tag:**
   ```powershell
   git add -A
   git commit -m "feat(gate-6.4): <summary>"
   git checkout main
   git merge feat/gate-6-4-<workstream-name> --no-ff -m "merge: Gate 6.4 (<release-tag>)"
   git tag -a v1.6.4-<tag> -m "Release v1.6.4"
   git push origin main
   git push origin --tags
   ```
7. **Synchronize Google Drive Mirror:**
   ```powershell
   python -B -m src.sync_drive_mirror --target "G:\My Drive\git_projects\aws-a30-prototype"
   ```

---

## 6. Key Repository File Map

| File / Directory | Purpose & Role |
| :--- | :--- |
| [`src/welding_ner.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/welding_ner.py) | Character-offset Welding NER, 3-tier compound grammar, process variations, homograph tracking |
| [`src/semantic_nlq_expander.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/semantic_nlq_expander.py) | In-memory `SemanticConceptGraph`, see-also hubs, lightface extraction, abbreviation resolver |
| [`src/evidence_phase4_bakeoff.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/evidence_phase4_bakeoff.py) | Question planner, 12 AST-guarded atomic action composers, whole-standard answering engine |
| [`src/deepseek_v41_adapter.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/deepseek_v41_adapter.py) | Layer 4 planner adapter, offline replay cassette harness, epistemic quarantine |
| [`src/sync_drive_mirror.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/src/sync_drive_mirror.py) | Google Drive mirror synchronizer with automatic pruning and `git_state_summary.txt` generation |
| [`storage/evidence_v2/`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/storage/evidence_v2/) | 45 cryptographically locked canonical stores and benchmark suites |
| [`tests/test_gate_6_3_blind_hardening.py`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/tests/test_gate_6_3_blind_hardening.py) | 45-artifact lock verifier, 20-Q offline runner, NER grammar tests, AST static guard |
| [`ROADMAP.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/ROADMAP.md) | Living master roadmap, milestone progression register, and 45-hash immutability ledger |
| [`goal.md`](file:///C:/Users/kenai/Documents/Codex/2026-10-21/task/aws-a2-source-aware-ingest/goal.md) | Architectural specification, 5-stage pipeline documentation, and deliverable checklists |
