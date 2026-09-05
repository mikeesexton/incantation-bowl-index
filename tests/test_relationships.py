import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.relationships import apply_relationship_review, relationship_evidence_sha256


class RelationshipReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / "db.sqlite3")
        migrate(self.conn)
        self.subject = add_candidate(self.conn, {
            "object_id": "IBI-SUBJECT", "label": "Subject bowl",
            "source": {"source_type": "museum_record", "title": "Museum subject",
                       "citation": "Museum subject record", "url": "https://example.org/subject"},
            "appearance": {"id": "APP-SUBJECT", "locator": "object subject"},
            "identifiers": [{"scheme": "collection designation", "value": "B1"}],
            "claims": [{"field": "catalogue_description", "value_text": "Duplicate of B2"}],
        })
        source_id = self.conn.execute(
            "SELECT source_id FROM appearances WHERE id='APP-SUBJECT'"
        ).fetchone()[0]
        self.target = add_candidate(self.conn, {
            "object_id": "IBI-TARGET", "label": "Target bowl",
            "source": {"source_type": "museum_record", "title": "Museum target",
                       "citation": "Museum target record", "url": "https://example.org/target"},
            "appearance": {"locator": "object target"},
            "identifiers": [{"scheme": "collection designation", "value": "B2"}],
        })
        self.conn.commit()
        self.entry = {
            "assertion_id": "IBI-REL-TEST", "subject_object_id": self.subject,
            "target_object_id": self.target, "source_id": source_id,
            "appearance_id": "APP-SUBJECT", "relationship_type": "duplicate_of",
            "relationship_scope": "unclear", "target_identifier_scheme": "collection designation",
            "target_identifier_value": "B2", "raw_statement": "Duplicate of B2",
            "interpretation_status": "unresolved", "locator": "object subject",
            "rationale": "The museum reports a relation, but does not define its physical scope.",
        }
        self.entry["expected_evidence_sha256"] = relationship_evidence_sha256(
            self.conn, self.entry
        )
        self.manifest = {"schema_version": 1, "reviewed_by": "Test reviewer",
                         "reviewed_at": "2026-09-05T19:00:00Z",
                         "scope": "Test source relationship", "entries": [self.entry]}
        self.path = self.root / "relationships.json"

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def apply(self):
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return apply_relationship_review(self.conn, self.path)

    def test_replay_is_idempotent_and_does_not_merge(self):
        before = self.conn.execute("SELECT count(*) FROM dedupe_candidates").fetchone()[0]
        self.assertEqual(self.apply()["changed"], 1)
        self.assertEqual(self.apply()["changed"], 0)
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM dedupe_candidates").fetchone()[0], before
        )
        row = self.conn.execute("SELECT * FROM object_relationship_assertions").fetchone()
        self.assertEqual(row["relationship_scope"], "unclear")
        for sql in (
            "UPDATE object_relationship_assertions SET relationship_scope='physical_identity'",
            "DELETE FROM object_relationship_assertions",
        ):
            with self.assertRaises(sqlite3.IntegrityError):
                self.conn.execute(sql)
            self.conn.rollback()

    def test_changed_or_missing_evidence_is_rejected_atomically(self):
        second = copy.deepcopy(self.entry)
        second["assertion_id"] = "IBI-REL-SECOND"
        second["target_identifier_value"] = "MISSING"
        self.manifest["entries"].append(second)
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM object_relationship_assertions").fetchone()[0], 0
        )
        self.manifest["entries"] = [self.entry]
        self.entry["expected_evidence_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            self.apply()

    def test_requires_source_statement_and_utc_review(self):
        self.entry["raw_statement"] = "Not in source"
        with self.assertRaisesRegex(ValueError, "absent"):
            self.apply()
        self.entry["raw_statement"] = "Duplicate of B2"
        self.manifest["reviewed_at"] = "2026-09-05T19:00:00"
        with self.assertRaisesRegex(ValueError, "UTC"):
            self.apply()
