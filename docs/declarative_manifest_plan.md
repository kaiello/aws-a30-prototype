# Declarative source manifest: bounded implementation plan

Planning/implementation branch: `plan/declarative-manifest-20261015`, based on `89f4a529b05509d8dc45e439c858347abb2cf469`. Source review: 2026-10-15. The owner subsequently authorized implementation of tasks 1-4. They are implemented and ready for review; see the [implementation receipt](declarative_manifest_implementation.md) for exact files, bounded test evidence and remaining gaps. No ingestion, graph rebuild, store migration, paid inference or framework integration ran. This plan retains the original review baseline below; runtime adoption is qualified by the receipt.

## Goal alignment and limits

Use one authoritative manifest to reduce confirmed citation and asset-resolution errors: incorrect page bases, invalid element IDs, dropped continuation pages, and ambiguous filename selection. Feed existing functions gradually. Preserve existing document/element/chunk IDs, API fields, figure chips, spatial manifest, BGE-large/1024 configuration, and retrieval algorithms. A schema or completed plan is not evidence of improved NLQ accuracy.

The work follows [project goals](goal.md) and the evidence-identity, independent retrieval/reading, and retire-after-replacement guidance in [lessons learned](navy_weld_multimodal_lessons_learned.md), [value assessment](navy_weld_value_and_outcomes_assessment.md), and [roadmap](navy_weld_framework_roadmap.md). The roadmap is advisory context, not implementation authority. Scope excludes a framework swap, new registry service, new UI, graph rebuild, store migration, re-embedding, ingestion, provider calls, and changes to frozen gold questions or scorer thresholds.

## Source validation receipt

This section preserves the planning-phase baseline. The implementation receipt adds subsequent verification of all 94 PNG bindings against the exact source.

Only `data/AWS_A3.0_2020.pdf` in this repository was examined. It has **190 PDF pages**, **3,377,668 bytes**, SHA-256 **`205fa58eefe084c64b7c7e4520fcb50e067116d6d71a6becf4671fb541858e2d`**. Its title page at PDF index 1 declares AWS A3.0M/A3.0:2020, *Standard Welding Terms and Definitions*, 13th Edition, superseding 2010; ANSI approval is dated 2019-10-22. PDF creation metadata is not the edition identifier. The existing graph document ID remains `doc:aws_a30_2020`; `AWS_A3.0_2020` is a standard alias, not another document.

Read-only PyMuPDF 1.26.5 checks examined the contents/lists and actual section/table/figure captions, including continuations. All 176 Arabic page labels at indices 13-188 matched the page text at header/footer geometry. All 62 figure IDs and printed-page ranges in `src/figure_inspectors.py:27` matched the actual captions; first pages also matched the source list of figures. All 11 table starts matched the list of tables; actual continued captions established their full spans. Local visual checks covered indices **1, 9, 10, 11, 17, 81, 84, 86, 93, 160, 177, 182**. Other inventory entries below are caption-text verified, not individually visually adjudicated. No table-cell, footnote, panel geometry, bitmap fidelity, answer support, or retrieval quality certification is implied. No source bytes were uploaded or added to this plan.

Page conventions must be explicit:

- `pdf_index` is zero based; `pdf_page_ordinal = pdf_index + 1` is a derived viewer page number, not a physical paper-sheet count.
- For this exact file, printed Arabic pages 1-176 correspond to indices 13-188 (`printed = index - 12`). This is an observed mapping, not a universal offset.
- Indices 2-12 visibly carry Roman labels ii-xii. Cover/index 0, title/index 1, and back/index 189 have no visible printed page label. The PDF has no embedded page-label dictionary or outline. Keep labels as strings or null; do not invent a printed `i` for index 1.
- Blank pages remain real source pages. Do not stretch an element span across a blank page merely to reach the next section.

### Candidate ZIP disposition

The ZIP's manifest fields were relayed by the parent task after Windows materialization failed; its original bytes/path/hash were not independently recovered. Validate the relayed fields rather than invent a bundle digest. Do not adopt its lists wholesale.

