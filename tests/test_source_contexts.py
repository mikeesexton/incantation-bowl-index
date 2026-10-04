import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.source_contexts import source_context_inventory


class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.conn = sqlite3.connect(':memory:'); self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        self.conn.executescript('''CREATE TABLE sources(id TEXT PRIMARY KEY,citation TEXT);
          CREATE TABLE captures(id TEXT PRIMARY KEY,source_id TEXT,sha256 TEXT,mime_type TEXT);
          CREATE TABLE document_assessments(id TEXT PRIMARY KEY,source_id TEXT,capture_id TEXT,
          document_sha256 TEXT,extraction_path TEXT,extraction_sha256 TEXT);''')
        self.conn.execute("INSERT INTO sources VALUES('SRC-1','Test scholar 2002')")
        self.conn.execute("INSERT INTO captures VALUES('CAP-TEST-1','SRC-1','sourcehash','application/pdf')")
        artifact = self.write('copy.txt', 'Original quotation <tag>\n')
        self.entry = dict(id='CTX-1',source_id='SRC-1',capture_id='CAP-TEST-1',
          assessment_id='DOC-1',source_sha256='sourcehash',reference='Manuscript A',
          kind='provided_translation',language='English',script=None,editor='Test scholar',
          locator='Test printed2/PDF3',source_copy_status='source_copy_checked',
          reviewed_by='Codex',reviewed_at='2026-10-04T08:00:00+00:00',notes='A tentative proposal.',
          artifact=artifact,pdf_pages=[3],rights_status='copyrighted',bundle_unit_id='CTX-1',
          editorial_annotations=[dict(substring='word',annotation='source deletion, not applied')])
        self.source_pdf = self.write('source.pdf', '%PDF-private-test-source')
        self.entry['source_sha256'] = self.source_pdf['sha256']
        self.conn.execute('UPDATE captures SET sha256=?',(self.source_pdf['sha256'],))
        unit=copy.deepcopy(self.entry);unit['content']='Original quotation <tag>';unit['pdf_page']=3
        self.bundle=self.write('bundle.json',json.dumps(dict(units=[unit],prior_contexts=[],source_pdf=self.source_pdf)))
        self.extraction=self.write('extraction.json',json.dumps(dict(current_contexts=self.bundle)))
        self.entry.update(checked_bundle=self.bundle,extraction=self.extraction)
        self.conn.execute('INSERT INTO document_assessments VALUES(?,?,?,?,?,?)',
          ('DOC-1','SRC-1','CAP-TEST-1',self.source_pdf['sha256'],self.extraction['path'],self.extraction['sha256']))
        self.registry={'schema_version':1,'entries':[self.entry]}
        self.save_registry()

    def write(self,name,content):
        p=self.root/name;p.write_text(content)
        return dict(path=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())

    def save_registry(self):
        (self.root/'registry.json').write_text(json.dumps(self.registry))

    def rows(self):
        return source_context_inventory(self.conn,{'CAP-TEST-1':'/api/private-captures/CAP-TEST-1'},
                                        self.root,'registry.json')

    def test_checked_copy_and_editorial_notes_are_retained_without_paths(self):
        row=self.rows()[0]
        self.assertEqual(row['content'],'Original quotation <tag>')
        self.assertEqual(row['source_url'],'/api/private-captures/CAP-TEST-1#page=3')
        self.assertEqual(row['notes'],'A tentative proposal.')
        self.assertEqual(row['editorial_annotations'],self.entry['editorial_annotations'])
        self.assertNotIn('artifact',row);self.assertNotIn('assessment_id',row)
        self.assertNotIn(str(self.root),json.dumps(row))

    def test_changed_copy_rejects_entire_inventory(self):
        (self.root/'copy.txt').write_text('Changed')
        with self.assertRaises(ValueError):self.rows()

    def test_source_capture_assignment_cannot_be_changed(self):
        self.conn.execute("UPDATE captures SET source_id='OTHER'")
        with self.assertRaises(ValueError):self.rows()

    def test_attribution_and_annotations_must_match_bound_check(self):
        for field,value in [('editor','Other scholar'),('notes','No uncertainty'),
                            ('editorial_annotations',[])]:
            original=self.entry[field];self.entry[field]=value;self.save_registry()
            with self.assertRaises(ValueError):self.rows()
            self.entry[field]=original

    def test_changed_assessment_binding_rejects(self):
        self.conn.execute("UPDATE document_assessments SET extraction_sha256='changed'")
        with self.assertRaises(ValueError):self.rows()

    def test_duplicate_units_or_invalid_pages_reject(self):
        self.registry['entries'].append(copy.deepcopy(self.entry));self.save_registry()
        with self.assertRaises(ValueError):self.rows()
        self.registry['entries'].pop();self.entry['pdf_pages']=[0];self.save_registry()
        with self.assertRaises(ValueError):self.rows()

    def test_path_escape_rejects_even_with_valid_hash(self):
        self.entry['artifact']['path']='../copy.txt';self.save_registry()
        with self.assertRaises(ValueError):self.rows()

    def test_unrelated_database_has_no_default_contexts(self):
        self.assertEqual(source_context_inventory(self.conn),[])

    def test_capture_hash_must_match_bound_review(self):
        self.conn.execute("UPDATE captures SET sha256='otherhash'")
        with self.assertRaises(ValueError):self.rows()

    def test_earlier_checked_pair_is_bound_to_current_bundle(self):
        review=dict(source_id='SRC-1',capture_id='CAP-TEST-1',source_pdf=self.source_pdf,
                    source_checked_English=self.entry['artifact'],locator=self.entry['locator'],
                    editor=self.entry['editor'],notes=self.entry['notes'])
        evidence=self.write('pair.json',json.dumps(review))
        bundle=self.write('bundle.json',json.dumps(dict(units=[],prior_contexts=[evidence,self.entry['artifact']],source_pdf=self.source_pdf)))
        extraction=self.write('extraction.json',json.dumps(dict(current_contexts=bundle)))
        self.entry.pop('bundle_unit_id');self.entry.update(checked_bundle=bundle,extraction=extraction,
                       pair_review=evidence,pair_review_field='source_checked_English')
        self.conn.execute('UPDATE document_assessments SET extraction_sha256=?',(extraction['sha256'],))
        self.save_registry();self.assertEqual(len(self.rows()),1)
        self.entry['kind']='transliteration';self.save_registry()
        with self.assertRaises(ValueError):self.rows()

    def test_changed_original_source_bytes_rejects_inventory(self):
        (self.root/'source.pdf').write_bytes(b'Changed source')
        with self.assertRaises(ValueError):self.rows()
