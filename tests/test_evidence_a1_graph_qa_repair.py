"""Generic A1 planner/traversal regressions; no owner questions or AWS labels."""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Synthetic planning/traversal tests must not call models or network")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def graph():
    def node(identifier, kind, label, code=None, y=0.1):
        result = {"id": identifier, "kind": kind, "label": label,
                  "region": [y, 0.1, y + 0.04, 0.4]}
        if code is not None:
            result["code"] = code
        return result
    def edge(source, target, kind):
        return {"from": source, "to": target, "type": kind, "region": [0.1, 0.1, 0.7, 0.8]}
    return {"schema_version": "a1-geometry-1.0", "root_id": "toy:root",
        "nodes": [node("toy:root", "root", "Toy joining chart"),
                  node("toy:alpha", "category", "ALPHA FAMILY (AF)"),
                  node("toy:beta", "category", "BETA FAMILY (BF)"),
                  node("toy:ribbon", "process", "Ribbon fold", "ZZR", 0.2),
                  node("toy:pulsed", "process", "Ribbon fold pulsed", "ZZRP", 0.3),
                  node("toy:deep", "process", "Ribbon fold pulsed fine", "ZZRPF", 0.4),
                  node("toy:foil", "process", "Foil bind", "ZZF", 0.5),
                  node("toy:squeeze", "process", "Squeeze join", "ZZS", 0.6)],
        "edges": [edge("toy:root", "toy:alpha", "CHART_CONNECTOR"),
                  edge("toy:root", "toy:beta", "CHART_CONNECTOR"),
                  *[edge("toy:alpha", target, "ENCLOSES_ROW") for target in
                    ("toy:ribbon", "toy:pulsed", "toy:deep", "toy:foil")],
                  edge("toy:beta", "toy:squeeze", "ENCLOSES_ROW"),
                  edge("toy:ribbon", "toy:pulsed", "INDENTED_UNDER"),
                  edge("toy:pulsed", "toy:deep", "INDENTED_UNDER")],
        "edge_qualifications": {
            "CHART_CONNECTOR": {"verification": "source_bound", "qualification": "Printed chart connector only."},
            "ENCLOSES_ROW": {"verification": "source_bound", "qualification": "Printed enclosure only, not semantic subtype."},
            "INDENTED_UNDER": {"verification": "candidate", "qualification": "Candidate layout parent; not reviewed IS_A."}},
        "region_space": "normalized_pdf_page_ymin_xmin_ymax_xmax",
        "native_text": "Original synthetic labels only.", "limits": ["Toy chart only."]}


def answer(graph, query, **kwargs):
    return importlib.import_module("src.evidence_a1_graph_qa").answer_graph(graph, query, **kwargs)


def rows(result):
    return {row["id"] for row in result["rows"]}


