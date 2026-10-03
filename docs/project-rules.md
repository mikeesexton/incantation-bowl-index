# Project rules

Single source of truth for how work is done in this repository. `CLAUDE.md` and
`AGENTS.md` carry a short extract and point here; they are kept byte-identical
below their title line by `tests/test_agent_docs_parity.py`. Change a rule
*here*, then re-run the parity test.

Two AI agents work in this repository — Claude Code and Codex — plus Mike. They
share one working directory and one database. Most of what follows exists so
that nothing silently overwrites anyone else's work.

---

## 1. Research rules

These are the original project rules and they take precedence over convenience.

- Preserve the distinction between a physical object and a source appearance.
- Every candidate appearance must cite a source. Every normalized assertion must
  retain its supporting source and locator.
- Do not erase conflicting claims; store them separately with certainty and notes.
- Do not automatically merge objects except on an exact, trusted identifier with
  corroborating context. Queue all other matches for review.
- Treat fragments, lost or unlocated bowls, pseudo-script objects, uncertain
  identifications, and suspected fakes as in scope and label them explicitly.
- Never bypass paywalls, logins, CAPTCHAs, robots exclusions, or site access
  controls.
- Record copyright and reuse status independently for every text, translation,
  image, and capture. Private archival availability does not imply public reuse
  permission.
- Keep the working database and source archive out of Git. Commit code,
  migrations, documentation, source manifests, and reproducible aggregate
  exports only.
- Use UTC ISO 8601 timestamps and stable `IBI-*` identifiers.

### Three access layers

The project maintains three separate surfaces. A record never moves from one to
another merely because it has been digitized, because access is free, or because
access is paid.

| Layer | May contain | Gate |
|---|---|---|
| **Private research vault / Mike Access** | Lawfully obtained source scans, working OCR and rich text, research notes, page-image coordinates, and protected scholarly expression needed for Mike's personal analysis | Record provenance, content hash, completeness, access restrictions, and any library copying conditions; keep outside Git and restrict every interface to Mike alone |
| **General public reference** | Bowl facts, citations, relationships, project-authored summaries, public-domain material, compatible open-license material, and specifically permitted content | Evidence-bound public-release decision; private captures and unapproved text or images fail closed |
| **Paid licensed service** | Research tools plus public-domain, compatible open-license, project-authored, or contractually licensed material | Documented rights chain and executed license for the actual text, transcription, translation, image, territory, term, display/export behavior, and revenue arrangement |

The reader has distinct operational visibility tiers inside that rights model:
Mike's private reader (localhost or a single-user authenticated remote surface),
the shared named-user scholar preview, and the future open public library. The
terms **Mike Access** and **Mike-facing** always mean that Mike is the sole user.
They are personal research access, not release, publication or distribution, and
must expose the complete lawfully held research record through
`PrivateResearchProjection`, including protected text and recorded images. Do
not apply public text or media-reuse gates to Mike Access.

For Mike Access, extract and retain the inscriptions, scholarly transcriptions,
transliterations, and translations that occur in lawfully held sources, with the
scholar's attribution, exact object and page locator, capture hash, and any
uncertainty or editorial intervention. Preserve the scholar's translation when
it is available; making a new translation is optional research, not a condition
for private access. Retain lawfully obtained bowl photographs and plates in the
private vault when source-specific copying conditions allow it, even when public
reuse is unapproved. A link to a book or an image is a useful pointer, but does
not count as capture of the inscription, translation, or image itself. Keep
protected payloads and their ingestion manifests outside Git. Record private
availability separately from public-release status, and never let a public gate
remove material from Mike's personal view.

The shared scholar preview and public library consume the reviewed
public-reference projection and continue to fail closed. Cloudflare Access by
itself does not define the tier: a route open to any person besides Mike is a
shared surface and may not consume the private projection. A remote Mike Access
route must be identity-restricted to Mike, prevent access through alternate
deployment hostnames, disable caching and indexing, and never place private
captures or database files in a repository.

Private possession does not authorize public distribution. Free public access
does not make protected expression reusable. Charging does not cure missing
permission. A private record may remain private permanently while its factual
claims and bibliographic pointer appear in the public reference.

