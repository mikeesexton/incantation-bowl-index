#!/usr/bin/env python3
"""Render private evidence packets for the checked QA-003 sample."""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect


def rows(conn, statement, params):
    return [dict(row) for row in conn.execute(statement, params)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument(
        "--include-private-payload", action="store_true",
        help="include stored appearance raw_json; output must remain outside Git",
    )
    args = parser.parse_args()
    sample = json.loads(args.sample.read_text(encoding="utf-8"))
    conn = connect()
    packets = []
    for role in ("representative", "high_risk"):
        for selected in sample[role]:
            member_ids = selected["member_ids"]
            placeholders = ",".join("?" for _ in member_ids)
            appearances = rows(
                conn,
                "SELECT a.*,l.object_id,l.relation_type,l.confidence,l.rationale "
                "FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id "
                "WHERE l.object_id IN (%s) ORDER BY a.source_id,a.locator,l.object_id" % placeholders,
                member_ids,
            )
            for appearance in appearances:
                raw = appearance.get("raw_json")
                appearance["raw_json_sha256"] = (
                    hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None
                )
                appearance["raw_json_bytes"] = len(raw.encode("utf-8")) if raw is not None else 0
                if not args.include_private_payload:
                    appearance["raw_json"] = None
            source_ids = sorted({item["source_id"] for item in appearances} | {
                row[0] for row in conn.execute(
                    "SELECT DISTINCT source_id FROM claims WHERE object_id IN (%s)" % placeholders,
                    member_ids,
                )
            })
            source_placeholders = ",".join("?" for _ in source_ids)
            sources = rows(
                conn, "SELECT * FROM sources WHERE id IN (%s) ORDER BY id" % source_placeholders,
                source_ids,
            ) if source_ids else []
            captures = rows(
                conn, "SELECT * FROM captures WHERE source_id IN (%s) ORDER BY source_id,id" % source_placeholders,
                source_ids,
            ) if source_ids else []
            packet = {
                "sample_role": role,
                "selection": selected,
                "objects": rows(
                    conn, "SELECT * FROM objects WHERE id IN (%s) ORDER BY id" % placeholders,
                    member_ids,
                ),
                "sources": sources,
                "captures": captures,
                "appearances": appearances,
                "identifiers": rows(
                    conn, "SELECT * FROM identifiers WHERE object_id IN (%s) ORDER BY object_id,scheme,id" % placeholders,
                    member_ids,
                ),
                "claims": rows(
                    conn, "SELECT * FROM claims WHERE object_id IN (%s) ORDER BY object_id,field,id" % placeholders,
                    member_ids,
                ),
                "dedupe_decisions": rows(
                    conn,
                    "SELECT * FROM dedupe_candidates WHERE status='same_object' AND "
                    "object_a_id IN (%s) AND object_b_id IN (%s) ORDER BY object_a_id,object_b_id" % (
                        placeholders, placeholders,
                    ),
                    member_ids + member_ids,
                ),
            }
            dedupe_ids = [item["id"] for item in packet["dedupe_decisions"]]
            if dedupe_ids:
                dedupe_placeholders = ",".join("?" for _ in dedupe_ids)
                packet["dedupe_evidence"] = rows(
                    conn,
                    "SELECT * FROM dedupe_evidence WHERE dedupe_id IN (%s) ORDER BY dedupe_id,id"
                    % dedupe_placeholders,
                    dedupe_ids,
                )
            else:
                packet["dedupe_evidence"] = []
            packets.append(packet)
    print(json.dumps({
        "audit_id": sample["audit_id"],
        "private_payloads_included": args.include_private_payload,
        "packets": packets,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
