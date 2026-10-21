"""Synthetic source geometry; no licensed chart labels or code pairs."""
from copy import deepcopy
from types import SimpleNamespace
import pytest

from src import evidence_a1 as a1


class SyntheticChart:
    rect = SimpleNamespace(width=600, height=800)

    def __init__(self):
        self.boxes = [(240,330,334,394), (65,65,270,272), (325,66,543,137),
                      (340,173,543,293), (66,288,200,392), (364,329,543,466),
                      (66,412,205,473), (66,494,205,638), (334,499,543,638)]
        self.segments = [((366,506),(288,389)), ((288,330),(351,121)),
                         ((276,336),(223,265)), ((305,339),(372,288)),
                         ((260,384),(200,451)), ((276,388),(202,546)),
                         ((198,359),(380,359))]
        self.lines = []
        for i, text in enumerate(("SYNTHETIC", "CENTRAL", "ROOT")):
            self.add(text, (250,335+i*15,325,346+i*15), True)
        for i, (x0,y0,x1,y1) in enumerate(self.boxes[1:]):
            self.add("GROUP " + chr(65+i), (x0+8,y0+4,x0+80,y0+14), True)
            self.add("fictional process " + chr(97+i), (x0+8,y0+24,x0+78,y0+33))
            self.add("fictional variant " + chr(97+i), (x0+18,y0+39,x0+88,y0+48))
            self.add("Q" + chr(65+i) + "A", (x1-30,y0+24,x1-8,y0+33))
            self.add("Q" + chr(65+i) + "B", (x1-30,y0+39,x1-8,y0+48))
        self.add("ACCOUNT FOOTER SYNTHETIC", (40,760,500,770))
        self.add("UNRELATED HEADER", (40,20,500,30))

    def add(self, text, box, bold=False):
        self.lines.append({"bbox":box, "spans":[{"text":text, "flags":16 if bold else 0}]})

    def get_drawings(self):
        return [{"type":"s", "items":[("re",box,1)]} for box in self.boxes] + [
            {"type":"s", "items":[("l",*s) for s in self.segments]}]

    def get_text(self, kind="text"):
        if kind == "dict":
            return {"blocks":[{"lines":deepcopy(self.lines)}]}
        return "Synthetic Figure A1 caption"


def test_exact_pairs_geometry_topology_and_indentation_qualifications():
    graph = a1.extract_a1_chart(SyntheticChart(), "fixture:geometry")
    assert len(graph["nodes"]) == 25
    assert sum(e["type"] == "CHART_CONNECTOR" for e in graph["edges"]) == 8
    assert sum(e["type"] == "ENCLOSES_ROW" for e in graph["edges"]) == 16
    assert sum(e["type"] == "INDENTED_UNDER" for e in graph["edges"]) == 8
    assert graph["edge_qualifications"]["INDENTED_UNDER"]["verification"] == "candidate"
    assert graph["edge_qualifications"]["CHART_CONNECTOR"]["verification"] == "source_bound"
    assert "ACCOUNT" not in graph["native_text"] and "HEADER" not in graph["native_text"]
    for node in graph["nodes"]:
        y0,x0,y1,x1 = node["region"]
        assert 0 <= y0 < y1 <= 1 and 0 <= x0 < x1 <= 1


def test_nested_ids_are_reproducible_and_edition_bound():
    first = a1.extract_a1_chart(SyntheticChart(), "fixture:one")
    assert first == a1.extract_a1_chart(SyntheticChart(), "fixture:one")
    other = a1.extract_a1_chart(SyntheticChart(), "fixture:two")
    assert set(n["id"] for n in first["nodes"]).isdisjoint(n["id"] for n in other["nodes"])


def test_missing_physical_connector_fails_closed():
    page = SyntheticChart()
    page.segments.pop(0)
    with pytest.raises(ValueError, match="CONNECTOR_COVERAGE_INCOMPLETE"):
        a1.extract_a1_chart(page, "fixture:one")


def test_missing_code_or_two_codes_cannot_become_a_row():
    for remove in (True, False):
        page = SyntheticChart()
        code = next(l for l in page.lines if l["spans"][0]["text"] == "QAA")
        if remove:
            page.lines.remove(code)
        else:
            page.add("ZZZ", (180,89,200,98))
        with pytest.raises(ValueError, match="ROW_CODE_AMBIGUOUS"):
            a1.extract_a1_chart(page, "fixture:one")


