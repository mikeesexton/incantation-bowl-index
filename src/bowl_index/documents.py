"""Evidence-bound document completeness and transformation assessments.

Captures inventory bytes.  This ledger records what those bytes contain and
what has been done to them without conflating completeness, inspection, text
processing or object-level extraction.  Rows are immutable; a later assessment
explicitly supersedes the current row for the same source/capture target.
"""

import hashlib
from datetime import datetime
from pathlib import Path


FORMS = {"no_document", "scan", "born_digital", "physical"}
EXTENTS = {"citation_only", "front_matter", "excerpt", "complete"}
INSPECTIONS = {"not_inspected", "digital", "physical"}
TEXT_STATES = {"none", "extractable", "ocr", "corrected_rich_text"}
EXTRACTION_STATES = {"none", "partial", "complete"}

_COLUMNS = (
    "id", "source_id", "capture_id", "document_form", "extent", "inspection",
    "text_state", "text_artifact_path", "text_artifact_sha256",
    "object_extraction", "extraction_path", "extraction_sha256",
    "document_sha256", "basis", "evidence_path", "evidence_sha256",
    "assessed_by", "assessed_at", "supersedes_id",
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _checked_file(root, path_value, digest, label, required=True):
    path_value = (path_value or "").strip()
    digest = (digest or "").strip().lower()
    if not path_value and not digest and not required:
        return None, None
    if not path_value or len(digest) != 64:
        raise ValueError("%s path and SHA-256 are required together" % label)
    relative = Path(path_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("%s path must stay inside the project" % label)
    root = Path(root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError("%s path must stay inside the project" % label)
    if not path.is_file() or _sha256(path) != digest:
        raise ValueError("%s evidence changed or is missing: %s" % (label, path_value))
    return path_value, digest


def current_assessments(conn):
    """Return immutable leaf assessments, including separate source holdings."""
    return [dict(row) for row in conn.execute(
        "SELECT d.* FROM document_assessments d "
        "LEFT JOIN document_assessments newer ON newer.supersedes_id=d.id "
        "WHERE newer.id IS NULL ORDER BY d.source_id,d.capture_id,d.id"
    )]


def source_document_status(conn):
    """Best current assessed holding per source, without hiding all leaf rows."""
    extent_rank = {"citation_only": 0, "front_matter": 1, "excerpt": 2, "complete": 3}
    inspection_rank = {"not_inspected": 0, "digital": 1, "physical": 2}
    text_rank = {"none": 0, "extractable": 1, "ocr": 2, "corrected_rich_text": 3}
    extraction_rank = {"none": 0, "partial": 1, "complete": 2}
    grouped = {}
    for row in current_assessments(conn):
        score = (
            extent_rank[row["extent"]], inspection_rank[row["inspection"]],
            text_rank[row["text_state"]], extraction_rank[row["object_extraction"]],
            row["assessed_at"], row["id"],
        )
        if row["source_id"] not in grouped or score > grouped[row["source_id"]][0]:
            grouped[row["source_id"]] = (score, row)
    return {source_id: item[1] for source_id, item in grouped.items()}


def document_metrics(conn):
    rows = current_assessments(conn)
    sources = source_document_status(conn)
    values = list(sources.values())
    return {
        "document_assessment_rows": len(rows),
        "sources_with_document_assessments": len(sources),
        "sources_with_complete_documents": sum(r["extent"] == "complete" for r in values),
        "sources_with_physically_inspected_documents": sum(
            r["inspection"] == "physical" for r in values),
        "sources_with_ocr": sum(r["text_state"] == "ocr" for r in values),
        "sources_with_corrected_rich_text": sum(
            r["text_state"] == "corrected_rich_text" for r in values),
        "sources_with_object_level_extraction": sum(
            r["object_extraction"] != "none" for r in values),
        "sources_with_complete_object_level_extraction": sum(
            r["object_extraction"] == "complete" for r in values),
    }


def _validate_combination(entry, capture):
    form, extent = entry["document_form"], entry["extent"]
    inspection, text_state = entry["inspection"], entry["text_state"]
    extraction = entry["object_extraction"]
    if form not in FORMS or extent not in EXTENTS or inspection not in INSPECTIONS:
        raise ValueError("invalid document form, extent or inspection state")
    if text_state not in TEXT_STATES or extraction not in EXTRACTION_STATES:
        raise ValueError("invalid text or extraction state")
    if extent == "citation_only":
        if (form, inspection, text_state, extraction) != (
                "no_document", "not_inspected", "none", "none") or capture:
            raise ValueError("citation-only assessments cannot claim a holding or transformation")
    elif form == "no_document":
        raise ValueError("a non-citation assessment needs a document form")
    if extent != "citation_only" and inspection == "not_inspected":
        raise ValueError("document extent requires a recorded inspection")
    if form in {"scan", "born_digital"} and capture is None:
        raise ValueError("digital document assessments require a capture")
    if form == "physical" and (capture is not None or inspection != "physical"):
        raise ValueError("physical documents have no capture and require physical inspection")
    if inspection == "physical" and form != "physical":
        raise ValueError("physical inspection requires a physical document assessment")
    if text_state != "none" and form not in {"scan", "born_digital"}:
        raise ValueError("text transformation requires a digital document")


def apply_document_assessments(conn, manifest, root):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 document-assessment batch with entries is required")
    reviewer = (manifest.get("reviewed_by") or "").strip()
    stamp = datetime.fromisoformat((manifest.get("reviewed_at") or "").replace("Z", "+00:00"))
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named reviewer and UTC timestamp required")
    assessed_at = stamp.isoformat(timespec="seconds")
    if conn.in_transaction:
        raise ValueError("document assessment requires a clean transaction")

    changed = 0
    seen_ids, seen_targets = set(), set()
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            assessment_id = (entry.get("id") or "").strip()
            source_id = (entry.get("source_id") or "").strip()
            capture_id = (entry.get("capture_id") or "").strip() or None
            target = (source_id, capture_id or "source")
            if not assessment_id or not source_id or not (entry.get("basis") or "").strip():
                raise ValueError("assessment ID, source ID and basis are required")
            if assessment_id in seen_ids or target in seen_targets:
                raise ValueError("duplicate assessment ID or source holding in batch")
            seen_ids.add(assessment_id); seen_targets.add(target)
            if not conn.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone():
                raise ValueError("No such source: %s" % source_id)

            capture = None
            if capture_id:
                capture = conn.execute("SELECT * FROM captures WHERE id=?", (capture_id,)).fetchone()
                if capture is None or capture["source_id"] != source_id:
                    raise ValueError("capture does not belong to source: %s" % capture_id)
            _validate_combination(entry, capture)

            document_sha = (entry.get("document_sha256") or "").strip().lower() or None
            if capture and document_sha != capture["sha256"]:
                raise ValueError("document SHA-256 does not match capture: %s" % capture_id)
            if not capture and document_sha:
                raise ValueError("document SHA-256 requires a capture")

            evidence_path, evidence_sha = _checked_file(
                root, entry.get("evidence_path"), entry.get("evidence_sha256"), "review")
            needs_text_artifact = entry["text_state"] in {"ocr", "corrected_rich_text"}
            if not needs_text_artifact and (
                    entry.get("text_artifact_path") or entry.get("text_artifact_sha256")):
                raise ValueError("text artifacts require an OCR or corrected-rich-text state")
            text_path, text_sha = _checked_file(
                root, entry.get("text_artifact_path"), entry.get("text_artifact_sha256"),
                "text artifact", needs_text_artifact)
            needs_extraction = entry["object_extraction"] != "none"
            if not needs_extraction and (
                    entry.get("extraction_path") or entry.get("extraction_sha256")):
                raise ValueError("extraction artifacts require partial or complete extraction")
            extraction_path, extraction_sha = _checked_file(
                root, entry.get("extraction_path"), entry.get("extraction_sha256"),
                "object extraction", needs_extraction)

            supersedes = (entry.get("supersedes_id") or "").strip() or None
            current = conn.execute(
                "SELECT d.id FROM document_assessments d "
                "LEFT JOIN document_assessments newer ON newer.supersedes_id=d.id "
                "WHERE d.source_id=? AND coalesce(d.capture_id,'')=coalesce(?, '') "
                "AND newer.id IS NULL", (source_id, capture_id)).fetchall()
            payload = {
                "id": assessment_id, "source_id": source_id, "capture_id": capture_id,
                "document_form": entry["document_form"], "extent": entry["extent"],
                "inspection": entry["inspection"], "text_state": entry["text_state"],
                "text_artifact_path": text_path, "text_artifact_sha256": text_sha,
                "object_extraction": entry["object_extraction"],
                "extraction_path": extraction_path, "extraction_sha256": extraction_sha,
                "document_sha256": document_sha, "basis": entry["basis"].strip(),
                "evidence_path": evidence_path, "evidence_sha256": evidence_sha,
                "assessed_by": reviewer, "assessed_at": assessed_at,
                "supersedes_id": supersedes,
            }
            old = conn.execute(
                "SELECT * FROM document_assessments WHERE id=?", (assessment_id,)).fetchone()
            if old:
                if dict(old) != payload:
                    raise ValueError("assessment ID reused with changed evidence: %s" % assessment_id)
                continue
            current_ids = [row["id"] for row in current]
            if len(current_ids) > 1:
                raise ValueError("source holding has multiple current assessments")
            if current_ids and supersedes != current_ids[0]:
                raise ValueError("new assessment must supersede the current source holding")
            if not current_ids and supersedes:
                raise ValueError("superseded assessment is not current for this source holding")
            conn.execute(
                "INSERT INTO document_assessments (%s) VALUES (%s)" % (
                    ",".join(_COLUMNS), ",".join("?" for _ in _COLUMNS)),
                [payload[column] for column in _COLUMNS],
            )
            changed += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"entries": len(manifest["entries"]), "changed": changed, **document_metrics(conn)}
