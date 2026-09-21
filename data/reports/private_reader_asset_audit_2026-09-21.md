# Private reader asset audit — 21 September 2026

This is an audit of what Mike's loopback-only research reader can actually show.
It is not a public-release or reuse decision.

## Text bank

- The database holds **273 text rows for 209 objects**, and the private
  projection makes all 273 available on localhost.
- Those rows comprise 216 project/research summaries, 55 translations
  (50 English and five German), one Jewish Babylonian Aramaic transcription,
  and one Jewish Babylonian Aramaic transliteration.
- **55 objects have a stored translation, transcription, or transliteration.**
  Edition references are much broader than this: a citation or a claim that a
  translation exists is not yet a locally searchable text.
- Davidovitz 41 now has Ford's ten-line English translation and lineated Jewish
  Babylonian Aramaic transcription, each source- and page-located and marked
  private research / not cleared for redistribution.
- The seven explicit `translation_availability` claim records now resolve as
  follows: Davidovitz 41 has its stated English translation stored; five
  Montgomery entries explicitly have no separate translation in that edition;
  and Levene's M163 translation is still a cited but untranscribed private-bank
  gap.

The original-language bank is therefore real but still very immature. The next
high-yield, low-rights-risk lane is a page-checked transcription of the
public-domain Montgomery 1913 originals. The database currently links 44
Montgomery objects but stores only its 35 English translations and project
summaries. Modern editorial transcriptions from protected editions can also be
added to Mike's private tier, but should remain source-specific and private;
the ancient inscription is public domain, while damaged-letter readings,
restorations, word division, and apparatus may embody modern editorial work.

## Images

- The database records **327 image rows for 327 objects**.
- 299 URLs have an ordinary raster-image suffix. Twenty-six are catalogue or
  repository page references without a raster suffix, and two are PDFs.
- Page and PDF references are no longer passed to an HTML `<img>` element. They
  render the bowl diagram plus a source link. Direct raster URLs also fall back
  to the diagram if a remote host blocks, moves, or removes the image.
- Davidovitz 41 now uses a reproducible, hash-bound private derivative extracted
  from figure 1 on printed page 218 (PDF page 228) of the held Ford volume. The
  derivative is served only from `/api/private-media/` by the loopback console;
  it is neither copied into a static build nor approved for sharing.

## Boundary verified

The local private projection now contains 273 available text rows and one
reviewed local image derivative. The separately built shared-release candidate
still includes 252 text contents and 298 images; it withholds the two new Ford
text contents (21 text rows withheld in all). No public or Cloudflare deployment
was performed.
