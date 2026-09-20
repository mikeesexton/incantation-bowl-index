-- QA-003 needs an identity-level, evidence-bound ledger rather than the older
-- object-level spot-check table. Reviews are append-only and can be superseded.
CREATE TABLE accuracy_audit_reviews (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    sample_role TEXT NOT NULL CHECK (sample_role IN ('representative','high_risk')),
    identity_id TEXT NOT NULL,
    canonical_object_id TEXT NOT NULL REFERENCES objects(id),
    member_ids_json TEXT NOT NULL,
    stratum TEXT NOT NULL,
    selection_evidence_sha256 TEXT NOT NULL CHECK (length(selection_evidence_sha256) = 64),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN (
        'verified','verified_with_notes','error','indeterminate')),
    citation_check TEXT NOT NULL CHECK (citation_check IN (
        'verified','error','not_reverifiable','not_applicable')),
    identifier_check TEXT NOT NULL CHECK (identifier_check IN (
        'verified','error','not_reverifiable','not_applicable')),
    identity_check TEXT NOT NULL CHECK (identity_check IN (
        'verified','error','not_reverifiable','not_applicable')),
    claim_check TEXT NOT NULL CHECK (claim_check IN (
        'verified','error','not_reverifiable','not_applicable')),
    error_categories_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    notes TEXT NOT NULL,
    review_sha256 TEXT NOT NULL CHECK (length(review_sha256) = 64),
    supersedes_id TEXT REFERENCES accuracy_audit_reviews(id)
);
CREATE INDEX accuracy_audit_reviews_batch_idx
    ON accuracy_audit_reviews(audit_id,sample_role,identity_id);
CREATE UNIQUE INDEX accuracy_audit_reviews_supersedes_uq
    ON accuracy_audit_reviews(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE TRIGGER accuracy_audit_reviews_no_update BEFORE UPDATE ON accuracy_audit_reviews BEGIN
    SELECT RAISE(ABORT, 'accuracy audit reviews are append-only');
END;
CREATE TRIGGER accuracy_audit_reviews_no_delete BEFORE DELETE ON accuracy_audit_reviews BEGIN
    SELECT RAISE(ABORT, 'accuracy audit reviews are append-only');
END;
