"""Hash-bound contextual passages for Mike alone, outside bowl reading metrics.

The private registry refers to immutable source-check artifacts and a retained
document assessment. It makes no scholarly or public-release decision. Missing,
changed or wrongly assigned evidence fails closed before any rows are returned.
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime

from .db import PROJECT_ROOT


REGISTRY = Path('data/private/reader/source_contexts.json')
KINDS = {'provided_transcription', 'transliteration', 'provided_translation'}


def checked_artifact(root, record):
    rel = Path(record['path'])
    candidate = (root / rel).resolve()
    if rel.is_absolute() or '..' in rel.parts or not candidate.is_relative_to(root):
        raise ValueError('Source-context evidence must remain inside the project')
    if not candidate.is_file() or (root / rel).is_symlink():
        raise ValueError('Source-context evidence missing or symlinked')
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Source-context artifact changed')
    return candidate


def source_context_inventory(conn, capture_urls=None, root=PROJECT_ROOT, registry=None):
    root = Path(root).resolve()
    if registry is None:
        database = next(row[2] for row in conn.execute('PRAGMA database_list') if row[1] == 'main')
        if not database:
            return []
        path = Path(database).parent / 'reader' / 'source_contexts.json'
    else:
        path = root / registry
    if not path.exists():
        return []
    # The registry itself may never be an external file or a symlink.
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError('Invalid private source-context registry path')
    manifest = json.loads(path.read_text())
    if manifest.get('schema_version') != 1 or not isinstance(manifest.get('entries'), list):
        raise ValueError('A version1 private source-context registry is required')
    sources = {row['id']: dict(row) for row in conn.execute('SELECT * FROM sources')}
    captures = {row['id']: dict(row) for row in conn.execute('SELECT * FROM captures')}
    rows, seen, verified_sources = [], set(), set()
    for entry in manifest['entries']:
        if entry['id'] in seen or entry['kind'] not in KINDS:
            raise ValueError('Duplicate source context or invalid kind')
        seen.add(entry['id'])
        stamp = datetime.fromisoformat(entry['reviewed_at'].replace('Z', '+00:00'))
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('Source-context review timestamp must be UTC')
        if entry['source_copy_status'] != 'source_copy_checked' or not entry['reviewed_by'].strip():
            raise ValueError('An attributed source-copy check is required')
        if (not isinstance(entry['pdf_pages'], list) or not entry['pdf_pages']
                or any(type(page) is not int or page < 1 for page in entry['pdf_pages'])):
            raise ValueError('Positive source-context PDF pages required')
        source = sources.get(entry['source_id']); capture = captures.get(entry['capture_id'])
        if not source or not capture or capture['source_id'] != entry['source_id']:
            raise ValueError('Source-context capture assignment differs')
        if entry['source_sha256'] != capture['sha256']:
            raise ValueError('Source-context capture hash differs')
        assessment = conn.execute('SELECT * FROM document_assessments WHERE id=?',
                                  (entry['assessment_id'],)).fetchone()
        if (not assessment or assessment['source_id'] != source['id']
                or assessment['capture_id'] != capture['id']
                or assessment['document_sha256'] != entry['source_sha256']
                or assessment['extraction_sha256'] != entry['extraction']['sha256']
                or assessment['extraction_path'] != entry['extraction']['path']):
            raise ValueError('Source-context document assessment differs')
        extraction = json.loads(checked_artifact(root, entry['extraction']).read_text())
        bundle = json.loads(checked_artifact(root, entry['checked_bundle']).read_text())
        if extraction.get('current_contexts') != entry['checked_bundle']:
            raise ValueError('Source-context bundle is not bound to the assessment')
        source_pdf = bundle['source_pdf']
        if source_pdf['sha256'] != entry['source_sha256']:
            raise ValueError('Source-context original PDF hash differs')
        source_key = (source_pdf['path'], source_pdf['sha256'])
        if source_key not in verified_sources:
            checked_artifact(root, source_pdf)
            verified_sources.add(source_key)
        artifact = entry['artifact']
        if entry.get('bundle_unit_id'):
            units = [u for u in bundle['units'] if u['id'] == entry['bundle_unit_id']]
            if len(units) != 1:
                raise ValueError('Source-context check unit missing or duplicated')
            unit = units[0]
            for field in ['source_id', 'kind', 'language', 'script', 'editor', 'locator',
                          'source_copy_status', 'reviewed_by', 'reviewed_at', 'notes', 'artifact']:
                if entry.get(field) != unit.get(field):
                    raise ValueError('Source-context registry differs from its source check')
            if entry['pdf_pages'] != [unit['pdf_page']]:
                raise ValueError('Source-context page differs')
            if entry.get('editorial_annotations', []) != unit.get('editorial_annotations', []):
                raise ValueError('Source-context annotations differ')
        else:
            # Earlier pairs have their own hash-bound review; the current bundle
            # explicitly references that review and the two retained copy files.
            evidence = entry['pair_review']
            if evidence not in bundle['prior_contexts'] or artifact not in bundle['prior_contexts']:
                raise ValueError('Earlier source-context evidence is not retained')
            review = json.loads(checked_artifact(root, evidence).read_text())
            expected = {'source_checked_native': ('provided_transcription', 'Mandaic', 'Hebrew'),
                        'source_checked_English': ('provided_translation', 'English', None)}
            if (entry['pair_review_field'] not in expected
                    or (entry['kind'], entry['language'], entry['script']) != expected[entry['pair_review_field']]):
                raise ValueError('Earlier source-context kind or language differs')
            if (review['source_id'] != entry['source_id'] or review['capture_id'] != entry['capture_id']
                    or review['source_pdf']['sha256'] != entry['source_sha256']
                    or review[entry['pair_review_field']] != artifact
                    or review['locator'] != entry['locator'] or review['editor'] != entry['editor']
                    or review['notes'] != entry['notes']):
                raise ValueError('Earlier source-context review differs')
        content = checked_artifact(root, artifact).read_text()
        content = content[:-1] if content.endswith('\n') else content
        if entry.get('bundle_unit_id') and content != unit['content']:
            raise ValueError('Source-context copy differs from its checked unit')
        if not content.strip() or not entry['reference'].strip() or not entry['locator'].strip():
            raise ValueError('Empty source context')
        url = (capture_urls or {}).get(capture['id'])
        if url and capture['mime_type'] == 'application/pdf':
            url += '#page=' + str(entry['pdf_pages'][0])
        # Browser rows contain no vault paths. Editorial intervention is textual
        # metadata; its local image paths remain exclusively in the registry.
        annotations = [dict(substring=a['substring'], annotation=a['annotation'])
                       for a in entry.get('editorial_annotations', [])]
        rows.append({key: entry.get(key) for key in ['id', 'source_id', 'capture_id', 'reference',
                    'kind', 'language', 'script', 'editor', 'locator', 'rights_status',
                    'source_copy_status', 'reviewed_by', 'reviewed_at', 'source_sha256', 'pdf_pages', 'notes']}
                    | dict(content=content, content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                           citation=source['citation'], source_url=url, editorial_annotations=annotations))
    return rows
