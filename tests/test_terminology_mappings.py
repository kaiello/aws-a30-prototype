"""Synthetic contracts for an opt-in terminology helper; no corpus/store access."""
import ast
from copy import deepcopy
import json
from pathlib import Path

import networkx as nx
import pytest

from src.terminology_mappings import (
    merge_mapping_records,
    parse_nonstandard_entry,
    project_mapping_records,
)


class SyntheticManifest:
    document = {"id": "doc:synthetic", "sha256": "a" * 64}

    def resolve(self, label):
        return {"status": "exact" if label == "clause:synthetic" else "unknown"}

    def anchors(self, label):
        return [{"pdf_index": index, "printed_label": str(index - 12)}
                for index in (25, 26)] if label == "clause:synthetic" else []


def nodes():
    return [
        {"id": "onto:legacy", "name": "legacy label", "sense": "default",
         "process_context": "", "verification_state": "verified"},
        {"id": "onto:alpha", "name": "target alpha", "sense": "",
         "process_context": "arc or gas welding", "verification_state": "verified"},
        {"id": "onto:beta", "name": "target beta", "sense": "",
         "process_context": "brazing", "verification_state": "verified"},
    ]


def entry(definition="A nonstandard term for target alpha (arc or gas welding); target beta (brazing).", **changes):
    text = "legacy label. " + definition
    result = {
        "term": "legacy label", "sense": "default", "process_context": "",
        "source_id": "onto:legacy", "definition": definition,
        "source": {"document_id": "doc:synthetic", "source_sha256": "a" * 64,
                   "section_id": "clause:synthetic", "pdf_index": 25,
                   "printed_label": "13", "record_id": "entry:one",
                   "span": [0, len(text)], "text": text,
                   "verification_state": "verified"},
    }
    result.update(changes)
    return result


def parse(value=None, supplied_nodes=None):
    return parse_nonstandard_entry(value or entry(), manifest=SyntheticManifest(),
                                   ontology_nodes=nodes() if supplied_nodes is None else supplied_nodes)


def graph_for(supplied_nodes=None):
    graph = nx.MultiDiGraph()
    for node in nodes() if supplied_nodes is None else supplied_nodes:
        graph.add_node(node["id"], **{key: value for key, value in node.items() if key != "id"})
    graph.add_edge("onto:legacy", "onto:alpha", key="NONSTANDARD_FOR",
                   rel_type="NONSTANDARD_FOR", description="legacy evidence", layer="ontology")
    return graph


def test_targets_remain_ordered_and_parenthesized_or_is_not_a_separator():
    result = parse()
    assert result["diagnostics"] == []
    assert [r["preferred_term"] for r in result["records"]] == ["target alpha", "target beta"]
    assert [r["target_process_context"] for r in result["records"]] == ["arc or gas welding", "brazing"]
    assert [r["target_id"] for r in result["records"]] == ["onto:alpha", "onto:beta"]
    assert all(r["verification_state"] == "verified" for r in result["records"])


def test_explicit_target_boundaries_disambiguate_top_level_or():
    value = entry("A nonstandard term for target alpha (arc or gas welding) or target beta (brazing).",
                  targets=[{"text": "target alpha (arc or gas welding)"},
                           {"text": "target beta (brazing)"}])
    assert [r["target_id"] for r in parse(value)["records"]] == ["onto:alpha", "onto:beta"]


def test_or_inside_an_explicit_target_phrase_survives():
    supplied = nodes() + [{"id": "onto:phrase", "name": "heat or pressure welding", "sense": "",
                           "process_context": "", "verification_state": "verified"}]
    value = entry("A nonstandard term for heat or pressure welding.",
                  targets=[{"text": "heat or pressure welding"}])
    record = parse(value, supplied)["records"][0]
    assert record["preferred_term"] == "heat or pressure welding"
    assert record["target_id"] == "onto:phrase"


def test_unbounded_or_ambiguity_is_explicit_instead_of_inventing_targets():
    result = parse(entry("A nonstandard term for unknown alpha or unknown beta."))
    assert result["records"] == []
    assert "ambiguous_target_boundaries" in result["diagnostics"]


def test_hyphenated_headword_and_conditional_qualification_are_preserved():
    supplied = nodes()
    supplied[0] = dict(supplied[0], name="legacy-name")
    value = entry("A nonstandard term when used for target beta (brazing).", term="legacy-name")
    value["source"]["text"] = "legacy-name. " + value["definition"]
    value["source"]["span"] = [0, len(value["source"]["text"])]
    record = parse(value, supplied)["records"][0]
    assert record["nonstandard_term"] == "legacy-name"
    assert record["qualification"] == "when used for"
    assert record["relation_type"] == "NONSTANDARD_FOR"


