"""Synthetic reviewed facts: no source PDF, private registry, models or services."""
from copy import deepcopy
import hashlib

import pytest

from src.grounded_answer import project_reviewed_facts, compose_grounded_answer
from src.citation_checker import validate_fact_bindings


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def anchor(page):
    return {"document_id": "doc:synthetic", "source_sha256": "a" * 64,
            "section_id": "clause:clause_4", "section_label": "Clause 4", "pdf_index": page + 4,
            "pdf_page_ordinal": page + 5, "printed_label": str(page),
            "verification_state": "verified"}


def proof(term, text, ref, page, member_id):
    return dict(anchor(page), record_id="projection:" + ref, text=text,
                span=[0, len(text)], span_space="local reviewed projection; not raw PDF offsets",
                native_entry_ref=ref, native_text_unchanged=text,
                exact_existing_chunk_id=member_id, exact_existing_full_doc_id="parent:" + member_id,
                chunk_content_sha256_utf8=digest("whole contextual row " + member_id))


def member(member_id, text, refs, supports, page, start=100):
    return {"id": member_id, "full_doc_id": "parent:" + member_id, "content": text,
            "excerpt_sha256": digest(text), "content_sha256": digest("whole contextual row " + member_id),
            "raw_content_span": [start, start + len(text)],
            "span_space": "half-open Unicode character offsets into the exact existing contextual row content",
            "source_entry_refs": refs, "supports": supports,
            "source_anchors": [anchor(page)], "verification_state": "verified"}


def reviewed_bundle(*, conditional=False, headword=None):
    term = headword or ("legacy condition" if conditional else "legacy join")
    qualification = "when used for" if conditional else "for"
    targets = ["target alpha"] if conditional else ["target alpha", "target beta"]
    target_wording = [target + (" (process alpha)" if index == 0 else "") for index, target in enumerate(targets)]
    mapping = term + ". A nonstandard term " + qualification + " " + " or ".join(target_wording) + "."
    standard = term + ". A synthetic bounded condition with a distinct standard meaning. See Figure B1(Z)."
    source_text = standard + "\n" + mapping if conditional else mapping
    source_refs = ["standard:entry", "mapping:entry"] if conditional else ["mapping:entry"]
    members = [member("source:chunk", source_text, source_refs,
                      ["standard_sense", "mapping"] if conditional else ["mapping"], 7)]
    definitions = ["target alpha. A synthetic elongated joint (for process alpha). See Figure B1(Z).",
                   "target beta. A synthetic localized joint. See Figures B2(A) and B2(B)."][:len(targets)]
    # An intervening entry must never become a third target/definition.
    target_text = ("\nincidental term. See another entry.\n").join(definitions)
    members.append(member("target:chunk", target_text,
                          ["definition:" + str(i) for i in range(len(targets))],
                          ["target:" + target for target in targets], 3, 300))
    records = []
    for index, target in enumerate(targets):
        records.append({"mapping_id": "mapping:" + str(index), "nonstandard_term": term,
                        "source_id": "onto:legacy", "source_sense": "conditional" if conditional else "",
                        "source_process_context": "", "preferred_term": target,
                        "target_id": "onto:" + str(index), "target_sense": "",
                        "target_process_context": "process alpha" if index == 0 else "",
                        "relation_type": "NONSTANDARD_FOR", "qualification": qualification,
                        "source": proof(term, mapping, "mapping:entry", 7, "source:chunk"),
                        "target_provenance": [proof(target, definitions[index], "definition:" + str(index), 3, "target:chunk")],
                        "verification_state": "verified", "diagnostics": []})
    provenance = {"entry_id": "entry:legacy", "original_entry": {
                     "text": source_text, "native_entry_refs": source_refs,
                     "verification_state": "verified"},
                  "source_anchor": anchor(7), "projection": {"is_raw_pdf_span": False},
                  "standard_sense": {"text": standard, "evidence_member_ids": ["source:chunk"],
                                     "source_entry_ref": "standard:entry"} if conditional else None}
    return {"id": "terminology:synthetic", "full_doc_id": "terminology:synthetic",
            "evidence_type": "terminology_mapping", "terminology_mappings": records,
            "supporting_evidence": members, "source_anchors": [anchor(7)],
            "terminology_resolution": {"status": "ambiguous_senses" if conditional else "mapped",
                                       "matched_terms": [term], "records": records,
                                       "preferred_terms": targets, "target_ids": [record["target_id"] for record in records],
                                       "source_provenance": [provenance]}}


