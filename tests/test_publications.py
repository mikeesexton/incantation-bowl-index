import tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.publications import (
    apply_publication_registry, publication_coverage, publication_key,
    publication_keys, publication_object_counts, unresolved_publication_keys,
)

class PublicationRegistryTests(unittest.TestCase):
    """A publication key must resolve to the publication it designates."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'Isbell bowl','source':{'source_type':'article','title':'Waller 2022',
            'citation':'Waller 2022','url':'https://example.org/w'},
            'appearance':{'locator':'p. 153','confidence':1},
            'identifiers':[{'scheme':'publication object key','value':'Isbell 1975::08'}]})
        self.conn.execute("INSERT INTO sources(id,source_type,title,citation) "
                          "VALUES ('SRC-ISBELL','book','Corpus of the Aramaic Incantation Bowls','Isbell 1975')")
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def batch(self,**over):
        e={'registry_id':'IBI-PUBREG-1','publication_key':'Isbell 1975','source_id':'SRC-ISBELL',
           'resolution':'resolved','basis':'Key names Isbell and 1975'}
        e.update(over)
        return {'schema_version':1,'reviewed_by':'Test reviewer',
                'reviewed_at':'2026-09-06T01:00:00+00:00','entries':[e]}

    def test_the_key_is_the_publication_not_the_object(self):
        self.assertEqual(publication_key('Isbell 1975::08'),'Isbell 1975')
        self.assertEqual(publication_key('Ford 2023 popularity bowl'),'Ford 2023')
        self.assertEqual(publication_keys(self.conn),{'Isbell 1975':1})

    def test_an_unregistered_key_is_reported(self):
        self.assertEqual(unresolved_publication_keys(self.conn),['Isbell 1975'])
        apply_publication_registry(self.conn,self.batch())
        self.assertEqual(unresolved_publication_keys(self.conn),[])

    def test_resolution_counts_objects_under_the_publication(self):
        apply_publication_registry(self.conn,self.batch())
        cov=publication_coverage(self.conn)
        self.assertEqual(cov['publication_keys_resolved'],1)
        self.assertEqual(cov['objects_under_a_resolved_publication'],1)
        row=publication_object_counts(self.conn)[0]
        self.assertEqual((row['resolution'],row['source_id']),('resolved','SRC-ISBELL'))

    def test_aliases_and_multiple_publications_count_distinct_records(self):
        from bowl_index.acquisitions import acquisition_rows, acquisition_metrics
        original = self.conn.execute(
            "SELECT object_id, source_id FROM identifiers WHERE scheme='publication object key'"
        ).fetchone()
        for identifier, value in [('ID-ALIAS', 'Isbell 1975::8'), ('ID-OTHER', 'Other 2000::1')]:
            self.conn.execute(
                "INSERT INTO identifiers(id,object_id,source_id,scheme,value,normalized_value) VALUES (?,?,?,?,?,?)",
                (identifier, original['object_id'], original['source_id'], 'publication object key', value, value))
        self.conn.commit()
        apply_publication_registry(self.conn, self.batch())
        apply_publication_registry(self.conn, self.batch(
            registry_id='IBI-PUBREG-2', publication_key='Other 2000'))
        self.assertEqual(publication_keys(self.conn), {'Isbell 1975': 1, 'Other 2000': 1})
        coverage = publication_coverage(self.conn)
        self.assertEqual(coverage['objects_under_a_publication_key'], 1)
        self.assertEqual(coverage['objects_under_a_resolved_publication'], 1)
        row = next(r for r in acquisition_rows(self.conn) if r['id'] == 'SRC-ISBELL')
        self.assertEqual(row['published_objects'], 1)
        # Moving the second key to a different publication must still count one
        # unique candidate in the overall missing-PDF metric.
        apply_publication_registry(self.conn, self.batch(
            registry_id='IBI-PUBREG-3', publication_key='Other 2000',
            source_id=original['source_id']))
        self.assertEqual(acquisition_metrics(self.conn)[
            'objects_depending_on_a_publication_without_pdf'], 1)

    def test_reporting_source_is_untouched_by_resolution(self):
        apply_publication_registry(self.conn,self.batch())
        reporter=self.conn.execute(
            "SELECT s.title FROM identifiers i JOIN sources s ON s.id=i.source_id "
            "WHERE i.scheme='publication object key'").fetchone()[0]
        self.assertEqual(reporter,'Waller 2022')   # who reported it, not what it designates

    def test_resolution_requires_an_existing_source(self):
        with self.assertRaises(ValueError):
            apply_publication_registry(self.conn,self.batch(source_id='SRC-NOPE'))
        with self.assertRaises(ValueError):
            apply_publication_registry(self.conn,self.batch(source_id=None))

    def test_unresolved_requires_a_precise_blocker(self):
        with self.assertRaises(ValueError):
            apply_publication_registry(self.conn,self.batch(resolution='unresolved',source_id=None))
        out=apply_publication_registry(self.conn,self.batch(
            resolution='unresolved',source_id=None,blocker='Series number unverified'))
        self.assertEqual(out['publication_keys_resolved'],0)

    def test_an_unknown_key_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_publication_registry(self.conn,self.batch(publication_key='Nobody 1900'))

    def test_replay_is_a_noop_and_history_is_append_only(self):
        self.assertEqual(apply_publication_registry(self.conn,self.batch())['changed'],1)
        self.assertEqual(apply_publication_registry(self.conn,self.batch())['changed'],0)
        with self.assertRaises(ValueError):
            apply_publication_registry(self.conn,self.batch(basis='A different reason'))
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM publication_registry")

if __name__=='__main__':
    unittest.main()
