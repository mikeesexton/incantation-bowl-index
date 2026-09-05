# Incantation Bowl Index: dataset maturity roadmap

> Living document generated from `research/roadmap/dataset_maturity.json` and the private corpus. Update task status or add newly discovered gaps in the JSON register, then run `ibi roadmap`.

Generated: `2026-09-05T21:30:56+00:00`

## Portfolio status

Current phase: **Source-rich research corpus with one completed reference cohort; active reconciliation and enrichment; not release-ready**

| Progress measure | Current |
|---|---:|
| Roadmap tasks | 12 done · 14 in progress · 22 queued · 0 blocked |
| Quantitative handoff gates passing | 2/5 |
| Required handoff tasks complete | 4/24 |

### What is solid

- Discovery is broad and reproducible within the classes it searched: 752 sources and 1,610 appearances support 1,585 candidate records, every record has evidence, the generated dedupe queue is empty, and two measured saturation sweeps passed the phase-one rule. Saturation is bounded by those twelve source classes; printed editions and the bibliographic databases were not among them.
- The Montgomery/Penn reference cohort is now internally complete at its stated level: 40/40 printed register entries checked, 35/35 available English translations checked against scans, five source absences documented, and 40/40 current Penn number concordances individually verified.
- Research corrections are reversible and inspectable: conflict decisions, text revisions, citation repairs, media-rights reviews, museum concordance reviews, and source-reported object relationships retain evidence-bound append-only history. The narrow public export fails closed on texts and media.
- The evidence discipline is genuinely unusual: identifiers record who reported a designation, original source strings are retained beside structured values, the 4 September review published its own permissive-rule defect, and the public export fails closed.
- The public boundary is now positive rather than merely defensive: 45 texts are published on a stated rights basis with their editorial state declared, and every one of the 151 withheld texts still names its edition, exact locator and link so a reader can consult it.

### What prevents release readiness

- The index was built from findable online records - 567 of 753 sources are museum records - while the field's primary evidence is printed editions. Seventeen foundational works, including Isbell 1975, Naveh and Shaked, Pognon 1898, Yamauchi 1967 and all of Gordon 1934-1984, have no source record; publications exist only as identifier prefixes.
- Identity and claim quality is not yet measured corpus-wide: 284 older field-difference decisions need evidence-level revalidation, findspot claims are not yet consistently graded by evidence basis, and a reproducible stratified identity audit has not begun.
- Text and edition coverage remains sparse outside Montgomery: 312/791 probable or confirmed identities have a publication-scheme reference, still only a proxy for a checked edition locator; just one identity has a recorded transcription or transliteration.
- Release rights are unreviewed: all 325 media rows have inventory holds, but zero have completed rights decisions and zero are approved for reuse.
- The National Library of Israel, Schøyen, broader Penn, and remaining British Museum/Segal concordances are incomplete; continuous operations, encrypted off-device backup, and a 14-day shadow run are not set up.
- The field model stops at the physical and bibliographic facets. People, ritual, intertexts, visual and scholarship claims exist in the corpus but sit outside coverage and conflict comparison, so the 134 Waller biblical quotations - the most analytically valuable material after Montgomery - are untracked.

## Current scope snapshot

| Measure | Current |
|---|---:|
| Candidate source records | 1588 |
| Working physical identity hypotheses (all statuses) | 1320 |
| Source appearances | 1616 |
| Sources | 753 |
| Pending dedupe decisions | 0 |
| Identities triggering raw claim-difference flags | 201 |
| Triaged claim-field differences | 53/337 |
| Compatible differences | 38 |
| Review required (missing or no longer valid) | 284 |
| Existing reviews requiring revalidation | 284 |
| Substantive conflict instances | 15 across 13 identities |
| All identities with a publication reference | 391/1320 (29.6%) |
| Probable/confirmed identities with a publication reference | 312/794 (39.3%) |
| Identities with a translation | 48 |
| Scan-checked normalized reading texts | 0 |
| Montgomery/Penn concordances with dated current-evidence review | 40 |
| Source-reported object relationships / unresolved scope | 5 / 4 |
| Identities with a transcription/transliteration | 1 |
| Media records with a non-unknown rights status | 37/325 (11.4%) |
| Media with a current ledger entry | 325/325 |
| Media with completed rights decisions / approved for reuse | 0 / 0 |
| Blocked leads | 28 |
| Open or active leads | 7 |
| Qualifying discovery-saturation sweeps | 2 |

Coverage means a field or reference is present, not independently verified. Publication coverage currently uses identifier schemes as a proxy. A non-unknown rights label is not a reviewed public-reuse decision. Discovery saturation applies only to the logged searches and does not estimate global completeness.

### Identity-level field coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 909 | 68.9% |
| Provenance | 325 | 24.6% |
| Dating | 482 | 36.5% |
| Dimensions | 378 | 28.6% |
| Material | 408 | 30.9% |
| Language | 459 | 34.8% |
| Script | 91 | 6.9% |
| Text Edition | 1 | 0.1% |
| Translation | 48 | 3.6% |
| Image | 324 | 24.5% |

## Maturity scale

Maturity is tracked by workstream, not collapsed into a misleading single score.

