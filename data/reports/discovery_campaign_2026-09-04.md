# Discovery campaign status

Generated: `2026-09-04T16:28:35+00:00`

## Corpus

- Candidate objects: **1584**
- Estimated distinct objects after resolved dedupe: **1357**
- Resolved duplicate records: **227**
- Probable or confirmed: **869**
- Source appearances: **1586**
- Sources: **730**
- Dedupe clusters pending: **34351**
- Objects with text: **158**
- Objects with translation: **14**
- Objects with provenance: **159**
- Objects with current location: **793**
- Open leads: **0**
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
| available | 637 |
| partial | 48 |
| unknown | 41 |
| paywalled | 3 |
| blocked | 1 |

## Corpus composition

| Dimension | Value | Objects |
|---|---|---:|
| object type | whole_bowl | 1017 |
| object type | uncertain | 294 |
| object type | fragment | 259 |
| object type | lost_or_unlocated | 14 |
| record status | candidate | 715 |
| record status | probable | 596 |
| record status | confirmed | 273 |
| authenticity | unassessed | 1098 |
| authenticity | accepted | 438 |
| authenticity | pseudo_script | 44 |
| authenticity | uncertain | 2 |
| authenticity | disputed | 1 |
| authenticity | suspected_fake | 1 |

## Acceptance checks

- [x] Every object has source evidence
- [x] No planned queries remain
- [x] No coverage targets remain
- [x] No open leads remain
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
| blocked | 1 | Retrieve the preserved Virtual Magic Bowl Archive data package and enumerate all item records once either Open Research Exeter or the Internet Archive permits access. |
| blocked | 1 | The National Library of Israel exhibition material highlights two bowls for Kafnai son of Imma (with Immai daughter of Anai) and Hai son of Aspindarmid. Resolve their names to the exact MMS and manuscript-part records among the 205 numbered NLI bowls already collected before adding appearances or claims. |
| blocked | 1 | Penn Museum robots.txt was unavailable; metadata was collected slowly, but full page captures were not archived. |
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
| blocked | 3 | Resolve the printed duplicate catalogue number 2972 for Montgomery texts 28 and 40 and the omitted catalogue number for text 19. |
| blocked | 3 | Reconcile Montgomery's statement that the University Museum catalogue held over 150 numbered bowls/fragments, including roughly 30 pseudo-inscribed examples, against the current Penn Museum database. |
| blocked | 3 | Resolve Kedar's numerical discrepancy: the text says Dukhtīč wrote ten bowls total, while note 546 appears to name ten parallels in addition to Davidovitz 2. |

## Interpretation and limitations

This is a maximum-recall discovery corpus, not a claim that every surviving bowl has been individually enumerated. The estimated-distinct count collapses only reviewed exact matches; the pending similarity queue deliberately preserves uncertain possible duplicates.

Major residual gaps are explicit above. They include inaccessible or only partially indexed print catalogues, unnumbered objects in private collections, collection-level totals that cannot safely be expanded into item records, and copyrighted full texts or translations that require authorized access. Blocked leads remain actionable research records rather than silently disappearing from coverage.

The public dashboard should publish only reviewed claims and rights-cleared text or media. The private working corpus can retain bibliographic and archival evidence with its rights metadata.