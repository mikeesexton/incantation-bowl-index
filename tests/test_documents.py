import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.acquisitions import acquisition_rows
from bowl_index.archive import capture_file
from bowl_index.db import connect, migrate
from bowl_index.documents import (
    apply_document_assessments, current_assessments, document_metrics,
)


class DocumentAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / "db.sqlite3")
        migrate(self.conn)
        self.conn.execute(
            "INSERT INTO sources(id,source_type,title,citation) "
            "VALUES ('SRC-1','book','One volume','One volume')"
        )
        self.conn.commit()
        document = self.root / "book.pdf"
        document.write_bytes(b"%PDF-1.4 complete test volume")
        self.capture = capture_file(
            self.conn, document, source_id="SRC-1", archive_root=self.root / "archive"
        )
        self.evidence = self.root / "review.json"
        self.evidence.write_text('{"visual_check":"title and final page"}\n')
        self.extraction = self.root / "objects.jsonl"
        self.extraction.write_text('{"object":"1"}\n')

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def batch(self, **overrides):
        entry = {
            "id": "IBI-DOC-1",
            "source_id": "SRC-1",
            "capture_id": self.capture["id"],
            "document_form": "scan",
            "extent": "complete",
            "inspection": "digital",
            "text_state": "extractable",
            "object_extraction": "complete",
            "document_sha256": self.capture["sha256"],
            "extraction_path": self.extraction.name,
            "extraction_sha256": self.digest(self.extraction),
            "basis": "Title, contents, representative pages and terminal matter checked.",
            "evidence_path": self.evidence.name,
            "evidence_sha256": self.digest(self.evidence),
        }
        entry.update(overrides)
        return {
            "schema_version": 1,
            "reviewed_by": "Test reviewer",
            "reviewed_at": "2026-09-17T12:00:00+00:00",
            "entries": [entry],
        }

    def test_complete_capture_is_assessed_separately_from_its_format(self):
        result = apply_document_assessments(self.conn, self.batch(), self.root)
        self.assertEqual(result["changed"], 1)
        self.assertEqual(result["sources_with_complete_documents"], 1)
        self.assertEqual(result["sources_with_complete_object_level_extraction"], 1)
        row = acquisition_rows(self.conn)[0]
        self.assertEqual(row["capture_status"], "pdf_captured")
        self.assertEqual(row["document_completeness"], "complete")
        self.assertEqual(row["text_state"], "extractable")
        self.assertEqual(row["assessed_document_sha256"], self.capture["sha256"])

    def test_document_review_and_transformation_hashes_are_verified(self):
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn, self.batch(document_sha256="0" * 64), self.root)
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn, self.batch(evidence_sha256="0" * 64), self.root)
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn,
                self.batch(text_state="ocr", text_artifact_path=None,
                           text_artifact_sha256=None), self.root,
            )

    def test_replay_is_a_no_op_and_changed_evidence_is_rejected(self):
        self.assertEqual(apply_document_assessments(
            self.conn, self.batch(), self.root)["changed"], 1)
        self.assertEqual(apply_document_assessments(
            self.conn, self.batch(), self.root)["changed"], 0)
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn, self.batch(basis="A different claim"), self.root)

    def test_a_revision_explicitly_supersedes_without_deleting_history(self):
        first = self.batch(extent="excerpt", object_extraction="partial")
        apply_document_assessments(self.conn, first, self.root)
        second = self.batch(id="IBI-DOC-2", supersedes_id="IBI-DOC-1")
        apply_document_assessments(self.conn, second, self.root)
        self.assertEqual(len(current_assessments(self.conn)), 1)
        self.assertEqual(current_assessments(self.conn)[0]["id"], "IBI-DOC-2")
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM document_assessments").fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM document_assessments WHERE id='IBI-DOC-1'")
        self.conn.rollback()

    def test_citation_only_and_physical_work_are_distinct_valid_states(self):
        citation = self.batch(
            id="IBI-CITE-1", capture_id=None, document_form="no_document",
            extent="citation_only", inspection="not_inspected", text_state="none",
            object_extraction="none", document_sha256=None,
            extraction_path=None, extraction_sha256=None,
        )
        apply_document_assessments(self.conn, citation, self.root)
        self.assertEqual(document_metrics(self.conn)["sources_with_complete_documents"], 0)
        physical = self.batch(
            id="IBI-PHYS-1", capture_id=None, document_form="physical",
            extent="complete", inspection="physical", text_state="none",
            object_extraction="none", document_sha256=None,
            extraction_path=None, extraction_sha256=None,
            supersedes_id="IBI-CITE-1",
        )
        apply_document_assessments(self.conn, physical, self.root)
        metrics = document_metrics(self.conn)
        self.assertEqual(metrics["sources_with_physically_inspected_documents"], 1)
        self.assertEqual(metrics["sources_with_complete_documents"], 1)

    def test_extent_cannot_be_inferred_without_inspection(self):
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn, self.batch(inspection="not_inspected"), self.root)
        with self.assertRaises(ValueError):
            apply_document_assessments(
                self.conn, self.batch(evidence_path="../outside.json"), self.root)


if __name__ == "__main__":
    unittest.main()
