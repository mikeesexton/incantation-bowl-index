-- Researcher decisions that an object record is outside the corpus (or back
-- inside it). The objects row carries the current status for queries; this
-- ledger keeps who decided, why, and the exact prior values.
CREATE TABLE object_scope_reviews (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    record_status TEXT NOT NULL CHECK (record_status IN (
        'candidate','probable','confirmed','rejected'
    )),
    object_type TEXT NOT NULL CHECK (object_type IN (
        'whole_bowl','fragment','reconstructed','lost_or_unlocated','non_bowl','uncertain'
    )),
    previous_record_status TEXT NOT NULL,
    previous_object_type TEXT NOT NULL,
    basis TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_at TEXT NOT NULL
);
CREATE INDEX object_scope_reviews_object_idx ON object_scope_reviews(object_id);
CREATE TRIGGER object_scope_reviews_no_update BEFORE UPDATE ON object_scope_reviews BEGIN
    SELECT RAISE(ABORT, 'object scope reviews are append-only');
END;
CREATE TRIGGER object_scope_reviews_no_delete BEFORE DELETE ON object_scope_reviews BEGIN
    SELECT RAISE(ABORT, 'object scope reviews are append-only');
END;
