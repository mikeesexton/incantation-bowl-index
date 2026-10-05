import copy
import json
import tempfile
import unittest
from pathlib import Path

from bowl_index.market import market_ledger, market_listings, listing_price
from bowl_index.market_results import listing_fingerprint, record_result_link, result_records
from bowl_index.market_intake import fingerprint
from bowl_index.market_monitor import _sha256
import test_market


class MarketResultTests(unittest.TestCase):
    def setUp(self):
        # Reuse the corpus fixture without inheriting/rerunning its test methods.
        self.fixture = test_market.MarketLedgerTests(); self.fixture.setUp()
        self.conn = self.fixture.conn; self.root = self.fixture.root / 'market'
        self.root.mkdir()
        self.body = b'''<input id="lot-is-ended" value="true" />
<time datetime='2026-10-04T12-00-00Z'>04 Oct 2026 13:00 BST</time>
<span id="closed-price" class="amount">300</span><span class="currency closed-currency"> GBP</span>'''
        sha = _sha256(self.body); (self.root/'raw').mkdir(); (self.root/'raw'/sha).write_bytes(self.body)
        self.result = {'url':'https://example.org/closed-lot', 'final_url':'https://example.org/closed-lot',
            'lot':'the-saleroom/uuid', 'observed_at':'2026-10-05T12:00:00Z',
            'sale_at':'2026-10-04T12:00:00Z', 'outcome':'sold', 'hammer_text':'300 GBP',
            'price_basis':"hammer price as shown by the platform; excludes buyer's premium", 'raw_sha256':sha}
        (self.root/'results').mkdir(); (self.root/'results/first.jsonl').write_text(json.dumps(self.result)+'\n')
        (self.root/'leads').mkdir(); (self.root/'leads/first.jsonl').write_text(json.dumps({
            'url':self.result['url'],'source_monitor_id':'the-saleroom','platform_lot_id':'uuid',
            'observed_at':'2026-10-04T00:00:00Z','house':'Apollo','lot_number':'1419'})+'\n')
        rows=market_listings(self.conn,today='2026-10-05')
        self.row=next(r for r in rows if r['source_title']=='Apollo lot 1419')
        self.manifest={'schema_version':1,'reviewer':'Source comparison','reviewed_at':'2026-10-05T12:00:00Z',
            'rationale':'Compared house, complete date and lot number on both platform records.',
            'quantity_text':'three bowls','result_fingerprint':fingerprint(self.result),
            'listings':[{k:self.row[k] for k in ('object_id','source_id','event_id')}]}
        self.manifest['listings'][0]['listing_fingerprint']=listing_fingerprint(self.row)

    def tearDown(self):
        self.fixture.tearDown()

    def test_link_updates_all_derived_views_without_writing_or_erasing_offer(self):
        before = self.conn.total_changes; original=copy.deepcopy(self.row)
        self.assertEqual(record_result_link(self.root,self.manifest,[self.row])['recorded'],1)
        self.assertTrue(record_result_link(self.root,self.manifest,[self.row])['replay'])
        ledger=market_ledger(self.conn,today='2026-10-05',monitor_dir=self.root)
        row=next(r for r in ledger['listings'] if r['event_id']==self.row['event_id'])
        self.assertEqual(row['status'],'sold');self.assertEqual(row['recorded_status'],'offered')
        self.assertEqual(row['event_type'],'offer');self.assertEqual(row['claims'],original['claims'])
        self.assertIn('Whole lot (three bowls): 300 GBP hammer',listing_price(row))
        self.assertIn("excludes buyer's premium",listing_price(row))
        self.assertEqual(ledger['metrics']['by_status']['sold'],2)
        self.assertNotIn(row,ledger['gaps']['offered_without_outcome'])
        self.assertEqual(ledger['result_followups'],[]);self.assertEqual(ledger['result_link_issues'],[])
        self.assertEqual(self.conn.total_changes,before)
        self.assertEqual(next(r for r in market_listings(self.conn,today='2026-10-05') if r['event_id']==self.row['event_id']),original)
        self.assertEqual(result_records(self.root),[self.result])

    def test_unlinked_results_are_explicit_followups_not_heuristic_overrides(self):
        ledger=market_ledger(self.conn,today='2026-10-05',monitor_dir=self.root)
        row=next(r for r in ledger['listings'] if r['event_id']==self.row['event_id'])
        self.assertEqual(row['status'],'offered')
        self.assertEqual(len(ledger['result_followups']),1)
        self.assertNotIn('result_observation',row)

    def test_full_sale_scope_rejects_reused_lot_other_house_or_unknown_date(self):
        for field,value in [('date','2025-10-04'),('date',None),('house','Apollo Other Auction'),('locator','lot 14190')]:
            row={**self.row,field:value}; m=copy.deepcopy(self.manifest)
            m['listings'][0]['listing_fingerprint']=listing_fingerprint(row)
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                record_result_link(self.root,m,[row])
        self.assertFalse((self.root/'result-links').exists())

    def test_batch_stale_target_or_tampered_archive_creates_no_receipt(self):
        m=copy.deepcopy(self.manifest);m['listings'].append({**m['listings'][0],'event_id':'unknown'})
        with self.assertRaises(ValueError):record_result_link(self.root,m,[self.row])
        m=copy.deepcopy(self.manifest);m['listings'][0]['listing_fingerprint']='old'
        with self.assertRaises(ValueError):record_result_link(self.root,m,[self.row])
        (self.root/'raw'/self.result['raw_sha256']).write_bytes(b'changed')
        with self.assertRaises(ValueError):record_result_link(self.root,self.manifest,[self.row])
        self.assertFalse((self.root/'result-links').exists())
        (self.root/'raw'/self.result['raw_sha256']).write_bytes(self.body)
        bad={**self.result,'price_basis':None}
        (self.root/'results/second.jsonl').write_text(json.dumps(bad)+'\n')
        with self.assertRaises(ValueError):record_result_link(self.root,{**self.manifest,'result_fingerprint':fingerprint(bad)},[self.row])
        self.assertFalse((self.root/'result-links').exists())

    def test_changed_offer_invalidates_current_link_and_preserves_receipt(self):
        record_result_link(self.root,self.manifest,[self.row])
        self.conn.execute('UPDATE events SET details=? WHERE id=?',('Changed source wording',self.row['event_id']))
        ledger=market_ledger(self.conn,today='2026-10-05',monitor_dir=self.root)
        row=next(r for r in ledger['listings'] if r['event_id']==self.row['event_id'])
        self.assertEqual(row['status'],'offered');self.assertEqual(len(ledger['result_link_issues']),1)
        self.assertEqual(len(list((self.root/'result-links').glob('*.json'))),1)
        self.assertEqual(len(ledger['result_followups']),1)

    def test_unsold_result_and_result_receipt_wording_validation(self):
        body=self.body.replace(b'>300<',b'>Passed<');sha=_sha256(body)
        (self.root/'raw'/sha).write_bytes(body)
        r={**self.result,'raw_sha256':sha,'outcome':'passed','hammer_text':'Passed'}
        (self.root/'results/first.jsonl').write_text(json.dumps(r)+'\n')
        m={**self.manifest,'result_fingerprint':fingerprint(r)}
        record_result_link(self.root,m,[self.row])
        ledger=market_ledger(self.conn,today='2026-10-05',monitor_dir=self.root)
        self.assertEqual(next(x for x in ledger['listings'] if x['event_id']==self.row['event_id'])['status'],'unsold')
        bad={**r,'hammer_text':'999 GBP'}
        (self.root/'results/second.jsonl').write_text(json.dumps(bad)+'\n')
        with self.assertRaises(ValueError):record_result_link(self.root,{**m,'result_fingerprint':fingerprint(bad)},[self.row])

    def test_group_components_share_one_lot_price_and_later_comparison_appends(self):
        from bowl_index.market_results import reconcile_results
        rows=[{**copy.deepcopy(self.row),'object_id':'component-%d'%i,'event_id':'offer-%d'%i} for i in range(3)]
        m={**self.manifest,'listings':[{**{k:r[k] for k in ('object_id','source_id','event_id')},
            'listing_fingerprint':listing_fingerprint(r)} for r in rows]}
        record_result_link(self.root,m,rows)
        reconciliation=reconcile_results(self.root,rows)
        self.assertEqual(reconciliation,{'issues':[],'followups':[]})
        self.assertTrue(all(r['status']=='sold' and 'Whole lot (three bowls)' in listing_price(r) for r in rows))
        body=self.body.replace(b'>300<',b'>350<');sha=_sha256(body);(self.root/'raw'/sha).write_bytes(body)
        r={**self.result,'observed_at':'2026-10-06T12:00:00Z','raw_sha256':sha,'hammer_text':'350 GBP'}
        (self.root/'results/second.jsonl').write_text(json.dumps(r)+'\n')
        record_result_link(self.root,{**m,'reviewed_at':'2026-10-06T12:00:00Z','result_fingerprint':fingerprint(r)},rows)
        reconcile_results(self.root,rows)
        self.assertTrue(all('350 GBP' in listing_price(x) for x in rows))
        self.assertEqual(len(list((self.root/'result-links').glob('*.json'))),2)
        self.assertEqual(result_records(self.root),[self.result,r])
