"""Retain every indexed Jena catalogue section in a private ingest manifest.

The full section is a working PDF text-layer extract. It preserves translations,
original-script editions, descriptions and notes together, without claiming that
automatic column ordering or editorial marks have been page-proofread.
"""

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-8A145FAA2EBB"
CAPTURE = "CAP-2861B06070B4"
SHA256 = "23431f46510c5cf729ca35282413e0bedd21be44dbc80e56dcde7c709b9a99d4"
HEADING = re.compile(r"(?m)^(\d{1,2})\. (HS [^\n]+)$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Jena capture hash mismatch")

    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    pdf = PdfReader(args.pdf)
    pages = {page: pdf.pages[page - 1].extract_text() for page in range(35, 268)}
    starts = {}
    for page, content in pages.items():
        for m in HEADING.finditer(content):
            number = int(m.group(1))
            if number in starts:
                raise ValueError(f"duplicate heading for entry {number}")
            starts[number] = (page, m.start(), m.group(2))
    if set(starts) != set(range(1, 70)):
        raise ValueError(f"Jena numbered sequence incomplete: {sorted(starts)}")

    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.match(r"Entry (\d+) \((HS [^)]+)\)", row[0])
        if m:
            appearances[int(m.group(1))] = (row[0], m.group(2))
    if set(appearances) != set(range(1, 69)):
        raise ValueError("expected the 68 existing source appearances")

    rows = []
    lengths = {}
    for number in range(1, 69):
        page, offset, hs = starts[number]
        locator, expected_hs = appearances[number]
        if hs != expected_hs:
            raise ValueError(f"entry {number} designation mismatch: {hs} / {expected_hs}")
        next_page, _, _ = starts[number + 1]
        pieces = []
        for pdf_page in range(page, next_page):
            if number == 40 and pdf_page >= 233:
                break  # Part IV introduction follows the HS 3054 figures.
            content = pages[pdf_page]
            if pdf_page == page:
                content = content[offset:]
            if content.strip():
                pieces.append(f"[PDF page {pdf_page}; printed p. {pdf_page - 24}]\n{content.strip()}")
        section = "\n\n".join(pieces).strip()
        if not section.startswith(f"[PDF page {page}; printed p. {page - 24}]\n{number}. {hs}"):
            raise ValueError(f"entry {number} section start is wrong")
        if len(section) < 65:
            raise ValueError(f"entry {number} section implausibly short")
        lengths[number] = len(section)
        last_page = next_page - 1
        if number == 40:
            last_page = 232
        printed = (f"p. {page - 24}" if last_page == page
                   else f"pp. {page - 24}–{last_page - 24}")
        source_locator = f"Entry {number} ({hs}), printed {printed}; PDF pp. {page}–{last_page}"
        note = (f"Ford and Morgenstern 2020, {source_locator}; capture {CAPTURE}, "
                f"SHA-256 {SHA256}. Complete numbered-section working text-layer extraction. "
                "Includes source description and any printed original-script edition, "
                "translation, commentary, and notes. PDF column order, damaged glyphs, "
                "line breaks, and typography require page proofing. Mike-only research access.")
        rows.append({
            "source_id": SOURCE,
            "appearance": {"locator": locator},
            "texts": [{"text_type": "summary", "language": "mixed",
                       "content": section, "editor": "James Nathan Ford and Matthew Morgenstern",
                       "locator": source_locator, "rights_status": "copyrighted",
                       "public_ok": False, "notes": note}],
            "media": [], "claims": [],
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "text_rows": len(rows),
                      "total_characters": sum(lengths.values()),
                      "shortest_entry": min(lengths, key=lengths.get),
                      "longest_entry": max(lengths, key=lengths.get)}))


if __name__ == "__main__":
    main()
