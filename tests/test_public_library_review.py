import json
import sqlite3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_public_library_review as review  # noqa: E402
import materialize_public_library_approval as approval  # noqa: E402


class PublicLibraryReviewPacketTests(unittest.TestCase):
    packet_path = ROOT / "research" / "reviews" / "public_library_expansion_review_2026-09-20.json"

    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(cls.packet_path.read_text(encoding="utf-8"))
        cls.conn = sqlite3.connect("file:%s?mode=ro" % review.DEFAULT_DB, uri=True)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_packet_is_owner_approved_and_contains_no_text_content(self):
        self.assertEqual(self.packet["status"], "approved_by_owner")
        self.assertFalse(self.packet["approval"]["deployment_authorized"])
        self.assertNotIn('"content"', self.packet_path.read_text(encoding="utf-8"))

    def test_exact_proposal_still_matches_live_evidence(self):
        packet_material = {
            "texts": self.packet["texts"],
            "media": self.packet["media"],
        }
        self.assertEqual(review.stable_hash(packet_material), self.packet["cohort_sha256"])
        live_text = {row["text_id"]: row for row in review.proposed_text_entries(self.conn)}
        live_media = {row["media_id"]: row for row in review.proposed_media_entries(self.conn)}
        for row in self.packet["texts"]:
            self.assertEqual(row["evidence_sha256"], live_text[row["text_id"]]["evidence_sha256"])
            self.assertEqual(row["proposed_review"], live_text[row["text_id"]]["proposed_review"])
        for row in self.packet["media"]:
            self.assertEqual(row["evidence_sha256"], live_media[row["media_id"]]["evidence_sha256"])
            self.assertEqual(row["proposed_review"], live_media[row["media_id"]]["proposed_review"])

    def test_bounded_cohorts_and_required_penn_credits(self):
        self.assertEqual(len(self.packet["texts"]), 6)
        self.assertEqual(len(self.packet["media"]), 288)
        self.assertEqual(len({row["image_url"] for row in self.packet["media"]}), 280)
        self.assertNotIn(review.EXCLUDED_PARTIAL_TEXT_ID,
                         {row["text_id"] for row in self.packet["texts"]})
        for row in self.packet["media"]:
            self.assertEqual(
                row["proposed_review"]["attribution"],
                "Object %s. Courtesy of the Penn Museum." % row["collection_designation"],
            )
            self.assertIn("penn.museum", row["proposed_review"]["rights_locator"])

    def test_ingestion_manifests_are_the_exact_approved_cohort(self):
        text_manifest = json.loads(approval.DEFAULT_TEXT_OUT.read_text(encoding="utf-8"))
        media_manifest = json.loads(approval.DEFAULT_MEDIA_OUT.read_text(encoding="utf-8"))
        self.assertEqual(text_manifest["approved_cohort_sha256"], approval.APPROVED_COHORT)
        self.assertEqual(media_manifest["approved_cohort_sha256"], approval.APPROVED_COHORT)
        self.assertEqual(len(text_manifest["entries"]), 6)
        self.assertEqual(len(media_manifest["entries"]), 288)
        self.assertNotIn('"content"', approval.DEFAULT_TEXT_OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
