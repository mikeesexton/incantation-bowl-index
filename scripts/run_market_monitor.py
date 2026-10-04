#!/usr/bin/env python3
"""Run one lead-only pass of the auction-listing monitor.

The corpus is opened read-only, only to flag lots that may already be recorded.
"""

import argparse
import json
import sqlite3
from pathlib import Path

from bowl_index.market import market_ledger
from bowl_index.market_monitor import run_market_monitor


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "market_monitors.json"))
    parser.add_argument("--destination",
                        default=str(PROJECT_ROOT / "data" / "private" / "monitoring" / "market"))
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "private" / "ibi.sqlite3"))
    args = parser.parse_args()
    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        ledger = market_ledger(conn)
    finally:
        conn.close()
    result = run_market_monitor(Path(args.config), Path(args.destination), ledger=ledger)
    print(json.dumps(result, indent=2, sort_keys=True))
    if any(item.get("disposition") == "error" for item in result["requests"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