| Candidate field | Source result / required disposition |
|---|---|
| `standard_id`, title, `pdf_filename` | Compatible identity alias/title/basename; bind to the verified local document ID and SHA above. |
| `glossary_start_page: 18` | Wrong if zero based: Glossary starts at **index 17**, viewer page 18, printed p. 5. |
| `annex_a_start_page: 81` | Correct as a zero-based section start; viewer page 82, printed p. 69. |
| `annex_b_start_page: 93` | Correct as a zero-based section introduction; first figure starts at **94**, not 93. |
| Clauses 1-4 and Annexes A-E | Present, but incomplete: include **Annex F**. Clause 1 is General Requirements; Scope is 1.1. |
| Tables A1-A9 and B1-B4 | Retain A1-A5 only; reject A6-A9 and B1-B4 as exact table IDs in this edition. Add **D1-D6**. |
| Figures A1-A14 and B1-B64 | Retain A1-A6 and B1-B54 **except standalone B16**. Add B16A/B16B/B16C. Reject A7-A14 and B55-B64 as exact caption IDs. `Figure B16` may be an explicit legacy group alias, never a guessed single-page citation. |
| A1 companions A1/A4; A2 companions A2/A3; A3 companion A6 | All targets exist, but these are not source-proven citation relationships. A2/A3 titles explicitly cross-reference **Table A1**, not the proposed exclusive figure mappings. Keep existing UI companions separately typed and provisional; do not substitute the changed ZIP links. |

**Source conflict requiring an explicit qualifier:** contents/index 9 calls Annex B informative; its own opening/index 93 calls it normative and describes mandatory elements. Record `normative_status: conflicting` with both anchors. Do not silently promote either label to authoritative applicability. Annex A is normative; C-F are informative in their opening headings. This conflict does not prevent verifying where a figure occurs.

## Validated mapping inventory

The following are source-location facts for the fingerprint above. Ranges are inclusive. Viewer ordinals are always the listed indices plus one; printed labels are stated separately. Section content spans omit following blank pages.

| Existing section ID suffix (`clause:`) | PDF indices | Printed pages | Heading / qualification |
|---|---:|---:|---|
| `clause_1` | 13-14 | 1-2 | General Requirements; includes Scope 1.1 |
| `clause_2` | 15 | 3 | Normative References |
| `clause_3` | 16 | 4 | Terms and Definitions |
| `clause_4` | 17-80 | 5-68 | Glossary |
| `annex_a` | 81-91 | 69-79 | Process, Classifications, and Designations; normative; index 92/p. 80 blank |
| `annex_b` | 93-169 | 81-157 | Figures; status conflict above; index 170/p. 158 blank |
| `annex_c` | 171-176 | 159-164 | Principles of A3.0M/A3.0 Style; informative |
| `annex_d` | 177-182 | 165-170 | Modifications from 2010; informative |
| `annex_e` | 183 | 171 | Terminology from Other Sources; informative; index 184/p. 172 blank |
| `annex_f` | 185-186 | 173-174 | Requesting an Official Interpretation; informative |

Index 187/p. 175 is the list of AWS documents; index 188/p. 176 is blank; index 189 is the unnumbered back page. Preserve these in document/page inventory without labeling them Annex B evidence.

| Table ID | PDF indices, in order | Printed labels | Continuation / shared-page detail |
|---|---|---|---|
| A1 | 81, 82 | 69, 70 | Second page continued |
| A2 | 83, 84 | 71, 72 | Second page continued; shares 84 with A3 |
| A3 | 84, 85 | 72, 73 | Second page continued |
| A4 | 86 | 74 | Shares page with A5 |
| A5 | 86 | 74 | Separate table on same page |
| D1 | 177, 178 | 165, 166 | Second page continued |
| D2 | 179, 180 | 167, 168 | Second page continued |
| D3 | 181 | 169 | Single page |
| D4 | 182 | 170 | Shares page with D5/D6 |
| D5 | 182 | 170 | Separate table on same page |
| D6 | 182 | 170 | Separate table on same page |

