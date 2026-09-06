# Discovery campaign status

Generated: `2026-09-06T00:36:40+00:00`

## Corpus

- Candidate objects: **1588**
- Unclassified claim fields: **[]**
- Estimated distinct objects after resolved dedupe: **1320**
- Resolved duplicate records: **268**
- Probable or confirmed: **872**
- Source appearances: **1616**
- Sources: **843**
- Dedupe clusters pending: **0**
- Objects with text: **193**
- Objects with translation: **49**
- Objects with provenance: **162**
- Objects with current location: **793**
- Open leads: **10**
- Planned queries: **0**
- Searched queries: **321**
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
| museum | 0 | 28 | 0 |
| private_collection | 0 | 17 | 0 |
| scholarship | 0 | 8 | 0 |
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
| available | 662 |
| unknown | 123 |
| partial | 54 |
| paywalled | 3 |
| blocked | 1 |

## Corpus composition

| Dimension | Value | Objects |
|---|---|---:|
| object type | whole_bowl | 1020 |
| object type | uncertain | 295 |
| object type | fragment | 259 |
| object type | lost_or_unlocated | 14 |
| record status | candidate | 716 |
| record status | probable | 599 |
| record status | confirmed | 273 |
| authenticity | unassessed | 1098 |
| authenticity | accepted | 441 |
| authenticity | pseudo_script | 44 |
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
| blocked | 1 | BM 117882 / Segal 119ES: inspect the full catalogue entry to assess the uncertain Syriac? classification against existing museum descriptions of Syriac. The apparent 117ES/119ES locator mismatch has been resolved as an importer defect; identity links remain unchanged. |
| open | 1 | Reconcile the author attribution for Another Look at Mandaic Incantation Bowl BM 91715: existing SRC-1EE58A703971 names Christa Müller-Kessler, while the JANES volume 29 and article pages name J. N. Ford. |
| open | 1 | Enumerate and concordance-check the editions in Ford 2014: AS 13 (Appendix 1, pp. 246–252), Davidovitz 27 (Appendix 2, pp. 253–258), and Museo Sefardí 1073 (re-edition p. 256; photographs pp. 259–260). |
| in_progress | 1 | Investigate Penn B2963 / Montgomery 3 Date Made: ca. 200 BCE. The value is preserved as a museum-reported claim, not accepted as a corrected chronology. Check primary catalogue dating and later scholarship; do not infer a replacement date. |
| in_progress | 1 | Reconcile Penn B9010 / Montgomery 9 Inscription Language: Hebrew Language with the edition-based Jewish Babylonian Aramaic claim. Determine whether the catalogue field reflects historical terminology, a script/language confusion or an error; preserve both assertions pending review. |
| in_progress | 1 | Reconcile Penn B9008 / Montgomery 31 Inscription Language: Hebrew Language with the existing Syriac attribution. The museum description also says Proto-Manichean. Distinguish language from script and catalogue terminology; retain disagreement. |
| open | 1 | Reconcile BM 91711 / N-1847's reported Arban findspot with Waller's assessment that the accessions-register attribution to Layard is plausible but unverified. Check the original museum register, Layard's excavation account, the published prospectus, and any later object-specific scholarship before changing the findspot status. |
| in_progress | 1 | Classify corpus findspot and provenance assertions by evidence basis: documented controlled excavation, museum or accessions register, dealer or antiquities-market report, later scholarly inference, or unverified/unknown. Preserve the original place claim and its source separately from the assessment. |
| in_progress | 1 | Complete the concordance for the controlled French-excavation Susa group: map Schwab 1891 N–P to current museum numbers, later editions, language/script assessments, and any more precise find contexts. Preserve the contemporary Susiana mission report separately from later Susa normalization. |
| blocked | 1 | Retrieve the preserved Virtual Magic Bowl Archive data package and enumerate all item records once either Open Research Exeter or the Internet Archive permits access. |
| blocked | 1 | The National Library of Israel exhibition material highlights two bowls for Kafnai son of Imma (with Immai daughter of Anai) and Hai son of Aspindarmid. Resolve their names to the exact MMS and manuscript-part records among the 205 numbered NLI bowls already collected before adding appearances or claims. |
| blocked | 1 | Penn Museum robots.txt was unavailable; metadata was collected slowly, but full page captures were not archived. |
| blocked | 2 | Obtain an authorized local copy of Ford 2002, Another Look at Mandaic Incantation Bowl BM 91715, JANES 29, pp. 31–47. |
| open | 2 | Index Ford 2014 corrections to Aramaic Bowl Spells volume 1 as separate source-reported claims with precise locators; retain the original edition readings and uncertainty. |
| blocked | 2 | Obtain authorized access to Isbell 1975, Corpus of the Aramaic Incantation Bowls, for page-level edition checks. |
| open | 2 | Investigate Montgomery 1913 appendix no. 42: locate Gottheil's original notes or later scholarship assessing whether the unlocated original was a bowl or another amulet. Do not assign a Nippur findspot, ancient date, CBS number or physical identity from the main forty-bowl corpus. |
| blocked | 2 | Obtain Christa Mueller-Kessler, Die Zauberschalentexte in der Hilprecht-Sammlung, Jena (TMH 7, Harrassowitz 2005), or at minimum a photograph of its title and imprint pages. Needed to confirm that the publication key TMH 7 designates this volume; two objects currently hang on an unresolved key, and the identification is presently an inference from the series name alone. Searched on 2026-09-05: no digital copy located. |
| blocked | 2 | Map Morgenstern's 2021 five-bowl edition and Morgenstern–Abudraham's 2025 four-bowl edition exactly onto the nine Mandaic objects M23, M24, M25, M26, M45, M139, M154, unnumbered A, and unnumbered B; capture the full texts and translations through authorized access. |
| blocked | 2 | Obtain authorized full-text access to Faraj 2023 to capture the edition, translation, dimensions, provenance details, and imagery for IM 77781. |
| blocked | 2 | Map the seven Avigdor Klagsbald donation bowls to exact NLI catalogue/manuscript identifiers and determine which overlap the 205 harvested NLI SRU records. |
| blocked | 2 | Obtain LMU Archaeology Museum accession numbers and item-level provenance, dimensions, scripts, texts, translations, images, and 3D records for the four-bowl project. |
| blocked | 2 | Locate the Nippur bowls retained by the Imperial Museum at Constantinople, as reported by Montgomery on p. 15. |
| blocked | 2 | Reconcile the National Library of Israel exhibition statement that 216 Moussaieff incantation bowls were donated with the 205 numbered incantation-bowl SRU records harvested in this campaign. |
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
| blocked | 3 | Obtain authorized access to the complete Segal 2000 catalogue; the openly indexed PDF located during discovery is only a two-page title/contents preview. |
| blocked | 3 | Extract the five Ābgīne Museum catalogue numbers, inscriptions, translations, dimensions, provenances, and concordances from Šafiʿī 2025 through authorized access or precise secondary citations. |
| blocked | 3 | Reconcile Montgomery's statement that the University Museum catalogue held over 150 numbered bowls/fragments, including roughly 30 pseudo-inscribed examples, against the current Penn Museum database. |
| blocked | 3 | Resolve Kedar's numerical discrepancy: the text says Dukhtīč wrote ten bowls total, while note 546 appears to name ten parallels in addition to Davidovitz 2. |

## Interpretation and limitations

This is a maximum-recall discovery corpus, not a claim that every surviving bowl has been individually enumerated. The estimated-distinct count collapses only reviewed exact matches; the pending similarity queue deliberately preserves uncertain possible duplicates.

Major residual gaps are explicit above. They include inaccessible or only partially indexed print catalogues, unnumbered objects in private collections, collection-level totals that cannot safely be expanded into item records, and copyrighted full texts or translations that require authorized access. Blocked leads remain actionable research records rather than silently disappearing from coverage.

The public dashboard should publish only reviewed claims and rights-cleared text or media. The private working corpus can retain bibliographic and archival evidence with its rights metadata.