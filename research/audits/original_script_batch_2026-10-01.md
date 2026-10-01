# Original-script extraction: first substantial batch — 1 October 2026

Mike authorized sustained original-script extraction from held sources. This first batch adds **20 source-specific Hebrew-script working transcriptions**, **170 numbered printed lines** and **12,921 characters**, from Montgomery 1913. All 20 have current **partial_review**, with exact printed/PDF-page pointers and unchanged source-page facsimiles. Zero full character-level checks or specialist certifications are claimed.

Montgomery now has working native-script text for **21 of its 40 main entries**, including the previous AIT27 lines 1–11 pilot. **19 entries remain without a working row**. Against the frozen nine-source, 99-appearance recovery/check worklist, **20 now have working rows and 79 await recovery**. All 20 still need full source collation; these numbers do not mean 20 fully proofread physical inscriptions. The 30 September worklist remains an unchanged historical baseline.

## Scope and editorial limits

The batch captures the bounded printed edition blocks, including Exterior portions for nos. 1, 12 and 13 and Montgomery’s separately printed witnesses 21–23. A printed block can contain lacunae or omit parts of the physical inscription. No parallel has been used silently to fill a witness. No new translation is generated.

Drafting combined manual visual transcription with locally processed Hebrew Tesseract 5.5.3 OCR (official tessdata_best Hebrew model). Raw OCR, the initial six manually keyed drafts, corrected draft files, rendered crops and exact source hashes are retained under the ignored private directory. OCR did not establish source readings: it misread consonants, numbers and source gaps, and missed the short Exterior line 13 of no. 12.

AI-assisted normalized consonant working transcription from Montgomery’s printed edition, visually compared with the held page image, not a diplomatic text or specialist certification. Printed inscription line numbers are retained; implicit opening line 1 is supplied by the project. Physical page wrapping and most typographic punctuation are normalized. Printed square brackets remain source restorations; ... normalizes printed loss runs without asserting a lost-letter count. ⟦word?⟧ is a project transcription doubt, not Montgomery’s restoration. ⸢word⸣ flags a recognized source-dotted uncertain word at word level; this first pass does NOT exhaustively encode or collate every inferior letter-dot or pointing mark. Exact uncertainty positions, diacritics, damaged passages, final letters and difficult words require full character-level source collation. The unchanged facsimile is authoritative for printed typography. No readings are silently supplied from parallel bowls; no translation or release decision is made.

No. 20’s brace places the invocation beside the two name lines. Its digital text puts the invocation on a separate unnumbered line, with an editorial dash, preserving the numbered five-line structure. No. 26 has Hebrew quotation material beside Aramaic wording and is labeled accordingly. Precise divine-name character counts require further collation. Source wording at no. 15 lines 4–5 remains an extended project doubt rather than a silently repaired sentence.

## Added source appearances

| Montgomery no. | Edition printed page | PDF page | Numbered lines | Stored text | Status |
|---|---:|---:|---:|---|---|
| 1 | 117 | 123 | 15 | `TXT-DB7EE3F0F524` | partial |
| 2 | 121 | 127 | 7 | `TXT-B3E117E7C76A` | partial |
| 10 | 165 | 171 | 7 | `TXT-7662F04E373F` | partial |
| 12 | 174 | 180 | 13 | `TXT-618B05B28A08` | partial |
| 13 | 178 | 184 | 12 | `TXT-8CCF16F0BDEE` | partial |
| 14 | 183 | 189 | 7 | `TXT-7F3508798F65` | partial |
| 15 | 185 | 191 | 9 | `TXT-23DA7F7A7A3B` | partial |
| 16 | 188 | 194 | 14 | `TXT-1A53F04B1B8D` | partial |
| 17 | 190 | 196 | 13 | `TXT-C4227E0C8605` | partial |
| 18 | 193 | 199 | 12 | `TXT-5E3D46D41FE7` | partial |
| 20 | 201 | 207 | 5 | `TXT-94810881E40B` | partial |
| 21 | 203 | 209 | 4 | `TXT-5C1B2110498F` | partial |
| 22 | 203 | 209 | 5 | `TXT-2AD343A4E286` | partial |
| 23 | 203 | 209 | 4 | `TXT-AB2E78F08206` | partial |
| 24 | 205 | 211 | 6 | `TXT-1EDCFF951B2E` | partial |
| 25 | 207 | 213 | 7 | `TXT-E5DB6B3A7C8D` | partial |
| 26 | 209 | 215 | 8 | `TXT-76D57DE9FCD0` | partial |
| 28 | 213 | 219 | 5 | `TXT-9B748691CB2A` | partial |
| 29 | 218 | 224 | 12 | `TXT-2093AEACB9E1` | partial |
| 30 | 221 | 227 | 5 | `TXT-BCECFE85E90E` | partial |

## Reproducibility and next pass

- Public-domain, attributed payload manifest: `research/enrichment/montgomery_original_script_batch_2026-10-01.jsonl`. All public_ok flags remain false.
- Evidence-bound partial-review manifest: `research/reviews/montgomery_original_script_batch_2026-10-01.json`. Each entry lists its unresolved concerns; original row snapshots are retained by the append-only ledger.
- A second visual pass corrected one omitted bet inside a tentative phrase in no.15 line5, through `research/reviews/montgomery_original_script_second_pass_2026-10-01.json`. There are twenty current partial reviews and twenty-one preserved review-history rows.
- Hash-bound source-page derivative manifest: `research/reviews/private_media_montgomery_originals_2026-10-01.json`. Images stay in the ignored private vault.
- Content-free, appearance-level progress companion: `research/audits/original_script_progress_2026-10-01.json`.
- First priority: complete the precise consonant/dot/restoration collation on these twenty rows, including project doubts and no.20 layout. Then recover the remaining Montgomery editions (long texts and Syriac/Mandaic scripts require separate handling); continue Stübe/Ford/Gordon/Ellis and Mandaic recovery under TEXT-009.
- AIT27’s later edition still needs a lawfully captured PDF. Existing ABS/Burberry/Jena/Levene native rows require completeness audits rather than duplicate imports.
- Capture, completed source-page review, linguistic interpretation and public release remain separate. No personal bowl-audit completion event is inferred from extraction.

## Import retry verification

Validation exposed a generic JSONL import bug after a content correction: an older draft could be recreated as a second current row. The importer now recognizes both before/after snapshots across metadata corrections and proofreading history, scoped to the exact source appearance, content, type and locator. Three regression checks cover original and intermediate draft retries, multiple revisions, and preserving another witness/new reading. The isolated batch was recovered to its verified pre-ingest SQLite backup and rebuilt through its manifests; the entire attempted database and manifests remain in the ignored private recovery archive. All pre-existing corpus tables were verified unchanged before recovery. The live corpus has exactly twenty added text rows, twenty media rows and twenty-one proofreading-history rows, with twenty current partial reviews.
