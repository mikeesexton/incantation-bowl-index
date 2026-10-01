# Discovery campaign status

Generated: `2026-10-01T21:55:58+00:00`

## Corpus

- Candidate objects: **2059**
- Unclassified claim fields: **['adversary_or_target', 'catalogue_script', 'edition_language_and_script_label', 'photograph_credit', 'physical_or_layout_note', 'project_summary', 'publication_reference', 'reported_bowl_form', 'reported_collection_location', 'reported_date', 'reported_diameter', 'reported_dimensions', 'reported_findspot', 'reported_fragment_type', 'reported_height', 'reported_physical_condition', 'reported_writing_condition', 'source_language_or_script_label', 'supernatural_name_or_class']**
- Estimated distinct objects after resolved dedupe: **1710**
- Resolved duplicate records: **349**
- Same source duplicate identifier groups: **1**
- Same source duplicate claim groups: **0**
- Probable or confirmed: **1195**
- Source appearances: **2360**
- Sources: **955**
- Dedupe clusters pending: **0**
- Objects with text: **772**
- Objects with translation: **389**
- Objects with provenance: **163**
- Objects with current location: **877**
- Open leads: **27**
- Planned queries: **0**
- Searched queries: **328**
- Coverage targets remaining: **0**
- Qualifying saturation sweeps: **2**
- Manual audits: **14**
- Manual audit failures: **0**
- Objects without evidence: **0**

## Coverage by source class

| Source class | Planned | Searched/exhausted | Blocked |
|---|---:|---:|---:|
| article | 0 | 35 | 0 |
| auction | 0 | 35 | 0 |
| book | 0 | 34 | 0 |
| catalogue | 0 | 34 | 0 |
| chapter | 0 | 17 | 0 |
| dealer | 0 | 33 | 0 |
| excavation_report | 0 | 34 | 0 |
| museum | 0 | 29 | 0 |
| private_collection | 0 | 17 | 0 |
| scholarship | 0 | 14 | 0 |
| thesis | 0 | 34 | 0 |
| web | 0 | 12 | 0 |

## Campaign source-class targets

| Source class | Target | Status | Assessment |
|---|---|---|---|
| auction | Auction-house and auction-aggregator archives | searched | Searched major auction houses, aggregators, indexed PDFs, historical lots, current 2026 listings, alternate terminology, and sale-number/lot-number combinations. Group lots were split into distinct physical components; robots-blocked pages remain explicit leads. |
| dealer | Dealer catalogues and archived listings | searched | Searched active and indexed dealer pages, SKUs, quoted descriptions, publication references, and the Korsvoll/Brodie online-market scholarship. Disappeared or repository-blocked listings remain documented leads. |
| excavation | Excavation reports and archaeological catalogues | searched | Searched Nippur, Seleucia, Babylon, Borsippa, Kutha, Ctesiphon, Khafajah, Uruk, Nimrud, Nineveh, and related excavation publications/catalogues. Legally excavated catalogued objects were prioritized; Ottoman division-list gaps remain blocked. |
| image | Reverse image and perceptual-match leads | searched | Ran image-index queries across museum, auction, dealer, exhibition, and scholarly contexts and retained image URLs/rights metadata. Perceptual hashes are supported by the schema; systematic image hashing awaits an authorized image corpus. |
| library | Digitized books, manuscripts, and institutional repositories | searched | Searched Google Books-style indexes, HathiTrust/Internet Archive-style holdings, university repositories, NLI SRU, DOI/OpenAlex/Crossref-style metadata, dissertations, and publisher previews. Public files were captured when robots and terms permitted. |
| multilingual | Non-English discovery sweeps | searched | Ran Arabic, Hebrew, Persian, German, French, Italian, Russian, Syriac/Mandaic terminology, transliteration variants, historic collection names, and auction vocabulary. New Tehran and German-portal records were ingested; unresolved language-specific print sources remain cited. |
| museum | Museum collection catalogues and APIs | searched | Harvested NLI's 205 numbered records and searched British Museum, Penn, Met, Kelsey, Jena/Hilprecht, Berlin, Hermitage, Iraq Museum, Tehran Ābgīne, university museums, and other named collections. The LMU four-bowl project was added; aggregate-versus-item discrepancies remain blocked. |
| private_collection | Published and referenced private collections | blocked | Searched published and indexed Schøyen, Moussaieff, Jeselsohn/Kedar, Davidovitz, Wolfe/Wolf, Pearson, Gorea, Barakat, and named private holdings. Large collection-level totals cannot be converted safely into item records without catalogues or owner-authorized access. |
| restricted | Paywalled, login-only, offline, and inaccessible leads | blocked | Every encountered restriction was logged with a precise source/URL and any lawful public metadata. Authentication, paywalls, CAPTCHAs, WAFs, robots exclusions, and publisher restrictions were not bypassed. |
| scholarship | Articles, chapters, dissertations, and reviews | searched | Searched bibliography indexes, author profiles, recent 2024–2026 scholarship, reviews, theses, citation chains, and object identifiers. Newly found Moussaieff Mandaic and Tehran groups were enumerated; inaccessible full editions remain explicit leads. |
| scholarship | Foundational editions and concordances | searched | Parsed Montgomery, Segal-related museum records, Waller's open list, Schøyen publications, Levene-related designations, catalogue concordances, and citations in later literature. Conflicts are retained as claims and unresolved mappings are blocked leads. |
| web_archive | Archived and disappeared web records | blocked | Searched Internet Archive/CDX-style records and captured the surviving Virtual Magic Bowl Archive landing page. Rate limits, vanished data packages, robots exclusions, and WAF challenges prevented complete recovery; no restriction was bypassed. |

