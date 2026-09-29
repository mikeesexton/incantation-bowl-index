"""Report scan-review coverage without exporting any protected text."""

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bowl_index.db import connect
from bowl_index.proofreading import current_text_reviews


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'data/reports/proofreading_status.md'
INVENTORY = ROOT / 'data/private/proofreading_inventory.csv'
EDITION_TYPES = {'translation', 'transcription', 'transliteration'}


def main():
    conn = connect()
    reviews = current_text_reviews(conn)
    source_titles = {row['id']: row['title'] for row in conn.execute('SELECT id,title FROM sources')}
    rows = []
    for row in conn.execute('SELECT id,source_id,text_type,language,locator FROM texts ORDER BY source_id,id'):
        review = reviews.get(row['id'])
        rows.append({
            'text_id': row['id'], 'source_id': row['source_id'],
            'source_title': source_titles.get(row['source_id'], ''),
            'text_type': row['text_type'], 'language': row['language'] or '',
            'locator': row['locator'] or '',
            'review_status': review['status'] if review else 'unreviewed',
            'review_id': review['id'] if review else '',
        })
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    with INVENTORY.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def counts(items):
        result = Counter(row['review_status'] for row in items)
        return [result['reading_text_checked'], result['partial_review'], result['unreviewed']]

    edition = [row for row in rows if row['text_type'] in EDITION_TYPES]
    other = [row for row in rows if row['text_type'] not in EDITION_TYPES]
    today = datetime.now(timezone.utc).date().isoformat()
    lines = [
        '# Scan proofreading progress', '',
        f'Generated {today} from the local corpus and current append-only proofreading reviews.',
        'This report contains counts and source titles only. The private row-level queue, including text IDs and locators, is `data/private/proofreading_inventory.csv`.',
        '',
        'A completed review means a normalized reading text was compared with its source pages. It does not certify an original inscription where the reviewed row is a translation, resolve scholarly uncertainty, or grant public reuse. “Unreviewed” means no current review is in the ledger; some rows were manually keyed or checked by another process.',
        '',
        '| Scope | Checked | Partial | Unreviewed | Total | Checked share |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for label, items in [('Edition text (translation, transcription, transliteration)', edition),
                         ('Other stored text (mostly source extracts and summaries)', other),
                         ('All stored text', rows)]:
        checked, partial, pending = counts(items)
        lines.append(f'| {label} | {checked} | {partial} | {pending} | {len(items)} | {checked / len(items):.1%} |')
    lines += ['', '## Edition text by type', '',
              '| Type | Checked | Partial | Unreviewed | Total |',
              '|---|---:|---:|---:|---:|']
    for kind in ('translation', 'transcription', 'transliteration'):
        items = [row for row in edition if row['text_type'] == kind]
        checked, partial, pending = counts(items)
        lines.append(f'| {kind} | {checked} | {partial} | {pending} | {len(items)} |')
    by_source = defaultdict(list)
    for row in edition:
        by_source[row['source_id']].append(row)
    lines += ['', '## Edition text by source', '',
              '| Source | Checked | Partial | Unreviewed | Total |',
              '|---|---:|---:|---:|---:|']
    for source_id, items in sorted(by_source.items(), key=lambda entry: (-counts(entry[1])[2], entry[0])):
        checked, partial, pending = counts(items)
        title = source_titles.get(source_id, source_id).replace('|', '\\|').replace('\n', ' ')
        lines.append(f'| {title} (`{source_id}`) | {checked} | {partial} | {pending} | {len(items)} |')
    REPORT.write_text('\n'.join(lines) + '\n')
    print(f'{REPORT}: {len(edition)} edition rows, {counts(edition)} checked/partial/unreviewed')
    print(f'{INVENTORY}: {len(rows)} private row-level records')


if __name__ == '__main__':
    main()
