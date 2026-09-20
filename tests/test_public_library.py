import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_public_library as build  # noqa: E402


class PublicLibraryBuildTests(unittest.TestCase):
    def test_build_is_outside_deployed_pages_directory(self):
        self.assertFalse(str(build.OUT).startswith(str(ROOT / "site" / "public")))

    def test_candidate_is_pending_and_all_audits_pass(self):
        if not build.OUT.exists():
            self.skipTest("library not built")
        candidate = json.loads((build.OUT / "release-candidate.json").read_text())
        self.assertEqual(candidate["approval"]["status"], "pending_owner_approval")
        self.assertTrue(all(check["passed"] for check in candidate["audit_checks"]))
        self.assertEqual(candidate["counts"]["texts"], 252)
        self.assertEqual(candidate["counts"]["media"], 298)

    def test_payload_contains_only_released_material(self):
        if not build.OUT.exists():
            self.skipTest("library not built")
        payload = json.loads((build.OUT / "data" / "library.json").read_text())
        texts = [row for item in payload["items"] for row in item["texts"]]
        media = [row for item in payload["items"] for row in item["media"]]
        self.assertNotIn(build.EXCLUDED_TEXT, {row["id"] for row in texts})
        self.assertTrue(all(row["content"] and row["attribution"] for row in texts))
        self.assertTrue(all(row["url"] and row["rights_locator"] for row in media))

    def test_interface_has_search_filters_and_safe_remote_links(self):
        self.assertIn('type="search"', build.INDEX)
        self.assertEqual(set(re.findall(r'data-filter="([^"]+)"', build.INDEX)),
                         {"all", "images", "translations", "texts"})
        self.assertIn('rel="external noreferrer"', build.JS)
        self.assertIn('loading="lazy"', build.JS)

    def test_candidate_is_self_contained_for_local_review(self):
        if not build.OUT.exists():
            self.skipTest("library not built")
        self.assertTrue((build.OUT / "fonts" / "frank-ruhl-libre-latin.woff2").is_file())
        self.assertIn("url('fonts/", (build.OUT / "library.css").read_text())


if __name__ == "__main__":
    unittest.main()
