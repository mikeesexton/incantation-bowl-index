"""Stage a page-bounded Levene Hebrew reading using PDF glyph positions.

Use the bundled workspace Python (pdfplumber). Output is protected source text:
write only under data/private/ and collate every line against the rendered PDF.
The script repairs glyph order and word gaps; it does not resolve editorial marks.

Levene 2013's text layer stores the Hebrew column in visual order without word
spaces. This reader orders glyphs right to left by position and restores:

* word gaps wider than ``--gap`` PDF points;
* mirrored paired signs, so a printed opening bracket, brace, parenthesis or
  angle bracket is emitted as the logical opening sign;
* left-to-right runs inside a Hebrew line (line numbers, "Exterior",
  "letters 4–5") in reading order;
* printed strikeouts, detected as thin horizontal rules through a glyph, as a
  U+0336 combining overlay after each struck glyph;
* short raised marks and glyphs set in a fallback font (some yods) merged into
  the nearest text line instead of emitted as a line of their own.

Footnote reference numerals are reported, not removed. Nothing here is a
completed review: compare every staged line with a rendered page.
"""

import argparse
import hashlib
import re
from pathlib import Path

import pdfplumber


SHA256 = "d4b2c6e2946e10ab295d5b45a7ce2b132b674e35da40c09e1818a8af53d92a3d"
PDF = Path("data/private/archive/sha256") / SHA256[:2] / SHA256
STRIKE = "̶"
MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{",
          "⟨": "⟩", "⟩": "⟨", "<": ">", ">": "<"}
LTR = "0-9A-Za-zÀ-ɏḀ-ỿ"
LTR_RUN = re.compile("[" + LTR + "]" + STRIKE + "?(?:[,./–\\-" + LTR + STRIKE + "]*[" + LTR + "]" + STRIKE + "?)?")


def _ltr_in_reading_order(line):
    return LTR_RUN.sub(lambda m: "".join(re.findall("." + STRIKE + "?", m.group(0))[::-1]), line)


def _struck(page, chars):
    rules = [r for r in page.lines + page.rects
             if (r["bottom"] - r["top"]) < 2 and (r["x1"] - r["x0"]) > 2]
    struck = set()
    for char in chars:
        centre, height = (char["x0"] + char["x1"]) / 2, char["bottom"] - char["top"]
        for rule in rules:
            y = (rule["top"] + rule["bottom"]) / 2
            if (rule["x0"] - 0.3 <= centre <= rule["x1"] + 0.3
                    and char["top"] + 0.3 * height <= y <= char["bottom"] - 0.2 * height):
                struck.add(id(char))
    return struck


def reading_lines(page, top, bottom, x_min=306, x_max=None, gap=1.4, notes=None):
    x_max = page.width if x_max is None else x_max
    chars = [c for c in page.chars
             if c["x0"] >= x_min and c["x1"] <= x_max + 0.5 and top <= c["top"] <= bottom and c["text"].strip()]
    struck = _struck(page, chars)
    lines = []
    for char in sorted(chars, key=lambda c: c["bottom"]):
        for line in lines:
            if abs(line["base"] - char["bottom"]) <= 2.2:
                line["chars"].append(char)
                break
        else:
            lines.append({"base": char["bottom"], "chars": [char]})

    def weak(line):
        group = line["chars"]
        return (len(group) < 4 or all(c["text"] in "יו" for c in group)
                or all("Guttman" in c.get("fontname", "") for c in group))

    strong = [line for line in lines if not weak(line)]
    for line in (line for line in lines if weak(line)):
        nearest = min(strong, key=lambda s: abs(s["base"] - line["base"])) if strong else None
        if nearest and abs(nearest["base"] - line["base"]) <= 7:
            nearest["chars"].extend(line["chars"])
        else:
            strong.append(line)
    result = []
    for line in sorted(strong, key=lambda l: l["base"]):
        ordered = sorted(line["chars"], key=lambda c: -(c["x0"] + c["x1"]) / 2)
        text = ""
        for index, char in enumerate(ordered):
            if index and ordered[index - 1]["x0"] - char["x1"] > gap:
                text += " "
            text += MIRROR.get(char["text"], char["text"]) + (STRIKE if id(char) in struck else "")
            if notes is not None and char["size"] < 8:
                notes.append(f"small glyph {char['text']!r} at y={line['base']:.1f}")
        result.append(_ltr_in_reading_order(text))
    if notes is not None and struck:
        notes.append(f"{len(struck)} struck glyph(s)")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, required=True, help="one-based PDF page")
    parser.add_argument("--top", type=float, required=True, help="PDF-point upper reading bound")
    parser.add_argument("--bottom", type=float, required=True, help="PDF-point lower reading bound")
    parser.add_argument("--x-min", type=float, default=306, help="left edge of the Hebrew column")
    parser.add_argument("--x-max", type=float, default=None, help="right edge (for multi-column pages)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.as_posix().startswith("data/private/"):
        raise ValueError("protected reading output must stay in data/private/")
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Levene capture hash mismatch")
    notes = []
    with pdfplumber.open(PDF) as pdf:
        lines = reading_lines(pdf.pages[args.page - 1], args.top, args.bottom, args.x_min, args.x_max, notes=notes)
    if not lines:
        raise ValueError("no Hebrew reading lines in requested bounds")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n")
    print(f"staged {len(lines)} lines from PDF p. {args.page} in {args.output}")
    for note in notes:
        print("check:", note)


if __name__ == "__main__":
    main()
