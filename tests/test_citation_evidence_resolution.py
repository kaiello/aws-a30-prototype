"""Synthetic claim/source identities, with no registry, source PDF or models."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src import standard_manifest
from src.standard_manifest import StandardManifest
from src.evidence_resolution import qualify_reference_hierarchy, resolve_claim_evidence


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class FakeManifest(StandardManifest):
    """Use the real manifest lookup/asset validator over synthetic local bytes."""

    def __init__(self, root):
        proof = {"state": "verified"}
        pages = [{"pdf_index": index, "printed_label": str(index + 10)} for index in range(8)]

        def asset(path, orders, *, candidate=False):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("synthetic asset " + path, encoding="utf-8")
            return {"relpath": path, "source_anchor_orders": orders,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "verification": {"state": "candidate" if candidate else "verified"}}

        def element(label, namespace, indices, assets=(), *, verified=True):
            return {"id": namespace + ":" + label.lower().replace(" ", "_"),
                    "label": label, "title": "Synthetic fixture", "parent_id": "clause:clause_4",
                    "anchors": [{"pdf_index": page, "printed_label": str(page + 10),
                                 "order": order, "role": "start" if order == 0 else "continuation",
                                 "verification": proof if verified else {"state": "candidate"}}
                                for order, page in enumerate(indices)],
                    "assets": list(assets)}

        shared = asset("parsed/figures/shared.png", [0, 1])
        continuation = asset("parsed/figures/continuation.png", [2])
        candidate_text = asset("parsed/tables/synthetic.md", [0, 1], candidate=True)
        table_image = asset("parsed/tables/synthetic.png", [0, 1])
        data = {
            "document": {"id": "doc:synthetic", "sha256": "a" * 64, "pages": pages},
            "sections": [{"id": "clause:clause_4", "label": "Clause 4", "title": "Synthetic source",
                          "spans": [{"start_pdf_index": 2, "end_pdf_index": 4}],
                          "normative_status": "conflicting", "verification": proof},
                         {"id": "clause:clause_5", "label": "Clause 5", "title": "Shared page source",
                          "spans": [{"start_pdf_index": 2, "end_pdf_index": 2}],
                          "normative_status": "normative", "verification": proof}],
            "figures": [element("Figure X1", "figure", [2, 3, 4], [continuation, shared]),
                        element("Figure X2", "figure", [2, 3], [shared]),
                        element("Figure X9A", "figure", [2], []),
                        element("Figure X9B", "figure", [3], [])],
            "tables": [element("Table Q1", "table", [2], []),
                       element("Table Q2", "table", [2, 3], [candidate_text, table_image]),
                       element("Table Q3", "table", [2], [], verified=False)],
            "links": [{"from_id": "table:table_q1", "to_id": "figure:figure_x1",
                       "kind": "ui_companion", "verification": {"state": "candidate"}}],
            "legacy_aliases": [{"legacy_value": "Figure X9", "namespace": "display",
                                "target_ids": ["figure:figure_x9a", "figure:figure_x9b"], "resolution": "group"}],
        }
        super().__init__(data, root)


@pytest.fixture
def manifest(tmp_path, monkeypatch):
    value = FakeManifest(tmp_path)
    # The existing validator's compatibility constants must never load the source PDF.
    monkeypatch.setattr(standard_manifest, "get_manifest", lambda: value)
    return value


def claim(text="A synthetic visual assertion cites Figure X1.", *, claim_id="claim:visual", selected=None):
    value = {"claim_id": claim_id, "claim": text}
    if selected is not None:
        value["selected_evidence_ids"] = list(selected)
    return value


def context(manifest, label="Figure X1", *, evidence_id="context:one"):
    return {"id": evidence_id, "content": "Unreviewed synthetic content.",
            "source_anchors": manifest.source_anchors(label)}


def reviewed(manifest, labels=("Clause 4",)):
    facts = []
    for index, label in enumerate(labels):
        source = manifest.source_anchors(label)[0]
        native = {"document_id": source["source_id"], "source_sha256": source["source_sha256"],
                  "section_id": source["element_id"], "section_label": label,
                  "pdf_index": source["pdf_index"], "printed_label": source["printed_label"],
                  "verification_state": "verified"}
        text = f"Synthetic fact {index} preserves its explicit qualification."
        binding = {"evidence_id": f"context:reviewed:{index}", "full_doc_id": "parent:synthetic",
                   "excerpt_sha256": digest(text), "content_sha256": digest("synthetic contextual row"),
                   "raw_content_span": [100, 100 + len(text)], "span_space": "synthetic Unicode offsets",
                   "source_entry_refs": [f"entry:{index}"], "source_entry_ref": f"entry:{index}",
                   "excerpt_span": [0, len(text)], "fact_raw_content_span": [100, 100 + len(text)],
                   "source_text": text, "source_anchor": native, "verification_state": "verified"}
        facts.append({"fact_id": f"fact:{index}", "text": text,
                      "anchors": [f"{label}, p. {source['printed_label']}"],
                      "source_anchors": [native], "source_bindings": [binding]})
    view = {"status": "SUPPORTED_REVIEWED_FACTS", "facts": facts, "diagnostics": []}
    claims = [{"claim_id": "claim:" + fact["fact_id"].removeprefix("fact:"), "claim": fact["text"],
               "fact_ids": [fact["fact_id"]], "anchors": deepcopy(fact["anchors"]),
               "source_anchors": deepcopy(fact["source_anchors"]),
               "source_bindings": deepcopy(fact["source_bindings"])} for fact in facts]
    return claims, view


def resolve(manifest, claims, evidence=(), view=None):
    return resolve_claim_evidence(claims, evidence, reviewed_fact_view=view, manifest=manifest)


def test_exact_selected_source_is_bound_but_visual_meaning_remains_unassessed(manifest):
    result = resolve(manifest, [claim(selected=["context:one"])], [context(manifest)])
    link = result["links"][0]
    assert (link["reference_status"], link["binding_status"], link["asset_status"], link["support_status"]) == (
        "exact", "matched", "complete", "UNASSESSED")
    assert result["assessment"]["status"] == "UNASSESSED"
    assert result["assessment"]["complete"] is False
    assert link["ordered_evidence"][0]["source_anchors"][0]["normative_status"] == "conflicting"


def test_no_explicit_context_selection_does_not_union_matching_sources(manifest):
    result = resolve(manifest, [claim()], [context(manifest)])
    assert result["links"][0]["binding_status"] == "unavailable"
    assert result["links"][0]["support_status"] == "UNASSESSED"


def test_selected_wrong_valid_element_is_insufficient_even_on_shared_pages_and_asset(manifest):
    result = resolve(manifest, [claim(selected=["context:wrong"])],
                     [context(manifest), context(manifest, "Figure X2", evidence_id="context:wrong")])
    link = result["links"][0]
    assert link["reference_status"] == "exact"
    assert link["binding_status"] == "mismatched"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert "selected_evidence_mismatch" in link["diagnostics"]


@pytest.mark.parametrize("field,value", [("source_id", "doc:wrong"), ("source_sha256", "b" * 64),
                                        ("element_id", "figure:figure_x2")])
def test_selected_context_requires_exact_explicit_source_identity(manifest, field, value):
    selected = context(manifest)
    for anchor in selected["source_anchors"]:
        anchor[field] = value
    result = resolve(manifest, [claim(selected=["context:one"])], [selected])
    assert result["links"][0]["binding_status"] == "mismatched"
    assert result["links"][0]["support_status"] == "INSUFFICIENT_EVIDENCE"


def test_context_page_or_filename_without_source_anchors_cannot_bind(manifest):
    selected = {"id": "context:one", "page": "12", "file_path": "parsed/figures/shared.png",
                "element_id": "figure:figure_x1", "source_id": "doc:synthetic", "source_sha256": "a" * 64}
    result = resolve(manifest, [claim(selected=["context:one"])], [selected])
    assert result["links"][0]["binding_status"] == "unavailable"
    assert result["links"][0]["support_status"] == "UNASSESSED"


@pytest.mark.parametrize("mutation", ["wrong_page", "wrong_printed_label", "malformed_member"])
def test_selected_anchor_coordinates_and_every_explicit_member_must_be_valid(manifest, mutation):
    selected = context(manifest)
    if mutation == "wrong_page":
        selected["source_anchors"][0]["pdf_index"] = 7
    elif mutation == "wrong_printed_label":
        selected["source_anchors"][0]["printed_label"] = "999"
    else:
        selected["source_anchors"].append({"pdf_index": 2, "printed_label": "12"})
    link = resolve(manifest, [claim(selected=[selected["id"]])], [selected])["links"][0]
    assert link["binding_status"] == "mismatched"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"


def test_ordinary_selected_source_anchor_subset_is_incomplete(manifest):
    selected = context(manifest)
    selected["source_anchors"] = selected["source_anchors"][:1]
    link = resolve(manifest, [claim(selected=[selected["id"]])], [selected])["links"][0]
    assert link["binding_status"] == "incomplete"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize("extra_anchors", [None, {}, []])
def test_an_explicitly_selected_item_without_anchors_cannot_disappear(manifest, extra_anchors):
    extra = {"id": "context:extra", "source_anchors": extra_anchors}
    item = claim(selected=["context:one", "context:extra"])
    link = resolve(manifest, [item], [context(manifest), extra])["links"][0]
    assert link["binding_status"] in {"incomplete", "mismatched"}
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert "selected_source_anchors_unavailable" in link["diagnostics"]


def test_incompatible_inline_page_qualifier_cannot_match_the_right_element(manifest):
    item = claim("A synthetic assertion cites Figure X1, p. 17.", selected=["context:one"])
    link = resolve(manifest, [item], [context(manifest)])["links"][0]
    assert link["reference_status"] == "exact"
    assert link["binding_status"] == "mismatched"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert "page_qualifier_mismatch" in link["diagnostics"]


def test_reviewed_page_qualifier_must_match_the_exact_entry_not_another_section_page(manifest):
    claims, view = reviewed(manifest)
    claims[0]["anchors"] = ["Clause 4, p. 13"]
    view["facts"][0]["anchors"] = deepcopy(claims[0]["anchors"])
    result = resolve(manifest, claims, view=view)
    assert result["links"][0]["binding_status"] == "mismatched"
    assert result["assessment"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert "page_qualifier_mismatch" in result["links"][0]["diagnostics"]


def test_privileged_page_only_mention_uses_exact_native_element_identity(manifest):
    claims, view = reviewed(manifest)
    claims[0]["anchors"] = ["p. 12"]
    view["facts"][0]["anchors"] = deepcopy(claims[0]["anchors"])
    result = resolve(manifest, claims, view=view)
    link = result["links"][0]
    assert link["mentions"][0]["resolution"]["status"] == "page_only"
    assert link["reference_status"] == "page_only"
    assert link["ordered_evidence"][0]["element_id"] == "clause:clause_4"
    assert link["ordered_evidence"][0]["relationship"] == "direct"
    assert link["binding_status"] == "matched"
    assert link["support_status"] == "SUPPORTED_REVIEWED_FACTS"
    assert result["assessment"]["complete"] is True


@pytest.mark.parametrize("evidence,selected,code", [
    ([], ["context:missing"], "selected_evidence_missing"),
    (["duplicate", "duplicate"], ["context:one"], "duplicate_evidence_id"),
])
def test_invalid_context_selection_cannot_match(manifest, evidence, selected, code):
    records = [context(manifest) for _ in evidence]
    link = resolve(manifest, [claim(selected=selected)], records)["links"][0]
    assert link["binding_status"] in {"mismatched", "unavailable"}
    assert code in link["diagnostics"]
    assert link["support_status"] != "SUPPORTED_REVIEWED_FACTS"


def test_per_claim_swapped_selection_is_not_masked_by_the_context_union(manifest):
    claims = [claim(selected=["context:two"]),
              claim("Another assertion cites Figure X2.", claim_id="claim:second", selected=["context:one"])]
    links = resolve(manifest, claims, [context(manifest), context(manifest, "Figure X2", evidence_id="context:two")])["links"]
    assert [link["binding_status"] for link in links] == ["mismatched", "mismatched"]
    assert [link["claim_id"] for link in links] == ["claim:visual", "claim:second"]


def test_manifest_assets_keep_explicit_many_anchor_bindings_and_existing_order(manifest):
    link = resolve(manifest, [claim()])["links"][0]
    evidence = link["ordered_evidence"][0]
    assert evidence["element_id"] == "figure:figure_x1"
    assert evidence["relationship"] == "direct"
    assert [Path(asset["path"]).name for asset in evidence["assets"]] == ["shared.png", "continuation.png"]
    assert [asset["source_anchor_orders"] for asset in evidence["assets"]] == [[0, 1], [2]]
    assert [asset["relpath"] for asset in evidence["declared_assets"]] == [
        "parsed/figures/continuation.png", "parsed/figures/shared.png"]
    assert [asset["source_anchor_orders"] for asset in evidence["declared_assets"]] == [[2], [0, 1]]
    assert all(set(asset) == {"path", "relpath", "sha256", "source_anchor_orders", "kind", "verification_state"}
               for asset in evidence["declared_assets"])
    assert len(evidence["source_anchors"]) == 3
    assert all(asset["sha256"] and asset["kind"] == "image" for asset in evidence["assets"])


def test_table_assets_include_candidate_markdown_without_semantic_promotion(manifest):
    link = resolve(manifest, [claim("A synthetic table assertion cites Table Q2.")])["links"][0]
    assert link["asset_status"] == "complete"
    assert [item["kind"] for item in link["ordered_evidence"][0]["assets"]] == ["text", "image"]
    assert link["ordered_evidence"][0]["assets"][0]["verification_state"] == "candidate"
    assert link["support_status"] == "UNASSESSED"


@pytest.mark.parametrize("mutation,expected", [("missing", "missing"), ("corrupt", "corrupt")])
def test_required_continuation_failure_is_explicit_without_mutating_manifest(manifest, mutation, expected):
    target = manifest.root / "parsed/figures/continuation.png"
    if mutation == "missing":
        target.unlink()
    else:
        target.write_text("corrupt synthetic bytes", encoding="utf-8")
    original = deepcopy(manifest._data)
    result = resolve(manifest, [claim()])
    assert result["links"][0]["asset_status"] == expected
    assert [Path(asset["path"]).name for asset in result["links"][0]["ordered_evidence"][0]["assets"]] == ["shared.png"]
    assert len(result["links"][0]["ordered_evidence"][0]["declared_assets"]) == 2
    assert result["assessment"]["complete"] is False
    assert manifest._data == original


def test_source_only_table_is_retained_and_optional_missing_companion_does_not_poison_it(manifest):
    (manifest.root / "parsed/figures/continuation.png").unlink()
    link = resolve(manifest, [claim("A synthetic source-only assertion cites Table Q1.")])["links"][0]
    assert link["asset_status"] == "source_only"
    assert link["ordered_evidence"][0]["element_id"] == "table:table_q1"
    assert link["ordered_evidence"][0]["assets"] == []
    companion = next(item for item in link["ordered_evidence"] if item["element_id"] == "figure:figure_x1")
    assert companion["relationship"] == "navigation_candidate"
    assert companion["asset_status"] == "missing"


def test_shared_file_does_not_collapse_distinct_cited_elements_or_claims(manifest):
    links = resolve(manifest, [claim("A paired assertion cites Figure X2 and Figure X1."),
                               claim(claim_id="claim:again")])["links"]
    assert [item["element_id"] for item in links[0]["ordered_evidence"]] == ["figure:figure_x2", "figure:figure_x1"]
    assert [link["claim_id"] for link in links] == ["claim:visual", "claim:again"]
    assert links[0]["ordered_evidence"][0]["assets"][0]["path"] == links[0]["ordered_evidence"][1]["assets"][0]["path"]


@pytest.mark.parametrize("text,status", [("Figure X1(A)", "unsupported_qualifier"),
                                        ("Figure X9", "group"), ("Table Q3", "unverified"),
                                        ("Figure X120", "unknown"), ("p. 12", "page_only"),
                                        ("No citation here.", "not_cited")])
def test_unresolved_and_navigation_only_requests_never_become_exact_support(manifest, text, status):
    link = resolve(manifest, [claim("Synthetic assertion: " + text)])["links"][0]
    assert link["reference_status"] == status
    assert link["binding_status"] == "unavailable"
    assert link["support_status"] == "UNASSESSED"
    if status in {"unsupported_qualifier", "group"}:
        assert link["asset_status"] == "unavailable"
        assert link["ordered_evidence"]
        assert all(item["relationship"] == "navigation_candidate" for item in link["ordered_evidence"])


def test_full_inline_panel_mention_survives_even_if_claim_has_parent_anchor(manifest):
    item = claim("Synthetic panel meaning cites Figure X1(A), p. 12.")
    item["anchors"] = ["Figure X1"]
    link = resolve(manifest, [item])["links"][0]
    assert link["reference_status"] == "unsupported_qualifier"
    assert any("X1(A)" in mention["raw"] and mention["qualifiers"]["panel"] == "(A)" for mention in link["mentions"])
    assert not any(item["relationship"] == "direct" for item in link["ordered_evidence"])


def test_complete_privileged_fact_set_preserves_supported_text_status(manifest):
    claims, view = reviewed(manifest, ("Clause 4", "Clause 5"))
    original = deepcopy((claims, view))
    result = resolve(manifest, claims, view=view)
    assert result["assessment"] == {
        "status": "SUPPORTED_REVIEWED_FACTS", "required_fact_ids": ["fact:0", "fact:1"],
        "observed_fact_ids": ["fact:0", "fact:1"], "complete": True, "diagnostics": []}
    assert [link["support_status"] for link in result["links"]] == ["SUPPORTED_REVIEWED_FACTS"] * 2
    assert [link["binding_status"] for link in result["links"]] == ["matched"] * 2
    assert [link["reference_status"] for link in result["links"]] == ["exact"] * 2
    assert (claims, view) == original


@pytest.mark.parametrize("mutation", ["omitted", "duplicate", "extra", "reordered", "entry", "span", "hash", "qualifier", "citation"])
def test_privileged_support_requires_the_exact_complete_ordered_claim_fact_set(manifest, mutation):
    claims, view = reviewed(manifest, ("Clause 4", "Clause 5"))
    if mutation == "omitted":
        claims.pop()
    elif mutation == "duplicate":
        claims[1] = deepcopy(claims[0])
    elif mutation == "extra":
        claims.append(claim("An extra asserted fact cites Clause 4.", claim_id="claim:extra"))
    elif mutation == "reordered":
        claims.reverse()
    elif mutation == "entry":
        claims[0]["source_bindings"][0]["source_entry_ref"] = "entry:wrong"
    elif mutation == "span":
        claims[0]["source_bindings"][0]["excerpt_span"][0] += 1
    elif mutation == "hash":
        claims[0]["source_anchors"][0]["source_sha256"] = "b" * 64
    elif mutation == "qualifier":
        claims[0]["claim"] = "Synthetic fact 0 applies universally."
    else:
        claims[0]["anchors"] = ["Clause 5, p. 12"]
    result = resolve(manifest, claims, view=view)
    assert result["assessment"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment"]["complete"] is False
    assert not any(link["support_status"] == "SUPPORTED_REVIEWED_FACTS" for link in result["links"])
    assert "claim_fact_binding_mismatch" in result["assessment"]["diagnostics"]


def test_claim_or_context_review_flags_cannot_create_privileged_fact_authority(manifest):
    claims, view = reviewed(manifest)
    claims[0].update(reviewed=True, status="SUPPORTED_REVIEWED_FACTS", reviewed_fact_view=view)
    selected = context(manifest, "Clause 4")
    selected.update(reviewed=True, status="SUPPORTED_REVIEWED_FACTS", facts=view["facts"])
    claims[0]["selected_evidence_ids"] = [selected["id"]]
    result = resolve(manifest, claims, [selected])
    assert result["assessment"]["status"] == "UNASSESSED"
    assert result["links"][0]["support_status"] == "UNASSESSED"


@pytest.mark.parametrize('flags',[{'relationship':'navigation_candidate'},
                                  {'relationship':'ui_companion'},
                                  {'selection_role':'ui_companion'}])
def test_navigation_only_selected_context_cannot_match_a_direct_reference(manifest,flags):
    selected=context(manifest);selected.update(flags)
    result=resolve(manifest,[claim(selected=[selected['id']])],[selected])
    link=result['links'][0]
    assert link['reference_status']=='exact'
    assert link['binding_status']=='unavailable'
    assert link['support_status']=='UNASSESSED'
    assert link['asset_status']=='complete'
    assert 'navigation_only_selected_evidence' in link['diagnostics']
    # A literal citation remains a citation; the chosen context retains its role.
    assert link['ordered_evidence'][0]['relationship']=='direct'
    for key,value in flags.items():assert link['binding_evidence'][0][key]==value


def test_selected_navigation_cannot_complete_a_privileged_fact_binding(manifest):
    claims,view=reviewed(manifest)
    fact=view['facts'][0];selected={'id':fact['source_bindings'][0]['evidence_id'],
        'source_anchors':deepcopy(fact['source_anchors']),'source_bindings':deepcopy(fact['source_bindings']),
        'relationship':'navigation_candidate','selection_role':'ui_companion'}
    claims[0]['selected_evidence_ids']=[selected['id']]
    result=resolve(manifest,claims,[selected],view)
    assert result['links'][0]['binding_status']=='incomplete'
    assert result['links'][0]['support_status']=='INSUFFICIENT_EVIDENCE'
    assert result['assessment']['complete'] is False


def test_a_navigation_item_cannot_disappear_from_a_mixed_selected_set(manifest):
    eligible=context(manifest,evidence_id='context:eligible')
    candidate=context(manifest,'Figure X2',evidence_id='context:companion')
    candidate['selection_role']='ui_companion'
    request=claim('Synthetic citation Figure X1 and Figure X2.',selected=[eligible['id'],candidate['id']])
    result=resolve(manifest,[request],[eligible,candidate])
    assert result['links'][0]['binding_status']=='incomplete'
    assert result['links'][0]['support_status']=='INSUFFICIENT_EVIDENCE'
    assert len(result['links'][0]['binding_evidence'])==2


@pytest.mark.parametrize("mutation", [None, "entry", "span", "excerpt_sha256", "content_sha256"])
def test_selected_reviewed_chunk_requires_its_exact_native_entry_binding(manifest, mutation):
    claims, view = reviewed(manifest)
    binding = deepcopy(view["facts"][0]["source_bindings"][0])
    selected = {"id": binding["evidence_id"], "source_anchors": deepcopy(claims[0]["source_anchors"]),
                "source_bindings": [binding]}
    claims[0]["selected_evidence_ids"] = [selected["id"]]
    if mutation == "entry":
        binding["source_entry_ref"] = "entry:different-on-the-same-page"
    elif mutation == "span":
        binding["excerpt_span"][0] += 1
    elif mutation:
        binding[mutation] = "b" * 64
    result = resolve(manifest, claims, [selected], view=view)
    if mutation is None:
        assert result["links"][0]["binding_status"] == "matched"
        assert result["assessment"]["status"] == "SUPPORTED_REVIEWED_FACTS"
    else:
        assert result["links"][0]["binding_status"] == "mismatched"
        assert result["assessment"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert "selected_evidence_mismatch" in result["links"][0]["diagnostics"]


def test_links_retain_selected_and_expected_native_binding_proof_without_source_text(manifest):
    claims, view = reviewed(manifest)
    native = deepcopy(view["facts"][0]["source_bindings"][0])
    selected = {"id": native["evidence_id"], "source_anchors": deepcopy(claims[0]["source_anchors"]),
                "source_bindings": [native]}
    claims[0]["selected_evidence_ids"] = [selected["id"]]
    link = resolve(manifest, claims, [selected], view=view)["links"][0]
    assert link["fact_ids"] == ["fact:0"]
    assert link["selected_evidence_ids"] == [selected["id"]]
    chosen = next(record for record in link["binding_evidence"] if record["role"] == "selected_context")
    expected = next(record for record in link["binding_evidence"] if record["role"] == "expected_reviewed")
    assert chosen["evidence_id"] == selected["id"]
    assert chosen["selection_status"] == "selected"
    assert chosen["source_anchors"] == selected["source_anchors"]
    assert expected["fact_id"] == "fact:0"
    expected_digest = digest(json.dumps(native, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    for record in [chosen, expected]:
        projection = record["source_bindings"][0]
        assert "source_text" not in projection
        assert projection["binding_sha256"] == expected_digest
        for key in ("evidence_id", "full_doc_id", "source_entry_ref", "source_entry_refs", "excerpt_span",
                    "raw_content_span", "fact_raw_content_span", "span_space", "excerpt_sha256", "content_sha256", "source_anchor"):
            assert projection[key] == native[key]


@pytest.mark.parametrize("duplicate", [False, True])
def test_unavailable_selected_identity_is_retained_without_choosing_ambiguous_context(manifest, duplicate):
    evidence = [context(manifest), context(manifest)] if duplicate else []
    link = resolve(manifest, [claim(selected=["context:one"])], evidence)["links"][0]
    proof = link["binding_evidence"][0]
    assert proof["role"] == "selected_context"
    assert proof["evidence_id"] == "context:one"
    assert proof["selection_status"] == ("duplicate" if duplicate else "missing")
    assert proof["source_anchors"] == []
    assert proof["source_bindings"] == []


def test_no_extracted_claims_is_explicitly_unassessed_not_vacuously_complete(manifest):
    result = resolve(manifest, [])
    assert result["links"] == []
    assert result["assessment"]["status"] == "UNASSESSED"
    assert result["assessment"]["complete"] is False
    assert "no_claims_extracted" in result["assessment"]["diagnostics"]


def test_missing_all_privileged_required_claims_is_explicitly_insufficient(manifest):
    _, view = reviewed(manifest)
    result = resolve(manifest, [], view=view)
    assert result["links"] == []
    assert result["assessment"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment"]["required_fact_ids"] == ["fact:0"]
    assert result["assessment"]["observed_fact_ids"] == []
    assert result["assessment"]["complete"] is False
    assert "missing_required_claims" in result["assessment"]["diagnostics"]


def test_resolver_reports_separate_nonnegative_stage_timings(manifest):
    timings = resolve(manifest, [claim()])["timings_ms"]
    assert set(timings) == {"reference_parse", "manifest_lookup", "asset_validation", "binding_checks", "total"}
    assert all(isinstance(value, (int, float)) and value >= 0 for value in timings.values())


def test_multiple_direct_elements_require_a_selected_binding_for_each_member(manifest):
    item = claim("A paired assertion cites Figure X1 and Figure X2.", selected=["context:one"])
    link = resolve(manifest, [item], [context(manifest)])["links"][0]
    assert link["binding_status"] == "incomplete"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"


def test_missing_required_declared_asset_prevents_privileged_complete_support(manifest):
    claims, view = reviewed(manifest, ("Figure X1",))
    (manifest.root / "parsed/figures/continuation.png").unlink()
    result = resolve(manifest, claims, view=view)
    assert result["links"][0]["asset_status"] == "missing"
    assert result["links"][0]["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment"]["complete"] is False


@pytest.fixture
def hierarchy_manifest(manifest):
    data = deepcopy(manifest._data)
    for suffix in ("X", "Y"):
        data["sections"].append({"id": "clause:annex_" + suffix.lower(), "label": "Annex " + suffix,
                                 "title": "Synthetic parent", "spans": [{"start_pdf_index": 2, "end_pdf_index": 4}],
                                 "normative_status": "informative", "verification": {"state": "verified"}})
    for figure in data["figures"]:
        figure["parent_id"] = "clause:annex_x"
    return StandardManifest(data, manifest.root)


@pytest.mark.parametrize("citation", ["[Annex X, Figure X1]", "Annex X, Figure X1"])
def test_attached_parent_is_a_location_qualifier_not_an_extra_required_source(hierarchy_manifest, citation):
    selected = context(hierarchy_manifest)
    item = claim("A synthetic statement cites " + citation + ".", selected=[selected["id"]])
    link = resolve(hierarchy_manifest, [item], [selected])["links"][0]
    assert link["reference_status"] == "exact"
    assert link["binding_status"] == "matched"
    assert link["support_status"] == "UNASSESSED"
    assert [entry["element_id"] for entry in link["ordered_evidence"] if entry["relationship"] == "direct"] == ["figure:figure_x1"]
    original = standard_manifest.extract_reference_records(item["claim"], manifest=hierarchy_manifest)
    for observed, expected in zip(link["mentions"], original):
        assert {key: observed[key] for key in expected} == expected
    assert len(link["mentions"]) == len(original) == 2
    assert link["mentions"][0]["reference_role"] == "location_qualifier"
    assert link["mentions"][0]["qualifies_target_ids"] == ["figure:figure_x1"]


@pytest.mark.parametrize("also_select_parent", [False, True])
def test_contradictory_parent_cannot_bind_even_if_all_cited_ids_are_selected(hierarchy_manifest, also_select_parent):
    selected = [context(hierarchy_manifest)]
    if also_select_parent:
        selected.append(context(hierarchy_manifest, "Annex Y", evidence_id="context:parent"))
    item = claim("A synthetic statement cites [Annex Y, Figure X1].", selected=[entry["id"] for entry in selected])
    link = resolve(hierarchy_manifest, [item], selected)["links"][0]
    assert link["binding_status"] == "mismatched"
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert "parent_qualifier_mismatch" in link["diagnostics"]
    assert [mention["requested_label"] for mention in link["mentions"]] == ["Annex Y", "Figure X1"]


@pytest.mark.parametrize("citation", ["[Annex X] and [Figure X1]", "Annex X and Figure X1", "[Annex X; Figure X1]"])
def test_independent_section_and_figure_keep_separate_required_bindings(hierarchy_manifest, citation):
    child = context(hierarchy_manifest)
    parent = context(hierarchy_manifest, "Annex X", evidence_id="context:parent")
    missing_parent = claim(citation, selected=[child["id"]])
    incomplete = resolve(hierarchy_manifest, [missing_parent], [child])["links"][0]
    assert incomplete["binding_status"] == "incomplete"
    assert incomplete["support_status"] == "INSUFFICIENT_EVIDENCE"
    complete = claim(citation, selected=[parent["id"], child["id"]])
    matched = resolve(hierarchy_manifest, [complete], [parent, child])["links"][0]
    assert matched["binding_status"] == "matched"
    assert [entry["element_id"] for entry in matched["ordered_evidence"] if entry["relationship"] == "direct"] == ["clause:annex_x", "figure:figure_x1"]


def test_hierarchical_figures_remain_distinct_despite_a_shared_asset(hierarchy_manifest):
    selected = [context(hierarchy_manifest, "Figure X1"),
                context(hierarchy_manifest, "Figure X2", evidence_id="context:two")]
    item = claim("See [Annex X, Figure X1 and Figure X2].", selected=[entry["id"] for entry in selected])
    link = resolve(hierarchy_manifest, [item], selected)["links"][0]
    assert link["binding_status"] == "matched"
    direct = [entry for entry in link["ordered_evidence"] if entry["relationship"] == "direct"]
    assert [entry["element_id"] for entry in direct] == ["figure:figure_x1", "figure:figure_x2"]
    assert direct[0]["assets"][0]["path"] == direct[1]["assets"][0]["path"]
    item["selected_evidence_ids"] = [selected[0]["id"]]
    assert resolve(hierarchy_manifest, [item], selected)["links"][0]["binding_status"] == "incomplete"


@pytest.mark.parametrize("page,expected", [("12", "matched"), ("17", "mismatched")])
def test_parent_page_qualifier_is_checked_against_its_child_evidence(hierarchy_manifest, page, expected):
    selected = context(hierarchy_manifest)
    item = claim(f"See [Annex X, p. {page}, Figure X1].", selected=[selected["id"]])
    link = resolve(hierarchy_manifest, [item], [selected])["links"][0]
    assert link["binding_status"] == expected
    if expected == "mismatched":
        assert "page_qualifier_mismatch" in link["diagnostics"]


def test_unsupported_panel_cannot_fall_back_to_hierarchical_parent_support(hierarchy_manifest):
    claims, view = reviewed(hierarchy_manifest, ("Figure X1",))
    claims[0]["anchors"] = ["[Annex X, Figure X1(C)]"]
    view["facts"][0]["anchors"] = deepcopy(claims[0]["anchors"])
    link = resolve(hierarchy_manifest, claims, view=view)["links"][0]
    assert link["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert not any(entry["relationship"] == "direct" for entry in link["ordered_evidence"])
    assert link["mentions"][1]["resolution"]["status"] == "unsupported_qualifier"


def test_hierarchical_citation_preserves_exact_reviewed_native_fact_support(hierarchy_manifest):
    claims, view = reviewed(hierarchy_manifest, ("Figure X1",))
    claims[0]["anchors"] = ["[Annex X, Figure X1, p. 12]"]
    view["facts"][0]["anchors"] = deepcopy(claims[0]["anchors"])
    result = resolve(hierarchy_manifest, claims, view=view)
    assert result["links"][0]["binding_status"] == "matched"
    assert result["assessment"]["status"] == "SUPPORTED_REVIEWED_FACTS"
    assert result["assessment"]["complete"] is True


def test_hierarchy_projection_can_check_full_prose_without_claim_extraction(hierarchy_manifest):
    text = "Ordinary generated prose cites [Annex Y, Figure X1]."
    mentions = standard_manifest.extract_reference_records(text, manifest=hierarchy_manifest)
    before = deepcopy(mentions)
    projection = qualify_reference_hierarchy(text, mentions, manifest=hierarchy_manifest)
    assert projection["diagnostics"] == ["parent_qualifier_mismatch"]
    assert projection["mentions"][0]["qualifies_target_ids"] == ["figure:figure_x1"]
    assert mentions == before


def test_one_attached_parent_must_match_every_qualified_figure_and_table(hierarchy_manifest):
    selected = [context(hierarchy_manifest), context(hierarchy_manifest, "Table Q1", evidence_id="context:table")]
    item = claim("See [Annex X, Figure X1 and Table Q1].", selected=[entry["id"] for entry in selected])
    link = resolve(hierarchy_manifest, [item], selected)["links"][0]
    assert link["binding_status"] == "mismatched"
    assert "parent_qualifier_mismatch" in link["diagnostics"]
    assert link["mentions"][0]["qualifies_target_ids"] == ["figure:figure_x1", "table:table_q1"]


def test_unresolved_parent_cannot_gain_reviewed_support_from_an_exact_child(hierarchy_manifest):
    claims, view = reviewed(hierarchy_manifest, ("Figure X1",))
    claims[0]["anchors"] = ["[Annex Z, Figure X1]"]
    view["facts"][0]["anchors"] = deepcopy(claims[0]["anchors"])
    result = resolve(hierarchy_manifest, claims, view=view)
    assert result["links"][0]["support_status"] == "INSUFFICIENT_EVIDENCE"
    assert "parent_qualifier_unresolved" in result["links"][0]["diagnostics"]
    assert result["assessment"]["complete"] is False


@pytest.mark.parametrize("page,diagnostics", [("12", []), ("17", ["page_qualifier_mismatch"]),
                                               ("999", ["page_qualifier_mismatch"])])
def test_full_prose_projection_checks_attached_page_against_canonical_element(manifest, monkeypatch, page, diagnostics):
    text = f"Ordinary generated prose cites Figure X1, p. {page}."
    mentions = standard_manifest.extract_reference_records(text, manifest=manifest)
    before = deepcopy(mentions)
    monkeypatch.setattr(manifest, "validated_assets", lambda *_: pytest.fail("Metadata projection must not read assets"))
    projection = qualify_reference_hierarchy(text, mentions, manifest=manifest)
    assert projection["diagnostics"] == diagnostics
    assert projection["mentions"] == before
    assert mentions == before


@pytest.mark.parametrize("page,diagnostics", [("12", []), ("13", ["page_qualifier_mismatch"])])
def test_full_prose_parent_page_is_checked_against_child_not_whole_section(hierarchy_manifest, page, diagnostics):
    text = f"Ordinary generated prose cites [Annex X, p. {page}, Figure X9A]."
    mentions = standard_manifest.extract_reference_records(text, manifest=hierarchy_manifest)
    projection = qualify_reference_hierarchy(text, mentions, manifest=hierarchy_manifest)
    assert projection["diagnostics"] == diagnostics
    assert projection["mentions"][0]["qualifies_target_ids"] == ["figure:figure_x9a"]


def test_valid_standalone_page_reference_remains_unassessed_without_element_binding(manifest):
    text = "Ordinary generated prose cites p. 17."
    mentions = standard_manifest.extract_reference_records(text, manifest=manifest)
    projection = qualify_reference_hierarchy(text, mentions, manifest=manifest)
    assert projection["diagnostics"] == []
    assert projection["mentions"] == mentions
    result = resolve(manifest, [claim(text)])
    assert result["links"][0]["reference_status"] == "page_only"
    assert result["links"][0]["support_status"] == "UNASSESSED"


def test_through_range_retains_all_evidence_through_compound_asset_faults(manifest):
    data = deepcopy(manifest._data)
    first, second = data["figures"][:2]
    tail = deepcopy(first["anchors"][-1])
    tail.update(pdf_index=5, printed_label="15", order=3)
    first["anchors"].append(tail)
    missing = deepcopy(first["assets"][0])
    missing.update(relpath="parsed/figures/absent.png", source_anchor_orders=[3])
    corrupt = deepcopy(first["assets"][0])
    corrupt.update(relpath="parsed/figures/changed.png", source_anchor_orders=[1])
    (manifest.root / corrupt["relpath"]).write_bytes(b"changed synthetic bytes")
    shared = deepcopy(first["assets"][1])
    shared["source_anchor_orders"] = [0, 2]
    first["assets"] = [missing, corrupt, shared]
    second["anchors"] = [dict(deepcopy(first["anchors"][2]), order=0, role="start")]
    second["assets"] = [dict(deepcopy(shared), source_anchor_orders=[0])]
    third = deepcopy(second)
    third.update(id="figure:figure_x3", label="Figure X3")
    third["anchors"] = [dict(deepcopy(tail), order=0, role="start")]
    data["figures"].insert(2, third)
    data["sections"][0]["spans"][0]["end_pdf_index"] = 5
    ranged = StandardManifest(data, manifest.root)
    original = deepcopy(ranged._data)
    labels = ["Figure X1", "Figure X2", "Figure X3"]
    selected = {"id": "context:range", "relationship": "direct",
                "source_anchors": [anchor for label in labels for anchor in ranged.source_anchors(label)]}
    result = resolve(ranged, [claim("Figures X1 through X3 retain their source identities.",
                                    selected=[selected["id"]])], [selected])
    link = result["links"][0]
    assert (link["reference_status"], link["binding_status"], link["asset_status"], link["support_status"]) == (
        "exact", "matched", "corrupt", "UNASSESSED")
    assert link["mentions"][0]["raw"] == "Figures X1 through X3"
    evidence = link["ordered_evidence"]
    assert [item["element_id"] for item in evidence] == ["figure:figure_x1", "figure:figure_x2", "figure:figure_x3"]
    assert [item["relationship"] for item in evidence] == ["direct"] * 3
    assert [item["source_anchors"] for item in evidence] == [ranged.source_anchors(label) for label in labels]
    assert [item["asset_status"] for item in evidence] == ["corrupt", "complete", "complete"]
    assert [item["relpath"] for item in evidence[0]["declared_assets"]] == [
        "parsed/figures/absent.png", "parsed/figures/changed.png", "parsed/figures/shared.png"]
    assert [item["source_anchor_orders"] for item in evidence[0]["declared_assets"]] == [[3], [1], [0, 2]]
    assert [[Path(asset["path"]).name for asset in item["assets"]] for item in evidence] == [["shared.png"]] * 3
    assert [asset["source_anchor_orders"] for asset in evidence[0]["assets"]] == [[0, 2]]
    assert [asset["source_anchor_orders"] for asset in evidence[1]["assets"]] == [[0]]
    assert {"MANIFEST_ASSET_MISSING", "MANIFEST_ASSET_MISMATCH"} <= set(link["diagnostics"])
    assert result["assessment"]["status"] == "UNASSESSED"
    assert result["assessment"]["complete"] is False
    assert ranged._data == original
