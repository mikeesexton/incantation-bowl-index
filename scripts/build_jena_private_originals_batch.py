"""Separate recoverable Jena Hebrew/Syriac edition columns for Mike Access.

These are private, page-located working text-layer readings. Mandaic font
encoding is not reliably recoverable and is deliberately excluded.
"""

import argparse
import hashlib
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect
from build_jena_private_readings_batch import TRANSLATIONS, SOURCE, CAPTURE, SHA256


REGIONS = {n: [(p, hi, lo) for p, hi, lo, _ in zones]
           for n, zones in TRANSLATIONS.items() if n <= 36}
REGIONS.update({
    4: [(53, 560, 495)],
    16: [(110, 370, 225), (111, 760, 590)],
    27: [(164, 590, 415)],
})
SKIP = {21, 37, 38, 39, 40}
EXPECTED = set(range(1, 41)) - {1, 2, 5, 7, 10, 11, 12, 14, 15, 20, 24, 25, 26, 28} - SKIP
assert set(REGIONS) == EXPECTED


def page_script(page, top, bottom, script):
    fragments = []
    def collect(text, cm, tm, font, size):
        x, y = tm[4], tm[5]
        if not (65 <= x <= 315 and bottom <= y <= top and text.strip()):
            return
        if not any(script(ch) for ch in text):
            return
        # A fragment with Latin prose plus a single quoted lemma belongs to
        # commentary, not the edition column.
        if sum(script(ch) for ch in text) < max(2, sum(ch.isalpha() for ch in text) * 0.55):
            return
        fragments.append((round(y), x, text.strip()))
    page.extract_text(visitor_text=collect)
    by_line = defaultdict(list)
    for y, x, fragment in fragments:
        by_line[y].append((x, fragment))
    lines = []
    for y in sorted(by_line, reverse=True):
        # The PDF gives each RTL fragment in reading order internally; joining
        # page fragments from right to left keeps the printed edition order.
        line = " ".join(t for x, t in sorted(by_line[y], reverse=True))
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Jena capture hash mismatch")
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    pdf = PdfReader(args.pdf)
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.match(r"Entry (\d+) \((HS [^)]+)\)", row[0])
        if m:
            appearances[int(m.group(1))] = (row[0], m.group(2))
    if set(appearances) != set(range(1, 69)):
        raise ValueError("expected 68 Jena appearances")
    existing = set()
    for row in conn.execute("SELECT t.locator FROM texts t JOIN appearances a ON a.id=t.appearance_id "
                            "WHERE a.source_id=? AND t.text_type='transcription'", (SOURCE,)):
        m = re.search(r"Entry (\d+)", row[0])
        if m:
            existing.add(int(m.group(1)))
    if existing & EXPECTED:
        raise ValueError(f"already transcribed: {sorted(existing & EXPECTED)}")
    rows = []
    lengths = {}
    for number in sorted(EXPECTED):
        script = (lambda c: '\u0590' <= c <= '\u05ff') if number <= 30 else (lambda c: '\u0700' <= c <= '\u074f')
        parts = []
        for pdf_page, top, bottom in REGIONS[number]:
            content = page_script(pdf.pages[pdf_page - 1], top, bottom, script)
            if not content:
                raise ValueError(f"empty script column: entry {number}, page {pdf_page}")
            parts.append(f"[PDF page {pdf_page}; printed p. {pdf_page-24}]\n{content}")
        content = "\n\n".join(parts)
        if sum(script(c) for c in content) < 10:
            raise ValueError(f"short script column: entry {number}")
        lengths[number] = len(content)
        first, last = REGIONS[number][0][0], REGIONS[number][-1][0]
        locator = (f"Entry {number} ({appearances[number][1]}), original-script edition column, "
                   f"printed pp. {first-24}–{last-24}; PDF pp. {first}–{last}")
        rows.append({"source_id": SOURCE,
                     "appearance": {"locator": appearances[number][0]},
                     "texts": [{"text_type": "transcription", "language": "Jewish Babylonian Aramaic" if number <= 30 else "Syriac",
                                "content": content, "editor": "James Nathan Ford and Matthew Morgenstern",
                                "locator": locator, "rights_status": "copyrighted", "public_ok": False,
                                "notes": (f"Ford and Morgenstern 2020; capture {CAPTURE}, SHA-256 {SHA256}. "
                                          "Original-script working PDF text-layer extract, privately indexed for Mike. "
                                          "Fragment order, line numbers, damaged glyphs, brackets and typography "
                                          "require proofing against the retained source page; source page controls.") }],
                     "media": [], "claims": []})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"transcriptions": len(rows), "characters": sum(lengths.values()),
                      "shortest": min(lengths.items(), key=lambda x:x[1]),
                      "longest": max(lengths.items(), key=lambda x:x[1])}))


if __name__ == "__main__":
    main()
