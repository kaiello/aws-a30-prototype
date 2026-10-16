"""Synthetic answer-assessment contracts; no database, model or source content."""
import ast
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set

import pytest


ROOT = Path(__file__).resolve().parents[1]
TRUTH_STATUSES = {"VERIFIED_GROUNDED", "SUPPORTED_REVIEWED_FACTS", "TRUTHFUL_ABSTENTION"}
EMPTY_CITATIONS = {"figures": [], "tables": [], "clauses": [], "unresolved_elements": []}


class FakeCursor:
    def __init__(self, nodes, bridges):
        self.nodes, self.bridges, self.rows = nodes, bridges, []

    def execute(self, sql, parameters=()):
        if "FROM grounding_bridges" in sql:
            self.rows = self.bridges
        elif "ontology_fts" in sql:
            self.rows = []
        elif "FROM ontology_nodes" in sql:
            self.rows = self.nodes
        else:
            raise AssertionError("Unexpected synthetic SQL")

    def fetchall(self):
        return deepcopy(self.rows)

    def fetchone(self):
        return deepcopy(self.rows[0]) if self.rows else None


def fixture_namespace(*, nodes=(), bridges=(), exists=True, citations=None):
    connections = []

    def connect(path):
        assert exists, "An absent fixture database must not be opened"
        connections.append(path)
        cursor = FakeCursor(list(nodes), list(bridges))
        return SimpleNamespace(cursor=lambda: cursor, close=lambda: None)

    return dict(
        __name__="answer_assessment_fixture", re=re, hashlib=hashlib,
        Any=Any, Dict=Dict, List=List, Optional=Optional, Set=Set,
        dataclass=dataclass, field=field, asdict=asdict,
        DUAL_SQLITE_PATH=SimpleNamespace(exists=lambda: exists),
        sqlite3=SimpleNamespace(connect=connect, OperationalError=RuntimeError),
        check_abstention=lambda answer: "outside scope" in answer.lower(),
        extract_citations=lambda answer: deepcopy(citations or EMPTY_CITATIONS),
    ), connections


def load_definitions(filename, names, namespace):
    tree = ast.parse((ROOT / "src" / filename).read_text(encoding="utf-8"))
    nodes = [node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, "exec"), namespace)
    return namespace


def verifier_fixture(**kwargs):
    namespace, connections = fixture_namespace(**kwargs)
    load_definitions("epistemic_verifier.py", {"_decision_status", "verify_epistemic_provenance"}, namespace)
    return namespace["verify_epistemic_provenance"], connections


def route_fixture(**kwargs):
    namespace, connections = fixture_namespace(**kwargs)
    load_definitions("epistemic_verifier.py", {"_decision_status"}, namespace)

    def source_metadata(item):
        item.metadata["source_location_verification"] = "verified"
        item.metadata["source_anchors"] = [{"source_id": "doc:synthetic", "pdf_index": 7}]

    namespace["_apply_source_metadata"] = source_metadata
    load_definitions("answer_routes.py",
                     {"EvidenceItem", "AnswerRoute", "_clean_term_for_fts", "resolve_answer_route"}, namespace)
    return namespace["resolve_answer_route"], namespace["AnswerRoute"], connections


def assert_unassessed(result):
    assert result["epistemic_status"] not in TRUTH_STATUSES
    assert result["assessment_status"] == "UNASSESSED"
    assert result["provenance_score"] is None


@pytest.mark.parametrize("answer", ["", "No known fixture concept occurs here.", "A made-up claim is correct."])
def test_zero_matching_concepts_has_no_truth_score_or_vacuous_coverage(answer):
    verify, _ = verifier_fixture()
    result = verify("A synthetic question", answer)
    assert_unassessed(result)
    assert result["graph_link_coverage"] is None
    assert result["total_concepts_evaluated"] == 0


