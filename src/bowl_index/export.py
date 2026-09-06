import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import write_identity_export


EXPORT_TABLES = (
    "sources", "captures", "search_runs", "search_queries", "coverage_targets", "saturation_sweeps", "manual_audits", "objects",
    "appearances", "appearance_object_links", "identifiers", "claims", "texts", "events", "media",
    "leads", "dedupe_candidates", "dedupe_evidence", "claim_conflict_reviews", "claim_conflict_review_history", "text_proofreading_reviews", "media_rights_reviews", "claim_locator_corrections", "source_corrections", "museum_concordance_reviews", "object_relationship_assertions", "merge_log",
)


def _public_rows(table, rows):
    """Redact text payloads; this is not a complete public-release review."""
    redactions = {}
    if table == "text_proofreading_reviews":
        for row in rows:
            row["before_json"] = None
            row["after_json"] = None
        redactions["redacted_text_snapshots"] = len(rows)
    if table == "texts":
        for row in rows:
            if not bool(row.get("public_ok")):
                row["content"] = None
                redactions["redacted_contents"] = redactions.get("redacted_contents", 0) + 1
    if table == "appearances":
        for row in rows:
            if row.get("raw_json") is not None:
                row["raw_json"] = None
                redactions["redacted_raw_json"] = redactions.get("redacted_raw_json", 0) + 1
    return rows, redactions


def export_all(conn, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "export_policy": (
            "Research snapshot, not cleared for public release: text content is included only when public_ok is true; "
            "restricted rows retain their identifiers, source links, and rights metadata. "
            "Raw source payloads remain private. Media URLs, capture metadata, and free-text "
            "fields require a separate release review."
        ),
        "tables": {},
    }
    for table in EXPORT_TABLES:
        rows = [dict(row) for row in conn.execute("SELECT * FROM %s ORDER BY rowid" % table)]
        rows, redactions = _public_rows(table, rows)
        jsonl_path = destination / (table + ".jsonl")
        with jsonl_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        csv_path = destination / (table + ".csv")
        columns = list(rows[0].keys()) if rows else [col[1] for col in conn.execute("PRAGMA table_info(%s)" % table)]
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        manifest["tables"][table] = {
            "rows": len(rows), "jsonl": jsonl_path.name, "csv": csv_path.name
        }
        manifest["tables"][table].update(redactions)
    manifest["tables"]["identity_clusters"] = write_identity_export(conn, destination)
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
