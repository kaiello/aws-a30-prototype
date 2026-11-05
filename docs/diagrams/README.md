# Recommended AWS A3.0 future architecture

This is an explanatory recommendation dated November 5, 2026, based on the review of `9475df7bc75ada23e8ddb8d401bd578bfb25eebb`. It is not a diagram of a completed integration. Gate 6.7's reader remains unqualified; Ken's independent review remains pending.

- [PNG](aws-a30-future-architecture.png): directly viewable image.
- [PDF](aws-a30-future-architecture.pdf): one vector landscape page, suitable for zoom/print.
- [SVG](aws-a30-future-architecture.svg): scalable and editable vector image.
- [DOT](aws-a30-future-architecture.dot): editable layout and connection source.

Blue marks existing reusable components, amber proposed integration/repairs, gray immutable source evidence, and purple unreviewed candidate authority. Green outlines denote reviewed authority; not all existing records qualify. Dashed connections are proposed. The existing routes are disconnected today. Source identity is not semantic validation, and candidate interpretations require separate review/admission.

The flow covers question subparts, deterministic lookup, evidence sufficiency for each part, missing-page discovery, source-only page-plus-region packets, conditional local VLM reading, source-linked claim checks, partial answers/abstention, and the candidate/reviewed boundary. Page-image retrieval remains a deferred separate experiment.

All diagram text and shapes are self-authored architecture documentation. No licensed source pages, excerpts, model responses, private review judgments or credentials are embedded.

See [the current architecture assessment](../AWS_A30_ARCHITECTURE_RECOMMENDATIONS.md#current-assessment-november-5-2026) for findings, evidence limits and the bounded comparison plan. Rendering and QA notes follow below.

## Render and verify

Rendered with Graphviz 12.2.0 using the DOT file's fixed positions:

```powershell
neato -n2 -Tsvg aws-a30-future-architecture.dot -o aws-a30-future-architecture.svg
neato -n2 -Tpdf aws-a30-future-architecture.dot -o aws-a30-future-architecture.pdf
```

Render the PDF to PNG with PyMuPDF, preserving aspect ratio:

```python
import fitz
with fitz.open("aws-a30-future-architecture.pdf") as document:
    page = document[0]
    page.get_pixmap(matrix=fitz.Matrix(2200 / page.rect.width, 2200 / page.rect.width), alpha=False).save("aws-a30-future-architecture.png")
```

QA: final PNG visually inspected after layout simplification; labels readable and no major line crossings. PDF has one landscape page and no text blocks outside its bounds. PNG is 2200 x 1630 pixels; SVG parses as XML. Diagram source and all exported formats are committed documentation, not runtime application assets.
