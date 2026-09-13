#!/usr/bin/env python3
"""Build checked Gordon 1934/1937 manifests from complete inspected scans."""

import argparse
import hashlib
import json
from pathlib import Path


OBSERVED_AT = "2026-09-12"
REVIEWED_AT = "2026-09-13T03:45:00Z"

SOURCES = {
    "AF": {
        "id": "SRC-60CB324330C9",
        "key": "Gordon 1934 Istanbul-Baghdad",
        "url": "https://kramerius.lib.cas.cz/uuid/4a5877af-4e59-43cd-8466-495357b59642",
        "capture": "CAP-138518C319C8",
        "sha256": "5abd9af65823f4fe8b19eb76ecc7f9668f1e3de35b2535c5166461eca23bd1ce",
    },
    "G": {
        "id": "SRC-0383E0E0A2F2",
        "key": "Gordon 1934 Exorcism",
        "url": "https://kramerius.lib.cas.cz/uuid/8a069457-1e3c-40d3-a658-3b1c51fe66e8",
        "capture": "CAP-EABFF9404C4C",
        "sha256": "71de7b86e0cc549b73d949f4a4b8923886f4d92dfd1b2f21907c9fe6058bafcc",
    },
    "HO": {
        "id": "SRC-43C1E102538E",
        "key": "Gordon 1937",
        "url": "https://kramerius.lib.cas.cz/uuid/b2bef7bf-5a00-4d50-ad2c-40872e98e1ff",
        "capture": "CAP-A5A03BFD5DC7",
        "sha256": "c2c86d28ae3201f95475d89c45789d58a37a0e9ba125876503b833c78d7fb612",
    },
    "IM9737": {
        "id": "SRC-C45C16AC2B8E",
        "key": "Gordon 1934 Incantation",
        "url": "https://ignca.gov.in/Asi_data/4567.pdf",
    },
}