Use existing labels `Table A1` etc. and graph IDs `table:table_a1` etc. A4/A5 already exist as parsed/query assets, although `STANDARD_TABLES` currently omits them; do not create a competing table namespace.

All **62 figure labels** below reuse `FIGURE_INSPECTORS` keys and existing `figure:figure_*` graph IDs. B16A/B/C are distinct captions; continued pages stay under one figure ID.

| Figure ID(s) | PDF index / ordered indices | Printed label(s) |
|---|---|---|
| A1 | 87 | 75 |
| A2; A3 | 88 (each) | 76 (each) |
| A4 | 89 | 77 |
| A5 | 90 | 78 |
| A6 | 91 | 79 |
| B1; B2; B3; B4; B5 | 94; 95; 96; 97; 98 | 82; 83; 84; 85; 86 |
| B6 | 99, 100, 101 | 87, 88, 89 |
| B7 | 102 | 90 |
| B8 | 103, 104, 105 | 91, 92, 93 |
| B9 | 106, 107 | 94, 95 |
| B10; B11; B12; B13; B14; B15 | 108; 109; 110; 111; 112; 113 | 96; 97; 98; 99; 100; 101 |
| B16A; B16B; B16C | 114; 115; 116 | 102; 103; 104 |
| B17 | 117 | 105 |
| B18 | 118, 119 | 106, 107 |
| B19 | 120, 121 | 108, 109 |
| B20 | 122, 123 | 110, 111 |
| B21; B22 | 124; 125 | 112; 113 |
| B23 | 126, 127, 128 | 114, 115, 116 |
| B24 | 129, 130, 131, 132, 133, 134 | 117, 118, 119, 120, 121, 122 |
| B25 | 135, 136, 137, 138 | 123, 124, 125, 126 |
| B26 | 139, 140, 141 | 127, 128, 129 |
| B27; B28; B29 | 142; 143; 144 | 130; 131; 132 |
| B30 | 145, 146 | 133, 134 |
| B31 | 147 | 135 |
| B32 | 148, 149, 150 | 136, 137, 138 |
| B33; B34 | 151; 152 | 139; 140 |
| B35; B36 | 153 (each) | 141 (each) |
| B37; B38; B39; B40 | 154; 155; 156; 157 | 142; 143; 144; 145 |
| B41; B42 | 158 (each) | 146 (each) |
| B43; B44; B45; B46; B47; B48 | 159; 160; 161; 162; 163; 164 | 147; 148; 149; 150; 151; 152 |
| B49; B50 | 165 (each) | 153 (each) |
| B51 | 166 | 154 |
| B52 | 167, 168 | 155, 156 |
| B53; B54 | 169 (each) | 157 (each) |

B44's body caption omits the word `Figure`; its identifier/location are confirmed by the source list and visual page inspection. Do not lose it through a `Figure B...` regex requirement. Same-page figures/tables require separate anchors; a shared page is not proof of identical regions.

### Existing drift, legacy exceptions and unverified data

