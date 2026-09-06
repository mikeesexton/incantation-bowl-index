import tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.identity import (
    CONTENT_COVERAGE, CORE_ORDER, display_name, identity_rows, reading_score,
)

class DisplayNameTests(unittest.TestCase):
    """Labels record how a record was found. A reader needs what it is."""
    def test_discovery_suffixes_are_removed(self):
        self.assertEqual(display_name('Penn Museum CBS 2923 / B2923 exhibition appearance'),
                         'Penn Museum CBS 2923 / B2923')
        self.assertEqual(display_name('Isbell 1975 bowl 23 / AIT 12 — COJS translation appearance'),
                         'Isbell 1975 bowl 23 / AIT 12')
    def test_discovery_prefixes_are_removed(self):
        self.assertEqual(display_name('Waller 2022: SD 34'), 'SD 34')
    def test_a_clean_label_is_left_alone(self):
        for label in ('CBS 2922', 'British Museum 113189 (Segal 139P)',
                      "Christie's London 1974 Hera auction lot 348"):
            self.assertEqual(display_name(label), label)
    def test_a_catalogue_identifier_is_preferred_when_there_is_no_label(self):
        self.assertEqual(
            display_name('', ['collection designation: X.0552',
                              'British Museum museum number: 113189']),
            '113189')
    def test_it_never_returns_empty(self):
        self.assertTrue(display_name(''))
        self.assertTrue(display_name(None))


class ReadingScoreTests(unittest.TestCase):
    def test_a_published_text_outweighs_any_single_flag(self):
        text_only = {'public_text_count': 1}
        flags = {'has_client': 1, 'has_ritual': 1}
        self.assertGreater(reading_score(text_only), reading_score(flags))
    def test_a_bare_record_scores_zero(self):
        self.assertEqual(reading_score({'label': 'stub'}), 0)
    def test_missing_keys_are_treated_as_absent(self):
        self.assertEqual(reading_score({}), 0)


class CompletenessTests(unittest.TestCase):
    """completeness_score is rendered as n/10 in four places; it must be <= 10."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'rich bowl','source':{'source_type':'catalogue',
            'title':'Cat','citation':'Cat 2026','url':'https://example.org/c'},
            'appearance':{'locator':'no. 1','confidence':1},
            'claims':[{'field':f,'value_text':'v','locator':'p. 1'} for f in (
                'current_location','findspot','dating','dimensions','material',
                'inscription_language','script','client','text_purpose','iconography',
                'biblical_quotation','condition','line_count')]})
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def test_core_score_never_exceeds_ten(self):
        row=identity_rows(self.conn)[0]
        self.assertLessEqual(row['completeness_score'], len(CORE_ORDER))
        self.assertLessEqual(row['completeness_score'], 10)
    def test_content_facets_are_counted_separately(self):
        row=identity_rows(self.conn)[0]
        self.assertGreater(row['content_completeness'], 0)
        self.assertLessEqual(row['content_completeness'], len(CONTENT_COVERAGE))
        # Content coverage must not inflate the core score, which is the 12/10 bug.
        self.assertLessEqual(row['completeness_score'], 10)
    def test_every_row_carries_a_display_name_and_reading_score(self):
        row=identity_rows(self.conn)[0]
        self.assertTrue(row['display_name'])
        self.assertIsInstance(row['reading_score'], int)

if __name__=='__main__':
    unittest.main()
