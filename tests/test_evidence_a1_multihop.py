"""Four bounded generic regressions; no owner questions or source answers."""
from copy import deepcopy

from test_evidence_a1_graph_qa_repair import graph, no_external_calls
from src.evidence_a1_graph_qa import answer_graph


def test_immediate_parents_keep_candidate_and_positive_enclosure_separate(graph):
    result = answer_graph(graph, "Show immediate parents of Ribbon fold pulsed.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    operation = next(item for item in result["operations"] if item["kind"] == "parents")
    assert operation["parent_groups"] == [{"subject_id": "toy:pulsed", "parent_ids": ["toy:ribbon"]}]
    assert operation["source_placements"] == [{"process_id": "toy:pulsed", "category_ids": ["toy:alpha"]}]
    assert any(edge["type"] == "INDENTED_UNDER" for edge in operation["trace"]["selected_edges"])
    assert "candidate" in operation["answer"].lower()
    assert result["semantic_validation"] is False


def test_sibling_path_preserves_common_ancestor_and_reverse_source_steps(graph):
    result = answer_graph(graph, "Show the path from Ribbon fold pulsed fine to Foil bind.", complete_chart=True)
    assert result["answer_outcome"] == "graph_answer"
    assert len(result["paths"]) == 1
    path = result["paths"][0]
    assert path["node_ids"] == ["toy:deep", "toy:pulsed", "toy:ribbon", "toy:alpha", "toy:foil"]
    assert path["common_ancestor_id"] == "toy:alpha"
    assert [step["direction"] for step in path["traversal_steps"]] == ["reverse", "reverse", "reverse", "forward"]
    assert path["edges"][0]["from"] == "toy:pulsed"  # source orientation remains intact
    assert "candidate" in path["qualification"].lower()


def test_descendant_expansion_receipt_keeps_all_rows_and_intermediate_groups(graph):
    result = answer_graph(graph, "List all recursive descendants of ALPHA FAMILY.", complete_chart=True)
    operation = next(item for item in result["operations"] if item["kind"] == "descendants")
    assert [row["id"] for row in operation["rows"]] == ["toy:ribbon", "toy:pulsed", "toy:deep", "toy:foil"]
    assert operation["expansion"]["status"] == "complete_within_supplied_chart"
    assert operation["expansion"]["no_top_k_truncation"] is True
    assert operation["expansion"]["returned_node_ids"] == operation["groups"][0]["node_ids"]
    assert operation["expansion"]["semantic_validation"] is False


def test_atomic_claims_do_not_authenticate_unbound_caller_graph(graph):
    original = deepcopy(graph)
    result = answer_graph(graph, "Show the path from Ribbon fold pulsed fine to Foil bind.", complete_chart=True)
    assert result["claims"]
    assert any(claim["predicate"] == "ordered_chart_path" for claim in result["claims"])
    assert all(claim["evidence_ids"] == [] and claim["support"] == "unbound_caller_graph" for claim in result["claims"])
    assert all(claim["semantic_validation"] is False for claim in result["claims"])
    assert result["support_state"] == "UNAUTHENTICATED_CALLER_GRAPH"
    assert result["record_evidence_catalog"] == []
    assert graph == original