- `src/config.py:31` uses glossary start 18. `parsed/text_chunks.jsonl` puts index 17 inside `clauses_1_to_3_scope` (indices 0-17); there is no dedicated `clause_4_p5` row. The first glossary page is misclassified, not proven lost. Preserve chunk IDs and disclose this exception; do not rewrite chunks or trigger ingestion during manifest adoption.
- `src/build_dual_graph.py:37` declares 180 total pages, and its section/table page constants at lines 46/59 disagree with the source. A4/A5 are missing from that table constant. Existing persisted graphs have not been opened or repaired here. Deriving future metadata reads does not repair cached graph data.
- `src/citation_checker.py:12` enumerates B1-B97, whereas extraction accepts syntactic figure labels without checking that list. A read-only call to the actual parser returned figure citations for **A7, A14, B16, B55, B64, B97, B120** and interpreted **Table A10 as Table A1**. These eight named cases form a bounded baseline: seven unknown exact IDs plus one ambiguous B16 group, all needing explicit resolution rather than acceptance as exact source captions.
- `resolve_figure_image_filename()` at `src/figure_inspectors.py:1207` currently picks `Figure_B6_p100.png`, a continued page (index 100), before primary index 99. The resolver exposes one image per figure and cannot enumerate all 13 multi-page figure spans. Do not infer correctness from glob order.
- Existing A-figure filenames use one-based viewer ordinals (`Figure_A1_p88.png` is intended for index 87); B filenames generally use zero-based indices (`Figure_B1_p94.png` corresponds to index 94). Never infer source coordinates from a filename suffix. PNGs exist for all 62 current figure keys, including B16A/B/C, B36, B42, B44, B50 and B54. Their complete pixel/region fidelity is **not yet verified**.
- The 97 Annex-B JSONL rows are per-page artifacts, not 97 distinct figures. Nineteen rows at indices 171-189 are mislabeled as Annex B despite falling after it. Intro/blank pages and shared-page records also need classification. Retain their original artifact/chunk IDs as legacy references; exclude invalid element aliases from canonical lookup rather than deleting source assets.
- `parsed/figures/figure_bboxes.json` remains the spatial registry. Its chip coordinates are not certified PDF-page anchors by this review; image-space versus page-space transforms must be verified before reuse. Table-cell spans, footnotes and conceptual companions also remain provisional.
- Preserve existing UI-only companions in `src/query.py:38`: A1 -> A1/A4; A2 -> A1/A2; A3 -> A1; A4 -> A1; A5 -> A2/A5/A6 (targets are figures). All nine edges remain `ui_companion`, project-curated, not source citation or entailment evidence. Do not adopt the ZIP's changed A2/A3 edges without separate evidence.

## Exact schema proposal and ownership

Adopt one UTF-8 JSON file, **`config/aws_a30_2020_manifest.json`**, plus a small standard-library reader in `src/standard_manifest.py`. Both were created under the owner's subsequent implementation authorization. This is a metadata lookup, not a registry framework. JSON avoids adding a parser dependency. The following closed-record contract defines version 1.0.0; lists are ordered, required unless marked `?`, and unknown fields are errors.

```text
Manifest {
  schema_version: "1.0.0", manifest_revision: integer >= 1,
  document: Document, sections: Section[], figures: Element[], tables: Element[],
  links: Link[], legacy_aliases: Alias[]
}
Document {
  id: "doc:aws_a30_2020", standard_id: "AWS_A3.0_2020",
  title: string, publisher: string, edition: "2020", edition_number: 13,
  pdf_relpath: "data/AWS_A3.0_2020.pdf", sha256: lowercase_hex64,
  byte_length: 3377668, page_count: 190, identity_pdf_indices: [1],
  verification: Verification, pages: Page[]
}
Page { pdf_index: integer, printed_label: string | null,
       role: "front_matter" | "body" | "blank" | "back" }
Section { id: existing_clause_id, label: string, title: string,
          spans: Span[], normative_status: Applicability,
          qualification_pdf_indices: integer[], verification: Verification }
Span { start_pdf_index: integer, end_pdf_index: integer }  # inclusive
Element { id: existing_figure_or_table_id, label: existing_display_key, title: string,
          parent_id: existing_clause_id, anchors: Anchor[], assets: AssetRef[] }
Anchor { pdf_index: integer, printed_label: string, order: integer >= 0,
         role: "start" | "continuation", region: Region | null,
         verification: Verification }
Region { space: "pdf_page_unrotated" | "asset_image", origin: "top_left",
         coordinate_order: "ymin_xmin_ymax_xmax", normalized: true,
         bbox: [number, number, number, number], rotation_degrees: integer,
         reference_width: number > 0, reference_height: number > 0 }
AssetRef { relpath: string, source_anchor_orders: integer[],
           sha256: lowercase_hex64 | null, verification: Verification }
Link { from_id: existing_id, to_id: existing_id,
       kind: "ui_companion" | "explicit_reference", verification: Verification }
Alias { legacy_value: string, namespace: "display" | "chunk_id" | "asset_name",
        target_ids: existing_id[], resolution: "exact" | "group" | "unresolved" }
Verification { state: "candidate" | "verified" | "rejected" | "stale",
               source_sha256: lowercase_hex64,
               method: "caption_text" | "manual_visual" | "legacy_unverified" | "render_match",
               verifier: string | null, verified_at_utc: string | null,
               evidence_pdf_indices: integer[], note: string }
Applicability = "normative" | "informative" | "conflicting" | "unknown"
```

