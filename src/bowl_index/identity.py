import csv
import json
from collections import defaultdict
from pathlib import Path

from .dedupe import _identity_roots
from .conflict_review import review_is_current


CORE_COVERAGE = {
    "location": {"current_location", "current_or_reported_collection"},
    "provenance": {
        "provenance", "provenance_summary", "findspot", "findspot_or_origin", "origin",
        "collection_history", "production_place", "excavation_context",
    },
    "dating": {"dating", "period"},
    "dimensions": {"dimensions"},
    "material": {"material"},
    "language": {"inscription_language", "script_or_language"},
    "script": {"script", "script_classification"},
}

PROVENANCE_EVENT_TYPES = {"excavation", "find", "ownership", "acquisition", "sale", "transfer"}
TEXT_EDITION_TYPES = {"inscription", "transcription", "transliteration"}


def _best_object(member_ids, objects, evidence_counts):
    status_rank = {"confirmed": 3, "probable": 2, "candidate": 1, "rejected": 0, "merged": 0}

    def rank(object_id):
        obj = objects[object_id]
        label = obj["label"].casefold()
        discovery_penalty = sum(
            token in label for token in ("context citation", "apotropaic index", "waller 2022:")
        )
        return (
            status_rank.get(obj["record_status"], 0),
            evidence_counts.get(object_id, 0),
            -discovery_penalty,
            -len(obj["label"]),
            object_id,
        )

    return max(member_ids, key=rank)


