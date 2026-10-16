"""Read-only, source-bound lookup for three reviewed terminology entries.

The local registry contains licensed evidence and stays outside published source.
This adapter does not edit indexes, resolve cached graph statuses, or call models.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from src.standard_manifest import get_manifest
from src.terminology_mappings import parse_nonstandard_entry, merge_mapping_records

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "storage/terminology_registry.json"
_SOURCE_FILE = "storage/vdb_chunks_contextual.json"
# Dispatch scope only; source facts, senses and bindings remain registry-owned.
_TERMS = ("burn-through weld", "burn-through", "root gap")
_DASH_TRANSLATION = str.maketrans({character: "-" for character in "‐‑‒–—−"})


class TerminologyRegistryError(RuntimeError):
    code = "TERMINOLOGY_REGISTRY_INVALID"


def _require(condition):
    if not condition:
        raise TerminologyRegistryError("Reviewed terminology evidence is unavailable or stale; restore the reviewed local registry and matching sources.")


def _normal(text):
    return " ".join(str(text).split()).casefold()


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _unique(values):
    result = []
    seen = set()
    for value in values:
        key = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if key not in seen:
            result.append(deepcopy(value))
            seen.add(key)
    return result


def _matches(query):
    # Typography normalization only; retain hyphens as word-boundary guards.
    query = query.translate(_DASH_TRANSLATION)
    found = []
    for term in _TERMS:
        pattern = r"(?<![\w-])" + r"\s+".join(re.escape(word) for word in term.split()) + r"(?![\w-])"
        found.extend((match.start(), match.end(), term) for match in re.finditer(pattern, query, re.IGNORECASE))
    selected = []
    for start, end, term in sorted(found, key=lambda item: (item[0], -(item[1] - item[0]))):
        if not any(start < previous_end and end > previous_start for previous_start, previous_end, _ in selected):
            selected.append((start, end, term))
    return list(dict.fromkeys(term for _, _, term in selected))


def _qualified_conditional_intent(query, entry):
    """Require unambiguous intent in each local clause mentioning this entry.

    A marker belonging to another term, a negation, or a request contrasting
    standard/nonstandard senses must not choose a conditional sense globally.
    """
    text = _normal(str(query).translate(_DASH_TRANSLATION).replace("’", "'").replace("‘", "'"))
    def mentions(term, clause):
        pattern = r"(?<![\w-])" + r"\s+".join(re.escape(word) for word in term.split()) + r"(?![\w-])"
        return re.search(pattern, clause) is not None
    clauses = [clause for clause in re.split(r"[,;.!?\n]|\b(?:and|but|while|whereas)\b", text)
               if mentions(entry["term"], clause)]
    if not clauses:
        return False
    for clause in clauses:
        if (re.search(r"\b(?:no|not|cannot|never|neither|nor|without)\b|n't\b", clause)
                or re.search(r"\bstandard\b", clause)
                or any(term != _normal(entry["term"]) and mentions(term, clause) for term in _TERMS)):
            return False
        if not (re.search(r"\bnonstandard\b", clause) or any(
                mentions(record["preferred_term"], clause) for record in entry["records"])):
            return False
    return True


def _anchor(value, manifest, document):
    _require(isinstance(value, dict) and type(value.get("pdf_index")) is int)
    section = value.get("section_id")
    _require(manifest.resolve(section)["status"] == "exact" and any(
        anchor["pdf_index"] == value["pdf_index"] and anchor["printed_label"] == value.get("printed_label")
        for anchor in manifest.anchors(section)))
    labels = manifest.resolve(section).get("labels", [])
    return {"document_id": document["id"], "source_sha256": document["sha256"],
            "section_id": section, "pdf_index": value["pdf_index"],
            "section_label": labels[0] if labels else section,
            "pdf_page_ordinal": value["pdf_index"] + 1, "printed_label": value["printed_label"],
            "verification_state": "verified"}


def _load_entries(path, root, manifest):
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    document = manifest.document
    _require(isinstance(registry, dict) and registry.get("schema_version") == "1.0.0"
             and registry.get("document_id") == document["id"] and registry.get("source_sha256") == document["sha256"])
    files = registry.get("source_files")
    _require(isinstance(files, list) and len(files) == 1 and files[0].get("relpath") == _SOURCE_FILE)
    source_path = root / _SOURCE_FILE
    _require(source_path.resolve().is_relative_to(root.resolve()) and not source_path.is_symlink())
    source_bytes = source_path.read_bytes()
    _require(hashlib.sha256(source_bytes).hexdigest() == files[0].get("sha256"))
    data = json.loads(source_bytes)["data"]
    _require(isinstance(data, list))
    by_id = {}
    for row in data:
        _require(isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"] not in by_id)
        by_id[row["id"]] = row
    entries = registry.get("entries")
    _require(isinstance(entries, list) and 0 < len(entries) <= len(_TERMS))
    seen, reviewed = set(), []
    for entry in entries:
        _require(isinstance(entry, dict) and isinstance(entry.get("entry_id"), str) and entry["entry_id"] not in seen
                 and _normal(entry.get("term")) in _TERMS)
        seen.add(entry["entry_id"])
        original, projection = entry.get("original_entry"), entry.get("projection")
        _require(isinstance(original, dict) and isinstance(original.get("text"), str) and original["text"].strip()
                 and original.get("verification_state") == "verified")
        original_anchor = _anchor(original, manifest, document)
        _require(isinstance(projection, dict) and projection.get("kind") == "reviewed_parser_projection"
                 and projection.get("source_entry_id") == entry["entry_id"] and projection.get("is_raw_pdf_span") is False
                 and isinstance(projection.get("note"), str) and projection["note"].strip())
        parser = entry.get("parser_entry")
        _require(isinstance(parser, dict) and _normal(parser.get("term")) == _normal(entry["term"]))
        parsed = parse_nonstandard_entry(parser, manifest=manifest, ontology_nodes=entry.get("ontology_bindings", []))
        _require(parsed["records"] and not parsed["diagnostics"])
        _require(all(record["verification_state"] == "verified" for record in parsed["records"]))
        _require(all(_normal(record["preferred_term"]) in _normal(original["text"]) for record in parsed["records"]))
        _require(_anchor(parser["source"], manifest, document) == original_anchor)
        members = entry.get("evidence_members")
        _require(isinstance(members, list) and bool(members))
        supporting = []
        for member in members:
            _require(isinstance(member, dict) and member.get("source_file") == _SOURCE_FILE
                     and member.get("verification_state") == "verified")
            row = by_id.get(member.get("id"))
            excerpt = member.get("excerpt")
            _require(row is not None and row.get("full_doc_id") == member.get("full_doc_id")
                     and isinstance(row.get("content"), str) and _digest(row["content"]) == member.get("content_sha256")
                     and isinstance(excerpt, str) and excerpt.strip() and _digest(excerpt) == member.get("excerpt_sha256")
                     and _normal(excerpt) in _normal(row["content"]))
            boundaries = {}
            if any(key in member for key in ("raw_content_span", "span_space", "source_entry_refs")):
                span = member.get("raw_content_span")
                refs = member.get("source_entry_refs")
                _require(isinstance(span, list) and len(span) == 2 and all(type(v) is int for v in span)
                         and 0 <= span[0] < span[1] <= len(row["content"])
                         and row["content"][span[0]:span[1]] == excerpt
                         and isinstance(member.get("span_space"), str) and member["span_space"].strip()
                         and isinstance(refs, list) and refs and all(isinstance(ref, str) and ref for ref in refs))
                boundaries = {key: deepcopy(member[key]) for key in ("raw_content_span", "span_space", "source_entry_refs")}
            supporting.append({"id": member["id"], "full_doc_id": member["full_doc_id"], "content": excerpt,
                               "excerpt_sha256": member["excerpt_sha256"], "content_sha256": member["content_sha256"],
                               "source_anchors": [_anchor(member, manifest, document)], "verification_state": "verified",
                               "supports": deepcopy(member.get("supports", [])), **boundaries})
        standard = entry.get("standard_sense")
        if standard is not None:
            _require(isinstance(standard, dict) and isinstance(standard.get("text"), str) and standard["text"].strip()
                     and isinstance(standard.get("evidence_member_ids"), list) and standard["evidence_member_ids"]
                     and set(standard["evidence_member_ids"]).issubset({member["id"] for member in supporting})
                     and _normal(standard["text"]) in _normal(original["text"]))
        reviewed.append(dict(entry, records=parsed["records"], supporting_evidence=supporting,
                             original_anchor=original_anchor))
    return reviewed, document


def get_terminology_evidence(query, *, registry_path=REGISTRY_PATH, root=ROOT, manifest=None):
    """Return one complete evidence bundle, or None without I/O for unrelated text."""
    matched = _matches(str(query))
    if not matched:
        return None
    try:
        reviewed, document = _load_entries(registry_path, Path(root), manifest or get_manifest())
        selected = [entry for term in matched for entry in reviewed if _normal(entry["term"]) == term]
        _require(len(selected) == len(matched))
        records = merge_mapping_records([record for entry in selected for record in entry["records"]])
        _require(records and all(record["verification_state"] == "verified" for record in records))
        ambiguous, qualified = False, False
        for entry in selected:
            if entry.get("standard_sense"):
                explicit = _qualified_conditional_intent(query, entry)
                qualified |= explicit
                ambiguous |= not explicit
        status = "ambiguous_senses" if ambiguous else "qualified_mapping" if qualified else "mapped"
        supporting = _unique([member for entry in selected for member in entry["supporting_evidence"]])
        resolution = {"status": status, "matched_terms": matched,
                      "preferred_terms": list(dict.fromkeys(record["preferred_term"] for record in records)),
                      "target_ids": list(dict.fromkeys(record["target_id"] for record in records)),
                      "mapping_ids": [record["mapping_id"] for record in records],
                      "source_entry_ids": [entry["entry_id"] for entry in selected], "records": records,
                      "source_provenance": [{"entry_id": entry["entry_id"], "original_entry": entry["original_entry"],
                                             "source_anchor": entry["original_anchor"], "projection": entry["projection"],
                                             "standard_sense": entry.get("standard_sense")} for entry in selected]}
        identity = hashlib.sha256(json.dumps(resolution, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        bundle_id = "terminology:" + identity
        content = "Reviewed terminology evidence; preserve every target, sense and conditional qualification.\n"
        content += "\n".join(entry["original_entry"]["text"] for entry in selected)
        content += "\n" + "\n".join(member["content"] for member in supporting)
        if ambiguous:
            content += "\nBoth a standard sense and a conditional nonstandard use exist; explain both or request clarification."
        return {"id": bundle_id, "full_doc_id": bundle_id, "content": content, "evidence_type": "terminology_mapping",
                "selection_method": "reviewed_terminology_lookup", "mapping_ids": resolution["mapping_ids"],
                "terminology_mappings": records, "supporting_evidence": supporting,
                "source_anchors": [entry["original_anchor"] for entry in selected], "terminology_resolution": resolution}
    except TerminologyRegistryError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
        _require(False)
