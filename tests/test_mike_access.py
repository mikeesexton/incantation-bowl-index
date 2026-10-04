"""Mike Access is complete private research, never a shared release."""

import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_mike_access as build  # noqa: E402


class MikeAccessBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_mike_access.py")],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )

    def test_build_stays_outside_deployment_tree(self):
        self.assertFalse(str(build.OUT).startswith(str(ROOT / "site" / "public")))

    def test_complete_private_projection_is_present(self):
        texts = json.loads((build.OUT / "data" / "texts.json").read_text(encoding="utf-8"))
        media = json.loads((build.OUT / "data" / "media.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (build.OUT / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["access_tier"], "private_research")
        self.assertEqual(manifest["texts_withheld_rows"], 0)
        self.assertEqual(manifest["media_withheld_rows"], 0)
        self.assertTrue(all(row["content"] is not None for row in texts["rows"]))
        self.assertEqual(len(media["rows"]), manifest["media_available_rows"])

    def test_barakat_private_texts_and_images_are_included(self):
        texts = json.loads((build.OUT / "data" / "texts.json").read_text(encoding="utf-8"))["rows"]
        media = json.loads((build.OUT / "data" / "media.json").read_text(encoding="utf-8"))["rows"]
        objects = {"IBI-42276229F0AD", "IBI-49CEAC0103D2", "IBI-9078953DB2E7"}
        private_translations = [row for row in texts
                                if row["object_id"] in objects and row["text_type"] == "translation"]
        barakat_media = [row for row in media if row["object_id"] in objects]
        # Research adds editions and contextual scans. Check the complete
        # current corpus rather than freezing an earlier intake's row counts.
        with sqlite3.connect(build.DEFAULT_DB.as_uri() + "?mode=ro", uri=True) as conn:
            expected_translations = {
                row[0] for row in conn.execute(
                    "SELECT id,object_id FROM texts WHERE text_type='translation'")
                if row[1] in objects
            }
            expected_media = {
                row[0] for row in conn.execute("SELECT id,object_id FROM media")
                if row[1] in objects
            }
        self.assertEqual({row["id"] for row in private_translations}, expected_translations)
        self.assertGreaterEqual(len(private_translations), 3)
        summary = next(row for row in texts if row["id"] == "TXT-C4E64CF6D96B")
        self.assertEqual(summary["text_type"], "summary")
        self.assertTrue(summary["content"])
        self.assertEqual(summary["content_status"], "private_research")
        self.assertTrue(all(row["content"] for row in private_translations))
        self.assertEqual({row["id"] for row in barakat_media}, expected_media)
        self.assertGreaterEqual(len(barakat_media), 5)
        self.assertTrue(all(row["url"] for row in barakat_media))

    def test_market_ledger_is_private_and_linked(self):
        page = (build.OUT / "market.html").read_text(encoding="utf-8")
        ledger = json.loads((build.OUT / "data" / "market.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["audience"], "Mike alone")
        self.assertIn("noindex, nofollow", page)
        self.assertIn("does not establish lawful ownership", " ".join(page.split()))
        self.assertEqual(page.count("<tr><td"), ledger["metrics"]["listings"])
        self.assertIn('href="market.html"',
                      (build.OUT / "index.html").read_text(encoding="utf-8"))

    def test_snapshot_audit_passes(self):
        snapshot = json.loads(
            (build.OUT / "private-snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["access"]["audience"], "Mike alone")
        self.assertTrue(all(check["passed"] for check in snapshot["audit_checks"]))

    def test_all_registered_contexts_are_private_and_separate_from_bowls(self):
        registry=json.loads((ROOT/'data/private/reader/source_contexts.json').read_text())
        rows=json.loads((build.OUT/'data/source_contexts.json').read_text())["rows"]
        self.assertEqual({r['id']for r in rows},{r['id']for r in registry['entries']})
        texts=json.loads((build.OUT/'data/texts.json').read_text())["rows"]
        self.assertFalse({r['id']for r in rows}&{r['id']for r in texts})
        for row in rows:
            entry=next(x for x in registry['entries']if x['id']==row['id'])
            self.assertEqual(row['content'],(ROOT/entry['artifact']['path']).read_text().removesuffix('\n'))
            self.assertEqual(row['notes'],entry['notes'])
            self.assertNotIn('artifact',row)
        shell=(build.OUT/'index.html').read_text()
        self.assertIn('href="#/contexts"',shell)

    def test_registered_nonnumeric_capture_ids_resolve_and_paths_cannot_escape(self):
        from bowl_index.web import CorpusCatalog
        catalog=CorpusCatalog(build.DEFAULT_DB)
        captures=json.loads((build.OUT/'data/captures.json').read_text())["rows"]
        for row in captures:
            self.assertIsNotNone(catalog.private_capture(row['id']))
        self.assertIsNone(catalog.private_capture('../CAP-IBI-CP107-FORD2002'))
        self.assertIsNone(catalog.private_capture('CAP-unknown'))

    def test_every_recorded_source_capture_is_packaged(self):
        snapshot = json.loads((build.OUT / "private-snapshot.json").read_text(encoding="utf-8"))
        manifest = json.loads((build.OUT / "data" / "manifest.json").read_text(encoding="utf-8"))
        captures = json.loads((build.OUT / "data" / "captures.json").read_text(encoding="utf-8"))["rows"]
        self.assertEqual(len(captures), snapshot["access"]["source_captures_held"])
        self.assertEqual(snapshot["access"]["source_captures_packaged"], len(captures))
        self.assertEqual(manifest["source_captures_url"], "./data/captures.json")
        self.assertTrue(all((build.OUT / row["url"].removeprefix("./")).is_file()
                            for row in captures))
        self.assertTrue(any(row["byte_length"] > 25 * 1024 * 1024 for row in captures))
        shell = (build.OUT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="#/scholarship"', shell)
        self.assertIn('!location.hash.startsWith("#/scholarship")', shell)


class MikeAccessHostLockTests(unittest.TestCase):
    worker_path = ROOT / "site" / "functions" / "mike" / "[[path]].js"
    worker = worker_path.read_text(encoding="utf-8")

    def test_only_custom_host_can_serve(self):
        self.assertIn('const GATED_HOST = "bowlam.com"', self.worker)
        self.assertIn("!==", self.worker)
        self.assertIn("404", self.worker)

    def test_no_cache_or_indexing(self):
        self.assertIn("private, no-store", self.worker)
        self.assertIn("noindex, nofollow", self.worker)

    def test_host_guard_runs_before_asset_fetch(self):
        self.assertLess(self.worker.index("404"), self.worker.index("ASSETS"))


if __name__ == "__main__":
    unittest.main()
