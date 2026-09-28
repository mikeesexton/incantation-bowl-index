"""Link the held Stübe scan's numbered catalogue and VA 2416 edition pages.

The volume has no usable text layer. The page map is checked against the
numbered catalogue and the alternating transcription/translation headings.
Protected working transcription pages, when supplied, stay in the vault.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from bowl_index.db import connect


SOURCE = "SRC-0B6C0E1133EF"
CAPTURE = "CAP-4C9D532C9194"
SHA256 = "ef983942f7fdc4c57af6ceb3c3b62c3444e75fd292cd241a2882f8d9a6b34650"
CATALOGUE = {
    1: (13,), 2: (13,), 3: (13,), 4: (13, 14),
    5: (14,), 6: (14,), 7: (14,), 8: (14, 15),
    9: (15,), 10: (15,), 11: (16,), 12: (16,), 13: (16,),
    14: (16, 17), 15: (17,), 16: (17,), 17: (17,),
    18: (17, 18), 19: (17, 18),
}
EDITION = {22: "transcription", 23: "translation", 24: "transcription",
           25: "translation", 26: "transcription", 27: "translation"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--working-translation", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Stübe capture hash mismatch")
    translations = {}
    if args.working_translation:
        translations = json.loads(args.working_translation.read_text(encoding="utf-8"))
        if set(translations) != {"23", "25", "27"}:
            raise ValueError("expected all three VA 2416 translation pages")
        if any(len(value) < 400 for value in translations.values()):
            raise ValueError("a translation page is unexpectedly short")
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        match = re.match(r"descriptive catalogue no\. (\d+),", row[0])
        if match:
            appearances[int(match[1])] = row[0]
    if set(appearances) != set(CATALOGUE):
        raise ValueError("the nineteen Stübe appearances differ from the checked page map")
    rows = []
    for number, pages in CATALOGUE.items():
        row = {"source_id": SOURCE, "appearance": {"locator": appearances[number]},
               "texts": [], "media": [], "claims": []}
        for printed in pages:
            pdf_page = printed + 22
            row["media"].append({
                "media_type": "scan",
                "url": f"private-capture:{CAPTURE}#page={pdf_page}",
                "rights_status": "public_domain",
                "notes": (f"Stübe 1895 descriptive catalogue no. {number}, printed p. {printed}, "
                          f"PDF p. {pdf_page}; held BSB scan {CAPTURE}, SHA-256 {SHA256}. "
                          "Private research facsimile; BSB digitization's noncommercial-use "
                          "notice remains attached. Item 14 and 15 are inscribed skulls, not bowls.")})
        if number == 4:
            for printed, kind in EDITION.items():
                pdf_page = printed + 22
                row["media"].append({
                    "media_type": "scan",
                    "url": f"private-capture:{CAPTURE}#page={pdf_page}",
                    "rights_status": "public_domain",
                    "notes": (f"Stübe 1895 VA 2416 {kind}, printed p. {printed}, "
                              f"PDF p. {pdf_page}; held BSB scan {CAPTURE}. "
                              "Private edition facsimile; BSB digitization's noncommercial-use "
                              "notice remains attached. The Hebrew-script reading is not OCRed.")})
            for page, content in sorted(translations.items()):
                printed = int(page)
                row["texts"].append({
                    "text_type": "translation", "language": "German", "content": content,
                    "editor": "Rudolf Stübe", "locator": f"VA 2416, Übersetzung, printed p. {printed}; PDF p. {printed+22}",
                    "rights_status": "public_domain", "public_ok": False,
                    "notes": (f"Manual working transcription of Stübe's German translation from "
                              f"printed p. {printed}; capture {CAPTURE}, SHA-256 {SHA256}. "
                              "Uncertain Hebrew words and nineteenth-century spellings remain as printed "
                              "where decipherable; proofread against the linked facsimile before citation. "
                              "Mike-only research access; BSB digitization notice retained.")})
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "media": sum(len(r["media"]) for r in rows),
                      "translation_pages": sum(len(r["texts"]) for r in rows)}))


if __name__ == "__main__":
    main()
