# Incantation Bowl Index

An evidence-first research corpus for identifying and reconciling every traceable incantation bowl, fragment, lost object, auction appearance, disputed example, suspected fake, and pseudo-script specimen.

## What this index is not

**Listing an object here is not a statement about its ownership, export history, or authenticity.** Provenance fields record what a source reports, nothing more. A dealer's stated findspot is a dealer's claim; a museum register is a museum's record; neither is an archaeological fact, and the index keeps them apart. Many bowls in this corpus left Iraq without documentation, and a substantial number cannot support any household, depositional, or geographic argument at all.

This is a scholarly finding aid. It is not a market resource, and it does not authenticate, value, or legitimize anything.

**On texts.** The ancient Aramaic on a bowl belongs to nobody. A modern scholar's transcription and translation of it are their work: reading damaged letters, restoring gaps, and dividing words are editorial judgments, and a translation is a derivative work. So this index publishes text only where the edition is out of copyright, openly licensed, or the index's own. Everywhere else it publishes the citation, the exact locator, and a link, so a reader can go and read it. See [`docs/project-rules.md`](docs/project-rules.md).

This repository contains the schema, research tooling, source manifests, reproducible reports, and the gated public dataset. The working SQLite database and downloaded evidence archive are private and ignored by Git.

## Phase-one discovery snapshot

The 4 September 2026 campaign produced 1,584 candidate records representing an estimated 1,357 distinct physical objects after 227 exact, evidenced duplicate resolutions. It records 1,586 source appearances from 730 sources. All 12 planned source-class targets are searched or explicitly blocked, every object has evidence, and two independent broad sweeps met the under-1% saturation rule.

- [Discovery campaign report](data/reports/discovery_campaign_2026-09-04.md)
- [Public dataset](data/public/2026-09-05/manifest.json) — the reviewed, gated projection. The full research snapshot stays local; regenerate it with `ibi export`.
- [Research and deduplication protocol](docs/research_protocol.md)

This is a maximum-recall research snapshot, not a claim of absolute completeness. The report preserves inaccessible catalogues, private-collection aggregates, uncertain concordances, and rights-restricted editions as explicit blocked leads.

Saturation is bounded by the twelve source classes that were searched. Waller's 115-title list of JBA bowl publications (1853–2024) is used as a bibliography audit: every title now has a source record, so the project knows what it still needs to inspect. Bowl-level work is measured separately. The database currently resolves **32 publication editions covering 895 candidate records**, and its complete inspected edition units supply 540 page-located source appearances. See the [control-list measurement](data/reports/waller_control_list_2026-09-05.md), the [current mission plan](docs/dataset_maturity_roadmap.md), and the [scoping review alignment](data/reports/scoping_review_alignment_2026-09-05.md).

## Identity and enrichment status

The current corpus contains **1,969 records representing 1,652 working identity hypotheses**, with 2,243 appearances from 862 sources. These are working research classifications, not an overall accuracy estimate. Complete inspected editions and catalogues now include both *Aramaic Bowl Spells* volumes, Montgomery, Moriggi's Syriac corpus, Ford–Morgenstern's Hilprecht catalogue, Levene's curse-text volume, the modern Berlin catalogue, Naveh–Shaked 1985, Pognon 1898–1899, Ellis's 1853 section, Stübe 1895, Wohlstein's 1893–1894 articles, and four Gordon articles from 1934–1937. The Gordon batch adds 24 located appearances: 16 full bowl editions, of which 15 attach to existing exact-label or exact-number records and one is a new Harvard candidate, plus eight separately numbered museum bowls retained as new candidates. No uncertain identity was merged.

The public reading-room count is deliberately narrower than edition coverage. It currently exposes **35 scan-checked public-domain translations and 77 project-authored summaries**. Another 159 text records retain their citation and locator but withhold protected or not-yet-approved scholarly wording. Thus “112 readable text records” does not mean that only 112 bowls are known from editions: 209 objects have a stored text record, 54 have a translation record, and many more have edition-level references without a locally publishable transcription or translation. The five newly transcribed Wohlstein translations are withheld pending human publication review; one also awaits a second reading of embedded Hebrew strings. Three earlier own-work approvals no longer match the current content fingerprint and therefore fail closed instead of silently publishing changed text.

