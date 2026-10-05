"""Evidence-bound links from a monitored auction result to a recorded occasion.

These are private presentation receipts, never corpus edits or bowl identity
matches. Cross-platform links require an explicit source comparison manifest.
"""
import json
import re
from pathlib import Path

from .market_intake import fingerprint, locked, utc
from .market_monitor import _atomic_json, _norm, _sha256, _utc_now, monitor_leads, parse_the_saleroom_lot


def listing_fingerprint(row):
    return fingerprint({k: row.get(k) for k in (
        'object_id', 'source_id', 'event_id', 'event_type', 'date', 'house',
        'url', 'locator', 'citation', 'details', 'claims')})


def result_records(root):
    records = []
    for path in sorted((Path(root) / 'results').glob('*.jsonl')):
        records.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    return records


def _validate(root, manifest, listings):
    if manifest.get('schema_version') != 1 or not manifest.get('reviewer') or not manifest.get('rationale'):
        raise ValueError('result link requires reviewer and source comparison rationale')
    utc(manifest['reviewed_at'])
    if not manifest.get('quantity_text'):
        raise ValueError('result link requires explicit lot quantity/scope wording')
    records = result_records(root)
    result = next((r for r in records if fingerprint(r) == manifest.get('result_fingerprint')), None)
    if not result or result.get('outcome') not in ('sold', 'passed'):
        raise ValueError('result link requires an archived explicit sold or unsold result')
    utc(result['observed_at'])
    if not isinstance(result.get('price_basis'), str) or not result['price_basis'].strip():
        raise ValueError('result needs an explicit monetary basis')
    sha = result.get('raw_sha256', '')
    if not re.fullmatch(r'[a-f0-9]{64}', sha):
        raise ValueError('result needs archived page hash')
    body = (Path(root) / 'raw' / sha).read_bytes()
    if _sha256(body) != sha:
        raise ValueError('altered result evidence')
    if not result.get('lot', '').startswith('the-saleroom/'):
        raise ValueError('result parser not supported for this source')
    parsed = parse_the_saleroom_lot(body.decode('utf-8', 'replace'))
    if any(parsed.get(k) != result.get(k) for k in ('sale_at', 'outcome', 'hammer_text')):
        raise ValueError('result wording does not match archived page')
    lead = next((r for r in monitor_leads(root) if r['url'] == result['url']), None)
    if not lead or not lead.get('lot_number') or not lead.get('house') or not result.get('sale_at'):
        raise ValueError('result link needs source house, lot number and complete sale date')
    targets = manifest.get('listings')
    if not isinstance(targets, list) or not targets:
        raise ValueError('result link needs exact recorded listings')
    by_key = {(r['object_id'], r['source_id'], r['event_id']): r for r in listings}
    seen, selected = set(), []
    for item in targets:
        key = (item.get('object_id'), item.get('source_id'), item.get('event_id'))
        row = by_key.get(key)
        if not row or key in seen or listing_fingerprint(row) != item.get('listing_fingerprint'):
            raise ValueError('unknown, duplicate or changed recorded listing')
        seen.add(key)
        if row['date'] != result['sale_at'][:10] or _norm(row['house']) != _norm(lead['house']) or \
                lead['lot_number'] not in re.findall(r'\blot\s+(\d+)\b', row['locator'], re.I):
            raise ValueError('result must match the full house, sale date and lot number')
        if row['event_type'] != 'offer':
            raise ValueError('only recorded offers may receive a result presentation link')
        selected.append(row)
    return result, selected


def record_result_link(root, manifest, listings):
    """Validate the complete comparison before one append-only private receipt."""
    root = Path(root)
    with locked(root):
        _validate(root, manifest, listings)
        for path in (root / 'result-links').glob('*.json'):
            if json.loads(path.read_text())['manifest'] == manifest:
                return {'recorded': 0, 'replay': True, 'corpus_writes': 0}
        receipt = {'manifest': manifest, 'recorded_at': _utc_now(), 'corpus_writes': 0}
        sequence = len(list((root / 'result-links').glob('*.json'))) + 1
        path = root / 'result-links' / ('%012d-' % sequence + fingerprint(receipt)[:12] + '.json')
        _atomic_json(path, receipt)
        return {'recorded': len(manifest['listings']), 'receipt': str(path.resolve()), 'corpus_writes': 0}


def reconcile_results(root, listings):
    """Overlay linked results while retaining original offer fields and claims."""
    issues, linked = [], set()
    for path in sorted((Path(root) / 'result-links').glob('*.json')):
        manifest = json.loads(path.read_text())['manifest']
        try:
            result, selected = _validate(root, manifest, listings)
        except (ValueError, KeyError, OSError) as exc:
            reason = 'Archived result evidence is missing or unreadable' if isinstance(exc, OSError) else str(exc)
            issues.append({'receipt': path.name, 'reason': reason})
            continue
        linked.add(manifest['result_fingerprint'])
        for row in selected:
            row['recorded_status'] = row.get('recorded_status', row['status'])
            row['result_observation'] = {**result, 'quantity_text': manifest['quantity_text'],
                'rationale': manifest['rationale'], 'link_receipt': path.name}
            row['status'] = ('sold' if result.get('hammer_text') else 'sold_no_price') if result['outcome'] == 'sold' else 'unsold'
            row['status_label'] = 'Sold · monitored result' if result['outcome'] == 'sold' else 'Unsold · monitored result'
    followups = []
    for result in result_records(root):
        if result.get('outcome') in ('sold', 'passed') and fingerprint(result) not in linked:
            followups.append({**result, 'result_fingerprint': fingerprint(result),
                'reason': 'Result captured; its recorded sale occasion still needs a source comparison link.'})
    return {'issues': issues, 'followups': followups}
