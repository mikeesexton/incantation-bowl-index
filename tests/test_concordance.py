import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.concordance import apply_concordance_review, concordance_evidence, current_concordance_reviews, fingerprint
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.public_export import export_public


class ConcordanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / 'db'); migrate(self.conn)
        add_candidate(self.conn, dict(object_id='IBI-A', label='Edition bowl',
            source={'source_type':'book','title':'Montgomery test','citation':'Test edition'},
            appearance={'locator':'text 1'},
            identifiers=[{'scheme':'Montgomery 1913 text number','value':'1'}],
            claims=[{'field':'publication_register_identifier','value_text':'CBS 1','locator':'register 1'}]))
        add_candidate(self.conn, dict(object_id='IBI-B', label='Museum bowl',
            source={'source_type':'museum_record','title':'Penn test','citation':'Penn test',
                    'url':'https://collections.penn.museum/collections/object/123'},
            appearance={'locator':'Penn 123'},
            identifiers=[{'scheme':'Penn web object ID','value':'123'},
                         {'scheme':'collection designation','value':'B1'}]))
        self.conn.execute("INSERT INTO dedupe_candidates(id,object_a_id,object_b_id,score,status,method,rationale) "
                          "VALUES ('DED-TEST','IBI-A','IBI-B',1,'same_object','test','Previously reviewed')")
        self.conn.commit()
        self.entry=dict(review_id='IBI-CONC-TEST',object_id='IBI-A',text_number=1,penn_web_id='123',
            expected_evidence_sha256=fingerprint(concordance_evidence(self.conn,'IBI-A',1,'123')),
            status='confirmed',rationale='Explicit catalogue concordance.',observation={
                'url':'https://collections.penn.museum/collections/object/123',
                'observed_at':'2026-09-05T14:00:00Z','locator':'Details: Object Number; Other Number',
                'fields':{'Object Number':'B1','Other Number':'PBS III: 1 - Other Number'}})
        self.manifest=dict(schema_version=1,reviewed_by='Test reviewer',reviewed_at='2026-09-05T14:01:00Z',
            method='Visible page review',scope='Existing number concordance only',entries=[self.entry])
        self.path=self.root/'review.json'

    def tearDown(self):
        self.conn.close(); self.tmp.cleanup()

    def apply(self):
        self.path.write_text(json.dumps(self.manifest))
        return apply_concordance_review(self.conn,self.path)

    def test_replay_preserves_identity_and_immutable_evidence(self):
        before=[tuple(r) for r in self.conn.execute('SELECT * FROM dedupe_candidates')]
        self.assertEqual(self.apply()['changed'],1)
        self.assertEqual(self.apply()['changed'],0)
        self.assertEqual(before,[tuple(r) for r in self.conn.execute('SELECT * FROM dedupe_candidates')])
        self.assertEqual(len(current_concordance_reviews(self.conn)),1)
        saved=self.conn.execute('SELECT * FROM museum_concordance_reviews').fetchone()
        self.assertEqual(fingerprint(json.loads(saved['evidence_json'])),saved['evidence_sha256'])
        for action in ("UPDATE museum_concordance_reviews SET status='unresolved'",'DELETE FROM museum_concordance_reviews'):
            with self.assertRaises(sqlite3.IntegrityError):self.conn.execute(action)
            self.conn.rollback()

    def test_bad_observations_and_non_utc_rejected(self):
        for field,value in [('Object Number','B2'),('Other Number','PBS III: 2 - Other Number')]:
            with self.subTest(field=field):
                old=self.entry['observation']['fields'][field]
                self.entry['observation']['fields'][field]=value
                with self.assertRaises(ValueError):self.apply()
                self.entry['observation']['fields'][field]=old
        self.entry['observation']['url']='https://example.org/wrong'
        with self.assertRaisesRegex(ValueError,'URL mismatch'):self.apply()
        self.entry['observation']['url']='https://collections.penn.museum/collections/object/123'
        self.entry['observation']['observed_at']='2026-09-05T14:00:00'
        with self.assertRaisesRegex(ValueError,'UTC'):self.apply()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM museum_concordance_reviews').fetchone()[0],0)

    def test_late_invalid_entry_is_atomic_and_duplicate_id_rejected(self):
        second=copy.deepcopy(self.entry);second['review_id']='IBI-CONC-SECOND';second['penn_web_id']='999'
        self.manifest['entries'].append(second)
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM museum_concordance_reviews').fetchone()[0],0)
        second['review_id']=self.entry['review_id']
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.apply()

    def test_changed_claim_invalidates_and_altered_replay_rejected(self):
        self.apply()
        self.entry['rationale']='Changed rationale'
        with self.assertRaisesRegex(ValueError,'reused'):self.apply()
        self.conn.execute("UPDATE claims SET value_text='CBS 2'");self.conn.commit()
        self.assertEqual(current_concordance_reviews(self.conn),{})
        with self.assertRaisesRegex(ValueError,'changed'):self.apply()

    def test_split_identity_invalidates_review(self):
        self.apply()
        self.conn.execute("UPDATE dedupe_candidates SET status='different_objects'");self.conn.commit()
        self.assertEqual(current_concordance_reviews(self.conn),{})
        with self.assertRaisesRegex(ValueError,'absent'):self.apply()

    def test_latest_unresolved_review_does_not_resurrect_confirmed_review(self):
        self.apply()
        self.entry['review_id']='IBI-CONC-SECOND';self.entry['status']='unresolved'
        self.entry['rationale']='Later evidence requires review.'
        self.apply()
        self.assertEqual(next(iter(current_concordance_reviews(self.conn).values()))['status'],'unresolved')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM museum_concordance_reviews').fetchone()[0],2)

    def test_public_scaffold_omits_concordance_history(self):
        self.entry['rationale']='PRIVATE-CONCORDANCE-REVIEW-CANARY'
        self.apply()
        destination=self.root/'public'
        result=export_public(self.conn,destination)
        self.assertNotIn('museum_concordance_reviews',result['tables'])
        for path in destination.iterdir():
            self.assertNotIn('PRIVATE-CONCORDANCE-REVIEW-CANARY',path.read_text())