## Source access

| Access status | Sources |
|---|---:|
| available | 784 |
| unknown | 102 |
| partial | 62 |
| paywalled | 5 |
| blocked | 1 |
| offline | 1 |

## Corpus composition

| Dimension | Value | Objects |
|---|---|---:|
| object type | whole_bowl | 1333 |
| object type | fragment | 374 |
| object type | uncertain | 332 |
| object type | lost_or_unlocated | 14 |
| object type | non_bowl | 6 |
| record status | probable | 922 |
| record status | candidate | 857 |
| record status | confirmed | 273 |
| record status | rejected | 7 |
| authenticity | unassessed | 1525 |
| authenticity | accepted | 441 |
| authenticity | pseudo_script | 88 |
| authenticity | uncertain | 3 |
| authenticity | disputed | 1 |
| authenticity | suspected_fake | 1 |

## Acceptance checks

- [x] Every object has source evidence
- [x] No planned queries remain
- [x] No coverage targets remain
- [ ] No open leads remain
- [x] Two independent saturation sweeps qualify
- [x] Stratified manual audit has at least twelve records
- [x] Manual audit has no failures

## Saturation

Campaign saturation requires two independent broad sweeps, each adding less than 1% net-new probable physical objects and revealing no new source class.

| Sweep | Strategy | Baseline | Net new | Rate | New class |
|---|---|---:|---:|---:|---:|
| Current-scholarship and first-edition sweep | Independent 2023–2026 DOI, journal, repository, author-profile, first-edition, and previously-unpublished phrase search in English and Hebrew, followed by exact object-identifier comparison. | 1346 | 3 | 0.22% | no |
| Auction and dealer market sweep | Independent broad and exact-phrase sweep of auction houses, aggregators, dealers, historical results, current listings, group lots, dimensions, provenance phrases, and pseudo-script vocabulary. | 1349 | 8 | 0.59% | no |

## Manual audit

| Stratum | Result | Records |
|---|---|---:|
| auction and scholarship | pass | 1 |
| auction record | pass | 1 |
| disputed or modern alteration | pass_with_notes | 1 |
| excavated fragment | pass | 1 |
| excavation context | pass | 1 |
| fragment | pass | 1 |
| museum catalogue | pass | 2 |
| museum pseudo-script | pass | 1 |
| pseudo-script market record | pass_with_notes | 1 |
| scholarly publication | pass | 1 |
| scholarly publication | pass_with_notes | 1 |
| suspected fake | pass_with_notes | 1 |
| uncertain aggregate component | pass_with_notes | 1 |

## Unresolved or access-blocked leads

