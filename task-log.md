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

## 2026-09-17 — Codex — Residual PDF full-file review

**Claimed:** ACCESS-004, SCHOL-005
**Corpus:** changed (eight document assessments; no object assertions) — state digest `b678f711053a`
**Tests:** 239 Python tests passed; assessment manifest replayed with zero changes; all three SQLite integrity checks passed

- Verified the retained SHA-256 for all eight residual PDFs, rendered every page
  with Poppler and inspected title matter, document sequence and terminal matter.
- Added complete-document assessments for the Waller 2025 chapter, Oriental
  Institute highlights guide, Moriggi 2024 article, Brand working list,
  Levene-Bhayro 2006 article, Kedar dissertation, Schwab's complete PSBA volume
  and the Auction 57 catalogue.
- Marked bounded extraction complete for the museum highlight, Moriggi's two
  editions, Brand's 41-item list plus three related candidates, SD 34 and the
  three auction bowls. Waller, Kedar and Schwab remain partial because their
  current artifacts cover selected objects rather than every object discussed.
- All 39 PDF-linked sources are now assessed through 40 holding rows: 38 sources
  have complete documents and Naveh-Shaked 1993 remains front matter only.
  Twenty-nine sources have object-level extraction, 22 complete and seven partial.
- No scan was promoted to OCR without a separate artifact; no object assertion,
  identity, claim, rights or publication decision changed.
- Next: classify the eleven HTML-only captures as landing pages, item pages or
  substantive documents without inferring completeness from MIME type.

## 2026-09-17 — Codex — Remaining reviewed-PDF ledger tranche

**Claimed:** ACCESS-004, SCHOL-005
**Corpus:** changed (ten document assessments across nine sources; no object assertions) — state digest `d6d436e99142`
**Tests:** 239 Python tests passed; six manifests replayed with zero changes; all three SQLite integrity checks passed

- Added evidence-bound holding assessments for Montgomery, both JSQ 6 articles,
  Ford 2014, the supplied Cook and Ford articles, the Ford 2023 English summary
  and three contributions in *Mehqarim be-Lashon* 20.
- Kept the Ford 2023 summary excerpt separate from the complete journal-volume
  capture. The ledger therefore gains ten holding rows across nine sources.
- Marked Montgomery, Shaked 1999 and Ford 2014 as partial extraction rather than
  overstating their reviewed artifacts; the separate Ford commentary is not
  treated as object-level extraction.
- Ledger coverage is now 31 of 50 source-linked captures via 32 assessment rows:
  30 sources have complete documents, one has front matter only, 21 have
  object-level extraction and 17 have complete extraction.
- Deliberately left eight PDFs unassessed where the existing evidence does not
  establish full-file extent or completeness. Eleven HTML captures also remain
  to be classified; file format alone is not evidence of document status.
- No object assertion, identity, claim, rights or publication decision changed.
- Next: create full-file review evidence for the remaining eight PDFs, then
  classify the eleven HTML captures as landing pages, item pages or substantive
  documents.

## 2026-09-17 — Codex — Complete-edition and open-scan ledger tranche

**Claimed:** ACCESS-004, SCHOL-005
**Corpus:** changed (eleven document assessments; no object assertions) — state digest `f2546cf46aa0`
**Tests:** 239 Python tests passed; four manifests replayed with zero changes; SQLite integrity check passed

- Added evidence-bound assessments for the five additional 11 September holdings:
  Levene 2013, Jullien's complete three-page review, the 2018 Berlin catalogue,
  Saar 2017 and the distinct Naveh-Shaked 1985 first edition.
- Added complete-scan assessments for Stübe 1895, both Wohlstein articles and
  three retained Gordon articles. Their document, review and extraction hashes
  are bound independently; none is labelled OCR without an OCR artifact.
- Nine of these sources have complete object-level extraction. Jullien and Saar
  correctly carry none because they do not contain finite bowl catalogues.
- Deliberately excluded Gordon's AASOR article from the holdings ledger. It was
  inspected temporarily but not archived when robots permission could not be
  verified; a temporary hash does not make it a retained document.
- Ledger coverage is now 22 of 50 source-linked captures: 21 complete documents,
  one front-matter-only holding, 15 with object-level extraction and 14 with
  complete extraction. Twenty-eight captures remain explicitly unassessed.
- No object assertion, identity, claim, rights or publication decision changed.
- Next: assess the remaining seventeen PDFs beginning with Montgomery, Schwab,
  Ford and the supplied-article batches, then classify the eleven HTML captures
  as landing pages, item pages or substantive documents.

## 2026-09-17 — Codex — September 12 document-ledger rollout

**Claimed:** ACCESS-004, SCHOL-005
**Corpus:** changed (seven document assessments; no object assertions) — state digest `82c5064226fc`
**Tests:** 239 Python tests passed; seven-entry manifest replayed with zero changes; SQLite integrity check passed

- Converted the already-inspected 12 September researcher-PDF batch into seven
  evidence-bound ledger rows. Coverage is now 11 of 50 source-linked captures:
  ten complete documents and one explicitly incomplete front-matter holding.
- Recorded Waller 2022, the Hornkohl-Khan volume, Molin's complete chapter,
  Layard/Ellis, Wajsberg's review and Pognon as complete. Kept the supplied
  Naveh-Shaked 1993 file at `front_matter`: its seven pages do not satisfy the
  acquisition of the book.
- Bound Pognon's complete thirty-bowl extraction and Layard/Ellis's partial
  extraction to the checked-in JSONL hash. Layard remains partial because the
  collective no. 7 fragment group is unquantified and was not invented as one
  physical object. Waller's older appearances are not certified as a current
  extraction artifact because no matching checked-in extraction manifest exists.
- Kept every text state at `extractable`; none was promoted to OCR or corrected
  rich text without a separately hash-bound artifact. The Wajsberg PDF remains a
  complete review and does not make the unheld Juusola monograph held.
- No new inspection, identity, claim, rights or publication decision was made.
- Next: convert the five additional 11 September volumes, then the documented
  Stübe, Wohlstein and Gordon open-scan batches; 39 source-linked captures remain.

## 2026-09-17 — Codex — General document-completeness ledger

**Claimed:** ACCESS-004, SCHOL-005
**Corpus:** changed (migration 015 and four document assessments; no object assertions) — state digest `99ea8cf2621a`
**Tests:** 239 Python tests passed; four-entry manifest replayed with zero changes; SQLite integrity check passed

- Added an immutable, explicitly supersedable per-holding ledger and
  `ibi ingest-document-assessment`. It keeps document form and extent, inspection
  method, text transformation and object-level extraction independent. Review
  evidence, retained bytes and every OCR/rich-text or extraction artifact bind by
  SHA-256; a capture alone still proves no completeness claim.
- Converted the four 11 September Brill volumes from interim evidence into the
  first durable batch: all four are complete digitally inspected born-digital
  documents with extractable text and complete catalogue-level object extraction.
  None is labelled OCR or corrected rich text. The batch replays idempotently.
- Acquisition and roadmap reports now consume current ledger assessments and show
  4 assessed complete sources alongside the 46 source-linked captures that remain
  explicitly unassessed. The research export includes the ledger; public exports
  still exclude private capture and transformation metadata.
- Added tests for hash binding, state combinations, source/capture ownership,
  append-only history, explicit supersession, idempotent replay, citation-only and
  physical-document states, and project-contained evidence paths.
- No identity, claim, rights or publication decision changed. ACCESS-004 remains in
  progress because every retained source holding has not yet been assessed.
- Next: ledger the already inspected 12 September batch, especially the
  Naveh-Shaked 1993 front matter and complete Pognon/Layard works, then work through
  the remaining captures without inferring extent from file format.

## 2026-09-15 — Claude — Rename the console tabs and write the reading room a description per bowl

**Claimed:** none — unregistered reading-room work, at the researcher's request
**Corpus:** changed (68 own_work card-line summaries, 67 client and purpose claims) — state digest `f8fac2d62654`
**Tests:** 233 Python and 21 Node tests passed; every tab, the workbench route and two bowl pages checked in the browser

- Renamed and reordered the tabs to Home · Explore · Search · Scholarship · Enrichment, and
  rotated the routes with the labels: the reading room is now `#/explore` and the research
  explorer `#/search`. Do the `explore`→`search` pass before `reading`→`explore`; `app.js`
  derives the panel id as `` `${route}-view` ``, so a single find-and-replace collides and
  points two tabs at one panel. Dropped the Concordance tab only — `#/reviews` and
  Enrichment's "Open workbench" still reach the workbench.
- The reading room led with "Exterior directs placement 'for the inner room of the hall'"
  because `summarise` took the **shortest** value in the `ritual` group and
  `installation_instruction` sits in it. Replaced that with an explicit field priority.
  Left the field in `ritual`: it is genuinely ritual information, there is exactly one such
  claim in the corpus, and no object depends on it for `has_ritual`, so moving it would have
  bought a fourteenth coverage group and nothing else. The defect was the display rule.
- Dropped `has_image` from `READING_WEIGHTS`. It scored 2 while `Projection._media` emits
  only rights-approved media and all 325 `media_rights_reviews` rows are still
  `needs_review` — two points, on 326 of 1,652 identities, for a picture the page cannot
  draw. Restore it when RIGHTS-002 lands. With client and purpose weighted at 2 the tab went
  from 61 bowls to 68, and the six blank Isbell cards left the top.
- Wrote one description per bowl for all 68, read from each bowl's stored translation, in a
  standard shape: what the text does, naming its most distinctive element, then the client.
  Stored as `own_work` summary rows marked `editor='Incantation Bowl Index card line'` so
  they never render as the bowl's own text, and approved through the publication ledger.
  Mike read all 68 before the decision was recorded.
- Added 67 client and `text_purpose` claims, each cited to the translation it was read from.
  **Did not** recast Komiš daughter of Mahlafta from practitioner to client on Montgomery 17:
  that is Kedar 2019's female-practitioner argument, and overturning it would be adjudicating
  a scholarly claim. Appended a client claim from Montgomery's own translation instead, so
  both readings now stand side by side. The same restraint applies to the other seven
  `attributed_author` rows Kedar supplies.
- Moved the five cited claim lists on a bowl page into the collapsed Research details. The
  authored line and the translation now lead; the evidence is one click away.
