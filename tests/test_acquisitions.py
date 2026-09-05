import tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.archive import capture_file
from bowl_index.acquisitions import acquisition_metrics, acquisition_rows, write_acquisition_report

class AcquisitionTests(unittest.TestCase):
    """A citation is not the document. The register must keep them apart."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        add_candidate(self.conn,{'label':'bowl','source':{'source_type':'catalogue','title':'Segal 2000',
            'citation':'Segal 2000','url':'https://example.org/segal'},
            'appearance':{'locator':'no. 1','confidence':1},
            'claims':[{'field':'current_location','value_text':'British Museum','locator':'p. 1'}]})
        self.conn.commit()
        self.sid=self.conn.execute("SELECT id FROM sources").fetchone()[0]
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def test_a_cited_source_is_not_a_held_document(self):
        row=acquisition_rows(self.conn)[0]
        self.assertFalse(row['held'])
        self.assertEqual(acquisition_metrics(self.conn)['sources_with_a_held_document'],0)
        self.assertGreater(row['priority'],0)   # it has dependants, so it is wanted

    def test_depositing_the_document_moves_it_to_held(self):
        doc=self.root/'segal.pdf'; doc.write_bytes(b'%PDF-1.4 scan')
        capture_file(self.conn, doc, source_id=self.sid, archive_root=self.root/'archive')
        row=acquisition_rows(self.conn)[0]
        self.assertTrue(row['held'])
        self.assertEqual(row['how'],'deposit')
        self.assertEqual(acquisition_metrics(self.conn)['sources_with_a_held_document'],1)

    def test_a_source_nothing_depends_on_is_not_on_the_want_list(self):
        self.conn.execute("INSERT INTO sources(id,source_type,title,citation) "
                          "VALUES ('SRC-IDLE','book','Unused','Unused 1900')")
        self.conn.commit()
        self.assertEqual(acquisition_metrics(self.conn)['sources_wanted_with_dependants'],1)

    def test_the_report_names_the_want_list_and_the_deposit_command(self):
        path=self.root/'acq.md'; write_acquisition_report(self.conn,path)
        text=path.read_text(encoding='utf-8')
        self.assertIn('Segal 2000',text)
        self.assertIn('ibi deposit',text)
        self.assertIn('never committed',text)

if __name__=='__main__':
    unittest.main()
