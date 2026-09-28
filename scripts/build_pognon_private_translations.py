"""Separate bounded French translation spans from Pognon's held scan.

The source OCR remains a working aid: page footnotes can interrupt a sentence.
Each row retains the exact source range and points back to its facsimile.
"""

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect
from build_pognon_private_content import SOURCE, CAPTURE, SHA256, START_PAGES, source_text, heading


# Translation end is the next editorial discussion, not the next bowl heading.
# Empty end means the numbered section closes with the translation itself.
BOUNDS = {
    1: (0, r"est\s+leparticipe passif"),
    2: (0, r"4o est une faute évidente"),
    3: (0, r"val doit être lu"),
    4: (0, r"Lemot"),
    5: (1, r"Cetexte finit"),
    6: (0, r"Malgré saforme"),
    7: (0, r"Au sujet des formules"),
    8: (0, r"Les lettres qui commencent"),
    9: (0, r"L'inscription finit"),
    10: (0, None),
    11: (0, r"Au sujet de"),
    12: (0, None),
    13: (0, r"Cette inscription estfort difficile"),
    14: (0, None),
    15: (0, r"Le mot"),
    16: (0, r"Letexte decette inscription"),
    17: (1, r"estune faute pour"),
    18: (0, r"L'homme est délivré de \.(?=\s)"),
    19: (0, r"Aulieu dugroupe"),
    20: (0, r"La formule magique"),
    21: (0, r"On voit que"),
    22: (0, r"Ce texte curieux"),
    23: (0, r"- \( 69 \)"),
    24: (0, r"Lemot \(plur"),
    25: (1, r"ةداركلا estécrit"),
    26: (0, r"Ce texte est composé"),
    27: (0, r"sont lepremier"),
    28: (0, r"Le mot de m'est inconnu"),
    29: (0, r"Les lacunes decette inscription"),
    30: (1, None),
    31: (0, r"J'ai parlé , à la page"),
}


def section_text(reader, n):
    first = START_PAGES[n - 1]
    last = START_PAGES[n] if n < 31 else 104
    pages = {p: source_text(reader.pages[p - 1]) for p in range(first, last + (last < 104))}
    start = heading(n, pages[first])
    end = heading(n + 1, pages[last]) if n < 31 else 0
    pieces = []
    for p in range(first, last + 1):
        if p == 104:
            break
        content = pages[p]
        if p == first == last:
            content = content[start:end]
        elif p == first:
            content = content[start:]
        elif p == last:
            content = content[:end]
        pieces.append(content.strip())
    return "\n".join(x for x in pieces if x), first, last


def translation_span(section, n):
    section = re.sub(r"\s+", " ", section.replace("\x00", " "))
    marker_index, end_pattern = BOUNDS[n]
    if n == 10:
        markers = list(re.finditer(r"traduction littérale\s*:", section, re.I))
    else:
        markers = list(re.finditer(r"Traduction\s*[.:]", section, re.I))
    if len(markers) <= marker_index:
        raise ValueError(f"translation marker missing for no. {n}")
    start = markers[marker_index].end()
    if end_pattern is None:
        end = len(section)
    else:
        matches = list(re.finditer(end_pattern, section[start:], re.I))
        m = (matches[-1] if n == 4 and matches else
             matches[0] if matches else None)
        if not m:
            raise ValueError(f"translation end missing for no. {n}")
        end = start + (m.end() if n == 18 else m.start())
    content = section[start:end].strip()
    if n in {3, 29}:
        second_start = markers[1].end()
        second_end_pattern = (r"Ausujet de coupe n° 29" if n == 3 else None)
        if second_end_pattern:
            second_end_match = re.search(second_end_pattern, section[second_start:], re.I)
            if not second_end_match:
                raise ValueError("second translation end missing for no. 3")
            second_end = second_start + second_end_match.start()
        else:
            second_end = len(section)
        second = section[second_start:second_end].strip()
        if n == 3:
            prefix = re.search(r"détourne lalumière sur les\s*$", section[:markers[1].start()], re.I)
            if prefix:
                second = prefix.group(0) + " " + second
        content = "[Interior inscription] " + content + "\n\n[Exterior inscription] " + second
    if len(content) < 80:
        raise ValueError(f"translation implausibly short for no. {n}: {len(content)}")
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Pognon capture hash mismatch")
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    reader = PdfReader(args.pdf)
    conn = connect()
    appearances = {}
    for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,)):
        m = re.match(r"Khouabir bowl no\. (\d+);", row[0])
        if m:
            appearances[int(m[1])] = row[0]
    if set(appearances) != set(range(1, 32)):
        raise ValueError("expected 31 Pognon appearances")
    existing = set()
    for row in conn.execute("SELECT a.locator FROM appearances a JOIN texts t ON t.appearance_id=a.id "
                            "WHERE a.source_id=? AND t.text_type='translation'", (SOURCE,)):
        existing.add(int(re.search(r"no\. (\d+)", row[0]).group(1)))
    if existing & BOUNDS.keys():
        raise ValueError(f"already translated: {sorted(existing & BOUNDS.keys())}")
    rows = []
    lengths = {}
    for n in sorted(BOUNDS):
        section, first, last = section_text(reader, n)
        content = translation_span(section, n)
        lengths[n] = len(content)
        locator = (f"No. {n}, French translation, printed pp. {first-11}–{last-11}; "
                   f"PDF pp. {first}–{last}")
        rows.append({"source_id": SOURCE, "appearance": {"locator": appearances[n]},
                     "texts": [{"text_type": "translation", "language": "French",
                                "content": content, "editor": "Henri Pognon", "locator": locator,
                                "rights_status": "public_domain", "public_ok": False,
                                "notes": (f"Pognon 1898–99; capture {CAPTURE}, SHA-256 {SHA256}. "
                                          "Bounded working OCR of the scholar's French translation. "
                                          "Scan text is unproofread and may contain interleaved page footnotes, "
                                          "hyphenation or damaged spacing. Consult the linked source-page facsimile. "
                                          "Mike-only research access.")}], "media": [], "claims": []})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"translations": len(rows), "characters": sum(lengths.values()),
                      "shortest": min(lengths.items(), key=lambda x: x[1]),
                      "longest": max(lengths.items(), key=lambda x: x[1])}))


if __name__ == "__main__":
    main()
