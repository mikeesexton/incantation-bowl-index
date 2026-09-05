# Extended review and research progress — 4 September 2026

Completed through 2026-09-05 03:44 UTC (the evening of September 4 in New York). The corpus is now a stronger, more auditable research index, with the beginnings of a directly checked reference cohort. It remains uneven as a source of verified scholarly text and metadata. The biggest gain in this pass is evidence quality and recoverability, not record growth.

## What changed

| Work | Completed | Qualification |
|---|---:|---|
| Segal citation-pointer repairs | 137 | Importer error fixed; original full claims retained; no scholarly readings, certainty labels or identity links changed |
| Montgomery main register | 40/40 entries checked | Direct scan review of printed pp. 321–326; historical measurements/condition, not new physical inspection |
| New main-cohort claims | 125 | 40 dimensions, 40 historical conditions, 40 literal register numbers, 5 source-specific translation-availability assertions |
| English reading texts checked against scans | 11/35 | Normalized reading texts; 24 OCR drafts remain; not diplomatic transcription or original-language verification |
| Main entries accounted for | 40/40 | Existing Penn links enumerated; five cases have no separate translation in this edition; current museum pages not all freshly checked |
| Scope correction | 1 candidate and 2 claims | Appendix 42 retained as an uncertain, unlocated possible bowl; carrier/date unconfirmed; appendix 41 explicitly a skull |
| Media-rights inventory | 325/325 | All `needs_review`; zero completed rights assessments and zero media approvals |
| Automated regression checks | 73 passing | Plus JavaScript syntax, database integrity, archive verification and database-backup restore checks |

Eleven checked translations are texts **10, 14, 20, 22, 24, 25, 26, 28, 30, 31 and 36**. Review recovered missing loss markers, corrected OCR punctuation/brackets and normalized typography under a recorded policy. Exact original and revised text rows remain in immutable private history. All eleven retain `public_ok=0`.

The register review preserves the source's internal discrepancies: text 14 has different heading/register numbers; text 19 has a blank register number; and text 40's printed register repeats the number assigned to text 28, while the heading and prior Penn correction identify a different object. Register readings are claims, not automatic identity keys.

## The most consequential defect

The compact-list importer reused claim dictionaries across a catalogue range. Assigning a default locator to the first entry silently assigned that same locator to later entries. The Segal seed was the only seed using ranges in the audited directory. Its five ranges produced 137 affected claims.

The repair matched each claim to its source, correct existing appearance, field, value, certainty and erroneous first-item locator. It changed only the locator and retained exact before/after claim rows. The importer now copies per-entry claims before assigning defaults. Tests cover range isolation, explicit locator exceptions, unchanged replay, stale evidence, immutable originals and atomic rollback. Zero mismatches remain in this scoped Segal audit; that is not a claim that every citation elsewhere is correct.

This explains the earlier apparent Segal 117ES/119ES mismatch for BM 117882. Its pointer now correctly names 119ES. Its `Syriac?` classification still needs full-catalogue inspection beside the museum's description. The blocked lead was updated and the evidence-bound language review refreshed; uncertainty and identity links were preserved. The earlier lead and review manifests remain available as historical evidence.

## Current corpus and maturity

| Measure | Current state |
|---|---:|
| Underlying records | 1,585 |
| Working identity hypotheses | 1,317 |
| Confirmed / probable / candidate identity statuses | 272 / 519 / 526 |
| Source appearances / sources | 1,609 / 752 |
| Priority identities (confirmed or probable) | 791 |
| Priority identities with publication-scheme identifiers | 312/791 (39.4%) |
| Current effective claim-field decisions | 24/328 |
| Claim-field instances requiring revalidation | 304 |
| Effective decisions: compatible / other dispositions | 18 / 6 |
| Generated dedupe candidates awaiting decisions | 0 |
| Completed media-rights assessments / public media approvals | 0 / 0 |

The publication metric is identifier presence, not verification of a usable edition and exact locator. A completed dedupe queue does not establish identity accuracy. The 304 pending fields are review requirements, not 304 proven errors. Source-class discovery saturation applies to the logged searches; it does not establish global completeness.

The earlier architecture review was right to prioritize conservative evidence-bound decisions. This pass demonstrates their value: a later citation repair automatically invalidates any decision tied to the previous claim evidence, and the revised decision must be recorded explicitly. Text proofreading and media permissions now have comparable histories and checks.

