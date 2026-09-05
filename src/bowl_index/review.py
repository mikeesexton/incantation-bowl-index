import json
from pathlib import Path

from .ids import new_id


REVIEW_STATUSES = {"same_object", "different_objects", "insufficient_evidence"}


def apply_dedupe_review(conn, record):
    status = record.get("status")
    if status not in REVIEW_STATUSES:
        raise ValueError("review status must be same_object, different_objects, or insufficient_evidence")
    row = None
    if record.get("dedupe_id"):
        row = conn.execute(
            "SELECT * FROM dedupe_candidates WHERE id=?", (record["dedupe_id"],)
        ).fetchone()
    if not row and record.get("object_a_id") and record.get("object_b_id"):
        object_a_id, object_b_id = sorted((record["object_a_id"], record["object_b_id"]))
        row = conn.execute(
            "SELECT * FROM dedupe_candidates WHERE object_a_id=? AND object_b_id=?",
            (object_a_id, object_b_id),
        ).fetchone()
    if not row:
        raise ValueError("review does not resolve an existing dedupe candidate")
    conn.execute(
        "UPDATE dedupe_candidates SET status=?,decided_at=?,decided_by=? WHERE id=?",
        (
            status, record.get("decided_at"), record.get("decided_by", "manual review"), row["id"],
        ),
    )
    for evidence in record.get("evidence", []):
        notes = evidence.get("notes")
        evidence_type = evidence["evidence_type"]
        if conn.execute(
            "SELECT 1 FROM dedupe_evidence WHERE dedupe_id=? AND evidence_type=? "
            "AND notes IS ? AND value_a IS ? AND value_b IS ?",
            (
                row["id"], evidence_type, notes, evidence.get("value_a"),
                evidence.get("value_b"),
            ),
        ).fetchone():
            continue
        conn.execute(
            "INSERT INTO dedupe_evidence "
            "(id,dedupe_id,evidence_type,value_a,value_b,weight,supports_match,source_id,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                new_id("dedupe_evidence"), row["id"], evidence_type,
                evidence.get("value_a"), evidence.get("value_b"),
                evidence.get("weight", 1.0), evidence.get("supports_match", 0),
                evidence.get("source_id"), notes,
            ),
        )
    return row["id"]


def load_dedupe_reviews(conn, path):
    path = Path(path)
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                apply_dedupe_review(conn, json.loads(line))
            except Exception as exc:
                conn.rollback()
                raise ValueError("%s:%s: %s" % (path, line_number, exc)) from exc
            count += 1
    conn.commit()
    return count
