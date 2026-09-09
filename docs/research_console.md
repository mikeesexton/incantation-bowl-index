# Private research console

The research console is a local working surface over the private SQLite corpus. It treats an identity cluster—not an individual catalogue row—as the primary browsing unit while preserving every underlying record and source claim.

## Start it

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli serve
```

Open `http://127.0.0.1:8765`. The server deliberately refuses non-local network bindings; it is not a public dashboard and should not be exposed through port forwarding or a reverse proxy.

## Introductory home

A visit without a hash route opens the scroll introduction (`#/home`). The bowl
placeholder and schematic map are local SVGs, not photographs or archaeological
findspot data. Historical copy is an editorial draft; the 1850 / 1853 milestones
are researcher-supplied chronology with citations pending. No new research or
media-rights decisions were made for this interface.

The five dark, reading-room-toned chapters introduce the objects, rediscovery,
indexed publications by decade, documentation coverage, and links into Explore.
Primary headings and display numbers use the locally bundled Frank Ruhl Libre;
interface text retains the system sans-serif stack. The bundled font is licensed
under the SIL Open Font License in `web/fonts/frank-ruhl-libre-OFL.txt`.
The map reveals only its approximate find-region shading; the rivers remain fixed.
Rediscovery years count forward from 750 CE, and publication bars rise in decade
order. The sticky desktop circle field keeps one circle per working identity.
Narrow screens stack the field and explanations, with buttons for comparing
coverage. Reduced-motion preferences remove transitions and chart animation. The
chart also has a text table.

`GET /api/introduction` is local-only and read-only. It returns `identity_count`,
`source_record_count`, sorted `identities` with three boolean presence flags,
`coverage` counts, `scholarship` decade rows and an undated-work count, and
`snapshot` metadata (`id`, `loaded_at`, `current_year`, `local_only`). It contains
no text content, provenance claim values, or media URLs. Numbers and the search
index are built from one SQLite read snapshot; a failed refresh retains the prior
complete snapshot. The search response includes the corresponding `snapshot_id`.

The introductory measures deliberately describe recorded evidence:

- `text_edition`: a stored inscription/transcription/transliteration record,
  a resolved publication-object identifier, or an accepted appearance in a source
  already classified as a single-object or corpus edition. A generic scholarly
  mention does not qualify. This is not a claim that a readable text is available.
- `provenance`: the existing provenance coverage group or provenance event;
  includes reported places and collection histories, not just excavated contexts.
- `image`: an image record, independently of display/reuse permission.

`#/explore?present=text_edition`, `?present=provenance`, and `?present=image`
open the matching identities. The new Recorded field control composes with search
and the existing filters. Explore stores its filters, sort, and page in the hash
so a copied URL, refresh, and back navigation preserve the selection. A plain
`#/explore` opens the full corpus. The existing `coverage=text_edition` missing
filter still means **no stored transcription-type record**; it intentionally
remains narrower than the introduction's edition-reference measure.

Publication bars use the existing decade series' `held` field as `indexed`:
that field counts dated bibliography works, not documents physically held. Missing
decades display zero and the current decade is marked incomplete. All counts
refresh with the corpus rather than being embedded in the page.

If the introduction cannot load, its story and database links remain usable and
a retry control appears. Restart the Python console after updating server code;
the existing Refresh control reloads data only.

## Views

- **Explore** searches labels, identity IDs, accessions, publication sigla, claims, descriptions, clients, source titles, and private text content. Filters cover record status, authenticity, object type, missing fields, and substantive claim conflicts. Compatible wording and metadata facets remain audited but no longer trigger the conflict filter.
- **Identity dossier** shows every member record, identifier, source appearance, claim, text, event, and media reference. Restricted text is visible because this is the private local corpus; its rights status remains prominent.
- **Enrichment** presents mutually exclusive next-action queues and field-coverage totals. Selecting a queue returns to a filtered identity list.
- **Concordance** compares candidate identities side by side, displays all matching evidence, and records a reversible same-object, different-object, or insufficient-evidence decision.

## Review safety

The console is read-only except for explicit concordance decisions. A decision requires a written evidence note, updates the existing dedupe record, and appends a new `manual_ui_review` evidence row documenting the previous and new states. It never deletes or rewrites an object record. Review writes require a random token delivered only to the loaded local page.

When the browser implements WebMCP, the page registers matching structured tools for identity search, dossier opening, and concordance decisions. The state-changing tool uses the same validation and per-session token as the visible form. Unsupported browsers simply ignore this optional interface.

The eventual public interface should use the reviewed public-safe export or a separate read-only API. It must not expose this server, the working database, restricted texts, or the private source archive.
