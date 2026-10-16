"""Deterministic claim/source links, without inferring semantic entailment.

``reviewed_fact_view`` is a privileged server argument from
``project_reviewed_facts``. Claim/context flags never establish that authority.
Available assets establish transport integrity, not diagram understanding.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from time import perf_counter

from src.standard_manifest import ManifestError, extract_reference_records, get_manifest


SUPPORTED = "SUPPORTED_REVIEWED_FACTS"
UNASSESSED = "UNASSESSED"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _records(value):
    return value if isinstance(value, (list, tuple)) else []


class _ReferenceManifest:
    """Keep parser lookup time separate from lexical reference parsing."""

    def __init__(self, manifest, timings):
        self.manifest, self.timings = manifest, timings

    def _call(self, function, *args):
        started = perf_counter()
        try:
            return function(*args)
        finally:
            self.timings["manifest_lookup"] += (perf_counter() - started) * 1000

    def resolve(self, label):
        return self._call(self.manifest.resolve, label)

    def labels(self, kind):
        return self._call(self.manifest.labels, kind)

    def element(self, label):
        return self._call(self.manifest.element, label)

    def source_anchors(self, label):
        return self._call(self.manifest.source_anchors, label)

    @property
    def document(self):
        return self._call(lambda: self.manifest.document)


def _identity(anchor):
    """Normalize only the two explicit server-owned source-anchor schemas."""
    if not isinstance(anchor, dict):
        return None
    if "source_id" in anchor and "element_id" in anchor:
        result = anchor.get("source_id"), anchor.get("source_sha256"), anchor.get("element_id")
    elif "document_id" in anchor and "section_id" in anchor:
        result = anchor.get("document_id"), anchor.get("source_sha256"), anchor.get("section_id")
    else:
        return None
    return result if all(isinstance(value, str) and value for value in result) else None


def _anchor_key(anchor):
    identity = _identity(anchor)
    if (identity is None or type(anchor.get("pdf_index")) is not int or anchor["pdf_index"] < 0
            or "printed_label" not in anchor):
        return None
    printed = anchor["printed_label"]
    if printed is not None and not isinstance(printed, str):
        return None
    return identity + (anchor["pdf_index"], printed)


def _reference_status(mentions):
    states = _unique(mention["resolution"]["status"] for mention in mentions)
    return states[0] if len(states) == 1 else "mixed" if states else "not_cited"


def _page_qualifier_matches(mention, anchors):
    """Match a printed-page request within supplied canonical/native anchors."""
    targets = set(mention.get("qualifies_target_ids", mention["resolution"].get("target_ids", [])))
    if targets:
        anchors = [anchor for anchor in anchors if _identity(anchor) is not None and _identity(anchor)[2] in targets]
    pages = mention.get("page_candidates", [])
    return bool(pages) and all(any(page.get("pdf_index") == anchor.get("pdf_index")
                                   and page.get("printed_label") == anchor.get("printed_label")
                                   for anchor in anchors) for page in pages)


def qualify_reference_hierarchy(text, mentions, *, manifest=None):
    """Retain occurrences while distinguishing an attached source location.

    ``Annex X, Figure X1`` names the figure within a parent; ``Annex X and
    Figure X1`` names independent sources. Only canonical ``parent_id`` proves
    the former hierarchy. Page/panel qualifiers and parser resolutions remain
    intact, and a contradictory parent never becomes an acceptable binding.
    Explicit page qualifiers are checked against canonical element anchors,
    without reading asset bytes. This projection is also usable on complete
    generated prose before claims have been extracted; it does not infer
    semantic support.
    """
    manifest = get_manifest() if manifest is None else manifest
    text = str(text or "")
    annotated = deepcopy(list(_records(mentions)))
    diagnostics = []
    for index, parent in enumerate(annotated[:-1]):
        if parent.get("kind") not in {"clause", "annex"}:
            continue
        children = []
        previous = parent
        for child in annotated[index + 1:]:
            if child.get("kind") not in {"figure", "table"}:
                break
            separator = text[previous["end"]:child["start"]]
            shape = r"\s*,\s*" if not children else r"\s*(?:,\s*(?:and\s+)?|and\s+|&\s*)"
            if not re.fullmatch(shape, separator, re.IGNORECASE):
                break
            children.append(child)
            previous = child
        if not children:
            continue
        target_ids = _unique(target for child in children for target in child["resolution"].get("target_ids", []))
        parent["reference_role"] = "location_qualifier"
        parent["qualifies_target_ids"] = target_ids
        parent_ids = parent["resolution"].get("target_ids", [])
        if parent["resolution"]["status"] != "exact" or len(parent_ids) != 1:
            diagnostics.append("parent_qualifier_unresolved")
        elif any((record := manifest.element(target)) is None or record.get("parent_id") != parent_ids[0]
                 for target in target_ids):
            diagnostics.append("parent_qualifier_mismatch")
    for mention in annotated:
        if not mention.get("qualifiers", {}).get("page") or mention["resolution"]["status"] != "exact":
            continue
        targets = mention.get("qualifies_target_ids", mention["resolution"].get("target_ids", []))
        anchors = [anchor for target in targets for anchor in manifest.source_anchors(target)]
        if not _page_qualifier_matches(mention, anchors):
            diagnostics.append("page_qualifier_mismatch")
    return {"mentions": annotated, "diagnostics": _unique(diagnostics)}


def _asset_descriptor(asset, manifest):
    relative = asset["relpath"]
    root = getattr(manifest, "root", None)
    return {"path": str(Path(root) / PurePosixPath(relative)) if root is not None else relative,
            "relpath": relative, "sha256": asset.get("sha256"),
            "source_anchor_orders": deepcopy(asset["source_anchor_orders"]),
            "kind": "text" if PurePosixPath(relative).suffix.lower() == ".md" else "image",
            "verification_state": asset.get("verification", {}).get("state", "candidate")}


def _element_evidence(manifest, label, relationship, timings):
    started = perf_counter()
    record = manifest.element(label)
    anchors = manifest.source_anchors(label)
    timings["manifest_lookup"] += (perf_counter() - started) * 1000
    if record is None:
        return None, ["element_unavailable"]
    declared = [_asset_descriptor(asset, manifest) for asset in record.get("assets", [])]
    result = {"element_id": record["id"], "label": record["label"], "relationship": relationship,
              "source_anchors": deepcopy(anchors), "declared_assets": declared, "assets": [],
              "asset_status": "source_only" if anchors else "unavailable"}
    if not declared:
        return result, []
    started = perf_counter()
    try:
        # This is the same canonical validator used by legacy asset_paths.
        # Its per-asset results retain healthy paths when another member fails.
        validated = manifest.validated_assets(label)
    except ManifestError as exc:
        result["asset_status"] = {"MANIFEST_ASSET_MISSING": "missing",
                                  "MANIFEST_ASSET_MISMATCH": "corrupt"}.get(exc.code, "unavailable")
        diagnostics = [exc.code]
    except OSError:
        result["asset_status"] = "unavailable"
        diagnostics = ["asset_validation_unavailable"]
    else:
        by_relative = {asset["relpath"]: asset for asset in declared}
        # Associate by canonical relative path, never by zipping assets to pages.
        if (len(validated) != len(declared)
                or any(asset.get("relpath") not in by_relative for asset in validated)):
            result["asset_status"] = "unavailable"
            diagnostics = ["asset_binding_unavailable"]
        else:
            states, diagnostics = [], []
            for asset in validated:
                declaration = by_relative[asset["relpath"]]
                status = asset.get("status", "unavailable")
                if status not in {"complete", "missing", "corrupt", "unavailable"}:
                    status = "unavailable"
                if (asset.get("sha256") != declaration["sha256"]
                        or asset.get("source_anchor_orders") != declaration["source_anchor_orders"]
                        or (status == "complete" and not asset.get("path"))):
                    status = "unavailable"
                    diagnostics.append("asset_binding_unavailable")
                states.append(status)
                if status == "complete":
                    rendered = {key: deepcopy(value) for key, value in declaration.items() if key != "relpath"}
                    rendered["path"] = asset["path"]
                    result["assets"].append(rendered)
                elif asset.get("error_code"):
                    diagnostics.append(asset["error_code"])
            result["asset_status"] = next((state for state in ("corrupt", "missing", "unavailable")
                                           if state in states), "complete")
    finally:
        timings["asset_validation"] += (perf_counter() - started) * 1000
    return result, diagnostics


def _ordered_evidence(manifest, mentions, timings, fact=None):
    requests = []
    for mention in mentions:
        if mention.get("reference_role") == "location_qualifier":
            continue
        resolution = mention["resolution"]
        relationship = "direct" if resolution["status"] == "exact" else "navigation_candidate"
        if resolution["status"] not in {"exact", "group", "unsupported_qualifier"}:
            continue
        for label in resolution.get("labels", []):
            previous = next((item for item in requests if item[0] == label), None)
            if previous is None:
                requests.append([label, relationship])
            elif relationship == "direct":
                previous[1] = "direct"
    # A reviewed page-only citation has native element identity in the trusted
    # fact bindings. Page numbers themselves never establish that identity.
    if fact is not None and mentions and all(mention["resolution"]["status"] == "page_only" for mention in mentions):
        started = perf_counter()
        for anchor in _records(fact.get("source_anchors")):
            identity = _identity(anchor)
            record = manifest.element(identity[2]) if identity is not None else None
            if record is not None and not any(item[0] == record["label"] for item in requests):
                requests.append([record["label"], "direct"])
        timings["manifest_lookup"] += (perf_counter() - started) * 1000
    # Typed companions remain optional navigation, even when their files fail.
    started = perf_counter()
    companions = manifest.companions()
    timings["manifest_lookup"] += (perf_counter() - started) * 1000
    for label, relationship in list(requests):
        if relationship == "direct":
            for candidate in companions.get(label, []):
                if not any(item[0] == candidate for item in requests):
                    requests.append([candidate, "navigation_candidate"])
    results, diagnostics = [], []
    for label, relationship in requests:
        evidence, codes = _element_evidence(manifest, label, relationship, timings)
        if evidence is not None:
            results.append(evidence)
        if relationship == "direct":
            diagnostics.extend(codes)
    return results, _unique(diagnostics)


def _required_asset_status(evidence):
    states = [item["asset_status"] for item in evidence if item["relationship"] == "direct"]
    if not states:
        return "unavailable"
    for state in ("corrupt", "missing", "unavailable"):
        if state in states:
            return state
    return "source_only" if all(state == "source_only" for state in states) else "complete"


def _reviewed_sources_match(fact, direct):
    supplied = _records(fact.get("source_anchors"))
    required = [anchor for evidence in direct for anchor in evidence["source_anchors"]]
    if not supplied or not required or any(_identity(anchor) is None for anchor in supplied):
        return False
    for anchor in supplied:
        if not any(_identity(anchor) == _identity(expected)
                   and anchor.get("pdf_index") == expected.get("pdf_index")
                   and anchor.get("printed_label") == expected.get("printed_label") for expected in required):
            return False
    return {_identity(anchor) for anchor in required} == {_identity(anchor) for anchor in supplied}


def _page_qualifiers_match(mentions, direct, fact=None):
    """Check explicit printed-page requests against the actual bound source."""
    for mention in mentions:
        if not mention.get("qualifiers", {}).get("page"):
            continue
        status = mention["resolution"]["status"]
        if status not in {"exact", "page_only"} or (status == "page_only" and fact is None):
            continue
        anchors = (_records(fact.get("source_anchors")) if fact is not None else
                   [anchor for item in direct for anchor in item["source_anchors"]])
        if not _page_qualifier_matches(mention, anchors):
            return False
    return True


def _binding_status(claim, direct, context_by_id, duplicate_ids, fact=None):
    if not direct:
        return "unavailable", []
    if fact is not None and not _reviewed_sources_match(fact, direct):
        return "mismatched", ["reviewed_source_mismatch"]
    if "selected_evidence_ids" not in claim:
        return ("matched", []) if fact is not None else ("unavailable", [])
    selected_ids = claim["selected_evidence_ids"]
    if not isinstance(selected_ids, (list, tuple)) or not selected_ids:
        return ("incomplete" if fact is not None else "unavailable"), ["selected_evidence_unavailable"]
    if any(not isinstance(value, str) or not value for value in selected_ids):
        return "unavailable", ["selected_evidence_invalid"]
    if len(selected_ids) != len(set(selected_ids)):
        return "mismatched", ["duplicate_selected_evidence_id"]
    if any(value in duplicate_ids for value in selected_ids):
        return "mismatched", ["duplicate_evidence_id"]
    if any(value not in context_by_id for value in selected_ids):
        return "mismatched", ["selected_evidence_missing"]
    selected = [context_by_id[value] for value in selected_ids]
    # Selection eligibility is separate from a literal citation's identity.
    # A typed navigation context cannot fill a required selected-source role,
    # even when its canonical document/element/page metadata matches exactly.
    navigation_only = [item.get("relationship") in ("navigation_candidate", "ui_companion")
                       or item.get("selection_role") == "ui_companion" for item in selected]
    if any(navigation_only):
        status = "incomplete" if fact is not None or not all(navigation_only) else "unavailable"
        return status, ["navigation_only_selected_evidence"]
    if fact is not None:
        bindings = [binding for item in selected for binding in _records(item.get("source_bindings"))]
        expected = _records(fact.get("source_bindings"))
        if not bindings:
            return "incomplete", ["selected_native_binding_unavailable"]
        if (bindings != expected or any(not isinstance(binding, dict) for binding in expected)
                or list(selected_ids) != _unique(binding.get("evidence_id") for binding in expected)):
            return "mismatched", ["selected_evidence_mismatch"]
        return "matched", []
    anchor_sets = [_records(item.get("source_anchors")) for item in selected]
    if any(not anchors for anchors in anchor_sets):
        status = "incomplete" if any(anchor_sets) else "unavailable"
        return status, ["selected_source_anchors_unavailable"]
    supplied = [anchor for anchors in anchor_sets for anchor in anchors]
    if any(_anchor_key(anchor) is None for anchor in supplied):
        return "mismatched", ["selected_source_anchor_invalid"]
    observed = {_anchor_key(anchor) for anchor in supplied}
    if not observed:
        return "unavailable", ["selected_source_anchors_unavailable"]
    required = {_anchor_key(anchor) for evidence in direct for anchor in evidence["source_anchors"]}
    if None in required:
        return "unavailable", ["canonical_source_anchors_unavailable"]
    if observed - required:
        return "mismatched", ["selected_evidence_mismatch"]
    if required - observed:
        return "incomplete", ["selected_evidence_incomplete"]
    return "matched", []


def _anchor_projection(anchor):
    fields = {"source_id", "document_id", "source_sha256", "element_id", "section_id", "section_label",
              "pdf_index", "pdf_page_ordinal", "printed_label", "normative_status", "verification_state"}
    return {key: deepcopy(value) for key, value in anchor.items() if key in fields} if isinstance(anchor, dict) else {}


def _binding_projection(binding):
    """Retain entry/span identity and a digest of the complete original binding."""
    if not isinstance(binding, dict):
        return {"binding_sha256": None}
    fields = {"evidence_id", "full_doc_id", "excerpt_sha256", "content_sha256", "raw_content_span",
              "span_space", "source_entry_refs", "source_entry_ref", "excerpt_span",
              "fact_raw_content_span", "verification_state"}
    projection = {key: deepcopy(value) for key, value in binding.items() if key in fields}
    if "source_anchor" in binding:
        projection["source_anchor"] = _anchor_projection(binding["source_anchor"])
    try:
        canonical = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        projection["binding_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        projection["binding_sha256"] = None
    return projection


def _binding_evidence(claim, context_by_id, duplicate_ids, fact=None):
    results = []
    for evidence_id in _records(claim.get("selected_evidence_ids")):
        status = "invalid"
        selected = None
        if isinstance(evidence_id, str):
            status = "duplicate" if evidence_id in duplicate_ids else "selected" if evidence_id in context_by_id else "missing"
            selected = context_by_id[evidence_id] if status == "selected" else None
        results.append({"role": "selected_context", "evidence_id": deepcopy(evidence_id), "selection_status": status,
                        "relationship": deepcopy(selected.get("relationship")) if selected else None,
                        "selection_role": deepcopy(selected.get("selection_role")) if selected else None,
                        "source_anchors": [_anchor_projection(anchor) for anchor in _records(selected.get("source_anchors"))] if selected else [],
                        "source_bindings": [_binding_projection(binding) for binding in _records(selected.get("source_bindings"))] if selected else []})
    if isinstance(fact, dict):
        results.append({"role": "expected_reviewed", "fact_id": fact.get("fact_id"),
                        "source_anchors": [_anchor_projection(anchor) for anchor in _records(fact.get("source_anchors"))],
                        "source_bindings": [_binding_projection(binding) for binding in _records(fact.get("source_bindings"))]})
    return results


def resolve_claim_evidence(claims, evidence_context=(), *, reviewed_fact_view=None, manifest=None):
    """Link ordered claims to exact source identities and validated asset sets.

    Only a complete unchanged server-projected reviewed fact view can establish
    support. Ordinary context must be explicitly selected per claim and can
    establish metadata binding only. Failure denotes insufficient selected
    evidence, never a global contradiction of the claim.
    """
    started = perf_counter()
    timings = {key: 0.0 for key in ("reference_parse", "manifest_lookup", "asset_validation", "binding_checks", "total")}
    lookup_started = perf_counter()
    manifest = get_manifest() if manifest is None else manifest
    timings["manifest_lookup"] += (perf_counter() - lookup_started) * 1000
    valid_claims = isinstance(claims, list) and all(isinstance(claim, dict) for claim in claims)
    claim_records = claims if valid_claims else []
    facts = reviewed_fact_view.get("facts", []) if isinstance(reviewed_fact_view, dict) else []
    facts = facts if isinstance(facts, list) else []
    required_ids = [fact.get("fact_id") for fact in facts if isinstance(fact, dict)]
    observed_ids = [fact_id for claim in claim_records for fact_id in _records(claim.get("fact_ids"))]
    context_by_id, duplicate_ids = {}, set()
    for item in _records(evidence_context):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        if item["id"] in context_by_id:
            duplicate_ids.add(item["id"])
        else:
            context_by_id[item["id"]] = item
    binding_started = perf_counter()
    reviewed_valid = False
    assessment_diagnostics = []
    if reviewed_fact_view is not None:
        # The legacy module has eager compatibility constants: import it only
        # for the privileged path, keeping ordinary resolution source-local.
        from src.citation_checker import validate_fact_bindings
        validation = validate_fact_bindings(claims, reviewed_fact_view)
        reviewed_valid = (validation["validated"] and bool(required_ids)
                          and all(isinstance(value, str) and value for value in required_ids)
                          and len(required_ids) == len(set(required_ids))
                          and observed_ids == required_ids
                          and len(observed_ids) == len(set(observed_ids)))
        if not reviewed_valid:
            assessment_diagnostics.append("claim_fact_binding_mismatch")
    timings["binding_checks"] += (perf_counter() - binding_started) * 1000
    links = []
    reference_manifest = _ReferenceManifest(manifest, timings)
    for index, claim in enumerate(claim_records):
        parse_started = perf_counter()
        lookup_before_parse = timings["manifest_lookup"]
        text = str(claim.get("claim", "") or "")
        hierarchy = qualify_reference_hierarchy(text, extract_reference_records(text, manifest=reference_manifest),
                                                manifest=reference_manifest)
        mentions, hierarchy_diagnostics = hierarchy["mentions"], hierarchy["diagnostics"]
        # Reviewed composer keeps citation strings separate from fact text.
        # Inline mentions take priority so a panel cannot become its parent.
        if not mentions:
            for anchor_index, anchor in enumerate(_records(claim.get("anchors"))):
                if isinstance(anchor, str):
                    hierarchy = qualify_reference_hierarchy(anchor, extract_reference_records(anchor, manifest=reference_manifest),
                                                            manifest=reference_manifest)
                    hierarchy_diagnostics.extend(hierarchy["diagnostics"])
                    for mention in hierarchy["mentions"]:
                        mention["origin"] = "claim_anchor"
                        mention["anchor_index"] = anchor_index
                        mention["order"] = len(mentions)
                        mentions.append(mention)
        timings["reference_parse"] += max(0.0, (perf_counter() - parse_started) * 1000
                                            - (timings["manifest_lookup"] - lookup_before_parse))
        reference_status = _reference_status(mentions)
        fact = facts[index] if reviewed_valid else None
        evidence, diagnostics = _ordered_evidence(manifest, mentions, timings, fact)
        direct = [item for item in evidence if item["relationship"] == "direct"]
        asset_status = _required_asset_status(evidence)
        binding_started = perf_counter()
        binding_status, binding_diagnostics = _binding_status(claim, direct, context_by_id, duplicate_ids, fact)
        diagnostics.extend(binding_diagnostics)
        diagnostics.extend(hierarchy_diagnostics)
        if "parent_qualifier_mismatch" in hierarchy_diagnostics:
            binding_status = "mismatched"
        reference_eligible = reference_status == "exact" or (fact is not None and reference_status == "page_only")
        if direct and not reference_eligible and binding_status == "matched":
            binding_status = "incomplete"
            diagnostics.append("unresolved_required_reference")
        if not _page_qualifiers_match(mentions, direct, fact):
            binding_status = "mismatched"
            diagnostics.append("page_qualifier_mismatch")
        if reviewed_fact_view is not None and not reviewed_valid:
            binding_status = "mismatched"
            diagnostics.append("claim_fact_binding_mismatch")
        if reviewed_valid:
            supported = (reference_eligible and binding_status == "matched"
                         and asset_status in {"complete", "source_only"})
            support_status = SUPPORTED if supported else INSUFFICIENT
            if asset_status not in {"complete", "source_only"}:
                diagnostics.append("required_asset_" + asset_status)
        elif reviewed_fact_view is not None or binding_status in {"mismatched", "incomplete"}:
            support_status = INSUFFICIENT
        else:
            support_status = UNASSESSED
        expected_fact = facts[index] if reviewed_fact_view is not None and index < len(facts) else None
        binding_evidence = _binding_evidence(claim, context_by_id, duplicate_ids, expected_fact)
        timings["binding_checks"] += (perf_counter() - binding_started) * 1000
        links.append({"claim_id": claim.get("claim_id") or f"claim:{index + 1}", "claim": text,
                      "fact_ids": deepcopy(list(_records(claim.get("fact_ids")))),
                      "selected_evidence_ids": deepcopy(list(_records(claim.get("selected_evidence_ids")))),
                      "binding_evidence": binding_evidence,
                      "mentions": deepcopy(mentions), "reference_status": reference_status,
                      "binding_status": binding_status, "asset_status": asset_status,
                      "support_status": support_status, "ordered_evidence": evidence,
                      "diagnostics": _unique(diagnostics)})
    complete = bool(links) and reviewed_valid and all(link["support_status"] == SUPPORTED for link in links)
    if complete:
        status = SUPPORTED
    elif not links:
        status = INSUFFICIENT if reviewed_fact_view is not None and required_ids else UNASSESSED
        assessment_diagnostics.append("no_claims_extracted" if valid_claims else "invalid_claims")
        if required_ids:
            assessment_diagnostics.append("missing_required_claims")
    elif reviewed_fact_view is not None or any(link["support_status"] == INSUFFICIENT for link in links):
        status = INSUFFICIENT
    else:
        status = UNASSESSED
    assessment_diagnostics.extend(code for link in links for code in link["diagnostics"])
    timings["total"] = (perf_counter() - started) * 1000
    return {"links": links,
            "assessment": {"status": status, "required_fact_ids": required_ids,
                           "observed_fact_ids": observed_ids, "complete": complete,
                           "diagnostics": _unique(assessment_diagnostics)},
            "timings_ms": timings}
