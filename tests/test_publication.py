import sqlite3
import tempfile
import unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.public_export import export_public
from bowl_index.publication import (
    apply_publication_batch, current_text_reviews, publication_metrics, sync_public_ok,
    text_evidence, text_fingerprint,
)

class TextPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'Montgomery bowl','source':{'source_type':'book','title':'Nippur texts',
            'citation':'Montgomery 1913','url':'https://example.org/nippur','issued_year':1913,
            'rights_status':'public_domain'},
            'appearance':{'locator':'text 1','confidence':1},
            'texts':[{'text_type':'translation','content':'ANCIENT READING TEXT','public_ok':False,
                      'locator':'printed pp. 117-118'}]})
        self.conn.commit()
        self.text_id=next(iter(text_evidence(self.conn)))
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def entry(self,**over):
        row=text_evidence(self.conn)[self.text_id]
        e={'review_id':'IBI-TEXTPUB-1','text_id':self.text_id,'evidence_sha256':text_fingerprint(row),
           'rights_basis':'public_domain_expired','rights_locator':'US publication before 1930',
           'publication_decision':'approved','attribution':'Montgomery 1913',
           'editorial_status':'First-pass scan check; not specialist certified','rationale':'Out of copyright'}
        e.update(over); return e
    def batch(self,**over):
        return {'schema_version':1,'reviewed_by':'Test reviewer','reviewed_at':'2026-09-05T22:00:00+00:00',
                'entries':[self.entry(**over)]}
    def output(self,path):
        return ''.join(p.read_text() for p in path.iterdir())

    def test_approval_publishes_and_replays_as_a_noop(self):
        self.assertEqual(apply_publication_batch(self.conn,self.batch())['changed'],1)
        self.assertEqual(apply_publication_batch(self.conn,self.batch())['changed'],0)
        self.assertEqual(publication_metrics(self.conn)['texts_approved'],1)
        path=self.root/'pub'; export_public(self.conn,path)
        self.assertIn('ANCIENT READING TEXT',self.output(path))

    def test_public_domain_source_alone_does_not_publish(self):
        path=self.root/'pub'; export_public(self.conn,path)
        self.assertNotIn('ANCIENT READING TEXT',self.output(path))
        self.assertEqual(publication_metrics(self.conn)['texts_approved'],0)

    def test_a_later_revision_revokes_the_approval(self):
        apply_publication_batch(self.conn,self.batch())
        self.assertEqual(self.conn.execute('SELECT public_ok FROM texts').fetchone()[0],1)
        self.conn.execute("UPDATE texts SET content='CORRECTED READING TEXT'"); self.conn.commit()
        self.assertEqual(current_text_reviews(self.conn),{})
        sync_public_ok(self.conn)
        self.assertEqual(self.conn.execute('SELECT public_ok FROM texts').fetchone()[0],0)
        path=self.root/'pub'; export_public(self.conn,path)
        self.assertNotIn('CORRECTED READING TEXT',self.output(path))

    def test_stale_evidence_is_rejected(self):
        batch=self.batch(); self.conn.execute("UPDATE texts SET content='changed'"); self.conn.commit()
        with self.assertRaises(ValueError): apply_publication_batch(self.conn,batch)

    def test_approval_requires_a_basis_and_a_stated_editorial_status(self):
        for over in ({'rights_basis':'not_established'},{'rights_locator':' '},
                     {'attribution':''},{'editorial_status':''},{'rationale':''}):
            with self.assertRaises(ValueError): apply_publication_batch(self.conn,self.batch(**over))
        self.assertEqual(publication_metrics(self.conn)['texts_approved'],0)

    def test_unresolved_decision_requires_a_followup(self):
        with self.assertRaises(ValueError):
            apply_publication_batch(self.conn,self.batch(publication_decision='needs_review'))
        self.assertEqual(apply_publication_batch(self.conn,self.batch(
            publication_decision='needs_review',followup='Check the 1913 imprint'))['changed'],1)

    def test_reviews_are_append_only(self):
        apply_publication_batch(self.conn,self.batch())
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE text_publication_reviews SET publication_decision='withhold'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM text_publication_reviews')

    def test_reusing_a_review_id_with_a_changed_decision_is_rejected(self):
        apply_publication_batch(self.conn,self.batch())
        with self.assertRaises(ValueError):
            apply_publication_batch(self.conn,self.batch(rationale='Different reason'))


class AccessPointerTests(unittest.TestCase):
    """A withheld text must still tell a reader where to consult it."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'Segal bowl','source':{'source_type':'catalogue',
            'title':'British Museum catalogue','citation':'Segal 2000','url':'https://example.org/segal',
            'doi':'10.1234/segal','issued_year':2000,'rights_status':'copyrighted','access_status':'paywalled'},
            'appearance':{'locator':'no. 042A','confidence':1},
            'texts':[{'text_type':'translation','content':'COPYRIGHTED TRANSLATION','public_ok':False,
                      'locator':'text 42, p. 88'}]})
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def rows(self,name):
        import json
        path=self.root/'pub'
        if not path.exists(): export_public(self.conn,path)
        return [json.loads(l) for l in (path/(name+'.jsonl')).read_text().splitlines()]

    def test_withheld_text_keeps_citation_locator_and_link(self):
        row=self.rows('texts')[0]
        self.assertEqual(row['content_status'],'withheld_consult_the_edition')
        self.assertIsNone(row['content'])
        self.assertEqual(row['access_citation'],'Segal 2000')
        self.assertEqual(row['access_locator'],'text 42, p. 88')
        self.assertEqual(row['access_url'],'https://doi.org/10.1234/segal')
        self.assertEqual(row['access_status'],'paywalled')

    def test_withheld_content_is_absent_from_every_exported_file(self):
        self.rows('texts')
        blob=''.join(p.read_text() for p in (self.root/'pub').iterdir())
        self.assertNotIn('COPYRIGHTED TRANSLATION',blob)

    def test_editions_table_names_where_the_object_is_published(self):
        editions=self.rows('editions')
        self.assertEqual(len(editions),1)
        self.assertEqual(editions[0]['citation'],'Segal 2000')
        self.assertEqual(editions[0]['locator'],'no. 042A')
        self.assertEqual(editions[0]['access_url'],'https://doi.org/10.1234/segal')

    def test_a_link_is_withheld_rather_than_leaking_a_captured_url(self):
        self.conn.execute(
            "INSERT INTO captures(id,source_id,url,retrieved_at,mime_type,status_code,sha256,"
            "byte_length,storage_path,rights_status) SELECT 'CAP-1',id,'https://example.org/segal',"
            "'2026-09-05T00:00:00Z','text/html',200,'abc',1,'data/private/archive/ab/abc','unknown' "
            "FROM sources LIMIT 1")
        self.conn.execute("UPDATE sources SET doi=NULL"); self.conn.commit()
        row=self.rows('texts')[0]
        self.assertIsNone(row['access_url'])
        self.assertEqual(row['access_citation'],'Segal 2000')

if __name__=='__main__':
    unittest.main()
