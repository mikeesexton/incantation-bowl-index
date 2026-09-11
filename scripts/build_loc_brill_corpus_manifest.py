#!/usr/bin/env python3
"""Build a checked candidate manifest from four researcher-supplied Brill PDFs.

The PDFs are converted to text outside this script. This parser reads only their
contents/concordance lines and emits catalogue-level metadata. It never emits
edition text, translations, commentary, or images and never writes the corpus.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path


OBSERVED_AT = "2026-09-11"


SOURCES = {
    "abs1": {
        "source_id": "SRC-7FBBB775E502",
        "publication": "Shaked-Ford-Bhayro 2013",
        "url": "https://doi.org/10.1163/9789004229372",
        "range": range(1, 65),
    },
    "abs2": {
        "source_id": "SRC-8C611BF93288",
        "publication": "Shaked-Ford-Bhayro 2022",
        "url": "https://doi.org/10.1163/9789004471719",
        "range": range(65, 120),
    },
}


MRLA8_LATE = {
    41: ("No visible script; bowl interior bears eight demon figures.", "whole_bowl", "candidate", "unassessed"),
    42: ("Pseudoscript arranged in circular and spiral bands.", "whole_bowl", "candidate", "pseudo_script"),
    43: ("Uninscribed or entirely faded bowl.", "whole_bowl", "candidate", "unassessed"),
    44: ("No visible writing; a B-like sign is scratched on the interior.", "whole_bowl", "candidate", "unassessed"),
    45: ("Cursive pseudoscript with scattered Pahlavi-like letters.", "whole_bowl", "candidate", "pseudo_script"),
    46: ("Pseudoscript, including an exterior line.", "whole_bowl", "candidate", "pseudo_script"),
    47: ("Very cursive script with some Pahlavi-like letter forms.", "whole_bowl", "candidate", "unassessed"),
    48: ("Pseudoscript in concentric circles with exterior writing.", "whole_bowl", "candidate", "pseudo_script"),
    49: ("Cursive pseudoscript with a small demon drawing.", "whole_bowl", "candidate", "pseudo_script"),
    50: ("Pseudoscript spiraling from the centre toward the rim.", "whole_bowl", "candidate", "pseudo_script"),
    51: ("Cursive Pahlavi-like script; central portion is fragmentary.", "reconstructed", "candidate", "unassessed"),
    52: ("Pseudoscript in concentric circles.", "whole_bowl", "candidate", "pseudo_script"),
    53: ("Pseudoscript on an approximately one-third bowl fragment.", "fragment", "candidate", "pseudo_script"),
    54: ("Pseudoscript with exterior writing.", "whole_bowl", "candidate", "pseudo_script"),
    55: ("Pseudoscript on a bowl missing more than half of its rim area.", "reconstructed", "candidate", "pseudo_script"),
    56: ("Pseudoscript in concentric circles with one exterior line.", "whole_bowl", "candidate", "pseudo_script"),
    57: ("Pahlavi script that may preserve meaningful text.", "reconstructed", "candidate", "unassessed"),
    58: ("Pahlavi script, similar in layout to HS 3048.", "whole_bowl", "candidate", "unassessed"),
    59: ("Pseudoscript on a bowl whose central portion is largely lost.", "reconstructed", "candidate", "pseudo_script"),
    60: ("Unknown script or pseudoscript with possible Pahlavi-like letters.", "reconstructed", "candidate", "pseudo_script"),
    61: ("Cursive Pahlavi-like script on five joining rim fragments.", "fragment", "candidate", "unassessed"),
    62: ("Uninscribed base fragment; cataloguers consider it probably not a magic bowl.", "fragment", "rejected", "unassessed"),
    63: ("Uninscribed base fragment; cataloguers consider it probably not a magic bowl.", "fragment", "rejected", "unassessed"),
    64: ("Pseudoscript on a fragment extending from rim to centre.", "fragment", "candidate", "pseudo_script"),
    65: ("Pseudoscript on two preserved rim-fragment groups.", "fragment", "candidate", "pseudo_script"),
    66: ("Parthian ostracon, not a bowl.", "non_bowl", "rejected", "unassessed"),
    67: ("Faded or uninscribed rim fragment with possible traces of writing.", "fragment", "candidate", "unassessed"),
    68: ("Uninscribed rim fragment; cataloguers consider it probably not from a magic bowl.", "fragment", "rejected", "unassessed"),
}


def normalize_collection(value):
    return "".join(value.strip().casefold().split())


def exact_objects(conn, scheme, value):
    normalized = normalize_collection(value) if scheme == "collection designation" else " ".join(value.strip().casefold().split())
    return {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT object_id FROM identifiers WHERE lower(scheme)=lower(?) AND normalized_value=? AND object_id IS NOT NULL",
            (scheme, normalized),
        )
    }


def match_object(conn, collection_values, publication_key):
    collection_sets = [exact_objects(conn, "collection designation", value) for value in collection_values]
    collection_hits = set().union(*collection_sets) if collection_sets else set()
    if len(collection_hits) == 1:
        return next(iter(collection_hits)), "exact collection designation"
    if len(collection_hits) > 1:
        return None, "multiple existing objects carry the joined collection designations"
    publication_hits = exact_objects(conn, "publication object key", publication_key)
    if len(publication_hits) == 1:
        return next(iter(publication_hits)), "exact publication-object key"
    if len(publication_hits) > 1:
        return None, "publication-object key is already ambiguous"
    return None, "no exact existing identifier match"


def parse_abs(path, expected):
    rows = {}
    pattern = re.compile(r"^jba\s+(\d+)\s+\(ms\s+([^)]+)\).*?\s(\d+)\s*$", re.I)
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        number = int(match.group(1))
        if number in expected and number not in rows:
            rows[number] = (f"MS {match.group(2).strip()}", int(match.group(3)))
    if set(rows) != set(expected):
        raise ValueError(f"{path}: expected {len(expected)} JBA rows, found {len(rows)}")
    return rows


def parse_moriggi(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    pages = {}
    descriptions = {}
    page_pattern = re.compile(r"^Bowl no\.\s+(\d+)\s+(?:\.\s*)+(\d+)\s*$")
    description_pattern = re.compile(
        r"^Bowl no\.\s+(\d+)\s+Bowl no\.\s+(.*?),\s+(?:editio princeps:|presented in)"
    )
    for line in lines:
        stripped = line.strip()
        page_match = page_pattern.match(stripped)
        if page_match and int(page_match.group(1)) not in pages:
            pages[int(page_match.group(1))] = int(page_match.group(2))
        desc_match = description_pattern.match(stripped)
        if desc_match:
            descriptions[int(desc_match.group(1))] = desc_match.group(2).strip()
    expected = set(range(1, 50))
    if set(pages) != expected or set(descriptions) != expected:
        raise ValueError(f"{path}: Moriggi parse incomplete ({len(pages)} pages, {len(descriptions)} designations)")
    return {number: (descriptions[number], pages[number]) for number in sorted(expected)}


def parse_mrla8(path):
    rows = {}
    pattern = re.compile(r"^(\d+)\.\s+(HS\s+.+?)\s+(\d+)\s*$")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        number = int(match.group(1))
        if 1 <= number <= 69 and number not in rows:
            rows[number] = (match.group(2).strip(), int(match.group(3)))
    if set(rows) != set(range(1, 70)):
        raise ValueError(f"{path}: expected 69 MRLA 8 entries, found {len(rows)}")
    return rows


def moriggi_collection_values(designation):
    if designation.startswith("–"):
        return []
    if " + " not in designation:
        return [designation]
    parts = [part.strip() for part in designation.split(" + ")]
    values = []
    previous_prefix = None
    for part in parts:
        if part.startswith("one frag.") or part.startswith("frag. nos."):
            continue
        prefix = re.match(r"^([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+", part)
        if prefix:
            previous_prefix = prefix.group(1)
            values.append(part)
        elif previous_prefix and re.match(r"^\d", part):
            values.append(f"{previous_prefix} {part}")
    return values


def base_record(source, label, object_type, record_status, authenticity, summary, locator, page, description, rationale, object_id=None):
    record = {
        "label": label,
        "object_type": object_type,
        "record_status": record_status,
        "authenticity": authenticity,
        "summary": summary,
        "source_id": source["source_id"],
        "appearance": {
            "locator": locator,
            "url": source["url"],
            "observed_at": OBSERVED_AT,
            "description": description,
            "relation_type": "primary",
            "confidence": 1.0,
            "rationale": rationale,
        },
        "identifiers": [],
        "claims": [
            {
                "field": "publication_status",
                "value_text": "Catalogued in a complete researcher-inspected corpus edition.",
                "locator": f"p. {page}",
                "certainty": "reported",
                "notes": "The copyrighted transcription, translation, commentary, and images remain in the private source archive and are not reproduced in the object record.",
            }
        ],
    }
    if object_id:
        record["object_id"] = object_id
    return record


def build_abs(conn, rows, key):
    source = SOURCES[key]
    output = []
    for number in source["range"]:
        designation, page = rows[number]
        publication_key = f"{source['publication']}::JBA {number}"
        object_id, basis = match_object(conn, [designation], publication_key)
        rationale = (
            f"Linked to the existing object by {basis}; the inspected contents explicitly pair JBA {number} with {designation}."
            if object_id
            else f"Created as a separate candidate because {basis}; no identity merge was inferred."
        )
        record = base_record(
            source,
            f"Schøyen {designation} (JBA {number})",
            "whole_bowl",
            "probable",
            "unassessed",
            f"Jewish Babylonian Aramaic bowl published as JBA {number} in {source['publication']}.",
            f"JBA {number} ({designation}), p. {page}",
            page,
            f"Full edition entry for JBA {number}; catalogue-level metadata only.",
            rationale,
            object_id,
        )
        record["identifiers"] = [
            {"scheme": "publication object key", "value": publication_key, "assigning_body": "Shaked, Ford, and Bhayro", "confidence": 1.0},
            {"scheme": "collection designation", "value": designation, "assigning_body": "Schøyen Collection", "confidence": 1.0},
        ]
        record["claims"].extend([
            {"field": "inscription_language", "value_text": "Jewish Babylonian Aramaic", "locator": f"JBA {number}, p. {page}", "certainty": "reported"},
            {"field": "current_or_reported_collection", "value_text": "Schøyen Collection", "locator": f"JBA {number}, p. {page}", "certainty": "reported"},
        ])
        output.append(record)
    return output


def build_moriggi(conn, rows):
    source = {"source_id": "SRC-3C4294DDB367", "url": "https://doi.org/10.1163/9789004272798"}
    output = []
    for number, (designation, page) in rows.items():
        publication_key = f"Moriggi 2014::{number}"
        collections = moriggi_collection_values(designation)
        object_id, basis = match_object(conn, collections, publication_key)
        rationale = (
            f"Linked to the existing object by {basis}; Moriggi's concordance explicitly assigns it corpus number {number}."
            if object_id
            else f"Created as a separate candidate because {basis}; no identity merge was inferred."
        )
        object_type = "fragment" if "frag." in designation.casefold() and designation.startswith("Nippur-frag") else "whole_bowl"
        record = base_record(
            source,
            f"Moriggi 2014 bowl {number}: {designation}",
            object_type,
            "probable",
            "unassessed",
            f"Syriac incantation bowl re-edited as bowl {number} in Moriggi 2014.",
            f"Bowl no. {number} ({designation}), p. {page}",
            page,
            f"Full re-edition entry for Syriac bowl {number}; catalogue-level metadata only.",
            rationale,
            object_id,
        )
        record["identifiers"] = [
            {"scheme": "publication object key", "value": publication_key, "assigning_body": "Marco Moriggi", "confidence": 1.0},
            {"scheme": "publication designation", "value": f"Moriggi 2014 bowl {number}: {designation}", "assigning_body": "Marco Moriggi", "confidence": 1.0},
        ]
        record["identifiers"].extend(
            {"scheme": "collection designation", "value": value, "confidence": 1.0}
            for value in collections
        )
        record["claims"].append({"field": "inscription_language", "value_text": "Syriac", "locator": f"Bowl no. {number}, p. {page}", "certainty": "reported"})
        if designation.startswith("–"):
            record["claims"].append({"field": "collection_history", "value_text": designation.lstrip("– "), "locator": "Syriac Incantation Bowls concordance", "certainty": "reported"})
        output.append(record)
    return output


def build_mrla8(conn, rows):
    source = {"source_id": "SRC-8A145FAA2EBB", "url": "https://doi.org/10.1163/9789004411838"}
    output = []
    for number in range(1, 69):
        designation, page = rows[number]
        publication_key = f"MRLA 8::{number}"
        collections = [part.strip() for part in designation.split(" + ")]
        object_id, basis = match_object(conn, collections, publication_key)
        if number <= 30:
            classification, object_type, status, authenticity = "JBA or Hebrew bowl", "whole_bowl", "probable", "unassessed"
            language = "Jewish Babylonian Aramaic and/or Hebrew"
        elif number <= 36:
            classification, object_type, status, authenticity = "Syriac bowl", "whole_bowl", "probable", "unassessed"
            language = "Syriac"
        elif number <= 40:
            classification, object_type, status, authenticity = "Mandaic bowl", "whole_bowl", "probable", "unassessed"
            language = "Mandaic"
        else:
            classification, object_type, status, authenticity = MRLA8_LATE[number]
            language = None
        rationale = (
            f"Linked to the existing object by {basis}; the inspected catalogue explicitly assigns {designation} to entry {number}."
            if object_id
            else f"Created as a separate candidate because {basis}; no identity merge was inferred."
        )
        record = base_record(
            source,
            f"Hilprecht Collection {designation} (MRLA 8, {number})",
            object_type,
            status,
            authenticity,
            f"Hilprecht Collection object catalogued as MRLA 8 entry {number}: {classification}",
            f"Entry {number} ({designation}), p. {page}",
            page,
            f"Catalogue entry {number} for {designation}; catalogue-level metadata only.",
            rationale,
            object_id,
        )
        record["identifiers"] = [
            {"scheme": "publication object key", "value": publication_key, "assigning_body": "Ford and Morgenstern", "confidence": 1.0},
        ]
        record["identifiers"].extend(
            {"scheme": "collection designation", "value": value, "assigning_body": "Frau Professor Hilprecht Collection", "confidence": 1.0}
            for value in collections
        )
        record["claims"].append({"field": "current_or_reported_collection", "value_text": "Frau Professor Hilprecht Collection of Babylonian Antiquities, Jena", "locator": f"Entry {number}, p. {page}", "certainty": "reported"})
        record["claims"].append({"field": "catalogue_classification", "value_text": classification, "locator": f"Entry {number}, p. {page}", "certainty": "reported"})
        if language:
            record["claims"].append({"field": "inscription_language", "value_text": language, "locator": f"Section heading and entry {number}, p. {page}", "certainty": "reported"})
        output.append(record)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--abs1", type=Path, required=True)
    parser.add_argument("--abs2", type=Path, required=True)
    parser.add_argument("--moriggi", type=Path, required=True)
    parser.add_argument("--mrla8", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    records = []
    records.extend(build_abs(conn, parse_abs(args.abs1, SOURCES["abs1"]["range"]), "abs1"))
    records.extend(build_abs(conn, parse_abs(args.abs2, SOURCES["abs2"]["range"]), "abs2"))
    records.extend(build_moriggi(conn, parse_moriggi(args.moriggi)))
    records.extend(build_mrla8(conn, parse_mrla8(args.mrla8)))
    if len(records) != 236:
        raise ValueError(f"expected 236 records, built {len(records)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    linked = sum("object_id" in record for record in records)
    print(json.dumps({"records": len(records), "linked_existing": linked, "new_candidates": len(records) - linked, "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
