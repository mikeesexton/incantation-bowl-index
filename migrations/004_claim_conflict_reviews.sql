CREATE TABLE claim_conflict_reviews (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL,
    field_group TEXT NOT NULL,
    disposition TEXT NOT NULL CHECK (disposition IN (
        'compatible','temporal_change','scholarly_disagreement','source_inconsistency',
        'source_error','data_error','unresolved'
    )),
    review_method TEXT NOT NULL,
    rationale TEXT NOT NULL,
    details_json TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (identity_id, field_group)
);

CREATE INDEX claim_conflict_reviews_disposition_idx
ON claim_conflict_reviews(disposition, field_group);
