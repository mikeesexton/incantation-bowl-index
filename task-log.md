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

## 2026-09-05 — Claude — SCHOL-001: the index has an external yardstick

**Claimed:** SCHOL-001 (in progress; the ingest is SCHOL-002)
**Corpus:** changed (one archive deposit; no claims, identities, texts or media) — state digest `979e2e9d7aab`
**Tests:** 119 passed

- Mike supplied Waller's full "State of the Art" chapter — 45 pages, printed
  pp. 3–47, the whole thing rather than the two-page excerpt. Deposited
  privately by content hash under `SRC-19F191B3F5C5`.
- Added **`ibi deposit`** for researcher-supplied documents. Same
  content-addressed store as `capture`, but the URL slot records a deposit
  marker rather than a fetch target, because nothing here made a robots or
  access-control decision and the record should not imply one.
- Transcribed the list at printed pp. 40–47: **115 entries, 52 authors**, in
  `research/sources/waller_2025_jba_publication_list.jsonl`. Rule-parsed then
  checked by inspection; one entry was corrupted where a footnote interrupted it
  across a page break, fixed by bounding footnotes to their own page.
- **First external completeness measurement: the index holds 46 of 115, 40%.**
  69 missing — 45 authors absent entirely, 24 where the index holds a different
  work by the same author. Those 24 were spot-checked and are genuine misses.
  The check is generous in the other direction, since a surname-and-year hit
  counts as held without verifying the edition, so 60% missing is a floor.
- **Gordon is the largest hole: eight publications, none held** — the prediction
  made from the scoping review, now confirmed against the list. The
  nineteenth-century layer is almost entirely absent, which is also where the
  least reliable findspots were established (META-005).
- Second benchmark, better than the EJCM working counts: Waller cites Ford and
  Abudraham 2018 for **62% JBA / 23% Mandaic / 13% Syriac**. The index runs
  80.0 / 10.6 / 9.5 across 729 classified records — short roughly **91 Mandaic
  objects**. Syriac is close; JBA is over-represented by about the margin
  publication bias predicts.
- Qualified `DISC-001`: two sweeps under 1% net-new measured marginal yield
  inside the twelve searched classes and say nothing about coverage of the
  published corpus. The README now leads with the 40%.
- Deliberately **not** done: no ingest of the 69. That is `SCHOL-002`, and it
  needs reconciling per-work against the 21 seed records transcribed from the
  scoping review first, or it will create duplicates.
- Next: `SCHOL-002`. Also worth obtaining Ford and Abudraham 2018 as a Mandaic
  control list — Waller's list is JBA only.

---

## 2026-09-05 — Claude — QA-008 and META-006: the field model

**Claimed:** QA-008, META-006 (both now done)
**Corpus:** unchanged — state digest `8a19ea187a26`. Model and code only.
**Tests:** 119 passed (106 before; +10 field model, +3 proofreading independence)

- Classified all **101 claim fields**: 66 in a comparison group, 35 explicitly
  excluded with a stated reason, 0 unclassified. `ibi stats` reports any field
  that is neither, and `tests/test_field_model.py` fails on a field in two
  groups, in both lists, excluded without a reason, or in neither.
- Added **13 content groups** for the scoping review's People, Ritual,
  Intertexts, Visual and Scholarship facets. Roles are kept apart — client,
  target and practitioner are separate groups — so a client name can no longer
  be compared against a contested authorship attribution. That is the
  groundwork META-007 needs.
- Exclusions carry their reasons, and most point somewhere better: market values
  are per-sale events; ownership history is event-shaped and belongs in
  `events`; object relationships belong in `object_relationship_assertions`;
  META-005 evidence gradings assess a claim rather than rival it.
- **Conflict denominator 337 → 365, with zero existing decisions invalidated.**
  The backlog is 312 rather than 284, and it is now a measured total instead of
  an artefact of seven hard-coded groups. New instances: publication 8,
  condition 7, text_form 3, ritual 2, biblical_intertexts 1, plus 6 provenance
  and 1 language from the widened core groups.
- **Language coverage 459 (34.8%) → 663 (50.2%)**, because the 205 NLI
  catalogue codes now count. Biblical intertexts is the best-covered content
  facet at 168 (12.7%).
- **Corrected an earlier overstatement.** The alignment report said 205 objects
  carried a catalogue language code disagreeing with an edition-based claim.
  Measured: **zero** objects carry both, so that disagreement does not occur in
  the data. The effect is on coverage, not conflicts. Report and roadmap
  amended, and META-008 now notes those 205 are unverified catalogue
  classifications rather than corroborated attributions.
- **Fixed a regression I introduced yesterday.** Approving the Montgomery texts
  flipped `texts.public_ok`, and the proofreading fingerprint hashed the whole
  row — so all 35 scan-checked reading texts silently went stale and the roadmap
  reported 0. Proofreading validity now compares against the reviewer's own
  after-snapshot, ignoring publication administration. A publication decision no
  longer invalidates a reading check; any change to the text still does. Both
  directions are tested.
- Roadmap now reports content-facet coverage separately from the release gates,
  so adding a content group cannot quietly move a gate.
- Next: `QA-002`/`CONC-005`, the 312-case revalidation queue. The denominator is
  stable now, so that work will not need redoing. Dating (171) and provenance
  (123) are the two large groups; both are better tackled by source cohort than
  by identity. **`SCHOL-001` still needs you** — the Marcus–Mokhtarian volume
  through a research library or interlibrary loan.

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
