#!/usr/bin/env python3
"""Build the checked QA-003 judgment manifest from inspected evidence packets.

The private packet is a local review aid and is never committed. Decisions are
conservative: an uncovered claim source is not treated as verified unless its
live source was inspected during this audit. High-risk rows remain separate.
"""

import argparse
import hashlib
import json
from pathlib import Path


REVIEWED_AT = "2026-09-20T05:00:00+00:00"
REVIEWED_BY = "Codex research audit (Mike Sexton workspace)"

# Live pages/documents inspected on 2026-09-20 after the retained packet pass.
# "full" means the sampled stored claims were exposed by the live evidence;
# "partial" means the identifier/context was exposed but at least one sampled
# factual claim remained unavailable.
LIVE_FULL_CLAIM_CHECKED = {
    "IDENT-04E65150CB94",  # Kedem catalogue PDF, lot 153
    "IDENT-3D8358A1D0CC",  # Ostracon/Trocadero item 1455520
    "IDENT-9078953DB2E7",  # Barakat X.0552
    "IDENT-AD8EFB15E4A0",  # Schøyen MS 1911/2
    "IDENT-DB6683F21ED5",  # Yale YBC 2359
}
LIVE_PARTIAL_CLAIM_CHECKED = {
    "IDENT-0C91DE9D2AEC",  # Apollo lot verified; Barnebys estimate unavailable
    "IDENT-2DB1150EAABF",  # BM056A index/condition; catalogue reading unavailable
    "IDENT-5430A0855D0E",  # Nippur context verified; client reading unavailable
    "IDENT-558CF7614F99",  # BM068A identifier; catalogue reading unavailable
}
LIVE_PARTIAL_SUFFICIENT_FOR_OVERALL_REVIEW = {
    "IDENT-0C91DE9D2AEC",  # eight Apollo facts checked; one Barnebys estimate unavailable
    "IDENT-2DB1150EAABF",  # designation and fragmentary condition checked
    "IDENT-5430A0855D0E",  # language, date, and excavated context checked
}


def _evidence(packet, uncovered_source_ids):
    refs = []
    for capture in packet["captures"]:
        refs.append("capture:%s sha256:%s" % (capture["id"], capture["sha256"]))
    for appearance in packet["appearances"]:
        if appearance.get("raw_json_bytes", 0):
            refs.append(
                "raw_payload:%s sha256:%s" %
                (appearance["id"], appearance["raw_json_sha256"])
            )
    for item in packet["dedupe_evidence"]:
        refs.append("dedupe_evidence:%s" % item["id"])
    for source in packet["sources"]:
        if source["id"] not in uncovered_source_ids:
            continue
        if source.get("url"):
            refs.append("live_or_bibliographic_source:%s" % source["url"])
        else:
            refs.append("bibliographic_source:%s %s" % (source["id"], source["citation"]))
    return sorted(set(refs))


def build(selection_path, packet_path):
    selection_bytes = selection_path.read_bytes()
    selection = json.loads(selection_bytes)
    packet_data = json.loads(packet_path.read_text(encoding="utf-8"))
    selected = {
        (role, item["identity_id"]): item
        for role in ("representative", "high_risk")
        for item in selection[role]
    }
    entries = []
    for packet in packet_data["packets"]:
        role = packet["sample_role"]
        identity_id = packet["selection"]["identity_id"]
        chosen = selected[(role, identity_id)]
        covered_source_ids = {
            capture["source_id"] for capture in packet["captures"]
        } | {
            appearance["source_id"] for appearance in packet["appearances"]
            if appearance.get("raw_json_bytes", 0)
        }
        all_source_ids = {source["id"] for source in packet["sources"]}
        uncovered_source_ids = all_source_ids - covered_source_ids
        uncovered_claims = [
            claim for claim in packet["claims"]
            if claim["source_id"] in uncovered_source_ids
        ]

        claim_check = "not_applicable" if not packet["claims"] else "verified"
        limitations = []
        if uncovered_claims and identity_id not in LIVE_FULL_CLAIM_CHECKED:
            claim_check = "not_reverifiable"
            limitations.append(
                "%d stored claim(s) from an uncaptured source could not all be "
                "rechecked" % len(uncovered_claims)
            )
        if identity_id in LIVE_PARTIAL_CLAIM_CHECKED:
            claim_check = "not_reverifiable"
            limitations.append("live evidence verified only part of the sampled claim set")
        if uncovered_source_ids:
            limitations.append(
                "%d cited source(s) were checked as live/bibliographic evidence rather "
                "than a retained capture" % len(uncovered_source_ids)
            )
        if role == "high_risk":
            limitations.append(
                "high-risk selection contains source-attributed value differences; the "
                "audit does not choose a preferred scholarly value"
            )

        outcome = "verified_with_notes" if limitations else "verified"
        if (
            claim_check == "not_reverifiable" and not covered_source_ids
            and identity_id not in LIVE_PARTIAL_SUFFICIENT_FOR_OVERALL_REVIEW
        ):
            outcome = "indeterminate"

        if len(chosen["member_ids"]) == 1:
            identity_check = "not_applicable"
            identity_note = "Singleton review found no positive evidence of an erroneous separation."
        else:
            identity_check = "verified"
            identity_note = (
                "Exact-identifier or explicit-concordance evidence supports the current "
                "multi-record cluster."
            )
        claim_note = (
            "Sampled factual claims agree with inspected retained/live evidence."
            if claim_check == "verified"
            else "No contradictory value was found, but the full sampled claim set was not re-verifiable."
            if claim_check == "not_reverifiable"
            else "No factual claims are stored for this identity."
        )
        notes = " ".join([
            "Citation and designation checks passed.", identity_note, claim_note,
            ("Limitations: " + "; ".join(limitations) + ".") if limitations else "",
        ]).strip()
        entries.append({
            "sample_role": role,
            "identity_id": identity_id,
            "selection_evidence_sha256": chosen["evidence_sha256"],
            "outcome": outcome,
            "citation_check": "verified",
            "identifier_check": "verified",
            "identity_check": identity_check,
            "claim_check": claim_check,
            "error_categories": [],
            "evidence": _evidence(packet, uncovered_source_ids),
            "notes": notes,
        })
    entries.sort(key=lambda item: (item["sample_role"], item["identity_id"]))
    if len(entries) != len(selected) or {
        (item["sample_role"], item["identity_id"]) for item in entries
    } != set(selected):
        raise ValueError("private packet and checked selection do not contain the same rows")
    return {
        "schema_version": 1,
        "audit_id": selection["audit_id"],
        "selection_manifest": str(selection_path),
        "selection_manifest_sha256": hashlib.sha256(selection_bytes).hexdigest(),
        "reviewed_by": REVIEWED_BY,
        "reviewed_at": REVIEWED_AT,
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("selection", type=Path)
    parser.add_argument("private_packet", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(
        build(args.selection, args.private_packet), ensure_ascii=False, indent=2
    ) + "\n"
    if args.check:
        if args.check.read_text(encoding="utf-8") != rendered:
            raise SystemExit("checked QA-003 review manifest does not reproduce")
        print("QA-003 review manifest matches the inspected packet")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