| Status | Priority | Lead |
|---|---:|---|
| open | 1 | Acquire a lawful full private PDF capture of Abudraham 2026, Bridging the Gaps; separately extract AIT27/B16041’s central synoptic column (pp. 111–116), photograph/drawing (pp. 119–120), and the comparative translation and relevant variants (pp. 120–123). Preserve NLI-vs-AIT27 personal names and lacunae; do not relabel the whole common translation as AIT27-specific. |
| blocked | 1 | BM 117882 / Segal 119ES: inspect the full catalogue entry to assess the uncertain Syriac? classification against existing museum descriptions of Syriac. The apparent 117ES/119ES locator mismatch has been resolved as an importer defect; identity links remain unchanged. |
| in_progress | 1 | Investigate Penn B2963 / Montgomery 3 Date Made: ca. 200 BCE. The value is preserved as a museum-reported claim, not accepted as a corrected chronology. Check primary catalogue dating and later scholarship; do not infer a replacement date. |
| in_progress | 1 | Reconcile Penn B9010 / Montgomery 9 Inscription Language: Hebrew Language with the edition-based Jewish Babylonian Aramaic claim. Determine whether the catalogue field reflects historical terminology, a script/language confusion or an error; preserve both assertions pending review. |
| in_progress | 1 | Reconcile Penn B9008 / Montgomery 31 Inscription Language: Hebrew Language with the existing Syriac attribution. The museum description also says Proto-Manichean. Distinguish language from script and catalogue terminology; retain disagreement. |
| open | 1 | Reconcile BM 91711 / N-1847's reported Arban findspot with Waller's assessment that the accessions-register attribution to Layard is plausible but unverified. Check the original museum register, Layard's excavation account, the published prospectus, and any later object-specific scholarship before changing the findspot status. |
| in_progress | 1 | Classify corpus findspot and provenance assertions by evidence basis: documented controlled excavation, museum or accessions register, dealer or antiquities-market report, later scholarly inference, or unverified/unknown. Preserve the original place claim and its source separately from the assessment. |
| in_progress | 1 | Complete the concordance for the controlled French-excavation Susa group: map Schwab 1891 N–P to current museum numbers, later editions, language/script assessments, and any more precise find contexts. Preserve the contemporary Susiana mission report separately from later Susa normalization. |
| blocked | 1 | Retrieve the preserved Virtual Magic Bowl Archive data package and enumerate all item records once either Open Research Exeter or the Internet Archive permits access. |
| open | 1 | Find publication or collection concordances for the 74 NLI digital records labelled IAA Bowl 1–74 and determine overlap with previously indexed objects. |
| in_progress | 1 | Map the seven Avigdor Klagsbald donation bowls to exact NLI catalogue/manuscript identifiers and determine which overlap the 205 harvested NLI SRU records. |
| blocked | 1 | The National Library of Israel exhibition material highlights two bowls for Kafnai son of Imma (with Immai daughter of Anai) and Hai son of Aspindarmid. Resolve their names to the exact MMS and manuscript-part records among the 205 numbered NLI bowls already collected before adding appearances or claims. |
| blocked | 1 | Penn Museum robots.txt was unavailable; metadata was collected slowly, but full page captures were not archived. |
| blocked | 1 | Obtain authorized access to the complete Segal 2000 catalogue; the openly indexed PDF located during discovery is only a two-page title/contents preview. |
| open | 1 | Reconcile NLI Ms. Heb. 6079=34 (MMS 990026405980205171) with the existing JNL Heb 4, 6079 and Naveh–Shaked 1985 Bowl 12a records. |
| in_progress | 1 | Reconcile the National Library of Israel exhibition statement that 216 Moussaieff incantation bowls were donated with the 205 numbered incantation-bowl SRU records harvested in this campaign. |
| blocked | 2 | Obtain an authorized local copy of Ford 2002, Another Look at Mandaic Incantation Bowl BM 91715, JANES 29, pp. 31–47. |
| open | 2 | Review whether provisional Davidovitz 27 (IBI-FORD2014-DAV27) has another source appearance under a different designation, including the existing Davidovitz popularity-and-success bowl IBI-6A5B95130C25. |
| open | 2 | Review Ford 2014 proposed readings and interpretations against the 2013 edition and relevant photographs, using the 14-discussion index; preserve differences as attributed evidence. |
| open | 2 | Hunter 2021's section on Nippur seasons names additional excavated or surface-find candidates absent from the index by exact field number: 18N71 (Mandaic bowl fragment), 18N99 (incomplete Mandaic bowl), 18N100 (incomplete Aramaic bowl with traces of characters), 11N7, 11N8 and 11N9 (bowl sherds), 11N77 and 11N78 (whole bowls), 11N104 (fragment with pseudo script), 12N387 (rim sherd), and 4N17 and 4N72 (incomplete pseudo-script bowls). Verify each against the chapter's printed pages and cited excavation catalogues, then ingest distinct source appearances and object candidates where appropriate. The chapter also mentions 18N70, an ostracon with pseudo script; assess scope separately rather than treating it as a bowl. |
| in_progress | 2 | Obtain authorized access to Isbell 1975, Corpus of the Aramaic Incantation Bowls, for page-level edition checks. |
| open | 2 | Kedar 2019 states that ten bowls were unpublished when she wrote: JNF 18, JNF 125, JNF 149, JNF 152, JNF 153 and JNF 188 ('unpublished texts by James Nathan Ford', p. 134 n. 546), Wolf 69 and CBS 85-48-914 (p. 105 n. 434), Wolf 23 (p. 135) and Davidovitz 2 ('being prepared for publishing by James Nathan Ford', p. 102 n. 410). Check Ford's and others' publications since 2019 (Ford published JNF 124 in 2016 and Davidovitz 41 in 2023). Any bowl still unpublished could become the corpus's first sourced no-known-edition finding, but a 2019 statement is dated evidence: decide the policy before recording one. |
| open | 2 | Investigate Montgomery 1913 appendix no. 42: locate Gottheil's original notes or later scholarship assessing whether the unlocated original was a bowl or another amulet. Do not assign a Nippur findspot, ancient date, CBS number or physical identity from the main forty-bowl corpus. |
| in_progress | 2 | Map the nine Mandaic bowls of Morgenstern 2012's preliminary survey to their editions. Five are edited in Morgenstern, 'Five Mandaic Magic Bowls from the Moussaieff Collection', Eretz-Israel 34 (2021): 106-122 (source SRC-553965D06B17); the rest in Morgenstern and Abudraham, 'Additional Mandaic Magic Bowls from the Moussaieff Collection', Mehqarim be-Lashon (Hebrew; listed as forthcoming on the author's page, reported elsewhere in the corpus as 2025). Seven survey identities are unlinked in TEXT-001: M23, M25, M26, M139, M154 and unnumbered A and B. Obtain the tables of contents or first pages before linking any bowl. |
| blocked | 2 | Obtain a complete authorized copy of Naveh and Shaked 1993, Magic Spells and Formulae, for object-level indexing. |
| in_progress | 2 | Consult the 1998 third edition of Naveh and Shaked, Amulets and Magic Bowls, through the Library of Congress for object-level edition indexing. |
| open | 2 | Two source records describe the same article: SRC-69C22D670211 (2005) and SRC-A84A167A5779 (2006). Archiv fuer Orientforschung 51 is a 2005/2006 volume, which explains the split. Reconcile to one record with the correct year and page range, keeping both citations in history. |
| in_progress | 2 | Consult Müller-Kessler 2005, TMH 7, through the Library of Congress for object-level edition indexing. |
| in_progress | 2 | Consult Yamauchi 1967, Mandaic Incantation Texts, for a page-level Mandaic text census and object indexing. |
| open | 2 | Penn B2970 (object 79917): obtain any inscription edition or curatorial documentation; current museum bibliography is empty, but the object has 13 reported interior lines and two images. |
| open | 2 | Acquire Geller, Four Aramaic Incantation Bowls, The Bible World (1980), pp. 47–60, and check bowl D against index designation GelD; establish museum accession and location without guessing a concordance. |
| open | 2 | Berlin VA.2451: seek later publication, legible imaging or curatorial documentation after the 2018 catalogue's dated unpublished and nearly-illegible reports. |
| open | 2 | Locate an edition or additional documentation for Penn B16038 (object 151160). The web-visible catalogue checked 2026-10-01 lists no bibliography; targeted searches for B16038 with bowl, incantation, Montgomery and Nippur found its museum record but no new edition. This is a dated search disposition, not a global no-known-edition finding. The page lists five image views; only the pre-existing primary thumbnail is currently recorded in the corpus. |
| blocked | 2 | Map Morgenstern's 2021 five-bowl edition and Morgenstern–Abudraham's 2025 four-bowl edition exactly onto the nine Mandaic objects M23, M24, M25, M26, M45, M139, M154, unnumbered A, and unnumbered B; capture the full texts and translations through authorized access. |
| blocked | 2 | Obtain authorized full-text access to Faraj 2023 to capture the edition, translation, dimensions, provenance details, and imagery for IM 77781. |
| blocked | 2 | Obtain LMU Archaeology Museum accession numbers and item-level provenance, dimensions, scripts, texts, translations, images, and 3D records for the four-bowl project. |
| blocked | 2 | Locate the Nippur bowls retained by the Imperial Museum at Constantinople, as reported by Montgomery on p. 15. |
| open | 3 | Obtain the complete Hannu Juusola 1999, Linguistic Peculiarities in the Aramaic Magic Bowl Texts, for controlled language and orthography normalization. |
| blocked | 3 | Obtain authorized access to Mokhtarian 2015, Rabbis, Sorcerers, Kings, and Priests, for contextual enrichment. |
| blocked | 3 | Preserve a private content-addressed capture of the Menil Collection record for incantation bowl X 831 if later permitted or supplied through authorized access. |
| blocked | 3 | Reconstruct Kedar's unenumerated analytical sample of 296 published JBA bowls from the dissertation's citations and working materials. |
| blocked | 3 | Verify every Apotropaic Arts designation and concordance against its cited primary edition. |
| blocked | 3 | Acquire and extract Waller's 2025 state-of-the-art chapter and its complete list of JBA bowl publications (1853–2024), then diff every listed object and bibliography entry against the corpus. |
| blocked | 3 | Locate publication or authorized research access for Davidovitz 2, Wolf 23, Wolf 69, CBS 85-48-914, and JNF 18/125/149/152/153/188. |
| blocked | 3 | Obtain authorized access to Fain, Ford, and Lyavdansky 2016 and resolve all eleven State Hermitage inventory numbers, texts, translations, and concordances; open metadata currently identifies S-442, S-444, S-446, S-447, and S-448, leaving six objects unresolved. |
| blocked | 3 | Deutsch Auction 69 bowl located as Bidspirit record 87924; resolve its printed lot number, sale result, provenance, images, and earlier/later appearances. |
| blocked | 3 | Enumerate and distinguish every bowl, fragment, skull, bone fragment, and eggshell among the 177 entries in the 2018 Vorderasiatisches Museum catalogue; do not treat the aggregate as 177 bowls. |
| blocked | 3 | Extract the item-level June 2019 gallery and auction corpus, earlier sale concordances, object descriptions, and provenance claims from Korsvoll 2020. |
| blocked | 3 | Extract every 2019 dealer listing and concordance from Korsvoll's online-market survey; current search snippets confirm Barakat SKUs X.0552 and LO.769 and the article compares these with Brodie's 2006 survey. |
| blocked | 3 | Reconcile the Schøyen overview's aggregate 654 Jewish-Aramaic bowls and jugs with individually identifiable MS records and the seven-volume publication programme. |
| blocked | 3 | Reconcile all 142 Segal text numbers to British Museum registration and museum numbers using the catalogue concordance and current collection pages. |
| blocked | 3 | Archive the two Bidsquare/Artemis auction appearance pages after robots policy permits automated capture; metadata and stable item identifiers are already recorded. |
| blocked | 3 | Identify and account for the difference between the 142 numbered texts and the 159 objects currently related to Segal 2000 on the British Museum site. |
| blocked | 3 | Extract the five Ābgīne Museum catalogue numbers, inscriptions, translations, dimensions, provenances, and concordances from Šafiʿī 2025 through authorized access or precise secondary citations. |
| blocked | 3 | Reconcile Montgomery's statement that the University Museum catalogue held over 150 numbered bowls/fragments, including roughly 30 pseudo-inscribed examples, against the current Penn Museum database. |
| blocked | 3 | Resolve Kedar's numerical discrepancy: the text says Dukhtīč wrote ten bowls total, while note 546 appears to name ten parallels in addition to Davidovitz 2. |

## Interpretation and limitations

This is a maximum-recall discovery corpus, not a claim that every surviving bowl has been individually enumerated. The estimated-distinct count collapses only reviewed exact matches; the pending similarity queue deliberately preserves uncertain possible duplicates.

Major residual gaps are explicit above. They include inaccessible or only partially indexed print catalogues, unnumbered objects in private collections, collection-level totals that cannot safely be expanded into item records, and copyrighted full texts or translations that require authorized access. Blocked leads remain actionable research records rather than silently disappearing from coverage.

The public dashboard should publish only reviewed claims and rights-cleared text or media. The private working corpus can retain bibliographic and archival evidence with its rights metadata.