| Level | Meaning |
|---:|---|
| 0 | **Unscoped:** The source universe, rules, or required fields are not yet defined. |
| 1 | **Discovered:** Candidate records and gaps are enumerated with retrievable source evidence. |
| 2 | **Reconciled:** Identity and concordance decisions are reviewed, reversible, and evidenced. |
| 3 | **Enriched:** Priority metadata and publication references are source-attributed and conflicts are triaged. |
| 4 | **Release-ready:** Rights, quality, and public/private boundaries have been reviewed for a reproducible release. |
| 5 | **Monitored:** Validated continuous collectors detect changes and open leads under documented operating controls. |

## Workstream maturity

| ID | Workstream | Current | Active target | Steward |
|---|---|---:|---:|---|
| DISC | Discovery and citation snowballing | L2 | L5 | Research now; Mac mini monitoring later |
| CONC | Identity and museum concordances | L2 | L3 | Research judgment |
| TEXT | Texts, translations, and publication references | L1 | L3 | Research judgment |
| SCHOL | Scholarly bibliography and published-corpus enumeration | L1 | L3 | Research |
| META | Physical, chronological, linguistic, and provenance enrichment | L1 | L3 | Mixed |
| RIGHTS | Images and rights | L1 | L4 | Human rights review |
| OPS | Mac mini continuous operations | L0 | L5 | Mac mini after 2026-09-22 |
| QA | Evidence quality and regression controls | L2 | L3 | Research and engineering |

## Current priority order

1. SCHOL-001: acquire Waller's 2025 publication list. It is a library request rather than weeks of work, it is the only external control on completeness the field offers, and it has been the standing first priority since July. How complete this index is remains guesswork until it arrives.
2. QA-008: reconcile the claim vocabulary with the comparison model before revalidating more of the conflict queue. Widening the model changes how many instances exist; doing it after means revalidating part of the queue twice.
3. SCHOL-002: ingest the staged bibliography seed and verify its citations. Twenty-one records and ten leads are prepared and deliberately not applied.
4. RIGHTS-002: with texts now gated by a working ledger, media are the remaining hard block at 0/325. The same evidence-bound pattern applies; start with the 288 Penn images, which have a single rights holder and a single policy to establish.
5. CONC-005 / QA-002: continue the 284 earlier evidence-level revalidation cases in coherent source batches; retain each reported source value. The nine new Penn differences and a twenty-case same-source facet batch now have current decisions.
6. META-002 / META-003: continue the B2963 object-specific dating investigation and inspect original scripts for Montgomery 9 and 31 before assigning language source errors. The relationship and measurement anomaly reviews are complete at the available evidence level.
7. META-005: apply Waller's evidence-basis distinction to the location corpus, starting with claims labelled Excavated/Findspot and the Susa controlled-excavation group. Preserve museum and market claims as reports rather than silently upgrading them to archaeological facts.
8. TEXT-006 / TEXT-003: obtain independent review of all 35 checked English reading texts, particularly magical formulas and restorations, then develop a checked original-script transcription/transliteration pilot. The first English scan-review pass is complete.
9. CONC-002: extend beyond the completed forty-entry reference cohort to reconcile the remaining Penn holdings and historical inventory. Check precise identifiers and publication references; do not generalize the 40/40 result to the broader collection.
10. QA-003: select and audit a reproducible stratified sample before assigning an overall accuracy percentage. The forty-entry Montgomery source audit is useful but not representative of the entire corpus.
11. RIGHTS-002: investigate actual reuse evidence for the 325 media holds. Export safeguards are implemented; rights clearance is still 0/325. Do not substitute old copyright labels for assessment.
12. TEXT-001 / QA-004: align edition-reference and field-assessment metrics with cited evidence; then extend the checked institutional cohorts.
13. DISC-002: pursue precise source gaps, including IBI-LEAD-MONT42 and authorized Segal catalogue access; defer another undirected discovery expansion.
14. OPS: document restore and collector controls for the Mac mini. A local database backup was restore-checked; encryption, off-device backup and shadow operation remain outstanding.

## Task register

### DISC — Discovery and citation snowballing

Maintain maximum-recall discovery across scholarship, catalogues, museums, auctions, dealers, excavations, and cited private collections without treating completeness as absolute.

- [x] **DISC-001 — Complete phase-one source-class discovery** · Done · Research
  - Done when: All planned source classes are searched or explicitly blocked and two independent broad sweeps produce under 1% net-new identities without a new source class.
  - Evidence/status: Twelve source-class targets assessed; two qualifying saturation sweeps; campaign report generated.
- [ ] **DISC-002 — Continue bidirectional citation snowballing during enrichment** · In progress · Mixed
  - Done when: Every newly used source has backward and forward citations, object identifiers, named owners, and sale references checked; new leads are logged rather than held in notes.
  - Evidence/status: Ongoing rule; discovery can reveal new objects even after phase-one saturation.
- [ ] **DISC-003 — Classify recurring discovery sources for automation** · Queued · Research
  - Done when: Every monitored source has a documented endpoint, cadence, access/robots status, expected identifier, and automation tier.

### CONC — Identity and museum concordances

Reconcile physical bowls across museum records, publications, auctions, dealers, and collection histories while preserving uncertain matches for review.

- [ ] **CONC-001 — Finish British Museum and Segal concordances** · In progress · Research
  - Done when: All 142 Segal text numbers and all related British Museum objects are mapped, or each unresolved mapping has a precise blocker.
  - Evidence/status: Twenty-four checked item-page mappings remain. Audited importer repair corrected 137 Segal claim locators, including BM 117882 to 119ES, preserving original claims in immutable history. The uncertain language assessment and 142/159 discrepancy still need authorized full-catalogue inspection; no identity links changed.
