"""Aggregate corpus findspot claims into a located dataset and a local map.

Reads the working database read-only. Writes research/geo/findspot_places.json
and research/geo/findspot_map.html. Changes no corpus record.

    PYTHONPATH=src .venv/bin/python research/geo/build_findspot_map.py
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = ROOT / "data/private/ibi.sqlite3"
GEO = ROOT / "research/geo"

# Best evidence first. An object is placed under the strongest tier claimed for it.
TIER_ORDER = [
    "excavation_stratified",
    "excavation_reported",
    "site_reported",
    "acquisition_site",
    "region_only",
    "unlocated",
]


def load(name):
    return json.loads((GEO / name).read_text())


def main() -> None:
    gaz = load("findspot_gazetteer.json")
    norm = load("findspot_normalization.json")
    by_value = {m["value"]: m for m in norm["mappings"]}

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    total_objects = con.execute("select count(*) from objects").fetchone()[0]
    rows = con.execute(
        """select c.object_id, o.label, c.value_text, c.certainty, c.locator,
                  s.title, s.source_type, s.issued_year
           from claims c
           join objects o on o.id = c.object_id
           join sources s on s.id = c.source_id
           where c.field = 'findspot'"""
    ).fetchall()

    # object -> best tier, and place -> objects at that tier
    obj_tier: dict[str, str] = {}
    place_objs: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    ambiguous: set[str] = set()
    obj_rows: dict[str, list] = defaultdict(list)

    for obj_id, label, value, certainty, locator, stitle, stype, syear in rows:
        m = by_value[value]
        tier = m["tier"]
        obj_rows[obj_id].append(
            {
                "value": value,
                "tier": tier,
                "certainty": certainty,
                "locator": locator,
                "source": stitle,
                "source_type": stype,
                "source_year": syear,
            }
        )
        rank = lambda t: TIER_ORDER.index(t) if t else len(TIER_ORDER)
        if rank(tier) < rank(obj_tier.get(obj_id)):
            obj_tier[obj_id] = tier
        if m.get("ambiguous"):
            ambiguous.add(obj_id)
        for place in m["places"]:
            place_objs[place][tier].add(obj_id)

    places = []
    for key, tiers in place_objs.items():
        meta = gaz["places"].get(key) or gaz["unlocated"].get(key) or gaz["regions"][key]
        # Count each object once, under its strongest tier at this place.
        seen: set[str] = set()
        counts: dict[str, int] = {}
        for tier in TIER_ORDER:
            fresh = tiers.get(tier, set()) - seen
            if fresh:
                counts[tier] = len(fresh)
                seen |= fresh
        kind = (
            "site" if key in gaz["places"]
            else "unlocated" if key in gaz["unlocated"]
            else "region"
        )
        places.append(
            {
                "key": key,
                "label": meta["label"],
                "kind": kind,
                "lat": meta.get("lat"),
                "lon": meta.get("lon"),
                "modern": meta.get("modern"),
                "note": meta.get("note") or meta.get("reason"),
                "objects": len(seen),
                "by_tier": counts,
                "best_tier": next(t for t in TIER_ORDER if t in counts),
                "object_ids": sorted(seen),
            }
        )
    places.sort(key=lambda p: (-p["objects"], p["label"]))

    with_findspot = len(obj_tier)
    located = {o for o, t in obj_tier.items() if t not in ("region_only", "unlocated")}
    dataset = {
        "generated_from": "data/private/ibi.sqlite3 (read-only)",
        "corpus_objects": total_objects,
        "objects_with_findspot_claim": with_findspot,
        "objects_with_located_findspot": len(located),
        "objects_with_no_findspot_claim": total_objects - with_findspot,
        "ambiguous_objects": sorted(ambiguous),
        "tier_totals": {
            t: sum(1 for v in obj_tier.values() if v == t) for t in TIER_ORDER
        },
        "places": places,
        "per_object": {k: v for k, v in sorted(obj_rows.items())},
    }
    (GEO / "findspot_places.json").write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n")
    print(f"corpus objects              {total_objects}")
    print(f"with a findspot claim       {with_findspot}")
    print(f"with a located findspot     {len(located)}")
    print(f"no findspot claim at all    {total_objects - with_findspot}")
    print(f"places written              {len(places)}")


if __name__ == "__main__":
    main()
