# Levene Hebrew and translation page checks — 28 September 2026

**Source:** Levene 2013, held private PDF SHA-256 `d4b2c6e2946e10ab295d5b45a7ce2b132b674e35da40c09e1818a8af53d92a3d`. The book remains in the private vault; no protected reading text is committed. The [content-free receipt](../receipts/levene_five_entries_proofreading_2026-09-28.json) binds the two private manifests and seven corrected files to this capture and their exact source pages.

The [glyph-position extractor](../../scripts/extract_levene_hebrew_geometry.py) reads Hebrew glyphs from the right-hand edition column in visual right-to-left order. A measured glyph gap above 1.4 PDF points restores word boundaries; the text layer itself has almost none. It also normalizes reversed numeric line-marker parentheses. Each call is bounded to the reading's visible vertical span; it is a staging aid, never an automatic `reading_text_checked` decision. I compared the selected output against rendered pp. 116 and 133. The private earlier text remains in the append-only proofreading ledger.

| Entry | PDF / printed page | Translation | Hebrew transcription | Finding |
|---|---:|---|---|---|
| 024A (BM 91760) | 130 / 116 | Checked | Checked | Removed a prefatory editorial sentence from the English reading and reversed Hebrew leaked after its ending. Rebuilt 15 Hebrew lines with word spaces and restored the final Hebrew “Amen” line, absent from the working row. |
| YBC 2393 | 147 / 133 | Checked | **Partial** | Removed reversed Hebrew leaked after the English ending. Rebuilt the Hebrew line sequence and restored its closing line. Two editorial punctuation/restoration sequences in the Hebrew remain uncertain; this row is explicitly *not* fully checked. |
| N&Sh B6 | 138 / 124 | Checked | Unreviewed | Removed reversed Hebrew leaked after the English ending. |
| N&Sh B7 | 139 / 125 | Checked | Unreviewed | Restored printed line 5, an untranslated transliteration that the automatic language split dropped from the English column; removed reversed Hebrew leaked after the ending. |
| N&Sh B23 | 144 / 130 | Checked | Unreviewed | Removed reversed Hebrew leaked after the English ending. |

The source-level check found Hebrew characters in 16 of Levene's 30 stored English-translation rows before this batch. Some are legitimate references or transliterations inside English prose; several are clear right-column leakage. These five rows were individually compared and corrected. The remaining rows require page-specific review rather than a blanket deletion of Hebrew characters. Twenty-eight of Levene's 30 Hebrew rows still have no completed or partial ledger review (one checked, one partial). The PDF's full private section remains available alongside every working extract in Mike Access.

Across all sources, the edition-row ledger is now **62 checked, three partial, 632 unreviewed out of 697**. This is exact row-review coverage, not a measure of source acquisition or total inscription completeness.

## Continuation and handoff

The next bounded page check inspected 005A on PDF pp. 128–129 and 043A on p. 137. In 005A, the English row had included a prefatory editorial sentence and three footnote lines, plus a malformed line marker and joined word; the corrected translation is fully checked. In 043A, the English row had included a prefatory sentence and Hebrew from the adjacent column, and had lost opening parentheses on several line markers. It is **partial** because the source strikes through the first “rebuke” in line 14 and the normalized row does not yet express that typography. The [content-free receipt](../receipts/levene_005A_043A_proofreading_2026-09-28.json) identifies both rows and their private manifest. YBC 2393 Hebrew also remains partial. The current ledger is **63 checked, four partial, 630 unreviewed** out of 697. See the [Claude handoff](claude_proofreading_handoff_2026-09-28.md) for the exact next rows and workflow.

## Claude continuation — all but the joint VA.2496/VA.2575 Hebrew

Claude compared 51 further Levene rows with rendered pages of the same held PDF and ingested them through two private manifests, bound by content-free receipts for the [English](../receipts/levene_claude_english_proofreading_2026-09-28.json) and [Hebrew](../receipts/levene_claude_hebrew_proofreading_2026-09-28.json) batches. Every row is now `reading_text_checked` except the two joint Hebrew rows noted below.

- **Both partial reviews are closed.** 043A English now represents the printed strikeout of the first “rebuke” in line 14 with a U+0336 combining overlay. In YBC 2393 Hebrew the two uncertain sequences are printed exactly as caret–dot–caret between letters and as a curly-brace deletion; the stored brace orientation was reversed and is corrected. The editor's signs are reproduced, not interpreted.
- **English (24 rows).** Removed editorial prefaces (039A, 040A, 041A, Royal Ontario Museum 907.1.1), footnote text and reference numerals, column headings and adjacent-column Hebrew; repaired truncated line markers and joined words; restored omitted lines or ellipses in VA.2484, VA.2509, VA.2424, VA.3382, VA.3381 and VA.2418. Isbell 22 and VA.2492 needed no change. The single joint translation of VA.2496 and VA.2575 is retained for both bowls. Printed omissions of line markers (VA.2416 line 9, VA.2484 line 21, VA.2509 line 3) and a printed typo are kept as printed.
- **Hebrew (27 rows).** Rebuilt every remaining reading from glyph positions and compared each line, line marker and editorial sign with the rendered page. Printed strikeouts in 005A, 040A, 043A, N&Sh B6 and M102 are represented with the combining overlay. VA.3382 regained nine yods that are typeset in a fallback font and had been dropped. VA.3381 had interleaved Levene's reading with the parallel AIT 12 column printed beside it; only Levene's VA.3381 column is kept. Footnote reference numerals (VA.2423) were removed.
- **Extractor.** [`extract_levene_hebrew_geometry.py`](../../scripts/extract_levene_hebrew_geometry.py) now mirrors paired signs, keeps embedded left-to-right runs in reading order, marks ruled strikeouts, merges raised marks and fallback-font glyphs into their lines, and accepts `--x-min/--x-max` for multi-column pages. It remains a staging aid, never a review.

**Not done, deliberately.** VA.2496 `TXT-5DBC54A45B0E` and VA.2575 `TXT-B1508DB0C989` Hebrew (PDF pp. 78–79) stay unreviewed. Both rows hold the same merged text, but the printed edition gives each bowl its own Hebrew column under one joint translation. Splitting them would change how the joint section is modelled, which the handoff reserves; Mike or Codex should decide whether each row should carry only its own column.

Levene is now **58 checked, 0 partial, 2 unreviewed** of 60 rows. Across all sources the ledger is **114 checked, 2 partial, 581 unreviewed out of 697** edition rows.