For Library of Congress work, record what staff permitted for each item and
visit. Do not treat onsite access as permission to scan a complete work, and do
not treat permission to make a personal research copy as permission to publish
or license it.

### What a source can and cannot verify

A publisher page, repository record, or museum catalogue entry can verify a
title, a date, a declared argument, an accession number, or a current location.
It cannot verify a reading, a translation, a measurement convention, a findspot,
or an identification. Those need the edition or the excavation report. The July
2026 scoping review is itself a secondary source under this rule: see
[`research/literature/README.md`](../research/literature/README.md).

### Evidence grades

Grade object evidence A–D, following the scoping review §1.4:

- **A** — published photograph or drawing *plus* a usable edition; documented
  collection history where available.
- **B** — a scholarly edition exists, but image, provenance, or full
  archaeological context is absent.
- **C** — provisional: abstract, catalogue notice, old hand copy, unverified
  reading, or an object discussed without documentation.
- **D** — unsuitable for historical inference: modern adaptation, dealer
  description, decontextualized online image, or a claim whose ancient source
  cannot be traced.

The grade is a property of the evidence for a specific assertion, not a verdict
on the object or on the scholar.

### Mike's standing rulings

Decisions Mike has made that settle a class of question. Apply them; do not
re-ask. Record each application in a manifest with the ruling named in its
evidence notes.

- **One designation is one bowl** (2026-09-27). Records that share one
  institution- or collection-scoped designation (a museum number, a shelfmark,
  a private-collection number) are the same bowl unless there is evidence that
  they differ. Differences of spelling, scheme, or completeness are not such
  evidence; conflicting physical facts, texts, or clients are. Record the
  decision with `ibi ingest-dedupe-review`, using `create_candidate` when the
  generated queue missed the pair.
- **Late-antique incantation bowls only** (2026-09-27). Later metal bowls,
  such as medieval Islamic magic-medicine bowls, are outside the corpus. Keep
  the record and its source, and mark it `rejected` / `non_bowl` with
  `ibi ingest-object-scope`.
- **Dated negative evidence is not current** (2026-09-27). A source saying a
  bowl was "unpublished" or "in preparation" as of its own date is not a
  no-known-edition finding. Keep such bowls as follow-up leads for later
  publication searches.

### Reader editorial policy — streamline (Mike, 2026-10-01)

Streamlining is a project-wide requirement. Default to the shortest presentation
that helps the reader understand the bowl. Extra information must earn its place.

- Show each useful fact once. Keep source citations, locators, URLs, MMS IDs,
  related-object pointers, check dates and ingestion notes in Sources or research
  details; never repeat them beside every fact.
- Omit empty sections and empty disclosure controls. Remove generic instructions
  such as “consult the sources” and repeated boilerplate caveats.
- Give a translation one brief attribution/status line. Keep full bibliographic,
  editorial and access metadata in Sources; retain required licence attribution.
- Summarize a meaningful limitation in one sentence beside the reading, for
  example “Translation covers the opening; later passage reportedly unintelligible.”
  Do not add a separate commentary panel merely to explain the same thing again.
- Use consistent typography, casing, spacing and indicators for disclosures.
- Preserve complete source records and substantive uncertainty in the underlying
  research data. Retention is not an instruction to display everything.
- Review the rendered bowl page for repetition and visual clutter before calling
  a reader change finished. Apply improvements across the corpus, not just examples.

### Separate the roles behind a name

Never collapse author, textual voice, copyist, producer, commissioner, client,
and beneficiary into one field. A first-person feminine text does not establish
a female scribe; a client named on a bowl is not its author; a "rabbi" in a bowl
may be the client. Where a source makes an attribution, store *that source's*
attribution with its role and its uncertainty, and do not upgrade it.

### Publishing text: what belongs to whom

Three layers sit on every published bowl, and only the first is free.

| Layer | Whose |
|---|---|
| The Aramaic written on the clay | Nobody's. ~1,500 years old. |
| A scholar's transcription of it | Usually theirs. Reading damaged letters, restoring gaps, and dividing words are editorial judgments. |
| A scholar's translation | Theirs. A translation is a derivative work. |
| Their analysis | Theirs. |

