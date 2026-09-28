"""Retain Auction 57's three bowl descriptions and illustrated lot page privately."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-FC77989995C8"
CAPTURE = "CAP-9CD9A67E0389"
SHA256 = "1fe6cd1c0af12a60f30c930d4258ee3e44bd76762d975754877656a5623aa14e"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Auction 57 capture hash mismatch")
    pdf = PdfReader(args.pdf)
    page = pdf.pages[92].extract_text()
    if not page.lstrip().startswith("92\n"):
        raise ValueError("expected printed p. 92 at PDF p. 93")
    photo_page = pdf.pages[93].extract_text()
    if not all(re.search(rf"(?m)^{n}$", photo_page) for n in (440, 441, 442)):
        raise ValueError("the three illustrated lot numbers are not on PDF p. 94")
    conn = connect()
    appearances = {int(m[1]): locator for (locator,) in conn.execute(
        "SELECT locator FROM appearances WHERE source_id=?", (SOURCE,))
        if (m := re.search(r"lot (\d+)", locator))}
    if set(appearances) != {440, 441, 442}:
        raise ValueError("auction appearance inventory changed")
    rows = []
    for lot in (440, 441, 442):
        match = re.search(rf"(?ms)^{lot}\s*\n(.*?)(?=^{lot+1}\s*\n)", page)
        if not match:
            raise ValueError(f"lot {lot} text not found")
        content = re.sub(r"\s+", " ", match[1]).strip()
        if not 150 <= len(content) <= 400:
            raise ValueError(f"lot {lot} extract implausible length: {len(content)}")
        row = {"source_id": SOURCE, "appearance": {"locator": appearances[lot]},
               "texts": [{"text_type": "summary", "language": "English", "content": content,
                          "editor": "Archaeological Center Ltd.",
                          "locator": f"Auction 57, lot {lot}, printed p. 92/PDF p. 93",
                          "rights_status": "copyrighted", "public_ok": False,
                          "notes": (f"Complete printed lot description from held PDF {CAPTURE}, "
                                    f"SHA-256 {SHA256}; scan-checked lot and page boundaries. "
                                    "Dealer assertions are attributed, not independently verified. "
                                    "Mike-only research access.")}],
               "media": [], "claims": []}
        for printed, pdf_page, kind in ((92, 93, "scan"), (93, 94, "image")):
            row["media"].append({
                "media_type": kind,
                "url": f"private-capture:{CAPTURE}#page={pdf_page}",
                "rights_status": "copyrighted",
                "notes": (f"Auction 57 lot {lot}, printed p. {printed}/PDF p. {pdf_page}; "
                          "page 93 photograph is one of three labelled bowls in the top row. "
                          f"Held PDF {CAPTURE}, SHA-256 {SHA256}. "
                          "Private research image; no public image reuse approval.")})
        if lot in (441, 442):
            if "Hillel Bar" not in content:
                raise ValueError("reported former collection absent from lot text")
            row["claims"].append({
                "field": "provenance",
                "value_text": "Auction catalogue reports former Hillel Bar-Sadeh collection, Jerusalem",
                "locator": f"Auction 57, lot {lot}, printed p. 92/PDF p. 93",
                "certainty": "reported",
                "notes": "Dealer's former-collection assertion only; no ownership chain or authenticity independently verified."})
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"lots": len(rows), "private_texts": sum(len(r["texts"]) for r in rows),
                      "page_links": sum(len(r["media"]) for r in rows),
                      "new_attributed_claims": sum(len(r["claims"]) for r in rows)}))


if __name__ == "__main__":
    main()