def test_changed_column_and_unfamiliar_indent_are_rejected():
    for column in (True, False):
        page = SyntheticChart()
        text = "QAB" if column else "fictional variant a"
        line = next(l for l in page.lines if l["spans"][0]["text"] == text)
        x0,y0,x1,y1 = line["bbox"]
        line["bbox"] = (x0+4,y0,x1+4,y1) if column else (x0+8,y0,x1+8,y1)
        with pytest.raises(ValueError, match="CODE_COLUMN_AMBIGUOUS|INDENTATION_AMBIGUOUS"):
            a1.extract_a1_chart(page, "fixture:one")


def test_a_table_cannot_be_passed_as_the_figure():
    with pytest.raises(ValueError, match="FIGURE_IDENTITY_REQUIRED"):
        a1.extract_a1_chart(SyntheticChart(), "fixture:one", element_id="Table A1")


def test_literal_retrieval_traverses_all_parents_and_preserves_chart_context():
    full = a1.extract_a1_chart(SyntheticChart(), "fixture:one")
    view = a1.retrieve_a1_graph(full, "Compare fictional variant a and QBB")
    retained = {n.get("code") for n in view["nodes"] if n["kind"] == "process"}
    assert retained == {"QAA", "QAB", "QBA", "QBB"}
    assert len(view["nodes"]) == 13
    assert sum(e["type"] == "CHART_CONNECTOR" for e in view["edges"]) == 8
    assert view["full_source_graph_counts"] == {"nodes":25,"edges":32}
    assert len(view["full_source_graph_sha256"]) == 64
    assert view["selection"]["status"] == "literal_process_match"
    # Traversal retains every supplied candidate ancestor, not just the first.
    variant = next(n for n in full["nodes"] if n.get("code") == "QAB")
    extra = next(n for n in full["nodes"] if n.get("code") == "QCA")
    full["edges"].append({"from":extra["id"],"to":variant["id"],"type":"INDENTED_UNDER","region":variant["region"]})
    expanded = a1.retrieve_a1_graph(full, "QAB")
    assert "QCA" in {n.get("code") for n in expanded["nodes"]}


def test_retrieval_requires_literal_case_sensitive_code_and_has_no_guessed_relevance():
    full = a1.extract_a1_chart(SyntheticChart(), "fixture:one")
    view = a1.retrieve_a1_graph(full, "What is qab or an unknown zenthorp process?")
    assert not any(n["kind"] == "process" for n in view["nodes"])
    assert view["selection"]["status"] == "category_context_only"
    assert not view["selection"]["seed_ids"]


def test_longest_literal_phrase_seeds_child_then_recovers_parent_by_traversal():
    full = a1.extract_a1_chart(SyntheticChart(), "fixture:one")
    parent = next(n for n in full["nodes"] if n.get("code") == "QAA")
    child = next(n for n in full["nodes"] if n.get("code") == "QAB")
    child["label"] = parent["label"] + " variation"
    view = a1.retrieve_a1_graph(full, child["label"])
    assert view["selection"]["seed_ids"] == [child["id"]]
    assert parent["id"] in view["selection"]["ancestor_ids"]


class SyntheticScopeManifest:
    def __init__(self):
        pages = [{"pdf_index":i,"printed_label":"synthetic-" + str(i)} for i in range(100)]
        pages[87]["printed_label"] = "75"
        pages[88]["printed_label"] = "76"
        pages[90]["printed_label"] = "88"
        self.document = {"pages":pages}

    def resolve(self, label):
        labels = {"figure a1":"Figure A1", "figure b6":"Figure B6", "figure a2":"Figure A2",
                  "table a1":"Table A1", "annex a":"Annex A", "annex b":"Annex B", "clause 4":"Clause 4"}
        key = label.casefold()
        if key in labels:
            return {"status":"exact", "labels":[labels[key]], "target_ids":["synthetic:" + key]}
        return {"status":"unknown", "labels":[], "target_ids":[]}

    def labels(self, kind):
        return {"figures":["Figure A1","Figure A2","Figure B6"],"tables":["Table A1"]}.get(kind,[])


@pytest.mark.parametrize("query", ["Figure A1 and B6", "Figure A1, B6", "Fig. A1 and B6",
                                    "Figures A1 and B6", "Figure A1 and 2", "Figure A1 and Table A1",
                                    "Annex B Figure A1", "Figure A1(A)"])
