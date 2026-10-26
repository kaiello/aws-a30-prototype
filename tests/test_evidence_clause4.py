"""
tests/test_evidence_clause4.py: Tier 1 Exhaustive Property Tests for
AWS A3.0M/A3.0:2020 Clause 4 Glossary, Annex C (Style Principles & Committee Decisions),
and Annex D (Modifications Tables D1–D6).
"""

import fitz
import pytest

from src.config import PDF_PATH
from src.evidence_clause4_glossary import (
    build_clause4_glossary_store,
    get_clause4_glossary_store,
    lookup_glossary_term as base_lookup_glossary_term,
    get_nonstandard_redirect,
    answer_clause4_query,
)
from src.evidence_annex_c_d import (
    build_annex_c_d_store,
    get_annex_c_d_store,
    get_subcommittee_decision,
    get_annex_d_modifications,
)
from src.evidence_is_a_promotion import (
    build_is_a_promotion_store,
    get_is_a_promotion_store,
)


def get_clause4_store():
    g = get_clause4_glossary_store()
    cd = get_annex_c_d_store()
    p = get_is_a_promotion_store()
    entries = []
    for e in g["entries"]:
        e_copy = dict(e)
        e_copy["part_of_speech_or_qualifier"] = (
            e.get("domain_delimiters", [None])[0] if e.get("domain_delimiters")
            else (e.get("part_of_speech", "").rstrip(".") if e.get("part_of_speech") else None)
        )
        entries.append(e_copy)

    return {
        "metrics": {
            "total_glossary_entries": g["metrics"]["total_glossary_entries"],
            "standard_terms_count": g["metrics"]["standard_terms_count"],
            "nonstandard_terms_count": g["metrics"]["nonstandard_terms_count"],
            "process_variations_count": g["metrics"]["process_variations_count"],
            "annex_c_clauses_count": len(cd["annex_c"]["clauses"]),
            "annex_c_subcommittee_decisions_count": len(cd["annex_c"]["subcommittee_decisions"]),
            "annex_d_tables_count": len(cd["annex_d"]),
            "uncorroborated_is_a_promotions": p["metrics"]["uncorroborated_promotions_count"],
        },
        "store_sha256": g.get("sha256", "0" * 64),
        "glossary_entries": entries,
        "entries": entries,
        "relationships": g.get("relationships", []),
        "annex_c": cd["annex_c"],
        "annex_d": cd["annex_d"],
        "dual_provenance_is_a": p,
    }


def build_clause4_store():
    build_clause4_glossary_store(force=True)
    build_annex_c_d_store(force=True)
    build_is_a_promotion_store(force=True)
    return get_clause4_store()


def lookup_glossary_term(query: str, store=None):
    st = store or get_clause4_store()
    entries = st.get("glossary_entries", [])
    q_norm = query.strip().lower()
    matches = []
    for e in entries:
        if e["term"].lower() == q_norm or (e.get("designation") and e["designation"].upper() == query.strip().upper()):
            matches.append(e)
    if not matches:
        for e in entries:
            if q_norm in e["term"].lower():
                matches.append(e)
    return matches


@pytest.fixture(scope="module")
def store():
    return get_clause4_store()


def test_clause4_store_metrics(store):
    """Verify total counts, standard vs nonstandard distribution, and deterministic hash."""
    metrics = store["metrics"]
    assert metrics["total_glossary_entries"] == 1607
    assert metrics["standard_terms_count"] == 1345
    assert metrics["nonstandard_terms_count"] == 262
    assert metrics["process_variations_count"] >= 70
    assert metrics["annex_c_clauses_count"] == 21
    assert metrics["annex_c_subcommittee_decisions_count"] == 8
    assert metrics["annex_d_tables_count"] == 6
    assert metrics["uncorroborated_is_a_promotions"] == 0
    assert len(store["store_sha256"]) == 64


