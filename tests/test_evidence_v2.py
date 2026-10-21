"""Software contract tests over original synthetic data, not AWS semantics."""
import base64
from dataclasses import replace
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from src.evidence_v2 import EvidenceStore, evidence_id
from src.evidence_reader import LocalVisionReader, build_messages, read_packet
from evidence_v2_fixture import fixture, png_bytes


def test_ids_bind_edition_locator_and_content(tmp_path):
    _, data = fixture(tmp_path)
    item = data["collar"]
    assert evidence_id(item.edition_id, item.kind, dict(item.locator), dict(item.content)) == item.evidence_id
    assert evidence_id(item.edition_id + "other", item.kind, item.locator, item.content) != item.evidence_id
    assert evidence_id(item.edition_id, item.kind, item.locator, dict(item.content, text="Other text")) != item.evidence_id


def test_alias_lookup_retains_all_definition_conditions(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Define retaining ring")
    assert packet.route.kind == "definition"
    assert data["collar"].evidence_id in [item.evidence_id for item in packet.evidence]
    result = read_packet(packet, tmp_path)
    assert result["answer_outcome"] == "composed"
    for text in [data["collar"].content["text"], *data["collar"].content["qualifiers"],
                 *data["collar"].content["exceptions"], *data["collar"].content["notes"]]:
        assert text in result["answer"]
    assert result["answer_assessment"]["status"] == "SOURCE_BOUND_EXTRACT"


def test_same_headword_multiple_senses_requires_clarification(tmp_path):
    store, _ = fixture(tmp_path)
    packet = store.packet("Define nozzle")
    assert packet.route.kind == "ambiguity"
    assert packet.status == "clarification_required"
    assert len(packet.route.alternatives) == 2
    assert read_packet(packet, tmp_path)["answer_outcome"] == "clarification_required"


def test_alias_shared_by_distinct_headwords_requires_clarification(tmp_path):
    _, data = fixture(tmp_path)
    items = []
    for item in (data["collar"], data["sleeve"]):
        content = dict(item.content, aliases=["common tip"])
        items.append(replace(item, content=content,
                             evidence_id=evidence_id(item.edition_id, item.kind, item.locator, content)))
    packet = EvidenceStore(items).packet("Define common tip")
    assert packet.status == "clarification_required"
    assert packet.route.kind == "ambiguity"
    assert len(packet.route.alternatives) == 2


def test_table_row_keeps_headers_cells_and_footnotes(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Table X1 copper")
    assert packet.route.kind == "table"
    assert packet.status == "complete"
    result = read_packet(packet, tmp_path)
    for text in [*data["row"].content["headers"], *data["row"].content["cells"],
                 *data["row"].content["footnotes"], *data["row"].content["exceptions"]]:
        assert text in result["answer"]


def test_unknown_table_selector_withholds_instead_of_dumping_whole_table(tmp_path):
    store, _ = fixture(tmp_path)
    packet = store.packet("Table X1 imaginary missing material")
    assert packet.status == "insufficient_evidence"
    assert "table_selector_not_found" in str(packet.missing)
    assert not read_packet(packet, tmp_path)["grounded_claims"]


def test_process_acronym_is_not_an_ordinary_question_word(tmp_path):
    _, data = fixture(tmp_path)
    item = data["row"]
    content = dict(item.content, headers=["Process", "Code"], cells=["invented stabilization", "IS"])
    row = replace(item, content=content, evidence_id=evidence_id(item.edition_id, item.kind, item.locator, content))
    store = EvidenceStore([row])
    missing = store.packet("In Table X1, what is the code for imaginary zenthorp welding?")
    assert missing.status == "insufficient_evidence"
    assert not read_packet(missing, tmp_path)["grounded_claims"]
    assert store.packet("Table X1 IS").status == "complete"


def test_explicit_alias_target_prunes_competing_alias_only_targets(tmp_path):
    _, data = fixture(tmp_path)
    items = []
    for key in ("collar", "sleeve"):
        item = data[key]
        content = dict(item.content, aliases=["common tip"])
        items.append(replace(item, content=content,
                             evidence_id=evidence_id(item.edition_id, item.kind, item.locator, content)))
    packet = EvidenceStore(items).packet("Define common tip meaning collar")
    assert packet.status == "complete"
    assert [i.content["headword"] for i in packet.evidence] == ["collar"]


def test_heading_only_table_is_insufficient_not_a_table_answer(tmp_path):
    _, data = fixture(tmp_path)
    row = data["row"]
    content = dict(row.content, cells=[])
    row = replace(row, content=content, evidence_id=evidence_id(row.edition_id, row.kind, row.locator, content))
    packet = EvidenceStore([row]).packet("Table X1 copper")
    assert packet.status == "insufficient_evidence"
    assert read_packet(packet, tmp_path)["answer_outcome"] == "insufficient_evidence"


def test_table_dict_cells_require_every_header(tmp_path):
    _, data = fixture(tmp_path)
    row = data["row"]
    content = dict(row.content, cells={"Material": "copper", "Cleaning solution": "water"})
    row = replace(row, content=content, evidence_id=evidence_id(row.edition_id, row.kind, row.locator, content))
    packet = EvidenceStore([row]).packet("Table X1 copper")
    assert packet.status == "insufficient_evidence"
    assert read_packet(packet, tmp_path)["answer_outcome"] == "insufficient_evidence"


def test_figure_packet_follows_required_continuations_and_note(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Figure X1")
    assert packet.route.kind == "visual"
    assert packet.status == "complete"
    figures = [item for item in packet.evidence if item.kind == "figure_region"]
    assert [item.locator["order"] for item in figures] == [0, 1]
    assert data["note"].evidence_id in [item.evidence_id for item in packet.evidence]
    text = str(build_messages(packet, tmp_path))
    assert data["note"].content["text"] in text


def test_final_reader_request_contains_actual_ordered_png_bytes(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Figure X1")
    seen = []
    def generate(messages):
        seen.extend(messages)
        return {"claims": [{"text": "The synthetic image has a colored field.",
                            "evidence_ids": [item.evidence_id for item in data["figures"]]}],
                "usage": {"input_tokens": 10, "output_tokens": 5}}
    result = read_packet(packet, tmp_path, generate=generate)
    images = [part["image_url"]["url"] for message in seen
              if isinstance(message.get("content"), list) for part in message["content"]
              if part.get("type") == "image_url"]
    assert len(images) == 2
    assert [base64.b64decode(url.split(",", 1)[1]) for url in images] == [
        png_bytes((38, 105, 184)), png_bytes((223, 146, 49))]
    assert result["answer_assessment"]["status"] == "UNASSESSED"
    assert result["answer_assessment"]["validated"] is False


def test_final_ollama_request_preserves_original_png_bytes_and_order(tmp_path):
    store, _ = fixture(tmp_path)
    # Test only the deterministic transport body, with no provider call.
    reader = LocalVisionReader("http://localhost:11434", "fixture-vision")
    body = reader.request_body(build_messages(store.packet("Figure X1"), tmp_path))
    images = [raw for message in body["messages"] for raw in message.get("images", [])]
    assert [base64.b64decode(raw) for raw in images] == [
        png_bytes((38, 105, 184)), png_bytes((223, 146, 49))]
    assert body["model"] == "fixture-vision"


def test_missing_required_continuation_blocks_reader(tmp_path):
    _, data = fixture(tmp_path)
    store = EvidenceStore([item for item in data["items"]
                           if item.evidence_id != data["figures"][1].evidence_id])
    packet = store.packet("Figure X1")
    assert packet.status == "insufficient_evidence"
    assert data["figures"][1].evidence_id in str(packet.missing)
    def generate(_):
        pytest.fail("Missing required evidence must prevent generation")
    assert read_packet(packet, tmp_path, generate=generate)["answer_outcome"] == "insufficient_evidence"


def test_stripping_dependency_tuples_does_not_hide_missing_continuation(tmp_path):
    _, data = fixture(tmp_path)
    items = [replace(item, required_ids=()) for item in data["items"]
             if item.evidence_id != data["figures"][1].evidence_id]
    packet = EvidenceStore(items).packet("Figure X1")
    assert packet.status == "insufficient_evidence"


def test_stripping_dependency_tuples_does_not_hide_required_note(tmp_path):
    _, data = fixture(tmp_path)
    items = [replace(item, required_ids=()) for item in data["items"]
             if item.evidence_id != data["note"].evidence_id]
    packet = EvidenceStore(items).packet("Figure X1")
    assert packet.status == "insufficient_evidence"


def test_candidate_record_cannot_become_supported_answer(tmp_path):
    _, data = fixture(tmp_path)
    store = EvidenceStore([replace(data["collar"], verification="candidate")])
    packet = store.packet("Define collar")
    def generate(_):
        pytest.fail("Candidate evidence must not reach generation")
    result = read_packet(packet, tmp_path, generate=generate)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert not result.get("grounded_claims")


def test_corrupted_asset_blocks_reader_before_model_call(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Figure X1")
    (tmp_path / data["figures"][1].content["asset_relpath"]).write_bytes(b"not an image")
    def generate(_):
        pytest.fail("Corrupt pixels must not reach generation")
    result = read_packet(packet, tmp_path, generate=generate)
    assert result["answer_outcome"] == "insufficient_evidence"


def test_asset_path_cannot_escape_fixture_root(tmp_path):
    _, data = fixture(tmp_path)
    first = data["figures"][0]
    content = dict(first.content, asset_relpath="../escaped.png")
    unsafe = replace(first, content=content,
                     evidence_id=evidence_id(first.edition_id, first.kind, first.locator, content))
    store = EvidenceStore([unsafe, data["figures"][1], data["note"]])
    def generate(_):
        pytest.fail("Outside-root image path must not reach generation")
    assert read_packet(store.packet("Figure X1"), tmp_path, generate=generate)["answer_outcome"] == "insufficient_evidence"


def test_unknown_generated_claim_binding_is_rejected(tmp_path):
    store, _ = fixture(tmp_path)
    def generate(_):
        return {"claims": [{"text": "Unsupported detail [Figure X1].",
                            "evidence_ids": ["ev:invented"]}], "usage": {}}
    result = read_packet(store.packet("Figure X1"), tmp_path, generate=generate)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert not result.get("grounded_claims")


def test_reversed_packet_evidence_order_is_withheld(tmp_path):
    store, _ = fixture(tmp_path)
    packet = store.packet("Figure X1")
    packet = replace(packet, evidence=tuple(reversed(packet.evidence)))
    def generate(_):
        pytest.fail("A reordered continuation packet must not reach generation")
    assert read_packet(packet, tmp_path, generate=generate)["answer_outcome"] == "insufficient_evidence"


def test_malformed_model_result_is_withheld(tmp_path):
    store, _ = fixture(tmp_path)
    result = read_packet(store.packet("Figure X1"), tmp_path, generate=lambda _: None)
    assert result["answer_outcome"] == "insufficient_evidence"
    assert not result.get("grounded_claims")


def test_crossmodal_comparison_uses_both_definition_and_image_evidence(tmp_path):
    store, data = fixture(tmp_path)
    packet = store.packet("Compare collar and sleeve in Figure X1")
    assert packet.route.kind == "comparison"
    ids = {item.evidence_id for item in packet.evidence}
    assert {data["collar"].evidence_id, data["sleeve"].evidence_id,
            *[item.evidence_id for item in data["figures"]]} <= ids
    assert "Only while the collar is tightened." in str(packet.to_dict())


def test_complete_packet_route_is_independent_of_source_insertion_order(tmp_path):
    store, data = fixture(tmp_path)
    query = "Compare collar and sleeve in Figure X1"
    packet = store.packet(query)
    reversed_packet = EvidenceStore(list(reversed(data["items"]))).packet(query)
    assert packet.route == reversed_packet.route
    assert packet.evidence == reversed_packet.evidence
    assert build_messages(packet, tmp_path) == build_messages(reversed_packet, tmp_path)


def test_unknown_source_reference_yields_explicit_missing_evidence(tmp_path):
    store, _ = fixture(tmp_path)
    packet = store.packet("Table X9 copper")
    assert packet.status == "insufficient_evidence"
    assert read_packet(packet, tmp_path)["answer_outcome"] == "insufficient_evidence"


def test_comparison_harness_keeps_software_counts_separate_from_semantics(tmp_path):
    from eval.evidence_v2_compare import ComparisonCase, compare_cases, fixture_cases, fixture_v2_lane
    store, data = fixture(tmp_path)
    def mocked_v1(query):
        return {"query": query, "answer_outcome": "generated",
                "answer_assessment": {"status": "UNASSESSED", "validated": False},
                "comparison_observation": {"model_image_count": 0}}
    receipt = compare_cases(fixture_cases(data), mocked_v1, fixture_v2_lane(store, tmp_path),
                            v1_mode="software_mocked", v2_mode="software_mocked")
    assert len(receipt["cases"]) == 6
    assert receipt["lane_modes"] == {"v1": "software_mocked", "v2": "software_mocked"}
    assert all(row[lane]["semantic_correctness"] is None
               for row in receipt["cases"] for lane in ("v1", "v2"))
    visual = next(row for row in receipt["cases"] if row["case_id"] == "multipage_figure")
    assert visual["v2"]["observed_model_image_count"] == 2
    assert visual["v2"]["all_required_evidence"] is True
    with pytest.raises(ValueError):
        compare_cases([ComparisonCase("x", "Define collar", "text")], mocked_v1, mocked_v1,
                      v1_mode="", v2_mode="software_mocked")
