"""Evidence-bound object-level publication links and research dispositions."""

from datetime import datetime


DISPOSITIONS = {"linked", "no_known_edition", "unresolved"}
_COLUMNS = (
    "id", "object_id", "disposition", "publication_source_id",
    "evidence_source_id", "evidence_locator", "publication_locator", "basis",
    "reviewed_by", "reviewed_at", "supersedes_id",
)


def current_publication_assessments(conn):
    """Return leaf reviews; history remains available in the underlying table."""
    return [dict(row) for row in conn.execute(
        "SELECT p.* FROM publication_assessments p "
        "LEFT JOIN publication_assessments newer ON newer.supersedes_id=p.id "
        "WHERE newer.id IS NULL ORDER BY p.object_id,p.publication_source_id,p.id"
    )]


def _object_has_source_evidence(conn, object_id, source_id):
    return bool(conn.execute(
        "SELECT 1 FROM object_source_evidence "
        "WHERE object_id=? AND source_id=? "
        "UNION SELECT 1 FROM appearance_object_links l "
        "JOIN appearances a ON a.id=l.appearance_id "
        "WHERE l.object_id=? AND a.source_id=? AND l.relation_type<>'rejected' LIMIT 1",
        (object_id, source_id, object_id, source_id),
    ).fetchone())


def apply_publication_assessments(conn, manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 publication-assessment batch with entries is required")
    reviewer = (manifest.get("reviewed_by") or "").strip()
    stamp = datetime.fromisoformat((manifest.get("reviewed_at") or "").replace("Z", "+00:00"))
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named reviewer and UTC timestamp required")
    reviewed_at = stamp.isoformat(timespec="seconds")
    if conn.in_transaction:
        raise ValueError("publication assessment requires a clean transaction")

    changed = 0
    seen_ids, seen_targets = set(), set()
    conn.execute("BEGIN IMMEDIATE")
    try:
        for entry in manifest["entries"]:
            assessment_id = (entry.get("id") or "").strip()
            object_id = (entry.get("object_id") or "").strip()
            disposition = (entry.get("disposition") or "").strip()
            publication_source_id = (entry.get("publication_source_id") or "").strip() or None
            evidence_source_id = (entry.get("evidence_source_id") or "").strip()
            evidence_locator = (entry.get("evidence_locator") or "").strip()
            publication_locator = (entry.get("publication_locator") or "").strip() or None
            basis = (entry.get("basis") or "").strip()
            supersedes_id = (entry.get("supersedes_id") or "").strip() or None
            target = (object_id, publication_source_id or "disposition")
            if not all((assessment_id, object_id, evidence_source_id, evidence_locator, basis)):
                raise ValueError("assessment, object, evidence source, locator and basis are required")
            if disposition not in DISPOSITIONS:
                raise ValueError("invalid publication disposition: %s" % disposition)
            if disposition == "linked" and not publication_source_id:
                raise ValueError("linked assessments require a publication source")
            if disposition != "linked" and (publication_source_id or publication_locator):
                raise ValueError("non-published dispositions cannot name a publication")
            if assessment_id in seen_ids or target in seen_targets:
                raise ValueError("duplicate assessment ID or target in batch")
            seen_ids.add(assessment_id); seen_targets.add(target)
            if not conn.execute("SELECT 1 FROM objects WHERE id=?", (object_id,)).fetchone():
                raise ValueError("No such object: %s" % object_id)
            for source_id, label in (
                (evidence_source_id, "evidence"),
                (publication_source_id, "publication"),
            ):
                if source_id and not conn.execute(
                    "SELECT 1 FROM sources WHERE id=?", (source_id,)
                ).fetchone():
                    raise ValueError("No such %s source: %s" % (label, source_id))
            if not _object_has_source_evidence(conn, object_id, evidence_source_id):
                raise ValueError("evidence source is not linked to object: %s" % object_id)

            payload = {
                "id": assessment_id, "object_id": object_id,
                "disposition": disposition,
                "publication_source_id": publication_source_id,
                "evidence_source_id": evidence_source_id,
                "evidence_locator": evidence_locator,
                "publication_locator": publication_locator,
                "basis": basis, "reviewed_by": reviewer,
                "reviewed_at": reviewed_at, "supersedes_id": supersedes_id,
            }
            old = conn.execute(
                "SELECT * FROM publication_assessments WHERE id=?", (assessment_id,)
            ).fetchone()
            if old:
                if dict(old) != payload:
                    raise ValueError("assessment ID reused with changed evidence: %s" % assessment_id)
                continue
            current = conn.execute(
                "SELECT p.id FROM publication_assessments p "
                "LEFT JOIN publication_assessments newer ON newer.supersedes_id=p.id "
                "WHERE p.object_id=? AND coalesce(p.publication_source_id,'')=coalesce(?, '') "
                "AND newer.id IS NULL",
                (object_id, publication_source_id),
            ).fetchall()
            current_ids = [row["id"] for row in current]
            if len(current_ids) > 1:
                raise ValueError("publication target has multiple current assessments")
            if current_ids and supersedes_id != current_ids[0]:
                raise ValueError("new assessment must supersede the current target")
            if not current_ids and supersedes_id:
                raise ValueError("superseded assessment is not current for this target")
            conn.execute(
                "INSERT INTO publication_assessments (%s) VALUES (%s)" % (
                    ",".join(_COLUMNS), ",".join("?" for _ in _COLUMNS)),
                [payload[column] for column in _COLUMNS],
            )
            changed += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    rows = current_publication_assessments(conn)
    return {
        "entries": len(manifest["entries"]), "changed": changed,
        "current": len(rows),
        "linked": sum(row["disposition"] == "linked" for row in rows),
        "no_known_edition": sum(
            row["disposition"] == "no_known_edition" for row in rows),
    }
