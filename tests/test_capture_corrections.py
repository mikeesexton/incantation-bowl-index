import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.acquisitions import acquisition_rows
from bowl_index.capture_corrections import apply_capture_source_corrections
from bowl_index.db import connect, migrate
from bowl_index.export import export_all
from bowl_index.ingest import add_source
from bowl_index.private_projection import PrivateResearchProjection


class CaptureCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / "test.db")
        migrate(self.conn)
        for source_id, title in [("SRC-BOOK", "The later book"), ("SRC-THESIS", "The actual thesis")]:
            add_source(self.conn, {"id": source_id, "source_type": "book", "title": title, "citation": title})
        self.conn.execute(
            "INSERT INTO captures(id,source_id,url,retrieved_at,mime_type,sha256,byte_length,storage_path,rights_status) "
            "VALUES ('CAP-TEST','SRC-BOOK','https://example.test/thesis.pdf','2026-10-01T00:00:00Z',"
            "'application/pdf',?,10,'sha256/test','copyrighted')", ("a" * 64,))
        self.conn.commit()
        self.original = dict(self.conn.execute("SELECT * FROM captures").fetchone())
        (self.root / "evidence.json").write_text('{"finding":"title page identifies thesis"}')

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def manifest(self):
        return {"schema_version": 1, "reviewed_by": "Test reviewer", "reviewed_at": "2026-10-01T00:00:00Z",
                "evidence_path": "evidence.json",
                "evidence_sha256": hashlib.sha256((self.root / "evidence.json").read_bytes()).hexdigest(),
                "entries": [{"id": "CORR-TEST", "capture_id": "CAP-TEST", "after_source_id": "SRC-THESIS",
                             "before": self.original, "rationale": "Actual title page differs from book citation."}]}

    def test_repair_changes_acquisition_and_reader_links_preserving_retrieval(self):
        manifest = self.manifest()
        self.assertEqual(apply_capture_source_corrections(self.conn, manifest, self.root)["applied"], 1)
        self.assertEqual(dict(self.conn.execute("SELECT * FROM captures").fetchone()),
                         dict(self.original, source_id="SRC-THESIS"))
        holdings = {r["id"]: r for r in acquisition_rows(self.conn)}
        self.assertEqual(holdings["SRC-BOOK"]["pdf_count"], 0)
        self.assertEqual(holdings["SRC-THESIS"]["pdf_count"], 1)
        reader = PrivateResearchProjection(self.conn, capture_base="/api/private-captures/")
        self.assertNotIn("SRC-BOOK", reader.capture_links)
        self.assertEqual(reader.capture_links["SRC-THESIS"], "/api/private-captures/CAP-TEST")
        self.assertEqual(apply_capture_source_corrections(self.conn, manifest, self.root)["unchanged"], 1)
        history = self.conn.execute("SELECT * FROM capture_source_corrections").fetchone()
        self.assertEqual(json.loads(history["before_json"]), self.original)
        for statement in ["UPDATE capture_source_corrections SET rationale='changed'", "DELETE FROM capture_source_corrections"]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.conn.execute(statement)
            self.conn.rollback()
        self.assertEqual(export_all(self.conn, self.root / "export")["tables"]["capture_source_corrections"]["rows"], 1)

    def test_stale_retrieval_and_changed_evidence_rejected(self):
        manifest = self.manifest()
        self.conn.execute("UPDATE captures SET byte_length=11")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "capture evidence changed"):
            apply_capture_source_corrections(self.conn, manifest, self.root)
        (self.root / "evidence.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            apply_capture_source_corrections(self.conn, manifest, self.root)

    def test_invalid_second_entry_rolls_back_entire_batch(self):
        manifest = self.manifest()
        manifest["entries"].append(dict(manifest["entries"][0], id="CORR-SECOND"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            apply_capture_source_corrections(self.conn, manifest, self.root)
        self.assertEqual(dict(self.conn.execute("SELECT * FROM captures").fetchone()), self.original)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM capture_source_corrections").fetchone()[0], 0)

    def test_assessed_capture_and_unsafe_evidence_paths_rejected(self):
        manifest = self.manifest()
        manifest["evidence_path"] = "../evidence.json"
        with self.assertRaisesRegex(ValueError, "inside the project"):
            apply_capture_source_corrections(self.conn, manifest, self.root)
        self.conn.execute(
            "INSERT INTO document_assessments(id,source_id,capture_id,document_form,extent,inspection,text_state,"
            "object_extraction,basis,evidence_path,evidence_sha256,assessed_by,assessed_at) VALUES "
            "('DOC-TEST','SRC-BOOK','CAP-TEST','scan','front_matter','digital','none','none',"
            "'Title checked','evidence.json',?,'Test reviewer','2026-10-01T00:00:00Z')", ("b" * 64,))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "document-ledger repair"):
            apply_capture_source_corrections(self.conn, self.manifest(), self.root)
