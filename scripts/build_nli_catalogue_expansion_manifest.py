#!/usr/bin/env python3
"""Build checked manifests for the NLI catalogue expansion found in September 2026."""

import argparse
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


NLI_SRU = "https://nli.alma.exlibrisgroup.com/view/sru/972NNL_INST"
SRU_NS = {"s": "http://www.loc.gov/zing/srw/", "m": "http://www.loc.gov/MARC21/slim"}


def fetch(query, maximum=100):
    params = {
        "version": "1.2",
        "operation": "searchRetrieve",
        "recordSchema": "marcxml",
        "maximumRecords": min(maximum, 50),
        "startRecord": 1,
        "query": query,
    }
    url = NLI_SRU + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = response.read()
    root = ET.fromstring(payload)
    total = int(root.findtext("./s:numberOfRecords", default="0", namespaces=SRU_NS))
    if total > maximum:
        raise ValueError(f"query returned {total} records, above checked manifest limit {maximum}")
    records = list(root.findall(".//m:record", SRU_NS))
    for start in range(51, total + 1, 50):
        page_params = dict(params, startRecord=start)
        page_url = NLI_SRU + "?" + urllib.parse.urlencode(page_params)
        with urllib.request.urlopen(page_url, timeout=30) as response:
            page_root = ET.fromstring(response.read())
        records.extend(page_root.findall(".//m:record", SRU_NS))
    if len(records) != total:
        raise ValueError(f"query reported {total} records but returned {len(records)}")
    return url, records


def fields(record, tag):
    result = []
    for field in record.findall(f"./m:datafield[@tag='{tag}']", SRU_NS):
        values = {}
        for subfield in field.findall("./m:subfield", SRU_NS):
            values.setdefault(subfield.attrib["code"], []).append(subfield.text or "")
        result.append(values)
    return result


def first(record, tag, code="a"):
    matched = fields(record, tag)
    return matched[0].get(code, [None])[0] if matched else None


def control(record, tag):
    return record.findtext(f"./m:controlfield[@tag='{tag}']", default="", namespaces=SRU_NS)


def organizations(record):
    result = []
    for field in fields(record, "710"):
        result.append({
            "name": field.get("a", [""])[0],
            "place": field.get("x", [None])[0],
            "country": field.get("c", [None])[0],
            "role": field.get("e", [None])[0],
        })
    return result


def digital_designations(record):
    return [field.get("e", [""])[0] for field in fields(record, "907") if field.get("e")]


def holder_designations(record, owner_name):
    return [
        field.get("z", [""])[0]
        for field in fields(record, "942")
        if field.get("a", [""])[0] == owner_name and field.get("z")
    ]


def source_for(title, mms_id, shelfmark):
    record_url = f"https://www.nli.org.il/en/manuscripts/NNL_ALEPH{mms_id}/NLI"
    locator = shelfmark or f"MMS {mms_id}"
    return record_url, {
        "source_type": "museum_record",
        "title": title,
        "authors": "National Library of Israel",
        "publisher": "National Library of Israel",
        "url": record_url,
        "citation": f"National Library of Israel, {title}, {locator}, MMS {mms_id}.",
        "access_status": "available",
        "rights_status": "unknown",
        "notes": "Item-level metadata observed through the NLI public Alma SRU catalogue.",
    }


