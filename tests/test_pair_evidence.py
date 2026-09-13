import tempfile
import unittest
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.dedupe import (
    IDENTITY_DISCRIMINATING_GROUPS, normalize_claim_value, pair_evidence,
)
from bowl_index.identity import COVERAGE_GROUPS


class NormalisationTests(unittest.TestCase):
    def test_definite_article_is_not_a_difference(self):
        self.assertEqual(
            normalize_claim_value("location", "The Schøyen Collection"),
            normalize_claim_value("location", "Schøyen Collection"),
        )

    def test_trailing_stop_and_spacing_are_not_a_difference(self):
        self.assertEqual(
            normalize_claim_value("location", "Penn  Museum."),
            normalize_claim_value("location", "Penn Museum"),
        )

    def test_long_and_short_collection_forms_collapse(self):
        self.assertEqual(
            normalize_claim_value(
                "location", "Frau Professor Hilprecht Collection of Babylonian Antiquities, Jena"),
            normalize_claim_value("location", "Frau Professor Hilprecht Collection, Jena"),
        )

    def test_collapsing_applies_only_to_location(self):
        # A bowl's material or dating should not be rewritten by a collection map.
        self.assertEqual(normalize_claim_value("material", "The ceramic"), "ceramic")
        self.assertEqual(
            normalize_claim_value("dating", "University of Pennsylvania Museum"),
            "university of pennsylvania museum",
        )


class DiscriminatingGroupTests(unittest.TestCase):
    def test_every_discriminating_group_is_a_real_coverage_group(self):
        unknown = IDENTITY_DISCRIMINATING_GROUPS - set(COVERAGE_GROUPS)
        self.assertEqual(unknown, set(), "not coverage groups: %s" % sorted(unknown))

    def test_publication_is_not_discriminating(self):
        # Two records of one bowl routinely cite different publications. Treating
        # that as a conflict marks genuine duplicates as suspect.
        self.assertNotIn("publication", IDENTITY_DISCRIMINATING_GROUPS)

    def test_biblical_intertexts_is_not_discriminating(self):
        # Sources list subsets of the verses on a bowl, so two disjoint lists are
        # not a contradiction. A shared verse still counts as agreement.
        self.assertNotIn("biblical_intertexts", IDENTITY_DISCRIMINATING_GROUPS)


class PairEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.conn = connect(Path(self.temp.name) / "t.sqlite3")
        migrate(self.conn)
        self.conn.execute(
            "INSERT INTO sources (id,source_type,title,citation) VALUES ('s1','book','S','S')")
        for oid in ("o1", "o2"):
            self.conn.execute(
                "INSERT INTO objects (id,label,object_type,record_status,authenticity) "
                "VALUES (?,?,'whole_bowl','probable','unassessed')", (oid, oid))

    def claim(self, object_id, field, value):
        self.conn.execute(
            "INSERT INTO claims (id,object_id,source_id,field,value_text,certainty,locator) "
            "VALUES (?,?,'s1',?,?,'reported','p. 1')",
            ("c-%s-%s" % (object_id, field), object_id, field, value))

    def test_location_synonyms_count_as_agreement(self):
        # The regression this module exists for. These two fields hold the same fact
        # under different names; comparing field names reported no overlap.
        self.claim("o1", "current_location", "The Schøyen Collection")
        self.claim("o2", "current_or_reported_collection", "Schøyen Collection")
        result = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(result["band"], "corroborated")
        self.assertEqual(result["agreeing_groups"], ["location"])
        self.assertEqual(result["conflicting_groups"], [])

    def test_differing_publications_are_not_a_conflict(self):
        self.claim("o1", "publication_status", "Edited in Moriggi 2014.")
        self.claim("o2", "publication_status", "Catalogued in MRLA 8.")
        result = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(result["conflicting_groups"], [])
        self.assertEqual(result["differing_non_discriminating_groups"], ["publication"])
        self.assertEqual(result["band"], "no_overlap")

    def test_differing_collections_are_a_conflict(self):
        self.claim("o1", "current_location", "Penn Museum")
        self.claim("o2", "current_or_reported_collection", "British Museum, London")
        result = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(result["band"], "conflict")
        self.assertEqual(result["conflicting_groups"], ["location"])

    def test_one_shared_verse_corroborates_disjoint_lists_do_not_conflict(self):
        self.claim("o1", "biblical_quotation", "Zechariah 3:2")
        self.claim("o2", "biblical_quotations", "Zechariah 3:2")
        self.assertEqual(pair_evidence(self.conn, "o1", "o2")["band"], "corroborated")
        self.conn.execute("UPDATE claims SET value_text='Psalm 24:8' WHERE object_id='o2'")
        second = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(second["conflicting_groups"], [])
        self.assertEqual(second["band"], "no_overlap")

    def test_silence_is_reported_as_no_overlap_not_as_agreement(self):
        self.claim("o1", "dimensions", "180x50 mm.")
        result = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(result["band"], "no_overlap")
        self.assertEqual(result["agreeing_groups"], [])
        self.assertEqual(result["groups_on_one_side_only"], ["dimensions"])


