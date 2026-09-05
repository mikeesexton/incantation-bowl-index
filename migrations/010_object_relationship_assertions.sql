CREATE TABLE object_relationship_assertions (
    id TEXT PRIMARY KEY,
    subject_object_id TEXT NOT NULL REFERENCES objects(id),
    target_object_id TEXT NOT NULL REFERENCES objects(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    appearance_id TEXT NOT NULL REFERENCES appearances(id),
    relationship_type TEXT NOT NULL CHECK(relationship_type IN (
        'duplicate_of','same_as','part_of','related_to'
    )),
    relationship_scope TEXT NOT NULL CHECK(relationship_scope IN (
        'physical_identity','physical_part','textual','catalogue','unclear'
    )),
    target_identifier_scheme TEXT NOT NULL,
    target_identifier_value TEXT NOT NULL,
    raw_statement TEXT NOT NULL,
    interpretation_status TEXT NOT NULL CHECK(interpretation_status IN (
        'accepted','unresolved','rejected'
    )),
    locator TEXT NOT NULL,
    rationale TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    assertion_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(subject_object_id <> target_object_id)
);

CREATE INDEX object_relationship_subject_idx
    ON object_relationship_assertions(subject_object_id);
CREATE INDEX object_relationship_target_idx
    ON object_relationship_assertions(target_object_id);

CREATE TRIGGER object_relationship_assertions_no_update
BEFORE UPDATE ON object_relationship_assertions BEGIN
    SELECT RAISE(ABORT, 'object relationship assertions are append-only');
END;

CREATE TRIGGER object_relationship_assertions_no_delete
BEFORE DELETE ON object_relationship_assertions BEGIN
    SELECT RAISE(ABORT, 'object relationship assertions are append-only');
END;
