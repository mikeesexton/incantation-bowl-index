# Incantation Bowl Index: dataset maturity roadmap

> Living document generated from `research/roadmap/dataset_maturity.json` and the private corpus. Update task status or add newly discovered gaps in the JSON register, then run `ibi roadmap`.

Generated: `2026-09-07T03:02:40+00:00`

## Portfolio status

Current phase: **Source-rich research corpus with one completed reference cohort; active reconciliation and enrichment; not release-ready**

| Progress measure | Current |
|---|---:|
| Roadmap tasks | 21 done · 16 in progress · 18 queued · 0 blocked |
| Quantitative handoff gates passing | 2/5 |
| Required handoff tasks complete | 7/24 |

### What is solid

- Discovery is broad and reproducible within the classes it searched: 843 sources and 1,632 appearances support 1,590 candidate records, every record has evidence, the generated dedupe queue is empty, and two measured saturation sweeps passed the phase-one rule. Saturation is bounded by those twelve source classes; printed editions and the bibliographic databases were not among them.
- The Montgomery/Penn reference cohort is now internally complete at its stated level: 40/40 printed register entries checked, 35/35 available English translations checked against scans, five source absences documented, and 40/40 current Penn number concordances individually verified.
- Research corrections are reversible and inspectable: conflict decisions, text revisions, citation repairs, media-rights reviews, museum concordance reviews, and source-reported object relationships retain evidence-bound append-only history. The narrow public export fails closed on texts and media.
- The evidence discipline is genuinely unusual: identifiers record who reported a designation, original source strings are retained beside structured values, the 4 September review published its own permissive-rule defect, and the public export fails closed.
- The public boundary is now positive rather than merely defensive: 45 texts are published on a stated rights basis with their editorial state declared, and every one of the 151 withheld texts still names its edition, exact locator and link so a reader can consult it.
- The comparison model now covers the whole claim vocabulary: 66 fields grouped, 35 excluded with a stated reason, none unclassified, and a test that fails when a new field appears in neither list.
- The project now has an external yardstick. Waller's list of JBA bowl publications 1853-2024 is held, transcribed and measured against, so completeness is a number rather than an impression.
- Bibliographic coverage of the field's JBA control list is complete: 115 of 115 publications 1853-2024 have a source record with a sourced citation, up from 46.
- Publications are first-class: a bowl can be asked which edition publishes it, separately from which source reported the designation. All 19 publication keys now resolve, covering 435 distinct candidate records. Counts deduplicate records across aliases and publications.

### What prevents release readiness

- Publication links exist but are thin: 435 of 1,590 distinct candidate records carry a publication key, although all 19 current keys resolve to publications. Most records still have no publication key.
- Identity and claim quality is not yet measured corpus-wide: 315 field-difference decisions need evidence-level revalidation, now measured against the full claim vocabulary rather than seven hard-coded groups, findspot claims are not yet consistently graded by evidence basis, and a reproducible stratified identity audit has not begun.
- Text and edition coverage remains sparse outside Montgomery: 312/794 probable or confirmed identities have a publication-scheme reference, still only a proxy for a checked edition locator; just one identity has a recorded transcription or transliteration.
- Release rights are unreviewed: all 325 media rows have inventory holds, but zero have completed rights decisions and zero are approved for reuse.
- The National Library of Israel, Schøyen, broader Penn, and remaining British Museum/Segal concordances are incomplete; continuous operations, encrypted off-device backup, and a 14-day shadow run are not set up.
- Acquisition completeness is not yet measured corpus-wide: 22 sources have captures, eleven with PDFs and eleven with only non-PDF captures. Ford 2014 now has a hash-bound complete-article scope review covering all 29 pages (235–263); this does not certify its readings. 355 distinct candidate records depend on publications without linked PDF captures. The Library of Congress is now the preferred offline route: both Aramaic Bowl Spells volumes, Segal 2000, Isbell 1975, Ford–Morgenstern Volume One, Müller-Kessler's TMH 7, Moriggi 2014 and Naveh–Shaked 1998 are confirmed available onsite.

## Current scope snapshot

| Measure | Current |
|---|---:|
| Candidate source records | 1591 |
| Working physical identity hypotheses (all statuses) | 1323 |
| Source appearances | 1635 |
| Sources | 843 |
| Pending dedupe decisions | 0 |
| Identities triggering raw claim-difference flags | 217 |
| Triaged claim-field differences | 52/372 |
| Compatible differences | 37 |
| Review required (missing or no longer valid) | 320 |
| Existing reviews requiring revalidation | 285 |
| Substantive conflict instances | 15 across 13 identities |
| All identities with a publication reference | 393/1323 (29.7%) |
| Probable/confirmed identities with a publication reference | 312/795 (39.2%) |
| Identities with a translation | 48 |
| Scan-checked normalized reading texts | 35 |
| Publication keys resolved to the publication they designate | 19/19 |
| Objects under a resolved publication | 435/435 |
| Montgomery/Penn concordances with dated current-evidence review | 40 |
| Source-reported object relationships / unresolved scope | 5 / 4 |
| Identities with a transcription/transliteration | 1 |
| Media records with a non-unknown rights status | 38/326 (11.7%) |
| Media with a current ledger entry | 325/326 |
| Media with completed rights decisions / approved for reuse | 0 / 0 |
| Blocked leads | 28 |
| Open or active leads | 19 |
| Qualifying discovery-saturation sweeps | 2 |

Coverage means a field or reference is present, not independently verified. Publication coverage currently uses identifier schemes as a proxy. A non-unknown rights label is not a reviewed public-reuse decision. Discovery saturation applies only to the logged searches and does not estimate global completeness.

