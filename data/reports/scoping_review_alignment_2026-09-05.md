# Aligning the index with the July 2026 scoping review — 5 September 2026

## What this review did

Read the imported [systematic scoping review](../../research/literature/README.md)
— 31 pages, coverage 1853 to July 2026 — together with its 26-record
bibliography control and 14-row search log, then checked the working corpus
against it. Inspected the schema, the claim vocabulary, the identifier layer,
the source table, the roadmap, and the test suite.

It did **not** re-read the 753 sources, verify any reading, authenticate any
object, or do new external research. Every count below comes from the working
database at corpus digest `106516128233`.

## Assessment

The index is in better shape than the field usually manages. The core
distinction — physical object versus source appearance — is right and is
enforced. Reviews are append-only and evidence-bound. The 4 September quality
review found its own permissive comparison rules and said so in public. The
public-export path fails closed. That is unusually honest infrastructure.

The gap is not rigour. It is **scope**: the index has been built from what is
*findable online* — 567 of 753 sources are museum records — and the scoping
review describes a field whose primary evidence is *printed editions*. The two
have not yet met. Everything below follows from that one fact.

---

## 1. The editions that publish bowls are largely absent from `sources`

Seventeen of the works the review names as foundational have no author or title
match in `sources` at all:

| Absent | What it is |
|---|---|
| Ellis 1853, in Layard | the beginning of JBA bowl scholarship |
| Pognon 1898 | the foundational Mandaic corpus (Khouabir) |
| Myhrman 1909 | Hilprecht material |
| Isbell 1975 | the concording compilation of all then-published bowls |
| Yamauchi 1967 | the early Mandaic corpus, grammar and glossary |
| Naveh & Shaked 1985/87, 1993 | the modern standard for bowl editions |
| Müller-Kessler 2005 | the Hilprecht/Jena re-editions |
| Gordon, 1934–1984 | dozens of bowl editions across many venues |
| Rossell 1953, Obermann, Kaufman | the mid-century layer |
| Morony 2003, 2007 | the basic social-historical statements |
| Mokhtarian 2015, Harari 2017 | the major syntheses |
| Häberl 2015, Frim 2021, Secunda 2025 | current disputes |
| Gross & Scarlassara 2025 | cross-script transmission, object-level |
| Mackenzie et al. 2020 | Schøyen provenance ethics |

Gordon is likely the largest single unrecorded publisher of bowls in the index.

Seeded as `research/seeds/scholarly_bibliography_2026-09-05.jsonl` (21 records,
citations transcribed from the review and **not** independently verified) and
`research/leads/scholarly_bibliography_gaps_2026-09-05.jsonl` (10 leads).
Neither has been ingested. → `SCHOL-002`

## 2. The index models *reporting* sources, not *publishing* editions

This is the structural version of finding 1, and it explains why `TEXT-001`'s
metric has to be called a proxy.

`identifiers.source_id` records who **reported** a designation. That is correct.
But there is no record of the publication being **designated**. Concretely:

```
Isbell 1975::08   reported by   Waller 2022, The Bible in the Bowls
Isbell 1975::22   reported by   Center for Online Judaic Studies
MRLA 8::12        reported by   (Hilprecht collection page)
```

Seventeen objects carry `Isbell 1975::NN`; Isbell 1975 has no row. Nineteen
carry `MRLA 8::NN`, two carry `TMH 7::NN`, eight carry `Naveh-Shaked
1985`/`1993` — none of those four publications has a row either.

So the corpus can answer "who told us this bowl is Isbell no. 8" and cannot
answer "which bowls does Isbell publish", "what is its access status", or "has
anyone collated it". A publication-scheme identifier proves a designation
exists; it says nothing about an edition. Until publications are first-class,
raising `publication_reference_pct` toward its 80% gate measures the wrong
thing — and it is one of only five quantitative conditions on the Mac mini
handoff gate. → `SCHOL-004`, and re-specify `TEXT-001`

## 3. The claim vocabulary has outgrown the comparison model

`claims.field` is free text and now holds about 100 distinct values, many of
them singletons and synonyms: `provenance` / `provenance_summary` /
`provenance_quality`, `findspot` / `findspot_or_origin` / `findspot_evidence` /
`findspot_evidence_level` / `findspot_assessment`, `client` / `clients` /
`client_or_beneficiary`, `text_parallel` / `textual_parallel`.

Conflict detection compares claims only within the seven groups hard-coded in
`identity.CORE_COVERAGE`. A field outside those groups is never compared and
never flagged. The clearest case is **`catalogue_language_codes`**: 205 objects
carry an NLI MARC language code (`heb`) that is invisible both to language
coverage and to conflict detection, even where an edition-based
`inscription_language` claim on the same object says Jewish Babylonian Aramaic
or Mandaic. That disagreement is not noise — it is exactly the
catalogue-classification-versus-scribal-tradition problem the review devotes
§2.5 to, and the index is currently silent about 205 instances of it.

So the "337 flagged instances, 284 pending" queue is an undercount by
construction, not a measured total. That should be said in the roadmap.

