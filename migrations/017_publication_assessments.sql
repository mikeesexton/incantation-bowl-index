-- Object-level publication research must distinguish an actual publication
-- link from an evidence-backed finding that no edition is presently known.
-- Rows are immutable; a later review supersedes the current row explicitly.
CREATE TABLE publication_assessments (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    disposition TEXT NOT NULL CHECK (disposition IN (
        'linked','no_known_edition','unresolved')),
    publication_source_id TEXT REFERENCES sources(id),
    evidence_source_id TEXT NOT NULL REFERENCES sources(id),
    evidence_locator TEXT NOT NULL,
    publication_locator TEXT,
    basis TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    supersedes_id TEXT REFERENCES publication_assessments(id),
    CHECK (
        (disposition = 'linked' AND publication_source_id IS NOT NULL)
        OR
        (disposition <> 'linked' AND publication_source_id IS NULL
         AND publication_locator IS NULL)
    )
);
CREATE INDEX publication_assessments_object_idx
    ON publication_assessments(object_id);
CREATE INDEX publication_assessments_publication_idx
    ON publication_assessments(publication_source_id);
CREATE UNIQUE INDEX publication_assessments_supersedes_uq
    ON publication_assessments(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE TRIGGER publication_assessments_no_update
BEFORE UPDATE ON publication_assessments BEGIN
    SELECT RAISE(ABORT, 'publication assessments are append-only');
END;
CREATE TRIGGER publication_assessments_no_delete
BEFORE DELETE ON publication_assessments BEGIN
    SELECT RAISE(ABORT, 'publication assessments are append-only');
END;
