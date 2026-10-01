-- Metadata-only repairs preserve complete private before/after snapshots.
CREATE TABLE text_metadata_corrections (
    id TEXT PRIMARY KEY,
    text_id TEXT NOT NULL REFERENCES texts(id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    expected_text_sha256 TEXT NOT NULL,
    changes_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE INDEX text_metadata_corrections_text_idx ON text_metadata_corrections(text_id);
CREATE TRIGGER text_metadata_corrections_no_update BEFORE UPDATE ON text_metadata_corrections BEGIN
    SELECT RAISE(ABORT, 'text metadata corrections are append-only');
END;
CREATE TRIGGER text_metadata_corrections_no_delete BEFORE DELETE ON text_metadata_corrections BEGIN
    SELECT RAISE(ABORT, 'text metadata corrections are append-only');
END;
