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

### Separate the roles behind a name

Never collapse author, textual voice, copyist, producer, commissioner, client,
and beneficiary into one field. A first-person feminine text does not establish
a female scribe; a client named on a bowl is not its author; a "rabbi" in a bowl
may be the client. Where a source makes an attribution, store *that source's*
attribution with its role and its uncertainty, and do not upgrade it.

### Script is not religion

Script is evidence for a scribal tradition, not proof of the religion of a
client or a practitioner. Keep catalogue language codes, edition-based language
attributions, and script observations as separate claims. They disagree often,
and the disagreement is informative.

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
- **Every corpus write goes through a checked-in manifest.** Write the JSON or
  JSONL under `research/`, then apply it with an `ibi ingest-*` command. Never
  hand-edit the database. The manifest is the reviewable artifact and it makes
  the corpus reproducible; a direct `UPDATE` is invisible to review and to the
  other agent.
- **Append, never overwrite.** Reviews, corrections, and revisions keep their
  originals. If a decision turns out wrong, add a superseding decision.
- **Back up before a batch that changes many rows.** Copy the database to
  `data/private/backups/before-<slug>-<UTC timestamp>.sqlite3`. Keep the last
  ten; that directory is already large.

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
- publish anything, or deploy a public dashboard,
- bypass an access control.

Those are review decisions. The research console binds to localhost and refuses
non-local addresses; keep it that way.

---

## 4. Release boundary

The private database is the authoritative store and stays private. Research
exports retain provenance and rights metadata but blank content unless the
record is explicitly `public_ok`; raw source payloads stay private. The separate
`export-public` path applies a narrower set of gates and currently withholds all
325 media, because zero have a completed rights decision.

Historical exports labelled "public-safe" overstate that boundary and should not
be treated as publication-cleared. A future public dashboard consumes a reviewed
export or a read-only API — never the ingestion database.

Provenance statements describe what sources report. They do not legitimize
ownership, export history, or authenticity, and the index should never read as
though publication settles any of those.
