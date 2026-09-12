#!/usr/bin/env python3
"""Build source appearances for Stübe's inspected 1895 Berlin catalogue.

Exact VA inventory numbers attach to the corresponding modern Berlin catalogue
records. Stübe nos. 18-19 lack inventory numbers, so they remain separate
provisional candidates rather than being guessed onto later catalogue entries.
"""

import argparse
import json
from pathlib import Path


SOURCE_ID = "SRC-0B6C0E1133EF"
SOURCE_URL = "https://mdz-nbn-resolving.de/details:bsb11552199"
OBSERVED_AT = "2026-09-12"


ITEMS = [
    (1, "VA 2412", "IBI-82CA6E55B82A", "printed p. 13", "whole_bowl", "No inscription; four drawings on the interior.", "12.5 cm diameter"),
    (2, "VA 2413", "IBI-CEBD4DE0052A", "printed p. 13", "whole_bowl", "Eight spiral lines described as meaningless pseudo-writing.", "10.5 cm diameter"),
    (3, "VA 2432", "IBI-5046801D13AA", "printed p. 13", "fragment", "Bowl broken into five pieces and reassembled; signs described as meaningless.", "12.5 cm diameter"),
    (4, "VA 2416", "IBI-83B79765A7BC", "printed pp. 13-14; edition pp. 22-27", "whole_bowl", "Two separated spiral inscriptions of sixteen and five lines; this is the text Stübe edits.", "18 cm diameter"),
    (5, "VA 2180", "IBI-00EC4D92D6BE", "printed p. 14", "whole_bowl", "Nine spiral lines in square script around a crude goat-like or demon-like drawing.", "17.8 cm diameter"),
    (6, "VA 2422", "IBI-D3117F96F92A", "printed p. 14", "fragment", "Nine spiral lines in square script with a figure at the bottom.", "17.7 cm diameter"),
    (7, "VA 2414", "IBI-7FC18C7513B3", "printed p. 14", "whole_bowl", "Eight spiral lines in square script.", "12 cm diameter"),
    (8, "VA 2417", "IBI-9B8289678F00", "printed pp. 14-15", "fragment", "Fourteen damaged spiral lines in square script; exterior drawing described as Lilith-like.", "18.5 cm diameter"),
    (9, "VA 2418", "IBI-46A19DD5509C", "printed p. 15", "whole_bowl", "Five spiral lines plus radial and concentric characters described as not yielding connected sense.", "12 cm diameter"),
    (10, "VA 2484", "IBI-920AA91FFE7D", "printed p. 15", "fragment", "Twenty-seven spiral lines; about one quarter of the rim is missing and several areas are damaged.", None),
    (11, "VA 2442", "IBI-DE0859066564", "printed p. 16", "whole_bowl", "Lid-like vessel with two surviving inscriptions of four and three lines and traces of another.", None),
    (12, "VA 2573", "IBI-2BB4AABCBAAF", "printed p. 16", "whole_bowl", "Lid-like vessel with irregular interior lines, three drawings, and a one-line exterior inscription.", None),
    (13, "VA 2426", "IBI-F8C4B2739328", "printed p. 16", "whole_bowl", "Seven spiral lines in large square-script characters.", "12 cm diameter"),
    (14, "VA 2458", "IBI-A800D52FE09F", "printed pp. 16-17", "non_bowl", "Inscribed portion of a human skull; explicitly not a bowl.", None),
    (15, "VA 2459", "IBI-BA780DAAB6D8", "printed p. 17", "non_bowl", "Inscribed human skull with a figure; explicitly not a bowl.", None),
    (16, "VA 2105", "IBI-1D782E80D0E1", "printed p. 17", "whole_bowl", "Two-part Syriac inscription described as Estrangela.", None),
    (17, "VA 2419", "IBI-14708ED2A2EE", "printed p. 17", "whole_bowl", "Three-part Syriac inscription described as Nestorian and possibly transitional toward Mandaic.", None),
]


