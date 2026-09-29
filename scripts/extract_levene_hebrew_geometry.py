"""Stage a page-bounded Levene Hebrew reading using PDF glyph positions.

Use the bundled workspace Python (pdfplumber). Output is protected source text:
write only under data/private/ and collate every line against the rendered PDF.
The script repairs glyph order and word gaps; it does not resolve editorial marks.
"""

import argparse
import hashlib
import re
from pathlib import Path

import pdfplumber
from pdfplumber.utils import cluster_objects


SHA256 = "d4b2c6e2946e10ab295d5b45a7ce2b132b674e35da40c09e1818a8af53d92a3d"
PDF = Path("data/private/archive/sha256") / SHA256[:2] / SHA256
HEBREW = re.compile(r"[\u0590-\u05ff]")


def reading_lines(page, top, bottom, x_min=306, gap=1.4):
    chars = [char for char in page.chars if char["x0"] > x_min and top <= char["top"] <= bottom]
    result = []
    for group in cluster_objects(chars, "top", tolerance=2):
        if sum(bool(HEBREW.search(char["text"])) for char in group) < 4:
            continue
        ordered = sorted(group, key=lambda char: -char["x0"])
        line = ""
        for index, char in enumerate(ordered):
            if index and ordered[index - 1]["x0"] - char["x1"] > gap:
                line += " "
            line += char["text"]
        # The PDF's right-to-left glyph positions also reverse the numeric
        # parenthesis glyph sequence. Keep the printed line marker as (n).
        line = re.sub(r"\)(\d+)\(", lambda match: "(" + match[1][::-1] + ")", line)
        result.append(line)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, required=True, help="one-based PDF page")
    parser.add_argument("--top", type=float, required=True, help="PDF-point upper reading bound")
    parser.add_argument("--bottom", type=float, required=True, help="PDF-point lower reading bound")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.as_posix().startswith("data/private/"):
        raise ValueError("protected reading output must stay in data/private/")
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Levene capture hash mismatch")
    with pdfplumber.open(PDF) as pdf:
        lines = reading_lines(pdf.pages[args.page - 1], args.top, args.bottom)
    if not lines:
        raise ValueError("no Hebrew reading lines in requested bounds")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n")
    print(f"staged {len(lines)} lines from PDF p. {args.page} in {args.output}")


if __name__ == "__main__":
    main()
