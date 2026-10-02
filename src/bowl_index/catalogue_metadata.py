"""Repair copied catalogue pointers with immutable source-bound snapshots.

Identity membership, scholarly text, provenance and rights decisions are outside
this narrow repair path. Earlier import manifests resolve to the corrected
appearance rather than recreating the erroneous pointer or identifier.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

FIELDS = {
    "objects": {"label"},
    "appearances": {"locator", "description"},
    "identifiers": {"value", "normalized_value", "notes"},
    "claims": {"value_text", "locator", "notes"},
}
CLAIM_FIELDS = {"current_or_reported_collection", "identifier_warning", "publication_status"}


def apply_catalogue_metadata(conn, manifest, root):
    from .ingest import normalize_identifier
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("unsupported catalogue correction schema")
    reviewer = manifest.get("reviewed_by", "").strip()
    stamp = manifest.get("reviewed_at", "")
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if not reviewer or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("reviewer and UTC timestamp required")
    relative = Path(manifest["evidence_path"])
    root = Path(root).resolve()
    evidence = (root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not evidence.is_relative_to(root):
        raise ValueError("correction evidence must stay inside project")
    if hashlib.sha256(evidence.read_bytes()).hexdigest() != manifest["evidence_sha256"]:
        raise ValueError("correction evidence changed")
    if conn.in_transaction:
        raise ValueError("correction requires a clean transaction")
    seen = set()
    applied = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            table, before, changes = entry["target_table"], entry["before"], entry["changes"]
            if table not in FIELDS or not changes or set(changes) - FIELDS[table]:
                raise ValueError("only catalogue pointer fields may change")
            target = (table, before["id"])
            if target in seen:
                raise ValueError("duplicate catalogue correction")
            seen.add(target)
            if not entry.get("id") or not entry.get("rationale", "").strip():
                raise ValueError("correction id and rationale required")
            if any(not isinstance(x, str) or not x.strip() for x in changes.values()):
                raise ValueError("nonempty catalogue metadata required")
            source_id = before.get("source_id") or entry.get("source_id")
            if not source_id:
                raise ValueError("source attribution required")
            if table == "objects" and not conn.execute(
                "SELECT 1 FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id "
                "WHERE l.object_id=? AND a.source_id=? AND l.relation_type<>'rejected'",
                (before["id"], source_id),
            ).fetchone():
                raise ValueError("object label correction requires linked source evidence")
            if table == "claims" and before.get("field") not in CLAIM_FIELDS:
                raise ValueError("scholarly and physical claims are outside catalogue repair")
            after = dict(before, **changes)
            if after == before:
                raise ValueError("correction must change metadata")
            if table == "identifiers" and after["normalized_value"] != normalize_identifier(after["scheme"], after["value"]):
                raise ValueError("identifier normalization does not match value")
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (before["id"],)).fetchone()
            if row is None:
                raise ValueError("catalogue row missing")
            payload = dict(id=entry["id"], target_table=table, target_id=before["id"], source_id=source_id,
                           reviewed_by=reviewer, reviewed_at=stamp,
                           evidence_path=manifest["evidence_path"], evidence_sha256=manifest["evidence_sha256"],
                           rationale=entry["rationale"],
                           before_json=json.dumps(before, ensure_ascii=False, sort_keys=True),
                           after_json=json.dumps(after, ensure_ascii=False, sort_keys=True))
            old = conn.execute("SELECT * FROM catalogue_metadata_corrections WHERE id=?", (entry["id"],)).fetchone()
            if old:
                if dict(old) != payload or dict(row) != after:
                    raise ValueError("correction replay differs from recorded evidence")
                continue
            if dict(row) != before:
                raise ValueError("catalogue evidence changed")
            assignments = ",".join(f"{field}=?" for field in changes)
            conn.execute(f"UPDATE {table} SET {assignments} WHERE id=?", list(changes.values()) + [before["id"]])
            columns = list(payload)
            conn.execute("INSERT INTO catalogue_metadata_corrections (%s) VALUES (%s)" %
                         (",".join(columns), ",".join("?" for _ in columns)), list(payload.values()))
            applied += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"applied": applied, "unchanged": len(seen) - applied}


def corrected_appearance(conn, source_id, locator):
    """Resolve an earlier exact source/locator to its current linked appearance."""
    for row in conn.execute("SELECT target_id,before_json FROM catalogue_metadata_corrections WHERE target_table='appearances'"):
        old = json.loads(row["before_json"])
        if old["source_id"] == source_id and old["locator"] == locator:
            current = conn.execute(
                "SELECT l.object_id,a.id AS appearance_id FROM appearances a "
                "JOIN appearance_object_links l ON l.appearance_id=a.id "
                "WHERE a.id=? AND a.source_id=? AND l.relation_type<>'rejected' LIMIT 1",
                (row["target_id"], source_id),
            ).fetchone()
            if current is None:
                raise ValueError("corrected appearance no longer has a usable object link")
            return current
    return None


def corrected_identifier_import(conn, object_id, source_id, scheme, normalized):
    for row in conn.execute("SELECT before_json FROM catalogue_metadata_corrections WHERE target_table='identifiers'"):
        old = json.loads(row["before_json"])
        if (old["object_id"], old["source_id"], old["scheme"], old["normalized_value"]) == (object_id, source_id, scheme, normalized):
            return True
    return False


def corrected_claim_import(conn, object_id, appearance_id, source_id, field, value_text, value_json, locator):
    expected = (object_id, appearance_id, source_id, field, value_text, value_json, locator)
    for row in conn.execute("SELECT before_json FROM catalogue_metadata_corrections WHERE target_table='claims'"):
        old = json.loads(row["before_json"])
        if tuple(old[key] for key in ("object_id", "appearance_id", "source_id", "field", "value_text", "value_json", "locator")) == expected:
            return True
    return False