def appearance(number, inventory, locator, summary):
    return {
        "locator": f"descriptive catalogue no. {number}, {locator}; {inventory}",
        "url": SOURCE_URL,
        "observed_at": OBSERVED_AT,
        "description": summary,
        "relation_type": "primary",
        "confidence": 1.0,
        "rationale": "The inspected primary edition prints this exact VA inventory number for the numbered item."
    }


def claims(number, locator, summary, dimensions):
    rows = [
        {
            "field": "publication_status",
            "value_text": f"Described as Stübe 1895 catalogue no. {number}.",
            "locator": locator,
            "certainty": "reported"
        },
        {
            "field": "catalogue_description",
            "value_text": summary,
            "locator": locator,
            "certainty": "reported",
            "notes": "Concise project-authored summary of Stübe's historical description; not a modern reassessment."
        }
    ]
    if dimensions:
        rows.append({
            "field": "dimensions",
            "value_text": dimensions,
            "locator": locator,
            "certainty": "reported",
            "notes": "Stübe's printed diameter statement; measurement convention not independently checked."
        })
    return rows


def records():
    result = []
    for number, inventory, object_id, pages, object_type, summary, dimensions in ITEMS:
        locator = f"descriptive catalogue no. {number}, {pages}; {inventory}"
        result.append({
            "object_id": object_id,
            "label": f"Stübe 1895 no. {number}: {inventory}",
            "object_type": object_type,
            "record_status": "probable",
            "authenticity": "unassessed",
            "source_id": SOURCE_ID,
            "appearance": appearance(number, inventory, pages, summary),
            "identifiers": [
                {"scheme": "publication object key", "value": f"Stübe 1895::{number}", "assigning_body": "Rudolf Stübe", "confidence": 1.0},
                {"scheme": "collection designation", "value": inventory, "assigning_body": "Königliches Museum zu Berlin", "confidence": 1.0}
            ],
            "claims": claims(number, locator, summary, dimensions)
        })
    for number in (18, 19):
        locator = f"descriptive catalogue no. {number}, printed pp. 17-18"
        summary = "One of two separately numbered thick-walled bowls with a six-to-eight-line spiral inscription described by Stübe as Pahlavi; no inventory number is printed."
        result.append({
            "label": f"Stübe 1895 Berlin bowl {number} (inventory number unreported)",
            "object_type": "whole_bowl",
            "record_status": "candidate",
            "authenticity": "unassessed",
            "summary": "Separate bowl in Stübe's inspected Berlin catalogue; later collection identity remains unresolved.",
            "source_id": SOURCE_ID,
            "appearance": {
                "locator": locator,
                "url": SOURCE_URL,
                "observed_at": OBSERVED_AT,
                "description": summary,
                "relation_type": "primary",
                "confidence": 1.0,
                "rationale": "Stübe explicitly numbers two different bowls as nos. 18 and 19; neither receives a VA inventory number, so no later identity is inferred."
            },
            "identifiers": [{"scheme": "publication object key", "value": f"Stübe 1895::{number}", "assigning_body": "Rudolf Stübe", "confidence": 1.0}],
            "claims": [
                {"field": "publication_status", "value_text": f"Described as Stübe 1895 catalogue no. {number}.", "locator": locator, "certainty": "reported"},
                {"field": "script_or_language", "value_text": "Pahlavi (Stübe's 1895 historical description)", "locator": locator, "certainty": "reported", "notes": "Historical classification retained without modern adjudication."},
                {"field": "line_count", "value_text": "approximately 6-8 lines", "locator": locator, "certainty": "reported"},
                {"field": "vessel_form", "value_text": "unusually thick-walled bowl", "locator": locator, "certainty": "reported"}
            ]
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"appearances": len(rows), "exact_va_attachments": len(ITEMS), "new_provisional_candidates": 2}, sort_keys=True))


if __name__ == "__main__":
    main()
