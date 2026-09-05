-- Publication decisions for text rows, separate from the source's copyright label.
-- A public-domain source does not by itself make a stored reading text publishable:
-- the editorial state of that text has to be stated too.
CREATE TABLE text_publication_reviews (
    id TEXT PRIMARY KEY,
    text_id TEXT NOT NULL REFERENCES texts(id),
    evidence_sha256 TEXT NOT NULL,
    rights_basis TEXT NOT NULL CHECK(rights_basis IN (
        'public_domain_expired','open_license','permission','own_work','not_established')),
    rights_locator TEXT,
    license_url TEXT,
    publication_decision TEXT NOT NULL CHECK(publication_decision IN (
        'needs_review','withhold','approved')),
    attribution TEXT,
    editorial_status TEXT,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    rationale TEXT NOT NULL,
    followup TEXT,
    CHECK(publication_decision <> 'needs_review' OR length(trim(followup)) > 0),
    CHECK(publication_decision <> 'approved' OR (
        rights_basis <> 'not_established'
        AND length(trim(coalesce(rights_locator,''))) > 0
        AND length(trim(coalesce(attribution,''))) > 0
        AND length(trim(coalesce(editorial_status,''))) > 0))
);
CREATE INDEX text_publication_text_idx ON text_publication_reviews(text_id);
CREATE TRIGGER text_publication_no_update BEFORE UPDATE ON text_publication_reviews BEGIN
    SELECT RAISE(ABORT, 'text publication reviews are append-only');
END;
CREATE TRIGGER text_publication_no_delete BEFORE DELETE ON text_publication_reviews BEGIN
    SELECT RAISE(ABORT, 'text publication reviews are append-only');
END;
