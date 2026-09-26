#!/usr/bin/env python3
"""Run one metadata-only shadow-monitoring pass without opening the corpus DB."""

import argparse
import json
from pathlib import Path

from bowl_index.shadow import run_shadow


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config" / "shadow_monitors.json"),
    )
    parser.add_argument(
        "--destination",
        default=str(PROJECT_ROOT / "data" / "private" / "monitoring"),
    )
    args = parser.parse_args()
    result = run_shadow(Path(args.config), Path(args.destination))
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["summary"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