def iaa_record(record, query_url):
    title = (first(record, "245") or "").rstrip(". ")
    match = re.fullmatch(r"קערת השבעה רה[\"״]ע מס['׳]\s*(\d+)", title)
    if not match:
        raise ValueError(f"unexpected IAA-series title: {title!r}")
    number = int(match.group(1))
    mms_id = control(record, "001")
    shelfmark = first(record, "090")
    orgs = organizations(record)
    owners = [item for item in orgs if item["role"] == "current owner"]
    if [item["name"] for item in owners] != ["Israel Antiquities Authority"]:
        raise ValueError(f"IAA bowl {number} has unexpected current owner metadata: {owners!r}")
    designations = digital_designations(record)
    collection_designations = holder_designations(record, "Israel Antiquities Authority")
    expected_collection_designation = f"Bowl {number}"
    if expected_collection_designation not in collection_designations:
        raise ValueError(
            f"IAA bowl {number} lacks MARC 942 designation {expected_collection_designation!r}"
        )
    digital_label_matches_number = any(
        value.casefold().endswith(expected_collection_designation.casefold())
        for value in designations
    )
    record_url, source = source_for(title, mms_id, shelfmark)
    raw = {
        "catalogue_query_url": query_url,
        "collection_designations": collection_designations,
        "digital_label_matches_number": digital_label_matches_number,
        "digital_designations": designations,
        "mms_id": mms_id,
        "modified_at": control(record, "005"),
        "organizations": orgs,
        "shelfmark": shelfmark,
        "title": title,
    }
    return number, {
        "label": f"IAA incantation bowl {number} (NLI digital record)",
        "object_type": "whole_bowl",
        "record_status": "candidate",
        "authenticity": "unassessed",
        "summary": (
            "NLI catalogue appearance for a numbered incantation bowl whose MARC metadata "
            "identifies the Israel Antiquities Authority as current owner; concordance with "
            "previously indexed objects remains unresolved."
        ),
        "source": source,
        "appearance": {
            "locator": f"MMS {mms_id}",
            "title": title,
            "url": record_url,
            "observed_at": "2026-09-26",
            "description": (
                f"NLI digital catalogue record for IAA bowl number {number}; the Hebrew "
                "abbreviation רה\"ע is preserved without expansion. Exact MARC 907 labels "
                f"are retained in raw metadata: {', '.join(designations)}."
            ),
            "confidence": 1.0,
            "rationale": "The official catalogue record describes this numbered IAA object.",
            "raw": raw,
        },
        "identifiers": [
            {
                "scheme": "NLI MMS ID",
                "value": mms_id,
                "assigning_body": "National Library of Israel",
            },
            {
                "scheme": "IAA bowl number",
                "value": str(number),
                "assigning_body": "Israel Antiquities Authority",
                "notes": (
                    f"NLI MARC 942 designation {expected_collection_designation}; "
                    f"MARC 907 digital label(s): {', '.join(designations)}."
                ),
            },
            {
                "scheme": "collection designation",
                "value": expected_collection_designation,
                "assigning_body": "Israel Antiquities Authority",
            },
        ],
        "claims": [
            {
                "field": "current_location",
                "value_text": "Israel Antiquities Authority, Jerusalem",
                "certainty": "reported",
                "notes": "NLI MARC 710 identifies the Israel Antiquities Authority as current owner.",
            },
            {
                "field": "catalogue_title",
                "value_text": title,
                "certainty": "reported",
                "notes": "Preserved exactly; the abbreviation רה\"ע is not expanded by the index.",
            },
        ],
    }