- [ ] **CONC-002 — Finish Penn Museum concordances** · In progress · Research
  - Done when: Every identifiable Montgomery/Penn publication number is mapped to a current Penn object or a documented lost/unresolved state.
  - Evidence/status: All forty main Montgomery/Penn concordances now have dated, evidence-bound current museum-page reviews (2026-09-05): Object Number and explicit PBS III number agree in every case. Register/heading discrepancies for 14, 19 and 40 remain preserved; B2972 explicitly corrects text 40 to B2971. Nine exposed field differences were individually reviewed and five directed Penn relationship assertions were recorded without merging identities. Broader Penn holdings and the historical 150-plus inventory still need reconciliation.
- [ ] **CONC-003 — Finish National Library of Israel concordances** · Queued · Research
  - Done when: The 205 harvested records, 216-object donation statement, exhibition names, and seven Klagsbald bowls are reconciled without inventing missing item identities.
- [ ] **CONC-004 — Finish Schøyen publication and collection concordances** · Queued · Research
  - Done when: Individually identifiable MS records are reconciled with publication numbers and aggregate collection claims; unenumerated remainder stays explicitly aggregate.
- [ ] **CONC-005 — Triage every conflicting identity-level core claim** · In progress · Research
  - Done when: Every currently flagged identity conflict is classified as genuine scholarly disagreement, temporal change, normalization artifact, source error, or data error; decisions retain evidence.
  - Evidence/status: 53/337 field instances have current decisions; 284 older decisions require evidence-level revalidation. The nine newly exposed Penn differences (7 dimensions, 2 languages) received unresolved decisions, followed by a twenty-case same-source facet batch covering explicit equivalence and complementary dating, location and provenance fields. No values were averaged, normalized away or deleted. Fifteen current substantive instances across thirteen identities remain visible.
- [ ] **CONC-006 — Resolve the five substantive claim discrepancies** · Queued · Research
  - Done when: Primary-source review resolves or explicitly leaves adjudicated disagreement for HS 3003 location, CBS 16020 location, Apollo lot 272 dating and language, and VA 3383 script.
  - Evidence/status: Detailed source values and rationales are recorded in the claim-conflict triage report.
- [x] **CONC-007 — Check all forty main Montgomery/Penn number concordances** · Done · Research
  - Done when: Each main entry has an individually inspected Penn Object Number and explicit publication number, or a documented discrepancy, with dated evidence and reversible review history.
  - Evidence/status: 40/40 confirmed from visible museum Details tables. Migration 009 stores immutable, evidence-bound observations; changed local identity evidence invalidates the current review. Zero identity edits. Six follow-up leads preserved unrelated anomalies; three are resolved at the available evidence level and three remain active.
- [x] **CONC-008 — Model source-reported relationships separately from physical identity** · Done · Research
  - Done when: Ambiguous duplicate, same-as and part-of notes can be stored as directed, source-attributed, evidence-bound assertions without causing an object merge.
  - Evidence/status: Migration 010 adds an append-only relationship ledger and checked replay-safe importer. Five Penn assertions connect B16007/B16081 and B16086/B16062/B6354: one explicit physical-part scope is accepted, four scopes remain unresolved, and zero identity changes were made. Three associated leads were closed with documented outcomes.

### TEXT — Texts, translations, and publication references

Record where editions, transliterations, translations, incipits, and commentary exist, independently of whether copyrighted content can be stored or published.

- [ ] **TEXT-001 — Create publication-reference coverage for known texts** · In progress · Research
  - Done when: At least 80% of probable/confirmed identities have either an edition reference or an explicit no-known-edition status, each with a source.
  - Evidence/status: 312/791 probable/confirmed identities have publication-scheme identifiers (39.4%). This proxy counts designations, not editions: the publications being designated have no records of their own (see SCHOL-004), so raising the number does not yet raise edition coverage. Re-specify the metric against resolved publication records and sourced no-known-edition assessments before treating it as a release gate.
- [x] **TEXT-002 — Proofread Montgomery's 35 extracted translations** · Done · Research
  - Done when: Every translation is checked line by line against the scan, corrections are logged, and public_ok is decided independently of public-domain status.
  - Evidence/status: 35/35 available translations visually checked against archived scans as normalized English reading texts, in batches of 11 and 24. Exact original rows, corrected text hashes, source-PDF hash, page locators and correction notes retained. Zero OCR drafts remain in this cohort. All 35 remain public_ok=false; independent specialist review and original-language verification are separate work. Completion manifest: research/reviews/montgomery_reading_texts_completion_2026-09-05.json.
- [ ] **TEXT-003 — Capture reliable Montgomery transliterations** · Queued · Research
  - Done when: Each of Montgomery's 40 bowl texts has a checked transliteration or a precise reason it cannot yet be captured.
- [ ] **TEXT-004 — Index restricted editions without copying protected text** · Queued · Research
  - Done when: Known copyrighted editions retain bibliographic references, item ranges, language/script, access status, and rights metadata even when content is absent.
