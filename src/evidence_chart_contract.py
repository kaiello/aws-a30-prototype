"""Load the checked-in chart planner contract; never execute a generated plan.

Only developer-controlled contract paths belong here, never request parameters.
The JSON centralizes definitions/guidance, while compiler/executor guards remain
code responsibilities. Its SHA identifies exact bytes, not semantic correctness.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

CONTRACT_PATH = Path(__file__).with_suffix(".json")
_MAX_BYTES = 65536
_KINDS = ("root", "category", "process")
_ID_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]{0,63}$"
_BUDGET_CEILINGS = {"MAX_OPERATIONS": 16, "MAX_PARTS": 16, "MAX_RESULT_REFS": 16,
    "MAX_LITERAL_IDS": 32, "MAX_RESOLVED_IDS": 512, "MAX_INFORMATION_FIELDS": 16,
    "MAX_QUERY_LENGTH": 16360, "MAX_STRING_LENGTH": 256, "MAX_REASON_LENGTH": 1024}
_WIRE_KEYS = {"operation": ("id", "kind", "query_layer", "subject_ids", "target_ids",
    "result_refs", "fields", "requested_fields", "requested_aspects"),
    "part": ("id", "quote", "status", "operation_ids", "reason"),
    "envelope": ("schema_version", "source_element", "query", "parts", "operations")}
_ROOT_KEYS = {"contract_version", "wire_schema_version", "instruction_version",
    "coverage_authority", "budgets", "node_kinds", "id_pattern", "wire_keys",
    "part_rules", "empty_subject_scopes", "operation_profiles", "static_routing_guidance",
    "question_interface", "archetype_profiles"}
_QUESTION_KEYS = {"schema_version", "instruction_version", "action_keys", "envelope_keys",
    "part_keys", "kinds", "fields", "modes", "scopes", "guidance", "part_metadata"}
_ACTION_KEYS = ["id", "kind", "query_layer", "subjects", "targets", "subjects_from",
    "targets_from", "fields", "mode", "information_fields", "scope"]
_ACTION_MODES = {"lookup_term": [""],
    "list_members": ["direct", "descendants", "parents", "row_partition", "physical_neighbors"],
    "check_relationship": ["membership", "layout", "semantic_subtype", "source_limits"],
    "explain_path": ["from_to"]}
_PROFILE_KEYS = {"minimum", "subjects", "single", "targets", "fields",
    "requested_fields", "requested_aspects", "layers", "produces", "meaning"}
# These are executor-supported capability ceilings, not routing substitutions.
_ROLE_CEILINGS = {
    "designation": (_KINDS, ()), "category": (("process",), ()),
    "direct_children": (_KINDS, ()), "descendants": (_KINDS, ()),
    "parents": (_KINDS, ()), "paths": (_KINDS, _KINDS),
    "membership": (("process",), ("category",)),
    "layout_relation": (("process",), ("category", "process")),
    "physical_neighbors": (("root", "category"), ()),
    "row_partition": (("category",), ()),
    "comparison": (("category", "process"), ()),
    "evidence": (_KINDS, ()), "epistemic_limits": (_KINDS, ()),
    "operating_information": (_KINDS, ()), "chart_layout": ((), ())}
_EVIDENCE_ONLY = {"direct_children", "descendants", "parents", "layout_relation",
    "row_partition", "evidence", "epistemic_limits", "operating_information", "chart_layout"}
_EMPTY_SCOPES = {"chart_layout": "chart",
    "epistemic_limits": "source", "operating_information": "source"}


class ContractError(ValueError):
    """The trusted local contract is malformed or outside supported capabilities."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError("CHART_PLAN_CONTRACT_" + code)


def _keys(value: Any, expected: set | dict, code: str) -> None:
    _require(isinstance(value, dict) and set(value) == set(expected), code)


def _text(value: Any, maximum: int = 4096) -> bool:
    return (isinstance(value, str) and bool(value.strip()) and len(value) <= maximum
        and not any(ord(char) < 32 for char in value))


def _choices(value: Any, allowed: tuple | set, *, empty: bool = True) -> bool:
    return (isinstance(value, list) and (empty or bool(value))
        and all(isinstance(item, str) and item in allowed for item in value)
        and len(value) == len(set(value)))