def test_fact_view_preserves_alternatives_and_exact_native_definition_boundaries():
    bundle = reviewed_bundle()
    original = deepcopy(bundle)
    view = project_reviewed_facts(bundle)
    assert view["status"] == "SUPPORTED_REVIEWED_FACTS"
    mapping = next(fact for fact in view["facts"] if fact["kind"] == "mapping")
    assert mapping["headword"] == "legacy join"
    assert mapping["targets"] == ["target alpha", "target beta"]
    assert [fact["headword"] for fact in view["facts"] if fact["kind"] == "target_definition"] == ["target alpha", "target beta"]
    assert all("incidental term" not in fact["text"] for fact in view["facts"])
    assert all("See Figure" not in fact["text"] for fact in view["facts"])
    assert bundle == original


def test_fact_bindings_preserve_coordinate_spaces_source_refs_and_source_identity():
    bundle = reviewed_bundle()
    view = project_reviewed_facts(bundle)
    for fact in view["facts"]:
        binding = fact["source_bindings"][0]
        source = next(item for item in bundle["supporting_evidence"] if item["id"] == binding["evidence_id"])
        assert binding["raw_content_span"] == source["raw_content_span"]
        assert binding["span_space"] == source["span_space"]
        assert binding["source_entry_ref"] in source["source_entry_refs"]
        assert binding["source_entry_refs"] == source["source_entry_refs"]
        start, end = binding["excerpt_span"]
        assert source["content"][start:end] == binding["source_text"]
        assert binding["fact_raw_content_span"] == [source["raw_content_span"][0] + start, source["raw_content_span"][0] + end]
        assert binding["source_anchor"]["source_sha256"] == "a" * 64


def test_fact_identity_is_stable_and_changes_with_exact_source_binding():
    bundle = reviewed_bundle()
    before = project_reviewed_facts(bundle)
    assert before == project_reviewed_facts(deepcopy(bundle))
    changed = deepcopy(bundle)
    changed["supporting_evidence"][0]["raw_content_span"] = [110, 110 + len(changed["supporting_evidence"][0]["content"])]
    after = project_reviewed_facts(changed)
    assert before["facts"][0]["fact_id"] != after["facts"][0]["fact_id"]


@pytest.mark.parametrize("mutation", ["missing_target", "wrong_same_page_ref", "changed_excerpt_hash", "changed_source_hash", "missing_raw_span"])
def test_incomplete_or_mismatched_reviewed_bindings_never_become_supported(mutation):
    bundle = reviewed_bundle()
    if mutation == "missing_target":
        bundle["terminology_mappings"][1]["target_provenance"] = []
    elif mutation == "wrong_same_page_ref":
        bundle["terminology_mappings"][1]["target_provenance"][0]["native_entry_ref"] = "definition:0"
    elif mutation == "changed_excerpt_hash":
        bundle["supporting_evidence"][1]["excerpt_sha256"] = "c" * 64
    elif mutation == "changed_source_hash":
        bundle["terminology_mappings"][1]["target_provenance"][0]["source_sha256"] = "b" * 64
    else:
        del bundle["supporting_evidence"][1]["raw_content_span"]
    view = project_reviewed_facts(bundle)
    assert view["status"] == "INSUFFICIENT_EVIDENCE"
    result = compose_grounded_answer("Define legacy join", bundle)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["answer_assessment"]["validated"] is False