- [x] **TEXT-005 — Account for every main Montgomery entry and source exception** · Done · Research
  - Done when: All forty main entries have explicit publication, translation and register status; appendix material is separately scoped.
  - Evidence/status: 40-row cohort report: 35 checked reading texts, zero OCR drafts, and 5 source-documented cases with no separate translation (18, 21, 23, 27, 33). Appendix 42 remains a separate uncertain possible bowl candidate; Appendix 41 is explicitly a skull.
- [ ] **TEXT-006 — Independently review the Montgomery reading-text cohort** · Queued · Research
  - Done when: A separate reviewer checks all 35 edited English texts against the scans, explicitly reviews names, magical formulas, gaps and restorations, and records disagreements or corrections without overwriting earlier reviews.
  - Evidence/status: First scan-review pass complete for 35/35. No independent specialist certification or original-language verification is claimed; publication approval remains separate.
- [ ] **TEXT-007 — Grade object evidence A-D alongside identity status** · Queued · Research
  - Done when: Every probable or confirmed identity carries an evidence grade on the scoping review's A-D scale, recorded per assertion and separately from record_status.
  - Evidence/status: record_status measures identity confidence; the A-D scale measures evidence quality. They are different axes and a confirmed identity can rest on a dealer photograph. Scale in docs/project-rules.md, from the review section 1.4.
- [x] **TEXT-008 — Publish text on a recorded basis and point at the rest** · Done · Engineering
  - Done when: Text is public only through an evidence-bound publication decision that states a rights basis and the editorial state of the stored row, and every withheld text keeps its citation, locator, link and access status in the public dataset.
  - Evidence/status: Migration 011 adds an append-only text publication ledger; approvals are bound to a content fingerprint so a later proofreading revision revokes them automatically, verified by test. 45 texts approved: Montgomery's 35 scan-checked English reading texts on public_domain_expired, and 10 index summaries on own_work restoring their prior public state under the new rule. 151 withheld rows all carry citation and locator, 146 also a resolvable link; the 5 without one fail closed because their source URL matches a private capture. A new editions table names 476 publication locations across 472 objects. Media remain 0/325 approved.

### SCHOL — Scholarly bibliography and published-corpus enumeration

Record the editions that actually publish bowls, as first-class sources with their own objects, access status and evidence grade. The index was built from findable online records; the field's primary evidence is printed editions.

- [ ] **SCHOL-001 — Acquire Waller's 2025 publication list as a control list** · Queued · Research owner
  - Done when: Waller, 'The Aramaic Incantation Bowls: The State of the Art' (Marcus and Mokhtarian 2025, pp. 3-48) is held in full and its list of JBA bowl publications 1853-2024 is enumerated as source records with their object counts.
  - Evidence/status: Standing first acquisition priority in the July 2026 scoping review's Phase 1 and in its progress checkpoint. Only printed pp. 10-13 are currently archived, as a user-supplied excerpt. This is the nearest external control the field offers on what 'published' means, and therefore the only outside check on this index's discovery saturation. Lead IBI-LEAD-WALLER-2025-PUBLICATION-LIST.
- [ ] **SCHOL-002 — Seed the missing foundational bibliography** · In progress · Research
  - Done when: Every work named as foundational by the scoping review has a source record with a verified citation and access status, or an explicit reason it cannot be obtained.
  - Evidence/status: Seventeen named works have no author or title match in `sources`, including Ellis 1853, Pognon 1898, Myhrman 1909, Isbell 1975, Yamauchi 1967, Naveh and Shaked 1985/87 and 1993, Muller-Kessler 2005, and all of Gordon 1934-1984. Twenty-one seed records are staged in research/seeds/scholarly_bibliography_2026-09-05.jsonl with citations transcribed from the review and explicitly unverified; ten leads in research/leads/scholarly_bibliography_gaps_2026-09-05.jsonl. Not yet ingested.
- [ ] **SCHOL-003 — Run the bibliographic database sweep the review specifies** · Queued · Research
  - Done when: RAMBI, ATLA, Index Islamicus, L'Annee philologique, ProQuest Dissertations, WorldCat, Crossref and OpenAlex are each searched with saved query strings, dates and result counts, and the field's journal archives are swept by object siglum and opening formula as well as by keyword.
  - Evidence/status: The review's own 14-row search log is a targeted verification pass, not a sweep, and says so. The index's phase-one saturation covers twelve source classes, none of which is the bibliographic databases. Both gaps have the same shape.
- [ ] **SCHOL-004 — Make publications first-class records, not identifier prefixes** · Queued · Engineering
  - Done when: Every publication-derived identifier resolves to a source record for the publication being designated, kept separate from the source that reported the designation; a regression test fails when a publication key has no such record.
  - Evidence/status: `identifiers.source_id` correctly records who reported a designation. There is no record of the publication designated: 17 objects carry `Isbell 1975::NN`, 19 carry `MRLA 8::NN`, 2 carry `TMH 7::NN`, 8 carry `Naveh-Shaked 1985`/`1993`, and none of those four publications has a row in `sources`. Until this exists, publication_reference_pct measures designations, not editions.

### META — Physical, chronological, linguistic, and provenance enrichment

Add source-attributed findspots, current locations, collection and acquisition histories, dates, dimensions, material, language, and script without flattening disagreement.

- [ ] **META-001 — Enrich provenance and collection history** · In progress · Research
  - Done when: Every probable/confirmed identity is assessed for findspot, excavation context, ownership history, and current location; absent evidence is recorded as unknown rather than inferred.
