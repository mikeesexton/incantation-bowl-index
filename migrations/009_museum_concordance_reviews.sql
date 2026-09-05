CREATE TABLE museum_concordance_reviews (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    publication_source_id TEXT NOT NULL REFERENCES sources(id),
    museum_source_id TEXT NOT NULL REFERENCES sources(id),
    text_number INTEGER NOT NULL CHECK(text_number BETWEEN 1 AND 40),
    penn_web_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('confirmed','unresolved')),
    reviewed_at TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    review_json TEXT NOT NULL
);
CREATE INDEX museum_concordance_object_idx ON museum_concordance_reviews(object_id);
CREATE TRIGGER museum_concordance_no_update BEFORE UPDATE ON museum_concordance_reviews BEGIN
    SELECT RAISE(ABORT, 'museum concordance history is append-only');
END;
CREATE TRIGGER museum_concordance_no_delete BEFORE DELETE ON museum_concordance_reviews BEGIN
    SELECT RAISE(ABORT, 'museum concordance history is append-only');
END;
