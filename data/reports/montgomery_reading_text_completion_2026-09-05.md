# Montgomery English reading-text completion — 5 September 2026

All **35 available English translations** in the main Montgomery cohort now have a first review against rendered pages of the archived 1913 edition. This pass completed the remaining 24. All forty main entries are accounted for: the other five have explicit, source-located explanations for the absence of a separate translation in this edition.

| Measure | Before this pass | After |
|---|---:|---:|
| Scan-checked English reading texts | 11 / 35 | 35 / 35 |
| OCR drafts awaiting first review | 24 | 0 |
| Main entries with documented translation status | 40 / 40 | 40 / 40 |
| Independent second text reviews | 0 | 0 |
| Main entries with checked original-script capture | 0 / 40 | 0 / 40 |
| Montgomery translations approved for public export | 0 | 0 |

The five source exceptions are texts 18, 21, 23, 27 and 33. An absence in Montgomery is not a claim that later scholarship has no translation. Appendix material remains separately scoped.

## What improved

The review corrected OCR substitutions in names and magical formulas, restored omitted gaps, repaired line-reference errors, and recovered paragraph divisions. Examples include the OCR name Marni corrected to Mami in text 34; misread numeral-like characters in the formula in text 35; and a whole omitted gap line between references 6 and 12 in text 40. The formula in text 15 retains its printed four-line arrangement. True compound hyphens were distinguished from hyphens caused by print wrapping.

These are normalized English reading texts of Montgomery’s translation, with the editorial policy recorded for each batch. They preserve restorations, uncertainty and source wording; they do not constitute a new translation or verification of the underlying Aramaic. Ordinary Latin-name diacritics and typography are simplified. Printed Latin-letter magical-formula diacritics in this batch are retained. A separate specialist review remains necessary before treating these as a scholarly text release.

Every new revision retains the exact original database row, corrected row, source-PDF hash, reviewed page numbers, content hashes, reviewer, UTC timestamp and correction notes. Texts 7, 37 and 39 have precise review-page lists excluding commentary pages included in their inherited broad locators.

## How good the dataset is becoming

The corpus now contains **1,585 records representing 1,317 working identity hypotheses**, with 1,609 source appearances and 752 sources. Its main strength is an increasingly auditable chain from a source appearance to an identity hypothesis, a cited claim and a reversible editorial decision. Montgomery is now a bounded source collection with complete first-pass English-text review and a checked forty-row register. This makes it more useful for finding and comparing evidence.

Quality remains uneven across the larger corpus. There are **304 field-conflict instances awaiting revalidation**. Only **312 of 791 probable/confirmed identities (39.4%)** have publication-scheme identifiers, and that is still a proxy for properly checked edition references. All 325 media records await completed rights assessment. A finished review queue or a source-specific audit does not measure overall identity accuracy; no defensible corpus-wide accuracy percentage is available yet.

The achievable target is a strong scholarly reference index: stable object identities, reversible concordances, precise edition locators, explicit disagreements, checked texts where available, and media with documented reuse decisions. Building that quality collection by collection is realistic. Exhaustive coverage of unlocated objects and inaccessible private collections will remain uncertain, and textual interpretation needs specialist judgment.

## Next work

1. Verify the forty Penn museum concordances against current item records, beginning with texts 14, 19 and 40, whose printed heading/register identifiers differ or are missing. Record the actual evidence and preserve discrepancies.
2. Arrange an independent second review of the 35 reading texts, emphasizing formulas, names, gaps and restorations; start a small original-script transcription/transliteration pilot with explicit conventions.
3. Revalidate the 304 remaining field-conflict instances in exact-evidence batches. Select a reproducible stratified identity sample to measure error categories across institutions and source types.
4. Replace publication-identifier proxies with checked edition references and assess reuse evidence for media before a public release.

The living roadmap marks **TEXT-002 complete**, adds **TEXT-006** for independent second review, and makes current Penn concordance verification the next priority. Overall text-workstream maturity remains conservative because this one completed source cohort does not establish coverage or quality across the full corpus. The operational handoff gate remains not ready.

## Validation and retained evidence

- All 73 automated tests passed; replay of the applied 24-entry batch changed zero rows.
- Full comparison with the pre-pass backup found only 24 text rows changed (content and notes), plus their 24 new audit rows. All other database tables and all eleven earlier proofreading records were unchanged.
- Every new original snapshot matched its exact pre-pass text row. All 35 reviews match the current text rows, and all 35 retain public_ok=false.
- SQLite integrity and foreign-key checks passed. Archive verification found no problems.
- Refreshed private research export has 25 tables and redacts all 35 before/after text-history payloads. The local public scaffold includes no Montgomery translation or media approvals; nothing was published.
- A new database backup was opened independently, passed integrity and foreign-key checks, and contained all 35 review records.

Backup: `data/private/backups/after-montgomery-completion-20260905T141742Z.sqlite3`.

- [Current forty-entry cohort](montgomery_cohort_current.md)
- [Machine-readable validation](montgomery_completion_validation_2026-09-05.json)
- [Completion manifest](../../research/reviews/montgomery_reading_texts_completion_2026-09-05.json)
- [Initial eleven-text manifest](../../research/reviews/montgomery_reading_texts_2026-09-04.json)
- [Living roadmap](../../docs/dataset_maturity_roadmap.md)

## Completion-batch page coverage

Page numbers below are one-based PDF pages; the archived scan identity is recorded in the manifest.

| Montgomery text | PDF pages checked |
|---|---|
| 1 | 123, 124 |
| 2 | 127, 128 |
| 3 | 133, 134 |
| 4 | 139, 140 |
| 5 | 144, 145 |
| 6 | 147, 148 |
| 7 | 153, 154 |
| 8 | 161, 162 |
| 9 | 167, 168 |
| 11 | 176 |
| 12 | 180, 181 |
| 13 | 184, 185 |
| 15 | 191, 192 |
| 16 | 194, 195 |
| 17 | 196, 197 |
| 19 | 202, 203 |
| 29 | 224, 225 |
| 32 | 231, 232 |
| 34 | 237, 238 |
| 35 | 242, 243 |
| 37 | 248 |
| 38 | 250, 251 |
| 39 | 254 |
| 40 | 258, 259 |
