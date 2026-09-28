"""Extract the final three appearance-bearing held PDF sources for Mike Access.

The Oriental Institute PDF disallows text copying but permits printing. Its
entry is summarized from the printed page without copying the prose layer.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SOURCES = {
    "gordon": ("SRC-0383E0E0A2F2", "CAP-EABFF9404C4C", "71de7b86e0cc549b73d949f4a4b8923886f4d92dfd1b2f21907c9fe6058bafcc"),
    "waller": ("SRC-19F191B3F5C5", "CAP-52643D00C6E1", "b60b030f13d2ae48ffd951b7bb59a8801cbbd71b0e060d13637228e1e4237c77"),
    "oim": ("SRC-1F676D0669B6", "CAP-66A5F6A4ACC7", "b3564079a55188e295fe49a88c4cb37804a79d404e70b3ec7eed65b19b23259d"),
}


def verified_pdf(path, key, page_count):
    expected = SOURCES[key][2]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"{key} held PDF hash mismatch")
    if key == "oim":
        # Do not extract an encrypted PDF's restricted text layer.
        return None
    pages = PdfReader(path).pages
    if len(pages) != page_count:
        raise ValueError(f"{key} page count mismatch")
    return pages


def normalized(page):
    return re.sub(r"\s+", " ", page.extract_text() or "").strip()


def media(key, page, label):
    _, cap, _ = SOURCES[key]
    return {"media_type": "scan", "url": f"private-capture:{cap}#page={page}",
            "rights_status": "unknown",
            "notes": f"{label}; PDF p. {page}. Private source-page facsimile. Public image reuse unreviewed."}


def appearance(key):
    rows = list(connect().execute("SELECT locator FROM appearances WHERE source_id=?", (SOURCES[key][0],)))
    if len(rows) != 1:
        raise ValueError(f"expected one existing {key} appearance")
    return rows[0][0]


def gordon_row(pages):
    source, cap, sha = SOURCES["gordon"]
    section = "\n\n".join(
        f"[PDF p. {n}; printed p. {n + 464}]\n{normalized(pages[n - 1])}"
        for n in range(2, 11))
    joined = " ".join(normalized(pages[n - 1]) for n in (6, 7))
    start = re.search(r"\bTranslation\.", joined)
    end = re.search(r"\bNotes\.", joined)
    if not start or not end or end.start() <= start.end():
        raise ValueError("Gordon G translation boundaries missing")
    translated = joined[start.end():end.start()].strip()
    if len(section) < 10000 or len(translated) < 3000:
        raise ValueError("Gordon G extract implausibly short")
    return {"source_id": source, "appearance": {"locator": appearance("gordon")},
            "texts": [
                {"text_type": "summary", "language": "English with damaged Aramaic OCR",
                 "content": section, "editor": "Cyrus H. Gordon",
                 "locator": "Gordon, An Aramaic Exorcism, printed pp. 466–474 / PDF pp. 2–10",
                 "rights_status": "unknown", "public_ok": False,
                 "notes": f"Working full article OCR, including edition, translation and notes. Original-script glyphs are damaged and are not a transcription. Held PDF {cap}, SHA-256 {sha}."},
                {"text_type": "translation", "language": "English", "content": translated,
                 "editor": "Cyrus H. Gordon",
                 "locator": "Gordon text G, published translation, printed pp. 470–471 / PDF pp. 6–7",
                 "rights_status": "unknown", "public_ok": False,
                 "notes": f"Working OCR of Gordon's published English translation; requires page proofing. Held PDF {cap}, SHA-256 {sha}."}],
            "media": [media("gordon", n, "Gordon text G, printed article page" if n <= 10 else f"Gordon text G, plate {('XXII', 'XXIII', 'XXIV', 'XXV')[n - 11]}") for n in range(2, 15)],
            "claims": []}


def waller_row(pages):
    source, cap, sha = SOURCES["waller"]
    content = normalized(pages[10])
    if "BM 91711" not in content or "Arban" not in content:
        raise ValueError("Waller BM 91711 discussion not found on PDF p. 11")
    return {"source_id": source, "appearance": {"locator": appearance("waller")},
            "texts": [{"text_type": "summary", "language": "English", "content": content,
                       "editor": "Daniel Waller", "locator": "Waller, printed p. 13 / PDF p. 11, BM 91711 discussion and note 49",
                       "rights_status": "unknown", "public_ok": False,
                       "notes": f"Working full-page text-layer extract for private research. Waller reports an Arban entry in the BM accessions register but says Layard did not record finding a bowl there; this is not a verified findspot. Held PDF {cap}, SHA-256 {sha}."}],
            "media": [media("waller", 11, "Waller printed p. 13, BM 91711 discussion")],
            "claims": [{"field": "reported_findspot", "value_text": "BM accessions register reportedly names Arban, Syria; Waller notes that Layard did not document a bowl find there.",
                        "locator": "Waller, printed p. 13 and note 49", "certainty": "uncertain",
                        "notes": "Attribution to Waller's discussion of an accession-register statement; not an accepted archaeological provenance."}]}


def oim_row():
    source, cap, sha = SOURCES["oim"]
    return {"source_id": source, "appearance": {"locator": appearance("oim")},
            "texts": [{"text_type": "summary", "language": "English",
                       "content": "The Oriental Institute catalogue's highlight 27 illustrates OIM A32675, a painted clay incantation bowl recovered at the surface of Nippur. Its entry gives a height of 7.5 cm and diameter of 17.0 cm, places it broadly in the Sasanian to Early Islamic period, and describes its writing as pseudoscript. The catalogue supplies no inscription edition or translation for this object.",
                       "editor": "Incantation Bowl Index",
                       "locator": "Highlights of the Collections, highlight 27, printed p. 51 / PDF p. 52",
                       "rights_status": "unknown", "public_ok": False,
                       "notes": f"Project-authored factual summary read from the printed catalogue page. The PDF allows printing but disables text copying; no restricted prose layer was extracted. Held PDF {cap}, SHA-256 {sha}."}],
            "media": [media("oim", 52, "OIM highlight 27, OIM A32675 photograph and entry, printed p. 51; PDF permits printing")],
            "claims": [
                {"field": "reported_findspot", "value_text": "Nippur, surface; excavated under James Knudstad, 1964–1965", "locator": "highlight 27, printed p. 51", "certainty": "reported"},
                {"field": "reported_height", "value_text": "7.5 cm", "locator": "highlight 27, printed p. 51", "certainty": "reported"},
                {"field": "reported_diameter", "value_text": "17.0 cm", "locator": "highlight 27, printed p. 51", "certainty": "reported"},
                {"field": "reported_date", "value_text": "Sasanian to Early Islamic periods, AD 500–800", "locator": "highlight 27, printed p. 51", "certainty": "reported"},
                {"field": "catalogue_script", "value_text": "pseudoscript", "locator": "highlight 27, printed p. 51", "certainty": "reported"}]}


def main():
    ap = argparse.ArgumentParser()
    for key, count in (("gordon", 14), ("waller", 45), ("oim", 153)):
        ap.add_argument(f"--{key}-pdf", type=Path, required=True)
        ap.add_argument(f"--{key}-output", type=Path, required=True)
    args = ap.parse_args()
    rows = {
        "gordon": gordon_row(verified_pdf(args.gordon_pdf, "gordon", 14)),
        "waller": waller_row(verified_pdf(args.waller_pdf, "waller", 45)),
    }
    verified_pdf(args.oim_pdf, "oim", 153)
    rows["oim"] = oim_row()
    for key, row in rows.items():
        dest = getattr(args, f"{key}_output")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"source": key, "texts": len(row["texts"]),
                          "page_links": len(row["media"]), "claims": len(row["claims"])}))


if __name__ == "__main__":
    main()
