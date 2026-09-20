# Licensing

Two licences, because this repository holds two different things.

| | Licence | Covers |
|---|---|---|
| **Code** | [MIT](../LICENSE) | `src/`, `tests/`, `migrations/`, `web/`, `config/`, `pyproject.toml` |
| **Everything else** | [CC BY 4.0](../LICENSE-DATA) | `data/public/`, `data/reports/`, `research/`, `docs/`, `README.md`, `task-log.md` |

Attribute as:

> Gabai, Moses. *Incantation Bowl Index*. https://github.com/mikeesexton/incantation-bowl-index

When you reuse a specific record, cite the source it names rather than this index.
The whole point of the dataset is that every assertion carries its own source and
locator; passing our aggregation off as the authority would defeat it.

## What the CC BY 4.0 grant does and does not reach

It reaches what this project authored: the schema and its vocabulary, the object
and identity records, the concordances and confidence judgments, the reports, the
documentation, the research manifests and review decisions, the index's own
descriptive summaries, and the selection and arrangement of the whole.

It does not reach material this project does not own. A licence cannot be granted
over someone else's work, and the index would be overclaiming if it pretended
otherwise — which is the same discipline it applies to provenance.

### Public-domain texts are not licensed, they are already free

The 35 Montgomery translations from *Aramaic Incantation Texts from Nippur*
(Philadelphia, 1913) and four scan-checked Wohlstein translations from
1893–1894 are published from United States public-domain sources. They are
marked `public_domain_expired` in the publication ledger and are **not**
offered under CC BY 4.0: applying a licence to public-domain material would claim
a right nobody holds.

The normalization applied to those texts — paragraph and punctuation spacing,
correcting OCR against the scan — is this project's editorial work and is covered
by CC BY 4.0. In practice: use Montgomery's words however you like, and credit the
index if you use its edited form.

Copyright terms vary by country. Pre-1930 US publication is decisive in the United
States; check your own jurisdiction if that matters to you.

### Facts about bowls are not owned by anyone

Which verse a bowl quotes, a client's name, a line count, a measurement, a museum
number, a formula type: these are facts. Recording them is not reproducing a
source's expression, which is why they can be published even when the edition that
established them cannot be.

The database of facts — its selection, arrangement, and verification — is the
project's own contribution and is licensed. Note that some jurisdictions
(UK, EU) recognise a database right distinct from copyright; the CC BY 4.0 grant
covers this project's database right in its own compilation.

### Where a source's own terms still apply

Some material is recorded from sources under licences narrower than CC BY 4.0.
Daniel James Waller's *The Bible in the Bowls* (Open Book Publishers, 2022) is
**CC BY-NC 4.0**: it forbids commercial use, so its content cannot be relicensed
here under CC BY 4.0, which permits it.

The 134 text rows derived from that catalogue are **published**, on the
`open_license` basis, by the project owner's decision of 20 September 2026. Their
whole content is a verse-citation list of the form `Biblical quotations: Zech. 3.2`
— what [`project-rules.md`](project-rules.md) calls a fact rather than the editor's
expression — and the identical information, from the same source at the same
locator, already exported as a `biblical_intertexts` fact. Publishing the fact while
withholding the text row stating it was incoherent, and the decision resolves it
toward publication.

**Waller's terms travel with those rows.** They are not relicensed under this
repository's CC BY 4.0. Each carries `rights_basis` = `open_license` and
`license_url` = the CC BY-NC 4.0 deed, so a consumer can tell them apart, and the
export manifest's `license_scope` names them and their count. If you build on those
rows, Waller's terms govern — including the non-commercial condition — not this
repository's. Two Martínez Borobio rows from *A Magical Bowl in
Judaeo-Aramaic* are also published under CC BY-NC 4.0: the source
transliteration and a clearly labelled project paraphrase. They carry the same
per-row licence link and attribution discipline.

The narrower-licence reasoning still applies to every text row whose
`content_status` is `withheld_consult_the_edition`: the pointer is ours to give,
the text is not.

### Third-party material recorded but not licensed here

- Bibliographic metadata — titles, authors, dates, DOIs, citations — is factual.
- Museum catalogue prose is **not** in this repository. Full-corpus research
  snapshots under `data/exports/` are deliberately untracked for that reason.
- Media are URLs only, and nothing here relicenses an image. Ten of 327 carry
  owner approvals based on their recorded public-domain or open-license status.
  Another 288 Penn rows carry the owner's exact approval for Bowlam's declared
  nonprofit educational, noncommercial use under Penn's current policy, with
  the required object credit and policy link. Those institutional terms remain
  narrower than this project's CC BY grant. The other 29 are withheld. Follow
  every URL and observe the holding institution's current terms.
- The July 2026 scoping review in `research/literature/` is this project's own
  work and is covered by CC BY 4.0. The works it discusses are not.

## For agents working in this repository

When you add a text row, record its rights basis in the publication ledger before
it can become public — `ibi ingest-text-publication`, never `texts.public_ok` by
hand. When a source's licence is narrower than CC BY 4.0, the decision is the owner's:
withhold the content and publish the pointer, or publish on the `open_license` basis
with the source's `license_url` recorded so its terms travel with the row. Do not make
that call yourself. See [`project-rules.md`](project-rules.md) → *Publishing text:
what belongs to whom*, and [`public_export_boundary.md`](public_export_boundary.md)
for what the export withholds.

None of this is legal advice.

## Product and access model

Payment is not the boundary. A rights-cleared service may use subscriptions,
institutional licences, grants, sponsorship, or no charge at all. The boundary is
whether this project owns or has permission to distribute the content exposed to
that audience.

The private vault may therefore be richer than either outward-facing product. It
can preserve a lawfully obtained scan, working OCR and a structured research
transcription while the public reference exposes only facts, citations and an
original summary. If a rights holder later grants a commercial licence, the paid
service may expose the licensed fields without copying the whole private record
or weakening the public export gate.

Commercial planning must identify rights at the contribution level. A book-level
agreement may not cover a chapter author's translation, a museum's bowl image, a
photographer's plate, or a third party's drawing. The commercial register must
therefore record rights holder, authority, territory, term, permitted uses,
display and export limits, attribution, royalty or fee, reporting, termination,
takedown and security obligations before launch.

Monetizable project-authored value includes concordances, claim histories,
cross-publication search, rights-safe structured facts, original summaries,
research workflows, saved workspaces, exports and APIs. Full protected text is an
optional licensed input to that service, not the service's only value proposition.