@pytest.mark.parametrize("definition", ["A standard definition.", "A nonstandard term for .",
                                        "A nonstandard term for target alpha (arc welding.",
                                        "A nonstandard term for target beta.\nAnother entry. More prose."])
def test_malformed_or_unbounded_entries_produce_diagnostics(definition):
    result = parse(entry(definition))
    assert not result["records"]
    assert result["diagnostics"]


@pytest.mark.parametrize("field,value", [("source_sha256", "b" * 64), ("document_id", "doc:other"),
                                         ("printed_label", "999"), ("span", [3, 2]),
                                         ("record_id", "")])
def test_source_provenance_must_match_supplied_manifest(field, value):
    value_entry = entry()
    value_entry["source"][field] = value
    result = parse(value_entry)
    assert result["diagnostics"]
    assert all(r["verification_state"] == "candidate" for r in result["records"])


def test_missing_source_and_unverified_source_cannot_be_promoted():
    for source in ({}, None, dict(entry()["source"], verification_state="candidate")):
        result = parse(entry(source=source))
        assert result["diagnostics"]
        assert all(r["verification_state"] == "candidate" for r in result["records"])


def test_reviewed_page_metadata_does_not_verify_an_unrelated_entry_span():
    value = entry()
    value["source"]["text"] = "An unrelated synthetic source entry."
    value["source"]["span"] = [0, len(value["source"]["text"])]
    result = parse(value)
    assert "source_span_mismatch" in result["diagnostics"]
    assert all(record["verification_state"] == "candidate" for record in result["records"])


@pytest.mark.parametrize("impostor", ["non{entry}", "{entry} Additional unrelated material."])
def test_source_span_requires_the_exact_bounded_entry_not_a_substring(impostor):
    value = entry()
    value["source"]["text"] = impostor.format(entry=value["source"]["text"])
    value["source"]["span"] = [0, len(value["source"]["text"])]
    result = parse(value)
    assert "source_span_mismatch" in result["diagnostics"]
    assert all(record["verification_state"] == "candidate" for record in result["records"])


def test_target_evidence_stays_separate_and_requires_its_own_valid_anchor():
    proof = dict(entry()["source"], record_id="target:definition", text="Synthetic target definition.")
    proof["span"] = [0, len(proof["text"])]
    value = entry("A nonstandard term for target beta (brazing).",
                  targets=[{"text": "target beta (brazing)", "provenance": [proof]}])
    result = parse(value)
    assert result["diagnostics"] == []
    assert result["records"][0]["target_provenance"] == [proof]
    assert result["records"][0]["provenance"] == [value["source"]]
    value["targets"][0]["provenance"][0]["printed_label"] = "999"
    assert parse(value)["records"][0]["verification_state"] == "candidate"


def test_spelling_alone_never_resolves_unknown_ambiguous_or_unverified_targets():
    value = entry("A nonstandard term for target beta (brazing).")
    for supplied in (nodes()[:2], nodes() + [dict(nodes()[2], id="onto:beta2")],
                     nodes()[:2] + [dict(nodes()[2], verification_state="candidate")]):
        result = parse(value, supplied)
        assert result["records"][0]["target_id"] is None
        assert result["records"][0]["verification_state"] == "candidate"
        assert result["diagnostics"]


def test_verified_process_and_sense_choose_only_compatible_existing_target():
    supplied = nodes() + [dict(nodes()[2], id="onto:beta:gas", process_context="gas welding")]
    record = parse(entry("A nonstandard term for target beta (brazing)."), supplied)["records"][0]
    assert record["target_id"] == "onto:beta"
    value = entry("A nonstandard term for target beta (brazing).",
                  targets=[{"text": "target beta (brazing)", "target_id": "onto:beta:gas"}])
    assert parse(value, supplied)["records"][0]["target_id"] is None


def test_duplicate_normalization_unions_evidence_without_mutating_inputs():
    first = parse()["records"][0]
    second = deepcopy(first)
    second["preferred_term"] = "  TARGET   ALPHA  "
    extra = dict(second["provenance"][0], record_id="additional evidence", pdf_index=26, printed_label="14")
    second["provenance"].append(extra)
    original = deepcopy([first, second])
    merged = merge_mapping_records([first, second, first])
    assert len(merged) == 1
    assert merged[0]["mapping_id"] == first["mapping_id"]
    assert merged[0]["preferred_term"] == "target alpha"
    assert [p["record_id"] for p in merged[0]["provenance"]] == ["entry:one", "additional evidence"]
    assert [first, second] == original


