import tempfile
import unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.conflicts import conflict_instances
from bowl_index.identity import (
    CONTENT_COVERAGE, CORE_COVERAGE, COVERAGE_GROUPS, EXCLUDED_CLAIM_FIELDS,
    identity_rows, unclassified_claim_fields,
)

class FieldModelTests(unittest.TestCase):
    """Every claim field is compared or explicitly excluded — never both, never neither."""
    def test_no_field_appears_in_two_groups(self):
        seen = {}
        for group, fields in COVERAGE_GROUPS.items():
            for field in fields:
                self.assertNotIn(field, seen,
                    '%s is in both %s and %s' % (field, seen.get(field), group))
                seen[field] = group
    def test_no_field_is_both_grouped_and_excluded(self):
        grouped = {f for fields in COVERAGE_GROUPS.values() for f in fields}
        overlap = grouped & set(EXCLUDED_CLAIM_FIELDS)
        self.assertEqual(overlap, set(), 'grouped and excluded: %s' % sorted(overlap))
    def test_every_exclusion_states_a_reason(self):
        for field, reason in EXCLUDED_CLAIM_FIELDS.items():
            self.assertGreater(len(reason.strip()), 20,
                '%s is excluded without a usable reason' % field)
    def test_core_and_content_groups_are_disjoint(self):
        self.assertEqual(set(CORE_COVERAGE) & set(CONTENT_COVERAGE), set())
        self.assertEqual(set(COVERAGE_GROUPS), set(CORE_COVERAGE) | set(CONTENT_COVERAGE))
    def test_release_gate_facets_keep_their_names(self):
        # next_action, the handoff gate and the research console address these by key.
        self.assertEqual(set(CORE_COVERAGE), {
            'location', 'provenance', 'dating', 'dimensions', 'material', 'language', 'script'})


class UnclassifiedFieldTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def candidate(self, field, value, label='bowl'):
        add_candidate(self.conn,{'label':label,'source':{'source_type':'catalogue','title':'Cat',
            'citation':'Cat 2026','url':'https://example.org/%s'%label},
            'appearance':{'locator':label,'confidence':1},
            'claims':[{'field':field,'value_text':value,'locator':'p. 1'}]})
        self.conn.commit()

    def test_a_new_field_is_reported_rather_than_silently_ignored(self):
        self.candidate('inscription_language','Mandaic')
        self.assertEqual(unclassified_claim_fields(self.conn),[])
        self.candidate('bowl_colour','buff','bowl-2')
        self.assertEqual(unclassified_claim_fields(self.conn),['bowl_colour'])

    def test_an_excluded_field_does_not_count_as_unclassified(self):
        self.candidate('sale_price','US$1,400')
        self.assertEqual(unclassified_claim_fields(self.conn),[])

    def test_an_excluded_field_is_never_compared(self):
        add_candidate(self.conn,{'label':'sold bowl','source':{'source_type':'auction_record',
            'title':'Auction','citation':'Auction 2026','url':'https://example.org/lot'},
            'appearance':{'locator':'lot 1','confidence':1},
            'claims':[{'field':'sale_price','value_text':'US$1,400','locator':'lot 1'},
                      {'field':'sale_price','value_text':'US$2,900','locator':'lot 2'}]})
        self.conn.commit()
        self.assertEqual([i['field_group'] for i in conflict_instances(self.conn)],[])

    def test_a_content_facet_is_counted_and_compared(self):
        add_candidate(self.conn,{'label':'client bowl','source':{'source_type':'catalogue',
            'title':'Cat','citation':'Cat 2026','url':'https://example.org/c'},
            'appearance':{'locator':'no. 1','confidence':1},
            'claims':[{'field':'client','value_text':'Mari son of Awirta','locator':'p. 1'},
                      {'field':'clients','value_text':'Dadbeh son of Asmanduk','locator':'p. 2'}]})
        self.conn.commit()
        row=identity_rows(self.conn)[0]
        self.assertTrue(row['has_client'])
        self.assertIn('client',[i['field_group'] for i in conflict_instances(self.conn)])

    def test_roles_are_not_collapsed_into_one_group(self):
        # A client and an attributed author are different people making different claims.
        add_candidate(self.conn,{'label':'role bowl','source':{'source_type':'thesis',
            'title':'Kedar','citation':'Kedar 2019','url':'https://example.org/k'},
            'appearance':{'locator':'NFP 1','confidence':1},
            'claims':[{'field':'client','value_text':'Mari son of Awirta','locator':'p. 1'},
                      {'field':'attributed_author','value_text':'Komis daughter of Mahlafta','locator':'p. 2'}]})
        self.conn.commit()
        self.assertEqual([i['field_group'] for i in conflict_instances(self.conn)],[])
        row=identity_rows(self.conn)[0]
        self.assertTrue(row['has_client'] and row['has_practitioner'])

if __name__=='__main__':
    unittest.main()
