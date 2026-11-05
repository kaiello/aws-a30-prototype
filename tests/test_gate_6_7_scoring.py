"""Independent semantic judgments must never be inferred from keyword presence."""
from copy import deepcopy

import pytest

from src.independent_reader_scoring import (
    canonical_digest, create_review_template, score_response,
)


@pytest.fixture
def inputs():
    evidence = {
        "evidence_id": "source:p10:term", "pdf_index": 10,
        "viewer_page": 11, "printed_page": 1, "crop": None,
        "locator": "Glossary: example",
    }
    case = {
        "id": "development-example", "question": "Is this obligatory?",
        "expected_status": "ANSWERED", "evidence": [deepcopy(evidence)],
        "claims": [{"claim_id": "obligation", "description": "It is obligatory",
                    "evidence_ids": [evidence["evidence_id"]], "qualifiers": []}],
    }
    packet = {"question": case["question"], "evidence": [evidence]}
    response = {"status": "ANSWERED", "answer": "It is obligatory.",
                "claims": [{"text": "It is obligatory.",
                            "evidence_ids": [evidence["evidence_id"]]}],
                "abstention_reason": None}
    return case, packet, response


def approved(case, packet, response):
    review = create_review_template(case, packet, response)
    review["reviewer"] = {"role": "human", "name": "Test reviewer"}
    review["source_review"] = {"checked": True, "notes": "Test source checked"}
    review["dimensions"] = {key: True for key in review["dimensions"]}
    for claim in review["claims"]:
        claim.update(disposition="supported", answer_span=response["claims"][0]["text"],
                     evidence_ids=response["claims"][0]["evidence_ids"])
    return review


def test_no_review_never_qualifies_even_with_expected_keywords(inputs):
    case, packet, response = inputs
    response["answer"] = "It is not obligatory."
    response["claims"][0]["text"] = response["answer"]
    result = score_response(case, packet, response)
    assert result["outcome"] == "PENDING_REVIEW"
    assert result["semantic_reviewed"] is False


def test_negation_fails_independent_contradiction_review(inputs):
    case, packet, response = inputs
    response["answer"] = "It is not obligatory."
    response["claims"][0]["text"] = response["answer"]
    review = approved(case, packet, response)
    review["claims"][0]["disposition"] = "contradicted"
    result = score_response(case, packet, response, review)
    assert result["outcome"] == "FAIL_REVIEW"
    assert result["semantic_reviewed"] is True


def test_unknown_citation_fails_without_waiting_for_semantic_review(inputs):
    case, packet, response = inputs
    response["claims"][0]["evidence_ids"] = ["source:p999:unrelated"]
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_offered_but_irrelevant_citation_cannot_support_required_claim(inputs):
    case, packet, response = inputs
    packet["evidence"].append({**packet["evidence"][0], "evidence_id": "other"})
    response["claims"][0]["evidence_ids"] = ["other"]
    review = approved(case, packet, response)
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


@pytest.mark.parametrize("field,value", [
    ("pdf_index", 11), ("viewer_page", 12), ("printed_page", 2),
    ("crop", [0, 0, 0.1, 0.1]),
])
def test_same_id_with_wrong_binding_fails(inputs, field, value):
    case, packet, response = inputs
    packet["evidence"][0][field] = value
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_prose_locator_does_not_override_source_identity(inputs):
    case, packet, response = inputs
    packet["evidence"][0]["locator"] = "AWS A3.0M/A3.0:2020 source page"
    assert score_response(case, packet, response)["outcome"] == "PENDING_REVIEW"


def test_page_text_digest_is_bound_to_supplied_text_digest(inputs):
    case, packet, response = inputs
    case["evidence"][0]["page_text_sha256"] = "verified-page-digest"
    packet["evidence"][0]["text_sha256"] = "different-page-digest"
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"
    packet["evidence"][0]["text_sha256"] = "verified-page-digest"
    assert score_response(case, packet, response)["outcome"] == "PENDING_REVIEW"


