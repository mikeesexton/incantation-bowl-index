import json
from pathlib import Path

from .ids import new_id


def seed_queries(conn, config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    inserted = 0
    for platform in config["platforms"]:
        for source_class in platform["source_classes"]:
            for term in config["terms"]:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO search_queries "
                    "(id,source_class,language,query,platform,status,notes) VALUES (?,?,?,?,?,'planned',?)",
                    (
                        new_id("search_query"), source_class, term["language"], term["query"],
                        platform["name"], term.get("notes"),
                    ),
                )
                inserted += int(cursor.rowcount > 0)
    for target in config["coverage_targets"]:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO coverage_targets "
            "(id,source_class,target_name,url,status,notes) VALUES (?,?,?,?,?,?)",
            (
                new_id("coverage"), target["source_class"], target["name"], target.get("url"),
                target.get("status", "planned"), target.get("notes"),
            ),
        )
        inserted += int(cursor.rowcount > 0)
    conn.commit()
    return inserted


def load_search_log(conn, path):
    """Upsert a human-checked JSONL research log into the campaign ledger.

    A log row records a query actually run, not a query merely proposed.  This
    keeps interactive web searches, catalogue browsing, and future automated
    sweeps auditable through the same tables.
    """
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (run_id, "Imported checked discovery log", str(path)),
    )
    count = 0
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            row = json.loads(line)
            required = ("source_class", "query", "platform", "status")
            missing = [key for key in required if not row.get(key)]
            if missing:
                raise ValueError("%s:%s missing %s" % (path, line_number, ", ".join(missing)))
            values = (
                row.get("result_count"), row.get("net_new_candidates"), row["status"],
                row.get("notes"),
            )
            existing = conn.execute(
                "SELECT id FROM search_queries WHERE source_class=? AND language IS ? "
                "AND query=? AND platform=?",
                (row["source_class"], row.get("language"), row["query"], row["platform"]),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE search_queries SET run_id=?,searched_at=coalesce(?,CURRENT_TIMESTAMP),"
                    "result_count=?,net_new_candidates=?,status=?,notes=? WHERE id=?",
                    (run_id, row.get("searched_at")) + values + (existing["id"],),
                )
            else:
                conn.execute(
                    "INSERT INTO search_queries "
                    "(id,run_id,source_class,language,query,platform,searched_at,result_count,"
                    "net_new_candidates,status,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        new_id("search_query"), run_id, row["source_class"], row.get("language"),
                        row["query"], row["platform"], row.get("searched_at"),
                    ) + values,
                )
            count += 1
    conn.execute(
        "UPDATE search_runs SET status='complete',completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (run_id,),
    )
    conn.commit()
    return count


def load_coverage_log(conn, path):
    """Apply a checked, version-controlled coverage assessment."""
    count = 0
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            row = json.loads(line)
            required = ("source_class", "target_name", "status", "notes")
            missing = [key for key in required if not row.get(key)]
            if missing:
                raise ValueError("%s:%s missing %s" % (path, line_number, ", ".join(missing)))
            existing = conn.execute(
                "SELECT id FROM coverage_targets WHERE source_class=? AND target_name=?",
                (row["source_class"], row["target_name"]),
            ).fetchone()
            values = (
                row.get("url"), row["status"], row.get("first_searched_at"),
                row.get("last_searched_at"), row["notes"],
            )
            if existing:
                conn.execute(
                    "UPDATE coverage_targets SET url=coalesce(?,url),status=?,"
                    "first_searched_at=coalesce(?,first_searched_at,CURRENT_TIMESTAMP),"
                    "last_searched_at=coalesce(?,CURRENT_TIMESTAMP),notes=? WHERE id=?",
                    values + (existing["id"],),
                )
            else:
                conn.execute(
                    "INSERT INTO coverage_targets "
                    "(id,source_class,target_name,url,status,first_searched_at,last_searched_at,notes) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (new_id("coverage"), row["source_class"], row["target_name"]) + values,
                )
            count += 1
    conn.commit()
    return count


def load_saturation_log(conn, path):
    """Upsert independently measured broad-sweep results."""
    count = 0
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            row = json.loads(line)
            required = (
                "name", "strategy", "baseline_distinct_objects", "net_new_distinct_objects",
                "revealed_new_source_class", "completed_at", "notes",
            )
            missing = [key for key in required if row.get(key) is None]
            if missing:
                raise ValueError("%s:%s missing %s" % (path, line_number, ", ".join(missing)))
            baseline = int(row["baseline_distinct_objects"])
            net_new = int(row["net_new_distinct_objects"])
            rate = (net_new / baseline) if baseline else 0.0
            conn.execute(
                "INSERT INTO saturation_sweeps "
                "(id,name,strategy,baseline_distinct_objects,net_new_distinct_objects,net_new_rate,"
                "revealed_new_source_class,status,completed_at,notes) VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET strategy=excluded.strategy,"
                "baseline_distinct_objects=excluded.baseline_distinct_objects,"
                "net_new_distinct_objects=excluded.net_new_distinct_objects,"
                "net_new_rate=excluded.net_new_rate,"
                "revealed_new_source_class=excluded.revealed_new_source_class,"
                "status=excluded.status,completed_at=excluded.completed_at,notes=excluded.notes",
                (
                    new_id("search_run"), row["name"], row["strategy"], baseline, net_new, rate,
                    int(bool(row["revealed_new_source_class"])), row.get("status", "complete"),
                    row["completed_at"], row["notes"],
                ),
            )
            count += 1
    conn.commit()
    return count


def load_audit_log(conn, path):
    """Upsert a human verification sample without editing the working DB by hand."""
    count = 0
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            row = json.loads(line)
            required = ("object_id", "stratum", "checked_at", "checked_by", "result")
            missing = [key for key in required if not row.get(key)]
            if missing:
                raise ValueError("%s:%s missing %s" % (path, line_number, ", ".join(missing)))
            if not conn.execute("SELECT 1 FROM objects WHERE id=?", (row["object_id"],)).fetchone():
                raise ValueError("%s:%s unknown object_id %s" % (path, line_number, row["object_id"]))
            conn.execute(
                "INSERT INTO manual_audits "
                "(id,object_id,stratum,checked_at,checked_by,citation_verified,identifier_verified,"
                "claims_source_attributed,result,notes) VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(object_id,stratum) DO UPDATE SET checked_at=excluded.checked_at,"
                "checked_by=excluded.checked_by,citation_verified=excluded.citation_verified,"
                "identifier_verified=excluded.identifier_verified,"
                "claims_source_attributed=excluded.claims_source_attributed,result=excluded.result,"
                "notes=excluded.notes",
                (
                    new_id("search_run"), row["object_id"], row["stratum"], row["checked_at"],
                    row["checked_by"], int(bool(row.get("citation_verified"))),
                    int(bool(row.get("identifier_verified"))),
                    int(bool(row.get("claims_source_attributed"))), row["result"], row.get("notes"),
                ),
            )
            count += 1
    conn.commit()
    return count