So the boundary is **not** "text yes, analysis no". A modern edition's transcription
and translation are the part their judgment created, and Germany has an explicit
right for scholarly editions of public-domain works.

Text is published only on a recorded basis:

- `public_domain_expired` — pre-1930 US publication. Montgomery 1913, Pognon 1898,
  Myhrman 1909, Schwab 1891, Ellis 1853: the whole early corpus.
- `open_license` — Waller 2022 (Open Book Publishers), Abudraham 2026, and other
  open-access editions, on their own licence terms and with attribution.
- `permission` — written, with a locator.
- `own_work` — the index's own summaries and any reading we make from our own images.

Everywhere else, **withhold the text and point at it**. A withheld row keeps its
`text_type`, language, script, editor, the exact locator, the citation, a resolvable
link, and the source's access status. A reader must always be able to find the text
even when they cannot read it here. The `editions` table does the same at object
level: which publications carry this bowl, and where.

Facts about a text are always publishable. "This bowl quotes Zechariah 3:2",
the client's name, the line count, the formula type, the demons invoked — those are
facts, not the editor's expression.

Watch the source's own licence, though, because a narrower one travels with the
material. Waller 2022 is CC BY-NC 4.0, which forbids commercial use and therefore
cannot be relicensed under this repository's CC BY 4.0. Its 134 fact-like
verse-citation rows are published by an explicit owner decision with their
attribution and CC BY-NC licence URL; that narrower licence still governs them.
Check the source's licence before approving anything derived from it, and see
[`licensing.md`](licensing.md).

A source's copyright status is necessary but not sufficient. The editorial state of
the stored row is declared too, because a normalized reading text produced from a
scan is not the same object as the printed page. Approvals are bound to a content
fingerprint: a later proofreading revision revokes the approval automatically rather
than carrying it silently onto changed text.

Record decisions with `ibi ingest-text-publication` against a manifest under
`research/reviews/`, and check [`licensing.md`](licensing.md) for what this
repository can and cannot license. Never set `texts.public_ok` by hand — it is derived from the
ledger and will be overwritten on the next sync.

### Script is not religion

Script is evidence for a scribal tradition, not proof of the religion of a
client or a practitioner. Keep catalogue language codes, edition-based language
attributions, and script observations as separate claims. They disagree often,
and the disagreement is informative.
Report a catalogue's stated bowl language as that language in headings and browse
categories (Mike, 2026-10-01). Do not add “catalogued as” qualifiers or suppress the
label because its cataloguing rationale is unknown. Seek clarification from the
institution when needed; do not reinterpret a language code as a script.

---

## 2. Two-agent working rules

### Before you touch anything

```sh
git -C . status --short          # the tree must be clean, or you must know why
PYTHONPATH=src .venv/bin/python -m bowl_index.cli state
```

`ibi state` compares the working database against the fingerprint recorded in
`data/db-state.json`. The database is not in Git, so this file is the only way a
clean working tree tells you the truth.

- `match` — the corpus is where the last session left it. Proceed.
- `drifted` — someone changed the corpus without recording it. **Stop and find
  out who.** Read `task-log.md` and `git log`. Do not write to the corpus until
  the drift is explained; an unexplained drift plus your own writes is
  unrecoverable without a backup restore.
- `unrecorded` — no baseline. Only expected on a fresh clone.

Then read the top entry of [`task-log.md`](../task-log.md).

### While you work

- **One workstream per session.** Claim the task IDs you are taking in
  `task-log.md` before you start, not after. The workstreams are `DISC`, `CONC`,
  `TEXT`, `META`, `RIGHTS`, `OPS`, `QA`, and `SCHOL`.
- **Every corpus write goes through a manifest.** Public-domain, permissively
  licensed, and project-authored manifests are checked in under `research/`.
  A manifest containing protected source text, transcription, translation,
  quotation, or other private expression lives under
  `data/private/manifests/` and is transferred and backed up with the private
  vault; Git may retain only a content-free receipt and hash. Never hand-edit
  the database. The manifest is the reviewable artifact and it makes the corpus
  reproducible; a direct `UPDATE` is invisible to review and to the other agent.
