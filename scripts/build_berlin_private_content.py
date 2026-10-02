"""Extract the held Berlin catalogue into an untracked Mike-only ingest manifest.

This is a text-layer extraction, not a diplomatic transcription. The source
capture is hash checked and every row retains a printed-page locator.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCE = "SRC-DA708912C2D3"
CAPTURE = "CAP-DBB06BEA4670"
SHA256 = "7a25b7b89f8160aaec249988f47a5fb08b654c8ca9506b44fcc48ee60cde6aac"
EDITIONS = [5, 99, 14, 24, 140, 7, 76, 15, 41, 35, 31, 95, 103, 159, 126, 102]
STARTS = [25, 30, 38, 41, 44, 47, 49, 51, 57, 60, 65, 68, 71, 74, 76, 79]
# Figure pages are identified from captions in the held volume. An edition may
# illustrate more than one shelf mark, or more than one view of the same bowl.
FIGURES = {
    5: [29], 99: [37], 14: [40], 24: [43], 140: [46], 7: [48],
    76: [50], 15: [56], 41: [59], 35: [63, 64], 31: [67],
    95: [70], 103: [73], 159: [75], 126: [78], 102: [81],
    149: [81],
}
FIELDS = {
    "Dimensions": "reported_dimensions",
    "Condition of bowl": "reported_physical_condition",
    "Condition of writing": "reported_writing_condition",
    "Dialect": "source_language_or_script_label",
    "Type of bowl": "reported_bowl_form",
    "Type of fragment": "reported_fragment_type",
}
FIELD_RE = re.compile(
    r"(?m)^\s*(Dimensions|Condition of bowl|Condition of writing|Dialect|Type of bowl|Type of fragment|Special features|Drawings|Personal names|Biblical [Qq]uotations|Description|Parallels|Publication|Origin|Linguistic and orthographic features|Lexical features):\s*"
)
ENTRY_RE = re.compile(r"(?m)^\s*(\d{1,3})\s+Shelf mark:\s*([^\n]+)")


def clean(s):
    return s.replace("\xa0", " ").replace("\u00ad", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Berlin capture hash mismatch")
    pdf = PdfReader(args.pdf)
    pages = {n: clean(pdf.pages[n - 1].extract_text()) for n in range(25, 188)}
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.match(r"Catalogue entry (\d+) ", row[0])
        if m:
            appearances.setdefault(int(m[1]), []).append(row[0])
    if set(appearances) != set(range(1, 170)) or sum(map(len, appearances.values())) != 170:
        raise ValueError("expected 169 entries and 170 source appearances")

    catalogue = ""
    page_offsets = []
    for n in range(85, 188):
        page_offsets.append((len(catalogue), n))
        catalogue += pages[n] + "\n"
    starts = list(ENTRY_RE.finditer(catalogue))
    if [int(m.group(1)) for m in starts] != list(range(1, 170)):
        raise ValueError("catalogue entry sequence incomplete")

    # Entry 168 has two explicitly distinct minimum objects. Keep separate rows.
    rows = [(n, {"source_id": SOURCE, "appearance": {"locator": loc},
                 "texts": [], "media": [], "claims": []})
            for n, locs in sorted(appearances.items()) for loc in locs]

    for ix, match in enumerate(starts):
        number = int(match.group(1))
        end = starts[ix + 1].start() if ix + 1 < len(starts) else len(catalogue)
        body = catalogue[match.start():end].strip()
        first_page = max(n for off, n in page_offsets if off <= match.start())
        last_page = max(n for off, n in page_offsets if off < end)
        locator = f"Catalogue entry {number}, printed pp. {first_page-14}–{last_page-14}"
        note = (f"Berlin 2018, {locator}; capture {CAPTURE}, SHA-256 {SHA256}. "
                "Born-digital working extraction; page headers, line breaks and typography "
                "need proofing. Mike-only research access.")
        fields = list(FIELD_RE.finditer(body))
        claims = []
        for fi, fm in enumerate(fields):
            field = FIELDS.get(fm.group(1))
            if not field:
                continue
            value = " ".join(body[fm.end():(fields[fi + 1].start() if fi + 1 < len(fields) else len(body))].split())
            # Avoid spilling prose or table/header noise into public factual claims.
            if value and len(value) < 100 and "Catalogue " not in value and (value.endswith(".") or value.endswith("?")):
                claims.append({"field": field, "value_text": value,
                               "locator": locator, "certainty": "reported"})
        for n, row in rows:
            if n != number:
                continue
            row["texts"].append({"text_type": "summary", "language": "English",
                                 "content": body, "editor": "Bhayro, Ford, Levene, Saar et al.",
                                 "locator": locator, "rights_status": "copyrighted",
                                 "public_ok": False, "notes": note})
            row["claims"].extend(claims)

    for i, (number, start) in enumerate(zip(EDITIONS, STARTS)):
        stop = STARTS[i + 1] - 1 if i + 1 < len(STARTS) else 81
        section = "\n".join(pages[p] for p in range(start, stop + 1)).strip()
        locator = f"Edition {i+1} (Roman section), printed pp. {start-14}–{stop-14}"
        note = (f"Berlin 2018, {locator}; capture {CAPTURE}, SHA-256 {SHA256}. "
                "Full born-digital section working extraction with commentary and notes; "
                "line breaks, damage, restorations and typography need page proofing. "
                "Mike-only research access.")
        targets = [number] + ([149] if i == 15 else [])
        for n, row in rows:
            if n not in targets:
                continue
            row["texts"].append({"text_type": "summary", "language": "mixed",
                                 "content": section, "editor": "Bhayro, Ford, Levene, Saar et al.",
                                 "locator": locator, "rights_status": "copyrighted",
                                 "public_ok": False, "notes": note})
            # Translation blocks are separately findable. Some sections edit
            # joining fragments; retain the full section beside this extraction.
            tm = re.search(r"(?m)^\s*TRANSLATION\s*$", section)
            if tm:
                before = section[:tm.start()]
                # The numbered reading starts after the edition's own metadata.
                origin = list(re.finditer(r"(?m)^\s*Origin:\s*", before))
                if origin:
                    reading = before[origin[-1].end():]
                    start_line = re.search(r"(?m)^\s*1\s+", reading)
                    if start_line:
                        reading = reading[start_line.start():].strip()
                        if len(reading) >= 20:
                            row["texts"].append({"text_type": "transliteration", "language": "source language",
                                                 "script": "Latin", "content": reading,
                                                 "editor": "Bhayro, Ford, Levene, Saar et al.",
                                                 "locator": locator + ", numbered reading block",
                                                 "rights_status": "copyrighted", "public_ok": False,
                                                 "notes": note + " Reading boundary is automatic; verify against page."})
                translation = re.split(r"(?im)^\s*Figure\s+\d+\b", section[tm.end():], maxsplit=1)[0].strip()
                if len(translation) >= 20:
                    row["texts"].append({"text_type": "translation", "language": "English",
                                         "content": translation, "editor": "Bhayro, Ford, Levene, Saar et al.",
                                         "locator": locator + ", translation block",
                                         "rights_status": "copyrighted", "public_ok": False,
                                         "notes": note + " Translation boundary is automatic; verify against page."})

    for n, row in rows:
        for page in FIGURES.get(n, []):
            row["media"].append({"media_type": "image",
                                 "url": f"private-capture:{CAPTURE}#page={page}",
                                 "rights_status": "copyrighted",
                                 "notes": (f"Berlin 2018, figure page, printed p. {page-14}; "
                                           f"PDF page {page}; capture {CAPTURE}. "
                                           "Private full-page derivative; no public reuse approval.")})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for _, row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "catalogue_entries": len(starts),
                      "texts": sum(len(r["texts"]) for _, r in rows),
                      "claims": sum(len(r["claims"]) for _, r in rows),
                      "image_links": sum(len(r["media"]) for _, r in rows)}))


if __name__ == "__main__":
    main()
