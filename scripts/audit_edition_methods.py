"""Content-free, reproducible screen of selected private edition rows.

This compares normalized 12-character windows with the held PDF text layer.
It is a triage signal, never a page proof or a proofreading-ledger review.
"""

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

from bowl_index.db import connect


SAMPLES = [
    ("ABS1", "SRC-7FBBB775E502", "39a8763373010f4703576f8917df901f4e170153c5014f5b344e60bb4775af9c", 28,
     ["JBA 1,", "JBA 32,", "JBA 64,"]),
    ("ABS2", "SRC-8C611BF93288", "e15f96f25da902065ea972aacb441034f99ca08fbdcdff73be5b11cc80fc3b00", 20,
     ["JBA 65,", "JBA 92,", "JBA 119,"]),
    ("Moriggi", "SRC-3C4294DDB367", "ce32170d182d4282a9610d42c2c6449b0435eba77851b18aa919544ddb4e5035", 18,
     ["Bowl no. 1,", "Bowl no. 25,", "Bowl no. 49,"]),
    ("Jena", "SRC-8A145FAA2EBB", "23431f46510c5cf729ca35282413e0bedd21be44dbc80e56dcde7c709b9a99d4", 24,
     ["Entry 1,", "Entry 20,", "Entry 36 "]),
    ("Levene", "SRC-F2BEFBEFFC2E", "d4b2c6e2946e10ab295d5b45a7ce2b132b674e35da40c09e1818a8af53d92a3d", 14,
     ["Edited section VA.2484,", "Edited section M102,", "Edited section YBC 2393,"]),
    ("Burberry", "SRC-53B93C8C8A0E", "63637559c176da93f3d20e346f9db17533573988f749f5cfabaf88e453119fbe", 0,
     ["ACB 1,", "ACB 13,", "ACB 24,"]),
]


def normalize(value):
    decomposed = unicodedata.normalize("NFKD", value).lower()
    return "".join(c for c in decomposed if c.isalnum() and not unicodedata.combining(c))


def window_coverage(content, page_text, width=12):
    row = normalize(content)
    page = normalize(page_text)
    windows = [row[i:i + width] for i in range(0, len(row) - width + 1, width)]
    return sum(window in page for window in windows), len(windows)


def main():
    archive = Path("data/private/archive/sha256")
    conn = connect()
    result = {"method": "normalized 12-character non-overlapping window presence in cited PDF text-layer pages",
              "meaning": "screen only; not visual collation or an individual proofreading review",
              "sources": []}
    for label, source_id, digest, offset, needles in SAMPLES:
        path = archive / digest[:2] / digest
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"source capture changed: {label}")
        pdf = PdfReader(path)
        sample = {"label": label, "source_id": source_id, "capture_sha256": digest, "entries": []}
        for needle in needles:
            rows = conn.execute(
                "SELECT id, text_type, locator, content FROM texts "
                "WHERE source_id=? AND locator LIKE ? "
                "AND text_type IN ('translation','transcription','transliteration') ORDER BY text_type",
                (source_id, needle + "%"),
            ).fetchall()
            if len(rows) != 2:
                raise ValueError(f"expected two edition rows: {label} {needle}; got {len(rows)}")
            match = re.search(r"printed pp?\. (\d+)(?:[–-](\d+))?", rows[0]["locator"])
            if not match:
                raise ValueError(f"no page range: {rows[0]['locator']}")
            first = int(match[1]) + offset
            last = int(match[2] or match[1]) + offset
            page_text = "\n".join(pdf.pages[p - 1].extract_text() or "" for p in range(first, last + 1))
            entry = {"locator": rows[0]["locator"], "pdf_pages": [first, last], "rows": []}
            for row in rows:
                found, total = window_coverage(row["content"], page_text)
                entry["rows"].append({"id": row["id"], "text_type": row["text_type"],
                                      "windows_found": found, "windows_total": total,
                                      "content_sha256": hashlib.sha256(row["content"].encode()).hexdigest()})
            sample["entries"].append(entry)
        result["sources"].append(sample)
    output = Path("research/audits/proofreading_method_screen_2026-09-28.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"screened {sum(len(x['entries']) for x in result['sources'])} entries / "
          f"{sum(len(e['rows']) for x in result['sources'] for e in x['entries'])} text rows; wrote {output}")


if __name__ == "__main__":
    main()
