-- Which publication does a publication-derived identifier designate?
--
-- `identifiers.source_id` already records who *reported* a designation, which is
-- correct and must not change. This table records the separate fact of which
-- publication is being *designated*, so a bowl can be asked which edition
-- publishes it. Append-only; a later decision supersedes rather than overwrites.
CREATE TABLE publication_registry (
    id TEXT PRIMARY KEY,
    publication_key TEXT NOT NULL,
    source_id TEXT REFERENCES sources(id),
    resolution TEXT NOT NULL CHECK (resolution IN ('resolved','unresolved','not_a_publication')),
    basis TEXT NOT NULL,
    blocker TEXT,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    CHECK (resolution <> 'resolved' OR source_id IS NOT NULL),
    CHECK (resolution <> 'unresolved' OR length(trim(coalesce(blocker,''))) > 0)
);
CREATE INDEX publication_registry_key_idx ON publication_registry(publication_key);
CREATE TRIGGER publication_registry_no_update BEFORE UPDATE ON publication_registry BEGIN
    SELECT RAISE(ABORT, 'the publication registry is append-only');
END;
CREATE TRIGGER publication_registry_no_delete BEFORE DELETE ON publication_registry BEGIN
    SELECT RAISE(ABORT, 'the publication registry is append-only');
END;
