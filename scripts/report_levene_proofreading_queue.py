"""Write a content-free Levene row queue from the current private corpus."""

import csv
import re
from pathlib import Path

from bowl_index.db import connect
from bowl_index.proofreading import current_text_reviews


SOURCE = "SRC-F2BEFBEFFC2E"
OUT = Path("research/audits/levene_proofreading_queue_2026-09-28.csv")
LOCATOR = re.compile(r"^Edited section (.*?), printed pp\. (\d+)–(\d+)")


def main():
    conn = connect()
    reviews = current_text_reviews(conn)
    pairs = {}
    rows = conn.execute(
        "SELECT id,text_type,locator,content FROM texts "
        "WHERE source_id=? AND text_type IN ('translation','transcription')",
        (SOURCE,),
    ).fetchall()
    for row in rows:
        match = LOCATOR.search(row["locator"])
        if not match:
            raise ValueError(f"unexpected Levene locator on {row['id']}")
        key = (match[1], int(match[2]), int(match[3]))
        pairs.setdefault(key, {})[row["text_type"]] = row
    if len(pairs) != 30 or any(set(pair) != {"translation", "transcription"} for pair in pairs.values()):
        raise ValueError("Levene edition pairs incomplete")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "entry", "printed_pages", "pdf_pages", "translation_id", "translation_review",
            "translation_hebrew_characters", "translation_preface", "transcription_id",
            "transcription_review", "transcription_hebrew_word_spaces",
        ])
        for (name, first, last), pair in sorted(pairs.items(), key=lambda item: item[0][1]):
            translation, transcription = pair["translation"], pair["transcription"]
            writer.writerow([
                name, f"{first}–{last}", f"{first + 14}–{last + 14}",
                translation["id"], reviews[translation["id"]]["status"] if translation["id"] in reviews else "unreviewed",
                len(re.findall(r"[\u0590-\u05ff]", translation["content"])),
                "yes" if "The readings given here are based" in translation["content"] else "no",
                transcription["id"], reviews[transcription["id"]]["status"] if transcription["id"] in reviews else "unreviewed",
                len(re.findall(r"(?<=[\u0590-\u05ff]) (?=[\u0590-\u05ff])", transcription["content"])),
            ])
    print(f"{OUT}: {len(pairs)} entries, {len(rows)} private edition rows")


if __name__ == "__main__":
    main()
