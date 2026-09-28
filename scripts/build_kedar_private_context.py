"""Retain Kedar's source-located NFP/handwriting evidence for Mike Access.

The thesis discusses groups of bowls. Shared page extracts are expressly
labelled as such and do not assert that an author or hand has been verified.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-A90AB34CA3FE"
CAPTURE = "CAP-E1FB74EF0432"
SHA256 = "8ae23ed1a2fdcbc6faba4f3a43039d2893aa201d9f84fcb2b88b9318c42dc944"
GROUPS = {102: (113, 10), 105: (116, 6), 106: (117, 2),
          134: (145, 10), 135: (146, 1)}


def page_excerpt(pdf, printed, page):
    raw = pdf.pages[page - 1].extract_text()
    marker = re.search(rf"(?m)^\s*{printed}\s*$", raw)
    if not marker:
        raise ValueError(f"printed page {printed} not found on PDF page {page}")
    content = raw[marker.end():]
    if printed == 135:
        content = content.split("4.6 Gušnazdukh", 1)[0]
    content = re.sub(r"\s+", " ", content).strip()
    if len(content) < 200:
        raise ValueError(f"short thesis extract at printed p. {printed}")
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Kedar capture hash mismatch")
    pdf = PdfReader(args.pdf)
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        match = re.match(r"p\. (\d+),", row[0])
        if not match:
            raise ValueError(f"unexpected appearance locator: {row[0]}")
        appearances.setdefault(int(match.group(1)), []).append(row[0])
    if {k: len(v) for k, v in appearances.items()} != {k: v[1] for k, v in GROUPS.items()}:
        raise ValueError("Kedar appearance groups differ from expected inventory")
    rows = []
    for printed, (pdf_page, _) in GROUPS.items():
        content = page_excerpt(pdf, printed, pdf_page)
        for locator in sorted(appearances[printed]):
            row = {"source_id": SOURCE, "appearance": {"locator": locator},
                   "texts": [{"text_type": "summary", "language": "English and Hebrew",
                              "content": content, "editor": "Dorit Kedar",
                              "locator": f"{locator}; PDF p. {pdf_page}",
                              "rights_status": "copyrighted", "public_ok": False,
                              "notes": (f"Kedar 2019, printed p. {printed}; capture {CAPTURE}, "
                                        f"SHA-256 {SHA256}. This is a shared table/page discussion "
                                        "associated with the appearance, not an individual inscription "
                                        "edition or independently verified handwriting/authorship finding. "
                                        "Working PDF text layer; Mike-only research access.")}],
                   "media": [], "claims": []}
            if locator == "p. 134, note 546":
                row["media"].append({"media_type": "image",
                                     "url": f"private-capture:{CAPTURE}#page=145",
                                     "rights_status": "copyrighted",
                                     "notes": ("Kedar 2019, image 8, printed p. 134/PDF p. 145: "
                                               "JNL Heb. 4, 6079 photograph credited to the National Library "
                                               "of Israel. Private page derivative only; no public image approval.")})
            if locator == "p. 102, table 6, NFP 5 and note 412":
                image_page = pdf.pages[145].extract_text()
                image_discussion = image_page.split("4.6 Gušnazdukh", 1)
                if len(image_discussion) != 2:
                    raise ValueError("Gorea B2 image discussion missing on PDF p. 146")
                row["texts"].append({"text_type": "summary", "language": "English and Hebrew",
                                     "content": "4.6 Gušnazdukh" + image_discussion[1].strip(),
                                     "editor": "Dorit Kedar",
                                     "locator": "NFP-bowl 5, image 9 discussion, printed p. 135; PDF p. 146",
                                     "rights_status": "copyrighted", "public_ok": False,
                                     "notes": (f"Kedar 2019; capture {CAPTURE}, SHA-256 {SHA256}. "
                                               "Source's bowl/image description and interpretation, "
                                               "not an independently verified identification or reading. "
                                               "Working PDF text layer; Mike-only research access.")})
                row["media"].append({"media_type": "image",
                                     "url": f"private-capture:{CAPTURE}#page=146",
                                     "rights_status": "copyrighted",
                                     "notes": ("Kedar 2019, image 9, printed p. 135/PDF p. 146: "
                                               "Gorea 2003 B2 photograph credited to Musée Champollion. "
                                               "Private page derivative only; no public image approval.")})
            rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "text_rows": sum(len(r["texts"]) for r in rows),
                      "photo_page_links": sum(len(r["media"]) for r in rows),
                      "distinct_source_pages": len(GROUPS)}))


if __name__ == "__main__":
    main()
