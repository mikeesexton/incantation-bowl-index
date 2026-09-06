import sqlite3, tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.scholarship import (
    apply_scope_batch, contributor_groups, contributor_key, decade_series,
    scholarship_metrics, split_authors, works,
)

class AuthorParsingTests(unittest.TestCase):
    def test_the_three_shapes_the_corpus_actually_contains(self):
        self.assertEqual(split_authors('Dan Levene; Siam Bhayro'), ['Dan Levene', 'Siam Bhayro'])
        self.assertEqual(split_authors('Babelon, Ernest, and Moïse Schwab'),
                         ['Babelon, Ernest', 'Moïse Schwab'])
        self.assertEqual(split_authors('J. B. Segal, with a contribution by Erica C. D. Hunter'),
                         ['J. B. Segal', 'Erica C. D. Hunter'])
    def test_editorial_roles_and_vague_coauthors_are_dropped(self):
        self.assertEqual(split_authors('Lauren E. Talalay and Margaret Cool Root, eds.'),
                         ['Lauren E. Talalay', 'Margaret Cool Root'])
        self.assertEqual(split_authors('Simon Mackenzie; and colleagues'), ['Simon Mackenzie'])
    def test_the_ingest_placeholder_never_becomes_an_author(self):
        # SCHOL-002 wrote "Surname [and others; see citation]"; left alone it invented
        # an author called "see citation]" and keyed others on the surname "others".
        self.assertEqual(split_authors('Abousamra [and others; see citation]'), ['Abousamra'])
        self.assertEqual(split_authors('Gordon [and others; see citation]'), ['Gordon'])

class ContributorKeyTests(unittest.TestCase):
    def test_spellings_of_one_person_share_a_key(self):
        keys = {contributor_key(n) for n in
                ('Ford, James Nathan', 'James Nathan Ford', 'Ford, J. N.')}
        self.assertEqual(len(keys), 1)
    def test_diacritics_do_not_split_a_person(self):
        self.assertEqual(contributor_key('Christa Müller-Kessler'),
                         contributor_key('Müller-Kessler, Christa'))
    def test_a_corporate_author_keys_on_its_whole_name(self):
        self.assertNotEqual(contributor_key('The British Museum'), contributor_key('Apotropaic Arts'))

class ContributorGroupingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def add(self, authors, year=2000, ident=None):
        self.conn.execute(
            "INSERT INTO sources(id,source_type,title,authors,issued_year,citation) "
            "VALUES (?,'article',?,?,?,?)",
            (ident or 'SRC-%d' % (year * 1000 + len(authors)), 'Work ' + authors, authors, year, 'c'))
        self.conn.commit()

    def test_a_bare_surname_folds_into_the_one_scholar_who_has_it(self):
        self.add('Dan Levene', 1999, 'SRC-A'); self.add('Levene', 2003, 'SRC-B')
        groups = contributor_groups(self.conn)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['works'], 2)
        self.assertEqual(groups[0]['display_name'], 'Dan Levene')

    def test_a_bare_surname_is_left_alone_when_it_would_be_a_guess(self):
        """The failure that misattributes someone's work. It must not happen."""
        self.add('James Nathan Ford', 2002, 'SRC-C')
        self.add('Alice Ford', 2010, 'SRC-D')
        self.add('Ford', 1950, 'SRC-E')
        groups = {g['display_name']: g for g in contributor_groups(self.conn)}
        self.assertIn('Ford', groups)                       # stayed separate
        self.assertEqual(groups['James Nathan Ford']['works'], 1)
        self.assertEqual(groups['Alice Ford']['works'], 1)

    def test_multi_spelling_groups_are_flagged_for_an_eye_check(self):
        self.add('Ford, James Nathan', 2002, 'SRC-F'); self.add('J. N. Ford', 2004, 'SRC-G')
        group = contributor_groups(self.conn)[0]
        self.assertTrue(group['needs_check'])
        self.assertEqual(len(group['spellings']), 2)

    def test_a_natural_spelling_is_preferred_for_display(self):
        self.add('Shaked, Shaul', 1987, 'SRC-H'); self.add('Shaul Shaked', 2021, 'SRC-I')
        self.assertEqual(contributor_groups(self.conn)[0]['display_name'], 'Shaul Shaked')

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.conn=connect(self.root/'db.sqlite3'); migrate(self.conn)
        self.conn.execute("INSERT INTO sources(id,source_type,title,citation) "
                          "VALUES ('SRC-1','article','A study','Study 2020')")
        self.conn.execute("INSERT INTO sources(id,source_type,title,citation) "
                          "VALUES ('SRC-2','museum_record','A record','Record')")
        self.conn.commit()
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def batch(self,**over):
        e={'review_id':'IBI-SCOPE-1','source_id':'SRC-1','scope':'thematic_study',
           'basis':'Reads as a thematic study of formula families'}
        e.update(over)
        return {'schema_version':1,'reviewed_by':'Test','reviewed_at':'2026-09-06T00:00:00+00:00',
                'entries':[e]}

    def test_museum_records_are_not_scholarship(self):
        self.assertEqual([w['source_id'] for w in works(self.conn)], ['SRC-1'])

    def test_an_unclassified_work_says_so_rather_than_guessing(self):
        self.assertEqual(works(self.conn)[0]['scope_basis'], 'unclassified')
        self.assertIsNone(works(self.conn)[0]['scope'])

    def test_a_recorded_decision_wins_and_is_marked_reviewed(self):
        apply_scope_batch(self.conn, self.batch())
        row = works(self.conn)[0]
        self.assertEqual((row['scope'], row['scope_basis']), ('thematic_study', 'reviewed'))
        self.assertEqual(scholarship_metrics(self.conn)['works_awaiting_scope'], 0)

    def test_an_invalid_scope_or_missing_basis_is_rejected(self):
        for over in ({'scope': 'interesting'}, {'basis': ' '}, {'source_id': 'SRC-NOPE'}):
            with self.assertRaises(ValueError):
                apply_scope_batch(self.conn, self.batch(**over))

    def test_decisions_replay_and_are_append_only(self):
        self.assertEqual(apply_scope_batch(self.conn, self.batch())['changed'], 1)
        self.assertEqual(apply_scope_batch(self.conn, self.batch())['changed'], 0)
        with self.assertRaises(ValueError):
            apply_scope_batch(self.conn, self.batch(basis='A different reason'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM source_scope_reviews")

    def test_the_decade_series_reports_both_lines(self):
        rows = decade_series(self.conn)
        self.assertTrue(all({'decade','held','field_control_list'} <= set(r) for r in rows))

if __name__=='__main__':
    unittest.main()
