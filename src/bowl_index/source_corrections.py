"""Evidence-bound bibliographic repairs with immutable before/after history."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .ingest import SOURCE_FIELDS


def _source_state(row):
    return {field: row[field] for field in SOURCE_FIELDS}


def apply_source_corrections(conn, manifest, root):
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported source correction schema")
    reviewer = manifest.get("reviewed_by", "").strip()
    stamp = manifest.get("reviewed_at", "")
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if not reviewer or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("reviewer and UTC timestamp required")
    evidence = Path(root) / manifest["evidence_path"]
    if hashlib.sha256(evidence.read_bytes()).hexdigest() != manifest["evidence_sha256"]:
        raise ValueError("correction evidence changed")
    if conn.in_transaction:
        raise ValueError("correction requires a clean transaction")

    expected_fields = set(SOURCE_FIELDS)
    seen_sources = set()
    seen_corrections = set()
    applied = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            correction_id = entry.get("id", "").strip()
            source_id = entry.get("source_id", "").strip()
            before = entry.get("before", {})
            after = entry.get("after", {})
            rationale = entry.get("rationale", "").strip()
            replacement = entry.get("replacement_source_id")
            if not correction_id or not source_id or not rationale:
                raise ValueError("correction id, source id and rationale required")
            if correction_id in seen_corrections or source_id in seen_sources:
                raise ValueError("duplicate source correction")
            seen_corrections.add(correction_id)
            seen_sources.add(source_id)
            if set(before) != expected_fields or set(after) != expected_fields:
                raise ValueError("before and after must contain every stable source field")
            if before == after:
                raise ValueError("correction must change the source")

            row = conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
            if row is None:
                raise ValueError("source missing")
            if replacement and not conn.execute(
                "SELECT 1 FROM sources WHERE id=?", (replacement,)
            ).fetchone():
                raise ValueError("replacement source missing")
            payload = {
                "id": correction_id,
                "source_id": source_id,
                "replacement_source_id": replacement,
                "reviewed_by": reviewer,
                "reviewed_at": stamp,
                "evidence_path": manifest["evidence_path"],
                "evidence_sha256": manifest["evidence_sha256"],
                "rationale": rationale,
                "before_json": json.dumps(before, ensure_ascii=False, sort_keys=True),
                "after_json": json.dumps(after, ensure_ascii=False, sort_keys=True),
            }
            old = conn.execute(
                "SELECT * FROM source_corrections WHERE id=?", (correction_id,)
            ).fetchone()
            current = _source_state(row)
            if old:
                if dict(old) != payload or current != after:
                    raise ValueError("correction replay differs from recorded evidence")
                continue
            if current != before:
                raise ValueError("source evidence changed")

            assignments = ",".join(f"{field}=?" for field in SOURCE_FIELDS)
            conn.execute(
                f"UPDATE sources SET {assignments},updated_at=CURRENT_TIMESTAMP WHERE id=?",
                [after[field] for field in SOURCE_FIELDS] + [source_id],
            )
            columns = list(payload)
            conn.execute(
                "INSERT INTO source_corrections (%s) VALUES (%s)"
                % (",".join(columns), ",".join("?" for _ in columns)),
                list(payload.values()),
            )
            applied += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"applied": applied, "unchanged": len(seen_sources) - applied}
