CREATE TABLE text_proofreading_reviews (
    id TEXT PRIMARY KEY,
    text_id TEXT NOT NULL REFERENCES texts(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    source_sha256 TEXT NOT NULL,
    expected_text_sha256 TEXT NOT NULL,
    result_text_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('reading_text_checked','partial_review')),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    source_pages_json TEXT NOT NULL,
    editorial_policy TEXT NOT NULL,
    correction_notes TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL
);
CREATE INDEX proofreading_text_idx ON text_proofreading_reviews(text_id);
CREATE TRIGGER proofreading_no_update BEFORE UPDATE ON text_proofreading_reviews BEGIN
    SELECT RAISE(ABORT, 'proofreading history is append-only');
END;
CREATE TRIGGER proofreading_no_delete BEFORE DELETE ON text_proofreading_reviews BEGIN
    SELECT RAISE(ABORT, 'proofreading history is append-only');
END;