@pytest.mark.parametrize("answer", [
    "Fixture alpha always has a fabricated property.",
    "Fixture alpha contradicts its supplied definition.",
])
def test_generic_graph_bridge_reports_links_without_certifying_claims(answer):
    verify, _ = verifier_fixture(
        nodes=[("onto:alpha", "fixture alpha", "Concept", "standard")],
        bridges=[("DEFINED_IN", "text_definition", "TextChunk", "Generic fixture context", "7", "")])
    result = verify("Define fixture alpha", answer)
    assert_unassessed(result)
    assert result["epistemic_status"] == "EVIDENCE_LINKS_FOUND"
    assert result["graph_link_coverage"] == 1.0
    assert result["concepts_verified"][0]["concept"] == "fixture alpha"  # Legacy navigation key.


def test_existing_citation_identity_does_not_assess_its_claim():
    citations = dict(EMPTY_CITATIONS, figures=["Figure B1"])
    verify, _ = verifier_fixture(citations=citations)
    result = verify("A synthetic question", "An unsupported assertion cites Figure B1.")
    assert_unassessed(result)
    assert result["evidence_summary"]["figures"] == ["Figure B1"]
    assert result["graph_link_coverage"] is None


def test_unresolved_citation_cannot_be_promoted_by_a_generic_bridge():
    citations = dict(EMPTY_CITATIONS, unresolved_elements=[
        {"text": "Figure B120", "status": "unknown", "candidates": []}])
    verify, _ = verifier_fixture(
        nodes=[("onto:alpha", "fixture alpha", "Concept", "standard")],
        bridges=[("DEFINED_IN", "text_definition", "TextChunk", "Unrelated context", "7", "")],
        citations=citations)
    assert_unassessed(verify("Define fixture alpha", "Fixture alpha appears in Figure B120."))


def test_missing_database_is_unassessed_without_a_connection():
    verify, connections = verifier_fixture(exists=False)
    result = verify("Define fixture alpha", "Fixture alpha has a property.")
    assert_unassessed(result)
    assert result["graph_link_coverage"] is None
    assert connections == []


@pytest.mark.parametrize("answer", [
    "This is outside scope.",
    "This is outside scope, but fixture alpha always requires 900 fictional units.",
])
def test_abstention_phrase_alone_does_not_establish_a_truthful_scope_decision(answer):
    verify, _ = verifier_fixture()
    result = verify("An answerable synthetic question", answer)
    assert_unassessed(result)
    assert result["is_abstention"] is False


def test_route_defaults_never_claim_measured_recall_or_complete_recovery():
    _, route_class, _ = route_fixture()
    result = route_class(query="Synthetic question", status="UNASSESSED").to_dict()
    assert result["evidence_recall_score"] is None
    assert result["epistemic_score"] is None
    assert result["all_evidence_recovered"] is False
    assert result["assessment_status"] == "UNASSESSED"


@pytest.mark.parametrize("exists", [False, True])
def test_missing_or_unmatched_route_does_not_invent_evidence_success(exists):
    resolve, _, connections = route_fixture(exists=exists)
    result = resolve("Unmatched synthetic question", "Unassessed synthetic answer").to_dict()
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment_status"] == "UNASSESSED"
    assert result["evidence_recall_score"] is None
    assert result["epistemic_score"] is None
    assert result["all_evidence_recovered"] is False
    if not exists:
        assert connections == []


@pytest.mark.parametrize("query", ["Show fixture alpha diagram", "Show fixture alpha table and diagram"])
def test_incomplete_figure_table_navigation_stays_insufficient(query):
    resolve, _, _ = route_fixture(
        nodes=[("onto:alpha", "fixture alpha", "Concept", "standard", "Synthetic description")],
        bridges=[("DEFINED_IN", "text_definition", "chunk:fixture", "TextChunk", "Fixture text", "7", "", "Preview")])
    result = resolve(query, "Fixture alpha has an unsupported property.").to_dict()
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment_status"] == "UNASSESSED"
    assert result["all_evidence_recovered"] is False
    assert result["evidence_recall_score"] is None
    assert result["epistemic_score"] is None


