import hashlib
import json
import tempfile
import unicodedata
import unittest
from pathlib import Path

from bowl_index.archive import capture_file
from bowl_index.db import connect, migrate
from bowl_index.vault import validate_rich_text_package


class PrivateRichTextPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / "db.sqlite3")
        migrate(self.conn)
        self.conn.execute(
            "INSERT INTO sources(id,source_type,title,citation) "
            "VALUES ('SRC-1','book','Private edition','Private edition')"
        )
        self.conn.commit()
        document = self.root / "edition.pdf"
        document.write_bytes(b"%PDF-1.4 private test edition")
        self.capture = capture_file(
            self.conn, document, source_id="SRC-1", archive_root=self.root / "archive"
        )
        self.package = self.root / "rich_text" / "IBI-RICH-1"
        self.package.mkdir(parents=True)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_package(self, xml=None, **manifest_overrides):
        xml = xml or (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader><fileDesc><titleStmt><title>Private pilot</title></titleStmt>'
            '<publicationStmt><p>Private research only.</p></publicationStmt>'
            '<sourceDesc><p>Bound to the capture ledger.</p></sourceDesc></fileDesc>'
            '<encodingDesc><p>IBI private rich-text profile version 1.</p></encodingDesc>'
            '</teiHeader><text><body>'
            '<pb n="1" facs="capture:%s#page=7"/>'
            '<p><unclear>ܐ</unclear> <supplied reason="lost">א</supplied></p>'
            '<pb n="2" facs="capture:%s#page=8"/>'
            '</body></text></TEI>\n' % (self.capture["id"], self.capture["id"])
        )
        text = self.package / "text.tei.xml"
        text.write_text(xml, encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "package_id": "IBI-RICH-1",
            "source_id": "SRC-1",
            "capture_id": self.capture["id"],
            "document_sha256": self.capture["sha256"],
            "text_path": "text.tei.xml",
            "text_sha256": self.digest(text),
            "access": {
                "layer": "private_research_vault",
                "public_release": False,
                "rights_status": "copyrighted",
                "lawful_acquisition_basis": "Researcher-supplied copy, 2026-09-18.",
                "copying_restrictions": "Personal research only.",
                "download_restrictions": "No redistribution.",
            },
            "transformation": {
                "state": "corrected_rich_text",
                "created_at": "2026-09-18T20:00:00Z",
                "created_by": "Test reviewer",
                "method": "OCR followed by page-image correction.",
            },
        }
        manifest.update(manifest_overrides)
        (self.package / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return manifest

    def test_valid_private_tei_package_is_hash_and_capture_bound(self):
        self.write_package()
        result = validate_rich_text_package(self.conn, self.package)
        self.assertTrue(result["valid"])
        self.assertEqual(result["page_anchors"], 2)
        self.assertEqual(result["first_image_page"], 7)
        self.assertEqual(result["last_image_page"], 8)
        self.assertFalse(result["public_release"])
        self.assertNotIn("content", result)

    def test_public_or_underspecified_access_is_rejected(self):
        manifest = self.write_package()
        manifest["access"]["public_release"] = True
        (self.package / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "public_release=false"):
            validate_rich_text_package(self.conn, self.package)
        manifest["access"]["public_release"] = False
        manifest["access"]["copying_restrictions"] = ""
        (self.package / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "copying_restrictions"):
            validate_rich_text_package(self.conn, self.package)

    def test_changed_text_or_capture_binding_is_rejected(self):
        manifest = self.write_package()
        (self.package / "text.tei.xml").write_text("<changed/>")
        with self.assertRaisesRegex(ValueError, "hash"):
            validate_rich_text_package(self.conn, self.package)
        self.write_package(document_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "capture ledger"):
            validate_rich_text_package(self.conn, self.package)

    def test_page_anchors_must_link_in_order_to_the_bound_capture(self):
        xml = (
            '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
            '<text><body><pb n="1" facs="capture:CAP-WRONG#page=1"/>'
            '</body></text></TEI>'
        )
        self.write_package(xml=xml)
        with self.assertRaisesRegex(ValueError, "pb@facs"):
            validate_rich_text_package(self.conn, self.package)
        xml = (
            '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
            '<text><body><pb n="2" facs="capture:%s#page=8"/>'
            '<pb n="1" facs="capture:%s#page=7"/></body></text></TEI>'
            % (self.capture["id"], self.capture["id"])
        )
        self.write_package(xml=xml)
        with self.assertRaisesRegex(ValueError, "unique and increasing"):
            validate_rich_text_package(self.conn, self.package)

    def test_non_normalized_unicode_and_path_escape_are_rejected(self):
        decomposed = unicodedata.normalize("NFD", "é")
        xml = (
            '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
            '<text><body><pb n="1" facs="capture:%s#page=1"/><p>%s</p>'
            '</body></text></TEI>' % (self.capture["id"], decomposed)
        )
        self.write_package(xml=xml)
        with self.assertRaisesRegex(ValueError, "NFC"):
            validate_rich_text_package(self.conn, self.package)
        self.write_package(text_path="../text.tei.xml")
        with self.assertRaisesRegex(ValueError, "inside the package"):
            validate_rich_text_package(self.conn, self.package)


if __name__ == "__main__":
    unittest.main()
