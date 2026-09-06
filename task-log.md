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

## 2026-09-06 — Codex — Ford 2014 commentary index

**Claimed:** TEXT-001
**Corpus:** changed (13 appearances, 27 claims, ten identifiers, lead outcomes) — 5762f532db36
**Tests:** 134 passed; replay digest unchanged; source bindings, archive, SQLite integrity/foreign keys and backup verified.

- Indexed all 14 bold JBA-labelled discussions in Ford 2014 main commentary, pp. 236–246, covering 13 existing records. Incidental parallels and appendices are outside this scope.
- Categories distinguish retained readings, proposed corrections, grammatical and orthographic analysis, comparative evidence and a bibliographic pointer. Stored brief attributed topic summaries, not scholarly transcriptions or translations.
- Reused existing JBA concordances; multiple records for JBA 15, 55 and 56 already belonged to single resolved identity clusters. No merge or physical-accession revalidation performed.
- Added ten missing publication keys for the 2013 volume, with Ford as reporting source. The commentary was not registered as a full new edition. Unique candidate publication coverage is 435/1,590; appearances now 1,632.
- Resolved the commentary-indexing lead and opened specialist comparison follow-up. The two JBA 23 topics add one unreviewed text-description flag (314 pending overall); no historical review cleared.
- Regenerated roadmap, acquisition/conflict/enrichment/campaign reports and private export. Objects, texts, media, sources and identity decisions unchanged.
- Next: obtain the 2013 edition for comparison, provisional-candidate concordance checks, and Ford 2002 attribution reconciliation. TEXT-001 remains in progress.


---

## 2026-09-06 — Codex — Ford 2014 edition enumeration

**Claimed:** TEXT-001
**Corpus:** changed (two candidate records, three appearances, eleven claims, seven identifiers, one publication registry entry and lead outcomes) — 21ccd3582380
**Tests:** 134 passed; candidate/registry replay leaves digest unchanged; archive, database integrity and foreign keys valid; post-batch backup verified.

- Inspected Ford 2014 edition boundaries and photographs; recorded exact page locators without copying scholarly readings or translations.
- AS 13 and Davidovitz 27 enter as provisional candidates. Measurements retain printed order without inferred axes; no authenticity or global uniqueness claim.
- Attached Museo Sefardí 1073 to existing IBI-035BA4ABBE6D via Ford p. 253 n. 56 explicit AC-MSEF concordance, corroborated by collection and client context. No existing objects merged.
- Registered Ford 2014 Aula Orientalis publication key. Unique publication coverage 423 → 425 of 1,590 records; 18/19 keys resolved. Corpus now 1,619 appearances and 1,322 working identities.
- Resolved the three-edition enumeration lead and opened a broader Davidovitz 27 identity follow-up. The corrections and attribution leads remain open.
- New Toledo bibliography/concordance statements trigger one publication-group difference; retained unreviewed, increasing the queue to 313. No old review was cleared.
- Regenerated roadmap, acquisition, conflict, enrichment and campaign reports and private export. No text, media, rights or merge history changed.
- Next: broader provisional-candidate concordances, Ford 2014 correction indexing, and Ford 2002 bibliographic reconciliation. TEXT-001 remains in progress.


---

## 2026-09-06 — Codex — Edition acquisition follow-through

**Claimed:** SCHOL-005
**Corpus:** changed (two sources, one capture, five leads, seven search-log rows) — state digest d99914408594
**Tests:** 134 passed; archive and scope hash checks valid; database integrity and foreign keys valid; verified post-batch backup.

- Archived Ford 2014 from the University of Barcelona journal host after robots allowance. All 29 pages inspected for document scope; title and boundaries match pp. 235–263. The scan is image-only. Source SRC-FORD2014-AUOR; archive SHA-256 0b7f1780d434...f1b2dd7.
- Staged edition follow-up for AS 13, Davidovitz 27 and Museo Sefardí 1073 with printed-page locators, plus a separate corrections-indexing lead. No object records, readings or translations ingested.
- Segal's indexed preview remains only two pages; full work not obtained. Isbell's Internet Archive item is explicitly access-restricted. Ford 2002's old PDF returns 404; the current journal-linked CDN failed robots allowance, so no PDF fetched.
- Added publisher-evidenced Ford 2002 metadata and flagged its author-attribution disagreement with SRC-1EE58A703971. The original Müller-Kessler attribution and dependent claims remain intact pending reconciliation.
- Acquisition manifest records scope, hashes and actual access outcomes. The generated acquisition report remains a format inventory; it does not yet consume scope reviews.
- Source and lead replay checks produced no duplicates. An initial lead manifest used unsupported type `access`; corrected to `restricted_source` before successful ingestion. Seven actual searches were logged.
- Regenerated roadmap, acquisition/enrichment/campaign reports and private rolling export. Changed tables limited to sources, captures, leads and search logs. No rights decision or public release.
- Next: use the acquired Ford 2014 article for edition/concordance review, reconcile Ford 2002 attribution, and continue authorized Segal acquisition. SCHOL-005 remains in progress.


