# Moriggi 2014 page proofing (29 September 2026)

**Agent:** Claude
**Task:** TEXT-004
**Source:** Moriggi, *A Corpus of Syriac Incantation Bowls* (2014), source `SRC-3C4294DDB367`, capture `CAP-EA64131E5F1D`.

This note contains no protected text. The corrected texts and both manifests are in `data/private/`. Git keeps only the receipts listed below.

## Result

All 98 edition rows were rebuilt and compared with rendered pages, and all 98 are recorded as `reading_text_checked`. These are the Latin-script transliteration and the English translation of bowls 1–49. Each manifest's fingerprints came from a snapshot taken before the session, and the ingest confirmed that none of the rows had changed in the meantime.

| Private manifest | Rows | Receipt |
|---|---:|---|
| `moriggi_claude_transliteration_proofreading_2026-09-29.json` | 49 | `research/receipts/moriggi_claude_transliteration_proofreading_2026-09-29.json` |
| `moriggi_claude_english_proofreading_2026-09-29.json` | 49 | `research/receipts/moriggi_claude_english_proofreading_2026-09-29.json` |

## Method

`scripts/stage_moriggi_edition_columns.py` is a staging aid only; its output is not a review.

**Page layout**
- The PDF page number is the printed page number + 18.
- The edition prints the transliteration, a line-number column and the translation side by side.
- On each page the script takes the number column at the median x of its numerals. Ranges such as `1–4` and suffixed numbers such as `17a` or `1b` are accepted.

**Where an entry starts and stops**
- An entry starts after its bold "Bowl no. N" heading.
- It stops at "Notes to the text", at the next bowl heading, or at a footnote rule.
- A footnote rule is a 48 pt rule followed by small type.
- In bowl 47, rules of the same width sit under body text. They are printed underlining (Faraj's reading, reproduced by Moriggi) and are shown with U+0332.

**Lines and labels**
- Each numbered line is joined across its printed wraps.
- Unnumbered lines at the top of a page are attached to the line they continue.
- Roman-type headings are kept as their own lines. Examples:
  - "I cartouche" to "IV cartouche" (bowl 30)
  - fragment names (bowls 43 and 45)
  - "On the body of the figure …" (bowl 2)
- Word labels printed in the number column ("External surface", bowls 18 and 25) are kept.

**Combining marks**
- The marks are seyame (U+0308, 492 in the output), dot above, caron and dot below.
- The text layer stores each mark as a zero-width glyph and often places it after the next letter, and even after a bracket or comma.
- Each mark is therefore attached to the letter it is drawn over, using the mark's x position minus 0.15 × font size.
- For 128 marks in the edition blocks, attachment by position and attachment by text order give different letters. All 128 were compared on 400 dpi crops, and every one matched the printed placement. Examples:
  - *brqʾ̈ brq̈ʾ*
  - *byš̈ʾ byšʾ̈*
  - *l[ḥddʾ̈]*
- Where the two methods agree, the mark was not checked separately.

**Word spacing and normalization**
- Word spaces come from gaps between glyphs.
- The stored rows had lost the spaces around marks.
- Output is normalized to NFC.

**English column**
- Line-end hyphens are removed only where the joined word occurs in the book.
- Italics are not represented.

## What changed

**Transliterations**
- A line number now starts each line; it used to sit at the end.
- Printed wraps are joined.
- Word divisions around marks are restored.
- Headings and number-column labels are placed as printed.

**Translations**
- Line numbers were added; the earlier extraction had none.
- Headings were restored.
- Words dropped by the earlier extraction were restored in 21 bowls. They were usually the last word of a numbered section, e.g. "ever.", "dreams.", "goddesses.", "selah.".
- Bowl 47's last two lines, lost at the underlining, were restored in both columns.

## Not done

- **Jena Syriac rows:** the six rows in Ford and Morgenstern 2020 are still partial. The same position-based method could close them; the next session should apply it there.
- **Reuse and interpretation:** no public reuse was decided, and no reading was interpreted.
