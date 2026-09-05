"""Triage identity-level claim differences without deleting source claims."""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .ids import new_id
from .conflict_review import _safe_classification, review_is_current, evidence_fingerprint
from .identity import COVERAGE_GROUPS, identity_rows


SUBSTANTIVE_DISPOSITIONS = {
    "temporal_change", "scholarly_disagreement", "source_inconsistency",
    "source_error", "data_error", "unresolved",
}


def conflict_instances(conn):
    instances = []
    for identity in identity_rows(conn):
        fields = json.loads(identity["raw_conflict_fields_json"])
        if not fields:
            continue
        member_ids = json.loads(identity["member_ids_json"])
        placeholders = ",".join("?" for _ in member_ids)
        for field_group in fields:
            claims = [dict(row) for row in conn.execute(
                "SELECT c.id,c.object_id,c.source_id,c.field,c.value_text,c.value_json,"
                "c.normalized_value,c.certainty,c.locator,s.title source_title,s.url source_url "
                "FROM claims c JOIN sources s ON s.id=c.source_id "
                "WHERE c.object_id IN (%s) AND c.field IN (%s) ORDER BY c.field,c.id"
                % (
                    placeholders,
                    ",".join("?" for _ in COVERAGE_GROUPS[field_group]),
                ),
                member_ids + list(COVERAGE_GROUPS[field_group]),
            )]
            values_by_field = defaultdict(set)
            for claim in claims:
                value = claim["normalized_value"] or claim["value_text"] or claim["value_json"]
                if value:
                    values_by_field[claim["field"]].add(value)
            instances.append({
                "identity_id": identity["identity_id"],
                "label": identity["label"],
                "field_group": field_group,
                "member_ids": member_ids,
                "claims": claims,
                "values_by_field": {key: sorted(value) for key, value in values_by_field.items()},
            })
    return instances


def triage_claim_conflicts(conn, review_path):
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    if review.get("schema_version") == 2:
        return apply_review_batch(conn, review)
    if review.get("overrides"):
        raise ValueError("Legacy count-only overrides are unsafe; use schema_version 2 with evidence fingerprints")
    if conn.execute("SELECT 1 FROM claim_conflict_reviews WHERE review_method='checked_override' LIMIT 1").fetchone():
        raise ValueError("Legacy bulk triage cannot overwrite checked decisions; use a version 2 batch")
    instances = conflict_instances(conn)
    if len(instances) != review["expected_conflict_instances"]:
        raise ValueError(
            "conflict snapshot changed: expected %s instances, found %s"
            % (review["expected_conflict_instances"], len(instances))
        )
    if len({item["identity_id"] for item in instances}) != review["expected_conflicted_identities"]:
        raise ValueError("conflicted identity count differs from checked snapshot")
    overrides = {
        (item["identity_id"], item["field_group"]): item
        for item in review.get("overrides", [])
    }
    counts = Counter()
    reviewed_at = review["reviewed_at"]
    for instance in instances:
        key = (instance["identity_id"], instance["field_group"])
        override = overrides.get(key)
        if override:
            disposition = override["disposition"]
            method = "checked_override"
            rationale = override["rationale"]
        else:
            values_by_field = {
                field: set(values) for field, values in instance["values_by_field"].items()
            }
            disposition, method, rationale = _safe_classification(
                instance["field_group"], values_by_field
            )
        details = json.dumps({
            "label": instance["label"],
            "member_ids": instance["member_ids"],
            "values_by_field": instance["values_by_field"],
            "claim_evidence": [
                {
                    key: claim[key] for key in (
                        "id", "object_id", "source_id", "field", "value_text", "value_json",
                        "normalized_value", "certainty", "locator", "source_title", "source_url",
                    )
                } for claim in instance["claims"]
            ],
        }, ensure_ascii=False, sort_keys=True)
        existing = conn.execute(
            "SELECT id FROM claim_conflict_reviews WHERE identity_id=? AND field_group=?",
            key,
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE claim_conflict_reviews SET disposition=?,review_method=?,rationale=?,"
                "details_json=?,reviewed_by=?,reviewed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (
                    disposition, method, rationale, details, review["reviewed_by"],
                    reviewed_at, existing["id"],
                ),
            )
        else:
            conn.execute(
                "INSERT INTO claim_conflict_reviews (id,identity_id,field_group,disposition,"
                "review_method,rationale,details_json,reviewed_by,reviewed_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    new_id("claim_conflict_review"), instance["identity_id"],
                    instance["field_group"], disposition, method, rationale, details,
                    review["reviewed_by"], reviewed_at,
                ),
            )
        counts[disposition] += 1
    unknown_overrides = set(overrides) - {
        (item["identity_id"], item["field_group"]) for item in instances
    }
    if unknown_overrides:
        conn.rollback()
        raise ValueError("review overrides do not match current conflicts: %s" % sorted(unknown_overrides))
    conn.commit()
    return {
        "conflicted_identities": review["expected_conflicted_identities"],
        "conflict_instances": len(instances),
        "dispositions": dict(sorted(counts.items())),
        "untriaged": 0,
    }


