"""Build private, source-page-bound working extracts from Gordon's 1934 scan.

The Kramerius scan has OCR text, but its Aramaic glyphs are damaged.  The
English translation spans are indexed separately; all rows require page review.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-60CB324330C9"
CAPTURE = "CAP-138518C319C8"
PDF_SHA = "5abd9af65823f4fe8b19eb76ecc7f9668f1e3de35b2535c5166461eca23bd1ce"
EDITIONS = {
    "A": ((4, 5, 6), 18, (5, 6)),
    "B": ((7, 8), 19, (7, 8)),
    "C": ((9, 10), 20, (9, 10)),
    "D": ((11, 12, 13), 21, (11, 12)),
    "E": ((14, 15, 16, 17), 22, (16, 16)),
    "F": ((14, 15, 16, 17), 23, (16, 16)),
}


def normalized(page):
    return re.sub(r"\s+", " ", page.extract_text() or "").strip()


def page_text(pages, numbers):
    return "\n\n".join(f"[PDF p. {n}; printed p. {n + 317}]\n{normalized(pages[n - 1])}"
                       for n in numbers)


def translation(pages, first, last):
    joined = " ".join(normalized(pages[n - 1]) for n in range(first, last + 1))
    start = re.search(r"Translation[.,]", joined)
    if not start:
        raise ValueError(f"translation heading missing on PDF pp. {first}-{last}")
    end = re.search(r"\bNotes\.", joined[start.end():])
    if not end:
        raise ValueError(f"notes boundary missing on PDF pp. {first}-{last}")
    value = joined[start.end():start.end() + end.start()].strip()
    if len(value) < 250:
        raise ValueError(f"implausibly short translation on PDF pp. {first}-{last}")
    return value


def media(page, label):
    return {"media_type": "scan", "url": f"private-capture:{CAPTURE}#page={page}",
            "rights_status": "unknown",
            "notes": f"Gordon 1934 {label}; printed p. {page + 317 if page <= 17 else 'plate'} / PDF p. {page}. Private Kramerius source facsimile; public reuse unreviewed."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != PDF_SHA:
        raise ValueError("held Gordon 1934 PDF hash mismatch")
    pages = PdfReader(args.pdf).pages
    if len(pages) != 23:
        raise ValueError("unexpected Gordon 1934 page count")
    conn = connect()
    appearances = {row["locator"] for row in conn.execute(
        "SELECT locator FROM appearances WHERE source_id=?", (SOURCE,))}
    rows = []
    for number in (5233, 5361, 5377, 1682, 1691, 5367, 5370):
        loc = next((x for x in appearances if x.startswith(f"Istanbul survey no. {number},")), None)
        if loc is None:
            raise ValueError(f"survey appearance {number} missing")
        page = 3 if "p. 320" in loc else 4
        rows.append({"source_id": SOURCE, "appearance": {"locator": loc},
                     "texts": [{"text_type": "summary", "language": "English with damaged Aramaic OCR",
                                "content": page_text(pages, (page,)), "editor": "Cyrus H. Gordon",
                                "locator": f"Gordon 1934 survey, printed p. {page + 317} (PDF p. {page}); shared source page",
                                "rights_status": "unknown", "public_ok": False,
                                "notes": f"Working full-page OCR includes neighboring survey entries. This is a source-page aid, not a checked individual inscription; Aramaic glyphs are damaged. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."}],
                     "media": [media(page, f"survey no. {number}")], "claims": []})
    for letter, (section_pages, plate, translation_pages) in EDITIONS.items():
        loc = next((x for x in appearances if x.startswith(f"text {letter},")), None)
        if loc is None:
            raise ValueError(f"edition appearance {letter} missing")
        span = page_text(pages, section_pages)
        if len(span) < 1500:
            raise ValueError(f"edition {letter} page extract too short")
        translated = translation(pages, *translation_pages)
        shared = letter in ("E", "F")
        rows.append({"source_id": SOURCE, "appearance": {"locator": loc},
                     "texts": [
                         {"text_type": "summary", "language": "English with damaged Aramaic OCR",
                          "content": span, "editor": "Cyrus H. Gordon",
                          "locator": f"Gordon 1934 text {letter}, printed pp. {section_pages[0] + 317}–{section_pages[-1] + 317} (PDF pp. {section_pages[0]}–{section_pages[-1]})",
                          "rights_status": "unknown", "public_ok": False,
                          "notes": f"Working full source-page OCR, including edition, translation, notes and neighboring material where pages are shared. Aramaic glyphs are damaged and are not an inscription transcription. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."},
                         {"text_type": "translation", "language": "English",
                          "content": translated, "editor": "Cyrus H. Gordon",
                          "locator": f"Gordon 1934 text {letter}, published translation, printed pp. {translation_pages[0] + 317}–{translation_pages[-1] + 317}",
                          "rights_status": "unknown", "public_ok": False,
                          "notes": ("Working OCR of Gordon's shared E/F parallel translation; attached to both source appearances, not separated into individual readings. " if shared else "Working OCR of Gordon's published translation. ") + f"Page proofing required. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."}],
                     "media": [media(n, f"text {letter}") for n in (*section_pages, plate)],
                     "claims": []})
    if len(rows) != 13:
        raise ValueError("expected 13 source appearances")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows),
                      "texts": sum(len(row["texts"]) for row in rows),
                      "page_links": sum(len(row["media"]) for row in rows)}))


if __name__ == "__main__":
    main()
