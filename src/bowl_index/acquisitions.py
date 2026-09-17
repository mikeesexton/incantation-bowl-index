"""Inventory archived captures without mistaking them for complete publications.

Capture formats are observable; completeness and reading status need separate
assessment. Rank sources without PDF captures as acquisition leads, preserving
that limitation and counting distinct candidate records rather than aliases.
"""

from datetime import datetime, timezone
from pathlib import Path

from .publications import current_registry, publication_object_sets
from .documents import document_metrics, source_document_status


def _source_captures(conn):
    """Inventory formats only: neither a PDF nor HTML proves complete text."""
    captures = {}
    for row in conn.execute(
        "SELECT source_id, url, sha256, mime_type, byte_length FROM captures "
        "WHERE source_id IS NOT NULL ORDER BY id"
    ):
        info = captures.setdefault(row["source_id"], {"capture_count": 0, "pdf_count": 0})
        info["capture_count"] += 1
        is_pdf = (row["mime_type"] or "").split(";")[0].strip().lower() == "application/pdf"
        info["pdf_count"] += int(is_pdf)
        if "sha256" not in info or (is_pdf and info["pdf_count"] == 1):
            info.update({
                "how": "deposit" if (row["url"] or "").startswith("local-deposit:") else "capture",
                "sha256": row["sha256"], "mime_type": row["mime_type"],
                "bytes": row["byte_length"],
            })
    return captures


def acquisition_rows(conn):
    captures = _source_captures(conn)
    assessments = source_document_status(conn)
    keys = publication_object_sets(conn)
    registry = current_registry(conn)
    # How many objects depend on each source as their publication.
    objects_by_source = {}
    for key, entry in registry.items():
        if entry["resolution"] == "resolved" and entry["source_id"]:
            objects_by_source.setdefault(entry["source_id"], set()).update(keys.get(key, set()))
    appearances = {row[0]: row[1] for row in conn.execute(
        "SELECT source_id, count(*) FROM appearances GROUP BY source_id")}
    claims = {row[0]: row[1] for row in conn.execute(
        "SELECT source_id, count(*) FROM claims GROUP BY source_id")}
    rows = []
    for row in conn.execute(
        "SELECT id,title,authors,issued_year,source_type,access_status,rights_status,notes "
        "FROM sources"
    ):
        source = dict(row)
        source.update(captures.get(source["id"], {"capture_count": 0, "pdf_count": 0}))
        source["capture_status"] = ("pdf_captured" if source["pdf_count"] else
                                    "non_pdf_only" if source["capture_count"] else "not_captured")
        assessment = assessments.get(source["id"])
        source["document_completeness"] = assessment["extent"] if assessment else "unassessed"
        source["document_form"] = assessment["document_form"] if assessment else "unassessed"
        source["inspection"] = assessment["inspection"] if assessment else "unassessed"
        source["text_state"] = assessment["text_state"] if assessment else "unassessed"
        source["object_extraction"] = (
            assessment["object_extraction"] if assessment else "unassessed")
        source["assessed_document_sha256"] = (
            assessment["document_sha256"] if assessment else None)
        source["published_object_ids"] = sorted(objects_by_source.get(source["id"], set()))
        source["published_objects"] = len(source["published_object_ids"])
        source["appearances"] = appearances.get(source["id"], 0)
        source["claims"] = claims.get(source["id"], 0)
        # A work is worth chasing in proportion to how much rests on it unread.
        source["priority"] = (
            source["published_objects"] * 10 + source["appearances"] + source["claims"]
        )
        rows.append(source)
    return rows


def acquisition_metrics(conn):
    rows = acquisition_rows(conn)
    captured = [r for r in rows if r["capture_count"]]
    pdfs = [r for r in rows if r["pdf_count"]]
    wanted = [r for r in rows if not r["pdf_count"] and r["priority"] > 0]
    return {
        **document_metrics(conn),
        "sources": len(rows),
        "sources_with_captures": len(captured),
        "sources_with_pdf_captures": len(pdfs),
        "sources_with_non_pdf_captures_only": len(captured) - len(pdfs),
        "sources_needing_acquisition_review": sum(r["priority"] > 0 for r in rows),
        "sources_without_pdf_with_dependants": len(wanted),
        "objects_depending_on_a_publication_without_pdf": len(set().union(
            *(set(r["published_object_ids"]) for r in wanted))),
    }


