# Jena edition columns proofed against rendered pages — 28 September 2026

**Source:** Ford and Morgenstern 2020, *Aramaic Incantation Bowls in Museum Collections, Volume One: The Frau Professor Hilprecht Collection* (`SRC-8A145FAA2EBB`), held private PDF SHA-256 `23431f46510c5cf729ca35282413e0bedd21be44dbc80e56dcde7c709b9a99d4`, PDF page = printed page + 24. No protected text is committed. Content-free receipts for the [English](../receipts/jena_claude_english_proofreading_2026-09-28.json) and [original-script](../receipts/jena_claude_original_script_proofreading_2026-09-28.json) batches bind two private manifests and 71 corrected files to this capture.

## Result

All 71 Jena edition rows now have a current review: **65 checked, 6 partial, 0 unreviewed.** The 36 English translations and the 29 Hebrew-script transcriptions are `reading_text_checked`. The six Syriac/Manichaean transcriptions (entries 31–36) are `partial_review`: their letters, word division, brackets and grey letters were collated, but the placement of seyame and other Syriac combining dots was assigned from glyph geometry and not collated mark by mark.

## Method

[`stage_jena_edition_columns.py`](../../scripts/stage_jena_edition_columns.py) stages each entry from glyph positions: original script read right to left, each printed line number starting a line, wraps joined. Every row was then compared with rendered pages. Conventions in the corrected rows follow the book's sigla (p. xxiii), with two additions for signs a plain-text row cannot show typographically:

- a letter printed **grey** ("partially preserved") is followed by U+0323 COMBINING DOT BELOW;
- a small **raised** letter is enclosed in ⸌ ⸍.

Footnote reference numerals are omitted; printed page markers and section headings (such as "Outside parallel to rim (as label):" or the roman column numbers of entry 37) are kept. Italic and bold type in translations is not represented.

## What the working rows had wrong

- **Brackets and sigla were reversed or lost** throughout the Hebrew rows: the text layer does not mirror paired signs in right-to-left lines, so the working extraction printed a restoration bracket pair as two opening or two closing brackets. The stager reads bracket orientation from the rendered glyph. The English working rows also had mirrored angle brackets (⟩of vats⟨).
- **Grey letters were invisible.** The working text carried no trace of the editors' "partially preserved" letters (1,385 grey glyphs across the edition pages).
- **Entry 20** had the damage the method audit found: a stray opening fragment and mangled restoration signs. It is now clean.
- **Syriac rows** had mis-joined seyame, spaces inside brackets and interleaved fragments.
- **Missing lines.** Entry 25's reading continues on printed p. 132 (lines 4–8); entry 28's composite text continues on p. 143 (lines 3′–7′); entry 40's translation has an eighth line on p. 205. All three are restored. The `locator` fields of these rows still name the shorter page span; correcting a locator needs a separate manifest type and is left for Codex.
- Footnote numerals were fused into words in many rows; line-wrap hyphens split words in translations.

## Not done

- **Entry 16** prints an English translation (Deut 6 and 11) that has no translation row; entries 4, 21 and 27 have none printed. Adding a row is an extraction task, not proofreading.
- **Entry 28's** fragment-by-fragment transcriptions (fragments a–d, p. 142) are not in the row, which holds the edited composite text.
- The **four Mandaic originals** (entries 37–40) remain unextracted; only their translations are rows. The PDF substitutes glyphs in the Mandaic font.
- The p. 133 fragment edited within entry 25's commentary (HS 3069 joined to HS 3046) is not a row.
