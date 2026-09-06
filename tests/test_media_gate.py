import json, tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.projection import Projection
from bowl_index.rights import apply_rights_batch, media_evidence, media_fingerprint

class MediaGateTests(unittest.TestCase):
    """The reading room renders whatever media the projection emits, so the
    projection is the only thing standing between an uncleared image and a page."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'photographed bowl','source':{'source_type':'museum_record',
            'title':'Museum','citation':'Museum record','url':'https://example.org/object',
            'rights_status':'public_domain'},
            'appearance':{'locator':'object 1','confidence':1},
            'media':[{'url':'https://example.org/bowl.jpg','media_type':'image',
                      'rights_status':'public_domain'}]})
        self.conn.commit()
        self.row=next(iter(media_evidence(self.conn).values()))

    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def approve(self, decision='approved'):
        return apply_rights_batch(self.conn, {'schema_version':1,'reviewed_by':'Test reviewer',
            'reviewed_at':'2026-09-06T00:00:00Z','entries':[{
              'review_id':'IBI-RIGHTS-1','media_id':self.row['id'],
              'evidence_sha256':media_fingerprint(self.row),
              'public_reuse_decision':decision,'private_capture_status':'not_captured',
              'rights_statement':'Museum states public domain','rights_locator':'Rights page',
              'attribution':'Test Museum','rationale':'Checked the rights page',
              'followup':'None' if decision=='needs_review' else None}]})

    def test_a_public_domain_source_does_not_put_an_image_on_the_page(self):
        self.assertEqual(Projection(self.conn).table('media'), [])
        self.assertNotIn('bowl.jpg', json.dumps(Projection(self.conn).tables()))

    def test_a_completed_approval_releases_the_image_with_its_attribution(self):
        self.approve()
        media = Projection(self.conn).table('media')
        self.assertEqual(len(media), 1)
        self.assertEqual(media[0]['url'], 'https://example.org/bowl.jpg')
        self.assertEqual(media[0]['attribution'], 'Test Museum')
        self.assertEqual(media[0]['media_type'], 'image')

    def test_withholding_keeps_it_off_the_page(self):
        self.approve('withhold')
        self.assertEqual(Projection(self.conn).table('media'), [])

if __name__=='__main__':
    unittest.main()