def apply_review_batch(conn, review):
    """Apply only listed, evidence-bound decisions atomically; replay is a no-op."""
    reviewed_by = review.get("reviewed_by", "").strip()
    stamp = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    if not reviewed_by or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Reviewer and UTC review timestamp are required")
    reviewed_at = stamp.isoformat(timespec="seconds")
    entries = review.get("entries", [])
    if not entries:
        raise ValueError("A review batch must contain decisions")
    with conn:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        instances = {(i["identity_id"], i["field_group"]): i for i in conflict_instances(conn)}
        planned = []
        seen = set()
        for entry in entries:
            key = (entry["identity_id"], entry["field_group"])
            if key in seen or key not in instances:
                raise ValueError("Duplicate or absent conflict: %s" % (key,))
            seen.add(key)
            instance = instances[key]
            fingerprint = evidence_fingerprint(instance["member_ids"], instance["claims"])
            if entry.get("evidence_sha256") != fingerprint:
                raise ValueError("Evidence changed for %s; re-inspect before applying" % (key,))
            if entry["disposition"] not in SUBSTANTIVE_DISPOSITIONS | {"compatible"}:
                raise ValueError("Invalid disposition")
            if not entry.get("rationale", "").strip() or not entry.get("review_basis", "").strip():
                raise ValueError("Each decision requires a rationale and explicit review basis")
            details = json.dumps({
                "label": instance["label"], "member_ids": instance["member_ids"],
                "values_by_field": instance["values_by_field"],
                "claim_evidence": instance["claims"], "evidence_sha256": fingerprint,
                "review_basis": entry["review_basis"],
                "supporting_references": entry.get("supporting_references", []),
            }, ensure_ascii=False, sort_keys=True)
            planned.append((key, entry, details))
        changed = 0
        for key, entry, details in planned:
            row = conn.execute("SELECT * FROM claim_conflict_reviews WHERE identity_id=? AND field_group=?", key).fetchone()
            values = (entry["disposition"], "checked_override", entry["rationale"],
                      details, reviewed_by, reviewed_at)
            columns = ("disposition", "review_method", "rationale", "details_json", "reviewed_by", "reviewed_at")
            if row and tuple(row[column] for column in columns) == values:
                continue
            if row:
                conn.execute("UPDATE claim_conflict_reviews SET disposition=?,review_method=?,rationale=?,"
                    "details_json=?,reviewed_by=?,reviewed_at=?,updated_at=? WHERE id=?",
                    values + (datetime.now(timezone.utc).isoformat(timespec="seconds"), row["id"]))
            else:
                conn.execute("INSERT INTO claim_conflict_reviews (id,identity_id,field_group,disposition,"
                    "review_method,rationale,details_json,reviewed_by,reviewed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("IBI-" + new_id("claim_conflict_review"),) + key + values)
            changed += 1
    return {"entries": len(entries), "changed": changed, "unchanged": len(entries) - changed}


def write_conflict_report(conn, destination):
    rows = [dict(row) for row in conn.execute(
        "SELECT * FROM claim_conflict_reviews ORDER BY disposition,field_group,identity_id"
    )]
    current_instances = {
        (item["identity_id"], item["field_group"]): item for item in conflict_instances(conn)
    }
    current_rows = []
    for row in rows:
        instance = current_instances.get((row["identity_id"], row["field_group"]))
        if instance and review_is_current(row, instance["member_ids"], instance["claims"]):
            current_rows.append(row)
    current_keys = {(row["identity_id"], row["field_group"]) for row in current_rows}
    pending = [item for key, item in current_instances.items() if key not in current_keys]
    counts = Counter(row["disposition"] for row in current_rows)
    substantive = [row for row in current_rows if row["disposition"] in SUBSTANTIVE_DISPOSITIONS]
    lines = [
        "# Identity-level claim conflict triage", "",
        "Generated: `%s`" % datetime.now(timezone.utc).isoformat(timespec="seconds"), "",
        "The original source claims remain unchanged. This review classifies apparent differences "
        "so compatible wording and distinct metadata facets are not mistaken for unresolved "
        "scholarly contradictions.", "", "## Results", "",
        "| Disposition | Claim-field instances |", "|---|---:|",
    ]
    for disposition, count in sorted(counts.items()):
        lines.append("| %s | %s |" % (disposition.replace("_", " ").title(), count))
    lines.append("| Requires current evidence review | %s |" % len(pending))
    lines.extend([
        "", "## Revalidation queue", "",
        "Historical decisions are retained. This queue contains missing reviews and decisions "
        "whose evidence changed or whose automatic compatibility rule is no longer supported. "
        "A queued difference is not a demonstrated contradiction.", "",
        "| Identity | Field | Current cited values |", "|---|---|---|",
    ])
    for item in pending:
        evidence = "; ".join(
            "%s: %s [%s; %s]" % (
                claim["field"], claim["value_text"] or claim["value_json"],
                claim["source_id"], claim["locator"],
            ) for claim in item["claims"]
        )
        lines.append("| %s — %s | %s | %s |" % (
            item["identity_id"], item["label"].replace("|", "\\|"),
            item["field_group"], evidence.replace("|", "\\|").replace("\n", " "),
        ))
    lines.extend([
        "", "## Substantive follow-up queue", "",
        "| Identity | Field | Disposition | Values | Rationale |",
        "|---|---|---|---|---|",
    ])
    for row in substantive:
        details = json.loads(row["details_json"])
        values = "; ".join(
            "%s: %s" % (field, " / ".join(items))
            for field, items in details["values_by_field"].items()
        )
        lines.append("| %s — %s | %s | %s | %s | %s |" % (
            row["identity_id"], details["label"].replace("|", "\\|"),
            row["field_group"], row["disposition"].replace("_", " "),
            values.replace("|", "\\|"), row["rationale"].replace("|", "\\|"),
        ))
    lines.extend([
        "", "## Interpretation", "",
        "A `compatible` disposition does not select a canonical value or delete a claim. It means "
        "the values can coexist: examples include date plus period, findspot plus production "
        "region, broad Aramaic plus Jewish Babylonian Aramaic, or institution-name variants.", "",
        "Substantive rows remain visible and require source-level adjudication. They are not safe "
        "for autonomous resolution by continuous agents.",
    ])
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"historical_rows": len(rows), "current_rows": len(current_rows),
            "review_required": len(pending), "substantive": len(substantive),
            "dispositions": dict(counts)}
