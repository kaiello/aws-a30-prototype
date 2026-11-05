"""Fail-closed Gate 6.7 scoring: structure is automated; meaning needs human review.

Review records are auditable assertions, not authentication of the reviewer. Callers
must obtain them from an independent human; a model must never fill its own form.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

DIMENSIONS = ("correctness", "completeness", "citation_support", "qualifiers", "abstention")
BINDING_FIELDS = ("pdf_index", "viewer_page", "printed_page", "crop",
                  "source_sha256", "text_sha256", "image_sha256")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bindings(case: dict, packet: dict, response: dict) -> dict:
    return {"case_sha256": canonical_digest(case), "packet_sha256": canonical_digest(packet),
            "response_sha256": canonical_digest(response)}


def create_review_template(case: dict, packet: dict, response: dict) -> dict:
    """Return an unapproved form bound to the complete case/rubric and run inputs."""
    return {
        "schema_version": "gate67-human-review-1", "case_id": case["id"],
        "bindings": _bindings(case, packet, response),
        "reviewer": {"role": "human", "name": ""},
        "source_review": {"checked": False, "notes": ""},
        "dimensions": dict.fromkeys(DIMENSIONS),
        "claims": [{"claim_id": claim["claim_id"], "disposition": "pending",
                    "answer_span": "", "evidence_ids": []} for claim in case["claims"]],
        "notes": "",
    }


def _record_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _ids(value: Any) -> bool:
    return (isinstance(value, list) and all(isinstance(item, str) and item for item in value)
            and len(value) == len(set(value)))


def score_response(case: dict, packet: dict, response: dict, review: dict | None = None) -> dict:
    """Check citation identity first, then accept only complete, bound human judgments.

    PENDING_REVIEW is deliberately excluded from passes and from reader accuracy.
    A supported negative sentence is valid; substring tests never adjudicate truth.
    """
    if not all(isinstance(value, dict) for value in (case, packet, response)):
        return {"outcome": "FAIL_STRUCTURAL", "structural_ok": False,
                "semantic_reviewed": False, "source_human_checked": False,
                "issues": ["invalid_top_level_schema"], "review_issues": [],
                "pending": [], "dimensions": {}}
    issues: list[str] = []
    review_issues: list[str] = []
    pending: list[str] = []
    offered = packet.get("evidence")
    required = case.get("evidence")
    expected_claims = case.get("claims")
    actual_claims = response.get("claims")
    if not all(_record_list(items) for items in (offered, required, expected_claims, actual_claims)):
        issues.append("invalid_evidence_or_claim_schema")
        offered, required, expected_claims, actual_claims = [], [], [], []
    offered_ids = [item.get("evidence_id") for item in offered]
    required_ids = [item.get("evidence_id") for item in required]
    if not _ids(offered_ids) or not _ids(required_ids):
        issues.append("invalid_or_duplicate_evidence_ids")
    if not _ids([claim.get("claim_id") for claim in expected_claims]):
        issues.append("invalid_or_duplicate_expected_claim_ids")
    by_id = {item.get("evidence_id"): item for item in offered if isinstance(item.get("evidence_id"), str)}
    for expected in required:
        evidence_id = expected.get("evidence_id")
        if not isinstance(evidence_id, str):
            continue
        actual = by_id.get(evidence_id)
        if actual is None:
            issues.append(f"required_evidence_missing:{evidence_id}")
        elif any(actual.get(field) != expected[field] for field in BINDING_FIELDS if field in expected):
            issues.append(f"evidence_binding_mismatch:{evidence_id}")
        elif ("page_text_sha256" in expected
              and actual.get("text_sha256") != expected["page_text_sha256"]):
            issues.append(f"page_text_digest_mismatch:{evidence_id}")
    for item in offered:
        index, viewer = item.get("pdf_index"), item.get("viewer_page")
        if type(index) is not int or type(viewer) is not int or index < 0 or viewer != index + 1:
            issues.append(f"invalid_page_coordinates:{item.get('evidence_id')}")
    answer = response.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        issues.append("missing_answer")
        answer = ""
    if packet.get("question") != case.get("question"):
        issues.append("question_mismatch")
    status = response.get("status")
    if status not in {"ANSWERED", "ABSTAIN"} or status != case.get("expected_status"):
        issues.append("status_mismatch")
    if status == "ANSWERED" and not actual_claims:
        issues.append("missing_answer_claims")
    if status == "ABSTAIN" and not (isinstance(response.get("abstention_reason"), str)
                                    and response["abstention_reason"].strip()):
        issues.append("missing_abstention_reason")
    for claim in actual_claims:
        text, citations = claim.get("text"), claim.get("evidence_ids")
        if not isinstance(text, str) or not text.strip() or text not in answer:
            issues.append("claim_not_in_answer")
        if not _ids(citations) or not citations:
            issues.append("missing_or_invalid_claim_citations")
        elif any(evidence_id not in by_id for evidence_id in citations):
            issues.append("unknown_claim_citation")

    human_source_checked = False
    semantic_reviewed = False
    dimensions: dict = {}
    if review is None:
        pending.append("independent_human_review_required")
    elif not isinstance(review, dict):
        review_issues.append("invalid_review_schema")
    else:
        if review.get("schema_version") != "gate67-human-review-1":
            review_issues.append("unsupported_review_schema")
        if review.get("case_id") != case.get("id") or review.get("bindings") != _bindings(case, packet, response):
            review_issues.append("stale_or_mismatched_review")
        reviewer = review.get("reviewer") or {}
        is_human = (isinstance(reviewer, dict) and reviewer.get("role") == "human"
                    and isinstance(reviewer.get("name"), str) and bool(reviewer["name"].strip()))
        if not is_human:
            pending.append("named_independent_human_reviewer_required")
        source_review = review.get("source_review") or {}
        human_source_checked = (is_human and isinstance(source_review, dict)
                                and source_review.get("checked") is True
                                and isinstance(source_review.get("notes"), str)
                                and bool(source_review["notes"].strip()))
        if not human_source_checked:
            pending.append("human_source_adjudication_required")
        dimensions = review.get("dimensions") or {}
        if not isinstance(dimensions, dict):
            dimensions = {}
            review_issues.append("invalid_review_dimensions")
        for dimension in DIMENSIONS:
            value = dimensions.get(dimension)
            if value is None:
                pending.append(f"dimension_pending:{dimension}")
            elif value is not True:
                review_issues.append(f"dimension_failed:{dimension}")
        judgments = review.get("claims")
        if not _record_list(judgments):
            judgments = []
            review_issues.append("invalid_review_claims")
        expected_by_id = {claim.get("claim_id"): claim for claim in expected_claims
                          if isinstance(claim.get("claim_id"), str)}
        judgment_ids = [claim.get("claim_id") for claim in judgments]
        if not _ids(judgment_ids) or set(judgment_ids) != set(expected_by_id):
            review_issues.append("missing_duplicate_or_unexpected_review_claims")
        for judgment in judgments:
            judgment_id = judgment.get("claim_id")
            expected = expected_by_id.get(judgment_id) if isinstance(judgment_id, str) else None
            if expected is None:
                continue
            disposition = judgment.get("disposition")
            if disposition == "pending":
                pending.append(f"claim_pending:{judgment.get('claim_id')}")
                continue
            if disposition != "supported":
                review_issues.append(f"claim_not_supported:{judgment.get('claim_id')}:{disposition}")
                continue
            span, citations = judgment.get("answer_span"), judgment.get("evidence_ids")
            if (not isinstance(span, str) or not span.strip() or span not in answer
                    or not _ids(citations) or not citations
                    or set(citations) != set(expected.get("evidence_ids") or [])
                    or any(evidence_id not in by_id for evidence_id in citations)
                    or not any(isinstance(claim.get("text"), str) and span in claim["text"]
                               and set(citations).issubset(claim.get("evidence_ids") or [])
                               for claim in actual_claims)):
                review_issues.append(f"claim_span_or_citation_mismatch:{judgment.get('claim_id')}")
        # Completed negative judgments count as reviewed failures, not unreviewed cases.
        semantic_reviewed = is_human and not pending and all(
            issue.startswith(("dimension_failed:", "claim_not_supported:"))
            for issue in review_issues
        )
    outcome = ("FAIL_STRUCTURAL" if issues else "FAIL_REVIEW" if review_issues else
               "PENDING_REVIEW" if pending else "PASS_SUPPORTED")
    return {"outcome": outcome, "structural_ok": not issues,
            "semantic_reviewed": semantic_reviewed, "source_human_checked": human_source_checked,
            "issues": issues, "review_issues": review_issues, "pending": pending,
            "dimensions": dimensions}
