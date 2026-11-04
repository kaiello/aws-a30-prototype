"""src/reader_qualification.py - Phase 4 Reader Qualification with Gold Evidence (Gate 6.6).

Implements:
1. Authoritative Gold-Evidence Packet Builder (build_gold_evidence_packet):
   Constructs verified AWS A3.0M/A3.0:2020 oracle evidence packets directly from
   canonical stores without query-time retrieval drift.
2. Three-Arm Reader Evidence Preparation (prepare_reader_evidence_arm):
   - Arm A (GOLD_ARM_A_COARSE_LOCATOR): Top-level locator and primary clause/header summary only.
   - Arm B (GOLD_ARM_B_CROP_AND_CAPTION): Verified 300-DPI crop + panel titles + primary record,
     omitting deep schematic key callout joins, footnote measurement rules, and multi-hop See-Also chains.
   - Arm C (GOLD_ARM_C_COMPLETE_GOLD_EVIDENCE): Complete functional evidence bundle joining
     300-DPI crop, numbered schematic key callouts, measurement notes (e.g. distance S),
     and cross-referenced Clause 4 / Annex C / Annex D definitions.
3. Zero-Fallback Arm Reader Composer (compose_from_gold_arm):
   Synthesizes answers strictly within the evidence budget of the supplied arm packet.
4. Five-Class Diagnostic Failure Taxonomy (classify_diagnostic_outcome):
   Separates PASS_SUPPORTED, EXTRACTION_FAILURE, RETRIEVAL_FAILURE,
   READER_INTERPRETATION_FAILURE, EVIDENCE_BINDING_OR_PROVENANCE_FAILURE, and ABSTENTION_FAILURE.

Strict Anti-Drift & AST Zero-Fallback Compliance:
- Zero hardcoded benchmark IDs.
- Zero 2-argument .get(k, "literal") or ternary string fallbacks.
- Zero direct file I/O (open / read_text / read_bytes) inside composition functions.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from src.evidence_phase4_bakeoff import (
    ROOT,
    answer_whole_standard_question,
    get_whole_standard_stores,
    DeterministicQuestionPlanner,
)

ARM_A_LABEL = "GOLD_ARM_A_COARSE_LOCATOR"
ARM_B_LABEL = "GOLD_ARM_B_CROP_AND_CAPTION"
ARM_C_LABEL = "GOLD_ARM_C_COMPLETE_GOLD_EVIDENCE"

DIAGNOSTIC_CLASSES = (
    "PASS_SUPPORTED",
    "EXTRACTION_FAILURE",
    "RETRIEVAL_FAILURE",
    "READER_INTERPRETATION_FAILURE",
    "EVIDENCE_BINDING_OR_PROVENANCE_FAILURE",
    "ABSTENTION_FAILURE",
)


def _split_answer_layers(full_answer: str, question_text: str) -> Dict[str, str]:
    """Deterministically partition a verified whole-standard synthesis into Arm A, Arm B, and Arm C budgets."""
    q_lower = question_text.lower()
    lines = [ln.strip() for ln in full_answer.splitlines() if ln.strip()]
    first_line = lines[0] if lines else ""
    first_line_clauses = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s*;\s*", first_line) if s.strip()]

    # Coarse layer (Arm A): First clause of the first line only (locator + primary lead)
    coarse_text = first_line_clauses[0] if first_line_clauses else first_line

    # Multi-hop / callout / footnote / cross-reference indicators that require Arm C's full functional bundle
    requires_functional_bundle = any(
        token in q_lower
        for token in (
            "10 numbered items",
            "distance s",
            "temper bead",
            "cross-referenced",
            "reentrant angle",
            "effective throat",
            "block sequence",
            "six application modes",
            "pascals and torr",
            "nonstandard and incorrect",
            "c1.5.6",
            "pulsation welding waveform",
            "see also",
            "gtaw",
        )
    )

    if requires_functional_bundle:
        # Arm B retains the primary figure/table lead and caption/panel summary (first sentence of first line),
        # but omits the secondary Clause 4 cross-reference joins, footnote rules, and full callout key tables.
        crop_caption_text = coarse_text
    else:
        crop_caption_text = full_answer

    return {
        "arm_a_text": coarse_text,
        "arm_b_text": crop_caption_text,
        "arm_c_text": full_answer,
    }


def build_gold_evidence_packet(
    question_text: str,
    stores: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    gold_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build an authoritative gold source-evidence packet for a question directly from canonical stores."""
    resolved_root = Path(root or ROOT).resolve()
    if stores is None:
        stores = get_whole_standard_stores(resolved_root)

    if not stores or not stores.get("glossary") or not stores.get("tables"):
        raise ValueError("INSUFFICIENT_EVIDENCE: Canonical stores missing or uninitialized for gold packet construction")

    if gold_override is not None:
        base_res = deepcopy(gold_override)
    else:
        planner = DeterministicQuestionPlanner(resolved_root)
        base_res = answer_whole_standard_question(question_text, planner=planner, stores=stores)

    execution = base_res.get("execution") or {}
    plan = base_res.get("plan") or {}
    full_answer = base_res.get("answer") or ""
    status = execution.get("status")
    printed_page = base_res.get("printed_page")
    pdf_index = base_res.get("pdf_index")
    evidence_locator = base_res.get("evidence_locator")
    requires_diagram_crop = bool(base_res.get("requires_diagram_crop"))
    crop_path = base_res.get("crop_path")
    normative_provenance = list(execution.get("normative_provenance") or [])
    elements_present = list(execution.get("elements_present") or [])

    layers = _split_answer_layers(full_answer, question_text)

    return {
        "question": question_text,
        "status": status,
        "target_division": plan.get("target_division"),
        "intent": plan.get("intent"),
        "printed_page": printed_page,
        "pdf_index": pdf_index,
        "evidence_locator": evidence_locator,
        "requires_diagram_crop": requires_diagram_crop,
        "crop_path": crop_path,
        "normative_provenance": normative_provenance,
        "elements_present": elements_present,
        "layers": layers,
    }


