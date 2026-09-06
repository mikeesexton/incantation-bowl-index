"""Introduction totals and browse shortcuts must describe the same bowl identities."""
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bowl_index.db import connect, migrate
from bowl_index.dedupe import adjudicate_exact_identifiers, queue_all
from bowl_index.ingest import add_candidate
from bowl_index.web import CorpusCatalog, INTRO_COVERAGE, make_handler


class IntroductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.sqlite3"
        self.conn = connect(self.path)
        migrate(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def candidate(self, name, accession):
        return {
            "label": name,
            "source": {"source_type": "article", "title": name, "citation": name,
                       "url": "https://example.org/" + name, "issued_year": 1853},
            "appearance": {"locator": accession, "confidence": 1},
            "identifiers": [{"scheme": "accession", "value": accession,
                             "assigning_body": "Test Museum"}],
        }

    def populated_catalog(self):
        sparse = self.candidate("First appearance", "SAME-1")
        sparse["claims"] = [{"field": "findspot", "value_text": "Reported place"}]
        rich = self.candidate("Second appearance", "SAME-1")
        rich["texts"] = [{"text_type": "transcription", "content": "PRIVATE READING",
                          "rights_status": "copyrighted", "public_ok": False}]
        rich["media"] = [{"media_type": "image", "url": "https://example.org/private-photo.jpg",
                          "rights_status": "copyrighted"}]
        for record in (sparse, rich, self.candidate("Uncovered bowl", "OTHER-2")):
            add_candidate(self.conn, record)
        queue_all(self.conn, threshold=.9)
        adjudicate_exact_identifiers(self.conn)
        self.conn.commit()
        return CorpusCatalog(self.path)

    def test_counts_roll_up_members_and_overlapping_coverage(self):
        catalog = self.populated_catalog()
        intro = catalog.introduction()
        self.assertEqual(intro["source_record_count"], 3)
        self.assertEqual(intro["identity_count"], 2)
        self.assertEqual(intro["coverage"], dict.fromkeys(INTRO_COVERAGE, 1))
        ids = [row["identity_id"] for row in intro["identities"]]
        self.assertEqual(ids, sorted(set(ids)))
        for field in INTRO_COVERAGE:
            present = catalog.search({"present": [field]})
            missing = catalog.search({"coverage": [field]})
            expected = {row["identity_id"] for row in intro["identities"] if row[field]}
            self.assertEqual({row["identity_id"] for row in present["items"]}, expected)
            self.assertEqual(present["snapshot_id"], intro["snapshot"]["id"])
            self.assertEqual(present["total"] + missing["total"], intro["identity_count"])
        self.assertEqual(catalog.search({"present": ["image"], "coverage": ["image"]})["total"], 0)
        self.assertEqual(catalog.search({"present": ["image"], "q": ["Uncovered"]})["total"], 0)

    def test_edition_pointer_counts_without_stored_transcription(self):
        from bowl_index.publications import apply_publication_registry
        record = self.candidate("Referenced edition", "EDITION-1")
        record["identifiers"].append({"scheme": "publication object key", "value": "Example 1853::1"})
        add_candidate(self.conn, record)
        source_id = self.conn.execute("SELECT id FROM sources LIMIT 1").fetchone()[0]
        apply_publication_registry(self.conn, {
            "schema_version": 1, "reviewed_by": "Test", "reviewed_at": "2026-09-06T00:00:00Z",
            "entries": [{"registry_id": "IBI-PUBREG-TEST", "publication_key": "Example 1853",
                         "resolution": "resolved", "source_id": source_id,
                         "basis": "Exact test edition reference in fixture"}],
        })
        self.conn.commit()
        catalog = CorpusCatalog(self.path)
        self.assertEqual(catalog.introduction()["coverage"]["text_edition"], 1)
        self.assertEqual(catalog.search({"present": ["text_edition"]})["total"], 1)
        # The existing missing-transcription measure keeps its original semantics.
        self.assertEqual(catalog.search({"coverage": ["text_edition"]})["total"], 1)

    def test_presence_does_not_disclose_restricted_contents_or_urls(self):
        payload = json.dumps(self.populated_catalog().introduction())
        self.assertNotIn("PRIVATE READING", payload)
        self.assertNotIn("private-photo.jpg", payload)
        self.assertNotIn("Reported place", payload)

    def test_read_only_snapshot_stays_stable_until_refresh(self):
        catalog = self.populated_catalog()
        original = catalog.introduction()
        changes = self.conn.total_changes
        self.assertEqual(catalog.introduction(), original)
        self.assertEqual(self.conn.total_changes, changes)
        add_candidate(self.conn, self.candidate("Newly recorded", "THIRD-3"))
        self.conn.commit()
        self.assertEqual(catalog.introduction()["identity_count"], 2)
        self.assertEqual(catalog.search({})["total"], 2)
        catalog.refresh()
        self.assertEqual(catalog.introduction()["identity_count"], 3)
        self.assertNotEqual(catalog.introduction()["snapshot"]["id"], original["snapshot"]["id"])
        self.assertEqual(catalog.search({})["snapshot_id"], catalog.introduction()["snapshot"]["id"])

    def test_failed_refresh_keeps_last_coherent_snapshot(self):
        from unittest.mock import patch
        catalog = self.populated_catalog()
        original = catalog.introduction()
        add_candidate(self.conn, self.candidate("Later object", "LATER-9"))
        self.conn.commit()
        with patch("bowl_index.web.Projection.tables", side_effect=ValueError("Test failure")):
            with self.assertRaises(ValueError):
                catalog.refresh()
        self.assertEqual(catalog.introduction(), original)
        self.assertEqual(catalog.search({})["total"], original["identity_count"])
        self.assertEqual(catalog.stats()["identities"], original["identity_count"])

    def test_generic_scholarly_mention_is_not_a_text_edition(self):
        add_candidate(self.conn, self.candidate("Unclassified article", "MENTION-1"))
        self.conn.commit()
        catalog = CorpusCatalog(self.path)
        self.assertEqual(catalog.introduction()["coverage"]["text_edition"], 0)
        self.assertEqual(catalog.search({"present": ["text_edition"]})["total"], 0)

    def test_empty_corpus_has_zero_coverage(self):
        intro = CorpusCatalog(self.path).introduction()
        self.assertEqual(intro["identity_count"], 0)
        self.assertEqual(intro["identities"], [])
        self.assertEqual(intro["coverage"], dict.fromkeys(INTRO_COVERAGE, 0))

    def test_graph_counts_indexed_works_not_document_holdings(self):
        year = datetime.now(timezone.utc).year
        for name, issued in (("Old work", 1853), ("Current work", year), ("Undated work", None)):
            record = self.candidate(name, name)
            record["source"]["issued_year"] = issued
            add_candidate(self.conn, record)
        self.conn.commit()
        scholarship = CorpusCatalog(self.path).introduction()["scholarship"]
        rows = {row["decade"]: row for row in scholarship["decades"]}
        self.assertEqual(rows[1850]["indexed"], 1)
        self.assertFalse(rows[1850]["incomplete"])
        self.assertTrue(rows[year // 10 * 10]["incomplete"])
        self.assertEqual(scholarship["undated_count"], 1)
        self.assertEqual(sum(row["indexed"] for row in rows.values()), 2)

    def test_http_endpoint_and_post_rejection(self):
        catalog = self.populated_catalog()
        handler = make_handler(catalog, "test-token")
        class Socket:
            def __init__(self, request):
                self.input = io.BytesIO(request)
                self.output = io.BytesIO()
            def makefile(self, *args, **kwargs):
                return self.input
            def sendall(self, data):
                self.output.write(data)
        for method, status in (("GET", b"200 OK"), ("POST", b"404 Not Found")):
            sock = Socket(f"{method} /api/introduction HTTP/1.0\r\nHost: localhost\r\n\r\n".encode())
            handler(sock, ("127.0.0.1", 12345), None)
            headers, body = sock.output.getvalue().split(b"\r\n\r\n", 1)
            self.assertIn(status, headers)
            if method == "GET":
                self.assertEqual(json.loads(body), catalog.introduction())
                self.assertIn(b"Cache-Control: no-store", headers)


if __name__ == "__main__":
    unittest.main()
