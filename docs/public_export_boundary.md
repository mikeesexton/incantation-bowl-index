# What the public export excludes

`ibi export-public` is the only sanctioned way corpus data leaves this machine.
This document enumerates what it withholds and why, so the boundary can be read
without running the exporter and diffing its output against the database.

Counts below are from the export run on 20 September 2026 against corpus digest
`f03b960f967db427499c7c37ba8e9e06ea7dfbe5b4a5e985e6c4255a39de5297`
(1,969 candidate objects, 1,652 identities after resolved dedupe). Regenerate with:

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli export-public --destination /tmp/pubexport
```

The gates live in one place — [`src/bowl_index/projection.py`](../src/bowl_index/projection.py).
The reader API and the file exporter both build rows there, so the local console
and a published static export are the same bytes through the same code path. A
second implementation would be a second chance to publish something withheld.

**A gate here is a rights decision, not a convenience.** Putting withheld
material behind a login does not clear it. Moving anything across this boundary
means recording a decision with `ibi ingest-text-publication` or
`ibi ingest-rights-review` against a manifest under `research/reviews/` — see
[`project-rules.md`](project-rules.md) §1 and [`licensing.md`](licensing.md).

> **Two decisions are recorded but not yet applied.** The counts in this document
> describe the boundary as it stands today. Two owner decisions of 20 September
> 2026 sit in manifests waiting to be ingested, and both loosen it:
>
> | Decision | Manifest | Effect on ingest |
> |---|---|---|
> | The 134 Waller rows are equally publishable | `research/reviews/waller_2022_text_publication_2026-09-20.json` | Texts published 112 → 246, withheld 159 → 25 |
> | A recorded `public_domain`/`open_license` label is the rights decision | `research/reviews/media_rights_permissive_candidates_2026-09-20.json` | Media approved 0 → 10, withheld 327 → 317 |
>
> Together they lift 122 bowls' `reading_score`, taking the reading room's default
> pool from 70 bowls to 191. Regenerate the counts below once both are applied.

---

## Tier 1 — Tables never exported

27 of the database's 34 tables have no public representation at all. This is the
research apparatus: how records were found, compared, argued over, and decided.
(Seven of the fourteen exported names are derived views rather than stored tables,
which is why the two figures do not sum to 34.)

| Table | Rows | What it holds |
|---|---|---|
| `dedupe_evidence` | 34,765 | Pairwise match evidence |
| `dedupe_candidates` | 34,763 | Machine dedupe workspace |
| `claims` | 7,218 | Raw claims with verbatim quotation and notes; `facts` is the gated derivative |
| `claim_conflict_review_history` | 962 | Every revision of a conflict decision |
| `claim_conflict_reviews` | 644 | Conflict adjudications |
| `search_queries` | 361 | The multilingual discovery matrix |
| `media_rights_reviews` | 327 | Rights ledger for media |
| `events` | 212 | Provenance and session event trail |
| `text_publication_reviews` | 163 | The ledger that decides `public_ok` |
| `claim_locator_corrections` | 137 | Citation-pointer repairs with originals |
| `source_scope_reviews` | 112 | What kind of work each source is |
| `leads` | 65 | Open research leads |
| `captures` | 55 | **Source scans and captured files** |
| `document_assessments` | 53 | Completeness and transformation states |
| `source_corrections` | 52 | Source metadata repairs |
| `text_proofreading_reviews` | 40 | Scan-checked revisions with retained originals |
| `museum_concordance_reviews` | 40 | Dated museum checks |
| `publication_registry` | 36 | Internal publication-key resolution |
| `accuracy_audit_reviews` | 80 | Stratified identity-accuracy audit (QA-003) |
| `search_runs`, `manual_audits`, `coverage_targets`, `saturation_sweeps`, `object_relationship_assertions`, `merge_log`, `contributor_aliases`, `schema_migrations` | 17 / 14 / 12 / 3 / 5 / 0 / 0 / 16 | Discovery, QA, and schema bookkeeping |

`captures` is the sharpest of these: it points at lawfully obtained source scans
held in the private vault. Private possession does not authorize distribution,
and the export never names a capture or its storage path.

## Tier 2 — Media: all 327 withheld

`media.jsonl` is empty and `media.csv` is a bare header. **Not even the URLs
survive.**

| `rights_status` | Rows |
|---|---|
| `unknown` | 288 |
| `copyrighted` | 29 |
| `public_domain` | 5 |
| `open_license` | 5 |

Zero have a *completed* rights assessment, so the gate fails closed on all 327 —
including the ten whose status looks permissive. A status is not a decision.

## Tier 3 — Texts: 159 of 271 blanked

Only `content` is nulled. A withheld row keeps `editor`, `language`, `script`,
`text_type`, `locator`, `access_citation`, `access_locator`, `access_url` and
`access_status`, so a reader can always find the edition and consult it.

| `text_type` | Released | Withheld |
|---|---|---|
| summary | 77 | 139 |
| translation | **35** | 19 |
| transliteration | 0 | 1 |

Genre is not the gate — rights are. All 35 released translations are Montgomery
1913, whose US copyright has expired. The largest withheld block is 134 rows
from Waller 2022, which is CC BY-NC 4.0 and therefore cannot be relicensed under
this repository's CC BY 4.0.

Released rows by editor: Incantation Bowl Index card line (68), James A.
Montgomery (35), Incantation Bowl Index summary (7), two discovery-campaign
summaries. Withheld by editor: Waller (134), Wohlstein (5), Schøyen Collection
specialist (4), Index summary (3), Isbell (2), and six others.

## Tier 4 — 836 claims dropped from `facts`

7,218 claims become 6,382 facts. A claim is publishable as a fact when its field
sits in a comparison group; 37 field types sit outside one. The reasons are
recorded per field in `EXCLUDED_CLAIM_FIELDS` in
[`identity.py`](../src/bowl_index/identity.py).

**Third-party expression** — someone else's prose, not ours to pass on:

| Field | Claims |
|---|---|
| `catalogue_description` | 344 |
| `dimensions_source_text` | 203 |
| `catalogue_shelf_mark` | 170 |

**The market cluster** (~45 claims) — `sale_estimate` (17), `sale_result` (8),
`offer_price` (3), `sale_offer` (3), `former_location` (3), `asking_price` (2),
`exhibition_history` (2), and one each of `sale_price`, `sale_reserve`,
`starting_price`, `current_bid`, `sale_location`, `sale_estimate_or_opening`,
`acquisition`, `export_status`, `collection_context`.

A provenance statement describes what a source reports. It does not legitimize
ownership, export history, or authenticity, and the index should never read as
though publication settles any of those.

**Assessments of claims, not claims** — `findspot_evidence_level` (34),
`physical_record_ambiguity` (10), `historical_collection` (6),
`scribal_relationship` (4), `provenance_quality` (2), `identification` (2), and
others. These grade or relate claims; they belong to `events`,
`object_relationship_assertions`, or the review ledgers rather than to a
comparable field value.

## Tier 5 — Columns blanked inside exported tables

| Table | Dropped |
|---|---|
| `objects` | `summary`, `created_at`, `updated_at` |
| `sources` | `container_title`, `publisher`, `url`, `access_status`, `rights_status`, `notes`, timestamps |
| `claims` → `facts` | `id`, `appearance_id`, `value_text`, `value_json`, `normalized_value`, `quotation`, `notes`, `supersedes_claim_id`, `created_at` |
| `texts` | `appearance_id`, `public_ok`, `notes`, `created_at` |
| `appearance_object_links` | free-text review rationales; the relation structure stays |

`quotation` and `notes` recur across these: the verbatim snippet that grounds a
claim is the source's expression, and a note is working commentary written for
review rather than for readers.

---

## What does survive

The export is 7.4 MB across 14 tables: 1,969 objects, 6,382 facts, 2,268
appearances and links, 4,741 identifiers, 1,063 editions, 862 sources, 271 text
rows (112 with content), 206 works, 114 contributors, 33 publications. It
carries its own `manifest.json` with the attribution string, the CC BY 4.0 grant
and its scope, and the included/withheld counts.

That grant reaches this project's own contribution — the schema, the records,
the concordances and confidence judgments, the summaries, and the selection and
arrangement. It does not reach material the project does not own, and the 35
Montgomery translations are public domain rather than licensed.

Each published text row carries `rights_basis` and `license_url`, so a row whose
source licence is narrower than CC BY 4.0 can be identified as such rather than
being read as covered by the export's headline grant. Both columns are null on a
withheld row: they state the terms content is published under, and a row with no
content has none. `license_scope` in the manifest is derived from that ledger
rather than written by hand, so it cannot drift from what the export actually
contains.
