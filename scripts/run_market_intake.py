#!/usr/bin/env python3
"""Read-only-corpus auction email intake, review, enrichment and daily reporting."""
import argparse
import json
import sqlite3
from pathlib import Path

from bowl_index.db import PROJECT_ROOT
from bowl_index.market_intake import (ack_report, daily_report, deposit_gmail, enrich,
                                     process, view, import_eml, image_receipt, collect_images, record_gap, record_source_checks)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('deposit', 'import-eml', 'run', 'enrich', 'review', 'status', 'report', 'ack', 'image', 'images', 'gap', 'source-check'))
    p.add_argument('--root', default=str(PROJECT_ROOT / 'data/private/monitoring/market-agent/intake'))
    p.add_argument('--config', default=str(PROJECT_ROOT / 'config/market_email_intake.json'))
    p.add_argument('--db', default=str(PROJECT_ROOT / 'data/private/ibi.sqlite3'))
    p.add_argument('--input', help='Private Gmail batch JSON, extraction overrides, or local .eml')
    p.add_argument('--packet', help='Exact JSON packet produced in this chat, for ack')
    p.add_argument('--enrich', action='store_true', help='Fetch only reviewed lot routes')
    p.add_argument('--retry-failures', action='store_true', help='Explicitly retry transport/robots failures once')
    p.add_argument('--url', help='Recorded source URL of a lawfully obtained local image')
    p.add_argument('--now', help='UTC timestamp (for rehearsals)')
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text())
    if config.get('schema_version') != 1:
        p.error('unsupported intake config')
    settings = json.loads((PROJECT_ROOT / 'config/market_monitors.json').read_text())['settings']
    root = Path(args.root)
    if args.action in ('deposit', 'review', 'import-eml', 'image', 'gap', 'source-check') and not args.input:
        p.error('--input required')
    if args.action == 'deposit':
        result = deposit_gmail(root, json.loads(Path(args.input).read_text()), config, args.now)
    elif args.action == 'import-eml':
        result = import_eml(root, Path(args.input), args.now)
    elif args.action == 'review':
        result = process(root, config, args.now, overrides=json.loads(Path(args.input).read_text()))
    elif args.action == 'source-check':
        result = record_source_checks(root, json.loads(Path(args.input).read_text()), args.now)
    elif args.action == 'gap':
        result = record_gap(root, json.loads(Path(args.input).read_text()), args.now)
    elif args.action == 'image':
        if not args.url:
            p.error('--url required')
        result = image_receipt(root, Path(args.input), args.url, args.now)
    elif args.action == 'status':
        snapshot = view(root)
        result = {'processed': len(snapshot['processed']), 'message_keys': sorted(snapshot['processed']),
                  'deposited_message_keys': sorted(p.stem for p in (root / 'inbox').glob('*.json')),
                  'deposited_message_ids': sorted(m['message_id'] for p in (root / 'inbox').glob('*.json')
                        for m in [json.loads(p.read_text())] if m.get('message_id')),
                  'listings': len(snapshot['listings']), 'counts': snapshot['counts'], 'errors': snapshot['errors']}
    elif args.action == 'ack':
        if not args.packet:
            p.error('--packet required')
        result = ack_report(root, Path(args.packet), args.now)
    else:
        result = {}
        if args.action == 'run':
            result['intake'] = process(root, config, args.now)
        if args.action == 'enrich' or args.enrich:
            result['enrichment'] = enrich(root, config, settings, now=args.now, retry_failures=args.retry_failures)
        if args.action == 'images' or args.enrich:
            result['images'] = collect_images(root, config, settings, now=args.now)
        # Never use db.connect or migrate, even for a report.
        conn = sqlite3.connect('file:%s?mode=ro' % Path(args.db).resolve(), uri=True)
        conn.row_factory = sqlite3.Row
        try:
            result['daily'] = daily_report(root, conn, args.now)
        finally:
            conn.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
