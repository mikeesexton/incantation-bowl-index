import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfWriter
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.proofreading import apply_proofreading, current_text_reviews, digest_text, text_fingerprint
from bowl_index.montgomery import apply_montgomery_review
from bowl_index.export import export_all


class ProofreadingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.conn = connect(self.root / 'db.sqlite3')
        migrate(self.conn)
        add_candidate(self.conn, {
            'label': 'Test bowl', 'source': {'source_type': 'book', 'title': 'Edition', 'citation': 'Edition'},
            'appearance': {'locator': 'text 1', 'confidence': 1},
            'identifiers': [{'scheme': 'publication object key', 'value': 'Montgomery 1913::1'}],
            'texts': [{'text_type': 'translation', 'content': 'OCR PRIVATE TEXT', 'editor': 'James A. Montgomery',
                       'public_ok': True, 'rights_status': 'public_domain'}]})
        self.row = dict(self.conn.execute('SELECT * FROM texts').fetchone())
        pdf = self.root / 'scan.pdf'
        writer = PdfWriter(); writer.add_blank_page(600, 800)
        with pdf.open('wb') as handle: writer.write(handle)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        self.conn.execute('INSERT INTO captures (id,source_id,url,retrieved_at,sha256,byte_length,storage_path) '
                          'VALUES (?,?,?,?,?,?,?)', ('CAP-TEST', self.row['source_id'], 'https://example.org/scan',
                          '2026-09-04T23:00:00Z', sha, pdf.stat().st_size, 'scan.pdf'))
        self.conn.commit()
        (self.root / 'corrected.txt').write_text('Corrected ... private text.\n')
        self.manifest = {'schema_version': 1, 'source_id': self.row['source_id'], 'source_pdf_path': 'scan.pdf',
            'source_pdf_sha256': sha, 'reviewed_by': 'Test reviewer', 'reviewed_at': '2026-09-04T23:00:00Z',
            'editorial_policy': 'Normalized reading text.', 'entries': [{
                'review_id': 'IBI-PROOF-TEST', 'text_id': self.row['id'],
                'expected_text_sha256': text_fingerprint(self.row), 'corrected_content_path': 'corrected.txt',
                'corrected_content_sha256': digest_text('Corrected ... private text.'), 'pdf_pages': [1],
                'status': 'reading_text_checked', 'correction_notes': 'Restored a gap marker.'}]}
        self.path = self.root / 'review.json'

    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def apply(self):
        self.path.write_text(json.dumps(self.manifest))
        return apply_proofreading(self.conn, self.path, self.root)

    def test_original_preserved_public_approval_reset_and_replay_safe(self):
        self.assertEqual(self.apply()['changed'], 1)
        self.assertEqual(self.apply()['changed'], 0)
        row = self.conn.execute('SELECT * FROM texts').fetchone()
        self.assertEqual(row['content'], 'Corrected ... private text.')
        self.assertEqual(row['public_ok'], 0)
        review = self.conn.execute('SELECT * FROM text_proofreading_reviews').fetchone()
        self.assertEqual(json.loads(review['before_json']), self.row)
        self.assertEqual(len(current_text_reviews(self.conn)), 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM text_proofreading_reviews')
        self.conn.rollback()
        self.conn.execute("UPDATE texts SET locator='changed'"); self.conn.commit()
        self.assertEqual(current_text_reviews(self.conn), {})
        with self.assertRaisesRegex(ValueError, 'stale evidence'): self.apply()

    def test_changed_scan_and_text_are_rejected(self):
        self.conn.execute("UPDATE texts SET content='changed'"); self.conn.commit()
        with self.assertRaisesRegex(ValueError, 'Text changed'): self.apply()
        (self.root / 'scan.pdf').write_bytes(b'changed scan')
        with self.assertRaisesRegex(ValueError, 'scan hash'): self.apply()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM text_proofreading_reviews').fetchone()[0], 0)

    def test_notes_name_the_text_language(self):
        self.conn.execute("UPDATE texts SET language='German'")
        self.conn.commit()
        self.row = dict(self.conn.execute('SELECT * FROM texts').fetchone())
        self.manifest['entries'][0]['expected_text_sha256'] = text_fingerprint(self.row)
        self.apply()
        notes = self.conn.execute('SELECT notes FROM texts').fetchone()[0]
        self.assertIn('normalized German reading text', notes)

    def test_invalid_second_entry_does_not_partially_apply(self):
        self.manifest['entries'].append(dict(self.manifest['entries'][0], text_id='ABSENT', review_id='SECOND'))
        with self.assertRaisesRegex(ValueError, 'Missing text'): self.apply()
        self.assertEqual(self.conn.execute('SELECT content FROM texts').fetchone()[0], self.row['content'])

    def test_ocr_reimport_cannot_overwrite_reviewed_text(self):
        self.apply()
        apply_montgomery_review(self.conn, {'source_id': self.row['source_id'], 'translation_text_numbers': [1]},
            {1: {'content': 'OCR overwrite', 'printed_page_start': 1, 'printed_page_end': 1,
                 'pdf_page_start': 1, 'pdf_page_end': 1}})
        self.assertEqual(self.conn.execute('SELECT content FROM texts').fetchone()[0], 'Corrected ... private text.')

    def reimport(self, content, locator='text 1'):
        add_candidate(self.conn, {
            'source_id': self.row['source_id'], 'label': 'Test bowl',
            'appearance': {'locator': locator},
            'texts': [{'text_type': 'translation', 'content': content,
                       'locator': 'text 1'}]})
        self.conn.commit()

    def test_generic_import_does_not_recreate_proofread_original(self):
        self.apply()
        self.reimport(self.row['content'])
        rows = self.conn.execute('SELECT id,content FROM texts').fetchall()
        self.assertEqual([(r['id'], r['content']) for r in rows],
                         [(self.row['id'], 'Corrected ... private text.')])

    def test_import_retries_preserve_multiple_proofreading_revisions(self):
        self.apply()
        intermediate = 'Corrected ... private text.'
        current = self.conn.execute('SELECT * FROM texts').fetchone()
        (self.root / 'corrected.txt').write_text('Second corrected reading.\n')
        entry = self.manifest['entries'][0]
        entry.update(review_id='IBI-PROOF-SECOND',
                     expected_text_sha256=text_fingerprint(current),
                     corrected_content_sha256=digest_text('Second corrected reading.'))
        self.apply()
        for content in (self.row['content'], intermediate, 'Second corrected reading.'):
            self.reimport(content)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM texts').fetchone()[0], 1)
        self.assertEqual(self.conn.execute('SELECT content FROM texts').fetchone()[0],
                         'Second corrected reading.')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM text_proofreading_reviews').fetchone()[0], 2)
        self.assertEqual(len(current_text_reviews(self.conn)), 1)

    def test_draft_history_does_not_suppress_another_witness_or_new_reading(self):
        self.apply()
        self.reimport(self.row['content'], locator='text 2')
        self.reimport('A separately imported new reading.')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM texts').fetchone()[0], 3)

    def test_research_export_does_not_leak_historical_text_payloads(self):
        self.apply()
        destination = self.root / 'exports'; export_all(self.conn, destination)
        output = ''.join(p.read_text() for p in destination.iterdir())
        self.assertNotIn('OCR PRIVATE TEXT', output)
        self.assertNotIn('Corrected ... private text.', output)

    def html_manifest(self):
        source = self.root / 'source.html'
        source.write_text('<p>Corrected ... private text.</p>')
        sha = hashlib.sha256(source.read_bytes()).hexdigest()
        self.conn.execute('UPDATE captures SET mime_type=?,sha256=?,storage_path=?',
                          ('text/html', sha, 'source.html'))
        self.conn.commit()
        self.manifest.update(schema_version=2, source_kind='html',
                             source_capture_path='source.html', source_capture_sha256=sha)
        self.manifest['entries'][0].pop('pdf_pages')
        self.manifest['entries'][0]['source_locators'] = ['Quoted text in catalogue description']

    def test_html_review_preserves_original_and_replays(self):
        self.html_manifest()
        self.assertEqual(self.apply()['changed'], 1)
        self.assertEqual(self.apply()['changed'], 0)
        review = self.conn.execute('SELECT * FROM text_proofreading_reviews').fetchone()
        self.assertEqual(json.loads(review['source_pages_json']), ['Quoted text in catalogue description'])
        self.assertEqual(json.loads(review['before_json']), self.row)
        self.assertEqual(self.conn.execute('SELECT public_ok FROM texts').fetchone()[0], 0)
        self.assertEqual(len(current_text_reviews(self.conn)), 1)
        (self.root / 'source.html').write_text('altered')
        with self.assertRaisesRegex(ValueError, 'scan hash'): self.apply()

    def test_html_requires_registered_mime_and_nonempty_locators(self):
        self.html_manifest()
        self.manifest['entries'][0]['source_locators'] = [1]
        with self.assertRaisesRegex(ValueError, 'locators'): self.apply()
        self.manifest['entries'][0]['source_locators'] = ['Text section']
        self.conn.execute("UPDATE captures SET mime_type='application/pdf'")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, 'not HTML'): self.apply()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM text_proofreading_reviews').fetchone()[0], 0)
