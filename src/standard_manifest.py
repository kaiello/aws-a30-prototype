"""Source-bound metadata lookup. No config, models, database or write side effects."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config/aws_a30_2020_manifest.json"
SOURCE_PATH = ROOT / "data/AWS_A3.0_2020.pdf"


class ManifestError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


def _require(condition, message):
    if not condition:
        raise ManifestError("MANIFEST_INVALID", message)


def _record(value, fields):
    _require(isinstance(value, dict) and set(value) == set(fields.split()), "Unexpected record fields.")


def _integer(value, minimum=0):
    _require(type(value) is int and value >= minimum, "Invalid integer.")


def _text(value):
    _require(isinstance(value, str) and bool(value.strip()), "Invalid text.")


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), "Invalid SHA-256.")


def _json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate JSON key.")
            result[key] = value
        return result
    def constant(value):
        raise ManifestError("MANIFEST_INVALID", "Non-finite JSON number.")
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except FileNotFoundError as exc:
        raise ManifestError("MANIFEST_MISSING", "Required metadata file is absent.") from exc
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ManifestError("MANIFEST_INVALID", "Metadata is not valid UTF-8 JSON.") from exc
    except OSError as exc:
        raise ManifestError("MANIFEST_UNAVAILABLE", "Cannot read required metadata.") from exc


def _safe_path(root, relpath, allowed):
    _text(relpath)
    _require(not any(c in relpath for c in "\\:%\x00") and not any(ord(c) < 32 for c in relpath), "Invalid relative path.")
    path = PurePosixPath(relpath)
    _require(not path.is_absolute() and not any(p in {"", ".", ".."} or p.endswith((" ", ".")) for p in relpath.split("/")), "Invalid relative path.")
    _require(any(relpath.startswith(prefix + "/") for prefix in allowed), "Path outside approved roots.")
    target = root / path
    _require(target.resolve().is_relative_to(root.resolve()), "Resolved path escapes repository.")
    for part in [target, *target.parents]:
        if part == root:
            break
        _require(not part.is_symlink() and not getattr(part, "is_junction", lambda: False)(), "Linked metadata assets are not allowed.")
    return target


def _validate(data, root):
    _record(data, "schema_version manifest_revision document sections figures tables links legacy_aliases")
    _require(data["schema_version"] == "1.0.0", "Unsupported schema version.")
    _integer(data["manifest_revision"], 1)
    doc = data["document"]
    _record(doc, "id standard_id title publisher edition edition_number pdf_relpath sha256 byte_length page_count identity_pdf_indices verification pages")
    _require((doc["id"], doc["standard_id"], doc["edition"], doc["edition_number"], doc["pdf_relpath"]) ==
             ("doc:aws_a30_2020", "AWS_A3.0_2020", "2020", 13, "data/AWS_A3.0_2020.pdf"), "Unsupported document identity.")
    for key in ["title", "publisher"]:
        _text(doc[key])
    _digest(doc["sha256"])
    _integer(doc["byte_length"], 1)
    _integer(doc["page_count"], 1)
    def indices(values):
        _require(isinstance(values, list), "Expected page indices.")
        for value in values:
            _integer(value)
            _require(value < doc["page_count"], "Page index out of bounds.")
        _require(len(values) == len(set(values)), "Duplicate page index.")
    def verification(value):
        _record(value, "state source_sha256 method verifier verified_at_utc evidence_pdf_indices note")
        _require(value["state"] in {"candidate", "verified", "rejected", "stale"}, "Invalid verification state.")
        _require(value["source_sha256"] == doc["sha256"], "Verification belongs to another source.")
        _require(value["method"] in {"caption_text", "manual_visual", "legacy_unverified", "render_match"}, "Invalid verification method.")
        indices(value["evidence_pdf_indices"])
        _text(value["note"])
        if value["state"] == "verified":
            _text(value["verifier"])
            _require(value["method"] != "legacy_unverified" and bool(value["evidence_pdf_indices"]), "Unsupported verification claim.")
            _require(isinstance(value["verified_at_utc"], str) and datetime.fromisoformat(value["verified_at_utc"]).utcoffset() is not None, "Verification timestamp needs timezone.")
        else:
            _require(value["verifier"] is None and value["verified_at_utc"] is None, "Unverified record claims a verifier.")
    indices(doc["identity_pdf_indices"])
    verification(doc["verification"])
    _require(isinstance(doc["pages"], list) and len(doc["pages"]) == doc["page_count"], "Incomplete page map.")
    for index, page in enumerate(doc["pages"]):
        _record(page, "pdf_index printed_label role")
        _integer(page["pdf_index"])
        _require(page["pdf_index"] == index, "Page map must be ordered and complete.")
        _require(page["printed_label"] is None or isinstance(page["printed_label"], str), "Invalid printed label.")
        _require(page["role"] in {"front_matter", "body", "blank", "back"}, "Invalid page role.")
    by_id, labels, sections = {}, {}, {}
    for group in ["sections", "figures", "tables"]:
        _require(isinstance(data[group], list) and bool(data[group]), "Empty inventory.")
        for item in data[group]:
            fields = "id label title spans normative_status qualification_pdf_indices verification" if group == "sections" else "id label title parent_id anchors assets"
            _record(item, fields)
            for field in ["id", "label", "title"]:
                _text(item[field])
            _require(item["id"] not in by_id and item["label"].casefold() not in labels, "Duplicate ID or label.")
            prefix = {"sections": "clause:", "figures": "figure:", "tables": "table:"}[group]
            _require(item["id"].startswith(prefix), "Wrong ID namespace.")
            by_id[item["id"]] = item
            labels[item["label"].casefold()] = item
            if group == "sections":
                _require(item["normative_status"] in {"normative", "informative", "conflicting", "unknown"}, "Invalid applicability.")
                indices(item["qualification_pdf_indices"])
                verification(item["verification"])
                _require(isinstance(item["spans"], list) and bool(item["spans"]), "Missing section span.")
                for span in item["spans"]:
                    _record(span, "start_pdf_index end_pdf_index")
                    indices([span["start_pdf_index"]])
                    indices([span["end_pdf_index"]])
                    _require(span["start_pdf_index"] <= span["end_pdf_index"], "Reversed span.")
                sections[item["id"]] = item
                continue
            parent = sections.get(item["parent_id"])
            _require(parent is not None, "Missing parent section.")
            expected_id = prefix + item["label"].lower().replace(" ", "_")
            _require(item["id"] == expected_id, "ID does not preserve the canonical label.")
            _require(isinstance(item["anchors"], list) and bool(item["anchors"]), "Missing anchors.")
            seen_pages = []
            for order, anchor in enumerate(item["anchors"]):
                _record(anchor, "pdf_index printed_label order role region verification")
                indices([anchor["pdf_index"]])
                _integer(anchor["order"])
                _require(anchor["order"] == order and anchor["role"] == ("start" if order == 0 else "continuation"), "Invalid continuation order.")
                page = anchor["pdf_index"]
                _require(anchor["printed_label"] == doc["pages"][page]["printed_label"], "Printed page mismatch.")
                _require(any(s["start_pdf_index"] <= page <= s["end_pdf_index"] for s in parent["spans"]), "Anchor outside parent.")
                seen_pages.append(page)
                verification(anchor["verification"])
                _require(anchor["verification"]["state"] != "verified" or page in anchor["verification"]["evidence_pdf_indices"], "Anchor proof does not cover its page.")
                region = anchor["region"]
                if region is not None:
                    _record(region, "space origin coordinate_order normalized bbox rotation_degrees reference_width reference_height")
                    _require(region["space"] in {"pdf_page_unrotated", "asset_image"} and region["origin"] == "top_left" and region["coordinate_order"] == "ymin_xmin_ymax_xmax" and region["normalized"] is True, "Invalid region space.")
                    box = region["bbox"]
                    _require(isinstance(box, list) and len(box) == 4 and all(type(v) in {int, float} and math.isfinite(v) for v in box), "Invalid region.")
                    _require(0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1, "Invalid region bounds.")
                    _integer(region["rotation_degrees"])
                    _require(all(type(region[k]) in {int, float} and math.isfinite(region[k]) and region[k] > 0 for k in ["reference_width", "reference_height"]), "Invalid region dimensions.")
            _require(seen_pages == sorted(set(seen_pages)), "Repeated or reversed continuation pages.")
            _require(isinstance(item["assets"], list), "Invalid assets.")
            seen_assets = set()
            seen_bindings = set()
            for asset in item["assets"]:
                _record(asset, "relpath source_anchor_orders sha256 verification")
                _safe_path(root, asset["relpath"], ["parsed/figures" if group == "figures" else "parsed/tables"])
                _require(asset["relpath"] not in seen_assets, "Duplicate asset binding.")
                seen_assets.add(asset["relpath"])
                suffix = PurePosixPath(asset["relpath"]).suffix.lower()
                _require(suffix in ({".png"} if group == "figures" else {".png", ".md"}), "Unsupported asset type.")
                orders = asset["source_anchor_orders"]
                _require(isinstance(orders, list) and bool(orders), "Missing asset anchors.")
                for order in orders:
                    _integer(order)
                    _require(order < len(item["anchors"]), "Asset anchor out of bounds.")
                _require(orders == sorted(set(orders)), "Duplicate or unordered asset anchors.")
                binding = suffix, tuple(orders)
                _require(binding not in seen_bindings, "Ambiguous asset binding.")
                seen_bindings.add(binding)
                verification(asset["verification"])
                _require(asset["verification"]["state"] != "verified" or asset["verification"]["evidence_pdf_indices"] == [seen_pages[o] for o in orders], "Asset proof does not cover its anchors.")
                if asset["sha256"] is not None:
                    _digest(asset["sha256"])
                _require(asset["verification"]["state"] != "verified" or asset["sha256"] is not None, "Verified asset lacks digest.")
    _require(isinstance(data["links"], list) and isinstance(data["legacy_aliases"], list), "Invalid references.")
    for link in data["links"]:
        _record(link, "from_id to_id kind verification")
        _require(link["from_id"] in by_id and link["to_id"] in by_id and link["kind"] in {"ui_companion", "explicit_reference"}, "Broken typed link.")
        verification(link["verification"])
        if link["kind"] == "ui_companion":
            _require(link["from_id"].startswith("table:") and link["to_id"].startswith("figure:"), "UI companion must link a table to a figure.")
            _require(link["verification"]["state"] != "verified", "UI companions cannot certify source support.")
    aliases = set()
    for alias in data["legacy_aliases"]:
        _record(alias, "legacy_value namespace target_ids resolution")
        _text(alias["legacy_value"])
        key = (alias["namespace"], alias["legacy_value"].casefold())
        _require(alias["namespace"] in {"display", "chunk_id", "asset_name"} and key not in aliases, "Invalid alias.")
        _require(alias["legacy_value"].casefold() not in labels, "Alias collides with canonical label.")
        aliases.add(key)
        targets = alias["target_ids"]
        _require(isinstance(targets, list) and len(set(targets)) == len(targets) and all(t in by_id for t in targets), "Broken alias targets.")
        _require((alias["resolution"] == "exact" and len(targets) == 1) or (alias["resolution"] == "group" and len(targets) >= 2) or (alias["resolution"] == "unresolved" and not targets), "Invalid alias resolution.")
    source = _safe_path(root, doc["pdf_relpath"], ["data"])
    try:
        actual = source.read_bytes()
    except FileNotFoundError as exc:
        raise ManifestError("MANIFEST_SOURCE_MISSING", "Verified local source is absent.") from exc
    except OSError as exc:
        raise ManifestError("MANIFEST_UNAVAILABLE", "Cannot read verified source.") from exc
    if len(actual) != doc["byte_length"] or hashlib.sha256(actual).hexdigest() != doc["sha256"]:
        raise ManifestError("MANIFEST_SOURCE_MISMATCH", "Local source differs from the verified manifest.")


class StandardManifest:
    def __init__(self, data, root):
        self._data, self.root = deepcopy(data), root
        self._records = {item["id"]: item for kind in ["sections", "figures", "tables"] for item in self._data[kind]}
        self._labels = {item["label"].casefold(): item for item in self._records.values()}

    @property
    def document(self):
        return deepcopy(self._data["document"])

    @property
    def links(self):
        return deepcopy(self._data["links"])

    def labels(self, kind):
        return tuple(item["label"] for item in self._data[kind])

    def resolve(self, label):
        key = re.sub(r"\s+", " ", str(label).strip()).casefold()
        key = re.sub(r"^fig\.? ", "figure ", key)
        key = re.sub(r"(?<=[abd])\.(?=\d)", "", key)
        record = self._labels.get(key) or self._records.get(key)
        if record:
            proofs = [a["verification"] for a in record["anchors"]] if "anchors" in record else [record["verification"]]
            status = "exact" if all(v["state"] == "verified" for v in proofs) else "unverified"
            return {"status": status, "labels": [record["label"]], "target_ids": [record["id"]]}
        for alias in self._data["legacy_aliases"]:
            if alias["namespace"] == "display" and alias["legacy_value"].casefold() == key:
                if alias["resolution"] == "exact":
                    return self.resolve(self._records[alias["target_ids"][0]]["label"])
                return {"status": alias["resolution"], "labels": [self._records[i]["label"] for i in alias["target_ids"]], "target_ids": list(alias["target_ids"])}
        return {"status": "unknown", "labels": [], "target_ids": []}

    def element(self, label):
        result = self.resolve(label)
        return deepcopy(self._records[result["target_ids"][0]]) if result["status"] == "exact" else None

    section = element

    def anchors(self, label):
        record = self.element(label)
        if not record:
            return []
        if "anchors" in record:
            return record["anchors"]
        return [{"pdf_index": i, "printed_label": self._data["document"]["pages"][i]["printed_label"]} for s in record["spans"] for i in range(s["start_pdf_index"], s["end_pdf_index"] + 1)]

    def source_anchors(self, label):
        item = self.element(label)
        if not item:
            return []
        parent = self._records.get(item.get("parent_id"), item)
        return [{"source_id": self._data["document"]["id"], "source_sha256": self._data["document"]["sha256"], "element_id": item["id"], "pdf_index": a["pdf_index"], "pdf_page_ordinal": a["pdf_index"] + 1, "printed_label": a["printed_label"], "normative_status": parent["normative_status"], "verification_state": a.get("verification", item.get("verification", {})).get("state", "candidate")} for a in self.anchors(label)]

    def page_range(self, label, *, ordinal=False):
        anchors = self.anchors(label)
        values = [str(a["pdf_index"] + 1) if ordinal else a["printed_label"] for a in anchors]
        return values[0] if len(values) == 1 else f"{values[0]}-{values[-1]}" if values else ""

    def asset_paths(self, label, suffixes=None):
        record = self.element(label)
        if not record:
            return []
        results = []
        for asset in sorted(record.get("assets", []), key=lambda a: a["source_anchor_orders"]):
            if suffixes and PurePosixPath(asset["relpath"]).suffix.lower() not in suffixes:
                continue
            path = _safe_path(self.root, asset["relpath"], ["parsed/figures", "parsed/tables"])
            try:
                actual = path.read_bytes()
            except FileNotFoundError as exc:
                raise ManifestError("MANIFEST_ASSET_MISSING", "A declared asset is unavailable.") from exc
            if asset["sha256"] is not None and hashlib.sha256(actual).hexdigest() != asset["sha256"]:
                raise ManifestError("MANIFEST_ASSET_MISMATCH", "A declared asset has changed.")
            results.append(str(path))
        return results

    def companions(self):
        result = {}
        for link in self._data["links"]:
            if link["kind"] == "ui_companion":
                result.setdefault(self._records[link["from_id"]]["label"], []).append(self._records[link["to_id"]]["label"])
        return result

    def document_metadata(self):
        doc = self.document
        return {"id": doc["id"], "title": doc["title"], "edition": doc["edition"],
                "publisher": doc["publisher"], "total_pages": doc["page_count"],
                "year": int(doc["edition"]), "source_sha256": doc["sha256"]}

    def section_metadata(self):
        return [{"id": item["id"], "clause_num": item["label"], "title": item["title"],
                 "pages": self.page_range(item["label"]), "normative_status": item["normative_status"]}
                for item in self._data["sections"]]

    def table_metadata(self):
        return [{"id": item["id"], "table_num": item["label"], "title": item["title"],
                 "clause": item["parent_id"], "page": self.page_range(item["label"])}
                for item in self._data["tables"]]


def load_manifest(path=MANIFEST_PATH, *, root=ROOT):
    data = _json(Path(path))
    try:
        _validate(data, Path(root))
    except ManifestError:
        raise
    except (TypeError, ValueError, KeyError, IndexError) as exc:
        raise ManifestError("MANIFEST_INVALID", "Malformed metadata record.") from exc
    return StandardManifest(data, Path(root))


@lru_cache(maxsize=1)
def _cached_manifest(manifest_stamp, source_stamp, receipt_stamp):
    manifest = load_manifest()
    receipt = _json(MANIFEST_PATH.with_suffix(".receipt.json"))
    _require(isinstance(receipt, dict) and receipt.get("schema_version") == manifest._data["schema_version"]
             and type(receipt.get("manifest_revision")) is int and receipt["manifest_revision"] == manifest._data["manifest_revision"], "Invalid manifest receipt identity.")
    canonical = json.dumps(manifest._data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    _require(receipt.get("manifest_sha256") == hashlib.sha256(canonical).hexdigest() and receipt.get("source_sha256") == manifest.document["sha256"], "Manifest receipt does not match metadata.")
    return manifest


def get_manifest():
    def stamp(path):
        try:
            stat = path.stat()
            return stat.st_size, stat.st_mtime_ns, stat.st_ino
        except FileNotFoundError:
            return None
    return _cached_manifest(stamp(MANIFEST_PATH), stamp(SOURCE_PATH), stamp(MANIFEST_PATH.with_suffix(".receipt.json")))


_REFERENCE = re.compile(r"(?<!\w)(Figures?|Fig\.?|Tables?|Clauses?|Annex(?:es)?)\s+([A-Za-z0-9])", re.IGNORECASE)
_SINGULAR_REFERENCE = re.compile(r"(?<!\w)(Figure|Fig\.?|Table)\s*([A-Za-z0-9])", re.IGNORECASE)
_REFERENCE_ATOM = re.compile(r"(?:[A-Za-z0-9]|\.(?=\d))[\w./–—-]*")
_RANGE_TAIL = re.compile(r"\s*(?:[-–—/]|(to|through)\b)\s*", re.IGNORECASE)
_FOLLOWING = re.compile(r"\s*(?:[,;]\s*(?:and\s+)?|and\s+)", re.IGNORECASE)
_NUMERIC_RANGE = re.compile(r"([A-Za-z]?)\.?(\d+)\s*[-–—]\s*([A-Za-z]?)\.?(\d+)", re.IGNORECASE)
_RANGE_MARKER = re.compile(r"[-–—/]|\b(?:to|through)\b", re.IGNORECASE)


def _reference_id_start(kind, text):
    shape = r"[A-Za-z](?=$|[\d.\s/–—-])" if kind == "Annex" else r"(?:[A-Za-z]\.?)?\d|\.\d"
    return re.match(shape, text)


def _reference_expression(text, start, kind):
    """Read whole ID expressions; prose after 'to'/'through' is not a range."""
    atom = _REFERENCE_ATOM.match(text, start)
    if not atom:
        return "", start
    end = atom.end()
    while tail := _RANGE_TAIL.match(text, end):
        endpoint = _REFERENCE_ATOM.match(text, tail.end())
        candidate_end = endpoint.end() if endpoint else tail.end()
        endpoint_kind = kind
        target = endpoint[0] if endpoint else ""
        # Repeated kinds belong to a range only when followed by an ID. Keep
        # them in unsupported expressions so their endpoint cannot leak out as
        # an independent citation.
        word = target.rstrip(".").casefold()
        if word in {"figure", "figures", "fig", "table", "tables", "clause", "clauses", "annex", "annexes"}:
            endpoint_kind = "Figure" if word.startswith("fig") else "Table" if word.startswith("table") else "Annex" if word.startswith("annex") else "Clause"
            following = re.match(r"\s+", text[candidate_end:])
            second = _REFERENCE_ATOM.match(text, candidate_end + following.end()) if following else None
            target = second[0] if second else ""
            if second:
                candidate_end = second.end()
        elif shorthand := _SINGULAR_REFERENCE.match(target):
            # Existing enrichment accepts FigureB3 / Fig.B3. Consume those
            # endpoints here too, before deciding that a word tail is prose.
            endpoint_kind = "Figure" if shorthand[1].lower().startswith("fig") else "Table"
            target = target[shorthand.start(2):]
        if tail[1] and not _reference_id_start(endpoint_kind, target):
            break  # e.g. "Figure B1 to explain...", not an ID range.
        end = candidate_end
    return text[start:end].strip(), end


def _reference_groups(text, *, lists=True, singular=False):
    """Shared lexical boundary for citations and legacy singular enrichment.

    Return kind plus raw expressions. Resolution belongs to extract_references;
    this helper never loads metadata or expands a range.
    """
    text = str(text)
    covered = 0
    for match in (_SINGULAR_REFERENCE if singular else _REFERENCE).finditer(text):
        if match.start() < covered:
            continue
        word = match[1].lower()
        kind = "Figure" if word.startswith("fig") else "Table" if word.startswith("table") else "Annex" if word.startswith("annex") else "Clause"
        raw, end = _reference_expression(text, match.start(2), kind)
        if not _reference_id_start(kind, raw):
            continue  # Descriptive prose such as "the figure shows" is not an ID.
        expressions = [raw]
        if lists and kind in {"Figure", "Table"} and word.endswith("s"):
            while not raw.endswith(".") and (separator := _FOLLOWING.match(text, end)):
                raw, following_end = _reference_expression(text, separator.end(), kind)
                if not _reference_id_start(kind, raw):
                    break
                expressions.append(raw)
                end = following_end
        covered = end
        yield kind, expressions


def extract_references(text, *, lists=True):
    """Resolve exact IDs and bounded numeric ranges without partial acceptance."""
    manifest = get_manifest()
    result = {"figures": [], "tables": [], "clauses": [], "unresolved_elements": []}

    def unresolved(kind, code, found=None):
        found = found or {"status": "unknown", "labels": []}
        entry = {"text": kind + " " + code, "status": found["status"], "candidates": found["labels"]}
        if entry not in result["unresolved_elements"]:
            result["unresolved_elements"].append(entry)

    def add(kind, code):
        found = manifest.resolve(kind + " " + code)
        if found["status"] != "exact":
            unresolved(kind, code, found)
            return
        bucket = "figures" if kind == "Figure" else "tables" if kind == "Table" else "clauses"
        canonical = found["labels"][0]
        if canonical not in result[bucket]:
            result[bucket].append(canonical)

    for kind, expressions in _reference_groups(text, lists=lists):
        prefix = ""
        for raw in expressions:
            code = raw.rstrip(".")
            explicit = re.match(r"([A-Za-z])(?=\.?\d)", code)
            if explicit:
                prefix = explicit[1]
            elif kind in {"Figure", "Table"} and prefix and re.match(r"\.?\d", code):
                code = prefix + code
            if not _RANGE_MARKER.search(code):
                add(kind, code)
                continue

            matched = _NUMERIC_RANGE.fullmatch(code)
            if not lists or kind not in {"Figure", "Table"} or not matched:
                unresolved(kind, code)
                continue
            first_prefix, first_digits, last_prefix, last_digits = matched.groups()
            last_prefix = last_prefix or first_prefix
            first = first_prefix + first_digits
            last = last_prefix + last_digits
            # Resolve original endpoints before numeric conversion: unknown and
            # enormous IDs cannot become real IDs by truncation/normalization.
            endpoints = [manifest.resolve(kind + " " + item) for item in (first, last)]
            if not first_prefix or first_prefix.casefold() != last_prefix.casefold() or any(item["status"] != "exact" for item in endpoints):
                unresolved(kind, code)
                continue
            inventory = manifest.labels("figures" if kind == "Figure" else "tables")
            width = max((len(m[0]) for label in inventory if (m := re.search(r"\d+", label))), default=0)
            if max(len(first_digits), len(last_digits)) > width:
                unresolved(kind, code)
                continue
            first_number, last_number = int(first_digits), int(last_digits)
            if first_number > last_number or last_number - first_number + 1 > len(inventory):
                unresolved(kind, code)
                continue
            members = [first_prefix + str(number) for number in range(first_number, last_number + 1)]
            resolutions = [manifest.resolve(kind + " " + member) for member in members]
            if any(item["status"] != "exact" for item in resolutions):
                # A range crossing B16 is not the B16 group itself. Retain its
                # candidates diagnostically without triggering group assets.
                candidates = list(dict.fromkeys(label for item in resolutions if item["status"] != "exact" for label in item["labels"]))
                unresolved(kind, code, {"status": "unknown", "labels": candidates})
                continue
            for member in members:
                add(kind, member)
    return result
