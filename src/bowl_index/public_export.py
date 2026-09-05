"""A deliberately narrow, media-gated reference export; never a private DB dump."""
import csv
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .identity import identity_rows
from .rights import current_media_reviews, media_evidence


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
            'texts': ('id','object_id','source_id','text_type','language','script','editor','locator','rights_status','content'),
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
        tables['texts'] = [dict(r) for r in conn.execute('SELECT '+','.join(columns['texts'])+' FROM texts WHERE public_ok=1 ORDER BY id')]
        tables['media'] = [{**{key: evidence[mid][key] for key in columns['media'] if key != 'attribution'},
                            'attribution': reviews[mid]['attribution']} for mid in sorted(approved)]
        tables['identity_clusters'] = [{key: row[key] for key in columns['identity_clusters']} for row in identity_rows(conn)]
        manifest = {'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'export_policy': 'Reference scaffold with explicit text and media gates. Not a certification of scholarly accuracy. '
            'No capture records/files, claim payloads, notes, raw JSON, or review history. No public dashboard is deployed.',
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
