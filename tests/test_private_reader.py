import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.private_projection import PrivateResearchProjection, private_manifest
from bowl_index.projection import PROJECTION_COLUMNS, Projection
from bowl_index.web import CorpusCatalog, make_handler


class PrivateReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.sqlite3"
        self.conn = connect(self.path)
        migrate(self.conn)
        add_candidate(self.conn, {
            "label": "Private research bowl",
            "source": {
                "source_type": "catalogue",
                "title": "Test catalogue",
                "citation": "Test catalogue 2026",
                "url": "https://example.org/object",
                "rights_status": "copyrighted",
            },
            "appearance": {"locator": "no. 1", "confidence": 1},
            "claims": [{
                "field": "text_feature",
                "value_text": (
                    "The editor supplies a long and distinctive description of the text "
                    "whose exact source wording remains useful in a private research bank."
                ),
            }],
            "texts": [{
                "text_type": "translation",
                "language": "English",
                "content": "THE COMPLETE PRIVATE TRANSLATION",
                "rights_status": "copyrighted",
                "locator": "p. 10",
            }],
            "media": [{
                "media_type": "image",
                "url": "https://example.org/private-bowl.jpg",
                "rights_status": "copyrighted",
            }],
        })
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_release_projection_still_withholds_private_material(self):
        release = Projection(self.conn).tables()
        self.assertIsNone(release["texts"][0]["content"])
        self.assertEqual(release["media"], [])
        self.assertNotIn("text_feature", {row["field"] for row in release["facts"]})

    def test_private_projection_exposes_everything_held_with_explicit_status(self):
        projection = PrivateResearchProjection(self.conn)
        tables = projection.tables()
        text = tables["texts"][0]
        self.assertEqual(text["content"], "THE COMPLETE PRIVATE TRANSLATION")
        self.assertEqual(text["content_status"], "private_research")
        self.assertEqual(text["editorial_status"], "not_checked")
        self.assertEqual(tables["media"][0]["url"], "https://example.org/private-bowl.jpg")
        self.assertIn("no public reuse permission", tables["media"][0]["rights_statement"])
        fact = next(row for row in tables["facts"] if row["field"] == "text_feature")
        self.assertEqual(fact["recorded_value"], fact["value"])
        self.assertEqual(fact["release_class"], "review_source_wording")
        for name, rows in tables.items():
            for row in rows:
                self.assertEqual(set(row), set(PROJECTION_COLUMNS[name]))

    def test_private_reader_distinguishes_partial_proofreading_from_public_approval(self):
        text_id = self.conn.execute("SELECT id FROM texts").fetchone()[0]
        with patch("bowl_index.private_projection.current_text_reviews",
                   return_value={text_id: {"status": "partial_review"}}):
            text = PrivateResearchProjection(self.conn).table("texts")[0]
        self.assertEqual(text["editorial_status"], "partial_review")
        self.assertEqual(text["content_status"], "private_research")
        release = Projection(self.conn).table("texts")[0]
        self.assertIsNone(release["content"])
        self.assertIsNone(release["editorial_status"])

    def test_private_manifest_and_local_catalog_report_the_private_tier(self):
        projection = PrivateResearchProjection(self.conn)
        tables = projection.tables()
        manifest = private_manifest(projection, tables, "2026-09-20T00:00:00Z")
        self.assertEqual(manifest["access_tier"], "private_research")
        self.assertEqual(manifest["texts_private_rows"], 1)
        self.assertEqual(manifest["media_private_rows"], 1)
        catalog = CorpusCatalog(self.path)
        self.assertEqual(catalog.reader_manifest()["access_tier"], "private_research")
        self.assertEqual(catalog.reader_table("texts", {})["rows"][0]["content"],
                         "THE COMPLETE PRIVATE TRANSLATION")
        self.assertEqual(catalog.search({"available": ["text_here"]})["total"], 1)
        self.assertEqual(catalog.search({"available": ["image_here"]})["total"], 1)

    def test_private_projection_prefers_a_reviewed_local_derivative(self):
        media_id = self.conn.execute("SELECT id FROM media").fetchone()[0]
        media_root = Path(self.temp.name) / "media"
        media_root.mkdir()
        (media_root / f"{media_id}.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
        projection = PrivateResearchProjection(self.conn, media_root=media_root)
        tables = projection.tables()
        self.assertEqual(tables["media"][0]["url"],
                         f"/api/private-media/{media_id}.png")
        self.assertEqual(projection.gate_counts(tables["texts"])["media_local_derivative_rows"], 1)

    def test_native_edition_facsimile_is_distinguished_privately_without_release(self):
        source_id = self.conn.execute("SELECT id FROM sources").fetchone()[0]
        add_candidate(self.conn, {"source_id": source_id, "appearance": {"locator": "no. 1"},
            "media": [{"media_type": "scan", "url": "https://example.org/native-edition.png",
                       "rights_status": "copyrighted",
                       "notes": "Original-script edition facsimile; no. 1, PDF p. 10."}]})
        self.conn.commit()
        private = PrivateResearchProjection(self.conn).table("media")
        native = next(row for row in private if row["url"].endswith("native-edition.png"))
        self.assertEqual(native["media_type"], "inscription_facsimile")
        self.assertEqual(native["attribution"], "no. 1, PDF p. 10.")
        self.assertEqual(Projection(self.conn).table("media"), [])

    def test_standardized_nli_dimensions_retain_the_original_source_label(self):
        source_id = self.conn.execute("SELECT id FROM sources").fetchone()[0]
        original = "Height 72 mm; source field ‘הקף’ 164 mm"
        add_candidate(self.conn, {"source_id": source_id, "appearance": {"locator": "no. 1"},
                                 "claims": [{"field": "dimensions", "value_text": original}]})
        self.conn.commit()
        row = next(row for row in PrivateResearchProjection(self.conn).table("facts")
                   if row["field"] == "dimensions")
        self.assertEqual(row["recorded_value"], original)
        self.assertEqual(row["value"], "Height 7.2 cm · Catalogue circumference 16.4 cm (measurement convention unverified)")
        self.assertEqual(self.conn.execute("SELECT value_text FROM claims WHERE field='dimensions'").fetchone()[0], original)

    def test_local_reader_links_registered_capture_without_exposing_its_path(self):
        source_id = self.conn.execute("SELECT id FROM sources").fetchone()[0]
        archive = Path(self.temp.name) / "archive"
        (archive / "sha256").mkdir(parents=True)
        capture = archive / "sha256" / "document.pdf"
        capture.write_bytes(b"%PDF-1.4\nprivate fixture")
        self.conn.execute(
            "INSERT INTO captures (id,source_id,url,retrieved_at,storage_path,mime_type,"
            "sha256,byte_length,rights_status) VALUES (?,?,?,?,?,?,?,?,?)",
            ("CAP-ABCDEF123456", source_id, "https://example.org/private-document.pdf",
             "2026-09-28T00:00:00Z", "sha256/document.pdf", "application/pdf",
             "0" * 64, capture.stat().st_size, "copyrighted"),
        )
        self.conn.commit()
        with patch("bowl_index.web.PRIVATE_ARCHIVE_ROOT", archive):
            catalog = CorpusCatalog(self.path)
            text = catalog.reader_table("texts", {})["rows"][0]
            self.assertEqual(text["access_url"], "/api/private-captures/CAP-ABCDEF123456")
            self.assertEqual(catalog.private_capture("CAP-ABCDEF123456"),
                             (capture.resolve(), "application/pdf"))
            self.assertEqual(catalog.reader_manifest()["source_captures_url"],
                             "/api/private-captures")
            self.assertEqual(catalog.private_capture_rows[0]["url"],
                             "/api/private-captures/CAP-ABCDEF123456")
            self.assertIsNone(catalog.private_capture("../../document.pdf"))
            self.assertNotIn(str(archive), str(catalog.reader_manifest()))

            class Socket:
                def __init__(self):
                    self.input = io.BytesIO(
                        b"GET /api/private-captures/CAP-ABCDEF123456 HTTP/1.0\r\n"
                        b"Host: localhost\r\n\r\n"
                    )
                    self.output = io.BytesIO()
                def makefile(self, *args, **kwargs):
                    return self.input
                def sendall(self, data):
                    self.output.write(data)

            sock = Socket()
            make_handler(catalog, "test-token")(sock, ("127.0.0.1", 12345), None)
            headers, body = sock.output.getvalue().split(b"\r\n\r\n", 1)
            self.assertIn(b"200 OK", headers)
            self.assertIn(b"Cache-Control: no-store", headers)
            self.assertEqual(body, capture.read_bytes())

            index_socket = Socket()
            index_socket.input = io.BytesIO(
                b"GET /api/private-captures HTTP/1.0\r\nHost: localhost\r\n\r\n"
            )
            make_handler(catalog, "test-token")(
                index_socket, ("127.0.0.1", 12345), None
            )
            index_headers, index_body = index_socket.output.getvalue().split(b"\r\n\r\n", 1)
            self.assertIn(b"200 OK", index_headers)
            self.assertEqual(json.loads(index_body)["rows"][0]["id"], "CAP-ABCDEF123456")


if __name__ == "__main__":
    unittest.main()