def test_complete_evidence_categories_are_navigation_not_claim_entailment():
    resolve, _, _ = route_fixture(
        nodes=[("onto:alpha", "fixture alpha", "Concept", "standard", "Synthetic description")],
        bridges=[
            ("ILLUSTRATED_BY", "figure_reference", "figure:fixture", "Figure", "Figure B1", "7", "fixture.png", ""),
            ("TABULATED_IN", "table_matrix", "table:fixture", "Table", "Table A1", "8", "", "")])
    result = resolve("Show fixture alpha table and diagram", "Fixture alpha is always a fabricated value.").to_dict()
    assert result["status"] == "EVIDENCE_LINKS_FOUND"
    assert result["assessment_status"] == "UNASSESSED"
    assert result["all_evidence_recovered"] is False
    assert result["evidence_recall_score"] is None
    assert result["epistemic_score"] is None
    assert [item["element_id"] for item in result["evidence_group"]] == ["Figure B1", "Table A1"]


def test_route_abstention_substring_does_not_create_truthful_success():
    resolve, _, _ = route_fixture(exists=False)
    result = resolve("An answerable question", "Outside scope, but a fabricated requirement applies.").to_dict()
    assert result["status"] not in TRUTH_STATUSES
    assert result["assessment_status"] == "UNASSESSED"
    assert result["all_evidence_recovered"] is False
    assert result["evidence_recall_score"] is None
    assert result["epistemic_score"] is None


def test_unresolved_route_citation_stays_insufficient_despite_existing_figure_link():
    citations = dict(EMPTY_CITATIONS, unresolved_elements=[
        {"text": "Figure B120", "status": "unknown", "candidates": []}])
    resolve, _, _ = route_fixture(
        nodes=[("onto:alpha", "fixture alpha", "Concept", "standard", "Synthetic description")],
        bridges=[("ILLUSTRATED_BY", "figure_reference", "figure:fixture", "Figure", "Figure B1", "7", "fixture.png", "")],
        citations=citations)
    result = resolve("Show fixture alpha diagram", "Fixture alpha requires Figure B120.").to_dict()
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessment_status"] == "UNASSESSED"
    assert result["all_evidence_recovered"] is False
    assert result["evidence_recall_score"] is None and result["epistemic_score"] is None


@pytest.mark.parametrize("status,scope", [
    ("SUPPORTED_REVIEWED_FACTS", "reviewed_fact_bindings"),
    ("TRUTHFUL_ABSTENTION", "deterministic_scope_policy"),
])
def test_only_validated_answer_bound_decision_can_assess_without_database(status, scope):
    answer = "A synthetic policy-controlled response."
    decision = {"status": status, "validated": True,
                "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                "assessment_scope": scope}
    verify, verifier_connections = verifier_fixture(exists=False)
    result = verify("Synthetic question", answer, decision=decision)
    assert result["epistemic_status"] == status
    assert result["assessment_status"] == status
    assert result["is_abstention"] is (status == "TRUTHFUL_ABSTENTION")
    assert result["provenance_score"] is None
    assert result["graph_link_coverage"] is None
    assert verifier_connections == []
    resolve, _, route_connections = route_fixture(exists=False)
    route = resolve("Synthetic question", answer, decision=decision).to_dict()
    assert route["status"] == status and route["assessment_status"] == status
    assert route["all_evidence_recovered"] is False
    assert route["evidence_recall_score"] is None and route["epistemic_score"] is None
    assert route_connections == []


@pytest.mark.parametrize("mutation", ["not-validated", "truthy-integer", "wrong-answer", "wrong-scope", "unknown-status"])
def test_invalid_or_unbound_decision_cannot_promote_an_answer(mutation):
    answer = "A synthetic response."
    decision = {"status": "SUPPORTED_REVIEWED_FACTS", "validated": True,
                "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                "assessment_scope": "reviewed_fact_bindings"}
    if mutation == "not-validated":
        decision["validated"] = False
    elif mutation == "truthy-integer":
        decision["validated"] = 1
    elif mutation == "wrong-answer":
        decision["answer_sha256"] = "0" * 64
    elif mutation == "wrong-scope":
        decision["assessment_scope"] = "deterministic_scope_policy"
    else:
        decision["status"] = "VERIFIED_GROUNDED"
    verify, _ = verifier_fixture(exists=False)
    assert_unassessed(verify("Synthetic question", answer, decision=decision))
    resolve, _, _ = route_fixture(exists=False)
    result = resolve("Synthetic question", answer, decision=decision).to_dict()
    assert result["status"] not in TRUTH_STATUSES
    assert result["assessment_status"] == "UNASSESSED"
    assert result["all_evidence_recovered"] is False
