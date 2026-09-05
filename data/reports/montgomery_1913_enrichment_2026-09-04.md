# Montgomery 1913 text and concordance enrichment

## Outcome

- Extracted **35 English translation blocks** from James A. Montgomery's public-domain *Aramaic Incantation Texts from Nippur* (1913).
- Linked Montgomery texts 19, 28, and 40 to current Penn Museum objects B16018, B2972, and B2971 respectively.
- Resolved the false text 28/text 40 duplicate caused by the book's closing register.
- Reduced the corpus estimate from 1,319 to **1,316 probable physical identities** through three new reviewed concordances.
- Increased identity-level translation coverage from 14 to **48 identities** (3.6%).

## Translation scope and QA

The parser found all 40 numbered bowl headings. Montgomery supplies separate English translations for 35: texts 1–17, 19–20, 22, 24–26, 28–32, and 34–40. It does not supply separate translations for texts 18, 21, 23, 27, or 33. The parallel block following texts 21–23 is explicitly labelled as the translation of text 22.

The embedded OCR was checked against rendered pages from each major language group:

- Jewish Babylonian Aramaic: text 1, printed p. 117 / PDF p. 123.
- Syriac: text 31, printed p. 223 / PDF p. 229.
- Mandaic: text 38, printed p. 244 / PDF p. 250.
- Identifier anomalies: texts 14, 19, and 40, plus the closing register on printed pp. 323–326 / PDF pp. 329–332.

OCR-derived translations are stored privately with `rights_status=public_domain` but `public_ok=0`. They remain excluded from public-safe exports until line-by-line proofreading corrects names, diacritics, lacunae, and scan/OCR errors.

## Identifier findings

| Text | Heading | Closing register | Resolution |
|---:|---|---|---|
| 14 | CBS 16917 | CBS 16017 | Retain both claims; current Penn B16017 supports the register reading. |
| 19 | CBS 16018 | blank | Identify with current Penn B16018; the blank register cell is an omission. |
| 28 | CBS 2972 | CBS 2972 | Identify with current Penn B2972. |
| 40 | CBS 2971 | CBS 2972 | Identify with current Penn B2971; the repeated register value is an error. |

The current Penn B2972 catalogue description explicitly notes that Montgomery published the number as both texts 28 and 40 and that text 40 is actually B2971. The erroneous text-40 value was moved out of identity-bearing identifiers and retained as a disputed, source-attributed register claim.

## Reproducibility

- Checked review manifest: `research/enrichment/montgomery_1913_review_2026-09-04.json`
- Importer: `src/bowl_index/montgomery.py`
- Archived PDF SHA-256: `c85f9eaadcd910652543bb54dab16e5a1a4ac7883df7b433ea2c9aa0b357abdf`
- Parser and importer are idempotent; a second run adds no duplicate texts, claims, or identifiers.
- All 41 automated tests pass, all archive hashes verify, and SQLite reports `integrity_check=ok`.

## Recommended next research pass

Proofread the 35 Montgomery translations against the page images, then capture reliable transliterations. The present OCR is good enough for private discovery search but not for public quotation or philological use; the original-script OCR is too error-prone to ingest as a transcription without manual correction.
