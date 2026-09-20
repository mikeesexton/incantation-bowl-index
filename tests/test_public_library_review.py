import json
import sqlite3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_public_library_review as review  # noqa: E402


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

    def test_packet_is_pending_and_contains_no_text_content(self):
        self.assertEqual(self.packet["status"], "pending_owner_decision")
        self.assertNotIn('"content"', self.packet_path.read_text(encoding="utf-8"))

    def test_exact_proposal_still_matches_live_evidence(self):
        material = {
            "texts": review.proposed_text_entries(self.conn),
            "media": review.proposed_media_entries(self.conn),
        }
        self.assertEqual(review.stable_hash(material), self.packet["cohort_sha256"])
        self.assertEqual(material, {
            "texts": self.packet["texts"],
            "media": self.packet["media"],
        })

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


if __name__ == "__main__":
    unittest.main()
