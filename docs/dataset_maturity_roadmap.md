# Incantation Bowl Index: dataset maturity roadmap

> Living document generated from `research/roadmap/dataset_maturity.json` and the private corpus. Update task status or add newly discovered gaps in the JSON register, then run `ibi roadmap`.

Generated: `2026-09-06T01:01:10+00:00`

## Portfolio status

Current phase: **Source-rich research corpus with one completed reference cohort; active reconciliation and enrichment; not release-ready**

| Progress measure | Current |
|---|---:|
| Roadmap tasks | 17 done · 14 in progress · 18 queued · 0 blocked |
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
- Publications are first-class: a bowl can be asked which edition publishes it, separately from which source reported the designation. 18 of 19 publication keys resolve, covering 435 distinct candidate records; TMH 7 remains unresolved. Counts deduplicate records across aliases and publications.

### What prevents release readiness

- Publication links exist but are thin: 435 of 1,590 distinct candidate records carry a publication key, and all 435 have at least one resolved publication. This does not resolve every key: the two TMH 7 records also carry resolved keys. Most records still have no publication key.
- Identity and claim quality is not yet measured corpus-wide: 314 field-difference decisions need evidence-level revalidation, now measured against the full claim vocabulary rather than seven hard-coded groups, findspot claims are not yet consistently graded by evidence basis, and a reproducible stratified identity audit has not begun.
- Text and edition coverage remains sparse outside Montgomery: 312/794 probable or confirmed identities have a publication-scheme reference, still only a proxy for a checked edition locator; just one identity has a recorded transcription or transliteration.
- Release rights are unreviewed: all 325 media rows have inventory holds, but zero have completed rights decisions and zero are approved for reuse.
- The National Library of Israel, Schøyen, broader Penn, and remaining British Museum/Segal concordances are incomplete; continuous operations, encrypted off-device backup, and a 14-day shadow run are not set up.
- Acquisition completeness is not yet measured corpus-wide: 21 sources have captures, ten with PDFs and eleven with only non-PDF captures. Ford 2014 now has a hash-bound complete-article scope review covering all 29 pages (235–263); this does not certify its readings. 355 distinct candidate records depend on publications without linked PDF captures; Segal 2000 remains the largest acquisition lead at 252 records.

## Current scope snapshot

| Measure | Current |
|---|---:|
| Candidate source records | 1590 |
| Working physical identity hypotheses (all statuses) | 1322 |
| Source appearances | 1632 |
| Sources | 843 |
| Pending dedupe decisions | 0 |
| Identities triggering raw claim-difference flags | 215 |
| Triaged claim-field differences | 53/367 |
| Compatible differences | 38 |
| Review required (missing or no longer valid) | 314 |
| Existing reviews requiring revalidation | 284 |
| Substantive conflict instances | 15 across 13 identities |
| All identities with a publication reference | 393/1322 (29.7%) |
| Probable/confirmed identities with a publication reference | 312/794 (39.3%) |
| Identities with a translation | 48 |
| Scan-checked normalized reading texts | 35 |
| Publication keys resolved to the publication they designate | 18/19 |
| Objects under a resolved publication | 435/435 |
| Montgomery/Penn concordances with dated current-evidence review | 40 |
| Source-reported object relationships / unresolved scope | 5 / 4 |
| Identities with a transcription/transliteration | 1 |
| Media records with a non-unknown rights status | 37/325 (11.4%) |
| Media with a current ledger entry | 325/325 |
| Media with completed rights decisions / approved for reuse | 0 / 0 |
| Blocked leads | 31 |
| Open or active leads | 10 |
| Qualifying discovery-saturation sweeps | 2 |

Coverage means a field or reference is present, not independently verified. Publication coverage currently uses identifier schemes as a proxy. A non-unknown rights label is not a reviewed public-reuse decision. Discovery saturation applies only to the logged searches and does not estimate global completeness.

### Identity-level field coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 910 | 68.8% |
| Provenance | 327 | 24.7% |
| Dating | 482 | 36.5% |
| Dimensions | 380 | 28.7% |
| Material | 408 | 30.9% |
| Language | 663 | 50.2% |
| Script | 91 | 6.9% |
| Text Edition | 1 | 0.1% |
| Translation | 48 | 3.6% |
| Image | 324 | 24.5% |

### Content-facet coverage

The scoping review's People, Ritual, Intertexts, Visual and Scholarship groups. These are counted and conflict-checked but are not release gates.