def test_independent_shorter_mention_survives_longer_name_elsewhere(graph):
    result = answer(graph, "Compare Ribbon fold pulsed and Ribbon fold.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert {"toy:ribbon", "toy:pulsed"} <= set(result["resolved_entities"])
    assert {"toy:ribbon", "toy:pulsed"} <= rows(result)
    assert "toy:deep" not in rows(result)


def test_contained_shorter_name_does_not_create_extra_subject(graph):
    result = answer(graph, "What is the abbreviation for Ribbon fold pulsed?")
    assert result["answer_outcome"] == "graph_answer"
    assert rows(result) == {"toy:pulsed"}
    assert result["resolved_entities"] == ["toy:pulsed"]


@pytest.mark.parametrize("query", [
    "What are the abbreviations for Ribbon fold, Foil bind, and Squeeze join?",
    "What do ZZR, ZZF, and ZZS stand for?",
    "Which families do Ribbon fold, Foil bind, and Squeeze join belong to?",
])
def test_n_subject_labels_codes_and_family_lookup_do_not_stop_at_one(graph, query):
    result = answer(graph, query, complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert rows(result) == {"toy:ribbon", "toy:foil", "toy:squeeze"}
    assert {"toy:ribbon", "toy:foil", "toy:squeeze"} <= set(result["resolved_entities"])


@pytest.mark.parametrize("selector,duplicate_field", [("Foil bind", "label"), ("ZZF", "code")])
def test_duplicate_labels_or_codes_are_explicit_ambiguity(graph, selector, duplicate_field):
    duplicate = deepcopy(next(node for node in graph["nodes"] if node["id"] == "toy:foil"))
    duplicate.update(id="toy:duplicate", label="Tape bind", code="ZZT")
    duplicate[duplicate_field] = "Foil bind" if duplicate_field == "label" else "ZZF"
    graph["nodes"].append(duplicate)
    graph["edges"].append({"from": "toy:beta", "to": duplicate["id"], "type": "ENCLOSES_ROW"})
    query = f"What is the abbreviation for {selector}?" if duplicate_field == "label" else f"What does {selector} stand for?"
    result = answer(graph, query)
    assert result["answer_outcome"] == "clarification_required"
    assert result["trace"]["diagnostics"]
    assert result.get("verdict", "not_established") == "not_established"


@pytest.mark.parametrize("query,missing", [
    ("What are abbreviations for Ribbon fold, Moon stitch, and Foil bind?", "Moon stitch"),
    ("What do ZZR, ZZMISSING, and ZZF stand for?", "ZZMISSING"),
])
def test_genuinely_missing_requested_subject_is_not_silently_dropped(graph, query, missing):
    result = answer(graph, query)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert missing.casefold() in json.dumps(result).casefold()
    assert result["trace"]["diagnostics"]


def test_direct_children_and_recursive_descendants_have_distinct_results(graph):
    direct = answer(graph, "Which entries are directly beneath Ribbon fold, and which broader category contains them?", complete_chart=True)
    recursive = answer(graph, "List all descendants of Ribbon fold.", complete_chart=True)
    assert direct["answer_outcome"] == recursive["answer_outcome"] == "graph_answer"
    assert rows(direct) == {"toy:pulsed"}
    assert rows(recursive) == {"toy:pulsed", "toy:deep"}
    category = next(operation for operation in direct["operations"] if operation["kind"] == "category")
    assert category["subject_ids"] == ["toy:pulsed"]
    assert "ALPHA FAMILY" in direct["answer"]
    assert any(edge["from"] == "toy:alpha" and edge["to"] == "toy:pulsed"
               for edge in direct["trace"]["selected_edges"])
    assert all(edge["type"] != "IS_A" for result in (direct, recursive)
               for edge in result["trace"]["selected_edges"])
    assert "candidate" in json.dumps(recursive).lower()


def test_process_category_membership_uses_enclosure_not_candidate_parentage(graph):
    result = answer(graph, "Is Ribbon fold pulsed in ALPHA FAMILY?", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert result["verdict"] == "yes"
    assert any(edge["from"] == "toy:alpha" and edge["to"] == "toy:pulsed"
               and edge["type"] == "ENCLOSES_ROW" for edge in result["trace"]["selected_edges"])
    assert result["semantic_validation"] is False


def test_process_process_membership_remains_candidate_layout(graph):
    result = answer(graph, "Is Ribbon fold pulsed directly under ALPHA FAMILY, or under Ribbon fold within that category in A1?", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert "candidate" in json.dumps(result).lower()
    assert any(edge["from"] == "toy:ribbon" and edge["to"] == "toy:pulsed"
               and edge["type"] == "INDENTED_UNDER" for edge in result["trace"]["selected_edges"])
    assert result["semantic_validation"] is False
    assert result["verdict"] == "not_established"
    operation = next(item for item in result["operations"] if item["kind"] == "layout_relation")
    by_target = {item["target_id"]: item for item in operation["alternatives"]}
    assert by_target["toy:ribbon"]["immediate_layout_parent"] is True
    assert by_target["toy:alpha"]["immediate_layout_parent"] is False
    assert by_target["toy:alpha"]["source_box_enclosure"] is True
    assert "IS_A" not in [edge["type"] for edge in result["trace"]["selected_edges"]]


def test_epistemic_query_reports_layout_support_without_semantic_upgrade(graph):
    result = answer(graph, "Does A1 establish that every indented entry means subtype, or is additional evidence needed to interpret indentation?")
    assert result["answer_outcome"] == "graph_answer"
    assert "candidate" in json.dumps(result).lower()
    assert result["semantic_validation"] is False
    assert "review" in result["answer"].lower() or "layout" in result["answer"].lower()


def test_process_control_information_is_not_inferred_from_chart(graph):
    result = answer(graph, "What operating temperature and timing should I use for Ribbon fold?")
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["semantic_validation"] is False
    assert result.get("verdict", "not_established") == "not_established"
    assert result["trace"]["diagnostics"]


def test_answering_does_not_mutate_graph_or_promote_candidate_is_a(graph):
    original = deepcopy(graph)
    result = answer(graph, "List all descendants of Ribbon fold.", complete_chart=True)
    assert graph == original
    assert graph["edge_qualifications"]["INDENTED_UNDER"]["verification"] == "candidate"
    assert result["semantic_validation"] is False
    assert not any(edge["type"] == "IS_A" for edge in graph["edges"])


def test_compound_plural_intent_executes_each_operation_for_every_subject(graph):
    result = answer(graph, "What are abbreviations for Ribbon fold, Foil bind, and Squeeze join, "
                          "and which families do they belong to?", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert rows(result) == {"toy:ribbon", "toy:foil", "toy:squeeze"}
    assert {operation["kind"] for operation in result["plan"]["operations"]} >= {"designation", "category"}
    assert {operation["kind"] for operation in result["operations"]} >= {"designation", "category"}
    assert not result["plan"]["unresolved_selectors"]


def test_compound_operating_request_is_not_silently_dropped(graph):
    result = answer(graph, "Give the abbreviation for Ribbon fold and its recommended operating temperature.",
                    complete_chart=True)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["partial_completion"] is True
    by_kind = {operation["kind"]: operation for operation in result["operations"]}
    assert by_kind["designation"]["answer_outcome"] == "graph_answer"
    assert by_kind["operating_information"]["answer_outcome"] == "insufficient_evidence"
    assert result["semantic_validation"] is False


def test_span_plan_distinguishes_containment_from_independent_occurrence(graph):
    query = "Compare Ribbon fold pulsed and Ribbon fold."
    plan = importlib.import_module("src.evidence_a1_graph_qa").plan_graph_query(graph, query)
    mentions = plan["mentions"]
    short = [mention for mention in mentions if "toy:ribbon" in mention["candidate_ids"]]
    longer = [mention for mention in mentions if "toy:pulsed" in mention["candidate_ids"]]
    assert len(short) == len(longer) == 1
    assert query[short[0]["start"]:short[0]["end"]] == "Ribbon fold"
    assert query[longer[0]["start"]:longer[0]["end"]] == "Ribbon fold pulsed"
    assert short[0]["start"] > longer[0]["end"]


def test_ordered_paths_keep_root_category_process_chain_and_qualifications(graph):
    result = answer(graph, "Show the paths from the root through the categories to Ribbon fold pulsed fine.",
                    complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    paths = [path for path in result["paths"] if path["target_id"] == "toy:deep"]
    assert paths
    expected = ["toy:root", "toy:alpha", "toy:ribbon", "toy:pulsed", "toy:deep"]
    assert any(path["node_ids"] == expected for path in paths)
    for path in paths:
        assert path["node_ids"][0] == "toy:root"
        assert path["node_ids"][-1] == "toy:deep"
        assert len(path["edges"]) == len(path["node_ids"]) - 1
        assert all(edge["from"] == first and edge["to"] == second
                   for edge, first, second in zip(path["edges"], path["node_ids"], path["node_ids"][1:]))
        assert path["qualification"]
        assert "IS_A" not in path["edge_types"]
    assert any("candidate" in path["qualification"].lower() for path in paths
               if "INDENTED_UNDER" in path["edge_types"])


def test_category_direct_children_exclude_indented_rows_while_descendants_include_them(graph):
    result = answer(graph, "List the direct children of ALPHA FAMILY separately from all descendants. Explain the difference in the two lists.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    by_kind = {operation["kind"]: operation for operation in result["operations"]}
    assert rows(by_kind["direct_children"]) == {"toy:ribbon", "toy:foil"}
    assert rows(by_kind["descendants"]) == {"toy:ribbon", "toy:pulsed", "toy:deep", "toy:foil"}
    comparison = result["list_comparisons"][0]
    assert comparison["direct_count"] == 2 and comparison["descendant_count"] == 4
    assert set(comparison["deeper_node_ids"]) == {"toy:pulsed", "toy:deep"}
    assert {tuple(edge[key] for key in ("from", "to", "type")) for edge in result["trace"]["selected_edges"]} == {
        ("toy:alpha", process, "ENCLOSES_ROW") for process in ("toy:ribbon", "toy:pulsed", "toy:deep", "toy:foil")
    } | {("toy:ribbon", "toy:pulsed", "INDENTED_UNDER"), ("toy:pulsed", "toy:deep", "INDENTED_UNDER")}


def test_partial_chart_does_not_establish_exhaustive_descendants(graph):
    result = answer(graph, "List all descendants of ALPHA FAMILY.", complete_chart=False)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert result["trace"]["diagnostics"]


def test_synthetic_wrapper_preserves_source_identity_image_and_graph_across_operations(graph, tmp_path, monkeypatch):
    from src.evidence_a1 import a1_source_identity_id
    from src.evidence_v2 import Evidence, evidence_id
    sys.path.insert(0, str(Path(__file__).parent))
    # This helper is already an original redistributable image fixture.
    from evidence_v2_fixture import png_bytes
    engine = importlib.import_module("src.evidence_a1_graph_qa")
    original = deepcopy(graph)
    edition = "fixture:repair:1@" + hashlib.sha256(b"Original planner repair toy").hexdigest()
    raw = png_bytes((21, 62, 119))
    asset = tmp_path / "assets/toy.png"
    asset.parent.mkdir()
    asset.write_bytes(raw)
    asset_hash = hashlib.sha256(raw).hexdigest()
    anchor = {"pdf_index": 0, "printed_label": "1", "order": 0, "role": "start", "region": None}
    identity = a1_source_identity_id(edition, "figure:figure_a1", anchor, asset_hash)
    note_locator = {"element_id": "Annex A", "order": 0}
    note_content = {"text": "Only the original toy chart is in scope.", "notes": [], "qualifiers": [], "exceptions": []}
    note = Evidence(evidence_id(edition, "note", note_locator, note_content), edition, "note",
                    note_locator, note_content, "synthetic")
    locator = {"element_id": "Figure A1", "canonical_element_id": "figure:figure_a1", "source_identity_id": identity,
               "pdf_index": 0, "printed_page": "1", "order": 0, "region": None, "region_scope": "full_page"}
    content = {"caption": "Original repair toy", "asset_relpath": "assets/toy.png", "asset_sha256": asset_hash,
               "source_identity_id": identity, "media_type": "image/png", "single_image_scope": True,
               "continuation_orders": [0], "chart_graph": graph, "required_evidence_ids": [note.evidence_id],
               "notes": [], "qualifiers": [], "exceptions": []}
    figure = Evidence(evidence_id(edition, "figure_region", locator, content), edition,
                      "figure_region", locator, content, "synthetic", required_ids=(note.evidence_id,))
    monkeypatch.setattr(engine, "load_a1_evidence", lambda *args, **kwargs: [note, figure])
    payload = {"schema_version": "a1-owner-cq-1.0", "source_element": "Figure A1", "questions": [
        {"id": "toy-n", "query": "What do ZZR, ZZF, and ZZS stand for?"},
        {"id": "toy-operating", "query": "What operating temperature should I use for Ribbon fold?"},
        {"id": "toy-compare", "query": "Compare Ribbon fold and Foil bind."},
        {"id": "toy-foreign", "query": "Compare Ribbon fold and Foil bind with Figure A2."}]}
    result = engine.run_graph_qa(tmp_path, payload)
    assert result["model"] == result["provider"] == "NONE"
    assert result["model_invocation_count"] == result["external_call_count"] == 0
    assert result["source_identity_id"] == identity
    assert result["edition_id"] == edition
    assert result["source_image_count"] == 1
    assert [item["answer_outcome"] for item in result["answers"]] == [
        "graph_answer", "insufficient_evidence", "graph_answer", "insufficient_evidence"]
    for item in result["answers"]:
        assert item["source_identity_id"] == identity
        assert item["source_image"]["asset_sha256"] == asset_hash
        assert item["source_locator"] == locator
        assert item["edition_id"] == edition
        assert figure.evidence_id in item["evidence_ids"]
        assert item["graph_sha256"] == result["graph_sha256"]
        assert item["semantic_validation"] is False
    assert asset.read_bytes() == raw and graph == original
