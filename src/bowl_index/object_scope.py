"""Researcher decisions that an object record falls outside (or inside) the corpus."""

from datetime import datetime

STATUSES = {"candidate", "probable", "confirmed", "rejected"}
TYPES = {"whole_bowl", "fragment", "reconstructed", "lost_or_unlocated", "non_bowl", "uncertain"}


def apply_object_scope_reviews(conn, manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 object-scope batch with entries is required")
    decided_by = (manifest.get("decided_by") or "").strip()
    stamp = datetime.fromisoformat((manifest.get("decided_at") or "").replace("Z", "+00:00"))
    if not decided_by or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named decider and UTC timestamp required")
    decided_at = stamp.isoformat(timespec="seconds")
    changed = 0
    with conn:
        for entry in manifest["entries"]:
            review_id = (entry.get("id") or "").strip()
            object_id = (entry.get("object_id") or "").strip()
            status, object_type = entry.get("record_status"), entry.get("object_type")
            basis = (entry.get("basis") or "").strip()
            if not (review_id and object_id and basis):
                raise ValueError("id, object_id and basis are required")
            if status not in STATUSES or object_type not in TYPES:
                raise ValueError("invalid status or object type for %s" % object_id)
            old = conn.execute(
                "SELECT * FROM object_scope_reviews WHERE id=?", (review_id,)
            ).fetchone()
            if old:
                if (old["object_id"], old["record_status"], old["object_type"], old["basis"]) != (
                    object_id, status, object_type, basis
                ):
                    raise ValueError("object scope review ID reused with a changed decision")
                continue
            current = conn.execute(
                "SELECT record_status, object_type FROM objects WHERE id=?", (object_id,)
            ).fetchone()
            if not current:
                raise ValueError("no such object: %s" % object_id)
            if current["record_status"] == "merged":
                raise ValueError("cannot re-scope a merged record: %s" % object_id)
            conn.execute(
                "INSERT INTO object_scope_reviews VALUES (?,?,?,?,?,?,?,?,?)",
                (review_id, object_id, status, object_type, current["record_status"],
                 current["object_type"], basis, decided_by, decided_at),
            )
            conn.execute(
                "UPDATE objects SET record_status=?, object_type=?, updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?", (status, object_type, object_id),
            )
            changed += 1
    return {"entries": len(manifest["entries"]), "changed": changed}
