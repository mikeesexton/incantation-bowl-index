import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.db import migrate
from bowl_index.ingest import add_candidate, add_source, load_jsonl
from bowl_index.state import corpus_fingerprint


class ReadingCaptureIngestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'capture.jsonl'
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.addCleanup(self.conn.close)
        migrate(self.conn)
        add_candidate(self.conn, dict(object_id='IBI-TEST', label='Test bowl',
            source=dict(id='SRC-TEST', source_type='article', title='Edition', citation='Edition'),
            appearance=dict(id='APP-TEST', locator='printed p. 1')))
        self.conn.execute('INSERT INTO captures (id,source_id,url,retrieved_at,sha256,byte_length,storage_path) '
            'VALUES (?,?,?,?,?,?,?)', ('CAP-TEST', 'SRC-TEST', 'local-deposit:test.pdf',
                '2026-10-03T20:00:00Z', '0' * 64, 100, 'test.pdf'))
        self.conn.commit()
        self.record = dict(source_id='SRC-TEST', appearance=dict(locator='printed p. 1'),
            texts=[dict(id='TXT-TEST', text_type='translation', content='Private translation',
                language='English', editor='Test editor', rights_status='copyrighted', public_ok=False,
                notes='Private source copy', created_at='2026-10-03T20:00:00Z')],
            media=[dict(id='MED-TEST', capture_id='CAP-TEST', media_type='drawing',
                url='private-capture:CAP-TEST#page=1', rights_status='copyrighted', notes='Hand copy')])

    def apply(self, records=None):
        self.path.write_text(''.join(json.dumps(r) + '\n' for r in (records or [self.record])))
        return load_jsonl(self.conn, self.path, 'candidate')

    def test_exact_rehearsal_and_replay(self):
        other = sqlite3.connect(':memory:'); other.row_factory = sqlite3.Row
        self.addCleanup(other.close)
        self.conn.backup(other)
        self.apply(); load_jsonl(other, self.path, 'candidate')
        self.assertEqual(corpus_fingerprint(self.conn), corpus_fingerprint(other))
        self.assertEqual(self.conn.execute('SELECT created_at FROM texts').fetchone()[0], '2026-10-03 20:00:00')
        self.assertEqual(self.conn.execute('SELECT capture_id FROM media').fetchone()[0], 'CAP-TEST')
        before = corpus_fingerprint(self.conn); self.apply()
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_source_manifest_creation_time_is_reproducible_and_not_replaced(self):
        other = sqlite3.connect(':memory:'); other.row_factory = sqlite3.Row
        self.addCleanup(other.close); self.conn.backup(other)
        source = dict(id='SRC-NEW', source_type='book', title='Collection', citation='Collection',
                      created_at='2026-10-03T21:00:00Z')
        add_source(self.conn, source); add_source(other, source)
        self.assertEqual(dict(self.conn.execute("SELECT * FROM sources WHERE id='SRC-NEW'").fetchone()),
                         dict(other.execute("SELECT * FROM sources WHERE id='SRC-NEW'").fetchone()))
        source['created_at'] = '2026-10-04T21:00:00Z'
        add_source(self.conn, source)
        row = self.conn.execute("SELECT * FROM sources WHERE id='SRC-NEW'").fetchone()
        self.assertEqual((row['created_at'], row['updated_at']), ('2026-10-03 21:00:00',) * 2)

    def test_new_source_non_utc_time_rejected(self):
        source = dict(id='SRC-NEW', source_type='book', title='Collection', citation='Collection',
                      created_at='2026-10-03T21:00:00-04:00')
        before = corpus_fingerprint(self.conn)
        with self.assertRaisesRegex(ValueError, 'Source creation timestamp must be UTC'):
            add_source(self.conn, source)
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_new_appearance_on_existing_object_rehearses_and_replays_exactly(self):
        other = sqlite3.connect(':memory:'); other.row_factory = sqlite3.Row
        self.addCleanup(other.close); self.conn.backup(other)
        record = copy.deepcopy(self.record)
        record.update(object_id='IBI-TEST', label='Existing bowl')
        record['appearance'] = dict(id='APP-NEW', locator='printed p. 2',
                                   created_at='2026-10-03T22:00:00Z')
        self.apply([record]); load_jsonl(other, self.path, 'candidate')
        self.assertEqual(corpus_fingerprint(self.conn), corpus_fingerprint(other))
        for table, key in [('appearances', 'id'), ('appearance_object_links', 'appearance_id')]:
            row = self.conn.execute(f"SELECT * FROM {table} WHERE {key}='APP-NEW'").fetchone()
            self.assertEqual(row['created_at'], '2026-10-03 22:00:00')
        before = corpus_fingerprint(self.conn)
        record['appearance']['created_at'] = '2026-10-04T22:00:00Z'
        self.apply([record]); self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_invalid_appearance_timestamp_rolls_back_reading_batch(self):
        record = copy.deepcopy(self.record)
        record.update(object_id='IBI-TEST', label='Existing bowl')
        record['appearance'] = dict(id='APP-NEW', locator='printed p. 2',
                                   created_at='2026-10-03T22:00:00-04:00')
        before = corpus_fingerprint(self.conn)
        with self.assertRaisesRegex(ValueError, 'Appearance creation timestamp must be UTC'):
            self.apply([self.record, record])
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_explicit_ids_cannot_replace_or_silently_alias(self):
        self.apply(); before = corpus_fingerprint(self.conn)
        for group, field, replacement in [('texts', 'content', 'Changed'), ('texts', 'editor', 'Other editor'),
                                          ('media', 'notes', 'Different drawing'), ('media', 'id', 'MED-OTHER'),
                                          ('texts', 'id', 'TXT-OTHER')]:
            record = copy.deepcopy(self.record); record[group][0][field] = replacement
            with self.assertRaises(ValueError): self.apply([record])
            self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_bad_capture_or_non_utc_stamp_rolls_back_entire_batch(self):
        before = corpus_fingerprint(self.conn)
        for bad in ['CAP-MISSING', None]:
            record = copy.deepcopy(self.record)
            if bad: record['media'][0]['capture_id'] = bad
            else: record['texts'][0]['created_at'] = '2026-10-03T20:00:00-04:00'
            with self.assertRaises(ValueError): self.apply([record])
            self.assertEqual(corpus_fingerprint(self.conn), before)
        bad = copy.deepcopy(self.record)
        bad['texts'] = []
        bad['media'][0].update(id='MED-SECOND', url='private-capture:bad', capture_id='CAP-MISSING')
        with self.assertRaises(ValueError): self.apply([self.record, bad])
        self.assertEqual(corpus_fingerprint(self.conn), before)
        self.conn.execute("INSERT INTO sources (id,source_type,title,citation) VALUES ('SRC-OTHER','article','Other','Other')")
        self.conn.execute("UPDATE captures SET source_id='SRC-OTHER'"); self.conn.commit()
        before = corpus_fingerprint(self.conn)
        with self.assertRaisesRegex(ValueError, 'belong to its source'): self.apply()
        self.assertEqual(corpus_fingerprint(self.conn), before)

    def test_replay_preserves_source_checked_revision_and_rejects_wrong_id(self):
        self.apply()
        old = dict(self.conn.execute('SELECT * FROM texts').fetchone())
        self.conn.execute("UPDATE texts SET content='Checked revision',notes='Checked note'")
        after = dict(self.conn.execute('SELECT * FROM texts').fetchone())
        self.conn.execute('INSERT INTO text_proofreading_reviews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            ('IBI-PROOF-TEST', 'TXT-TEST', 'SRC-TEST', '0' * 64, 'before', 'after', 'partial_review',
             'Test reviewer', '2026-10-03T20:00:00+00:00', '[1]', 'Policy', 'Checked source',
             json.dumps(old), json.dumps(after)))
        self.conn.commit(); before = corpus_fingerprint(self.conn); self.apply()
        self.assertEqual(corpus_fingerprint(self.conn), before)
        self.record['texts'][0]['id'] = 'TXT-WRONG'
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(corpus_fingerprint(self.conn), before)
