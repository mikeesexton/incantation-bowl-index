# Held-source original-language extraction and separate source pass — 1 October 2026

The frozen [99-appearance worklist](original_script_backlog_2026-09-30.json) has
an explicit disposition for every entry. This run adds **28 working edition
texts** (25 native-script transcriptions and three Hebrew-letter Mandaic
transliterations), **28,663 characters**, and separate partial source reviews.
It also revisits all forty main Montgomery texts, including the AIT27 pilot.
This is a completed pass through the frozen roster, not complete character
extraction or complete scholarly proofreading of the corpus.

| Frozen roster outcome | Source appearances |
|---|---:|
| Working native-script transcription | 54 |
| Working Hebrew-letter edition transliteration; native script still missing | 13 |
| No reliable character transcription; source facsimile retained | 32 |
| Total | 99 |

Thus 67/99 have a working edition text and **45 still lack same-source native
script recovery**. AIT27 lies outside the frozen roster; its eleven printed
Montgomery lines have an additional partial source pass. Counts refer to source
appearances, not distinct physical bowls or complete physical inscriptions.

## Capture and proofreading results

- Jena entries37–40: four actual Unicode Mandaic captures from the broken
  embedded font, recovered against rendered glyph shapes and a retained glyph
  atlas. Grey uncertain letters use a declared project underdot convention;
  contextual shapes are normalized. Entry40 includes its printed native body
  only; the Latin-rendered fragment and Exterior8 remain excluded.
- Gordon A–O: fifteen edition captures, with twelve Hebrew-script transcriptions
  and three source-printed Hebrew-letter Mandaic transliterations (M–O). Parallel
  columns are isolated: E left/F middle; I left/J right; N left; O left and its
  boxed text; G's own witness across four pages. No adjacent witness supplies a
  reading. F has no invented line numbering; D's lost first line is not supplied.
- Ellis1–5: five Hebrew-character edition captures, retaining printed wraps,
  unusual spellings and magical strings. Project doubts distinguish unreadable
  letters and apparently unpaired source brackets from scholarly restorations.
- Stübe VA2416: all printed numbered anchors1–67, preserving the source's repeated
  54–57 (71 labelled rows). The repetition remains evidence, not a dedupe error.
- Ford2014 AS13, Davidovitz27 and Museo Sefardí1073: three Hebrew-script edition
  blocks, including printed outside text and source restorations/excess. A
  footnote interrupting a word is kept out of the ancient-language character text.

A separate source pass changed **22 of the 28 initial drafts**. It corrected
letters, bracket/ellipse boundaries, a displaced continuation, OCR duplications
and footnote intrusion, and flagged remaining capture doubts. All twenty-eight
first drafts survive in the append-only proofreading ledger and private files.

The subsequent Montgomery pass changed content in **eight** earlier texts:
1,14,17,26,27,29,30,34. It also recorded unchanged content checks on the other32.
AIT27's project doubts now use distinct double brackets; source readings have
not been supplied from its parallel. No34's repeated word remains as printed.
All **68 additional reviews are partial_review**. Exact inferior dots, Syriac
upper dots/seyame, marked-dalet placement, some final-letter forms, damaged names,
magical letter counts and specialist interpretation remain open. No diplomatic
accuracy or full character-level check is claimed.

## Unresolved character recovery

All31 Pognon Mandaic editions and Ellis6's Syriac edition have explicit
[per-entry native-recovery dispositions](original_script_native_gaps_2026-10-01.json)
with exact edition pages, including continuations and exterior text. All76
Pognon section pages were rendered and the main edition boundaries inspected.
There is no usable native Unicode text layer. Available Hebrew OCR and a
contextual glyph probe were unreliable for these scripts; their output was not
promoted to character text. Mandaic/Syriac-aware recognition plus manual source
collation, or specialist manual transcription, is required. Extra token budget
alone does not supply a trustworthy reading.

The facsimile manifests associate61 exact edition-page links with these32
appearances; most were already registered. The combined capture manifests add
**eight new scan rows**, while preserving existing page captures. Facsimiles
are useful private evidence, not searchable transcription. The13 Hebrew-letter
transliterations likewise leave actual Mandaic/Syriac-script recovery open.

## Validation and reproducibility

The content-free [receipt](../receipts/held_original_script_2026-10-01.json)
records private/public-domain manifest hashes, source hashes, text identifiers,
page locators, draft/result hashes and scoped validation. The
[item-level progress snapshot](original_script_progress_all_held_2026-10-01.json)
covers exactly99 distinct appearance IDs. Historical snapshots are unchanged.

A consistent SQLite backup preceded this batch. This session adds28 text rows,
eight scan rows and68 proofreading history rows, modifying only the forty
specified existing Montgomery text rows through the proofreading importer.
During that write window another authorized OPS session added one Pognon14
commentary summary; that row and its manifest are explicitly distinguished in
validation and are not part of these extraction counts. All other pre-existing
rows, identity membership, claims, translations and rights decisions are unchanged.

SQLite integrity and foreign keys pass. All68 affected original-language rows
have current partial reviews and full private projection content; all68 are
withheld by the public projection. Replaying every capture and proof manifest
leaves the complete corpus fingerprint unchanged. The personal audit ledger was
unchanged during this session's extraction write window. Protected expressions,
OCR, drafts, fonts, source images and protected ingestion manifests stay ignored
under data/private; Git holds only public-domain source manifests, review
metadata and content-free receipts. No public release, deployment, push, new
translation, identity judgment or personal-audit completion is inferred.

The full repository checks pass:367 Python tests and51 Node tests. The rebuilt
local Mike Access snapshot passes7/7 checks and includes all68 affected
original-language rows with their complete content and partial-review labels.

Next: reliable native Mandaic/Syriac recovery for the45 remaining native gaps,
full diacritic/character collation of these working texts, and a separate
appearance inventory before expanding to other held editions. Existing
ABS/Burberry/Jena/Levene script rows require coverage auditing, not blind reimport.
