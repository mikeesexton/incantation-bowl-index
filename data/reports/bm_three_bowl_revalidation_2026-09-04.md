# First conflict revalidation batch — British Museum

## Outcome

Reviewed nine field instances across BM 113189, 117880, and 117882 against the stored source-attributed evidence and the existing item-page mapping manifest. Eight are compatible descriptions; one remains unresolved. The remaining revalidation queue falls from 313 to 304. There are now 24 effective reviews: 18 compatible, five previously recorded substantive discrepancies, and one newly recorded unresolved issue.

This is a bounded stored-evidence comparison, **not fresh primary-source verification**. Attempts to retrieve all three British Museum item pages returned HTTP 403. No access controls were bypassed. No original claims, text, media, identifiers, or identity links were changed.

| Bowl | Field | Decision and limit |
|---|---|---|
| BM 113189 | Dimensions | Same four measurements and cm units; 5 versus 5.00 is decimal formatting. This does not verify the physical measurements. |
| BM 113189 | Location | All claims name the British Museum. Room 1 is retained as display information qualified to the original time of access. |
| BM 113189 | Production place | Iraq versus Made in: Iraq is interface labeling; this is not excavation provenance. |
| BM 113189 | Dating | Stored ranges all express sixth–seventh centuries. The shared co-reported period label is retained separately, not equated to an exact calendar interval. |
| BM 117880 | Dating | The stored sixth–eighth-century ranges differ in dash style; the co-reported period label remains separate. |
| BM 117880 | Provenance | Both stored findspots name Tell Ibrahim (Kutha); the interface label differs. Production region remains distinct from findspot and excavation context. |
| BM 117882 | Dating | Same stored range with different dash style; this does not validate the Segal concordance. |
| BM 117882 | Provenance | Both stored findspots name Abu Habba (Sippar); one retains an interface label. This does not validate the Segal concordance. |
| BM 117882 | Language | Unresolved: Syriac? versus Syriac, Estrangelo script. The uncertain claim cites Segal 117ES, while the mapping identifies 119ES. |

The BM 117882 question requires the catalogue entries and museum evidence to distinguish a locator error, extraction error, mistaken identity link, or attribution difference. It is recorded as blocked lead `IBI-LEAD-BM117882-SEGAL`, linked to the Segal source. The merge was not reversed without sufficient evidence.

## Audit trail and verification

The version 2 [review manifest](../../research/reviews/bm_three_bowl_revalidation_2026-09-04.json) includes every inspected claim, its source and locator, a complete-evidence fingerprint, an individual rationale, and the limits of review. The original 328 review rows were snapshotted during migration 005; applying the batch produced nine additional immutable history snapshots, for 337 total. Replaying the batch changed zero rows.

A consistent SQLite backup was created before migration at `data/private/backups/before-conflict-revalidation-20260904T223815Z.sqlite3`. Database integrity and foreign-key checks passed afterward. All 52 automated tests pass, including atomic batch rejection, stale-evidence rejection, duplicate detection, replay idempotency, history protection, and rejection of legacy count-only overrides.

## Next work

Primary-source revalidation of the remaining 304 instances continues as access permits. Prioritize BM 117882's Segal locator and identity issue; preserve its uncertainty. The public media ledger and export boundary are still unfinished. The first fully verified text cohort remains Montgomery/Penn, whose scans are locally archived; these stored-description decisions do not advance translation proofreading or public-release readiness.
