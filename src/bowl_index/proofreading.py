"""Apply scan-checked text revisions without losing OCR or granting publication rights."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader


def digest_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


# A proofreading review asserts that a text matches the scan. Whether that text may
# be published is a separate decision recorded in text_publication_reviews, and
# flipping public_ok must not invalidate the reading check.
PUBLICATION_ADMIN_FIELDS = ('public_ok',)


def text_fingerprint(row, include_publication_admin=True):
    payload = dict(row)
    if not include_publication_admin:
        for field in PUBLICATION_ADMIN_FIELDS:
            payload.pop(field, None)
    return digest_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _matches(review, row):
    """A review is current while the text it checked is unchanged.

    Compares against the reviewer's own after-snapshot rather than a hash of the
    whole row, so a later publication decision does not invalidate a reading
    check. Any change to the text itself still does. Falls back to the stored
    digest when a snapshot is unavailable.
    """
    try:
        after = json.loads(review['after_json'])
    except (KeyError, TypeError, ValueError):
        return review['result_text_sha256'] == text_fingerprint(row)
    if not isinstance(after, dict) or 'content' not in after:
        return review['result_text_sha256'] == text_fingerprint(row)
    current = dict(row)
    for field in PUBLICATION_ADMIN_FIELDS:
        after.pop(field, None)
        current.pop(field, None)
    return all(current.get(key) == value for key, value in after.items())


def current_text_reviews(conn):
    latest = {}
    for row in conn.execute('SELECT * FROM text_proofreading_reviews ORDER BY rowid'):
        latest[row['text_id']] = dict(row)
    texts = {r['id']: r for r in conn.execute('SELECT * FROM texts')}
    return {key: value for key, value in latest.items()
            if key in texts and _matches(value, texts[key])}


def apply_proofreading(conn, manifest_path, project_root):
    review = json.loads(Path(manifest_path).read_text())
    if review.get('schema_version') != 1:
        raise ValueError('Unsupported proofreading manifest version')
    root = Path(project_root)
    pdf = root / review['source_pdf_path']
    source_sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if source_sha != review['source_pdf_sha256']:
        raise ValueError('Source scan hash changed')
    page_count = len(PdfReader(str(pdf)).pages)
    stamp = datetime.fromisoformat(review['reviewed_at'].replace('Z', '+00:00'))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('Review timestamp must be UTC')
    if not review.get('reviewed_by', '').strip() or not review.get('editorial_policy', '').strip():
        raise ValueError('Reviewer and editorial policy are required')
    if not review.get('entries'):
        raise ValueError('No proofreading entries')
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM captures WHERE source_id=? AND sha256=?',
                            (review['source_id'], source_sha)).fetchone():
            raise ValueError('The scan is not registered to this source')
        planned, seen = [], set()
        for entry in review['entries']:
            text_id = entry['text_id']
            if text_id in seen:
                raise ValueError('Duplicate text in proofreading batch')
            seen.add(text_id)
            old_row = conn.execute('SELECT * FROM texts WHERE id=?', (text_id,)).fetchone()
            if not old_row or old_row['source_id'] != review['source_id']:
                raise ValueError('Missing text or source mismatch')
            old = dict(old_row)
            content = (root / entry['corrected_content_path']).read_text().rstrip('\n')
            if not content.strip() or digest_text(content) != entry['corrected_content_sha256']:
                raise ValueError('Corrected content hash mismatch or empty text')
            pages = entry['pdf_pages']
            if not pages or any(type(p) is not int or not 1 <= p <= page_count for p in pages):
                raise ValueError('Invalid scan page range')
            if entry['status'] not in ('reading_text_checked', 'partial_review') or not entry.get('correction_notes', '').strip():
                raise ValueError('Status and correction notes are required')
            prior = conn.execute('SELECT * FROM text_proofreading_reviews WHERE id=?', (entry['review_id'],)).fetchone()
            if prior:
                same = (prior['text_id'] == text_id and prior['source_id'] == review['source_id']
                        and prior['source_sha256'] == source_sha
                        and prior['expected_text_sha256'] == entry['expected_text_sha256']
                        and prior['status'] == entry['status']
                        and prior['source_pages_json'] == json.dumps(pages)
                        and prior['editorial_policy'] == review['editorial_policy']
                        and prior['correction_notes'] == entry['correction_notes']
                        and prior['reviewed_by'] == review['reviewed_by']
                        and prior['reviewed_at'] == stamp.isoformat(timespec='seconds')
                        and json.loads(prior['after_json'])['content'] == content
                        and prior['result_text_sha256'] == text_fingerprint(old))
                if not same:
                    raise ValueError('Review ID reused with different or stale evidence')
                continue
            if text_fingerprint(old) != entry['expected_text_sha256']:
                raise ValueError('Text changed since proofreading snapshot')
            after = dict(old, content=content, public_ok=0,
                         notes='Scan-checked normalized English reading text. ' + review['editorial_policy']
                               + ' Review: ' + entry['review_id'] + '. Public reuse remains unapproved.')
            planned.append((entry, old, after))
        for entry, old, after in planned:
            conn.execute('UPDATE texts SET content=?,notes=?,public_ok=0 WHERE id=?',
                         (after['content'], after['notes'], old['id']))
            conn.execute('INSERT INTO text_proofreading_reviews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                entry['review_id'], old['id'], review['source_id'], source_sha,
                entry['expected_text_sha256'], text_fingerprint(after), entry['status'],
                review['reviewed_by'], stamp.isoformat(timespec='seconds'), json.dumps(entry['pdf_pages']),
                review['editorial_policy'], entry['correction_notes'],
                json.dumps(old, ensure_ascii=False, sort_keys=True),
                json.dumps(after, ensure_ascii=False, sort_keys=True)))
            changed += 1
    return {'entries': len(review['entries']), 'changed': changed,
            'unchanged': len(review['entries']) - changed, 'public_approvals': 0}