---

## 2026-09-06 — Codex — Acquisition and publication measurement review

**Claimed:** QA-004
**Corpus:** unchanged — state digest fd0fc6eb5883
**Tests:** 134 passed; archive hashes valid; SQLite integrity and foreign keys valid; diff check clean.

- Confirmed clean handoff from Claude and unchanged corpus fingerprint.
- Corrected acquisition reporting: 20 captured sources are nine with PDFs and eleven with only non-PDF captures, not 20 complete documents held. Completeness remains unassessed; no prior corpus claims or reviews were changed.
- Corrected publication and acquisition counts to use distinct candidate records across aliases and publications: 423 records have publication keys and at least one resolved key. TMH 7 remains unresolved; its two records also have other resolved keys.
- The acquisition queue now reports 670 sources with dependants and no PDF capture, covering 345 distinct candidate records through publication links. Segal 2000 leads with 252 distinct candidate records.
- Added regression coverage for overlapping references, non-PDF captures and excerpts; regenerated acquisition and roadmap reports and ran enrichment regeneration.
- Refreshed stale/duplicate priorities, retaining completed bibliography and field-model work. QA-004 remains in progress: acquisition completeness needs evidence-bound assessment, and general field verification is still outstanding.
- Next: acquire and assess edition scope (Segal first), extend publication references, then revalidate coherent source cohorts. No new scholarly assertions, identity decisions, rights decisions or public release.

---

## 2026-09-05 — Claude — Bowl SD 34 is in the corpus twice

**Claimed:** none (two leads opened for review)
**Corpus:** changed (one deposit, two leads)
**Tests:** 134 passed

- Mike asked whether the bowl in Levene & Bhayro's "Bring to the Gates … upon a
  good smell and upon good fragrances" is in the corpus. Another image-only
  scan; OCR'd with the newly installed tesseract, which worked first try.
- The bowl is **SD 34**, Samir Dehays collection. **It is in the corpus twice**,
  as two object records for one physical bowl:
  `IBI-358AAAF4ED2B` ("Waller 2022: SD 34") and `IBI-12617DC13FC0`
  ("Success-in-business bowl SD 34").
- The generated dedupe queue is empty, so this pair was never surfaced. The
  likely cause is that the two designations arrived under different schemes —
  `Waller 2022 table designation` and `publication designation` — rather than a
  shared trusted namespace, so the exact-identifier rule never compared them.
  **That is a detector gap, not just one missed pair**, and the second half of
  the lead asks for it to be investigated as such.
- Did **not** merge. Corroborating evidence is now held instead: the article
  gives 153 mm across, 55 mm deep, fourteen lines in a neat formal hand
  spiralling clockwise from base to rim, mostly well preserved, Mesopotamia,
  fourth to seventh centuries. None of those measurements is recorded on either
  record yet, so the honest order is to record the physical description first
  and adjudicate second.
- Also found two source records for the same article, 2005 and 2006 — AfO 51 is
  a 2005/2006 volume. Second lead opened.
- Deposited the scan against SRC-A84A167A5779.

---

## 2026-09-05 — Claude — A clickable launcher for the console

**Claimed:** none
**Corpus:** unchanged
**Tests:** 131 passed

- Added `bin/Incantation Bowl Index.app`, a hand-built macOS bundle: no build
  step, no AppleScript, just `Info.plist` plus a shell script, so it lives in
  Git like any other file and works from Finder, the Dock or Spotlight.
- Behaviour: if the console is already up it just opens the browser; otherwise
  it starts it in the background, waits for it to answer, then opens the
  browser. `LSUIElement` keeps it out of the Dock switcher and no Terminal
  window appears. Cold start measured at **0.69s**, and a second click leaves
  exactly one listener.