def test_scope_checks_shorthand_lists_external_sources_and_unsupported_qualifiers(query):
    diagnostics = a1.scope_query_diagnostics(query, SyntheticScopeManifest(), {"pdf_index":87})
    assert diagnostics


@pytest.mark.parametrize("query", ["Figure A1, p. 75", "Annex A Figure A1 on printed page 75",
                                    "Figure A1, PDF page 88", "Figure A1 PDF p.88",
                                    "Figure A1 at PDF ordinal 88"])
def test_scope_accepts_only_matching_printed_page_or_explicit_pdf_ordinal(query):
    assert a1.scope_query_diagnostics(query, SyntheticScopeManifest(), {"pdf_index":87}) == []


@pytest.mark.parametrize("query", ["Figure A1, p. 88", "Figure A1, printed page 76",
                                    "Figure A1, PDF page 75", "Figure A1 PDF pages 88-89",
                                    "Figure A1 pp.75-76", "Figure A1 page 999999999",
                                    "Figure A1 PDF page 999999999", "Figure A1 pages 75 and 76"])
def test_scope_rejects_wrong_ambiguous_unknown_or_extra_page_binding(query):
    diagnostics = a1.scope_query_diagnostics(query, SyntheticScopeManifest(), {"pdf_index":87})
    assert any("page_" in diagnostic for diagnostic in diagnostics)


def test_scope_requires_every_duplicate_printed_page_candidate_to_match_selected_anchor():
    manifest = SyntheticScopeManifest()
    manifest.document["pages"][2]["printed_label"] = "75"
    assert a1.scope_query_diagnostics("Figure A1 p.75", manifest, {"pdf_index":87})


def test_source_identity_is_view_independent_and_binds_edition_element_anchor_and_asset():
    anchor = {"pdf_index":7,"printed_label":"3","order":0,"role":"start","region":None}
    identity = a1.a1_source_identity_id("fixture:one", "figure:figure_a1", anchor, "a"*64)
    assert identity == a1.a1_source_identity_id("fixture:one", "figure:figure_a1", dict(anchor), "a"*64)
    assert identity != a1.a1_source_identity_id("fixture:two", "figure:figure_a1", anchor, "a"*64)
    assert identity != a1.a1_source_identity_id("fixture:one", "table:table_a1", anchor, "a"*64)
    assert identity != a1.a1_source_identity_id("fixture:one", "figure:figure_a1", dict(anchor,pdf_index=8), "a"*64)
    assert identity != a1.a1_source_identity_id("fixture:one", "figure:figure_a1", anchor, "b"*64)
    first = a1._make("fixture:one", "figure_region", {"element_id":"Figure A1","canonical_element_id":"figure:figure_a1", "source_identity_id":identity},
                     {"source_identity_id":identity,"selected_graph":"synthetic view one"})
    second = a1._make("fixture:one", "figure_region", dict(first.locator),
                      {"source_identity_id":identity,"selected_graph":"synthetic view two"})
    assert first.evidence_id != second.evidence_id
    assert first.locator["source_identity_id"] == second.locator["source_identity_id"]


@pytest.mark.parametrize("fault", ["table", "pages", "missing_image"])
def test_loader_checks_single_source_identity_and_asset(monkeypatch, tmp_path, fault):
    record = {"id":"figure:figure_a1", "label":"Figure A1", "parent_id":"clause:annex_a",
              "anchors":[{"pdf_index":0,"printed_label":"1","order":0,"role":"start",
                          "region":None,"verification":{"state":"verified"}}],
              "assets":[{"source_anchor_orders":[0],"relpath":"parsed/figure.png",
                         "sha256":"a"*64,"verification":{"state":"verified"}}]}
    if fault == "table":
        record["id"],record["label"] = "table:table_a1","Table A1"
    elif fault == "pages":
        record["anchors"].append(dict(record["anchors"][0],order=1))
    manifest = SimpleNamespace(element=lambda label:record if label == "Figure A1" else {
        "id":"table:table_a1","label":"Table A1"}, validated_assets=lambda *args:[{
        "status":"missing" if fault == "missing_image" else "complete"}])
    monkeypatch.setattr(a1,"_source",lambda _: (manifest,"fixture:one",tmp_path/"unused.pdf"))
    with pytest.raises(ValueError, match="MANIFEST_IDENTITY_INVALID|ONE_SOURCE_PAGE_REQUIRED|SOURCE_IMAGE_INVALID"):
        a1.load_a1_evidence(tmp_path)