### Identity-level field coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 911 | 68.9% |
| Provenance | 327 | 24.7% |
| Dating | 482 | 36.4% |
| Dimensions | 381 | 28.8% |
| Material | 408 | 30.8% |
| Language | 664 | 50.2% |
| Script | 92 | 7.0% |
| Text Edition | 1 | 0.1% |
| Translation | 48 | 3.6% |
| Image | 325 | 24.6% |

### Content-facet coverage

The scoping review's People, Ritual, Intertexts, Visual and Scholarship groups. These are counted and conflict-checked but are not release gates.

| Facet | Identities | Coverage |
|---|---:|---:|
| Biblical Intertexts | 168 | 12.7% |
| Condition | 140 | 10.6% |
| Publication | 79 | 6.0% |
| Client | 59 | 4.5% |
| Ritual | 44 | 3.3% |
| Text Form | 37 | 2.8% |
| Practitioner | 29 | 2.2% |
| Visual | 27 | 2.0% |
| Text Description | 20 | 1.5% |
| Parallels | 6 | 0.5% |
| Authenticity Assessment | 4 | 0.3% |
| Target | 2 | 0.2% |
| Vessel Form | 2 | 0.2% |

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
| SCHOL | Scholarly bibliography and published-corpus enumeration | L3 | L3 | Research |
| META | Physical, chronological, linguistic, and provenance enrichment | L1 | L3 | Mixed |
| RIGHTS | Images and rights | L1 | L4 | Human rights review |
| OPS | Mac mini continuous operations | L0 | L5 | Mac mini after 2026-09-22 |
| QA | Evidence quality and regression controls | L2 | L3 | Research and engineering |

## Current priority order

1. TEXT-001 / SCHOL-004 follow-through: all 19 current publication keys resolve; extend evidence-backed publication references beyond the current 435 of 1,591 distinct candidate records. Enumerate object-level coverage for the 69 bibliography additions; some now resolve existing keys, so do not assume all are unattached.
2. SCHOL-005 / QA-004: obtain the Library of Congress Reader Identification Card, then consult Segal 2000 and Aramaic Bowl Spells Volume One from the priority reading-room queue. TMH 7, Moriggi 2014 and Naveh–Shaked 1998 are now confirmed follow-on holdings. Record document scope and page-level evidence; do not call a cataloged holding read until it has actually been inspected.
3. SCHOL-006: classify the remaining 164 unclassified works by scope. Seven held publications have inspected scope judgments; continue with authoritative abstracts, tables of contents and newly acquired documents, leaving ambiguous works unclassified.
4. TEXT-001 follow-through: Ford 2014 editions and all 14 main JBA-labelled commentary discussions are indexed, and the Ford 2002 attribution discrepancy is resolved with immutable correction history. The official 2013 edition requires purchase or institutional access; obtain it through IBI-LEAD-JBA2013-ACCESS before specialist comparison, then review the provisional-candidate concordances.
5. QA-002 / CONC-005: revalidate the 320-case queue in coherent source batches, including 285 earlier reviews. Preserve reported values and uncertainty; claim-vocabulary coverage is now complete.
6. META-008: assemble a Mandaic denominator from corpus editions represented in the bibliography. The earlier 23% expectation is Morony's historical estimate, not a collection target; no dedicated control list has yet been identified by this project.
7. META-002 / META-003: continue the B2963 object-specific dating investigation and inspect original scripts for Montgomery 9 and 31 before assigning language source errors. The relationship and measurement anomaly reviews are complete at the available evidence level.
8. META-005: apply Waller's evidence-basis distinction to the location corpus, starting with claims labelled Excavated/Findspot and the Susa controlled-excavation group. Preserve museum and market claims as reports rather than silently upgrading them to archaeological facts.
9. TEXT-006 / TEXT-003: obtain independent review of all 35 checked English reading texts, particularly magical formulas and restorations, then develop a checked original-script transcription/transliteration pilot. The first English scan-review pass is complete.
10. CONC-002: extend beyond the completed forty-entry reference cohort to reconcile the remaining Penn holdings and historical inventory. Check precise identifiers and publication references; do not generalize the 40/40 result to the broader collection.
11. QA-003: select and audit a reproducible stratified sample before assigning an overall accuracy percentage. The forty-entry Montgomery source audit is useful but not representative of the entire corpus.
12. RIGHTS-002: investigate evidence for 326 media records, starting with the newly added M163 plate reference and shared institutional policies. The 325 initial rows have provisional holds; zero media have completed rights decisions, and agents collect evidence for human review.
13. TEXT-001 / QA-004: align edition-reference and field-assessment metrics with cited evidence; then extend the checked institutional cohorts.
14. DISC-002: pursue precise source gaps, including IBI-LEAD-MONT42 and authorized Segal catalogue access; defer another undirected discovery expansion.
15. OPS: document restore and collector controls for the Mac mini. A local database backup was restore-checked; encryption, off-device backup and shadow operation remain outstanding.

## Offline research queue

The Library of Congress in Washington, DC is the default offline source for this project. Search its catalog first, request available General Collections items for onsite consultation, and use other libraries or interlibrary loan only when LC lacks the work. Onsite consultation requires a Reader Identification Card.

