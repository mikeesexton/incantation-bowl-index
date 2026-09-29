# Aramaic Bowl Spells page proofing — 29 September 2026

**Agent:** Claude · **Task:** TEXT-004 · **Sources:** Shaked, Ford and Bhayro 2013,
*Aramaic Bowl Spells* vol. 1 (`SRC-7FBBB775E502`, capture `CAP-295A7FE7BF01`) and
Ford, Bhayro and Shaked 2022, vol. 2 (`SRC-8C611BF93288`, capture
`CAP-DE113C20CBBA`).

This note is content-free. The corrected texts and the four manifests are under
`data/private/`; Git holds only the receipts listed below.

## Result

All 238 edition rows of the two volumes, the Hebrew-script column and the English
translation of JBA 1–119, were rebuilt and compared line by line with the rendered
pages. All are recorded `reading_text_checked`. Vol. 1 has 128 rows (64 entries)
and vol. 2 has 110 (55 entries).

| Manifest (private) | Rows | Receipt |
|---|---:|---|
| `abs1_claude_hebrew_proofreading_2026-09-29.json` | 64 | `research/receipts/abs1_claude_hebrew_proofreading_2026-09-29.json` |
| `abs1_claude_english_proofreading_2026-09-29.json` | 64 | `research/receipts/abs1_claude_english_proofreading_2026-09-29.json` |
| `abs2_claude_hebrew_proofreading_2026-09-29.json` | 55 | `research/receipts/abs2_claude_hebrew_proofreading_2026-09-29.json` |
| `abs2_claude_english_proofreading_2026-09-29.json` | 55 | `research/receipts/abs2_claude_english_proofreading_2026-09-29.json` |

Every manifest entry's expected fingerprint was taken from a pre-session snapshot,
and the ingest confirmed that none of the rows had changed in the meantime.

## Method

`scripts/stage_abs_edition_columns.py` stages both columns of each entry from PDF
glyph positions. It is a staging aid: every staged row was then compared with the
rendered page before a manifest entry was written. The vol. 1 PDF page is the
printed page + 28, and vol. 2 is printed + 20. Body sizes are Hebrew 9.1 / Latin
10.0 in vol. 1 and 10.3 / 11.0 in vol. 2.

- **Page span.** An entry is extended through following pages that carry numbered
  lines and no new "JBA n (" heading. Unnumbered lines at the head of a
  continuation page are attached to the line they continue.
- **Line numbers.** A number counts only at the page's median column x, which
  excludes footnote digits and figure labels. A printed gap in the numbering,
  such as a drawing label numbered after a jump, is kept as printed.
- **Block bounds.** A block stops at the footnote rule, at "Notes" or "Previous
  readings" headings, at text larger than 12.5 pt, and at italic footnote digits.
  Running heads and "Fig." captions are skipped.
- **Headings.** Printed section headings are kept as their own lines: "Outside:",
  "Main inscription:", "Central sections:", "In the centre:", "Inside the
  drawing:", "Alongside the drawing:", "Beneath the drawing:", "Above l. n:".

### Hebrew column

The Hebrew column is read right to left. Bracket orientation is taken from the
rendered glyph, because the text layer does not mirror it. Embedded Latin labels
such as "(magic characters)" are kept in reading order.

- **Editors' signs.** Kept as printed:
  - `[ ]`: missing or restored text
  - `[-]` / `[...]`: lacuna
  - `{ }`: superfluous letters
  - `⟨ ⟩`: scribal omission
  - U+05AF: partially preserved letter, already present in the text layer
- **ASCII angle brackets.** In two entries (JBA 99 and 106) the text layer uses
  ASCII `< >` for the omission sign. These are normalized to `⟨ ⟩`, and the entry's
  correction note records the change.
- **Added markers.** These show typography the text layer drops:
  - `⸌ ⸍`: small or raised type
  - U+0336: printed strikeout
  - U+0332: printed underline (only JBA 63, lines 2–3)
  - `⟦ ⟧`: printed box or frame
- **Printed spacing.** Spacing irregularities in the print, such as a missing word
  space in JBA 111 line 5 or a space before a brace group in JBA 116 line 1, are
  reproduced, not corrected. Both were confirmed on 400–500 dpi renders.

### English column

Printed wraps are joined. A line-end hyphen is removed only where the joined word
occurs in the same volume; otherwise the hyphen is kept with no space. This session
also fixed a stager bug that inserted a space after a hyphen following ṯ and
similar letters.

Small capitals (YHWH, YYYY, KYP, ʾHW, HH) are restored as capitals, detected by
normalized glyph widths in Roman, non-bold type. Small type is enclosed in
`⸌ ⸍`. Italics and bold, including the bold transliterated magic names, are not
represented.

- **Footnote numerals.** Footnote reference numerals are removed from both
  columns.

## Fixes found during review (stager, before ingest)

The first visual pass exposed these problems, all fixed before any row was
written:

- Continuation lines lost at page tops (JBA 99, printed p. 149).
- Running-head remnants (JBA 93, 98, 100, 114). These are now dropped.
- Spurious underlines from box top edges.
- Small-caps false positives in italic and small type.
- Footnote-digit line numbers.
- The hyphen-space join.

The replaced texts had many problems:

- "Unresolved in PDF extraction" placeholder lines, for example JBA 33, 41 and 112.
- Unspaced Hebrew.
- Missing sigla.
- Footnote leakage.

## Not done

- **Figure transcriptions.** Figure-only magic signs and drawings are represented
  only by the edition's own labels. Transcriptions printed inside figures, with
  no numbered line, were not added as new rows.
- **Other volumes and rows.** No locator repairs were made. No public reuse was
  decided. No reading was interpreted or adjudicated.
