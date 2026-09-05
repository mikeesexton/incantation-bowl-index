# Private research console

The research console is a local working surface over the private SQLite corpus. It treats an identity cluster—not an individual catalogue row—as the primary browsing unit while preserving every underlying record and source claim.

## Start it

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli serve
```

Open `http://127.0.0.1:8765`. The server deliberately refuses non-local network bindings; it is not a public dashboard and should not be exposed through port forwarding or a reverse proxy.

## Views

- **Explore** searches labels, identity IDs, accessions, publication sigla, claims, descriptions, clients, source titles, and private text content. Filters cover record status, authenticity, object type, missing fields, and substantive claim conflicts. Compatible wording and metadata facets remain audited but no longer trigger the conflict filter.
- **Identity dossier** shows every member record, identifier, source appearance, claim, text, event, and media reference. Restricted text is visible because this is the private local corpus; its rights status remains prominent.
- **Enrichment** presents mutually exclusive next-action queues and field-coverage totals. Selecting a queue returns to a filtered identity list.
- **Concordance** compares candidate identities side by side, displays all matching evidence, and records a reversible same-object, different-object, or insufficient-evidence decision.

## Review safety

The console is read-only except for explicit concordance decisions. A decision requires a written evidence note, updates the existing dedupe record, and appends a new `manual_ui_review` evidence row documenting the previous and new states. It never deletes or rewrites an object record. Review writes require a random token delivered only to the loaded local page.

When the browser implements WebMCP, the page registers matching structured tools for identity search, dossier opening, and concordance decisions. The state-changing tool uses the same validation and per-session token as the visible form. Unsupported browsers simply ignore this optional interface.

The eventual public interface should use the reviewed public-safe export or a separate read-only API. It must not expose this server, the working database, restricted texts, or the private source archive.
