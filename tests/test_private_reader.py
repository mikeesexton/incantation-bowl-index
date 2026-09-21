import tempfile
import unittest
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.private_projection import PrivateResearchProjection, private_manifest
from bowl_index.projection import PROJECTION_COLUMNS, Projection
from bowl_index.web import CorpusCatalog


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
        self.assertEqual(tables["media"][0]["url"], "https://example.org/private-bowl.jpg")
        self.assertIn("no public reuse permission", tables["media"][0]["rights_statement"])
        fact = next(row for row in tables["facts"] if row["field"] == "text_feature")
        self.assertEqual(fact["recorded_value"], fact["value"])
        self.assertEqual(fact["release_class"], "review_source_wording")
        for name, rows in tables.items():
            for row in rows:
                self.assertEqual(set(row), set(PROJECTION_COLUMNS[name]))

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


if __name__ == "__main__":
    unittest.main()
