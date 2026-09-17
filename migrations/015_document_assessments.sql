-- A capture proves that bytes were retained, not what those bytes contain or
-- what work has been done to them.  These immutable assessments keep document
-- extent, inspection, text transformation and object extraction independent.
CREATE TABLE document_assessments (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    capture_id TEXT REFERENCES captures(id),
    document_form TEXT NOT NULL CHECK (document_form IN (
        'no_document','scan','born_digital','physical')),
    extent TEXT NOT NULL CHECK (extent IN (
        'citation_only','front_matter','excerpt','complete')),
    inspection TEXT NOT NULL CHECK (inspection IN (
        'not_inspected','digital','physical')),
    text_state TEXT NOT NULL CHECK (text_state IN (
        'none','extractable','ocr','corrected_rich_text')),
    text_artifact_path TEXT,
    text_artifact_sha256 TEXT CHECK (
        text_artifact_sha256 IS NULL OR length(text_artifact_sha256) = 64),
    object_extraction TEXT NOT NULL CHECK (object_extraction IN (
        'none','partial','complete')),
    extraction_path TEXT,
    extraction_sha256 TEXT CHECK (
        extraction_sha256 IS NULL OR length(extraction_sha256) = 64),
    document_sha256 TEXT CHECK (
        document_sha256 IS NULL OR length(document_sha256) = 64),
    basis TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL CHECK (length(evidence_sha256) = 64),
    assessed_by TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    supersedes_id TEXT REFERENCES document_assessments(id)
);
CREATE INDEX document_assessments_source_idx ON document_assessments(source_id);
CREATE INDEX document_assessments_capture_idx ON document_assessments(capture_id);
CREATE UNIQUE INDEX document_assessments_supersedes_uq
    ON document_assessments(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE TRIGGER document_assessments_no_update BEFORE UPDATE ON document_assessments BEGIN
    SELECT RAISE(ABORT, 'document assessments are append-only');
END;
CREATE TRIGGER document_assessments_no_delete BEFORE DELETE ON document_assessments BEGIN
    SELECT RAISE(ABORT, 'document assessments are append-only');
END;
