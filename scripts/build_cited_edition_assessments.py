"""Build publication links where a held secondary source names an object's edition.

Each seed row pairs an object with the exact appearance locator in a held source
that cites the edition publishing it (for example, a footnote giving author,
title and page). The locator must match an existing appearance of that object
in the evidence source; nothing is inferred beyond what the row states.
"""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect


def stable_id(object_id, publication_source, evidence_source):
    digest = hashlib.sha256(
        (object_id + "\0" + publication_source + "\0" + evidence_source).encode()
    ).hexdigest()[:12].upper()
    return "IBI-PUBASSESS-" + digest


def build(conn, seed, reviewed_at):
    entries = []
    for row in seed["records"]:
        found = conn.execute(
            "SELECT 1 FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id "
            "WHERE a.source_id=? AND a.locator=? AND l.object_id=? AND l.relation_type<>'rejected'",
            (row["evidence_source_id"], row["evidence_locator"], row["object_id"]),
        ).fetchone()
        if not found:
            raise ValueError("no appearance %r for %s" % (row["evidence_locator"], row["object_id"]))
        if not conn.execute("SELECT 1 FROM sources WHERE id=?", (row["publication_source_id"],)).fetchone():
            raise ValueError("no publication source %s" % row["publication_source_id"])
        entries.append({
            "id": stable_id(row["object_id"], row["publication_source_id"], row["evidence_source_id"]),
            "object_id": row["object_id"],
            "disposition": "linked",
            "publication_source_id": row["publication_source_id"],
            "evidence_source_id": row["evidence_source_id"],
            "evidence_locator": row["evidence_locator"],
            "publication_locator": row.get("publication_locator"),
            "basis": row["basis"] + " This records the publication link only; it adopts no reading and merges no identity.",
        })
    return {
        "schema_version": 1,
        "reviewed_by": seed["prepared_by"],
        "reviewed_at": reviewed_at,
        "scope": seed["scope"],
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    with connect() as conn:
        manifest = build(conn, seed, args.reviewed_at)
    args.destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote %d publication assessments to %s" % (len(manifest["entries"]), args.destination))


if __name__ == "__main__":
    main()