def test_composer_uses_all_reviewed_facts_and_server_built_printed_page_citations():
    result = compose_grounded_answer("Define legacy join and its preferred alternatives", reviewed_bundle())
    assert result["answer_outcome"] == "extractive"
    assert result["answer_origin"] == "composed"
    assert "legacy join" in result["answer"]
    assert "target alpha" in result["answer"] and "target beta" in result["answer"]
    assert "synthetic elongated joint (for process alpha)" in result["answer"]
    assert "synthetic localized joint" in result["answer"]
    assert "incidental term" not in result["answer"] and "B1(Z)" not in result["answer"]
    assert "p. 7" in result["answer"] and "p. 3" in result["answer"]
    assert result["answer_assessment"]["status"] == "SUPPORTED_REVIEWED_FACTS"
    assert result["answer_assessment"]["validated"] is True
    assert result["answer_assessment"]["answer_sha256"] == digest(result["answer"])
    assert result["answer_assessment"]["assessment_scope"] == "reviewed_fact_bindings"
    assert result["answer_assessment"]["citation_support"] == "validated"
    assert all(claim["claim_id"] and claim["fact_ids"] and claim["anchors"] and claim["source_anchors"] and claim["source_bindings"] for claim in result["grounded_claims"])


@pytest.mark.parametrize("question", [
    "Is legacy condition always nonstandard?", "Is legacy condition not nonstandard?",
    "Legacy condition isn’t nonstandard, correct?", "Can legacy condition have no standard meaning?",
    "Legacy condition cannot be standard, can it?", "Define legacy condition",
])
def test_standard_and_conditional_senses_survive_universal_or_negated_premises(question):
    result = compose_grounded_answer(question, reviewed_bundle(conditional=True))
    assert result["answer_outcome"] == "extractive"
    assert "distinct standard meaning" in result["answer"]
    assert "when used for target alpha" in result["answer"]
    assert result["answer_assessment"]["status"] == "SUPPORTED_REVIEWED_FACTS"
    view = project_reviewed_facts(reviewed_bundle(conditional=True))
    assert {fact["kind"] for fact in view["facts"]} == {"mapping", "standard_definition", "target_definition"}


def test_explicit_conditional_mapping_retains_qualification_and_standard_context():
    bundle = reviewed_bundle(conditional=True)
    bundle["terminology_resolution"]["status"] = "qualified_mapping"
    result = compose_grounded_answer("Explain the nonstandard use of legacy condition for target alpha", bundle)
    assert result["answer_outcome"] == "extractive"
    assert "when used for target alpha" in result["answer"]
    assert "distinct standard meaning" in result["answer"]


def test_missing_application_context_keeps_all_alternatives_and_requests_context():
    result = compose_grounded_answer("Which preferred alternative does legacy join mean in my application?", reviewed_bundle())
    assert result["answer_outcome"] == "clarification"
    assert "target alpha" in result["answer"] and "target beta" in result["answer"]
    assert "context" in result["answer"].lower()


def test_unicode_dash_headword_matches_without_changing_source_spelling():
    result = compose_grounded_answer("Define LEGACY–JOIN", reviewed_bundle(headword="legacy-join"))
    assert result["answer_origin"] == "composed"
    assert "legacy-join" in result["answer"]


@pytest.mark.parametrize("question", ["Define legacy join; do not discuss acceptance criteria", "What does LEGACY JOIN mean?", "What does legacy\njoin mean?"])
def test_definition_intent_remains_available_with_typography_or_negated_excluded_topic(question):
    result = compose_grounded_answer(question, reviewed_bundle())
    assert result is not None and result["answer_origin"] == "composed"
    assert result["answer_assessment"]["validated"] is True


@pytest.mark.parametrize("question", ["Design a controller using legacy join", "Calculate fatigue life for legacy join", "Define an unrelated alloy", "What welding current should legacy join use?"])
def test_unrelated_or_unsupported_extension_intents_do_not_enter_composed_route(question):
    assert compose_grounded_answer(question, reviewed_bundle()) is None


