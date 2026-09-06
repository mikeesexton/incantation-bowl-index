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
    'No public dashboard is deployed. A withheld text keeps its citation, locator and link so a '
    'reader can consult the edition; the editions table names where each object has been published.'
)
LICENSE_SCOPE = (
    "Covers this project's own contribution: records, concordances, judgments, summaries, and the "
    "selection and arrangement. Text rows marked public_domain_expired in the publication ledger "
    "are public domain and are not licensed here. Withheld rows carry a pointer only; the source's "
    "own terms govern them. Media are URLs and none is approved for reuse. See docs/licensing.md."
)


def projection_manifest(projection, tables):
    """The manifest the exporter writes and the reader API serves, minus file names."""
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'export_policy': EXPORT_POLICY,
        'license': 'CC-BY-4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'attribution': ('Gabai, Moses. Incantation Bowl Index. '
                        'https://github.com/mikeesexton/incantation-bowl-index'),
        'license_scope': LICENSE_SCOPE,
        **projection.gate_counts(tables['texts']),
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
