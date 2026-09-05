# Task log

One entry per working session, **newest first**. Insert new entries directly
below this block — never append at the end of the file, and never start a second
oldest-first region at the bottom.

Sessions before 5 September 2026 predate this log. Their history is in the
change log at the foot of
[`docs/dataset_maturity_roadmap.md`](docs/dataset_maturity_roadmap.md) and in
the dated reports under `data/reports/`.

## Entry format

```
## YYYY-MM-DD — <agent> — <short title>

**Claimed:** <task IDs, or "none">
**Corpus:** unchanged | changed (<one line>) — state digest <first 12 chars>
**Tests:** <result>

- What was done.
- What was deliberately not done, and why.
- What the next session should pick up.
```

---

## 2026-09-05 — Claude — Import the scoping review; put the repo under version control

**Claimed:** none (no corpus work)
**Corpus:** unchanged — state digest `106516128233`
**Tests:** 94 passed (84 before; +6 for `state`, +4 for agent-docs parity)

- Put the repository under version control. It had **zero commits** and 827
  untracked files. Baseline commit covers code, migrations, docs, research
  manifests, reports, and the two dated export snapshots the README cites.
  `data/exports/latest/` and the `dedupe_candidates`/`dedupe_evidence` dumps are
  now ignored: regenerable intermediates, ~100 MB, rewritten by every export.
  Nothing was deleted from disk.
- Imported the July 2026 systematic scoping review, its 26-record bibliography
  control, its 14-row search log, and its progress checkpoint into
  `research/literature/`, with SHA-256 digests and a text extraction for grep.
- Added `ibi state`: a content fingerprint of every table, recorded in the
  tracked `data/db-state.json`. The corpus is not in Git, so a clean working
  tree does not mean an unchanged corpus. Run `ibi state` at the start of every
  session; `--write --agent <you>` at the end.
- Added `docs/project-rules.md` as the single source of truth, and rewrote
  `CLAUDE.md` and `AGENTS.md` as parity-kept extracts pointing at it. The
  original research rules from `AGENTS.md` are preserved verbatim in §1.
  `tests/test_agent_docs_parity.py` fails if the two drift.
- Reviewed the corpus against the scoping review and wrote up six findings in
  `data/reports/scoping_review_alignment_2026-09-05.md`. Added a `SCHOL`
  workstream and nine tasks (`SCHOL-001`–`004`, `TEXT-007`, `META-006`–`008`,
  `QA-008`), re-ordered the priorities, and qualified two claims that were
  reading as stronger than the evidence: discovery saturation is bounded by the
  twelve searched source classes, and the 337/284 conflict queue is an
  undercount bounded by seven hard-coded field groups.
- Headline finding: the index was built from what is findable online — 567 of
  753 sources are museum records — while the field's primary evidence is
  printed editions. Seventeen foundational works have no source record, and
  publications exist only as identifier prefixes: 17 objects carry
  `Isbell 1975::NN` and Isbell 1975 has no row.
- Deliberately **not** done: no writes to the corpus. The bibliography seed
  manifest is staged as `research/seeds/scholarly_bibliography_2026-09-05.jsonl`
  but not ingested, because the previous session's state is the baseline and
  ingestion should be a claimed task with its own review.
- Next: `SCHOL-002` — ingest the scholarly bibliography seed; then `SCHOL-001`,
  acquiring Waller's 2025 publication list, which is the only control list the
  field offers for what "all published JBA bowls" means.
