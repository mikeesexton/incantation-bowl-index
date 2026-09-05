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

The 35 Montgomery translations in `data/public/` are from *Aramaic Incantation
Texts from Nippur* (Philadelphia, 1913). United States copyright has expired.
They are marked `public_domain_expired` in the publication ledger and are **not**
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

Accordingly the 134 text rows derived from that catalogue are **withheld** in
`data/public/`. They keep their citation, locator, and DOI so a reader can consult
the open-access original, and nothing of Waller's is republished. If you build on
those rows, Waller's terms govern, not this repository's.

The same reasoning applies to every text row whose `content_status` is
`withheld_consult_the_edition`: the pointer is ours to give, the text is not.

### Third-party material recorded but not licensed here

- Bibliographic metadata — titles, authors, dates, DOIs, citations — is factual.
- Museum catalogue prose is **not** in this repository. Full-corpus research
  snapshots under `data/exports/` are deliberately untracked for that reason.
- Media are URLs only. Zero of 325 have a completed rights assessment and none is
  approved for reuse, so nothing here licenses an image. Follow the URL and
  observe the holding institution's terms.
- The July 2026 scoping review in `research/literature/` is this project's own
  work and is covered by CC BY 4.0. The works it discusses are not.

## For agents working in this repository

When you add a text row, record its rights basis in the publication ledger before
it can become public — `ibi ingest-text-publication`, never `texts.public_ok` by
hand. When a source's licence is narrower than CC BY 4.0, withhold the content and
publish the pointer. See [`project-rules.md`](project-rules.md) → *Publishing text:
what belongs to whom*.

None of this is legal advice.
