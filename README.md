# Incantation Bowl Index

An evidence-first, local research corpus for identifying and reconciling every traceable incantation bowl, fragment, lost object, auction appearance, disputed example, suspected fake, and pseudo-script specimen.

This repository contains the schema, research tooling, source manifests, and reproducible reports. The working SQLite database and downloaded evidence archive are private and ignored by Git.

## Phase-one discovery snapshot

The 4 September 2026 campaign produced 1,584 candidate records representing an estimated 1,357 distinct physical objects after 227 exact, evidenced duplicate resolutions. It records 1,586 source appearances from 730 sources. All 12 planned source-class targets are searched or explicitly blocked, every object has evidence, and two independent broad sweeps met the under-1% saturation rule.

- [Discovery campaign report](data/reports/discovery_campaign_2026-09-04.md)
- [Historical CSV/JSONL research export (not publication-cleared)](data/exports/phase-one-2026-09-04/manifest.json)
- [Research and deduplication protocol](docs/research_protocol.md)

This is a maximum-recall research snapshot, not a claim of absolute completeness. The report preserves inaccessible catalogues, private-collection aggregates, uncertain concordances, and rights-restricted editions as explicit blocked leads.

## Identity and enrichment status

The current corpus contains **1,585 records representing 1,317 working identity hypotheses** (272 confirmed, 519 probable, 526 candidate), with 1,610 appearances from 752 sources. These are working research classifications, not an overall accuracy estimate. The latest source review checked all forty Montgomery register rows, added 125 source-attributed claims, completed scan review of all thirty-five available English translations, and separately recorded Appendix 42 as an uncertain possible bowl. The five entries without separate translations have source-located explanations. All forty Penn museum number concordances have also been checked individually against the current catalogue, with dated evidence retained. Independent second review and original-script verification remain outstanding.

An importer defect was repaired in 137 Segal claim locators, with immutable before/after records and no changes to scholarly values or identity links. This explains the BM 117882 117ES/119ES pointer mismatch; its language uncertainty still needs catalogue review. The Penn review added eleven reported metadata claims and six follow-up leads. All nine newly exposed language and measurement differences now have exact-evidence unresolved decisions, followed by twenty revalidated same-source field facets. Current review coverage is 53/337 instances, with 284 older decisions still needing revalidation. Five source-reported Penn relationships are stored separately from physical identity, with no automatic merges. The full decision history is preserved.

All 325 media now have explicit rights-review holds, with **zero completed rights assessments and zero media approvals**. A separate tested public-export path creates a narrow reference scaffold while withholding unapproved media; the research export remains private. No public dashboard has been deployed.

- [Forty Penn concordances and catalogue follow-ups](data/reports/penn_montgomery_concordance_review_2026-09-05.md)
- [Penn field, dating-context, and object-relationship review](data/reports/penn_anomaly_review_2026-09-05.md)
- [Twenty-case same-source conflict revalidation](data/reports/same_source_conflict_revalidation_2026-09-05.md)
- [Waller 2025 findspot evidence review](data/reports/waller_findspot_review_2026-09-05.md)
- [Schwab 1891 Dieulafoy/Susiana cohort](data/reports/schwab_susa_bowls_2026-09-05.md)
- [Completed Montgomery reading-text review](data/reports/montgomery_reading_text_completion_2026-09-05.md)
- [Extended source review and status](data/reports/extended_review_2026-09-04.md)
- [Forty-entry Montgomery reference cohort](data/reports/montgomery_cohort_current.md)
- [Text revisions, citation repairs and release boundaries](docs/evidence_review_and_release.md)
- [Independent quality review and priorities](data/reports/quality_review_2026-09-04.md)
- [Current identity and enrichment report](data/reports/identity_enrichment_current.md)
- [First BM revalidation batch](data/reports/bm_three_bowl_revalidation_2026-09-04.md)
- [Evidence-bound review workflow](docs/conflict_review_workflow.md)
- [Current cited conflict revalidation queue](data/reports/claim_conflict_revalidation_current.md)
- [Historical identity-level research export (not publication-cleared)](data/exports/identity-enrichment-2026-09-04/manifest.json)
- [Checked identity review decisions](research/reviews/identity_review_2026-09-04.jsonl)
- [British Museum item-page mappings](research/enrichment/british_museum_item_pages_2026-09-04.json)
- [Montgomery text and concordance review](research/enrichment/montgomery_1913_review_2026-09-04.json)
- [Montgomery enrichment report](data/reports/montgomery_1913_enrichment_2026-09-04.md)
- [Living dataset-maturity roadmap](docs/dataset_maturity_roadmap.md)
- [Historical claim-conflict triage report (superseded)](data/reports/claim_conflict_triage_2026-09-04.md)

The derived `identity_clusters` export is the preferred starting point for browsing the corpus: it aggregates member records, identifiers, appearances, source counts, coverage flags, conflicts, completeness, and a suggested next enrichment action without erasing the underlying source records.

### Private research UI

The local research console now provides identity search and facets, an evidence dossier for each probable bowl, a side-by-side concordance workbench, and queues for missing fields and conflicting claims. It runs only on localhost and writes only validated review actions. A later public dashboard can reuse the search and dossier views against reviewed, rights-safe exports rather than the private ingestion database.

## Quick start

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
ibi init
ibi seed-queries
ibi stats
ibi export --destination data/private/exports/latest
ibi report
ibi report-enrichment
ibi roadmap
ibi report-montgomery-cohort
ibi ingest-relationship-review research/reviews/penn_object_relationships_2026-09-05.json
ibi ingest-montgomery data/private/archive/sha256/c8/c85f9eaadcd910652543bb54dab16e5a1a4ac7883df7b433ea2c9aa0b357abdf research/enrichment/montgomery_1913_review_2026-09-04.json
ibi serve
python -m unittest discover -s tests -v
```

Without installation, set `PYTHONPATH=src` and run `python -m bowl_index.cli`.

## Core principle

A physical bowl is not the same thing as a catalogue entry, auction lot, publication number, or web page. The database stores those appearances separately and links them with an explicit confidence and rationale. All factual assertions are source-attributed claims.

See [docs/research_protocol.md](docs/research_protocol.md) for the discovery and deduplication protocol.

## Repository boundaries

- `migrations/` contains the versioned SQLite schema.
- `src/bowl_index/` contains ingestion, collection, archive, dedupe, export, and reporting code.
- `research/` contains checked source manifests, search logs, coverage assessments, saturation measurements, and audit records.
- `data/exports/` contains historical research snapshots; `data/reports/` contains aggregate reports. Historical exports are not publication-cleared.
- `data/private/ibi.sqlite3` and `data/private/archive/` are intentionally ignored because they contain the mutable research database and private evidence captures.

Research exports retain text-row provenance and rights metadata but blank content unless its record is explicitly marked `public_ok`; raw source payloads also remain private. Media URLs, capture metadata, and free-text fields still require a separate release review. Historical “public-safe” labels overstate this boundary. Keep refreshed full research exports private; the separate public-export path applies a narrower set of publication gates. The private database remains the authoritative store for restricted research material.

The future dashboard should consume reviewed exports or a read-only API, never the private ingestion database directly. Scheduled collectors for a continuously running Mac mini belong in a later monitoring phase after review rules and backup policy are in place.

## Research console

Run `ibi serve` and open `http://127.0.0.1:8765` to use the private research console. It provides corpus-wide identity search, evidence dossiers, enrichment queues, and a reversible concordance workbench. The server refuses non-local bindings and should never be placed directly on the public internet. See the [research console guide](docs/research_console.md).
