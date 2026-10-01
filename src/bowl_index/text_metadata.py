"""Evidence-bound metadata repairs; never replace or manufacture an inscription."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .proofreading import text_fingerprint


def declared_summary(item):
    """Use explicit editorial declarations, never infer from an incantation's prose."""
    editor = item.get("editor") or ""
    notes = item.get("notes") or ""
    return bool(re.search(r"^(?:discovery summary|summary of|paraphrase of)\b", editor, re.I)
                or re.search(r",\s*summarized\s*$", editor, re.I)
                or re.search(r"\bdiscovery(?:-pass)? (?:summary|paraphrase|paraphrased)\b", notes, re.I))


def validate_text_classification(item):
    if item.get("text_type") == "translation" and declared_summary(item):
        raise ValueError("declared summary or paraphrase must use text_type summary, not translation")


def apply_text_metadata(conn, manifest, root):
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported text metadata schema")
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
    applied = 0
    seen = set()
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            changes = entry.get("changes", {})
            text_id = entry["text_id"]
            if text_id in seen:
                raise ValueError("duplicate text correction")
            seen.add(text_id)
            if not entry.get("id") or not entry.get("rationale", "").strip():
                raise ValueError("correction id and rationale required")
            if not changes or set(changes) - {"text_type", "locator"}:
                raise ValueError("only text_type and locator may change")
            if any(not isinstance(value, str) or not value.strip() for value in changes.values()):
                raise ValueError("nonempty metadata values required")
            row = conn.execute("SELECT * FROM texts WHERE id=?", (text_id,)).fetchone()
            if row is None:
                raise ValueError("text missing")
            current = dict(row)
            base = {
                "id": entry["id"], "text_id": text_id,
                "reviewed_by": reviewer, "reviewed_at": stamp,
                "evidence_path": manifest["evidence_path"],
                "evidence_sha256": manifest["evidence_sha256"],
                "expected_text_sha256": entry["expected_text_sha256"],
                "changes_json": json.dumps(changes, ensure_ascii=False, sort_keys=True),
                "rationale": entry["rationale"],
            }
            old = conn.execute("SELECT * FROM text_metadata_corrections WHERE id=?", (entry["id"],)).fetchone()
            if old:
                recorded_after = json.loads(old["after_json"])
                # Publication administration can be recomputed independently.
                current.pop("public_ok", None)
                recorded_after.pop("public_ok", None)
                if any(old[key] != value for key, value in base.items()) or current != recorded_after:
                    raise ValueError("correction replay differs from recorded evidence")
                continue
            if text_fingerprint(row) != entry["expected_text_sha256"]:
                raise ValueError("text evidence changed")
            after = dict(current, **changes, public_ok=0)
            if all(current[key] == value for key, value in changes.items()):
                raise ValueError("correction must change metadata")
            validate_text_classification(after)
            assignments = ",".join(f"{field}=?" for field in changes)
            conn.execute(f"UPDATE texts SET {assignments},public_ok=0 WHERE id=?",
                         list(changes.values()) + [text_id])
            payload = dict(base,
                           before_json=json.dumps(current, ensure_ascii=False, sort_keys=True),
                           after_json=json.dumps(after, ensure_ascii=False, sort_keys=True))
            columns = list(payload)
            conn.execute("INSERT INTO text_metadata_corrections (%s) VALUES (%s)" %
                         (",".join(columns), ",".join("?" for _ in columns)), list(payload.values()))
            applied += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"applied": applied, "unchanged": len(seen) - applied}


def previously_corrected_import(conn, object_id, appearance_id, source_id, item, locator):
    """Do not recreate a retained draft superseded by a source-bound repair.

    Both the imported original and intermediate proofreading revisions remain
    in the append-only snapshots. Match only the same source appearance, type,
    content and locator; a different witness or new reading is still importable.
    """
    for table in ("text_metadata_corrections", "text_proofreading_reviews"):
        snapshots = conn.execute(
            f"SELECT c.before_json,c.after_json FROM {table} c "
            "JOIN texts t ON t.id=c.text_id WHERE t.object_id=? AND t.appearance_id=? AND t.source_id=?",
            (object_id, appearance_id, source_id),
        )
        for row in snapshots:
            for field in ("before_json", "after_json"):
                snapshot = json.loads(row[field])
                if (snapshot["text_type"] == item["text_type"]
                        and snapshot["content"] == item["content"]
                        and snapshot["locator"] == locator):
                    return True
    return False
