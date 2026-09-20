import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from bowl_index.accuracy_audit import (
    _current_snapshot, _selection_evidence_digest, apply_accuracy_audit,
)
from bowl_index.db import connect, migrate
from bowl_index.identity import identity_rows
from bowl_index.ingest import add_candidate


class AccuracyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / "test.sqlite3")
        migrate(self.conn)
        self.object_id = add_candidate(self.conn, {
            "label": "Audit bowl",
            "source": {
                "source_type": "museum_record", "title": "Audit museum record",
                "citation": "Audit Museum, A1", "url": "https://example.org/A1",
            },
            "appearance": {"locator": "A1", "confidence": 1.0},
            "identifiers": [
                {"scheme": "accession", "value": "A1", "assigning_body": "Audit Museum"}
            ],
            "claims": [{"field": "material", "value_text": "ceramic"}],
        })
        self.conn.commit()
        identity = identity_rows(self.conn)[0]
        selected = {
            "identity_id": identity["identity_id"],
            "canonical_object_id": identity["canonical_object_id"],
            "member_ids": json.loads(identity["member_ids_json"]),
            "record_status": identity["record_status"],
            "linkage_method": "singleton",
            "source_family": "museum",
            "source_ids": [row[0] for row in self.conn.execute("SELECT id FROM sources")],
            "identifiers": json.loads(identity["identifiers_json"]),
            "stratum": "candidate|singleton|museum",
        }
        selected["evidence_sha256"] = _selection_evidence_digest(self.conn, selected)
        self.selected = selected
        selection = {
            "schema_version": 1, "audit_id": "QA003-TEST",
            "representative": [selected], "high_risk": [],
        }
        self.selection_path = self.root / "selection.json"
        self.selection_path.write_text(
            json.dumps(selection, sort_keys=True) + "\n", encoding="utf-8"
        )

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def review(self, **overrides):
        entry = {
            "sample_role": "representative",
            "identity_id": self.selected["identity_id"],
            "selection_evidence_sha256": self.selected["evidence_sha256"],
            "outcome": "verified",
            "citation_check": "verified",
            "identifier_check": "verified",
            "identity_check": "not_applicable",
            "claim_check": "verified",
            "error_categories": [],
            "evidence": ["Audit Museum record A1"],
            "notes": "Checked against the source fixture.",
        }
        entry.update(overrides)
        review = {
            "schema_version": 1,
            "audit_id": "QA003-TEST",
            "selection_manifest": "selection.json",
            "selection_manifest_sha256": hashlib.sha256(
                self.selection_path.read_bytes()
            ).hexdigest(),
            "reviewed_by": "test reviewer",
            "reviewed_at": "2026-09-20T04:00:00+00:00",
            "entries": [entry],
        }
        path = self.root / "review.json"
        path.write_text(json.dumps(review), encoding="utf-8")
        return path

    def test_apply_replay_and_append_only_supersession(self):
        path = self.review()
        self.assertEqual(apply_accuracy_audit(self.conn, path, self.root)["changed"], 1)
        self.assertEqual(apply_accuracy_audit(self.conn, path, self.root)["changed"], 0)
        path = self.review(
            outcome="verified_with_notes", identifier_check="not_reverifiable",
            notes="Citation checked; identifier was not exposed by the fixture.",
        )
        self.assertEqual(apply_accuracy_audit(self.conn, path, self.root)["changed"], 1)
        rows = list(self.conn.execute("SELECT * FROM accuracy_audit_reviews ORDER BY rowid"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["supersedes_id"], rows[0]["id"])
        with self.assertRaises(Exception):
            self.conn.execute("DELETE FROM accuracy_audit_reviews")

    def test_rejects_stale_selection_and_inconsistent_error(self):
        current = _current_snapshot(self.conn, self.selected)
        self.assertEqual(
            _selection_evidence_digest(self.conn, current), self.selected["evidence_sha256"]
        )
        self.conn.execute(
            "INSERT INTO identifiers (id,object_id,source_id,scheme,value,normalized_value,confidence) "
            "SELECT 'IDN-NEW', ?, id, 'accession', 'A2', 'a2', 1.0 FROM sources LIMIT 1",
            (self.object_id,),
        )
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            apply_accuracy_audit(self.conn, self.review(), self.root)

        self.conn.execute("DELETE FROM identifiers WHERE id='IDN-NEW'")
        self.conn.execute("UPDATE claims SET value_text='glass' WHERE object_id=?", (self.object_id,))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            apply_accuracy_audit(self.conn, self.review(), self.root)

        self.conn.execute("UPDATE claims SET value_text='ceramic' WHERE object_id=?", (self.object_id,))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "Error outcome"):
            apply_accuracy_audit(
                self.conn,
                self.review(outcome="error", error_categories=["identifier"]),
                self.root,
            )


if __name__ == "__main__":
    unittest.main()
