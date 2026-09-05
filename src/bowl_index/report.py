from datetime import datetime, timezone
from pathlib import Path


from .identity import unclassified_claim_fields


def _count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def statistics(conn):
    total = _count(conn, "SELECT count(*) FROM objects")
    object_ids = [row[0] for row in conn.execute("SELECT id FROM objects")]
    parent = {object_id: object_id for object_id in object_ids}

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for object_a, object_b in conn.execute(
        "SELECT object_a_id,object_b_id FROM dedupe_candidates WHERE status='same_object'"
    ):
        root_a, root_b = find(object_a), find(object_b)
        if root_a != root_b:
            parent[root_b] = root_a
    estimated_distinct = len({find(object_id) for object_id in object_ids})
    unclassified = unclassified_claim_fields(conn)
    return {
        "candidate_objects": total,
        # A claim field outside the comparison model is neither counted nor
        # conflict-checked, so it has to be visible rather than silent (QA-008).
        "unclassified_claim_fields": unclassified,
        "estimated_distinct_objects_after_resolved_dedupe": estimated_distinct,
        "resolved_duplicate_records": total - estimated_distinct,
        "probable_or_confirmed": _count(conn, "SELECT count(*) FROM objects WHERE record_status IN ('probable','confirmed')"),
        "source_appearances": _count(conn, "SELECT count(*) FROM appearances"),
        "sources": _count(conn, "SELECT count(*) FROM sources"),
        "dedupe_clusters_pending": _count(conn, "SELECT count(*) FROM dedupe_candidates WHERE status='pending'"),
        "objects_with_text": _count(conn, "SELECT count(DISTINCT object_id) FROM texts"),
        "objects_with_translation": _count(conn, "SELECT count(DISTINCT object_id) FROM texts WHERE text_type='translation'"),
        "objects_with_provenance": _count(conn, "SELECT count(DISTINCT object_id) FROM events WHERE event_type IN ('excavation','find','ownership','acquisition','sale','transfer')"),
        "objects_with_current_location": _count(conn, "SELECT count(DISTINCT object_id) FROM claims WHERE field='current_location'"),
        "open_leads": _count(conn, "SELECT count(*) FROM leads WHERE status IN ('open','in_progress')"),
        "planned_queries": _count(conn, "SELECT count(*) FROM search_queries WHERE status='planned'"),
        "searched_queries": _count(conn, "SELECT count(*) FROM search_queries WHERE status IN ('searched','exhausted')"),
        "coverage_targets_remaining": _count(conn, "SELECT count(*) FROM coverage_targets WHERE status IN ('planned','in_progress')"),
        "qualifying_saturation_sweeps": _count(conn, "SELECT count(*) FROM saturation_sweeps WHERE status='complete' AND net_new_rate < 0.01 AND revealed_new_source_class=0"),
        "manual_audits": _count(conn, "SELECT count(*) FROM manual_audits"),
        "manual_audit_failures": _count(conn, "SELECT count(*) FROM manual_audits WHERE result='fail'"),
        "objects_without_evidence": _count(conn, "SELECT count(*) FROM objects o WHERE NOT EXISTS (SELECT 1 FROM object_source_evidence e WHERE e.object_id=o.id)"),
    }


