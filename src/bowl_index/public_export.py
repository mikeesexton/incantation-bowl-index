"""Write the gated projection to files. The gates themselves live in projection.py."""
import csv
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .projection import PROJECTION_COLUMNS, Projection

# Kept for callers that imported it from here before the projection was extracted.
from .projection import EDITION_SOURCE_TYPES  # noqa: F401


EXPORT_POLICY = (
    'Reference scaffold with explicit text and media gates. Not a certification of scholarly '
    'accuracy. No capture records/files, claim payloads, notes, raw JSON, or review history. '
    'No unrestricted corpus dashboard is deployed. A withheld text keeps its citation, locator and link so a '
    'reader can consult the edition; the editions table names where each object has been published.'
)
LICENSE_BASE = (
    "Covers this project's own contribution: records, concordances, judgments, summaries, and the "
    "selection and arrangement."
)


def license_scope(texts, counts):
    """Describe the terms this export actually ships under.

    Derived from the ledger rather than written down. The gate state moves every
    time a review lands, and a scope sentence maintained by hand is one that goes
    stale the first time someone forgets — which is the failure that matters here,
    because the sentence is what tells a reader which rows are not CC BY 4.0.
    """
    included = [row for row in texts if row["content_status"] == "included"]
    public_domain = sum(1 for row in included if row["rights_basis"] == "public_domain_expired")
    licensed = [row for row in included if row["rights_basis"] == "open_license"]
    licences = sorted({row["license_url"] for row in licensed if row["license_url"]})
    parts = [LICENSE_BASE]
    if public_domain:
        parts.append("%d text rows are public domain and are not licensed here." % public_domain)
    if licensed:
        parts.append(
            "%d text rows carry their source's own licence, which travels with them and is NOT "
            "replaced by CC BY 4.0%s. Read the row's license_url before reuse." % (
                len(licensed), " (%s)" % "; ".join(licences) if licences else "")
        )
    if counts["texts_withheld_rows"]:
        parts.append(
            "%d withheld rows carry a pointer only; the source's own terms govern them."
            % counts["texts_withheld_rows"])
    if counts["media_approved_rows"]:
        parts.append(
            "%d of %d media URLs carry an explicit rights decision and its attribution; the rest "
            "are withheld, and none is relicensed here." % (
                counts["media_approved_rows"],
                counts["media_approved_rows"] + counts["media_withheld_rows"]))
    else:
        parts.append("Media are URLs and none is approved for reuse.")
    parts.append("See docs/licensing.md.")
    return " ".join(parts)


def projection_manifest(projection, tables):
    """The manifest the exporter writes and the reader API serves, minus file names."""
    counts = projection.gate_counts(tables['texts'])
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'access_tier': 'reviewed_release',
        'export_policy': EXPORT_POLICY,
        'license': 'CC-BY-4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'attribution': ('Gabai, Moses. Incantation Bowl Index. '
                        'https://github.com/mikeesexton/incantation-bowl-index'),
        'license_scope': license_scope(tables['texts'], counts),
        **counts,
        'tables': {},
    }


def export_public(conn, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Public export requires a new destination; existing files may contain private data')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.ibi-public-', dir=destination.parent))
    try:
        projection = Projection(conn)
        tables = projection.tables()
        manifest = projection_manifest(projection, tables)
        for table, rows in tables.items():
            with (temporary / (table + '.jsonl')).open('w') as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            with (temporary / (table + '.csv')).open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=PROJECTION_COLUMNS[table])
                writer.writeheader()
                writer.writerows(rows)
            manifest['tables'][table] = {
                'rows': len(rows), 'jsonl': table + '.jsonl', 'csv': table + '.csv'}
        (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        os.rename(temporary, destination)
        return manifest
    except Exception:
        shutil.rmtree(temporary)
        raise
