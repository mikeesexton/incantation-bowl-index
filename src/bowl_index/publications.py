"""Resolve publication-derived identifiers to the publication they designate.

`identifiers.source_id` says who reported a designation. It does not say which
publication the designation belongs to, so the corpus could answer "who told us
this bowl is Isbell no. 8" but not "which bowls does Isbell publish". This module
adds the second relation without disturbing the first.
"""

import re
from datetime import datetime

PUBLICATION_SCHEME = "publication object key"
_TRAILING = re.compile(r"\s+(?:bowl|popularity bowl)\b.*$", re.I)


def publication_key(value):
    """The publication part of an object key such as `Isbell 1975::08`."""
    return _TRAILING.sub("", (value or "").split("::")[0]).strip()


def publication_object_sets(conn):
    """Distinct candidate records per publication, regardless of alias count."""
    objects = {}
    for row in conn.execute(
        "SELECT value, object_id FROM identifiers "
        "WHERE scheme=? AND object_id IS NOT NULL", (PUBLICATION_SCHEME,)
    ):
        key = publication_key(row["value"])
        if key:
            objects.setdefault(key, set()).add(row["object_id"])
    return objects


def publication_keys(conn):
    """Every distinct publication key, with unique candidate-record counts."""
    return {key: len(objects) for key, objects in publication_object_sets(conn).items()}


def current_registry(conn):
    latest = {}
    for row in conn.execute("SELECT * FROM publication_registry ORDER BY rowid"):
        latest[row["publication_key"]] = dict(row)
    return latest


def unresolved_publication_keys(conn):
    """Keys with no registry entry at all — the gap a regression test guards."""
    registry = current_registry(conn)
    return sorted(key for key in publication_keys(conn) if key not in registry)


def publication_coverage(conn):
    keys = publication_keys(conn)
    registry = current_registry(conn)
    resolved = {k for k, r in registry.items() if r["resolution"] == "resolved" and k in keys}
    object_sets = publication_object_sets(conn)
    objects_total = len(set().union(*object_sets.values()))
    objects_resolved = len(set().union(*(object_sets[k] for k in resolved)))
    return {
        "publication_keys": len(keys),
        "publication_keys_resolved": len(resolved),
        "publication_keys_unregistered": len(unresolved_publication_keys(conn)),
        "publication_keys_resolved_pct": len(resolved) / len(keys) if keys else 1,
        "objects_under_a_publication_key": objects_total,
        "objects_under_a_resolved_publication": objects_resolved,
    }


def publication_object_counts(conn):
    """How many objects each resolved publication publishes, per this corpus."""
    keys = publication_keys(conn)
    registry = current_registry(conn)
    rows = []
    for key, n in sorted(keys.items(), key=lambda kv: -kv[1]):
        entry = registry.get(key)
        rows.append({
            "publication_key": key, "objects": n,
            "resolution": entry["resolution"] if entry else "unregistered",
            "source_id": entry["source_id"] if entry else None,
            "blocker": entry["blocker"] if entry else None,
        })
    return rows


def apply_publication_registry(conn, manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 publication-registry batch with entries is required")
    stamp = datetime.fromisoformat(manifest["reviewed_at"].replace("Z", "+00:00"))
    reviewer = (manifest.get("reviewed_by") or "").strip()
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named reviewer and UTC timestamp required")
    known = publication_keys(conn)
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        seen = set()
        planned = []
        for entry in manifest["entries"]:
            key = entry["publication_key"]
            if key in seen:
                raise ValueError("Duplicate publication key in batch: %s" % key)
            seen.add(key)
            if key not in known:
                raise ValueError("No object carries publication key %s" % key)
            resolution = entry["resolution"]
            if resolution not in ("resolved", "unresolved", "not_a_publication"):
                raise ValueError("Invalid resolution for %s" % key)
            if not (entry.get("basis") or "").strip():
                raise ValueError("Every registry decision needs a basis: %s" % key)
            source_id = entry.get("source_id")
            if resolution == "resolved":
                if not source_id or not conn.execute(
                    "SELECT 1 FROM sources WHERE id=?", (source_id,)
                ).fetchone():
                    raise ValueError("Resolved key %s needs an existing source" % key)
            elif resolution == "unresolved" and not (entry.get("blocker") or "").strip():
                raise ValueError("An unresolved key needs a precise blocker: %s" % key)
            values = (entry["registry_id"], key, source_id, resolution, entry["basis"],
                      entry.get("blocker"), reviewer, stamp.isoformat(timespec="seconds"))
            old = conn.execute(
                "SELECT * FROM publication_registry WHERE id=?", (entry["registry_id"],)
            ).fetchone()
            if old:
                if tuple(old) != values:
                    raise ValueError("Registry ID reused with a changed decision: %s" % key)
                continue
            planned.append(values)
        for values in planned:
            conn.execute(
                "INSERT INTO publication_registry VALUES (?,?,?,?,?,?,?,?)", values)
            changed += 1
    return {"entries": len(manifest["entries"]), "changed": changed,
            "unchanged": len(manifest["entries"]) - changed, **publication_coverage(conn)}
