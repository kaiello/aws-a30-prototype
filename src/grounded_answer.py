"""Pure, bounded rendering of already reviewed terminology evidence.

This is an extractive route, not model entailment or general question answering.
It reads no registry, manifest, database, evaluation labels or external files.
"""
from copy import deepcopy
import hashlib
import json
import re

from src.citation_checker import validate_fact_bindings

_DASHES = str.maketrans({character: "-" for character in "‐‑‒–—−"})


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require(condition):
    if not condition:
        raise ValueError("reviewed_fact_binding_incomplete")


def _normal(text):
    return " ".join(str(text).split())


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(deepcopy(value))
    return result


def _entry_span(excerpt, native):
    """Find a unique full reviewed entry, retaining exact excerpt coordinates."""
    tokens = list(re.finditer(r"\S+", excerpt))
    text, offsets = "", []
    for token in tokens:
        if text:
            text += " "
            offsets.append(token.start() - 1)
        text += token[0]
        offsets.extend(range(token.start(), token.end()))
    needle = _normal(native)
    positions = [match.start() for match in re.finditer(re.escape(needle), text)] if needle else []
    _require(len(positions) == 1)
    start = positions[0]
    return [offsets[start], offsets[start + len(needle) - 1] + 1]


def _binding(proof, native, ref, role, members, document, ref_text):
    _require(isinstance(proof, dict) and proof.get("verification_state") == "verified"
             and isinstance(native, str) and native.strip() and isinstance(ref, str) and ref)
    identity = _normal(native)
    _require(ref not in ref_text or ref_text[ref] == identity)
    ref_text[ref] = identity
    candidates = []
    for member in members:
        if ref not in member.get("source_entry_refs", []) or role not in member.get("supports", []):
            continue
        if proof.get("exact_existing_chunk_id", member["id"]) != member["id"]:
            continue
        _require(proof.get("exact_existing_full_doc_id", member["full_doc_id"]) == member["full_doc_id"]
                 and proof.get("chunk_content_sha256_utf8", member["content_sha256"]) == member["content_sha256"])
        for anchor in member["source_anchors"]:
            keys = ("document_id", "source_sha256", "section_id", "pdf_index", "printed_label")
            if any(proof.get(key) != anchor.get(key) for key in keys):
                continue
            _require((anchor["document_id"], anchor["source_sha256"]) == document
                     and anchor.get("verification_state") == "verified"
                     and isinstance(anchor.get("section_label"), str) and anchor["section_label"]
                     and ("section_label" not in proof or proof["section_label"] == anchor["section_label"]))
            try:
                span = _entry_span(member["content"], native)
            except ValueError:
                continue
            candidates.append({"evidence_id": member["id"], "full_doc_id": member["full_doc_id"],
                               "excerpt_sha256": member["excerpt_sha256"], "content_sha256": member["content_sha256"],
                               "raw_content_span": deepcopy(member["raw_content_span"]),
                               "span_space": member["span_space"], "source_entry_refs": deepcopy(member["source_entry_refs"]),
                               "source_entry_ref": ref, "excerpt_span": span,
                               "fact_raw_content_span": [member["raw_content_span"][0] + value for value in span],
                               "source_text": member["content"][span[0]:span[1]],
                               "source_anchor": deepcopy(anchor), "verification_state": "verified"})
    _require(len(candidates) == 1)
    return candidates


def _fact(kind, headword, native, bindings, *, sense="", context="", targets=(), qualification="", mapping_ids=()):
    # Native 'See...' clauses are navigation, not reviewed panel-understanding
    # claims. Render the supported definition without promoting those panels.
    text = re.split(r"\s+See(?:\s+also)?\s+", _normal(native), maxsplit=1)[0].strip()
    _require(text.startswith(headword + ".") and len(text) > len(headword) + 2)
    anchors = _unique([binding["source_anchor"] for binding in bindings])
    fact = {"kind": kind, "headword": headword, "sense": sense, "process_context": context,
            "targets": list(targets), "qualification": qualification, "mapping_ids": list(mapping_ids),
            "text": text, "source_bindings": bindings, "source_anchors": anchors,
            "anchors": _unique([f"{anchor['section_label']}, p. {anchor['printed_label']}" for anchor in anchors])}
    fact["fact_id"] = "fact:" + _digest(_json(fact))
    return fact


