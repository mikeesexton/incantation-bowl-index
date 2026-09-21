# Public release preparation

Status: working plan at corpus state `6cd15c856898`, 20 September 2026. This is
release engineering and conservative rights triage, not legal advice or a
substitute for an item-specific decision by the project owner.

## The governing distinction

Cloudflare Access controls who can reach a copy; it does not create permission
to make or distribute that copy. The staged scholar preview must therefore use
the same fail-closed projection as an open release. Protected scans, OCR,
transcriptions, translations, photographs and source prose stay in the private
vault unless a recorded basis covers the actual use.

United States Copyright Office guidance distinguishes facts from their
expression: facts and individual short phrases are not protected, while the way
facts are expressed and a sufficiently original database selection or
arrangement may be. See the [Copyright Office FAQ](https://copyright.gov/help/faq/faq-protect.html),
[37 C.F.R. § 202.1](https://www.copyright.gov/title37/202/37cfr202-1.html), and
the Office's [automated-database guidance](https://www.copyright.gov/register/tx-databases.html).
The practical rule for Bowlam is therefore:

1. Preserve each source's wording, citation and locator in the research record.
2. Browse through concise project-authored labels instead of reproducing a
   source's descriptive sentence as the taxonomy.
3. Treat terse factual metadata separately from sentence-like source wording.
4. Never infer permission for a text or image from permission to publish facts.

The new `facets` projection implements the second rule. It does not overwrite
claims. Each controlled label retains the object, source field, source and
locator from which it was derived.

## Operational reader tiers

| Reader | Audience | Data source | Current boundary |
|---|---|---|---|
| Private localhost | Mike | `PrivateResearchProjection` | All 273 stored texts, all 327 recorded media records, one reviewed local image derivative, and all eligible source wording; binds only to loopback and is not a redistribution surface |
| Cloudflare Access preview | Up to 50 individually authorized users | `Projection` | The reviewed release candidate only: currently 252 text rows and 298 approved media rows |
| Public library | Anyone | `Projection` | The same fail-closed rights model; remains local and unpublished |

The UI code is shared, but its manifest identifies the tier. A row marked
`private_research` is rendered only when the manifest itself is the local
private tier. The static preview and public builders never receive those rows.

## Current release inventory

The rights-gated release projection currently contains:

| Material | Rows | Operational status |
|---|---:|---|
| Working physical identities | 1,652 | Public-reference structure |
| Sources and citations | 862 | Public-reference structure |
| Object/source appearances | 2,268 | Public-reference structure |
| Identifiers | 4,741 | Factual metadata |
| Short fact candidates | 6,382 | 6,352 included; 30 non-public-domain wording values withheld for priority review |
| Project-authored controlled facets | 3,636 | Public candidate, with claim-level traceability |
| Text rows | 273 | 252 included by recorded decision; 21 withheld with citation and locator |
| Media resources known | 327 | 298 included by recorded decision; 29 withheld |
| Private captures | 55 | Never staged; storage paths are forbidden by the projection guard |

The 252 included text rows comprise 39 public-domain translations, 77
project-authored summaries, and 136 open-license rows. The last group includes
134 Waller summaries and the Martínez Borobio transliteration and labelled
project paraphrase; it is
CC BY-NC 4.0 and must retain its attribution, licence link and noncommercial
limit; it cannot silently become CC BY 4.0 or enter a commercial surface. The
[CC BY-NC 4.0 terms](https://creativecommons.org/licenses/by-nc/4.0/) also forbid
adding legal or technological restrictions that prevent recipients from doing
what that licence allows. This means the Access gate may protect the preview as
a whole, but it must not be presented as changing the licence of those rows.

## Deployed gated staging baseline

The exact candidate is recorded in
`research/reviews/scholar_preview_release_candidate_2026-09-20.json` as
`1b16d886bb3ef092e0b5a324abac796bf6d6d9b1d3de9cc66a87a12ec2a01fc0`.
It binds nineteen built files by SHA-256 to corpus state `abf8105be933` and is
approved by the project owner for gated staging. Ten of ten automated checks pass: declared
schema, shared-projection row equivalence, absence of private/reviewer columns,
local paths/contact data/secrets, all 51 private storage paths, all 30 withheld
wording values, the short-claim boundary, text and media gates, and traceability
of all controlled facets. Those exact nineteen files are deployed at
`https://bowlam.com/preview/` behind Cloudflare Access in production deployment
`e5aabb22-bf0d-4cc3-85d1-193d687e6cff`. The host lock returns 404 for the
project's `*.pages.dev` aliases. Expanded preview candidate
`a16b8f19061b...` was then approved and deployed as Cloudflare Pages production
deployment `a78d885f-18c7-46db-9c57-07f73ae1d211`. It contains 252 text rows
and 298 media rows and passes all ten release checks. The custom-domain preview
and its nested data redirect through Cloudflare Access; the project and
per-deployment `*.pages.dev` aliases return 404 for preview paths.

## Controlled browse vocabulary

The first normalization pass changes the visitor-facing cardinality without
discarding evidence:

| Bowlam facet | Raw distinct values | Controlled labels | Key correction |
|---|---:|---:|---|
| What they do | 78 | 11 | Excludes named demons, named angels, installation instructions and non-functional traditions |
| Where they are | 78 | 48 | Collapses articles, accessions and institutional spelling variants |
| Language | 52 | 9 | Collapses punctuation, catalogue codes, historical prose and OCR debris; preserves multi-language claims |
| Where they come from | 101 | 29 | Uses geographic claims only; excludes owners, donors, dealers and acquisition narratives |

Examples: `Schøyen Collection` and `The Schøyen Collection` now browse together;
`Halbas-Lilit` remains a cited `named_demon` fact but is no longer a ritual
purpose; a private-collection acquisition narrative remains provenance history
but is no longer treated as a place of origin.

These categories are deliberately broad. They are navigation, not adjudication:
a bowl can appear in more than one language or purpose label when its sources
are composite or disagree. The raw object page remains the place to see that
uncertainty.

## Release classes and decisions

### Ready for staging under current project policy

- Identity, source, citation, identifier and appearance structure.
- Facts marked `factual_metadata`, subject to a final privacy and accuracy scan.
- Controlled `facets`, because their wording and selection are project-authored
  and every row is traceable.
- The 252 text rows and 298 media rows that already have current, evidence-bound
  publication decisions, on their individual terms.

### Keep local for review, not presumed cleared for an open launch

The triage deliberately does not turn a copyright principle into an automated
legal decision. Forty rows in prose-prone fields come from sources already
recorded as public domain. Another 185 are at most 80 characters, contain no
embedded quotation, and are marked
`short_source_claim`; they are strong candidates for direct publication or
replacement by a controlled label, but retain their source attribution. Thirty
rows from non-public-domain sources are marked `review_source_wording`: 28 are
longer statements and two short rows embed quoted wording. They form the first
human review packet, generated by
`scripts/build_public_fact_review.py` under
`data/private/reviews/public_fact_wording_review_2026-09-20.json`. The packet
itself repeats the wording under review and therefore stays out of Git. Until
reviewed, the shared projection omits the raw value while still exposing the
controlled facet and the ordinary source/citation structure.

### Withhold until a new decision exists

- All 21 text rows whose content is currently withheld.
- All 29 media resources without an approved reuse decision.
- Every source scan, local capture, OCR product, rich-text package, research
  note and filesystem path from the private vault.
- Any commercial use of the 134 CC BY-NC rows unless the rights holder supplies
  broader permission.

## Proposed public educational library

The next public surface should be `bowlam.com/library`, not a public
`/workshop`. It will contain only material with an affirmative public reuse
basis and will remain separate from the general landing page. The gated
`/preview` will consume the same approved rows inside its richer scholarly view.
A separate workshop tier is unnecessary unless the owner later chooses an
item-specific fair-use position for protected modern expression.

The owner-approved exact proposal is
`research/reviews/public_library_expansion_review_2026-09-20.json`, cohort hash
`cc5f8440930decc9a7c42d4cc4fc13de910618837ffddd4d72d575d3d8f92c44`.
It approves four scan-checked public-domain Wohlstein translations, two CC
BY-NC Martínez Borobio rows and 288 Penn Museum media rows under Penn's stated
nonprofit educational/personal noncommercial terms. It deliberately excludes
the fifth partially reviewed Wohlstein translation, fourteen protected modern
translations, one modern transcription, and twenty-nine other unapproved media rows. The append-only
publication and rights ledgers now carry those decisions.

The current public `/library` candidate `8491daf233bf...` groups the released material
into 454 browseable bowl records. It contains 252 texts and 298 media rows and
passes ten checks covering projection gates, required attribution and terms,
Penn credits, coherent shared URLs, private paths, reviewer-only fields and
declared counts. It supersedes the earlier local candidate only because the two
new private Ford pointers change the projection; no new protected content is
released. It is built outside `site/public` and is not deployed.

## Next release sequence

1. Keep the exact public-library candidate local until the owner separately
   approves it; the expanded gated preview is already deployed.
2. Review the 30 priority wording rows in source cohorts. The 185 short claims
   passed a structural spot-check. Replace copied descriptive phrasing with a project-authored
   summary where useful, retain the original in the private evidence layer, and
   record who made the determination.
3. Run a privacy scan for living-person contact details, private notes and local
   paths even though the projection already excludes those fields.
4. Split the downloadable licence notice by material: Bowlam-authored database
   elements, public-domain material, CC BY-NC rows, and item-specific media
   terms must not be described by one blanket licence.
5. Have the project owner approve a versioned release manifest. Counsel review
   is advisable before an unrestricted or commercial launch; engineering gates
   cannot make that legal judgment.
6. Publish first as a factual reference. Add protected editions or images later
   only through evidence-bound decisions or executed licences.

## Acceptance checks

- A visitor cannot retrieve any private capture path or unapproved text/media.
- Every controlled facet row resolves to at least one cited source claim.
- Removing the raw facts table still leaves a coherent public browse surface.
- Every included text and media row states its rights basis and applicable
  licence or permission locator.
- The Pages host lock still returns 404 on every ungated `*.pages.dev` alias.
- The owner signs the release manifest; an agent never converts “likely factual”
  into a copyright approval.