@pytest.mark.parametrize("mutation", ["wrong_page", "wrong_hash", "wrong_section_label", "same_page_wrong_sense", "invented_fact", "claim_changed", "missing_target", "invented_panel"])
def test_exact_claim_validator_rejects_existing_wrong_sources_and_unsupported_claims(mutation):
    bundle = reviewed_bundle(conditional=True)
    view = project_reviewed_facts(bundle)
    result = compose_grounded_answer("Define legacy condition", bundle)
    claims = deepcopy(result["grounded_claims"])
    if mutation == "wrong_page":
        claims[0]["source_bindings"][0]["source_anchor"] = anchor(3)
    elif mutation == "wrong_hash":
        claims[0]["source_bindings"][0]["excerpt_sha256"] = "c" * 64
    elif mutation == "wrong_section_label":
        claims[0]["source_bindings"][0]["source_anchor"]["section_label"] = "Clause 1"
    elif mutation == "same_page_wrong_sense":
        claims[0]["source_bindings"][0]["source_entry_ref"] = "standard:entry"
    elif mutation == "invented_fact":
        claims[0]["fact_ids"] = ["fact:invented"]
    elif mutation == "claim_changed":
        claims[0]["claim"] += " It always means an extra target."
    elif mutation == "missing_target":
        claims = [claim for claim in claims if "synthetic elongated" not in claim["claim"]]
    else:
        claims[0]["anchors"].append("Figure B1(Z)")
    assessment = validate_fact_bindings(claims, view)
    assert assessment["validated"] is False
    assert assessment["citation_support"] == "invalid"


def test_exact_claim_validator_accepts_complete_server_composed_claim_set():
    bundle = reviewed_bundle()
    result = compose_grounded_answer("Define legacy join", bundle)
    assessment = validate_fact_bindings(result["grounded_claims"], project_reviewed_facts(bundle))
    assert assessment["validated"] is True
    assert assessment["status"] == "SUPPORTED_REVIEWED_FACTS"


@pytest.mark.parametrize("question", ["What's legacy join?", "What’s legacy join?", "legacy join", "LEGACY JOIN?"])
def test_common_definition_contractions_and_bare_reviewed_headword(question):
    result = compose_grounded_answer(question, reviewed_bundle())
    assert result is not None
    assert result["answer_outcome"] == "extractive"
    assert result["answer_assessment"]["validated"] is True


@pytest.mark.parametrize("mutation", ["record_only", "record_and_resolution", "partial_native_definition"])
def test_complete_projection_rejects_lost_alternative_or_truncated_native_definition(mutation):
    bundle = reviewed_bundle()
    if mutation == "record_only":
        bundle["terminology_mappings"] = bundle["terminology_mappings"][:1]
    elif mutation == "record_and_resolution":
        bundle["terminology_mappings"] = bundle["terminology_mappings"][:1]
        bundle["terminology_resolution"]["records"] = bundle["terminology_mappings"]
        bundle["terminology_resolution"]["preferred_terms"] = ["target alpha"]
        bundle["terminology_resolution"]["target_ids"] = ["onto:0"]
    else:
        bundle["terminology_mappings"][0]["target_provenance"][0]["native_text_unchanged"] = "target alpha. A synthetic elongated joint"
    view = project_reviewed_facts(bundle)
    assert view["status"] == "INSUFFICIENT_EVIDENCE"
    result = compose_grounded_answer("Define legacy join", bundle)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["answer_assessment"]["validated"] is False


def test_listing_preferred_terms_is_not_an_application_choice():
    result = compose_grounded_answer("Which preferred terms replace legacy join?", reviewed_bundle())
    assert result["answer_outcome"] == "extractive"
    assert "target alpha" in result["answer"] and "target beta" in result["answer"]
    assert "Please provide" not in result["answer"]


def test_positive_unsupported_request_after_unrelated_exclusion_does_not_receive_partial_answer():
    result = compose_grounded_answer("Define legacy join without examples and state acceptance criteria", reviewed_bundle())
    assert result is None


def test_coordinated_visual_request_survives_negated_topic_removal():
    result = compose_grounded_answer("Define legacy join without acceptance criteria and explain Figure A1", reviewed_bundle())
    assert result is None


