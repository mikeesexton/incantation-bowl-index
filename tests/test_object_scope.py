import sqlite3
import unittest

from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.object_scope import apply_object_scope_reviews
from bowl_index.review import apply_dedupe_review


def _object(conn, label, locator):
    return add_candidate(conn, {
        "label": label, "record_status": "probable",
        "source": {"source_type": "article", "title": label, "citation": label},
        "appearance": {"locator": locator},
    })


class ObjectScopeTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        migrate(self.conn)
        self.object_id = _object(self.conn, "Metal bowl", "p. 1")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def manifest(self, **entry):
        base = {"id": "IBI-OBJSCOPE-1", "object_id": self.object_id,
                "record_status": "rejected", "object_type": "non_bowl",
                "basis": "Fourteenth-century metal bowl; outside the corpus."}
        base.update(entry)
        return {"schema_version": 1, "decided_by": "Mike Sexton",
                "decided_at": "2026-09-27T22:00:00Z", "entries": [base]}

    def test_rejects_and_keeps_prior_values(self):
        result = apply_object_scope_reviews(self.conn, self.manifest())
        self.assertEqual(result["changed"], 1)
        row = self.conn.execute(
            "SELECT record_status, object_type FROM objects WHERE id=?", (self.object_id,)
        ).fetchone()
        self.assertEqual(tuple(row), ("rejected", "non_bowl"))
        review = self.conn.execute("SELECT * FROM object_scope_reviews").fetchone()
        self.assertEqual(review["previous_record_status"], "probable")
        self.assertEqual(apply_object_scope_reviews(self.conn, self.manifest())["changed"], 0)

    def test_reused_id_with_changed_decision_fails(self):
        apply_object_scope_reviews(self.conn, self.manifest())
        with self.assertRaises(ValueError):
            apply_object_scope_reviews(self.conn, self.manifest(basis="different"))

    def test_ledger_is_append_only(self):
        apply_object_scope_reviews(self.conn, self.manifest())
        with self.assertRaises(sqlite3.DatabaseError):
            self.conn.execute("DELETE FROM object_scope_reviews")


class ResearcherIdentifiedPairTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        migrate(self.conn)
        self.a = _object(self.conn, "Edition bowl", "pp. 1-5")
        self.b = _object(self.conn, "Museum record", "object 1")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_creates_and_decides_missing_candidate(self):
        apply_dedupe_review(self.conn, {
            "object_a_id": self.b, "object_b_id": self.a, "status": "same_object",
            "decided_by": "Mike Sexton", "decided_at": "2026-09-27T22:00:00+00:00",
            "create_candidate": {"rationale": "Same museum number under two schemes."},
            "evidence": [{"evidence_type": "shared_designation", "supports_match": 1}],
        })
        row = self.conn.execute("SELECT * FROM dedupe_candidates").fetchone()
        self.assertEqual(row["status"], "same_object")
        self.assertEqual(row["method"], "researcher_identified")
        self.assertLess(row["object_a_id"], row["object_b_id"])

    def test_without_create_flag_still_requires_existing_candidate(self):
        with self.assertRaises(ValueError):
            apply_dedupe_review(self.conn, {
                "object_a_id": self.a, "object_b_id": self.b, "status": "same_object"})


if __name__ == "__main__":
    unittest.main()