def _projection_text(proof):
    text, span = proof.get("text"), proof.get("span")
    _require(isinstance(text, str) and isinstance(span, list) and len(span) == 2
             and all(type(value) is int for value in span) and 0 <= span[0] < span[1] <= len(text))
    return _normal(text[span[0]:span[1]])


def _complete_mapping(group):
    """Every qualified alternative in the reviewed parser span must survive."""
    first = group[0]
    targets = []
    for record in group:
        wording = record["preferred_term"]
        if record.get("target_process_context"):
            wording += " (" + record["target_process_context"] + ")"
        targets.append(re.escape(_normal(wording)))
        _require(record["qualification"] == first["qualification"])
    pattern = (re.escape(first["nonstandard_term"] + ". A nonstandard term " + first["qualification"] + " ")
               + r"(?:\s+or\s+|\s*;\s*)".join(targets) + r"\.")
    _require(re.fullmatch(pattern, _projection_text(first["source"]), re.IGNORECASE) is not None)


def project_reviewed_facts(bundle):
    """Project complete native-entry bindings; never infer absent definitions."""
    empty = {"status": "UNASSESSED", "facts": [], "diagnostics": ["not_reviewed_terminology"]}
    if not isinstance(bundle, dict) or bundle.get("evidence_type") != "terminology_mapping":
        return empty
    try:
        records = bundle["terminology_mappings"]
        members = bundle["supporting_evidence"]
        resolution = bundle["terminology_resolution"]
        source_anchors = bundle["source_anchors"]
        _require(records and members and source_anchors)
        _require(resolution.get("records") == records
                 and resolution.get("preferred_terms") == _unique([record["preferred_term"] for record in records])
                 and resolution.get("target_ids") == _unique([record["target_id"] for record in records]))
        document = (source_anchors[0]["document_id"], source_anchors[0]["source_sha256"])
        _require(re.fullmatch(r"[0-9a-f]{64}", document[1]) is not None)
        for member in members:
            span = member["raw_content_span"]
            _require(member.get("verification_state") == "verified" and isinstance(member["content"], str)
                     and _digest(member["content"]) == member["excerpt_sha256"]
                     and re.fullmatch(r"[0-9a-f]{64}", member["content_sha256"]) is not None
                     and isinstance(span, list) and len(span) == 2 and all(type(v) is int for v in span)
                     and 0 <= span[0] < span[1] and span[1] - span[0] == len(member["content"])
                     and isinstance(member["span_space"], str) and member["span_space"]
                     and member["source_entry_refs"] and member["source_anchors"])
        groups = {}
        for record in records:
            _require(record.get("verification_state") == "verified" and not record.get("diagnostics")
                     and record.get("relation_type") == "NONSTANDARD_FOR" and record.get("target_id")
                     and record.get("qualification") in {"for", "when used for"})
            key = _json([record["nonstandard_term"], record.get("source_sense", ""),
                         record.get("source_process_context", ""), record["source"]])
            groups.setdefault(key, []).append(record)
        facts, ref_text = [], {}
        provenance = resolution.get("source_provenance", [])
        for group in groups.values():
            _complete_mapping(group)
            first = group[0]
            source = first["source"]
            headword, ref = first["nonstandard_term"], source["native_entry_ref"]
            native = source["native_text_unchanged"]
            bindings = _binding(source, native, ref, "mapping", members, document, ref_text)
            facts.append(_fact("mapping", headword, native, bindings, sense=first.get("source_sense", ""),
                               context=first.get("source_process_context", ""),
                               targets=_unique([record["preferred_term"] for record in group]),
                               qualification=first["qualification"], mapping_ids=[record["mapping_id"] for record in group]))
            entries = [entry for entry in provenance if ref in entry.get("original_entry", {}).get("native_entry_refs", [])]
            _require(len(entries) == 1)
            standard = entries[0].get("standard_sense")
            if standard is not None:
                standard_ref = standard["source_entry_ref"]
                allowed = [member for member in members if member["id"] in standard["evidence_member_ids"]]
                proof = dict(entries[0]["source_anchor"], verification_state="verified")
                bindings = _binding(proof, standard["text"], standard_ref, "standard_sense", allowed, document, ref_text)
                facts.append(_fact("standard_definition", headword, standard["text"], bindings, sense="standard"))
            for record in group:
                proofs = record.get("target_provenance", [])
                _require(len(proofs) == 1)
                proof = proofs[0]
                _require(_projection_text(proof) == _normal(proof["native_text_unchanged"]))
                bindings = _binding(proof, proof["native_text_unchanged"], proof["native_entry_ref"],
                                    "target:" + record["preferred_term"], members, document, ref_text)
                fact = _fact("target_definition", record["preferred_term"], proof["native_text_unchanged"], bindings,
                             sense=record.get("target_sense", ""), context=record.get("target_process_context", ""))
                if fact not in facts:
                    facts.append(fact)
        _require(facts)
        return {"status": "SUPPORTED_REVIEWED_FACTS", "facts": facts, "diagnostics": [],
                "resolution_status": resolution.get("status"), "bundle_id": bundle["id"]}
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return {"status": "INSUFFICIENT_EVIDENCE", "facts": [], "diagnostics": ["reviewed_fact_binding_incomplete"]}


