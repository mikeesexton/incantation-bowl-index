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
