-- Two judgments the scholarship index needs and cannot derive.
--
-- Scope: `source_type` records format (article, chapter), not what a work does.
-- Only publications with a resolved object count can have scope derived; the
-- rest is a reading judgment and is recorded as one.
CREATE TABLE source_scope_reviews (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    scope TEXT NOT NULL CHECK (scope IN (
        'single_object_edition','corpus_edition','catalogue','thematic_study','synthesis',
        'linguistic_study','provenance_ethics','excavation_report','not_scholarship')),
    basis TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL
);
CREATE INDEX source_scope_source_idx ON source_scope_reviews(source_id);
CREATE TRIGGER source_scope_no_update BEFORE UPDATE ON source_scope_reviews BEGIN
    SELECT RAISE(ABORT, 'source scope reviews are append-only');
END;
CREATE TRIGGER source_scope_no_delete BEFORE DELETE ON source_scope_reviews BEGIN
    SELECT RAISE(ABORT, 'source scope reviews are append-only');
END;

-- Contributors: `authors` is free text, so one scholar appears under several
-- spellings. Grouping them is the object-identity problem one level up, and a
-- wrong merge misattributes someone's work. Derivation groups by surname and
-- first initial; this ledger overrides it in either direction.
CREATE TABLE contributor_aliases (
    id TEXT PRIMARY KEY,
    alias TEXT NOT NULL UNIQUE,
    contributor_key TEXT NOT NULL,
    display_name TEXT,
    basis TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL
);
CREATE INDEX contributor_alias_key_idx ON contributor_aliases(contributor_key);
CREATE TRIGGER contributor_alias_no_update BEFORE UPDATE ON contributor_aliases BEGIN
    SELECT RAISE(ABORT, 'contributor aliases are append-only');
END;
CREATE TRIGGER contributor_alias_no_delete BEFORE DELETE ON contributor_aliases BEGIN
    SELECT RAISE(ABORT, 'contributor aliases are append-only');
END;
