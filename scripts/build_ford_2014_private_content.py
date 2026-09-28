"""Link Ford 2014's scan pages and three manually read translations privately."""

import argparse
import hashlib
import json
from pathlib import Path

from bowl_index.db import connect


SOURCE = "SRC-FORD2014-AUOR"
CAPTURE = "CAP-877D87C47D82"
SHA256 = "0b7f1780d434c86cd2999eb895c2729130a105f74759708129f89c8e2f1b2dd7"
PAGES = {
    "Commentary on JBA 3, Ford 2014 pp. 236": (236,),
    "Commentary on JBA 15, Ford 2014 pp. 236": (236,),
    "Commentary on JBA 18, Ford 2014 pp. 236": (236,),
    "Commentary on JBA 23, Ford 2014 pp. 236–237, 237–239": tuple(range(236, 240)),
    "Commentary on JBA 25, Ford 2014 pp. 239": (239,),
    "Commentary on JBA 35, Ford 2014 pp. 239": (239,),
    "Commentary on JBA 37, Ford 2014 pp. 239–241": tuple(range(239, 242)),
    "Commentary on JBA 44, Ford 2014 pp. 241–242": (241, 242),
    "Commentary on JBA 45, Ford 2014 pp. 242": (242,),
    "Commentary on JBA 49, Ford 2014 pp. 242": (242,),
    "Commentary on JBA 55, Ford 2014 pp. 242–244": (242, 243, 244),
    "Commentary on JBA 56, Ford 2014 pp. 244–246": (244, 245, 246),
    "Commentary on JBA 63, Ford 2014 pp. 246": (246,),
    "Appendix 1, pp. 246–252": tuple(range(246, 253)),
    "Appendix 2, pp. 253–258": tuple(range(253, 259)),
    "p. 256; figures 25–26, pp. 259–260": (256, 259, 260),
}
IMAGE_PAGES = set(range(250, 253)) | {257, 258, 259, 260}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--working-translations", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Ford 2014 capture hash mismatch")
    translations = json.loads(args.working_translations.read_text(encoding="utf-8"))
    if set(translations) != {"Appendix 1, pp. 246–252", "Appendix 2, pp. 253–258",
                             "p. 256; figures 25–26, pp. 259–260"}:
        raise ValueError("the three edited translation sections are required")
    if [translations[k]["printed_page"] for k in translations] != [248, 254, 256]:
        raise ValueError("translation page map differs from inspected scan")
    conn = connect()
    actual = {row[0] for row in conn.execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCE,))}
    if actual != set(PAGES):
        raise ValueError("Ford appearance inventory differs from inspected page map")
    rows = []
    for locator, pages in PAGES.items():
        row = {"source_id": SOURCE, "appearance": {"locator": locator},
               "texts": [], "media": [], "claims": []}
        for printed in pages:
            pdf_page = printed - 234
            row["media"].append({
                "media_type": "image" if printed in IMAGE_PAGES else "scan",
                "url": f"private-capture:{CAPTURE}#page={pdf_page}",
                "rights_status": "copyrighted",
                "notes": (f"Ford 2014, {locator}; printed p. {printed}/PDF p. {pdf_page}. "
                          f"Held institutional article scan {CAPTURE}, SHA-256 {SHA256}. "
                          "Private page facsimile only; no public image or text reuse approval.")})
        if locator in translations:
            item = translations[locator]
            printed = item["printed_page"]
            content = item["content"].strip()
            if len(content) < 250:
                raise ValueError("translation text unexpectedly short")
            row["texts"].append({
                "text_type": "translation", "language": "English", "content": content,
                "editor": "James Nathan Ford",
                "locator": f"{locator}; translation, printed p. {printed}/PDF p. {printed-234}",
                "rights_status": "copyrighted", "public_ok": False,
                "notes": (f"Manual working transcription of Ford's published English translation "
                          f"from printed p. {printed}; capture {CAPTURE}, SHA-256 {SHA256}. "
                          "Line numbers and uncertainty marks follow the printed block where legible. "
                          "Check the linked facsimile before quotation; Mike-only research access.")})
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"appearances": len(rows), "translation_rows": sum(len(r["texts"]) for r in rows),
                      "page_links": sum(len(r["media"]) for r in rows),
                      "distinct_pages": len({m["url"] for r in rows for m in r["media"]})}))


if __name__ == "__main__":
    main()
