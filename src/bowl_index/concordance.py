"""Dated museum-page observations supporting existing Montgomery identity links.

These reviews neither merge objects nor certify unrelated museum metadata.
The observation is a reviewer record, not a hash-verified capture of a web page.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .dedupe import _identity_roots


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def concordance_evidence(conn, object_id, text_number, penn_web_id, roots=None):
    roots = _identity_roots(conn) if roots is None else roots
    if object_id not in roots:
        raise ValueError('Missing publication object')
    members = sorted(k for k, v in roots.items() if v == roots[object_id])
    publication = [dict(r) for r in conn.execute(
        "SELECT * FROM identifiers WHERE object_id=? AND scheme='Montgomery 1913 text number' "
        "AND value=? ORDER BY id", (object_id, str(text_number)))]
    museum = [dict(r) for r in conn.execute(
        "SELECT * FROM identifiers WHERE scheme='Penn web object ID' AND value=? ORDER BY id",
        (penn_web_id,)) if r['object_id'] in members]
    if len(publication) != 1 or len(museum) != 1:
        raise ValueError('Publication/Penn mapping is absent or ambiguous')
    pub, web = publication[0], museum[0]
    source_ids = sorted({pub['source_id'], web['source_id']})
    sources = [dict(conn.execute('SELECT * FROM sources WHERE id=?', (s,)).fetchone())
               for s in source_ids]
    identifiers = [dict(r) for r in conn.execute(
        'SELECT * FROM identifiers WHERE object_id IN (?,?) AND source_id IN (?,?) ORDER BY id',
        (object_id, web['object_id'], pub['source_id'], web['source_id']))]
    claims = [dict(r) for r in conn.execute(
        "SELECT * FROM claims WHERE object_id=? AND source_id=? "
        "AND field IN ('publication_heading_identifier','publication_register_identifier') ORDER BY id",
        (object_id, pub['source_id']))]
    links = [dict(r) for r in conn.execute(
        'SELECT * FROM appearance_object_links WHERE object_id IN (?,?) ORDER BY appearance_id,object_id',
        (object_id, web['object_id']))]
    return dict(object_id=object_id, text_number=text_number, penn_web_id=penn_web_id,
                member_ids=members, publication_source_id=pub['source_id'],
                museum_source_id=web['source_id'], museum_object_id=web['object_id'],
                sources=sources, identifiers=identifiers, publication_number_claims=claims,
                appearance_links=links)


def _utc(value):
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('Observation and review timestamps must be UTC')
    return stamp


def apply_concordance_review(conn, path):
    manifest = json.loads(Path(path).read_text())
    if manifest.get('schema_version') != 1 or not manifest.get('entries'):
        raise ValueError('Invalid concordance manifest')
    for key in ('reviewed_by', 'method', 'scope'):
        if not manifest.get(key, '').strip():
            raise ValueError('Reviewer, method and scope are required')
    reviewed_at = _utc(manifest['reviewed_at'])
    header = {k: v for k, v in manifest.items() if k != 'entries'}
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute('BEGIN IMMEDIATE')
        roots = _identity_roots(conn)
        seen, ids, planned = set(), set(), []
        for entry in manifest['entries']:
            n = entry['text_number']
            if type(n) is not int or not 1 <= n <= 40:
                raise ValueError('Invalid main-cohort number')
            key = (entry['object_id'], entry['penn_web_id'])
            if key in seen or entry['review_id'] in ids:
                raise ValueError('Duplicate concordance review')
            seen.add(key); ids.add(entry['review_id'])
            if entry['status'] not in ('confirmed', 'unresolved') or not entry.get('rationale', '').strip():
                raise ValueError('Status and rationale are required')
            evidence = concordance_evidence(conn, key[0], n, key[1], roots=roots)
            digest = fingerprint(evidence)
            if digest != entry['expected_evidence_sha256']:
                raise ValueError('Concordance evidence changed since review snapshot')
            observation = entry['observation']
            if _utc(observation['observed_at']) > reviewed_at:
                raise ValueError('Observation cannot postdate review')
            url = 'https://collections.penn.museum/collections/object/' + entry['penn_web_id']
            museum_source = next(s for s in evidence['sources'] if s['id'] == evidence['museum_source_id'])
            if observation['url'] != url or museum_source['url'] != url:
                raise ValueError('Museum source URL mismatch')
            fields = observation['fields']
            if not observation.get('locator', '').strip() or not fields.get('Object Number'):
                raise ValueError('Observation needs a locator and object number')
            if entry['status'] == 'confirmed':
                numbers = re.findall(r'PBS III:\s*(\d+)\s*- Other Number', fields.get('Other Number', ''))
                if numbers != [str(n)]:
                    raise ValueError('Observed publication number does not match')
                matches = [i for i in evidence['identifiers']
                           if i['object_id'] == evidence['museum_object_id']
                           and i['source_id'] == evidence['museum_source_id']
                           and i['scheme'] == 'collection designation'
                           and i['value'] == fields['Object Number']]
                if not matches:
                    raise ValueError('Observed museum object number does not match')
            payload = canonical(dict(header=header, entry=entry))
            prior = conn.execute('SELECT * FROM museum_concordance_reviews WHERE id=?',
                                 (entry['review_id'],)).fetchone()
            if prior:
                if prior['review_json'] != payload or prior['evidence_sha256'] != digest:
                    raise ValueError('Review ID reused with different evidence or observations')
                continue
            planned.append((entry, evidence, digest, payload))
        for entry, evidence, digest, payload in planned:
            conn.execute('INSERT INTO museum_concordance_reviews VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                entry['review_id'], entry['object_id'], evidence['publication_source_id'],
                evidence['museum_source_id'], entry['text_number'], entry['penn_web_id'],
                entry['status'], reviewed_at.isoformat(timespec='seconds'), digest,
                canonical(evidence), payload))
            changed += 1
    return dict(entries=len(manifest['entries']), changed=changed,
                unchanged=len(manifest['entries']) - changed, identity_changes=0)


def current_concordance_reviews(conn):
    latest = {}
    for row in conn.execute('SELECT * FROM museum_concordance_reviews ORDER BY rowid'):
        latest[(row['object_id'], row['penn_web_id'])] = dict(row)
    roots = _identity_roots(conn)
    current = {}
    for key, review in latest.items():
        try:
            evidence = concordance_evidence(conn, key[0], review['text_number'], key[1], roots=roots)
        except ValueError:
            continue
        if fingerprint(evidence) == review['evidence_sha256']:
            current[key] = review
    return current