| Priority | Status | Publication | Library record | Call number | Needed for |
|---:|---|---|---|---|---|
| 1 | Card Pending | Segal — Catalogue of the Aramaic and Mandaic Incantation Bowls in the British Museum (2000) · `SRC-72D809FB4249` | [2001369942](https://lccn.loc.gov/2001369942) | `PJ5208.A5 S45 2000` | SCHOL-005; CONC-001; 252 candidate records |
| 1 | Card Pending | Shaked, Ford and Bhayro — Aramaic Bowl Spells, Volume One (2013) · `SRC-7FBBB775E502` | [2013009563](https://lccn.loc.gov/2013009563) | `PJ5208.A2 S53 2013 · v. 1` | TEXT-001; Ford 2014 specialist comparison |
| 2 | Card Pending | Ford and Morgenstern — Aramaic Incantation Bowls in Museum Collections, Volume One (2019) · `SRC-8A145FAA2EBB` | [2019026750](https://lccn.loc.gov/2019026750) | `PJ5208.A2 2020 · v. 1` | TEXT-001; 19 candidate records; MRLA 8 verification |
| 2 | Card Pending | Isbell — Corpus of the Aramaic Incantation Bowls (1975) · `SRC-1FE46019356A` | [75015949](https://lccn.loc.gov/75015949) | `PJ5208.A5 I8 1975` | TEXT-001; 17 candidate records |
| 2 | Card Pending | Shaked, Ford and Bhayro — Aramaic Bowl Spells, Volume Two (2021) · `SRC-8C611BF93288` | [2013009563](https://lccn.loc.gov/2013009563) | `PJ5208.A2 S53 2013 · v. 2` | TEXT-001; 16 candidate records |
| 2 | Card Pending | Naveh and Shaked — Amulets and Magic Bowls, third edition (1998) · `SRC-696E71D7E586` | [99201169](https://lccn.loc.gov/99201169) | `BM729.A4 N38` | TEXT-001; 7 candidate records; first edition also onsite under LCCN 87182340 |
| 2 | Card Pending | Müller-Kessler — Die Zauberschalentexte in der Hilprecht-Sammlung (TMH 7) (2005) · `SRC-63345F60155B` | [2006364726](https://lccn.loc.gov/2006364726) | `PJ5208.A5 M85 2005` | TEXT-001; 2 candidate records; publication key now bibliographically resolved |
| 2 | Card Pending | Moriggi — A Corpus of Syriac Incantation Bowls (2014) · `SRC-3C4294DDB367` | [2014006700](https://lccn.loc.gov/2014006700) | `PJ5615 .M665 2014` | TEXT-001; 2 candidate records; Syriac corpus coverage |

Availability is a live catalog state, not proof that a volume has been consulted. Confirm status and request items before each visit; after consultation, deposit only researcher-supplied files that may lawfully be retained and record page-level evidence through the normal manifests.


## Publication purchase backups

Purchases are backup options after the Library of Congress, other authorized libraries, interlibrary loan and repository routes have been checked. Keep a work here when a purchase link is known and the publication remains important, but do not recommend buying while an easier lawful route is available.

| Priority | Status | Publication | Needed for | Purchase |
|---:|---|---|---|---|
| 1 | Backup Only | Shaked, Ford and Bhayro — Aramaic Bowl Spells: Jewish Babylonian Aramaic Bowls, Volume One (2013) · `SRC-7FBBB775E502` | TEXT-001; Ford 2014 specialist comparison | [Publisher](https://brill.com/display/title/20045) |

Prices are deliberately not frozen here because they change. When a volume is bought, supplied, or consulted through authorized library access, update its status and preserve the acquisition evidence rather than deleting the row.


## Task register

### DISC — Discovery and citation snowballing

Maintain maximum-recall discovery across scholarship, catalogues, museums, auctions, dealers, excavations, and cited private collections without treating completeness as absolute.

- [x] **DISC-001 — Complete phase-one source-class discovery** · Done · Research
  - Done when: All planned source classes are searched or explicitly blocked and two independent broad sweeps produce under 1% net-new identities without a new source class.
  - Evidence/status: Twelve source-class targets assessed; two qualifying saturation sweeps; campaign report generated. Now qualified by an external check: measured against Waller's control list of JBA bowl publications 1853-2024, the index holds 40% of them. Saturation measured marginal yield within the twelve searched classes and does not indicate coverage of the published corpus.
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
  - Evidence/status: 312/795 probable/confirmed identities have publication-scheme identifiers (39.2%). This proxy counts designations, not editions: the publications being designated have no records of their own (see SCHOL-004), so raising the number does not yet raise edition coverage. Re-specify the metric against resolved publication records and sourced no-known-edition assessments before treating it as a release gate. SCHOL-004 is now done, so the metric can be re-specified: all 435 objects carrying a publication key sit under a resolved publication source, and all 19 keys resolve. That is still designation coverage, not a checked edition locator, but the denominator is now meaningful. On 2026-09-06 Ford 2014 added three precisely located edition appearances and a registered publication key: AS 13 and Davidovitz 27 are new provisional candidates, while Museo Sefardí 1073 attaches to existing AC-MSEF via the explicit p. 253 n. 56 concordance. No scholarly text or images were republished. A second Ford 2014 batch indexed all 14 bold JBA-labelled main commentary discussions on pp. 236–246 across 13 existing records, with no new identity decisions. Ten missing 2013-volume publication keys were added, raising unique candidate coverage to 435/1,590. Retained readings and grammatical comments are distinguished from correction proposals; no preferred text was chosen. A targeted access pass then confirmed that the official 2013 volume requires purchase or institutional access; the Library of Congress now supplies the preferred authorized route. A complete Internet Archive community upload carries no license, rights statement or depositor-authority evidence and was not acquired or used. IBI-LEAD-JBA2013-ACCESS records the access dependency, so the specialist comparison remains open rather than being attempted from metadata or an unverified copy. The Ford 2002 attribution discrepancy is resolved: the old row was an OpenAlex metadata artifact and is now classified accordingly, its exact imported state is preserved in the append-only correction ledger, and the verified J. N. Ford article appearance is attached to BM 91715. On 2026-09-06 the researcher-supplied Levene-Shaked JSQ 6 scan added a fully located edition appearance for M163 and a distinct provisional MS 2054/124 record, without copying the modern transcriptions or translations.
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

- [x] **SCHOL-001 — Acquire Waller's 2025 publication list as a control list** · Done · Research owner
  - Done when: Waller's chapter is held in full, its list of JBA bowl publications 1853-2024 is enumerated, and the index is measured against it. Turning the missing entries into source records is SCHOL-002.
  - Evidence/status: Held. The researcher supplied the full 45-page chapter on 2026-09-05; deposited privately by content hash (archive SHA-256 b60b030f...4237c77) under SRC-19F191B3F5C5, superseding the two-page excerpt. The list at printed pp. 40-47 is transcribed to research/sources/waller_2025_jba_publication_list.jsonl: 115 entries by 52 authors. First external completeness measurement: the index holds 46 and is missing 69, so published-JBA coverage is 40%. Gordon is the largest single hole at 8 publications, none held; the nineteenth-century layer is almost entirely absent. See data/reports/waller_control_list_2026-09-05.md. SCHOL-002 has since closed the bibliographic side of the gap; object-level coverage of those publications remains unmeasured.
- [x] **SCHOL-002 — Seed the missing foundational bibliography** · Done · Research
  - Done when: Every work named by the field's control lists has a source record with a sourced citation, or an explicit reason it cannot be obtained. Linking those publications to the objects they publish is SCHOL-004 and TEXT-001, not this task.
  - Evidence/status: Ingested 69 publications from Waller's control list with citations verbatim from printed pp. 40-47, plus 17 works from the scoping review that fall outside his JBA scope - Pognon 1898, Yamauchi 1967, Naveh and Shaked 1987, Morony, Mokhtarian, Harari, Haberl, Frim, Secunda, Gross and Scarlassara, Mackenzie, and four Manekin-Bamberger titles. Four overlaps were resolved in favour of Waller's sourced citation. Sources 753 to 839; ingest is idempotent on the exact citation. Control-list coverage 46/115 to 115/115. That is bibliographic presence only: the publications have not been read, their editions are not located, and the bowls they publish are not linked. Parsed titles and source types are the least reliable field; the verbatim citation is authoritative.
- [ ] **SCHOL-003 — Run the bibliographic database sweep the review specifies** · Queued · Research
  - Done when: RAMBI, ATLA, Index Islamicus, L'Annee philologique, ProQuest Dissertations, WorldCat, Crossref and OpenAlex are each searched with saved query strings, dates and result counts, and the field's journal archives are swept by object siglum and opening formula as well as by keyword.
  - Evidence/status: The review's own 14-row search log is a targeted verification pass, not a sweep, and says so. The index's phase-one saturation covers twelve source classes, none of which is the bibliographic databases. Both gaps have the same shape. SCHOL-002 has closed the bibliographic gap against Waller's list; assess a database sweep by additional publications beyond that list and improved object-level enumeration.
- [x] **SCHOL-004 — Make publications first-class records, not identifier prefixes** · Done · Engineering
  - Done when: Every publication-derived identifier resolves to a source record for the publication being designated, kept separate from the source that reported the designation; a regression test fails when a publication key has no such record.
  - Evidence/status: Migration 012 adds an append-only publication registry recording which publication a designation belongs to, separately from `identifiers.source_id`, which correctly records who reported it. All 19 current publication keys now resolve to source records, covering 435 distinct candidate records. The earlier overlapping totals were corrected by QA-004 on 2026-09-06. MRLA 8 was resolved from the volume's own imprint page. TMH 7 was resolved on 2026-09-06 from official Library of Congress record 2006364726, which explicitly names Müller-Kessler's 2005 Harrassowitz publication as Texte und Materialien der Frau Professor Hilprecht Collection, Bd. 7; this supersedes IBI-PUBREG-18 without claiming the book has been read. Four keys - Isbell 1975, Naveh-Shaked 1993, Naveh-Shaked 1985/1993 and Gorea 2003 - became resolvable only because SCHOL-002 ingested their publications. `unresolved_publication_keys` and tests/test_publications.py fail when a key has no registry entry; the roadmap reports both counts.
- [ ] **SCHOL-005 — Keep an acquisition register and work the want list** · In progress · Mixed
  - Done when: Every source record shows whether the document is held, and the want list is ranked by how much of the corpus depends on each unread work. Works with dependants are either held, or carry a documented reason they cannot be obtained.
  - Evidence/status: `ibi report-acquisitions` inventories captures separately from completeness: 24 of 843 sources have captures, thirteen with PDFs and eleven with only non-PDF captures. All completeness states are unassessed unless a separate scope review exists; a MIME type cannot certify that a work has been read. 670 sources with dependants have no PDF capture and 355 distinct candidate records depend on publications without PDFs. Ford 2014 has a hash-bound complete-article scope review for all 29 pages (235–263; SHA-256 0b7f1780d434...). The complete researcher-supplied JSQ 6 scan is bound by hash to both Levene 1999 and Shaked 1999 and has inspected scope decisions. On 2026-09-06 the Library of Congress became the preferred offline repository. Its live catalog now supplies eight queued onsite volumes: Segal 2000; both Aramaic Bowl Spells volumes; Isbell 1975; Ford–Morgenstern Volume One; Müller-Kessler's TMH 7; Moriggi 2014; and Naveh–Shaked 1998. The separately cataloged 1985 first edition of Naveh–Shaked is also onsite but is recorded only as an alternate because it must not be conflated with the 1987 source record. Segal remains the highest-impact item at 252 distinct records. PURCHASE-001 remains backup-only.
- [ ] **SCHOL-006 — Classify the scholarship by scope** · In progress · Research
  - Done when: Every scholarship record carries a scope, either derived from the publication registry or recorded as a reading judgment with a basis.
  - Evidence/status: Migration 013 adds an append-only scope ledger and `ibi ingest-source-scope`; the vocabulary is single_object_edition, corpus_edition, catalogue, thematic_study, synthesis, linguistic_study, provenance_ethics, excavation_report, not_scholarship. The resolved TMH 7 registry entry raises derived coverage to 27 works. On 2026-09-06 the first reading-judgment batch classified all five held documents that remained unclassified: Schwab 1891 as a corpus edition; Levene and Bhayro 2006 as a single-object edition; Kedar 2019 and Waller 2022 as thematic studies; and Waller 2025 as a synthesis. A second inspected batch classified Levene 1999 as a single-object edition and Shaked 1999 as a thematic study. Scope coverage is now 34 of 198 works, leaving 164 unclassified rather than guessed.
- [ ] **SCHOL-007 — Check the contributor groupings by eye** · In progress · Research
  - Done when: Every contributor group with more than one spelling has been confirmed as one person, and any wrong merge has an alias-ledger override.
  - Evidence/status: 107 contributors derived from 199 works by surname and first initial, with bare surnames folded into a named scholar only where exactly one scholar of that surname exists. Fourteen multi-spelling groups were checked by eye on 2026-09-05 and all are one person. Two defects were found and fixed in the process: the SCHOL-002 authors placeholder invented an author called 'see citation]' and keyed every '[and others' name on the surname 'others', which had merged Geller with Gordon and Schwab with Shaked; and bare surnames left by stripping it were splitting Levene and Gordon from their full names. Migration 013 adds an append-only alias ledger for overrides in either direction.
- [x] **SCHOL-008 — Expose the publication registry to readers** · Done · Engineering
  - Done when: A reader can ask which bowls a publication publishes, and see which designations do not resolve.
  - Evidence/status: A `publications` projection table over migration 012's registry, and a page listing all 19 keys with their object counts: Segal 2000 at 252 bowls, Montgomery 1913 at 84, Shaked-Ford-Bhayro 2013 at 33, MRLA 8 at 19, Isbell 1975 at 17. All 19 resolve to a work in the library after TMH 7 was verified from official Library of Congress series-volume metadata on 2026-09-06. Selecting a publication filters the corpus to its bowls.

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
- [x] **META-006 — Extend the field model to the content facets** · Done · Mixed
  - Done when: People, Ritual, Intertexts, Visual and Scholarship are modelled field groups with coverage reporting and conflict comparison, not stray claim names.
  - Evidence/status: Thirteen content groups added alongside the seven release-gate facets: condition, vessel_form, text_form, text_description, client, target, practitioner, ritual, biblical_intertexts, parallels, visual, publication and authenticity_assessment. They are counted for coverage and compared for conflicts, and they flow through identity_rows, the enrichment report and the identity export without changing next_action or the handoff gate. Biblical intertexts are the best-covered content facet at 168 identities (12.7%), then client 58, ritual 43, practitioner 29, publication 62, condition 139. Widening the language group with catalogue_language_codes raised language coverage from 459 (34.8%) to 663 (50.2%).
- [ ] **META-007 — Separate the roles behind a named person** · Queued · Research
  - Done when: Every person claim records which role the source assigns - author, textual voice, copyist, producer, commissioner, client, beneficiary - with its uncertainty, and contested attributions link to the scholarship that contests them.
  - Evidence/status: Eleven objects carry handwriting_attribution claims whose values are women's names, from Kedar 2019's contested female-authorship argument. Saar 2024 and Manekin-Bamberger 2025 respond by separating the roles. The field name asserts more than the source does; keep the claim, add the role and the dispute link. QA-008 laid the groundwork: client, target and practitioner are separate comparison groups rather than one people group, so a client name and a contested authorship attribution can no longer be compared against each other. What remains is recording the role and the dispute link on each claim.
- [ ] **META-008 — Bring Mandaic, Syriac and Pahlavi to parity** · Queued · Research
  - Done when: Each language group has enumerated corpora from its primary editions, and the 819 records with no language claim are assessed or explicitly marked unreadable or unknown.
  - Evidence/status: Measured against the EJCM working counts the review quotes: JBA/Aramaic 379 of about 500, Mandaic 77 of about 125, Syriac 69 against about 50, Pahlavi 2, pseudo-script 35, and 819 records - 52% - with no language claim at all. Mandaic and Pahlavi have an obvious cause: Pognon 1898 and Yamauchi 1967 are not in the corpus. See SCHOL-002. Since QA-008, the 205 NLI catalogue language codes count toward language coverage. Note that none of those 205 objects also carries an edition-based language claim, so they are unverified catalogue classifications rather than corroborated attributions; the earlier expectation that they would expose catalogue-versus-edition disagreements was not borne out. A better external benchmark is now available. The corpus-wide distribution benchmark traces to Morony 2003: 87 - approximately 62% Jewish, 23% Mandaean, 13% Syriac - cited and endorsed by Ford and Abudraham 2018 n. 3, and quoted from there by Waller 2025 p. 3 n. 1. Ford and Abudraham note Morony worked from a corpus far smaller than what is now available, so this is a twenty-year-old estimate endorsed twice rather than a current census; cite it as Morony's, with the caveat. Against it the index runs 80.0% JBA, 10.6% Mandaic, 9.5% Syriac across 729 classified records - a shortfall of roughly 91 Mandaic objects. Syriac is close; JBA is over-represented by about the margin publication bias predicts. Waller's list is JBA only, so Mandaic needs its own control list. Ford and Abudraham 2018 was obtained on 2026-09-05 and is NOT the Mandaic control list this task needs: it publishes eight confiscated bowls, six Syriac and two Mandaic, and is an object publication rather than a census. No Mandaic equivalent of Waller's JBA list is known to exist, so the Mandaic denominator has to be assembled from the corpus editions themselves - Pognon 1898, Yamauchi 1967, McCullough 1967, Segal 2000, Muller-Kessler and Morgenstern, Abudraham's re-editions - all now in `sources`.
- [x] **META-009 — Make the content facets browsable** · Done · Engineering
  - Done when: Every content facet is an entry point with counts, and a reader can move from a value to the bowls carrying it.
  - Evidence/status: Eight browse axes in the reading room - people named, what they do, scripture quoted, hands and scribes, what is drawn, where they are, language, provenance - counted from the projection's facts table client-side, so a published static export computes them the same way and no query endpoint breaks the equivalence. Ritual purpose alone yields 35 distinct values across 43 bowls, including 'Divorce document' (4) and 'Semamit historiola' (4). Corpus-wide search covers display names, every fact value and the 45 published texts; 'lilith' returns 31 bowls.

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
- [x] **RIGHTS-005 — Render approved images, and only approved images** · Done · Engineering
  - Done when: The reading room shows a bowl's photograph when its media has a completed approval, and shows nothing of it otherwise, with tests covering both directions.
  - Evidence/status: The reading room renders whatever media the projection emits, and the projection emits a media row only for a current approval - so an uncleared image has no row to render and the data-drawn spiral carries the grid instead. tests/test_media_gate.py covers all three states: a public-domain source alone releases nothing, a completed approval releases the URL with its attribution, and a withhold decision keeps it off the page. Currently 0 of 325 media are approved, so no image appears; when RIGHTS-002 clears one it appears with no further work. Circular crop, since a bowl photographed from above is a circle.

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
  - Evidence/status: Current full-vocabulary queue: 367 field-difference instances, 53 with current decisions, 314 needing review; 284 of those have earlier reviews requiring revalidation. Use coherent source batches and exact current evidence. Museum concordance confirmation does not adjudicate metadata. The Ford 2014 Toledo bibliography/concordance pair adds one publication-group flag; it has not been adjudicated. The two JBA 23 commentary topics add a text-description difference; it remains unreviewed.
- [ ] **QA-003 — Audit a stratified sample of identity and extraction decisions** · Queued · Research
  - Done when: Publish reproducible sample selection across institutions, market records, status classes and merge methods; check primary evidence and report denominators, error categories and uncertainty.
  - Evidence/status: Zero generated pending dedupe candidates is queue completion, not measured identity accuracy. Current review examined architecture, integrity, archive hashes, aggregate metrics and selected rule evidence, not all objects.
- [ ] **QA-004 — Separate presence, assessment, verification and source coverage metrics** · In progress · Mixed
  - Done when: Track field assessment and verification independently of presence; distinguish excavation provenance from production region and ownership; reconcile item-level denominators for major sources; align publication and rights gates with reviewed evidence.
  - Evidence/status: Roadmap now separates 325 initial media ledger holds from 0 completed rights assessments and 0 public approvals. The newly indexed M163 plate reference brings media to 326 rows and remains without a rights decision; no image was republished. The roadmap counts 35 current scan-checked reading texts separately from text presence. Main Montgomery denominator is explicit: 40 entries, 35 translations and 5 documented absences in this edition. General field-assessment and edition-reference metrics still need work. Forty current-evidence museum concordance reviews are now counted separately from existing identity links; observations retain review dates and do not certify unchanged live websites or unrelated metadata. On 2026-09-06 acquisition reporting was corrected to separate any capture, PDF capture and unassessed document completeness. Publication and acquisition totals now count unique candidate records rather than identifiers or summed memberships. Regression tests cover aliases, overlapping publications, non-PDF captures and excerpts. Completeness review remains outstanding.
- [x] **QA-005 — Implement evidence-bound subset reviews and append-only history** · Done · Engineering
  - Done when: Review batches reject changed evidence, duplicate or absent fields and count-only overrides; writes are atomic and replay-idempotent; all original and subsequent decisions remain in immutable history.
  - Evidence/status: Migration 005 preserved all 328 starting decisions. The nine-instance batch and one later refreshed decision yield 338 immutable snapshots; all original and subsequent judgments remain inspectable.
- [x] **QA-006 — Repair range-generated citation pointers with retained originals** · Done · Engineering
  - Done when: Importer assigns each range item its own locator and exact-evidence repairs retain before/after snapshots; regression tests cover exceptions, replay, stale input and rollback.
  - Evidence/status: 137/137 affected Segal claims repaired; zero remaining source/appearance locator mismatches in that scoped audit. Scholarly values, uncertainty and identity links unchanged. Migration 008 and research/reviews/segal_locator_corrections_2026-09-04.json.
- [x] **QA-007 — Preserve originals and evidence for text proofreading** · Done · Engineering
  - Done when: Scan-bound revision batches preserve original and corrected texts, reject stale evidence, and prevent OCR reimport from overwriting checked work.
  - Evidence/status: Migration 006, thirty-five current scan-checked reading texts and passing regression tests; exact originals retained and private text histories redacted from research exports. Completion batch replays with zero changes.
- [x] **QA-008 — Reconcile the claim vocabulary with the comparison model** · Done · Engineering
  - Done when: Every claim field is either in a CORE_COVERAGE group or explicitly excluded with a recorded reason; a test fails when an unclassified field appears; and the conflict counts are reported against that full denominator.
  - Evidence/status: All 101 claim fields are now classified: 66 in a comparison group, 35 explicitly excluded with a stated reason, 0 unclassified. `unclassified_claim_fields` reports any new field and `ibi stats` surfaces it; tests/test_field_model.py fails on a field that is in two groups, both grouped and excluded, excluded without a reason, or neither. The conflict denominator moved from 337 to 365 with zero existing decisions invalidated, so the backlog is 312 rather than 284 and is now a measured total rather than an artefact of seven hard-coded groups. Exclusions carry their reason: market values are per-sale events, ownership history is event-shaped and belongs in `events`, object relationships belong in `object_relationship_assertions`, and META-005 evidence gradings assess a claim rather than rival it.
- [x] **QA-009 — Keep the filters usable on a small screen** · Done · Engineering
  - Done when: Structured filtering is reachable at every viewport width.
  - Evidence/status: Below 900px the stylesheet set `#filters fieldset { display: none }`, so every structured filter disappeared on tablet and phone and only free-text search remained. The fieldsets are now inside a native disclosure: the summary is hidden above 900px so a wide screen reads as before, and below it the panel starts collapsed but all five selects stay in the DOM and reachable. Widening the window reopens it, since the summary is hidden at that width and the panel would otherwise be shut with no control to open it.

## Mac mini handoff gate

Target availability: **2026-09-22**. This is an operational eligibility date, not an automatic permission to publish or to make scholarly judgments.

Overall gate: **NOT READY**

### Quantitative conditions

- [x] No unreviewed generated dedupe candidates — current `0`; target `<= 0`.
- [ ] Every generated claim-difference flag has a recorded triage — current `320`; target `<= 0`.
- [x] Discovery saturation demonstrated by independent sweeps — current `2`; target `>= 2`.
- [ ] Publication-reference coverage reaches the operational threshold. Currently a proxy over identifier schemes; SCHOL-004 must land before this gate means edition coverage — current `39.2%`; target `>= 80.0%`.
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
- [x] SCHOL-002 — Seed the missing foundational bibliography
- [x] SCHOL-004 — Make publications first-class records, not identifier prefixes
- [x] QA-008 — Reconcile the claim vocabulary with the comparison model
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
- **2026-09-05:** Completed QA-008 and META-006. Classified all 101 claim fields — 66 grouped, 35 excluded with reasons, none unclassified — and added thirteen content groups for the scoping review's People, Ritual, Intertexts, Visual and Scholarship facets. Conflict instances moved 337 to 365 with no existing decision invalidated; the backlog is 312 and is now a measured total. Language coverage rose from 34.8% to 50.2% because 205 NLI catalogue codes now count. Corrected an earlier overstatement: no object carries both a catalogue code and an edition-based language claim, so that specific disagreement does not occur in the data; the effect is on coverage, not conflicts. Client, target and practitioner are separate groups, so contested authorship attributions can no longer be compared against client names.
- **2026-09-05:** SCHOL-001: the researcher supplied Waller's full 'State of the Art' chapter, deposited privately by content hash. Transcribed its list of JBA bowl publications 1853-2024 - 115 entries, 52 authors - and measured the index against it for the first time: 46 held, 69 missing, 40% coverage of the published JBA corpus. Gordon is the largest hole at 8 publications. Added a second benchmark from Ford and Abudraham 2018 via Waller: the corpus should run about 62% JBA, 23% Mandaic, 13% Syriac, against the index's 80.0/10.6/9.5, a shortfall of roughly 91 Mandaic objects. Added `ibi deposit` for researcher-supplied documents, which archives by hash without implying a fetch or an access-control decision. No corpus writes beyond the deposit.
- **2026-09-05:** SCHOL-002 complete. Ingested the 69 publications Waller's control list named and the index lacked, citations verbatim from printed pp. 40-47, plus 17 works outside his JBA scope from the scoping review; four overlaps resolved in favour of the sourced citation. Sources 753 to 839, control-list coverage 46/115 to 115/115. Recorded explicitly that this is bibliographic presence and not object enumeration: none of those publications is linked to the bowls it publishes, which makes SCHOL-004 the binding constraint.
- **2026-09-05:** Obtained Ford and Abudraham 2018 and deposited it privately. Traced the language-distribution benchmark to its origin: Morony 2003: 87, endorsed by Ford and Abudraham n. 3 and quoted by Waller - a twenty-year-old estimate over a smaller corpus, not a current census. Corrected the attribution in the report and META-008. The chapter is not a Mandaic control list; it publishes eight confiscated bowls, so no Mandaic equivalent of Waller's JBA list is known and the denominator must be built from the corpus editions. Recorded that the volume publishes antiquities confiscated in Judea and Samaria, whose provenance is contested and must not be read as excavation context.
- **2026-09-05:** SCHOL-004 complete. Migration 012 adds an append-only publication registry separating which publication a designation belongs to from which source reported it. 16 of 18 publication keys resolved, covering 414 of 435 objects; MRLA 8 and TMH 7 left unresolved with precise blockers rather than inferred. Four keys became resolvable only because SCHOL-002 had ingested their publications. A regression test fails when any key lacks a registry entry.
- **2026-09-05:** Resolved MRLA 8 from the volume's own imprint page rather than by inference: Ford and Morgenstern, Aramaic Incantation Bowls in Museum Collections vol. 1 (Brill 2019), now in `sources`. Registry coverage 16/18 to 17/18 keys and 414 to 433 objects. TMH 7 remains unresolved pending the same check against its printed volume.
- **2026-09-05:** Added SCHOL-005 and `ibi report-acquisitions`: a generated register separating what the project holds as a document from what it merely cites, with the want list ranked by dependants. 20 of 841 sources have the document held; 347 objects depend on an unheld publication; Segal 2000 ranks first at 253 objects. Logged TMH 7 as blocked - no digital copy of Mueller-Kessler 2005 could be located, so that registry entry stays unresolved rather than inferred.
- **2026-09-06:** QA-004: reviewed Claude work against the matching corpus state. Corrected acquisition metrics that treated all captures as held documents, separated PDF presence from unassessed completeness, and deduplicated publication counts across aliases and publications (435 memberships become 423 unique candidate records). Refreshed obsolete and duplicate priorities; bibliography seeding and field-model expansion are complete, while acquisition, publication enrichment and evidence revalidation remain the next priorities. No corpus assertions changed.
- **2026-09-06:** SCHOL-005 acquisition batch: archived the complete 29-page Ford 2014 journal article from its institutional host after robots allowance and page-scope review. Added two source records and five precise follow-up leads, retained the earlier conflicting Ford 2002 author attribution, and logged seven targeted searches. Segal and Isbell remain unacquired; the JANES CDN failed robots allowance. No candidate identities, readings, media approvals or public release changed.
- **2026-09-06:** TEXT-001: enumerated AS 13, Davidovitz 27 and Museo Sefardí 1073 in the archived Ford 2014 article. Added two provisional candidates and attached one source appearance to the existing AC-MSEF record using an explicit source concordance. Registered one publication key; unique publication coverage rises from 423 to 425 records. Retained original measurement order; no reading adjudication, identity merge or rights decision. Candidate and registry replay left the corpus digest unchanged.
- **2026-09-06:** TEXT-001: indexed 14 labelled Ford 2014 discussions across 13 existing JBA records, recording short topic summaries and exact line/page pointers. Distinguished retained readings, proposals and grammatical/bibliographic commentary. Added ten missing 2013 publication-key references; unique publication coverage is 435/1,590. No objects, texts, media or identity decisions changed. New JBA 23 topic difference remains visible, taking review queue to 314. Replay left the digest unchanged.
- **2026-09-05:** Built the scholarship index: 199 works separated from the 644 museum, auction and dealer records, a scope ledger (migration 013) with 26 derived and 173 honestly unclassified, 107 contributors grouped from free-text author strings, and a decade curve plotted against Waller's control list. Fixed two contributor defects found while building it: the SCHOL-002 authors placeholder had merged Geller with Gordon and Schwab with Shaked, and bare surnames were splitting Levene and Gordon from their full names. Gordon now shows correctly at 8 works. Ranking is by publications, not citations, because only 9% of sources carry a DOI.
- **2026-09-05:** Ways in: corpus-wide search, eight counted browse axes over the content facets, and publication pages backed by a new `publications` projection table. Facets are computed client-side from the facts table so a published static export behaves identically; the API/export equivalence still holds across all 13 tables.
- **2026-09-05:** Tranche 5: restored structured filtering below 900px, where the stylesheet had been hiding every fieldset, using a native disclosure that is invisible on wide screens. Added the rights-gated image path so an approved photograph replaces the spiral automatically, with tests for approved, withheld and unreviewed. Dark mode landed earlier with the reading room. The interface plan is complete.
- **2026-09-06:** TEXT-001 access follow-through: confirmed the 2013 Aramaic Bowl Spells volume at the official publisher, where it requires purchase or institutional access, and recorded WorldCat as the authorized library route. A complete Internet Archive community upload supplies no license, rights statement or depositor-authority evidence and was not acquired or used. Opened IBI-LEAD-JBA2013-ACCESS and bound the Ford 2014 specialist-comparison lead to it; no reading comparison, identity decision, rights decision or publication was attempted.
- **2026-09-06:** TEXT-001 attribution repair: resolved the Ford 2002 discrepancy from the journal record, the author's institutional publication record and current OpenAlex metadata. Added an append-only source-correction ledger that retains the exact imported Müller-Kessler state; reclassified that row as OpenAlex metadata and attached the verified J. N. Ford article appearance to BM 91715. No full-text reading, identity merge, rights decision or publication occurred.
- **2026-09-06:** SCHOL-005: added a running publications-to-purchase register to the generated roadmap. PURCHASE-001 is Shaked, Ford and Bhayro's 2013 Aramaic Bowl Spells, Volume One, verified from the user-supplied Brill title page and linked to IBI-LEAD-JBA2013-ACCESS. Prices are checked at purchase time rather than frozen in the roadmap; authorized library or researcher-supplied access can satisfy the need without a purchase.
- **2026-09-06:** SCHOL-005 Segal 2000 access review: confirmed ISBN 0714111457 / 9780714111452 and found the complete 239-page, 159-plate catalogue in the NYPL Research Catalog as an offsite item available by advance request. New retail listings were out of stock and the visible used copy was about US$408 plus shipping, so Segal was not added to the purchase register; LED-DF20C6F96C3F is reopened with library access as the next action.
- **2026-09-06:** SCHOL-005 Library of Congress strategy: confirmed the user's LCCN records for Aramaic Bowl Spells (2013009563; both Volumes 1 and 2 available onsite) and Segal 2000 (2001369942; one copy available onsite). Continued the catalog sweep and found Isbell 1975 (75015949) and Ford–Morgenstern Volume One (2019026750) available onsite. Added an LC reading-room queue, made LC the default offline search, reopened or created the relevant access leads, and changed PURCHASE-001 to backup-only.
- **2026-09-06:** SCHOL-004 / SCHOL-005 Library of Congress priority sweep: official LCCN 2006364726 explicitly identifies Müller-Kessler 2005 as Texte und Materialien der Frau Professor Hilprecht Collection, Bd. 7, resolving the final publication key TMH 7 and replacing its blocked bibliographic lead with an onsite consultation lead. Added confirmed onsite routes for TMH 7, Moriggi 2014 and the exact 1998 third edition of Naveh–Shaked. Recorded the available 1985 first edition as an alternate only, without conflating it with the 1987 second-edition source.
- **2026-09-06:** SCHOL-006 first scope batch: reviewed the five held scholarship PDFs that remained outside derived publication-registry scopes. Classified Schwab 1891 as a corpus edition, Levene–Bhayro 2006 as a single-object edition, Kedar 2019 and Waller 2022 as thematic studies, and Waller 2025 as a synthesis. Append-only scope coverage rises from 27/198 to 32/198; 166 works remain explicitly unclassified.
- **2026-09-06:** Ingested the researcher-supplied JSQ 6 scan by content hash. Enriched the existing M163 record with dimensions, condition, line count, script, layout, provenance, sale history, edition pointers and a withheld plate reference; added Schøyen MS 2054/124 as a distinct probable Mandaic bowl from Shaked's discussion and translated excerpts. Corrected Shaked's imported 2016 date to the printed 1999 article and classified Levene as a single-object edition and Shaked as a thematic study. No modern transcription, translation or image was copied or approved for publication.