def _query_normal(query):
    text = _normal(str(query).translate(_DASHES).replace("’", "'").replace("‘", "'")).casefold()
    return re.sub(r"\bwhat's\b", "what is", text)


def _mentions(term, query):
    pattern = r"(?<![\w-])" + r"\s+".join(re.escape(word) for word in _query_normal(term).split()) + r"(?![\w-])"
    return re.search(pattern, query) is not None


def _without_excluded_topics(query):
    # Remove only adjacent named topics, including an explicit known-topic list.
    # A coordinated verb/unknown phrase ends the exclusion immediately.
    topic = r"(?:acceptance\s+criteria|welding\s+current|preheat\s+temperatures?)\b"
    verb = r"(?:discuss(?:ing)?|includ(?:e|ing)|cover(?:ing)?|address(?:ing)?|provid(?:e|ing))"
    pattern = (r"\b(?:do not|don't|without|excluding)\s+(?:" + verb + r"\s+)?" + topic
               + r"(?:\s*(?:,|and|or)\s*" + topic + r")*")
    return re.sub(pattern, "", query)


def _definition_intent(query):
    text = _without_excluded_topics(query)
    if re.search(r"\bacceptance\s+criteria\b|\b(?:calculate|design|fatigue|currents?|voltages?|temperatures?|strengths?|dimensions?|inspections?|repairs?|procedures?|diagrams?|figures?|tables?|footnotes?|pixels?|spatial)\b", text):
        return False
    return bool(re.search(r"\b(?:define|definition|meaning|mean|means|term|terminology|preferred|nonstandard|standard|alternative|refer|replacement|replace|difference|distinguish|explain|compare|correct|only|always|never|which|choose|select)\b|\bwhat\s+(?:is|are|does)\b", text))


def _supported_definition_subjects(query, known_terms):
    """Do not certify a partial answer to an explicit coordinated subject list."""
    text = _without_excluded_topics(query)
    for request in re.finditer(r"\b(?:define|describe|explain|what\s+(?:is|are))\s+([^;.!?]+)", text):
        subjects = re.split(r"\s*[,;]\s*|\b(?:and|or|plus)\b", request[1])
        if len(subjects) < 2:
            continue
        for subject in subjects:
            if any(_mentions(term, subject) for term in known_terms):
                continue
            # Explicit local references request properties of the known entry,
            # rather than introducing another unreviewed definition subject.
            local = re.fullmatch(r"\s*(?:(?:define|describe|explain)\s+)?(?:its|their)\s+(?:(?:preferred|standard|conditional)\s+)?(?:definitions?|meanings?|senses?|terms?|alternatives|names|replacements)\s*", subject)
            if not local:
                return False
    return True


