"""Span-aware literal graph query planning, independent of source vocabulary."""
from __future__ import annotations

import re

PLANNER_VERSION = "a1-graph-planner-1.3.0"


def _words(value):
    return re.findall(r"[a-z0-9]+", str(value).casefold())


def _category_parts(node):
    found = re.fullmatch(r"(.*?)\s*\(([A-Z]+(?:-[A-Z]+)?)\)\s*", node["label"])
    return (found[1].strip(), found[2]) if found else (node["label"], None)


def _source_context_spans(query):
    """Identify the supported chart reference without changing query offsets."""
    return [{"start": found.start(), "end": found.end(), "text": found[0],
             "source_element": "Figure A1", "kind": "source_context"}
            for found in re.finditer(r"(?<![\w.])(?:Figure\s+)?A1(?!\w|\.\w)", query, re.I)]


def resolve_mentions(graph, query):
    """Keep every occurrence; suppress only a shorter overlapping occurrence.

    Equal-span competing identities stay ambiguous. Code matching never uses
    a prefix and process codes remain case-sensitive. Offsets refer to the
    original query, including punctuation and repeated independent mentions.
    """
    grouped = {}
    context = _source_context_spans(query)

    def add_match(match, identifier, method, kind):
        if any(span["start"] < match.end() and match.start() < span["end"] for span in context):
            return
        grouped.setdefault((match.start(), match.end()), []).append((identifier, method, kind))

    for node in graph["nodes"]:
        if node["kind"] not in {"category", "process"}:
            continue
        label, code = _category_parts(node) if node["kind"] == "category" else (node["label"], node.get("code"))
        words = _words(label)
        if words:
            pattern = r"(?<!\w)" + r"[\W_]+".join(map(re.escape, words)) + r"(?!\w)"
            for match in re.finditer(pattern, query, re.I):
                add_match(match, node["id"], "literal_label", node["kind"])
        if code:
            flags = re.I if node["kind"] == "category" else 0
            for match in re.finditer(r"(?<![\w-])" + re.escape(code) + r"(?![\w-])", query, flags):
                if node["kind"] == "category" and len(code) == 1 and match[0] != code:
                    before, after = query[:match.start()].rstrip(), query[match.end():].lstrip()
                    if not before.endswith("(") or not after.startswith(")"):
                        continue
                add_match(match, node["id"], "exact_heading_code" if node["kind"] == "category" else "exact_process_code", node["kind"])
    mentions = []
    for (start, end), candidates in sorted(grouped.items()):
        if any(other_start <= start and end <= other_end and (other_start < start or end < other_end)
               and any(method == "literal_label" for _, method, _ in other)
               for (other_start, other_end), other in grouped.items()):
            continue
        identifiers = list(dict.fromkeys(identifier for identifier, _, _ in candidates))
        mentions.append({"start": start, "end": end, "text": query[start:end],
                         "candidate_ids": identifiers, "status": "resolved" if len(identifiers) == 1 else "ambiguous",
                         "methods": list(dict.fromkeys(method for _, method, _ in candidates)),
                         "kinds": list(dict.fromkeys(kind for _, _, kind in candidates))})
    return mentions


def _masked(query, mentions):
    characters = list(query)
    for mention in [*mentions, *_source_context_spans(query)]:
        characters[mention["start"]:mention["end"]] = " " * (mention["end"] - mention["start"])
    return "".join(characters)


def _relation_text(query):
    """Keep offsets while excluding source framing and later statements."""
    characters = list(query)
    for span in _source_context_spans(query):
        first = span["start"]
        framing = re.search(r"\b(?:in|from|on|within|using|according\s+to)\s+(?:the\s+)?$", query[:first], re.I)
        if not framing:
            # A chart reference can itself be the grammatical subject in
            # "Does Figure ... place ..."; retain that form for its parser.
            continue
        first = framing.start()
        characters[first:span["end"]] = " " * (span["end"] - first)
    text = "".join(characters)
    boundary = re.search(r"[?;]|\.(?=\s+(?:What|Which|How|Why|Does|Is|Are|Explain|Give|Show)\b|\s*$)", text, re.I)
    return text[:boundary.start() if boundary else len(text)].rstrip()


