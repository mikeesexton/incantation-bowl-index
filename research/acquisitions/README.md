# Acquisition evidence

Dated JSON files record actual access attempts and document-scope inspections.
A source citation, a captured file, a complete article and a checked reading are
separate facts. Document assessments bind to a source, capture, archived SHA-256,
review evidence and any transformed artifact; they do not approve text or image
reuse. `ibi report-acquisitions` consumes the immutable current assessment while
leaving every unassessed capture explicitly unassessed.

The document ledger keeps four dimensions separate:

- form and extent (`citation_only`, `front_matter`, `excerpt`, `complete`);
- inspection (`not_inspected`, `digital`, `physical`);
- text state (`none`, `extractable`, `ocr`, `corrected_rich_text`); and
- object-level extraction (`none`, `partial`, `complete`).

Apply a checked manifest with:

```sh
ibi ingest-document-assessment research/reviews/<manifest>.json
```

OCR and corrected rich text require their own path and hash. Partial or complete
object extraction requires the extraction manifest's path and hash. A later
assessment supersedes the current row explicitly; history is never overwritten.

## 2026-09-06 batch

- Ford 2014: complete 29-page article scan (pp. 235–263), privately archived.
  All page images inspected for scope, with detailed checks of the title,
  final page and edition-section boundaries. The scan lacks a text layer.
- Segal 2000: the indexed title/contents PDF is two pages; full work not obtained.
- Isbell 1975: Internet Archive marks its item access-restricted; not obtained.
- Ford 2002: current publisher metadata found; old PDF URL returns 404 and the
  current document host fails the robots allowance check. No PDF acquired.
  The publisher names Ford while prior source SRC-1EE58A703971 names
  Müller-Kessler. Both source records are retained and a reconciliation lead
  records the discrepancy.

The exact URLs, outcomes, hashes and locators are in
`edition_access_2026-09-06.json`. Follow-up leads stage edition and attribution
review; no new physical-object records or transcriptions were inferred.

## Replay

Run from the project root with the project environment. Capturing requires
current robots permission and may fail if the remote host changes. A retrieved
file must match the review hash before reusing its scope assessment.

```sh
ibi ingest source research/sources/edition_acquisitions_2026-09-06.jsonl
ibi capture https://www.ub.edu/ipoa/wp-content/uploads/2021/08/2014AuOrFord-c.pdf --source-id SRC-FORD2014-AUOR --rights-status copyrighted
ibi ingest lead research/leads/edition_acquisition_followups_2026-09-06.jsonl
ibi ingest-search-log research/searches/edition_acquisition_2026-09-06.jsonl
ibi verify-archive
```

Source and lead manifests were replay-checked without duplicate records. Search
logs describe the original dated searches; replay does not mean a new search
was conducted. Capture IDs may differ in a reconstructed database; the source,
URL and SHA-256 are the stable evidence binding.
