"""Extract bounded working OCR from the held Ellis 1853 and Schwab 1891 scans.

Internet Archive OCR is retained in the private vault and hash checked here.
The OCR damages original-script glyphs; whole sections are searchable research
aid only, while separately indexed translations contain prose blocks.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from bowl_index.db import connect


LAYARD_SOURCE = "SRC-8900A7CAF037"
LAYARD_CAPTURE = "CAP-9ACDF2639CDE"
LAYARD_PDF_HASH = "bf304bcb7f5600b3186468de76dd50aba6de7ef58331c886d2e33befea16c633"
LAYARD_OCR_HASH = "af61d187ebc2e6ec2740e9d5926f7c2bfee3a6606d2adea26e1450bc63298ec4"
SCHWAB_SOURCE = "SRC-F42955665921"
SCHWAB_CAPTURE = "CAP-A514265C9E93"
SCHWAB_PDF_HASH = "f34353aac1877681ca20691e6e2fb955f11cb37766fe943067f1255944d2f43d"
SCHWAB_OCR_HASH = "cc6df89a88d2f602a3b0f94283687e9517287ce27c4e96dfd1c101c2ff4a4007"
LAYARD_PAGES = {1: (512, 513, 514), 2: (514, 515, 516),
                3: (516, 517, 518), 4: (518, 519),
                5: (519, 520, 521), 6: (521, 522)}
SCHWAB_PAGES = {"N": (590, 591), "O": (590, 591, 592),
                "P": (590, 592, 593)}


def verified_text(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"source hash mismatch: {path}")
    return raw.decode("utf-8", errors="replace")


def clean_ocr(value):
    value = re.sub(r"[ \t]{2,}", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def appearance_map(conn, source):
    return {row[0] for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (source,))}


def layard_rows(conn, ocr):
    anchor = ocr.index("“ I now  proceed  to  give  translations")
    starts = {}
    for m in re.finditer(r"(?m)^No\.  ([1-6])\.[ \t]*$", ocr[anchor:]):
        n = int(m[1])
        starts.setdefault(n, anchor + m.start())
    if set(starts) != set(LAYARD_PAGES) or list(starts) != sorted(starts):
        raise ValueError("six Ellis numbered headings not recovered in order")
    end = ocr.index("Ko.  7.", starts[6])
    limits = {**starts, 7: end}
    appearances = appearance_map(conn, LAYARD_SOURCE)
    rows = []
    for n, pages in LAYARD_PAGES.items():
        # Some page spans in the source inventory overlap their neighbors; use
        # the registered locator as the authoritative appearance key.
        registered = next((x for x in appearances if x.startswith(f"Ellis bowl no. {n},")), None)
        if not registered:
            raise ValueError(f"Ellis no. {n} has no registered appearance")
        section = clean_ocr(ocr[limits[n]:limits[n+1]])
        if len(section) < 500:
            raise ValueError(f"Ellis no. {n} section implausibly short")
        row = {"source_id": LAYARD_SOURCE, "appearance": {"locator": registered},
               "texts": [{"text_type": "summary", "language": "English and original script",
                          "content": section, "editor": "Thomas Ellis",
                          "locator": f"Ellis bowl no. {n}, {registered.split(', ',1)[1]}; OCR from printed pp. {pages[0]}–{pages[-1]}",
                          "rights_status": "public_domain", "public_ok": False,
                          "notes": (f"Working Internet Archive OCR of the numbered Ellis 1853 section; "
                                    f"OCR SHA-256 {LAYARD_OCR_HASH}, held PDF {LAYARD_CAPTURE}, "
                                    f"SHA-256 {LAYARD_PDF_HASH}. Original-script glyphs and some "
                                    "English letters are damaged in OCR. Consult the linked facsimiles "
                                    "before citation; this is not a checked inscription transcription.")}],
               "media": [], "claims": []}
        if n != 3:
            opener = re.search(r"[“«]", section)
            if not opener:
                raise ValueError(f"Ellis no. {n} translation opening quote missing")
            closer = section.find("”", opener.end()+150)
            if closer < 0:
                raise ValueError(f"Ellis no. {n} translation ending quote missing")
            translation = clean_ocr(section[opener.end():closer])
            if len(translation) < 250:
                raise ValueError(f"Ellis no. {n} translation too short")
            row["texts"].append({"text_type": "translation", "language": "English",
                                 "content": translation, "editor": "Thomas Ellis",
                                 "locator": f"Ellis no. {n} published translation, printed pp. {pages[0]}–{pages[-1]}",
                                 "rights_status": "public_domain", "public_ok": False,
                                 "notes": ("Working OCR of Ellis's English translation only. "
                                           "OCR errors, line wrapping and damaged readings require "
                                           "page proofing; no original-script transcription is claimed. "
                                           f"OCR SHA-256 {LAYARD_OCR_HASH}; PDF {LAYARD_CAPTURE}.")})
        for printed in pages:
            row["media"].append({"media_type": "scan",
                                 "url": f"private-capture:{LAYARD_CAPTURE}#page={printed+59}",
                                 "rights_status": "public_domain",
                                 "notes": (f"Ellis 1853 no. {n}, printed p. {printed}/PDF p. {printed+59}. "
                                           "Private source-page facsimile, including any bowl drawing "
                                           "on the page. Internet Archive scan; no public reuse decision.")})
        rows.append(row)
    return rows


def schwab_rows(conn, ocr):
    anchor = ocr.index("En  ces  derniers  temps,  les  fouilles  de  la  mission")
    headings = [(m[1], m.start()) for m in re.finditer(r"(?m)^([NOPQ])\.[ \t]*$", ocr)
                if anchor-300 < m.start() < anchor+9000]
    if [key for key, _ in headings] != ["N", "O", "P", "Q"]:
        raise ValueError("Schwab item headings not found in expected order")
    starts = dict(headings[:3])
    end = headings[3][1]
    if not (0 < starts["N"] < starts["O"] < starts["P"] < end):
        raise ValueError("Schwab item boundaries do not match N–P")
    limits = {**starts, "Q": end}
    appearances = appearance_map(conn, SCHWAB_SOURCE)
    rows = []
    for key, next_key in (("N", "O"), ("O", "P"), ("P", "Q")):
        pages = SCHWAB_PAGES[key]
        registered = next((x for x in appearances if x.endswith(f"item {key}")), None)
        if not registered:
            raise ValueError(f"Schwab {key} has no registered appearance")
        section = clean_ocr(ocr[limits[key]:limits[next_key]])
        if len(section) < 500:
            raise ValueError(f"Schwab {key} section implausibly short")
        row = {"source_id": SCHWAB_SOURCE, "appearance": {"locator": registered},
               "texts": [{"text_type": "summary", "language": "French and original script",
                          "content": section, "editor": "Moïse Schwab",
                          "locator": f"Schwab item {key}, printed pp. {pages[0]}–{pages[-1]}",
                          "rights_status": "public_domain", "public_ok": False,
                          "notes": (f"Working Internet Archive OCR of Schwab's numbered item; "
                                    f"OCR SHA-256 {SCHWAB_OCR_HASH}, held PDF {SCHWAB_CAPTURE}, "
                                    f"SHA-256 {SCHWAB_PDF_HASH}. Hebrew-script glyphs are corrupt "
                                    "in OCR and are not treated as a transcription. Consult linked "
                                    "facsimile pages for readings and scan-check French prose.")}],
               "media": [], "claims": []}
        if key == "N":
            match = re.search(r"Sois  scelle.*?Amen,  Amen,  Selah\.", ocr[limits[key]:limits[next_key]], re.S)
            if not match:
                raise ValueError("Schwab N French translation span missing")
            row["texts"].append({"text_type": "translation", "language": "French",
                                 "content": clean_ocr(match[0]), "editor": "Moïse Schwab",
                                 "locator": "Schwab item N, partial French translation, printed p. 591",
                                 "rights_status": "public_domain", "public_ok": False,
                                 "notes": ("Schwab explicitly presents this as a possible reading with "
                                           "uncertain word divisions, not a complete certain edition. "
                                           "Working OCR needs page proofing; no Hebrew-script "
                                           f"transcription is claimed. OCR SHA-256 {SCHWAB_OCR_HASH}.")})
        for printed in pages:
            row["media"].append({"media_type": "scan",
                                 "url": f"private-capture:{SCHWAB_CAPTURE}#page={printed+68}",
                                 "rights_status": "public_domain",
                                 "notes": (f"Schwab 1891 item {key}, printed p. {printed}/PDF p. {printed+68}. "
                                           "Private source-page facsimile from Internet Archive; "
                                           "no public reuse decision.")})
        rows.append(row)
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    for label in ("layard", "schwab"):
        ap.add_argument(f"--{label}-pdf", type=Path, required=True)
        ap.add_argument(f"--{label}-ocr", type=Path, required=True)
        ap.add_argument(f"--{label}-output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.layard_pdf.read_bytes()).hexdigest() != LAYARD_PDF_HASH:
        raise ValueError("Layard PDF hash mismatch")
    if hashlib.sha256(args.schwab_pdf.read_bytes()).hexdigest() != SCHWAB_PDF_HASH:
        raise ValueError("Schwab PDF hash mismatch")
    conn = connect()
    layard = layard_rows(conn, verified_text(args.layard_ocr, LAYARD_OCR_HASH))
    schwab = schwab_rows(conn, verified_text(args.schwab_ocr, SCHWAB_OCR_HASH))
    write_rows(args.layard_output, layard)
    write_rows(args.schwab_output, schwab)
    for name, rows in (("layard", layard), ("schwab", schwab)):
        print(json.dumps({"source": name, "appearances": len(rows),
                          "text_rows": sum(len(r["texts"]) for r in rows),
                          "page_links": sum(len(r["media"]) for r in rows)}))


if __name__ == "__main__":
    main()