@pytest.mark.parametrize("field", ["source_sha256", "text_sha256", "image_sha256"])
def test_declared_source_digests_cannot_be_swapped(inputs, field):
    case, packet, response = inputs
    case["evidence"][0][field] = "verified-digest"
    packet["evidence"][0][field] = "substituted-digest"
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_omitted_evidence_fails(inputs):
    case, packet, response = inputs
    packet["evidence"] = []
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


@pytest.mark.parametrize("disposition", ["missing", "qualifier_missing", "contradicted"])
def test_missing_or_unqualified_claim_fails(inputs, disposition):
    case, packet, response = inputs
    review = approved(case, packet, response)
    review["claims"][0]["disposition"] = disposition
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


def test_missing_review_claim_fails(inputs):
    case, packet, response = inputs
    review = approved(case, packet, response)
    review["claims"] = []
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


def test_reviewed_legitimate_negative_can_pass(inputs):
    case, packet, response = inputs
    case["claims"][0]["description"] = "It is not obligatory"
    response["answer"] = "It is not obligatory."
    response["claims"][0]["text"] = response["answer"]
    review = approved(case, packet, response)
    assert score_response(case, packet, response, review)["outcome"] == "PASS_SUPPORTED"


def test_stale_review_cannot_pass_changed_answer(inputs):
    case, packet, response = inputs
    review = approved(case, packet, response)
    response["answer"] = "It is not obligatory."
    response["claims"][0]["text"] = response["answer"]
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


@pytest.mark.parametrize("changed", ["case", "packet"])
def test_stale_review_cannot_pass_changed_inputs(inputs, changed):
    case, packet, response = inputs
    review = approved(case, packet, response)
    if changed == "case":
        case["claims"][0]["description"] = "Changed expectation"
    else:
        packet["evidence"][0]["text"] = "Changed source text"
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


def test_source_review_must_be_human_checked(inputs):
    case, packet, response = inputs
    review = approved(case, packet, response)
    review["source_review"]["checked"] = False
    assert score_response(case, packet, response, review)["outcome"] == "PENDING_REVIEW"


def test_agent_review_does_not_qualify_reader(inputs):
    case, packet, response = inputs
    review = approved(case, packet, response)
    review["reviewer"]["role"] = "agent"
    assert score_response(case, packet, response, review)["outcome"] == "PENDING_REVIEW"


def test_false_abstention_fails_status(inputs):
    case, packet, response = inputs
    response.update(status="ABSTAIN", claims=[], abstention_reason="Insufficient evidence")
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_supported_abstention_still_requires_human_dimensions(inputs):
    case, packet, response = inputs
    case.update(expected_status="ABSTAIN", claims=[])
    response.update(status="ABSTAIN", claims=[], abstention_reason="Outside supplied scope")
    review = approved(case, packet, response)
    review["dimensions"]["abstention"] = False
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_REVIEW"


def test_unquoted_claim_and_missing_citations_fail(inputs):
    case, packet, response = inputs
    response["claims"][0].update(text="Another claim", evidence_ids=[])
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_duplicate_evidence_id_fails(inputs):
    case, packet, response = inputs
    packet["evidence"].append(deepcopy(packet["evidence"][0]))
    assert score_response(case, packet, response)["outcome"] == "FAIL_STRUCTURAL"


def test_duplicate_expected_claim_ids_fail(inputs):
    case, packet, response = inputs
    case["claims"].append(deepcopy(case["claims"][0]))
    review = approved(case, packet, response)
    review["claims"] = review["claims"][:1]
    assert score_response(case, packet, response, review)["outcome"] == "FAIL_STRUCTURAL"


def test_malformed_top_level_response_fails(inputs):
    case, packet, _ = inputs
    assert score_response(case, packet, ["invalid"])["outcome"] == "FAIL_STRUCTURAL"


def test_canonical_digest_is_order_independent():
    assert canonical_digest({"a": 1, "b": 2}) == canonical_digest({"b": 2, "a": 1})


def test_review_template_exposes_no_assumed_success(inputs):
    review = create_review_template(*inputs)
    assert all(value is None for value in review["dimensions"].values())
    assert review["source_review"]["checked"] is False
    assert review["claims"][0]["disposition"] == "pending"
