import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.export import export_all
from bowl_index.ingest import add_candidate
from bowl_index.proofreading import text_fingerprint
from bowl_index.text_metadata import apply_text_metadata, validate_text_classification


class TextMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / "test.db")
        migrate(self.conn)
        add_candidate(self.conn, {"label": "Bowl", "source": {"title": "Edition", "citation": "Test edition", "source_type": "book"},
                                 "appearance": {"locator": "p. 1"}, "texts": [{
                                     "text_type": "translation", "content": "Private payload",
                                     "locator": "p. 1", "public_ok": True}]})
        self.conn.commit()
        self.row = self.conn.execute("SELECT * FROM texts").fetchone()
        self.evidence = self.root / "evidence.md"
        self.evidence.write_text("Metadata audit, no quotation")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def manifest(self):
        return {"schema_version": 1, "reviewed_by": "Test", "reviewed_at": "2026-10-01T02:00:00Z",
                "evidence_path": "evidence.md", "evidence_sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
                "entries": [{"id": "TMC-1", "text_id": self.row["id"],
                             "expected_text_sha256": text_fingerprint(self.row),
                             "changes": {"text_type": "summary"}, "rationale": "Imported classification incorrect"}]}

    def test_repair_retains_private_original_and_replay_is_safe(self):
        manifest = self.manifest()
        self.assertEqual(apply_text_metadata(self.conn, manifest, self.root)["applied"], 1)
        after = self.conn.execute("SELECT * FROM texts").fetchone()
        self.assertEqual(after["content"], self.row["content"])
        self.assertEqual(after["public_ok"], 0)
        self.assertEqual(after["text_type"], "summary")
        history = self.conn.execute("SELECT * FROM text_metadata_corrections").fetchone()
        self.assertEqual(json.loads(history["before_json"]), dict(self.row))
        self.assertEqual(apply_text_metadata(self.conn, manifest, self.root)["unchanged"], 1)
        manifest["entries"][0]["rationale"] = "different evidence"
        with self.assertRaisesRegex(ValueError, "replay differs"):
            apply_text_metadata(self.conn, manifest, self.root)
        for sql in ["UPDATE text_metadata_corrections SET rationale='changed'", "DELETE FROM text_metadata_corrections"]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.conn.execute(sql)
            self.conn.rollback()
        export_all(self.conn, self.root / "export")
        exported = json.loads((self.root / "export/text_metadata_corrections.jsonl").read_text())
        self.assertIsNone(exported["before_json"])
        self.assertIsNone(exported["after_json"])
        self.assertNotIn("Private payload", (self.root / "export/text_metadata_corrections.csv").read_text())

    def test_stale_evidence_and_text_fail_closed(self):
        manifest = self.manifest()
        self.conn.execute("UPDATE texts SET content='later revision'")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "text evidence changed"):
            apply_text_metadata(self.conn, manifest, self.root)
        self.evidence.write_text("changed")
        with self.assertRaisesRegex(ValueError, "correction evidence changed"):
            apply_text_metadata(self.conn, manifest, self.root)

    def test_partial_batch_rolls_back_and_payload_changes_are_disallowed(self):
        manifest = self.manifest()
        manifest["entries"].append(dict(manifest["entries"][0], id="TMC-2"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            apply_text_metadata(self.conn, manifest, self.root)
        self.assertEqual(self.conn.execute("SELECT text_type FROM texts").fetchone()[0], "translation")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM text_metadata_corrections").fetchone()[0], 0)
        manifest = self.manifest()
        manifest["entries"][0]["changes"] = {"content": "manufactured translation"}
        with self.assertRaisesRegex(ValueError, "only text_type and locator"):
            apply_text_metadata(self.conn, manifest, self.root)

    def test_ingestion_rejects_declared_paraphrases_before_any_write(self):
        before = self.conn.execute("SELECT count(*) FROM objects").fetchone()[0]
        for editor in ["Discovery summary after Scholar", "Summary of Scholar", "Paraphrase of Scholar", "Dealer translation, summarized"]:
            with self.assertRaisesRegex(ValueError, "declared summary"):
                add_candidate(self.conn, {"source_id": self.row["source_id"], "appearance": {"locator": editor},
                                         "texts": [{"text_type": "translation", "editor": editor, "content": "x"}]})
        self.assertEqual(self.conn.execute("SELECT count(*) FROM objects").fetchone()[0], before)
        validate_text_classification({"text_type": "translation", "editor": "Scholar", "content": "This bowl is for ..."})
        validate_text_classification({"text_type": "summary", "editor": "Summary of Scholar", "content": "x"})

    def test_reimport_cannot_restore_an_old_locator(self):
        manifest = self.manifest()
        manifest["entries"][0]["changes"] = {"locator": "p. 2"}
        apply_text_metadata(self.conn, manifest, self.root)
        add_candidate(self.conn, {"source_id": self.row["source_id"], "appearance": {"locator": "p. 1"},
                                 "texts": [{"text_type": "translation", "content": "Private payload", "locator": "p. 1"}]})
        self.conn.commit()
        rows = list(self.conn.execute("SELECT locator FROM texts"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "p. 2")