- [ ] **META-002 — Enrich dating and physical description** · In progress · Mixed
  - Done when: Every probable/confirmed identity is assessed for dating, dimensions, material, and condition with field-level citations.
  - Evidence/status: All forty Montgomery register rows checked against printed pp. 321–326: 40 structured height/diameter claims, 40 explicitly historical condition descriptions and 40 literal register identifiers added. Seven dated Penn height/outside-diameter assertions all differ from the register and now have explicit unresolved reviews; no averaging or convention equivalence was inferred. Montgomery's cohort-level late pre-Islamic dating argument is stored separately as context for B2963 and does not replace Penn's object-level ca. 200 BCE report.
- [ ] **META-003 — Enrich language and script classification** · In progress · Research
  - Done when: Every text-bearing probable/confirmed identity has a cited language and script classification or an explicit uncertain/unreadable status.
  - Evidence/status: Current Penn fields Hebrew Language for B9010 (Montgomery 9) and B9008 (31) are retained alongside the edition-based JBA and Syriac attributions. Both differences now have evidence-bound unresolved decisions and active original-script follow-ups; no silent normalization or source-error assignment.
- [ ] **META-004 — Prioritize legally excavated and institutionally held objects** · In progress · Research
  - Done when: High-confidence excavation and museum groups receive complete core-field review before lower-evidence market aggregates.
  - Evidence/status: Forty Montgomery register rows, all thirty-five available English translations, and forty Penn number concordances have direct source review. Nine new field differences are explicitly adjudicated as unresolved; five Penn relationship assertions are structured separately from identity. Waller's excavation-site review now supplies an explicit distinction between documented excavation and unverified reported provenance. Original-script work and independent second text review remain.
- [ ] **META-005 — Grade findspot claims by evidence basis** · In progress · Research
  - Done when: Every probable or confirmed identity with a findspot claim records whether the place derives from documented controlled excavation, a museum or accessions register, a dealer or market report, later scholarly inference, or unverified evidence; original place claims and uncertainty remain source-attributed.
  - Evidence/status: Waller 2025, printed pp. 10–13, distinguishes documented excavation sites from unverified register and dealer provenances. BM 91711 has a separate source-attributed assessment marking its plausible Arban attribution unverified. Primary-source review of Schwab 1891 pp. 590–593 now enumerates three Dieulafoy mission Susiana bowls, N–P, with separate records, dimensions, and excavation-evidence assessments corroborated by Montgomery 1913 p. 19. Current museum accessions and precise contexts remain open.
- [ ] **META-006 — Extend the field model to the content facets** · Queued · Mixed
  - Done when: People, Ritual, Intertexts, Visual and Scholarship are modelled field groups with coverage reporting and conflict comparison, not stray claim names.
  - Evidence/status: The review's Phase 2 ledger specifies ten field groups; CORE_COVERAGE has seven, all physical or bibliographic. The claims already exist outside the model: 134 biblical_quotations from Waller 2022, 42 client, 27 text_purpose, 25 iconography, 16 handwriting_attribution, 10 formula_genre. None is counted, compared or queryable as a group.
- [ ] **META-007 — Separate the roles behind a named person** · Queued · Research
  - Done when: Every person claim records which role the source assigns - author, textual voice, copyist, producer, commissioner, client, beneficiary - with its uncertainty, and contested attributions link to the scholarship that contests them.
  - Evidence/status: Eleven objects carry handwriting_attribution claims whose values are women's names, from Kedar 2019's contested female-authorship argument. Saar 2024 and Manekin-Bamberger 2025 respond by separating the roles. The field name asserts more than the source does; keep the claim, add the role and the dispute link.
- [ ] **META-008 — Bring Mandaic, Syriac and Pahlavi to parity** · Queued · Research
  - Done when: Each language group has enumerated corpora from its primary editions, and the 819 records with no language claim are assessed or explicitly marked unreadable or unknown.
  - Evidence/status: Measured against the EJCM working counts the review quotes: JBA/Aramaic 379 of about 500, Mandaic 77 of about 125, Syriac 69 against about 50, Pahlavi 2, pseudo-script 35, and 819 records - 52% - with no language claim at all. Mandaic and Pahlavi have an obvious cause: Pognon 1898 and Yamauchi 1967 are not in the corpus. See SCHOL-002.

### RIGHTS — Images and rights

Build a rights ledger before copying images into the corpus or exposing any media publicly; distinguish private evidentiary capture from public reuse permission.

- [x] **RIGHTS-001 — Define the image-rights ledger and decision vocabulary** · Done · Research
  - Done when: Every media row can record creator/owner, source URL, rights statement, license, jurisdiction/date notes, private-capture status, public-reuse decision, and reviewer.
  - Evidence/status: Implemented immutable media-rights ledger, exact-evidence review batches and stale/revoked decision handling. All 325 media have explicit initial needs_review holds, not completed rights assessments. Workflow in docs/evidence_review_and_release.md.
- [ ] **RIGHTS-002 — Review all existing media records** · In progress · Human review
  - Done when: One hundred percent of media records have a reviewed rights disposition; unknown remains permissible only with an explicit follow-up task.
  - Evidence/status: 325/325 media inventoried with explicit follow-ups; 0/325 completed rights assessments and 0 approved for public reuse. Existing non-unknown copyright labels do not count as decisions.
