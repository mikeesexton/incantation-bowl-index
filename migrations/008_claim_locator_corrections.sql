CREATE TABLE claim_locator_corrections (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    rationale TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE TRIGGER claim_locator_corrections_no_update BEFORE UPDATE ON claim_locator_corrections BEGIN
    SELECT RAISE(ABORT, 'claim corrections are append-only');
END;
CREATE TRIGGER claim_locator_corrections_no_delete BEFORE DELETE ON claim_locator_corrections BEGIN
    SELECT RAISE(ABORT, 'claim corrections are append-only');
END;
