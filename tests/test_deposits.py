import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.db import migrate
from bowl_index.deposits import ingest_deposits
from bowl_index.ingest import SOURCE_FIELDS
from bowl_index.state import corpus_fingerprint


class LocalDepositTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.addCleanup(self.conn.close)
        migrate(self.conn)
        source = dict.fromkeys(SOURCE_FIELDS)
        source.update(id="SRC-DEPOSIT-TEST", source_type="article", title="Supplied edition",
                      citation="Test edition", access_status="available", rights_status="unknown")
        body = b"%PDF-test supplied bytes"
        (self.root / "edition.pdf").write_bytes(body)
        self.manifest = dict(schema_version=1, reviewed_by="Codex",
                             reviewed_at="2026-10-03T20:00:00+00:00", new_sources=[source],
                             entries=[dict(id="CAP-DEPOSIT-TEST", source_id=source["id"],
                                           path="edition.pdf", original_filename="edition.pdf",
                                           sha256=hashlib.sha256(body).hexdigest(), byte_length=len(body),
                                           mime_type="application/pdf", rights_status="unknown",
                                           note="Mike supplied this local file for private research.")])

    def test_reproducible_receipt_and_replay_preserve_original_file(self):
        result = ingest_deposits(self.conn, self.manifest, self.root)
        self.assertEqual((result["new_sources"], result["new_captures"], result["network_requests"]), (1, 1, 0))
        row = dict(self.conn.execute("SELECT * FROM captures").fetchone())
        self.assertEqual(row["retrieved_at"], self.manifest["reviewed_at"])
        self.assertIsNone(row["status_code"])
        self.assertEqual(row["url"], "local-deposit:edition.pdf")
        self.assertEqual((self.root / "data/private/archive" / row["storage_path"]).read_bytes(),
                         (self.root / "edition.pdf").read_bytes())
        headers = json.loads(row["headers_json"])
        self.assertIn("no robots or access-control decision", headers["retrieval"])
        before = corpus_fingerprint(self.conn)
        result = ingest_deposits(self.conn, self.manifest, self.root)
        self.assertEqual((result["new_sources"], result["new_captures"], result["unchanged_captures"]), (0, 0, 1))
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_changed_file_rejects_entire_batch(self):
        second = copy.deepcopy(self.manifest["entries"][0])
        second.update(id="CAP-SECOND", path="bad.pdf", original_filename="bad.pdf")
        (self.root / "bad.pdf").write_bytes(b"changed")
        self.manifest["entries"].append(second)
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sources").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM captures").fetchone()[0], 0)

    def test_existing_receipt_or_source_cannot_be_replaced(self):
        ingest_deposits(self.conn, self.manifest, self.root)
        before = corpus_fingerprint(self.conn)
        self.manifest["entries"][0]["note"] = "Different provenance"
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)
        self.manifest["entries"][0]["note"] = "Mike supplied this local file for private research."
        self.manifest["new_sources"][0]["title"] = "Different work"
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_archive_corruption_and_marker_collision_reject(self):
        ingest_deposits(self.conn, self.manifest, self.root)
        row = self.conn.execute("SELECT * FROM captures").fetchone()
        target = self.root / "data/private/archive" / row["storage_path"]
        target.write_bytes(b"corrupted")
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)
        target.write_bytes((self.root / "edition.pdf").read_bytes())
        self.manifest["entries"][0]["id"] = "CAP-DIFFERENT"
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)

    def test_constraint_failure_rolls_back_sources_and_captures(self):
        self.manifest["new_sources"][0]["source_type"] = "invalid-type"
        with self.assertRaises(sqlite3.IntegrityError):
            ingest_deposits(self.conn, self.manifest, self.root)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sources").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM captures").fetchone()[0], 0)

    def test_outside_project_and_duplicate_ids_reject(self):
        self.manifest["entries"][0]["path"] = "../edition.pdf"
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)
        self.manifest["entries"][0]["path"] = "edition.pdf"
        self.manifest["entries"].append(copy.deepcopy(self.manifest["entries"][0]))
        with self.assertRaises(ValueError):
            ingest_deposits(self.conn, self.manifest, self.root)

    def test_independent_rehearsal_has_identical_corpus(self):
        other = sqlite3.connect(":memory:")
        other.row_factory = sqlite3.Row
        self.addCleanup(other.close)
        migrate(other)
        ingest_deposits(self.conn, self.manifest, self.root)
        ingest_deposits(other, self.manifest, self.root)
        self.assertEqual(dict(self.conn.execute("SELECT * FROM captures").fetchone()),
                         dict(other.execute("SELECT * FROM captures").fetchone()))
        self.assertEqual(dict(self.conn.execute("SELECT * FROM sources").fetchone()),
                         dict(other.execute("SELECT * FROM sources").fetchone()))
