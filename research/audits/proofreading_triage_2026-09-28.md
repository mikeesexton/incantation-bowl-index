# Proofreading triage for Mike Access

The scan-review ledger measures **exact text fidelity for stored rows**, not overall research completeness. On 28 September 2026 it has 55 checked, two partial, and 640 unreviewed edition-text rows (697 total). These are counts of translation, transcription, and transliteration *rows*, not distinct bowls or independent passages. The queue also excludes inscriptions that have not yet been extracted into a structured row. The 654 other stored text rows include source extracts and summaries, which need different checks. Therefore `55/697` must not be presented as a percentage of the whole project finished.

## Three outcomes, with different proofing costs

1. **Private discovery:** A lawfully held working text can be searchable in Mike Access with its source, page, rights state, and a clear working/OCR warning. Page-by-page collation is not a prerequisite for Mike's private search. All 1,351 stored private text rows are in the local Mike Access build; that count says nothing about completeness of the source's editions.
2. **Reliable structured extraction:** Before treating a source's split translation/transcription columns as reliable across the batch, check a small, deliberately varied sample against the PDF. Record which extraction method was tested and every failure. If a sample exposes a wrong bowl boundary, omitted passage, mixed column, changed letter order, or lost restoration mark, repair that method and inspect every affected row or segment. A passing sample does **not** mark uninspected rows `reading_text_checked`.
3. **Exact quotation or release:** Proof the particular row and page span in full, including names, damaged letters, lacunae, and editorial brackets, before exact quotation or a publication decision. Rights review is separate. Only this outcome gets a completed proofreading-ledger status.

## Risk-ranked work order

| Priority | Work | Reason and stopping rule |
|---|---|---|
| 1 | Recover **missing structured inscription readings** where the PDF's original-script encoding is corrupt: especially Jena's four Mandaic editions and Pognon's Mandaic editions. | These are extraction gaps, not merely unreviewed rows. Retained facsimiles help Mike now, but do not make the inscription searchable. Index a reading only after image-based checking, with source and uncertainty. |
| 2 | Audit methods known to scramble structure: Levene's interleaved English/Hebrew columns (60 edition rows), Moriggi's two-column text (98), Jena's split sections (71), and Pognon's scan OCR French translations (31). | Sample first, middle, last, damaged, and multi-page examples per source/method where available. Any critical mismatch triggers a batch repair and affected-row review. Preserve the full source section as a fallback. |
| 3 | Audit the large born-digital edition batches: the two *Aramaic Bowl Spells* volumes (238 rows), Burberry (51), and the Berlin selected editions (30). | Sample distinct layouts and both translation and original-language fields. If the samples pass, retain remaining rows as attributed working extracts; proof exact rows when used. Failure triggers method repair and targeted full checks. |
| 4 | Finish small scan-OCR or manually keyed groups when their pages are already open: Gordon H (partial), Ellis 1/2/4, Schwab N, Stübe's three German rows, Ford's three English rows. | These are exposed to missing gaps and OCR words, but collectively have far fewer rows. Full page checks are cheap after source setup. |
| 5 | Review the 654 other stored text rows by their purpose: source-section extracts for completeness and boundaries; project-authored summaries for factual provenance. | Do not force a translation-proofreading status onto a catalogue extract or summary. Prioritize rows that support a current claim or answer. |

Six sources account for **518 of the 640 unreviewed edition rows**: both *Aramaic Bowl Spells* volumes, Moriggi, Jena, Levene, and Burberry. Their source-level method audits have more leverage than continuing a row-by-row march through whichever page is easiest.

## First triage milestone

Audit five varied row/page pairs for each of those six large sources (about 30 pairs), recording the exact selection, extraction method, discrepancies, and decision in a content-free audit. Include original-language and translation rows wherever both exist. If a cohort fails, fix the extractor or segmentation and review the affected rows; if it passes, stop batch-wide manual proofing until a row is needed for an exact quotation or another source-specific problem appears. Run a separate extraction inventory for the missing original-script rows. The individual ledger remains the authority for which texts were actually page-checked.
