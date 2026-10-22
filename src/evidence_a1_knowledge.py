"""Persisted A1 observations and deterministic, qualified assertion admission.

The canonical caller authenticates source/image bytes before preparing this
store. No model, reviewed semantics, registry rewrite or arbitrary SQL API is
introduced. The runtime database is a versioned backup of the existing spine.
"""
from copy import deepcopy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3

from src.evidence_a1 import validate_a1_graph_evidence

SCHEMA_VERSION = "a1-epistemic-1.0"
RUNTIME_RELPATH = "storage/evidence_v2/a1_epistemic_002/registry.db"
PREDICATES = {"PRINTED_LABEL", "PRINTED_DESIGNATION", "CHART_MEMBER_OF", "CHART_CONNECTED",
              "CANDIDATE_LAYOUT_PARENT", "IS_A"}
FUNCTIONAL = {"PRINTED_DESIGNATION", "CHART_MEMBER_OF"}
RULES = {
    "literal-record-1": "Accept the printed label/designation from its bound source observation only.",
    "source-layout-1": "Accept scoped rectangle membership or physical connection, not semantic subtype.",
    "candidate-source-relation-1": "The bound source relation remains candidate; it does not meet source-bound admission.",
    "candidate-layout-1": "Indentation remains a candidate displayed parent; never accepted IS_A.",
    "functional-conflict-1": "Contrary observed values for one functional fact in one scope dispute all alternatives.",
    "semantic-proposal-1": "A geometry-supported IS_A proposal is candidate only; no human review is invented.",
}
TABLES = ("a1k_source_meta", "a1k_source_observations", "a1k_domain_concepts",
          "a1k_typed_assertions", "a1k_assertion_evidence")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _error(code):
    raise ValueError("A1_KNOWLEDGE_" + code)


def _safe_path(root, path):
    if not path.resolve().is_relative_to(root):
        _error("PATH_OUTSIDE_ROOT")
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            _error("LINKED_RUNTIME_PATH")


