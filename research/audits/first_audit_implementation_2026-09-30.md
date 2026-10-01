# First audit implementation and verification

Companion to the hash-bound research evidence in
[first_personal_audit_2026-09-30.md](first_personal_audit_2026-09-30.md).
The original evidence report is kept unchanged after ingestion.

## Metadata repair workflow

`ibi ingest-text-metadata PATH` accepts version 1 manifests with a named
reviewer, UTC time, checked evidence file/hash and entries containing correction
ID, text ID, expected complete text-row SHA-256, changes and rationale.
Only `text_type` and `locator` may change. The importer validates a clean
transaction, applies the whole batch atomically, and retains complete private
before/after snapshots in append-only `text_metadata_corrections`.

Changed classification or locators invalidate evidence-bound release decisions;
no approval is transferred automatically. Research exports redact both snapshot
payloads. Original owner-approved packets remain historical artifacts. Tests
verify their retained original evidence and fail-closed release for revised rows.
Explicit summary/paraphrase declarations are rejected under `translation` during
candidate ingestion; normal translation prose is not classified heuristically.
Replaying an original source manifest cannot recreate a locator-repaired text.

## Applied records

- Seven explicitly declared summaries/paraphrases reclassified, without changing
  their content. AIT27 and VA.2451 were already summaries: their misleading reader
  heading was a separate display error.
- VA.2451 text locator and six extracted claim locators repaired to printed
  p. 101 / PDF p. 115 with immutable originals.
- B2970 gains source-reported condition, inscription layout/line count, hedged
  language, expedition credit, scoped field number and its second museum image
  URL. An image URL remains distinct from a retained local image.
- VA.2451 gains source-reported condition and dimensions. The diameter/height
  convention was checked visually on the same held book's introduction,
  printed p. 5 / PDF p. 19. Its 2018 unpublished report stays dated.
- GelD gains a project-authored explanatory card line and bibliographic claim;
  its physical identity remains provisional. No uncertain merges or new bowls.
- AIT27 gains a facsimile scan row and private PNG derivative of Montgomery's
  No. 27, printed p. 212 / PDF p. 218. The full source-page image includes the
  printed Hebrew-script passage and its discussion, without claiming a separate
  translation or complete transcription.
- The new original-text expansion also exposes previously retained source scans,
  labelled as facsimiles that can include text, translations, commentary or
  photographs. They are distinct from object photographs and readable texts.
- Two structural compatibility reviews keep B2970's line count and layout as
  complementary features, and distinguish VA.2451's catalogue appearance from
  its dated inscription-edition status. They neither validate a reading nor
  settle a scholarly disagreement. Both reviews retain their full history.
- Bibliography links prefer the museum record over a photograph, while retaining
  Mike-private held-edition links as the preferred publication route.
- Open documentation leads for B2970, VA.2451 and GelD are retained separately.
  Segal 2000 remains an acquisition need. No outgoing email or release decision.

## Validation

- 353 Python tests and 42 Node interface tests pass.
- Metadata and claim correction manifests replay with zero new corrections;
  enrichment manifests replay without new bowls, claims, texts or media.
- Original corpus text content remains unchanged; the only new text content is
  the project-authored GelD description. All private snapshots remain retained.
- SQLite integrity and foreign keys pass. Existing identity memberships remain
  unchanged. Audit progress remains 5 reviewed / 1,699 remaining.
- Browser checks cover AIT27's absent translation, expandable source page, single
  dimensions citation, source-attributed maker outside the collapsed details,
  and one identifier apparatus; B2970's image views and sourced details;
  VA.2451's explicit empty translation and corrected page; and GelD's explanation.
- Regenerated roadmap, campaign/enrichment and proofreading reports plus Mike
  Access. Edition-row proofreading now counts 688 checked / 2 unreviewed of 690
  after the seven metadata repairs. **The missing-translation acquisition work
  remains open**; the improved percentage is not evidence of new editions.
- Private ledger, source-page derivative, screenshot and Mike build are ignored
  by Git. Existing public/shared release gates continue to withhold revised text
  and unapproved media. No deployment or push.
