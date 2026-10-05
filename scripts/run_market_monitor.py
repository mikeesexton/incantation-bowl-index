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
from bowl_index.market_intake import process, enrich, collect_images, daily_report, import_eml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "market_monitors.json"))
    parser.add_argument("--destination",
                        default=str(PROJECT_ROOT / "data" / "private" / "monitoring" / "market"))
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "private" / "ibi.sqlite3"))
    args = parser.parse_args()
    root = PROJECT_ROOT / "data/private/monitoring/market-agent/intake"
    email_config = json.loads((PROJECT_ROOT / "config/market_email_intake.json").read_text())
    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        ledger = market_ledger(conn)
    finally:
        conn.close()
    result = run_market_monitor(Path(args.config), Path(args.destination), ledger=ledger)
    # The existing 06:40 LaunchAgent now also processes private email deposits.
    # Gmail itself is read only by the connected Codex pass, never via local tokens.
    for path in sorted((root.parent / "evidence/inbox").glob("*.eml")):
        import_eml(root, path)
    intake = process(root, email_config)
    settings = json.loads(Path(args.config).read_text())["settings"]
    pages = enrich(root, email_config, settings)
    images = collect_images(root, email_config, settings)
    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        packet = daily_report(root, conn)
    finally:
        conn.close()
    result["email_intake"] = {"processed": intake.get("processed", 0),
        "new_listings": intake.get("new_listings", 0), "changes": intake.get("changes", 0),
        "errors": intake.get("errors", []), "report": packet["report"],
        "page_checks": len(pages.get("coverage", [])), "image_checks": len(images.get("coverage", []))}
    print(json.dumps(result, indent=2, sort_keys=True))
    if any(item.get("disposition") == "error" for item in result["requests"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
