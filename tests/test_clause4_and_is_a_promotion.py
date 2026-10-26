"""
tests/test_clause4_and_is_a_promotion.py: Tier 1 Exhaustive Property Tests for
Clause 4 Glossary, Annex C/D Ingestion, and Dual-Provenance IS_A Promotion Engine.

Standard: AWS A3.0M/A3.0:2020 (13th Edition)
"""

import unittest
import fitz

from src.config import PDF_PATH
from src.evidence_clause4_glossary import (
    get_clause4_glossary_store,
    lookup_glossary_term,
    get_nonstandard_redirect,
    MANDATORY_SENTINELS,
)
from src.evidence_annex_c_d import (
    get_annex_c_d_store,
    get_subcommittee_decision,
    get_annex_d_modifications,
)
from src.evidence_is_a_promotion import get_is_a_promotion_store
from src.evidence_tables_a1_a5 import extract_table_a3, extract_table_a5


class TestClause4AndIsAPromotion(unittest.TestCase):
    """Tier 1 Exhaustive Property Tests for Gate 3A."""

    @classmethod
    def setUpClass(cls):
        cls.doc = fitz.open(PDF_PATH)
        cls.glossary_store = get_clause4_glossary_store()
        cls.annex_c_d_store = get_annex_c_d_store()
        cls.promotion_store = get_is_a_promotion_store()
        cls.table_a3 = extract_table_a3(cls.doc)
        cls.table_a5 = extract_table_a5(cls.doc)

    def test_clause4_glossary_entry_count_and_sentinels(self):
        """Verify >= 1400 entries parsed and 100% of 27 alphabetical sentinels present and standard."""
        entries = self.glossary_store.get("entries", [])
        metrics = self.glossary_store.get("metrics", {})

        self.assertGreaterEqual(len(entries), 1400, "Clause 4 must contain >= 1400 parsed entries")
        self.assertGreaterEqual(metrics.get("standard_terms_count", 0), 1300)
        self.assertGreaterEqual(metrics.get("nonstandard_terms_count", 0), 250)

        terms_map = {e["term"].lower(): e for e in entries}

        for sentinel in MANDATORY_SENTINELS:
            self.assertIn(
                sentinel.lower(),
                terms_map,
                f"Mandatory sentinel '{sentinel}' missing from Clause 4 glossary store",
            )
            entry = terms_map[sentinel.lower()]
            self.assertEqual(
                entry.get("term_status"),
                "standard",
                f"Sentinel '{sentinel}' must have term_status='standard'",
            )
            self.assertTrue(entry.get("is_standard"), f"Sentinel '{sentinel}' must have is_standard=True")
            self.assertIsNotNone(entry.get("definition"), f"Sentinel '{sentinel}' must have definition")
            self.assertGreaterEqual(entry.get("printed_page", 0), 5)
            self.assertLessEqual(entry.get("printed_page", 0), 67)
            self.assertTrue(entry.get("observation_id", "").startswith("obs:clause4:p"))

    def test_table_a3_and_a5_coverage_in_clause4(self):
        """Verify 100% of Table A3 (134 designations) and Table A5 (13 obsolete processes) map into Clause 4."""
        entries = self.glossary_store.get("entries", [])
        desig_map = {e["designation"].upper(): e for e in entries if e.get("designation")}
        term_map = {e["term"].lower(): e for e in entries}

        # Verify Table A3 (134 designations)
        self.assertEqual(len(self.table_a3), 134, "Table A3 must contain 134 letter designations")
        missing_a3 = []
        for r in self.table_a3:
            desig = r["designation"].upper()
            proc = r["process"].lower()
            match = desig_map.get(desig) or term_map.get(proc)
            if not match:
                for k, cand in term_map.items():
                    if proc in k or k in proc:
                        match = cand
                        break
            if not match:
                missing_a3.append((desig, proc))

        self.assertEqual(
            len(missing_a3),
            0,
            f"Table A3 designations unmapped in Clause 4: {missing_a3}",
        )

        # Verify Table A5 (13 obsolete processes)
        self.assertEqual(len(self.table_a5), 13, "Table A5 must contain 13 obsolete processes")
        missing_a5 = []
        for r in self.table_a5:
            proc = r["process"].lower()
            desig = r.get("designation")
            match = None
            if desig and desig.upper() in desig_map:
                match = desig_map[desig.upper()]
            elif proc in term_map:
                match = term_map[proc]
            else:
                for k, cand in term_map.items():
                    if proc in k or k in proc:
                        match = cand
                        break
            if not match:
                missing_a5.append((desig, proc))
            else:
                # Ensure entry acknowledges obsolete status or cross references Table A5
                is_flagged = match.get("is_obsolete", False) or "obsolete" in match.get("definition", "").lower()
                self.assertTrue(
                    is_flagged,
                    f"Table A5 process '{proc}' in Clause 4 must reflect obsolete status",
                )

        self.assertEqual(
            len(missing_a5),
            0,
            f"Table A5 obsolete processes unmapped in Clause 4: {missing_a5}",
        )

    def test_dual_provenance_is_a_promotions(self):
        """Verify dual-provenance IS_A promotion engine contracts."""
        metrics = self.promotion_store.get("metrics", {})
        promoted = self.promotion_store.get("promoted_is_a", [])
        retained = self.promotion_store.get("retained_candidates", [])

        self.assertEqual(metrics.get("total_indented_rows"), 118)
        self.assertEqual(metrics.get("promoted_is_a_count"), 35)
        self.assertEqual(metrics.get("retained_candidate_count"), 83)
        self.assertEqual(metrics.get("uncorroborated_promotions_count"), 0)
        self.assertEqual(len(promoted), 35)
        self.assertEqual(len(retained), 83)

        # Check all 35 promoted assertions
        for p in promoted:
            self.assertEqual(p.get("predicate"), "IS_A_PROCESS_VARIATION_OF")
            self.assertEqual(p.get("status"), "ACCEPTED")
            self.assertTrue(p.get("knowledge_eligible"))
            self.assertEqual(p.get("rule_id"), "dual-provenance-is-a-1")

            # Must carry >= 2 distinct source observation IDs
            obs_ids = p.get("source_observation_ids", [])
            self.assertGreaterEqual(len(obs_ids), 2, f"Promoted {p['child_process']} must have >= 2 observation IDs")
            self.assertTrue(any(oid.startswith("obs:table_a1:") for oid in obs_ids))
            self.assertTrue(any(oid.startswith("obs:clause4:") for oid in obs_ids))

            # Must carry verbatim Clause 4 definition quote and corroborating phrase
            self.assertGreater(len(p.get("clause4_quote", "")), 10)
            self.assertGreater(len(p.get("corroborating_phrase", "")), 3)

        # Check retained candidates
        for r in retained:
            self.assertEqual(r.get("predicate"), "CANDIDATE_LAYOUT_PARENT")
            self.assertEqual(r.get("status"), "CANDIDATE")
            self.assertFalse(r.get("knowledge_eligible"))
            self.assertEqual(r.get("rule_id"), "candidate-layout-1")

    def test_nonstandard_terms_never_promoted(self):
        """Verify nonstandard terms are never promoted as standard IS_A parents and resolve to preferred terms."""
        promoted = self.promotion_store.get("promoted_is_a", [])
        glossary_entries = self.glossary_store.get("entries", [])
        nonstd_terms = {e["term"].lower() for e in glossary_entries if e["term_status"] == "nonstandard"}

        for p in promoted:
            self.assertNotIn(
                p["child_process"].lower(),
                nonstd_terms,
                f"Nonstandard term '{p['child_process']}' must NEVER be promoted to standard IS_A subtype",
            )
            self.assertNotIn(
                p["parent_process"].lower(),
                nonstd_terms,
                f"Nonstandard term '{p['parent_process']}' must NEVER be promoted to standard IS_A parent",
            )

        # Verify nonstandard redirects
        test_nonstd = [
            ("MIG", "gas metal arc welding"),
            ("TIG", "gas tungsten arc welding"),
            ("stick electrode welding", "shielded metal arc welding"),
            ("weldor", "welder"),
            ("butt weld", "weld in a butt joint"),
        ]
        for query, expected_target in test_nonstd:
            redir = get_nonstandard_redirect(query, self.glossary_store)
            self.assertIsNotNone(redir, f"Nonstandard query '{query}' must return redirect")
            preferred = [p.lower() for p in redir.get("preferred_terms", [])]
            target_str = (redir.get("target_standard_term") or "").lower()
            matches = any(expected_target.lower() in p for p in preferred) or (expected_target.lower() in target_str)
            self.assertTrue(
                matches,
                f"Nonstandard '{query}' expected '{expected_target}', got preferred={preferred}, target={target_str}",
            )

    def test_annex_d_modifications_cross_check(self):
        """Verify Annex D Tables D1..D6 extraction and Clause 4 cross-verification."""
        cross_check = self.annex_c_d_store.get("cross_verification", {})

        # Table D1 New Terms cross-check
        d1_check = cross_check.get("table_d1_cross_check", {})
        self.assertGreaterEqual(d1_check.get("total_d1_terms", 0), 150)
        self.assertGreaterEqual(d1_check.get("matched_in_clause4", 0), 150)
        self.assertGreaterEqual(d1_check.get("underline_correlation_rate", 0), 0.80)

        # Table D2 Modified Terms cross-check
        d2_check = cross_check.get("table_d2_cross_check", {})
        self.assertGreaterEqual(d2_check.get("total_d2_terms", 0), 150)
        self.assertGreaterEqual(d2_check.get("matched_in_clause4", 0), 150)
        self.assertGreaterEqual(d2_check.get("margin_bar_correlation_rate", 0), 0.80)

        # Table D6 Deleted Terms cross-check
        d6_check = cross_check.get("table_d6_cross_check", {})
        self.assertGreaterEqual(d6_check.get("total_d6_deleted_terms", 0), 25)
        self.assertGreaterEqual(d6_check.get("absence_verification_rate", 0), 0.75)

    def test_domain_delimiters_and_annex_c_rules(self):
        """Verify domain delimiters extraction and Annex C subcommittee decisions."""
        # Check domain delimiters on ultrasonic welding (plastics)
        c4_entries = self.glossary_store.get("entries", [])
        usw_plastics = None
        usw_solid_state = None
        for e in c4_entries:
            if "ultrasonic welding" in e["term"].lower():
                if "plastics" in [d.lower() for d in e.get("domain_delimiters", [])]:
                    usw_plastics = e
                else:
                    usw_solid_state = e

        self.assertIsNotNone(usw_plastics, "Must extract ultrasonic welding with domain_delimiter 'plastics'")
        self.assertIn("fusion welding process", usw_plastics["definition"].lower())

        self.assertIsNotNone(usw_solid_state, "Must extract ultrasonic welding without plastics delimiter")
        self.assertIn("solid-state welding process", usw_solid_state["definition"].lower())

        # Verify Annex C Decisions C1.5.1..C1.5.8
        for i in range(1, 9):
            cid = f"C1.5.{i}"
            dec = get_subcommittee_decision(cid, self.annex_c_d_store)
            self.assertIsNotNone(dec, f"Annex C decision {cid} must be present")
            self.assertGreater(len(dec.get("takeaway", "")), 20)
            self.assertGreater(len(dec.get("clause", {}).get("text", "")), 50)


if __name__ == "__main__":
    unittest.main()
