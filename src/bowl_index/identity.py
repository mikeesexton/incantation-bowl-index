import csv
import json
from collections import defaultdict
from pathlib import Path

from .dedupe import _identity_roots
from .conflict_review import review_is_current
from .presentation import collection_name, display_date, display_name, language_name


# The release-gate facets. Names are load-bearing: the handoff gate, next_action
# and the research console all address them by these keys.
CORE_COVERAGE = {
    "location": {"current_location", "current_or_reported_collection"},
    "provenance": {
        "provenance", "provenance_summary", "findspot", "findspot_or_origin", "origin",
        "collection_history", "production_place", "excavation_context",
        "geography", "geographic_association", "associated_find",
    },
    "dating": {"dating", "period", "culture"},
    "dimensions": {"dimensions"},
    "material": {"material"},
    "language": {"inscription_language", "script_or_language", "catalogue_language_codes"},
    "script": {"script", "script_classification"},
}

# The facets the scholarship actually turns on (META-006). The scoping review's
# Phase 2 ledger names ten field groups; CORE_COVERAGE held only the physical and
# bibliographic ones, so these claims existed in the corpus but were never counted
# and never compared. Roles are kept apart on purpose: a client is not an author,
# and collapsing them is the error META-007 exists to prevent.
CONTENT_COVERAGE = {
    "condition": {"condition"},
    "vessel_form": {"vessel_form", "object_form"},
    "text_form": {"line_count", "inscription_extent", "text_layout", "inscription_placement"},
    "text_description": {
        "text_content", "text_feature", "textual_feature", "text_characterization",
    },
    "client": {"client", "clients", "client_or_beneficiary"},
    "target": {"target", "targets"},
    "practitioner": {
        "attributed_author", "handwriting_attribution", "scribal_attribution",
        "handwriting_group",
    },
    "ritual": {
        "text_purpose", "formula_genre", "named_demon", "named_angels", "text_tradition",
        "installation_instruction",
    },
    "biblical_intertexts": {
        "biblical_quotations", "biblical_quotation", "biblical_citation", "biblical_citations",
    },
    "parallels": {"text_parallel", "textual_parallel", "comparandum"},
    "visual": {"iconography", "iconography_or_caption"},
    "publication": {
        "bibliography", "publication_status", "catalogue_concordance",
        "publication_register_identifier", "publication_heading_identifier",
        "translation_availability",
    },
    "authenticity_assessment": {"authenticity_assessment", "technical_test"},
}

# Every group that is counted for coverage and compared for conflicts.
COVERAGE_GROUPS = {**CORE_COVERAGE, **CONTENT_COVERAGE}

# The ten facets the release gates, next_action and the coverage bars address.
# `completeness_score` counts these and only these: it is reported as "n/10"
# everywhere, and summing all 23 flags into it produced scores of 12/10.
CORE_ORDER = (
    "location", "provenance", "dating", "dimensions", "material", "language",
    "script", "text_edition", "translation", "image",
)

# What a reader, rather than a curator, can actually engage with. Weighted so a
# published text outranks a filled-in measurement: 736 of 1,322 identities score
# zero here, and completeness ordering cannot tell them from the readable ones.
READING_WEIGHTS = {
    "public_text": 3, "has_image": 2, "has_translation": 2,
    "has_client": 1, "has_ritual": 1, "has_biblical_intertexts": 1,
    "has_visual": 1, "has_text_form": 1, "has_practitioner": 1,
}

def reading_score(row):
    """How much of this record a reader can actually engage with."""
    total = READING_WEIGHTS["public_text"] if row.get("public_text_count") else 0
    for key, weight in READING_WEIGHTS.items():
        if key != "public_text":
            total += weight * int(row.get(key, 0))
    return total

