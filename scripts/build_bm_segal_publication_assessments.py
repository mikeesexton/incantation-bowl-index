"""Build the reviewed British Museum → Segal publication-link manifest.

The official BIB3908 relation names 159 related collection objects.  It proves
an object-level publication relationship, but not an exact Segal text number;
the latter remains a separate concordance task.
"""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect


ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "research" / "seeds" / "british_museum_segal_related_159.json"
PUBLICATION_SOURCE = "SRC-72D809FB4249"
EVIDENCE_SOURCE = "SRC-3D4B57D27A24"


def stable_id(object_id):
    digest = hashlib.sha256(
        (object_id + "\0" + PUBLICATION_SOURCE + "\0" + EVIDENCE_SOURCE).encode()
    ).hexdigest()[:12].upper()
    return "IBI-PUBASSESS-" + digest


def registration_value(url):
    key = url.rstrip("/").rsplit("/", 1)[-1]
    return key[2:] if key.startswith("W_") else key


def build(conn, reviewed_at):
    dataset = json.loads(SEED.read_text(encoding="utf-8"))
    if dataset.get("relation_count") != 159 or len(dataset.get("records", [])) != 159:
        raise ValueError("checked British Museum relation seed must contain 159 records")
    entries = []
    for record in dataset["records"]:
        object_key = record["url"].rstrip("/").rsplit("/", 1)[-1]
        rows = conn.execute(
            "SELECT i.object_id FROM identifiers i "
            "JOIN object_source_evidence e ON e.object_id=i.object_id "
            "AND e.source_id=? WHERE i.scheme='British Museum object key' "
            "AND lower(i.normalized_value)=lower(?)",
            (EVIDENCE_SOURCE, object_key),
        ).fetchall()
        object_ids = sorted({row["object_id"] for row in rows})
        if len(object_ids) != 1:
            raise ValueError("expected one object for British Museum key %s" % object_key)
        object_id = object_ids[0]
        if not conn.execute(
            "SELECT 1 FROM object_source_evidence WHERE object_id=? AND source_id=?",
            (object_id, EVIDENCE_SOURCE),
        ).fetchone():
            raise ValueError("relation evidence is missing for %s" % object_id)
        entries.append({
            "id": stable_id(object_id),
            "object_id": object_id,
            "disposition": "linked",
            "publication_source_id": PUBLICATION_SOURCE,
            "evidence_source_id": EVIDENCE_SOURCE,
            "evidence_locator": "Related objects: %s" % registration_value(record["url"]),
            "publication_locator": None,
            "basis": (
                "The British Museum's BIB3908 Related objects relation explicitly "
                "places this collection object under Segal 2000a. This records the "
                "publication link only; it does not infer an exact Segal text number."
            ),
        })
    return {
        "schema_version": 1,
        "reviewed_by": "Codex",
        "reviewed_at": reviewed_at,
        "scope": (
            "All 159 objects in the checked British Museum BIB3908 relation; exact "
            "Segal-number concordances remain separately unresolved where not displayed."
        ),
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    with connect() as conn:
        manifest = build(conn, args.reviewed_at)
    args.destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote %s publication assessments to %s" % (
        len(manifest["entries"]), args.destination,
    ))


if __name__ == "__main__":
    main()
