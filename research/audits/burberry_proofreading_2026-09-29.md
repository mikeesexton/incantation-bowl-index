# Burberry 2020 page proofing — 29 September 2026

**Agent:** Claude · **Task:** TEXT-004 · **Source:** Burberry, *Edition and Analysis of Twenty-Five Unpublished Aramaic Magic Bowl Texts in the Collection of the Vorderasiatisches Museum (Berlin)* (Exeter PhD thesis, 2020), `SRC-53B93C8C8A0E`, capture `CAP-FEA23FB9B4F1`.

This note contains no protected text. The corrected texts and both manifests are under `data/private/`, and Git holds only the receipts.

## Result

All 50 edition rows that had no current review were rebuilt and compared with rendered pages, and all are now `reading_text_checked`:

- 26 Hebrew-script transcriptions, covering ACB 1–25 with fragments A and B of ACB 19 as separate rows.
- 24 English translations. ACB 25 has no translation row.

ACB 24's translation was already checked on 28 September and was not touched, so the source now stands at 51/51 checked. For every entry, the manifest's expected fingerprints matched the pre-session snapshot.

| Private manifest | Rows | Receipt |
|---|---:|---|
| `burberry_claude_hebrew_proofreading_2026-09-29.json` | 26 | `research/receipts/burberry_claude_hebrew_proofreading_2026-09-29.json` |
| `burberry_claude_english_proofreading_2026-09-29.json` | 24 | `research/receipts/burberry_claude_english_proofreading_2026-09-29.json` |

## Method

`scripts/stage_burberry_edition_columns.py` stages the text; it is a staging aid only. The PDF page number equals the printed page number. Each bowl's text follows an italic "Text" heading and ends at italic "Notes" or "Commentary". On each page, the columns are split at the median x of the line numbers.

- **Hebrew order and spacing.** Hebrew is ordered right to left. The Word text layer also lays space glyphs over some final letters, which split some words before their final letter, so a space that overlaps a letter is dropped.
- **Bracket orientation.** Orientation is read from the rendered glyph in both columns, because the text layer's bracket codes are sometimes reversed, even in English. The test uses a slant-safe tick comparison for square brackets and a shape test for parentheses and braces. The classification was checked on a sample of 66 rendered brackets, including italic ones, and all were correct. Many stored rows had reversed brackets, such as `]---[`, and these are fixed.
- **Thesis sigla.** The printed signs are marked as follows:
  - Grey highlight ("text partially visible") becomes U+05AF after each letter.
  - A cartouche box becomes ⟦ ⟧; it is built from its four rules. ACB 11, 14 and 21 have boxes, and ACB 21 has boxes in both columns.
  - Crossed-out text becomes U+0336 (ACB 12, 13 and 16).
  - Small raised Hebrew insertions become ⸌ ⸍.
  - `[-]`, `[---]`, `{ }` and `(!)` are kept as printed. Printed spacing irregularities, such as a space inside a bracketed name, are also kept.
- **Line wraps.** A wrap after a hyphen is joined without a space, since Word breaks inside `[---]`. An English wrap before a capital keeps its hyphen, as in *Bat-Šabbetay*.
- **Italic English lines.** Some English lines are wholly italic, such as the Shema in ACB 16–18. They are kept as translation text and are not treated as headings.
- **Footnote numerals.** These are dropped.

## What changed

- **Hebrew rows:** bracket orientation fixed; highlights, cartouches, strikeouts and raised insertions now shown; words split by stray spaces rejoined; page markers added.
- **English rows:** the earlier `[[printed page N]]` artefacts and line numbers embedded mid-line are removed. Wraps are rejoined, and words the earlier extraction had dropped at section ends are restored, for example in ACB 11, 12 and 16.

## Not done

- No public reuse was decided, and no reading was interpreted.
- ACB 25 has no English row, and none was created, because modelling it is not a proofreading task.
