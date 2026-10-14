# AWS A3.0 Multimodal Prototype Benchmark Report (Card 08 - Answer Routes & Context-Bench)

**Date:** 2026-10-14 13:19:40 UTC
**Inference Engine:** DEEPSEEK (`deepseek-chat`)
**Retrieval Mode:** mix
**Total Queries Evaluated:** 50
**Total Passed:** 50 / 50 (100.0%)

## Context-Bench Multi-Stage Retrieval Metrics

Adopting the evaluation framework from Perplexity Research & Turbopuffer (*Contextual Embedding: Beyond the Gold Passage*):

| Context-Bench Metric | Tested | Passed / Score | Rate | Capability Tested |
|---|:---:|:---:|:---:|---|
| **Document@1** | 50 | 41 | **82.0%** | Document Disambiguation & Strict Scope Boundaries |
| **Answer@1** | 50 | 50 | **100.0%** | Primary Answer-Bearing Chunk Retrieval |
| **Evidence Recall@K** | 50 | — | **99.0%** | Supporting Evidence Completeness (Figures, Tables, Callouts) |
| **All-Evidence@10** | 50 | 49 | **98.0%** | Complete Answer Route Bundle Recovery |
| **Epistemic Provenance Score** | 50 | — | **0.996 / 1.000** | Unbroken Bridges to Normative Evidence Nodes |

## Performance by Modality

| Modality | Tested | Passed | Pass Rate |
|---|:---:|:---:|:---:|
| Text | 8 | 8 | 100.0% |
| Nonstandard | 5 | 5 | 100.0% |
| Table | 7 | 7 | 100.0% |
| Figure | 18 | 18 | 100.0% |
| Cross-modal | 2 | 2 | 100.0% |
| Qualifier | 2 | 2 | 100.0% |
| Abstention | 8 | 8 | 100.0% |

## Detailed Query Results & Answer Route Manifest

| ID | Modality | Result | Doc@1 | Ans@1 | Evid Recall | Evidence Items | Citations Found |
|---|---|:---:|:---:|:---:|:---:|---|---|
| Q01 | text | ✅ PASS | ✅ | ✅ | 1.00 | 10 items | Figure B26, Figure B13, Annex B |
| Q02 | nonstandard | ✅ PASS | ✅ | ✅ | 1.00 | 14 items | Figure B6, Clause 4 |
| Q03 | table | ✅ PASS | ✅ | ✅ | 1.00 | 24 items | Figure A1, Table A1, Annex A |
| Q04 | table | ✅ PASS | ✅ | ✅ | 1.00 | 20 items | Figure A1, Table A1, Annex A |
| Q05 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 12 items | Figure B5, Annex B |
| Q06 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 17 items | Figure B4, Annex B |
| Q07 | cross-modal | ✅ PASS | ✅ | ✅ | 1.00 | 15 items | Figure B20, Clause 4, Annex B |
| Q08 | cross-modal | ✅ PASS | ✅ | ✅ | 1.00 | 18 items | Figure B6, Annex B |
| Q09 | qualifier | ✅ PASS | ✅ | ✅ | 1.00 | 17 items | Clause 4, Annex B |
| Q10 | qualifier | ✅ PASS | ✅ | ✅ | 1.00 | 3 items | Clause 4, Annex B |
| Q11 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | None |
| Q12 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | None |
| Q13 | text | ✅ PASS | ✅ | ✅ | 1.00 | 22 items | Table A4, Clause 4, Annex A |
| Q14 | text | ✅ PASS | ✅ | ✅ | 1.00 | 13 items | Figure B25, Clause 4, Annex B |
| Q15 | text | ✅ PASS | ✅ | ✅ | 1.00 | 16 items | Clause 4, Annex D |
| Q16 | text | ✅ PASS | ✅ | ✅ | 1.00 | 6 items | Clause 4 |
| Q17 | nonstandard | ✅ PASS | ✅ | ✅ | 1.00 | 5 items | Figure B32, Clause 4, Annex D |
| Q18 | nonstandard | ✅ PASS | ✅ | ✅ | 1.00 | 5 items | Clause 4 |
| Q19 | nonstandard | ✅ PASS | ✅ | ✅ | 1.00 | 16 items | Clause 4 |
| Q20 | nonstandard | ✅ PASS | ✅ | ✅ | 1.00 | 17 items | Figure A1, Table A5, Clause 4, Annex A, Annex D |
| Q21 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 9 items | Figure A6, Clause 4, Annex A |
| Q22 | figure | ✅ PASS | ✅ | ✅ | 0.50 | 4 items | Figure B19, Clause 4, Annex B |
| Q23 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 8 items | Figure B25, Clause 4, Annex B |
| Q24 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 20 items | Figure B26, Annex B |
| Q25 | table | ✅ PASS | ✅ | ✅ | 1.00 | 26 items | Figure A2, Table A1, Table A4, Annex A |
| Q26 | table | ✅ PASS | ✅ | ✅ | 1.00 | 9 items | Table A1, Table A2, Annex A |
| Q27 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | None |
| Q28 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | None |
| Q29 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | Figure B54, Figure B120, Figure B1, Annex B |
| Q30 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | Table A1, Table A5 |
| Q31 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 9 items | Figure B16, Figure B16A, Annex B |
| Q32 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 9 items | Figure B23, Clause 4, Annex B |
| Q33 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 21 items | Figure A1, Figure B46, Figure A5, Annex A, Annex B |
| Q34 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 10 items | Figure B12, Annex B |
| Q35 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 3 items | Figure B40, Annex B |
| Q36 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 32 items | Figure B39, Clause 4, Annex B |
| Q37 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 14 items | Figure B28, Figure B29, Clause 4, Annex B |
| Q38 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 8 items | Figure B5, Figure B13, Figure B33, Figure B6, Figure B1, Annex B |
| Q39 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 12 items | Figure B35, Annex B |
| Q40 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 12 items | Figure B41, Clause 4, Annex B |
| Q41 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 4 items | Figure B34, Clause 4, Annex B |
| Q42 | figure | ✅ PASS | ✅ | ✅ | 1.00 | 13 items | Figure B51 |
| Q43 | text | ✅ PASS | ❌ | ✅ | 1.00 | 13 items | Annex C |
| Q44 | text | ✅ PASS | ✅ | ✅ | 1.00 | 16 items | Clause 4, Annex B, Annex C, Annex D |
| Q45 | table | ✅ PASS | ✅ | ✅ | 1.00 | 10 items | Table D1, Clause 4, Annex D |
| Q46 | table | ✅ PASS | ✅ | ✅ | 1.00 | 6 items | Table D4, Annex D |
| Q47 | table | ✅ PASS | ✅ | ✅ | 1.00 | 5 items | Table D6, Annex D |
| Q48 | text | ✅ PASS | ✅ | ✅ | 1.00 | 2 items | Annex F |
| Q49 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | Figure B39, Figure B53, Figure B52, Annex B |
| Q50 | abstention | ✅ PASS | ❌ | ✅ | 1.00 | 0 items | Figure B75 |