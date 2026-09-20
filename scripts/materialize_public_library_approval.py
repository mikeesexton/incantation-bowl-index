#!/usr/bin/env python3
"""Materialize the owner's exact public-library approval as ingestion manifests.

This script does not decide rights. It accepts only the already reviewed cohort
hash and copies its proposed decisions into the two append-only ledger formats.
The content-free proposal remains the human-review record.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from build_public_library_review import stable_hash


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACKET = ROOT / "research" / "reviews" / "public_library_expansion_review_2026-09-20.json"
DEFAULT_TEXT_OUT = ROOT / "research" / "reviews" / "public_library_text_publication_2026-09-20.json"
DEFAULT_MEDIA_OUT = ROOT / "research" / "reviews" / "penn_educational_media_rights_2026-09-20.json"
APPROVED_COHORT = "cc5f8440930decc9a7c42d4cc4fc13de910618837ffddd4d72d575d3d8f92c44"


def utc_stamp(value: str) -> str:
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("approval timestamp must be UTC")
    return stamp.isoformat(timespec="seconds")


def ledger_entries(rows: list[dict], id_key: str) -> list[dict]:
    return [
        {
            id_key: row[id_key],
            "evidence_sha256": row["evidence_sha256"],
            **row["proposed_review"],
        }
        for row in rows
    ]


def materialize(packet: dict, reviewer: str, approved_at: str) -> tuple[dict, dict, dict]:
    material = {"texts": packet["texts"], "media": packet["media"]}
    if packet.get("cohort_sha256") != APPROVED_COHORT:
        raise ValueError("refusing a cohort other than the exact owner-approved hash")
    if stable_hash(material) != APPROVED_COHORT:
        raise ValueError("proposal bytes no longer match the owner-approved cohort")
    if len(packet["texts"]) != 6 or len(packet["media"]) != 288:
        raise ValueError("approved cohort row counts changed")
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("named reviewer required")
    approved_at = utc_stamp(approved_at)

    packet = {
        **packet,
        "status": "approved_by_owner",
        "approval": {
            "approved_by": reviewer,
            "approved_at": approved_at,
            "scope": (
                "All six text rows and all 288 Penn media rows, for the public educational "
                "library and Cloudflare Access scholar preview described in this packet."
            ),
            "deployment_authorized": False,
        },
    }
    common = {
        "schema_version": 1,
        "reviewed_by": reviewer,
        "reviewed_at": approved_at,
        "source_review_packet": str(DEFAULT_PACKET.relative_to(ROOT)),
        "approved_cohort_sha256": APPROVED_COHORT,
    }
    text_manifest = {
        **common,
        "purpose": "Owner-approved publication decisions for the Bowlam educational library",
        "entries": ledger_entries(packet["texts"], "text_id"),
    }
    media_manifest = {
        **common,
        "purpose": "Owner-approved Penn Museum educational-use media decisions",
        "entries": ledger_entries(packet["media"], "media_id"),
    }
    return packet, text_manifest, media_manifest


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", default=str(DEFAULT_PACKET))
    parser.add_argument("--text-out", default=str(DEFAULT_TEXT_OUT))
    parser.add_argument("--media-out", default=str(DEFAULT_MEDIA_OUT))
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--approved-at", required=True)
    args = parser.parse_args()

    packet_path = Path(args.packet)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet, text_manifest, media_manifest = materialize(
        packet, args.reviewed_by, args.approved_at
    )
    write_json(packet_path, packet)
    write_json(Path(args.text_out), text_manifest)
    write_json(Path(args.media_out), media_manifest)
    print(json.dumps({
        "cohort_sha256": APPROVED_COHORT,
        "text_entries": len(text_manifest["entries"]),
        "media_entries": len(media_manifest["entries"]),
        "deployment_authorized": False,
    }, indent=2))


if __name__ == "__main__":
    main()
