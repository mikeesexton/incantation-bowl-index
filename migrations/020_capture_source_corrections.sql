-- Correct a mistaken work assignment without discarding retrieval provenance.
CREATE TABLE capture_source_corrections (
    id TEXT PRIMARY KEY,
    capture_id TEXT NOT NULL REFERENCES captures(id),
    before_source_id TEXT REFERENCES sources(id),
    after_source_id TEXT NOT NULL REFERENCES sources(id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    rationale TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE INDEX capture_source_corrections_capture_idx ON capture_source_corrections(capture_id);
CREATE TRIGGER capture_source_corrections_no_update BEFORE UPDATE ON capture_source_corrections BEGIN
    SELECT RAISE(ABORT, 'capture source corrections are append-only');
END;
CREATE TRIGGER capture_source_corrections_no_delete BEFORE DELETE ON capture_source_corrections BEGIN
    SELECT RAISE(ABORT, 'capture source corrections are append-only');
END;