def _validate(doc: Any) -> None:
    _keys(doc, _ROOT_KEYS, "ROOT_KEYS_INVALID")
    if "archetype_profiles" in doc:
        _require(isinstance(doc["archetype_profiles"], dict), "ARCHETYPE_PROFILES_INVALID")
    _require(doc["contract_version"] == "chart-plan-contract-1.2", "VERSION_UNSUPPORTED")
    _require(doc["wire_schema_version"] == "chart-llm-plan-1.0", "WIRE_VERSION_UNSUPPORTED")
    _require(isinstance(doc["instruction_version"], str) and re.fullmatch(
        r"chart-llm-plan-instructions-1\.[0-9]+", doc["instruction_version"]), "INSTRUCTION_VERSION_INVALID")
    _require(doc["coverage_authority"] == "MODEL_PROPOSED_UNVERIFIED", "COVERAGE_INVALID")
    _require(doc["node_kinds"] == list(_KINDS) and doc["id_pattern"] == _ID_PATTERN,
        "IDENTITY_CONTRACT_INVALID")
    _keys(doc["budgets"], _BUDGET_CEILINGS, "BUDGET_KEYS_INVALID")
    for name, ceiling in _BUDGET_CEILINGS.items():
        value = doc["budgets"][name]
        _require(type(value) is int and 1 <= value <= ceiling, "BUDGET_INVALID")
    _require(doc["budgets"]["MAX_RESOLVED_IDS"] >= doc["budgets"]["MAX_LITERAL_IDS"],
        "RESOLVED_BUDGET_INVALID")
    _keys(doc["wire_keys"], _WIRE_KEYS, "WIRE_KEYS_INVALID")
    for name, keys in _WIRE_KEYS.items():
        _require(doc["wire_keys"][name] == list(keys), "WIRE_KEYS_INVALID")
    rules = doc["part_rules"]
    _keys(rules, {"planned_reason", "reason", "operations"}, "PART_RULES_INVALID")
    _require(rules["planned_reason"] == "" and _text(rules["reason"])
        and _text(rules["operations"]), "PART_RULES_INVALID")
    _require(doc["empty_subject_scopes"] == _EMPTY_SCOPES, "EMPTY_SUBJECT_SCOPE_INVALID")
    profiles = doc["operation_profiles"]
    _keys(profiles, _ROLE_CEILINGS, "OPERATIONS_INVALID")
    for kind, profile in profiles.items():
        _keys(profile, _PROFILE_KEYS, "PROFILE_KEYS_INVALID")
        minimum = 0 if kind in _EMPTY_SCOPES else (2 if kind == "comparison" else 1)
        _require(type(profile["minimum"]) is int and profile["minimum"] == minimum,
            "MINIMUM_INVALID")
        for role, allowed in zip(("subjects", "targets"), _ROLE_CEILINGS[kind]):
            _require(_choices(profile[role], allowed, empty=not allowed), "ROLE_TYPES_INVALID")
        _require(type(profile["single"]) is bool and profile["single"] ==
            (kind in {"paths", "membership", "layout_relation"}), "CARDINALITY_INVALID")
        layers = ["evidence"] if kind in _EVIDENCE_ONLY else ["evidence", "knowledge"]
        _require(profile["layers"] == layers, "LAYERS_INVALID")
        fields = ["designation", "category"] if kind == "comparison" else []
        _require(profile["fields"] == fields, "FIELDS_INVALID")
        _require(type(profile["requested_fields"]) is bool and profile["requested_fields"] ==
            (kind == "operating_information"), "REQUESTED_FIELDS_INVALID")
        _require(type(profile["requested_aspects"]) is bool and profile["requested_aspects"] ==
            (kind in {"evidence", "epistemic_limits"}), "REQUESTED_ASPECTS_INVALID")
        produces = profile["produces"]
        _require(isinstance(produces, dict) and set(produces) <=
            {"rows", "categories", "parents", "groups"}, "RESULT_SELECTION_INVALID")
        for selection, kinds in produces.items():
            _require(_choices(kinds, ("category",) if selection == "categories" else _KINDS,
                empty=False), "RESULT_TYPES_INVALID")
        _require(_text(profile["meaning"], 512), "MEANING_INVALID")
    lines = doc["static_routing_guidance"]
    _require(isinstance(lines, list) and 1 <= len(lines) <= 32
        and all(_text(line) for line in lines), "GUIDANCE_INVALID")
    question = doc["question_interface"]
    _keys(question, _QUESTION_KEYS, "QUESTION_KEYS_INVALID")
    _require(question["schema_version"] == "chart-question-actions-1.0"
        and question["instruction_version"] == "chart-question-actions-instructions-1.1",
        "QUESTION_VERSION_INVALID")
    _require(question["action_keys"] == _ACTION_KEYS
        and question["envelope_keys"] == ["schema_version", "source_element", "query", "parts", "actions"]
        and question["part_keys"] == ["id", "quote", "status", "action_ids", "reason"],
        "QUESTION_WIRE_KEYS_INVALID")
    _require(question["kinds"] == list(_ACTION_MODES) and question["modes"] == _ACTION_MODES,
        "QUESTION_ACTIONS_INVALID")
    _require(question["fields"] == ["name", "acronym", "group", "evidence", "source_limits"]
        and question["scopes"] == ["selected", "chart"], "QUESTION_ARGUMENTS_INVALID")
    metadata = question["part_metadata"]
    _keys(metadata, {"planned_reason", "unresolved_reason", "description"}, "QUESTION_PART_METADATA_INVALID")
    _require(metadata["planned_reason"] == "trace_only_map_to_part_rules.planned_reason"
        and metadata["unresolved_reason"] == "required_forward_unchanged"
        and _text(metadata["description"]), "QUESTION_PART_METADATA_INVALID")
    _require(isinstance(question["guidance"], list) and 1 <= len(question["guidance"]) <= 24
        and all(_text(line) for line in question["guidance"]), "QUESTION_GUIDANCE_INVALID")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ChartContract:
    definitions: Mapping[str, Any]
    sha256: str

    def as_dict(self) -> dict:
        """Return an independent JSON-serializable copy, not shared mutable state."""
        return _thaw(self.definitions)


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, "DUPLICATE_KEY")
        result[key] = value
    return result