| Facet | Identities | Coverage |
|---|---:|---:|
| Biblical Intertexts | 168 | 12.7% |
| Condition | 139 | 10.5% |
| Publication | 78 | 5.9% |
| Client | 58 | 4.4% |
| Ritual | 43 | 3.3% |
| Text Form | 36 | 2.7% |
| Practitioner | 29 | 2.2% |
| Visual | 27 | 2.0% |
| Text Description | 19 | 1.4% |
| Authenticity Assessment | 4 | 0.3% |
| Parallels | 4 | 0.3% |
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
| SCHOL | Scholarly bibliography and published-corpus enumeration | L2 | L3 | Research |
| META | Physical, chronological, linguistic, and provenance enrichment | L1 | L3 | Mixed |
| RIGHTS | Images and rights | L1 | L4 | Human rights review |
| OPS | Mac mini continuous operations | L0 | L5 | Mac mini after 2026-09-22 |
| QA | Evidence quality and regression controls | L2 | L3 | Research and engineering |

## Current priority order

1. TEXT-001 / SCHOL-004 follow-through: extend evidence-backed publication references beyond the current 435 of 1,590 distinct candidate records. Enumerate object-level coverage for the 69 bibliography additions; some now resolve existing keys, so do not assume all are unattached.
2. SCHOL-005 / QA-004: work the acquisition queue from Segal 2000 (252 distinct candidate records) and record document scope against archived evidence. Distinguish full works, excerpts, front matter and catalogue pages before calling a publication held or read.
3. TEXT-001 follow-through: Ford 2014 editions and all 14 main JBA-labelled commentary discussions are indexed. Obtain the 2013 edition for specialist comparison, review provisional-candidate concordances, and resolve the Ford 2002 author-attribution discrepancy while retaining earlier citations.
4. QA-002 / CONC-005: revalidate the 314-case queue in coherent source batches, including 284 earlier reviews. Preserve reported values and uncertainty; claim-vocabulary coverage is now complete.
5. META-008: assemble a Mandaic denominator from corpus editions represented in the bibliography. The earlier 23% expectation is Morony's historical estimate, not a collection target; no dedicated control list has yet been identified by this project.
6. META-002 / META-003: continue the B2963 object-specific dating investigation and inspect original scripts for Montgomery 9 and 31 before assigning language source errors. The relationship and measurement anomaly reviews are complete at the available evidence level.
7. META-005: apply Waller's evidence-basis distinction to the location corpus, starting with claims labelled Excavated/Findspot and the Susa controlled-excavation group. Preserve museum and market claims as reports rather than silently upgrading them to archaeological facts.
8. TEXT-006 / TEXT-003: obtain independent review of all 35 checked English reading texts, particularly magical formulas and restorations, then develop a checked original-script transcription/transliteration pilot. The first English scan-review pass is complete.
9. CONC-002: extend beyond the completed forty-entry reference cohort to reconcile the remaining Penn holdings and historical inventory. Check precise identifiers and publication references; do not generalize the 40/40 result to the broader collection.
10. QA-003: select and audit a reproducible stratified sample before assigning an overall accuracy percentage. The forty-entry Montgomery source audit is useful but not representative of the entire corpus.
11. RIGHTS-002: investigate evidence for the 325 media holds, starting with shared institutional policies. Zero media have completed rights decisions; agents collect evidence for human review.
12. TEXT-001 / QA-004: align edition-reference and field-assessment metrics with cited evidence; then extend the checked institutional cohorts.
13. DISC-002: pursue precise source gaps, including IBI-LEAD-MONT42 and authorized Segal catalogue access; defer another undirected discovery expansion.
14. OPS: document restore and collector controls for the Mac mini. A local database backup was restore-checked; encryption, off-device backup and shadow operation remain outstanding.

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
  - Evidence/status: 312/791 probable/confirmed identities have publication-scheme identifiers (39.4%). This proxy counts designations, not editions: the publications being designated have no records of their own (see SCHOL-004), so raising the number does not yet raise edition coverage. Re-specify the metric against resolved publication records and sourced no-known-edition assessments before treating it as a release gate. SCHOL-004 is now done, so the metric can be re-specified: 414 of 435 objects carrying a publication key sit under a publication with a source record. That is still designation coverage, not a checked edition locator, but the denominator is now meaningful. On 2026-09-06 Ford 2014 added three precisely located edition appearances and a registered publication key: AS 13 and Davidovitz 27 are new provisional candidates, while Museo Sefardí 1073 attaches to existing AC-MSEF via the explicit p. 253 n. 56 concordance. Unique candidate publication coverage is now 425/1,590, with 18/19 keys resolved. No scholarly text or images were republished. A second Ford 2014 batch indexed all 14 bold JBA-labelled main commentary discussions on pp. 236–246 across 13 existing records, with no new identity decisions. Ten missing 2013-volume publication keys were added, raising unique candidate coverage to 435/1,590. Retained readings and grammatical comments are distinguished from correction proposals; no preferred text was chosen.
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
  - Evidence/status: Migration 012 adds an append-only publication registry recording which publication a designation belongs to, separately from `identifiers.source_id`, which correctly records who reported it. Eighteen publication keys cover 423 distinct candidate records; 17 keys resolve, covering all 423 via at least one resolved key. TMH 7 remains unresolved for two records that also have resolved keys. The earlier 435/433 totals counted overlapping memberships rather than unique records; QA-004 corrected this on 2026-09-06. MRLA 8 was resolved on 2026-09-05 from the volume's own imprint page - 'magical and religious literature of late antiquity 8', ISSN 2211-016X volume 8, ISBN 978-90-04-37700-4 - superseding the earlier unresolved decision; Ford and Morgenstern 2019 is now in `sources`. TMH 7's candidate SRC-63345F60155B (Mueller-Kessler 2005) is plausible but inferred from the series name rather than verified against the volume. Four keys - Isbell 1975, Naveh-Shaked 1993, Naveh-Shaked 1985/1993 and Gorea 2003 - became resolvable only because SCHOL-002 ingested their publications. `unresolved_publication_keys` and tests/test_publications.py fail when a key has no registry entry; the roadmap reports both counts.
