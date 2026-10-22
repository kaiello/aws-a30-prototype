"""Compose source-linked requests into the existing typed graph operations.

This is bounded dictionary/grammar planning, not a general language model. Every
clause receives a coverage record, including clauses this grammar cannot plan.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re

from src.evidence_a1_lexicon import suggest_identities, words

_CUES = {
    "designation": {"abbreviation", "abbreviations", "acronym", "acronyms", "designation", "designations",
                    "code", "codes", "meaning", "meanings", "expand", "expansion", "expanded"},
    "category": {"family", "families", "category", "categories", "group", "groups", "box", "boxes", "enclosure", "enclosures"},
    "paths": {"path", "paths", "route", "routes", "chain", "chains", "hierarchy"},
    "parents": {"parent", "parents"},
    "operating_information": {"operating", "conditions", "temperature", "timing", "duration", "voltage", "amperage",
        "settings", "setting", "parameters", "parameter", "controls", "control", "speed", "procedure", "acceptance",
        "strength", "mechanism", "equipment", "current", "pressure"},
}
_GRAMMAR = set("""a an the and or for of in on from to with within into through between under beneath
    by at as is are was were be been do does did can could will would should shall has have it its their them they
    this that those these each both all every any only not no yes what which how why where whether i me us we
    give gives giving provide provides providing return returns returning show shows showing list lists listing
    tell tells include includes including indicate indicates explain explains describe describes identify identifies
    find finds name names please printed print source figure chart a1 according using about same broader broad
    direct directly immediate immediately recursive recursively descendant descendants child children subprocess
    subprocesses process processes entry entries row rows separate separately versus vs difference differences
    compare contrast stands stand means mean spells spell spelled out full complete entire everything also
    contains contain containing enclose encloses enclosed enclosing belongs belong part member type subtype relationship relationships relation relations
    observed observation observations indentation indented indent evidence support supports supporting establish
    establishes established needed additional alone reviewed semantic semantics confirmed accepted knowledge
    confirm justification interpretation justify prove proves true false visible shown layout lexical sharing share
    words word labels label prefix prefixes similar common make makes imply implies top root up back connect
    connects connected connection nesting nested below above underlies missing information values value unavailable
    available tell alone actually universally universal normative enough alone require requires required supported
    unsupported difference longer short shorter individually separately vs basis given since because then next
    first second third both respective respectively such whether rather than instead schematic supply supplied
    interpret interpreted interpretation go goes lead leads leading
    name naming spelling spelled singular plural include including get gets
    """.split()) | set().union(*_CUES.values())
_IDENTITY_HEAD = r"\b(?:identify|name)\s+(?:the\s+)?(?:process|entry)\b"
_RELATION_OPERATOR = r"\b(?:subtype|type|part|member)\s+of\b|\b(?:directly\s+)?(?:under|beneath)\b"


def _mask(query, mentions, context):
    characters = list(query)
    for item in [*mentions, *context]:
        characters[item["start"]:item["end"]] = " " * (item["end"] - item["start"])
    return "".join(characters)


def _language_roles(graph, text, outside, kinds, previous_kinds, *, lexical_premise=False):
    """Account for recognized argument/framing spans, not a word allowlist.

    An unknown entity/property such as ``Mystery bind`` or ``cost`` remains
    uncovered. Source-information fields are captured as requested fields and
    stay unsupported by the chart; they are never treated as supplied values.
    """
    roles = []
    def capture(role, pattern, target_kinds=()):
        for match in re.finditer(pattern, outside, re.I):
            roles.append({"start":match.start(),"end":match.end(),"text":text[match.start():match.end()],
                          "role":role,"target_kinds":list(target_kinds)})
    # Match on original text: the preceding noun can already be masked as a
    # source identity. Only the suffix is grammar; an unknown noun stays visible.
    for match in re.finditer(r"(?<=\w)['\u2019]s\b", text, re.I):
        roles.append({"start":match.start(),"end":match.end(),"text":match[0],
                      "role":"possessive_grammar","target_kinds":[]})
    for match in re.finditer(r"\bstate\b", outside, re.I):
        command_position = re.search(r"(?:^|,\s*|\b(?:then|also)\s+)(?:please\s+)?$",outside[:match.start()],re.I)
        targets = [kind for kind,cues in _CUES.items() if kind in kinds and set(words(outside[match.end():])) & cues]
        if command_position and targets:
            roles.append({"start":match.start(),"end":match.end(),"text":text[match.start():match.end()],
                          "role":"request_verb","target_kinds":targets})
    capture("source_frame", r"\b(?:in|from|within|on)\s+(?:this|the)\s+(?:chart|image|figure)\b")
    capture("source_record_reference", r"\b(?:the\s+)?(?:entry|row|process)\s+(?:marked|labelled|labeled)\b")
    heads = {"designation":r"process\s+name", "category":r"category|group|box", "parents":r"parent",
             "epistemic_limits":r"subtype|relationship|relation|claim", "layout_relation":r"subtype|relationship|relation|claim"}
    for kind, head in heads.items():
        if kind in kinds:
            capture("attribute_modifier", r"\b(?:(?:printed|displayed|visible|observed|verified|confirmed|semantic|immediate|immediately|direct|directly|enclosing|larger|broader)\s+)+(?:"+head+r")\b", [kind])
    if "paths" in kinds:
        capture("path_command", r"\b(?:trace|follow)\s+(?:the\s+)?(?:displayed\s+)?(?:route|path|chain)\b", ["paths"])
        capture("path_origin", r"\bstarting\s+from\b", ["paths"])
        capture("path_support", r"\bevidence[\s-]+backed\s+(?:route|path|chain)\b", ["paths"])
        capture("path_node_fields", r"\bnaming\s+(?:every|each|all)\s+intermediate\s+(?:process|group)(?:\s+or\s+(?:process|group))?\b", ["paths"])
        capture("path_hop_fields", r"\b(?:the\s+)?kind\s+of\s+(?:visible\s+)?connection\s+at\s+each\s+step\b|\bevidence\s+for\s+each\s+link\b", ["paths"])
        capture("root_navigation_frame", r"\bcentral\b|\btop\b", ["paths"])
    if len(kinds & {"designation","category","parents"}) and re.search(r"\bside\s+by\s+side\b", outside, re.I):
        capture("comparison_frame", r"\bput\b|\bside\s+by\s+side\b", kinds)
    if kinds & {"layout_relation","epistemic_limits","parents"}:
        capture("semantic_question_frame", r"\b(?:can|may)\s+i\s+treat\b|\b(?:just\s+)?because\s+of\s+(?:its|their|the)\s+(?:position|placement)\b", kinds)
        capture("layout_parent_field", r"\b(?:either|both|each)\s+as\s+directly\s+indented\s+under\s+(?:another|any\s+other)\s+process\b", ["parents"])
        capture("epistemic_comparison", r"\bdistinguish\s+(?:displayed\s+)?indentation\s+from\s+(?:a\s+)?confirmed\s+subtype\s+claim\b", ["epistemic_limits"])
    if "operating_information" in kinds:
        for match in re.finditer(r"\b(?:what|which)\s+(.+?)\s+(?:does|do|can|is|are)\b",outside,re.I):
            fields = [field.strip() for field in re.split(r",|\band\b",text[match.start(1):match.end(1)],flags=re.I) if field.strip()]
            unknown = [field for field in fields if not set(words(field)) & _CUES["operating_information"]]
            roles.append({"start":match.start(),"end":match.end(),"text":text[match.start():match.end()],
                "role":"requested_source_information_fields","target_kinds":["operating_information"],
                "requested_fields":fields,"unsupported_fields":unknown})
        capture("source_information_predicate", r"\b(?:prescribe|prescribes|specify|specifies|supply|supplies)\b", ["operating_information"])
    root = next(node for node in graph["nodes"] if node["id"] == graph["root_id"])
    root_terms = [word for word in words(root["label"]) if word not in {"the","and","of"}]
    if "category" in kinds and root_terms:
        capture("source_title_category_modifier", r"\b(?:"+"|".join(map(re.escape,root_terms))+r")\s+(?:group|box|category)\b", ["category"])
    if "row_partition" in kinds:
        capture("partition_field", r"\bunindented\s+(?:process\s+)?(?:rows|entries|processes)\b|\bindented\s+(?:rows|entries|processes)\b", ["row_partition"])
    source_followup = (r"\b(?:if\s+not,?\s*)?(?:identify|state|explain)\s+what\s+information\s+is\s+missing\b|"
                       r"\b(?:state|explain)\s+what\s+(?:this|the)\s+(?:image|chart|figure)\s+can\s+and\s+cannot\s+establish\b|"
                       r"\btell\s+me\s+what\s+is\s+actually\s+shown\b")
    if previous_kinds & {"operating_information","epistemic_limits","layout_relation","membership"}:
        capture("source_followup", source_followup, previous_kinds)
    if previous_kinds >= {"direct_children","descendants"}:
        capture("list_comparison", r"\bexplain\s+(?:the\s+)?difference\s+(?:in|between)\s+(?:the\s+)?(?:two|these|those|both)\s+lists\b", previous_kinds)
    if lexical_premise:
        capture("lexical_premise", r"[\"'\u2018\u201c][^\"'\u2019\u201d]+[\"'\u2019\u201d]", ["epistemic_limits"])
    return roles


def _clauses(query, masked):
    # Entity spans have already been blanked: "and" inside a source label or
    # coordinated names is not a language-clause boundary.
    splits = list(re.finditer(r"[?;]|\.(?=\s|$)|\band\b(?=\s+(?:(?:then|also)\s+)?(?:what|which|how|why|where|give|show|provide|list|"
                             r"explain|describe|include|its|their|all|every|the\s+[a-z])\b)", masked, re.I))
    cursor, clauses = 0, []
    for split in [*splits, None]:
        if split is not None and split[0].casefold() == "and":
            # A coordinated identity field can share a trailing selector with
            # another field: "identify the process and its parent for <name>".
            # This applies only before a selector in the same syntactic request;
            # it never borrows a name from a later sentence or independent clause.
            leading_identity = re.search(_IDENTITY_HEAD+r"\s*$",query[cursor:split.start()],re.I)
            trailing_field = re.match(r"\s+(?:its|their|the)\s+(.+?)\s+(?:for|of)\s+([^?;.]+)",query[split.end():],re.I)
            if leading_identity and trailing_field and any(set(words(trailing_field[1])) & _CUES[kind]
                    for kind in ("designation","category","parents")):
                continue
        end = len(query) if split is None else split.start()
        first = cursor
        while first < end and query[first].isspace():
            first += 1
        if query[first:end].strip():
            clauses.append((first, end, query[first:end]))
        if split is not None:
            cursor = split.end()
    return clauses


def _relation_request(graph, text, mentions):
    """Bind predicate argument spans; question modality does not change roles."""
    predicate = re.search(_RELATION_OPERATOR,text,re.I)
    if not predicate:
        return None
    left = sorted((m for m in mentions if m["status"]=="resolved" and m["end"]<=predicate.start()),key=lambda m:m["end"])
    right = [m for m in mentions if m["status"]=="resolved" and m["start"]>=predicate.end()]
    if not left or not right:
        return None
    child = left[-1]["candidate_ids"][0]
    targets = list(dict.fromkeys(m["candidate_ids"][0] for m in right))
    nodes = {node["id"]:node for node in graph["nodes"]}
    kind = "membership" if all(nodes[target]["kind"]=="category" for target in targets) else "layout_relation"
    return {"kind":kind,"subject_ids":[child,*targets],"left_ids":[child],"right_ids":targets,
            **({"directness":True} if re.search(r"\bdirectly\b",predicate[0],re.I) else {})}


def _bound_relation_predicate_roles(text, mentions, relation, source_context):
    """Account for a placement verb only after both relation arguments bind."""
    operator = re.search(_RELATION_OPERATOR,text,re.I)
    if not relation or not operator:
        return []
    left = [mention for mention in mentions if mention["status"]=="resolved"
            and mention["end"]<=operator.start() and mention["candidate_ids"][0] in relation["left_ids"]]
    right = [mention for mention in mentions if mention["status"]=="resolved"
             and mention["start"]>=operator.end() and mention["candidate_ids"][0] in relation["right_ids"]]
    if not left or not right:
        return []
    subject = max(left,key=lambda mention:mention["end"])
    verb = re.search(r"\b(?:place|show|list|put|depict|indicate|indent)\b(?=\s+(?:the\s+)?$)",text[:subject["start"]],re.I)
    if not verb:
        return []
    prefix = text[:verb.start()]
    for span in reversed(source_context):
        if span["end"]<=verb.start():
            prefix = prefix[:span["start"]]+"chart"+prefix[span["end"]:]
    if not re.fullmatch(r"\s*(?:please\s+)?(?:(?:does|do)\s+(?:(?:this|the)\s+)?(?:chart|image|figure|indentation)\s+)?",prefix,re.I):
        return []
    return [{"start":verb.start(),"end":verb.end(),"text":verb[0],"role":"bound_relation_predicate",
             "target_kinds":[relation["kind"]],
             "argument_spans":[[subject["start"],subject["end"]],*[[mention["start"],mention["end"]] for mention in right]]}]


def _path_parameters(graph, text, mentions):
    def identifiers(first, last):
        selected = [identifier for mention in mentions if first <= mention["start"] and mention["end"] <= last
                    and mention["status"] == "resolved" for identifier in mention["candidate_ids"]]
        if re.search(r"\b(?:root|top)\b", text[first:last], re.I):
            selected.insert(0, graph["root_id"])
        return list(dict.fromkeys(selected))
    directed = re.search(r"\bfrom\s+(.+?)\s+(?:to|towards?)\s+(.+)$", text, re.I)
    if directed is None:
        directed = re.search(r"\bbetween\s+(.+?)\s+and\s+(.+)$", text, re.I)
    if directed:
        starts, ends = identifiers(*directed.span(1)), identifiers(*directed.span(2))
        if starts and ends:
            explicit_waypoints = bool(re.search(r"\b(?:through|via)\b", directed[1], re.I))
            return {"start_ids": starts[:1] if explicit_waypoints else starts, "end_ids": ends,
                    "waypoint_ids": starts[1:] if explicit_waypoints else [], "requested_direction": "from_to"}
    selected = identifiers(0, len(text))
    nonroot = [identifier for identifier in selected if identifier != graph["root_id"]]
    if len(nonroot) == 1 and re.search(r"\b(?:up|back)\b", text, re.I) and re.search(r"\b(?:root|top)\b", text, re.I):
        return {"start_ids": nonroot, "end_ids": [graph["root_id"]], "requested_direction": "from_to"}
    if len(selected) == 2 and re.search(r"\b(?:between|connect\w*)\b", text, re.I):
        return {"start_ids": selected[:1], "end_ids": selected[1:], "requested_direction": "from_to"}
    return {}


def compose_plan(graph, query, legacy, resolve_mentions, context_spans, *, concept_bindings=None):
    mentions = resolve_mentions(graph, query)
    for mention in mentions:
        if concept_bindings is not None:
            mention["candidate_concept_ids"] = [concept_bindings[node] for node in mention["candidate_ids"] if node in concept_bindings]
    context = context_spans(query)
    entities = list(dict.fromkeys(m["candidate_ids"][0] for m in mentions if m["status"] == "resolved"))
    by_id = {node["id"]: node for node in graph["nodes"]}
    operations, parts, previous_subjects, previous_children = [], [], [], []
    language_roles, previous_operation_ids, previous_kinds = [], [], set()
    operation_keys = {}

    def part(text, span, kind, subjects, candidates=(), reason=None):
        item = {"id": f"intent:{len(parts)+1:03d}", "text": text, "span": list(span), "kind": kind,
                "subject_ids": list(subjects), "operation_ids": [], "status": "planned"}
        if reason:
            item.update(status="ambiguous" if candidates else "unsupported", reason=reason)
        if candidates:
            item["candidate_ids"] = list(candidates)
        parts.append(item)
        return item

    def operation(request, intent):
        request = deepcopy(request)
        request.setdefault("query_layer", "knowledge" if request["kind"] in {"designation", "category", "membership"} else "evidence")
        identity = json.dumps([intent["span"], request], sort_keys=True, separators=(",", ":"))
        if identity not in operation_keys:
            request.update(operation_id=f"op:{len(operations)+1:03d}", request_ids=[])
            operation_keys[identity] = request
            operations.append(request)
        ready = operation_keys[identity]
        ready["request_ids"].append(intent["id"])
        intent["operation_ids"].append(ready["operation_id"])
        return ready["operation_id"]

    def clarify_unbound_parts(span, resolution):
        # Keep every requested field linked to the unresolved argument. A
        # dictionary choice list does not execute an operation or accept a name.
        for intent in parts:
            if intent["span"] == list(span) and intent.get("reason") == "no_source_linked_subject":
                intent.update(status="ambiguous",reason="ambiguous_source_identity",
                              candidate_ids=list(resolution["candidate_ids"]),
                              resolution_part_ids=[resolution["id"]])

    for first, last, text in _clauses(query, _mask(query, mentions, context)):
        local = [dict(m, start=m["start"]-first, end=m["end"]-first) for m in mentions if first <= m["start"] and m["end"] <= last]
        parsed = legacy(graph, text)
        # The relation parser can resolve a qualified category token-subsequence.
        # Account for that interpretation span without declaring a source alias.
        for mention in parsed["mentions"]:
            if not any(m["start"] == mention["start"] and m["end"] == mention["end"] for m in local):
                qualified = dict(mention,identity_evidence_ids=list(dict.fromkeys(by_id[node].get("evidence",{}).get("evidence_id")
                    for node in mention["candidate_ids"] if by_id[node].get("evidence",{}).get("evidence_id"))),
                    qualification="query_interpretation_not_verified_alias")
                local.append(qualified)
                mentions.append(dict(qualified, start=first+mention["start"],end=first+mention["end"],
                    qualification="query_interpretation_not_verified_alias"))
        local_context = context_spans(text)
        outside = _mask(text, local, local_context)
        tokens = set(words(outside))
        if not tokens and local_context:
            continue
        subjects = list(dict.fromkeys(m["candidate_ids"][0] for m in local if m["status"] == "resolved"))
        explicit_context_changed = bool(subjects and subjects != previous_subjects)
        relation = _relation_request(graph,text,local)
        if relation and not any(item["kind"] in {"membership","layout_relation"} for item in parsed["operations"]):
            parsed["operations"].append(relation)
        preview_kinds = {item["kind"] for item in parsed["operations"]}
        preview_kinds.update(kind for kind,cues in _CUES.items() if tokens & cues)
        identity_request = bool(re.search(_IDENTITY_HEAD,outside,re.I))
        if identity_request:
            preview_kinds.add("designation")
        partition = "unindented" in tokens and "indented" in tokens
        if partition:
            preview_kinds.add("row_partition")
        parent_field = bool(re.search(r"\bdirectly\s+indented\s+under\s+(?:another|any\s+other)\s+process\b",outside,re.I))
        if parent_field:
            preview_kinds.add("parents")
        context_kinds = previous_kinds | {item["kind"] for item in operations if item["operation_id"] in previous_children}
        roles = _language_roles(graph,text,outside,preview_kinds,context_kinds if not local else set(),
            lexical_premise=any(item.get("lexical_overlap") for item in parsed["operations"]))
        roles.extend(_bound_relation_predicate_roles(text,local,relation,local_context))
        for role in roles:
            traced = dict(role,start=first+role["start"],end=first+role["end"])
            if "argument_spans" in role:
                traced["argument_spans"] = [[first+start,first+end] for start,end in role["argument_spans"]]
            language_roles.append(traced)
        residual_text = _mask(outside,roles,[])
        residual = [token for token in words(residual_text) if token not in _GRAMMAR]
        anaphora = not local and bool(tokens & {"it", "its", "them", "their", "they", "those", "these"})
        attributes = preview_kinds & {"designation","category","parents"}
        ellipsis = not local and bool(attributes) and bool(previous_subjects) and not residual
        plural_reference = bool(tokens & {"each","both","their","them","they","those","these","acronyms","abbreviations","codes","names","categories","parents"})
        ambiguous_anaphora = (anaphora or ellipsis) and not plural_reference and len(previous_subjects) > 1
        if (anaphora or ellipsis) and not residual and not ambiguous_anaphora:
            subjects = list(previous_subjects)
        if ambiguous_anaphora:
            part(text, (first,last), "entity_resolution", [], previous_subjects, "singular_reference_has_multiple_antecedents")
        if not subjects and tokens & {"root", "top"}:
            subjects = [graph["root_id"]]
        process_ids = [identifier for identifier in subjects if by_id[identifier]["kind"] == "process"]
        requested = deepcopy(parsed["operations"])
        if not local and not residual and any(role["role"] in {"source_followup","list_comparison"} for role in roles):
            requested = []
        for request in requested:
            if not request["subject_ids"]:
                request["subject_ids"] = list(process_ids if request["kind"] in {"designation", "category"} else subjects)
        if partition:
            requested = [item for item in requested if item["kind"] not in {"direct_children","descendants","epistemic_limits"}]
            requested.append({"kind":"row_partition","subject_ids":[identifier for identifier in subjects if by_id[identifier]["kind"]=="category"]})
        if parent_field and not any(item["kind"]=="parents" for item in requested):
            requested.append({"kind":"parents","subject_ids":process_ids})
        requested_kinds = {item["kind"] for item in requested}
        for kind, cues in _CUES.items():
            wanted = bool(tokens & cues)
            if kind == "designation":
                wanted |= identity_request
                wanted |= bool(re.search(r"\bstand(?:s)?\s+for\b|\bspell(?:ed)?\s+out\b", outside, re.I))
                wanted |= bool(subjects and any("_code" in method for mention in local for method in mention["methods"])
                               and re.search(r"\b(?:what|name|mean|means|meaning|expand)\b", outside, re.I))
            if kind == "paths":
                wanted |= bool(tokens & {"connect", "connects", "connected"} and len(subjects) > 1)
            if kind == "parents" and "epistemic_limits" in requested_kinds:
                wanted = False
            if wanted and kind not in requested_kinds:
                selected = process_ids if kind == "category" else subjects
                request = {"kind": kind, "subject_ids": list(selected)}
                if kind == "paths":
                    request.update(_path_parameters(graph, text, local))
                requested.append(request)
                requested_kinds.add(kind)
        row_list = bool(tokens & {"list","show","give","provide","return","identify"}) and bool(tokens & {"rows","entries","children","processes","subprocesses"})
        immediate_rows = row_list and bool(tokens & {"direct","directly","immediate","immediately"}) and bool(tokens & {"under","beneath","below","children"})
        if immediate_rows and not requested_kinds & {"direct_children","row_partition","layout_relation","membership"}:
            requested.append({"kind":"direct_children","subject_ids":list(subjects)})
            requested_kinds.add("direct_children")
        if "children" in tokens and not tokens & {"all", "every", "recursive", "recursively", "descendants"} and not requested_kinds & {"direct_children", "descendants", "layout_relation", "membership"}:
            requested.append({"kind": "direct_children", "subject_ids": list(subjects)})
        if tokens & {"all", "every", "everything", "entire"} and tokens & {"processes", "entries", "rows", "children", "subprocesses"} and not requested_kinds & {"descendants", "direct_children", "layout_relation", "membership"}:
            requested.append({"kind": "descendants", "subject_ids": list(subjects)})
        expanded = []
        for request in requested:
            if request["kind"] == "paths":
                parameters = _path_parameters(graph, text, local)
                if parameters:
                    request.update(parameters)
                if len(request.get("start_ids", [])) > 1:
                    for start in request["start_ids"]:
                        expanded.append(dict(request, start_ids=[start], subject_ids=list(dict.fromkeys(
                            [start] + request["end_ids"] + request.get("waypoint_ids", [])))))
                    continue
            expanded.append(request)
        requested = expanded
        child_requests = [item for item in requested if item["kind"] in {"direct_children", "descendants","row_partition"}]
        child_kinds = [item["kind"] for item in child_requests]
        if child_requests:
            for request in requested:
                if request["kind"]=="category":
                    request.update(use_returned_children=True,after_operations=child_kinds,subject_scope="returned_children")
        # Pronouns after a list refer to the returned rows, not the list selector.
        if not local and (anaphora or ellipsis) and not ambiguous_anaphora and previous_children:
            for request in requested:
                if request["kind"] in {"designation", "category"}:
                    request.update(use_returned_children=True, dependency_operation_ids=previous_children, subject_scope="returned_children")
        local_child_ids, local_operations = [], []
        for request in requested:
            if request.get("use_returned_children"):
                request["subject_ids"] = list(subjects)
                request["selector_subject_ids"] = list(subjects)
            intent = part(text, (first, last), request["kind"], request["subject_ids"])
            if request["kind"] == "designation" and child_requests:
                for child in child_requests:
                    operation(child, intent)
                intent.update(subject_scope="returned_children",subject_ids=[],selector_subject_ids=list(subjects))
            elif not request["subject_ids"] and not request.get("use_returned_children") and request["kind"] not in {"epistemic_limits", "operating_information"}:
                intent.update(status="unsupported", reason="no_source_linked_subject")
            else:
                if request.get("use_returned_children"):
                    intent.update(subject_scope="returned_children",subject_ids=[],selector_subject_ids=list(request["subject_ids"]))
                if request["kind"] == "paths" and not request.get("start_ids"):
                    request.update(_path_parameters(graph, text, local))
                if tokens & {"accepted", "knowledge"}:
                    request["query_layer"] = "knowledge"
                identifier = operation(request, intent)
                local_operations.append(identifier)
                if request["kind"] in {"direct_children", "descendants","row_partition"}:
                    local_child_ids.append(identifier)
        for completed in operations:
            if completed["operation_id"] in local_operations and completed.get("use_returned_children") and not completed.get("dependency_operation_ids"):
                completed["dependency_operation_ids"] = list(local_child_ids)
        # An explicit abbreviation request can already be included in list rows.
        if tokens & _CUES["designation"] and child_requests and not any(p["span"] == [first,last] and p["kind"] == "designation" for p in parts):
            intent = part(text, (first,last), "designation", subjects)
            intent.update(subject_scope="returned_children",subject_ids=[],selector_subject_ids=list(subjects))
            for child in child_requests:
                operation(child, intent)
        for mention in local:
            if mention["status"] == "ambiguous":
                resolution = part(mention["text"], (first+mention["start"],first+mention["end"]), "entity_resolution", [], mention["candidate_ids"], "ambiguous_source_identity")
                clarify_unbound_parts((first,last),resolution)
        for role in roles:
            for field in role.get("unsupported_fields",[]):
                part(field,(first+role["start"],first+role["end"]),"operating_information",subjects,
                     reason="requested_information_field_not_supported")
            if role["role"] in {"source_followup","list_comparison"} and previous_operation_ids and not residual:
                contextual = part(text,(first,last),role["role"],[])
                contextual["operation_ids"] = list(previous_operation_ids)
                contextual["subject_scope"] = "prior_request"
                for completed in operations:
                    if completed["operation_id"] in contextual["operation_ids"]:
                        completed["request_ids"].append(contextual["id"])
        missing = []
        for selector in parsed["unresolved_selectors"]:
            if set(words(selector)) & set(residual):
                missing.append(selector)
        if residual and not missing:
            missing.append(" ".join(residual))
        for selector in dict.fromkeys(missing):
            candidates = suggest_identities(graph, selector)
            kind = "entity_resolution" if candidates or not local else "unsupported_intent"
            resolution = part(selector, (first,last), kind, [], candidates, "uncovered_request_content")
            if candidates:
                clarify_unbound_parts((first,last),resolution)
        if not requested and not child_requests and not missing and not any(role["role"] in {"source_followup","list_comparison"} for role in roles):
            part(text, (first,last), "unsupported_intent", subjects, reason="query_operation_not_supported")
        if subjects:
            previous_subjects = subjects
        if child_kinds:
            previous_children = local_child_ids
        elif explicit_context_changed:
            previous_children = []
        if local_operations:
            previous_operation_ids = local_operations
            previous_kinds = {item["kind"] for item in requested}
        if any(mention["status"]=="ambiguous" for mention in local) or missing and not local:
            # A new unresolved identity blocks later pronouns; it cannot borrow
            # subject/list authority from an older, independently answered clause.
            previous_subjects, previous_children, previous_operation_ids, previous_kinds = [], [], [], set()
    mentions.sort(key=lambda item:(item["start"],item["end"]))
    entities = list(dict.fromkeys(m["candidate_ids"][0] for m in mentions if m["status"]=="resolved"))
    if concept_bindings is not None:
        for mention in mentions:
            mention["candidate_concept_ids"] = [concept_bindings[node] for node in mention["candidate_ids"] if node in concept_bindings]
    unresolved = [item for item in parts if item["status"] != "planned"]
    status = ("clarification_required" if any(item["status"] == "ambiguous" for item in unresolved) else
              "insufficient_evidence" if unresolved and operations else "capability_gap" if unresolved or not operations else "ready")
    return {"planner_version": "a1-graph-planner-1.6.1", "query": query, "status": status,
        "source_context": context, "mentions": mentions, "resolved_entities": entities,
        "unresolved_selectors": list(dict.fromkeys(item["text"] for item in unresolved if item["kind"] == "entity_resolution")),
        "operations": operations, "requested_parts": parts, "unresolved_parts": unresolved,"language_roles":language_roles,
        "comparison": bool(re.search(r"\b(?:compare|contrast|versus|differences?)\b", query, re.I)),
        "comparison_kind": "operation_views" if {item["kind"] for item in operations} >= {"direct_children", "descendants"} else "entities",
        "diagnostics": list(dict.fromkeys(item.get("reason", "request_not_planned") for item in unresolved)),
        "limits": ["Source-backed literal names/codes and explicitly source-bound printed aliases only.",
                   "Qualified category-token interpretation and chart-root navigation are marked query interpretation, not verified aliases.",
                   "Bounded clause/cue grammar; unrecognized requests remain explicit and do not establish general NLQ.",
                   "Identity matching and spelling normalization do not admit semantic relationships."]}