def load_contract(path: Path | str | None = None) -> ChartContract:
    """Read a developer-controlled manifest; invalid contracts fail closed.

    The optional path supports local validation, not per-request configuration.
    Exact-byte hashing permits receipts; it cannot certify correct instructions.
    """
    raw = (Path(path) if path is not None else CONTRACT_PATH).read_bytes()
    _require(len(raw) <= _MAX_BYTES, "FILE_TOO_LARGE")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ContractError(
                "CHART_PLAN_CONTRACT_NONFINITE_NUMBER")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("CHART_PLAN_CONTRACT_JSON_INVALID") from exc
    _validate(doc)
    return ChartContract(_freeze(doc), hashlib.sha256(raw).hexdigest())


CONTRACT = load_contract()
CONTRACT_SHA256 = CONTRACT.sha256
CONTRACT_VERSION = CONTRACT.definitions["contract_version"]
SCHEMA_VERSION = CONTRACT.definitions["wire_schema_version"]
INSTRUCTION_VERSION = CONTRACT.definitions["instruction_version"]
COVERAGE = CONTRACT.definitions["coverage_authority"]
BUDGETS = CONTRACT.definitions["budgets"]
MAX_OPERATIONS = BUDGETS["MAX_OPERATIONS"]
MAX_PARTS = BUDGETS["MAX_PARTS"]
MAX_RESULT_REFS = BUDGETS["MAX_RESULT_REFS"]
MAX_LITERAL_IDS = BUDGETS["MAX_LITERAL_IDS"]
MAX_RESOLVED_IDS = BUDGETS["MAX_RESOLVED_IDS"]
MAX_INFORMATION_FIELDS = BUDGETS["MAX_INFORMATION_FIELDS"]
MAX_QUERY_LENGTH = BUDGETS["MAX_QUERY_LENGTH"]
MAX_STRING_LENGTH = BUDGETS["MAX_STRING_LENGTH"]
MAX_REASON_LENGTH = BUDGETS["MAX_REASON_LENGTH"]
ALL_KINDS = CONTRACT.definitions["node_kinds"]
ID_PATTERN = CONTRACT.definitions["id_pattern"]
OPERATION_KEYS = CONTRACT.definitions["wire_keys"]["operation"]
PART_KEYS = CONTRACT.definitions["wire_keys"]["part"]
ARCHETYPE_PROFILES = CONTRACT.definitions.get("archetype_profiles", {})
ENVELOPE_KEYS = CONTRACT.definitions["wire_keys"]["envelope"]
PLANNED_REASON = CONTRACT.definitions["part_rules"]["planned_reason"]
PART_REASON_RULE = CONTRACT.definitions["part_rules"]["reason"]
PART_OPERATIONS_RULE = CONTRACT.definitions["part_rules"]["operations"]
OPERATION_PROFILES = CONTRACT.definitions["operation_profiles"]
EMPTY_SUBJECT_SCOPES = CONTRACT.definitions["empty_subject_scopes"]
STATIC_ROUTING_GUIDANCE = CONTRACT.definitions["static_routing_guidance"]
QUESTION_INTERFACE = CONTRACT.definitions["question_interface"]


def planner_instructions() -> str:
    """Static routing guidance consumed alongside generated profile descriptions."""
    return "\n".join(STATIC_ROUTING_GUIDANCE)