def additional_record(record, query_url):
    title = (first(record, "245") or "").rstrip(". ")
    if title != "קערה מאגית":
        raise ValueError(f"unexpected magical-bowl title: {title!r}")
    mms_id = control(record, "001")
    shelfmark = first(record, "090")
    expected = {"Ms. Heb. 6079=34"} | {f"Ms. Heb. 6417.{number}=34" for number in range(1, 8)}
    if shelfmark not in expected:
        raise ValueError(f"unexpected magical-bowl shelfmark: {shelfmark!r}")
    orgs = organizations(record)
    owners = [item for item in orgs if item["role"] == "current owner"]
    if [item["name"] for item in owners] != ["The National Library of Israel"]:
        raise ValueError(f"{shelfmark} has unexpected current owner metadata: {owners!r}")
    provenance_notes = [value for field in fields(record, "561") for value in field.get("a", [])]
    language_codes = sorted({value for field in fields(record, "041") for value in field.get("a", [])})
    record_url, source = source_for(title, mms_id, shelfmark)
    is_scholem = shelfmark == "Ms. Heb. 6079=34"
    group = "Scholem" if is_scholem else "Klagsbald"
    claims = [
        {
            "field": "current_location",
            "value_text": "National Library of Israel, Jerusalem",
            "certainty": "reported",
            "notes": "NLI MARC 710 identifies the National Library of Israel as current owner.",
        }
    ]
    normalized_history = {
        "הקערה נתרמה לבית הספרים על ידי פרופסור גרשם שלום, שקיבל אותה במתנה מאת ולדימיר רוזנבאום, סוחר עתיקות באסקונה, שווייץ.": (
            "Donated to the National Library of Israel by Gershom Scholem, who had received "
            "the bowl as a gift from Vladimir Rosenbaum, an antiquities dealer in Ascona, Switzerland."
        ),
        "לפנים פריס - קלגסבלד": "Formerly Paris – Klagsbald.",
        "נתרמו על ידי מר אביגדור קלגסבלד": "Donated by Avigdor Klagsbald.",
    }
    for note in provenance_notes:
        claims.append({
            "field": "collection_history_source_text",
            "value_text": note,
            "certainty": "reported",
            "notes": "Hebrew MARC 561 text preserved verbatim.",
        })
        normalized = normalized_history.get(note)
        if normalized:
            claims.append({
                "field": "collection_history",
                "value_text": normalized,
                "certainty": "reported",
                "notes": (
                    "Project translation and normalization of the NLI MARC 561 statement; "
                    "the Hebrew source string is retained separately."
                ),
            })
    if language_codes:
        claims.append({
            "field": "catalogue_language_codes",
            "value_text": "; ".join(language_codes),
            "certainty": "reported",
            "notes": "MARC 041 codes; not treated as an adjudicated inscription-language claim.",
        })
    raw = {
        "catalogue_query_url": query_url,
        "language_codes": language_codes,
        "mms_id": mms_id,
        "modified_at": control(record, "005"),
        "organizations": orgs,
        "provenance_notes": provenance_notes,
        "shelfmark": shelfmark,
        "title": title,
    }
    return shelfmark, {
        "label": f"NLI {group} incantation bowl ({shelfmark})",
        "object_type": "whole_bowl",
        "record_status": "candidate",
        "authenticity": "unassessed",
        "summary": (
            f"Item-level NLI catalogue appearance for the {group} bowl at {shelfmark}; "
            "identity against existing source-derived records remains unresolved."
        ),
        "source": source,
        "appearance": {
            "locator": f"MMS {mms_id}",
            "title": title,
            "url": record_url,
            "observed_at": "2026-09-26",
            "description": f"NLI item-level catalogue record for {shelfmark}.",
            "confidence": 1.0,
            "rationale": "The official NLI catalogue record describes this shelfmarked object.",
            "raw": raw,
        },
        "identifiers": [
            {
                "scheme": "NLI MMS ID",
                "value": mms_id,
                "assigning_body": "National Library of Israel",
            },
            {
                "scheme": "collection designation",
                "value": shelfmark,
                "assigning_body": "National Library of Israel",
            },
        ],
        "claims": claims,
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    root = args.output_root

    iaa_query = 'alma.title="קערת השבעה רה\\"ע"'
    iaa_url, iaa_xml = fetch(iaa_query)
    iaa_rows = [iaa_record(record, iaa_url) for record in iaa_xml]
    iaa_numbers = [number for number, _ in iaa_rows]
    if sorted(iaa_numbers) != list(range(1, 75)) or len(set(iaa_numbers)) != 74:
        raise ValueError(f"IAA series is not exactly 1–74: {sorted(iaa_numbers)!r}")
    digital_label_anomalies = [
        {
            "number": number,
            "digital_designations": row["appearance"]["raw"]["digital_designations"],
        }
        for number, row in sorted(iaa_rows)
        if not row["appearance"]["raw"]["digital_label_matches_number"]
    ]

    additional_query = 'alma.title="קערה מאגית"'
    additional_url, additional_xml = fetch(additional_query)
    additional_rows = [additional_record(record, additional_url) for record in additional_xml]
    expected_shelfmarks = {"Ms. Heb. 6079=34"} | {
        f"Ms. Heb. 6417.{number}=34" for number in range(1, 8)
    }
    if {shelfmark for shelfmark, _ in additional_rows} != expected_shelfmarks:
        raise ValueError("magical-bowl query did not return the expected Scholem/Klagsbald set")

    main_query = 'alma.title="קערת השבעה"'
    main_url, main_xml = fetch(main_query, maximum=400)
    numbered = []
    shelfmarks = []
    for record in main_xml:
        title = (first(record, "245") or "").rstrip(". ")
        match = re.fullmatch(r"קערת השבעה מס['׳]?\s*(\d+)", title)
        if match:
            numbered.append(int(match.group(1)))
            shelfmarks.append(first(record, "090"))
    missing_numbers = sorted(set(range(1, 217)) - set(numbered))
    if len(numbered) != 205 or missing_numbers != [2, 52, 97, 98, 152, 202, 203, 204, 205, 206, 216]:
        raise ValueError(
            f"unexpected main-series reconciliation: {len(numbered)} records, missing {missing_numbers}"
        )
    expected_run = {f"Ms. Heb. 9467.{number}" for number in range(3, 208)}
    if set(shelfmarks) != expected_run:
        raise ValueError("main NLI shelfmarks are not exactly Ms. Heb. 9467.3–207")

    write_jsonl(
        root / "research/seeds/nli_iaa_catalogue_series_2026-09-26.jsonl",
        [row for _, row in sorted(iaa_rows)],
    )
    write_jsonl(
        root / "research/seeds/nli_additional_holdings_2026-09-26.jsonl",
        [row for _, row in sorted(additional_rows)],
    )
    write_jsonl(
        root / "research/searches/nli_catalogue_expansion_2026-09-26.jsonl",
        [
            {
                "source_class": "museum",
                "language": "he",
                "query": iaa_query,
                "platform": "National Library of Israel Alma SRU",
                "searched_at": "2026-09-26",
                "result_count": 74,
                "net_new_candidates": 74,
                "status": "searched",
                "notes": (
                    "All 74 item records were ingested as catalogue-backed candidates. Every "
                    "record names the Israel Antiquities Authority as current owner and carries "
                    "a MARC 942 designation from Bowl 1 through Bowl 74; no expansion of "
                    "the Hebrew abbreviation רה\"ע was inferred. Exact MARC 907 labels were "
                    f"retained; mismatches were found at: {digital_label_anomalies}."
                ),
            },
            {
                "source_class": "museum",
                "language": "he",
                "query": additional_query,
                "platform": "National Library of Israel Alma SRU",
                "searched_at": "2026-09-26",
                "result_count": 8,
                "net_new_candidates": 8,
                "status": "follow_up",
                "notes": (
                    "Located the item-level record for the Scholem bowl at Ms. Heb. 6079=34 and "
                    "the seven Klagsbald bowls at Ms. Heb. 6417.1–7=34. Catalogue appearances "
                    "were ingested without merging them into existing source-derived objects."
                ),
            },
        ],
    )
    leads = [
        {
            "id": "LED-F6E157C6B6AD",
            "source": {
                "source_type": "web_page",
                "title": "Magic Bowls",
                "authors": "National Library of Israel",
                "publisher": "National Library of Israel",
                "url": "https://exhibition.nli.org.il/en/exhibition-items-en/magic-bowls",
                "citation": (
                    "National Library of Israel, “Magic Bowls,” permanent exhibition item, "
                    "accessed 26 September 2026."
                ),
                "access_status": "available",
                "rights_status": "copyrighted",
                "notes": (
                    "States that 216 rare magical bowls from the private collection of the late "
                    "Shlomo Moussaieff were donated to the Library."
                ),
            },
            "lead_type": "collection",
            "description": (
                "Reconcile the National Library of Israel exhibition statement that 216 "
                "Moussaieff incantation bowls were donated with the 205 numbered "
                "incantation-bowl SRU records harvested in this campaign."
            ),
            "url": "https://exhibition.nli.org.il/en/exhibition-items-en/magic-bowls",
            "status": "in_progress",
            "priority": 1,
            "resolution_notes": (
                "The 205 public records form the complete shelfmark run Ms. Heb. 9467.3–207. "
                "Their titles omit bowl numbers 2, 52, 97, 98, 152, 202–206, and 216, exactly "
                "eleven numbers. NLI staff clarification has been requested; no absent object "
                "record has been invented."
            ),
        },
        {
            "id": "LED-763822DAE92A",
            "source_id": "SRC-BCC98AAE8C40",
            "lead_type": "identifier",
            "description": (
                "Map the seven Avigdor Klagsbald donation bowls to exact NLI "
                "catalogue/manuscript identifiers and determine which overlap the 205 "
                "harvested NLI SRU records."
            ),
            "url": "https://blog.nli.org.il/en/magical_bowls/",
            "status": "in_progress",
            "priority": 1,
            "resolution_notes": (
                "The exact item-level NLI records are now known: Ms. Heb. 6417.1=34 through "
                "Ms. Heb. 6417.7=34. They are outside the 205-record Ms. Heb. 9467 series. "
                "The catalogue appearances were ingested as separate candidates; mapping to "
                "the seven earlier anonymous donation components remains unadjudicated."
            ),
        },
        {
            "lead_type": "identifier",
            "description": (
                "Reconcile NLI Ms. Heb. 6079=34 (MMS 990026405980205171) with the existing "
                "JNL Heb 4, 6079 and Naveh–Shaked 1985 Bowl 12a records."
            ),
            "url": "https://www.nli.org.il/en/manuscripts/NNL_ALEPH990026405980205171/NLI",
            "status": "open",
            "priority": 1,
            "resolution_notes": (
                "The NLI record supplies the exact shelfmark and Scholem/Rosenbaum collection "
                "history, but no identity merge was made without a checked concordance review."
            ),
        },
        {
            "lead_type": "identifier",
            "description": (
                "Find publication or collection concordances for the 74 NLI digital records "
                "labelled IAA Bowl 1–74 and determine overlap with previously indexed objects."
            ),
            "url": iaa_url,
            "status": "open",
            "priority": 1,
            "resolution_notes": (
                "All 74 item-level catalogue appearances and IAA identifiers are now retained; "
                "they remain candidates until external concordances establish identity links."
            ),
        },
    ]
    write_jsonl(root / "research/leads/nli_collection_reconciliation_2026-09-26.jsonl", leads)

    evidence = {
        "observed_at": "2026-09-26",
        "source": "National Library of Israel public Alma SRU",
        "main_numbered_series": {
            "query_url": main_url,
            "record_count": len(numbered),
            "number_range_checked": [1, 216],
            "missing_numbers": missing_numbers,
            "shelfmark_run": ["Ms. Heb. 9467.3", "Ms. Heb. 9467.207"],
            "shelfmark_count": len(set(shelfmarks)),
        },
        "iaa_owned_series": {
            "query_url": iaa_url,
            "record_count": len(iaa_rows),
            "number_range": [1, 74],
            "digital_label_anomalies": digital_label_anomalies,
            "validation": (
                "Every record identifies Israel Antiquities Authority as current owner and "
                "contains the matching MARC 942 designation Bowl N. Exact MARC 907 digital "
                "labels are retained, including catalogue anomalies."
            ),
        },
        "separate_nli_holdings": {
            "query_url": additional_url,
            "record_count": len(additional_rows),
            "shelfmarks": sorted(expected_shelfmarks),
        },
        "limits": [
            "The 74-record result establishes the extent of this NLI catalogue series, not the total size of all IAA bowl holdings.",
            "The expansion of רה\"ע is not established by the catalogue metadata and remains unasserted.",
            "No identity merge follows solely from these catalogue records.",
            "No records were created for the eleven unlisted Moussaieff-series numbers.",
        ],
    }
    evidence_path = root / "research/reviews/nli_catalogue_expansion_evidence_2026-09-26.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
