"""Repair a captured document's work assignment with immutable provenance.

The capture remains the same retrieval and bytes. Only its source association
changes. Assessed captures require a separate repair of their document ledger;
this narrow workflow refuses to silently invalidate those assessments.
"""

import json
from datetime import datetime

from .documents import _checked_file


def apply_capture_source_corrections(conn, manifest, root):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("version 1 capture correction batch required")
    reviewer = (manifest.get("reviewed_by") or "").strip()
    stamp = manifest.get("reviewed_at", "")
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if not reviewer or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("reviewer and UTC timestamp required")
    evidence_path, evidence_sha = _checked_file(
        root, manifest.get("evidence_path"), manifest.get("evidence_sha256"), "capture correction")
    if conn.in_transaction:
        raise ValueError("capture correction requires a clean transaction")
    seen_captures, seen_ids = set(), set()
    applied = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            correction_id = (entry.get("id") or "").strip()
            capture_id = (entry.get("capture_id") or "").strip()
            source_id = (entry.get("after_source_id") or "").strip()
            rationale = (entry.get("rationale") or "").strip()
            before = entry.get("before", {})
            if not correction_id or not capture_id or not source_id or not rationale:
                raise ValueError("correction, capture, replacement source and rationale required")
            if capture_id in seen_captures or correction_id in seen_ids:
                raise ValueError("duplicate capture correction")
            seen_captures.add(capture_id); seen_ids.add(correction_id)
            row = conn.execute("SELECT * FROM captures WHERE id=?", (capture_id,)).fetchone()
            if row is None or set(before) != set(row.keys()) or before.get("id") != capture_id:
                raise ValueError("complete original capture snapshot required")
            if not conn.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone():
                raise ValueError("replacement source missing")
            if before["source_id"] == source_id:
                raise ValueError("capture source must change")
            after = dict(before, source_id=source_id)
            payload = {
                "id": correction_id, "capture_id": capture_id,
                "before_source_id": before["source_id"], "after_source_id": source_id,
                "reviewed_by": reviewer, "reviewed_at": stamp,
                "evidence_path": evidence_path, "evidence_sha256": evidence_sha,
                "rationale": rationale,
                "before_json": json.dumps(before, ensure_ascii=False, sort_keys=True),
                "after_json": json.dumps(after, ensure_ascii=False, sort_keys=True),
            }
            old = conn.execute("SELECT * FROM capture_source_corrections WHERE id=?", (correction_id,)).fetchone()
            if old:
                if dict(old) != payload or dict(row) != after:
                    raise ValueError("capture correction replay differs from recorded evidence")
                continue
            if dict(row) != before:
                raise ValueError("capture evidence changed")
            if conn.execute("SELECT 1 FROM document_assessments WHERE capture_id=?", (capture_id,)).fetchone():
                raise ValueError("assessed capture requires document-ledger repair")
            conn.execute("UPDATE captures SET source_id=? WHERE id=?", (source_id, capture_id))
            columns = list(payload)
            conn.execute("INSERT INTO capture_source_corrections (%s) VALUES (%s)" % (
                ",".join(columns), ",".join("?" for _ in columns)), list(payload.values()))
            applied += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"applied": applied, "unchanged": len(seen_captures) - applied}