- Failure modes give a dialog rather than silence: missing `.venv` (with the
  one-line fix), or the port occupied by something else. Logs to
  `data/private/console.log`; `IBI_PORT` overrides the port.
- `bin/stop-console.command` stops it.
- Nothing needs rebuilding before opening — the console reads the working
  database live, so it is current by construction.
- Tested cold start, warm start and double-click safety before committing.

---

## 2026-09-05 — Claude — An acquisition register

**Claimed:** SCHOL-005 (new, in progress)
**Corpus:** changed (one blocked lead)
**Tests:** 131 passed (127 before; +4)

- Added **`ibi report-acquisitions`** → `data/reports/acquisition_status.md`.
  It separates two things the corpus had been conflating: a *citation* and a
  *held document*. Only the second lets a claim be checked at page level.
- Current state: **20 of 841 sources have the document held (2.4%)**, 661 are
  wanted with something depending on them, and **347 objects depend on a
  publication nobody here has read**.
- The want list is ranked by dependants — ten points per object a work
  publishes, one per appearance or claim. **Segal 2000 dominates: 253 objects,
  142 appearances, 142 claims.** It is also CONC-001's blocker, so the same
  acquisition unblocks two workstreams. Then Shaked–Ford–Bhayro 2013 (23),
  MRLA 8 (19), Isbell 1975 (17), Shaked–Ford–Bhayro 2022 (16), Naveh–Shaked (7).
- Holding front matter only counts as **not held** — MRLA 8 appears on the want
  list even though its prospectus is archived, which is the conservative and
  correct reading: we have the imprint page, not the editions.
- `TMH 7` logged as **blocked**: no digital copy of Müller-Kessler 2005 located.
  The registry entry stays unresolved rather than inferred; a photograph of the
  title and imprint pages alone would settle it.
- poppler and tesseract are now installed, so image-only scans can be rendered
  and OCR'd — worth knowing, since the nineteenth-century layer is all scans.
- Next: work the want list from the top. Every document obtained converts
  citations into checkable page-level evidence.

---

## 2026-09-05 — Claude — Resolve MRLA 8 from the volume itself

**Claimed:** SCHOL-004 follow-up
**Corpus:** changed (one deposit, one source, one registry decision)
**Tests:** 127 passed

- Mike supplied Ford & Morgenstern, *Aramaic Incantation Bowls in Museum
  Collections* vol. 1 (Hilprecht). Front matter, 30 pages, deposited privately.
- **Series number verified from the imprint page, not inferred**: cover and
  copyright page read "magical and religious literature of late antiquity 8",
  ISSN 2211-016X volume 8, ISBN 978-90-04-37700-4, LCCN 2019026750, series
  editors Shaked and Bhayro. That is evidence, so the earlier unresolved
  decision (IBI-PUBREG-17) is superseded rather than second-guessed.
- Registry coverage **16/18 → 17/18 keys, 414 → 433 objects**.
- `TMH 7` alone remains unresolved, 2 objects, awaiting the same check against
  Müller-Kessler 2005's printed volume.
- The volume reports forty Jena bowls in Jewish, Manichaean Syriac or Mandaic
  script plus about twenty-five in Pahlavi or pseudoscript — a concrete lead for
  META-008's Pahlavi gap, where the index currently holds two objects.

---

## 2026-09-05 — Claude — SCHOL-004: publications become first-class

**Claimed:** SCHOL-004 (done)
**Corpus:** changed (18 registry decisions; no claims, identities, texts or media)
**Tests:** 127 passed (119 before; +8 for the registry)

- Migration 012 adds an append-only **publication registry**. It records which
  publication a designation *belongs to*, kept separate from
  `identifiers.source_id`, which correctly records who *reported* it. A test
  asserts the reporting link is untouched by resolution.
- **16 of 18 publication keys resolved, covering 414 of 435 objects.** The index
  can now answer "which edition publishes this bowl", which it could not before.
- Two left unresolved with precise blockers rather than guessed. `MRLA 8` has no
  source record for its expected publication (Ford & Morgenstern, *Museum
  Collections* vol. 1) and its series number is unchecked. `TMH 7`'s candidate
  (Müller-Kessler 2005) is plausible but inferred from the series name, not
  verified against the volume — 19 and 2 objects respectively hang on those.
