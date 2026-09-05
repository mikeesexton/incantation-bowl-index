# Evidence review, text revisions and release boundaries

The private database is the authoritative working record. A completed coding check, an inspected source page, an editorial reading text and a public-reuse decision are different kinds of evidence. None should silently substitute for another.

## Scan-checked reading texts

`ibi ingest-proofreading PATH` applies a version 1 proofreading manifest. The manifest identifies the source, archived PDF and its SHA-256, exact PDF pages, reviewer, UTC timestamp, editorial policy, original full-row fingerprint, corrected content file and hash, status, and correction notes. The importer verifies both the registered source capture and actual PDF bytes, checks page bounds, and rejects stale text or altered replay input. A batch either applies completely or rolls back.

Migration 006 retains exact before/after text rows in an append-only ledger. Importing OCR again cannot overwrite a text with a proofreading history. If later editing changes the text row, its earlier review stops counting as current. An explicit new proofreading batch is then required. Research exports redact both text-history payloads as well as text content whose `public_ok` is false; the private database retains the originals.

The September 4 batch comprises eleven **normalized English reading texts** of Montgomery's translations; the September 5 completion batch adds the remaining twenty-four. All thirty-five available translations now have a first scan review. Source typography is simplified under the recorded policy: print line wrapping, line-end hyphenation, italics, small capitals, Latin-name diacritics and some punctuation spacing are normalized. Gaps, restorations, line references and uncertainty are retained; `...` marks loss without asserting a missing-character count. These are neither diplomatic transcriptions nor new translations, and do not establish an Aramaic reading. Review is by Codex against rendered scans, not independent specialist certification. A second reviewer should check the reference cohort before a scholarly text release.

The completion batch preserves printed Latin-letter magical-formula diacritics and the four-line formula in text 15; ordinary Latin-name diacritics remain normalized. Missing source wording is represented explicitly, including the printed gap between line references 6 and 12 in text 40.

All thirty-five remain `public_ok=0`. Proofreading sets this flag to false; public-domain source status does not itself approve an edited text for publication.

## Montgomery register and cohort

`ibi ingest-montgomery-register research/enrichment/montgomery_register_checked_2026-09-04.json` appends 125 source-located claims to the forty existing main entries. It verifies the registered scan hash and each source/appearance/object link, requires all forty entries, preserves conflicting source claims and replays without duplicates. It does not re-inspect the scan; the named manifest is the editorial review record.

`ibi report-montgomery-cohort` regenerates an exact forty-row source account with existing Penn web identifiers, register measurements and translation status. The register scan review and dated museum-page concordance review are separate. The current report shows how many museum links have evidence-bound reviews and gives their observation dates in the companion JSON. The five missing separate translations are absences **in this edition**, not claims about all scholarship. Source number discrepancies are stored as register assertions rather than promoted to merge keys. Appendix 42 has a separate uncertain candidate and follow-up lead; appendix 41 is explicitly a skull and is excluded from the main bowl cohort.

## Dated museum concordance reviews

`ibi ingest-concordance-review research/reviews/penn_montgomery_concordance_2026-09-05.json` records checks of existing Montgomery/Penn identity links. All forty current item pages were individually inspected in the browser on September 5. Object Number and the explicit PBS III component of Other Number match in every case. Confirmation applies to this concordance, not to dating, language, dimensions or all statements on the page.

Migration 009 retains the review and exact supporting local evidence in an append-only ledger. The importer validates publication and museum identifiers, observed number pairs, source URL, UTC dates and evidence fingerprints. It rejects stale evidence, changed replays and duplicate reviews; batches apply atomically. It never merges objects. A later identity split or a change to supporting identifiers, source records or publication-number claims removes the old review from current counts. An unresolved later review does not resurrect an earlier confirmation.

These are dated, selected-field observations, not archived full-page captures. Penn's robots.txt returned 404, and automated collection/full-page archival fetching remained paused. The stored fingerprint covers local supporting evidence; it is not a hash of the website and cannot prove that the site remains unchanged. Research exports retain the review ledger; the narrow public export omits it.

