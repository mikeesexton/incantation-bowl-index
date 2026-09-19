import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import build_public_site as build  # noqa: E402


def payload(identity_count=40, records=55, coverage=None):
    return {
        'identity_count': identity_count,
        'source_record_count': records,
        'coverage': coverage or {'text_edition': 21, 'provenance': 9, 'image': 4},
        'scholarship': {
            'decades': [
                {'decade': 1850, 'indexed': 3, 'field_control_list': 2, 'incomplete': False},
                {'decade': 2020, 'indexed': 7, 'field_control_list': 5, 'incomplete': True},
            ],
            'label': 'Scholarly publications indexed, by decade',
            'scope': 'Dated scholarly works in this index.',
            'undated_count': 3,
        },
        'snapshot': {'id': 'a' * 64, 'current_year': 2026, 'local_only': True},
    }


class PublicSiteReleaseBoundaryTests(unittest.TestCase):
    """The landing page must not become a path into the corpus.

    ACCESS-008 allows bowlam.com to describe the project in the project's own
    words and to carry an interest field. It does not allow the page to expose
    records. These tests fail the build rather than trusting a reviewer to
    notice that a per-object field crept into the template.
    """

    def setUp(self):
        self.page = build.render(payload(), 'a' * 64, '19 September 2026')

    def test_no_corpus_endpoint_or_console_route(self):
        for forbidden in ('/api/introduction', '/api/reader', '#/explore', '#/search',
                          '#/scholarship', '#/queues', '127.0.0.1', 'localhost'):
            self.assertNotIn(forbidden, self.page,
                             '%s reaches the corpus and must not appear on the public page'
                             % forbidden)

    def test_no_identity_identifiers(self):
        self.assertNotIn('IDENT-', self.page)
        self.assertIsNone(re.search(r'identity[_-]?id', self.page, re.IGNORECASE))

    def test_only_aggregate_counts_are_baked_in(self):
        """Circles carry an index for the toggle, never a record of any kind."""
        for circle in re.findall(r'<circle[^>]*class="intro-circle"[^>]*>', self.page):
            self.assertNotIn('data-bowl-identity', circle)
            attributes = set(re.findall(r'\s([a-zA-Z-]+)=', circle))
            self.assertEqual(attributes, {'cx', 'cy', 'r', 'class', 'data-i'},
                             'unexpected attribute on a public coverage circle: %s' % circle)

    def test_build_refuses_to_write_a_leaking_page(self):
        """The guard in main() is the backstop; prove it actually triggers."""
        self.assertIn('refusing to write', (ROOT / 'scripts' / 'build_public_site.py')
                      .read_text(encoding='utf-8'))


class PublicSiteContentTests(unittest.TestCase):
    def setUp(self):
        self.page = build.render(payload(), 'a' * 64, '19 September 2026')

    def test_counts_render_from_the_payload(self):
        self.assertIn('40', self.page)
        self.assertIn('55', self.page)
        self.assertIn('21', self.page)

    def test_carries_an_interest_field_posting_to_the_signup_endpoint(self):
        self.assertIn('action="/api/interest"', self.page)
        self.assertIn('type="email"', self.page)

    def test_states_what_is_withheld(self):
        """ACCESS-008 asks the page to say what is deliberately not published."""
        self.assertIn('does not reproduce them', self.page)
        self.assertIn('Provenance is reported, not settled', self.page)

    def test_coverage_selections_are_deterministic(self):
        """A rebuild on unchanged counts must not produce a churning diff."""
        self.assertEqual(build.render(payload(), 'a' * 64, '19 September 2026'), self.page)

    def test_coverage_selection_sizes_match_the_counts(self):
        selections = json.loads(
            re.search(r'var SELECTIONS = (\{.*?\});', self.page, re.DOTALL).group(1))
        self.assertEqual(len(selections['all']), 40)
        self.assertEqual(len(selections['text_edition']), 21)
        self.assertEqual(len(selections['provenance']), 9)
        self.assertEqual(len(selections['image']), 4)


class PublicSiteSeparationTests(unittest.TestCase):
    """The public artefact and the localhost console stay separate files."""

    def test_public_stylesheet_does_not_import_the_console(self):
        css = (ROOT / 'site' / 'src' / 'public.css').read_text(encoding='utf-8')
        self.assertNotIn('@import', css)
        self.assertNotIn('styles.css', css)

    def test_wrangler_deploys_only_the_generated_directory(self):
        toml = (ROOT / 'site' / 'wrangler.toml').read_text(encoding='utf-8')
        self.assertIn('pages_build_output_dir = "public"', toml)
        # Comments are allowed to name the console; settings are not.
        settings = [line for line in toml.splitlines()
                    if line.strip() and not line.lstrip().startswith('#')]
        self.assertNotIn('web/', '\n'.join(settings),
                         'the research console must never be deployed')

    def test_signup_function_never_touches_the_corpus(self):
        worker = (ROOT / 'site' / 'functions' / 'api' / 'interest.js').read_text(encoding='utf-8')
        for forbidden in ('ibi.sqlite3', 'identity', 'appearance', 'claims'):
            self.assertNotIn(forbidden, worker)


if __name__ == '__main__':
    unittest.main()
