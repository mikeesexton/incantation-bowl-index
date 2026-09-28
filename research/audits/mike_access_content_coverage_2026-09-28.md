# Mike Access content coverage — 28 September 2026

This is a private-ingestion audit, not a public-release assessment. Counts come
from the working database at state digest `48440b7c1be5` before this session's
documentation and local-reader changes. The database was queried read-only.

| Material | Held or recorded | Structured for Mike Access | Gap |
|---|---:|---:|---|
| Source captures | 59 files from 56 sources | Local reader now offers registered capture links | Static Mike build does not package source scans |
| Complete held documents | 49 sources | 26 are scope-reviewed editions or catalogues | 17 of those 26 have no text or media rows |
| Text rows | 308: 73 translations, 16 transcriptions, 1 transliteration, 218 summaries | All 308 display in the private projection | Many held editions have no extracted inscription or scholarly translation |
| Image rows | 354 remote or local references | All 354 display in the private projection | Only 7 have a retained local image derivative; a URL is not a preserved picture |

The private projection's zero withheld count is accurate **for rows already
entered**. It does not measure whether a held book's bowl text, translation, or
plate has been extracted. Nor does the static Mike snapshot include the 59
archived source files. The local research console now serves registered captures
by opaque ID and points edition/text links to them; the remote single-user
surface still needs a source-document delivery design and gate review.

The immediate extraction queue includes complete held works with zero structured
text and zero media rows: *Aramaic Bowl Spells* volumes 1 and 2; *Aramaic
Incantation Bowls in Museum Collections* volume 1; Moriggi's *Corpus of Syriac
Incantation Bowls*; Burberry's 25-text Berlin thesis; Pognon's Khouabir edition;
and several smaller editions. These are source holdings, not empty books. Their
object appearances and publication links were captured, but their inscriptions,
scholarly translations, and plates have not been structured for Mike Access.

For the next private-ingestion batch, select one complete held edition and record
each bowl's inscription and existing scholarly translation under the exact
edition locator. Preserve the scholar's wording and attribution in a protected
manifest under `data/private/manifests/`, bind it to the archived capture hash,
and add image files or page-image pointers under the source's copying conditions.
Record absent content as absent; do not substitute a new translation or a public
reuse decision. Rebuild the local private reader and check the counts against the
manifest. Then scale source by source.

## First private extraction

Cook 1992, *An Aramaic Incantation Bowl from Khafaje*, provides a small
source-checked example. Its published English translation (p. 79, lines 1–5)
is now a private text row, attributed to Cook and unavailable to the public
projection. Figure 1 on p. 80 is a private full-page image derivative, and
the complete article remains linked from the local reader. The content-free
[receipt](../receipts/cook_1992_khafaje_private_2026-09-28.json) binds both to
the held PDF and protected ingestion manifest. The original-script OCR was
unusable, so the inscription still needs visual transcription from the page.

## Source delivery update

The later 28 September `ACCESS-010` session packaged and hash-checked all 59
registered captures in the ignored local static Mike build. The local research
console and static reader now list every capture, including the two without a
source assignment. The remote deployment remains pending a Mike-only identity
policy and private delivery for nine PDFs larger than Cloudflare Pages' 25 MiB
per-asset limit. See the [delivery roadmap](../../docs/mike_access_source_delivery.md).
