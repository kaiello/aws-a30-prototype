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

HARNESS_VERSION = "a1-graph-qa-1.2.0"
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
        segments = []
        for target, reverse in ((end, False), (start, True)):
            for path in self.paths(target):
                sought = end if reverse else start
                if sought not in path["node_ids"]:
                    continue
                index = path["node_ids"].index(sought)
                identifiers, edges = path["node_ids"][index:], path["edges"][index:]
                if reverse:
                    identifiers, edges = list(reversed(identifiers)), list(reversed(edges))
                available = iter(identifiers)
                if not all(any(wanted == identifier for identifier in available) for wanted in waypoints):
                    continue
                segments.append({"target_id": end, "start_id": start, "end_id": end,
                    "node_ids": identifiers, "edges": edges, "edge_types": [edge["type"] for edge in edges],
                    "direction": "child_to_ancestor" if reverse else "ancestor_to_child",
                    "traversal_steps": [{"from": first, "to": last, "source_edge": edge,
                        "direction": "reverse" if reverse else "forward"}
                        for first, last, edge in zip(identifiers, identifiers[1:], edges)],
                    "qualification": "Requested ordered chart segment. Source edges retain printed organizational orientation; reverse traversal is explicit. Candidate indentation is not reviewed semantic IS_A."})
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
                return stop("requested_direction_or_waypoints_not_established_by_ancestor_paths")
            result["requested_endpoints"] = {"start_ids": starts, "end_ids": ends, "waypoint_ids": operation.get("waypoint_ids", [])}
        else:
            result["paths"] = [path for identifier in subjects for path in view.paths(identifier)]
        if not result["paths"]:
            return stop("ordered_path_to_root_unavailable")
        result["rows"] = [view.row(identifier) for identifier in subjects if nodes[identifier]["kind"] == "process"]
        result["trace"]["selected_edges"] = [edge for path in result["paths"] for edge in path["edges"]]
        result["trace"]["visited_node_ids"] = sorted({identifier for path in result["paths"] for identifier in path["node_ids"]})
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


def answer_graph(graph, query, *, complete_chart=False):
    """Execute a typed, span-aware plan without changing any graph fact."""
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
        return result
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
        operations.append(_operation(view, operation, complete_chart))
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
    return result


def run_graph_qa(root, payload):
    """Load one unchanged full graph, validate pixels, execute no model calls."""
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
    validated = time.perf_counter()
    graph_hash = hashlib.sha256(json.dumps(graph, ensure_ascii=False, sort_keys=True,
                                          allow_nan=False, separators=(",", ":")).encode()).hexdigest()
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
            answer = answer_graph(graph, query, complete_chart=True)
        else:
            answer = {"query": query, "answer": "The complete single-image scope cannot answer this request.",
                      "answer_outcome": packet.status, "route": packet.route.kind, "resolved_entities": plan["resolved_entities"],
                      "plan": plan,
                      "rows": [], "trace": {"seed_ids": plan["resolved_entities"], "visited_node_ids": [], "selected_edges": [],
                          "method": "single_image_packet_scope_gate", "direction": "none", "diagnostics": list(packet.missing)},
                      "verdict": "not_established", "support_state": "INSUFFICIENT_EVIDENCE", "semantic_validation": False}
        answer.update(id=question["id"], evidence_ids=[item.evidence_id for item in packet.evidence],
                      source_identity_id=figure.content["source_identity_id"], edition_id=figure.edition_id,
                      graph_sha256=graph_hash, source_locator=figure.locator,
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