- **Append, never overwrite.** Reviews, corrections, and revisions keep their
  originals. If a decision turns out wrong, add a superseding decision.
- **Back up before a batch that changes many rows.** Copy the database to
  `data/private/backups/before-<slug>-<UTC timestamp>.sqlite3`. Keep the last
  ten; that directory is already large.
- An earlier lawful project capture may be transferred from a local rehearsal
  with `ibi ingest-capture-receipts`. The private manifest binds the original
  database, retrieval receipt, archived bytes and original robots evidence by
  hash. This preserves the original retrieval row and makes no new network
  request or access-permission claim. It cannot replace an existing capture.
- Researcher-supplied local files can be archived with `ibi ingest-deposits`.
  The manifest binds file hashes, work assignments, stable capture IDs and a UTC
  deposit time; whole-batch validation precedes append-only intake. New sources
  may be declared explicitly, but existing sources and receipts cannot be
  replaced. Local deposits imply no HTTP retrieval or access-control decision.
- Private reading batches can declare stable text/media `id` values in
  `ibi ingest candidate`, a UTC text `created_at`, and a media `capture_id`
  belonging to the same source. These allow exact rehearsal against an existing
  appearance. Reused IDs must match the retained evidence; they cannot replace
  rows or silently alias another ID. Earlier source-checked drafts remain in
  their correction snapshots, and replay cannot revert them. JSONL intake rolls
  back the batch if any record fails.
- A new-source JSONL record may also declare UTC `created_at` to reproduce its
  initial creation/update timestamps during rehearsal and production. Replaying
  it never replaces an existing source's lifecycle timestamps.
- If an archived PDF turns out to be a different work, keep the works separate.
  Repair its source assignment with `ibi ingest-capture-source-corrections`
  against a hash-bound manifest. The immutable ledger retains the complete
  original retrieval snapshot; the correction changes only the work association.
  An existing document assessment requires a separate ledger repair and cannot
  be silently reassigned by this command.
- `ibi ingest-catalogue-metadata` repairs copied catalogue pointers and display
  labels against complete before snapshots and hash-bound evidence. Its immutable
  ledger preserves earlier rows; replaying an earlier candidate import resolves
  the corrected appearance and cannot restore superseded identifier or claim
  metadata. This narrow command does not change identity links, source attribution,
  readings or physical claims. When source pages themselves disagree, retain both
  reports and correct only their attribution; do not turn a pointer repair into
  an accession adjudication. Research exports redact ledger snapshots because an
  appearance's original payload may include protected expression.
- `ibi ingest-source-corrections` repairs copied bibliographic metadata against
  hash-bound evidence, retaining complete immutable before/after source fields.
  Source imports cannot restore a field value superseded in that ledger; unrelated
  new metadata remains importable. Correction timestamps come from the manifest's
  UTC review time so trial and production runs reproduce the same source record.
- `ibi ingest-text-metadata` repairs a copied text type, locator, language or
  script against hash-bound evidence, retaining complete immutable before/after
  snapshots. It cannot change the wording or source association. A classification
  repair invalidates earlier reading checks; renew them against the source through
  a new proofreading manifest. Earlier candidate imports cannot restore a retained
  superseded draft. Old proofreading manifests reject stale evidence rather than
  reverting the corrected record.