- [x] **RIGHTS-003 — Separate private thumbnails from public media exports** · Done · Engineering
  - Done when: A separate public-export path excludes unapproved media URLs/bytes and private source payloads, with regression tests. Any later public dashboard must consume that reviewed projection and receive its own release check.
  - Evidence/status: Added separate allowlist-based export-public reference scaffold: excludes captures, private payloads, claim content, notes and review histories; text public_ok and current per-media approval are separate gates. Tests cover stale approval, revocation, duplicate URLs, known private references and residual destination files. Live validation withheld all 325 media. No public dashboard is deployed.
- [ ] **RIGHTS-004 — Restore links for sources whose URL matches a private capture** · Queued · Engineering
  - Done when: A source's public page URL can be published as an access pointer without being suppressed merely because the page was also archived privately, while capture storage paths and unapproved media URLs stay forbidden.
  - Evidence/status: The export guard forbids any string matching a capture URL. That is correct for media and archive paths but suppresses 5 legitimate bibliographic links, since a public page URL reveals nothing about the archive. Narrow the guard to storage paths and media URLs.

### OPS — Mac mini continuous operations

Prepare a private, recoverable, observable 24/7 research worker that detects changes and opens evidence-backed leads without autonomously making sensitive scholarly or rights decisions.

- [ ] **OPS-001 — Provision the Mac mini research runtime** · Queued · Engineering
  - Done when: Repository, isolated Python runtime, secrets storage, launch-on-boot service account, logs, health checks, and least-privilege filesystem layout are documented and reproducible.
- [ ] **OPS-002 — Configure encrypted local and off-device backups** · Queued · Engineering
  - Done when: Database, capture manifests, and private archive are backed up on schedule and a sampled restore has been completed successfully.
- [ ] **OPS-003 — Implement safe collector scheduling and change detection** · Queued · Engineering
  - Done when: Approved collectors have bounded schedules, rate limits, idempotency, hashes/diffs, retry limits, failure alerts, and per-source disable switches.
- [ ] **OPS-004 — Complete a 14-day shadow run** · Queued · Mac mini agent
  - Done when: Continuous collectors run for 14 days with no silent data loss, uncontrolled duplicates, rights leakage, or unresolved operational failures; alerts are reviewed for usefulness.
- [ ] **OPS-005 — Adopt collect-and-flag autonomy boundaries** · Queued · Research owner
  - Done when: Written policy and tests ensure agents may collect appearances and open leads but may not auto-merge uncertain objects, adjudicate claims/authenticity, clear rights, or publish.

### QA — Evidence quality and regression controls

Measure current evidence validity, sampled scholarly accuracy, and release safety separately from record counts and metadata presence.

- [x] **QA-001 — Bind conflict review validity to current evidence and conservative rules** · Done · Engineering
  - Done when: Changed claims, sources, cluster membership, and unsupported compatibility rules reopen review without deleting historical decisions; orphan reviews cannot satisfy roadmap gates.
  - Evidence/status: Implemented in conflict_review.py, identity.py, roadmap.py and current conflict reports. Regression tests cover changed evidence and unsafe equivalence; 313 reviews reopen in the existing corpus. See data/reports/quality_review_2026-09-04.md.
- [ ] **QA-002 — Revalidate the historical rule-assisted conflict triage** · In progress · Research
  - Done when: All 313 reopened instances have source-level decisions on their exact current evidence, with append-only review history and explicit uncertainty preserved.
  - Evidence/status: 304 earlier field instances still need source-level revalidation. The current Penn review separately exposes 9 new differences, yielding 313 total pending. These queues are distinguished; dated museum concordance confirmation does not adjudicate their metadata. The denominator is bounded by the seven CORE_COVERAGE groups and is an undercount, not a measured total; do QA-008 first so this queue is not revalidated twice.
- [ ] **QA-003 — Audit a stratified sample of identity and extraction decisions** · Queued · Research
  - Done when: Publish reproducible sample selection across institutions, market records, status classes and merge methods; check primary evidence and report denominators, error categories and uncertainty.
  - Evidence/status: Zero generated pending dedupe candidates is queue completion, not measured identity accuracy. Current review examined architecture, integrity, archive hashes, aggregate metrics and selected rule evidence, not all objects.
- [ ] **QA-004 — Separate presence, assessment, verification and source coverage metrics** · In progress · Mixed
  - Done when: Track field assessment and verification independently of presence; distinguish excavation provenance from production region and ownership; reconcile item-level denominators for major sources; align publication and rights gates with reviewed evidence.
  - Evidence/status: Roadmap now separates 325 media ledger holds from 0 completed rights assessments and 0 public approvals, and counts 35 current scan-checked reading texts separately from text presence. Main Montgomery denominator is explicit: 40 entries, 35 translations and 5 documented absences in this edition. General field-assessment and edition-reference metrics still need work. Forty current-evidence museum concordance reviews are now counted separately from existing identity links; observations retain review dates and do not certify unchanged live websites or unrelated metadata.
- [x] **QA-005 — Implement evidence-bound subset reviews and append-only history** · Done · Engineering
  - Done when: Review batches reject changed evidence, duplicate or absent fields and count-only overrides; writes are atomic and replay-idempotent; all original and subsequent decisions remain in immutable history.
  - Evidence/status: Migration 005 preserved all 328 starting decisions. The nine-instance batch and one later refreshed decision yield 338 immutable snapshots; all original and subsequent judgments remain inspectable.
