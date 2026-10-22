"""Source-record identity lookup; name recognition grants no relation authority."""
from __future__ import annotations

import re

LEXICON_VERSION = "a1-source-lexicon-1.0"


def words(value):
    return re.findall(r"[a-z0-9]+", str(value).casefold())


def heading(node):
    found = re.fullmatch(r"(.*?)\s*\(([A-Z]+(?:-[A-Z]+)?)\)\s*", node["label"])
    return (found[1].strip(), found[2]) if found else (node["label"], None)


def source_dictionary(graph):
    """Index literal fields, not QA outputs, inferred synonyms or layout edges.

    Optional printed aliases must be part of the immutable source record and
    explicitly source-bound. The canonical A1 extractor currently supplies none.
    Caller graphs remain caller declarations; this function authenticates no PDF.
    """
    entries = []
    for node in graph["nodes"]:
        if node["kind"] not in {"process", "category", "root"}:
            continue
        label, code = heading(node) if node["kind"] == "category" else (node["label"], node.get("code"))
        proof = node.get("evidence", {})
        common = {"node_id": node["id"], "kind": node["kind"],
                  "evidence_ids": [proof["evidence_id"]] if proof.get("evidence_id") else [],
                  "edition_id": proof.get("edition_id"), "source_identity_id": proof.get("source_identity_id")}
        entries.append(dict(common, text=label, method="literal_label"))
        if code:
            entries.append(dict(common, text=code,
                method="exact_heading_code" if node["kind"] == "category" else "exact_process_code"))
        for alias in node.get("printed_aliases", []):
            if (isinstance(alias, dict) and isinstance(alias.get("text"), str) and alias["text"].strip()
                    and alias.get("verification") == "source_bound" and alias.get("basis") == "printed_alias"
                    and proof.get("verification") == "source_bound" and proof.get("record_id") == node["id"]
                    and proof.get("evidence_id") and proof.get("edition_id") and proof.get("source_identity_id")):
                entries.append(dict(common, text=alias["text"], method="source_bound_printed_alias"))
    return entries


def link_entities(graph, query, context_spans=()):
    grouped = {}
    for entry in source_dictionary(graph):
        text, method = entry["text"], entry["method"]
        code = method.endswith("_code")
        pattern = (r"(?<![\w-])" + re.escape(text) + r"(?![\w-])" if code else
                   r"(?<!\w)" + r"[\W_]+".join(map(re.escape, words(text))) + r"(?!\w)")
        if not words(text):
            continue
        flags = re.I if not code or entry["kind"] == "category" or len(text) >= 3 else 0
        for match in re.finditer(pattern, query, flags):
            if any(span["start"] < match.end() and match.start() < span["end"] for span in context_spans):
                continue
            if code and len(text) == 1 and match[0] != text:
                if not (query[:match.start()].rstrip().endswith("(") and query[match.end():].lstrip().startswith(")")):
                    continue
            grouped.setdefault((match.start(), match.end()), []).append(entry)
    root = next(node for node in graph["nodes"] if node["id"] == graph["root_id"])
    root_words = set(words(root["label"]))
    controls = {"central", "root", "top", "box", "node", "heading", "the", "chart"}
    navigation = r"\b(?:central|top|root)(?:[\s-]+[a-z]+){0,9}?[\s-]+(?:box|node|heading)\b|\b(?:chart\s+)?root\b"
    for match in re.finditer(navigation, query, re.I):
        payload = set(words(match[0])) - controls
        if not payload <= root_words:
            continue
        if any(first < match.end() and match.start() < last and any(item["node_id"] == root["id"] for item in entries)
               for (first,last), entries in grouped.items()):
            continue
        proof = root.get("evidence", {})
        grouped.setdefault((match.start(),match.end()), []).append({"node_id": root["id"], "kind":"root",
            "method":"chart_root_navigation", "evidence_ids":[proof["evidence_id"]] if proof.get("evidence_id") else []})
    mentions = []
    for (start, end), entries in sorted(grouped.items()):
        if any(first <= start and end <= last and (first < start or end < last)
               and any(not entry["method"].endswith("_code") for entry in others)
               for (first, last), others in grouped.items()):
            continue
        identifiers = list(dict.fromkeys(entry["node_id"] for entry in entries))
        mentions.append({"start": start, "end": end, "text": query[start:end],
            "candidate_ids": identifiers, "status": "resolved" if len(identifiers) == 1 else "ambiguous",
            "methods": list(dict.fromkeys(entry["method"] for entry in entries)),
            "kinds": list(dict.fromkeys(entry["kind"] for entry in entries)),
            "identity_evidence_ids": list(dict.fromkeys(identifier for entry in entries for identifier in entry["evidence_ids"]))})
    return mentions


def suggest_identities(graph, fragment):
    """Expose source-visible choices without silently accepting a partial name."""
    wanted = words(fragment)
    if not wanted or len(wanted) == 1 and (len(wanted[0]) < 3 or wanted[0] in {"the","and","for","from","with","this","that"}):
        return []
    matches = []
    for entry in source_dictionary(graph):
        if entry["method"].endswith("_code"):
            continue
        available = words(entry["text"])
        if any(available[index:index + len(wanted)] == wanted for index in range(len(available) - len(wanted) + 1)):
            matches.append(entry["node_id"])
    matches = list(dict.fromkeys(matches))
    # A single common corpus word is not a useful selector. Keep meaningful
    # sparse choices, with no best-guess admission or arbitrary top-k truncation.
    if len(wanted) == 1 and len(matches) > len(graph["nodes"]) / 2:
        return []
    return matches
