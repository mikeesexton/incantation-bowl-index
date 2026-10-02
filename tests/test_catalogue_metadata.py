import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bowl_index.catalogue_metadata import apply_catalogue_metadata
from bowl_index.db import connect, migrate
from bowl_index.export import export_all
from bowl_index.ingest import add_source, add_candidate
from bowl_index.state import corpus_fingerprint


class CatalogueMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = connect(self.root / 'test.sqlite3')
        migrate(self.conn)
        add_source(self.conn, {'id': 'SRC-TEST', 'source_type': 'book', 'title': 'Edition', 'citation': 'Edition'})
        self.record = {'source_id': 'SRC-TEST', 'label': 'Bowl 4: 1042',
                       'appearance': {'locator': 'Bowl 4 (1042), p. 152'},
                       'identifiers': [{'scheme': 'collection designation', 'value': 'Museum 1042'}],
                       'claims': [{'field': 'current_or_reported_collection', 'value_text': 'Museum 1042'}]}
        self.oid = add_candidate(self.conn, self.record)
        self.conn.commit()
        self.evidence = self.root / 'evidence.json'
        self.evidence.write_text('{"finding":"heading checked"}')

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def manifest(self):
        entries = []
        for table, changes in [('objects', {'label': 'Bowl 4: 1402'}),
                               ('appearances', {'locator': 'Bowl 4 (1402), p. 152'}),
                               ('identifiers', {'value': 'Museum 1402', 'normalized_value': 'museum1402'}),
                               ('claims', {'value_text': 'Museum 1402', 'locator': 'Bowl 4 (1402), p. 152'})]:
            row = dict(self.conn.execute('SELECT * FROM ' + table).fetchone())
            entries.append({'id': 'CORR-' + table, 'target_table': table, 'source_id': 'SRC-TEST',
                            'before': row, 'changes': changes, 'rationale': 'Correct a copied catalogue number from the held heading.'})
        return {'schema_version': 1, 'reviewed_by': 'Test reviewer', 'reviewed_at': '2026-10-01T20:00:00Z',
                'evidence_path': 'evidence.json', 'evidence_sha256': hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
                'entries': entries}

    def test_repair_replay_preserves_identity_and_immutable_private_history(self):
        manifest = self.manifest()
        links = [dict(x) for x in self.conn.execute('SELECT * FROM appearance_object_links')]
        self.assertEqual(apply_catalogue_metadata(self.conn, manifest, self.root)['applied'], 4)
        self.assertEqual(apply_catalogue_metadata(self.conn, manifest, self.root)['unchanged'], 4)
        self.assertEqual(links, [dict(x) for x in self.conn.execute('SELECT * FROM appearance_object_links')])
        history = self.conn.execute("SELECT * FROM catalogue_metadata_corrections WHERE target_table='objects'").fetchone()
        self.assertEqual(json.loads(history['before_json'])['label'], 'Bowl 4: 1042')
        self.assertEqual(json.loads(history['after_json'])['label'], 'Bowl 4: 1402')
        for action in ["UPDATE catalogue_metadata_corrections SET rationale='changed'", 'DELETE FROM catalogue_metadata_corrections']:
            with self.assertRaises(sqlite3.IntegrityError):
                self.conn.execute(action)
            self.conn.rollback()
        exported = export_all(self.conn, self.root / 'export')
        self.assertEqual(exported['tables']['catalogue_metadata_corrections']['redacted_catalogue_snapshots'], 4)
        for line in (self.root / 'export/catalogue_metadata_corrections.jsonl').read_text().splitlines():
            self.assertIsNone(json.loads(line)['before_json'])

    def test_original_manifest_replay_cannot_restore_bad_catalogue_data(self):
        apply_catalogue_metadata(self.conn, self.manifest(), self.root)
        before = corpus_fingerprint(self.conn)['corpus_digest']
        self.assertEqual(add_candidate(self.conn, copy.deepcopy(self.record)), self.oid)
        self.conn.commit()
        self.assertEqual(corpus_fingerprint(self.conn)['corpus_digest'], before)

    def test_institution_repair_retains_original_and_blocks_stale_import(self):
        manifest = self.manifest()
        entry = next(x for x in manifest['entries'] if x['target_table'] == 'identifiers')
        entry['changes']['assigning_body'] = 'Correct institution'
        manifest['entries'] = [entry]
        self.assertEqual(apply_catalogue_metadata(self.conn, manifest, self.root)['applied'], 1)
        current = self.conn.execute('SELECT * FROM identifiers').fetchone()
        self.assertEqual(current['assigning_body'], 'Correct institution')
        self.assertEqual(current['source_id'], entry['before']['source_id'])
        history = self.conn.execute('SELECT * FROM catalogue_metadata_corrections').fetchone()
        self.assertEqual(json.loads(history['before_json']), entry['before'])
        before = corpus_fingerprint(self.conn)['corpus_digest']
        self.assertEqual(apply_catalogue_metadata(self.conn, manifest, self.root)['unchanged'], 1)
        self.assertEqual(add_candidate(self.conn, copy.deepcopy(self.record)), self.oid)
        self.conn.commit()
        self.assertEqual(corpus_fingerprint(self.conn)['corpus_digest'], before)

    def test_stale_evidence_or_row_is_rejected(self):
        manifest = self.manifest()
        self.conn.execute("UPDATE objects SET label='Later edit'")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, 'catalogue evidence changed'):
            apply_catalogue_metadata(self.conn, manifest, self.root)
        self.evidence.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'correction evidence changed'):
            apply_catalogue_metadata(self.conn, manifest, self.root)

    def test_failed_batch_rolls_back_all_repairs(self):
        manifest = self.manifest()
        manifest['entries'][-1]['before']['value_text'] = 'Stale claim'
        with self.assertRaisesRegex(ValueError, 'catalogue evidence changed'):
            apply_catalogue_metadata(self.conn, manifest, self.root)
        self.assertEqual(self.conn.execute('SELECT label FROM objects').fetchone()[0], 'Bowl 4: 1042')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM catalogue_metadata_corrections').fetchone()[0], 0)

    def test_identity_scholarly_and_unattributed_changes_are_rejected(self):
        for table, changes in [('objects', {'record_status': 'merged'}), ('appearances', {'source_id': 'OTHER'}),
                               ('claims', {'certainty': 'certain'})]:
            manifest = self.manifest()
            manifest['entries'] = [x for x in manifest['entries'] if x['target_table'] == table]
            manifest['entries'][0]['changes'] = changes
            with self.assertRaisesRegex(ValueError, 'only catalogue pointer fields'):
                apply_catalogue_metadata(self.conn, manifest, self.root)
        manifest = self.manifest()
        manifest['entries'][0]['source_id'] = 'UNLINKED'
        with self.assertRaisesRegex(ValueError, 'linked source evidence'):
            apply_catalogue_metadata(self.conn, manifest, self.root)
