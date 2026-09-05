CREATE TABLE media_rights_reviews (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL REFERENCES media(id),
    evidence_sha256 TEXT NOT NULL,
    creator TEXT,
    rights_holder TEXT,
    source_url TEXT NOT NULL,
    rights_statement TEXT,
    rights_locator TEXT,
    license_url TEXT,
    jurisdiction_notes TEXT,
    private_capture_status TEXT NOT NULL CHECK(private_capture_status IN ('not_captured','captured_private','unknown')),
    public_reuse_decision TEXT NOT NULL CHECK(public_reuse_decision IN ('needs_review','withhold','approved')),
    attribution TEXT,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    rationale TEXT NOT NULL,
    followup TEXT,
    CHECK(public_reuse_decision <> 'needs_review' OR length(trim(followup)) > 0),
    CHECK(public_reuse_decision <> 'approved' OR
          (length(trim(rights_statement)) > 0 AND length(trim(rights_locator)) > 0 AND length(trim(attribution)) > 0))
);
CREATE INDEX media_rights_media_idx ON media_rights_reviews(media_id);
CREATE TRIGGER media_rights_no_update BEFORE UPDATE ON media_rights_reviews BEGIN
    SELECT RAISE(ABORT, 'rights reviews are append-only');
END;
CREATE TRIGGER media_rights_no_delete BEFORE DELETE ON media_rights_reviews BEGIN
    SELECT RAISE(ABORT, 'rights reviews are append-only');
END;
