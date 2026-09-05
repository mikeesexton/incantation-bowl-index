"""A deliberately narrow, media-gated reference export; never a private DB dump."""
import csv
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .identity import identity_rows
from .publication import current_text_reviews
from .rights import current_media_reviews, media_evidence


EDITION_SOURCE_TYPES = ('book', 'article', 'chapter', 'catalogue', 'thesis', 'excavation_report')


def _access_link(source, forbidden):
    """A citation is a pointer only if a reader can act on it.

    Prefers a DOI, falls back to the source URL, and yields nothing rather than
    emitting a string the media/capture guard forbids. Callers always emit the
    citation and locator too, so an object never loses its pointer entirely.
    """
    doi = (source.get('doi') or '').strip()
    if doi:
        link = doi if doi.startswith('http') else 'https://doi.org/' + doi
        if not any(private and private in link for private in forbidden):
            return link
    url = (source.get('url') or '').strip()
    if url.startswith(('http://', 'https://')) and not any(
        private and private in url for private in forbidden
    ):
        return url
    return None


def export_public(conn, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Public export requires a new destination; existing files may contain private data')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.ibi-public-', dir=destination.parent))
    try:
        reviews, evidence = current_media_reviews(conn), media_evidence(conn)
        approved = {key for key, r in reviews.items() if r['public_reuse_decision'] == 'approved'}
        # Conflicting reviews for the same resource fail closed.
        blocked_urls = {row['url'] for key, row in evidence.items() if key not in approved and row['url']}
        approved = {key for key in approved if evidence[key]['url'] not in blocked_urls}
        allowed_urls = {evidence[key]['url'] for key in approved}
        forbidden = blocked_urls | {r['storage_path'] for r in conn.execute('SELECT storage_path FROM captures')}
        forbidden |= {r['url'] for r in conn.execute('SELECT url FROM captures') if r['url'] not in allowed_urls}
        columns = {
            'sources': ('id','source_type','title','authors','issued_year','citation','doi','isbn'),
            'objects': ('id','label','object_type','record_status','authenticity'),
            'appearances': ('id','source_id','locator'),
            'appearance_object_links': ('appearance_id','object_id','relation_type','confidence','rationale'),
            'texts': ('id','object_id','source_id','text_type','language','script','editor','locator',
                      'rights_status','content_status','content','access_citation','access_locator',
                      'access_url','access_status'),
            'editions': ('object_id','source_id','source_type','citation','locator','access_url','access_status'),
            'media': ('id','object_id','appearance_id','source_id','media_type','url','attribution'),
            'identity_clusters': ('identity_id','canonical_object_id','record_status','member_count','source_count','appearance_count'),
        }
        tables = {}
        for name in ('sources','objects','appearances'):
            tables[name] = [dict(r) for r in conn.execute('SELECT '+','.join(columns[name])+' FROM '+name+' ORDER BY id')]
        # Free-text review rationales are private; keep the relation structure only.
        columns['appearance_object_links'] = ('appearance_id','object_id','relation_type','confidence')
        tables['appearance_object_links'] = [dict(r) for r in conn.execute(
            'SELECT appearance_id,object_id,relation_type,confidence FROM appearance_object_links '
            'ORDER BY appearance_id,object_id')]
        # Every text row is listed. Content appears only for a currently valid approval;
        # a withheld row still says what it is and where a reader can consult it.
        approved_texts = {key for key, review in current_text_reviews(conn).items()
                          if review['publication_decision'] == 'approved'}
        tables['texts'] = []
        for row in conn.execute(
            'SELECT t.id,t.object_id,t.source_id,t.text_type,t.language,t.script,t.editor,t.locator,'
            't.rights_status,t.content,s.citation source_citation,s.url source_url,s.doi source_doi,'
            's.access_status source_access_status FROM texts t JOIN sources s ON s.id=t.source_id '
            'ORDER BY t.id'
        ):
            row = dict(row)
            included = row['id'] in approved_texts
            tables['texts'].append({
                'id': row['id'], 'object_id': row['object_id'], 'source_id': row['source_id'],
                'text_type': row['text_type'], 'language': row['language'], 'script': row['script'],
                'editor': row['editor'], 'locator': row['locator'],
                'rights_status': row['rights_status'],
                'content_status': 'included' if included else 'withheld_consult_the_edition',
                'content': row['content'] if included else None,
                'access_citation': row['source_citation'],
                'access_locator': row['locator'],
                'access_url': _access_link(
                    {'doi': row['source_doi'], 'url': row['source_url']}, forbidden
                ),
                'access_status': row['source_access_status'],
            })
        # Where a bowl's text is published but cannot be reproduced here, name the editions.
        tables['editions'] = []
        seen_editions = set()
        for row in conn.execute(
            'SELECT l.object_id,s.id source_id,s.source_type,s.citation,a.locator,s.url,s.doi,'
            's.access_status FROM appearance_object_links l '
            'JOIN appearances a ON a.id=l.appearance_id JOIN sources s ON s.id=a.source_id '
            'WHERE s.source_type IN (' + ','.join('?' for _ in EDITION_SOURCE_TYPES) + ') '
            'ORDER BY l.object_id,s.id,a.locator', EDITION_SOURCE_TYPES
        ):
            row = dict(row)
            key = (row['object_id'], row['source_id'], row['locator'])
            if key in seen_editions:
                continue
            seen_editions.add(key)
            tables['editions'].append({
                'object_id': row['object_id'], 'source_id': row['source_id'],
                'source_type': row['source_type'], 'citation': row['citation'],
                'locator': row['locator'],
                'access_url': _access_link({'doi': row['doi'], 'url': row['url']}, forbidden),
                'access_status': row['access_status'],
            })
        tables['media'] = [{**{key: evidence[mid][key] for key in columns['media'] if key != 'attribution'},
                            'attribution': reviews[mid]['attribution']} for mid in sorted(approved)]
        tables['identity_clusters'] = [{key: row[key] for key in columns['identity_clusters']} for row in identity_rows(conn)]
        manifest = {'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'export_policy': 'Reference scaffold with explicit text and media gates. Not a certification of scholarly accuracy. '
            'No capture records/files, claim payloads, notes, raw JSON, or review history. No public dashboard is deployed. '
            'A withheld text keeps its citation, locator and link so a reader can consult the edition; '
            'the editions table names where each object has been published.',
            'license': 'CC-BY-4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'attribution': 'Gabai, Moses. Incantation Bowl Index. '
                           'https://github.com/mikeesexton/incantation-bowl-index',
            'license_scope': (
                'Covers this project\'s own contribution: records, concordances, judgments, '
                'summaries, and the selection and arrangement. Text rows marked '
                'public_domain_expired in the publication ledger are public domain and are not '
                'licensed here. Withheld rows carry a pointer only; the source\'s own terms '
                'govern them. Media are URLs and none is approved for reuse. See docs/licensing.md.'
            ),
            'texts_included_rows': len(approved_texts),
            'texts_withheld_rows': len(tables['texts']) - len(approved_texts),
            'media_approved_rows': len(approved), 'media_withheld_rows': len(evidence)-len(approved), 'tables': {}}
        for table, rows in tables.items():
            # Defense in depth: permitted metadata must not repeat known private media references.
            strings = [value for row in rows for value in row.values() if isinstance(value, str)]
            if any(private and private in value for private in forbidden for value in strings):
                raise ValueError('Public projection contains a private media/capture reference in '+table)
            with (temporary / (table+'.jsonl')).open('w') as handle:
                for row in rows: handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
            with (temporary / (table+'.csv')).open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=columns[table]); writer.writeheader(); writer.writerows(rows)
            manifest['tables'][table] = {'rows':len(rows),'jsonl':table+'.jsonl','csv':table+'.csv'}
        (temporary / 'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        os.rename(temporary, destination)
        return manifest
    except Exception:
        shutil.rmtree(temporary)
        raise
