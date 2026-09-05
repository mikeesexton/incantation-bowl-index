-- Preserve the starting ledger and every subsequent decision; never rewrite history.
CREATE TABLE claim_conflict_review_history (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    snapshot_json TEXT NOT NULL
);
CREATE INDEX conflict_history_review_idx ON claim_conflict_review_history(review_id);
INSERT INTO claim_conflict_review_history
SELECT 'IBI-REVH-' || upper(hex(randomblob(12))), id,
       strftime('%Y-%m-%dT%H:%M:%SZ','now'),
       json_object('id',id,'identity_id',identity_id,'field_group',field_group,
          'disposition',disposition,'review_method',review_method,'rationale',rationale,
          'details_json',details_json,'reviewed_by',reviewed_by,'reviewed_at',reviewed_at,
          'created_at',created_at,'updated_at',updated_at)
FROM claim_conflict_reviews;
CREATE TRIGGER conflict_history_insert AFTER INSERT ON claim_conflict_reviews BEGIN
    INSERT INTO claim_conflict_review_history VALUES (
        'IBI-REVH-' || upper(hex(randomblob(12))), NEW.id,
        strftime('%Y-%m-%dT%H:%M:%SZ','now'),
        json_object('id',NEW.id,'identity_id',NEW.identity_id,'field_group',NEW.field_group,
          'disposition',NEW.disposition,'review_method',NEW.review_method,'rationale',NEW.rationale,
          'details_json',NEW.details_json,'reviewed_by',NEW.reviewed_by,'reviewed_at',NEW.reviewed_at,
          'created_at',NEW.created_at,'updated_at',NEW.updated_at));
END;
CREATE TRIGGER conflict_history_update AFTER UPDATE ON claim_conflict_reviews BEGIN
    INSERT INTO claim_conflict_review_history VALUES (
        'IBI-REVH-' || upper(hex(randomblob(12))), NEW.id,
        strftime('%Y-%m-%dT%H:%M:%SZ','now'),
        json_object('id',NEW.id,'identity_id',NEW.identity_id,'field_group',NEW.field_group,
          'disposition',NEW.disposition,'review_method',NEW.review_method,'rationale',NEW.rationale,
          'details_json',NEW.details_json,'reviewed_by',NEW.reviewed_by,'reviewed_at',NEW.reviewed_at,
          'created_at',NEW.created_at,'updated_at',NEW.updated_at));
END;
CREATE TRIGGER conflict_history_no_update BEFORE UPDATE ON claim_conflict_review_history BEGIN
    SELECT RAISE(ABORT, 'review history is append-only');
END;
CREATE TRIGGER conflict_history_no_delete BEFORE DELETE ON claim_conflict_review_history BEGIN
    SELECT RAISE(ABORT, 'review history is append-only');
END;
CREATE TRIGGER conflict_review_no_delete BEFORE DELETE ON claim_conflict_reviews BEGIN
    SELECT RAISE(ABORT, 'supersede a review; do not delete it');
END;