def identity_rows(conn):
    objects = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM objects")}
    roots = _identity_roots(conn)
    components = defaultdict(list)
    for object_id, root in roots.items():
        components[root].append(object_id)

    appearances = defaultdict(set)
    sources = defaultdict(set)
    for row in conn.execute(
        "SELECT l.object_id,a.id appearance_id,a.source_id FROM appearance_object_links l "
        "JOIN appearances a ON a.id=l.appearance_id WHERE l.relation_type<>'rejected'"
    ):
        appearances[row["object_id"]].add(row["appearance_id"])
        sources[row["object_id"]].add(row["source_id"])
    identifiers = defaultdict(list)
    for row in conn.execute(
        "SELECT object_id,scheme,value,assigning_body FROM identifiers WHERE object_id IS NOT NULL"
    ):
        identifiers[row["object_id"]].append(dict(row))
    claims = defaultdict(list)
    for row in conn.execute(
        "SELECT c.*,s.title source_title,s.url source_url "
        "FROM claims c JOIN sources s ON s.id=c.source_id ORDER BY c.id"
    ):
        claims[row["object_id"]].append(dict(row))
    texts = defaultdict(list)
    for row in conn.execute(
        "SELECT object_id,text_type,public_ok,rights_status FROM texts ORDER BY id"
    ):
        texts[row["object_id"]].append(dict(row))
    events = defaultdict(list)
    for row in conn.execute("SELECT object_id,event_type FROM events ORDER BY id"):
        events[row["object_id"]].append(dict(row))
    media = defaultdict(list)
    for row in conn.execute("SELECT object_id,media_type,rights_status FROM media WHERE object_id IS NOT NULL"):
        media[row["object_id"]].append(dict(row))
    conflict_reviews = {
        (row["identity_id"], row["field_group"]): dict(row)
        for row in conn.execute(
            "SELECT * FROM claim_conflict_reviews"
        )
    }

    rows = []
    for root, member_ids in sorted(components.items()):
        member_ids = sorted(member_ids)
        evidence_counts = {
            object_id: (
                len(appearances[object_id]) + len(sources[object_id]) + len(identifiers[object_id])
                + len(claims[object_id]) + len(texts[object_id]) + len(events[object_id])
            )
            for object_id in member_ids
        }
        canonical = _best_object(member_ids, objects, evidence_counts)
        cluster_claims = [claim for object_id in member_ids for claim in claims[object_id]]
        claim_fields = {claim["field"] for claim in cluster_claims}
        cluster_texts = [item for object_id in member_ids for item in texts[object_id]]
        cluster_events = [item for object_id in member_ids for item in events[object_id]]
        cluster_media = [item for object_id in member_ids for item in media[object_id]]
        coverage = {
            name: bool(fields & claim_fields) for name, fields in CORE_COVERAGE.items()
        }
        coverage["provenance"] = coverage["provenance"] or any(
            event["event_type"] in PROVENANCE_EVENT_TYPES for event in cluster_events
        )
        coverage["text_edition"] = any(
            item["text_type"] in TEXT_EDITION_TYPES for item in cluster_texts
        )
        coverage["translation"] = any(
            item["text_type"] == "translation" for item in cluster_texts
        )
        coverage["image"] = any(item["media_type"] == "image" for item in cluster_media)
        core_order = (
            "location", "provenance", "dating", "dimensions", "material", "language",
            "script", "text_edition", "translation", "image",
        )
        next_action = next((name for name in core_order if not coverage[name]), "rights review")
        conflict_fields = []
        for name, fields in CORE_COVERAGE.items():
            values = {
                (claim["normalized_value"] or claim["value_text"] or claim["value_json"] or "")
                .strip().casefold()
                for claim in cluster_claims if claim["field"] in fields
            }
            values.discard("")
            if len(values) > 1:
                conflict_fields.append(name)
        cluster_identifiers = {
            "%s: %s" % (item["scheme"], item["value"])
            for object_id in member_ids for item in identifiers[object_id]
        }
        authenticity_values = sorted({objects[object_id]["authenticity"] for object_id in member_ids})
        identity_id = "IDENT-" + root.removeprefix("IBI-")
        current_reviews = {
            field: conflict_reviews[(identity_id, field)]
            for field in conflict_fields
            if review_is_current(
                conflict_reviews.get((identity_id, field)), member_ids,
                [claim for claim in cluster_claims if claim["field"] in CORE_COVERAGE[field]],
            )
        }
        substantive_conflict_fields = [
            field for field in conflict_fields
            if current_reviews.get(field, {}).get("disposition") != "compatible"
        ]
        row = {
            "identity_id": identity_id,
            "canonical_object_id": canonical,
            "label": objects[canonical]["label"],
            "member_count": len(member_ids),
            "record_status": objects[canonical]["record_status"],
            "authenticity": authenticity_values[0] if len(authenticity_values) == 1 else "conflicting",
            "appearance_count": len(set().union(*(appearances[value] for value in member_ids))),
            "source_count": len(set().union(*(sources[value] for value in member_ids))),
            "identifier_count": len(cluster_identifiers),
            "claim_count": len(cluster_claims),
            "text_count": len(cluster_texts),
            "public_text_count": sum(bool(item["public_ok"]) for item in cluster_texts),
            "media_count": len(cluster_media),
            "completeness_score": sum(coverage.values()),
            "next_action": next_action,
            "conflict_fields_json": json.dumps(
                sorted(substantive_conflict_fields), ensure_ascii=False
            ),
            "raw_conflict_fields_json": json.dumps(sorted(conflict_fields), ensure_ascii=False),
            "conflict_reviewed_count": sum(
                field in current_reviews for field in conflict_fields
            ),
            "untriaged_conflict_fields_json": json.dumps(sorted(
                field for field in conflict_fields if field not in current_reviews
            )),
            "stale_conflict_fields_json": json.dumps(sorted(
                field for field in conflict_fields
                if (identity_id, field) in conflict_reviews and field not in current_reviews
            )),
            "member_ids_json": json.dumps(member_ids, ensure_ascii=False),
            "identifiers_json": json.dumps(sorted(cluster_identifiers), ensure_ascii=False),
        }
        row.update({"has_" + key: int(value) for key, value in coverage.items()})
        rows.append(row)
    return rows


