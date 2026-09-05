# Independent dataset quality review — 4 September 2026

## Assessment

The project is a useful, unusually traceable research index with substantial discovery breadth. It is still an early enrichment corpus: present fields, completed queues, and source counts do not establish scholarly accuracy or completeness. The architecture is worth building on; the next investment should be verified depth and measurable quality.

This review inspected the schema, ingestion/deduplication architecture, identity aggregation, conflict rules and recorded evidence, export policy, roadmap metrics, archive integrity, and automated tests. It did **not** independently reread all 752 sources, authenticate objects, validate every merge, or proofread the translations. No new external research was used. There is no defensible corpus-wide accuracy percentage yet.

## Verified local snapshot

| Measure | Result |
|---|---:|
| Candidate source records | 1,584 |
| Working physical identity hypotheses | 1,316 |
| Confirmed / probable / candidate identities | 272 / 519 / 525 |
| Source appearances / source records | 1,608 / 752 |
| Probable/confirmed identities with publication-scheme identifiers | 312/791 (39.4%) |
| Identities with translations / transcription or transliteration | 48 / 1 |
| Identities with 0–2 / 3–5 / 6–8 / 9–10 fields present | 495 / 712 / 108 / 1 |
| Media records with unknown rights | 288/325 |
| Database integrity / foreign-key violations | OK / 0 |
| Archived captures verified by byte length and SHA-256 | 18/18 |
| Existing tests / tests after repair | 44 passed / 48 passed |

A source record is not necessarily independent corroboration. All 1,316 clusters are hypotheses; only 791 have probable/confirmed status. Publication-scheme identifiers are a coverage proxy, not proof of a verified edition and locator. The 35 Montgomery translations remain OCR drafts pending proofreading. Rights labels include copyrighted material: the 37 non-unknown labels are not 37 public approvals.

## Findings and completed repair

**Conflict confidence was overstated.** The previous 323-compatible/five-substantive result was largely rule-assisted, not 328 independent source-level reviews. In particular:

- Dimensions were concatenated per field before comparison; with only one field, the comparison could succeed regardless of unequal measurements. Numeric-only fallbacks also ignored units and measurement type. The two current dimension cases appear plausibly compatible; the defect does not prove either is wrong.
- Dating rules could ignore competing period values whenever there was at most one explicit date. Different provenance facets were assumed compatible without checking their geographic or historical relationship.
- Substring and language-family matching could erase uncertainty or negation. Actual stored evidence for British Museum 117882 includes “Syriac?” and “Syriac, Estrangelo script”; the old rule labeled these compatible.
- Reviews were applied by identity and field alone, so added or corrected claims could remain hidden by an old compatibility decision. The roadmap subtracted all review rows from current flags; orphan or obsolete reviews could falsely satisfy its gate.

Completed QA-001 replaces those permissive rules with case/whitespace equivalence and a small set of exact institution-name variants. Other comparisons require explicit source-level judgment. Review validity now checks member IDs, claim IDs and values, certainty, locators, and source title/URL against the recorded evidence. Reports, identity exports, and the research console use current validity. Historical decisions and source claims were preserved.

**Result: 15 current reviews, 313 requiring revalidation.** The 15 comprise ten compatible decisions and five substantive discrepancies across four identities. The 313 are not 313 proven errors: most may be resolved as compatible after inspection. They are an honest queue replacing unsupported confidence. The [revalidation report](claim_conflict_revalidation_2026-09-04.md) lists every instance with current values, source IDs, and locators. Five retained compatible decisions are historical checked overrides, not new independent verification in this review.

Regression tests cover unequal dimensions, units and measurement types, ignored period conflicts, uncertainty/negation, non-Latin text, added claims, changed values/certainty/locators/source titles, and orphan-review counting. The existing preservation test also checks that a third claim reopens a previously compatible field without deleting its decision.

**Public-release protection is incomplete.** The export blanks unapproved text content and raw appearance payloads, but still exports media URLs and capture metadata without per-media public decisions. The schema has no such decision field for media yet. Free-text fields also need assessment. The manifest wording now accurately calls this a research snapshot, and the CLI default export destination is private. This run's refreshed export is private at `data/private/exports/quality-review-2026-09-04/`; earlier snapshots labeled public-safe should not be treated as publication-cleared. No material was published.

**Other metrics need qualification.** Provenance presence currently includes production region and ownership events, so it does not measure excavation provenance. Publication coverage does not yet implement the roadmap's sourced no-known-edition alternative. The two logged qualifying discovery sweeps describe marginal yield in those searches, not the percentage of all surviving bowls found. The roadmap now excludes incomplete/invalidated sweeps from its gate.

## Priorities and achievable quality

1. Revalidate the cited conflict queue and preserve uncertainty. Before bulk re-triage, add append-only review history and evidence-bound override manifests; the legacy triage loader still replaces the current review row and accepts count-based input manifests. Do not replay old overrides against changed evidence.
2. Implement the media rights ledger and a tested complete release boundary. A private research record and a publishable artifact need separate decisions.
3. Finish Montgomery/Penn as a checked reference cohort: all 40 texts accounted for, 35 translation drafts proofread against scans, precise concordances, publication locators, and explicit transcription/access gaps.
4. Expand this standard to British Museum, NLI, and Schøyen. Audit a reproducible sample across collection, record status, and merge method to estimate errors and direct corrections.
5. Prepare backups and bounded private collectors for the Mac mini. Separate technical readiness, source eligibility, shadow-run completion, and publication approval; the current combined handoff gate needs that refinement before implementation.

The achievable target is a dependable cross-source catalogue linking physical identity hypotheses, source disagreements, editions, translations, and collection histories, with a smaller thoroughly checked text corpus. Cross-corpus textual analysis becomes credible as checked transcriptions and editions grow. Absolute completeness and unrestricted access to every image or edition are not established targets: inaccessible sources and unenumerated private holdings remain explicit gaps.

## Reproduction

From the project root:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m bowl_index.cli verify-archive
PYTHONPATH=src .venv/bin/python -m bowl_index.cli roadmap
PYTHONPATH=src .venv/bin/python -m bowl_index.cli report-conflicts --destination data/reports/claim_conflict_revalidation_2026-09-04.md
PYTHONPATH=src .venv/bin/python -m bowl_index.cli report-enrichment --destination data/reports/identity_enrichment_reviewed_2026-09-04.md
PYTHONPATH=src .venv/bin/python -m bowl_index.cli export --destination data/private/exports/quality-review-2026-09-04
```

System Python lacked `pypdf`; the project's existing `.venv` has the required dependency and passed the suite. The working database and archive were not modified by this review; regenerated outputs and review validity are derived from existing evidence. The repository was entirely untracked at the start, so no Git diff can serve as a baseline review. No commit or publication was made.