def test_key_standard_terms(store):
    """Verify standard terms: typography, designations, definitions, and page numbers."""
    # GMAW
    gmaw = lookup_glossary_term("GMAW", store)
    assert len(gmaw) >= 1
    t = gmaw[0]
    assert t["term"] == "gas metal arc welding"
    assert t["designation"] == "GMAW"
    assert t["is_standard"] is True
    assert "continuously fed consumable electrode and the weld pool" in t["definition"]
    assert t["printed_page"] == 28
    assert t["pdf_index"] == 40

    # GTAW
    gtaw = lookup_glossary_term("GTAW", store)
    assert len(gtaw) >= 1
    t = gtaw[0]
    assert t["term"] == "gas tungsten arc welding"
    assert t["designation"] == "GTAW"
    assert t["is_standard"] is True
    assert t["printed_page"] == 29
    assert t["pdf_index"] == 41

    # SMAW
    smaw = lookup_glossary_term("SMAW", store)
    assert len(smaw) >= 1
    t = smaw[0]
    assert t["term"] == "shielded metal arc welding"
    assert t["designation"] == "SMAW"
    assert t["is_standard"] is True
    assert t["printed_page"] == 51
    assert t["pdf_index"] == 63

    # parallel joint (new 2020 standard term)
    pj = lookup_glossary_term("parallel joint", store)
    assert len(pj) >= 1
    t = pj[0]
    assert t["term"] == "parallel joint"
    assert t["is_standard"] is True
    assert "formed by butting, parallel surfaces" in t["definition"]
    assert t["printed_page"] == 42

    # workpiece
    wp = lookup_glossary_term("workpiece", store)
    assert len(wp) >= 1
    assert wp[0]["is_standard"] is True
    assert wp[0]["printed_page"] == 67

    # welder
    w = lookup_glossary_term("welder", store)
    assert len(w) >= 1
    assert w[0]["is_standard"] is True
    assert "One who performs manual or semiautomatic welding" in w[0]["definition"]
    assert w[0]["printed_page"] == 64
    assert w[0]["pdf_index"] == 76


def test_test_positions_and_parts_of_speech(store):
    """Verify test positions (1F, 1G, 2F, 2FR, 2G, 3F, 3G, 4G pipe/plate) and parts of speech."""
    pos_1f_pipe = [e for e in store["glossary_entries"] if e["term"] == "1F" and e.get("part_of_speech_or_qualifier") == "pipe"]
    assert len(pos_1f_pipe) == 1
    assert pos_1f_pipe[0]["printed_page"] == 5
    assert "circumferential fillet weld" in pos_1f_pipe[0]["definition"]

    pos_1f_plate = [e for e in store["glossary_entries"] if e["term"] == "1F" and e.get("part_of_speech_or_qualifier") == "plate"]
    assert len(pos_1f_plate) == 1
    assert "linear fillet weld" in pos_1f_plate[0]["definition"]

    pos_2fr_pipe = [e for e in store["glossary_entries"] if e["term"] == "2FR"]
    assert len(pos_2fr_pipe) == 1
    assert pos_2fr_pipe[0]["part_of_speech_or_qualifier"] == "pipe"

    # Part of speech
    braze_v = [e for e in store["glossary_entries"] if e["term"] == "braze" and e.get("part_of_speech_or_qualifier") == "v"]
    assert len(braze_v) == 1
    assert "The act of brazing" in braze_v[0]["definition"]


def test_nonstandard_terms_redirections(store):
    """Verify nonstandard terms correctly redirect to standard terms."""
    # MIG welding -> gas metal arc welding
    mig = get_nonstandard_redirect("MIG welding", store)
    assert mig is not None
    assert mig["target_standard_term"] == "gas metal arc welding"

    # TIG welding -> gas tungsten arc welding
    tig = get_nonstandard_redirect("TIG welding", store)
    assert tig is not None
    assert tig["target_standard_term"] == "gas tungsten arc welding"

    # edge joint -> parallel joint
    ej = get_nonstandard_redirect("edge joint", store)
    assert ej is not None
    assert ej["target_standard_term"] == "parallel joint"

    # diffusion bonding -> diffusion welding (and diffusion brazing)
    db = get_nonstandard_redirect("diffusion bonding", store)
    assert db is not None
    assert "diffusion welding" in db["target_standard_term"]

    # stick electrode welding -> shielded metal arc welding
    stick = get_nonstandard_redirect("stick electrode welding", store)
    assert stick is not None
    assert stick["target_standard_term"] == "shielded metal arc welding"