if __name__ == "__main__":
    unittest.main()


class LanguageRefinementTests(PairEvidenceTests):
    """A qualifier appended to a shared reading is not a disagreement."""

    def test_qualified_reading_agrees_with_the_plain_one(self):
        self.claim("o1", "inscription_language", "Jewish Babylonian Aramaic and/or Hebrew")
        self.claim("o2", "inscription_language", "Jewish Babylonian Aramaic")
        self.assertEqual(pair_evidence(self.conn, "o1", "o2")["band"], "corroborated")

    def test_differing_readings_remain_a_conflict(self):
        # CBS 9008: Moriggi reads Syriac, the museum record says Hebrew. A real
        # question for a reviewer, not something to normalise away.
        self.claim("o1", "inscription_language", "Syriac")
        self.claim("o2", "inscription_language", "Hebrew Language")
        result = pair_evidence(self.conn, "o1", "o2")
        self.assertEqual(result["band"], "conflict")
        self.assertEqual(result["conflicting_groups"], ["language"])

    def test_refinement_does_not_apply_outside_language(self):
        # "180x50 mm." must not be read as refining "180x50 mm. with a chipped rim".
        self.claim("o1", "dimensions", "180x50 mm")
        self.claim("o2", "dimensions", "180x50 mm, rim chipped")
        self.assertEqual(pair_evidence(self.conn, "o1", "o2")["band"], "conflict")


class CollectionFormTests(unittest.TestCase):
    def test_third_hilprecht_form_collapses(self):
        base = normalize_claim_value("location", "Frau Professor Hilprecht Collection, Jena")
        for variant in (
            "Frau Professor Hilprecht Collection of Babylonian Antiquities, Jena",
            "Frau Professor Hilprecht Collection, Friedrich Schiller University Jena",
        ):
            self.assertEqual(normalize_claim_value("location", variant), base, variant)

    def test_unrelated_collections_stay_apart(self):
        self.assertNotEqual(
            normalize_claim_value("location", "Vorderasiatisches Museum"),
            normalize_claim_value("location", "Penn Museum"),
        )


class ConsoleWiringTests(unittest.TestCase):
    """The console review surfaces facet evidence, and never a recommendation."""

    def setUp(self):
        from bowl_index.ingest import add_candidate
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "c.sqlite3"
        self.conn = connect(self.db_path)
        migrate(self.conn)
        self.conn.execute(
            "INSERT INTO sources (id,source_type,title,citation) VALUES ('s1','book','S','S')")

        def candidate(label, value, field, claim_value):
            return {
                "label": label, "source_id": "s1", "object_type": "whole_bowl",
                "record_status": "probable", "authenticity": "unassessed",
                "appearance": {"locator": label, "relation_type": "primary",
                               "confidence": 1.0, "rationale": "test"},
                "identifiers": [{"scheme": "collection designation", "value": value,
                                 "assigning_body": "Test Collection", "confidence": 1.0}],
                "claims": [{"field": field, "value_text": claim_value,
                            "certainty": "reported", "locator": "p. 1"}],
            }

        self.a = add_candidate(self.conn, candidate("A", "TC 1", "current_location",
                                                    "The Test Collection"))
        self.b = add_candidate(self.conn, candidate("B", "TC 1", "current_or_reported_collection",
                                                    "Test Collection"))
        self.conn.execute(
            "INSERT INTO dedupe_candidates (id,object_a_id,object_b_id,score,method,rationale) "
            "VALUES (?,?,?,?,?,?)",
            ("ded-x", min(self.a, self.b), max(self.a, self.b), .99, "exact_identifier",
             "Shared identifier: collection designation=tc 1"))
        self.conn.commit()

    def catalog(self):
        from bowl_index.web import CorpusCatalog
        return CorpusCatalog(self.db_path)

    def test_review_carries_facet_evidence(self):
        item = self.catalog().review("ded-x")
        self.assertIn("pair_evidence", item)
        self.assertEqual(item["pair_evidence"]["band"], "corroborated")
        self.assertEqual(item["pair_evidence"]["agreeing_groups"], ["location"])

    def test_queue_rows_carry_a_band(self):
        data = self.catalog().reviews({"status": ["all"], "limit": ["10"]})
        self.assertTrue(data["items"])
        self.assertEqual(data["items"][0]["pair_band"], "corroborated")

    def test_facet_evidence_never_proposes_a_decision(self):
        # The payload reports what the claims say. Deciding is the reviewer's.
        item = self.catalog().review("ded-x")
        self.assertEqual(
            set(item["pair_evidence"]),
            {"band", "agreeing_groups", "conflicting_groups",
             "differing_non_discriminating_groups", "groups_on_one_side_only"},
        )
        self.assertEqual(item["status"], "pending")
