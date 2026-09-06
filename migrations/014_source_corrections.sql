-- Audited bibliographic repairs. The mutable source row remains convenient for
-- queries, while this ledger preserves the exact imported and corrected states.
CREATE TABLE source_corrections (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    replacement_source_id TEXT REFERENCES sources(id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    rationale TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE INDEX source_corrections_source_idx ON source_corrections(source_id);
CREATE INDEX source_corrections_replacement_idx ON source_corrections(replacement_source_id);
CREATE TRIGGER source_corrections_no_update BEFORE UPDATE ON source_corrections BEGIN
    SELECT RAISE(ABORT, 'source corrections are append-only');
END;
CREATE TRIGGER source_corrections_no_delete BEFORE DELETE ON source_corrections BEGIN
    SELECT RAISE(ABORT, 'source corrections are append-only');
END;
