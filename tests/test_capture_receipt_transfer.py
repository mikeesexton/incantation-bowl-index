import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.archive import import_capture_receipts


class CaptureReceiptTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        schema = ('CREATE TABLE captures (id TEXT PRIMARY KEY,source_id TEXT,url TEXT,'
                  'retrieved_at TEXT,mime_type TEXT,status_code INTEGER,sha256 TEXT,'
                  'byte_length INTEGER,storage_path TEXT,rights_status TEXT,headers_json TEXT);'
                  'CREATE TABLE sources (id TEXT PRIMARY KEY);')
        self.conn.executescript(schema)
        self.conn.execute("INSERT INTO sources VALUES ('SRC-1')")
        self.conn.commit()
        self.origin = self.root / 'origin.sqlite3'
        row = dict(id='CAP-1',source_id='SRC-1',url='https://example.org/edition.pdf',
                   retrieved_at='2026-10-01T10:00:00+00:00',mime_type='application/pdf',
                   status_code=200,sha256=hashlib.sha256(b'%PDF-test').hexdigest(),
                   byte_length=9,storage_path='sha256/test',rights_status='unknown',
                   headers_json='{"original":"headers"}')
        with sqlite3.connect(self.origin) as db:
            db.executescript(schema)
            db.execute('INSERT INTO captures VALUES (' + ','.join('?' for _ in row) + ')',list(row.values()))
        archive = self.root / 'data/private/archive/sha256'
        archive.mkdir(parents=True)
        (archive / 'test').write_bytes(b'%PDF-test')
        (self.root / 'receipt.json').write_text(json.dumps(row))
        (self.root / 'robots.txt').write_text('User-agent: *\nDisallow:\n')
        sha = lambda name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
        self.manifest = dict(schema_version=1,reviewed_by='Codex',
                             reviewed_at='2026-10-02T10:00:00+00:00',
                             origin_database_path='origin.sqlite3',origin_database_sha256=sha('origin.sqlite3'),
                             entries=[dict(receipt_path='receipt.json',receipt_sha256=sha('receipt.json'),
                                           robots_path='robots.txt',robots_sha256=sha('robots.txt'),
                                           robots_url='https://example.org/robots.txt',robots_status_code=200,
                                           retrieval_basis='Earlier lawful project retrieval, no new network request')])

    def test_transfer_preserves_original_receipt_and_replays(self):
        self.assertEqual(import_capture_receipts(self.conn,self.manifest,self.root)['changed'],1)
        self.assertEqual(dict(self.conn.execute('SELECT * FROM captures').fetchone()),
                         json.loads((self.root/'receipt.json').read_text()))
        result=import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual((result['changed'],result['unchanged'],result['network_requests']),(0,1,0))

    def test_changed_archive_rejects_without_writing(self):
        (self.root/'data/private/archive/sha256/test').write_bytes(b'%PDF-changed')
        with self.assertRaises(ValueError): import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM captures').fetchone()[0],0)

    def test_changed_receipt_or_origin_cannot_rewrite_retrieval(self):
        row=json.loads((self.root/'receipt.json').read_text());row['url']='https://other.example/edition.pdf'
        (self.root/'receipt.json').write_text(json.dumps(row))
        self.manifest['entries'][0]['receipt_sha256']=hashlib.sha256((self.root/'receipt.json').read_bytes()).hexdigest()
        with self.assertRaises(ValueError): import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM captures').fetchone()[0],0)

    def test_entire_batch_validated_before_append(self):
        self.manifest['entries'].append(dict(self.manifest['entries'][0]))
        with self.assertRaises(ValueError): import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM captures').fetchone()[0],0)

    def test_original_robots_prohibition_rejects(self):
        (self.root/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
        self.manifest['entries'][0]['robots_sha256']=hashlib.sha256((self.root/'robots.txt').read_bytes()).hexdigest()
        with self.assertRaises(ValueError): import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM captures').fetchone()[0],0)

    def test_existing_capture_cannot_be_overwritten(self):
        import_capture_receipts(self.conn,self.manifest,self.root)
        self.conn.execute("UPDATE captures SET source_id='OTHER' WHERE id='CAP-1'")
        self.conn.commit()
        with self.assertRaises(ValueError): import_capture_receipts(self.conn,self.manifest,self.root)
        self.assertEqual(self.conn.execute('SELECT source_id FROM captures').fetchone()[0],'OTHER')