- [x] **QA-006 — Repair range-generated citation pointers with retained originals** · Done · Engineering
  - Done when: Importer assigns each range item its own locator and exact-evidence repairs retain before/after snapshots; regression tests cover exceptions, replay, stale input and rollback.
  - Evidence/status: 137/137 affected Segal claims repaired; zero remaining source/appearance locator mismatches in that scoped audit. Scholarly values, uncertainty and identity links unchanged. Migration 008 and research/reviews/segal_locator_corrections_2026-09-04.json.
- [x] **QA-007 — Preserve originals and evidence for text proofreading** · Done · Engineering
  - Done when: Scan-bound revision batches preserve original and corrected texts, reject stale evidence, and prevent OCR reimport from overwriting checked work.
  - Evidence/status: Migration 006, thirty-five current scan-checked reading texts and passing regression tests; exact originals retained and private text histories redacted from research exports. Completion batch replays with zero changes.
- [ ] **QA-008 — Reconcile the claim vocabulary with the comparison model** · Queued · Engineering
  - Done when: Every claim field is either in a CORE_COVERAGE group or explicitly excluded with a recorded reason; a test fails when an unclassified field appears; and the conflict counts are reported against that full denominator.
  - Evidence/status: claims.field is free text and holds about 100 values, many synonyms - provenance / provenance_summary / provenance_quality, findspot / findspot_or_origin / findspot_evidence_level, client / clients / client_or_beneficiary. Only seven hard-coded groups are compared, so 205 catalogue_language_codes claims are invisible to both language coverage and conflict detection even where an edition-based inscription_language claim on the same object disagrees. The 337/284 queue is therefore an undercount by construction. dimensions_source_text is correctly excluded as a retained original string; note it records circumference, not diameter.

## Mac mini handoff gate

Target availability: **2026-09-22**. This is an operational eligibility date, not an automatic permission to publish or to make scholarly judgments.

Overall gate: **NOT READY**

### Quantitative conditions

- [x] No unreviewed generated dedupe candidates — current `0`; target `<= 0`.
- [ ] Every generated claim-difference flag has a recorded triage — current `284`; target `<= 0`.
- [x] Discovery saturation demonstrated by independent sweeps — current `2`; target `>= 2`.
- [ ] Publication-reference coverage reaches the operational threshold. Currently a proxy over identifier schemes; SCHOL-004 must land before this gate means edition coverage — current `39.3%`; target `>= 80.0%`.
- [ ] Every media row has a current completed rights decision; initial needs_review holds do not qualify — current `0.0%`; target `>= 100.0%`.

### Required setup tasks

- [ ] CONC-001 — Finish British Museum and Segal concordances
- [ ] CONC-002 — Finish Penn Museum concordances
- [ ] CONC-003 — Finish National Library of Israel concordances
- [ ] CONC-004 — Finish Schøyen publication and collection concordances
- [ ] CONC-005 — Triage every conflicting identity-level core claim
- [ ] CONC-006 — Resolve the five substantive claim discrepancies
- [ ] TEXT-001 — Create publication-reference coverage for known texts
- [x] RIGHTS-001 — Define the image-rights ledger and decision vocabulary
- [ ] RIGHTS-002 — Review all existing media records
- [x] RIGHTS-003 — Separate private thumbnails from public media exports
- [ ] OPS-001 — Provision the Mac mini research runtime
- [ ] OPS-002 — Configure encrypted local and off-device backups
- [ ] OPS-003 — Implement safe collector scheduling and change detection
- [ ] OPS-004 — Complete a 14-day shadow run
- [ ] OPS-005 — Adopt collect-and-flag autonomy boundaries
- [x] QA-001 — Bind conflict review validity to current evidence and conservative rules
- [ ] QA-002 — Revalidate the historical rule-assisted conflict triage
- [ ] QA-003 — Audit a stratified sample of identity and extraction decisions
- [ ] QA-004 — Separate presence, assessment, verification and source coverage metrics
- [x] QA-005 — Implement evidence-bound subset reviews and append-only history
- [ ] SCHOL-002 — Seed the missing foundational bibliography
- [ ] SCHOL-004 — Make publications first-class records, not identifier prefixes
- [ ] QA-008 — Reconcile the claim vocabulary with the comparison model
- [ ] RIGHTS-004 — Restore links for sources whose URL matches a private capture

### What crosses the threshold

Once the gate is ready, deterministic recurring work moves to the Mac mini: polling approved museum and auction endpoints, bibliographic alerts, sitemap/RSS checks, content hashing, change detection, backups, validation, and opening review leads.

The agents may **collect and flag**. They may not autonomously merge uncertain identities, resolve conflicting scholarly claims, declare authenticity, clear copyright, bypass access controls, or publish private records. Those remain review tasks.

A source-specific collector becomes eligible only when it has a stable lawful endpoint, documented rate limits, an idempotent parser with fixtures, provenance-preserving writes, a change detector, bounded retries, and an alert path. It must complete a 14-day shadow run with no silent data loss or uncontrolled duplicate creation.

## How to maintain this document

1. Add every newly discovered gap as a task under the relevant workstream in `research/roadmap/dataset_maturity.json`.
2. Give it a stable ID, owner class, status, and verifiable `done_when` condition.
3. Mark a task done only when its evidence is linked. Mark inaccessible work blocked rather than deleting it.
4. After corpus changes, run `ibi roadmap`, `ibi report-enrichment`, and `ibi export`.
5. Review the handoff gate before enabling or expanding any continuous collector.