def write_acquisition_report(conn, destination):
    rows = acquisition_rows(conn)
    metrics = acquisition_metrics(conn)
    held = sorted((r for r in rows if r["capture_count"]), key=lambda r: (-r["priority"], r["id"]))
    wanted = sorted((r for r in rows if not r["pdf_count"] and r["priority"] > 0),
                    key=lambda r: (-r["priority"], r["id"]))
    def label(r):
        who = (r["authors"] or "").split(";")[0].split(",")[0].strip() or "—"
        return "%s %s — %s" % (who, r["issued_year"] or "n.d.", (r["title"] or "")[:78])
    L = [
        "# Acquisition register",
        "",
        "> Generated by `ibi report-acquisitions`. Capture presence and format are inventory",
        "> facts. They do not establish that the complete publication is held or has been read.",
        "",
        "Generated: `%s`" % datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "",
        "| Measure | Current |",
        "|---|---:|",
        "| Source records | %d |" % metrics["sources"],
        "| Sources with any capture | %d |" % metrics["sources_with_captures"],
        "| Sources with PDF captures (not proof of completeness) | %d |" % metrics["sources_with_pdf_captures"],
        "| Sources with non-PDF captures only | %d |" % metrics["sources_with_non_pdf_captures_only"],
        "| Sources with a current document assessment | %d |" % metrics["sources_with_document_assessments"],
        "| Sources assessed as complete | %d |" % metrics["sources_with_complete_documents"],
        "| Sources with object-level extraction | %d |" % metrics["sources_with_object_level_extraction"],
        "| Sources with dependants needing acquisition review | %d |" % metrics["sources_needing_acquisition_review"],
        "| Sources with dependants and no PDF capture | %d |" % metrics["sources_without_pdf_with_dependants"],
        "| Unique candidate records depending on publications without PDF captures | %d |" % metrics["objects_depending_on_a_publication_without_pdf"],
        "",
        "A PDF may be front matter, an excerpt or a complete work. HTML may be a landing page",
        "or full text. Neither format certifies completeness, page-level verification or rights.",
        "Completeness decisions come only from the append-only document ledger; unassessed",
        "captures remain unassessed. Counts refer to candidate records, not physical identities.",
        "",
        "Documents are archived privately by content hash under `data/private/archive/` and are",
        "never committed. What is committed is the hash, the citation and the locator.",
        "",
        "## Captured sources — document ledger status",
        "",
        "| Work | How / format | Extent · inspection · text · extraction | Candidate records | SHA-256 |",
        "|---|---|---|---:|---|",
    ]
    for r in held:
        L.append("| %s | %s | %s · %s · %s · %s | %d | `%s` |" % (
            label(r).replace("|", "\\|"), r.get("how", "—") + " / " + r["capture_status"],
            r["document_completeness"], r["inspection"], r["text_state"],
            r["object_extraction"], r["published_objects"],
            (r.get("assessed_document_sha256") or r.get("sha256") or "")[:12]))
    L += [
        "",
        "## Acquisition leads — no PDF capture",
        "",
        "This is a starting queue, not proof of missing full text. Ten points per candidate record the work",
        "publishes, one per appearance or claim already attributed to it.",
        "",
        "| Work | Candidate records | Appearances | Claims | Access |",
        "|---|---:|---:|---:|---|",
    ]
    for r in wanted[:40]:
        L.append("| %s | %d | %d | %d | %s |" % (
            label(r).replace("|", "\\|"), r["published_objects"], r["appearances"],
            r["claims"], r["access_status"]))
    if len(wanted) > 40:
        L.append("")
        L.append("Plus %d further sources with dependants. The full list is in the corpus." % (len(wanted) - 40))
    L += [
        "",
        "## How to add one",
        "",
        "Send the PDF. It is archived by content hash and linked to its source record:",
        "",
        "```sh",
        "ibi deposit <path> --source-id <SRC-…> --rights-status <status> --note '<provenance>'",
        "```",
        "",
        "`deposit` records a researcher-supplied file. It never implies a fetch, a robots check, or",
        "an access-control decision — use `capture` only for URLs the project may lawfully retrieve.",
        "Assess retained bytes separately with `ibi ingest-document-assessment <manifest>`; the",
        "assessment must bind its review, document and any transformed artifacts by SHA-256.",
        "",
    ]
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(L) + "\n", encoding="utf-8")
    return {"destination": str(destination), **metrics}
