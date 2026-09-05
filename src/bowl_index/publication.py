"""Evidence-bound publication decisions for stored texts.

A source's copyright label is not a publication decision. Montgomery 1913 is out
of copyright, but the row stored here is a normalized reading text produced from
a scan, and its editorial state has to be declared before it is published. The
fingerprint covers the content, so a later proofreading revision revokes the
approval rather than silently carrying it forward.
"""

import hashlib
import json
from datetime import datetime


DECISIONS = ("needs_review", "withhold", "approved")
BASES = ("public_domain_expired", "open_license", "permission", "own_work", "not_established")


def text_evidence(conn):
    return {row["id"]: dict(row) for row in conn.execute(
        "SELECT t.id,t.object_id,t.source_id,t.text_type,t.language,t.script,t.content,t.editor,"
        "t.locator,t.rights_status,s.title source_title,s.citation source_citation,s.url source_url,"
        "s.doi source_doi,s.issued_year source_year,s.access_status source_access_status,"
        "s.rights_status source_rights_status "
        "FROM texts t JOIN sources s ON s.id=t.source_id")}


def text_fingerprint(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def current_text_reviews(conn):
    evidence = text_evidence(conn)
    latest = {}
    for row in conn.execute("SELECT * FROM text_publication_reviews ORDER BY rowid"):
        latest[row["text_id"]] = dict(row)
    return {key: value for key, value in latest.items()
            if key in evidence and value["evidence_sha256"] == text_fingerprint(evidence[key])}


def sync_public_ok(conn):
    """Recompute texts.public_ok from currently valid approvals.

    Self-healing in both directions: an approval whose text has since been
    revised no longer fingerprints, so the text falls back to withheld.
    """
    approved = {key for key, review in current_text_reviews(conn).items()
                if review["publication_decision"] == "approved"}
    changed = 0
    for row in conn.execute("SELECT id,public_ok FROM texts"):
        wanted = 1 if row["id"] in approved else 0
        if row["public_ok"] != wanted:
            conn.execute("UPDATE texts SET public_ok=? WHERE id=?", (wanted, row["id"]))
            changed += 1
    return {"approved": len(approved), "public_ok_changed": changed}


def apply_publication_batch(conn, manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 publication batch with entries is required")
    stamp = datetime.fromisoformat(manifest["reviewed_at"].replace("Z", "+00:00"))
    reviewer = (manifest.get("reviewed_by") or "").strip()
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named reviewer and UTC timestamp required")
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        evidence = text_evidence(conn)
        planned, seen = [], set()
        for entry in manifest["entries"]:
            text_id = entry["text_id"]
            if text_id in seen or text_id not in evidence:
                raise ValueError("Duplicate or absent text: %s" % text_id)
            seen.add(text_id)
            if text_fingerprint(evidence[text_id]) != entry["evidence_sha256"]:
                raise ValueError("Text evidence changed since review: %s" % text_id)
            decision = entry["publication_decision"]
            basis = entry["rights_basis"]
            if decision not in DECISIONS or basis not in BASES:
                raise ValueError("Invalid decision or rights basis for %s" % text_id)
            if not (entry.get("rationale") or "").strip():
                raise ValueError("Every publication decision needs a rationale")
            if decision == "needs_review" and not (entry.get("followup") or "").strip():
                raise ValueError("An unresolved text needs an explicit follow-up")
            if decision == "approved":
                if basis == "not_established":
                    raise ValueError("Cannot approve a text whose rights basis is not established")
                for key in ("rights_locator", "attribution", "editorial_status"):
                    if not (entry.get(key) or "").strip():
                        raise ValueError("Approval requires %s for %s" % (key, text_id))
            values = (
                entry["review_id"], text_id, entry["evidence_sha256"], basis,
                entry.get("rights_locator"), entry.get("license_url"), decision,
                entry.get("attribution"), entry.get("editorial_status"), reviewer,
                stamp.isoformat(timespec="seconds"), entry["rationale"], entry.get("followup"),
            )
            old = conn.execute(
                "SELECT * FROM text_publication_reviews WHERE id=?", (entry["review_id"],)
            ).fetchone()
            if old:
                if tuple(old) != values:
                    raise ValueError("Publication review ID reused with a changed decision")
                continue
            planned.append(values)
        for values in planned:
            conn.execute(
                "INSERT INTO text_publication_reviews VALUES (%s)" % ",".join("?" for _ in values),
                values,
            )
            changed += 1
        synced = sync_public_ok(conn)
    return {"entries": len(manifest["entries"]), "changed": changed,
            "unchanged": len(manifest["entries"]) - changed, **synced}


def publication_metrics(conn):
    reviews = current_text_reviews(conn)
    total = conn.execute("SELECT count(*) FROM texts").fetchone()[0]
    decided = sum(r["publication_decision"] in ("approved", "withhold") for r in reviews.values())
    return {
        "texts": total,
        "texts_with_current_publication_review": len(reviews),
        "texts_publication_decided": decided,
        "texts_approved": sum(r["publication_decision"] == "approved" for r in reviews.values()),
        "texts_awaiting_publication_review": total - decided,
    }
