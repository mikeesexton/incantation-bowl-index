"""Recover Jena source-page addenda and private working English translations.

The PDF's reading columns use distinct page coordinates. Each extraction region
below was checked against its rendered page. Output is a working text-layer
reading with exact page anchors; damaged letters and font-order details still
require source-page proofing before quotation.
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


SOURCE = "SRC-8A145FAA2EBB"
CAPTURE = "CAP-2861B06070B4"
SHA256 = "23431f46510c5cf729ca35282413e0bedd21be44dbc80e56dcde7c709b9a99d4"

# Entry: (PDF page, upper y, lower y, left x of English column). These cover
# the numbered English translation only, excluding adjacent commentary/notes.
TRANSLATIONS = {
    3: [(43, 480, 160, 300), (44, 760, 520, 300)],
    6: [(57, 520, 245, 300), (58, 760, 650, 300)],
    8: [(67, 600, 230, 300), (68, 760, 660, 300)],
    9: [(70, 520, 395, 300), (71, 760, 670, 300)],
    13: [(92, 560, 205, 300), (93, 760, 630, 300)],
    17: [(116, 585, 220, 300), (117, 760, 690, 300)],
    18: [(119, 560, 320, 300)],
    19: [(123, 615, 210, 300)],
    22: [(137, 465, 220, 300), (138, 760, 500, 300)],
    23: [(144, 550, 290, 270), (145, 760, 600, 270)],
    29: [(173, 650, 350, 200)],
    30: [(176, 630, 575, 200)],
    31: [(181, 450, 285, 300), (182, 760, 420, 300)],
    32: [(188, 600, 230, 300), (189, 760, 590, 300)],
    33: [(197, 205, 120, 250), (198, 760, 440, 250)],
    34: [(201, 520, 310, 280), (202, 760, 525, 270)],
    35: [(208, 480, 285, 280)],
    36: [(211, 560, 420, 270)],
    37: [(215, 560, 200, 280), (216, 760, 65, 280),
         (217, 760, 440, 260)],
    38: [(220, 545, 150, 300), (221, 760, 630, 300)],
    39: [(224, 505, 190, 300), (225, 760, 495, 300)],
    40: [(228, 600, 165, 300)],
}

# On these first pages pypdf emits part of the current entry before its heading
# because of the two-column content-stream order. The previous pass began at
# the heading and therefore omitted these page portions.
ADDENDA_PAGES = {1: 35, 4: 53, 24: 153, 28: 166, 31: 181,
                 33: 197, 35: 208, 39: 224, 40: 227}
HEADING = re.compile(r"(?m)^(\d{1,2})\. (HS [^\n]+)$")


def english_region(page, top, bottom, left, exceptional_line=None):
    fragments = []

    def collect(text, cm, tm, font, size):
        x, y = tm[4], tm[5]
        off_column_number = (exceptional_line is not None and 150 <= x < left
                             and re.search(rf"\b{exceptional_line}\b", text)
                             and len(re.findall(r"[A-Za-z]", text)) >= 6)
        if text.strip() and (left <= x <= 570 or off_column_number) and bottom <= y <= top:
            fragments.append((round(y), x, text.strip()))

    page.extract_text(visitor_text=collect)
    by_line = defaultdict(list)
    for y, x, fragment in fragments:
        # Original-script glyphs occasionally overlap the column edge. The
        # English translation may retain Latin-script magic words verbatim.
        fragment = re.sub(r"[\u0590-\u08ff]+", "", fragment).strip()
        if fragment:
            by_line[y].append((x, fragment))
    lines = []
    for y in sorted(by_line, reverse=True):
        words = [s for _, s in sorted(by_line[y], key=lambda item: item[0])]
        line = " ".join(words)
        line = re.sub(r"\s+([.,;:!?])", r"\1", line)
        if line.strip():
            lines.append(line.strip())
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
        raise ValueError("expected 68 indexed Jena appearances")
    existing = set()
    for row in conn.execute("SELECT t.locator FROM texts t JOIN appearances a ON a.id=t.appearance_id "
                            "WHERE a.source_id=? AND t.text_type='translation'", (SOURCE,)):
        m = re.search(r"Entry (\d+)", row[0])
        if m:
            existing.add(int(m.group(1)))
    if existing & TRANSLATIONS.keys():
        raise ValueError(f"already translated entries: {sorted(existing & TRANSLATIONS.keys())}")

    rows = {}
    for number in set(ADDENDA_PAGES) | set(TRANSLATIONS):
        rows[number] = {"source_id": SOURCE,
                        "appearance": {"locator": appearances[number][0]},
                        "texts": [], "media": [], "claims": []}

    for number, pdf_page in sorted(ADDENDA_PAGES.items()):
        raw = pdf.pages[pdf_page - 1].extract_text()
        heading = HEADING.search(raw)
        if not heading or int(heading.group(1)) != number:
            raise ValueError(f"entry {number} heading missing on PDF page {pdf_page}")
        prefix = re.sub(r"^©[^\n]+\n", "", raw[:heading.start()]).strip()
        if len(prefix) < 90:
            raise ValueError(f"entry {number} omitted page portion too short")
        locator = f"Entry {number} ({appearances[number][1]}), printed p. {pdf_page-24}; PDF p. {pdf_page}, pre-heading text-layer portion"
        rows[number]["texts"].append({
            "text_type": "summary", "language": "mixed", "content": prefix,
            "editor": "James Nathan Ford and Matthew Morgenstern",
            "locator": locator, "rights_status": "copyrighted",
            "public_ok": False,
            "notes": (f"Ford and Morgenstern 2020; capture {CAPTURE}, SHA-256 {SHA256}. "
                      "Supplement to the earlier full-section extraction: pypdf emitted "
                      "this part of the SAME entry before its heading because of PDF "
                      "content-stream order. Verified on rendered page. Working text "
                      "layer; source page controls. Mike-only research access."),
        })

    translation_chars = 0
    for number, regions in sorted(TRANSLATIONS.items()):
        parts = []
        for pdf_page, top, bottom, left in regions:
            text = english_region(pdf.pages[pdf_page - 1], top, bottom, left,
                                  exceptional_line=38 if (number, pdf_page) == (37, 217) else None)
            if len(text) < 50:
                raise ValueError(f"entry {number}, page {pdf_page}: short translation zone")
            parts.append(f"[PDF page {pdf_page}; printed p. {pdf_page-24}]\n{text}")
        content = "\n\n".join(parts)
        if not re.search(r"\b1[’′']?\b", content):
            raise ValueError(f"entry {number}: missing line 1 in translation")
        translation_chars += len(content)
        first, last = regions[0][0], regions[-1][0]
        locator = (f"Entry {number} ({appearances[number][1]}), translation column, "
                   f"printed pp. {first-24}–{last-24}; PDF pp. {first}–{last}")
        rows[number]["texts"].append({
            "text_type": "translation", "language": "English", "content": content,
            "editor": "James Nathan Ford and Matthew Morgenstern",
            "locator": locator, "rights_status": "copyrighted", "public_ok": False,
            "notes": (f"Ford and Morgenstern 2020; capture {CAPTURE}, SHA-256 {SHA256}. "
                      "Scholar's English column extracted from page-specific regions; "
                      + ("fragmentary scholarly rendering, lacunae retained. "
                         if number in {18, 23, 29, 30, 33, 34, 35, 36, 40} else "")
                      + "Working text layer with printed line numbers; italic word order, "
                      "damage marks, and typography require source-page proofing. "
                      "Mike-only research access."),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for number in sorted(rows):
            out.write(json.dumps(rows[number], ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "supplemental_sections": len(ADDENDA_PAGES),
                      "translations": len(TRANSLATIONS), "translation_characters": translation_chars}))


if __name__ == "__main__":
    main()
