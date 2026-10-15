"""Exact source IDs and explicit ambiguity, independent of answer generation."""
import pytest
from src.citation_checker import extract_citations, extract_grounded_claims, verify_response
from src.standard_manifest import get_manifest, extract_references


@pytest.mark.parametrize("label", ["Figure A7", "Figure A14", "Figure B16", "Figure B55", "Figure B64", "Figure B97", "Figure B120", "Table A10"])
def test_eight_legacy_false_or_ambiguous_citations(label):
    result = extract_citations(label)
    assert result["figures"] == []
    assert result["tables"] == []
    assert not result["has_citation"]
    assert result["unresolved_elements"]


def test_all_verified_element_ids_resolve_without_renaming():
    manifest = get_manifest()
    for kind in ["figures", "tables"]:
        for label in manifest.labels(kind):
            result = extract_citations(label)
            assert result[kind] == [label]
            assert [a["pdf_index"] for a in result["source_anchors"][label]] == [a["pdf_index"] for a in manifest.anchors(label)]


def test_exact_boundaries_plural_lists_and_case():
    result = extract_citations("Figures B.24, B.25, and B.26; fig. b16c; Table D6. Clause 10. Annex F.")
    assert result["figures"] == ["Figure B24", "Figure B25", "Figure B26", "Figure B16C"]
    assert result["tables"] == ["Table D6"]
    assert result["clauses"] == ["Annex F"]
    assert extract_references("Figure B1.5; Figure B1suffix; Table A10")["figures"] == []


def test_unknown_citation_does_not_pass_existing_verifier():
    item = {"expected_answer_keywords": ["weld"], "required_qualifiers": [], "gold_citation": {}}
    result = verify_response(item, "A weld is shown in Figure B120.")
    assert not result["pass"]


def test_conflicting_applicability_is_not_silently_normative():
    anchors = extract_citations("Figure B25")["source_anchors"]["Figure B25"]
    assert all(a["normative_status"] == "conflicting" for a in anchors)


def test_plural_annex_d_tables_preserve_all_identifiers():
    assert extract_citations("Tables D1, D2, and D3")['tables'] == ["Table D1", "Table D2", "Table D3"]
    assert extract_citations("Tables D.1, 2, and 3")['tables'] == ["Table D1", "Table D2", "Table D3"]


def test_unicode_bullet_claims_keep_exact_suffix_and_d_table_anchors():
    claims = extract_grounded_claims("\u2022 Weld geometry is illustrated in Figure B16C.\n- Changes appear in Table D2.")
    assert len(claims) == 2
    assert claims[0]['claim'].startswith("Weld geometry")
    assert claims[0]['anchors'] == ["Figure B16C"]
    assert claims[1]['anchors'] == ["Table D2"]


def test_descriptive_prose_is_not_an_unknown_identifier():
    text = "A weld is shown in Figure B25. The figure shows its geometry; the table below and clause above provide context."
    assert extract_citations(text)['unresolved_elements'] == []
    item = {"expected_answer_keywords": ["weld"], "required_qualifiers": [], "gold_citation": {}}
    assert verify_response(item, text)['pass']


@pytest.mark.parametrize("text, key, expected", [
    ("Figures B1-B3", "figures", ["Figure B1", "Figure B2", "Figure B3"]),
    ("Figures B1–B3", "figures", ["Figure B1", "Figure B2", "Figure B3"]),
    ("Figure B1 — B3", "figures", ["Figure B1", "Figure B2", "Figure B3"]),
    ("fig. b.1 - 3", "figures", ["Figure B1", "Figure B2", "Figure B3"]),
    ("Tables D.1–3, and D6", "tables", ["Table D1", "Table D2", "Table D3", "Table D6"]),
    ("Tables D.1, .2, and .3", "tables", ["Table D1", "Table D2", "Table D3"]),
    ("Figures B1–B3, B2 and B4", "figures", ["Figure B1", "Figure B2", "Figure B3", "Figure B4"]),
    ("Figures A1, B2, 3", "figures", ["Figure A1", "Figure B2", "Figure B3"]),
    ("Figures B.1; 2; and B3", "figures", ["Figure B1", "Figure B2", "Figure B3"]),
])
def test_element_ranges_and_lists_resolve_ordered_canonical_members(text, key, expected):
    result = extract_citations(text)
    assert result[key] == expected
    assert result["unresolved_elements"] == []
    assert list(result["source_anchors"]) == expected
    for label in expected:
        assert result["source_anchors"][label] == get_manifest().source_anchors(label)


