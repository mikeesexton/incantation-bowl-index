"""Evidence-bound repairs of citation pointers, retaining exact original claims."""
import hashlib
import json
from datetime import datetime
from pathlib import Path


def previously_repaired_locator_import(conn, object_id, appearance_id, source_id, claim, locator):
    """Recognize exact historical imports without suppressing a different claim."""
    expected = dict(object_id=object_id, appearance_id=appearance_id, source_id=source_id,
                    field=claim['field'], value_text=claim.get('value_text'),
                    value_json=json.dumps(claim['value_json'], ensure_ascii=False, sort_keys=True)
                    if claim.get('value_json') is not None else None,
                    normalized_value=claim.get('normalized_value'),
                    certainty=claim.get('certainty', 'reported'), locator=locator,
                    quotation=claim.get('quotation'), notes=claim.get('notes'))
    for row in conn.execute(
        'SELECT h.before_json,h.after_json FROM claim_locator_corrections h '
        'JOIN claims c ON c.id=h.claim_id '
        'WHERE c.object_id=? AND c.appearance_id=? AND c.source_id=?',
        (object_id, appearance_id, source_id),
    ):
        for key in ('before_json', 'after_json'):
            snapshot = json.loads(row[key])
            if all(snapshot.get(field) == value for field, value in expected.items()):
                return True
    return False


def apply_locator_corrections(conn, manifest, root):
    if manifest.get('schema_version') != 1:
        raise ValueError('unsupported locator correction schema')
    reviewer = manifest.get('reviewed_by', '').strip()
    stamp = manifest.get('reviewed_at', '')
    parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if not reviewer or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError('reviewer and UTC timestamp required')
    evidence = Path(root) / manifest['evidence_path']
    if hashlib.sha256(evidence.read_bytes()).hexdigest() != manifest['evidence_sha256']:
        raise ValueError('correction evidence changed')
    if conn.in_transaction:
        raise ValueError('correction requires a clean transaction')
    seen = set()
    applied = 0
    conn.execute('BEGIN IMMEDIATE')
    try:
        for entry in manifest['entries']:
            before = entry['before']
            claim_id = before['id']
            if claim_id in seen:
                raise ValueError('duplicate claim correction')
            seen.add(claim_id)
            if not entry.get('locator', '').strip() or not entry.get('rationale', '').strip():
                raise ValueError('locator and rationale required')
            after = dict(before, locator=entry['locator'])
            if before == after:
                raise ValueError('correction must change the locator')
            row = conn.execute('SELECT * FROM claims WHERE id=?', (claim_id,)).fetchone()
            if row is None:
                raise ValueError('claim missing')
            payload = dict(id=entry['id'], claim_id=claim_id, reviewed_by=reviewer,
                           reviewed_at=stamp, evidence_path=manifest['evidence_path'],
                           evidence_sha256=manifest['evidence_sha256'], rationale=entry['rationale'],
                           before_json=json.dumps(before, ensure_ascii=False, sort_keys=True),
                           after_json=json.dumps(after, ensure_ascii=False, sort_keys=True))
            old = conn.execute('SELECT * FROM claim_locator_corrections WHERE id=?', (entry['id'],)).fetchone()
            if old:
                if dict(old) != payload or dict(row) != after:
                    raise ValueError('correction replay differs from recorded evidence')
                continue
            if dict(row) != before:
                raise ValueError('claim evidence changed')
            conn.execute('UPDATE claims SET locator=? WHERE id=?', (entry['locator'], claim_id))
            columns = list(payload)
            conn.execute('INSERT INTO claim_locator_corrections (%s) VALUES (%s)' %
                         (','.join(columns), ','.join('?' for _ in columns)), list(payload.values()))
            applied += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {'applied': applied, 'unchanged': len(seen) - applied}
