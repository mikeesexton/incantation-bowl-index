import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.export import export_all
from bowl_index.ingest import SOURCE_FIELDS, add_source
from bowl_index.source_corrections import apply_source_corrections


class SourceCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / "test.db")
        migrate(self.conn)
        add_source(self.conn, {
            "id": "SRC-OLD", "source_type": "article", "title": "A title",
            "authors": "Wrong Author", "issued_year": 2002, "citation": "Wrong citation",
            "url": "https://example.test/metadata", "access_status": "partial",
            "rights_status": "copyrighted",
        })
        add_source(self.conn, {
            "id": "SRC-RIGHT", "source_type": "article", "title": "A title",
            "authors": "Right Author", "issued_year": 2002, "citation": "Right citation",
            "url": "https://example.test/article",
        })
        self.conn.commit()
        self.evidence = self.root / "evidence.json"
        self.evidence.write_text('{"finding":"checked"}')

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def manifest(self):
        row = self.conn.execute("SELECT * FROM sources WHERE id='SRC-OLD'").fetchone()
        before = {field: row[field] for field in SOURCE_FIELDS}
        after = dict(before, source_type="repository", authors="Metadata Author",
                     citation="Metadata record", rights_status="unknown")
        return {
            "schema_version": 1,
            "reviewed_by": "Test reviewer",
            "reviewed_at": "2026-09-06T14:00:00Z",
            "evidence_path": "evidence.json",
            "evidence_sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
            "entries": [{
                "id": "IBI-SOURCE-CORR-TEST", "source_id": "SRC-OLD",
                "replacement_source_id": "SRC-RIGHT", "before": before, "after": after,
                "rationale": "The old row describes discovery metadata, not the article.",
            }],
        }

    def test_audited_repair_replay_and_immutable_history(self):
        manifest = self.manifest()
        self.assertEqual(apply_source_corrections(self.conn, manifest, self.root)["applied"], 1)
        self.assertEqual(apply_source_corrections(self.conn, manifest, self.root)["unchanged"], 1)
        history = self.conn.execute("SELECT * FROM source_corrections").fetchone()
        self.assertEqual(json.loads(history["before_json"]), manifest["entries"][0]["before"])
        self.assertEqual(json.loads(history["after_json"]), manifest["entries"][0]["after"])
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE source_corrections SET rationale='changed'")
        self.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM source_corrections")
        self.conn.rollback()
        export = export_all(self.conn, self.root / "export")
        self.assertEqual(export["tables"]["source_corrections"]["rows"], 1)

    def test_stale_source_and_evidence_are_rejected(self):
        manifest = self.manifest()
        self.conn.execute("UPDATE sources SET notes='later edit' WHERE id='SRC-OLD'")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "source evidence changed"):
            apply_source_corrections(self.conn, manifest, self.root)
        self.evidence.write_text("{}")
        with self.assertRaisesRegex(ValueError, "correction evidence changed"):
            apply_source_corrections(self.conn, manifest, self.root)

    def test_batch_failure_rolls_back_first_repair(self):
        manifest = self.manifest()
        manifest["entries"].append(dict(manifest["entries"][0], id="IBI-SOURCE-CORR-2"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            apply_source_corrections(self.conn, manifest, self.root)
        row = self.conn.execute("SELECT authors FROM sources WHERE id='SRC-OLD'").fetchone()
        self.assertEqual(row["authors"], "Wrong Author")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM source_corrections").fetchone()[0], 0)

    def test_manifest_requires_complete_stable_states_and_replacement(self):
        manifest = self.manifest()
        del manifest["entries"][0]["after"]["notes"]
        with self.assertRaisesRegex(ValueError, "every stable source field"):
            apply_source_corrections(self.conn, manifest, self.root)
        manifest = self.manifest()
        manifest["entries"][0]["replacement_source_id"] = "SRC-MISSING"
        with self.assertRaisesRegex(ValueError, "replacement source missing"):
            apply_source_corrections(self.conn, manifest, self.root)