def _body_end(query, start):
    tail = query[start:]
    stop = re.search(r"[:;?]|\band\s+(?:which|what|give|show|include|provide|explain|describe|its|their)\b|"
                     r"\b(?:give|giving|include|including|return|provide)\s+(?:each|their|the|its|acronyms?|abbreviations?|codes?|categor\w*|famil\w*)\b|"
                     r"\b(?:belong\s+to|a\s+part\s+of|part\s+of|stand(?:s)?\s+for)\b|"
                     r"\bseparately\s+(?:from|and)\b|"
                     r"\b(?:because|since|given\s+that|on\s+the\s+basis\s+of)\b|"
                     r"\b(?:in|from|using|within|of|on|according\s+to)\s+(?:the\s+)?(?:Figure\s+)?A1\b", tail, re.I)
    return start + stop.start() if stop else len(query.rstrip(" .?"))


def _selector_bodies(query):
    """Identify explicit coordinated selector lists without splitting labels."""
    patterns = [
        r"\b(?:compare|contrast)\s+", r"\bdifferences?\s+between\s+",
        r"\b(?:abbreviations?|acronyms?|designations?|codes?|families|categories)\s+(?:for|of)\s+",
        r"\bWhat\s+(?:do|does|is|are)\s+(?=.+?\bstand(?:s)?\s+for\b)",
        r"\b(?:Which|What)\s+(?:families|family|categories|category|process)\s+(?:do|does|is|are)\s+",
        r"\b(?:children|descendants|parents?)\s+(?:of|under|for)\s+",
        r"\bdirectly\s+(?:under|beneath)\s+",
        r"\bpaths?\b[^:;?]*?\bto\s+",
    ]
    bodies = []
    for pattern in patterns:
        for found in re.finditer(pattern, query, re.I):
            start, end = found.end(), _body_end(query, found.end())
            if end > start and (start, end) not in bodies:
                bodies.append((start, end))
    return bodies


def _unresolved_selectors(query, mentions, *, operation_views=False, relation_spans=()):
    masked = _masked(query, mentions)
    ignored = {"the", "a", "an", "process", "processes", "and", "or", "both", "each", "all", "every", "in", "figure", "a1",
               "direct", "immediate", "children", "recursive", "recursively", "descendants", "of",
               "they", "them", "their", "it", "its", "these", "those"}
    # These are grammatical tails, not aliases or entity vocabulary. Replacing
    # them with spaces retains span boundaries and leaves unknown names intact.
    grammar = []
    if relation_spans:
        grammar.extend([
            r"\b(?:within|in|under)\s+(?:that|the\s+same)\s+(?:category|family)\b",
            r"\b(?:rather\s+than|instead\s+of)\b",
            r"\b(?:is|are|does|do)\s+(?:it|the\s+process|they)\b",
            r"\b(?:shown|listed|depicted|placed|presented)\s+as\b",
            r"\b(?:directly|immediately)\b(?=\s+(?:under|beneath|within|inside)\b)",
            r"\b(?:nested|indented|placed|listed|shown|sits?|falls?|appears?|belongs?)\b(?=\s+(?:directly\s+)?(?:under|beneath|within|inside|to)\b)",
            r"\b(?:under|beneath|within|inside|to)\b",
        ])
    if operation_views:
        grammar.extend([
            r"\bseparately\s+(?:from|and)\b",
            r"\b(?:explain|describe)\s+(?:the\s+)?differences?\b",
            r"\b(?:direct|immediate|recursive)\s+(?:children|descendants|subprocesses|processes)\b",
            r"\b(?:from|separately|between|versus|vs)\b",
        ])
    for pattern in grammar:
        masked = re.sub(pattern, lambda found: " " * len(found[0]), masked, flags=re.I)
    unresolved = []
    bodies = list(dict.fromkeys([*_selector_bodies(query), *relation_spans]))
    for start, end in bodies:
        boundaries = [start]
        for separator in re.finditer(r",|\band\b|\bor\b|\bversus\b|\bvs\.?\b", masked[start:end], re.I):
            boundaries.extend((start + separator.start(), start + separator.end()))
        boundaries.append(end)
        for first, last in zip(boundaries[::2], boundaries[1::2]):
            raw = query[first:last].strip(" ,.? ")
            remainder = [word for word in _words(masked[first:last]) if word not in ignored]
            if raw and remainder and raw not in unresolved:
                unresolved.append(raw)
    return unresolved