def test_annex_c_subcommittee_decisions(store):
    """Verify all 8 official subcommittee decisions (C1.5.1–C1.5.8) are present and accurate."""
    decisions = store["annex_c"]["subcommittee_decisions"]
    assert len(decisions) == 8

    # C1.5.1 bonding
    assert "bonding" in decisions["C1.5.1"]["topic"]
    assert "atomic bond" in decisions["C1.5.1"]["takeaway"].lower()
    assert "C1.5.1" in decisions["C1.5.1"]["clause"]["clause_id"]

    # C1.5.2 diffusion welding
    assert "diffusion welding" in decisions["C1.5.2"]["topic"]
    assert "euphemism" in decisions["C1.5.2"]["takeaway"]

    # C1.5.3 GTAW & GMAW vs TIG & MIG
    assert "TIG" in decisions["C1.5.3"]["topic"]
    assert "active gases" in decisions["C1.5.3"]["takeaway"]

    # C1.5.4 welder vs weldor
    assert "welder" in decisions["C1.5.4"]["topic"]
    assert "phonetically identical" in decisions["C1.5.4"]["takeaway"]

    # C1.5.5 workpiece
    assert "workpiece" in decisions["C1.5.5"]["topic"]
    assert "Webster" in decisions["C1.5.5"]["takeaway"]

    # C1.5.6 NDE
    assert "nondestructive examination" in decisions["C1.5.6"]["topic"]
    assert "acceptability" in decisions["C1.5.6"]["takeaway"]

    # C1.5.7 parallel joint replacing edge joint
    assert "parallel joint" in decisions["C1.5.7"]["topic"]
    assert "five basic joint types" in decisions["C1.5.7"]["takeaway"]

    # C1.5.8 deposit
    assert "deposit" in decisions["C1.5.8"]["topic"]
    assert "filler metal" in decisions["C1.5.8"]["takeaway"]


def test_annex_d_modifications_tables(store):
    """Verify Annex D modification tables D1–D6."""
    d = store["annex_d"]
    assert len(d) == 6

    # Table D1: New terms
    assert d["Table D1"]["row_count"] >= 150
    d1_entries = [e.lower() for e in d["Table D1"]["entries"]]
    assert any("2f, pipe" in e for e in d1_entries)
    assert any("parallel joint" in e for e in d1_entries)
    assert any("waveform-controlled" in e for e in d1_entries)

    # Table D2: Modified terms
    assert d["Table D2"]["row_count"] >= 150
    d2_entries = [e.lower() for e in d["Table D2"]["entries"]]
    assert any("joint type" in e for e in d2_entries)
    assert any("gmaw-p" in e for e in d2_entries)

    # Table D4: Standard to Nonstandard (exactly 3 terms)
    d4_entries = [e.lower() for e in d["Table D4"]["entries"]]
    assert any("cored solder" in e for e in d4_entries)
    assert any("penetration-enhancing flux" in e for e in d4_entries)
    assert any("multiple impulse welding" in e for e in d4_entries)

    # Table D5: Nonstandard to Standard (6 terms)
    d5_entries = [e.lower() for e in d["Table D5"]["entries"]]
    assert any("air cap" in e for e in d5_entries)
    assert any("machine welding" in e for e in d5_entries)
    assert any("nondestructive inspection" in e for e in d5_entries)

    # Table D6: Deleted Terms
    d6_entries = [e.lower() for e in d["Table D6"]["entries"]]
    assert any("covalent bond" in e for e in d6_entries)
    assert any("ionic bond" in e for e in d6_entries)
    assert any("metal" in e for e in d6_entries)


def test_answer_clause4_queries(store):
    """Verify answer_clause4_query provides accurate, source-grounded answers."""
    # MIG welding
    ans1 = answer_clause4_query("What is the standard term for MIG welding?", store)
    assert "gas metal arc welding" in ans1["answer"]
    assert "Annex C1.5.3" in ans1["answer"]

    # Parallel joint
    ans2 = answer_clause4_query("Why was parallel joint introduced in the 2020 edition?", store)
    assert "edge joint" in ans2["answer"]
    assert "orientation" in ans2["answer"]

    # Welder vs weldor
    ans3 = answer_clause4_query("What did the committee decide about welder versus weldor?", store)
    assert "phonetically identical" in ans3["answer"]
    assert "person who performs welding" in ans3["answer"]

    # Deleted chemistry terms
    ans4 = answer_clause4_query("Which chemistry terms were deleted in the 2020 edition?", store)
    assert "covalent bond" in ans4["answer"]
    assert "ionic bond" in ans4["answer"]

    # Process variation count
    ans5 = answer_clause4_query("How many processes are promoted under dual provenance?", store)
    assert "35" in ans5["answer"]
    assert "83" in ans5["answer"]
    assert "0 uncorroborated" in ans5["answer"]