@contextmanager
def _connect(path, *, write=False):
    connection = sqlite3.connect(path.resolve().as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        with connection:
            yield connection
    finally:
        connection.close()


def _meta(connection):
    return {key: json.loads(value) for key, value in connection.execute("SELECT key,value_json FROM a1k_source_meta")}


def _integrity(connection):
    # Only fixed, owned table names enter SQL; caller data is always a parameter.
    rows = {table: connection.execute("SELECT * FROM " + table + " ORDER BY 1,2").fetchall()
            for table in TABLES if table != "a1k_source_meta"}
    rows["a1k_source_meta"] = connection.execute(
        "SELECT key,value_json FROM a1k_source_meta WHERE key!='integrity_sha256' ORDER BY key").fetchall()
    rows["schema"] = connection.execute(
        "SELECT name,type,sql FROM sqlite_master WHERE name LIKE 'a1k_%' ORDER BY name").fetchall()
    return _digest(rows)


def _seal(connection):
    connection.execute("INSERT OR REPLACE INTO a1k_source_meta VALUES (?,?)", ("integrity_sha256", _json(_integrity(connection))))


def _source_graph(connection):
    graph = _meta(connection)["graph_template"]
    for kind, key in (("node", "nodes"), ("edge", "edges")):
        graph[key] = [json.loads(row[0]) for row in connection.execute(
            "SELECT payload_json FROM a1k_source_observations WHERE record_kind=? ORDER BY ordinal", (kind,))]
    return graph


def _assertions(connection):
    results = []
    for (payload,) in connection.execute("SELECT payload_json FROM a1k_typed_assertions ORDER BY assertion_id"):
        record = json.loads(payload)
        links = connection.execute("SELECT role,evidence_id FROM a1k_assertion_evidence WHERE assertion_id=? ORDER BY role,evidence_id",
                                   (record["assertion_id"],)).fetchall()
        record["support_evidence_ids"] = [evidence for role, evidence in links if role == "support"]
        record["counter_evidence_ids"] = [evidence for role, evidence in links if role == "counter"]
        results.append(record)
    return results


def _insert_assertion(connection, record):
    record = deepcopy(record)
    links = [(record["assertion_id"], evidence, role) for role in ("support", "counter")
             for evidence in record.pop(role + "_evidence_ids")]
    connection.execute("INSERT INTO a1k_typed_assertions VALUES (?,?)", (record["assertion_id"], _json(record)))
    connection.executemany("INSERT INTO a1k_assertion_evidence VALUES (?,?,?)", links)


def _admit(graph):
    binding = graph["source_binding"]
    family = binding["edition_id"].split("@", 1)[0]
    scope = {**binding, "native_graph_sha256": graph["native_graph_sha256"]}
    concepts, node_concepts, assertions = {}, {}, {}
    records = {record["id"]: record for record in graph["nodes"] + graph["edges"]}
    for node in graph["nodes"]:
        label_key = " ".join(node["label"].casefold().split())
        concept = "a1concept:" + _digest([family, node["kind"], label_key])
        node_concepts[node["id"]] = concept
        concepts.setdefault(concept, {"concept_id": concept, "document_family": family,
            "kind": node["kind"], "label_key": label_key,
            "identity_qualification": "Exact normalized lexical identity within a document family; no reviewed cross-edition or semantic equivalence.",
            "codes": []})
        if node.get("code") and node["code"] not in concepts[concept]["codes"]:
            concepts[concept]["codes"].append(node["code"])

    def add(subject, predicate, value, origin, supports, status, rule):
        identifier = "a1assertion:" + _digest([subject, predicate, value, scope])
        assertion = assertions.setdefault(identifier, {"assertion_id": identifier, "predicate": predicate,
            "subject_id": subject, "object_value": value, "status": status, "rule_id": rule,
            "admission_reason": RULES[rule], "scope": scope, "origin_record_ids": [],
            "support_evidence_ids": [], "counter_evidence_ids": []})
        assertion["origin_record_ids"] = sorted(set(assertion["origin_record_ids"]) | {origin})
        assertion["support_evidence_ids"] = sorted(set(assertion["support_evidence_ids"]) |
            {records[record]["evidence"]["evidence_id"] for record in supports})

    for node in graph["nodes"]:
        concept = node_concepts[node["id"]]
        add(concept, "PRINTED_LABEL", node["label"], node["id"], [node["id"]], "ACCEPTED", "literal-record-1")
        if node.get("code"):
            add(concept, "PRINTED_DESIGNATION", node["code"], node["id"], [node["id"]], "ACCEPTED", "literal-record-1")
    for edge in graph["edges"]:
        parent, child = node_concepts[edge["from"]], node_concepts[edge["to"]]
        if edge["type"] == "ENCLOSES_ROW":
            subject, predicate, value, status, rule = child, "CHART_MEMBER_OF", parent, "ACCEPTED", "source-layout-1"
        elif edge["type"] == "CHART_CONNECTOR":
            subject, predicate, value, status, rule = parent, "CHART_CONNECTED", child, "ACCEPTED", "source-layout-1"
        else:
            subject, predicate, value, status, rule = child, "CANDIDATE_LAYOUT_PARENT", parent, "CANDIDATE", "candidate-layout-1"
        if edge["type"] in {"ENCLOSES_ROW", "CHART_CONNECTOR"} and edge["evidence"]["verification"] != "source_bound":
            status, rule = "CANDIDATE", "candidate-source-relation-1"
        add(subject, predicate, value, edge["id"], [edge["id"], edge["from"], edge["to"]], status, rule)
    groups = {}
    for assertion in assertions.values():
        if assertion["predicate"] in FUNCTIONAL:
            groups.setdefault((assertion["subject_id"], assertion["predicate"]), []).append(assertion)
    for alternatives in groups.values():
        if len({item["object_value"] for item in alternatives}) < 2:
            continue
        for assertion in alternatives:
            assertion.update(status="DISPUTED", rule_id="functional-conflict-1", admission_reason=RULES["functional-conflict-1"])
            assertion["counter_evidence_ids"] = sorted({records[origin]["evidence"]["evidence_id"]
                for other in alternatives if other["object_value"] != assertion["object_value"]
                for origin in other["origin_record_ids"]})
    return concepts, node_concepts, list(assertions.values())


def _proposal_record(graph, subject_id, predicate, object_value, support_evidence_ids, counter_evidence_ids):
    if predicate not in PREDICATES:
        _error("PREDICATE_UNSUPPORTED")
    if predicate != "IS_A":
        _error("LITERAL_FACTS_REQUIRE_OBSERVATION_ADMISSION")
    nodes = {node["id"]: node for node in graph["nodes"]}
    if subject_id not in nodes or object_value not in nodes or subject_id == object_value:
        _error("PROPOSAL_ENDPOINT_INVALID")
    relevant = [edge for edge in graph["edges"] if edge["type"] == "INDENTED_UNDER"
                and edge["from"] == object_value and edge["to"] == subject_id]
    evidence = {edge["evidence"]["evidence_id"] for edge in relevant}
    if not support_evidence_ids or not set(support_evidence_ids) <= evidence:
        _error("PROPOSAL_SUPPORT_NOT_RELEVANT_GEOMETRY")
    if counter_evidence_ids:
        _error("SEMANTIC_COUNTEREVIDENCE_NOT_ESTABLISHED_BY_GEOMETRY")
    _, concepts, _ = _admit(graph)
    scope = {**graph["source_binding"], "native_graph_sha256": graph["native_graph_sha256"]}
    identifier = "a1assertion:" + _digest([concepts[subject_id], predicate, concepts[object_value], scope])
    supports = set(support_evidence_ids) | {nodes[node]["evidence"]["evidence_id"] for node in (subject_id, object_value)}
    return {"assertion_id": identifier, "predicate": predicate, "subject_id": concepts[subject_id],
        "object_value": concepts[object_value], "status": "CANDIDATE", "rule_id": "semantic-proposal-1",
        "admission_reason": RULES["semantic-proposal-1"], "scope": scope,
        "origin_record_ids": sorted(edge["id"] for edge in relevant if edge["evidence"]["evidence_id"] in support_evidence_ids),
        "support_evidence_ids": sorted(supports), "counter_evidence_ids": []}


def _validate_admission(connection, metadata, graph, assertions, concepts):
    """Recompute admission, rather than treating a resealable hash as authority."""
    expected_concepts, expected_bindings, baseline = _admit(graph)
    actual = {item["assertion_id"]: item for item in assertions}
    if (metadata.get("admission_rules") != RULES or metadata.get("node_concepts") != expected_bindings
            or {item["concept_id"]: item for item in concepts} != expected_concepts
            or len(actual) != len(assertions)):
        _error("ADMISSION_INVALID")
    for expected in baseline:
        if actual.pop(expected["assertion_id"], None) != expected:
            _error("ADMISSION_INVALID")
    edges = {edge["id"]: edge for edge in graph["edges"]}
    for proposal in actual.values():
        try:
            origins = [edges[identifier] for identifier in proposal["origin_record_ids"]]
            if not origins:
                _error("ADMISSION_INVALID")
            expected = _proposal_record(graph, origins[0]["to"], proposal["predicate"], origins[0]["from"],
                [edge["evidence"]["evidence_id"] for edge in origins], proposal["counter_evidence_ids"])
            if proposal != expected:
                _error("ADMISSION_INVALID")
        except (ValueError, KeyError, TypeError):
            _error("ADMISSION_INVALID")
    expected_links = sorted((item["assertion_id"], evidence, role) for item in assertions
        for role in ("support", "counter") for evidence in item[role + "_evidence_ids"])
    stored_links = connection.execute("SELECT assertion_id,evidence_id,role FROM a1k_assertion_evidence ORDER BY 1,2,3").fetchall()
    if stored_links != expected_links:
        _error("ADMISSION_INVALID")


class A1KnowledgeStore:
    def __init__(self, root, path, fingerprint):
        self.root, self.path, self.fingerprint = root, path, fingerprint

    def _read(self):
        _safe_path(self.root, self.path)
        try:
            with _connect(self.path) as connection:
                metadata = _meta(connection)
                if metadata.get("schema_version") != SCHEMA_VERSION or metadata.get("integrity_sha256") != _integrity(connection):
                    _error("STORE_TAMPERED")
                if metadata.get("source_graph_sha256") != self.fingerprint:
                    _error("SOURCE_CHANGED")
                graph = _source_graph(connection)
                validate_a1_graph_evidence(graph, require_complete=True)
                if _digest(graph) != self.fingerprint:
                    _error("STORE_TAMPERED")
                assertions = _assertions(connection)
                concepts = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM a1k_domain_concepts ORDER BY concept_id")]
                _validate_admission(connection, metadata, graph, assertions, concepts)
            return metadata, graph, assertions, concepts
        except (sqlite3.Error, KeyError, TypeError, json.JSONDecodeError):
            _error("STORE_TAMPERED")

    def graph(self, layer="evidence"):
        metadata, graph, assertions, _ = self._read()
        if layer == "evidence":
            return graph
        if layer != "knowledge":
            _error("LAYER_INVALID")
        accepted = [item for item in assertions if item["status"] == "ACCEPTED"]
        accepted_origins = {origin for item in accepted for origin in item["origin_record_ids"]}
        graph["edges"] = [edge for edge in graph["edges"] if edge["id"] in accepted_origins]
        graph.update(derived_layer="knowledge", accepted_assertions=accepted,
            concept_bindings=metadata["node_concepts"], assertion_bindings={
                record["id"]: [item["assertion_id"] for item in accepted if record["id"] in item["origin_record_ids"]]
                for record in graph["nodes"] + graph["edges"]},
            selection={"method": "persisted_accepted_assertions_only", "status": "derived_knowledge_projection",
                "qualification": "Source records remain unchanged; predicates are admitted chart facts, not reviewed semantic taxonomy."})
        validate_a1_graph_evidence(graph, require_complete=False)
        return graph

    def describe(self):
        metadata, graph, assertions, concepts = self._read()
        return {"schema_version": SCHEMA_VERSION, "runtime_relpath": RUNTIME_RELPATH,
            "source_binding": graph["source_binding"], "native_graph_sha256": graph["native_graph_sha256"],
            "source_graph_sha256": self.fingerprint, "source_observation_count": len(graph["nodes"]) + len(graph["edges"]),
            "concept_count": len(concepts), "assertion_count": len(assertions),
            "assertion_status_counts": {status: sum(item["status"] == status for item in assertions)
                                        for status in ("ACCEPTED", "CANDIDATE", "DISPUTED")},
            "registry_source_sha256": metadata["registry_source_sha256"], "admission_rules": RULES,
            "source_authentication": "caller_must_authenticate_canonical_source", "semantic_validation": False}

    def support_for(self, record_ids=(), evidence_ids=(), assertion_ids=()):
        _, graph, assertions, _ = self._read()
        records = {record["id"]: record for record in graph["nodes"] + graph["edges"]}
        by_evidence = {record["evidence"]["evidence_id"]: record for record in records.values()}
        wanted_records, wanted_evidence, wanted_assertions = set(record_ids), set(evidence_ids), set(assertion_ids)
        if (not wanted_records <= records.keys() or not wanted_evidence <= by_evidence.keys()
                or not wanted_assertions <= {item["assertion_id"] for item in assertions}):
            _error("SUPPORT_REFERENCE_UNKNOWN")
        selected = [item for item in assertions if item["assertion_id"] in wanted_assertions
            or wanted_records.intersection(item["origin_record_ids"])
            or wanted_evidence.intersection(item["support_evidence_ids"] + item["counter_evidence_ids"])]
        closure = wanted_evidence | {evidence for item in selected for key in ("support_evidence_ids", "counter_evidence_ids") for evidence in item[key]}
        closure.update(records[identifier]["evidence"]["evidence_id"] for identifier in wanted_records)
        for evidence in list(closure):
            record = by_evidence[evidence]
            if record["evidence"]["record_kind"] == "edge":
                closure.update(records[record[key]]["evidence"]["evidence_id"] for key in ("from", "to"))
        observations = [{"record_id": record["id"], "observation": record, "proof": record["evidence"]}
                        for record in records.values() if record["evidence"]["evidence_id"] in closure]
        return {"assertions": selected, "observations": observations, "missing_evidence_ids": [],
                "source_authentication": "caller_must_authenticate_canonical_source", "semantic_validation": False}

    def propose(self, subject_id, predicate, object_value, *, support_evidence_ids=(), counter_evidence_ids=()):
        _, graph, assertions, _ = self._read()
        record = _proposal_record(graph, subject_id, predicate, object_value, support_evidence_ids, counter_evidence_ids)
        old = next((item for item in assertions if item["assertion_id"] == record["assertion_id"]), None)
        if old:
            return old
        with _connect(self.path, write=True) as connection:
            # Recheck the seal under the write transaction; never overwrite a
            # changed/corrupted runtime after the read above.
            connection.execute("BEGIN IMMEDIATE")
            if _meta(connection)["integrity_sha256"] != _integrity(connection):
                _error("STORE_TAMPERED")
            _insert_assertion(connection, record)
            _seal(connection)
        return record


def prepare_a1_knowledge(root, graph):
    """Create once, or validate the existing versioned runtime without rebuilding."""
    validate_a1_graph_evidence(graph, require_complete=True)
    from src.evidence_a1_graph_qa import _graph_index
    _graph_index(graph)
    root = Path(root).resolve(strict=True)
    source, target = root / "storage/dual_layer_registry.db", root / RUNTIME_RELPATH
    _safe_path(root, source)
    _safe_path(root, target)
    if not source.is_file():
        _error("SOURCE_REGISTRY_MISSING")
    fingerprint = _digest(graph)
    store = A1KnowledgeStore(root, target, fingerprint)
    if target.exists():
        metadata, _, _, _ = store._read()
        if metadata["registry_source_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest():
            _error("REGISTRY_SOURCE_CHANGED")
        return store
    target.parent.mkdir(parents=True, exist_ok=True)
    _safe_path(root, target)
    with target.open("xb"):
        pass
    with _connect(source) as original, _connect(target, write=True) as connection:
        original.backup(connection)
        if connection.execute("SELECT name FROM sqlite_master WHERE name LIKE 'a1k_%'").fetchone():
            _error("NAMESPACE_ALREADY_PRESENT")
        connection.executescript("""
            CREATE TABLE a1k_source_meta(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);
            CREATE TABLE a1k_source_observations(record_id TEXT PRIMARY KEY,evidence_id TEXT UNIQUE NOT NULL,
                record_kind TEXT NOT NULL CHECK(record_kind IN ('node','edge')),ordinal INTEGER NOT NULL,payload_json TEXT NOT NULL);
            CREATE TABLE a1k_domain_concepts(concept_id TEXT PRIMARY KEY,payload_json TEXT NOT NULL);
            CREATE TABLE a1k_typed_assertions(assertion_id TEXT PRIMARY KEY,payload_json TEXT NOT NULL);
            CREATE TABLE a1k_assertion_evidence(assertion_id TEXT NOT NULL REFERENCES a1k_typed_assertions(assertion_id),
                evidence_id TEXT NOT NULL REFERENCES a1k_source_observations(evidence_id),
                role TEXT NOT NULL CHECK(role IN ('support','counter')),PRIMARY KEY(assertion_id,evidence_id,role));
        """)
        template = deepcopy(graph)
        template["nodes"], template["edges"] = [], []
        concepts, node_concepts, assertions = _admit(graph)
        metadata = {"schema_version": SCHEMA_VERSION, "source_graph_sha256": fingerprint,
            "registry_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "graph_template": template, "node_concepts": node_concepts, "admission_rules": RULES}
        connection.executemany("INSERT INTO a1k_source_meta VALUES (?,?)", [(key, _json(value)) for key, value in metadata.items()])
        for kind, records in (("node", graph["nodes"]), ("edge", graph["edges"])):
            connection.executemany("INSERT INTO a1k_source_observations VALUES (?,?,?,?,?)",
                [(record["id"], record["evidence"]["evidence_id"], kind, ordinal, _json(record)) for ordinal, record in enumerate(records)])
        connection.executemany("INSERT INTO a1k_domain_concepts VALUES (?,?)", [(key, _json(value)) for key, value in concepts.items()])
        for assertion in assertions:
            _insert_assertion(connection, assertion)
        _seal(connection)
    store._read()
    return store
