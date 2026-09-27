"""Build publication links for objects that appear in a scope-reviewed edition.

When a source's current scope review says it is a single-object or corpus
edition, and an object's appearance in it is the edition's own treatment of
that object, the edition is both the evidence and the publication. The seed
lists each pair explicitly; nothing is inferred from scope alone.
"""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect
from bowl_index.scholarship import current_scopes

ROOT = Path(__file__).resolve().parent.parent
EDITION_SCOPES = {"single_object_edition", "corpus_edition"}


def stable_id(object_id, source_id):
    digest = hashlib.sha256((object_id + "\0" + source_id + "\0edition-appearance").encode())
    return "IBI-PUBASSESS-" + digest.hexdigest()[:12].upper()


def build(conn, seed, reviewed_at):
    scopes = current_scopes(conn)
    entries = []
    for record in seed["records"]:
        object_id, source_id = record["object_id"], record["source_id"]
        scope = scopes.get(source_id)
        scope = scope.get("scope") if isinstance(scope, dict) else scope
        if scope not in EDITION_SCOPES:
            raise ValueError("%s is not scope-reviewed as an edition (%r)" % (source_id, scope))
        rows = conn.execute(
            "SELECT DISTINCT a.locator FROM appearances a "
            "JOIN appearance_object_links l ON l.appearance_id=a.id "
            "WHERE a.source_id=? AND l.object_id=? AND l.relation_type<>'rejected'",
            (source_id, object_id),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError("expected one appearance of %s in %s" % (object_id, source_id))
        locator = rows[0]["locator"]
        entries.append({
            "id": stable_id(object_id, source_id),
            "object_id": object_id,
            "disposition": "linked",
            "publication_source_id": source_id,
            "evidence_source_id": source_id,
            "evidence_locator": locator,
            "publication_locator": locator,
            "basis": (
                "The source's current scope review classifies it as a %s, and this object's "
                "appearance at '%s' is the edition's own treatment of it (%s). This records "
                "the publication link only; it adopts no reading, identity or date."
                % (scope.replace("_", " "), locator, record["note"])
            ),
        })
    return {
        "schema_version": 1,
        "reviewed_by": "Claude Code",
        "reviewed_at": reviewed_at,
        "scope": "Unlinked probable/confirmed identities that appear in a scope-reviewed "
                 "edition; %d linked." % len(entries),
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
    args.destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote %d publication assessments to %s" % (len(manifest["entries"]), args.destination))


if __name__ == "__main__":
    main()