def write_identity_export(conn, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    rows = identity_rows(conn)
    jsonl_path = destination / "identity_clusters.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    csv_path = destination / "identity_clusters.csv"
    columns = list(rows[0]) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        if columns:
            writer.writeheader()
            writer.writerows(rows)
    return {
        "rows": len(rows), "jsonl": jsonl_path.name, "csv": csv_path.name,
        "derived": True,
    }


def write_enrichment_report(conn, destination):
    rows = identity_rows(conn)
    total = len(rows)
    fields = (
        "location", "provenance", "dating", "dimensions", "material", "language", "script",
        "text_edition", "translation", "image",
    )
    lines = [
        "# Identity and enrichment status", "", "## Identity review", "",
        "- Working physical identity hypotheses (all statuses): **%s**" % total,
        "- Multi-record identity clusters: **%s**" % sum(row["member_count"] > 1 for row in rows),
        "- Underlying source records (all identities): **%s**" % sum(row["member_count"] for row in rows),
        "- Pending dedupe decisions: **%s**" % conn.execute(
            "SELECT count(*) FROM dedupe_candidates WHERE status='pending'"
        ).fetchone()[0],
        "", "## Identity-level coverage", "", "| Field | Identities | Coverage |", "|---|---:|---:|",
    ]
    for field in fields:
        count = sum(row["has_" + field] for row in rows)
        lines.append("| %s | %s | %.1f%% |" % (field.replace("_", " ").title(), count, 100 * count / total if total else 0))
    lines.extend([
        "", "## Completeness distribution", "", "| Core fields present | Identities |", "|---|---:|",
    ])
    bands = ((0, 2), (3, 5), (6, 8), (9, 10))
    for low, high in bands:
        lines.append("| %s–%s of 10 | %s |" % (
            low, high, sum(low <= row["completeness_score"] <= high for row in rows)
        ))
    lines.extend([
        "", "## Next-action queue", "", "| Next action | Identities |", "|---|---:|",
    ])
    for action in list(fields) + ["rights review"]:
        count = sum(row["next_action"] == action for row in rows)
        if count:
            lines.append("| %s | %s |" % (action.replace("_", " ").title(), count))
    raw_conflicts = [row for row in rows if row["raw_conflict_fields_json"] != "[]"]
    conflicts = [row for row in rows if row["conflict_fields_json"] != "[]"]
    reviewed = sum(row["conflict_reviewed_count"] for row in rows)
    compatible = sum(len(json.loads(row["raw_conflict_fields_json"]))
                     - len(json.loads(row["conflict_fields_json"])) for row in rows)
    pending = sum(len(json.loads(row["untriaged_conflict_fields_json"])) for row in rows)
    review_counts = {"compatible": compatible, "substantive": reviewed - compatible}
    lines.extend([
        "", "## Claim conflicts", "",
        "**%s** identities triggered raw difference flags. Current reviews support **%s** compatible "
        "field-level instances and **%s** substantive instances. **%s** instances require review "
        "or revalidation; these are not established contradictions. No source claim or historical "
        "decision was deleted." % (
            len(raw_conflicts), compatible, reviewed - compatible, pending,
        ),
        "", "## Recommended private research UI", "",
        "A local read-only-first interface is justified now because the current generated identity-review queue is clear and the bottleneck has shifted to inspecting claims and filling gaps. Its first release should have four views:", "",
        "1. **Identity search:** full-text search across labels, accessions, publication sigla, owners, clients, and sources; faceted by location, script/language, authenticity, record status, and completeness.",
        "2. **Identity dossier:** one page per probable physical bowl showing all member records, identifiers, appearances, claims grouped by field and source, texts, media, events, rights, and conflicts.",
        "3. **Review workbench:** side-by-side identity comparison with reversible same/different/insufficient decisions and recorded evidence.",
        "4. **Enrichment queue:** filters for missing fields, blocked sources, conflicts, rights review, and recently changed museum or auction appearances.",
        "", "The private UI should write only through validated review/enrichment actions and keep the SQLite database on localhost. The eventual public dashboard can reuse the identity dossier and facets against reviewed, rights-safe exports.",
    ])
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "identities": total, "raw_conflicts": len(raw_conflicts),
        "conflicts": len(conflicts), "conflict_review_dispositions": review_counts,
    }
