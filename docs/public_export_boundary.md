# What the public export excludes

`ibi export-public` is the only sanctioned way corpus data leaves this machine.
This document enumerates what it withholds and why, so the boundary can be read
without running the exporter and diffing its output against the database.

Counts below are from the export run on 20 September 2026 against corpus digest
`abf8105be9339a684fdcb94fa7b80c9168043121deb5c0a277ac2b27d0baf5c4`
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

## Tier 1 — Tables never exported

27 of the database's 34 tables have no public representation at all. This is the
research apparatus: how records were found, compared, argued over, and decided.
(Eight of the fifteen exported names are derived views rather than stored tables,
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

## Tier 2 — Media: 317 of 327 withheld

Ten reviewed resources survive with their URL, attribution, rights statement,
rights locator and licence URL. The other 317 do not emit a row; **not even their
URLs survive.**

| `rights_status` | Included | Withheld |
|---|---:|---:|
| `unknown` | 0 | 288 |
| `copyrighted` | 0 | 29 |
| `public_domain` | 5 | 0 |
| `open_license` | 5 | 0 |

The ten permissive rows have current evidence-bound owner decisions. A status by
itself is still not a decision, and every unknown or copyrighted row fails closed.

## Tier 3 — Texts: 25 of 271 blanked

Only `content` is nulled. A withheld row keeps `editor`, `language`, `script`,
`text_type`, `locator`, `access_citation`, `access_locator`, `access_url` and
`access_status`, so a reader can always find the edition and consult it.

| `text_type` | Released | Withheld |
|---|---|---|
| summary | 211 | 5 |
| translation | **35** | 19 |
| transliteration | 0 | 1 |

Genre is not the gate — rights are. All 35 released translations are Montgomery
1913, whose US copyright has expired. The 134 Waller 2022 summary rows are
released under CC BY-NC 4.0 and carry that narrower licence on each row; they
cannot be relicensed under this repository's CC BY 4.0.

Released rows by editor: Daniel James Waller (134), Incantation Bowl Index card
line (68), James A. Montgomery (35), Incantation Bowl Index summary (7), and two
discovery-campaign summaries. The largest withheld editor groups are Wohlstein
(5), Schøyen Collection specialist (4), Index summary (3), and Isbell (2).

## Tier 4 — 866 claims omitted from public `facts`

7,218 claims first become 6,382 short fact candidates. Of those, 6,352 are
emitted and 30 non-public-domain source-wording values fail closed: 28 longer
statements and two short rows containing embedded quotation. The
other 836 claims never become candidates because their fields sit outside the
comparison model; 37 field types are excluded. The reasons are recorded per
field in `EXCLUDED_CLAIM_FIELDS` in
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

The emitted facts carry `release_class`. This is conservative triage, not an
automated copyright decision: 6,127 are ordinary factual metadata, 40
prose-prone rows come from public-domain sources, and 185 are short source
claims with no embedded quotation. The 30 non-public-domain candidates are the private priority
wording-review queue and do not emit a fact row.
The derived `facets` table supplies 3,245 project-authored browse labels with the
source field, source and locator retained; it never replaces the raw claim.

---

## What does survive

The export spans 15 tables: 1,969 objects, 6,352 facts, 3,245 controlled facets,
2,268 appearances and links, 4,741 identifiers, 1,063 editions, 862 sources, 271 text
rows (246 with content), 10 approved media rows, 206 works, 114 contributors,
and 33 publications. It
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

Each published media row similarly carries its attribution, rights statement,
rights locator and licence URL from the current media review. Those fields are
absent along with the whole row when no current approval exists.