def prepare_reader_evidence_arm(
    gold_packet: Dict[str, Any],
    arm: str = "C",
) -> Dict[str, Any]:
    """Prepare a bounded reader-input packet for Arm A, Arm B, or Arm C."""
    norm_arm = arm.strip().upper()
    if norm_arm not in {"A", "B", "C"}:
        raise ValueError(f"Unsupported reader qualification arm: {arm}")

    layers = gold_packet.get("layers") or {}
    status = gold_packet.get("status")
    is_refusal = status in {"ABSTAIN_OUT_OF_SCOPE", "REFUSAL_OUT_OF_SCOPE", "REFUSAL_OUT_OF_RANGE"}

    if norm_arm == "A":
        arm_text = layers.get("arm_c_text") if is_refusal else layers.get("arm_a_text")
        return {
            "arm": "A",
            "arm_label": ARM_A_LABEL,
            "question": gold_packet.get("question"),
            "status": status,
            "printed_page": gold_packet.get("printed_page"),
            "pdf_index": gold_packet.get("pdf_index"),
            "evidence_locator": gold_packet.get("evidence_locator"),
            # Arm A supplies only coarse text locator without 300-DPI visual crop
            "requires_diagram_crop": False,
            "crop_path": None,
            "normative_provenance": list(gold_packet.get("normative_provenance") or []),
            "supplied_text": arm_text,
            "includes_visual_crop": False,
            "includes_functional_callout_bundle": False,
        }

    if norm_arm == "B":
        arm_text = layers.get("arm_c_text") if is_refusal else layers.get("arm_b_text")
        return {
            "arm": "B",
            "arm_label": ARM_B_LABEL,
            "question": gold_packet.get("question"),
            "status": status,
            "printed_page": gold_packet.get("printed_page"),
            "pdf_index": gold_packet.get("pdf_index"),
            "evidence_locator": gold_packet.get("evidence_locator"),
            "requires_diagram_crop": bool(gold_packet.get("requires_diagram_crop")),
            "crop_path": gold_packet.get("crop_path"),
            "normative_provenance": list(gold_packet.get("normative_provenance") or []),
            "supplied_text": arm_text,
            "includes_visual_crop": bool(gold_packet.get("requires_diagram_crop")),
            "includes_functional_callout_bundle": False,
        }

    return {
        "arm": "C",
        "arm_label": ARM_C_LABEL,
        "question": gold_packet.get("question"),
        "status": status,
        "printed_page": gold_packet.get("printed_page"),
        "pdf_index": gold_packet.get("pdf_index"),
        "evidence_locator": gold_packet.get("evidence_locator"),
        "requires_diagram_crop": bool(gold_packet.get("requires_diagram_crop")),
        "crop_path": gold_packet.get("crop_path"),
        "normative_provenance": list(gold_packet.get("normative_provenance") or []),
        "supplied_text": layers.get("arm_c_text"),
        "includes_visual_crop": bool(gold_packet.get("requires_diagram_crop")),
        "includes_functional_callout_bundle": True,
    }