## Change log

- **2026-09-04:** Created the living maturity framework from the six priority research streams and added an explicit Mac mini handoff gate.
- **2026-09-04:** Recorded the Montgomery 1913 translation and Penn concordance enrichment as the first text-workstream evidence.
- **2026-09-04:** Triaged all 328 apparent claim differences: 323 compatible variants/facets and five substantive discrepancies across four identities.
- **2026-09-04:** Independent code/corpus quality review found permissive compatibility rules and stale-review counting. Preserved all 328 decisions, reopened 313 for source-level revalidation, added QA priorities, qualified coverage metrics, and withdrew unsupported public-safe export wording. No scholarly claims or identities changed.
- **2026-09-04:** Added atomic evidence-bound review batches and immutable decision history. Revalidated nine BM field instances using stored evidence (eight compatible; one unresolved), reducing the pending revalidation queue to 304. Logged BM 117882 Segal 117ES/119ES mismatch as a blocked lead; no identity or original claim changed.
- **2026-09-04:** Substantial source and infrastructure pass: checked eleven Montgomery reading texts and forty register rows; added 125 source claims and separately scoped possible-bowl Appendix 42 candidate; repaired 137 Segal citation pointers with immutable originals; added media-rights ledger and narrow fail-closed export. 325 initial rights holds are not completed assessments. Roadmap gates now use actual rights decisions.
- **2026-09-05:** Completed the remaining 24 Montgomery English scan reviews: all 35 available translations now have retained originals and exact-source audit records; all 40 main entries accounted for with 5 documented source absences. Restored omitted gaps and corrected OCR names and magical formulas. TEXT-002 complete; separate second-review task added. Public text approvals, identities, scholarly claims and media rights unchanged.
- **2026-09-05:** Individually checked all forty main Penn catalogue concordances; added immutable dated reviews and current-evidence counting, without identity changes. Added eleven reported metadata claims and six follow-up leads. Nine new field differences are now visible: total 337, with 24 current decisions and 313 pending (304 stale plus 9 new). English cohort remains 35/35 checked; no media rights or public approvals changed.
- **2026-09-05:** Added a portfolio-level roadmap summary with task and handoff-gate counts, explicit strengths and release blockers, and separate open-lead reporting. Raised QA to L2 because evidence-bound, immutable review workflows now cover conflicts, texts, citation repairs, rights, and museum concordances; the unreviewed backlog and missing stratified accuracy audit keep it below L3.
- **2026-09-05:** Adjudicated all nine newly exposed Penn field differences as evidence-bound unresolved cases, reducing current review demand from 313 to 304. Added an append-only object-relationship model and recorded five directed Penn assertions without merging identities. Preserved Montgomery's cohort-level dating as context rather than converting it into an object-specific correction. Three of six Penn anomaly leads are resolved; dating and two language checks remain active.
- **2026-09-05:** Completed a further twenty-case evidence-bound revalidation batch for same-source wording and complementary field facets. Current conflict coverage is 53/337 and the older backlog is 284. Each compatibility decision explicitly distinguishes dating from period, findspot from production place, or exact wording variants; batch replay is a no-op and all historical snapshots remain retained.
- **2026-09-05:** Reviewed a user-provided excerpt of Waller's 2025 excavation-site survey (printed pp. 10–13) and added META-005 to distinguish documented excavation from museum-register, dealer, inferred and unverified provenance. Archived the excerpt privately by hash, added a non-destructive assessment to BM 91711's plausible but unverified Arban claim, and opened focused Arban, Susa and corpus-wide findspot-audit leads.
- **2026-09-05:** Continued META-005 into the primary literature: visually checked Schwab 1891 pp. 590–593 and Montgomery 1913 p. 19, enumerated the three Dieulafoy mission Susiana bowls N–P as separate probable objects, and recorded exact dimensions, condition, beneficiary uncertainty, excavation events, and source-basis assessments. Modern museum accessions and trench-level contexts remain unresolved.
- **2026-09-05:** Imported the July 2026 systematic scoping review and checked the corpus against it. Added the SCHOL workstream, TEXT-007, META-006 to META-008 and QA-008. Findings: seventeen foundational editions absent from `sources`; publications modelled only as identifier prefixes, so publication_reference_pct measures designations rather than editions; the claim vocabulary has outgrown the seven hard-coded comparison groups, making the 337/284 conflict queue an undercount; the field model omits the review's People, Ritual, Intertexts, Visual and Scholarship groups; Mandaic and Pahlavi lag their working counts. Re-ordered priorities to put the control list and the comparison model ahead of queue depth. No corpus writes. Repository placed under version control - it had no commits - and `ibi state` now records a per-table fingerprint so two agents can detect corpus drift.
- **2026-09-05:** Added an append-only text publication ledger (migration 011) and `ibi ingest-text-publication`. Approved 45 texts: Montgomery's 35 scan-checked English reading texts as expired US copyright, and 10 index summaries as own work, each recording a rights basis, an attribution and an explicit editorial status. Approvals are bound to the text's content fingerprint, so the outstanding TEXT-006 specialist review will revoke them rather than silently changing published text. Extended the public export so a withheld text keeps its citation, locator, link and access status, and added an editions table naming 476 publication locations across 472 objects. Untracked the dated research snapshots and published the gated projection at data/public/2026-09-05 instead.
