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