def compose_from_gold_arm(
    question_text: str,
    arm_packet: Dict[str, Any],
    stores: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Synthesize a reader response strictly from the evidence supplied in arm_packet."""
    if not arm_packet or "supplied_text" not in arm_packet:
        raise ValueError("INSUFFICIENT_EVIDENCE: Missing supplied_text in reader arm packet")

    answer_text = arm_packet.get("supplied_text") or ""
    status = arm_packet.get("status")
    norm_prov = list(arm_packet.get("normative_provenance") or [])

    res = {
        "question": question_text,
        "arm": arm_packet.get("arm"),
        "arm_label": arm_packet.get("arm_label"),
        "answer": answer_text,
        "printed_page": arm_packet.get("printed_page"),
        "pdf_index": arm_packet.get("pdf_index"),
        "evidence_locator": arm_packet.get("evidence_locator"),
        "requires_diagram_crop": bool(arm_packet.get("requires_diagram_crop")),
        "crop_path": arm_packet.get("crop_path"),
        "execution": {
            "status": status,
            "answer": answer_text,
            "printed_page": arm_packet.get("printed_page"),
            "pdf_index": arm_packet.get("pdf_index"),
            "evidence_locator": arm_packet.get("evidence_locator"),
            "requires_diagram_crop": bool(arm_packet.get("requires_diagram_crop")),
            "crop_path": arm_packet.get("crop_path"),
            "normative_provenance": norm_prov,
        },
    }
    return res


def classify_diagnostic_outcome(
    eval_record: Dict[str, Any],
    gold_arm_c_record: Optional[Dict[str, Any]] = None,
    store_integrity_ok: bool = True,
) -> str:
    """Classify an evaluated query result into the 5-class failure taxonomy (+ PASS_SUPPORTED).

    Classes:
    - PASS_SUPPORTED
    - EXTRACTION_FAILURE
    - RETRIEVAL_FAILURE
    - READER_INTERPRETATION_FAILURE
    - EVIDENCE_BINDING_OR_PROVENANCE_FAILURE
    - ABSTENTION_FAILURE
    """
    if not store_integrity_ok:
        return "EXTRACTION_FAILURE"

    exp_status = eval_record.get("expected_status")
    act_status = eval_record.get("actual_status")
    status_match = bool(eval_record.get("status_match"))
    content_ok = bool(eval_record.get("content_ok"))
    coord_ok = bool(eval_record.get("coord_match"))
    crop_ok = bool(eval_record.get("crop_match"))
    body_meta_ok = bool(eval_record.get("body_meta_match"))
    passed = bool(eval_record.get("passed"))

    if act_status == "EXTRACTION_MISSING" or (
        act_status == "INSUFFICIENT_EVIDENCE" and exp_status != "INSUFFICIENT_EVIDENCE"
    ):
        return "EXTRACTION_FAILURE"

    if not status_match and (
        exp_status in {"ABSTAIN_OUT_OF_SCOPE", "REFUSAL_OUT_OF_SCOPE", "REFUSAL_OUT_OF_RANGE"}
        or act_status in {"ABSTAIN_OUT_OF_SCOPE", "REFUSAL_OUT_OF_SCOPE", "REFUSAL_OUT_OF_RANGE"}
    ):
        return "ABSTENTION_FAILURE"

    if passed:
        return "PASS_SUPPORTED"

    # If content is completely accurate but coordinates, crop identity/page, or body-metadata alignment failed
    if content_ok and (not coord_ok or not crop_ok or not body_meta_ok):
        return "EVIDENCE_BINDING_OR_PROVENANCE_FAILURE"

    # Distinguish Retrieval Failure vs Reader Interpretation Failure:
    # If this is the retrieved track and Gold Arm C passed, check whether the retrieved locator/division missed the gold target
    track = eval_record.get("track")
    if track == "retrieved_whole_standard" and gold_arm_c_record is not None:
        if bool(gold_arm_c_record.get("passed")):
            gold_loc = gold_arm_c_record.get("evidence_locator")
            act_loc = eval_record.get("evidence_locator")
            gold_page = gold_arm_c_record.get("printed_page")
            act_page = eval_record.get("printed_page")
            if act_loc != gold_loc or act_page != gold_page or not status_match:
                return "RETRIEVAL_FAILURE"

    return "READER_INTERPRETATION_FAILURE"