- [ ] **SCHOL-005 — Keep an acquisition register and work the want list** · In progress · Mixed
  - Done when: Every source record shows whether the document is held, and the want list is ranked by how much of the corpus depends on each unread work. Works with dependants are either held, or carry a documented reason they cannot be obtained.
  - Evidence/status: `ibi report-acquisitions` inventories captures separately from completeness. QA-004 corrected the original held-document metric: 20 of 841 sources have captures, nine with PDFs and eleven with only non-PDF captures. All completeness states are unassessed by this report, including PDFs that may be excerpts. 670 sources with dependants have no PDF capture; 345 distinct candidate records depend on publications without PDFs. Segal 2000 ranks first at 252 distinct records, 142 appearances and 142 claims. Acquisition completeness needs evidence-bound review; a MIME type cannot certify that a work has been read. TMH 7 remains blocked pending the printed volume evidence (IBI-LEAD-TMH7-MUELLER-KESSLER). On 2026-09-06 a targeted acquisition pass archived Ford 2014, Aula Orientalis 32/2: 235–263 (29 scanned pages; SHA-256 0b7f1780d434...), after reviewing all page images for article scope. See research/acquisitions/edition_access_2026-09-06.json. Capture inventory is now 21/843 sources, ten with PDFs. AS 13, Davidovitz 27 and Museo Sefardí 1073 edition sections are queued with locators. Segal preview remains two pages; Isbell Internet Archive is access-restricted. Ford 2002 publisher metadata was located but its current PDF host failed robots allowance; the publisher author attribution conflicts with an earlier source record and is flagged without overwriting it.

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
  - Evidence/status: Current full-vocabulary queue: 367 field-difference instances, 53 with current decisions, 314 needing review; 284 of those have earlier reviews requiring revalidation. Use coherent source batches and exact current evidence. Museum concordance confirmation does not adjudicate metadata. The Ford 2014 Toledo bibliography/concordance pair adds one publication-group flag; it has not been adjudicated. The two JBA 23 commentary topics add a text-description difference; it remains unreviewed.
- [ ] **QA-003 — Audit a stratified sample of identity and extraction decisions** · Queued · Research
  - Done when: Publish reproducible sample selection across institutions, market records, status classes and merge methods; check primary evidence and report denominators, error categories and uncertainty.
  - Evidence/status: Zero generated pending dedupe candidates is queue completion, not measured identity accuracy. Current review examined architecture, integrity, archive hashes, aggregate metrics and selected rule evidence, not all objects.
- [ ] **QA-004 — Separate presence, assessment, verification and source coverage metrics** · In progress · Mixed
  - Done when: Track field assessment and verification independently of presence; distinguish excavation provenance from production region and ownership; reconcile item-level denominators for major sources; align publication and rights gates with reviewed evidence.
  - Evidence/status: Roadmap now separates 325 media ledger holds from 0 completed rights assessments and 0 public approvals, and counts 35 current scan-checked reading texts separately from text presence. Main Montgomery denominator is explicit: 40 entries, 35 translations and 5 documented absences in this edition. General field-assessment and edition-reference metrics still need work. Forty current-evidence museum concordance reviews are now counted separately from existing identity links; observations retain review dates and do not certify unchanged live websites or unrelated metadata. On 2026-09-06 acquisition reporting was corrected to separate any capture, PDF capture and unassessed document completeness. Publication and acquisition totals now count unique candidate records rather than identifiers or summed memberships. Regression tests cover aliases, overlapping publications, non-PDF captures and excerpts. Completeness review remains outstanding.
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

## Mac mini handoff gate

Target availability: **2026-09-22**. This is an operational eligibility date, not an automatic permission to publish or to make scholarly judgments.

Overall gate: **NOT READY**

### Quantitative conditions

- [x] No unreviewed generated dedupe candidates — current `0`; target `<= 0`.
- [ ] Every generated claim-difference flag has a recorded triage — current `314`; target `<= 0`.
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