EXISTING = {
    "A": "IBI-444B0B07BA0E",
    "B": "IBI-6CF4E4167D3E",
    "C": "IBI-87782BA285D5",
    "D": "IBI-54398C1767BE",
    "E": "IBI-8B111BFD04DA",
    "F": "IBI-AA3D4D3C35CC",
    "G": "IBI-28C0A68E5312",
    "H": "IBI-F0173A70F87B",
    "I": "IBI-67E68F81FE63",
    "J": "IBI-A941F1E8B2F0",
    "K": "IBI-4949F2DB777F",
    "L": "IBI-410C07F078B6",
    "N": "IBI-F265C68D7662",
    "O": "IBI-7BCBBD6A6A80",
    "IM9737": "IBI-762F23251BD0",
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def edition_row(group, letter, object_id, locator, description, collection=None, object_type="uncertain"):
    source = SOURCES[group]
    ids = [{
        "scheme": "publication object key",
        "value": f"{source['key']}::{letter}",
        "assigning_body": "Cyrus H. Gordon",
        "confidence": 1.0,
    }]
    if collection:
        ids.append({
            "scheme": "collection designation",
            "value": collection[0],
            "assigning_body": collection[1],
            "confidence": 1.0,
        })
    return {
        **({"object_id": object_id} if object_id else {}),
        "label": f"Gordon {source['key'].split()[1]} text {letter}",
        "object_type": object_type,
        "record_status": "candidate" if object_id is None else "probable",
        "authenticity": "unassessed",
        "summary": "A separately edited physical bowl in the inspected Gordon article; later collection identity remains unresolved." if object_id is None else None,
        "source_id": source["id"],
        "appearance": {
            "locator": locator,
            "url": source["url"],
            "observed_at": OBSERVED_AT,
            "description": description,
            "relation_type": "primary",
            "confidence": 1.0,
            "rationale": (
                "The inspected primary article prints this exact Gordon text label and collection designation. "
                "The existing object carries the same published label or museum number."
                if object_id else
                "The inspected primary article separately labels and fully edits this physical bowl; no later identity is inferred."
            ),
        },
        "identifiers": ids,
        "claims": [
            {
                "field": "publication_status",
                "value_text": description,
                "locator": locator,
                "certainty": "reported",
            },
            {
                "field": "catalogue_description",
                "value_text": description,
                "locator": locator,
                "certainty": "reported",
                "notes": "Project-authored summary of the inspected primary edition; not a modern reassessment.",
            },
        ],
    }


def candidate_rows():
    rows = []
    af_collections = {
        "B": ("Istanbul 1167", "Museum of Antiquities, Istanbul"),
        "C": ("Istanbul 5365", "Museum of Antiquities, Istanbul"),
        "D": ("IM 6519", "Iraq Museum"),
        "E": ("IM 9745", "Iraq Museum"),
        "F": ("IM 9746", "Iraq Museum"),
    }
    for letter in "ABCDEF":
        rows.append(edition_row(
            "AF", letter, EXISTING[letter],
            f"text {letter}, printed pp. 321-334; plate {'X' if letter == 'A' else {'B':'XI','C':'XII','D':'XIII','E':'XIV','F':'XV'}[letter]}",
            "Complete transcription, English translation, commentary, and hand-copy plate.",
            af_collections.get(letter),
        ))

    survey = [
        ("5233", "whole_bowl", "Large bowl with a clearly written eight-line text and a central bound demon figure; Gordon can read only words and formulae."),
        ("5361", "whole_bowl", "Reddish-brown bowl with a six-line inscription and a central figure with flowing hair, raised elbows, and outspread fingers."),
        ("5377", "whole_bowl", "Bowl with a partly illegible ten-line text, a central knob, and a corrugated exterior."),
        ("1682", "fragment", "Five fragments preserving five concentric circular lines that Gordon classifies as an imitation of Aramaic writing."),
        ("5370", "whole_bowl", "Bowl with three concentrically arranged lines that Gordon classifies as an imitation of Aramaic writing."),
        ("5367", "whole_bowl", "Bowl with a neatly written ten-line text that Gordon describes as perhaps an imitation of Syriac, with a central standing figure."),
        ("1691", "whole_bowl", "Bowl with simulated writing, a central sign, and two holes near the rim that Gordon suggests may have tied it to another bowl."),
    ]
    for number, object_type, description in survey:
        locator = f"Istanbul survey no. {number}, printed {'p. 320' if number in {'5233','5361','5377'} else 'p. 321'}"
        rows.append({
            "label": f"Gordon 1934 Istanbul survey no. {number}",
            "object_type": object_type,
            "record_status": "candidate",
            "authenticity": "unassessed",
            "summary": "A separately numbered museum bowl described in Gordon's inspected Istanbul survey; no later identity is inferred.",
            "source_id": SOURCES["AF"]["id"],
            "appearance": {
                "locator": locator,
                "url": SOURCES["AF"]["url"],
                "observed_at": OBSERVED_AT,
                "description": description,
                "relation_type": "primary",
                "confidence": 1.0,
                "rationale": "The primary article separately describes this exact Istanbul catalogue number; it is not guessed onto a later record.",
            },
            "identifiers": [{
                "scheme": "collection designation",
                "value": f"Istanbul {number}",
                "assigning_body": "Museum of Antiquities, Istanbul",
                "confidence": 1.0,
            }],
            "claims": [
                {"field": "publication_status", "value_text": "Described in Gordon's 1934 Istanbul survey but not fully edited there.", "locator": locator, "certainty": "reported"},
                {"field": "catalogue_description", "value_text": description, "locator": locator, "certainty": "reported", "notes": "Historical source description retained without modern script or authenticity adjudication."},
            ],
        })

    rows.append(edition_row(
        "G", "G", EXISTING["G"], "text G, printed pp. 466-474; plates XXII-XXV; catalogue no. 5497",
        "Complete transcription, English translation, commentary, and hand-copy plates.",
        ("Istanbul 5497", "Museum of Antiquities, Istanbul"),
    ))

    ho_collections = {
        "H": ("JTS 950", "Jewish Theological Seminary"),
        "L": ("USNM 207963", "National Museum, Washington"),
        "M": ("Harvard Semitic Museum 8669", "Harvard Semitic Museum"),
        "O": ("BM 91724", "British Museum"),
    }
    for letter in "HIJKLMNO":
        object_id = None if letter == "M" else EXISTING[letter]
        detail = "Texts H-L are printed in Aramaic characters; texts M-O are Mandaic. The article supplies transcription, English translation, commentary, and plates."
        if letter == "N":
            detail += " Gordon reports no. 91731 as Ashmolean(?) while the current museum record places 91731 in the British Museum; both attributions are retained as source evidence."
        rows.append(edition_row(
            "HO", letter, object_id,
            f"text {letter}, printed pp. 86-106; article plates II-XIVa",
            detail,
            ho_collections.get(letter),
            "whole_bowl" if letter in "MNO" else "uncertain",
        ))

    locator = "introductory footnote 4, printed p. 85; National Museum no. 207962"
    description = "Bowl with two central human figures, a possible serpent, and an interior spiral imitation inscription; Gordon says it seemed to him an ancient fake sold to an unsuspecting buyer."
    rows.append({
        "label": "Gordon 1937 National Museum bowl 207962",
        "object_type": "whole_bowl",
        "record_status": "candidate",
        "authenticity": "unassessed",
        "summary": "A separately numbered National Museum bowl described in Gordon's inspected article; no later identity is inferred.",
        "source_id": SOURCES["HO"]["id"],
        "appearance": {
            "locator": locator,
            "url": SOURCES["HO"]["url"],
            "observed_at": OBSERVED_AT,
            "description": description,
            "relation_type": "primary",
            "confidence": 1.0,
            "rationale": "The primary article separately describes this exact museum number; the historical authenticity opinion is preserved only as a reported claim.",
        },
        "identifiers": [{"scheme": "collection designation", "value": "USNM 207962", "assigning_body": "National Museum, Washington", "confidence": 1.0}],
        "claims": [
            {"field": "publication_status", "value_text": "Briefly described in a footnote to Gordon 1937; not edited there.", "locator": locator, "certainty": "reported"},
            {"field": "catalogue_description", "value_text": description, "locator": locator, "certainty": "reported", "notes": "Gordon's historical opinion is not adopted as the project's authenticity assessment."},
        ],
    })

    rows.append(edition_row(
        "IM9737", "IM9737", EXISTING["IM9737"],
        "article printed pp. 141-144; PDF pp. 154-157; Iraq Museum no. 9737",
        "Complete transcription, English translation, commentary, and hand-copy plate of Iraq Museum no. 9737.",
        ("IM 9737", "Iraq Museum"),
    ))
    for row in rows:
        if row.get("summary") is None:
            row.pop("summary", None)
    return rows


def evidence_manifest():
    return {
        "schema_version": 1,
        "reviewed_by": "Codex",
        "reviewed_at": REVIEWED_AT,
        "method": "Complete articles were downloaded from official institutional repositories, rendered, visually checked at title, catalogue, text, translation, and plate pages, and compared against exact existing publication labels or museum numbers. No uncertain identity was merged.",
        "rights_policy": "Open access is not treated as an open reuse license. Kramerius labels these scans as contractually published works and limits use to non-commercial scientific and educational purposes; source and capture rights therefore remain copyrighted.",
        "sources": [
            {
                "source_id": SOURCES["AF"]["id"], "capture_id": SOURCES["AF"]["capture"], "sha256": SOURCES["AF"]["sha256"],
                "institution": "Library of the Czech Academy of Sciences, Kramerius 7", "volume_uuid": "uuid:5eb9708a-1d6a-4fd2-b4be-b6d1c8360d04",
                "article_page_uuid": "uuid:4a5877af-4e59-43cd-8466-495357b59642", "extent": "printed pp. 319-334 and plates X-XV", "findings": "Full editions A-F plus seven separately numbered Istanbul survey bowls."
            },
            {
                "source_id": SOURCES["G"]["id"], "capture_id": SOURCES["G"]["capture"], "sha256": SOURCES["G"]["sha256"],
                "institution": "Library of the Czech Academy of Sciences, Kramerius 7", "volume_uuid": "uuid:5eb9708a-1d6a-4fd2-b4be-b6d1c8360d04",
                "article_page_uuid": "uuid:8a069457-1e3c-40d3-a658-3b1c51fe66e8", "extent": "printed pp. 466-474 and plates XXII-XXV", "findings": "Full edition G, catalogue no. 5497."
            },
            {
                "source_id": SOURCES["HO"]["id"], "capture_id": SOURCES["HO"]["capture"], "sha256": SOURCES["HO"]["sha256"],
                "institution": "Library of the Czech Academy of Sciences, Kramerius 7", "volume_uuid": "uuid:d12e97ad-d4a3-414f-8461-b2a9e757b680",
                "article_page_uuid": "uuid:b2bef7bf-5a00-4d50-ad2c-40872e98e1ff", "extent": "printed pp. 84-106 and plates II-XIVa", "findings": "Full editions H-O plus National Museum no. 207962; the source's uncertain Ashmolean attribution for no. 91731 is retained."
            },
            {
                "source_id": SOURCES["IM9737"]["id"], "capture_id": None, "sha256": "e0ed2b419f00a1873b01730b144272ca822545344b83969eb8a01c3c187b63cc",
                "institution": "Indira Gandhi National Centre for the Arts scan of AASOR 14", "url": SOURCES["IM9737"]["url"],
                "extent": "printed pp. 141-144; PDF pp. 154-157", "findings": "Full edition of Iraq Museum no. 9737.",
                "archive_note": "The public scan was inspected but not deposited because the project crawler could not verify robots permission. The hash identifies the inspected temporary download only."
            },
        ],
        "independent_checks": [
            {"url": "https://cal.huc.edu/browsesigla.php?generalclass=JBA&subclass=Incantations", "finding": "The Comprehensive Aramaic Lexicon bibliography confirms the four Gordon citations."},
            {"url": "https://www.asor.org/wp-content/uploads/2018/04/2011-04-cop-aasor-list.pdf", "finding": "ASOR's official contents list confirms AASOR 14 and Gordon's article."},
            {"url": "https://apotropaicarts.com/articles/amuletindices/bowlsa/", "finding": "The independent bowl concordance maps Gordon labels A-L and IM 9737 to the existing CAIB and museum designations used for exact attachments."},
        ],
    }


def source_corrections(evidence_path, evidence_sha):
    original_note = "Citation transcribed verbatim from Waller 2025, list of JBA bowl publications, printed pp. 40-47 (SRC-19F191B3F5C5, archive SHA-256 b60b030f13d2...). Not independently verified against the publication itself; title and type are parsed from the citation and may need correction."
    specs = [
        ("AF", "Aramaic Magical Bowls in the Istanbul and Baghdad Museums", "Gordon, Cyrus H", "ArOr", "Gordon, Cyrus H. “ Aramaic Magical Bowls in the Istanbul and Baghdad Museums.” ArOr 6 (1934): 319–34.", "Aramaic Magical Bowls in the Istanbul and Baghdad Museums", "Gordon, Cyrus H. “Aramaic Magical Bowls in the Istanbul and Baghdad Museums.” Archiv orientální 6 (1934): 319–334.", "Complete official repository scan: printed pp. 319-334 and plates X-XV. It fully edits texts A-F and separately describes seven numbered Istanbul bowls recorded in this review."),
        ("G", "An Aramaic Exorcism", "Gordon [and others; see citation]", "ArOr", "———. “ An Aramaic Exorcism.” ArOr 6 (1934): 466–74.", "An Aramaic Exorcism", "Gordon, Cyrus H. “An Aramaic Exorcism.” Archiv orientální 6 (1934): 466–474.", "Complete official repository scan: printed pp. 466-474 and plates XXII-XXV. It fully edits text G, Istanbul catalogue no. 5497."),
        ("HO", "Aramaic and Mandaic Magical Bowls", "Gordon [and others; see citation]", "ArOr", "———. “ Aramaic and Mandaic Magical Bowls.” ArOr 9 (1937): 84–106.", "Aramaic and Mandaic Magical Bowls", "Gordon, Cyrus H. “Aramaic and Mandaic Magical Bowls.” Archiv orientální 9 (1937): 84–106.", "Complete official repository scan: printed pp. 84-106 and plates II-XIVa. It fully edits texts H-O and separately describes National Museum no. 207962."),
        ("IM9737", "An Aramaic Incantation", "Gordon [and others; see citation]", "Annual of the American Schools of Oriental Research", "———. “ An Aramaic Incantation.” Annual of the American Schools of Oriental Research 14 (1934): 141–44.", "An Aramaic Incantation", "Gordon, Cyrus H. “An Aramaic Incantation.” Annual of the American Schools of Oriental Research 14 (1934): 141–144.", "Complete public institutional scan inspected at PDF pp. 154-157 / printed pp. 141-144. It fully edits Iraq Museum no. 9737. The scan was not archived because robots permission could not be verified."),
    ]
    entries = []
    for group, old_title, old_authors, old_container, old_citation, title, citation, note in specs:
        source = SOURCES[group]
        before = {
            "source_type": "article", "title": old_title, "authors": old_authors,
            "issued_year": 1937 if group == "HO" else 1934, "container_title": old_container,
            "publisher": None, "url": None, "doi": None, "isbn": None, "citation": old_citation,
            "access_status": "unknown", "rights_status": "unknown", "notes": original_note,
        }
        if group == "AF":
            before["authors"] = "Gordon, Cyrus H"
        after = {
            "source_type": "article", "title": title, "authors": "Cyrus H. Gordon",
            "issued_year": before["issued_year"],
            "container_title": "Archiv orientální" if group != "IM9737" else "Annual of the American Schools of Oriental Research",
            "publisher": None, "url": source["url"], "doi": None, "isbn": None, "citation": citation,
            "access_status": "available", "rights_status": "copyrighted", "notes": note,
        }
        entries.append({
            "id": f"IBI-SOURCE-CORR-GORDON-{group}-OPEN-COMPLETE",
            "source_id": source["id"], "replacement_source_id": None,
            "rationale": "The complete inspected article and institutional bibliographic checks verify the corrected author, journal title, pagination, access route, rights treatment, and object scope.",
            "before": before, "after": after,
        })
    return {"schema_version": 1, "reviewed_by": "Codex", "reviewed_at": REVIEWED_AT, "evidence_path": str(evidence_path), "evidence_sha256": evidence_sha, "entries": entries}


def scopes():
    return {
        "schema_version": 1, "reviewed_by": "Codex", "reviewed_at": REVIEWED_AT,
        "batch": "Classify four complete Gordon article editions inspected remotely",
        "policy": "Scope follows the complete primary articles. Separately described but unedited bowls receive appearances without publication membership.",
        "entries": [
            {"review_id": "IBI-SCOPE-GORDON-AF-COMPLETE", "source_id": SOURCES["AF"]["id"], "scope": "corpus_edition", "basis": "Complete transcriptions, English translations, commentary, and plates for six bowls, texts A-F."},
            {"review_id": "IBI-SCOPE-GORDON-G-COMPLETE", "source_id": SOURCES["G"]["id"], "scope": "single_object_edition", "basis": "Complete transcription, English translation, commentary, and plates for text G, Istanbul no. 5497."},
            {"review_id": "IBI-SCOPE-GORDON-HO-COMPLETE", "source_id": SOURCES["HO"]["id"], "scope": "corpus_edition", "basis": "Complete transcriptions, English translations, commentary, and plates for eight bowls, texts H-O."},
            {"review_id": "IBI-SCOPE-GORDON-IM9737-COMPLETE", "source_id": SOURCES["IM9737"]["id"], "scope": "single_object_edition", "basis": "Complete transcription, English translation, commentary, and hand copy for Iraq Museum no. 9737."},
        ],
    }


def registry():
    return {
        "schema_version": 1, "reviewed_by": "Codex", "reviewed_at": REVIEWED_AT,
        "entries": [
            {"registry_id": "IBI-PUBREG-GORDON-AF-COMPLETE", "publication_key": SOURCES["AF"]["key"], "source_id": SOURCES["AF"]["id"], "resolution": "resolved", "basis": "Resolved against the complete article: texts A-F at printed pp. 321-334 and plates X-XV."},
            {"registry_id": "IBI-PUBREG-GORDON-G-COMPLETE", "publication_key": SOURCES["G"]["key"], "source_id": SOURCES["G"]["id"], "resolution": "resolved", "basis": "Resolved against the complete article: text G at printed pp. 466-474 and plates XXII-XXV."},
            {"registry_id": "IBI-PUBREG-GORDON-HO-COMPLETE", "publication_key": SOURCES["HO"]["key"], "source_id": SOURCES["HO"]["id"], "resolution": "resolved", "basis": "Resolved against the complete article: texts H-O at printed pp. 86-106 and plates II-XIVa."},
            {"registry_id": "IBI-PUBREG-GORDON-IM9737-COMPLETE", "publication_key": SOURCES["IM9737"]["key"], "source_id": SOURCES["IM9737"]["id"], "resolution": "resolved", "basis": "Resolved against the complete AASOR article: Iraq Museum no. 9737 at printed pp. 141-144."},
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root
    evidence_path = root / "research/reviews/gordon_1934_1937_open_scan_evidence_2026-09-12.json"
    write_json(evidence_path, evidence_manifest())
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    write_json(root / "research/reviews/gordon_1934_1937_source_corrections_2026-09-12.json", source_corrections(evidence_path.relative_to(root), evidence_sha))
    write_json(root / "research/reviews/gordon_1934_1937_source_scopes_2026-09-12.json", scopes())
    write_json(root / "research/reviews/gordon_1934_1937_publication_registry_2026-09-12.json", registry())
    rows = candidate_rows()
    write_jsonl(root / "research/enrichment/gordon_1934_1937_editions_2026-09-12.jsonl", rows)
    print(json.dumps({"appearances": len(rows), "complete_editions": 16, "exact_existing_attachments": 15, "new_candidates": 9, "evidence_sha256": evidence_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
