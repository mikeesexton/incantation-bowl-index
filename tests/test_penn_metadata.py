import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bowl_index.penn_metadata import penn_fields, penn_metadata_claims
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_penn_metadata


class PennMetadataTests(unittest.TestCase):
    def claims(self, fields=None, description=""):
        return penn_metadata_claims(fields or {}, description, "https://collections.penn.museum/collections/object/1")

    def test_nested_table_values_and_alternative_labels_survive(self):
        fields = penn_fields('<table><tr><td>Object Number</td><td>B8697</td></tr>'
                             '<tr><td>Inscription Language</td><td><a>Aramaic</a> | Hebrew Language</td></tr>'
                             '<tr><td>Provenience</td><td>Iraq | Nippur</td></tr>'
                             '<tr><td>Description</td><td><p>12 fragments &amp; ink.</p></td></tr></table>')
        claims = self.claims(fields)
        by = {r['field']: r for r in claims}
        self.assertEqual(by['inscription_language']['value_text'], 'Aramaic | Hebrew Language')
        self.assertEqual(by['provenance']['value_text'], 'Iraq | Nippur')
        self.assertTrue(by['provenance']['locator'].endswith(' — Provenience'))
        self.assertEqual(fields['Description'], ['12 fragments & ink.'])

    def test_description_promotes_only_explicit_details_without_inventing_text(self):
        claims = self.claims(description='Incomplete-12 Frag; 7 Line Inscription around 2 Demons; '
                            'object has a rounded bottom; text is in concentric circles; '
                            'a circle appears in the center with two figures in it.')
        by = {}
        for c in claims:
            by.setdefault(c['field'], []).append(c['value_text'])
        self.assertEqual(by['reported_physical_condition'], ['Incomplete-12 Frag'])
        self.assertEqual(by['line_count'], ['7 lines (catalogue report)'])
        self.assertEqual(by['reported_bowl_form'], ['object has a rounded bottom'])
        self.assertEqual(by['text_layout'], ['text is in concentric circles'])
        self.assertEqual(len(by['iconography_or_caption']), 2)
        self.assertNotIn('translation', by)

    def test_abbreviated_fragment_report_and_qualified_manufacture(self):
        claims = self.claims(description='Near Complete-8 Frag/11 Line; probably wheel-made; '
                            'object has a rounded bottom.')
        self.assertIn('Near Complete-8 Frag', [c['value_text'] for c in claims])
        self.assertIn('probably wheel-made', [c['value_text'] for c in claims])
        self.assertIn('11 lines (catalogue report)', [c['value_text'] for c in claims])
        unusual = self.claims(description='Complete-1 Frag/7 Line; the object has a rounded bottom.')
        self.assertIn('Complete-1 Frag', [c['value_text'] for c in unusual])

    def test_title_credit_and_demon_do_not_infer_language_script_dates_or_people(self):
        claims = self.claims({'Title': ['Hebrew Bowl'], 'Credit Line': ['Nippur IV, 1900'],
                             'Description': ['Demon']}, description='Demon; 12 fragments.')
        fields = {c['field'] for c in claims}
        self.assertNotIn('inscription_language', fields)
        self.assertNotIn('script', fields)
        self.assertNotIn('dating', fields)
        self.assertNotIn('findspot', fields)
        self.assertNotIn('named_demon', fields)

    def test_all_repeated_language_rows_remain_and_uncertainty_is_retained(self):
        claims = self.claims({'Inscription Language': ['Mandaic', 'Possibly Aramaic']})
        self.assertEqual([c['value_text'] for c in claims], ['Mandaic', 'Possibly Aramaic'])
        self.assertTrue(all(c['certainty'] == 'reported' for c in claims))

    def test_register_and_quoted_translation_never_spill_into_layout(self):
        claims = self.claims(description='text is in concentric circles Aramaic Levy: '
                            '"A translation about demons and the creator."')
        self.assertEqual([c['value_text'] for c in claims], ['text is in concentric circles'])
        claims = self.claims(description='CBS Register: complete bowl, 9 fragments, 8 lines around demon')
        self.assertEqual(claims, [])

    def test_ranges_and_internal_external_counts_are_not_reduced_to_totals(self):
        claims = self.claims(description='Near Complete-6 Frag/6-7 Lines of Inscription.')
        self.assertIn('6-7 lines (catalogue report)', [c['value_text'] for c in claims])
        claims = self.claims(description='Complete-11 Frag/13 Lines Inscription Internal/1 External.')
        self.assertNotIn('line_count', [c['field'] for c in claims])
        self.assertIn('inscription_extent', [c['field'] for c in claims])


class Response(io.BytesIO):
    def __init__(self, body, code=200):
        super().__init__(body)
        self.code = self.status = code
        self.headers = {}


class PennPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / 'test.sqlite3')
        self.addCleanup(self.conn.close)
        migrate(self.conn)
        add_candidate(self.conn, dict(label='Penn B1', source=dict(source_type='museum_record',
            publisher='Penn Museum', title='Hebrew Bowl B1', citation='Penn Museum B1',
            url='https://collections.penn.museum/collections/object/1'),
            appearance=dict(locator='Penn web object 1'),
            identifiers=[dict(scheme='collection designation', value='B1')]))
        self.conn.commit()
        self.conn.execute('PRAGMA query_only=ON')
        self.page = ('<table><tr><td>Object Number</td><td>B1</td></tr>'
                     '<tr><td>Inscription Language</td><td>Mandaic</td></tr>'
                     '<tr><td>Description</td><td>Complete-1 Frag/7 Line.</td></tr></table>').encode()

    def prepare(self, robots=b'User-agent: *\nDisallow:\n', page=None):
        with mock.patch.object(prepare_penn_metadata.urllib.request, 'urlopen',
                               return_value=Response(robots)), \
             mock.patch.object(prepare_penn_metadata, '_open', return_value=Response(page or self.page)) as opened:
            result = prepare_penn_metadata.prepare(self.conn, self.root / 'private', delay=0)
        return result, opened

    def test_preparation_is_read_only_hash_bound_and_resumes_without_network(self):
        before = list(self.conn.iterdump())
        result, opened = self.prepare()
        self.assertEqual(result['records'], 1)
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(before, list(self.conn.iterdump()))
        with mock.patch.object(prepare_penn_metadata, '_open', side_effect=AssertionError('network')):
            repeat = prepare_penn_metadata.prepare(self.conn, self.root / 'private', delay=0)
        self.assertEqual(repeat['manifest_sha256'], result['manifest_sha256'])
        path = self.root / 'private/1.html'
        path.write_bytes(path.read_bytes() + b'changed')
        failed, opened = self.prepare()
        self.assertEqual(failed['records'], 0)
        self.assertEqual(len(failed['failures']), 1)
        self.assertEqual(opened.call_count, 0)

    def test_wrong_object_number_and_robots_denial_produce_no_claim_manifest(self):
        result, opened = self.prepare(page=self.page.replace(b'B1', b'B2'))
        self.assertEqual(result['claims'], 0)
        self.assertIn('does not match', result['failures'][0]['error'])
        # Use a fresh evidence directory for the policy-denial check.
        for path in (self.root / 'private').iterdir():
            path.unlink()
        result, opened = self.prepare(robots=b'User-agent: *\nDisallow: /collections/object/*\n')
        self.assertEqual(result['claims'], 0)
        self.assertEqual(opened.call_count, 0)


if __name__ == '__main__':
    unittest.main()
