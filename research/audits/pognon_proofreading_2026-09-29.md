# Pognon 1898 page proofing — 29 September 2026

**Agent:** Claude · **Task:** TEXT-004 · **Source:** Pognon, *Inscriptions mandaïtes des coupes de Khouabir* (1898), `SRC-E7D5F020B31C`, capture `CAP-EED4A3FE59EC`.

This note contains no protected text. The corrected texts, the OCR specs and the manifest are under `data/private/`, and Git holds only the receipt.

## Result

All 31 French translation rows (Nos. 1–31) were rebuilt, compared with the page images and ingested as `reading_text_checked`. The manifest's expected fingerprints matched the pre-session snapshot for every entry.

| Private manifest | Rows | Receipt |
|---|---:|---|
| `pognon_claude_french_proofreading_2026-09-29.json` | 31 | `research/receipts/pognon_claude_french_proofreading_2026-09-29.json` |

## Method

The scan has no usable text layer. Each page was rendered at 300 dpi in grey and read with Tesseract (French). The PDF page is the printed page + 11.

`scripts/stage_pognon_ocr.py` is a staging aid only. It assembles each translation from explicit TSV line ranges and records a crop of every line it uses. The drafts were then read line by line against those crops, and every OCR misreading was corrected against the image. The corrections are recorded as exact pairs in the private spec file, and each one must match the draft. Typical misreadings were:

- `Hs` for *Ils*;
- `el` for *et*;
- `ete.` for *etc.*;
- a lost circumflex or tréma;
- running heads and footnote numerals read into the text.

The reading text follows these rules:

- **Headings.** The printed location headings, such as the headings for the interior and exterior inscriptions, are kept.
- **Exterior legends.** Where a legend's translation is given inline in «…», it is included. No. 27's exterior legend is printed without a translation, so no exterior text is included for it.
- **Footnotes.** Footnotes and footnote reference numerals, such as `(1)`, are omitted.
- **Printed signs.** The editor's own question marks after doubtful words are kept, and so is *(sic)*.
- **Gaps.** Dot leaders marking gaps become ` … `.
- **Punctuation.** Spacing is modernized, with no space before `; : ! ?`, and apostrophes are typographic.
- **Line-end hyphens.** A hyphen at the end of a line is removed where the word continues, including across a page break. Hyphens inside names and transliterated magic words are kept.
- **Page markers.** These give the PDF page and the printed page.

## What changed

- The stored rows were raw OCR with spaced punctuation, broken hyphenation and misreadings, and these are now corrected.
- No. 5's stored row lacked the translation of the exterior inscription; it is now included.
- No. 10 omits the editor's lead-in sentence introducing the literal translation.
- No. 30's interior translation is fragmentary. It keeps the editor's line references (l. 2 to l. 9) and gaps.

## Not done

- No public reuse was decided, and no reading was interpreted. The Mandaic transliterations and original-script text were not in scope.
