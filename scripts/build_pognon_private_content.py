"""Extract the held Pognon volume as private per-bowl OCR and page facsimiles.

The historical scan's Mandaic text layer is corrupted. We keep the full
working OCR of each numbered French edition section and page facsimiles for
verification, rather than mislabeling that OCR as a reliable transcription.
"""

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-E7D5F020B31C"
CAPTURE = "CAP-EED4A3FE59EC"
SHA256 = "667521b689e12947f7911d9542b7fc0e57bee1179f0c057ec7d59de7ee5ed44a"
# First PDF page of each numbered section, checked against the page images.
START_PAGES = [28, 32, 33, 36, 37, 39, 41, 42, 43, 44, 45, 46, 47, 52, 54,
               61, 64, 66, 69, 70, 71, 72, 76, 80, 83, 87, 88, 92, 95, 98, 99]


def source_text(page):
    raw = page.extract_text().replace("\x00", "")
    return re.sub(r"[\ud800-\udfff]", "\ufffd", raw)


def heading(number, text):
    matches = list(re.finditer(r"(?i)N\s*[°oº]\s*" + str(number) + r"(?!\d)", text))
    if not matches:
        raise ValueError(f"numbered heading {number} missing on expected page")
    # Cross-references can precede the actual heading on the same page.
    return matches[-1].start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Pognon capture hash mismatch")
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    reader = PdfReader(args.pdf)
    pages = {p: source_text(reader.pages[p - 1]) for p in range(28, 104)}
    starts = {n: (p, heading(n, pages[p])) for n, p in enumerate(START_PAGES, 1)}

    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.match(r"Khouabir bowl no\. (\d+);", row[0])
        if m:
            appearances[int(m[1])] = row[0]
    if set(appearances) != set(range(1, 32)):
        raise ValueError("expected all 31 numbered appearances, including corrected no. 31")

    rows = []
    for n in range(1, 32):
        start_page, start_offset = starts[n]
        end_page, end_offset = starts.get(n + 1, (104, 0))
        if n == 31:
            end_page, end_offset = 104, 0
        parts = []
        for p in range(start_page, end_page + 1):
            if p == 104:
                break
            text = pages[p]
            if p == start_page and p == end_page:
                text = text[start_offset:end_offset]
            elif p == start_page:
                text = text[start_offset:]
            elif p == end_page:
                text = text[:end_offset]
            parts.append(text.strip())
        section = "\n".join(x for x in parts if x).strip()
        if len(section) < 150:
            raise ValueError(f"numbered section {n} too short")
        last_page = end_page if end_offset else end_page - 1
        locator = f"No. {n}, printed pp. {start_page-11}–{last_page-11}"
        note = (f"Pognon 1898–99, {locator}; capture {CAPTURE}, SHA-256 {SHA256}. "
                "Working historical OCR of the entire numbered section, including French "
                "translation and philological commentary. Mandaic glyphs are corrupted in "
                "the scan's text layer; consult the attached facsimile pages for readings. "
                "Mike-only research access.")
        row = {"source_id": SOURCE,
               "appearance": {"locator": appearances[n]},
               "texts": [{"text_type": "summary", "language": "French and Mandaic",
                          "content": section, "editor": "Henri Pognon", "locator": locator,
                          "rights_status": "public_domain", "public_ok": False,
                          "notes": note}],
               "media": [], "claims": []}
        # Retain every source page of the numbered section. Some pages hold
        # two sections and are deliberately linked to both appearances.
        for p in range(start_page, last_page + 1):
            row["media"].append({"media_type": "scan",
                                 "url": f"private-capture:{CAPTURE}#page={p}",
                                 "rights_status": "public_domain",
                                 "notes": (f"Pognon 1898–99, {locator}, PDF page {p}; "
                                           "numbered text, translation or commentary facsimile. "
                                           "Private research derivative; digitization-use notice retained.")})
        if n <= 30:
            plate = 118 + 2 * (n - 1)
            plate_text = source_text(reader.pages[plate - 1])
            row["media"].append({"media_type": "drawing",
                                 "url": f"private-capture:{CAPTURE}#page={plate}",
                                 "rights_status": "public_domain",
                                 "notes": (f"Pognon 1898–99, plate no. {n}, PDF page {plate}; "
                                           "bowl drawing. Private research derivative; "
                                           "digitization-use notice retained.")})
            diameter = re.search(r"Diam[eè]tre\s*[:.]?\s*(\d{3})\s*(?:milli|inilli)",
                                 plate_text, re.I)
            if diameter:
                if not 100 <= int(diameter.group(1)) <= 250:
                    raise ValueError(f"implausible plate diameter for no. {n}")
                row["claims"].append({"field": "reported_diameter",
                                      "value_text": f"approximately {diameter.group(1)} mm",
                                      "certainty": "reported",
                                      "locator": f"Plate no. {n}, PDF page {plate}",
                                      "notes": "Diameter printed on Pognon's plate; OCR numeral checked for plausible range."})
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows),
                      "ocr_sections": sum(len(r["texts"]) for r in rows),
                      "scan_links": sum(sum(m["media_type"] == "scan" for m in r["media"]) for r in rows),
                      "plate_drawings": sum(sum(m["media_type"] == "drawing" for m in r["media"]) for r in rows),
                      "diameters": sum(len(r["claims"]) for r in rows)}))


if __name__ == "__main__":
    main()
