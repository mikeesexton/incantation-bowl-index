"""Store source-reported object relationships without changing physical identity."""

import hashlib
import json
from datetime import datetime
from pathlib import Path


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _fingerprint(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _utc(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Relationship reviews require a UTC timestamp")
    return stamp


def relationship_evidence(conn, entry):
    appearance = conn.execute(
        "SELECT * FROM appearances WHERE id=? AND source_id=?",
        (entry["appearance_id"], entry["source_id"]),
    ).fetchone()
    if not appearance:
        raise ValueError("Source appearance is absent")
    link = conn.execute(
        "SELECT * FROM appearance_object_links WHERE appearance_id=? AND object_id=? "
        "AND relation_type<>'rejected'",
        (entry["appearance_id"], entry["subject_object_id"]),
    ).fetchone()
    if not link:
        raise ValueError("Appearance does not support the subject object")
    source = conn.execute("SELECT * FROM sources WHERE id=?", (entry["source_id"],)).fetchone()
    subject = conn.execute("SELECT * FROM objects WHERE id=?", (entry["subject_object_id"],)).fetchone()
    target = conn.execute("SELECT * FROM objects WHERE id=?", (entry["target_object_id"],)).fetchone()
    if not source or not subject or not target:
        raise ValueError("Relationship source, subject, or target is absent")
    target_identifiers = [dict(row) for row in conn.execute(
        "SELECT * FROM identifiers WHERE object_id=? AND scheme=? AND value=? ORDER BY id",
        (entry["target_object_id"], entry["target_identifier_scheme"],
         entry["target_identifier_value"]),
    )]
    if not target_identifiers:
        raise ValueError("Target identifier does not match the target object")
    claims = [dict(row) for row in conn.execute(
        "SELECT * FROM claims WHERE object_id=? AND appearance_id=? AND source_id=? "
        "AND field='catalogue_description' ORDER BY id",
        (entry["subject_object_id"], entry["appearance_id"], entry["source_id"]),
    )]
    if not claims or not any(entry["raw_statement"] in (row["value_text"] or "") for row in claims):
        raise ValueError("Raw relationship statement is absent from the cited description")
    subject_identifiers = [dict(row) for row in conn.execute(
        "SELECT * FROM identifiers WHERE object_id=? AND source_id=? ORDER BY id",
        (entry["subject_object_id"], entry["source_id"]),
    )]
    return {
        "source": dict(source),
        "appearance": dict(appearance),
        "appearance_link": dict(link),
        "subject": dict(subject),
        "target": dict(target),
        "subject_identifiers": subject_identifiers,
        "target_identifiers": target_identifiers,
        "catalogue_description_claims": claims,
    }


def relationship_evidence_sha256(conn, entry):
    return _fingerprint(relationship_evidence(conn, entry))


def apply_relationship_review(conn, path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("Invalid relationship-review manifest")
    reviewed_by = manifest.get("reviewed_by", "").strip()
    reviewed_at = _utc(manifest["reviewed_at"]).isoformat(timespec="seconds")
    if not reviewed_by or not manifest.get("scope", "").strip():
        raise ValueError("Reviewer and scope are required")
    header = {key: value for key, value in manifest.items() if key != "entries"}
    planned = []
    seen = set()
    with conn:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        for entry in manifest["entries"]:
            if entry["assertion_id"] in seen:
                raise ValueError("Duplicate relationship assertion ID")
            seen.add(entry["assertion_id"])
            if entry["relationship_type"] not in {
                "duplicate_of", "same_as", "part_of", "related_to"
            }:
                raise ValueError("Invalid relationship type")
            if entry["relationship_scope"] not in {
                "physical_identity", "physical_part", "textual", "catalogue", "unclear"
            }:
                raise ValueError("Invalid relationship scope")
            if entry["interpretation_status"] not in {"accepted", "unresolved", "rejected"}:
                raise ValueError("Invalid interpretation status")
            if not entry.get("raw_statement", "").strip() or not entry.get("rationale", "").strip():
                raise ValueError("Raw statement and rationale are required")
            evidence = relationship_evidence(conn, entry)
            digest = _fingerprint(evidence)
            if digest != entry.get("expected_evidence_sha256"):
                raise ValueError("Relationship evidence changed since review snapshot")
            assertion_json = _canonical({"header": header, "entry": entry})
            prior = conn.execute(
                "SELECT assertion_json,evidence_sha256 FROM object_relationship_assertions WHERE id=?",
                (entry["assertion_id"],),
            ).fetchone()
            if prior:
                if prior["assertion_json"] != assertion_json or prior["evidence_sha256"] != digest:
                    raise ValueError("Relationship assertion ID reused with different evidence")
                continue
            planned.append((entry, evidence, digest, assertion_json))
        for entry, evidence, digest, assertion_json in planned:
            conn.execute(
                "INSERT INTO object_relationship_assertions "
                "(id,subject_object_id,target_object_id,source_id,appearance_id,relationship_type,"
                "relationship_scope,target_identifier_scheme,target_identifier_value,raw_statement,"
                "interpretation_status,locator,rationale,reviewed_by,reviewed_at,evidence_sha256,"
                "evidence_json,assertion_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (entry["assertion_id"], entry["subject_object_id"], entry["target_object_id"],
                 entry["source_id"], entry["appearance_id"], entry["relationship_type"],
                 entry["relationship_scope"], entry["target_identifier_scheme"],
                 entry["target_identifier_value"], entry["raw_statement"],
                 entry["interpretation_status"], entry["locator"], entry["rationale"],
                 reviewed_by, reviewed_at, digest, _canonical(evidence), assertion_json),
            )
    return {
        "entries": len(manifest["entries"]),
        "changed": len(planned),
        "unchanged": len(manifest["entries"]) - len(planned),
        "identity_changes": 0,
    }
