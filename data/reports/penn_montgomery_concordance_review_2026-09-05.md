# Forty Penn concordances checked — 5 September 2026

All **40 main Montgomery/Penn number concordances** are now supported by individual, dated museum-page observations. Each page displays both its expected museum Object Number and an explicit PBS III text number. The existing identity links were confirmed; no objects were merged, split or relabelled.

This completes the main-cohort museum-number check after the earlier review of all forty printed register rows and all thirty-five available English translations. It does not complete reconciliation of the wider Penn collection or independently validate every catalogue field.

| Measure | Result |
|---|---:|
| Main Penn number concordances checked | 40 / 40 |
| Available Montgomery English translations scan-checked | 35 / 35 |
| Additional reported metadata claims | 11 |
| New focused follow-up leads | 6 |
| Identity changes | 0 |
| Automated tests passing | 80 |

## Number discrepancies

- **Text 14:** Penn B16017 explicitly carries PBS III: 14. This agrees with the printed register CBS 16017; the conflicting heading CBS 16917 remains preserved. [Penn B16017](https://collections.penn.museum/collections/object/97562).
- **Text 19:** Penn B16018 explicitly carries PBS III: 19, supporting the heading CBS 16018 despite the blank register cell. [Penn B16018](https://collections.penn.museum/collections/object/104403).
- **Texts 28 and 40:** B2972 carries PBS III: 28, and its description explicitly corrects text 40 to B2971. B2971 independently carries PBS III: 40. The repeated 2972 in the printed register is retained as source evidence, without merging these bowls. [Penn B2972](https://collections.penn.museum/collections/object/19798), [Penn B2971](https://collections.penn.museum/collections/object/64458).

## Newly visible issues

The concordances are strong, but several other catalogue assertions require separate review. Eleven dated claims were appended as museum-reported assertions: seven measurement pairs, two dates and two language labels. Existing scholarly claims remain intact.

- **Dating:** B2963 lists ca. 200 BCE. This is an open source-level dating question, not an accepted new chronology or an inferred correction. B16018 separately lists 400–800 CE. [B2963](https://collections.penn.museum/collections/object/40422), [B16018](https://collections.penn.museum/collections/object/104403).
- **Language:** B9010 and B9008 both have the structured label Hebrew Language. Existing edition-based claims identify text 9 as Jewish Babylonian Aramaic and text 31 as Syriac; the B9008 description also uses Proto-Manichean. These differences require attention to language, script and historical catalogue terminology. [B9010](https://collections.penn.museum/collections/object/271621), [B9008](https://collections.penn.museum/collections/object/222626).
- **Relationships:** B16007 has an ambiguous duplicate reference to 16081; B16086 has an ambiguous reference to B16062/B6354. Neither phrase alone establishes physical identity. [B16007](https://collections.penn.museum/collections/object/329808), [B16086](https://collections.penn.museum/collections/object/161879).

All seven museum measurement pairs differ from the 1913 register. Penn specifies **Outside Diameter**, while the register labels **Diameter**. No equivalence of measurement conventions, restoration history or rounding is assumed.

| Text | 1913 height × diameter (cm) | Penn height × outside diameter (cm) | Museum source |
|---|---|---|---|
| 2 | 7.2 × 17.4 | 7.5 cm × 18.3 cm | [B2945](https://collections.penn.museum/collections/object/82460) |
| 4 | 7.5 × 17.3 | 7.8 cm × 17.7 cm | [B2923](https://collections.penn.museum/collections/object/275285) |
| 9 | 6 × 17.7 | 6.3 cm × 17.8 cm | [B9010](https://collections.penn.museum/collections/object/271621) |
| 12 | 7.2 × 17.7 | 8 cm × 18 cm | [B9009](https://collections.penn.museum/collections/object/271620) |
| 19 | 6.6 × 17.6 | 7 cm × 16.8 cm | [B16018](https://collections.penn.museum/collections/object/104403) |
| 20 | 7 × 17 | 7 cm × 18 cm | [B16023](https://collections.penn.museum/collections/object/284364) |
| 22 | 6.5 × 16 | 7 cm × 16.5 cm | [B16006](https://collections.penn.museum/collections/object/102142) |

Adding these source assertions exposed **nine new field-difference instances**: seven dimensions and two languages. The corpus now has **337 flagged field instances**, of which 24 have current review decisions and **313 need review**. That pending total comprises 304 earlier stale decisions and nine new differences. The new dates are flagged through a lead where the field-difference detector has no competing dating assertion to compare.

## Evidence and limits

The browser observations were made between 14:29:20 and 14:31:21 UTC on September 5. The manifest records individual observation times, URLs, table-field locators, selected reported values and reviewer rationales. This was individual page inspection; Penn robots.txt returned HTTP 404, and the automated collector/full-page archival fetch remained paused. No new images or full HTML captures were archived.

Migration 009 stores immutable concordance review records with snapshots and hashes of the supporting local identity membership, sources, identifiers, appearance links and publication-number claims. Changed local evidence invalidates the current review count. These hashes bind the research decision to local evidence; they are not hashes of the live website. The reviews are dated observations and cannot prove that the catalogue has remained unchanged since inspection.

Confirmation applies to the explicit number mapping. It does not adjudicate dating, language, measurements, provenance, attribution or reuse rights. The broader corpus remains 1,585 records representing 1,317 working identity hypotheses, with 1,609 appearances and 752 sources. No corpus-wide accuracy percentage is justified by this institutional cohort alone.

## What follows

1. Review the nine new field differences and the separate dating/relationship leads against exact source evidence. Preserve unknowns where conventions or terminology cannot be resolved.
2. Continue the 304 earlier field-review cases, and select a reproducible stratified identity sample to assess quality beyond the Montgomery/Penn cohort.
3. Extend Penn reconciliation beyond the forty main Montgomery texts; pursue the precise cited identifiers instead of assuming the historical inventory is already accounted for.
4. Obtain independent review of the English texts and begin a checked original-script pilot. The main cohort now has enough documented evidence to support that next stage.

The main Montgomery/Penn collection is becoming a useful scholarly reference set: source rows, edited reading texts and museum identities are all traceable. The next gains will come from resolving the exposed differences and repeating this level of review across other collections.

## Validation and artifacts

- All 80 automated tests passed, including stale-evidence rejection, changed-replay rejection, atomic batch failure, immutable history, identity-split invalidation, later unresolved decisions and public-export exclusion.
- The forty-review manifest replays with zero changes; the eleven-claim import replays without duplicates.
- Full database comparison with the pre-pass backup found eleven added claims and six added leads, with zero changes or deletions to existing rows. Apart from migration metadata and the forty new review records, all other data tables were unchanged.
- All 35 text reviews remain current. SQLite integrity, foreign-key and archive checks passed.
- The refreshed private research export contains 26 tables, including forty concordance reviews; all 35 private text-history payloads remain redacted. The local public scaffold omits the new review ledger and contains zero media rows. Nothing was published.
- The new backup was reopened independently and passed integrity checks with forty concordance records and thirty-five proofreading records.

Backup: `data/private/backups/after-penn-concordance-20260905T144820Z.sqlite3`.

- [Current forty-entry cohort](montgomery_cohort_current.md)
- [Dated review manifest](../../research/reviews/penn_montgomery_concordance_2026-09-05.json)
- [Reported discrepancy claims](../../research/enrichment/penn_observed_discrepancy_claims_2026-09-05.jsonl)
- [Six follow-up leads](../../research/reviews/penn_concordance_followups_2026-09-05.jsonl)
- [Validation results](penn_concordance_validation_2026-09-05.json)
- [Living roadmap](../../docs/dataset_maturity_roadmap.md)

## Complete checked concordance

All rows below are dated confirmations of existing links. The current cohort JSON gives the associated review IDs, supporting object IDs and full selected-field observations.

| Montgomery text | Penn Object Number | Penn publication number | Museum page |
|---|---|---|---|
| 1 | B8693 | PBS III: 1 | [84603](https://collections.penn.museum/collections/object/84603) |
| 2 | B2945 | PBS III: 2 | [82460](https://collections.penn.museum/collections/object/82460) |
| 3 | B2963 | PBS III: 3 | [40422](https://collections.penn.museum/collections/object/40422) |
| 4 | B2923 | PBS III: 4 | [275285](https://collections.penn.museum/collections/object/275285) |
| 5 | B2952 | PBS III: 5 | [327632](https://collections.penn.museum/collections/object/327632) |
| 6 | B2916 | PBS III: 6 | [254819](https://collections.penn.museum/collections/object/254819) |
| 7 | B16007 | PBS III: 7 | [329808](https://collections.penn.museum/collections/object/329808) |
| 8 | B9013 | PBS III: 8 | [8794](https://collections.penn.museum/collections/object/8794) |
| 9 | B9010 | PBS III: 9 | [271621](https://collections.penn.museum/collections/object/271621) |
| 10 | B16014 | PBS III: 10 | [206952](https://collections.penn.museum/collections/object/206952) |
| 11 | B16022 | PBS III: 11 | [252830](https://collections.penn.museum/collections/object/252830) |
| 12 | B9009 | PBS III: 12 | [271620](https://collections.penn.museum/collections/object/271620) |
| 13 | B8694 | PBS III: 13 | [32204](https://collections.penn.museum/collections/object/32204) |
| 14 | B16017 | PBS III: 14 | [97562](https://collections.penn.museum/collections/object/97562) |
| 15 | B16087 | PBS III: 15 | [257049](https://collections.penn.museum/collections/object/257049) |
| 16 | B2920 | PBS III: 16 | [139404](https://collections.penn.museum/collections/object/139404) |
| 17 | B2922 | PBS III: 17 | [257210](https://collections.penn.museum/collections/object/257210) |
| 18 | B8695 | PBS III: 18 | [225726](https://collections.penn.museum/collections/object/225726) |
| 19 | B16018 | PBS III: 19 | [104403](https://collections.penn.museum/collections/object/104403) |
| 20 | B16023 | PBS III: 20 | [284364](https://collections.penn.museum/collections/object/284364) |
| 21 | B16054 | PBS III: 21 | [182721](https://collections.penn.museum/collections/object/182721) |
| 22 | B16006 | PBS III: 22 | [102142](https://collections.penn.museum/collections/object/102142) |
| 23 | B16090 | PBS III: 23 | [50873](https://collections.penn.museum/collections/object/50873) |
| 24 | B2926 | PBS III: 24 | [11597](https://collections.penn.museum/collections/object/11597) |
| 25 | B16009 | PBS III: 25 | [303320](https://collections.penn.museum/collections/object/303320) |
| 26 | B3997 | PBS III: 26 | [59666](https://collections.penn.museum/collections/object/59666) |
| 27 | B16041 | PBS III: 27 | [326671](https://collections.penn.museum/collections/object/326671) |
| 28 | B2972 | PBS III: 28 | [19798](https://collections.penn.museum/collections/object/19798) |
| 29 | B16055 | PBS III: 29 | [316216](https://collections.penn.museum/collections/object/316216) |
| 30 | B16096 | PBS III: 30 | [139925](https://collections.penn.museum/collections/object/139925) |
| 31 | B9008 | PBS III: 31 | [222626](https://collections.penn.museum/collections/object/222626) |
| 32 | B16086 | PBS III: 32 | [161879](https://collections.penn.museum/collections/object/161879) |
| 33 | B16019 | PBS III: 33 | [44307](https://collections.penn.museum/collections/object/44307) |
| 34 | B9012 | PBS III: 34 | [58680](https://collections.penn.museum/collections/object/58680) |
| 35 | B16097 | PBS III: 35 | [87498](https://collections.penn.museum/collections/object/87498) |
| 36 | B2933 | PBS III: 36 | [132910](https://collections.penn.museum/collections/object/132910) |
| 37 | B2943 | PBS III: 37 | [152707](https://collections.penn.museum/collections/object/152707) |
| 38 | B2941 | PBS III: 38 | [189411](https://collections.penn.museum/collections/object/189411) |
| 39 | B9005 | PBS III: 39 | [140769](https://collections.penn.museum/collections/object/140769) |
| 40 | B2971 | PBS III: 40 | [64458](https://collections.penn.museum/collections/object/64458) |
