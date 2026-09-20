"""The gated scholar preview must stay a projection, not a console.

ACCESS-009 serves data, so the things that keep it honest are: it is built from
`projection.Projection` like every other public surface, it never ships the
console's own scripts, and it is not written into the Pages output directory
where it would deploy before an Access policy exists.
"""
import re
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
        import json
        texts = json.loads((build.OUT / 'data' / 'texts.json').read_text(encoding='utf-8'))
        withheld = [row for row in texts['rows']
                    if row['content_status'] != 'included']
        self.assertTrue(withheld, 'expected some rows to be withheld')
        for row in withheld:
            self.assertIsNone(row['content'], 'a withheld row shipped its content')
            self.assertIsNone(row['license_url'])
            self.assertTrue(row['access_citation'], 'a withheld row lost its pointer')

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


if __name__ == '__main__':
    unittest.main()
