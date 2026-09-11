#!/usr/bin/env python3
"""Build catalogue-level object appearances from three supplied editions.

The generated manifest contains identifiers, locators, and conservative source-
attributed classifications only. It does not reproduce transcriptions,
translations, commentary, or images from the copyrighted books.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path


OBSERVED_AT = "2026-09-11"


LEVENE_ROWS = [
    ("VA.2484", 20), ("VA.2509", 30), ("VA.2423", 35), ("VA.2416", 45),
    ("VA.2434", 52), ("VA.2424", 57), ("VA.2496", 62), ("VA.2575", 62),
    ("VA.3382", 74), ("VA.3381", 79), ("VA.2492", 84), ("VA.2418", 87),
    ("VA.2417", 90), ("SD 27", 95), ("M102", 108), ("M163", 110),
    ("005A (BM 91745)", 114), ("024A (BM 91760)", 116),
    ("039A (BM 91771)", 117), ("040A (BM 91767)", 119),
    ("041A (BM 91763)", 121), ("043A (BM 91770)", 123),
    ("N&Sh B6", 124), ("N&Sh B7", 125), ("N&Sh B9", 126),
    ("N&Sh B21", 128), ("N&Sh B23", 130),
    ("Isbell 22 (Gordon 1934b)", 131), ("Royal Ontario Museum 907.1.1", 132),
    ("YBC 2393", 133),
]


NAVEH_ROWS = [
    ("Bowl 1", "Former V. Barakat collection", 124, "Syriac"),
    ("Bowl 2", "Hebrew University Institute of Archaeology 1401", 134, "Jewish Babylonian Aramaic"),
    ("Bowl 3", "Hebrew University Institute of Archaeology 1399", 146, "Jewish Babylonian Aramaic"),
    ("Bowl 4", "Hebrew University Institute of Archaeology 1042", 152, "Jewish Babylonian Aramaic"),
    ("Bowl 5", "Israel Museum 80.1.1", 158, "Jewish Babylonian Aramaic"),
    ("Bowl 6", "Israel Museum 80.1.2", 164, "Jewish Babylonian Aramaic"),
    ("Bowl 7", "Israel Museum 80.1.3", 168, "Jewish Babylonian Aramaic"),
    ("Bowl 8", "Israel Museum 69.20.265", 172, "Jewish Babylonian Aramaic"),
    ("Bowl 9", "Former V. Barakat collection", 174, "Jewish Babylonian Aramaic"),
    ("Bowl 10", "Jewish Historical Museum, Belgrade 243", 180, "Syriac"),
    ("Bowl 11", "Jewish Historical Museum, Belgrade 242/1", 184, "Jewish Babylonian Aramaic"),
    ("Bowl 12a", "National Library of Israel Heb. 4° 6079", 188, "Jewish Babylonian Aramaic"),
    ("Bowl 12b", "Metropolitan Museum of Art 86.11.259", 188, "Jewish Babylonian Aramaic"),
    ("Bowl 13", "V. Klagsbald collection", 198, "Jewish Babylonian Aramaic"),
]


BERLIN_EDITIONS = {
    "VA.2182": ("I", 11), "VA.3854": ("II", 16), "VA.2418": ("III", 24),
    "VA.2428": ("IV", 27), "VA.Bab.2829": ("V", 30), "VA.2269": ("VI", 33),
    "VA.2510": ("VII", 35), "VA.2419": ("VIII", 37), "VA.2445": ("IX", 43),
    "VA.2439": ("X", 46), "VA.2435": ("XI", 51), "VA.3383": ("XII", 54),
    "VA.Bab.2765": ("XIII", 57), "VA.Bab.4167i": ("XIV", 60),
    "VA.Bab.2792": ("XV", 62), "VA.Bab.2764": ("XVIa", 65),
    "VA.Bab.2840": ("XVIb", 65),
}


def normalized(value):
    return "".join(value.strip().casefold().split())


def exact_objects(conn, scheme, value):
    return {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT object_id FROM identifiers WHERE lower(scheme)=lower(?) AND normalized_value=? AND object_id IS NOT NULL",
            (scheme, normalized(value)),
        )
    }


def match_object(conn, collections, publication_key):
    hits = set()
    for value in collections:
        hits.update(exact_objects(conn, "collection designation", value))
    if len(hits) == 1:
        return next(iter(hits)), "exact collection designation"
    if len(hits) > 1:
        return None, "the supplied designations resolve to multiple existing objects"
    hits = exact_objects(conn, "publication object key", publication_key)
    if len(hits) == 1:
        return next(iter(hits)), "exact publication-object key"
    if len(hits) > 1:
        return None, "the publication-object key is already ambiguous"
    return None, "no exact existing identifier match"


def make_record(source_id, url, label, summary, locator, publication_key, collections,
                claims, object_type="whole_bowl", status="probable", authenticity="unassessed",
                object_id=None, rationale_basis="no exact existing identifier match"):
    record = {
        "label": label,
        "object_type": object_type,
        "record_status": status,
        "authenticity": authenticity,
        "summary": summary,
        "source_id": source_id,
        "appearance": {
            "locator": locator,
            "url": url,
            "observed_at": OBSERVED_AT,
            "description": "Catalogue-level metadata from a complete researcher-inspected edition.",
            "relation_type": "primary",
            "confidence": 1.0,
            "rationale": (
                f"Linked to an existing object by {rationale_basis}."
                if object_id else
                f"Created as a separate candidate because {rationale_basis}; no identity merge was inferred."
            ),
        },
        "identifiers": [
            {"scheme": "publication object key", "value": publication_key, "confidence": 1.0},
        ] + [
            {"scheme": "collection designation", "value": value, "confidence": 1.0}
            for value in collections
        ],
        "claims": claims + [{
            "field": "publication_status",
            "value_text": "Catalogued in a complete researcher-inspected edition.",
            "locator": locator,
            "certainty": "reported",
            "notes": "Copyrighted transcription, translation, commentary, and images remain in the private source archive and are not reproduced here.",
        }],
    }
    if object_id:
        record["object_id"] = object_id
    return record


def levene_collections(designation):
    parenthetical = re.search(r"\((BM \d+)\)", designation)
    if parenthetical:
        return [parenthetical.group(1)]
    if designation.startswith("N&Sh ") or designation.startswith("Isbell "):
        return []
    return [designation]


def build_levene(conn):
    records = []
    for designation, page in LEVENE_ROWS:
        key = f"Levene 2013::{designation}"
        collections = levene_collections(designation)
        object_id, basis = match_object(conn, collections, key)
        records.append(make_record(
            "SRC-F2BEFBEFFC2E", "https://doi.org/10.1163/9789004257269",
            f"Levene 2013: {designation}",
            f"Jewish Babylonian Aramaic curse bowl discussed as {designation} in Levene 2013.",
            f"{designation}, p. {page}", key, collections,
            [{"field": "inscription_language", "value_text": "Jewish Babylonian Aramaic", "locator": f"{designation}, p. {page}", "certainty": "reported"},
             {"field": "text_function", "value_text": "Aggressive or curse magic", "locator": f"{designation}, p. {page}", "certainty": "reported"}],
            object_id=object_id, rationale_basis=basis,
        ))
    return records


def build_naveh(conn):
    records = []
    for designation, collection, page, language in NAVEH_ROWS:
        key = f"Naveh-Shaked 1985::{designation}"
        collections = [] if collection.startswith(("Former ", "V. Klagsbald")) else [collection]
        object_id, basis = match_object(conn, collections, key)
        records.append(make_record(
            "SRC-1E2E21DC61BD", None,
            f"Naveh–Shaked 1985 {designation}: {collection}",
            f"Aramaic incantation bowl published as {designation} in Naveh and Shaked 1985.",
            f"{designation} ({collection}), p. {page}", key, collections,
            [{"field": "inscription_language", "value_text": language, "locator": f"{designation}, p. {page}", "certainty": "reported"},
             {"field": "current_or_reported_collection", "value_text": collection, "locator": f"contents and {designation}, p. {page}", "certainty": "reported"}],
            object_id=object_id, rationale_basis=basis,
        ))
    return records


def clean_berlin_shelf(raw):
    value = re.sub(r"\s*\([^)]*\)\s*$", "", raw.strip())
    value = value.replace("VA.Bab.281488", "VA.Bab.2814").replace("VA.Bab.282089", "VA.Bab.2820")
    return value


def field(block, name):
    match = re.search(rf"(?ms)^{re.escape(name)}:\s*(.*?)(?=^[A-Z][A-Za-z ]+:|\Z)", block)
    if not match:
        return None
    return " ".join(match.group(1).replace("\u00ad", "").split())


def berlin_type(raw_shelf, block):
    lower = raw_shelf.casefold()
    if "skull" in lower or "eggshell" in lower or field(block, "Condition of item"):
        return "non_bowl"
    condition = (field(block, "Condition of bowl") or "").casefold()
    if "fragment" in condition:
        return "fragment"
    if "reconstruct" in condition:
        return "reconstructed"
    if "complete" in condition:
        return "whole_bowl"
    return "uncertain"


def parse_berlin(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    starts = list(re.finditer(r"(?m)^\f*(\d{1,3})\s+Shelf mark:\s*(.+?)\s*$", text))
    if len(starts) != 169 or [int(m.group(1)) for m in starts] != list(range(1, 170)):
        raise ValueError(f"expected Berlin entries 1-169, found {len(starts)}")
    rows = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else text.find("Joined Fragments", match.end())
        block = text[match.end():end]
        pdf_page = text[:match.start()].count("\f") + 1
        rows.append((int(match.group(1)), match.group(2).strip(), pdf_page - 14, block))
    return rows


def build_berlin(conn, rows):
    records = []
    for number, raw_shelf, page, block in rows:
        shelf = clean_berlin_shelf(raw_shelf)
        collections = [part.strip() for part in shelf.split(" + ")]
        dialect = field(block, "Dialect")
        object_type = berlin_type(raw_shelf, block)
        authenticity = "pseudo_script" if dialect and "pseudo" in dialect.casefold() else "unassessed"
        status = "rejected" if object_type == "non_bowl" else ("candidate" if authenticity == "pseudo_script" or object_type == "uncertain" else "probable")
        components = [None]
        if number == 168:
            components = ["minimum bowl A", "minimum bowl B"]
            collections = []
            object_type = "uncertain"
            status = "candidate"
        for component in components:
            suffix = f"::{component[-1]}" if component else ""
            key = f"Bhayro-Ford-Levene-Saar 2018::{number}{suffix}"
            object_id, basis = match_object(conn, collections, key)
            locator = f"Catalogue entry {number} ({raw_shelf}), p. {page}"
            if component:
                locator += f", {component}"
            claims = [
                {"field": "current_or_reported_collection", "value_text": "Vorderasiatisches Museum, Berlin", "locator": locator, "certainty": "reported"},
                {"field": "catalogue_shelf_mark", "value_text": raw_shelf, "locator": locator, "certainty": "reported"},
            ]
            if dialect:
                claims.append({"field": "catalogue_dialect", "value_text": dialect, "locator": locator, "certainty": "reported"})
            if component:
                claims.append({"field": "physical_object_count", "value_text": "Entry contains fragments from at least two different bowls; component assignment is unresolved.", "locator": locator, "certainty": "uncertain"})
            for collection in collections:
                if collection in BERLIN_EDITIONS:
                    roman, edition_page = BERLIN_EDITIONS[collection]
                    claims.append({"field": "publication_status", "value_text": f"Receives a selected full edition as text {roman}.", "locator": f"Text {roman}, p. {edition_page}", "certainty": "reported"})
            records.append(make_record(
                "SRC-DA708912C2D3", "https://doi.org/10.1163/9789004373686",
                f"Vorderasiatisches Museum {raw_shelf} (catalogue {number}{' ' + component if component else ''})",
                f"Berlin catalogue entry {number}{' ' + component if component else ''}; object type is retained conservatively from the catalogue description.",
                locator, key, collections, claims, object_type, status, authenticity,
                object_id, basis,
            ))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--berlin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    records = build_levene(conn) + build_naveh(conn) + build_berlin(conn, parse_berlin(args.berlin))
    if len(records) != 214:
        raise ValueError(f"expected 214 records, built {len(records)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    print(json.dumps({
        "records": len(records),
        "linked_existing": sum("object_id" in row for row in records),
        "new_candidates": sum("object_id" not in row for row in records),
        "by_source": {source: sum(row["source_id"] == source for row in records) for source in sorted({row["source_id"] for row in records})},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
