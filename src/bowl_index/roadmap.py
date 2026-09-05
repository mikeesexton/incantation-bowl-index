"""Living dataset-maturity roadmap backed by current corpus metrics."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import identity_rows
from .proofreading import current_text_reviews
from .rights import rights_metrics
from .concordance import current_concordance_reviews


STATUS_LABELS = {
    "done": "Done",
    "in_progress": "In progress",
    "queued": "Queued",
    "blocked": "Blocked",
    "monitoring": "Continuous monitoring",
}


def roadmap_metrics(conn):
    identities = identity_rows(conn)
    raw_conflict_instances = sum(
        len(json.loads(row["raw_conflict_fields_json"])) for row in identities
    )
    reviewed_conflict_instances = sum(row["conflict_reviewed_count"] for row in identities)
    compatible_conflict_instances = sum(
        len(json.loads(row["raw_conflict_fields_json"]))
        - len(json.loads(row["conflict_fields_json"])) for row in identities
    )
    publication_referenced = 0
    publication_referenced_priority = 0
    priority_identities = 0
    for row in identities:
        identifiers = json.loads(row["identifiers_json"])
        has_publication_reference = any(
            value.casefold().startswith(("publication object key:", "bibliographic concordance:"))
            for value in identifiers
        )
        if has_publication_reference:
            publication_referenced += 1
        if row["record_status"] in ("probable", "confirmed"):
            priority_identities += 1
            publication_referenced_priority += int(has_publication_reference)
    media_total = conn.execute("SELECT count(*) FROM media").fetchone()[0]
    media_rights_known = conn.execute(
        "SELECT count(*) FROM media WHERE rights_status NOT IN ('unknown','')"
    ).fetchone()[0]
    return {
        **rights_metrics(conn),
        "checked_reading_texts": sum(r["status"] == "reading_text_checked" for r in current_text_reviews(conn).values()),
        "confirmed_penn_concordances": sum(r['status'] == 'confirmed' for r in current_concordance_reviews(conn).values()),
        "relationship_assertions": conn.execute(
            "SELECT count(*) FROM object_relationship_assertions"
        ).fetchone()[0],
        "unresolved_relationship_assertions": conn.execute(
            "SELECT count(*) FROM object_relationship_assertions "
            "WHERE interpretation_status='unresolved'"
        ).fetchone()[0],
        "candidate_records": conn.execute("SELECT count(*) FROM objects").fetchone()[0],
        "probable_identities": len(identities),
        "source_appearances": conn.execute("SELECT count(*) FROM appearances").fetchone()[0],
        "sources": conn.execute("SELECT count(*) FROM sources").fetchone()[0],
        "pending_dedupe": conn.execute(
            "SELECT count(*) FROM dedupe_candidates WHERE status='pending'"
        ).fetchone()[0],
        "raw_conflicted_identities": sum(
            row["raw_conflict_fields_json"] != "[]" for row in identities
        ),
        "conflicted_identities": sum(row["conflict_fields_json"] != "[]" for row in identities),
        "adjudicated_conflicted_identities": sum(
            bool(set(json.loads(row["conflict_fields_json"]))
                 - set(json.loads(row["untriaged_conflict_fields_json"]))) for row in identities
        ),
        "stale_conflict_instances": sum(
            len(json.loads(row["stale_conflict_fields_json"])) for row in identities
        ),
        "raw_conflict_instances": raw_conflict_instances,
        "reviewed_conflict_instances": reviewed_conflict_instances,
        "compatible_conflict_instances": compatible_conflict_instances,
        "substantive_conflict_instances": reviewed_conflict_instances - compatible_conflict_instances,
        "untriaged_conflict_instances": max(0, raw_conflict_instances - reviewed_conflict_instances),
        "publication_referenced_identities": publication_referenced,
        "priority_identities": priority_identities,
        "publication_referenced_priority_identities": publication_referenced_priority,
        "publication_reference_pct": (
            publication_referenced_priority / priority_identities if priority_identities else 0
        ),
        "translation_identities": sum(row["has_translation"] for row in identities),
        "text_edition_identities": sum(row["has_text_edition"] for row in identities),
        "media_records": media_total,
        "media_rights_known": media_rights_known,
        "media_rights_pct": media_rights_known / media_total if media_total else 1,
        "blocked_leads": conn.execute(
            "SELECT count(*) FROM leads WHERE status='blocked'"
        ).fetchone()[0],
        "open_leads": conn.execute(
            "SELECT count(*) FROM leads WHERE status IN ('open','in_progress')"
        ).fetchone()[0],
        "qualifying_saturation_sweeps": conn.execute(
            "SELECT count(*) FROM saturation_sweeps WHERE net_new_rate < .01 "
            "AND revealed_new_source_class=0 AND status='complete'"
        ).fetchone()[0],
        "coverage": {
            field: sum(row["has_" + field] for row in identities)
            for field in (
                "location", "provenance", "dating", "dimensions", "material",
                "language", "script", "text_edition", "translation", "image",
            )
        },
    }


def _metric_passes(value, operator, target):
    return {
        ">=": value >= target,
        "<=": value <= target,
        "==": value == target,
    }[operator]


def _display_metric(key, value):
    if key.endswith("_pct"):
        return "%.1f%%" % (100 * value)
    return str(value)


def write_roadmap(conn, config_path, destination):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    metrics = roadmap_metrics(conn)
    tasks = {
        task["id"]: task
        for stream in config["workstreams"] for task in stream.get("tasks", [])
    }
    metric_gates = []
    for gate in config["handoff_gate"]["metric_conditions"]:
        value = metrics[gate["metric"]]
        passed = _metric_passes(value, gate["operator"], gate["target"])
        metric_gates.append((gate, value, passed))
    task_gates = [tasks[task_id] for task_id in config["handoff_gate"]["required_task_ids"]]
    tasks_ready = all(task["status"] == "done" for task in task_gates)
    metrics_ready = all(item[2] for item in metric_gates)
    handoff_ready = tasks_ready and metrics_ready
    task_status_counts = {
        status: sum(task["status"] == status for task in tasks.values())
        for status in STATUS_LABELS
    }
    metric_gates_passing = sum(item[2] for item in metric_gates)
    required_tasks_done = sum(task["status"] == "done" for task in task_gates)
    portfolio = config.get("portfolio_summary", {})

    lines = [
        "# Incantation Bowl Index: dataset maturity roadmap",
        "",
        "> Living document generated from `research/roadmap/dataset_maturity.json` and the private corpus. "
        "Update task status or add newly discovered gaps in the JSON register, then run `ibi roadmap`.",
        "",
        "Generated: `%s`" % datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "",
        "## Portfolio status",
        "",
        "Current phase: **%s**" % portfolio.get(
            "current_phase", "Research corpus under active review; not release-ready."
        ),
        "",
        "| Progress measure | Current |",
        "|---|---:|",
        "| Roadmap tasks | %s done · %s in progress · %s queued · %s blocked |" % (
            task_status_counts["done"], task_status_counts["in_progress"],
            task_status_counts["queued"], task_status_counts["blocked"],
        ),
        "| Quantitative handoff gates passing | %s/%s |" % (
            metric_gates_passing, len(metric_gates),
        ),
        "| Required handoff tasks complete | %s/%s |" % (
            required_tasks_done, len(task_gates),
        ),
        "",
    ]
    if portfolio.get("strengths"):
        lines.extend(["### What is solid", ""])
        lines.extend("- " + item for item in portfolio["strengths"])
        lines.append("")
    if portfolio.get("blockers"):
        lines.extend(["### What prevents release readiness", ""])
        lines.extend("- " + item for item in portfolio["blockers"])
        lines.append("")
    lines.extend([
        "## Current scope snapshot",
        "",
        "| Measure | Current |",
        "|---|---:|",
        "| Candidate source records | %s |" % metrics["candidate_records"],
        "| Working physical identity hypotheses (all statuses) | %s |" % metrics["probable_identities"],
        "| Source appearances | %s |" % metrics["source_appearances"],
        "| Sources | %s |" % metrics["sources"],
        "| Pending dedupe decisions | %s |" % metrics["pending_dedupe"],
        "| Identities triggering raw claim-difference flags | %s |" % metrics["raw_conflicted_identities"],
        "| Triaged claim-field differences | %s/%s |" % (
            metrics["reviewed_conflict_instances"], metrics["raw_conflict_instances"],
        ),
        "| Compatible differences | %s |" % metrics["compatible_conflict_instances"],
        "| Review required (missing or no longer valid) | %s |" % metrics["untriaged_conflict_instances"],
        "| Existing reviews requiring revalidation | %s |" % metrics["stale_conflict_instances"],
        "| Substantive conflict instances | %s across %s identities |" % (
            metrics["substantive_conflict_instances"], metrics["adjudicated_conflicted_identities"],
        ),
        "| All identities with a publication reference | %s/%s (%.1f%%) |" % (
            metrics["publication_referenced_identities"],
            metrics["probable_identities"],
            100 * metrics["publication_referenced_identities"] / metrics["probable_identities"]
            if metrics["probable_identities"] else 0,
        ),
        "| Probable/confirmed identities with a publication reference | %s/%s (%.1f%%) |" % (
            metrics["publication_referenced_priority_identities"],
            metrics["priority_identities"], 100 * metrics["publication_reference_pct"],
        ),
        "| Identities with a translation | %s |" % metrics["translation_identities"],
        "| Scan-checked normalized reading texts | %s |" % metrics["checked_reading_texts"],
        "| Montgomery/Penn concordances with dated current-evidence review | %s |" % metrics["confirmed_penn_concordances"],
        "| Source-reported object relationships / unresolved scope | %s / %s |" % (
            metrics["relationship_assertions"], metrics["unresolved_relationship_assertions"],
        ),
        "| Identities with a transcription/transliteration | %s |" % metrics["text_edition_identities"],
        "| Media records with a non-unknown rights status | %s/%s (%.1f%%) |" % (
            metrics["media_rights_known"], metrics["media_records"],
            100 * metrics["media_rights_pct"],
        ),
        "| Media with a current ledger entry | %s/%s |" % (metrics["media_current_ledger_rows"], metrics["media_records"]),
        "| Media with completed rights decisions / approved for reuse | %s / %s |" % (metrics["media_rights_assessed"], metrics["media_approved"]),
        "| Blocked leads | %s |" % metrics["blocked_leads"],
        "| Open or active leads | %s |" % metrics["open_leads"],
        "| Qualifying discovery-saturation sweeps | %s |" % metrics["qualifying_saturation_sweeps"],
        "",
        "Coverage means a field or reference is present, not independently verified. "
        "Publication coverage currently uses identifier schemes as a proxy. A non-unknown "
        "rights label is not a reviewed public-reuse decision. Discovery saturation applies "
        "only to the logged searches and does not estimate global completeness.",
        "",
        "### Identity-level field coverage",
        "",
        "| Field | Identities | Coverage |",
        "|---|---:|---:|",
    ])
    total = metrics["probable_identities"]
    for field, count in metrics["coverage"].items():
        lines.append("| %s | %s | %.1f%% |" % (
            field.replace("_", " ").title(), count, 100 * count / total if total else 0,
        ))

    lines.extend([
        "",
        "## Maturity scale",
        "",
        "Maturity is tracked by workstream, not collapsed into a misleading single score.",
        "",
        "| Level | Meaning |",
        "|---:|---|",
    ])
    for level in config["maturity_levels"]:
        lines.append("| %s | **%s:** %s |" % (
            level["level"], level["name"], level["definition"],
        ))

    lines.extend([
        "",
        "## Workstream maturity",
        "",
        "| ID | Workstream | Current | Active target | Steward |",
        "|---|---|---:|---:|---|",
    ])
    for stream in config["workstreams"]:
        lines.append("| %s | %s | L%s | L%s | %s |" % (
            stream["id"], stream["title"], stream["current_level"],
            stream["target_level"], stream["steward"],
        ))

    lines.extend(["", "## Current priority order", ""])
    for index, priority in enumerate(config.get("priorities", []), 1):
        lines.append("%s. %s" % (index, priority))
    lines.extend(["", "## Task register", ""])
    for stream in config["workstreams"]:
        lines.extend(["### %s — %s" % (stream["id"], stream["title"]), "", stream["scope"], ""])
        for task in stream.get("tasks", []):
            checkbox = "x" if task["status"] == "done" else " "
            lines.append("- [%s] **%s — %s** · %s · %s" % (
                checkbox, task["id"], task["title"], STATUS_LABELS[task["status"]],
                task["owner"],
            ))
            lines.append("  - Done when: %s" % task["done_when"])
            if task.get("evidence"):
                lines.append("  - Evidence/status: %s" % task["evidence"])
        lines.append("")

    lines.extend([
        "## Mac mini handoff gate",
        "",
        "Target availability: **%s**. This is an operational eligibility date, not an automatic permission to publish or to make scholarly judgments." % config["handoff_gate"]["target_date"],
        "",
        "Overall gate: **%s**" % ("READY" if handoff_ready else "NOT READY"),
        "",
        "### Quantitative conditions",
        "",
    ])
    for gate, value, passed in metric_gates:
        lines.append("- [%s] %s — current `%s`; target `%s %s`." % (
            "x" if passed else " ", gate["description"],
            _display_metric(gate["metric"], value), gate["operator"],
            _display_metric(gate["metric"], gate["target"]),
        ))
    lines.extend(["", "### Required setup tasks", ""])
    for task in task_gates:
        lines.append("- [%s] %s — %s" % (
            "x" if task["status"] == "done" else " ", task["id"], task["title"],
        ))

    lines.extend([
        "",
        "### What crosses the threshold",
        "",
        "Once the gate is ready, deterministic recurring work moves to the Mac mini: polling approved museum and auction endpoints, bibliographic alerts, sitemap/RSS checks, content hashing, change detection, backups, validation, and opening review leads.",
        "",
        "The agents may **collect and flag**. They may not autonomously merge uncertain identities, resolve conflicting scholarly claims, declare authenticity, clear copyright, bypass access controls, or publish private records. Those remain review tasks.",
        "",
        "A source-specific collector becomes eligible only when it has a stable lawful endpoint, documented rate limits, an idempotent parser with fixtures, provenance-preserving writes, a change detector, bounded retries, and an alert path. It must complete a 14-day shadow run with no silent data loss or uncontrolled duplicate creation.",
        "",
        "## How to maintain this document",
        "",
        "1. Add every newly discovered gap as a task under the relevant workstream in `research/roadmap/dataset_maturity.json`.",
        "2. Give it a stable ID, owner class, status, and verifiable `done_when` condition.",
        "3. Mark a task done only when its evidence is linked. Mark inaccessible work blocked rather than deleting it.",
        "4. After corpus changes, run `ibi roadmap`, `ibi report-enrichment`, and `ibi export`.",
        "5. Review the handoff gate before enabling or expanding any continuous collector.",
        "",
        "## Change log",
        "",
    ])
    for entry in config.get("change_log", []):
        lines.append("- **%s:** %s" % (entry["date"], entry["note"]))

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "destination": str(destination),
        "handoff_ready": handoff_ready,
        "metric_gates_ready": metrics_ready,
        "required_tasks_ready": tasks_ready,
        "tasks": len(tasks),
        "task_status_counts": task_status_counts,
        "metric_gates_passing": metric_gates_passing,
        "metric_gates_total": len(metric_gates),
        "required_tasks_done": required_tasks_done,
        "required_tasks_total": len(task_gates),
    }
