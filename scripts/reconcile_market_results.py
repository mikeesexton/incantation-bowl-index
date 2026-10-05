#!/usr/bin/env python3
"""Record a private, source-compared lot-result link; never write the corpus."""
import argparse
import json
import sqlite3
from pathlib import Path
from bowl_index.db import PROJECT_ROOT
from bowl_index.market import market_listings
from bowl_index.market_results import record_result_link


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, help='Source comparison manifest JSON')
    p.add_argument('--root', default=str(PROJECT_ROOT / 'data/private/monitoring/market'))
    p.add_argument('--db', default=str(PROJECT_ROOT / 'data/private/ibi.sqlite3'))
    a = p.parse_args()
    conn = sqlite3.connect('file:%s?mode=ro' % Path(a.db).resolve(), uri=True)
    conn.row_factory = sqlite3.Row
    try:
        receipt = record_result_link(a.root, json.loads(Path(a.input).read_text()), market_listings(conn))
    finally:
        conn.close()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
