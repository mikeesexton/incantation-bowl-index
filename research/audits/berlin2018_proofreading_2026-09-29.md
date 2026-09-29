# Berlin 2018 page proofing — 29 September 2026

**Agent:** Claude · **Task:** TEXT-004 · **Source:** Bhayro et al., *Aramaic Magic Bowls in the Vorderasiatisches Museum in Berlin: Descriptive List and Edition of Selected Texts* (2018), `SRC-DA708912C2D3`, capture `CAP-DBB06BEA4670`.

This note contains no protected text. The corrected texts and both manifests are in `data/private/`. Git holds only the receipts.

## Result

All 30 edition rows are now `reading_text_checked`: the numbered transliteration and the translation of each of the 15 selected-text editions. Each was rebuilt and compared with the rendered pages. The catalogue summary rows (187) are not edition text and were not in scope. The manifest fingerprints matched the pre-session snapshot.

| Private manifest | Rows | Receipt |
|---|---:|---|
| `berlin2018_claude_transliteration_proofreading_2026-09-29.json` | 15 | `research/receipts/berlin2018_claude_transliteration_proofreading_2026-09-29.json` |
| `berlin2018_claude_translation_proofreading_2026-09-29.json` | 15 | `research/receipts/berlin2018_claude_translation_proofreading_2026-09-29.json` |

## Method

`scripts/stage_berlin2018_editions.py` is a staging aid only.

- **Page offset.** The PDF page is the printed page + 14.
- **Block boundaries.** Each edition prints a numbered transliteration and then a numbered TRANSLATION. The script starts at the first line numbered 1 and keeps a part heading printed just before it. That heading may be:
  - a fragment label such as "a VA.2439";
  - a Roman section numeral;
  - a position phrase such as "Above the figure, perpendicular to the rim:".
- **Fragmentary editions.** Some editions repeat the transliteration/translation pair for each fragment (Edition 9). All transliterations go to the transliteration row and all translations to the translation row. Fragment labels are kept only where they are printed.
- **Composite text.** Edition 10 prints three fragments and then a composite text. The transliteration row keeps all four, as printed; the translation is of the composite.
- **Footnotes.** Footnote text is dropped, and so are footnote reference numerals, which are recognized by their narrow superscript width. The earlier extraction had mixed footnotes into ten rows; for example, Edition 12's translation carried a 900-character note.
- **Grey shading.** The edition marks "unclear letters" with grey shading, drawn as translucent 10 pt strokes. These letters are enclosed in ⸢ ⸣.
- **Small insertions.** Small raised insertions are enclosed in ⸌ ⸍ and small lowered ones in ⸜ ⸝. Examples:
  - Edition 2, line 17 (lowered);
  - Edition 3, line 5 (lowered);
  - Edition 4, line 6 (raised);
  - Edition 11, line 17 (raised).
- **Printed signs.** The edition's own signs are kept as printed: `^x^`, `//`, `:` for seyame, `< >`, `{ }` and `|` separators.
- **Spacing.** The text layer lays space glyphs over the next letter after some hyphens and footnote marks. Such a space is dropped only when it overlaps a letter by more than 70%, because tightly justified lines have smaller overlaps that are real word spaces.
- **Line-end hyphens.** In the transliteration, a hyphen at the end of a line is removed where the word continues. In the translation, a hyphen before a capital letter is kept (Farrokh-Khusraw).

## Not done

- No public reuse was decided, and no reading was interpreted.
- The translation rows of multi-fragment editions do not carry fragment labels, because the print does not repeat them there.