def test_valid_range_is_bounded_by_inventory_not_arbitrary_twenty_member_limit():
    result = extract_citations("Figures B17–B54")
    assert result["figures"] == [f"Figure B{i}" for i in range(17, 55)]
    assert result["unresolved_elements"] == []


@pytest.mark.parametrize("text", [
    "Figures B54–B55", "Tables A1–A10", "Figures B3–B1", "Figures A1-B3",
    "Figures B15–B17", "Figures B16A–B16C", "Figure B1 to B3", "Figure B1 through B3",
    "Figures B1/B3", "Figure B1–", "Figure B1--B3", "Figure B1–B1.5",
    "Figure B16C-extra", "Clause 1–4", "Annex A–F",
    "Figures B1–" + "9" * 5000,
], ids=["unknown-end", "unknown-table", "descending", "mixed-prefix", "group-interior",
        "suffix-range", "to", "through", "slash", "missing-end", "double-dash",
        "decimal-suffix", "trailing-suffix", "clause-range", "annex-range", "huge-end"])
def test_invalid_or_unsupported_expression_never_accepts_partial_exact_citation(text):
    result = extract_citations(text)
    assert result["figures"] == []
    assert result["tables"] == []
    assert result["clauses"] == []
    assert not result["has_citation"]
    assert result["source_anchors"] == {}
    assert result["unresolved_elements"]
    assert all(set(item) == {"text", "status", "candidates"} for item in result["unresolved_elements"])


def test_invalid_range_does_not_hide_independent_valid_reference():
    result = extract_citations("Figures B54–B55; Table D1")
    assert result["figures"] == []
    assert result["tables"] == ["Table D1"]
    assert result["unresolved_elements"]


def test_range_claims_keep_exact_existing_evidence_ids_and_all_continuations():
    result = extract_citations("Figures B6–B7")
    b6 = result["source_anchors"]["Figure B6"]
    assert [a["element_id"] for a in b6] == ["figure:figure_b6"] * 3
    assert [a["pdf_index"] for a in b6] == [99, 100, 101]
    assert all(a["normative_status"] == "conflicting" for a in b6)
    claims = extract_grounded_claims("- Weld geometry appears in Figures B6–B7.")
    assert claims[0]["anchors"] == ["Figure B6", "Figure B7"]


def test_lists_false_does_not_expand_or_partially_accept_a_range():
    result = extract_references("Figure B1–B3; Figure B4", lists=False)
    assert result["figures"] == ["Figure B4"]
    assert result["unresolved_elements"]


def test_reference_lists_stop_at_prose_and_keep_existing_page_contract():
    result = extract_citations("Figures B1, B2 describe 3 welds. Figure B6, pp. 87–89")
    assert result["figures"] == ["Figure B1", "Figure B2", "Figure B6"]
    assert result["pages"] == [87]  # Page-range expansion is explicitly deferred.
    assert all(type(page) is int for page in result["pages"])
    assert result["unresolved_elements"] == []


@pytest.mark.parametrize("text", [
    "Use Figure B1 to explain the weld.",
    "Follow Figure B1 through the diagram notes.",
])
def test_prose_after_reference_is_not_an_unsupported_range(text):
    result = extract_citations(text)
    assert result["figures"] == ["Figure B1"]
    assert result["unresolved_elements"] == []
    assert result["source_anchors"]["Figure B1"] == get_manifest().source_anchors("Figure B1")


@pytest.mark.parametrize("text", [
    "Figure B1 to FigureB3", "Figure B1 to Fig.B3",
    "Figure B1 through FigureB3", "Figure B1 through Fig.B3",
])
def test_repeated_shorthand_range_is_not_a_partial_exact_citation(text):
    result = extract_citations(text + "; Figure B4")
    assert result["figures"] == ["Figure B4"]
    assert result["unresolved_elements"]
    assert list(result["source_anchors"]) == ["Figure B4"]