- **SCHOL-002 paid off immediately:** Isbell 1975, Naveh–Shaked 1993,
  Naveh–Shaked 1985/1993 and Gorea 2003 became resolvable only because their
  publications had just been ingested. Yesterday those keys pointed at nothing.
- Roadmap reports both counts, and `unresolved_publication_keys` plus
  `tests/test_publications.py` fail when a key has no registry entry.
- The honest limit: only **435 of 1,588 records carry a publication key at
  all**, and none of the 69 publications ingested under SCHOL-002 has a single
  object attached. Resolution works; coverage is thin. That is now priority 1.
- Next: extend publication keys to the objects those 69 publications contain.

---

## 2026-09-05 — Claude — Trace the language benchmark to its source

**Claimed:** META-008 (evidence corrected; still open)
**Corpus:** changed (one deposit, one source record)
**Tests:** 119 passed

- Mike supplied Ford & Abudraham 2018, "Syriac and Mandaic Incantation Bowls"
  (*Finds Gone Astray: ADCA Confiscated Items*, Jerusalem 2018, pp. 75–111).
  Deposited privately by content hash; source record added.
- **It is not the Mandaic control list.** It publishes eight confiscated bowls —
  six Syriac (four Manichaean script, two Estrangelo) and two Mandaic — and is
  an object publication, not a census. No Mandaic equivalent of Waller's JBA
  list appears to exist, so that denominator has to be built from the corpus
  editions themselves, all of which are now in `sources` after SCHOL-002.
- **Corrected the benchmark's attribution.** I had it as "Ford & Abudraham
  2018". Their n. 3 attributes it to **Morony 2003: 87**, and adds a caveat I
  had not carried: Morony worked from "the corpus that was then known, which
  represents only a small portion of the material now available," though they
  judge the distribution still reflects the overall picture fairly accurately.
  Chain: Morony 2003 → Ford & Abudraham 2018 n. 3 → Waller 2025 p. 3 n. 1 → us.
  It is a twenty-year-old estimate endorsed twice, not a current census, and
  the 23% Mandaic figure should be treated as an expectation rather than a
  target. Morony 2003 is in `sources`, ingested yesterday under SCHOL-002.
- Recorded that this volume publishes antiquities **confiscated in Judea and
  Samaria**. Provenance there is legally and archaeologically contested and must
  not be read as excavation context if those eight bowls are ever ingested.
- Next: `SCHOL-004`, publications as first-class records — still the binding
  constraint.

---

## 2026-09-05 — Claude — SCHOL-002: close the bibliographic gap

**Claimed:** SCHOL-002 (done), SCHOL-001 (done)
**Corpus:** changed (86 new source records; no claims, identities, texts or media)
**Tests:** 119 passed

- Reconciled the 21 hand-written seed records against Waller's list **per work,
  not per author**, as the roadmap warned. Four overlaps — Myhrman 1909, Isbell
  1975, Naveh–Shaked 1993, Müller-Kessler 2005 — resolved in favour of Waller's
  sourced citation. 17 seeds kept: Pognon, Yamauchi, Naveh–Shaked 1987, Morony,
  Mokhtarian, Harari, Häberl, Frim, Secunda, Gross–Scarlassara, Mackenzie and
  four Manekin-Bamberger titles, all outside Waller's JBA scope.
- Ingested 69 + 17 = **86 source records**, sources 753 → 839. Citations are
  verbatim from Waller printed pp. 40–47; the ingest is idempotent on the exact
  citation and a replay adds nothing.
- **Control-list coverage 46/115 → 115/115.**
- **And that number means less than it looks, which the report and roadmap now
  say plainly.** It measures bibliographic presence. The publications have not
  been read, their editions are not located, and the bowls they publish are not
  linked — Gordon's eight publications are cited, and not one of his bowls is
  attached to them. Publication-record coverage is 100%; object-level coverage
  of the published record is unmeasured and mostly zero.
- That makes `SCHOL-004` the binding constraint and it is now priority 1: until
  publications are first-class records, the index cannot ask a bowl which
  edition publishes it, and `publication_reference_pct` cannot mean anything as
  a handoff gate.
- Parsed titles and source types are the least reliable field in the new
  records; the verbatim citation is authoritative. Worth a correction pass.
- Next: `SCHOL-004`, then Ford & Abudraham 2018 as the Mandaic control list.

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