def _epistemic_intent(outside):
    lexical = bool(re.search(
        r"\b(?:shar(?:e[sd]?|ing)|same|common|similar|overlapping)\b.*\b(?:words?|labels?|names?|prefix(?:es)?)\b|"
        r"\b(?:words?|labels?|names?|prefix(?:es)?)\b.*\b(?:shar(?:e[sd]?|ing)|same|common|similar|overlap)\b|"
        r"\bshar(?:e[sd]?|ing)\s+[\"'\u201c\u2018]|"
        r"\b(?:lexical|wording|name\s+alone|label\s+alone)\b", outside))
    epistemic = lexical or bool(re.search(
        r"\b(?:indent(?:ation|ed)?|epistemic|reviewed|semantic|normative|equivalen\w*)\b|"
        r"\bevidence\b.*\b(?:parent|relationship|support|subtype)\b|"
        r"\b(?:parent|relationship|subtype)\b.*\bevidence\b|"
        r"\b(?:what|which|how)\b.*\b(?:supports?|justif(?:y|ies)|proves?)\b.*\b(?:interpretation|relationship|claim|subtype)\b", outside))
    return epistemic, lexical


def _subsequence_category(graph, fragment):
    wanted = _words(re.sub(r"^\s*(?:the|a|an)\s+", "", fragment, flags=re.I))
    if len(wanted) < 2:
        return []
    matches = []
    for node in graph["nodes"]:
        if node["kind"] != "category":
            continue
        available = iter(_words(_category_parts(node)[0]))
        if all(any(word == candidate for candidate in available) for word in wanted):
            matches.append(node["id"])
    return matches