- Applying the publication batch ran `sync_public_ok`, which revoked three older
  "Incantation Bowl Index summary" approvals — Davidovitz 41, Moussaieff M163 and Schøyen
  MS 2054/124. They were `public_ok=1` in the column without a current fingerprinted
  approval. Nothing changed on screen: `Projection.approved_texts` reads the ledger, not the
  column, so those three were already withheld from the reader and the export; only the stale
  column caught up. **Worth a decision next session:** those three summaries were evidently
  meant to be public and now are not.
- Two new rows in the conflict revalidation queue, both expected: on Montgomery 17 and
  Montgomery 2 the fuller `text_purpose` now sits beside Kedar's terser `formula_genre`
  ("Divorce document", "General charm"). They are compatible rather than contradictory and
  want marking as such.
- Next session could: differentiate the two identical BM 127395/127396 lines and the two
  identical Semamit historiola lines if that matters more than accuracy; decide the three
  revoked summaries; and retarget the home page's "Browse the database" buttons, which still
  read "Explore…" while landing on Search.

## 2026-09-14 — Claude — Track the bowlam.com access layer

**Claimed:** ACCESS-008, ACCESS-009 (registering only — neither is started)
**Corpus:** unchanged — state digest `4a7c6ca8d9a9` (read-only throughout)
**Tests:** 228 Python tests passed

- Registered two queued tasks in the roadmap at the researcher's request, to track the
  bowlam.com plan without scheduling it. ACCESS-008 is the public landing page, which
  needs no rights decision because it is the project describing itself. ACCESS-009 is
  the scholar preview behind Cloudflare Access, now provisioned on the free tier.
- Wrote the constraints into ACCESS-009's evidence field rather than leaving them in a
  conversation, because they are the parts most likely to be relitigated at build time:
  the research console is not the deliverable and must never be exposed, the gate is
  the export rather than the password, and the corpus file is not shareable even
  privately while it carries 136 CC BY-NC and 15 copyrighted text rows.
- Edited `research/roadmap/dataset_maturity.json` and regenerated, per the
  generated-files rule. Neither task was added to `handoff_gate.required_task_ids`:
  both are post-handoff work, and adding them would have moved the 7/24 figure without
  anything having been achieved.
- Also committed `data/reports/acquisition_status.md`, regenerated while answering a
  question about acquisition bottlenecks. The change is real rather than a timestamp:
  the VMBA source now has dependants, taking sources-with-dependants from 695 to 696.
- Not done: no page was built, no export produced, no DNS or Cloudflare configuration
  touched. The researcher explicitly wanted this tracked, not executed.
- Worth recording for whoever picks ACCESS-009 up: the acquisition register now shows
  Segal 2000 accounts for 252 of the 287 candidate records blocked on unheld
  publications, and it is not obtainable by automated research.

## 2026-09-13 — Claude — Pair evidence in the concordance workbench

**Claimed:** QA, OPS-001
**Corpus:** unchanged — state digest `4a7c6ca8d9a9` (read-only throughout)
**Tests:** 228 Python tests and 15 Node unit tests passed; panel checked in the browser against a corroborated pair and a conflicting one

- Wired `pair_evidence` into the console. The review payload now carries the facet
  comparison, and every queue row carries its band, so a reviewer can see which pairs
  actually hold a disagreement before opening any of them. Eighty rows band in 97 ms.
- Wrote the panel as description, not advice. The band reads "claims agree", "claims
  disagree" or "nothing compared" rather than anything resembling a verdict, each band
  carries a sentence saying what it does and does not mean, and the panel closes by
  saying it compared stored claims only. A unit test asserts the rendered markup never
  contains proposing language such as "should be merged" or "safe to merge".
- "Nothing compared" is worded deliberately. Thirty of the seventy-seven pairs landed
  there, and the panel says in as many words that this is silence rather than
  disagreement, because the earlier mis-banding came from reading one as the other.
- Colour never carries meaning alone: every facet is a labelled chip and the band has a
  text label beside it. Reused the console's existing tokens, which are defined for
  both themes.
- The browser check found a real problem that no test would have. The console on port
  8765 has been running since 6 September, so `ibi serve` could not bind and the page
  under inspection was serving a week-old build: fresh `app.js`, stale API, no panel.
  Verified on a spare port instead of killing the researcher's process. **That console
  needs restarting before any of this is visible in it.**
- Next: the queue cannot yet be filtered or sorted by band, which is the obvious
  follow-on now that every row carries one.

## 2026-09-13 — Claude — Pair-evidence comparison for the next sweep

**Claimed:** QA, CONC-001
**Corpus:** unchanged — state digest `4a7c6ca8d9a9` (read-only throughout)
**Tests:** 225 Python tests passed, 22 of them new in `tests/test_pair_evidence.py`

- Corrected the record first. The earlier entry called this a project banding
  weakness; it was not. `CORE_COVERAGE["location"]` in `identity.py` has grouped
  `current_location` with `current_or_reported_collection` all along, and
  `conflicts.py` uses it. The fault was that this session's dedupe comparison was a
  throwaway script that compared raw field names and never reached for that map.
- The real gap was that nothing in the codebase compared a dedupe pair at all, so the
  next sweep would have repeated the mistake. Added `dedupe.pair_evidence`, which
  returns agreeing and conflicting facets and a band, and never a decision.
- It compares by coverage group, so the two location fields, the four spellings of the
  biblical-quotation field and the three of client each count once.
- It normalises before comparing. Twenty-one of the seventy-seven pairs looked like
  conflicts over a definite article. Three forms of the Hilprecht Collection name are
  collapsed explicitly rather than by fuzzy matching, which would risk merging two
  genuinely different collections.
- It restricts conflict to ten facets that are properties of the physical object.
  Comparing by group alone made things worse, not better: `publication` is a
  grab-bag, and two records of one bowl routinely cite different publications, which
  produced eight fresh false conflicts. `biblical_intertexts` is corroborating-only
  for a related reason — sources list subsets of the verses on a bowl, so two
  disjoint lists are not a contradiction, while a shared verse is still real evidence.
- A language attribution that refines another is treated as compatible, matched on a
  prefix rather than any substring so that a qualifier appended to a shared reading
  counts while "Syriac" against "Hebrew Language" stays a conflict.
- Re-banded the same 77 pairs as a check. 23 apparent conflicts fall to 2, and those 2
  are exactly the pairs the researcher was asked to decide — CBS 9008 and HS 3003. No
  decision changes; all 77 were already resolved. Recorded the recount in the dossier
  beside the original bands rather than overwriting them.
- Next session: `pair_evidence` is available but nothing calls it yet. Wiring it into
  the research console's dedupe review, so a reviewer sees the facets rather than only
  the shared identifier, is the obvious next step.

## 2026-09-13 — Claude — Remaining exact-identifier pairs and the last VMBA bowl

**Claimed:** CONC-001, DISC-003
**Corpus:** changed (51 dedupe decisions applied; JBA 5 attached) — state digest `4a7c6ca8d9a9`
**Tests:** 203 Python tests passed; reports regenerated; exact-identifier queue now empty

- Re-examined the 30 pairs banded "no overlapping evidence" on 13 September. The band
  name was misleading: these are not evidence-free, they are complementary. Each pair
  shares an institution-scoped accession number — 13 Berlin VA, 8 Penn CBS, 2 Hilprecht
  HS, 1 Yale YBC, 5 Schøyen MS — with a museum or collection catalogue on one side and
  a text edition on the other. No field agreed because the two record types describe
  different things, not because they disagree.
- Resolved all 51 as `same_object` with per-group rationale naming the identifier
  namespace. Distinct objects moved from 1,683 to 1,652, resolved duplicate records
  from 286 to 317, and no exact-identifier pair remains pending.
- `DED-97D7DA99E25B` turned out to be positively corroborated rather than merely
  unopposed, and the VMBA recovery is what showed it. The context-citation record for
  MS 1927/64 carries `biblical_quotation` Zechariah 3:2, and the recovered VMBA record
  lists Zech 3:2 for JBA 5 — the only bowl among JBA 1-64 carrying that verse. Recorded
  as independent corroboration.
