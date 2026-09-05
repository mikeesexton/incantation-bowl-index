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

## 2026-09-05 — Claude — Attribute the project to Moses Gabai

**Claimed:** none
**Corpus:** changed (45 reissued publication decisions; no scholarly values altered)
**Tests:** 106 passed

- The project is published under the scholarly name **Moses Gabai**. Copyright
  lines, the CC BY 4.0 attribution string, the README, `docs/licensing.md` and
  the `ibi export-public` manifest all now read `Gabai, Moses`.
- Reissued the 45 text publication decisions under that name. The ledger is
  append-only, so the original rows stay: the reissued entries carry `-V2` IDs
  and byte-identical decisions, rights bases, attributions, editorial statuses
  and evidence fingerprints. Only the recorded reviewer name differs. Ledger is
  now 90 rows, 45 current; `public_ok` is unchanged at 45 and replay is a no-op.
- Rewrote author and committer on all commits. The public history had carried a
  personal legal name and a personal email address; it now reads
  `Moses Gabai <114828727+mikeesexton@users.noreply.github.com>`. Force-pushed;
  the repository had 0 forks, 0 stars and 0 watchers at the time.
  **Commit hashes changed again — re-clone rather than pull.**
- Not resolved: the GitHub account and repository URL are still `mikeesexton`,
  so the pseudonym is partial. Separating those means a new account or an
  organisation, and a transfer or re-push. Flagged for a decision.
- `git config user.name/user.email` are set locally in this repository only, so
  other repositories on this machine are unaffected.

## 2026-09-05 — Claude — Add MIT and CC BY 4.0, and correct a licence overstatement

**Claimed:** none
**Corpus:** unchanged — state digest `220020601c92`
**Tests:** 106 passed

- MIT for the code (`src/`, `tests/`, `migrations/`, `web/`, `config/`),
  CC BY 4.0 for data, documentation and research materials. `docs/licensing.md`
  carries the scope map, the exceptions, and the attribution string.
- Two things the CC BY grant deliberately does not reach, because they are not
  ours to give: the 35 Montgomery translations are **public domain** and are
  offered as such rather than licensed — applying a licence to public-domain
  material claims a right nobody holds — and material from narrower-licensed
  sources is withheld rather than relicensed.
- **Corrected an error in the previous session.** `docs/project-rules.md` and my
  summary both said Waller 2022's biblical-quotation data was in the public
  dataset as an example of "facts are publishable". It is not: all 134 rows are
  withheld and carry only a pointer. Worse, Waller 2022 is **CC BY-NC 4.0**,
  which forbids commercial use and so cannot be relicensed under CC BY 4.0 at
  all. The rule now says to check a source's licence before approving anything
  derived from it.
- The licence, its URL, the attribution string and the scope note are now written
  into every `ibi export-public` manifest, so they travel with the data rather
  than living only in the repository.
- Next unchanged: `RIGHTS-002` for the 288 Penn images, then `SCHOL-001`.

## 2026-09-05 — Claude — Publish 45 texts on a recorded basis; make the repo public-ready

**Claimed:** TEXT-008 (new), RIGHTS-004 (new, queued)
**Corpus:** changed (45 text publication approvals; no claims, identities or media touched) — state digest `220020601c92`
**Tests:** 106 passed (94 before; +12 for the publication ledger and access pointers)

- Audited the whole tree for a public push. Clean on secrets, personal data,
  images, and archived bytes: the Waller 2025 excerpt, the Montgomery scans and
  the corrected translations are all tracked as hashes and paths only.
- The one real exposure was the two dated export snapshots — 334 claims and
  ~62,000 characters of museum catalogue prose, some of it embedding verbatim
  scholarly translations, from sources whose rights are `unknown` or
  `copyrighted`. Untracked them (files kept on disk, regenerable with
  `ibi export`) and published the gated projection at `data/public/2026-09-05`
  instead, 2.1 MB.
- Added migration 011 and `ibi ingest-text-publication`: an append-only ledger
  where a text goes public only on a stated rights basis, with attribution and
  an explicit editorial status. Approvals are bound to the text's content
  fingerprint, so the outstanding `TEXT-006` specialist review revokes them
  rather than silently altering published text.
- Approved 45 texts: Montgomery's 35 scan-checked English reading texts
  (`public_domain_expired` — pre-1930 US publication) and 10 index summaries
  (`own_work`). The summaries needed their own batch because the first sync
  correctly revoked them: they had carried `public_ok=1` with no recorded
  decision. Scope was held to what was already public plus Montgomery; the
  other 66 summary rows stay withheld pending their own decision.
- Every withheld text now points at its source: 151/151 keep citation and exact
  locator, 146 also carry a resolvable link. The 5 without one fail closed
  because their source URL matches a private capture — logged as `RIGHTS-004`,
  since a public page URL reveals nothing about the archive.
- Added an `editions` table to the public export: 476 publication locations
  across 472 objects, so an object with no publishable text still says where it
  has been published.
- Wrote the three-layer text rule into `docs/project-rules.md` — the ancient
  text is free, a modern transcription and translation are not, and facts about
  a text always are. Moved the provenance disclaimer to the top of the README.
- **Rewrote history before pushing.** The snapshots were still in the first
  commit, so removing them from the tree was not enough. `git filter-branch`
  stripped both paths from all five commits, the backup refs were purged and the
  objects collected. Verified by scanning all 224 blobs in history for the
  catalogue prose: zero hits. Repository is 1.2 MB. **Anyone holding an older
  clone must re-clone** — the commit hashes all changed.
- Pushed public: https://github.com/mikeesexton/incantation-bowl-index
  Remote verified at 208 files, 5 commits, nothing under `data/exports/` but the
  placeholder, and the live manifest reporting 45 texts included / 151 withheld
  / 0 media approved.
- Deliberately **not** done: no media approved (still 0/325), no bibliography
  seed ingested, no claim data published, **no licence chosen** — the repository
  currently carries no LICENSE file, which means all rights reserved. For a
  dataset meant to be used that is worth a decision; a licence for the code and
  a separate one for the data is the usual arrangement.
- Next: `RIGHTS-002` for the 288 Penn images, which have one rights holder and
  one policy to establish, then `SCHOL-001`.

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
