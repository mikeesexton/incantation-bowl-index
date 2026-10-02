CREATE TABLE catalogue_metadata_corrections (
    id TEXT PRIMARY KEY,
    target_table TEXT NOT NULL CHECK(target_table IN ('objects','appearances','identifiers','claims')),
    target_id TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    rationale TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE INDEX catalogue_metadata_target ON catalogue_metadata_corrections(target_table,target_id);
CREATE TRIGGER catalogue_metadata_no_update BEFORE UPDATE ON catalogue_metadata_corrections
BEGIN SELECT RAISE(ABORT,'catalogue correction history is immutable'); END;
CREATE TRIGGER catalogue_metadata_no_delete BEFORE DELETE ON catalogue_metadata_corrections
BEGIN SELECT RAISE(ABORT,'catalogue correction history is immutable'); END;
