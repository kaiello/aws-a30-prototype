"""Deterministic questions over the unchanged, source-bound single-image graph.

This is an explicit graph QA path, not LLM evaluation. No source vocabulary,
question IDs, expected verdicts or process/code answers are embedded here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time

from src.evidence_a1 import load_a1_evidence
from src.evidence_reader import build_messages
from src.evidence_v2 import EvidenceStore, EvidencePacket, RoutePlan
from src.evidence_a1_planner import plan_graph_query
from src.evidence_a1 import a1_source_identity_id

HARNESS_VERSION = "a1-graph-qa-1.4.0"
RELATIONS = {"CHART_CONNECTOR", "ENCLOSES_ROW", "INDENTED_UNDER"}


def _graph_index(graph):
    if not isinstance(graph, dict) or graph.get("schema_version") != "a1-geometry-1.0":
        raise ValueError("GRAPH_QA_SCHEMA_INVALID")
    nodes, edges, qualifications = graph.get("nodes"), graph.get("edges"), graph.get("edge_qualifications")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(qualifications, dict):
        raise ValueError("GRAPH_QA_RECORDS_INVALID")
    by_id = {}
    for node in nodes:
        if (not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]
                or node["id"] in by_id or node.get("kind") not in {"root", "category", "process"}
                or not isinstance(node.get("label"), str) or not node["label"].strip()
                or (node["kind"] == "process" and not isinstance(node.get("code"), str))):
            raise ValueError("GRAPH_QA_NODE_INVALID")
        by_id[node["id"]] = node
    if graph.get("root_id") not in by_id or by_id[graph["root_id"]]["kind"] != "root":
        raise ValueError("GRAPH_QA_ROOT_INVALID")
    outgoing, incoming, seen_edges = {}, {}, set()
    for edge in edges:
        key = (edge.get("from"), edge.get("to"), edge.get("type"))
        qualification = qualifications.get(edge.get("type"), {})
        if (key[0] not in by_id or key[1] not in by_id or key[2] not in RELATIONS
                or key in seen_edges or not qualification.get("qualification")
                or qualification.get("verification") not in {"source_bound", "candidate", "synthetic"}
                or (key[2] == "INDENTED_UNDER" and qualification["verification"] != "candidate")):
            raise ValueError("GRAPH_QA_EDGE_INVALID")
        expected = {"CHART_CONNECTOR": ("root", "category"),
                    "ENCLOSES_ROW": ("category", "process"),
                    "INDENTED_UNDER": ("process", "process")}[key[2]]
        if (by_id[key[0]]["kind"], by_id[key[1]]["kind"]) != expected:
            raise ValueError("GRAPH_QA_EDGE_KINDS_INVALID")
        seen_edges.add(key)
        outgoing.setdefault(key[0], []).append(edge)
        incoming.setdefault(key[1], []).append(edge)
    active, visited = set(), set()

    def visit(identifier):
        if identifier in active:
            raise ValueError("GRAPH_QA_DIRECTED_CYCLE")
        if identifier in visited:
            return
        active.add(identifier)
        for edge in outgoing.get(identifier, []):
            visit(edge["to"])
        active.remove(identifier)
        visited.add(identifier)

    for identifier in by_id:
        visit(identifier)
    return by_id, outgoing, incoming


def _category_name(node):
    matched = re.fullmatch(r"(.*?)\s*\(([A-Z]+(?:-[A-Z]+)?)\)\s*", node["label"])
    return (matched[1].strip(), matched[2]) if matched else (node["label"], None)


def _closure(seeds, adjacency, direction):
    pending, visited, traversed = list(seeds), set(), []
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for edge in adjacency.get(current, []):
            traversed.append(edge)
            pending.append(edge["to"] if direction == "outbound" else edge["from"])
    return visited, traversed


def _source_order(node):
    region = node.get("region", [])
    return (region[0], region[1], node["id"]) if len(region) == 4 else (0, 0, node["id"])


class _GraphView:
    def __init__(self, graph):
        self.graph = graph
        self.nodes, self.outgoing, self.incoming = _graph_index(graph)
        self.source_receipt = None
        if ("source_binding" in graph or "record_evidence_schema_version" in graph
                or any("evidence" in record for record in graph["nodes"] + graph["edges"])):
            # Declared record identity is checked, but does not authenticate the
            # caller's source image. Only the canonical wrapper checks that file.
            from src.evidence_a1 import validate_a1_graph_evidence
            self.source_receipt = validate_a1_graph_evidence(graph,
                require_complete=graph.get("derived_layer") != "knowledge")

    def families(self, identifier):
        return sorted({edge["from"] for edge in self.incoming.get(identifier, []) if edge["type"] == "ENCLOSES_ROW"})

    def row(self, identifier):
        node = self.nodes[identifier]
        families = self.families(identifier)
        return dict(node, family_id=families[0] if len(families) == 1 else None,
                    family_ids=families, indent_parent_ids=sorted({edge["from"] for edge in self.incoming.get(identifier, [])
                        if edge["type"] == "INDENTED_UNDER"}), indent_parent_verification="candidate")

    def ancestors(self, identifiers):
        return _closure(identifiers, self.incoming, "inbound")

    def layout_parents(self, identifier):
        incoming = self.incoming.get(identifier, [])
        if self.nodes[identifier]["kind"] == "process":
            indents = [edge for edge in incoming if edge["type"] == "INDENTED_UNDER"]
            return indents or [edge for edge in incoming if edge["type"] == "ENCLOSES_ROW"]
        return [edge for edge in incoming if edge["type"] == "CHART_CONNECTOR"]

    def children(self, identifier):
        return [edge for edge in self.graph["edges"] if edge["from"] == identifier
                and edge in self.layout_parents(edge["to"])]

    def descendants(self, identifiers, direct=False):
        pending, visited, traversed = list(identifiers), set(identifiers), []
        while pending:
            parent = pending.pop()
            for edge in self.children(parent):
                traversed.append(edge)
                if edge["to"] not in visited:
                    visited.add(edge["to"])
                    if not direct:
                        pending.append(edge["to"])
        return visited, traversed

    def paths(self, identifier):
        root = self.graph["root_id"]
        def ascend(current):
            if current == root:
                return [([root], [])]
            found = []
            for edge in self.layout_parents(current):
                for nodes, edges in ascend(edge["from"]):
                    found.append((nodes + [current], edges + [edge]))
                    if len(found) > 4096:
                        raise ValueError("GRAPH_QA_PATH_BUDGET_EXCEEDED")
            return found
        return [{"target_id": identifier, "node_ids": nodes, "edges": edges,
                 "edge_types": [edge["type"] for edge in edges],
                 "qualification": "Ordered chart path; physical connector/enclosure and candidate indentation, not reviewed semantic IS_A."}
                for nodes, edges in ascend(identifier)]

    def segment_paths(self, start, end, waypoints=()):
        segments, seen = [], set()
        # Effective-layout paths retain all candidate parent alternatives. Join
        # each compatible pair at its lowest common ancestor, rather than
        # inventing a semantic relationship between sibling process records.
        for left in self.paths(start):
            for right in self.paths(end):
                common = 0
                for first, last in zip(left["node_ids"], right["node_ids"]):
                    if first != last:
                        break
                    common += 1
                if not common:
                    continue
                pivot = common - 1
                identifiers = list(reversed(left["node_ids"][pivot:])) + right["node_ids"][pivot+1:]
                edges = list(reversed(left["edges"][pivot:])) + right["edges"][pivot:]
                if len(set(identifiers)) != len(identifiers):
                    continue  # Different candidate root paths must not create a cycle.
                available = iter(identifiers)
                if not all(any(wanted == identifier for identifier in available) for wanted in waypoints):
                    continue
                key = tuple(identifiers)
                if key in seen:
                    continue
                seen.add(key)
                directions = ["forward" if edge["from"] == first and edge["to"] == last else "reverse"
                              for first, last, edge in zip(identifiers, identifiers[1:], edges)]
                direction = ("identity" if not directions else
                             "ancestor_to_child" if all(value == "forward" for value in directions)
                             else "child_to_ancestor" if all(value == "reverse" for value in directions)
                             else "through_common_ancestor")
                segments.append({"target_id": end, "start_id": start, "end_id": end,
                    "node_ids": identifiers, "edges": edges, "edge_types": [edge["type"] for edge in edges],
                    "common_ancestor_id": left["node_ids"][pivot], "direction": direction,
                    "traversal_steps": [{"from": first, "to": last, "source_edge": edge,
                        "direction": step_direction}
                        for first, last, edge, step_direction in zip(identifiers, identifiers[1:], edges, directions)],
                    "qualification": "Requested ordered chart-layout segment through a common ancestor. Source edges retain organizational orientation; reverse traversal is explicit and is not a reversed semantic assertion. Candidate indentation is not reviewed semantic IS_A."})
                if len(segments) > 4096:
                    raise ValueError("GRAPH_QA_PATH_BUDGET_EXCEEDED")
        return segments


def _operation(view, operation, complete_chart):
    kind, subjects = operation["kind"], operation["subject_ids"]
    nodes = view.nodes
    visited, traversed = view.ancestors(subjects)
    result = {"kind": kind, "subject_ids": subjects, "answer_outcome": "graph_answer",
              "subject_scope": operation.get("subject_scope", "selectors"),
              "selector_subject_ids": operation.get("selector_subject_ids", subjects),
              "answer": "", "rows": [], "paths": [], "verdict": "not_established",
              "trace": {"seed_ids": subjects, "visited_node_ids": sorted(visited), "selected_edges": traversed,
                        "method": kind + ":typed_graph_operation", "direction": "inbound", "diagnostics": []}}

    def stop(code):
        result["answer_outcome"] = "insufficient_evidence"
        result["answer"] = "The supplied chart graph does not establish this request: " + code + "."
        result["trace"]["diagnostics"].append(code)
        return result

    if kind == "operating_information":
        stop("classification_and_layout_are_not_verified_operating_control_information")
        result["missing_information"] = {
            "role": "information_requirements_not_source_facts",
            "fields": ["applicable qualified procedure/specification", "workpiece material and thickness",
                       "joint and tool configuration", "rotation speed", "travel speed",
                       "applied force or pressure", "temperature/control limits"],
            "qualification": "Examples of information an applicable operating procedure must resolve; this chart establishes neither their values nor their process-specific applicability.",
        }
        result["answer"] = (
            "Figure A1 supplies process names, designations and chart layout, not verified operating conditions. "
            "Missing operating information includes an applicable qualified procedure/specification, workpiece material "
            "and thickness, joint and tool configuration, and applicable settings such as rotation speed, travel speed, "
            "applied force/pressure and temperature/control limits. A separate authorized process-specific procedure "
            "must establish which fields and values apply. These are absent information requirements/examples, not "
            "operating values or universally applicable requirements asserted by A1. Classification and candidate "
            "indentation cannot supply them."
        )
        return result
    if kind == "epistemic_limits":
        result["rows"] = [view.row(identifier) for identifier in subjects if nodes[identifier]["kind"] == "process"]
        result["answer"] = "The graph supplies printed labels/designations, source-box enclosure and candidate indentation relationships. Indentation is layout evidence only; it does not establish reviewed semantic IS_A, equivalence, normative hierarchy or operating information. Additional explicitly reviewed evidence defining the relationship is needed before treating indentation as semantic subtype authority."
        if operation.get("lexical_overlap"):
            result["answer"] = "Sharing words in process labels does not establish a subtype relationship. " + result["answer"]
        for row in result["rows"]:
            if row["indent_parent_ids"]:
                result["answer"] += " " + row["label"] + " has candidate layout parent(s): " + "; ".join(nodes[parent]["label"] for parent in row["indent_parent_ids"]) + "."
        return result
    if not subjects:
        return stop("literal_subject_required_for_operation")
    if kind == "parents":
        parent_ids, selected_edges = set(), []
        result["parent_groups"], result["source_placements"] = [], []
        lines = []
        for identifier in subjects:
            parents = view.layout_parents(identifier)
            if identifier != view.graph["root_id"] and not parents:
                return stop("immediate_layout_parent_not_established")
            ordered = sorted(parents, key=lambda edge: _source_order(nodes[edge["from"]]))
            identifiers = [edge["from"] for edge in ordered]
            result["parent_groups"].append({"subject_id": identifier, "parent_ids": identifiers})
            parent_ids.update(identifiers)
            selected_edges.extend(ordered)
            lines.append(nodes[identifier]["label"] + ": immediate chart-layout parent(s): "
                         + ("; ".join(nodes[parent]["label"] for parent in identifiers) or "none; this is the chart root") + ".")
            if nodes[identifier]["kind"] == "process":
                families = view.families(identifier)
                result["source_placements"].append({"process_id": identifier, "category_ids": families})
                selected_edges.extend(edge for edge in view.incoming.get(identifier, []) if edge["type"] == "ENCLOSES_ROW")
                if families:
                    lines.append("Positive enclosing source category: " + "; ".join(nodes[family]["label"] for family in families) + ".")
            if any(edge["type"] == "INDENTED_UNDER" for edge in ordered):
                lines.append("The immediately indented process parent remains candidate layout, not reviewed semantic subtype.")
        result["rows"] = [view.row(identifier) for identifier in sorted(parent_ids, key=lambda item: _source_order(nodes[item]))]
        result["trace"].update(selected_edges=[edge for edge in view.graph["edges"] if edge in selected_edges],
            visited_node_ids=sorted(set(subjects) | parent_ids | {edge["from"] for edge in selected_edges}),
            method="immediate_effective_layout_parents_with_separate_enclosure", direction="inbound")
        result["answer"] = "\n".join(lines) + "\nEnclosure and physical chart connection are layout observations; neither supplies reviewed semantic IS_A."
        return result
    if kind in {"direct_children", "descendants"}:
        if not complete_chart:
            return stop("complete_chart_required_for_exhaustive_children_or_descendants")
        groups, all_ids, edges = [], set(), []
        for identifier in subjects:
            if nodes[identifier]["kind"] == "category":
                enclosed = {edge["to"] for edge in view.outgoing.get(identifier, []) if edge["type"] == "ENCLOSES_ROW"}
                if any(view.families(child) != [identifier] or any(view.families(parent) != [identifier]
                    for parent in view.row(child)["indent_parent_ids"]) for child in enclosed):
                    return stop("candidate_crosses_or_ambiguously_encloses_categories")
            found, walked = view.descendants([identifier], direct=kind == "direct_children")
            selected = found - {identifier}
            if nodes[identifier]["kind"] == "category" and kind == "descendants" and selected != enclosed:
                return stop("recursive_layout_does_not_cover_all_enclosed_rows")
            if nodes[identifier]["kind"] == "process" and any(view.families(child) != view.families(identifier)
                    for child in selected if nodes[child]["kind"] == "process"):
                return stop("candidate_descendant_crosses_categories")
            all_ids.update(selected)
            edges.extend(walked)
            groups.append({"subject_id": identifier, "node_ids": sorted(selected, key=lambda item: _source_order(nodes[item]))})
        result["groups"] = groups
        result["rows"] = [view.row(identifier) for identifier in sorted(all_ids, key=lambda item: _source_order(nodes[item]))
                          if nodes[identifier]["kind"] == "process"]
        # Returned row objects expose their positive family bindings. Retain the
        # enclosure edges supporting those bindings as well as the layout path.
        proof_ids = all_ids | set(subjects)
        enclosure_edges = [edge for identifier in proof_ids for edge in view.incoming.get(identifier, [])
                           if edge["type"] == "ENCLOSES_ROW"]
        proof_ids.update(edge["from"] for edge in enclosure_edges)
        proof_edges = [edge for edge in view.graph["edges"] if edge in edges or edge in enclosure_edges]
        result["trace"].update(visited_node_ids=sorted(proof_ids), selected_edges=proof_edges,
                               direction="outbound", method="effective_layout_" + kind + ":enclosure_roots_then_candidate_indentation")
        checks = ["directed_graph_acyclic", "requested_layout_depth_exhausted_without_top_k"]
        if any(nodes[identifier]["kind"] == "process" for identifier in subjects):
            checks.append("process_descendants_preserve_category")
        if any(nodes[identifier]["kind"] == "category" for identifier in subjects):
            checks.append("category_enclosure_and_candidate_parent_scope_checked")
            if kind == "descendants":
                checks.append("category_recursive_rows_equal_positive_enclosure")
        result["expansion"] = {"status": "complete_within_supplied_chart", "operation": kind,
            "complete_chart_supplied": bool(complete_chart), "no_top_k_truncation": True,
            "returned_node_ids": sorted(all_ids, key=lambda item: _source_order(nodes[item])),
            "groups": groups, "selected_edge_count": len(proof_edges),
            "checks": checks,
            "qualification": "Completeness within the supplied chart and requested direct/recursive view; caller completeness is not source authentication or reviewed semantics.",
            "semantic_validation": False}
        lines = ["Direct layout children" if kind == "direct_children" else "All recursive layout descendants"]
        for group in groups:
            lines.append(nodes[group["subject_id"]]["label"] + ":")
            for identifier in group["node_ids"]:
                node = nodes[identifier]
                parents = view.row(identifier)["indent_parent_ids"] if node["kind"] == "process" else []
                qualifier = (" [candidate layout parent: " + "; ".join(nodes[parent]["label"] for parent in parents) + "]") if parents else ""
                lines.append("- " + node["label"] + (" (" + node["code"] + ")" if "code" in node else "") + qualifier)
        lines.append("These are chart-layout children, including intermediate rows when recursive; candidate indentation is not reviewed semantic subtype.")
        result["answer"] = "\n".join(lines)
        return result
    if kind == "paths":
        if operation.get("requested_direction") == "from_to":
            starts, ends = operation.get("start_ids", []), operation.get("end_ids", [])
            if len(starts) != 1 or not ends:
                return stop("explicit_path_endpoints_not_resolved")
            result["paths"] = [path for end in ends for path in view.segment_paths(starts[0], end, operation.get("waypoint_ids", []))]
            if any(not any(path["end_id"] == end for path in result["paths"]) for end in ends):
                return stop("requested_direction_or_waypoints_not_established_by_chart_layout_paths")
            result["requested_endpoints"] = {"start_ids": starts, "end_ids": ends, "waypoint_ids": operation.get("waypoint_ids", [])}
        else:
            result["paths"] = [path for identifier in subjects for path in view.paths(identifier)]
        if not result["paths"]:
            return stop("ordered_path_to_root_unavailable")
        result["rows"] = [view.row(identifier) for identifier in subjects if nodes[identifier]["kind"] == "process"]
        result["trace"]["selected_edges"] = [edge for path in result["paths"] for edge in path["edges"]]
        result["trace"]["visited_node_ids"] = sorted({identifier for path in result["paths"] for identifier in path["node_ids"]})
        result["expansion"] = {"status": "complete_within_supplied_chart", "operation": kind,
            "complete_chart_supplied": bool(complete_chart), "no_top_k_truncation": True,
            "path_count": len(result["paths"]),
            "checks": ["all_effective_layout_parent_alternatives_retained", "every_requested_endpoint_resolved",
                       "source_edge_orientation_preserved", "reverse_hops_explicit"],
            "qualification": "All matching qualified paths in this supplied graph; path existence is not semantic entailment or proof of a source-level negative.",
            "semantic_validation": False}
        result["answer"] = "\n".join(" -> ".join(nodes[identifier]["label"] + (" (" + nodes[identifier]["code"] + ")" if "code" in nodes[identifier] else "") for identifier in path["node_ids"]) + ". " + path["qualification"] for path in result["paths"])
        return result
    if kind in {"membership", "layout_relation"}:
        left, right = operation["left_ids"], operation["right_ids"]
        if len(left) != 1 or not right:
            return stop("relation_requires_one_subject_and_explicit_resolved_targets")
        child = left[0]
        if nodes[child]["kind"] != "process":
            return stop("membership_subject_must_be_a_process_row")
        result["rows"] = [view.row(child)]
        if kind == "layout_relation":
            process_ids = list(dict.fromkeys(identifier for identifier in subjects if nodes[identifier]["kind"] == "process"))
            placements = []
            for identifier in process_ids:
                families = view.families(identifier)
                if len(families) != 1:
                    return stop("unique_positive_source_enclosure_required")
                placements.append({"process_id": identifier, "category_id": families[0],
                                   "qualification": "Explicit positive source-box enclosure, not semantic subtype."})
            result["rows"] = [view.row(identifier) for identifier in process_ids]
            result["source_placements"] = placements
            alternatives, texts = [], []
            for parent in right:
                matches = [path for path in view.paths(child) if parent in path["node_ids"]]
                if not matches and not complete_chart:
                    return stop("complete_chart_required_for_absent_layout_relation")
                relation = "yes" if matches else "no"
                direct_edges = [edge for edge in view.layout_parents(child) if edge["from"] == parent]
                alternatives.append({"target_id": parent, "candidate_layout_relation": relation, "paths": matches,
                    "immediate_layout_parent": bool(direct_edges),
                    "source_box_enclosure": parent in view.families(child),
                    "qualification": "Alternative chart placement; distinct hierarchy levels may both be present. No exclusive semantic parent is inferred."})
                texts.append(nodes[child]["label"] + (" has a shown chart path through " if matches else " has no shown chart path through ") + nodes[parent]["label"] + ".")
                result["paths"].extend(matches)
            result["alternatives"] = alternatives
            result["candidate_layout_relation"] = alternatives[0]["candidate_layout_relation"] if len(alternatives) == 1 else "alternatives_reported"
            result["answer"] = " ".join(texts) + " All shown paths retain candidate indentation; reviewed semantic subtype is not established. Alternative targets can describe different levels of one path and are not forced into an exclusive choice."
            for placement in placements:
                process, family = nodes[placement["process_id"]], nodes[placement["category_id"]]
                result["answer"] += " Positive source placement: " + process["label"] + " (" + process["code"] + ") is enclosed by " + family["label"] + "."
            if operation.get("directness"):
                immediate = view.layout_parents(child)
                result["answer"] += " Immediate chart-layout parent: " + "; ".join(nodes[edge["from"]]["label"] for edge in immediate) + "."
                if any(edge["type"] == "INDENTED_UNDER" for edge in immediate):
                    result["answer"] += " This is the immediately indented candidate process parent; the enclosing category is the broader source box, not that immediate process row."
            if any(item["candidate_layout_relation"] == "no" for item in alternatives):
                result["trace"]["negative_proof"] = "explicit_positive_source_enclosures_plus_complete_chart_layout"
            for path in result["paths"]:
                result["answer"] += " Path: " + " -> ".join(nodes[identifier]["label"] for identifier in path["node_ids"]) + "."
            return result
        families = view.families(child)
        if len(families) != 1:
            return stop("unique_positive_source_enclosure_required")
        actual, texts, alternatives = families[0], [], []
        for parent in right:
            if nodes[parent]["kind"] != "category":
                return stop("enclosure_membership_requires_category_targets")
            if actual != parent and not complete_chart:
                return stop("complete_chart_required_for_bounded_negative")
            verdict = "yes" if actual == parent else "no"
            alternatives.append({"target_id": parent, "verdict": verdict})
            texts.append(("Yes" if actual == parent else "No") + ", within Figure A1's chart: " + nodes[child]["label"] + " (" + nodes[child]["code"] + ") is listed inside " + nodes[actual]["label"] + ("." if actual == parent else ", rather than " + nodes[parent]["label"] + "."))
        result["alternatives"] = alternatives
        result["verdict"] = alternatives[0]["verdict"] if len(alternatives) == 1 else "not_established"
        result["trace"]["negative_proof"] = "explicit_positive_foreign_enclosure_plus_complete_chart" if any(item["verdict"] == "no" for item in alternatives) else None
        result["answer"] = " ".join(texts) + " This is source-box membership, not a universal semantic taxonomy claim."
        return result
    if kind in {"designation", "category"}:
        lines = []
        for identifier in subjects:
            node = nodes[identifier]
            if node["kind"] == "process":
                row = view.row(identifier)
                result["rows"].append(row)
                if kind == "designation":
                    lines.append(node["label"] + " — " + node["code"] + " (printed designation).")
                else:
                    families = row["family_ids"]
                    if len(families) != 1:
                        return stop("unique_positive_source_enclosure_required")
                    text = node["label"] + " (" + node["code"] + ") — " + nodes[families[0]]["label"] + "."
                    if row["indent_parent_ids"]:
                        text += " Candidate layout parent: " + "; ".join(nodes[parent]["label"] + " (" + nodes[parent]["code"] + ")" for parent in row["indent_parent_ids"]) + "; semantic subtype is unreviewed."
                    lines.append(text)
            elif kind == "designation" and node["kind"] == "category":
                label, code = _category_name(node)
                result["rows"].append(dict(node, code=code, family_id=identifier, indent_parent_ids=[]))
                lines.append(label + " — " + (code if code else "no overall designation printed in this heading") + ".")
            else:
                return stop("category_lookup_requires_process_subjects")
        result["answer"] = "\n".join(lines)
        return result
    return stop("operation_not_implemented")


def _attach_claim_bindings(view, result, *, source_authenticated=False):
    """Bind atomic observations, without certifying the answer's prose.

    Record hashes validate declared identities. Authentication additionally
    requires the canonical loader and image-byte checks in run_graph_qa. Pure
    caller graphs, including self-declared bound ones, cannot assert that step.
    """
    declared = view.source_receipt is not None
    if source_authenticated and not declared:
        raise ValueError("GRAPH_QA_AUTHENTICATED_RECORD_BINDINGS_REQUIRED")
    support = ("source_record_bound" if source_authenticated else
               "declared_record_binding_source_unverified" if declared else "unbound_caller_graph")
    result["source_binding_status"] = ("canonical_source_and_image_validated" if source_authenticated else
        "declared_record_identities_validated_source_unverified" if declared else "unbound_caller_graph")
    if result.get("support_state") != "INSUFFICIENT_EVIDENCE":
        result["support_state"] = "SOURCE_BOUND_CHART_LAYOUT" if source_authenticated else "UNAUTHENTICATED_CALLER_GRAPH"
    result["answer_binding_scope"] = "Atomic source observations only; full prose completeness and semantic support remain unassessed."
    result["semantic_validation"] = False
    all_claims = {}

    def observation(predicate, identifiers, edges, text, qualification, verification):
        records = [view.nodes[identifier] for identifier in identifiers] + edges
        evidence_ids = list(dict.fromkeys(record["evidence"]["evidence_id"] for record in records if "evidence" in record))
        shape = {"predicate": predicate, "node_ids": list(identifiers),
                 "edge_ids": [edge["id"] for edge in edges if "id" in edge],
                 "edge_keys": [{key: edge[key] for key in ("from", "to", "type")} for edge in edges],
                 "evidence_ids": evidence_ids}
        claim_id = "claim:a1:" + hashlib.sha256(json.dumps(shape, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        return dict(shape, claim_id=claim_id, text=text, qualification=qualification,
                    verification=verification, support=support, semantic_validation=False)

    for index, operation in enumerate(result.get("operations", [])):
        claims = []
        identifiers = operation["trace"]["visited_node_ids"]
        for identifier in identifiers:
            node = view.nodes[identifier]
            text = node["label"] + (" (" + node["code"] + ")" if "code" in node else "")
            claims.append(observation("printed_label_and_designation", [identifier], [], text,
                "Observed printed record; no process semantics or operating values are inferred.",
                node.get("evidence", {}).get("verification", "unbound")))
        for edge in operation["trace"]["selected_edges"]:
            qualification = view.graph["edge_qualifications"][edge["type"]]
            claims.append(observation("observed_chart_relation", [edge["from"], edge["to"]], [edge],
                view.nodes[edge["from"]]["label"] + " --" + edge["type"] + "--> " + view.nodes[edge["to"]]["label"],
                qualification["qualification"], qualification["verification"]))
        for path in operation["paths"]:
            claims.append(observation("ordered_chart_path", path["node_ids"], path["edges"],
                " -> ".join(view.nodes[identifier]["label"] for identifier in path["node_ids"]),
                path["qualification"], "candidate" if "INDENTED_UNDER" in path["edge_types"] else "source_bound"))
        operation["claims"] = claims
        operation["answer_binding_scope"] = result["answer_binding_scope"]
        for claim in claims:
            if claim["claim_id"] not in all_claims:
                all_claims[claim["claim_id"]] = dict(claim, operation_indices=[])
            if index not in all_claims[claim["claim_id"]]["operation_indices"]:
                all_claims[claim["claim_id"]]["operation_indices"].append(index)
    result["claims"] = list(all_claims.values())
    selected = {identifier for claim in result["claims"] for identifier in claim["evidence_ids"]}
    result["record_evidence_catalog"] = [record["evidence"] for record in view.graph["nodes"] + view.graph["edges"]
        if "evidence" in record and record["evidence"]["evidence_id"] in selected]
    return result


def _epistemic_operation(store, requested, complete_chart, query_layer):
    """Execute against the persisted layer, then return its assertion proofs.

    Auto keeps layout questions on the evidence graph. Knowledge statements
    use accepted source-scoped assertions, never candidate subtype authority.
    """
    kind = requested["kind"]
    layer = ("knowledge" if kind in {"designation", "category", "membership"} else "evidence") if query_layer == "auto" else query_layer
    graph = store.graph(layer=layer)
    view = _GraphView(graph)
    unsupported = layer == "knowledge" and kind in {
        "direct_children", "descendants", "parents", "layout_relation", "epistemic_limits", "operating_information"}
    if unsupported:
        result = {"kind": kind, "subject_ids": requested["subject_ids"],
            "answer_outcome": "insufficient_evidence", "rows": [], "paths": [],
            "verdict": "not_established", "answer":
            "Accepted knowledge does not establish this layout or semantic request. "
            "Candidate relationships remain separately queryable in the evidence layer.",
            "trace": {"seed_ids": requested["subject_ids"], "visited_node_ids": [],
                "selected_edges": [], "method": "accepted_assertion_gate", "direction": "none",
                "diagnostics": ["requested_relation_not_admitted_to_knowledge"]}}
    else:
        result = _operation(view, requested, complete_chart)
    result["query_layer"] = layer
    result["knowledge_paths"] = []
    if layer == "knowledge":
        accepted = {item["assertion_id"]: item for item in graph["accepted_assertions"]}
        bindings = graph["assertion_bindings"]
        concepts = graph["concept_bindings"]
        needed = set(result["trace"]["visited_node_ids"])
        needed.update(edge["id"] for edge in result["trace"]["selected_edges"])
        selected = {identifier for record in needed for identifier in bindings.get(record, []) if identifier in accepted}
        missing = []
        # Source node payloads stay immutable for their record proofs. Admission
        # is checked before any such payload can serve as an accepted answer.
        for row in result["rows"]:
            required = {"PRINTED_LABEL"} | ({"PRINTED_DESIGNATION"} if row["kind"] == "process" else set())
            predicates = {accepted[identifier]["predicate"] for identifier in bindings.get(row["id"], []) if identifier in accepted}
            missing.extend(sorted(required - predicates))
        for path in result["paths"]:
            ids = []
            for edge in path["edges"]:
                support = [identifier for identifier in bindings.get(edge["id"], []) if identifier in accepted]
                if len(support) != 1:
                    missing.append("accepted_path_hop_not_established")
                    break
                ids.extend(support)
            else:
                evidence_ids = list(dict.fromkeys(identifier for assertion in ids
                    for identifier in accepted[assertion]["support_evidence_ids"]))
                concept_ids = [concepts[identifier] for identifier in path["node_ids"]]
                steps = [{"from_concept_id": first, "to_concept_id": last, "assertion_id": identifier,
                    "predicate": accepted[identifier]["predicate"],
                    "direction": "forward" if (accepted[identifier]["subject_id"], accepted[identifier]["object_value"]) == (first, last) else "reverse"}
                    for first, last, identifier in zip(concept_ids, concept_ids[1:], ids)]
                result["knowledge_paths"].append({"concept_ids": concept_ids, "steps": steps,
                    "assertion_ids": ids, "evidence_ids": evidence_ids,
                    "qualification": "Accepted, source-scoped chart connections and membership; no semantic subtype or transitive IS_A assertion is created."})
        if missing:
            result.update(answer_outcome="insufficient_evidence", verdict="not_established", rows=[], paths=[], knowledge_paths=[])
            result["answer"] = "The requested accepted knowledge is incomplete or disputed: " + "; ".join(sorted(set(missing))) + "."
            result["trace"]["diagnostics"].extend(missing)
        result["knowledge_support"] = store.support_for(assertion_ids=sorted(selected))
        result["accepted_assertion_ids"] = sorted(selected)
        if kind == "paths" and result["answer_outcome"] == "graph_answer":
            result["answer"] = ("Accepted source-scoped knowledge path; candidate indentation is excluded. "
                "This does not establish a complete indentation route or semantic subtype chain.\n" + result["answer"])
    else:
        ids = result["trace"]["visited_node_ids"] + [edge["id"] for edge in result["trace"]["selected_edges"]]
        result["knowledge_support"] = store.support_for(record_ids=ids)
        result["accepted_assertion_ids"] = []
    result["epistemic_scope"] = "Source-scoped accepted facts" if layer == "knowledge" else "Direct observations, including explicitly qualified candidates"
    return result


def answer_graph(graph, query, *, complete_chart=False, knowledge_store=None, query_layer="auto"):
    """Execute a typed, span-aware plan without changing any graph fact."""
    if query_layer not in {"auto", "evidence", "knowledge"}:
        raise ValueError("GRAPH_QA_QUERY_LAYER_INVALID")
    if query_layer != "auto" and knowledge_store is None:
        raise ValueError("GRAPH_QA_PERSISTED_LAYER_REQUIRED")
    if knowledge_store is not None:
        graph = knowledge_store.graph(layer="evidence")
    view = _GraphView(graph)
    plan = plan_graph_query(graph, query)
    result = {"query": query, "answer": "", "answer_outcome": plan["status"],
              "route": "compound" if len(plan["operations"]) > 1 else (plan["operations"][0]["kind"] if plan["operations"] else "unsupported"),
              "plan": plan, "operations": [], "rows": [], "paths": [], "resolved_entities": plan["resolved_entities"],
              "verdict": "not_established", "support_state": "SOURCE_BOUND_CHART_LAYOUT", "semantic_validation": False,
              "trace": {"seed_ids": plan["resolved_entities"], "visited_node_ids": [], "selected_edges": [],
                        "method": "typed_span_aware_plan", "direction": "mixed", "diagnostics": list(plan["diagnostics"]),
                        "edge_qualifications": graph["edge_qualifications"], "complete_chart_supplied": bool(complete_chart)}}
    if plan["status"] != "ready":
        result["answer"] = "The requested query is not completely resolved: " + "; ".join(plan["diagnostics"] + plan["unresolved_selectors"]) + "."
        return _attach_claim_bindings(view, result)
    operations = []
    # Child-category follow-ups consume the enumerated rows, not the original
    # selector. Execute those follow-ups after the requested list operations.
    requested_operations = [operation for operation in plan["operations"] if not operation.get("use_returned_children")]
    requested_operations += [operation for operation in plan["operations"] if operation.get("use_returned_children")]
    for requested in requested_operations:
        operation = dict(requested)
        if operation.get("use_returned_children"):
            after = operation.get("after_operations", ["direct_children", "descendants"])
            operation["subject_ids"] = list(dict.fromkeys(row["id"] for previous in operations
                if previous["kind"] in after for row in previous["rows"]))
            operation["selector_subject_ids"] = requested["subject_ids"]
        operations.append(_epistemic_operation(knowledge_store, operation, complete_chart, query_layer)
            if knowledge_store is not None else _operation(view, operation, complete_chart))
    result["operations"] = operations
    succeeded = sum(operation["answer_outcome"] == "graph_answer" for operation in operations)
    result["answer_outcome"] = "graph_answer" if succeeded == len(operations) else "insufficient_evidence"
    result["partial_completion"] = 0 < succeeded < len(operations)
    result["answer"] = "\n\n".join(operation["answer"] for operation in operations)
    direct_groups = {group["subject_id"]: group["node_ids"] for operation in operations
                     if operation["kind"] == "direct_children" for group in operation.get("groups", [])}
    recursive_groups = {group["subject_id"]: group["node_ids"] for operation in operations
                        if operation["kind"] == "descendants" for group in operation.get("groups", [])}
    result["list_comparisons"] = []
    for identifier in direct_groups.keys() & recursive_groups.keys():
        direct, recursive = set(direct_groups[identifier]), set(recursive_groups[identifier])
        result["list_comparisons"].append({"subject_id": identifier,
            "direct_count": len(direct), "descendant_count": len(recursive),
            "deeper_node_ids": [node for node in recursive_groups[identifier] if node not in direct],
            "qualification": "Effective chart layout; indentation remains candidate, not reviewed semantic subtype."})
        result["answer"] += ("\n\nFor " + view.nodes[identifier]["label"] + ": " + str(len(direct))
            + " direct layout children versus " + str(len(recursive)) + " recursive descendants. "
            "The direct list contains immediate layout rows; the recursive list retains those rows and all deeper "
            "indented rows, including intermediate groups, each once. This compares chart layout, not reviewed semantic IS_A.")
    selected_rows = {row["id"]: row for operation in operations for row in operation["rows"]}
    result["rows"] = list(selected_rows.values())
    result["paths"] = [path for operation in operations for path in operation["paths"]]
    visited = {identifier for operation in operations for identifier in operation["trace"]["visited_node_ids"]}
    edges = [edge for operation in operations for edge in operation["trace"]["selected_edges"]]
    result["trace"].update(visited_node_ids=sorted(visited), selected_edges=[edge for edge in graph["edges"] if edge in edges])
    result["trace"]["diagnostics"].extend(code for operation in operations for code in operation["trace"]["diagnostics"])
    for operation in operations:
        if operation["kind"] == "membership":
            result["verdict"] = operation["verdict"]
            if operation["trace"].get("negative_proof"):
                result["trace"]["negative_proof"] = operation["trace"]["negative_proof"]
        if "candidate_layout_relation" in operation:
            result["candidate_layout_relation"] = operation["candidate_layout_relation"]
    return _attach_claim_bindings(view, result)


def run_graph_qa(root, payload, *, query_layer="auto"):
    """Load one unchanged full graph, validate pixels, execute no model calls."""
    if query_layer not in {"auto", "evidence", "knowledge"}:
        raise ValueError("GRAPH_QA_QUERY_LAYER_INVALID")
    from src.evidence_a1_cli import validate_cqs
    validate_cqs(payload)
    started = time.perf_counter()
    items = load_a1_evidence(Path(root))
    projected = time.perf_counter()
    figures = [item for item in items if item.kind == "figure_region"]
    if len(figures) != 1 or figures[0].locator.get("element_id") != "Figure A1":
        raise ValueError("GRAPH_QA_ONE_A1_IMAGE_REQUIRED")
    figure = figures[0]
    notes = [item for item in items if item.kind == "note" and item.locator.get("element_id") == "Annex A"]
    anchor = {"pdf_index": figure.locator.get("pdf_index"), "printed_label": figure.locator.get("printed_page"),
              "order": figure.locator.get("order"), "role": "start", "region": figure.locator.get("region")}
    expected_identity = a1_source_identity_id(figure.edition_id, "figure:figure_a1", anchor, figure.content["asset_sha256"])
    if (len(items) != 2 or len(notes) != 1 or {item.edition_id for item in items} != {figure.edition_id}
            or figure.locator.get("canonical_element_id") != "figure:figure_a1"
            or figure.content.get("source_identity_id") != expected_identity
            or figure.locator.get("source_identity_id") != expected_identity
            or figure.locator.get("order") != 0 or figure.content.get("continuation_orders") != [0]
            or notes[0].evidence_id not in figure.content.get("required_evidence_ids", [])):
        raise ValueError("GRAPH_QA_SOURCE_IDENTITY_OR_CLOSURE_INVALID")
    graph = figure.content["chart_graph"]
    _graph_index(graph)
    if "selection" in graph or "full_source_graph_sha256" in graph:
        raise ValueError("GRAPH_QA_REQUIRES_FULL_NATIVE_GRAPH")
    store = EvidenceStore(items)
    inventory = store.packet("Figure A1")
    build_messages(inventory, Path(root))  # Integrity/complete image transport, no inference.
    from src.evidence_a1 import validate_a1_graph_evidence
    binding_receipt = validate_a1_graph_evidence(graph, expected_source={
        "edition_id": figure.edition_id, "source_identity_id": figure.content["source_identity_id"],
        "asset_sha256": figure.content["asset_sha256"], "locator": figure.locator}, require_complete=True)
    from src.evidence_a1_knowledge import prepare_a1_knowledge
    knowledge_store = prepare_a1_knowledge(Path(root), graph)
    authenticated_view = _GraphView(graph)
    validated = time.perf_counter()
    record_graph_hash = hashlib.sha256(json.dumps(graph, ensure_ascii=False, sort_keys=True,
                                                 allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    graph_hash = binding_receipt["native_graph_sha256"]
    answers = []
    for question in payload["questions"]:
        question_started = time.perf_counter()
        query = question["query"]
        contextual = query if re.search(r"\bfigure\s+a1\b", query, re.I) else "Figure A1. " + query
        packet = store.packet(contextual)
        plan = plan_graph_query(graph, query)
        # Source count and comparison subject count are different contracts.
        # Remove only this obsolete diagnostic, and only after a complete typed
        # plan resolves independent same-image subjects. Foreign-source/page
        # diagnostics and incomplete source closure are never bypassed.
        if (packet.status == "insufficient_evidence"
                and set(packet.missing) == {"comparison_requires_two_subjects"}
                and plan["status"] == "ready" and (len(plan["resolved_entities"]) >= 2
                    or (plan.get("comparison_kind") == "operation_views" and plan["resolved_entities"]))
                and inventory.status == "complete" and packet.evidence == inventory.evidence):
            packet = EvidencePacket(contextual, RoutePlan("comparison", inventory.route.evidence_ids), inventory.evidence)
        if packet.status == "complete":
            answer = answer_graph(graph, query, complete_chart=True,
                knowledge_store=knowledge_store, query_layer=query_layer)
        else:
            answer = {"query": query, "answer": "The complete single-image scope cannot answer this request.",
                      "answer_outcome": packet.status, "route": packet.route.kind, "resolved_entities": plan["resolved_entities"],
                      "plan": plan,
                      "rows": [], "trace": {"seed_ids": plan["resolved_entities"], "visited_node_ids": [], "selected_edges": [],
                          "method": "single_image_packet_scope_gate", "direction": "none", "diagnostics": list(packet.missing)},
                      "verdict": "not_established", "support_state": "INSUFFICIENT_EVIDENCE", "semantic_validation": False}
        _attach_claim_bindings(authenticated_view, answer, source_authenticated=True)
        for operation in answer.get("operations", []):
            operation["knowledge_support"]["source_authentication"] = "canonical_source_and_image_validated"
        answer.update(id=question["id"], evidence_ids=[item.evidence_id for item in packet.evidence],
                      source_identity_id=figure.content["source_identity_id"], edition_id=figure.edition_id,
                      graph_sha256=graph_hash, native_graph_sha256=graph_hash,
                      record_graph_sha256=record_graph_hash, source_locator=figure.locator,
                      source_image={"asset_relpath": figure.content["asset_relpath"], "asset_sha256": figure.content["asset_sha256"]},
                      packet_status=packet.status, packet_route=packet.route.kind,
                      selected_nodes=[node for node in graph["nodes"] if node["id"] in answer["trace"]["visited_node_ids"]],
                      latency_ms=round((time.perf_counter() - question_started) * 1000, 3),
                      model="NONE", provider="NONE", model_invocation_count=0,
                      answer_support="Chart-layout extraction; semantic accuracy requires independent source grading.")
        answers.append(answer)
    return {"harness_version": HARNESS_VERSION, "model": "NONE", "provider": "NONE",
            "model_invocation_count": 0, "external_call_count": 0,
            "evaluation_kind": "deterministic_graph_retrieval_QA_not_end_to_end_LLM",
            "answers": answers, "source_identity_id": figure.content["source_identity_id"],
            "edition_id": figure.edition_id, "graph_sha256": graph_hash,
            "native_graph_sha256": graph_hash, "record_graph_sha256": record_graph_hash,
            "record_binding_receipt": binding_receipt,
            "epistemic_store": dict(knowledge_store.describe(), source_authentication="canonical_source_and_image_validated"),
            "query_layer": query_layer,
            "record_evidence_catalog": [record["evidence"] for record in graph["nodes"] + graph["edges"]],
            "source_evidence_packet": inventory.to_dict(), "graph_nodes": len(graph["nodes"]),
            "graph_edges": len(graph["edges"]), "source_image_count": 1,
            "limitations": ["Indentation relationships remain candidate layout, not reviewed semantic subtypes.",
                "Category-subsequence resolution is qualified query interpretation, not an asserted source alias.",
                "Negatives are limited to explicit membership in this complete chart.",
                "Typed literal operations support bounded grammar; unknown or ambiguous requested subjects remain explicit failures.",
                "One-image source closure is independent of N comparison subjects; foreign-source/page guards remain enforced.",
                "Operating information is not inferred from classification or candidate layout."],
            "timings_ms": {"source_projection": round((projected-started)*1000, 3),
                           "image_validation": round((validated-projected)*1000, 3),
                           "qa_operations": round((time.perf_counter()-validated)*1000, 3),
                           "total": round((time.perf_counter()-started)*1000, 3)}}
