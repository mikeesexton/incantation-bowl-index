"""Build private working source-page OCR and translations from Gordon 1937."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-43C1E102538E"
CAPTURE = "CAP-A5A03BFD5DC7"
PDF_SHA = "c2c86d28ae3201f95475d89c45789d58a37a0e9ba125876503b833c78d7fb612"
ITEMS = {
    "H": ((4, 5, 6, 7), (23, 24, 25), (5, 6)),
    "I": ((8, 9), (26,), (9,)),
    "J": ((8, 9), (27,), (9,)),
    "K": ((10, 11), (28,), (10, 11)),
    "L": ((11, 12), (29, 30), (12,)),
    "M": ((13, 14, 15, 16, 17), (31, 32), (15, 16)),
    "N": ((18, 19, 20, 21), (33, 34, 35), (20,)),
    "O": ((21, 22, 37), (), (22, 37)),
}


def normalize(page):
    return re.sub(r"\s+", " ", page.extract_text() or "").strip()


def printed(pdf_page):
    return pdf_page + 82 if pdf_page <= 22 else pdf_page + 68


def page_text(pages, numbers):
    return "\n\n".join(f"[PDF p. {n}; printed p. {printed(n)}]\n{normalize(pages[n - 1])}"
                       for n in numbers)


def translation(pages, key, numbers):
    joined = " ".join(normalize(pages[n - 1]) for n in numbers)
    if key == "I":
        start = re.search(r"Translation I\.", joined)
        end = re.search(r"Translation J\.", joined)
    elif key == "J":
        start = re.search(r"Translation J\.", joined)
        end = re.search(r"\bNotes\b", joined[start.end():]) if start else None
        if start and end:
            return joined[start.end():start.end() + end.start()].strip()
    else:
        start = re.search(r"(?:Translation|Traslation)\s*(?:\([^)]*\))?\s*[.,]", joined)
        end = re.search(r"\bNotes\b", joined[start.end():]) if start else None
        if start and end:
            return joined[start.end():start.end() + end.start()].strip()
    if not start or not end:
        raise ValueError(f"translation bounds missing for {key}")
    value = joined[start.end():end.start()].strip()
    if len(value) < 100:
        raise ValueError(f"translation too short for {key}")
    return value


def media(page, label):
    note = f"printed p. {printed(page)}" if page <= 22 or page == 37 else f"plate PDF p. {page}"
    return {"media_type": "scan", "url": f"private-capture:{CAPTURE}#page={page}",
            "rights_status": "unknown",
            "notes": f"Gordon 1937 {label}, {note}. Private Kramerius source facsimile; public reuse unreviewed."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != PDF_SHA:
        raise ValueError("held Gordon 1937 PDF hash mismatch")
    pages = PdfReader(args.pdf).pages
    if len(pages) != 38:
        raise ValueError("unexpected Gordon 1937 page count")
    appearances = {r["locator"] for r in connect().execute(
        "SELECT locator FROM appearances WHERE source_id=?", (SOURCE,))}
    footnote = next((x for x in appearances if x.startswith("introductory footnote 4,")), None)
    if footnote is None:
        raise ValueError("introductory appearance missing")
    rows = [{"source_id": SOURCE, "appearance": {"locator": footnote},
             "texts": [{"text_type": "summary", "language": "English",
                        "content": page_text(pages, (3,)), "editor": "Cyrus H. Gordon",
                        "locator": "Gordon 1937, printed p. 85 / PDF p. 3, footnote 4 and surrounding source page",
                        "rights_status": "unknown", "public_ok": False,
                        "notes": f"Working full-page OCR includes neighboring introductory material; not an edition of National Museum no. 207962. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."}],
             "media": [media(3, "introductory footnote 4")], "claims": []}]
    for key, (section_pages, plates, translation_pages) in ITEMS.items():
        loc = next((x for x in appearances if x.startswith(f"text {key},")), None)
        if loc is None:
            raise ValueError(f"appearance {key} missing")
        span = page_text(pages, section_pages)
        if len(span) < 1200:
            raise ValueError(f"section {key} too short")
        trans = translation(pages, key, translation_pages)
        rows.append({"source_id": SOURCE, "appearance": {"locator": loc},
                     "texts": [
                         {"text_type": "summary", "language": "English with damaged Aramaic/Mandaic OCR",
                          "content": span, "editor": "Cyrus H. Gordon",
                          "locator": f"Gordon 1937 text {key}, source pages PDF {', '.join(map(str, section_pages))}",
                          "rights_status": "unknown", "public_ok": False,
                          "notes": f"Working full source-page OCR includes neighboring material where pages are shared. Original-script glyphs are damaged and are not a transcription. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."},
                         {"text_type": "translation", "language": "English",
                          "content": trans, "editor": "Cyrus H. Gordon",
                          "locator": f"Gordon 1937 text {key}, published translation, PDF pp. {', '.join(map(str, translation_pages))}",
                          "rights_status": "unknown", "public_ok": False,
                          "notes": f"Working OCR of Gordon's published English translation. Page proofing required; original-script OCR is not adopted. Held PDF {CAPTURE}, SHA-256 {PDF_SHA}."}],
                     "media": [media(n, f"text {key}") for n in (*section_pages, *plates)],
                     "claims": []})
    if len(rows) != 9:
        raise ValueError("expected nine appearances")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows),
                      "texts": sum(len(r["texts"]) for r in rows),
                      "page_links": sum(len(r["media"]) for r in rows)}))


if __name__ == "__main__":
    main()
