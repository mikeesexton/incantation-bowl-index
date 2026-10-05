#!/usr/bin/env python3
"""Collect market evidence or finalize the agent's private, evidence-bound extraction."""
import argparse
import json
from pathlib import Path

from bowl_index.market_agent import collect, finish

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("collect", "finish"))
    parser.add_argument("--collection")
    parser.add_argument("--input", help="Private JSON array of candidate observations")
    args = parser.parse_args()
    root = ROOT / "data/private/monitoring/market-agent"
    if args.action == "collect":
        settings = json.loads((ROOT / "config/market_monitors.json").read_text())["settings"]
        result = collect(ROOT / "config/market_agent_sources.json", root, settings)
    else:
        if not args.collection or not args.input:
            parser.error("finish requires --collection and --input")
        result = finish(args.collection, json.loads(Path(args.input).read_text()), root,
                        ROOT / "data/private/monitoring/market")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
