# Claude Code — Project Instructions

## Start here

**[`docs/project-rules.md`](docs/project-rules.md) is the single source of truth
for this repository.** Read it before your first edit of a session.

Two AI agents work here — Claude Code and Codex — plus Mike. You share one
working directory and one SQLite database that Git does not track. Add or change
a rule in `docs/project-rules.md`, never in this file alone: `CLAUDE.md` and
`AGENTS.md` are kept byte-identical below their title line by
`tests/test_agent_docs_parity.py`.

## Open every session with this

```sh
git status --short
PYTHONPATH=src .venv/bin/python -m bowl_index.cli state
```

If `ibi state` says **drifted**, the corpus changed since the last recorded
session. Stop, read `task-log.md` and `git log`, and find out who changed it
before you write anything.

Then read the top entry of [`task-log.md`](task-log.md) and claim the task IDs
you are taking.

## Non-negotiables

The rules most easily broken in practice. Full text in
[`docs/project-rules.md`](docs/project-rules.md).

1. **A physical bowl is not a catalogue entry.** Objects and source appearances
   are separate records, linked with an explicit confidence and rationale. Every
   assertion is a source-attributed claim with a locator.
2. **Never hand-edit the database.** Write a manifest under `research/`, then
   apply it with an `ibi ingest-*` command. A direct `UPDATE` is invisible to
   review and to the other agent, and it makes the corpus unreproducible.
3. **Append, never overwrite.** Conflicting claims are stored side by side, not
   reconciled away. A wrong decision is superseded, not deleted.
4. **A publisher page cannot verify a reading.** Bibliographic metadata verifies
   titles, dates, and declared arguments — never a reading, a measurement, a
   findspot, or an identification.
5. **Close every session.** Run the tests, regenerate what you invalidated,
   `ibi state --write --agent <you>`, add an entry to the **top** of
   `task-log.md`, and commit. Documentation-only sessions included. Do not push
   unless Mike asks.
6. **Agents collect and flag; they do not decide.** No merging uncertain
   identities, adjudicating scholarly claims, declaring authenticity, clearing
   rights, or publishing.

## Before specific kinds of work

| If you are touching… | Read first |
|---|---|
| the corpus, in any way | `docs/project-rules.md` → Two-agent working rules |
| identity, dedupe, or concordances | `docs/research_protocol.md`, then `docs/conflict_review_workflow.md` |
| claims about origin, date, or findspot | `docs/project-rules.md` → Evidence grades |
| people named on a bowl | `docs/project-rules.md` → Separate the roles behind a name |
| publishing any bowl text | `docs/project-rules.md` → Publishing text: what belongs to whom |
| licensing, reuse, or attribution | `docs/licensing.md` |
| language or script | `docs/project-rules.md` → Script is not religion |
| images, texts, or anything outward-facing | `docs/evidence_review_and_release.md` |
| the scholarly literature | `research/literature/README.md` |
| priorities or planning | `docs/dataset_maturity_roadmap.md` (generated — edit `research/roadmap/dataset_maturity.json`) |