def plan_graph_query(graph, query):
    if not isinstance(query, str) or not query.strip() or len(query) > 16360:
        raise ValueError("GRAPH_QA_QUERY_INVALID")
    mentions = resolve_mentions(graph, query)
    epistemic, lexical_overlap = _epistemic_intent(_masked(query, mentions).casefold())
    relation_text = _relation_text(query)
    membership = None
    relation_patterns = [
        r"(?:^|[.:?]\s*)(?:Is|Are)\s+(.+?)\s+(?:(?:a\s+)?(?:type|subtype|part|member)\s+of|in|under|beneath|within)\s+(.+?)(?:\s+in\s+Figure\s+A1)?[?.]*$",
        r"(?:^|[.:?]\s*)Does\s+(?:the\s+)?(?:chart|(?:figure\s+)?A1|indentation)\s+(?:place|show|list|put|depict|indicate|indent)\s+(.+?)\s+(?:under|beneath|in|within|as\s+(?:a\s+)?(?:sub)?type\s+of)\s+(.+?)[?.]*$",
        r"(?:^|[.:?]\s*)Does\s+(.+?)\s+(?:(?:appear|fall|sit|belong|go)\s+)?(?:under|beneath|in|within|to)\s+(.+?)[?.]*$",
    ]
    # Evidence intent supplements literal relations. The captured-mention
    # guard below rejects pure meta questions without dropping Does relations.
    active_patterns = relation_patterns
    if lexical_overlap:
        # Lexical sharing is the proposed basis, not the left-hand entity.
        # The two captured selectors remain ordinary literal graph subjects.
        active_patterns = [
            r"(?:^|[.:?]\s*)(?:Does|Can)\s+.+?\s+(?:make|mean|imply|prove|establish|show|indicate|demonstrate)\s+(?:that\s+)?(.+?)\s+(?:(?:is|are)\s+)?(?:an?\s+)?(?:type|subtype|part|member)\s+of\s+(.+?)$",
            *relation_patterns,
        ]
    for pattern in active_patterns:
        membership = re.search(pattern, relation_text, re.I)
        if membership:
            if epistemic and pattern in relation_patterns[1:]:
                first, last = membership.span(1)
                if not any(first <= mention["start"] and mention["end"] <= last for mention in mentions):
                    membership = None
                    continue
            break
    member_sides = None
    relation_spans = []
    if membership:
        sides = []
        for group in (1, 2):
            first, last = membership.span(group)
            last = min(last, _body_end(query, first))
            relation_spans.append((first, last))
            selected = [m for m in mentions if first <= m["start"] and m["end"] <= last]
            if not selected and group == 2:
                candidates = _subsequence_category(graph, query[first:last].strip(" ?."))
                if candidates:
                    selected = [{"start": first, "end": last, "text": query[first:last], "candidate_ids": candidates,
                                 "status": "resolved" if len(candidates) == 1 else "ambiguous",
                                 "methods": ["ordered_category_token_subsequence_candidate_resolution"], "kinds": ["category"]}]
                    mentions.extend(selected)
            sides.append(list(dict.fromkeys(identifier for mention in selected for identifier in mention["candidate_ids"])))
        member_sides = sides
    mentions.sort(key=lambda item: (item["start"], item["end"]))
    entities = list(dict.fromkeys(m["candidate_ids"][0] for m in mentions if m["status"] == "resolved"))
    by_id = {node["id"]: node for node in graph["nodes"]}
    processes = [identifier for identifier in entities if by_id[identifier]["kind"] == "process"]
    categories = [identifier for identifier in entities if by_id[identifier]["kind"] == "category"]
    outside = _masked(query, mentions).casefold()
    operations = []

    def add(kind, subjects=None, **parameters):
        operations.append({"kind": kind, "subject_ids": list(entities if subjects is None else subjects), **parameters})

    if re.search(r"\b(?:abbreviations?|acronyms?|designations?|codes?)\b|\bstand(?:s)?\s+for\b", outside):
        add("designation", processes)
    if re.search(r"\b(?:famil(?:y|ies)|categor(?:y|ies))\b", outside) or (
            re.search(r"\b(?:what|which)\s+process(?:es)?\b", outside) and re.search(r"\b(?:in|under|part\s+of)\b", outside)):
        add("category", processes)
    if re.search(r"\b(?:immediate\s+|direct\s+|layout\s+)?parents?\s+(?:of|for)\b", outside):
        add("parents")
    direct_list = bool(re.search(r"\bdirect\s+(?:children|subprocesses|processes)\b|\bimmediate\s+(?:children|subprocesses)\b", outside))
    direct_relation = bool(re.search(r"\bdirectly\s+(?:under|beneath)\b", outside))
    direct = direct_list or direct_relation
    descendants = bool(re.search(r"\bdescendants?\b|\brecursive(?:ly)?\b|\ball\b.*\b(?:processes|children|subprocesses)\b", outside))
    if direct and (not member_sides or direct_list):
        add("direct_children")
    if descendants and (not direct or re.search(r"\bdescendants?\b|\brecursive(?:ly)?\b", outside)):
        add("descendants")
    if re.search(r"\bpaths?\b|\broot\b.*\bthrough\b", outside):
        parameters = {}
        path_match = re.search(r"\bpaths?\s+from\s+(.+?)\s+to\s+(.+?)[?.]*$", query, re.I)
        if path_match:
            sides = []
            for group in (1, 2):
                first, last = path_match.span(group)
                sides.append(list(dict.fromkeys(identifier for mention in mentions
                    if first <= mention["start"] and mention["end"] <= last for identifier in mention["candidate_ids"])))
            starts = sides[0]
            if re.search(r"\broot\b", path_match[1], re.I):
                starts = [graph["root_id"]] + starts
            parameters = {"start_ids": starts[:1], "end_ids": sides[1],
                          "waypoint_ids": starts[1:] if starts else [], "requested_direction": "from_to"}
        add("paths", processes or categories, **parameters)
    if member_sides:
        left, right = member_sides
        relation_kind = "membership" if right and all(by_id[identifier]["kind"] == "category" for identifier in right) else "layout_relation"
        add(relation_kind, list(dict.fromkeys(left + right)), left_ids=left, right_ids=right,
            **({"directness": True} if direct_relation else {}))
    if epistemic:
        add("epistemic_limits", processes or entities, lexical_overlap=lexical_overlap)
    if re.search(r"\b(?:operating|temperature|timing|duration|voltage|amperage|settings?|parameters?|controls?|speed|procedure|acceptance|strength|mechanism|equipment|current|pressure)\b", outside):
        add("operating_information", processes or entities)
    comparison = bool(re.search(r"\b(?:compare|contrast|differences?|versus)\b|\bvs\.?\b", outside))
    if comparison and not operations:
        add("designation", processes)
        add("category", processes)
    child_operations = [operation["kind"] for operation in operations if operation["kind"] in {"direct_children", "descendants"}]
    if child_operations:
        # Codes are already on child-list rows. An explicit category request
        # remains an operation and applies to those returned process rows.
        operations = [operation for operation in operations if operation["kind"] != "designation"]
        for operation in operations:
            if operation["kind"] == "category":
                operation.update({"subject_scope": "returned_children", "use_returned_children": True,
                                  "after_operations": child_operations})
    view_comparison = bool(entities and set(child_operations) >= {"direct_children", "descendants"})
    unresolved = _unresolved_selectors(query, mentions, operation_views=view_comparison, relation_spans=relation_spans)
    if member_sides and any(len(side) != 1 for side in member_sides):
        unresolved.extend(query[first:last].strip(" ?.") for (first, last), side in zip(relation_spans, member_sides) if not side)
    diagnostics = []
    if any(mention["status"] == "ambiguous" for mention in mentions):
        status = "clarification_required"
        diagnostics.append("ambiguous_literal_label_or_exact_code")
    elif unresolved:
        status = "insufficient_evidence"
        diagnostics.append("requested_selector_not_resolved")
    elif comparison and len(processes or entities) < 2 and not view_comparison:
        status = "insufficient_evidence"
        diagnostics.append("comparison_requires_independent_subjects")
    elif not operations:
        status = "capability_gap"
        diagnostics.append("query_operation_not_supported")
    elif not entities and not all(operation["kind"] in {"epistemic_limits", "operating_information"} for operation in operations):
        status = "insufficient_evidence"
        diagnostics.append("no_literal_source_entity")
    else:
        status = "ready"
    return {"planner_version": PLANNER_VERSION, "query": query, "status": status,
            "source_context": _source_context_spans(query),
            "mentions": mentions, "resolved_entities": entities, "unresolved_selectors": list(dict.fromkeys(unresolved)),
            "operations": operations, "comparison": comparison, "comparison_kind": "operation_views" if view_comparison else "entities", "diagnostics": diagnostics,
            "limits": ["Literal labels and exact codes; span-local overlap suppression.",
                       "Qualified category token-subsequence is query interpretation, not a reviewed source alias.",
                       "Unsupported grammar and unresolved explicitly requested selectors remain explicit failures."]}
