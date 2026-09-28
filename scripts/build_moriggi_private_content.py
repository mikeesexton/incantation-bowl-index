"""Stage Moriggi 2014's two-column bowl readings for Mike's private vault.

Requires pdfplumber from the bundled workspace Python. The output manifest is
protected source expression and must remain under data/private/manifests/.
This script only stages rows; ingestion and rendered-page review are separate.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import pdfplumber

from bowl_index.db import connect


SOURCE = "SRC-3C4294DDB367"
CAPTURE = "CAP-EA64131E5F1D"
SHA256 = "ce32170d182d4282a9610d42c2c6449b0435eba77851b18aa919544ddb4e5035"
TABLE_PAGES = [
    41, 46, 50, 55, 62, 66, 71, 75, 79, 83, 86, 89, 93, 98, 103,
    106, 111, 115, 120, 122, 125, 128, 133, 139, 143, 146, 152,
    157, 162, 165, 169, 173, 179, 181, 183, 187, 190, 192, 196,
    200, 204, 207, 209, 211, 212, 215, 218, 224, 227,
]
IMAGE_PAGES = {
    1: [44], 2: [49], 3: [53], 4: [60], 5: [64], 6: [69],
    7: [73], 8: [77], 9: [81], 10: [85], 11: [88], 12: [91],
    13: [96], 14: [101], 15: [105], 16: [109], 17: [113],
    18: [117, 118], 19: [121], 20: [124], 21: [126],
    22: [130, 131, 132], 23: [136, 137], 24: [141],
    25: [145], 26: [149, 150, 151], 27: [155], 28: [160, 161],
    29: [163], 30: [167], 31: [171], 32: [177, 178],
    34: [182], 35: [186], 36: [189], 37: [191], 38: [195],
    39: [198, 199], 40: [202], 41: [206], 42: [208],
    45: [214], 46: [217], 47: [220, 221, 222],
    48: [225], 49: [229, 230],
}


def line_groups(page):
    groups = []
    for word in page.extract_words(x_tolerance=1.5, y_tolerance=2):
        if not groups or abs(groups[-1][0] - word["top"]) > 3:
            groups.append((word["top"], [word]))
        else:
            groups[-1][1].append(word)
    return [(top, " ".join(w["text"] for w in words)) for top, words in groups]


def table_top(page, number):
    pattern = re.compile(rf"Bowl\s*no\.\s*{number}\s*\(" if number != 21
                         else r"Bowl\s*no\.\s*21")
    for top, line in line_groups(page):
        if pattern.search(line) and top > 45:
            return top + 19
    raise ValueError(f"PDF page {page.page_number}: bowl {number} table heading absent")


def notes_top(page, after):
    for top, line in line_groups(page):
        if top > after and re.search(r"Notes\s+to\s+the\s+text", line, re.I):
            return top - 3
    return None


def reading_columns(pdf, number, start):
    left, right, pages = [], [], []
    for page_number in range(start, min(start + 3, len(pdf.pages) + 1)):
        page = pdf.pages[page_number - 1]
        top = table_top(page, number) if page_number == start else 80
        end = notes_top(page, top)
        if end is None:
            end = min(page.height - 48, 740)
        if end <= top:
            raise ValueError(f"PDF page {page_number}: invalid table bounds")
        # Footnotes use a smaller font and are excluded even when they precede
        # the next printed notes heading on a page.
        page = page.filter(lambda item: item.get("object_type") != "char" or item.get("size", 10) >= 9.5)
        divider = 304 if page_number % 2 else 332
        ltext = page.crop((70, top, divider - 7, end)).extract_text(x_tolerance=1.5, y_tolerance=2) or ""
        rtext = page.crop((divider - 5, top, page.width - 55, end)).extract_text(x_tolerance=1.5, y_tolerance=2) or ""
        left.append(ltext.strip())
        right.append(rtext.strip())
        pages.append(page_number)
        if notes_top(page, top) is not None:
            break
        if number in {19, 34, 44}:
            # These fragmentary entries end at their footnote with no notes section.
            break
        if number == 43 and page_number == 210:
            # Three separately labelled fragments occupy two table pages.
            break
    else:
        raise ValueError(f"bowl {number}: notes boundary not found within three pages")
    return "\n".join(x for x in left if x), "\n".join(x for x in right if x), pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Moriggi PDF hash differs from registered capture")
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        match = re.match(r"Bowl no\. (\d+) \(", row[0])
        if match:
            appearances[int(match[1])] = row[0]
    if set(appearances) != set(range(1, 50)):
        raise ValueError(f"expected 49 source appearances; found {len(appearances)}")
    rows = []
    with pdfplumber.open(args.pdf) as pdf:
        for number, start in enumerate(TABLE_PAGES, 1):
            transliteration, translation, pages = reading_columns(pdf, number, start)
            if len(transliteration) < 10 or len(translation) < 10:
                raise ValueError(f"bowl {number}: empty reading column")
            locator = f"Bowl no. {number}, printed pp. {pages[0]-18}" + (
                f"–{pages[-1]-18}" if len(pages) > 1 else ""
            )
            note = (f"Moriggi 2014, {locator}; source capture {CAPTURE}, SHA-256 {SHA256}. "
                    "Born-digital two-column working extraction; editorial punctuation, damaged readings, "
                    "and line breaks require page proofing. Private research access only.")
            row = {
                "source_id": SOURCE,
                "appearance": {"locator": appearances[number]},
                "texts": [
                    {"text_type": "transliteration", "language": "Syriac", "script": "Latin",
                     "content": transliteration, "editor": "Marco Moriggi", "locator": locator,
                     "rights_status": "copyrighted", "public_ok": False, "notes": note},
                    {"text_type": "translation", "language": "English",
                     "content": translation, "editor": "Marco Moriggi", "locator": locator,
                     "rights_status": "copyrighted", "public_ok": False, "notes": note},
                ],
                "media": [
                    {"media_type": "image", "url": f"private-capture:{CAPTURE}#page={page}",
                     "rights_status": "copyrighted",
                     "notes": (f"Moriggi 2014, bowl no. {number}, printed image page {page-18}; "
                               f"PDF page {page}. Source capture {CAPTURE}; SHA-256 {SHA256}. "
                               "Private full-page derivative; no public reuse approval.")}
                    for page in IMAGE_PAGES.get(number, [])
                ],
            }
            rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"bowls": len(rows), "texts": sum(len(x["texts"]) for x in rows),
                      "image_pages": sum(len(x["media"]) for x in rows),
                      "unpictured_bowls": sorted(set(range(1, 50)) - set(IMAGE_PAGES))}))


if __name__ == "__main__":
    main()