# Fields deliberately outside comparison, each with the reason. A claim field that
# is neither grouped nor listed here is a gap, not a default: see
# `unclassified_claim_fields` and tests/test_field_model.py.
EXCLUDED_CLAIM_FIELDS = {
    "dimensions_source_text": "Retained original source string behind a structured dimensions claim, not an independent assertion.",
    "dating_context": "Context supporting a dating argument, not a competing date.",
    "catalogue_description": "Free-text catalogue prose. Third-party expression rather than a comparable assertion, and withheld from public export.",
    "findspot_evidence_level": "Grades the basis of a findspot claim (META-005); an assessment of a claim, not a rival claim.",
    "findspot_evidence": "Grades the basis of a findspot claim (META-005).",
    "findspot_assessment": "Grades the basis of a findspot claim (META-005).",
    "provenance_quality": "Assesses the quality of a provenance claim (META-005).",
    "former_location": "Ownership history is a sequence, not a competing description. Model it in `events` with the provenance event types.",
    "historical_collection": "Ownership history is a sequence; see `events`.",
    "historical_location_status": "Ownership history is a sequence; see `events`.",
    "acquisition": "Acquisition is an event; see `events`.",
    "exhibition_history": "Exhibition is an event; see `events`.",
    "relationship": "Object-to-object relationship. Belongs in `object_relationship_assertions` (CONC-008), which stores direction and scope without merging identities.",
    "scribal_relationship": "Object-to-object relationship; see `object_relationship_assertions`.",
    "family_relationship": "Kinship between named persons. Belongs with the role modelling in META-007, not with a single-value comparison.",
    "physical_record_ambiguity": "Records that a source may describe the same physical object twice; a dedupe signal, not a field value.",
    "identification": "States what the object might be; the object_type and record_status columns carry this.",
    "object_identification": "States what the object might be; see object_type and record_status.",
    "identifier_warning": "Flags a wrong catalogue number in a publication; a correction note, not a claim about the bowl.",
    "source_identity": "Describes the source record itself, not the bowl.",
    "source_physical_description": "Describes the source carrier, for example a glass-plate negative, not the bowl.",
    "source_creation_date": "Dates the source record, not the bowl.",
    "collection_context": "Situates the object within a publication cohort; narrative context, not a comparable value.",
    "export_status": "Legal or regulatory status of a sale, not a description of the object.",
    "sale_estimate": "Market event. Each sale is its own occurrence, so two values are a history, not a disagreement.",
    "sale_estimate_or_opening": "Market event; see sale_estimate.",
    "sale_result": "Market event; see sale_estimate.",
    "sale_offer": "Market event; see sale_estimate.",
    "sale_price": "Market event; see sale_estimate.",
    "sale_reserve": "Market event; see sale_estimate.",
    "sale_location": "Market event; see sale_estimate.",
    "offer_price": "Market event; see sale_estimate.",
    "asking_price": "Market event; see sale_estimate.",
    "starting_price": "Market event; see sale_estimate.",
    "current_bid": "Market event; see sale_estimate.",
}


def unclassified_claim_fields(conn):
    """Claim fields that are neither compared nor explicitly excluded."""
    grouped = {field for fields in COVERAGE_GROUPS.values() for field in fields}
    present = {row[0] for row in conn.execute("SELECT DISTINCT field FROM claims")}
    return sorted(present - grouped - set(EXCLUDED_CLAIM_FIELDS))

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
            name: bool(fields & claim_fields) for name, fields in COVERAGE_GROUPS.items()
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
        next_action = next((name for name in CORE_ORDER if not coverage[name]), "rights review")
        conflict_fields = []
        for name, fields in COVERAGE_GROUPS.items():
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
                [claim for claim in cluster_claims if claim["field"] in COVERAGE_GROUPS[field]],
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
            "completeness_score": sum(int(coverage[name]) for name in CORE_ORDER),
            "content_completeness": sum(
                int(coverage[name]) for name in CONTENT_COVERAGE if name in coverage
            ),
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
        row["display_name"] = display_name(row["label"], sorted(cluster_identifiers))
        row["display_date"] = display_date(cluster_claims)
        row["display_language"] = language_name(cluster_claims)
        location_values = sorted({
            (claim["normalized_value"] or claim["value_text"] or claim["value_json"] or "").strip()
            for claim in cluster_claims if claim["field"] in CORE_COVERAGE["location"]
        } - {""})
        row["display_collection"] = collection_name(
            row["label"], sorted(cluster_identifiers), location_values
        )
        row["reading_score"] = reading_score(row)
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
