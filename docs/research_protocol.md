# Research protocol

## Unit of record

The canonical object record represents a hypothesized physical artifact. A source appearance represents one description, listing, catalogue entry, publication item, photograph, or other observation. Multiple appearances may resolve to one object, and one appearance may initially be linked to several candidate objects.

## Minimum candidate record

Every candidate requires a stable object ID, a source, a precise source locator, and an appearance-to-object link with a confidence and rationale. Unknown fields remain unknown; they are never filled by inference without an attributed claim.

## Source capture

Record a full citation even when a URL is unavailable. For public URLs, store retrieval time, response metadata, SHA-256, size, rights status, and the content-addressed archive path. If robots permission cannot be verified, do not fetch automatically; create a lead for manual inspection.

## Deduplication

1. Normalize identifiers without discarding their original spelling.
2. Treat an exact trusted accession or publication identifier as strong evidence, not an unconditional merge instruction.
3. Compare dimensions, material, text language and script, inscription incipit, line count, drawings, photographs, provenance events, collection history, and sale references.
4. Store both positive and negative evidence.
5. Queue uncertain pairs. A human decision records same object, different objects, or insufficient evidence.
6. All merges require a dedupe decision and an append-only, reversible merge record.

## Search coverage and saturation

Each search action records its platform, source class, language, query, time, result count, net-new candidates, status, and notes. Each newly discovered citation, identifier, collection, person, auction, or restricted source becomes a lead. The campaign is saturated only after all planned source classes and leads are resolved or explicitly blocked and two independent broad sweeps each add less than one percent net-new candidate objects without exposing a new source class.

## Public release

The future public dataset may expose metadata and material marked `public_ok`. Copyrighted or unclear transcriptions, translations, and images remain private until rights are resolved. Provenance statements describe what sources report and do not legitimize ownership or authenticity.

