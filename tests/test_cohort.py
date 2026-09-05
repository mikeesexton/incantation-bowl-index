import json
import tempfile
import unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import load_compact_list
from bowl_index.cohort import apply_montgomery_register


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.conn = connect(self.root / 'db'); migrate(self.conn)
        seed = self.root / 'seed.json'
        seed.write_text(json.dumps({'source': {'source_type': 'book', 'title': 'Montgomery test', 'citation': 'Test'},
                                   'ranges': [{'start': 1, 'end': 40, 'section_pages': '321–326'}]}))
        load_compact_list(self.conn, seed)
        source = self.conn.execute('SELECT id FROM sources').fetchone()[0]
        self.conn.execute('INSERT INTO captures(id,source_id,url,retrieved_at,sha256,byte_length,storage_path) '
                          'VALUES (?,?,?,?,?,?,?)', ('CAP-TEST',source,'https://example.org/scan','2026-09-04T23:00:00Z','test-sha',1,'scan'))
        rows = self.conn.execute('SELECT a.id,l.object_id FROM appearances a JOIN appearance_object_links l '
                                 'ON l.appearance_id=a.id ORDER BY a.locator').fetchall()
        self.manifest = dict(source_id=source, source_pdf_sha256='test-sha', entries=[
            dict(text_number=n, object_id=r['object_id'], appearance_id=r['id'], claims=[
                dict(field='dimensions', value_text='height 6 cm; diameter 12 cm', value_json={'height_cm':6,'diameter_cm':12},
                     locator='Register text %s' % n, notes='Checked historical register dimensions')]) for n,r in enumerate(rows,1)])
        self.path = self.root/'register.json';self.conn.commit()

    def tearDown(self):
        self.conn.close();self.tmp.cleanup()

    def apply(self):
        self.path.write_text(json.dumps(self.manifest))
        return apply_montgomery_register(self.conn,self.path)

    def test_all_forty_claims_replay_without_duplicates(self):
        self.assertEqual(self.apply()['claims_added'],40)
        self.assertEqual(self.apply()['claims_added'],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM claims').fetchone()[0],40)

    def test_wrong_last_appearance_rolls_back_entire_batch(self):
        self.manifest['entries'][-1]['object_id']='IBI-MISSING'
        with self.assertRaisesRegex(ValueError,'link mismatch'):self.apply()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM claims').fetchone()[0],0)

    def test_missing_entry_and_unregistered_scan_rejected(self):
        entry=self.manifest['entries'].pop()
        with self.assertRaisesRegex(ValueError,'1-40'):self.apply()
        self.manifest['entries'].append(entry);self.manifest['source_pdf_sha256']='different'
        with self.assertRaisesRegex(ValueError,'registered'):self.apply()