The Montgomery cohort is becoming useful as a worked reference set. All forty entries have source-level accounting, and eleven translations have direct scan review. It is still only one edition and is not representative of institutions, private collections, market descriptions, uncertain objects or all merge methods. There is no defensible overall accuracy percentage yet.

## How good this can get

A realistic near-term target is a dependable, edition-linked catalogue of known objects and appearances: stable identifiers, precise source locators, visible competing claims, checked reference cohorts and explicit unknowns. The data model is well suited to that target because it keeps objects, appearances, claims and review histories separate.

A critical text corpus is a further stage. It requires reliable original-script transcription or transliteration, comparison with later editions, specialist review, and a clear distinction between historical translations and current readings. More model-driven extraction alone cannot establish those things. Authorized access to restricted catalogues and unenumerated collections also limits how complete the inventory can become.

The corpus should improve first by making selected groups deeply trustworthy, then extending that standard. Adding another large batch of weakly described records would raise the count without demonstrating a comparable gain in scholarly reliability.

## Roadmap priorities

1. Finish the remaining **24 Montgomery reading texts**, then obtain a second review and verify the forty current museum concordances. Keep original-script work as a separate task.
2. Revalidate the **304 claim-field instances** in small, evidence-bound source batches. Prioritize questions that could change identity or materially affect language, dating or provenance. Seek authorized full Segal access for the remaining catalogue questions.
3. Run a **reproducible stratified accuracy audit** spanning institutions, market sources, status classes and merge methods. Report inspected denominators and uncertainty before assigning a corpus-wide accuracy estimate.
4. Investigate actual rights evidence for the **325 media holds**. The rights inventory and export controls are implemented; permissions research is not complete.
5. Extend checked institutional cohorts and replace presence-only publication/metadata measures with source-assessment measures. Pursue precise discovery leads such as Appendix 42 alongside that work.
6. Prepare Mac mini operations: encrypted and off-device backups, collector bounds, failure reporting and a shadow run. A successful local database restore is one component, not completion of the operations workstream.

The living roadmap now records completed text-history controls, audited citation repair, the forty-entry source account and the rights-export boundary. It measures completed media assessments separately from inventory holds. The overall handoff gate remains **NOT READY**.

## Validation and delivery

All **73 tests pass**. JavaScript syntax checks pass, and the dossier exposes current proofreading and reuse-review status. SQLite integrity is `ok`, with no foreign-key violations. All **18 archived captures** match recorded sizes and SHA-256 hashes.

Comparison with the pre-work database backup found exactly **127 added claims**, **137 locator-only claim updates**, **11 text-content/notes revisions**, one new candidate appearance/object/link and one source-note correction. No prior object, appearance, media, merge decision or identity link was changed or deleted. The 137 original claims and eleven original texts match their retained snapshots exactly. A new database backup was opened, checked and sampled successfully.

A refreshed private research export contains 25 tables. A separate public-scaffold validation contains **zero media rows**, with all 325 withheld, and the ten pre-existing `public_ok` text rows. No text or media approval was granted in this pass. The scaffold is intentionally narrow and is not a complete publication-ready scholarly catalogue. No deployment or publication occurred.

Evidence and outputs:

- [Living roadmap](../../docs/dataset_maturity_roadmap.md)
- [Montgomery forty-entry cohort](montgomery_cohort_2026-09-04.md) and [machine-readable rows](montgomery_cohort_2026-09-04.json)
- [Validation record](dinner_validation_2026-09-04.json)
- [Text, citation and release workflow](../../docs/evidence_review_and_release.md)
- [Checked register manifest](../../research/enrichment/montgomery_register_checked_2026-09-04.json)
- [Proofreading manifest](../../research/reviews/montgomery_reading_texts_2026-09-04.json)
- [Audited Segal repairs](../../research/reviews/segal_locator_corrections_2026-09-04.json)
- [Refreshed BM 117882 review](../../research/reviews/bm117882_post_locator_repair_2026-09-04.json)
- [Current conflict report](claim_conflict_revalidation_current.md)

Private corrected reading texts are in `data/private/proofreading/montgomery/`; the refreshed research snapshot is in `data/private/exports/extended-review-2026-09-04/`. Retain the private scan, correction files and database snapshots together to reproduce the work.
