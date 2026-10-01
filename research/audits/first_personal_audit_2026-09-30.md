# First personal audit: reader corrections and documentation checks

Mike reviewed all five batch-one identities on 30 September 2026. His notes
are retained in the ignored private audit ledger. This report records the
implementation and research response, not a scholarly sign-off or release decision.

## Reader-wide corrections

- Reserve “What it says” for actual translation rows. An unavailable translation
  has an explicit empty state; catalogue prose and research summaries are
  separately labelled, collapsed commentary.
- Place expandable original transcriptions/transliterations immediately under
  the translation. Retain original-language text, editorial signs, attribution,
  and private access. When no original is stored, say so rather than manufacture one.
- Promote source-reported maker/hand, named people, targets, ritual and intertexts
  into the main view. Keep collection/publication designations and original
  source labels in one collapsed identifier apparatus.
- Combine equivalent citations for the same source, printed page and item,
  retaining the richer locator. Distinct source/page/item and numbered
  line/figure/column references remain separate. Source claims remain intact.
- Keep recorded alternative forms in details without repeating their normalized
  main-display value and citation.

## Universal text-label sweep

All 406 translation rows were examined for explicit summary/paraphrase labels
in their editor/notes metadata. Seven were incorrectly classified:

| Text ID | Recorded declaration | Correct type |
| --- | --- | --- |
| TXT-5AD1D8AE244B | McCullough discovery summary | summary |
| TXT-809171D23704 | McCullough discovery-pass paraphrase | summary |
| TXT-B40E7B6820A5 | Martínez Borobio paraphrase | summary |
| TXT-B91E459A48AD | Jena discovery summary | summary |
| TXT-C4296C80CCD2 | Matenadaran discovery summary | summary |
| TXT-C4E64CF6D96B | Barakat listing summarized | summary |
| TXT-D40450F0C247 | Skirball museum discovery summary | summary |

These metadata repairs retain all content and exact original rows in an
append-only private snapshot ledger. They do not create missing translations,
certify readings, or approve reuse. Ingestion rejects translations explicitly
labelled as summaries/paraphrases, including replayed older manifests. The
remaining edition-acquisition work listed in
`remaining_proofreading_2026-09-30.md` remains open; a smaller translation
count does not mean those missing editions have been obtained.

## Bowl-specific findings

### AIT27 — IDENT-917397575566

The stored Kedar table excerpt is a research summary, not a translation.
Montgomery 1913, No. 27 (CBS 16041), printed p. 212 / PDF p. 218, gives
Hebrew-script text and discussion but deliberately does not give a separate
translation: the published portion closely parallels No. 2. Do not substitute
No. 2's translation or present the unrelated table as this bowl's words.
The unpresented damaged portion must remain a limitation. The held edition is
available in Mike Access, capture CAP-560EB584740F, SHA-256
`c85f9eaadcd910652543bb54dab16e5a1a4ac7883df7b433ea2c9aa0b357abdf`.
The duplicate dimensions citations both refer to printed p. 325, item/text 27;
the richer locator also records PDF p. 331. Display one, preserve both claims.

### B2970 — IDENT-62DA4A36AF2B

Checked [Penn Museum object 79917](https://collections.penn.museum/collections/object/79917)
in the normal browser, including Details and Bibliography. The museum reports
19 joined fragments, 13 interior lines in concentric circles, possibly Aramaic,
bitumen traces, expedition credit (Nippur I, 1889) and field number 262. It
provides two object photographs. The Bibliography panel lists no bibliography.
These are museum reports, not a transcription or translation checked against
an edition. Exact-designation web searches did not locate an additional
object-specific edition. Keep a documentation lead; absence of a web result or
museum bibliography is not proof of unpublished status.

### VA.2451 — IDENT-BFA332B1C70A

Visually checked Bhayro et al. 2018, catalogue entry 45, printed p. 101 /
PDF p. 115. The stored prose describes the catalogue entry, not the spell.
The source reports complete but badly faded pottery, nearly illegible writing,
Mandaic, round base, no visible drawing and an unpublished status **as of 2018**.
The text and six extracted claim pointers incorrectly said printed p. 99; repair
them to p. 101 through retained-history manifests. Original wording is retained.
Held capture CAP-DBB06BEA4670, SHA-256
`7a25b7b89f8160aaec249988f47a5fb08b654c8ca9506b44fcc48ee60cde6aac`.
Exact designation searches did not identify a later edition. This is a dated
negative report and an open later-publication lead, not a current definitive
no-known-edition assessment.

### Segal 2000, 113M — IDENT-A58C2D4572FF

The full 2000 British Museum catalogue is still needed. No accession or
translation is inferred from the provisional edition designation.
A relevant contact beyond the museum is **Erica C. D. Hunter**, whose contribution
covers the typology of these bowls (pp. 163–205):
[Macquarie institutional bibliography](https://researchers.mq.edu.au/en/publications/the-typology-of-the-incantation-bowls-physical-features-and-decor/).
Her [SOAS affiliate page](https://www.soas.ac.uk/about/erica-hunter) provides
public contact details. A short email is drafted for Mike; no message is sent.
The [British Museum Middle East department](https://www.britishmuseum.org/our-work/departments/middle-east)
is the institutional route for accession concordances and collection documentation.

### GelD — IDENT-B26A8CEA33A7

[Apotropaic Arts, Aramaic bowl index](https://apotropaicarts.com/articles/amuletindices/bowlsa/)
lists GelA, GelB, GelC (=BM023A) and GelD under Markham J. Geller's
“Four Aramaic Incantation Bowls,” in *The Bible World: Essays in Honor of
Cyrus H. Gordon* (1980), pp. 47–60. **GelD denotes bowl D in that index's
Geller group**, not a museum accession. The primary publication is not held
and its bowl D has not been independently checked. Add the bibliographic lead
and an explanatory description, without guessing location or merging identities.