Validation rules: exactly one `Page` per index 0-189; no bools accepted as integer indices; all IDs unique and every reference resolvable; ordered anchors without duplicates; exactly one start followed by explicit continuations; labels agree with document page map; section bounds contain their elements; exact aliases have one target, group aliases have at least two, unresolved aliases have none; normalized regions satisfy `0 <= ymin < ymax <= 1` and `0 <= xmin < xmax <= 1`. Same-page elements remain distinct. Null regions mean unverified geometry, not whole-page semantic support. A verified record requires the matching document digest, method, named verifier, timestamp and evidence indices. Unknown/candidate/stale/conflicting metadata must not silently become trusted source or applicability evidence.

Ownership by field: the manifest becomes the sole editable authority for document identity, section/element inventory, source locations and typed links. Seed its figure labels and IDs from the **existing** registry, whose page mappings are already correct. `FIGURE_INSPECTORS` continues to own UI categories, groups, chips and queries; `figure_bboxes.json` owns image-space geometry. Each metadata field moves once: the corresponding old constant becomes a read-only projection through the adapter, with no independently editable duplicate. Keep the same public constant/function names where practical. For migrated source-location/citation decisions, persisted GraphML/SQLite labels or pages cannot override the manifest; those unchanged caches remain retrieval inputs, not competing source authority. Do not copy chip payloads or invent new graph IDs. The B16 group alias targets the three existing B16A/B/C IDs, not a new source element.

For source and asset paths, allow only repository-relative paths under the existing approved data/asset roots. No URLs, credentials, external absolute paths, symlinks or traversal overrides. Preserve the server's existing `AssetStore` containment and startup allowlist; the manifest does not grant file-read permission.

Version/provenance: schema version changes for incompatible structure; `manifest_revision` increments for mapping/qualification changes. Record the exact source digest and source-review base commit. Store a receipt with canonical JSON SHA-256 (sorted keys, UTF-8, compact separators; no self-hash field), verifier/date and tool version. The receipt holds metadata, not source paragraphs, watermarks, page renders or base64 images. A changed PDF hash invalidates verification until rechecked; matching edition text alone cannot retain old anchors. Verified asset bindings require a non-null asset digest and a checked source-page binding; a digest alone does not verify pixels or regions. A hash proves byte identity, not reading quality or standard applicability.

## Small implementation sequence

Each task ends with focused offline fixtures. The owner has now authorized and completed implementation of this sequence; the table records its acceptance design. Only confirmed source/citation/asset differences are intended behavior changes; retrieval algorithms and stores stay frozen.

