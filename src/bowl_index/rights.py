"""Evidence-bound media reuse decisions, independent of source copyright labels."""
import hashlib
import json
from datetime import datetime
from urllib.parse import urlsplit


def media_evidence(conn):
    return {r['id']: dict(r) for r in conn.execute(
        'SELECT m.*,s.title source_title,s.url source_url,s.rights_status source_rights_status,'
        'c.sha256 capture_sha256,c.url capture_url,c.rights_status capture_rights_status '
        'FROM media m JOIN sources s ON s.id=m.source_id LEFT JOIN captures c ON c.id=m.capture_id')}


def media_fingerprint(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def current_media_reviews(conn):
    evidence = media_evidence(conn)
    latest = {}
    for row in conn.execute('SELECT * FROM media_rights_reviews ORDER BY rowid'):
        latest[row['media_id']] = dict(row)
    return {key: value for key, value in latest.items()
            if key in evidence and value['evidence_sha256'] == media_fingerprint(evidence[key])}


def apply_rights_batch(conn, manifest):
    if manifest.get('schema_version') != 1 or not manifest.get('entries'):
        raise ValueError('A version 1 rights batch with entries is required')
    stamp = datetime.fromisoformat(manifest['reviewed_at'].replace('Z', '+00:00'))
    reviewer = manifest.get('reviewed_by', '').strip()
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('Named reviewer and UTC timestamp required')
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute('BEGIN IMMEDIATE')
        evidence = media_evidence(conn)
        planned, seen = [], set()
        for entry in manifest['entries']:
            media_id = entry['media_id']
            if media_id in seen or media_id not in evidence:
                raise ValueError('Duplicate or absent media')
            seen.add(media_id)
            row = evidence[media_id]
            if media_fingerprint(row) != entry['evidence_sha256']:
                raise ValueError('Media evidence changed; review again')
            decision = entry['public_reuse_decision']
            if decision not in ('needs_review', 'withhold', 'approved') or not entry.get('rationale', '').strip():
                raise ValueError('Valid decision and rationale required')
            if decision == 'needs_review' and not entry.get('followup', '').strip():
                raise ValueError('Unresolved rights require an explicit follow-up')
            if entry['private_capture_status'] not in ('not_captured','captured_private','unknown'):
                raise ValueError('Invalid private-capture status')
            if decision == 'approved':
                if urlsplit(row['url'] or '').scheme not in ('http', 'https'):
                    raise ValueError('Only explicitly reviewed HTTP(S) media URLs may be exported')
                if not all(entry.get(key, '').strip() for key in ('rights_statement', 'rights_locator', 'attribution')):
                    raise ValueError('Approval requires rights evidence, locator and attribution')
            source_url = row['url'] or row['source_url'] or ''
            if not source_url:
                raise ValueError('A media/source URL is required for the rights ledger')
            values = (entry['review_id'], media_id, entry['evidence_sha256'], entry.get('creator'),
                entry.get('rights_holder'), source_url, entry.get('rights_statement'), entry.get('rights_locator'),
                entry.get('license_url'), entry.get('jurisdiction_notes'), entry['private_capture_status'], decision,
                entry.get('attribution'), reviewer, stamp.isoformat(timespec='seconds'), entry['rationale'], entry.get('followup'))
            old = conn.execute('SELECT * FROM media_rights_reviews WHERE id=?', (entry['review_id'],)).fetchone()
            if old:
                if tuple(old) != values:
                    raise ValueError('Rights review ID reused with changed decision')
                continue
            planned.append(values)
        for values in planned:
            conn.execute('INSERT INTO media_rights_reviews VALUES (' + ','.join('?' for _ in values) + ')', values)
            changed += 1
    return {'entries': len(manifest['entries']), 'changed': changed,
            'unchanged': len(manifest['entries']) - changed}


def rights_metrics(conn):
    reviews = current_media_reviews(conn)
    total = conn.execute('SELECT count(*) FROM media').fetchone()[0]
    assessed = sum(r['public_reuse_decision'] in ('approved', 'withhold') for r in reviews.values())
    return {'media_records': total, 'media_current_ledger_rows': len(reviews),
            'media_rights_assessed': assessed, 'media_rights_assessed_pct': assessed / total if total else 1,
            'media_approved': sum(r['public_reuse_decision'] == 'approved' for r in reviews.values()),
            'media_needs_rights_review': total - assessed}
