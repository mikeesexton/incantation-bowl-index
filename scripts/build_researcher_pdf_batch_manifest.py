#!/usr/bin/env python3
"""Build conservative object manifests for Pognon 1898 and Ellis 1853.

The generated records contain only catalogue-level identifiers, source scope,
and historical provenance/classification claims. They do not reproduce the
edition texts, translations, commentary, or images.
"""

import argparse
import json
from pathlib import Path


OBSERVED_AT = "2026-09-12"


def pognon_records():
    records = []
    for number in range(1, 31):
        locator = f"Khouabir bowl no. {number}; numbered text section, printed pp. 17-92; corresponding plate no. {number}"
        records.append({
            "label": f"Pognon 1898 Khouabir bowl {number}",
            "object_type": "uncertain",
            "record_status": "probable",
            "authenticity": "unassessed",
            "summary": (
                f"One physical bowl published as Khouabir no. {number} by Pognon. "
                "Its modern collection identity and current location remain unresolved."
            ),
            "source_id": "SRC-E7D5F020B31C",
            "appearance": {
                "locator": locator,
                "url": "https://hdl.handle.net/2027/oxu1.602450713",
                "observed_at": OBSERVED_AT,
                "description": "Numbered bowl text and plate in the complete 1898-1899 corpus; catalogue-level metadata only.",
                "relation_type": "primary",
                "confidence": 1.0,
                "rationale": "Created as a separate candidate for the separately numbered physical bowl; no later museum identity or cross-publication concordance was inferred."
            },
            "identifiers": [{
                "scheme": "publication object key",
                "value": f"Pognon 1898::{number}",
                "assigning_body": "Henri Pognon",
                "confidence": 1.0
            }],
            "claims": [
                {
                    "field": "publication_status",
                    "value_text": "Published as a separately numbered bowl in Pognon's complete Khouabir corpus.",
                    "locator": locator,
                    "certainty": "reported"
                },
                {
                    "field": "findspot",
                    "value_text": "Khouabir, on the Euphrates",
                    "locator": "introduction, printed pp. 1-3; numbered text and plate",
                    "certainty": "reported",
                    "notes": "Pognon reports that local Arabs found the bowls and that Baghdad antiquities dealers brought them to him; exact archaeological context is absent."
                },
                {
                    "field": "findspot_evidence_level",
                    "value_text": "contemporary purchaser report based initially on local and dealer statements; exact archaeological context absent",
                    "locator": "introduction, printed pp. 1-3",
                    "certainty": "reported"
                },
                {
                    "field": "inscription_language",
                    "value_text": "Mandaic (Pognon's historical classification)",
                    "locator": locator,
                    "certainty": "reported",
                    "notes": "The source's nineteenth-century classification is retained as a reported claim pending modern rechecking."
                }
            ]
        })
    return records


LAYARD_PAGES = {
    1: "printed pp. 512-515",
    2: "printed pp. 515-516",
    3: "printed pp. 516-518",
    4: "printed pp. 518-519",
    5: "printed pp. 519-521",
    6: "printed pp. 521-522",
}


def layard_records():
    records = []
    for number, pages in LAYARD_PAGES.items():
        locator = f"Ellis bowl no. {number}, {pages}"
        records.append({
            "label": f"Ellis 1853 bowl {number}",
            "object_type": "whole_bowl",
            "record_status": "probable",
            "authenticity": "unassessed",
            "summary": (
                f"Earthenware incantation bowl separately published as no. {number} "
                "in Thomas Ellis's section of Layard 1853; later museum identity unresolved."
            ),
            "source_id": "SRC-8900A7CAF037",
            "appearance": {
                "locator": locator,
                "url": "https://archive.org/details/HHaAntigua90435LAYDis",
                "observed_at": OBSERVED_AT,
                "description": "Separate numbered treatment in Ellis's foundational bowl publication; catalogue-level metadata only.",
                "relation_type": "primary",
                "confidence": 1.0,
                "rationale": "Created as a separate candidate for the separately numbered physical bowl; no later British Museum identity was inferred from the supplied volume alone."
            },
            "identifiers": [{
                "scheme": "publication object key",
                "value": f"Ellis 1853::{number}",
                "assigning_body": "Thomas Ellis",
                "confidence": 1.0
            }],
            "claims": [
                {
                    "field": "publication_status",
                    "value_text": "Published as a separately numbered bowl in Ellis's 1853 section.",
                    "locator": locator,
                    "certainty": "reported"
                },
                {
                    "field": "script_or_language",
                    "value_text": "Ellis's nineteenth-century language and script description; modern classification not adjudicated here",
                    "locator": "printed pp. 509-512 and the numbered treatment",
                    "certainty": "reported",
                    "notes": "The source uses obsolete and internally variable labels. This record does not convert them into a modern language assignment."
                }
            ]
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = pognon_records() + layard_records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    print(json.dumps({"records": len(records), "pognon": 30, "ellis": 6}, sort_keys=True))


if __name__ == "__main__":
    main()