By contrast `dimensions_source_text` (203 claims, e.g. `גובה: 221 ממ, הקף: 443 ממ`)
is correctly excluded: it is the retained original string behind a structured
claim. Note that it reads **circumference**, not diameter — the same
measurement-convention trap already logged for the Penn/Montgomery heights.
→ `QA-008`

## 4. The field model stops where the scholarship starts

The review's Phase 2 ledger specifies ten field groups. The index's coverage
model has seven, all physical or bibliographic:

| Review field group | In `CORE_COVERAGE`? | In the corpus |
|---|---|---|
| Identity, Provenance, Physical | yes | well populated |
| Text | partly | 1 transcription, 48 translations |
| People | **no** | 42 `client`, 13 `clients`, 3 `client_or_beneficiary` |
| Ritual | **no** | 27 `text_purpose`, 10 `formula_genre`, 1 `named_demon` |
| Intertexts | **no** | 134 `biblical_quotations` from Waller 2022 |
| Visual | **no** | 25 `iconography` |
| Scholarship | **no** | 16 `handwriting_attribution`, 2 `handwriting_group` |
| Ethics/QA | partly | rights ledger yes, evidence grade no |

Those claims exist. They are simply outside the model, so they do not appear in
coverage, do not get conflict-checked, and cannot be queried as a group. The 134
Waller biblical quotations are the single most analytically valuable thing in
the corpus after Montgomery, and nothing in the roadmap currently tracks them.
→ `META-006`

## 5. Two interpretive guardrails the review requires and the index lacks

**Roles behind a name.** Eleven objects carry `handwriting_attribution` claims
whose values are women's names — Kedar 2019's contested argument that named
women wrote those bowls. Saar 2024 and Manekin-Bamberger 2025 respond by
separating author, textual voice, copyist, producer, commissioner, client, and
beneficiary. Storing a contested authorship attribution in a field named
`handwriting_attribution` asserts more than Kedar's source does. The claim
should be kept — it is properly source-attributed — but it needs an explicit
role and an explicit dispute link. → `META-007`

**Evidence grades.** The review grades object evidence A–D: A needs image plus
edition, D is unsuitable for historical inference. The index has `record_status`
(candidate/probable/confirmed), which measures identity confidence, not evidence
quality. They are different axes: a confirmed identity can rest on a dealer
photograph. → `TEXT-007`

## 6. Language parity, measured

The review's gap 2 asks for Mandaic, Syriac, Pahlavi and pseudo-script
infrastructure equal to JBA's. Against the EJCM working counts the review
quotes:

| | in the index | EJCM working count | note |
|---|---:|---:|---|
| JBA / Aramaic | 379 | ~500 | includes 129 generic "Aramaic" |
| Mandaic | 77 | ~125 | ~60% |
| Syriac | 69 | ~50 | exceeds the working count |
| Pahlavi | 2 | — | effectively unpopulated |
| pseudo-script | 35 | — | |
| **no language claim at all** | **819** | | 52% of records |

Syriac is genuinely ahead. Mandaic is behind and Pahlavi is absent, and both
have an obvious cause: Pognon 1898 and Yamauchi 1967 are not in the corpus.
→ `META-008`

## 7. The repository had no commits

827 files, two days of intensive work, zero commits — which is also why the
4 September quality review noted it had no diff to use as a baseline. Fixed:
see `task-log.md`. The corpus itself is still outside Git by design, so
`ibi state` now records a per-table fingerprint in the tracked
`data/db-state.json`.

---

## What to change about work already done

Nothing needs undoing. Three things need re-labelling:

1. **Say that the conflict queue is an undercount.** "284 pending" reads as a
   measured backlog. It is the backlog *within seven hard-coded field groups*.
2. **Say that discovery saturation is source-class-bounded.** Two sweeps under
   1% net-new is a real result about the searched classes. Printed editions were
   not a searched class, and finding 1 is what that looks like from outside. The
   roadmap already carries the right caveat; the README's phase-one paragraph
   does not.
3. **Stop treating `publication_reference_pct` as a release gate** until
   publications are first-class records (finding 2). Measuring it harder will
   not make it mean more.

## What to change about what comes next

The current priority list is ordered by *queue depth* — 284 revalidations first.
Depth-first on a queue whose denominator is wrong is the wrong order. Two
changes:

- **Promote `SCHOL-001`** (acquire Waller's 2025 publication list) to the front.
  It is the only external control on completeness the field offers, it is a
  library request rather than weeks of work, and it has been the standing first
  priority in the scoping review since July. Everything about "how complete is
  this index" is guesswork until it arrives.
- **Do `QA-008` before more of `QA-002`.** Widening the comparison model changes
  how many instances there are to revalidate. Revalidating 284 first and then
  widening means doing part of it twice.

The revalidation queue, the Penn and BM concordances, the rights ledger, and the
Mac mini gate all stay where they are. This is a change of order and of framing,
not of direction.

## Reproduction

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
PYTHONPATH=src .venv/bin/python -m bowl_index.cli state
PYTHONPATH=src .venv/bin/python -m bowl_index.cli roadmap
```

The queries behind findings 1–6 are ad-hoc reads of `data/private/ibi.sqlite3`
against `sources`, `claims`, and `identifiers`; finding 2's check — every
`publication object key` prefix against the source table — is worth making a
standing test under `QA-008`. No corpus writes were made by this review.