### Before you finish

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
PYTHONPATH=src .venv/bin/python -m bowl_index.cli roadmap        # if the corpus changed
PYTHONPATH=src .venv/bin/python -m bowl_index.cli report-enrichment
PYTHONPATH=src .venv/bin/python -m bowl_index.cli state --write --agent <you> --note "<what changed>"
```

Then add an entry to the **top** of `task-log.md` and commit. Commit at the end
of *every* session, including documentation-only ones — the repository went two
days and 827 files without a single commit, which is exactly what stopped the
4 September quality review from having a baseline to diff against.

Commit locally. Do not push, and do not open a pull request, unless Mike asks.

### Generated files

`docs/dataset_maturity_roadmap.md` and everything under `data/reports/` are
generated. Edit the input, not the output:

| Generated | Input | Command |
|---|---|---|
| `docs/dataset_maturity_roadmap.md` | `research/roadmap/dataset_maturity.json` | `ibi roadmap` |
| `data/reports/enrichment_status.md`, `identity_enrichment_current.md` | the corpus | `ibi report-enrichment` |
| `data/reports/campaign_status.md` | the corpus | `ibi report` |
| `data/reports/claim_conflict_revalidation_current.md` | the corpus | `ibi report-conflicts` |
| `data/reports/montgomery_cohort_current.md` | the corpus | `ibi report-montgomery-cohort` |
| `data/reports/proofreading_status.md` | the corpus and current proofreading reviews | `PYTHONPATH=src .venv/bin/python scripts/report_proofreading.py` |

Only the session that changed the corpus regenerates these. Two agents
regenerating from divergent database states produce conflicting files that look
like content disagreements and are not.

### Splitting the work

Codex built the corpus, the ingestion pipeline, and the collectors, and knows
that code best. Claude arrived with the scoping review. A sensible default
division, not a rule:

- **Codex** — `CONC`, `QA`, `OPS`, `RIGHTS`: concordances, revalidation queues,
  collectors, and the operational runtime.
- **Claude** — `SCHOL`, `TEXT`, `META`: the scholarly bibliography, the
  published-corpus enumeration, the field model, and evidence grading.
- **Either** — `DISC`, and anything the other has explicitly handed over in
  `task-log.md`.

Whoever picks up a task writes it in the log first.

---

## 3. What must never be automated

Agents may collect appearances and open leads. Agents may **not**:

- merge uncertain identities,
- adjudicate conflicting scholarly claims,
- declare an object authentic or fake,
- clear copyright or approve media for reuse,
- bypass an access control.

Those are review decisions. The research console binds to localhost and refuses
non-local addresses; keep it that way.

**Deploying `site/` is not one of them.** An agent working interactively, with
Mike reading what it produces, may build and deploy the public page when asked.
The judgement that matters is what goes *into* the page — the release boundary
in §4, and the evidence rules above — and that is held by the build script's
leak guard and by review before the deploy, not by keeping `wrangler` out of an
agent's hands. Deploy on an explicit instruction, not on your own initiative,
and record it in `task-log.md` like any other change.

Revisit this if unattended agents ever arrive. A scheduled or 24/7 search agent,
running with nobody reading its output, should not hold a deploy credential.
That is not the current setup and is not planned.

---

## 4. Release boundary

The private database is the authoritative store and stays private. Research
exports retain provenance and rights metadata but blank content unless the
record is explicitly `public_ok`; raw source payloads stay private. The separate
`export-public` path applies a narrower set of gates and currently releases 319
of 354 media rows with completed owner decisions while withholding the other 35.

Historical exports labelled "public-safe" overstate that boundary and should not
be treated as publication-cleared. A future public dashboard consumes a reviewed
export or a read-only API — never the ingestion database.

Provenance statements describe what sources report. They do not legitimize
ownership, export history, or authenticity, and the index should never read as
though publication settles any of those.

---

## 5. Mike's personal audit runtime

The [daily personal audit](personal_audit.md) uses a private operational ledger
outside the corpus. Mike alone marks reviews complete; personal completion does
not verify every source claim or authorize identity, authenticity, or rights
decisions. Corrections still require the existing manifest/ingest workflows.
When Mike gives a personal audit response in chat, follow that document to record
the explicit result against the shown batch and fingerprint immediately. Do not
wait for the next scheduled run or merely acknowledge his review without saving it.

Scheduled preparation opens the corpus read-only, bypasses migrations, and may
write only private audit progress. It must not advance on delivery alone, skip
unfinished bowls, infer reviews, or silently transfer reviews across identity
membership changes. This bounded runtime is authorized by Mike's five-bowl
personal audit instruction; unattended corpus writes remain prohibited.

Runtime-only audit deliveries and recording Mike's audit responses do not edit
the repository or corpus, so they do not require a new task-log entry, state
stamp, report regeneration, or commit on each reminder. Implementation changes
and corpus corrections remain full working sessions under §2.