An importer defect was repaired in 137 Segal claim locators, with immutable before/after records and no changes to scholarly values or identity links. This explains the BM 117882 117ES/119ES pointer mismatch; its language uncertainty still needs catalogue review. The Penn review added eleven reported metadata claims and six follow-up leads. Current evidence has 52 triaged claim-field differences and 432 that require review, including 285 older decisions that must be revalidated against changed evidence. Five source-reported Penn relationships are stored separately from physical identity, with no automatic merges. The full decision history is preserved.

Of 327 media rows, 325 have explicit rights-ledger entries, with **zero completed rights assessments and zero media approvals**. A separate tested public-export path creates a narrow reference scaffold while withholding unapproved media; the research export remains private. No public dashboard has been deployed.

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
- [Public dataset manifest and gates](data/public/2026-09-05/manifest.json)
- [Checked identity review decisions](research/reviews/identity_review_2026-09-04.jsonl)
- [British Museum item-page mappings](research/enrichment/british_museum_item_pages_2026-09-04.json)
- [Montgomery text and concordance review](research/enrichment/montgomery_1913_review_2026-09-04.json)
- [Montgomery enrichment report](data/reports/montgomery_1913_enrichment_2026-09-04.md)
- [Scoping review alignment and corpus-scope findings](data/reports/scoping_review_alignment_2026-09-05.md)
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
ibi state          # does the corpus match what the last session recorded?
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

## Licence

Code is [MIT](LICENSE). Data, documentation, and research materials are
[CC BY 4.0](LICENSE-DATA). Attribute as:

> Gabai, Moses. *Incantation Bowl Index*. https://github.com/mikeesexton/incantation-bowl-index

Two things the grant does not reach, because they are not this project's to give:
the 35 Montgomery 1913 translations are public domain and are offered as such
rather than under a licence, and material from sources with narrower terms is
withheld rather than relicensed — Waller 2022 is CC BY-NC 4.0, so its 134 derived
rows carry only a citation and a link. Media are URLs; nothing here licenses an
image. Full scope and exceptions: [`docs/licensing.md`](docs/licensing.md).

When you reuse a record, cite the source it names rather than this index.

## Working here

Two AI agents share this repository — Claude Code and Codex — alongside Mike.
[`docs/project-rules.md`](docs/project-rules.md) is the single source of truth for how work is
done; `CLAUDE.md` and `AGENTS.md` are parity-kept extracts of it. Open every session with
`ibi state`, which compares the working database against the fingerprint recorded in the tracked
`data/db-state.json` — the corpus is not in Git, so a clean working tree does not mean an
unchanged corpus. Close every session with a `task-log.md` entry and a commit.

The field-level counterpart to this object-level corpus is the July 2026 systematic scoping
review in [`research/literature/`](research/literature/README.md).

## Repository boundaries

- `migrations/` contains the versioned SQLite schema.
- `src/bowl_index/` contains ingestion, collection, archive, dedupe, export, and reporting code.
- `research/` contains checked source manifests, search logs, coverage assessments, saturation measurements, and audit records.
- `data/public/<date>/` is the reviewed, gated dataset produced by `ibi export-public`; `data/reports/` contains aggregate reports. `data/exports/` holds local full-corpus research snapshots and is not tracked: their free-text fields, catalogue descriptions, and media URLs have had no release review.
- `data/private/ibi.sqlite3` and `data/private/archive/` are intentionally ignored because they contain the mutable research database and private evidence captures.
- `research/literature/` holds the July 2026 scoping review, its bibliography control, and its search log.
- `data/exports/` is ignored in full, as are the `dedupe_candidates`/`dedupe_evidence` dumps. Regenerate with `ibi export`.

Research exports retain text-row provenance and rights metadata but blank content unless its record is explicitly marked `public_ok`; raw source payloads also remain private. Media URLs, capture metadata, and free-text fields still require a separate release review. Historical “public-safe” labels overstate this boundary. Keep refreshed full research exports private; the separate public-export path applies a narrower set of publication gates. The private database remains the authoritative store for restricted research material.

The future dashboard should consume reviewed exports or a read-only API, never the private ingestion database directly. Scheduled collectors for a continuously running Mac mini belong in a later monitoring phase after review rules and backup policy are in place.

## Research console

Double-click **`bin/Incantation Bowl Index.app`**, or keep it in the Dock — it starts the console if it is not running, opens your browser, and never starts a second copy. `bin/stop-console.command` stops it. Or run `ibi serve` and open `http://127.0.0.1:8765` to use the private research console. It provides corpus-wide identity search, evidence dossiers, enrichment queues, and a reversible concordance workbench. The server refuses non-local bindings and should never be placed directly on the public internet. See the [research console guide](docs/research_console.md).
