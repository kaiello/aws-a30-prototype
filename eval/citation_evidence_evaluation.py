"""Offline declarative citation/evidence checks; never an entailment grader.

The caller supplies a pure local resolver callback. This module imports no app,
provider, database, model, or previous capture executor. Keep private cases,
trusted source payloads, raw observations and receipts outside published source.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import time


ROOT = Path(__file__).resolve().parents[1]
AXES = ("reference", "binding", "assets", "support")
REFERENCE = {"exact", "group", "unsupported_qualifier", "page_only", "unknown", "unverified", "mixed", "not_cited"}
BINDING = {"matched", "mismatched", "incomplete", "unavailable"}
ASSET = {"complete", "source_only", "missing", "corrupt", "unavailable"}
SUPPORT = {"SUPPORTED_REVIEWED_FACTS", "UNASSESSED", "INSUFFICIENT_EVIDENCE"}
CACHE_POLICY = "cold=fresh adapter state; OS filesystem cache uncontrolled; warm=reused adapter per case"
INTERPRETATION = ("Frozen identity/binding/availability/support-state contracts only; "
                  "claim truth and visual meaning are not automatically adjudicated")
BINDING_LIMITATION = ("Binding/support state contracts and reference identities only; "
                      "selected-entry/span/reviewed-pairing proof is not independently reconstructed")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def evaluator_fingerprint():
    return _sha(Path(__file__).resolve().read_bytes())


def _asset_tuple(asset):
    if not isinstance(asset, dict) or not _hash(asset.get("sha256")):
        raise ValueError("Invalid asset digest")
    orders = asset.get("source_anchor_orders")
    if (not isinstance(orders, list) or not orders
            or any(type(i) is not int or i < 0 for i in orders)
            or orders != sorted(set(orders))):
        raise ValueError("Invalid asset anchor orders")
    if asset.get("kind") not in {"image", "text"} or asset.get("verification_state") not in {"verified", "candidate", "unverified"}:
        raise ValueError("Invalid asset kind/verification state")
    return [asset["sha256"], orders, asset["kind"], asset["verification_state"]]


def _reference(link):
    if not isinstance(link, dict) or not _text(link.get("claim_id")) or not isinstance(link.get("mentions"), list):
        raise ValueError("Invalid claim/mention identity")
    mentions = []
    for item in link["mentions"]:
        if (not isinstance(item, dict) or not _text(item.get("raw"))
                or type(item.get("start")) is not int or type(item.get("end")) is not int
                or item["start"] < 0 or item["end"] <= item["start"]
                or type(item.get("order")) is not int or item["order"] < 0
                or item.get("span_space") != "half_open_unicode_characters"
                or not isinstance(item.get("resolution"), dict) or not isinstance(item.get("qualifiers"), dict)):
            raise ValueError("Invalid complete citation mention")
        mentions.append({key: deepcopy(item[key]) for key in
                         ("raw", "start", "end", "order", "span_space", "kind", "requested_label", "resolution", "qualifiers")})
    evidence = []
    if not isinstance(link.get("ordered_evidence"), list):
        raise ValueError("Invalid ordered evidence")
    for item in link["ordered_evidence"]:
        if (not isinstance(item, dict) or not _text(item.get("element_id"))
                or item.get("relationship") not in {"direct", "navigation_candidate"}
                or not isinstance(item.get("source_anchors"), list)):
            raise ValueError("Invalid evidence identity")
        for anchor in item["source_anchors"]:
            if (not isinstance(anchor, dict) or not _text(anchor.get("source_id"))
                    or not _hash(anchor.get("source_sha256")) or anchor.get("element_id") != item["element_id"]
                    or type(anchor.get("pdf_index")) is not int or anchor["pdf_index"] < 0):
                raise ValueError("Invalid canonical source anchor")
        evidence.append({key: deepcopy(item[key]) for key in ("element_id", "label", "relationship", "source_anchors")})
    return [link["claim_id"], mentions, link["reference_status"], evidence]


def _validate_link(link):
    _reference(link)
    if (link.get("reference_status") not in REFERENCE or link.get("binding_status") not in BINDING
            or link.get("asset_status") not in ASSET or link.get("support_status") not in SUPPORT):
        raise ValueError("Invalid independent result state")
    for item in link["ordered_evidence"]:
        if item.get("asset_status") not in ASSET or not isinstance(item.get("assets"), list):
            raise ValueError("Invalid element asset state")
        for asset in item["assets"]:
            _asset_tuple(asset)
        if "rendered_assets" in item:
            if not isinstance(item["rendered_assets"], list):
                raise ValueError("Invalid frozen renderable asset subset")
            for asset in item["rendered_assets"]:
                _asset_tuple(asset)


def _references_match(expected, observed):
    if _reference(expected) != _reference(observed):
        return False
    return all("page_candidates" not in want or want["page_candidates"] == got.get("page_candidates")
               for want, got in zip(expected["mentions"], observed["mentions"]))


def validate_cases(data):
    if (not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or not _text(data.get("suite_id")) or data.get("cohort") not in {"DEVELOPMENT", "HELDOUT"}
            or not isinstance(data.get("cases"), list) or not data["cases"]):
        raise ValueError("Invalid frozen citation/evidence suite")
    seen = set()
    for case in data["cases"]:
        if (not isinstance(case, dict) or not _text(case.get("id")) or case["id"] in seen
                or not isinstance(case.get("runtime_input"), dict) or not isinstance(case.get("expected"), dict)
                or not isinstance(case["runtime_input"].get("claims"), list)
                or not isinstance(case["expected"].get("links"), list) or not case["expected"]["links"]):
            raise ValueError("Invalid/duplicate frozen case")
        seen.add(case["id"])
        ids = []
        for link in case["expected"]["links"]:
            _validate_link(link)
            ids.append(link["claim_id"])
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate expected claim identity")
        groups = case["expected"].get("required_groups", [])
        if not isinstance(groups, list) or any(not isinstance(group, list) or not group
                or len(group) != len(set(group)) or any(identifier not in ids for identifier in group) for group in groups):
            raise ValueError("Invalid required AND-of-OR assertion groups")
    _json(data)
    return deepcopy(data)


def _navigation_allowances(link, manifest, excluded):
    """Exact optional ledger from frozen expectations/inventory, never outputs."""
    records = {record['id']: record for group in ('sections','figures','tables') for record in manifest[group]}
    occupied = {item['element_id'] for item in link['ordered_evidence']}
    candidates = []
    for item in link['ordered_evidence']:
        if item['relationship'] != 'direct':
            continue
        for edge in manifest.get('links', []):
            identity = edge['to_id']
            if edge['kind'] != 'ui_companion' or edge['from_id'] != item['element_id'] or identity in occupied:
                continue
            occupied.add(identity)
            record = records[identity];parent = records[record['parent_id']]
            anchors = [{'source_id':manifest['document']['id'],'source_sha256':manifest['document']['sha256'],
                        'element_id':identity,'pdf_index':anchor['pdf_index'],'pdf_page_ordinal':anchor['pdf_index']+1,
                        'printed_label':anchor['printed_label'],'normative_status':parent['normative_status'],
                        'verification_state':anchor['verification']['state']} for anchor in record['anchors']]
            raw = sorted(record.get('assets', []),key=lambda asset:asset['source_anchor_orders'])
            assets = [{'sha256':asset['sha256'],'source_anchor_orders':asset['source_anchor_orders'],
                       'kind':'text' if Path(asset['relpath']).suffix.lower()=='.md' else 'image',
                       'verification_state':asset['verification']['state']} for asset in raw]
            failures = [excluded[asset['relpath']] for asset in raw if asset['relpath'] in excluded]
            state = ('corrupt' if 'corrupt' in failures else 'missing') if failures else 'complete' if assets else 'source_only'
            candidate = {'element_id':identity,'label':record['label'],'relationship':'navigation_candidate',
                         'source_anchors':anchors,'asset_status':state,'assets':assets}
            if failures:
                candidate['rendered_assets'] = [descriptor for asset,descriptor in zip(raw,assets) if asset['relpath'] not in excluded]
            candidates.append(candidate)
    return candidates


def load_frozen_cases(case_path, *, manifest_path=None, include_navigation=False):
    """Project exact healthy asset subsets from the already-frozen inventory.

    This never reads asset/PDF bytes or changes the frozen file. The manifest's
    raw byte digest must equal the digest frozen before implementation. Only
    isolated missing/corrupt fixture declarations remove renderable members.
    """
    suite = validate_cases(json.loads(Path(case_path).read_text(encoding="utf-8")))
    if manifest_path is None:
        return suite
    raw = Path(manifest_path).read_bytes()
    if _sha(raw) != suite.get("source_fingerprints", {}).get("manifest_sha256"):
        raise ValueError("Frozen manifest inventory digest mismatch")
    manifest = json.loads(raw.decode("utf-8"))
    records = {record["id"]: record for kind in ("figures", "tables") for record in manifest[kind]}
    for case in suite["cases"]:
        mutations = case["runtime_input"].get("fixture", {}).get("asset_mutations", [])
        excluded = set()
        for mutation in mutations:
            if (not isinstance(mutation, dict) or not _text(mutation.get("relpath"))
                    or mutation.get("mode") not in {"missing", "corrupt"}):
                raise ValueError("Invalid frozen isolated asset mutation")
            excluded.add(mutation["relpath"])
        matched_mutations = set()
        for link in case["expected"]["links"]:
            if include_navigation:
                link['allowed_navigation'] = _navigation_allowances(link,manifest,{m['relpath']:m['mode'] for m in mutations})
                for candidate in link['allowed_navigation']:
                    matched_mutations.update(asset['relpath'] for asset in records[candidate['element_id']].get('assets',[])
                                             if asset['relpath'] in excluded)
            for item in link["ordered_evidence"]:
                if item["asset_status"] not in {"missing", "corrupt"}:
                    continue
                assets = sorted(records[item["element_id"]]["assets"], key=lambda asset: asset["source_anchor_orders"])
                projected = [{"sha256": asset["sha256"], "source_anchor_orders": asset["source_anchor_orders"],
                              "kind": "text" if Path(asset["relpath"]).suffix.lower() == ".md" else "image",
                              "verification_state": asset["verification"]["state"]} for asset in assets]
                if projected != item["assets"]:
                    raise ValueError("Frozen asset ledger differs from the frozen manifest")
                item["rendered_assets"] = [descriptor for asset, descriptor in zip(assets, projected) if asset["relpath"] not in excluded]
                matched_mutations.update(asset["relpath"] for asset in assets if asset["relpath"] in excluded)
        if excluded != matched_mutations:
            raise ValueError("Frozen asset mutation does not belong to an expected failed asset set")
    suite["asset_expectation_projection"] = "healthy subsets from frozen manifest digest and frozen isolated mutations; original labels/file unchanged"
    if include_navigation:
        suite['adjudication_amendment'] = 'Exact optional navigation ledger from frozen expected direct IDs and pinned typed manifest links; DEVELOPMENT protocol amended after initial results'
    return validate_cases(suite)


def _assets_match(expected, observed):
    if observed.get("asset_status") != expected["asset_status"]:
        return False
    if len(expected["ordered_evidence"]) != len(observed.get("ordered_evidence", [])):
        return False
    for want, got in zip(expected["ordered_evidence"], observed["ordered_evidence"]):
        if any(want[key] != got.get(key) for key in ("element_id", "relationship", "asset_status")):
            return False
        required = [_asset_tuple(item) for item in want["assets"]]
        actual = [_asset_tuple(item) for item in got.get("assets", [])]
        declared = got.get("declared_assets")
        if declared is not None:
            if not isinstance(declared, list):
                return False
            # Declared records retain raw manifest order; the frozen consumption
            # order is the existing asset_paths source-anchor-order sort.
            inventory = [_asset_tuple(item) for item in sorted(declared, key=lambda a: a["source_anchor_orders"])]
            if inventory != required:
                return False
        elif want["asset_status"] in {"missing", "corrupt"}:
            return False
        if want["asset_status"] in {"missing", "corrupt"}:
            # Do not accept an arbitrary healthy subset. This expectation must
            # come from a frozen fixture or an independently hashed manifest
            # projection, never from the resolver's available output.
            if "rendered_assets" not in want:
                return False
            renderable = [_asset_tuple(item) for item in want["rendered_assets"]]
            if actual != renderable or len(renderable) >= len(required):
                return False
        elif actual != required:
            return False
    return True


def _navigation_projection(expected, observed):
    """Separate exact optional candidates from the unchanged required ledger."""
    allowed = expected.get('allowed_navigation', [])
    expected_ids = {item['element_id'] for item in expected['ordered_evidence']}
    extra = [item for item in observed['ordered_evidence'] if item['element_id'] not in expected_ids]
    by_id = {item['element_id']:item for item in allowed}
    ids = [item['element_id'] for item in extra]
    if len(ids)!=len(set(ids)) or ids != [item['element_id'] for item in allowed if item['element_id'] in ids]:
        return observed, False
    for item in extra:
        want = by_id.get(item['element_id'])
        if want is None or item.get('relationship')!='navigation_candidate':
            return observed, False
        if any(want[key]!=item.get(key) for key in ('element_id','label','relationship','source_anchors')):
            return observed, False
        if not _assets_match({'asset_status':want['asset_status'],'ordered_evidence':[want]},
                             {'asset_status':item.get('asset_status'),'ordered_evidence':[item]}):
            return observed, False
    projected = dict(observed,ordered_evidence=[item for item in observed['ordered_evidence'] if item['element_id'] in expected_ids])
    return projected, True


def check_case(case, observed):
    """Compare frozen states; reported SUPPORTED is never independent truth."""
    expected = case["expected"]
    wanted = expected["links"]
    rows = []
    malformed = False
    try:
        if not isinstance(observed, dict) or not isinstance(observed.get("links"), list):
            raise ValueError("Malformed resolver result")
        actual = observed["links"]
        for item in actual:
            _validate_link(item)
        ids = [item["claim_id"] for item in actual]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate observed claim identity")
    except (ValueError, KeyError, TypeError, IndexError):
        actual, malformed = [], True
    actual_by_id = {item["claim_id"]: item for item in actual}
    for want in wanted:
        got = actual_by_id.get(want["claim_id"])
        checks = dict.fromkeys(AXES, False)
        if got is not None:
            try:
                projected, navigation_valid = _navigation_projection(want, got)
                checks = {"reference": navigation_valid and _references_match(want, projected),
                          "binding": want["binding_status"] == got["binding_status"],
                          "assets": navigation_valid and _assets_match(want, projected),
                          "support": want["support_status"] == got["support_status"]}
            except (ValueError, KeyError, TypeError, IndexError):
                pass
        rows.append({"claim_id": want["claim_id"], "checks": checks, "passed": all(checks.values())})
    order_matches = [item["claim_id"] for item in actual] == [item["claim_id"] for item in wanted]
    checks = {axis: order_matches and all(item["checks"][axis] for item in rows) for axis in AXES}
    if "assessment" in expected:
        assessment = observed.get("assessment") if isinstance(observed, dict) else None
        checks["support"] = checks["support"] and isinstance(assessment, dict) and all(
            assessment.get(key) == value for key, value in expected["assessment"].items())
    groups = expected.get("required_groups", [])
    passed = {item["claim_id"] for item in rows if item["passed"]}
    matched = sum(bool(passed.intersection(group)) for group in groups)
    return {"passed": all(checks.values()), "checks": checks, "link_checks": rows,
            "expected_links": len(wanted), "observed_links": len(actual), "malformed_output": malformed,
            "required_groups": {"matched": matched, "declared": len(groups),
                                "complete": matched == len(groups) if groups else None},
            "claim_truth": "not_automatically_adjudicated", "binding_interpretation": BINDING_LIMITATION}


def _summary(suite, rows):
    links = sum(len(case["expected"]["links"]) for case in suite["cases"])
    groups = sum(len(case["expected"].get("required_groups", [])) for case in suite["cases"])
    return {"declared_cases": len(suite["cases"]), "declared_links": links, "declared_required_groups": groups,
            "attempted_cases": sum(row.get("attempted") is True for row in rows),
            "passed_cases": sum(row.get("result", {}).get("passed") is True for row in rows),
            "errors": sum(bool(row.get("error")) for row in rows),
            "case_checks": {axis: {"passed": sum(row.get("result", {}).get("checks", {}).get(axis) is True for row in rows),
                                   "denominator": len(suite["cases"])} for axis in AXES},
            "link_checks": {axis: {"passed": sum(item["checks"][axis] is True for row in rows
                                        for item in row.get("result", {}).get("link_checks", [])),
                                   "denominator": links} for axis in AXES},
            "required_groups_matched": sum(row.get("result", {}).get("required_groups", {}).get("matched", 0) for row in rows),
            "claim_truth": "not_automatically_adjudicated", "binding_interpretation": BINDING_LIMITATION}


def evaluate_cases(suite, invoke):
    frozen = validate_cases(suite)
    executor = evaluator_fingerprint()
    rows = []
    for case in frozen["cases"]:
        row = {"id": case["id"], "attempted": True}
        started = time.perf_counter()
        try:
            observed = invoke(deepcopy(case["runtime_input"]))
            row["request_wall_ms"] = (time.perf_counter() - started) * 1000
            row["response"] = deepcopy(observed)
            row["result"] = check_case(case, observed)
            if row["result"]["malformed_output"]:
                row["error"] = {"type": "MalformedResult", "message": "Resolver returned an invalid contract."}
        except Exception as error:
            row["request_wall_ms"] = (time.perf_counter() - started) * 1000
            row["error"] = {"type": type(error).__name__, "message": "Local resolver execution failed; details omitted."}
            row["result"] = check_case(case, None)
        rows.append(row)
    return {"kind": "citation-evidence-offline-adjudication", "lane": "deterministic_contract",
            "suite": frozen, "suite_sha256": _sha(_json(frozen)), "evaluator_sha256": executor,
            "evaluator_unchanged": executor == evaluator_fingerprint(),
            "rows": rows, "summary": _summary(frozen, rows), "interpretation": INTERPRETATION}


def validate_report(report):
    if (not isinstance(report, dict) or report.get("kind") != "citation-evidence-offline-adjudication"
            or report.get("lane") != "deterministic_contract" or report.get("evaluator_unchanged") is not True
            or not _hash(report.get("evaluator_sha256"))):
        raise ValueError("Invalid offline adjudication receipt")
    if "inputs_unchanged" in report and report["inputs_unchanged"] is not True:
        raise ValueError("Frozen evaluation input drift")
    suite = validate_cases(report.get("suite"))
    if report.get("suite_sha256") != _sha(_json(suite)):
        raise ValueError("Frozen suite fingerprint mismatch")
    expected = [case["id"] for case in suite["cases"]]
    rows = report.get("rows")
    if (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)
            or [row.get("id") for row in rows] != expected):
        raise ValueError("Missing/duplicate/unknown/reordered declared case rows")
    for case, row in zip(suite["cases"], rows):
        if row.get("attempted") is not True or row.get("result") != check_case(case, row.get("response")):
            raise ValueError("Stored adjudication differs from the frozen case/response")
        if row["result"]["malformed_output"] and not row.get("error"):
            raise ValueError("Malformed result is missing its execution error")
    if report.get("summary") != _summary(suite, rows):
        raise ValueError("Receipt summary/denominator mismatch")
    return report


def latency_statistics(values):
    if not values:
        return None
    if any(not _number(value) for value in values):
        raise ValueError("Invalid latency sample")
    ordered = sorted(values)
    return {"n": len(values), "median": statistics.median(values), "min": ordered[0], "max": ordered[-1],
            "p95_nearest_rank": ordered[math.ceil(.95 * len(ordered)) - 1]}


def _timing_stats(rows):
    successful = [row for row in rows if not row.get("error")]
    stages = {}
    for row in successful:
        for key, value in row.get("reported_stages_ms", {}).items():
            if _number(value):
                stages.setdefault(key, []).append(value)
    return {"declared_samples": len(rows), "successful_samples": len(successful),
            "errors": len(rows) - len(successful),
            "wall_ms": latency_statistics([row["wall_ms"] for row in rows]),
            "successful_wall_ms": latency_statistics([row["wall_ms"] for row in successful]),
            "stages_ms": {key: latency_statistics(values) for key, values in stages.items()}}


def benchmark_cases(suite, invoke_factory, *, cold_runs=5, warm_runs=30):
    """Fresh callback state is cold; this does not evict filesystem/OS caches."""
    frozen = validate_cases(suite)
    if cold_runs != 5 or warm_runs != 30:
        raise ValueError("Frozen resolver schedule is five cold and thirty warm samples per case")
    executor, rows, statistics_by_case = evaluator_fingerprint(), [], []
    for case in frozen["cases"]:
        warm_invoke, warm_error = None, None
        for temperature, count in (("cold", cold_runs), ("warm", warm_runs)):
            if temperature == "warm":
                try:
                    warm_invoke = invoke_factory()
                except Exception as error:
                    warm_error = type(error).__name__
            for repetition in range(count):
                row = {"id": case["id"], "temperature": temperature, "repetition": repetition + 1}
                started = time.perf_counter()
                try:
                    if temperature == "cold":
                        invoke = invoke_factory()
                    else:
                        if warm_error:
                            raise RuntimeError("Warm adapter initialization failed")
                        invoke = warm_invoke
                    observed = invoke(deepcopy(case["runtime_input"]))
                    row["wall_ms"] = (time.perf_counter() - started) * 1000
                    row["response"] = deepcopy(observed)
                    row["result"] = check_case(case, observed)
                    if row["result"]["malformed_output"]:
                        raise ValueError("Malformed resolver result")
                    timing = observed.get("timings_ms")
                    row["reported_stages_ms"] = deepcopy(timing) if isinstance(timing, dict) else {}
                except Exception as error:
                    row.setdefault("wall_ms", (time.perf_counter() - started) * 1000)
                    row["error"] = {"type": type(error).__name__, "message": "Local benchmark sample failed; details omitted."}
                rows.append(row)
        selected = [row for row in rows if row["id"] == case["id"]]
        statistics_by_case.append({"id": case["id"], **{temperature: _timing_stats(
            [row for row in selected if row["temperature"] == temperature]) for temperature in ("cold", "warm")}})
    return {"kind": "citation-evidence-offline-latency", "lane": "deterministic_contract", "suite": frozen,
            "suite_sha256": _sha(_json(frozen)), "evaluator_sha256": executor,
            "evaluator_unchanged": executor == evaluator_fingerprint(), "cache_policy": CACHE_POLICY,
            "timing_scope": "cold includes fresh adapter creation; warm reuses one adapter per case; scoring is outside wall time",
            "environment": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
            "rows": rows, "case_statistics": statistics_by_case,
            "summary": {"declared_cases": len(frozen["cases"]), "declared_samples": len(frozen["cases"]) * 35,
                        "cold_samples": sum(row["temperature"] == "cold" for row in rows),
                        "warm_samples": sum(row["temperature"] == "warm" for row in rows),
                        "errors": sum(bool(row.get("error")) for row in rows),
                        "contract_failures": sum(row.get("result", {}).get("passed") is False for row in rows)},
            "interpretation": "Exploratory nearest-rank p95; finite small sample, not a stable tail/SLA. " + INTERPRETATION}


def validate_latency_report(report):
    if (not isinstance(report, dict) or report.get("kind") != "citation-evidence-offline-latency"
            or report.get("lane") != "deterministic_contract" or report.get("evaluator_unchanged") is not True
            or not _hash(report.get("evaluator_sha256")) or report.get("cache_policy") != CACHE_POLICY):
        raise ValueError("Invalid offline latency receipt")
    suite = validate_cases(report.get("suite"))
    if report.get("suite_sha256") != _sha(_json(suite)):
        raise ValueError("Frozen latency suite mismatch")
    rows = report.get("rows")
    schedule = [(case["id"], temperature, repetition + 1) for case in suite["cases"]
                for temperature, count in (("cold", 5), ("warm", 30)) for repetition in range(count)]
    if (not isinstance(rows, list) or len(rows) != len(schedule)
            or any(not isinstance(row, dict) or (row.get("id"), row.get("temperature"), row.get("repetition")) != slot
                   or not _number(row.get("wall_ms")) for row, slot in zip(rows, schedule))):
        raise ValueError("Missing/duplicate/reordered/invalid latency observations")
    stats = []
    for case in suite["cases"]:
        selected = [row for row in rows if row["id"] == case["id"]]
        for row in selected:
            if not row.get("error") and row.get("result") != check_case(case, row.get("response")):
                raise ValueError("Stored benchmark adjudication differs from its frozen response")
        stats.append({"id": case["id"], **{temperature: _timing_stats(
            [row for row in selected if row["temperature"] == temperature]) for temperature in ("cold", "warm")}})
    summary = {"declared_cases": len(suite["cases"]), "declared_samples": len(suite["cases"]) * 35,
               "cold_samples": sum(row["temperature"] == "cold" for row in rows),
               "warm_samples": sum(row["temperature"] == "warm" for row in rows),
               "errors": sum(bool(row.get("error")) for row in rows),
               "contract_failures": sum(row.get("result", {}).get("passed") is False for row in rows)}
    if report.get("case_statistics") != stats or report.get("summary") != summary:
        raise ValueError("Latency summary/statistics mismatch")
    return report


def write_receipt(report, output_dir, *, input_paths=(), repo_root=ROOT):
    """Save private results in a fresh external directory, never overwriting data."""
    path, root = Path(output_dir).resolve(), Path(repo_root).resolve()
    if path.is_relative_to(root) or path.exists():
        raise ValueError("Receipt output must be fresh and outside the repository")
    fingerprints = {str(Path(value).resolve()): _sha(Path(value).read_bytes()) for value in input_paths}
    path.mkdir(parents=True)
    value = deepcopy(report)
    value["input_file_fingerprints"] = fingerprints
    (path / "report.json").write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--observations", required=True, help="Local JSON list of {id,response}; no live calls")
    parser.add_argument("--manifest", type=Path, help="Raw-SHA-pinned manifest for frozen healthy asset subsets")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    paths = [Path(args.cases), Path(args.observations), Path(__file__)]
    if args.manifest is not None:
        paths.append(args.manifest)
    before = {str(path.resolve()): _sha(path.read_bytes()) for path in paths}
    suite = load_frozen_cases(args.cases, manifest_path=args.manifest)
    observed = json.loads(Path(args.observations).read_text(encoding="utf-8"))
    if not isinstance(observed, list) or any(not isinstance(row, dict) or not _text(row.get("id")) for row in observed):
        raise ValueError("Invalid local observations")
    ids = [row["id"] for row in observed]
    expected = [case["id"] for case in suite["cases"]]
    if len(ids) != len(set(ids)) or set(ids) - set(expected):
        raise ValueError("Duplicate/unknown local observation IDs")
    lookup = {row["id"]: row.get("response") for row in observed}
    ordered = iter(expected)
    report = evaluate_cases(suite, lambda _: lookup.get(next(ordered)))
    report["input_file_fingerprints"] = before
    report["inputs_unchanged"] = before == {str(path.resolve()): _sha(path.read_bytes()) for path in paths}
    if not report["inputs_unchanged"] or not report["evaluator_unchanged"]:
        raise ValueError("Frozen evaluation input/executor drift")
    validate_report(report)
    write_receipt(report, args.output, input_paths=paths, repo_root=args.repo_root)


if __name__ == "__main__":
    main()