- Noted a banding weakness to fix before the next sweep: a pair agreeing on collection
  could still look like it had no overlap, because `current_location` and
  `current_or_reported_collection` hold the same fact under different field names. The
  JBA 5 pair agreed on the Schøyen Collection and the comparison missed it. (Corrected
  in the following session: the fault was in this session's throwaway comparison
  script, not in the project's field model, which already grouped those two fields.)
- Attached JBA 5 to its cluster's canonical record. All 64 VMBA bowls now carry
  dimensions, clients and biblical quotations: 64 appearances and 213 claims.
- Pruned the backup directory on the researcher's instruction, bringing it into line
  with the stated limit of ten. Compressed the ten most recent snapshots and verified
  every archive before deleting anything: sound gzip stream, byte-exact decompression,
  SQLite `integrity_check` ok, and object and claim counts that decrease monotonically
  going back in time. Then removed the ten superseded originals, the 24 older
  snapshots, and 26 orphaned `-shm`/`-wal` sidecars. Backups went from 1.1 GB to 67 MB
  and `data/private` from 2.1 GB to 1.1 GB. The source archive (669 MB) was not
  touched; it is the part Git cannot reconstruct.
- A restore is now `gunzip -c <archive>.gz > data/private/ibi.sqlite3`. Worth
  remembering that the corpus is reproducible from the checked-in manifests anyway —
  every write this session replayed idempotently — so these snapshots are a
  convenience, not the system of record.

## 2026-09-13 — Claude — Exact-identifier dedupe decisions and the four unblocked bowls

**Claimed:** CONC-001, DISC-003
**Corpus:** changed (26 dedupe decisions applied; four VMBA appearances and 13 claims attached) — state digest `907a6b99ccd5`
**Tests:** 203 Python tests passed; both manifests replayed idempotently (209 VMBA claims before and after); reports regenerated

- Did not run `ibi adjudicate-exact`. It marks every pending exact-identifier pair
  `same_object` in one pass with no per-pair check, and research_protocol step 2 is
  explicit that an exact identifier is strong evidence rather than a merge
  instruction. Compared all 77 pairs on the step 3 fields instead and committed the
  evidence as a dossier containing no decisions.
- The bands were 24 corroborated, 30 with no overlapping evidence, 21 differing only
  in wording, and 2 substantive. The 21 were artefacts: `The Schøyen Collection`
  against `Schøyen Collection`, the long and short forms of the Hilprecht Collection
  name, and language granularity such as `Jewish Babylonian Aramaic and/or Hebrew`
  against `Jewish Babylonian Aramaic`. Checked whether that wording noise inflates the
  wider conflict surface; it does not, only 10 of 266 objects.
- The researcher resolved the two substantive pairs. CBS 9008 is read as Syriac on
  Moriggi 2014, a corpus edition, against an undated Penn Museum record's "Hebrew
  Language" — and a museum catalogue entry cannot verify a reading. HS 3003 is
  collection history, Brand 2019's private Berlin collection preceding Ford and
  Morgenstern 2020's Hilprecht Collection, Jena; a collection catalogue can verify a
  current location. Both differences were recorded as not evidence against identity.
  Neither competing claim was deleted: the corpus holds both sides, which is what
  keeps the collection-history reading legible.
- Applied 26 decisions — the 24 corroborated plus those 2 — as `same_object` through a
  checked manifest, attributed to the researcher with the evidence prepared here.
  Distinct objects moved from 1,701 to 1,683. Deliberately left the 30 evidence-free
  and 21 wording-only pairs pending rather than bundling them into an approval that
  covered 24.
- Four of the five bowls withheld on 13 September are now unblocked. Attached JBA 17,
  19, 20 and 56 to each cluster's canonical record, chosen with the project's own
  `_best_object` ranking rather than by hand. 63 of the 64 VMBA bowls now carry
  dimensions, clients and biblical quotations.
- JBA 5 stays withheld. Its pair (`MS 1927/64` against a context-citation record)
  shares one identifier and no comparable claims, so it is still pending.
- Next session: the 51 pending pairs, of which 21 are wording-only and ready for the
  same treatment once approved, and 30 need evidence that does not exist in the corpus
  yet. `data/private/backups/` now holds 33 files against a stated limit of ten and
  still needs a human decision before anything is deleted.

## 2026-09-13 — Claude — Virtual Magic Bowl Archive recovery

**Claimed:** DISC-003, META-008, CONC-001
**Corpus:** changed (59 source appearances and 196 claims on existing Schøyen objects; exact-identifier dedupe sweep queued 77 pending pairs) — state digest `b9c37ff1eb1f`
**Tests:** 203 Python tests passed; manifest replayed idempotently (196 claims before and after); SQLite integrity and foreign-key checks clean

- Recovered the Virtual Magic Bowl Archive, which carried zero appearances and zero
  claims because the September campaign hit an AWS WAF challenge on the Exeter
  repository and HTTP 429 on the Wayback CDX API. The CDX API answered normally this
  time and the archived listing pages are intact. Nothing was bypassed: every request
  returned HTTP 200 from the public Internet Archive, and `ore.exeter.ac.uk` was not
  touched, so `SRC-E26693A4D198` stays `blocked` and untested.
- Recovered all 64 VMBA records — JBA 1-64, the Schøyen bowls edited in Shaked, Ford
  and Bhayro vol. 1 — with Schøyen MS number, dimensions, clients, biblical
  quotations and per-bowl photograph counts. All 64 already existed as objects and
  the JBA↔MS concordance already in the corpus matched on all 64, so the recovery is
  independent confirmation of the concordance and new content for everything else:
  63 of the 64 carried no `dimensions`, no `client` and no `biblical_quotations`
  claim from any source.
- Applied 59 of 64 as `reported` claims. Dimensions carry the measurement-convention
  caveat and are not verified against the printed edition; `client` records the
  archive's own label without separating commissioner, beneficiary and scribe.
- Held back five bowls (JBA 5, 17, 19, 20, 56) that each resolve to two object
  records. Auditing that gap found 62 exact-identifier pairs missing from
  `dedupe_candidates` entirely, five of them sharing two exact identifiers. The
  matcher is fine; the sweep was simply stale, because the second record in each pair
  came from the 11 September ingest. Ran `ibi dedupe --threshold 0.6` — above 0.55, so
  the exact pass runs and the O(n²) label pass is skipped — which queued 77 pairs, all
  `pending`. No merge was made and no pair was decided.
- Deposited no image. The ~1,239 surviving VMBA photographs are © Matthew Morgenstern
  and the Schøyen Collection, released for non-commercial research only — the same
  NC-versus-CC-BY conflict that already withholds Waller 2022. The claims record only
  that photographs exist and how many.
- Also closed out the uncommitted 7 September findspot session, which had been sitting
  in the working tree for six days. Its two corpus-parity tests were failing from a
  WAL read problem, not a data problem: the corpus runs in WAL mode, a plain `mode=ro`
  connection has to create the `-shm` file and cannot, so the test failed whenever the
  last writer closed cleanly. Switched it to `mode=ro&immutable=1`, which reads the
  snapshot directly. Parity still holds exactly — 61 findspot strings, none unmapped,
  none orphaned.
- Next session should adjudicate the 77 queued pairs, starting with the five that
  share two exact identifiers, one of which is a Hilprecht pair
  (`HS 3039` / `MRLA 8::32`) unrelated to this work. Also outstanding: the five
  withheld VMBA bowls, which attach as soon as their duplicates are resolved; and
  `data/private/backups/` now holds 32 files against a stated limit of ten, which
  needs a human decision before anything is deleted.

## 2026-09-12 — Codex — Gordon open-edition reconciliation

**Claimed:** TEXT-001, SCHOL-005, DISC-003
**Corpus:** changed (three complete PDF deposits, four corrected and scoped sources, four resolved publication keys, 24 source appearances, 15 exact existing-object attachments, and 9 new candidates) — state digest `5a268171bafc`
**Tests:** 203 Python tests passed; all manifests replayed idempotently; archive hashes, SQLite integrity and foreign keys, JavaScript syntax, JSON/JSONL parsing, deterministic manifest generation, and diff whitespace all passed

- Used the Czech Academy's official Kramerius service to recover and visually inspect complete article-and-plate sequences for Gordon's 1934 texts A–F, 1934 text G, and 1937 texts H–O. Deposited all three by hash and retained the repository's contractual-use terms as copyrighted rather than confusing open access with an open reuse licence.
- Inspected Gordon's complete 1934 AASOR edition of Iraq Museum no. 9737 through an institutional scan. Corrected and scoped its source record but did not archive the file because the project crawler could not verify robots permission. CAL and ASOR bibliographic records independently confirm the four citations.
- Added 24 page-located source appearances. Sixteen are complete bowl editions: fifteen attach to existing records by exact Gordon labels or museum numbers, and Harvard Semitic Museum 8669 is a new candidate. Seven numbered Istanbul survey bowls and National Museum 207962 are eight further new candidates. No uncertain identity was merged.
- Preserved Gordon's uncertain 1937 Ashmolean attribution for no. 91731 beside the current British Museum evidence rather than silently replacing either source. No protected transcription, translation, plate, or commentary was published.
- Updated the repository overview, the Waller control-list note, all current reports, and the living mission plan. Current scale is 1,969 records, 1,701 identities, 2,179 appearances, 32/32 resolved publication keys covering 895 records, and 540 located appearances across 16 complete inspected edition units. The next automation step is a 14-day read-only shadow run over Kramerius, LOC and Crossref/OpenAlex; corpus writes, merges, rights decisions and publication remain human-reviewed.

## 2026-09-12 — Codex — Wohlstein open-edition reconciliation

**Claimed:** TEXT-001, SCHOL-005, DISC-003
**Corpus:** changed (two open PDF captures, two corrected and scoped publication sources, two resolved publication keys, and 11 exact-VA appearances on six existing Berlin objects) — state digest `fae0ba6fd9e8`
**Tests:** 203 Python tests passed; manifest replay was idempotent; archive hashes, SQLite integrity and foreign keys, JavaScript syntax, JSON/JSONL parsing, deterministic manifest generation, and diff whitespace all passed

- Ran the first bounded remote open-repository research pilot while Library of Congress work is paused. Located complete scans of Joseph Wohlstein's 1893 and 1894 articles, retained repository and DOI evidence, captured both PDFs with headers and hashes, and visually checked the pages carrying the editions.
- Corrected the two provisional bibliography records, classified the 1893 article as a single-object edition and the 1894 continuation as a four-object corpus edition, and registered both publication keys. All 28 current publication keys now resolve; the held-document count is 35 scholarship works and 36 source-linked PDFs.
- Added eleven exact-VA source appearances across six existing Berlin objects. Five are complete editions with transcription and German translation (VA 2422, 2416, 2426, 2414, and 2417); six are exact contextual cross-references, including Wohlstein's fragment report for VA 2434. No new candidate or identity was created and no merge was made.
- Did not import the public-domain German text from noisy OCR. A separate page-by-page transcription, verification, and content-bound publication review is required before it can expand the 44-item public reading room. Next remote work can proofread these five texts, reconcile further open early editions (especially Gordon and Pognon), classify the 155 unscoped scholarship works from authoritative metadata, and build a no-write shadow monitor for LOC and open repositories.

## 2026-09-12 — Codex — Public-copy repair and publication reconciliation

**Claimed:** TEXT-001, SCHOL-005, DISC-003, OPS-001
**Corpus:** changed (Stübe 1895 source correction and scope, one complete PDF capture, 19 source appearances, 17 exact-object attachments, 2 new candidates, and one resolved publication key) — state digest `73bd84d088e1`
**Tests:** 203 Python tests passed; manifest replay was idempotent; archive hashes, SQLite integrity and foreign keys, JavaScript syntax, JSON/JSONL parsing, and diff whitespace all passed

- Replaced the misleading “115 of 115” reading-room language with separate measures: the 115-title JBA bibliography checklist; 26 bowl-level publication keys covering 879 candidate records and 715 projected identities; 775 identities carrying any publication reference; and 44 currently readable text records (35 public-domain translations plus nine project-authored summaries). Three stale approvals correctly fail closed. Updated the repository overview, living mission plan, generated reports, and the dated control-list report with the same distinction.
- Located Stübe 1895 through the open Bayerische Staatsbibliothek copy linked by its stable catalogue identity, assembled and deposited the complete 92-image scan by hash, corrected the provisional source record, and recorded its inspected corpus-edition scope and rights/access evidence.
- Indexed all 19 numbered Stübe catalogue objects with printed-page locators. Seventeen attach as new source appearances to existing modern Berlin records by exact VA inventory number; two separately numbered Pahlavi bowls lack inventory numbers and remain new provisional candidates. Stübe nos. 14–15 are explicitly classified as inscribed skulls, not bowls. No uncertain identities were merged.
- Updated the LOC queue: Stübe is satisfied digitally outside LOC; Segal 2000 and Naveh–Shaked 1993 remain unavailable and queued, Mokhtarian remains onsite-digital but not located, and the requested Isbell 1975, Naveh–Shaked 1998, Müller-Kessler/TMH 7, and Yamauchi 1967 volumes remain pending.
- The database is ready for bounded, lead-only automated internet research, but not unattended scholarly ingestion or publication. The next automation work is a shadow-mode LOC/open-repository monitor with no corpus writes, plus backup, alerting, rate limits, and a kill switch before scheduling.

## 2026-09-12 — Codex — Researcher-supplied LOC follow-up PDFs

**Claimed:** SCHOL-005, SCHOL-006, TEXT-001, META-008, ACCESS-002
**Corpus:** changed — state digest `150b3848c948`
**Tests:** 203 Python tests passed; archive verification, SQLite integrity and foreign-key checks passed; JSON/JSONL manifests validated

- Audited all six supplied files by hash, text, page structure and representative rendered pages. Waller 2022 is an exact duplicate of the held capture; Hornkohl-Khan 2020, Layard 1853 and Pognon 1898-1899 are complete books; Molin's chapter is complete within Hornkohl-Khan; the Naveh-Shaked 1993 file is only seven-page partial front matter; and the Project MUSE file is Wajsberg's review rather than Juusola's book.
- Deposited the five unique PDFs under their actual source identities and linked the shared Hornkohl-Khan file to Molin's chapter. Rights and completeness remain explicit; no modern copyrighted transcription, translation, commentary or image was copied into the public corpus.
- Indexed thirty separately numbered Pognon bowls and six separately numbered Ellis bowls as conservative probable candidates with exact publication locators. No identity merges were inferred, and Ellis's unquantified fragment group was not misrepresented as a single bowl.
- Recorded the researcher's LOC outcomes: Isbell 1975, Naveh-Shaked 1998, TMH 7 and Yamauchi 1967 are requested; Segal 2000, Naveh-Shaked 1993 and Mokhtarian 2015 remain blocked but queued; Juusola 1999 remains unheld because only its review was supplied.
- Updated the generated acquisition, campaign, conflict, enrichment and mission-plan reports. Current scale is 1,958 candidate records, 1,690 identity hypotheses, 862 sources and 2,125 appearances; all 25 publication keys resolve, and nine complete corpus/catalogue holdings support 486 located appearances.

## 2026-09-11 — Codex — LOC access map and automation readiness

**Claimed:** SCHOL-005, DISC-003, OPS-003
**Corpus:** unchanged — state digest 46e1246db3ff
**Tests:** 203 Python tests passed; roadmap generation, JSON parsing and diff-whitespace checks passed

- Updated the living maturity roadmap with a verified Library of Congress access map that separates remotely open digital works, onsite-only digital resources, physical books, and microform. Added onsite routes for Naveh–Shaked 1993, Yamauchi 1967, Pognon 1898, Juusola 1999, the full Moriggi–Bhayro Syriac volume, and Stübe 1895 microfilm.
- Added a separate digital queue for the already held *Bible in the Bowls*, the CC BY 4.0 *Studies in Semitic Vocalisation and Reading Traditions*, LOC's onsite-only digital edition of Mokhtarian 2015, and the LOC-linked electronic copy of Layard 1853. A Digital catalog label is no longer treated as proof of remote access.
- Marked DISC-003 in progress and documented the current automation boundary: lead-only monitoring over stable public endpoints can begin, but unattended corpus writes remain gated by per-source policies, encrypted off-device backup, scheduling and alert controls, disable switches, and a 14-day shadow run.
- No source, object, claim, identity, rights decision, capture, or public release changed.

## 2026-09-11 — Codex — Additional Library of Congress scholarship volumes

**Claimed:** SCHOL-005, SCHOL-006, TEXT-001, META-001, ACCESS-002
**Corpus:** updated — state digest 46e1246db3ff; pre-batch backup integrity-checked
**Tests:** 203 Python tests passed; archive verification, SQLite integrity and foreign-key checks passed; manifests replayed without corpus changes

- Deposited five researcher-supplied PDFs in the private content-addressed archive: complete Levene 2013, Berlin 2018, Saar 2017, and Naveh–Shaked 1985 volumes, plus Christelle Jullien’s complete three-page review of *Studies in the Syriac Magical Traditions*. The review file is explicitly not treated as the reviewed book.
- Added 214 rights-safe, page-located object appearances: 30 physical bowls from Levene 2013, fourteen from the distinct 1985 first edition of Naveh–Shaked, and 170 minimum physical-object appearances from the Berlin catalogue’s 169 numbered entries. Berlin entry 168 is represented as two unresolved minimum bowl components because the catalogue says its fragments come from at least two different bowls; skull and eggshell material remains typed as non-bowl rather than inflated into the bowl count.
- Corrected the Berlin source from provisional repository metadata to the inspected title, author/contributor order, DOI, ISBNs, and 169-entry scope. Registered all three new publication keys; all 23 current keys resolve, covering 841 candidate records before identity deduplication.
- Added Saar’s monograph as a thematic study. Used Jullien’s complete contents list to index the reviewed 2021 volume and all nine contributions, including Moriggi’s Syriac-bowl chapter, while recording that none of those chapter texts or the book itself was supplied.
- Scholarship now contains 214 works, 26 source-linked held documents, 53 classified scopes, and 161 unclassified works. Complete corpus/catalogue holdings now support 450 direct appearances; publication-reference coverage rises to 598/1,074 probable or confirmed identities (55.7%).
- No copyrighted transcription, translation, commentary, review prose, or image was copied into the corpus or public layer. Added the four new claim labels to the explicit field model so all 106 current claim fields remain classified (69 grouped, 37 deliberately excluded).
- Updated acquisition, campaign, conflict, enrichment, and maturity reports and wrote a private research export. The remaining LC priorities are still Segal 2000, Isbell 1975, TMH 7, and the 1998 third edition of Naveh–Shaked; the newly held 1985 first edition is not conflated with it.

---

## 2026-09-11 — Codex — Library of Congress Brill corpus editions

**Claimed:** SCHOL-005, SCHOL-006, TEXT-001, META-001, ACCESS-002
**Corpus:** changed (four complete copyrighted source captures, four source corrections, four explicit scope reviews, 236 source appearances, 519 identifiers, 704 claims, 117 new candidate objects, and four resolved access leads) — state digest 74dda51021f3
**Tests:** 203 passed; archive hashes valid; source-correction, scope, and 236-row candidate manifests replay idempotently; JSON/JSONL, report generation, and diff-whitespace checks passed.

- Deposited complete researcher-supplied copies of *Aramaic Bowl Spells* Volumes One and Two, Moriggi's *A Corpus of Syriac Incantation Bowls*, and Ford–Morgenstern's Hilprecht catalogue in the private content-addressed archive. Corrected their full titles, subtitles, series, ISBNs and imprint years from the books themselves; notably Volume Two is 2022 and the Hilprecht catalogue is 2020.
- Indexed 236 page-located source appearances: JBA 1–64, JBA 65–119, Moriggi's 49 Syriac bowls, and Hilprecht catalogue entries 1–68. Unique exact collection or publication identifiers linked 119 appearances to existing objects; the other 117 remain separate new candidates. No ambiguous identity was merged. Hilprecht entry 69 was deliberately not treated as one object because it is a storage box holding fragments from multiple bowls.
- Added only catalogue-level metadata and source-attributed language/classification claims. All four sources contain full editions and photographs, but the new source records have zero text and zero media rows: copyrighted transcriptions, translations, commentary, and images remain private and uncleared for public reuse.
- Closed the four Library of Congress access leads, marked the old Volume One purchase item satisfied by the private copy, and refreshed the living maturity, acquisition, enrichment, and campaign reports. The scholarship index now has 201 works, 21 source-linked held documents, and 39 scoped works; 162 remain unclassified.
- Publication-reference coverage rises to 524/1,442 distinct identities and 427/904 probable or confirmed identities; all 20 publication keys resolve and cover 627 candidate records. The next high-impact onsite targets remain Segal 2000, Isbell 1975, Müller-Kessler's TMH 7, and Naveh–Shaked 1998. The private rich-text/TEI transformation layer and general completeness ledger remain follow-up work.

---

## 2026-09-11 — Codex — Mehqarim be-Lashon 20 bowl scholarship

**Claimed:** SCHOL-005, SCHOL-006, TEXT-001, META-001
**Corpus:** changed (two scholarship sources, two bowl records, four source-linked captures, four appearances, five identifiers, 35 claims, one media pointer, four scope reviews, one source correction, and two publication-key resolutions) — state digest 77081d22b185
**Tests:** 203 passed; archive hashes valid; candidate, scope, and publication-registry manifests replay idempotently; JSON/JSONL and diff-whitespace checks passed.

- Deposited both the initial one-page English summary (`80a284d04ebf...`) and the subsequently supplied complete 298-page *Mehqarim be-Lashon* 20 volume (`2d087410e676...`) as copyrighted private captures. The full volume is source-linked to its three bowl-relevant articles; Ford's source is corrected from partial to available with the volume imprint, publisher/distributor, and completeness evidence retained.
- Enriched Davidovitz 41 (`IBI-6A5B95130C25`) from Ford's complete pp. 215–230 edition with dimensions, condition, layout, beneficiary/textual voice Aḥay son of Maḥozanita, ten-line extent, Psalm 33:22, formula and lexicon findings, an image pointer, and precise transcription/translation locators. Ford explicitly says popularity and influence; economic success is inferred rather than stated in the readable text, so both the older broad claim and the new qualification are preserved.
- Superseded the incorrect `IBI-PUBREG-14` resolution that had assigned the bowl's `Ford 2023` key to Monika Amsler's differently authored article. The current append-only registry now resolves it to Ford's *My Foes Loved Me*, restoring the correct one-object scholarship count without deleting the historical decision.
- A full contents and term scan found two additional bowl-relevant contributions. Added and classified Ohad Abudraham's pp. 13–30 single-object re-edition and Matthew Morgenstern's pp. 171–194 linguistic study; the remaining volume articles concern other linguistic subjects and were not added.
- Added the Miami University Art Museum Mandaic bowl (`IBI-ADF5E95842DB`) with its dimensions, seven-fragment condition, spiral/exterior layout, script, beneficiary and household, demons, protective purpose, Schøyen parallel, and edition history. Retained an internal source discrepancy: the prose says eleven physical lines, but the edition numbers ten. Added Hilprecht 40c / VT 1981.8 (`IBI-B5259E1CC555`) as a separate comparandum with Abudraham's same-hand and possible shared-beneficiary proposals; no identity merge or independent scribal adjudication was made.
- The scholarship index now holds 201 works, 17 source-linked documents, and 39 classified scopes. No modern transcription or translation, bowl image, authenticity decision, rights approval, or public release was added.

## 2026-09-09 — Codex — Three-layer access roadmap

**Claimed:** ACCESS-001, ACCESS-002, ACCESS-003, ACCESS-006, SCHOL-005
**Corpus:** unchanged — state digest 7aa85d83f9a5
**Tests:** 203 passed; roadmap generation, JSON parsing, and diff-whitespace checks passed.

- Added separate private-research, maximal factual public-reference, and optional paid licensed-service layers to the living maturity model, project rules, licensing guidance, and generated roadmap. Each layer now has a content boundary, next gate, and non-automatic promotion rules.
- Added live scholarship-holdings metrics and provisional collection bands: 15–30 inspected core works for a strong foundation, 50–75 for a visibly impressive collection, and 150–200 plus a defensible multilingual denominator and expert gap review for expert-comprehensive status. Current holdings are 14 source-linked scholarship documents among 199 indexed works.
- Queued pre-Library safeguards: a document completeness/transformation ledger; a private Unicode rich-text package with page anchors; encrypted local and off-device backup; per-item copying-permission notes; and a public-projection audit. Added later gates for rights-chain registration, customer discovery, contracts, access controls, royalty accounting, and takedown procedures.
- Refreshed stale current-state prose to 844 sources, 1,591 candidates, 26 source-linked captures, 37 classified scholarship works and 162 awaiting scope. No source content, rights decision, public release, or commercial offering was created.

---

## 2026-09-09 — Codex — Researcher-supplied scholarship PDFs

**Claimed:** SCHOL-005, SCHOL-006
**Corpus:** changed (one scholarship source, two linked captures, three source-scope reviews) — state digest 7aa85d83f9a5
**Tests:** 203 passed; archive hashes valid; source and scope manifests replay idempotently; JSON/JSONL and diff-whitespace checks passed.

- Checked all four researcher-supplied PDFs by SHA-256, extracted text and rendered-page inspection. Ford–Morgenstern's 30-page MRLA 8 front matter (`3bbe7fbc...`) and Ford–Abudraham's complete 2018 chapter (`123bcea3...`) exactly match files already in the private archive, so no duplicate captures were created.
- Added James Nathan Ford's complete 2002 JSAI review, *Notes on the Mandaic Incantation Bowls in the British Museum*, as a new scholarship source and copyrighted private capture (`86cbcd17...`). It is a high-value linguistic study supplying bowl-by-bowl corrections to Segal's Mandaic readings.
- Linked Edward M. Cook's complete 1992 Khafaje single-bowl edition to its existing source record as a copyrighted private capture (`1e5a426a...`). Recorded evidence-bound scope reviews for Ford 2002, Cook 1992, and Ford–Abudraham 2018; the Ford–Morgenstern catalogue already receives its catalogue scope from the publication registry.
- Regenerated the roadmap, acquisition, enrichment and campaign reports. The corpus now has 844 sources, 26 source-linked captures (15 PDFs), 199 scholarship works, 37 classified scopes and 162 unclassified works.
- No transcriptions, translations, images, bowl claims, identities, rights approvals, or public release were added. Object-level extraction from Cook, Ford–Abudraham and Ford's Segal corrections is valuable follow-up work, but remains a separate review batch.

---

## 2026-09-09 — Codex — Frank Ruhl Libre typography

**Claimed:** none — OPS site typography selected by the researcher
**Corpus:** unchanged — state digest 12a0c0d20986
**Tests:** 203 Python tests and 8 JavaScript controller tests passed; font asset, MIME response, JavaScript, and diff-whitespace checks passed.

- Applied Frank Ruhl Libre to Bowlam's shared serif token, covering the wordmark, narrative headings, historical dates, reader headings, and other display roles while preserving the existing sans-serif interface text.
- Bundled Latin, Latin Extended, and Hebrew variable-font subsets locally with the SIL Open Font License, avoiding an external runtime font dependency and retaining Hebrew-script coverage.
- Added a regression check for the chosen typeface and confirmed the localhost server returns the font with the correct WOFF2 media type. No corpus, source, rights, or publication changes.

## 2026-09-09 — Codex — Bowlam opening palette and motion

**Claimed:** none — OPS homepage palette and animation refinements requested by the researcher
**Corpus:** unchanged — state digest 12a0c0d20986
**Tests:** 203 Python tests and 7 JavaScript controller tests passed; JavaScript syntax, diff-whitespace, and local HTTP checks passed.

- Darkened all five opening chapters with the reading room's ink, clay, and muted teal palette, including the map, coverage panel, chart, calls to action, header, and finale.
- Changed the map reveal to a 2.8-second directional sweep of only the approximate find-region shading; the river geometry stays fixed.
- Replaced the independent digit reels with a slower count from 750 CE to 1850 and 1853, and made the decade bars rise in a slower left-to-right stagger.
- Preserved immediate final values under reduced-motion preferences and documented/tested the animation contract. No corpus, rights, source, or publication changes; the console remains localhost-only.

## 2026-09-07 — Codex — Catalogue default-load resilience

**Claimed:** none — OPS visitor catalogue bug report
**Corpus:** unchanged — state digest 12a0c0d20986
**Tests:** 203 Python tests and 6 JavaScript tests passed; fresh uncached browser check confirmed 40 default rows render with no filters.

- Fixed the default Explore page crash when a sparse or stale API row omitted optional script presentation metadata.
- Made visitor row rendering resilient to missing name, language, date, script, source-count, and facet-list fields so one incomplete row cannot blank the page.
- Added JavaScript regression coverage for sparse rows and separate script/language display.
- No corpus, rights, projection, research, or deployment changes.

## 2026-09-07 — Codex — Visitor catalogue presentation

**Claimed:** none — OPS local catalogue and reader presentation requested by the researcher
**Corpus:** unchanged — state digest 12a0c0d20986
**Tests:** 203 Python tests and 4 JavaScript controller tests passed; JS syntax and diff checks; desktop, direct-entry, Back-link, and 390px mobile browser checks.

- Added one shared presentation module for visitor names, collection labels, language, and dates. The three requested naming examples now render as specified; equivalent date spellings collapse while distinct proposals remain attributed on the bowl page.
- Replaced research-first catalogue rows with Bowl, Language, Date, and Explore; added collection, language, material-availability, and object-form filters; made “Most to explore” the default; retained completeness and internal status controls under More research filters.
- Rows now open stable reader pages. Entry pages lead with the bowl and its text, group supported people/purpose and physical facts, distinguish journey labels, group sources while preserving locators, list aliases and catalogue numbers, and move internal IDs/counts into Research details.
- Availability labels follow the gated reader projection: withheld text and unapproved images never qualify as available here. Unapproved image references remain explicitly labelled as references.
- Kept existing `#/reading/<identity-id>` links working and restored the originating catalogue query through the Back link. Fixed the docked homepage browse-button precedence leak outside Home and added a stacked 390px row layout.
- No corpus records, source assertions, rights decisions, private endpoints, publication state, or deployment changed. A later pass can consolidate noisy collection aliases and further refine long source-derived row descriptions.

## 2026-09-07 — Claude — Findspot gazetteer and distribution map

**Claimed:** none — researcher-requested enumeration of recorded findspots, plus a map
**Corpus:** unchanged — state digest 12a0c0d20986 (read-only throughout; the state record is left as Codex wrote it, since nothing in the corpus moved)
**Tests:** 198 Python tests passed (189 existing, plus 9 new gazetteer and corpus-parity tests). Label placement and canvas bounds checked analytically on both map frames; page structure verified in the browser at 800px and 1240px.

- Enumerated every `findspot` claim in the corpus: 225 claims over 205 objects, 60 distinct strings. Added `research/geo/findspot_gazetteer.json` (coordinates for 20 sites, 2 named-but-unlocated places, 5 regions) and `research/geo/findspot_normalization.json`, which maps all 60 strings to a place and an evidence tier. A parity check asserts the two files and the corpus agree exactly, in both directions.
- Added `build_findspot_map.py` (aggregates to `findspot_places.json`, counting objects once at their strongest tier) and `render_findspot_map.py` (renders `findspot_map.html`). Both read the database read-only and write nothing to it.
- Kept coordinates out of the corpus. Locating "Nippur" on the globe is reference data, not a source-attributed claim, so the gazetteer sits beside the corpus rather than inside it; the claim, its source and its locator remain the authority.
- Preserved the distinction the British Museum's data collapses. `Found/Acquired` and `Excavated/Findspot` are separate tiers and separate colours, because the former does not say whether a site is where a bowl was found or where it was bought. 12 objects rest on that weaker field.
- Sites in Babylonia lie within ~15 km and overlap at national scale. They are drawn again in a 4.5× detail inset rather than nudged apart, so no marker sits at a false coordinate. Label positions are solved by a placer that scores candidates against markers, other labels and the canvas edge; no offset is hand-set.
- Did not merge the five objects whose museum record names two findspots (Babylon and Borsippa); they are counted under both and flagged in the dataset as `ambiguous_objects`. Did not publish: the map is a local file, per the rule against deploying a public dashboard.
- Next session could route the two unlocated places — Tell al-Duwayhi (Babil) and Kiamiaz on the Tigris — through the normal lead process, and decide whether the 53 region-only objects deserve a `findspot_evidence_level` claim rather than living only in this projection.

## 2026-09-07 — Codex — Bowlam homepage refinement

**Claimed:** none — OPS local homepage, requested branding, copy, map and motion improvements
**Corpus:** unchanged — state digest 12a0c0d20986
**Tests:** 189 Python tests and 4 JavaScript controller tests passed; JS syntax and diff checks; desktop and 390px mobile browser checks.

- Renamed the brand Bowlam with the requested subtitle; shortened the introductory copy, removed draft notices from the story, and used plain language for collection coverage.
- Matched the desktop opening and docked header browse buttons; the latter appears only after the opening button passes the header, independent of API availability.
- Added a broad shaded find region, inline period wording, verified 1850/1853 references and a collapsed source note. Source locators are in docs/homepage_sources.md.
- Added rolling year digits, timeline drawing, bowl entrance and ring drawing, map shading/river reveal, and section reveals with reduced-motion fallbacks. Browser inspection caught and resolved CSP-blocked inline animation variables by moving them into stylesheet selectors.
- Checked the hero, map, header handoff and final settled year digits on desktop/mobile; mobile has no document overflow. Corpus unchanged; no release or publication.

---

## 2026-09-06 — Codex — Levene–Shaked JSQ 6 source ingestion

**Claimed:** TEXT-001, META-001, META-002, META-003, META-008, SCHOL-006
**Corpus:** changed (M163 enriched; MS 2054/124 added; two source records corrected/scoped) — state digest 12a0c0d20986
**Tests:** 189 passed; archive verification, SQLite integrity and foreign keys valid; JSON/JSONL manifests parse; correction, scope and candidate replay are idempotent; diff whitespace check passed.

- Deposited the complete researcher-supplied JSQ 6 scan privately once for each of its two source records, sharing content hash `19a0ad766308…`. Levene 1999 is now classified as a single-object edition; Shaked 1999 as a thematic companion study.
- Enriched existing Moussaieff M163 (`IBI-63D659859D54`) with source-located dimensions, condition, 30-line count, script, layout, pre-sale provenance limit, June 1997 Christie's sale event, edition/translation pointers, a project-authored summary, and a copyrighted plate reference.
- Added Schøyen MS 2054/124 (`IBI-EAB5621DEDA2`) as a distinct probable whole bowl, with exact collection designation and source-attributed Mandaic language, aggressive purpose, egg historiola, beneficiary-role caution, Trinitarian ending, and comparisons to M163 and MSF B21.
- Corrected the imported Shaked source from OpenAlex's 2016 date to the article's printed JSQ 6 (1999), pp. 309–319 metadata through the immutable source-correction ledger. Attached Shaked's discussion as a second source appearance for M163.
- Did not copy or publish either scholar's modern transcription, translation, or images. The M163 media pointer remains copyrighted and unapproved; only project-authored factual summaries are stored as text. No identity merge, authenticity judgment, or rights approval was made. The new complementary facts add five mechanical comparison flags to the review queue; none is treated as an adjudicated conflict.

---

## 2026-09-06 — Codex — Reviewed GitHub release

**Claimed:** none — OPS release, explicitly authorized by the researcher
**Corpus:** unchanged — state digest 14a1a17d4839
**Tests:** 189 Python tests and 4 JavaScript controller tests passed; outgoing file audit and JSON/JSONL parsing passed.

- Prepared a public snapshot of nine pending commits. Original local history is retained on a local-only backup branch; that branch must not be pushed.
- Reviewed new code, tests, factual bibliographic manifests, source-scope summaries, and aggregate reports against the repository's existing release rules. No new source scans, artifact photos, restricted transcriptions/translations, database files, or full research exports are included.
- Removed personal residence and visit-scheduling context from the outgoing acquisition metadata, lead notes, and roadmap policy. This is a public-file redaction only; the private corpus and original ingestion history are unchanged.
- Automatic approval review blocked the public push because it requires explicit approval of the 41-file payload and destination. Nothing was pushed; the release remains local pending that approval.
- The local UI remains localhost-only. The hero is an original SVG placeholder; historical wording is draft. No rights approval, historical research, public site deployment, or regeneration of the public dataset is part of this release.

---

## 2026-09-06 — Codex — Local introductory home and evidence coverage

**Claimed:** none — OPS local interface workstream, user-approved introduction
**Corpus:** unchanged — state digest 14a1a17d4839
**Tests:** 189 Python tests and 4 isolated JavaScript controller tests passed; JS syntax and diff whitespace checks passed.

- Added a five-chapter scroll introduction at the default home route, with a local illustrative bowl placeholder, schematic map, researcher-supplied 1850/1853 timeline, live publication bars, stable per-identity coverage circles, and links into Explore. Historical copy is explicitly draft; research remains paused.
- Added a local-only read-only snapshot endpoint. Counts use one SQLite read snapshot, and failed refreshes preserve the previous complete catalog. The current snapshot has 1,322 working identities from 1,590 records; 284 edition references, 327 provenance flags, and 324 image references. No restricted contents or media URLs enter the endpoint.
- Added positive coverage filters and URL-backed Explore state. Edition-reference coverage includes resolved publication pointers and sources already classified as editions, while the existing missing-transcription filter retains its narrower meaning.
- Desktop browser checks confirmed the page composition, stable circle positions, all three shortcut counts, refresh/back filter preservation, keyboard dossier opening, and the Read view. Further browser testing was blocked by automatic approval review because the workspace was out of credits; mobile visual verification and the remaining browser checks are pending. Controller tests independently cover failed loads, malformed snapshots, invalidation, and reduced-motion navigation. Responsive layouts and the accessible chart table are implemented.
- No historical research, corpus changes, rights approvals, report regeneration, or public deployment. Documented the routes, count semantics, refresh behavior, and draft assets in the console guide.

---

## 2026-09-06 — Codex — Held-publication scholarship scope classification

**Claimed:** SCHOL-006
**Corpus:** changed (five append-only source-scope reviews) — state digest 14a1a17d4839
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; JSON manifest parses; scope-batch replay is idempotent; corpus-state check recorded.

- Reviewed the five held scholarship PDFs that still required a human scope judgment, using rendered pages plus text extraction: Schwab 1891 is a seven-bowl corpus edition; Levene and Bhayro 2006 is a single-object edition; Kedar 2019 and Waller 2022 are thematic studies; Waller 2025 is a field synthesis.
- Added the five decisions through the append-only source-scope ledger. Together with 27 scopes derived from source type or the publication registry, coverage is now 32/198 works; 166 remain explicitly unclassified.
- Updated the roadmap's stale current publication and conflict-queue numbers while preserving historical change-log statements. All 19 publication keys resolve, 435/435 keyed candidate records sit under a resolved publication, and the current claim-difference review queue is 315 cases, including 285 earlier decisions needing revalidation.
- These labels describe publication scope only. They do not certify complete object enumeration, adjudicate readings, or change text and media rights. Next: continue SCHOL-006 from authoritative abstracts and tables of contents for unheld works, or prioritize newly obtained LC volumes as they become available.

---

## 2026-09-06 — Codex — Library of Congress priority-edition sweep

**Claimed:** SCHOL-004, SCHOL-005
**Corpus:** changed (one source correction, one publication-registry decision, three access leads opened and two bibliographic leads resolved) — state digest c6576fb19da1
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; JSON/JSONL manifests parse; correction and registry replay checks are idempotent; corpus-state check recorded.

- Resolved the last publication key. Official Library of Congress LCCN 2006364726 explicitly identifies Christa Müller-Kessler's 2005 Harrassowitz volume as *Texte und Materialien der Frau Professor Hilprecht Collection*, Bd. 7, so TMH 7 now resolves to SRC-63345F60155B in append-only IBI-PUBREG-20. All 19 current keys resolve and cover 435 distinct candidates.
- Corrected the Waller-derived Müller-Kessler source row from that official metadata while preserving its exact prior state in IBI-SOURCE-CORR-TMH7-LOC-BIBLIOGRAPHY. The record now carries the verified author, imprint, series, ISBN, LCCN URL and onsite call number; it remains explicitly unread.
- Confirmed three additional exact-edition access routes and expanded the LC queue from five to eight volumes: TMH 7 under PJ5208.A5 M85 2005, Moriggi 2014 under PJ5615 .M665 2014, and Naveh–Shaked's 1998 third edition under BM729.A4 N38. The available 1985 first edition is recorded as an alternate, not conflated with the corpus's 1987 source.
- Resolved the old TMH-specific and combined MRLA 8/TMH 7 bibliographic leads, and opened separate consultation leads for the three newly queued works. PURCHASE-001 remains backup-only; no new purchase was added because LC holds each checked edition onsite.
- No item was requested, purchased, read or captured, and no bowl reading, text, image, identity, rights decision or public release changed. Next: obtain the Reader Identification Card, consult LOC-READ-001 and LOC-READ-002 first, then work down the remaining six-item queue with page-level evidence.

---

## 2026-09-06 — Codex — Library of Congress offline-access strategy

**Claimed:** SCHOL-005
**Corpus:** changed (three access leads updated and two opened for confirmed LC holdings) — state digest 119b9e4e20e8
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; roadmap and acquisition manifests parse; corpus-state check passes.

- Confirmed both user-supplied records in the live Library of Congress catalog. LCCN 2013009563 holds *Aramaic Bowl Spells* Volumes 1 and 2, both available onsite under PJ5208.A2 S53 2013; LCCN 2001369942 holds Segal 2000, available onsite under PJ5208.A5 S45 2000.
- Made the Library of Congress the roadmap's default offline source, added a five-item reading-room queue pending the researcher's Reader Identification Card, and changed PURCHASE-001 to backup-only. Purchases now follow LC, other libraries, interlibrary loan and repository checks.
- Continued the next acquisition step: confirmed Isbell 1975 available onsite under PJ5208.A5 I8 1975 (LCCN 75015949), and Ford–Morgenstern Volume One available onsite under PJ5208.A2 2020 (LCCN 2019026750). Opened or updated evidence-bound access leads for both and for *Aramaic Bowl Spells* Volume Two.
- The LC record dates Ford–Morgenstern as [2020]- while the source cites the 2019 Brill imprint; both are preserved pending inspection of the physical volume. No item was requested, purchased, read or captured, and no bowl claim, identity, text, image, rights decision or release changed. Next: obtain the Reader Identification Card, request LOC-READ-001 and LOC-READ-002, then record page-level evidence from Segal 2000 and the 2013 volume.

---

## 2026-09-06 — Codex — Segal 2000 acquisition-route review

**Claimed:** SCHOL-005
**Corpus:** changed (one acquisition lead reopened with an authorized library route) — state digest 0522f7d4a37e
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; roadmap and acquisition manifests parse; corpus-state check passes.

- Assessed Segal 2000, the highest-impact acquisition item at 252 distinct candidate records. British Museum and Google Books expose metadata, not the complete work; Foyles and Hatchards list it out of stock.
- Found the complete 239-page, 159-plate volume in the NYPL Research Catalog as an offsite item available by advance request, call number *ODF+ 02-6279. Reopened LED-DF20C6F96C3F from blocked to open with this authorized route and ISBN 0714111457 / 9780714111452.
- Did not add Segal to the purchase register. The visible used copy was about US$408 plus shipping, so library or interlibrary access should be attempted before purchase. PURCHASE-001 remains the 2013 *Aramaic Bowl Spells* volume.
- Updated stale roadmap acquisition and scholarship-scope counts and regenerated roadmap, acquisition, enrichment, campaign and private-export outputs. No copy was requested, borrowed, bought or read; no catalogue extraction, bowl claim, identity, text, image, rights decision or public release changed. Next: Mike can request the NYPL copy; otherwise continue SCHOL-005 by assessing Isbell 1975 or another high-impact access lead.

---

## 2026-09-06 — Codex — Roadmap publication purchase register

**Claimed:** SCHOL-005
**Corpus:** changed (one acquisition lead linked to the verified purchase record) — state digest a06079c9cf02
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; roadmap and acquisition manifests parse; corpus-state check passes.

- Added a durable `purchase_register` to the roadmap input and renderer. The generated roadmap now has a Publications to purchase table with stable IDs, priority, status, source linkage, research need and publisher URL; a regression test covers its rendering.
- Confirmed the user-supplied Brill title 20045 as Shaked, Ford and Bhayro, *Aramaic Bowl Spells: Jewish Babylonian Aramaic Bowls, Volume One* (2013), e-ISBN 9789004229372. Added it as PURCHASE-001 and updated IBI-LEAD-JBA2013-ACCESS to the canonical purchase page.
- Prices are checked at purchase time, not frozen in the roadmap. Authorized institutional access, interlibrary loan or a researcher-supplied copy can satisfy the need and will change the status without deleting its history.
- No other blocked work was promoted to the purchase list: unlocated and merely paywalled publications remain acquisition leads until open, repository and library routes are checked. No document, bowl reading, text, image, rights decision or public release changed. Next: acquire or supply PURCHASE-001, or assess the next high-impact acquisition lead for purchase necessity.

---

## 2026-09-06 — Codex — Ford 2002 attribution reconciliation

**Claimed:** TEXT-001
**Corpus:** changed (one source correction, one appearance, one identifier, one claim and one resolved lead) — state digest 917a7aede409
**Tests:** 180 passed; archive verification, SQLite integrity and foreign keys valid; manifests parse as JSON/JSONL; correction replay and corpus-state checks pass.

- Resolved IBI-LEAD-FORD2002-ATTRIBUTION. The JANES and Bar-Ilan publication records identify J. N. Ford; current OpenAlex metadata names Jane Ford. The earlier Müller-Kessler row was an OpenAlex metadata artifact rather than the journal article.
- Added migration 014 and `ibi ingest-source-corrections`: checked bibliographic repairs now retain immutable before/after source states, evidence hashes and optional replacement-source pointers. The exact imported Müller-Kessler state is preserved in IBI-SOURCE-CORR-FORD2002-ATTRIBUTION; the live row is now honestly classified as repository metadata.
- Attached the correctly attributed SRC-FORD2002-JANES appearance, museum number and title-supported Mandaic claim to the existing BM 91715 object without an identity merge. Regenerated roadmap, acquisition, enrichment, conflict, campaign and private-export outputs.
- The source fingerprint change returned one BM 91715 location comparison to the QA revalidation queue (314 to 315); it was not silently re-approved. No full article reading, text/media ingestion, rights decision or publication occurred. The separate full-text access lead remains blocked. Next: continue TEXT-001 with the provisional Ford concordances, or obtain the 2013 volume through the recorded authorized route.

---

## 2026-09-06 — Codex — Ford 2013 edition access follow-through

**Claimed:** TEXT-001
**Corpus:** changed (one acquisition lead, one lead update, four search queries) — state digest 32216dd4da51
**Tests:** 176 passed; archive verification, SQLite integrity and foreign keys valid; manifests parse as JSON/JSONL.

- Inspected the official De Gruyter Brill page: the 2013 *Aramaic Bowl Spells* volume requires purchase or institutional access and exposes no complete authorized reading copy. Recorded WorldCat as the library route.
- Inspected the existing Internet Archive item's metadata without acquiring the file. Its complete community upload has no license, rights statement or evidence of depositor authority, so it was not used as an authorized edition.
- Added the evidence-bound acquisition review, opened priority-1 IBI-LEAD-JBA2013-ACCESS, and updated IBI-LEAD-FORD2014-SPECIALIST so reading comparison cannot proceed from publisher/catalogue metadata or the unverified upload. Regenerated roadmap, acquisition, enrichment and campaign reports.
- A replay check of `ingest-search-log` created one extra empty search-run row while leaving the four query rows idempotent (4, not 8). It was retained and disclosed rather than hand-deleted, in keeping with the append-only rule.
- Ford 2002 attribution and Davidovitz 27 identity remain separate open leads. No identity merge, reading adjudication, rights decision, text/media ingestion or publication occurred. Next: obtain the volume through institutional access, purchase or researcher supply; otherwise continue a different bounded TEXT-001 publication-reference cohort.

---

## 2026-09-06 — Codex — Ford batch closeout after Claude reader work

**Claimed:** none (completed TEXT-001 batch integration verification)
**Corpus:** unchanged — state digest 2e8740192442
**Tests:** 176 passed; archive verification, SQLite integrity and foreign keys valid; live reader projection assertions passed.

- Re-read Claude's handoff and commits through 05ba1dc. Working tree clean and database matched Claude's recorded baseline. Preserved the new reading room, scholarship index, search/browse, media gates and interface changes.
- Verified the completed Ford batch in the current reader projection: all 16 source appearances and 38 attributed metadata claims survive; no Ford transcription, translation or media content is emitted.
- Verified both edition-enumeration and commentary-indexing leads are resolved. Checked both research-review hashes against the archived article; no corpus writes during inspection.
- This closes the bounded Ford edition/commentary indexing task. TEXT-001 remains in progress corpus-wide; obtaining the 2013 edition, specialist comparison and remaining attribution/concordance questions are separate open roadmap work, not silently treated as completed.
- No code or corpus edits were needed. No derived reports invalidated or public artifact published. Tests reflect Claude's current 176-test suite, replacing the earlier 134-test validation baseline for this handoff.

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

## 2026-09-05 — Claude — Tokenise the stylesheet; fix contrast everywhere

**Claimed:** none (defect fix)
**Corpus:** unchanged
**Tests:** 176 passed

Mike flagged Explore, Enrichment and Concordance. The previous fix treated
symptoms; this is the cause.

- **The stylesheet was written light-only with 91 literal colours.** Adding a
  dark palette flipped the tokens and left every literal behind, so any rule
  with a hard-coded colour kept its light value on a dark ground. Replaced ~40
  literals in rules with semantic tokens — `--th-bg`, `--row-hover`, `--track`,
  `--ok-bg` / `--ok-ink` / `--ok-line` / `--ok-dot`, `--danger-soft` /
  `--danger-ink`, `--amber-ink`, `--chip-bg` / `--chip-hover`, `--monogram`,
  `--on-accent` — each with a dark counterpart. Three literals remain, all on
  the always-dark chrome bar where they are correct.
- **`background: white` is a keyword, so the hex sweep missed it.** Eleven rules
  used it, including `.queue-card`, `.coverage-matrix`, `.pressure-grid article`
  and `.review-workbench` — which is why Enrichment and Concordance were white
  cards with pale text at a **1.3:1** ratio. All tokenised.
- Found the rest by measurement rather than eye: a script walking every visible
  text node in all five views, computing contrast against its resolved
  background. That is what caught `.search-field span` at **1.07:1**, the
  identifier previews at 2.8, and the eyebrows at 2.6.
- Also raised `--faint`, `--amber` and `--cyan`, which were pale enough to fail
  as small text even in light mode, and moved `.eyebrow` and `.queue-rank` off
  `--faint`.

**Worst contrast, before and after, across all five views:**

| | before | after |
|---|---:|---:|
| dark | 1.07 | **4.6** |
| light | 2.6 | **4.3** |

- Lesson recorded: I verified this interface in an ~800px browser pane and
  called it polished. Both rounds of colour defects would have been obvious in
  a real window. Measure contrast, and screenshot at the actual viewport.

---

## 2026-09-05 — Claude — Fix the dark palette

**Claimed:** none (defect fix)
**Corpus:** unchanged
**Tests:** 176 passed

Mike flagged the colours on a real monitor. Two were outright bugs in my own
dark-mode work, one was a taste failure. I had only ever viewed it in an ~800px
browser pane.

- **The topbar inverted the wrong way.** `.topbar`, `.toast` and `.dossier-head`
  use `background: var(--ink)` with hard-coded `color: white`. My dark palette
  flipped `--ink` from dark slate to cream, so those backgrounds went cream and
  kept white text on them — a washed-out bar with barely-legible wordmark. The
  cause was treating `--ink` as if it were only a text colour. Added semantic
  `--chrome` / `--chrome-text` / `--chrome-dim` / `--chrome-hover` /
  `--chrome-line` tokens that stay dark in both modes, and pointed every piece
  of chrome at them. No rule now depends on `--ink` for a background.
- **`--clay-line: #3a322800`** — an eight-digit hex ending `00` is fully
  transparent, so card and list borders vanished in dark mode. Typo; fixed.
- **The accent clashed.** `#7fb6c9` is an icy cyan and the ground is warm
  brown-black, which reads as a mistake rather than a choice. Moved to a
  verdigris `#8fb9b4` — aged bronze belongs to the same world as the pots, and
  it sits with clay instead of against it. Light mode keeps lapis, which is
  right on cream.
- Also lifted the card surface clear of the page ground (they were two shades
  apart, so nothing separated) and warmed the shell background to agree with the
  reading room rather than fight it.
- Verified both modes: dark is chrome `#100d0a` on page `#17130f` with cards at
  `#221c16` and visible borders; light is unchanged at slate-on-cream with lapis.

---

## 2026-09-05 — Claude — Tranche 5, and the interface plan is done

**Claimed:** reading-room plan, tranche 5 (RIGHTS-005, QA-009 done)
**Corpus:** unchanged
**Tests:** 176 passed (173 before; +3)

- **Filters work on a small screen again.** Below 900px the stylesheet did
  `#filters fieldset { display: none }` — every structured filter vanished on
  tablet and phone, leaving only free-text search. They are now in a native
  disclosure: the summary is hidden above 900px so a wide screen reads exactly
  as before, and below it the panel starts collapsed with all five selects
  reachable. Verified at 375×812: 5 selects present, 0 before.
  - Edge case closed: widening the window reopens the panel, because the
    summary is hidden at that width and it would otherwise be shut with no
    control to open it.
- **Rights-gated images.** The reading room now renders a photograph where one
  is approved and the spiral where none is. It cannot leak: the projection emits
  a media row only for a current approval, so an uncleared image has no row to
  render. Tested in all three states — a public-domain *source* alone releases
  nothing, a completed approval releases URL and attribution, a withhold keeps
  it off. 0 of 325 are approved today, so nothing shows; when RIGHTS-002 clears
  one it appears with no further work. Circular crop, because a bowl
  photographed from above is a circle.
- Dark mode was done in tranche 2, so that item was already closed.
- **The interface plan is complete.** Tranches 1–5, plus the projection hinge.
- What now limits this project is not the interface: 173 of 199 works are
  unclassified by scope (`SCHOL-006`), 736 of 1,322 bowls have nothing a reader
  can engage with, 312 claim differences await revalidation (`QA-002`), and
  0 of 325 images are cleared (`RIGHTS-002`). All research and rights work.

---

## 2026-09-05 — Claude — Ways in

**Claimed:** reading-room plan, tranche 4 (META-009, SCHOL-008 done)
**Corpus:** unchanged
**Tests:** 173 passed (170 before; +3)

- **Search** over the whole corpus: display names, every fact value, and the 45
  published texts. "lilith" returns 31 bowls.
- **Eight browse axes** over the content facets — people named, what they do,
  scripture quoted, hands and scribes, what is drawn, where they are, language,
  provenance — each with counts. Ritual purpose alone gives 35 distinct values
  across 43 bowls: "Divorce document" (4), "Semamit historiola" (4),
  "Expulsion of the child-killing demon from Mama, Abraham, and their household".
  This is the thing the corpus knew and could not show.
- Facets are computed **client-side from the projection's facts table** rather
  than through a query endpoint. That was deliberate: a published static export
  computes them the same way, so adding a server-side facet API would have
  broken the equivalence the whole projection layer exists to guarantee.
- **Publication pages** from a new `publications` projection table over
  migration 012's registry. Segal 2000 publishes 252 bowls, Montgomery 1913
  84, Shaked–Ford–Bhayro 2013 33, MRLA 8 19, Isbell 1975 17. 18 of 19 keys
  resolve; the unresolved one shows its status rather than implying a source.
  Selecting one filters the corpus to its bowls — the payoff for SCHOL-004.
- Equivalence re-verified after adding three tables: **13 tables, live API
  identical to the file export.**
- Remaining from the plan: tranche 5 polish — mobile filters below 900px in the
  curation views, and image thumbnails once rights clear.

---

## 2026-09-05 — Claude — The scholarship index

**Claimed:** reading-room plan, tranche 3 (SCHOL-006, SCHOL-007 opened)
**Corpus:** changed (migration 013 only; both new tables empty)
**Tests:** 170 passed (154 before; +16)

- `#/scholarship` — "The literature". **199 works**, separated from the 644
  museum, auction and dealer records that are sources but not scholarship.
- **How the field grew**, as two lines rather than one: what this index holds
  against Waller's JBA control list, by decade, drawn as SVG. The nineteenth
  century is where they should agree and roughly does (3 vs 2, 4 vs 4, 7 vs 8);
  ours runs higher after 2000 because it counts every language and genre.
- **107 contributors** grouped from free-text author strings. Two real defects
  surfaced while building it, both mine:
  - The SCHOL-002 ingest wrote `"Surname [and others; see citation]"`, which
    invented an author called `see citation]` with 32 works and keyed every
    `[and others` name on the surname **"others"** — **merging Geller with
    Gordon, and Schwab with Shaked.** Exactly the misattribution the plan
    warned about.
  - Stripping that placeholder then left bare surnames, which split "Levene"
    from "Dan Levene" and "Gordon" from "Gordon, Cyrus H".
  Both fixed. **Gordon now shows correctly at 8 works.** A bare surname folds
  into a named scholar only where exactly one scholar of that surname exists;
  with two Fords it stays separate, visibly under-attributed rather than
  silently attributed to the wrong person. There is a test for that.
- All fourteen remaining multi-spelling groups checked by eye: each is one
  person. Migration 013 adds an append-only alias ledger for overrides either
  way, and the UI marks a grouped entry "2 spellings" so it stays visible.
- **Ranked by publications, not citations**, and the page says why: no citation
  graph, and only 9% of sources carry a DOI, so a citation ranking would cover
  a tenth of the field and flatter whoever has the better metadata.
- Scope: 26 of 199 derived from the publication registry or source type, **173
  honestly unclassified**. `ibi ingest-source-scope` records the rest as reading
  judgments with a basis. That is SCHOL-006 and it is slow work.
- The console's CSP forbids inline styles, so the chart is SVG with geometry in
  attributes. Right answer anyway; the CSP was not weakened.
- Next: SCHOL-006, and the alias ledger if any grouping turns out wrong.

---

## 2026-09-05 — Claude — The reading room

**Claimed:** reading-room plan, tranche 2
**Corpus:** unchanged
**Tests:** 154 passed

- `#/reading` is now the default view. Explore, Enrichment and Concordance are
  unchanged and still reachable; they were good at their job, the problem was
  that they were the only job.
- **The projection had no facts.** Building this exposed it: `objects` carried
  only id, label, type and status, so the reader could not say where a bowl is,
  what language it is in, or who it protects. Added a gated `facts` table —
  4,473 rows — whose gate reuses the field model rather than inventing a second
  one: a claim is publishable as a fact when its field sits in a comparison
  group. That set was built to hold assertions comparable to one another, which
  is the same property that makes them facts rather than expression, and it
  already excludes `catalogue_description`, the museum prose that kept the
  research snapshots out of Git. Longest value in any comparison group is 215
  characters; the cap is 300.
- Also added `member_ids` to `identity_clusters`, without which texts and
  editions keyed by object could not be attached to the identity that owns them.
- **The spiral is drawn from the data.** Turns come from the object's recorded
  line count — "Eleven spiral lines" gives eleven — and a record with no line
  count gets a faint dashed estimate rather than a confident lie. For the 996
  records with no image it says something true instead of showing a grey box.
- Object pages read as catalogue entries: what it says, who it names, who wrote
  it *as reported*, what is drawn on it, size, condition, where it is published,
  where it is said to come from. The evidence chain is present but collapsed.
- The discipline survives into the reading view: CBS 2923 shows Montgomery's
  17.3 cm beside the Penn register's 17.7 cm, each with its source, rather than
  picking one.
- Dark mode built from the start, both in the reading room and in the base
  shell, which was `color-scheme: light` only. Added a Hebrew stack (SBL Hebrew
  → Ezra SIL → Frank Ruehl) for when original-script texts arrive.
- Verified: front page leads with the readable bowls, withheld texts show a
  citation and link, no media URL appears while approvals are 0, and the three
  curation tabs work unchanged.
- Next: tranche 3, the scholarship index.

---

## 2026-09-05 — Claude — The projection layer

**Claimed:** reading-room plan, the projection hinge
**Corpus:** unchanged
**Tests:** 154 passed (145 before; +9)

- Extracted `src/bowl_index/projection.py`: one gated view of the corpus that
  both the file exporter and the console now build from. The gates — which
  texts may be shown, which media URLs may be named, whether a link would leak
  a private capture — exist in exactly one place. A second implementation is a
  second chance to publish something withheld.
- `public_export.py` shrank to what it should be: writing files. The gating
  logic left it entirely.
- Added `/api/reader/manifest` and `/api/reader/<table>` to the console. They
  serve the projection **unchanged**, so a published static export and the
  local reading room are the same bytes through the same code path. That is the
  whole "local now, public later" bet, and it is now structural rather than a
  promise.
- **The equivalence is tested, not asserted.** `test_reader_projection.py`
  builds every table through the API path and diffs it against the file the
  exporter writes. Verified on the real corpus too: all eight tables identical,
  1,590 objects and 196 texts included.
- Gate behaviour confirmed live: 45 texts included, 151 withheld, **all 151
  carrying citation and locator**, 146 with a resolvable link, 0 of 325 media
  emitted, and no withheld content anywhere in the payload.
- `identity_clusters` now carries `display_name`, `completeness_score`,
  `content_completeness` and `reading_score`, so the reading room can rank and
  name records without reading a raw identity row.
- An unknown table 404s rather than falling through to something private.
- Next: the reading room itself, on top of this.

---

## 2026-09-05 — Claude — Reading room, tranche 1: foundations

**Claimed:** reading-room plan, tranche 1
**Corpus:** unchanged — derived fields only
**Tests:** 145 passed (134 before; +11)

- **Fixed the 12/10 bug.** `completeness_score` summed all 23 coverage flags
  while four UI sites rendered it as `n/10`; five rows displayed `12/10`, and
  the default sort ordered the corpus by it. It now counts the ten core facets
  only — max across the corpus is 9 — and `content_completeness` reports the
  thirteen content facets separately. Every consumer already assumed /10, so
  narrowing the definition fixed all four sites at once.
- **`display_name(label, identifiers)`.** Labels record how a record was found:
  "Penn Museum CBS 2923 / B2923 exhibition appearance", "Waller 2022: SD 34".
  The resolver strips those discovery prefixes and suffixes, falls back to a
  catalogue identifier when there is no usable label, and never returns empty.
  The raw label is untouched in the data — object pages will show it under
  "Recorded as".
- **`reading_score`.** What a reader can engage with, weighted so a published
  text outranks a filled-in measurement. Confirms the premise of the plan:
  **736 of 1,322 identities score zero**, and completeness ordering cannot tell
  them apart from the 48 readable ones.
- `CORE_ORDER` is now a module constant rather than a local tuple, so
  `next_action` and the score cannot drift apart.
- Found while verifying: the launcher serves **stale code** after a Python
  edit, because the server is a long-lived process and `↻ Refresh` reloads data
  from SQLite, not code. Documented in `bin/README.md`; restart with
  `bin/stop-console.command`.
- Not yet done: the `/api/reader/*` projection. That is the publish-safety
  hinge and gets its own tranche and its own equivalence test.

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
