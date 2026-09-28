"""Build a private, page-located manifest from the held 2013 curse-text book.

The PDF text layer interleaves English and Hebrew lines. The split into
translation and transcription is a working extraction; each complete edited
section is also retained so no reading or commentary is lost.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-F2BEFBEFFC2E"
CAPTURE = "CAP-67B01E39FED1"
SHA256 = "d4b2c6e2946e10ab295d5b45a7ce2b132b674e35da40c09e1818a8af53d92a3d"
HEBREW = re.compile(r"[\u0590-\u05ff]")
LATIN = re.compile(r"[A-Za-z]")
STOP = re.compile(
    r"(?im)^\s*(?:Notes(?: for [^:\n]+)?|Previous readings|Formulaic parallels(?: in the other texts)?|"
    r"Further notes|Commentary):\s*"
)
FIGURE_PAGES = {
    "VA.2484": [42, 43, 48], "VA.2509": [47, 48],
    "VA.2423": [57, 58, 65], "VA.2416": [63, 64, 65],
    "VA.2434": [69, 70, 75], "VA.2424": [73, 74, 75],
    "VA.2496": [81, 82, 83, 87], "VA.2575": [84, 85, 86, 87],
    "VA.3382": [92, 97], "VA.3381": [96, 97],
    "VA.2492": [100], "VA.2418": [103], "VA.2417": [107, 108],
    "SD 27": [116, 117, 118, 119],
}


def split_reading(section):
    heading = re.search(r"Transcription and translation:\s*", section, re.I)
    if not heading:
        return "", ""
    working = section[heading.end():]
    stop = STOP.search(working)
    if stop:
        working = working[:stop.start()]
    english, hebrew = [], []
    for line in working.splitlines():
        line = line.strip()
        if not line or re.match(r"(?i)^(?:\d+\s+bowls (?:newly edited|that have already been published)|"
                                 r"[a-z&.\d ]+\s+\d{2,3}|VA\.\d+(?:\s*&\s*VA\.\d+)?)$", line):
            continue
        nh = len(HEBREW.findall(line))
        nl = len(LATIN.findall(line))
        if nh > nl:
            hebrew.append(line)
        elif nl or nh:
            english.append(line)
    return "\n".join(hebrew).strip(), "\n".join(english).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("curse-text capture hash mismatch")
    pdf = PdfReader(args.pdf)
    pages = {p: re.sub(r"[\ud800-\udfff]", "\ufffd",
                       pdf.pages[p - 1].extract_text().replace("\xa0", " "))
             for p in range(34, 148)}
    appearances = []
    conn = connect()
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.search(r"p\. (\d+)", row[0])
        if not m:
            raise ValueError("appearance lacks printed page: " + row[0])
        appearances.append((int(m[1]) + 14, row[0]))
    if len(appearances) != 30:
        raise ValueError(f"expected 30 source appearances, got {len(appearances)}")
    starts = sorted(set(p for p, _ in appearances))
    rows = []
    for start, appearance in sorted(appearances):
        end = next((p for p in starts if p > start), 148) - 1
        section = "\n".join(pages[p] for p in range(start, end + 1)).strip()
        reading, translation = split_reading(section)
        if len(reading) < 100 or len(translation) < 100:
            raise ValueError(f"missing bilingual reading for {appearance}")
        locator = f"Edited section {appearance.split(', p.')[0]}, printed pp. {start-14}–{end-14}"
        note = (f"Levene 2013, {locator}; capture {CAPTURE}, SHA-256 {SHA256}. "
                "Born-digital working extraction; the Hebrew/English separation is automatic "
                "and damaged readings, layout, notes and line breaks need page proofing. "
                "Mike-only research access.")
        row = {"source_id": SOURCE, "appearance": {"locator": appearance},
               "texts": [
                   {"text_type": "summary", "language": "mixed", "content": section,
                    "editor": "Dan Levene", "locator": locator + ", full edited section",
                    "rights_status": "copyrighted", "public_ok": False,
                    "notes": note + " Full section includes introduction, readings, commentary and notes."},
                   {"text_type": "transcription", "language": "Jewish Babylonian Aramaic",
                    "script": "Hebrew", "content": reading, "editor": "Dan Levene",
                    "locator": locator + ", Hebrew reading block",
                    "rights_status": "copyrighted", "public_ok": False, "notes": note},
                   {"text_type": "translation", "language": "English", "content": translation,
                    "editor": "Dan Levene", "locator": locator + ", translation block",
                    "rights_status": "copyrighted", "public_ok": False, "notes": note},
               ], "media": [], "claims": []}
        key = appearance.split(", p.")[0]
        for p in FIGURE_PAGES.get(key, []):
            row["media"].append({"media_type": "image",
                                 "url": f"private-capture:{CAPTURE}#page={p}",
                                 "rights_status": "copyrighted",
                                 "notes": (f"Levene 2013, printed photograph p. {p-14}, PDF page {p}; "
                                           f"capture {CAPTURE}. Private full-page derivative; "
                                           "no public reuse approval.")})
        # Concise measurements and collection labels are source-reported facts.
        prefix = section[:re.search(r"Transcription and translation:", section, re.I).start()]
        for source_field, field in [("Dimensions", "reported_dimensions"),
                                    ("Physical location", "reported_collection_location")]:
            m = re.search(rf"(?im)^{re.escape(source_field)}:\s*([^\n]+)", prefix)
            if m:
                value = " ".join(m.group(1).split())
                if len(value) < 120:
                    row["claims"].append({"field": field, "value_text": value,
                                          "locator": locator, "certainty": "reported"})
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "texts": sum(len(x["texts"]) for x in rows),
                      "media": sum(len(x["media"]) for x in rows),
                      "claims": sum(len(x["claims"]) for x in rows)}))


if __name__ == "__main__":
    main()
