import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.claim_corrections import apply_locator_corrections
from bowl_index.db import connect, migrate
from bowl_index.ingest import load_compact_list


class LocatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / 'test.db')
        migrate(self.conn)
        self.seed = self.root / 'seed.json'
        self.seed.write_text(json.dumps({
            'source': {'source_type': 'catalogue', 'title': 'Test catalogue', 'citation': 'Test'},
            'ranges': [{'start': 1, 'end': 3, 'suffix': 'A', 'section_pages': '10–12',
                        'claims': [{'field': 'inscription_language', 'value_text': 'Aramaic'},
                                   {'field': 'script', 'value_text': 'Test', 'locator': 'explicit appendix'}]}]
        }))
        load_compact_list(self.conn, self.seed)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_ranges_isolate_default_locators_and_preserve_explicit_locators(self):
        rows = self.conn.execute('SELECT c.field,c.locator,a.locator appearance_locator '
                                 'FROM claims c JOIN appearances a ON a.id=c.appearance_id').fetchall()
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row['locator'], row['appearance_locator'] if row['field'] == 'inscription_language' else 'explicit appendix')
        load_compact_list(self.conn, self.seed)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM claims').fetchone()[0], 6)

    def manifest(self):
        row = dict(self.conn.execute("SELECT * FROM claims WHERE field='inscription_language' ORDER BY locator LIMIT 1 OFFSET 1").fetchone())
        right = row['locator']
        row['locator'] = 'text 001A; section pp. 10–12'
        self.conn.execute('UPDATE claims SET locator=? WHERE id=?', (row['locator'], row['id']))
        self.conn.commit()
        return dict(schema_version=1, reviewed_by='Test reviewer', reviewed_at='2026-09-04T23:00:00Z',
                    evidence_path='seed.json', evidence_sha256=hashlib.sha256(self.seed.read_bytes()).hexdigest(),
                    entries=[dict(id='IBI-CORR-TEST', before=row, locator=right, rationale='Range locator aliasing repair')])

    def test_audited_repair_replay_and_immutable_original(self):
        m = self.manifest()
        self.assertEqual(apply_locator_corrections(self.conn, m, self.root)['applied'], 1)
        self.assertEqual(apply_locator_corrections(self.conn, m, self.root)['unchanged'], 1)
        history = self.conn.execute('SELECT * FROM claim_locator_corrections').fetchone()
        self.assertEqual(json.loads(history['before_json']), m['entries'][0]['before'])
        before = json.loads(history['before_json']); after = json.loads(history['after_json'])
        self.assertEqual(set(k for k in before if before[k] != after[k]), {'locator'})
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE claim_locator_corrections SET rationale='changed'")
        self.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM claim_locator_corrections')
        self.conn.rollback()

    def test_stale_claim_and_seed_are_rejected(self):
        m = self.manifest()
        self.conn.execute("UPDATE claims SET certainty='uncertain' WHERE id=?", (m['entries'][0]['before']['id'],))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, 'claim evidence changed'):
            apply_locator_corrections(self.conn, m, self.root)
        self.seed.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'correction evidence changed'):
            apply_locator_corrections(self.conn, m, self.root)

    def test_batch_failure_rolls_back_first_repair(self):
        m = self.manifest()
        m['entries'].append(dict(m['entries'][0], id='IBI-CORR-DUPLICATE'))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            apply_locator_corrections(self.conn, m, self.root)
        current = dict(self.conn.execute('SELECT * FROM claims WHERE id=?', (m['entries'][0]['before']['id'],)).fetchone())
        self.assertEqual(current, m['entries'][0]['before'])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM claim_locator_corrections').fetchone()[0], 0)
