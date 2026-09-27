"""Build the reviewed Waller 2022 → edition publication-link manifest.

Waller's Table of Distribution (printed pp. 155-161) groups each bowl under the
publication that edits it. For bowls the corpus knows only by their Waller
table designation, that statement is the evidence for an object-level
publication link. Rows whose cited work has no single matching source record
are held in the seed and reported, never linked by guesswork.
"""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect


ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "research" / "seeds" / "waller_2022_table_of_distribution_publications.json"
EVIDENCE_SOURCE = "SRC-73C44B143A9D"


def stable_id(object_id, publication_source):
    digest = hashlib.sha256(
        (object_id + "\0" + publication_source + "\0" + EVIDENCE_SOURCE).encode()
    ).hexdigest()[:12].upper()
    return "IBI-PUBASSESS-" + digest


def build(conn, reviewed_at):
    dataset = json.loads(SEED.read_text(encoding="utf-8"))
    if dataset.get("source_id") != EVIDENCE_SOURCE:
        raise ValueError("seed must be transcribed from Waller 2022")
    entries, held = [], []
    for record in dataset["records"]:
        locator = "p. %s, distribution table, %s" % (record["page"], record["designation"])
        rows = conn.execute(
            "SELECT DISTINCT l.object_id FROM appearances a "
            "JOIN appearance_object_links l ON l.appearance_id=a.id "
            "WHERE a.source_id=? AND a.locator=? AND l.relation_type<>'rejected'",
            (EVIDENCE_SOURCE, locator),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError("expected one object for Waller locator %r" % locator)
        object_id = rows[0]["object_id"]
        if record.get("hold"):
            held.append({"object_id": object_id, "designation": record["designation"],
                         "reason": record["hold"]})
            continue
        publication_source = record["publication_source_id"]
        basis = (
            "Waller 2022's Table of Distribution lists this bowl as '%s', naming the "
            "publication that edits it. This records the publication link only; it "
            "does not adopt Waller's or the edition's reading." % record["waller_citation"]
        )
        if record.get("resolution"):
            basis += " " + record["resolution"]
        entries.append({
            "id": stable_id(object_id, publication_source),
            "object_id": object_id,
            "disposition": "linked",
            "publication_source_id": publication_source,
            "evidence_source_id": EVIDENCE_SOURCE,
            "evidence_locator": locator,
            "publication_locator": record["publication_locator"],
            "basis": basis,
        })
    return {
        "schema_version": 1,
        "reviewed_by": "Claude Code",
        "reviewed_at": reviewed_at,
        "scope": (
            "Waller 2022 Table of Distribution designations lacking a publication "
            "link on 2026-09-27; %d linked, %d held for missing or ambiguous "
            "publication source records." % (len(entries), len(held))
        ),
        "entries": entries,
    }, held


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    with connect() as conn:
        manifest, held = build(conn, args.reviewed_at)
    args.destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote %s publication assessments to %s" % (
        len(manifest["entries"]), args.destination,
    ))
    print(json.dumps(held, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
