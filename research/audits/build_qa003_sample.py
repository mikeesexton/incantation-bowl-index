#!/usr/bin/env python3
"""Build the deterministic QA-003 identity-accuracy sample.

The representative sample uses composite strata for record status, linkage
method, and dominant source family. Every non-empty stratum receives one seat;
remaining seats are allocated by largest remainder. Selection within a stratum
uses a SHA-256 rank bound to the declared seed. A separate high-risk sample is
drawn from records not selected for the representative estimate.
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from bowl_index.db import connect
from bowl_index.identity import identity_rows
from bowl_index.accuracy_audit import _selection_evidence_digest


SEED = "qa003-identity-accuracy-2026-09-20-v1"
REPRESENTATIVE_N = 60
HIGH_RISK_N = 20

SOURCE_FAMILIES = {
    "museum": {"museum_record"},
    "scholarship": {"article", "book", "catalogue", "chapter", "excavation_report", "thesis"},
    "market": {"auction_record", "dealer_record"},
    "repository_web": {"archive_snapshot", "database", "other", "repository", "web_page"},
}


def stable_rank(*parts):
    payload = "\x1f".join(str(part) for part in (SEED,) + parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def largest_remainder_alloc(counts, target):
    nonempty = sorted(key for key, value in counts.items() if value)
    if target < len(nonempty):
        raise ValueError("sample target is smaller than the non-empty stratum count")
    allocation = {key: 1 for key in nonempty}
    remaining = target - len(nonempty)
    capacities = {key: counts[key] - 1 for key in nonempty}
    capacity_total = sum(capacities.values())
    if remaining > capacity_total:
        raise ValueError("sample target exceeds the population")
    if not remaining:
        return allocation
    quotas = {
        key: remaining * capacities[key] / capacity_total if capacity_total else 0
        for key in nonempty
    }
    for key in nonempty:
        seats = min(capacities[key], int(quotas[key]))
        allocation[key] += seats
    unassigned = target - sum(allocation.values())
    order = sorted(
        nonempty,
        key=lambda key: (-(quotas[key] - int(quotas[key])), stable_rank("allocation", key)),
    )
    while unassigned:
        advanced = False
        for key in order:
            if allocation[key] < counts[key]:
                allocation[key] += 1
                unassigned -= 1
                advanced = True
                if not unassigned:
                    break
        if not advanced:
            raise RuntimeError("could not complete sample allocation")
    return allocation


def build_population(conn):
    object_sources = defaultdict(set)
    source_types = {}
    for row in conn.execute("SELECT id,source_type FROM sources"):
        source_types[row["id"]] = row["source_type"]
    for row in conn.execute(
        "SELECT l.object_id,a.source_id FROM appearance_object_links l "
        "JOIN appearances a ON a.id=l.appearance_id WHERE l.relation_type<>'rejected'"
    ):
        object_sources[row["object_id"]].add(row["source_id"])
    for row in conn.execute("SELECT object_id,source_id FROM claims"):
        object_sources[row["object_id"]].add(row["source_id"])

    dedupe_methods = defaultdict(set)
    for row in conn.execute(
        "SELECT object_a_id,object_b_id,method FROM dedupe_candidates WHERE status='same_object'"
    ):
        pair = frozenset((row["object_a_id"], row["object_b_id"]))
        dedupe_methods[pair].add(row["method"])

    population = []
    for row in identity_rows(conn):
        member_ids = json.loads(row["member_ids_json"])
        source_ids = sorted(set().union(*(object_sources[value] for value in member_ids)))
        family_counts = Counter()
        for source_id in source_ids:
            source_type = source_types.get(source_id, "other")
            family = next(
                (name for name, types in SOURCE_FAMILIES.items() if source_type in types),
                "repository_web",
            )
            family_counts[family] += 1
        source_family = sorted(
            family_counts or {"repository_web": 0},
            key=lambda name: (-family_counts[name], name),
        )[0]
        methods = set()
        for index, left in enumerate(member_ids):
            for right in member_ids[index + 1:]:
                methods.update(dedupe_methods.get(frozenset((left, right)), set()))
        if len(member_ids) == 1:
            linkage_method = "singleton"
        elif methods & {"explicit_concordance", "checked_concordance"}:
            linkage_method = "concordance"
        else:
            linkage_method = "exact_identifier"
        item = {
            "identity_id": row["identity_id"],
            "canonical_object_id": row["canonical_object_id"],
            "label": row["label"],
            "member_ids": member_ids,
            "member_count": row["member_count"],
            "record_status": row["record_status"],
            "linkage_method": linkage_method,
            "source_family": source_family,
            "source_ids": source_ids,
            "source_count": row["source_count"],
            "appearance_count": row["appearance_count"],
            "claim_count": row["claim_count"],
            "identifiers": json.loads(row["identifiers_json"]),
            "raw_conflict_fields": json.loads(row["raw_conflict_fields_json"]),
            "substantive_conflict_fields": json.loads(row["conflict_fields_json"]),
            "authenticity": row["authenticity"],
        }
        item["stratum"] = "%s|%s|%s" % (
            item["record_status"], item["linkage_method"], item["source_family"]
        )
        population.append(item)
    return population


def risk_features(item):
    reasons = []
    score = 0
    if item["member_count"] > 1:
        score += 5 + 2 * item["member_count"]
        reasons.append("multi-record identity cluster")
    if item["linkage_method"] == "concordance":
        score += 5
        reasons.append("concordance-based linkage")
    if item["raw_conflict_fields"]:
        score += 2 + len(item["raw_conflict_fields"])
        reasons.append("multiple stored values")
    if item["substantive_conflict_fields"]:
        score += 5 + 2 * len(item["substantive_conflict_fields"])
        reasons.append("substantive claim disagreement")
    if item["record_status"] in {"candidate", "rejected"}:
        score += 3
        reasons.append("non-priority record status")
    if item["authenticity"] in {"conflicting", "disputed", "suspected_fake"}:
        score += 4
        reasons.append("authenticity-sensitive metadata")
    if item["source_count"] >= 4:
        score += 2
        reasons.append("four or more cited sources")
    if len(item["identifiers"]) >= 5:
        score += 2
        reasons.append("five or more identifiers")
    return score, reasons


def build_manifest(conn):
    population = build_population(conn)
    by_stratum = defaultdict(list)
    for item in population:
        by_stratum[item["stratum"]].append(item)
    counts = {key: len(value) for key, value in by_stratum.items()}
    allocation = largest_remainder_alloc(counts, REPRESENTATIVE_N)
    representative = []
    for stratum in sorted(by_stratum):
        selected = sorted(
            by_stratum[stratum], key=lambda item: stable_rank("representative", item["identity_id"])
        )[:allocation[stratum]]
        for item in selected:
            entry = dict(item)
            entry.update({
                "population_n": counts[stratum],
                "stratum_sample_n": allocation[stratum],
                "inclusion_probability": allocation[stratum] / counts[stratum],
                "analysis_weight": counts[stratum] / allocation[stratum],
            })
            entry["evidence_sha256"] = _selection_evidence_digest(conn, entry)
            representative.append(entry)
    representative_ids = {item["identity_id"] for item in representative}
    high_risk_pool = []
    for item in population:
        if item["identity_id"] in representative_ids:
            continue
        score, reasons = risk_features(item)
        entry = dict(item)
        entry["risk_score"] = score
        entry["risk_reasons"] = reasons
        high_risk_pool.append(entry)
    high_risk = sorted(
        high_risk_pool,
        key=lambda item: (-item["risk_score"], stable_rank("high-risk", item["identity_id"])),
    )[:HIGH_RISK_N]
    for entry in high_risk:
        entry["evidence_sha256"] = _selection_evidence_digest(conn, entry)

    manifest = {
        "schema_version": 1,
        "audit_id": "QA003-2026-09-20",
        "generated_at": "2026-09-20T04:00:00+00:00",
        "seed": SEED,
        "population_definition": (
            "All current derived identity hypotheses, including confirmed, probable, candidate, "
            "and rejected canonical statuses; one row per identity cluster."
        ),
        "population_n": len(population),
        "representative_target_n": REPRESENTATIVE_N,
        "high_risk_target_n": HIGH_RISK_N,
        "design": {
            "strata": ["record_status", "linkage_method", "dominant_source_family"],
            "allocation": (
                "One seat per non-empty composite stratum, then largest-remainder allocation "
                "proportional to remaining stratum capacity."
            ),
            "selection": "Ascending SHA-256 rank of seed, sample role, and identity_id.",
            "estimation": (
                "Representative outcomes use analysis_weight = population_n / stratum_sample_n. "
                "High-risk outcomes are reported separately and never pooled into the estimate."
            ),
        },
        "source_family_mapping": {
            key: sorted(value) for key, value in SOURCE_FAMILIES.items()
        },
        "population_counts_by_stratum": dict(sorted(counts.items())),
        "representative": sorted(representative, key=lambda item: item["identity_id"]),
        "high_risk": sorted(high_risk, key=lambda item: item["identity_id"]),
    }
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path, help="verify that a checked-in manifest reproduces")
    args = parser.parse_args()
    manifest = build_manifest(connect())
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        expected = args.check.read_text(encoding="utf-8")
        if rendered != expected:
            raise SystemExit("checked-in QA-003 sample does not match the current corpus")
        print("QA-003 sample matches the current corpus")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
