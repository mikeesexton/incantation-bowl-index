import json, tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.projection import Projection
from bowl_index.publications import apply_publication_registry

class PublicationProjectionTests(unittest.TestCase):
    """"Which bowls does Isbell publish" must be answerable from the projection."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        for n in (1, 2):
            add_candidate(self.conn,{'label':'bowl %d'%n,'source':{'source_type':'article',
                'title':'Waller','citation':'Waller 2022','url':'https://example.org/w%d'%n},
                'appearance':{'locator':'p. %d'%n,'confidence':1},
                'identifiers':[{'scheme':'publication object key','value':'Isbell 1975::0%d'%n}]})
        self.conn.execute("INSERT INTO sources(id,source_type,title,citation) "
                          "VALUES ('SRC-ISBELL','book','Corpus','Isbell 1975')")
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def test_a_publication_lists_the_bowls_it_publishes(self):
        row = Projection(self.conn).table('publications')[0]
        self.assertEqual(row['publication_key'], 'Isbell 1975')
        self.assertEqual(row['objects'], 2)
        self.assertEqual(len(json.loads(row['object_ids'])), 2)

    def test_an_unregistered_key_says_so_rather_than_claiming_a_source(self):
        row = Projection(self.conn).table('publications')[0]
        self.assertEqual(row['resolution'], 'unregistered')
        self.assertIsNone(row['source_id'])

    def test_resolution_attaches_the_publication(self):
        apply_publication_registry(self.conn, {'schema_version':1,'reviewed_by':'Test',
            'reviewed_at':'2026-09-06T00:00:00+00:00','entries':[{
              'registry_id':'IBI-PUBREG-1','publication_key':'Isbell 1975',
              'source_id':'SRC-ISBELL','resolution':'resolved','basis':'Key names Isbell 1975'}]})
        row = Projection(self.conn).table('publications')[0]
        self.assertEqual((row['resolution'], row['source_id']), ('resolved', 'SRC-ISBELL'))

if __name__=='__main__':
    unittest.main()