def _citations(facts):
    anchors = _unique([anchor for fact in facts for anchor in fact["source_anchors"]])
    labels = _unique([anchor["section_label"] for anchor in anchors])
    return {"clauses": labels, "pages": _unique([int(anchor["printed_label"]) for anchor in anchors if anchor["printed_label"].isdigit()]),
            "figures": [], "tables": [], "unresolved_elements": [], "has_citation": bool(anchors),
            "source_anchors": {label: [anchor for anchor in anchors if anchor["section_label"] == label] for label in labels}}


def compose_grounded_answer(query, bundle):
    """Return a bounded extract/clarification, or None for an unsupported intent."""
    if not isinstance(bundle, dict) or bundle.get("evidence_type") != "terminology_mapping":
        return None
    normalized = _query_normal(query)
    terms = bundle.get("terminology_resolution", {}).get("matched_terms", [])
    bare_headword = any(normalized.strip(" ?.!\"'“”") == _query_normal(term) for term in terms)
    if not terms or not all(_mentions(term, normalized) for term in terms) or not (bare_headword or _definition_intent(normalized)):
        return None
    if not _supported_definition_subjects(normalized, terms + bundle.get("terminology_resolution", {}).get("preferred_terms", [])):
        return None
    view = project_reviewed_facts(bundle)
    if view["status"] != "SUPPORTED_REVIEWED_FACTS":
        answer = "Reviewed evidence is incomplete for this definition. A source review is required before answering."
        return {"answer": answer, "citations": {}, "grounded_claims": [],
                "answer_outcome": "insufficient_evidence", "answer_origin": "none",
                "answer_assessment": {"status": "INSUFFICIENT_EVIDENCE", "validated": False,
                                      "answer_sha256": _digest(answer), "assessment_scope": "reviewed_fact_bindings",
                                      "citation_support": "invalid", "diagnostics": view["diagnostics"]}}
    facts = view["facts"]
    claims = [{"claim_id": "claim:" + fact["fact_id"].removeprefix("fact:"), "claim": fact["text"],
               "fact_ids": [fact["fact_id"]], "anchors": deepcopy(fact["anchors"]),
               "source_anchors": deepcopy(fact["source_anchors"]), "source_bindings": deepcopy(fact["source_bindings"])} for fact in facts]
    lines = [f"- {claim['claim']} ({'; '.join(claim['anchors'])})" for claim in claims]
    application_choice = bool(re.search(r"\b(?:choose|select|apply)\b|\bmy\s+(?:application|case|context)\b", normalized))
    listing = bool(re.search(r"\bwhich\s+(?:preferred\s+)?(?:terms|alternatives|names|replacements)\b", normalized))
    selection = application_choice or (bool(re.search(r"\bwhich\b", normalized)) and not listing)
    has_options = any(len(fact["targets"]) > 1 for fact in facts) or any(fact["kind"] == "standard_definition" for fact in facts)
    clarify = selection and has_options
    if any(fact["kind"] == "standard_definition" for fact in facts):
        lines.append("The standard definition and the conditional nonstandard use are distinct; the conditional wording does not classify every use of the headword as nonstandard.")
    if any(len(fact["targets"]) > 1 for fact in facts):
        lines.append("The reviewed mapping preserves all listed alternatives; the headword alone does not select one.")
    if clarify:
        lines.append("Please provide the application context needed to choose the intended sense or alternative.")
    policy_notes = [{"kind": "process_scope_limit", "scope": "supplied_reviewed_entries",
                     "text": "Scope note: The supplied reviewed entries do not by themselves establish a process-specific rule making the listed meanings universally interchangeable. Any stated conditions still apply; process-specific application requires additional supporting evidence."}]
    lines.extend(note["text"] for note in policy_notes)
    answer = "\n\n".join(lines)
    assessment = validate_fact_bindings(claims, view)
    assessment["answer_sha256"] = _digest(answer)
    return {"answer": answer, "citations": _citations(facts), "grounded_claims": claims,
            "answer_outcome": "clarification" if clarify else "extractive", "answer_origin": "composed",
            "answer_assessment": assessment, "answer_policy_notes": policy_notes}