@pytest.mark.parametrize("topic", ["Figures A1 and A2", "tables", "diagrams", "dimensions", "temperatures"])
def test_positive_plural_unsupported_extensions_do_not_receive_partial_definitions(topic):
    assert compose_grounded_answer("Define legacy join and explain " + topic, reviewed_bundle()) is None


@pytest.mark.parametrize("verb", ["discussing", "including", "covering", "addressing", "providing"])
def test_adjacent_negated_topic_gerund_keeps_reviewed_definition(verb):
    result = compose_grounded_answer("Define legacy join without " + verb + " acceptance criteria", reviewed_bundle())
    assert result is not None
    assert result["answer_outcome"] == "extractive"
    assert result["answer_assessment"]["validated"] is True


def test_coordinated_unknown_definition_subject_falls_through():
    assert compose_grounded_answer("Define legacy join and another synthetic term", reviewed_bundle()) is None


def test_adjacent_known_negated_topic_list_keeps_definition():
    result = compose_grounded_answer("Define legacy join without acceptance criteria or welding current", reviewed_bundle())
    assert result is not None
    assert result["answer_outcome"] == "extractive"


def test_positive_request_after_negated_topic_list_remains_unsupported():
    assert compose_grounded_answer("Define legacy join without acceptance criteria or welding current and explain Figure A1", reviewed_bundle()) is None


@pytest.mark.parametrize("question", [
    "Define legacy join for process omega",
    "Does legacy join always name one preferred term in every process?",
])
def test_reviewed_entry_scope_note_limits_process_universal_inference(question):
    bundle = reviewed_bundle()
    baseline = compose_grounded_answer("Define legacy join", bundle)
    result = compose_grounded_answer(question, bundle)
    notes = result["answer_policy_notes"]
    assert len(notes) == 1
    assert notes[0]["kind"] == "process_scope_limit"
    assert notes[0]["scope"] == "supplied_reviewed_entries"
    assert notes[0]["text"] in result["answer"]
    assert "do not by themselves establish" in notes[0]["text"]
    assert "process-specific rule" in notes[0]["text"]
    assert "universally interchangeable" in notes[0]["text"]
    assert not {"fact_ids", "source_bindings", "source_anchors", "anchors"}.intersection(notes[0])
    assert result["grounded_claims"] == baseline["grounded_claims"]
    assert result["citations"] == baseline["citations"]
    assert "target alpha" in result["answer"] and "target beta" in result["answer"]
    assert "process alpha" in result["answer"]
    assert "process omega" not in result["answer"]
    assert all(notes[0]["text"] != claim["claim"] for claim in result["grounded_claims"])
    assert result["answer_assessment"]["answer_sha256"] == digest(result["answer"])


def test_process_scope_policy_keeps_conditional_and_standard_facts_separate():
    bundle = reviewed_bundle(conditional=True)
    bundle["terminology_resolution"]["status"] = "qualified_mapping"
    baseline = compose_grounded_answer("Define legacy condition", bundle)
    result = compose_grounded_answer("Explain the nonstandard use of legacy condition for process omega", bundle)
    assert result["answer_policy_notes"][0]["scope"] == "supplied_reviewed_entries"
    assert result["grounded_claims"] == baseline["grounded_claims"]
    assert "distinct standard meaning" in result["answer"]
    assert "when used for target alpha" in result["answer"]
    assert result["answer_assessment"]["validated"] is True


def test_process_qualification_does_not_relax_missing_evidence_or_extension_guards():
    bundle = reviewed_bundle()
    bundle["terminology_mappings"][1]["target_provenance"] = []
    incomplete = compose_grounded_answer("Define legacy join for process omega", bundle)
    assert incomplete["answer_outcome"] == "insufficient_evidence"
    assert incomplete["answer_assessment"]["validated"] is False
    assert not incomplete.get("answer_policy_notes")
    assert compose_grounded_answer("Design a procedure using legacy join for process omega", reviewed_bundle()) is None
