import tempfile
import unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.state import compare_state, corpus_fingerprint, write_state

class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def candidate(self,label):
        add_candidate(self.conn,{'label':label,'source':{'source_type':'museum_record','title':'Museum',
            'citation':'Museum catalogue','url':'https://example.org/%s'%label},
            'appearance':{'locator':label,'confidence':1}})
        self.conn.commit()
    def test_unrecorded_before_a_baseline_exists(self):
        self.assertEqual(compare_state(self.conn,self.root)['status'],'unrecorded')
    def test_matches_after_recording_and_survives_a_read(self):
        self.candidate('bowl-1'); write_state(self.conn,self.root,'codex')
        list(self.conn.execute('SELECT * FROM objects'))
        result=compare_state(self.conn,self.root)
        self.assertEqual(result['status'],'match')
        self.assertEqual(result['recorded_by'],'codex')
        self.assertEqual(result['changed_tables'],[])
    def test_reports_which_tables_another_agent_changed(self):
        self.candidate('bowl-1'); write_state(self.conn,self.root,'codex')
        self.candidate('bowl-2')
        result=compare_state(self.conn,self.root)
        self.assertEqual(result['status'],'drifted')
        changed={row['table'] for row in result['changed_tables']}
        self.assertIn('objects',changed)
        objects=next(row for row in result['changed_tables'] if row['table']=='objects')
        self.assertEqual((objects['recorded_rows'],objects['current_rows']),(1,2))
    def test_edit_in_place_drifts_without_changing_row_counts(self):
        self.candidate('bowl-1'); write_state(self.conn,self.root,'codex')
        self.conn.execute("UPDATE objects SET label='relabelled'"); self.conn.commit()
        result=compare_state(self.conn,self.root)
        self.assertEqual(result['status'],'drifted')
        objects=next(row for row in result['changed_tables'] if row['table']=='objects')
        self.assertEqual((objects['recorded_rows'],objects['current_rows']),(1,1))
    def test_analyze_does_not_report_drift(self):
        self.candidate('bowl-1'); write_state(self.conn,self.root,'codex')
        self.conn.execute('ANALYZE'); self.conn.commit()
        self.assertEqual(compare_state(self.conn,self.root)['status'],'match')
    def test_fingerprint_is_stable_across_connections(self):
        self.candidate('bowl-1'); first=corpus_fingerprint(self.conn)['corpus_digest']
        self.conn.close(); self.conn=connect(self.root/'db.sqlite3')
        self.assertEqual(corpus_fingerprint(self.conn)['corpus_digest'],first)

if __name__=='__main__':
    unittest.main()
