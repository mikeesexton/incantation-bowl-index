"""Retain every item of Brand's held 2021 Syriac Manichaean working list.

This is a bibliographic concordance, not an edition or image source. Three
additional contextual appearances are tied to their exact printed references.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-6D313A7AA389"
CAPTURE = "CAP-E1E6C8B56AD6"
SHA256 = "bdbe5384e38fcbe39b6b621e4cc3df0f4c70ac94f49a3348e46af29431999f06"
ITEM = re.compile(r"(?m)^(\d{1,2})\.\s")


def clean(value):
    return re.sub(r"\s+", " ", value).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Brand capture hash mismatch")
    reader = PdfReader(args.pdf)
    if len(reader.pages) != 3:
        raise ValueError("expected three-page working list")
    pages = {p: reader.pages[p - 1].extract_text() for p in (1, 2)}
    conn = connect()
    appearances = {r[0] for r in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,))}
    if len(appearances) != 44:
        raise ValueError("expected 41 numbered and 3 contextual appearances")
    rows = []
    items = {}
    for page, content in pages.items():
        numbered = content if page == 1 else content.split("\n• CBS 16014", 1)[0]
        matches = list(ITEM.finditer(numbered))
        for index, match in enumerate(matches):
            number = int(match.group(1))
            following = matches[index + 1].start() if index + 1 < len(matches) else len(numbered)
            text = clean(numbered[match.start():following].rstrip("; \n"))
            if not text.startswith(f"{number}. ") or len(text) < 25:
                raise ValueError(f"bad item {number}")
            items[number] = (page, text)
    if set(items) != set(range(1, 42)):
        raise ValueError(f"numbered items missing: {sorted(set(range(1,42))-set(items))}")

    def add(locator, page, content, note):
        if locator not in appearances:
            raise ValueError(f"appearance missing: {locator}")
        rows.append({"source_id": SOURCE, "appearance": {"locator": locator},
                     "texts": [{"text_type": "summary", "language": "English",
                                "content": content, "editor": "Mattias Brand, with Alexandra Probst",
                                "locator": locator + f"; PDF p. {page}",
                                "rights_status": "copyrighted", "public_ok": False,
                                "notes": (f"Brand 2021, working list version 1; capture {CAPTURE}, "
                                          f"SHA-256 {SHA256}. Exact list item or contextual reference. "
                                          f"{note} Mike-only research access.")}],
                     "media": [], "claims": []})

    for number, (page, content) in sorted(items.items()):
        add(f"p. {page}, item {number}", page, content,
            "Bibliographic concordance only; this source prints no incantation edition or bowl image.")
    bullet = re.search(r"(?m)^• CBS 16014\.[^\n]*(?:\n[^\n]*)?", pages[2])
    if not bullet:
        raise ValueError("CBS 16014 contextual bullet missing")
    add("p. 2, designation CBS 16014", 2, clean(bullet.group(0)),
        "Contextual comparison outside the numbered Syriac-script list; do not infer script or identity from adjacency.")
    for designation in ("MS 2055/16", "MS 2055/25"):
        add(f"p. 2, designation {designation}", 2, items[37][1],
            "Contextual parallel named within item 37; this is not a separate numbered list item.")
    if len(rows) != 44:
        raise ValueError("expected 44 appearance-linked rows")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"numbered_items": 41, "contextual_references": 3,
                      "text_rows": len(rows),
                      "characters": sum(len(r["texts"][0]["content"]) for r in rows)}))


if __name__ == "__main__":
    main()
