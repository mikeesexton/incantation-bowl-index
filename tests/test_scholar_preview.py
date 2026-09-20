"""The gated scholar preview must stay a projection, not a console.

ACCESS-009 serves data, so the things that keep it honest are: it is built from
`projection.Projection` like every other public surface, it never ships the
console's own scripts, and it is not written into the Pages output directory
where it would deploy before an Access policy exists.
"""
import re
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))

import build_scholar_preview as build  # noqa: E402


class ScholarPreviewBuildTests(unittest.TestCase):
    source = (ROOT / 'scripts' / 'build_scholar_preview.py').read_text(encoding='utf-8')

    def test_builds_outside_the_pages_output_directory(self):
        """Anything under site/public ships with the next deploy, gate or no gate."""
        public = ROOT / 'site' / 'public'
        self.assertFalse(str(build.OUT).startswith(str(public)),
                         'the preview must not be built into the Pages output directory')

    def test_never_copies_the_console(self):
        """styles.css is read for its palette tokens; nothing of it is shipped."""
        copied = re.findall(r'shutil\.copy\w*\(WEB / "([^"]+)"', self.source)
        self.assertEqual(copied, ['reading.js'],
                         'only the reading room may be copied out of web/, got %r' % copied)

    def test_built_output_carries_no_console_asset(self):
        if not build.OUT.exists():
            self.skipTest('preview not built; run scripts/build_scholar_preview.py')
        names = {path.name for path in build.OUT.rglob('*') if path.is_file()}
        for forbidden in ('app.js', 'home.js', 'styles.css'):
            self.assertNotIn(forbidden, names,
                             '%s belongs to the research console' % forbidden)

    def test_built_output_withholds_what_the_projection_withholds(self):
        if not build.OUT.exists():
            self.skipTest('preview not built; run scripts/build_scholar_preview.py')
        texts = json.loads((build.OUT / 'data' / 'texts.json').read_text(encoding='utf-8'))
        withheld = [row for row in texts['rows']
                    if row['content_status'] != 'included']
        self.assertTrue(withheld, 'expected some rows to be withheld')
        for row in withheld:
            self.assertIsNone(row['content'], 'a withheld row shipped its content')
            self.assertIsNone(row['license_url'])
            self.assertTrue(row['access_citation'], 'a withheld row lost its pointer')

    def test_built_output_carries_a_pending_release_candidate(self):
        if not build.OUT.exists():
            self.skipTest('preview not built; run scripts/build_scholar_preview.py')
        candidate = json.loads(
            (build.OUT / 'release-candidate.json').read_text(encoding='utf-8'))
        self.assertEqual(candidate['approval']['status'], 'pending_owner_approval')
        self.assertTrue(candidate['candidate_id'])
        self.assertTrue(all(check['passed'] for check in candidate['audit_checks']))
        self.assertEqual(candidate['withheld_counts']['source_wording'], 30)
        self.assertEqual(candidate['withheld_counts']['text_content'], 19)
        self.assertEqual(candidate['withheld_counts']['media'], 29)
        self.assertEqual(candidate['withheld_counts']['private_capture_rows'], 55)
        index = (build.OUT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('release-candidate.json', index)
        self.assertIn('pending project-owner approval', index)

    def test_rows_come_from_the_shared_projection(self):
        """A second row-builder would be a second chance to publish something withheld."""
        self.assertIn('from bowl_index.projection import', self.source)
        self.assertIn('Projection(conn)', self.source)
        self.assertNotIn('SELECT', self.source.replace(
            'SELECT storage_path FROM captures', ''),
            'the preview must not query the corpus directly')

    def test_refuses_to_write_a_leaking_build(self):
        self.assertIn('refusing to write', self.source)

    def test_palette_tokens_still_resolve(self):
        """reading.css borrows these from the console; a rename must fail loudly."""
        css = (ROOT / 'web' / 'styles.css').read_text(encoding='utf-8')
        light, dark = build.tokens(css)
        for name in build.TOKENS:
            self.assertRegex(light, r'--%s\s*:' % re.escape(name))
        for name in ('ink', 'paper', 'lapis'):
            self.assertRegex(dark, r'--%s\s*:' % re.escape(name))

    def test_reading_room_is_shared_verbatim(self):
        """The published build is the same file the console runs, not a fork."""
        self.assertIn('shutil.copy2(WEB / "reading.js"', self.source)
        reading = (ROOT / 'web' / 'reading.js').read_text(encoding='utf-8')
        self.assertIn('window.READER_BASE', reading)
        self.assertIn('window.READER_STANDALONE', reading)


class PreviewHostLockTests(unittest.TestCase):
    """A Cloudflare Access policy covers one hostname; a Pages project answers on several.

    bowlam.com, bowlam.pages.dev and a per-deployment <hash>.bowlam.pages.dev all
    serve the same bytes, so a policy on the custom domain alone leaves the rest
    ungated. That happened on 20 September 2026. The host lock is the code-side
    guarantee, and it must not be quietly removed.
    """

    worker = (ROOT / 'site' / 'functions' / 'preview' / '[[path]].js').read_text(encoding='utf-8')

    def test_the_lock_exists(self):
        self.assertTrue((ROOT / 'site' / 'functions' / 'preview' / '[[path]].js').is_file())

    def test_serves_only_the_host_access_covers(self):
        self.assertIn('const GATED_HOST = "bowlam.com"', self.worker)
        self.assertIn('!==', self.worker)
        self.assertIn('404', self.worker)

    def test_refuses_before_reaching_the_asset(self):
        """The 404 must return before env.ASSETS is consulted, or it serves the file."""
        guard = self.worker.index('404')
        assets = self.worker.index('ASSETS')
        self.assertLess(guard, assets,
                        'the host check must short-circuit before the asset is fetched')

    def test_gated_responses_are_never_stored(self):
        self.assertIn('no-store', self.worker)
        self.assertIn('noindex', self.worker)


if __name__ == '__main__':
    unittest.main()