def test_distinct_entries_pages_senses_and_contexts_have_stable_mapping_ids():
    first = parse()["records"][0]
    later = entry()
    later["source"] = dict(later["source"], pdf_index=26, printed_label="14", record_id="entry:two")
    second = parse(later)["records"][0]
    different_sense = entry(sense="conditional")
    supplied = nodes() + [dict(nodes()[0], id="onto:legacy:conditional", sense="conditional")]
    different_sense["source_id"] = "onto:legacy:conditional"
    third = parse(different_sense, supplied)["records"][0]
    assert len({first["mapping_id"], second["mapping_id"], third["mapping_id"]}) == 3
    assert first["mapping_id"] == parse()["records"][0]["mapping_id"]
    assert len(merge_mapping_records([first, second, third])) == 3
    assert all(not record["mapping_id"].startswith("clause3_") for record in (first, second, third))


def test_conflicting_same_context_target_resolutions_are_preserved_as_candidates():
    first = parse()["records"][0]
    second = dict(deepcopy(first), target_id="onto:conflicting-resolution")
    merged = merge_mapping_records([first, second])
    assert len(merged) == 2
    assert {record["target_id"] for record in merged} == {"onto:alpha", "onto:conflicting-resolution"}
    assert all(record["verification_state"] == "candidate" for record in merged)
    assert all("conflicting_target_resolution" in record["diagnostics"] for record in merged)


def test_successive_projection_calls_reject_conflicting_qualified_target_ids():
    supplied = nodes() + [dict(nodes()[1], id="onto:alpha:alternative")]
    value = entry("A nonstandard term for target alpha (arc or gas welding).",
                  targets=[{"text": "target alpha (arc or gas welding)", "target_id": "onto:alpha"}])
    first = parse(value, supplied)["records"][0]
    value["targets"][0]["target_id"] = "onto:alpha:alternative"
    second = parse(value, supplied)["records"][0]
    assert first["verification_state"] == second["verification_state"] == "verified"
    graph = graph_for(supplied)
    node_state = deepcopy(dict(graph.nodes(data=True)))
    legacy_state = deepcopy(graph["onto:legacy"]["onto:alpha"]["NONSTANDARD_FOR"])
    assert project_mapping_records(graph, [first])["projected_ids"] == [first["mapping_id"]]
    result = project_mapping_records(graph, [second])
    assert result["projected_ids"] == []
    assert any(issue.startswith("conflicting_target_resolution") for issue in result["diagnostics"])
    assert not graph.has_edge("onto:legacy", "onto:alpha:alternative")
    assert graph.number_of_edges() == 2
    assert dict(graph.nodes(data=True)) == node_state
    assert graph["onto:legacy"]["onto:alpha"]["NONSTANDARD_FOR"] == legacy_state


def test_same_pair_qualified_evidence_preserves_legacy_edges_and_node_ids():
    first = parse()["records"][0]
    second = deepcopy(first)
    second["qualification"] = "when used for"
    records = merge_mapping_records([first, second])
    graph = graph_for()
    before_nodes = deepcopy(dict(graph.nodes(data=True)))
    legacy = deepcopy(graph["onto:legacy"]["onto:alpha"]["NONSTANDARD_FOR"])
    result = project_mapping_records(graph, records)
    assert len(result["projected_ids"]) == 2
    assert dict(graph.nodes(data=True)) == before_nodes
    assert graph["onto:legacy"]["onto:alpha"]["NONSTANDARD_FOR"] == legacy
    assert graph.number_of_edges("onto:legacy", "onto:alpha") == 3
    project_mapping_records(graph, records)
    assert graph.number_of_edges("onto:legacy", "onto:alpha") == 3


def test_projection_does_not_create_nodes_or_promote_candidates():
    graph = graph_for()
    record = parse()["records"][0]
    record["target_id"] = "onto:missing"
    before = deepcopy(graph)
    result = project_mapping_records(graph, [record])
    assert result["projected_ids"] == []
    assert result["diagnostics"]
    assert nx.utils.graphs_equal(graph, before)
    candidate = parse(entry(source={}))["records"][0]
    assert project_mapping_records(graph, [candidate])["projected_ids"] == []


