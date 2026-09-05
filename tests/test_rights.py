import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.rights import apply_rights_batch, media_evidence, media_fingerprint, current_media_reviews, rights_metrics
from bowl_index.public_export import export_public

class RightsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn, {'label':'Museum bowl','source':{'source_type':'museum_record','title':'Museum',
            'citation':'Museum catalogue','url':'https://example.org/object','rights_status':'public_domain'},
            'appearance':{'locator':'bowl 1','confidence':1,'raw':{'private':'PRIVATE_RAW_SENTINEL'}},
            'media':[{'url':'https://example.org/private.jpg','rights_status':'public_domain','notes':'PRIVATE_MEDIA_NOTES'}],
            'texts':[{'text_type':'translation','content':'PRIVATE_TRANSLATION','public_ok':False}]})
        self.conn.commit(); self.row=next(iter(media_evidence(self.conn).values()))
    def tearDown(self):
        self.conn.close();self.temp.cleanup()
    def batch(self,decision='approved',key='IBI-RIGHTS-1'):
        return {'schema_version':1,'reviewed_by':'Test reviewer','reviewed_at':'2026-09-04T23:00:00Z','entries':[{
            'review_id':key,'media_id':self.row['id'],'evidence_sha256':media_fingerprint(self.row),
            'public_reuse_decision':decision,'private_capture_status':'not_captured',
            'rights_statement':'Explicit test permission','rights_locator':'Test license statement',
            'attribution':'Test Museum','rationale':'Test only','followup':'Check the rights holder'}]}
    def output(self,path):
        return ''.join(p.read_text() for p in path.iterdir())
    def test_source_public_domain_does_not_approve_media(self):
        path=self.root/'public';manifest=export_public(self.conn,path)
        self.assertEqual(manifest['media_approved_rows'],0)
        for secret in ['private.jpg','PRIVATE_RAW_SENTINEL','PRIVATE_TRANSLATION','PRIVATE_MEDIA_NOTES']:
            self.assertNotIn(secret,self.output(path))
        self.assertEqual(rights_metrics(self.conn)['media_rights_assessed'],0)
    def test_approval_is_bound_to_current_evidence_and_replay_safe(self):
        batch=self.batch();self.assertEqual(apply_rights_batch(self.conn,batch)['changed'],1)
        self.assertEqual(apply_rights_batch(self.conn,batch)['changed'],0)
        path=self.root/'approved';self.assertEqual(export_public(self.conn,path)['media_approved_rows'],1)
        self.assertIn('https://example.org/private.jpg',self.output(path))
        self.conn.execute("UPDATE media SET url='https://example.org/replaced.jpg'");self.conn.commit()
        self.assertEqual(current_media_reviews(self.conn),{})
        path=self.root/'stale';self.assertEqual(export_public(self.conn,path)['media_approved_rows'],0)
        self.assertNotIn('replaced.jpg',self.output(path))
        with self.assertRaisesRegex(ValueError,'evidence changed'):apply_rights_batch(self.conn,batch)
    def test_latest_withhold_revokes_approval_without_erasing_it(self):
        apply_rights_batch(self.conn,self.batch())
        apply_rights_batch(self.conn,self.batch('withhold','IBI-RIGHTS-2'))
        self.assertEqual(export_public(self.conn,self.root/'revoked')['media_approved_rows'],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM media_rights_reviews').fetchone()[0],2)
        with self.assertRaises(sqlite3.IntegrityError):self.conn.execute('DELETE FROM media_rights_reviews')
    def test_unapproved_duplicate_url_blocks_an_approved_copy(self):
        apply_rights_batch(self.conn,self.batch())
        self.conn.execute('INSERT INTO media (id,object_id,source_id,media_type,url) VALUES (?,?,?,?,?)',
            ('MED-DUP',self.row['object_id'],self.row['source_id'],'image',self.row['url']));self.conn.commit()
        self.assertEqual(export_public(self.conn,self.root/'duplicate')['media_approved_rows'],0)
    def test_private_reference_in_allowed_metadata_aborts_export(self):
        self.conn.execute('UPDATE sources SET citation=?',(self.row['url'],));self.conn.commit()
        path=self.root/'leak'
        with self.assertRaisesRegex(ValueError,'private media/capture reference'):export_public(self.conn,path)
        self.assertFalse(path.exists())
        self.assertFalse(list(self.root.glob('.ibi-public-*')))
    def test_escaped_private_reference_is_detected_before_serialization(self):
        private = 'https://example.org/image?title="private"'
        self.conn.execute('UPDATE media SET url=?', (private,))
        self.conn.execute('UPDATE sources SET citation=?', (private,))
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, 'private media/capture reference'):
            export_public(self.conn, self.root/'escaped')

    def test_existing_destination_is_never_reused(self):
        path=self.root/'existing';path.mkdir();(path/'private.bin').write_bytes(b'private')
        with self.assertRaisesRegex(ValueError,'new destination'):export_public(self.conn,path)
        self.assertEqual((path/'private.bin').read_bytes(),b'private')
    def test_missing_rights_evidence_and_partial_batches_rejected(self):
        batch=self.batch();del batch['entries'][0]['rights_statement']
        with self.assertRaisesRegex(ValueError,'rights evidence'):apply_rights_batch(self.conn,batch)
        batch=self.batch();batch['entries'].append(dict(batch['entries'][0],media_id='ABSENT'))
        with self.assertRaisesRegex(ValueError,'absent media'):apply_rights_batch(self.conn,batch)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM media_rights_reviews').fetchone()[0],0)
    def test_unknown_rights_hold_is_not_a_completed_assessment(self):
        apply_rights_batch(self.conn,self.batch('needs_review'))
        self.assertEqual(rights_metrics(self.conn)['media_current_ledger_rows'],1)
        self.assertEqual(rights_metrics(self.conn)['media_rights_assessed'],0)
