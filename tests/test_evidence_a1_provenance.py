"""Record-level provenance over synthetic geometry; no model or AWS answers."""
from copy import deepcopy
import hashlib
import json

import pytest

from src.evidence_a1 import bind_a1_graph_evidence, validate_a1_graph_evidence


def fixture():
    graph = {"schema_version": "a1-geometry-1.0", "root_id": "toy:root",
        "region_space": "normalized_pdf_page_ymin_xmin_ymax_xmax",
        "nodes": [{"id": "toy:root", "kind": "root", "label": "Toy chart", "region": [0.1, 0.1, 0.2, 0.4]},
                  {"id": "toy:family", "kind": "category", "label": "ALPHA (AF)", "region": [0.3, 0.1, 0.8, 0.7]},
                  {"id": "toy:parent", "kind": "process", "label": "Ribbon fold", "code": "ZZR", "region": [0.4, 0.2, 0.45, 0.6]},
                  {"id": "toy:child", "kind": "process", "label": "Pulsed fold", "code": "ZZP", "region": [0.5, 0.3, 0.55, 0.6]}],
        "edges": [{"from": "toy:root", "to": "toy:family", "type": "CHART_CONNECTOR", "region": [0.19, 0.3, 0.31, 0.31]},
                  {"from": "toy:family", "to": "toy:parent", "type": "ENCLOSES_ROW", "region": [0.4, 0.2, 0.45, 0.6]},
                  {"from": "toy:family", "to": "toy:child", "type": "ENCLOSES_ROW", "region": [0.5, 0.3, 0.55, 0.6]},
                  {"from": "toy:parent", "to": "toy:child", "type": "INDENTED_UNDER", "region": [0.4, 0.2, 0.55, 0.6]}],
        "edge_qualifications": {"CHART_CONNECTOR": {"verification": "source_bound", "qualification": "Observed line."},
            "ENCLOSES_ROW": {"verification": "source_bound", "qualification": "Observed enclosure."},
            "INDENTED_UNDER": {"verification": "candidate", "qualification": "Observed indentation, not reviewed semantic subtype."}},
        "native_text": "Toy chart", "limits": ["Synthetic test only."]}
    source = {"edition_id": "doc:toy@" + "a" * 64, "source_identity_id": "source2:toy",
        "asset_sha256": "b" * 64, "locator": {"element_id": "Figure A1", "canonical_element_id": "figure:figure_a1",
            "source_identity_id": "source2:toy", "pdf_index": 4, "printed_page": "2", "order": 0,
            "region": None, "region_scope": "full_page"}}
    return graph, source


def test_each_record_has_stable_source_and_region_without_changing_facts():
    graph, source = fixture()
    original = deepcopy(graph)
    bound = bind_a1_graph_evidence(graph, **source)
    assert graph == original
    native_hash = hashlib.sha256(json.dumps(graph, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    assert bound["native_graph_sha256"] == native_hash
    assert bound == bind_a1_graph_evidence(graph, **source)
    records = bound["nodes"] + bound["edges"]
    assert len({r["evidence"]["evidence_id"] for r in records}) == 8
    for record in records:
        evidence = record["evidence"]
        assert evidence["source_identity_id"] == source["source_identity_id"]
        assert evidence["edition_id"] == source["edition_id"]
        assert evidence["asset_sha256"] == source["asset_sha256"]
        assert evidence["locator"]["region"] == record["region"]
        assert evidence["locator"]["pdf_index"] == 4
    candidate = next(e for e in bound["edges"] if e["type"] == "INDENTED_UNDER")
    assert candidate["evidence"]["verification"] == "candidate"
    assert validate_a1_graph_evidence(bound, expected_source=source)["record_evidence_count"] == 8


def test_tampered_or_incomplete_record_proofs_and_edition_are_rejected():
    graph, source = fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    for change in (lambda g: g["nodes"][2].update(code="WRONG"),
                   lambda g: g["edges"].pop(),
                   lambda g: g["nodes"][0].pop("evidence"),
                   lambda g: g["edges"][0]["evidence"].update(edition_id="other")):
        altered = deepcopy(bound)
        change(altered)
        with pytest.raises(ValueError):
            validate_a1_graph_evidence(altered, expected_source=source)
    with pytest.raises(ValueError):
        validate_a1_graph_evidence(bound, expected_source=dict(source, edition_id="wrong"))


def test_invalid_regions_fail_closed_and_source_change_changes_record_evidence():
    graph, source = fixture()
    bound = bind_a1_graph_evidence(graph, **source)
    changed = bind_a1_graph_evidence(graph, **dict(source, asset_sha256="c" * 64))
    assert changed["nodes"][0]["evidence"]["evidence_id"] != bound["nodes"][0]["evidence"]["evidence_id"]
    graph["edges"][0]["region"] = [0.3, 0.1, 0.2, 0.2]
    with pytest.raises(ValueError):
        bind_a1_graph_evidence(graph, **source)
