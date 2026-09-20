#!/usr/bin/env python3
"""Build the content-free owner decision packet for the public library expansion.

The packet binds every proposed release decision to the current text or media
fingerprint, but deliberately contains no text content. It is a proposal, not an
ingestion manifest: an agent may refresh the evidence, while only the project
owner may approve the proposed rights dispositions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from bowl_index.publication import current_text_reviews, text_evidence, text_fingerprint
from bowl_index.rights import current_media_reviews, media_evidence, media_fingerprint


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
DEFAULT_OUT = ROOT / "research" / "reviews" / "public_library_expansion_review_2026-09-20.json"
PENN_RIGHTS = "https://www.penn.museum/about-collections/rights-and-permissions"
PENN_TERMS = "https://www.penn.museum/about/statements-and-policies/terms-and-conditions"
CC_BY_NC = "https://creativecommons.org/licenses/by-nc/4.0/"

PUBLIC_DOMAIN_TEXT_IDS = (
    "TXT-0F5F558E6619",
    "TXT-1EEA7F77C865",
    "TXT-BE351FA0BE2F",
    "TXT-33E8BD50E1CE",
)
OPEN_LICENSE_TEXT_IDS = (
    "TXT-7DBC5A7924A5",
    "TXT-B40E7B6820A5",
)
EXCLUDED_PARTIAL_TEXT_ID = "TXT-D39E05041A00"


def stable_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def proposed_text_entries(conn: sqlite3.Connection) -> list[dict]:
    evidence = text_evidence(conn)
    reviews = current_text_reviews(conn)
    entries = []
    for text_id in PUBLIC_DOMAIN_TEXT_IDS + OPEN_LICENSE_TEXT_IDS:
        row = evidence[text_id]
        public_domain = text_id in PUBLIC_DOMAIN_TEXT_IDS
        entry = {
            "text_id": text_id,
            "evidence_sha256": text_fingerprint(row),
            "object_id": row["object_id"],
            "source_id": row["source_id"],
            "source_title": row["source_title"],
            "text_type": row["text_type"],
            "editor": row["editor"],
            "locator": row["locator"],
            "characters": len(row["content"]),
            "current_decision": (reviews.get(text_id) or {}).get("publication_decision"),
            "proposed_review": {
                "review_id": "IBI-TEXTPUB-LIBRARY-2026-09-20-" + text_id.removeprefix("TXT-"),
                "rights_basis": "public_domain_expired" if public_domain else "open_license",
                "rights_locator": (
                    "Wohlstein 1893–1894 public-domain edition and registered scan; "
                    + row["locator"]
                    if public_domain else
                    "DOI 10.15366/isimu2003.6.018; Crossref license metadata records "
                    "CC BY-NC 4.0 from 2016-02-19; UAM repository version of record; "
                    + row["locator"]
                ),
                "license_url": None if public_domain else CC_BY_NC,
                "publication_decision": "approved",
                "attribution": (
                    "Josef Wohlstein, Ueber einige aramäische Inschriften auf "
                    "Thongefässen des Königlichen Museums zu Berlin (1893–1894)"
                    if public_domain else
                    "Emiliano Martínez Borobio, A Magical Bowl in Judaeo-Aramaic, "
                    "Isimu 6 (2003), CC BY-NC 4.0"
                ),
                "editorial_status": (
                    "scan-checked normalized German reading text"
                    if public_domain else
                    ("source transliteration" if row["text_type"] == "transliteration"
                     else "project paraphrase of the licensed English translation")
                ),
                "rationale": (
                    "The source edition is public domain in the United States and this row "
                    "has a current scan-checked reading review."
                    if public_domain else
                    "The version of record carries CC BY-NC 4.0; the owner has declared "
                    "the Bowlam library and bowl-making activity strictly educational and "
                    "noncommercial. Attribution, license link and adaptation labeling travel "
                    "with the row."
                ),
            },
        }
        entries.append(entry)
    return entries


def proposed_media_entries(conn: sqlite3.Connection) -> list[dict]:
    evidence = media_evidence(conn)
    reviews = current_media_reviews(conn)
    designations = {
        row["object_id"]: row["value"]
        for row in conn.execute(
            "SELECT object_id,value FROM identifiers WHERE scheme='collection designation'"
        )
    }
    entries = []
    for media_id, row in sorted(evidence.items()):
        if not (row["url"] or "").startswith("https://www.penn.museum//collections/assets/"):
            continue
        designation = designations.get(row["object_id"])
        if not designation:
            raise ValueError("Penn media lacks a collection designation: " + media_id)
        entries.append({
            "media_id": media_id,
            "evidence_sha256": media_fingerprint(row),
            "object_id": row["object_id"],
            "collection_designation": designation,
            "source_id": row["source_id"],
            "source_url": row["source_url"],
            "image_url": row["url"],
            "current_decision": (reviews.get(media_id) or {}).get("public_reuse_decision"),
            "proposed_review": {
                "review_id": "IBI-RIGHTS-PENN-EDU-2026-09-20-" + media_id.removeprefix("MED-"),
                "creator": None,
                "rights_holder": "Penn Museum",
                "source_url": row["url"],
                "rights_statement": (
                    "Penn Museum permits sharing images from its site for nonprofit educational "
                    "or personal noncommercial use without separate permission, excluding "
                    "high-resolution or publication-quality files; modifications must be identified."
                ),
                "rights_locator": PENN_RIGHTS + "; " + PENN_TERMS,
                "license_url": None,
                "jurisdiction_notes": (
                    "Cohort approved only for Bowlam's declared strictly educational, "
                    "noncommercial public library and gated preview. Recheck the policy before "
                    "commercial use, high-resolution use, redistribution as a download package, "
                    "or a later release after the review date."
                ),
                "private_capture_status": (
                    "captured_private" if row["capture_id"] else "not_captured"
                ),
                "public_reuse_decision": "approved",
                "attribution": f"Object {designation}. Courtesy of the Penn Museum.",
                "rationale": (
                    "The project owner declared the intended use strictly educational and "
                    "noncommercial, with no sales, commissions, advertising or business use. "
                    "The reviewed resource is an 800-pixel collection image served by Penn; "
                    "Bowlam will display the remote URL with the required object credit and link."
                ),
                "followup": (
                    "Honor takedown or object-specific notice; revalidate Penn's policy before "
                    "any materially different use."
                ),
            },
        })
    if len(entries) != 288:
        raise ValueError(f"expected 288 Penn media rows, found {len(entries)}")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    texts = proposed_text_entries(conn)
    media = proposed_media_entries(conn)
    state = json.loads((ROOT / "data" / "db-state.json").read_text(encoding="utf-8"))
    material = {"texts": texts, "media": media}
    duplicate_urls = sorted({
        row["image_url"] for row in media
        if sum(other["image_url"] == row["image_url"] for other in media) > 1
    })
    packet = {
        "schema_version": 1,
        "status": "pending_owner_decision",
        "purpose": "Exact rights and publication proposal for Bowlam's public educational library and gated preview",
        "corpus_state_digest": state["corpus_digest"],
        "intended_use": {
            "educational": True,
            "commercial": False,
            "sales_commissions_advertising_or_business_use": False,
            "surfaces": ["public educational library", "Cloudflare Access scholar preview"],
        },
        "counts": {
            "proposed_text_approvals": len(texts),
            "public_domain_translations": sum(
                row["proposed_review"]["rights_basis"] == "public_domain_expired"
                for row in texts
            ),
            "cc_by_nc_text_rows": sum(
                row["proposed_review"]["rights_basis"] == "open_license"
                for row in texts
            ),
            "proposed_penn_media_approvals": len(media),
            "distinct_penn_image_urls": len({row["image_url"] for row in media}),
            "shared_penn_image_urls": len(duplicate_urls),
        },
        "deliberately_excluded": {
            "partial_review_public_domain_text_id": EXCLUDED_PARTIAL_TEXT_ID,
            "protected_modern_translation_rows": 13,
            "other_unapproved_media_rows": 29,
            "reason": "Accuracy review or affirmative permission remains incomplete; no fair-use release is proposed.",
        },
        "shared_image_urls": duplicate_urls,
        "cohort_sha256": stable_hash(material),
        **material,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": str(out), **packet["counts"],
                      "cohort_sha256": packet["cohort_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
