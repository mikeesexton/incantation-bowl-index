"""Evidence-bound identity and extraction accuracy reviews for QA-003."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .ids import new_id
from .identity import identity_rows


CHECK_STATES = {"verified", "error", "not_reverifiable", "not_applicable"}
OUTCOMES = {"verified", "verified_with_notes", "error", "indeterminate"}


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _row_dicts(conn, statement, params=()):
    return [dict(row) for row in conn.execute(statement, params)]


def _selection_evidence_snapshot(conn, item):
    member_ids = item["member_ids"]
    placeholders = ",".join("?" for _ in member_ids)
    source_ids = sorted({row[0] for row in conn.execute(
        "SELECT DISTINCT a.source_id FROM appearance_object_links l "
        "JOIN appearances a ON a.id=l.appearance_id "
        "WHERE l.relation_type<>'rejected' AND l.object_id IN (%s) "
        "UNION SELECT DISTINCT source_id FROM claims WHERE object_id IN (%s)" % (
            placeholders, placeholders,
        ), member_ids + member_ids,
    )})
    source_placeholders = ",".join("?" for _ in source_ids)
    dedupe = _row_dicts(
        conn,
        "SELECT * FROM dedupe_candidates WHERE object_a_id IN (%s) "
        "AND object_b_id IN (%s) AND status='same_object' "
        "ORDER BY object_a_id,object_b_id,id" % (placeholders, placeholders),
        member_ids + member_ids,
    )
    dedupe_ids = [row["id"] for row in dedupe]
    dedupe_placeholders = ",".join("?" for _ in dedupe_ids)
    payload = {
        "selection": {
        key: item[key]
        for key in (
            "identity_id", "canonical_object_id", "member_ids", "record_status",
            "linkage_method", "source_family", "source_ids", "identifiers",
        )
        },
        "objects": _row_dicts(
            conn, "SELECT * FROM objects WHERE id IN (%s) ORDER BY id" % placeholders,
            member_ids,
        ),
        "sources": _row_dicts(
            conn, "SELECT * FROM sources WHERE id IN (%s) ORDER BY id" % source_placeholders,
            source_ids,
        ) if source_ids else [],
        "captures": _row_dicts(
            conn, "SELECT * FROM captures WHERE source_id IN (%s) ORDER BY source_id,id"
            % source_placeholders, source_ids,
        ) if source_ids else [],
        "appearances": _row_dicts(
            conn,
            "SELECT a.*,l.object_id,l.relation_type,l.confidence,l.rationale "
            "FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id "
            "WHERE l.object_id IN (%s) ORDER BY a.source_id,a.locator,l.object_id,a.id"
            % placeholders, member_ids,
        ),
        "identifiers": _row_dicts(
            conn, "SELECT * FROM identifiers WHERE object_id IN (%s) "
            "ORDER BY object_id,scheme,normalized_value,id" % placeholders, member_ids,
        ),
        "claims": _row_dicts(
            conn, "SELECT * FROM claims WHERE object_id IN (%s) "
            "ORDER BY object_id,field,source_id,locator,id" % placeholders, member_ids,
        ),
        "dedupe_decisions": dedupe,
        "dedupe_evidence": _row_dicts(
            conn, "SELECT * FROM dedupe_evidence WHERE dedupe_id IN (%s) "
            "ORDER BY dedupe_id,id" % dedupe_placeholders, dedupe_ids,
        ) if dedupe_ids else [],
    }
    return payload


def _selection_evidence_digest(conn, item):
    return _sha256_bytes(
        json.dumps(
            _selection_evidence_snapshot(conn, item), ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
    )


def _current_snapshot(conn, selected):
    rows = {row["identity_id"]: row for row in identity_rows(conn)}
    identity = rows.get(selected["identity_id"])
    if not identity:
        raise ValueError("Selected identity no longer exists: %s" % selected["identity_id"])
    member_ids = json.loads(identity["member_ids_json"])
    placeholders = ",".join("?" for _ in member_ids)
    source_ids = sorted({row[0] for row in conn.execute(
        "SELECT DISTINCT a.source_id FROM appearance_object_links l "
        "JOIN appearances a ON a.id=l.appearance_id "
        "WHERE l.relation_type<>'rejected' AND l.object_id IN (%s) "
        "UNION SELECT DISTINCT source_id FROM claims WHERE object_id IN (%s)" % (
            placeholders, placeholders,
        ), member_ids + member_ids,
    )})
    current = {
        "identity_id": identity["identity_id"],
        "canonical_object_id": identity["canonical_object_id"],
        "member_ids": member_ids,
        "record_status": identity["record_status"],
        # These classifications are properties of the checked selection design.
        # Recompute their inputs above and retain the selected labels; any member,
        # source, status, canonical record, or identifier change invalidates the hash.
        "linkage_method": selected["linkage_method"],
        "source_family": selected["source_family"],
        "source_ids": source_ids,
        "identifiers": json.loads(identity["identifiers_json"]),
    }
    return current


def apply_accuracy_audit(conn, review_path, project_root):
    review_path = Path(review_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("schema_version") != 1:
        raise ValueError("Accuracy audit manifest must use schema_version 1")
    reviewed_by = review.get("reviewed_by", "").strip()
    stamp = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    if not reviewed_by or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Reviewer and UTC review timestamp are required")
    selection_path = Path(project_root) / review["selection_manifest"]
    selection_bytes = selection_path.read_bytes()
    if _sha256_bytes(selection_bytes) != review["selection_manifest_sha256"]:
        raise ValueError("Selection manifest hash changed")
    selection = json.loads(selection_bytes)
    if selection["audit_id"] != review["audit_id"]:
        raise ValueError("Audit ID does not match the selection manifest")
    selected = {}
    for role in ("representative", "high_risk"):
        for item in selection[role]:
            selected[(role, item["identity_id"])] = item
    entries = review.get("entries", [])
    if not entries:
        raise ValueError("Accuracy audit manifest has no review entries")
    seen = set()
    planned = []
    for entry in entries:
        key = (entry["sample_role"], entry["identity_id"])
        if key in seen or key not in selected:
            raise ValueError("Duplicate or unselected audit identity: %s" % (key,))
        seen.add(key)
        selected_item = selected[key]
        current = _current_snapshot(conn, selected_item)
        current_digest = _selection_evidence_digest(conn, current)
        if current_digest != selected_item["evidence_sha256"]:
            raise ValueError("Selected identity evidence changed: %s" % entry["identity_id"])
        if entry.get("selection_evidence_sha256") != current_digest:
            raise ValueError("Review is not bound to current selection evidence")
        outcome = entry["outcome"]
        if outcome not in OUTCOMES:
            raise ValueError("Invalid accuracy audit outcome")
        checks = {
            name: entry[name]
            for name in ("citation_check", "identifier_check", "identity_check", "claim_check")
        }
        if any(value not in CHECK_STATES for value in checks.values()):
            raise ValueError("Invalid accuracy audit check state")
        errors = entry.get("error_categories", [])
        if any(value == "error" for value in checks.values()) != (outcome == "error"):
            raise ValueError("Error outcome must match check-level errors")
        if outcome == "error" and not errors:
            raise ValueError("Error outcomes require at least one error category")
        if outcome != "error" and errors:
            raise ValueError("Non-error outcomes cannot carry error categories")
        evidence = entry.get("evidence", [])
        notes = entry.get("notes", "").strip()
        if not evidence or not notes:
            raise ValueError("Every accuracy review requires evidence and notes")
        snapshot = {
            "audit_id": review["audit_id"], "sample_role": key[0],
            "identity_id": key[1], "selection_evidence_sha256": current_digest,
            "reviewed_by": reviewed_by, "reviewed_at": stamp.isoformat(timespec="seconds"),
            "outcome": outcome, **checks, "error_categories": errors,
            "evidence": evidence, "notes": notes,
        }
        review_sha = _sha256_bytes(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
        )
        planned.append((selected_item, snapshot, review_sha))

    changed = 0
    with conn:
        for selected_item, snapshot, review_sha in planned:
            prior = conn.execute(
                "SELECT r.* FROM accuracy_audit_reviews r "
                "WHERE r.audit_id=? AND r.sample_role=? AND r.identity_id=? "
                "AND NOT EXISTS (SELECT 1 FROM accuracy_audit_reviews n WHERE n.supersedes_id=r.id) "
                "ORDER BY r.rowid DESC LIMIT 1",
                (snapshot["audit_id"], snapshot["sample_role"], snapshot["identity_id"]),
            ).fetchone()
            if prior and prior["review_sha256"] == review_sha:
                continue
            conn.execute(
                "INSERT INTO accuracy_audit_reviews "
                "(id,audit_id,sample_role,identity_id,canonical_object_id,member_ids_json,stratum,"
                "selection_evidence_sha256,reviewed_by,reviewed_at,outcome,citation_check,"
                "identifier_check,identity_check,claim_check,error_categories_json,evidence_json,"
                "notes,review_sha256,supersedes_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    new_id("accuracy_audit_review"), snapshot["audit_id"],
                    snapshot["sample_role"], snapshot["identity_id"],
                    selected_item["canonical_object_id"],
                    json.dumps(selected_item["member_ids"], ensure_ascii=False, sort_keys=True),
                    selected_item["stratum"], snapshot["selection_evidence_sha256"],
                    snapshot["reviewed_by"], snapshot["reviewed_at"], snapshot["outcome"],
                    snapshot["citation_check"], snapshot["identifier_check"],
                    snapshot["identity_check"], snapshot["claim_check"],
                    json.dumps(snapshot["error_categories"], ensure_ascii=False, sort_keys=True),
                    json.dumps(snapshot["evidence"], ensure_ascii=False, sort_keys=True),
                    snapshot["notes"], review_sha, prior["id"] if prior else None,
                ),
            )
            changed += 1
    return {"entries": len(entries), "changed": changed, "unchanged": len(entries) - changed}
