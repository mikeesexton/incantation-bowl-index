"""Build the bounded human queue for public fact wording.

This does not decide copyright status. It selects the projection rows already
classified ``review_source_wording`` and binds each one to the exact value,
source and locator a reviewer must assess.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from bowl_index.projection import Projection


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
# The packet deliberately repeats the source wording under review. Keep
# it beside the private corpus, not in Git; only the builder and aggregate counts
# are checked in.
DEFAULT_OUT = ROOT / "data" / "private" / "reviews" / "public_fact_wording_review_2026-09-20.json"


def fingerprint(row):
    evidence = {key: row[key] for key in (
        "object_id", "field", "value", "source_id", "locator",
    )}
    return hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    projection = Projection(conn)
    sources = {row["id"]: row for row in projection.table("sources")}
    objects = {row["id"]: row for row in projection.table("objects")}
    facet_index = {}
    for row in projection.table("facets"):
        key = (row["object_id"], row["source_field"], row["source_id"], row["locator"])
        facet_index.setdefault(key, set()).add(row["facet_label"])

    entries = []
    # This is a private review builder, so it reads the pre-gate candidates. The
    # public ``facts`` table has already removed the rows selected below.
    for row in projection._fact_candidates():
        if row["release_class"] != "review_source_wording":
            continue
        key = (row["object_id"], row["field"], row["source_id"], row["locator"])
        source = sources[row["source_id"]]
        entries.append({
            "evidence_sha256": fingerprint(row),
            "object_id": row["object_id"],
            "object_label": objects[row["object_id"]]["label"],
            "source_id": row["source_id"],
            "source_title": source["title"],
            "source_year": source["issued_year"],
            "source_rights_status": next(
                item["rights_status"] for item in conn.execute(
                    "SELECT rights_status FROM sources WHERE id=?", (row["source_id"],)
                )
            ),
            "field": row["field"],
            "value": row["value"],
            "characters": len(row["value"]),
            "certainty": row["certainty"],
            "locator": row["locator"],
            "controlled_labels": sorted(facet_index.get(key, set())),
            "suggested_handling": (
                "publish_controlled_labels_and_review_raw"
                if facet_index.get(key) else "review_or_replace_with_project_summary"
            ),
            "owner_disposition": None,
            "owner_note": None,
        })
    entries.sort(key=lambda row: (
        row["source_title"].casefold(), row["object_label"].casefold(), row["field"]
    ))
    state = json.loads((ROOT / "data" / "db-state.json").read_text(encoding="utf-8"))
    packet = {
        "schema_version": 1,
        "purpose": "Human review of non-public-domain source wording before open release",
        "corpus_state_digest": state["corpus_digest"],
        "generated_date": "2026-09-20",
        "allowed_dispositions": [
            "publish_raw_factual_claim", "publish_project_summary", "omit_raw_value",
        ],
        "note": (
            "A disposition is a project-owner release decision, not a correction to the source claim. "
            "The controlled label may remain public when raw wording is omitted."
        ),
        "entries": entries,
    }
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": str(destination), "entries": len(entries)}, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