def write_report(conn, destination):
    stats = statistics(conn)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = ["# Discovery campaign status", "", "Generated: `%s`" % generated, "", "## Corpus", ""]
    for key, value in stats.items():
        lines.append("- %s: **%s**" % (key.replace("_", " ").capitalize(), value))
    lines.extend(["", "## Coverage by source class", "", "| Source class | Planned | Searched/exhausted | Blocked |", "|---|---:|---:|---:|"])
    for row in conn.execute(
        "SELECT source_class, sum(status='planned'), sum(status IN ('searched','exhausted')), "
        "sum(status='blocked') FROM search_queries GROUP BY source_class ORDER BY source_class"
    ):
        lines.append("| %s | %s | %s | %s |" % tuple(row))
    lines.extend(["", "## Campaign source-class targets", "", "| Source class | Target | Status | Assessment |", "|---|---|---|---|"])
    for row in conn.execute(
        "SELECT source_class,target_name,status,coalesce(notes,'') FROM coverage_targets "
        "ORDER BY source_class,target_name"
    ):
        lines.append("| %s | %s | %s | %s |" % tuple(
            str(value).replace("|", "\\|").replace("\n", " ") for value in row
        ))
    lines.extend(["", "## Source access", "", "| Access status | Sources |", "|---|---:|"])
    for row in conn.execute(
        "SELECT coalesce(access_status,'unrecorded'),count(*) FROM sources "
        "GROUP BY coalesce(access_status,'unrecorded') ORDER BY 2 DESC,1"
    ):
        lines.append("| %s | %s |" % tuple(row))
    lines.extend(["", "## Corpus composition", "", "| Dimension | Value | Objects |", "|---|---|---:|"])
    for dimension, column in (
        ("object type", "object_type"), ("record status", "record_status"),
        ("authenticity", "authenticity"),
    ):
        for row in conn.execute(
            "SELECT %s,count(*) FROM objects GROUP BY %s ORDER BY count(*) DESC,%s"
            % (column, column, column)
        ):
            lines.append("| %s | %s | %s |" % (dimension, row[0], row[1]))
    lines.extend(["", "## Acceptance checks", ""])
    checks = {
        "Every object has source evidence": stats["objects_without_evidence"] == 0,
        "No planned queries remain": stats["planned_queries"] == 0,
        "No coverage targets remain": stats["coverage_targets_remaining"] == 0,
        "No open leads remain": stats["open_leads"] == 0,
        "Two independent saturation sweeps qualify": stats["qualifying_saturation_sweeps"] >= 2,
        "Stratified manual audit has at least twelve records": stats["manual_audits"] >= 12,
        "Manual audit has no failures": stats["manual_audit_failures"] == 0,
    }
    for name, passed in checks.items():
        lines.append("- [%s] %s" % ("x" if passed else " ", name))
    lines.extend(["", "## Saturation", "", "Campaign saturation requires two independent broad sweeps, each adding less than 1% net-new probable physical objects and revealing no new source class.", "", "| Sweep | Strategy | Baseline | Net new | Rate | New class |", "|---|---|---:|---:|---:|---:|"])
    for row in conn.execute(
        "SELECT name,strategy,baseline_distinct_objects,net_new_distinct_objects,net_new_rate,revealed_new_source_class FROM saturation_sweeps WHERE status='complete' ORDER BY completed_at,name"
    ):
        lines.append("| %s | %s | %s | %s | %.2f%% | %s |" % (
            row[0], row[1], row[2], row[3], row[4] * 100, "yes" if row[5] else "no"
        ))
    lines.extend(["", "## Manual audit", "", "| Stratum | Result | Records |", "|---|---|---:|"])
    for row in conn.execute(
        "SELECT stratum,result,count(*) FROM manual_audits GROUP BY stratum,result "
        "ORDER BY stratum,result"
    ):
        lines.append("| %s | %s | %s |" % tuple(row))
    lines.extend(["", "## Unresolved or access-blocked leads", "", "| Status | Priority | Lead |", "|---|---:|---|"])
    for row in conn.execute(
        "SELECT status,priority,description FROM leads WHERE status IN ('open','in_progress','blocked') ORDER BY priority,id"
    ):
        lines.append("| %s | %s | %s |" % (row[0], row[1], row[2].replace("|", "\\|")))
    lines.extend([
        "", "## Interpretation and limitations", "",
        "This is a maximum-recall discovery corpus, not a claim that every surviving bowl has been individually enumerated. The estimated-distinct count collapses only reviewed exact matches; the pending similarity queue deliberately preserves uncertain possible duplicates.",
        "",
        "Major residual gaps are explicit above. They include inaccessible or only partially indexed print catalogues, unnumbered objects in private collections, collection-level totals that cannot safely be expanded into item records, and copyrighted full texts or translations that require authorized access. Blocked leads remain actionable research records rather than silently disappearing from coverage.",
        "",
        "The public dashboard should publish only reviewed claims and rights-cleared text or media. The private working corpus can retain bibliographic and archival evidence with its rights metadata.",
    ])
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return stats
