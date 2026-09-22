"""Mike Access is complete private research, never a shared release."""

import json
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
        self.assertEqual(len(private_translations), 4)
        self.assertTrue(all(row["content"] for row in private_translations))
        self.assertEqual(len(barakat_media), 5)
        self.assertTrue(all(row["url"] for row in barakat_media))

    def test_snapshot_audit_passes(self):
        snapshot = json.loads(
            (build.OUT / "private-snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["access"]["audience"], "Mike alone")
        self.assertTrue(all(check["passed"] for check in snapshot["audit_checks"]))


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