| Task / dependency | Files likely touched (small slices) | Verification and exit condition |
|---|---|---|
| **1. Seed metadata and validate**, no dependency | New JSON, thin reader, `tests/test_standard_manifest.py` | Seed the 10 sections, 62 figures and 11 tables above from current IDs. Verify SHA/page bounds/continuations; retain Annex B conflict and all provisional fields. Pure loader has no config dotenv, model, database or file-write side effects. Reader remains unused by runtime initially; no accuracy claim. |
| **2. Canonical citation lookup**, after 1 | `src/citation_checker.py`, `src/pre_retrieval.py`, `tests/test_manifest_citations.py` | Existing citation parsing delegates exact token resolution to the manifest, including D tables and B16A/B/C. Keep existing output keys/valid canonical labels. Unknowns remain explicit diagnostics; B16 resolves as a group requiring selection, not a fabricated exact citation. All 73 valid figure/table labels resolve, with the eight negative/ambiguous cases handled correctly and Table A10 never matching A1. |
| **3a. Explicit asset binding**, after 1 | Manifest asset entries, `src/figure_inspectors.py`, `tests/test_manifest_assets.py` | Audit existing PNG-to-source bindings locally; preserve filenames/chips/bboxes. Resolve B6 primary to index 99 deterministically; verify all 62 primary bindings against their actual source pages. Do not mark pixels/regions verified based on names alone. No image regeneration. |
| **3b. Continuation-aware resolution**, after 2 and 3a | `src/query.py`, reader, focused asset tests | Return ordered internal anchors/assets for all 13 multi-page figures and five multi-page tables. Keep existing API primary `image_path`/table fields and ID strings; no UI work. Additional internal evidence must refer to its actual page, not the first page's citation. B16A/B/C and same-page pairs resolve without conflation. |
| **4. Remove duplicated metadata reads**, after 2/3 | First `src/config.py`/`src/extract.py`; separately `src/build_dual_graph.py`; metadata parity tests | Derive start indices and document/section/table constants from the same reader while preserving imports and function signatures. Report discrepancies before switching each consumer. Do not run extraction, graph projection, database updates, reindexing or migration. Cached graph/legacy chunk anomalies stay explicitly unresolved until separately authorized. |

Additional existing readers to inspect during those slices: `src/answer_routes.py` consumes `FIGURE_INSPECTORS`; `src/web.py` serves its catalog; `src/indexer.py:135` and `src/contextual_indexer.py:115` load existing chunk IDs. They should inherit canonical metadata through existing entry points, without separate inventories. No retrieval/reranking code change is necessary for this plan.

## Focused acceptance, compatibility and rollback

Add the proposed tests above using tiny synthetic pages/records and the validated metadata inventory. The local licensed PDF is an optional fingerprint-bound validation input, never copied into new fixtures. Stub model constructors, retrieval calls and SQLite connections to fail if invoked. Run with plugin autoload disabled, no cache, `python -B`, and a fresh authorized scratch directory. Preserve and rerun existing isolated security/credential tests; do not run live model benchmarks under the current authorization.

Before switching adapters, freeze a deterministic report of the current parser and resolver outputs. Required measurable changes are: the eight named invalid/ambiguous citation cases no longer accepted as exact source IDs; **73/73** valid figure/table labels resolve without dropping qualifiers; **13/13** multi-page figure and **5/5** multi-page table spans retain all verified page anchors in order; B6 no longer starts at continuation index 100. Record errors before/after, not just test pass counts.

For no retrieval regression, compare a fixed set of injected sparse/dense candidates and query fixtures before/after: valid chunk IDs, candidate order, scores and selected retrieval mode remain identical; only explicit source/citation corrections change. Assert BGE model configuration and 1024 dimensions unchanged, and existing success/error API shapes, missing-index HTTP 503/CLI exit 1, credential/origin/path boundaries still hold. Retain the historical retrieval receipt unchanged. This establishes bounded deterministic compatibility, **not** live semantic recall or answer accuracy; live retrieval/reading evaluation remains unrun and needs separate authorization.

**Adoption decision:** adapters were switched after their focused fixtures passed; no permanent legacy-selection flag or second editable inventory was retained. This refines the originally proposed temporary selection setting. Missing/invalid metadata, source/receipt mismatch and changed verified asset bytes fail explicitly. Rollback requires reverting the complete adapter change set, including config/graph projections and reader imports, together; keep IDs/assets/stores intact. Removing only the JSON is not rollback. No rebuild or data deletion is needed.

Stop a consumer switch on fingerprint mismatch, unresolved applicability/anchor ambiguity, changed valid IDs, API/security regression or changed retrieval candidate order. The completed plan and schema are preparatory work; goal gain is demonstrated only by the bounded citation/asset error reductions and preserved retrieval behavior above.
