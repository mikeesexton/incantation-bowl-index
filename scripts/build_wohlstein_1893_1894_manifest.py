#!/usr/bin/env python3
"""Build exact-VA source appearances for the inspected Wohlstein articles."""

import argparse
import json
from pathlib import Path


OBSERVED_AT = "2026-09-12"

OBJECTS = {
    "VA 2414": "IBI-7FC18C7513B3",
    "VA 2416": "IBI-83B79765A7BC",
    "VA 2417": "IBI-9B8289678F00",
    "VA 2422": "IBI-D3117F96F92A",
    "VA 2426": "IBI-F8C4B2739328",
    "VA 2434": "IBI-CB0178C61399",
}

SOURCES = {
    "1893": {
        "source_id": "SRC-A12DF738AF6A",
        "url": "https://archive.org/details/zeitschriftfuras8189deut",
        "publication_key": "Wohlstein 1893",
    },
    "1894": {
        "source_id": "SRC-53202A840D51",
        "url": "https://archive.org/details/zeitschriftfuras9189deut",
        "publication_key": "Wohlstein 1894",
    },
}

ROWS = [
    ("1893", "VA 2422", "edition of VA 2422, printed pp. 328-340; scan pp. 344-356", True,
     "Complete transcription, German translation, notes, and commentary."),
    ("1893", "VA 2417", "introductory discussion, printed p. 314; scan p. 330", False,
     "Wohlstein distinguishes this bowl's purpose from the other Berlin texts."),
    ("1893", "VA 2414", "palaeographic discussion, printed p. 324; scan p. 340", False,
     "Exact inventory-number comparison in the introductory analysis."),
    ("1893", "VA 2416", "commentary cross-references, printed pp. 330, 335, 338; scan pp. 346, 351, 354", False,
     "Exact inventory-number comparisons in the VA 2422 commentary."),
    ("1893", "VA 2426", "commentary cross-references, printed pp. 331, 333; scan pp. 347, 349", False,
     "Exact inventory-number comparisons in the VA 2422 commentary."),
    ("1893", "VA 2434", "fragment report, printed p. 332; scan p. 348", False,
     "Reports another bowl as fragmentary, with clear script and a parallel opening formula."),
    ("1894", "VA 2416", "edition of VA 2416, printed pp. 11-27; scan pp. 19-35", True,
     "Complete transcription, German translation, notes, and commentary."),
    ("1894", "VA 2426", "edition of VA 2426, printed pp. 27-30; scan pp. 35-38", True,
     "Complete transcription, German translation, notes, and commentary."),
    ("1894", "VA 2414", "edition of VA 2414, printed pp. 30-34; scan pp. 38-42", True,
     "Complete transcription, German translation, notes, and commentary."),
    ("1894", "VA 2417", "edition of VA 2417, printed pp. 34-41; scan pp. 42-49", True,
     "Complete transcription, German translation, notes, and commentary."),
    ("1894", "VA 2422", "commentary cross-references, printed pp. 28-29, 32; scan pp. 36-37, 40", False,
     "Exact inventory-number comparisons with the article's newly edited texts."),
]


def records():
    result = []
    for year, inventory, locator, edited, description in ROWS:
        source = SOURCES[year]
        identifiers = [
            {
                "scheme": "collection designation",
                "value": inventory,
                "assigning_body": "Königliches Museum zu Berlin",
                "confidence": 1.0,
            }
        ]
        claims = [
            {
                "field": "catalogue_description",
                "value_text": description,
                "locator": locator,
                "certainty": "reported",
            }
        ]
        if edited:
            identifiers.append({
                "scheme": "publication object key",
                "value": f"{source['publication_key']}::{inventory}",
                "assigning_body": "Joseph Wohlstein",
                "confidence": 1.0,
            })
            claims.append({
                "field": "publication_status",
                "value_text": f"Edited in Wohlstein {year} with transcription and German translation.",
                "locator": locator,
                "certainty": "reported",
            })
        result.append({
            "object_id": OBJECTS[inventory],
            "label": f"Wohlstein {year}: {inventory}",
            "object_type": "fragment" if inventory == "VA 2434" else "whole_bowl",
            "record_status": "probable",
            "authenticity": "unassessed",
            "source_id": source["source_id"],
            "appearance": {
                "locator": locator,
                "url": source["url"],
                "observed_at": OBSERVED_AT,
                "description": description,
                "relation_type": "primary",
                "confidence": 1.0,
                "rationale": "The inspected primary article prints this exact VA inventory number; the modern Berlin record carries the same designation.",
            },
            "identifiers": identifiers,
            "claims": claims,
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({
        "appearances": len(rows),
        "edited_bowl_appearances": sum(1 for row in ROWS if row[3]),
        "exact_cross_reference_appearances": sum(1 for row in ROWS if not row[3]),
        "new_candidates": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
