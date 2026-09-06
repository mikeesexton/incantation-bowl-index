import json, tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.projection import PROJECTION_COLUMNS, TABLE_NAMES, Projection
from bowl_index.public_export import export_public
from bowl_index.publication import apply_publication_batch, text_evidence, text_fingerprint

class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'Segal bowl','source':{'source_type':'catalogue',
            'title':'BM catalogue','citation':'Segal 2000','url':'https://example.org/segal',
            'doi':'10.1234/segal','issued_year':2000,'rights_status':'copyrighted',
            'access_status':'paywalled'},
            'appearance':{'locator':'no. 042A','confidence':1},
            'media':[{'url':'https://example.org/bowl.jpg','rights_status':'copyrighted'}],
            'texts':[{'text_type':'translation','content':'WITHHELD TRANSLATION',
                      'public_ok':False,'locator':'text 42, p. 88'}]})
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def rows(self, name):
        return Projection(self.conn).table(name)

    # -- the gates -----------------------------------------------------------

    def test_withheld_text_content_is_never_emitted(self):
        row=self.rows('texts')[0]
        self.assertEqual(row['content_status'],'withheld_consult_the_edition')
        self.assertIsNone(row['content'])

    def test_a_withheld_text_still_carries_citation_and_locator(self):
        row=self.rows('texts')[0]
        self.assertEqual(row['access_citation'],'Segal 2000')
        self.assertEqual(row['access_locator'],'text 42, p. 88')
        self.assertEqual(row['access_url'],'https://doi.org/10.1234/segal')

    def test_unapproved_media_is_never_emitted(self):
        self.assertEqual(self.rows('media'),[])
        blob=json.dumps(Projection(self.conn).tables(), ensure_ascii=False)
        self.assertNotIn('bowl.jpg', blob)

    def test_a_link_matching_a_private_capture_is_withheld(self):
        self.conn.execute(
            "INSERT INTO captures(id,source_id,url,retrieved_at,mime_type,status_code,sha256,"
            "byte_length,storage_path,rights_status) SELECT 'CAP-1',id,'https://example.org/segal',"
            "'2026-09-05T00:00:00Z','text/html',200,'abc',1,'data/private/archive/ab/abc','unknown' "
            "FROM sources LIMIT 1")
        self.conn.execute("UPDATE sources SET doi=NULL"); self.conn.commit()
        self.assertIsNone(self.rows('texts')[0]['access_url'])

    def test_the_guard_rejects_a_leaked_private_reference(self):
        projection=Projection(self.conn)
        projection.forbidden.add('SENSITIVE')
        with self.assertRaises(ValueError):
            projection.guard('texts',[{'id':'x','note':'contains SENSITIVE path'}])

    def test_approving_a_text_publishes_it(self):
        row=text_evidence(self.conn)[self.rows('texts')[0]['id']]
        apply_publication_batch(self.conn,{'schema_version':1,'reviewed_by':'Test',
            'reviewed_at':'2026-09-06T00:00:00+00:00','entries':[{
              'review_id':'IBI-TEXTPUB-1','text_id':row['id'],
              'evidence_sha256':text_fingerprint(row),'rights_basis':'own_work',
              'rights_locator':'Test','publication_decision':'approved',
              'attribution':'Test','editorial_status':'Test','rationale':'Test'}]})
        after=self.rows('texts')[0]
        self.assertEqual(after['content_status'],'included')
        self.assertEqual(after['content'],'WITHHELD TRANSLATION')

    # -- the hinge -----------------------------------------------------------

    def test_every_declared_table_builds_with_its_declared_columns(self):
        tables=Projection(self.conn).tables()
        self.assertEqual(set(tables), set(TABLE_NAMES))
        for name, rows in tables.items():
            for row in rows:
                self.assertEqual(set(row), set(PROJECTION_COLUMNS[name]),
                                 '%s row does not match its declared columns' % name)

    def test_the_api_projection_and_the_file_export_are_identical(self):
        """The publish-safety guarantee: one gating implementation, not two.

        If these ever diverge, the local console and a published export are no
        longer the same bytes, and the export's gates stop guaranteeing the
        console's behaviour.
        """
        tables=Projection(self.conn).tables()
        destination=self.root/'export'
        export_public(self.conn, destination)
        for name, rows in tables.items():
            written=[json.loads(line) for line in
                     (destination/(name+'.jsonl')).read_text(encoding='utf-8').splitlines()]
            self.assertEqual(written, rows, '%s differs between the API and the export' % name)

    def test_the_manifest_reports_the_gates(self):
        manifest=export_public(self.conn, self.root/'export2')
        self.assertEqual(manifest['texts_included_rows'],0)
        self.assertEqual(manifest['texts_withheld_rows'],1)
        self.assertEqual(manifest['media_approved_rows'],0)
        self.assertEqual(manifest['media_withheld_rows'],1)
        self.assertEqual(manifest['license'],'CC-BY-4.0')

if __name__=='__main__':
    unittest.main()
