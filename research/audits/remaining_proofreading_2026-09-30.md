# Remaining edition proofreading — 30 September 2026

Codex, TEXT-004. Starting state matched Claude's local handoff: 634 checked,
two partial and 61 unreviewed of 697 edition rows. Ending coverage is **688
checked, zero partial and nine unreviewed**. This is coverage of stored rows,
not completeness of the ancient corpus or of all scholarly editions.

## Completed comparisons

| Source | Rows newly checked | Evidence |
|---|---:|---|
| Naveh and Shaked, *Amulets and Magic Bowls* | 28 | Complete held scan; translations and original-script renderings, including both parts of bowl 12 |
| *Gabriel Is on Their Right* | 2 | Held article, printed pp. 188–189 |
| Cook, Khafaje bowl | 1 | Held article, printed p. 79 |
| Ford, *My Foes Loved Me* | 2 | English abstract p. XV; full volume's Hebrew edition pp. 216–217 |
| Ford 2014, *Aula Orientalis* | 3 | Held article, printed pp. 248, 254, 256 |
| Stübe 1895 | 3 | Held scan, printed pp. 23, 25, 27 |
| Ellis in Layard 1853 | 3 | Held scan, printed pp. 512–515, 518 |
| Schwab 1891, item N | 1 | Held scan, printed p. 591 |
| Gordon 1937, text H | 1 | Both translation pages, printed pp. 87–88; previous partial closed |
| Wohlstein 1894 | 1 | Complete translation, printed pp. 16–18; previous partial closed |
| Barakat quotation rows | 3 | Retained HTML quotation fields |
| Schøyen quotation rows | 3 | Retained HTML Text fields, including the opening excerpt of MS 1911/2 |
| Hamburg, *What Will Save the Household?* | 1 | Retained article's quoted fragment |
| COJS, expulsion and family protection | 2 | Newly retained HTML; existing opening excerpts checked |
| **Total** | **54** | **45 PDF comparisons and nine HTML quotation comparisons** |

The work retained edition wording and uncertainty while repairing OCR, restoring
omitted passages, joining print wrapping and removing footnote material. The
Hebrew rows for *Amulets* bowls 9 and 11 had substantial omitted passages.
Stübe's embedded Hebrew placeholders were replaced from the printed page.
Gordon's entire demon-name list was compared, including transliteration marks.
The Ford Hebrew edition received a second enlarged-word mark collation: several
circles attached to adjacent letters in the first revision were corrected, and
an unidentified sign was retained without asserting a definite letter or an
erasure. Both same-session revisions remain in the append-only ledger.

HTML checks certify reproduction of the source's quotation, **not** the
catalogue's reading of the original inscription. Source errors and doubtful
words remain attributed to that source. The excerpt reviews do not imply capture
of the full editions. Version 2 proofreading manifests now bind HTML quotations
to registered capture hashes and named section locators; PDF manifests remain
version 1. The importer preserves originals, rejects altered evidence and stale
rows, and resets public approval in both paths.

## Nine rows still requiring evidence or edition replacement

| Text ID | Source | Required next step |
|---|---|---|
| `TXT-D40450F0C247` | Cincinnati Skirball, *Mandaic Bowl* | Stored English prose summarizes the spell; obtain and retain the attributed translation rather than certify the summary as verbatim text |
| `TXT-C4296C80CCD2` | Abousamra, Matenadaran | Stored abstract-derived summary is not an edition translation; acquire the article's edition pages |
| `TXT-7DBC5A7924A5` | Martínez Borobio 2003 | Acquire the repository PDF with verifiable access permission; compare the transliteration on printed p. 324, including editorial signs and uncertain reading |
| `TXT-B40E7B6820A5` | Martínez Borobio 2003 | Replace the stored English summary with the attributed printed translation on p. 325 after retaining the source |
| `TXT-B91E459A48AD` | Jena, Hilprecht collection feature | Stored prose is a summary; retain the source edition or actual translation before replacing it |
| `TXT-5AD1D8AE244B` | McCullough 1967, DA 5 | Stored prose is a summary; acquire the cited 1967 edition |
| `TXT-809171D23704` | McCullough 1967, DA 4 | Verify and replace the abbreviated wording against the cited 1967 edition |
| `TXT-C4E64CF6D96B` | Barakat X.0552 | Stored prose summarizes the separate quotation; keep distinct from the source's actual translation |
| `TXT-F6B208BDB88C` | Kedem auction 32, lot 154 | Retain the source quotation through a permitted route; the current site's robots rules disallow automated retrieval |

The McCullough source URL delivers *Two Mandaean Incantation Bowls*, an earlier
Toronto thesis, not the cited 1967 book. It was retained as related evidence,
but neither ROM row was marked checked against it. The UAM PDF can be located
online, but its robots permission could not be verified, so no direct archival
fetch was made. No access controls were bypassed. The stored denominator and
text-type metadata have not been changed to make the remaining queue disappear.

## Preservation and validation

- 54 distinct rows received current checked reviews; 49 have changed content.
  The additional Ford mark correction is a superseding review of the same row.
- Private staging, before-snapshot, full diffs, corrected text files and protected
  manifests remain in `data/private/`; manifests are under `data/private/manifests/`.
  Git receives only content-free receipts and this audit.
- Four additional source captures were retained through the standard archival
  command from a private acquisition manifest. The source archive now has 63
  captures. The related thesis is not treated as a complete holding of the book.
- Pre-batch SQLite backup passed integrity checking; backups retained to ten.
  The working database passed integrity and foreign-key checks. Every initial
  before-snapshot matched the original private session snapshot.
- 329 tests passed, including new HTML evidence/replay validation. Mike Access
  passed its seven private-projection audit checks and packages all 63 captures.
  Proofreading, enrichment, roadmap and Levene queue outputs were regenerated.
- All reviewed rows remain private. No public reuse, scholarly adjudication,
  deployment or push was performed.
