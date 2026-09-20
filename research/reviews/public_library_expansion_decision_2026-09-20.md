# Bowlam public-library expansion: owner decision

Status: **pending owner decision** at corpus state `abf8105be933`.

This packet implements the owner's declared use: strictly educational and
noncommercial, with no sales, commissions, advertising or business use. It
does not rely on fair use and does not propose publishing protected modern
translations.

The exact 294-row proposal is bound in
[`public_library_expansion_review_2026-09-20.json`](public_library_expansion_review_2026-09-20.json)
as cohort SHA-256
`cc5f8440930decc9a7c42d4cc4fc13de910618837ffddd4d72d575d3d8f92c44`.
The JSON contains evidence fingerprints and metadata, not text content.

## Proposed architecture

- `bowlam.com/library` will be public and will contain only affirmatively
  reusable text and images, with per-item attribution and terms.
- `bowlam.com/preview` stays behind Cloudflare Access and receives the same
  cleared material within its richer scholarly interface.
- No separate `/workshop` surface is needed now. A later restricted workshop
  tier would be justified only if the owner chose an item-specific fair-use
  position for protected material. This packet does not do that.

## Proposed approvals

| Cohort | Rows | Basis | Conditions carried into the interface |
|---|---:|---|---|
| Wohlstein translations | 4 | US public domain; current scan-checked reading texts | Credit the source and label the project normalization |
| Martínez Borobio translation/paraphrase and transliteration | 2 | CC BY-NC 4.0 recorded in Crossref for DOI `10.15366/isimu2003.6.018` | Author/source attribution, licence link, adaptation label, noncommercial use |
| Penn Museum collection images | 288 rows / 280 URLs | Penn's stated nonprofit educational and personal noncommercial permission | `Object [number]. Courtesy of the Penn Museum.`, link to Penn, identify modifications, no high-resolution or commercial use |

The Penn proposal displays the existing remote 800-pixel collection URLs; it
does not copy image bytes into the repository or offer a download package. All
288 rows have exactly one collection designation for the required credit. Three
URLs are shared by multiple records; the packet keeps each shared resource's
disposition coherent.

Evidence:

- [Penn Museum rights and permissions](https://www.penn.museum/about-collections/rights-and-permissions)
- [Penn Museum website terms](https://www.penn.museum/about/statements-and-policies/terms-and-conditions)
- [Crossref DOI record](https://api.crossref.org/works/10.15366/isimu2003.6.018)
- [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

## Deliberately excluded

- Wohlstein `TXT-D39E05041A00`: public-domain source, but its embedded Hebrew
  strings still need a second reading.
- Thirteen protected modern translations: no permission and no proposed
  fair-use publication decision.
- Twenty-nine other unapproved media rows: no affirmative permission basis.
- Source scans, PDFs, OCR, private notes, capture paths and review payloads.

## Decision requested

The owner may approve the exact cohort, approve only the six text rows, approve
only the 288 Penn media rows, or leave either cohort pending. Approval authorizes
append-only evidence-bound publication/rights decisions and construction of the
two local release candidates; deployment remains a separate approval after the
built bytes and privacy audit are available.

This is operational rights triage, not legal advice.