Eleven separately cited reported claims preserve the seven current measurement pairs, two dates and two divergent language labels. Six leads retain the unresolved issues. No observation grants image or text reuse permission, and no scholarly source value is overwritten.

## Citation-pointer corrections

`ibi ingest-locator-corrections research/reviews/segal_locator_corrections_2026-09-04.json` applies the documented importer repair. Every entry includes its exact original claim row, corrected locator, rationale and evidence-manifest hash. Only `locator` can change. Migration 008 stores exact before/after rows in immutable correction history. Changed input or evidence causes rejection; replay of the unchanged applied batch changes nothing. No scholarly value, certainty or identity link is edited by this operation.

The range importer formerly shared each range's claim dictionaries, so assigning a default locator to the first item affected later items. Only the Segal seed used ranges in the audited seed directory. All 137 affected claims were matched on source, appearance, field, value, certainty and first-item locator before correction. This is a scoped deterministic data repair, not validation of the catalogue's classifications. Evidence-bound conflict decisions naturally become stale when their cited claims change; the BM 117882 language decision was explicitly refreshed and remains unresolved.

## Media-rights ledger

`ibi ingest-rights-review PATH` accepts version 1 batches with a reviewer, UTC timestamp and exact current media-evidence fingerprints. Each entry can record creator, rights holder, source URL, rights statement and locator, license URL, jurisdiction/date notes, private-capture status, public-reuse decision, attribution, rationale and follow-up. Migration 007 retains decisions in append-only history. A later decision supersedes an earlier one without deleting it. Changed media/source/capture evidence invalidates the earlier decision.

The vocabulary is:

| Decision | Meaning | Counts as completed assessment | Public media export |
|---|---|---|---|
| `needs_review` | Permission is unassessed or unresolved; explicit follow-up required | No | Withheld |
| `withhold` | Reviewer has decided to withhold reuse and supplied a rationale | Yes | Withheld |
| `approved` | Reviewer supplies rights evidence, locator and attribution for this exact resource | Yes | Eligible while evidence remains current |

The initial 325 rows are mechanical `needs_review` inventory holds. They contain no inferred permissions and count as **zero completed assessments**. Historical `media.rights_status` labels and a source's public-domain label are not media approvals. The software validates the decision record; it cannot establish the legal correctness of its rationale.

## Two distinct exports

`ibi export --destination data/private/exports/latest` creates the research snapshot. This includes media URLs, capture metadata, source claims and review metadata; it is **not publication-cleared**. Text content and original text snapshots receive specific redaction, which does not make every other field public.

`ibi export-public --destination NEW_DIRECTORY` creates a narrow local reference scaffold; it does not publish anything. Its explicit allowlist includes bibliographic metadata, object identifiers/labels/status, appearance locators and links, selected identity counts, already-approved text rows and eligible media references. It omits capture records and bytes, raw payloads, source/appearance URL columns, free-text notes, claims, and review histories. It withholds media without a current explicit approval. An unapproved row sharing an exact URL also blocks any approved copy of that URL.

The exporter rejects known private media/capture references repeated in its permitted strings, writes into a temporary directory, and refuses to reuse an existing destination. Tests cover stale approval, revocation, repeated URLs, escaped reference strings, forbidden metadata leakage, failed-batch rollback and residual files. This is a bounded projection with specific controls, not a general scanner that proves arbitrary metadata legally publishable. It does not certify object accuracy or clear a future public dashboard. The current web console remains a private localhost application.

## Reproducibility and next review

Private corrected-text files, scans, database snapshots and research exports stay outside Git. Retain them together for replay; public manifests intentionally do not embed the private content. The September 4 validation compared the live database with the pre-work backup, checked exact preserved originals, verified all eighteen archived captures, checked SQLite integrity and foreign keys, and opened a new database backup successfully.

Next: arrange an independent second text review, reconcile the newly documented Penn metadata differences and extend to the remaining museum holdings, source-review the pending conflict instances, and investigate actual rights evidence before any media release. Keep institutional-cohort work and a representative accuracy audit separate: the Montgomery cohort is not a statistically representative sample of the whole corpus.