def test_projection_does_not_overwrite_a_legacy_edge_with_a_colliding_mapping_key():
    graph = graph_for()
    record = parse()["records"][0]
    graph.add_edge(record["source_id"], record["target_id"], key=record["mapping_id"],
                   mapping_id=record["mapping_id"], mapping_json=json.dumps(record),
                   rel_type="LEGACY_RELATION", layer="evidence", weight=7.0,
                   verification_state="verified", description="unowned legacy attributes")
    before = deepcopy(graph)
    result = project_mapping_records(graph, [record])
    assert result["projected_ids"] == []
    assert any(issue.startswith("graph_edge_key_conflict") for issue in result["diagnostics"])
    assert nx.utils.graphs_equal(graph, before)


@pytest.mark.parametrize("field,value", [("source", ["bad"]), ("source", []),
                                         ("target_id", ["onto:alpha"]),
                                         ("source_id", ["onto:legacy"])])
def test_malformed_record_containers_or_ids_fail_explicitly_without_graph_changes(field, value):
    record = parse()["records"][0]
    record[field] = value
    with pytest.raises(ValueError, match="invalid_mapping_record"):
        merge_mapping_records([record])
    graph = graph_for()
    before = deepcopy(graph)
    result = project_mapping_records(graph, [record])
    assert result["projected_ids"] == []
    assert any(issue.startswith("invalid_mapping_record") for issue in result["diagnostics"])
    assert nx.utils.graphs_equal(graph, before)


@pytest.mark.parametrize("field", ["nonstandard_term", "preferred_term"])
def test_missing_mapping_labels_fail_explicitly_without_graph_changes(field):
    record = parse()["records"][0]
    del record[field]
    with pytest.raises(ValueError, match="invalid_mapping_record"):
        merge_mapping_records([record])
    graph = graph_for()
    before = deepcopy(graph)
    result = project_mapping_records(graph, [record])
    assert result["projected_ids"] == []
    assert any(issue.startswith("invalid_mapping_record") for issue in result["diagnostics"])
    assert nx.utils.graphs_equal(graph, before)


def test_standard_and_conditional_nonstandard_sense_nodes_are_unchanged():
    standard = dict(nodes()[0], id="onto:legacy:standard", sense="standard", standard_status="standard")
    conditional = dict(nodes()[0], id="onto:legacy:conditional", sense="conditional", standard_status="nonstandard")
    supplied = [standard, conditional] + nodes()[1:]
    graph = nx.MultiDiGraph()
    for node in supplied:
        graph.add_node(node["id"], **{key: value for key, value in node.items() if key != "id"})
    graph.add_edge(standard["id"], "onto:alpha", key="SEMANTIC_RELATION", description="standard sense evidence")
    graph.add_edge(conditional["id"], "onto:beta", key="NONSTANDARD_FOR", description="conditional sense evidence")
    original_nodes = deepcopy(dict(graph.nodes(data=True)))
    original_edges = deepcopy(list(graph.edges(keys=True, data=True)))
    value = entry("A nonstandard term when used for target beta (brazing).",
                  sense="conditional", source_id=conditional["id"])
    record = parse(value, supplied)["records"][0]
    assert record["source_id"] == conditional["id"]
    assert record["qualification"] == "when used for"
    assert project_mapping_records(graph, [record])["projected_ids"] == [record["mapping_id"]]
    assert dict(graph.nodes(data=True)) == original_nodes
    for source, target, key, attributes in original_edges:
        assert graph[source][target][key] == attributes


def test_graphml_round_trip_retains_canonical_json_provenance(tmp_path):
    graph = graph_for()
    records = parse()["records"]
    projected = project_mapping_records(graph, records)["projected_ids"]
    target = tmp_path / "synthetic.graphml"
    nx.write_graphml(graph, target)
    restored = nx.read_graphml(target, force_multigraph=True)
    for record, key in zip(records, projected):
        attributes = restored[record["source_id"]][record["target_id"]][key]
        assert json.loads(attributes["mapping_json"])["provenance"] == record["provenance"]
        assert attributes["mapping_json"] == json.dumps(json.loads(attributes["mapping_json"]), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_builder_adapter_is_opt_in_and_operates_only_on_supplied_graph():
    path = Path(__file__).resolve().parents[1] / "src" / "build_dual_graph.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "project_terminology_mappings")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    graph = graph_for()
    result = namespace[function.name](graph, parse()["records"])
    assert len(result["projected_ids"]) == 2
    assert set(graph.nodes) == {node["id"] for node in nodes()}
