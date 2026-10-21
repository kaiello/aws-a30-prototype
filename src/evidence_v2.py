"""Version 2 canonical evidence and bounded query planning (standard library only).

The manifest/SQLite remain the source spine. This in-memory lookup is a derived
index, never a new source of authority. A source binding is not semantic review.
"""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "2.0.0"
KINDS = {"definition", "table_row", "figure_region", "note"}
VERIFICATIONS = {"source_bound", "candidate", "reviewed", "synthetic"}


def evidence_id(edition_id: str, kind: str, locator: dict, content: dict) -> str:
    raw = json.dumps([SCHEMA_VERSION, edition_id, kind, locator, content],
                     sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return "ev2:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    edition_id: str
    kind: str
    locator: dict
    content: dict
    verification: str
    required_ids: tuple[str, ...] = ()
    relationships: tuple[dict, ...] = ()

    def __post_init__(self):
        if (self.kind not in KINDS or self.verification not in VERIFICATIONS
                or not self.edition_id or not isinstance(self.locator, dict)
                or not self.locator.get("element_id") or not isinstance(self.content, dict)
                or self.evidence_id != evidence_id(self.edition_id, self.kind, self.locator, self.content)
                or not all(isinstance(i, str) for i in self.required_ids)):
            raise ValueError("Invalid canonical evidence or content hash")
        if self.verification == "synthetic" and not self.edition_id.startswith("fixture:"):
            raise ValueError("Synthetic evidence requires a fixture edition")
        for edge in self.relationships:
            if (set(edge) != {"predicate", "target_id", "qualification", "verification"}
                    or edge["predicate"] not in {"ALIAS_FOR", "ILLUSTRATED_BY", "COMPARES_WITH", "CONTINUES", "CANDIDATE_CONCEPT", "CANDIDATE_REGISTRY"}
                    or edge["verification"] not in VERIFICATIONS or not edge["qualification"]):
                raise ValueError("Unqualified or unsupported evidence relationship")
            if edge["predicate"] in {"CANDIDATE_CONCEPT", "CANDIDATE_REGISTRY"} and edge["verification"] != "candidate":
                raise ValueError("Derived concept identity is candidate only")

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class RoutePlan:
    kind: str
    evidence_ids: tuple[str, ...] = ()
    alternatives: tuple[dict, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self):
        # Seed membership is a set, while the evidence packet separately owns
        # canonical source/continuation order. Lookup insertion order must not
        # make a freshly retrieved complete packet look modified to the reader.
        object.__setattr__(self, "evidence_ids", tuple(sorted(set(self.evidence_ids))))


@dataclass(frozen=True)
class EvidencePacket:
    query: str
    route: RoutePlan
    evidence: tuple[Evidence, ...] = ()
    missing: tuple[str, ...] = ()
    status: str = "complete"

    def to_dict(self):
        return dict(schema_version=SCHEMA_VERSION, **asdict(self))


def _normal(value):
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _contains(query, term):
    return bool(term) and re.search(r"(?<!\w)" + re.escape(_normal(term)) + r"(?!\w)", _normal(query)) is not None


class EvidenceStore:
    """Exact aliases, typed element lookup and explicit sense ambiguity.

    No lexical similarity/graph reachability is promoted to semantic support.
    Required closure is unrestricted by retrieval top-k but bounded by corpus.
    """
    def __init__(self, items: list[Evidence]):
        self.items = {}
        for item in items:
            # Frozen dataclasses contain dictionaries: revalidate at the boundary.
            item.__post_init__()
            if item.evidence_id in self.items:
                raise ValueError("Duplicate evidence ID")
            self.items[item.evidence_id] = item
        self.editions = {item.edition_id for item in items}

    def route(self, query: str) -> RoutePlan:
        if not isinstance(query, str) or not query.strip() or len(query) > 16384:
            raise ValueError("Query must be nonempty text within 16384 characters")
        original_query = query
        query = _normal(query)
        selected, definition_groups = [], {}
        explicit = set(re.findall(r"\b(?:figure|table)\s+[a-z]\d+[a-z]?\b", query))
        unknown = explicit - {_normal(i.locator["element_id"]) for i in self.items.values()}
        comparison = bool(re.search(r"\b(compare|versus|vs\.?|difference|distinction)\b", query))
        scoped_images = [i for i in self.items.values() if i.kind == "figure_region"
                         and i.content.get("single_image_scope") is True]
        if scoped_images:
            # This gate describes this bounded workflow, not source-wide
            # answerability. Never truncate a question's required evidence to
            # fit one image and then call its packet complete.
            for image in scoped_images:
                declared = image.content.get("scope_query_diagnostics", [])
                if declared:
                    return RoutePlan("missing", diagnostics=tuple(declared))
                short = _normal(image.locator["element_id"]).split()[-1]
                if (_contains(query, short) and not any(
                        _contains(query, label) for label in image.content.get("identity_alternatives", []))):
                    labels = image.content.get("identity_alternatives", [])
                    if len(labels) > 1:
                        return RoutePlan("ambiguity", alternatives=tuple(
                            {"headword": label, "sense": "source element identity"} for label in labels),
                            diagnostics=("select_figure_or_table_identity",))
                foreign_ids = {token.casefold() for token in re.findall(
                    r"(?<![\w.])[a-z]\d+[a-z]?(?![\w.])", query)} - {short}
                if foreign_ids:
                    return RoutePlan("missing", diagnostics=tuple(
                        "single_image_scope_deferred:unqualified_element:" + token for token in sorted(foreign_ids)))
                for page in re.finditer(r"\b(?:(pdf|viewer|printed)\s+)?(?:pages?\s+|pp?\.\s*)(\d+)\b", query):
                    expected = (str(image.locator.get("pdf_index", -2) + 1) if page[1] in {"pdf", "viewer"}
                                else str(image.locator.get("printed_page")))
                    if page[2] != expected:
                        return RoutePlan("missing", diagnostics=("single_image_scope_deferred:page_outside_selected_image",))
                for page in re.finditer(r"\bpdf\s+index\s+(\d+)\b", query):
                    if page[1] != str(image.locator.get("pdf_index")):
                        return RoutePlan("missing", diagnostics=("single_image_scope_deferred:pdf_index_outside_selected_image",))
            external = re.search(
                r"\b(?:two|three|multiple|both|all|every|other|next|previous|additional|remaining)\s+"
                r"(?:source\s+)?(?:figures?|images?|pages?)\b|"
                r"\bacross\s+(?:\w+\s+){0,3}(?:pages|images|figures)\b|"
                r"\bclause\s+\d+\b|\bdefinitions?\b|"
                r"\b(?:numerical\s+)?acceptance\s+(?:limits?|criteria)\b|"
                r"\b(?:source|standard)[ -]wide\b", query)
            if external:
                return RoutePlan("missing", diagnostics=("single_image_scope_deferred:" + external[0],))
        # Longest matching headword avoids selecting 'face' within 'root face'.
        matches, alias_targets = [], {}
        exact_headwords = {_normal(i.content.get("headword", "")) for i in self.items.values()
                           if i.kind == "definition" and _contains(query, i.content.get("headword", ""))}
        for item in self.items.values():
            if item.kind == "definition":
                names = [item.content.get("headword", ""), *item.content.get("aliases", [])]
                names = [name for name in names if _contains(query, name)]
                if not _contains(query, item.content.get("headword", "")):
                    names = [n for n in names if _normal(n) not in exact_headwords]
                if names:
                    matches.append((max(len(n) for n in names), item))
                    for name in names:
                        alias_targets.setdefault(_normal(name), []).append(item)
        excluded = set()
        if not comparison:
            for group in alias_targets.values():
                chosen = {_normal(i.content["headword"]) for i in group}.intersection(exact_headwords)
                if len(chosen) == 1:
                    excluded.update(i.evidence_id for i in group if _normal(i.content["headword"]) not in chosen)
        matches = [(length, item) for length, item in matches if item.evidence_id not in excluded]
        alias_targets = {name: [i for i in group if i.evidence_id not in excluded] for name, group in alias_targets.items()}
        for length, item in matches:
            headword = _normal(item.content["headword"])
            if any(length < other_len and _contains(other.content["headword"], headword)
                   for other_len, other in matches):
                continue
            definition_groups.setdefault(headword, []).append(item)
        ambiguity = []
        for name, group in alias_targets.items():
            targets = {_normal(i.content["headword"]) for i in group}
            if len(targets) > 1 and (comparison or not targets.intersection(exact_headwords)):
                ambiguity.extend({"evidence_id": i.evidence_id, "headword": i.content["headword"],
                                  "sense": i.content.get("sense", ""), "matched_alias": name,
                                  "qualifiers": i.content.get("qualifiers", [])} for i in group)
        for headword, group in definition_groups.items():
            senses = {i.content.get("sense", "") for i in group}
            if len(senses) > 1:
                qualified = [i for i in group if i.content.get("sense") and _contains(query, i.content["sense"])]
                if len(qualified) == 1:
                    group = qualified
                else:
                    ambiguity.extend({"evidence_id": i.evidence_id, "headword": headword,
                                      "sense": i.content.get("sense", ""),
                                      "qualifiers": i.content.get("qualifiers", [])} for i in group)
            selected.extend(i.evidence_id for i in group)
        table_groups, table_missing = {}, []
        for item in self.items.values():
            label = _normal(item.locator["element_id"])
            if label not in explicit:
                continue
            if item.kind == "table_row":
                table_groups.setdefault(label, []).append(item)
            elif item.kind == "figure_region":
                selected.append(item.evidence_id)
            elif item.kind == "note":
                selected.append(item.evidence_id)
        for label, rows in table_groups.items():
            residual = query.replace(label, " ").strip(" ?.:")
            browsing = not residual or all(word in {
                "show", "me", "display", "list", "all", "rows", "cells", "contents", "of", "in",
                "the", "for", "please", "what", "is", "are", "processes", "designations", "and"}
                for word in residual.split())
            matching = []
            if not browsing and not comparison:
                for item in rows:
                    cells = item.content.get("cells", [])
                    values = cells.values() if isinstance(cells, dict) else cells
                    lengths = []
                    for value in values:
                        wording = str(value)
                        if re.fullmatch(r"[A-Z]+(?:-[A-Z]+)?", wording):
                            # An exact source acronym is case-sensitive inside
                            # prose; otherwise ordinary 'is' can select code IS.
                            matched = (re.search(r"(?<!\w)" + re.escape(wording) + r"(?!\w)", original_query)
                                       is not None or residual == wording.casefold())
                        else:
                            matched = _contains(residual, wording)
                        if matched:
                            lengths.append(len(wording))
                    if lengths:
                        matching.append((max(lengths), item))
                if matching:
                    longest = max(length for length, _ in matching)
                    rows = [item for length, item in matching if length == longest]
                elif all(item.verification != "candidate" for item in rows):
                    rows = []
                    table_missing.append("table_selector_not_found:" + label)
            selected.extend(item.evidence_id for item in rows)
        if ambiguity:
            return RoutePlan("ambiguity", tuple(selected), tuple(ambiguity), ("select_source_sense",))
        if unknown or table_missing:
            return RoutePlan("missing", tuple(selected), diagnostics=tuple("unknown_element:" + i for i in sorted(unknown)) + tuple(table_missing))
        selected = tuple(dict.fromkeys(selected))
        modalities = {self.items[i].kind for i in selected}
        if comparison:
            # A comparison requires at least two subjects, not two continuation pages.
            subjects = {(_normal(self.items[i].content.get("headword", self.items[i].locator["element_id"])))
                        for i in selected if self.items[i].kind != "note"}
            chart_subjects = {identifier for i in scoped_images if i.evidence_id in selected
                              for identifier in i.content.get("chart_graph", {}).get("selection", {}).get("seed_ids", [])}
            if len(subjects) < 2 and len(chart_subjects) < 2:
                return RoutePlan("missing", selected, diagnostics=("comparison_requires_two_subjects",))
            kind = "comparison"
        elif "figure_region" in modalities:
            kind = "visual"
        elif "table_row" in modalities:
            kind = "table"
        elif "definition" in modalities:
            kind = "definition"
        else:
            kind = "missing"
        return RoutePlan(kind, selected, diagnostics=() if selected else ("no_exact_evidence",))

    def packet(self, query: str) -> EvidencePacket:
        route = self.route(query)
        pending, found, missing = list(route.evidence_ids), {}, list(route.diagnostics)
        while pending:
            identifier = pending.pop(0)
            if identifier in found:
                continue
            item = self.items.get(identifier)
            if item is None:
                missing.append("required_evidence_missing:" + identifier)
                continue
            found[identifier] = item
            if item.verification == "candidate":
                missing.append("unverified_evidence:" + identifier)
            if item.kind == "table_row" and (not item.content.get("headers") or not item.content.get("cells")):
                missing.append("table_cells_missing:" + identifier)
            if item.kind == "definition" and not item.content.get("text"):
                missing.append("definition_text_missing:" + identifier)
            pending.extend(i for i in (*item.required_ids, *item.content.get("required_evidence_ids", ())) if i not in found)
        # Every required item belongs to the selected edition. Cross-edition
        # comparisons are deliberately deferred until explicitly version-routed.
        if len({i.edition_id for i in found.values()}) > 1:
            missing.append("mixed_source_editions")
        for item in found.values():
            if item.kind == "figure_region":
                expected = item.content.get("continuation_orders")
                members = [i for i in found.values() if i.kind == "figure_region"
                           and i.edition_id == item.edition_id and i.locator["element_id"] == item.locator["element_id"]]
                actual = sorted(i.locator.get("order") for i in members)
                if (not isinstance(expected, list) or expected != list(range(len(expected)))
                        or not expected or actual != expected
                        or any(i.content.get("continuation_orders") != expected for i in members)):
                    missing.append("figure_continuations_incomplete:" + item.locator["element_id"])
            if item.kind == "table_row":
                headers, cells = item.content.get("headers", []), item.content.get("cells", [])
                if (len(headers) != len(set(headers)) or
                        (isinstance(cells, dict) and (set(cells) != set(headers) or any(cells[h] in {None, ""} for h in headers)))
                        or (isinstance(cells, list) and (len(cells) != len(headers) or any(c in {None, ""} for c in cells)))):
                    missing.append("table_cells_incomplete:" + item.evidence_id)
        ordered = sorted(found.values(), key=lambda i: (
            i.locator.get("element_id", ""), i.locator.get("order", 0), i.evidence_id))
        status = ("clarification_required" if route.kind == "ambiguity" else
                  "insufficient_evidence" if missing or route.kind == "missing" else "complete")
        return EvidencePacket(query, route, tuple(ordered), tuple(dict.fromkeys(missing)), status)
