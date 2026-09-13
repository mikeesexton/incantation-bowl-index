"""Render research/geo/findspot_places.json as a self-contained local map.

Equirectangular projection with a cosine latitude correction, so every marker
position comes from the gazetteer coordinates rather than by hand. Sites in
Babylonia lie within a few kilometres of one another and overlap at national
scale, so they are drawn again in a magnified detail inset instead of being
nudged apart. Writes research/geo/findspot_map.html — a local file that loads
nothing remote and deploys nowhere.

    PYTHONPATH=src .venv/bin/python research/geo/render_findspot_map.py
"""
from __future__ import annotations

import html
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GEO = ROOT / "research/geo"

MAIN = {"lat0": 30.0, "lat1": 37.0, "lon0": 39.8, "lon1": 48.8, "w": 900}
DETAIL = {"lat0": 32.33, "lat1": 33.17, "lon0": 44.15, "lon1": 44.70, "w": 252}

TIERS = {
    "excavation_stratified": ("#7c3f10", "Excavated, with stratigraphy"),
    "excavation_reported": ("#a45235", "Reported as an excavation findspot"),
    "site_reported": ("#c98a5e", "Site named as the findspot"),
    "acquisition_site": ("#8d8878",
                         "Museum “Found/Acquired” — a site is named, but finding "
                         "and acquisition are not separated"),
}

TIGRIS = [(36.34,43.13),(35.95,43.20),(35.46,43.26),(34.80,43.55),(34.20,43.87),
          (33.75,44.10),(33.32,44.36),(32.95,44.90),(32.51,45.82),(32.10,46.55),
          (31.84,47.15),(31.30,47.35),(31.01,47.43)]
EUPHRATES = [(35.33,40.14),(34.80,41.20),(34.13,42.38),(33.60,42.90),(33.42,43.30),
             (33.35,43.78),(32.90,44.20),(32.47,44.42),(31.99,44.93),(31.32,45.29),
             (31.05,46.26),(31.01,47.43)]
SHATT = [(31.01,47.43),(30.51,47.82),(30.20,48.20),(30.02,48.45)]
KHABUR = [(36.80,40.75),(36.40,40.85),(36.07,40.93),(35.60,40.65),(35.15,40.43)]
GULF = [(30.40,48.05),(30.30,48.45),(30.20,48.80),(30.00,48.80),(30.00,48.25)]

# Drawn in the magnified inset rather than labelled on the national map.
DETAIL_KEYS = ["seleucia", "tell_baruda", "sippar", "babylon",
               "amran_babylon", "hillah", "borsippa"]

SHORT = {"seleucia": "Seleucia", "amran_babylon": "Amran ibn Ali",
         "tell_baruda": "Tell Baruda", "hillah": "Al-Hillah"}

# Which keys carry a label on each frame. Positions are solved, not hand-set.
MAIN_LABELLED = ["nippur", "kutha", "khorsabad", "nimrud", "nineveh", "ashur",
                 "baghdad", "khafajah", "uruk", "susa", "kermanshah", "arban"]
DETAIL_LABELLED = ["seleucia", "tell_baruda", "sippar", "babylon",
                   "amran_babylon", "hillah", "borsippa"]


class Frame:
    def __init__(self, b):
        self.lat0, self.lat1 = b["lat0"], b["lat1"]
        self.lon0, self.lon1 = b["lon0"], b["lon1"]
        self.kx = math.cos(math.radians((self.lat0 + self.lat1) / 2))
        self.w = b["w"]
        self.scale = self.w / ((self.lon1 - self.lon0) * self.kx)
        self.h = (self.lat1 - self.lat0) * self.scale

    def xy(self, lat, lon):
        return ((lon - self.lon0) * self.kx * self.scale,
                (self.lat1 - lat) * self.scale)

    def holds(self, p):
        return (self.lon0 < p["lon"] < self.lon1) and (self.lat0 < p["lat"] < self.lat1)

    def path(self, pts, close=False):
        d = " ".join(("M" if i == 0 else "L") + "%.1f %.1f" % self.xy(la, lo)
                     for i, (la, lo) in enumerate(pts))
        return d + ("Z" if close else "")


def radius(n, k=3.1):
    return 4.6 + math.sqrt(n) * k


def place_labels(frame, items, char_w, line_h):
    """Choose a label position for each item that avoids markers, other labels
    and the canvas edge. Biggest sites are placed first and keep the best spot."""
    dirs = [(1, 0, "start"), (-1, 0, "end"), (1, -1, "start"), (-1, -1, "end"),
            (1, 1, "start"), (-1, 1, "end"), (0, -1, "middle"), (0, 1, "middle")]
    placed = []
    for it in items:
        w = len(it["name"]) * char_w + 20
        best, best_cost = None, None
        for gap in (8, 22, 38, 56):
            for ux, uy, anchor in dirs:
                dx = ux * (it["r"] + gap)
                dy = uy * (it["r"] + gap) + (line_h * 0.35 if uy == 0 else 0)
                cx, cy = it["x"] + dx, it["y"] + dy
                x0 = cx if anchor == "start" else cx - w if anchor == "end" else cx - w / 2
                box = (x0, cy - line_h * 0.78, x0 + w, cy + line_h * 0.24)
                cost = gap * 0.35
                if box[0] < 2 or box[2] > frame.w - 2 or box[1] < 2 or box[3] > frame.h - 2:
                    cost += 600
                for o in items:
                    nx = max(box[0], min(o["x"], box[2]))
                    ny = max(box[1], min(o["y"], box[3]))
                    over = o["r"] - math.hypot(o["x"] - nx, o["y"] - ny)
                    if over > 0:
                        cost += 40 + over * 5
                for pb in placed:
                    if box[0] < pb[2] and pb[0] < box[2] and box[1] < pb[3] and pb[1] < box[3]:
                        cost += 220
                cost += 4 if ux < 0 else 0          # prefer labels to the right
                cost += 3 if anchor == "middle" else 0
                if best_cost is None or cost < best_cost:
                    best, best_cost = (cx, cy, anchor, box, gap), cost
        placed.append(best[3])
        it["label_at"] = best
    return items


def draw(frame, places, labelled, rscale=3.1, fontclass="", char_w=6.5, line_h=13):
    items = []
    for p in sorted(places, key=lambda p: -p["objects"]):
        x, y = frame.xy(p["lat"], p["lon"])
        items.append({"p": p, "x": x, "y": y, "r": radius(p["objects"], rscale),
                      "name": SHORT.get(p["key"], p["label"].split(" (")[0]),
                      "wants_label": p["key"] in labelled})
    place_labels(frame, [i for i in items if i["wants_label"]], char_w, line_h)

    markers, labels = [], []
    for it in items:
        p, x, y, r = it["p"], it["x"], it["y"], it["r"]
        colour = TIERS[p["best_tier"]][0]
        tip = "%s — %d object%s · %s" % (
            p["label"], p["objects"], "" if p["objects"] == 1 else "s",
            TIERS[p["best_tier"]][1].split("—")[0].strip())
        markers.append(
            f'<g class="site" tabindex="0" role="listitem" aria-label="{html.escape(tip)}">'
            f'<title>{html.escape(tip)}</title>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{colour}" fill-opacity=".7" '
            f'stroke="{colour}" stroke-width="1.4"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="#3d3a30"/></g>')
        if not it.get("label_at"):
            continue
        cx, cy, anchor, box, gap = it["label_at"]
        if gap > 12:
            ex = x + (r + 2) * (1 if cx > x else -1 if cx < x else 0)
            ey = y + (r + 2) * (1 if cy - line_h * 0.3 > y else -1 if cy < y - r else 0)
            labels.append(
                f'<path d="M{ex:.1f} {ey:.1f}L{cx - (3 if anchor == "start" else -3 if anchor == "end" else 0):.1f} '
                f'{cy - line_h * 0.28:.1f}" fill="none" stroke="#a8a08c" stroke-width=".8"/>')
        labels.append(
            f'<text class="{fontclass}" x="{cx:.1f}" y="{cy:.1f}" text-anchor="{anchor}">'
            f'{html.escape(it["name"])}<tspan class="count" dx="5">{p["objects"]}</tspan></text>')
    return "\n        ".join(markers), "\n        ".join(labels)


def main() -> None:
    d = json.loads((GEO / "findspot_places.json").read_text())
    main_f, det_f = Frame(MAIN), Frame(DETAIL)
    sites = [p for p in d["places"] if p["kind"] == "site"]
    on_main = [p for p in sites if main_f.holds(p)]
    outliers = [p for p in sites if not main_f.holds(p)]
    in_detail = [p for p in sites if p["key"] in DETAIL_KEYS]
    regions = [p for p in d["places"] if p["kind"] == "region"]
    unloc = [p for p in d["places"] if p["kind"] == "unlocated"]

    m_markers, m_labels = draw(main_f, on_main, MAIN_LABELLED)
    d_markers, d_labels = draw(det_f, in_detail, DETAIL_LABELLED, rscale=4.4,
                               fontclass="dl", char_w=5.8, line_h=11.5)

    bx0, by0 = main_f.xy(DETAIL["lat1"], DETAIL["lon0"])
    bx1, by1 = main_f.xy(DETAIL["lat0"], DETAIL["lon1"])
    pad = 5
    box = (f'<rect x="{bx0-pad:.1f}" y="{by0-pad:.1f}" width="{bx1-bx0+2*pad:.1f}" '
           f'height="{by1-by0+2*pad:.1f}" fill="none" stroke="#7c3f10" stroke-width="1.2" '
           f'stroke-dasharray="4 3" opacity=".8"/>'
           f'<text class="geo" x="{bx1+pad+7:.1f}" y="{by0+2:.1f}">BABYLONIA — SEE DETAIL</text>')

    W, H = main_f.w, main_f.h
    dW, dH = det_f.w, det_f.h
    legend = "\n          ".join(
        f'<li><span class="sw" style="background:{TIERS[k][0]}"></span>{html.escape(TIERS[k][1])}</li>'
        for k in ["excavation_stratified", "excavation_reported", "site_reported", "acquisition_site"])
    rows = lambda items: "\n          ".join(
        f'<li><b>{p["objects"]}</b> {html.escape(p["label"])}</li>' for p in items)
    table_rows = "\n        ".join(
        f'<tr class="{p["kind"]}"><td class="n">{p["objects"]}</td>'
        f'<td>{html.escape(p["label"])}</td>'
        f'<td class="c">{"%.3f, %.3f" % (p["lat"], p["lon"]) if p["lat"] is not None else "—"}</td>'
        f'<td class="t"><span class="dot" style="background:'
        f'{TIERS.get(p["best_tier"], ("#b9b3a1", ""))[0]}"></span>'
        f'{html.escape(p["best_tier"].replace("_", " "))}</td>'
        f'<td class="note">{html.escape(p["note"] or "")}</td></tr>' for p in d["places"])

    outlier_html = ""
    for o in outliers:
        outlier_html += f"""
      <div class="panel">
        <h2>Off the map</h2>
        <div class="inset-box">
          <span class="dot-big" style="background:{TIERS[o['best_tier']][0]}"></span>
          <div><b>{html.escape(o['label'])}</b>
            <span class="modern">{html.escape(o['modern'] or '')} · {o['lat']:.2f}, {o['lon']:.2f}</span>
            <p>{html.escape(o['note'] or '')} About 1,900&nbsp;km north-west of Nippur.</p>
          </div>
        </div>
    </div>"""

    pct = 100 * d["objects_with_findspot_claim"] / d["corpus_objects"]
    doc = f"""<!doctype html>
<meta charset="utf-8">
<title>Where the bowls were found — Incantation Bowl Index</title>
<style>
  :root {{ --parchment:#f4efe2; --card:#fbf8f0; --ink:#3d3a30; --muted:#6f6a5a;
    --rule:#d9cfb6; --river:#6c918f; --land:#e9e2cf; --accent:#a45235;
    --sans:"Helvetica Neue",Helvetica,Arial,sans-serif;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--parchment); color:var(--ink);
          font-family:var(--sans); font-size:15px; line-height:1.5; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:2.4rem 1.5rem 4rem; }}
  h1 {{ font-family:var(--serif); font-size:2.1rem; line-height:1.15; margin:0 0 .4rem;
        font-weight:400; letter-spacing:-.01em; }}
  .sub {{ color:var(--muted); margin:0 0 1.6rem; max-width:64ch; }}
  code {{ font-size:.88em; background:#eae3d0; padding:.06em .3em; border-radius:2px; }}
  .figures {{ display:flex; flex-wrap:wrap; gap:1px; background:var(--rule);
              border:1px solid var(--rule); margin:0 0 1.6rem; }}
  .fig {{ background:var(--card); padding:.85rem 1.1rem; flex:1 1 170px; }}
  .fig b {{ display:block; font-family:var(--serif); font-size:1.7rem; line-height:1.1; }}
  .fig span {{ color:var(--muted); font-size:.82rem; }}
  .fig.warn b {{ color:var(--accent); }}
  .layout {{ display:grid; grid-template-columns:minmax(0,1fr) 288px; gap:1.5rem; align-items:start; }}
  @media (max-width:900px) {{ .layout {{ grid-template-columns:1fr; }} }}
  .strip {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; margin-top:1.4rem; }}
  .strip .panel {{ margin-bottom:0; }}
  @media (max-width:900px) {{ .strip {{ grid-template-columns:1fr; }} }}
  figure {{ margin:0; }}
  .mapcard {{ background:var(--land); border:1px solid var(--rule); }}
  svg.map {{ display:block; width:100%; height:auto; }}
  svg.map text {{ font-family:var(--sans); font-size:12.5px; fill:#4a4638; paint-order:stroke;
                  stroke:var(--land); stroke-width:3.2px; stroke-linejoin:round; }}
  svg.map text.dl {{ font-size:11px; }}
  svg.map .count {{ font-size:10.5px; fill:var(--muted); font-weight:700; stroke-width:3px; }}
  .site {{ outline:none; }}
  .site:hover circle:first-of-type, .site:focus circle:first-of-type {{ fill-opacity:.96; }}
  .geo {{ font-size:10.5px !important; fill:#96907e !important; letter-spacing:.14em;
          stroke-width:2.6px !important; }}
  figcaption {{ color:var(--muted); font-size:.82rem; padding:.55rem .2rem 0; }}
  .panel {{ background:var(--card); border:1px solid var(--rule); padding:1rem 1.1rem; margin-bottom:1rem; }}
  .panel h2 {{ font-family:var(--serif); font-weight:400; font-size:1.02rem; margin:0 0 .6rem; }}
  .panel ul {{ list-style:none; margin:0; padding:0; font-size:.85rem; }}
  .panel li {{ margin:.36rem 0; padding-left:1.4rem; position:relative; }}
  .sw {{ position:absolute; left:0; top:.3em; width:.85rem; height:.85rem; border-radius:50%; }}
  .panel.plain li {{ padding-left:0; }}
  .panel.plain b {{ display:inline-block; min-width:2.2rem; font-family:var(--serif); font-size:1rem; }}
  .detail {{ background:var(--land); border:1px solid var(--rule); }}
  .inset-box {{ display:flex; gap:.7rem; align-items:flex-start; }}
  .dot-big {{ flex:none; width:.95rem; height:.95rem; border-radius:50%; margin-top:.3rem; }}
  .modern {{ color:var(--muted); font-size:.78rem; }}
  .panel p {{ margin:.4rem 0 0; font-size:.82rem; color:var(--muted); }}
  table {{ border-collapse:collapse; width:100%; margin-top:.6rem; font-size:.86rem; }}
  th {{ text-align:left; font-weight:600; font-size:.72rem; letter-spacing:.09em;
        text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--rule);
        padding:.45rem .6rem; }}
  td {{ padding:.42rem .6rem; border-bottom:1px solid #e8e0cb; vertical-align:top; }}
  td.n {{ font-family:var(--serif); font-size:1rem; text-align:right; width:3.4rem; }}
  td.c {{ color:var(--muted); font-variant-numeric:tabular-nums; white-space:nowrap; }}
  td.t {{ white-space:nowrap; }} td.note {{ color:var(--muted); }}
  tr.region td, tr.unlocated td {{ color:var(--muted); font-style:italic; }}
  .dot {{ display:inline-block; width:.6rem; height:.6rem; border-radius:50%; margin-right:.42rem; }}
  h2.sec {{ font-family:var(--serif); font-weight:400; font-size:1.3rem; margin:2.4rem 0 .2rem; }}
  .caveat {{ border-left:3px solid var(--accent); padding:.5rem 0 .5rem .9rem;
             margin:1.5rem 0 0; color:var(--muted); font-size:.87rem; max-width:76ch; }}
</style>
<div class="wrap">
  <h1>Where the bowls were found</h1>
  <p class="sub">Every findspot recorded in the corpus, plotted from site coordinates held
     separately in <code>research/geo/findspot_gazetteer.json</code>. Marker area is proportional
     to the number of objects; colour is the strongest evidence any source offers for that place.</p>

  <div class="figures">
    <div class="fig"><b>{d['corpus_objects']:,}</b><span>objects in the corpus</span></div>
    <div class="fig"><b>{d['objects_with_findspot_claim']}</b><span>have any findspot claim ({pct:.0f}%)</span></div>
    <div class="fig"><b>{d['objects_with_located_findspot']}</b><span>name a place that can be mapped</span></div>
    <div class="fig"><b>{d['tier_totals']['excavation_stratified']}</b><span>have stratigraphic context</span></div>
    <div class="fig warn"><b>{d['objects_with_no_findspot_claim']:,}</b><span>have no findspot at all</span></div>
  </div>

  <div class="layout">
    <figure>
      <div class="mapcard">
      <svg class="map" viewBox="0 0 {W:.0f} {H:.0f}" role="list"
           aria-label="Map of recorded incantation bowl findspots across Mesopotamia">
        <rect width="{W:.0f}" height="{H:.0f}" fill="var(--land)"/>
        <path d="{main_f.path(GULF, close=True)}" fill="#a7b9b4" opacity=".6"/>
        <g fill="none" stroke="var(--river)" stroke-width="2.6" opacity=".75"
           stroke-linejoin="round" stroke-linecap="round">
          <path d="{main_f.path(TIGRIS)}"/><path d="{main_f.path(EUPHRATES)}"/>
          <path d="{main_f.path(SHATT)}" stroke-width="3.4"/>
          <path d="{main_f.path(KHABUR)}" stroke-width="1.8"/>
        </g>
        <text class="geo" x="{main_f.xy(35.6,43.95)[0]:.0f}" y="{main_f.xy(35.6,43.95)[1]:.0f}"
              transform="rotate(60 {main_f.xy(35.6,43.95)[0]:.0f} {main_f.xy(35.6,43.95)[1]:.0f})">TIGRIS</text>
        <text class="geo" x="{main_f.xy(33.95,42.35)[0]:.0f}" y="{main_f.xy(33.95,42.35)[1]:.0f}"
              transform="rotate(40 {main_f.xy(33.95,42.35)[0]:.0f} {main_f.xy(33.95,42.35)[1]:.0f})">EUPHRATES</text>
        <text class="geo" x="{main_f.xy(30.28,48.72)[0]:.0f}" y="{main_f.xy(30.28,48.72)[1]:.0f}"
              text-anchor="end">PERSIAN GULF</text>
        {box}
        {m_labels}
        {m_markers}
        <g transform="translate({W-80:.0f},36)">
          <path d="M0 44V6m-6 11 6-11 6 11" fill="none" stroke="#96907e" stroke-width="1.4"/>
          <text x="0" y="-3" text-anchor="middle" class="geo">N</text>
        </g>
      </svg>
      </div>
      <figcaption>Equirectangular projection, cosine-corrected at 33.5°N. Rivers follow their
        modern courses, for orientation only — several ran elsewhere in late antiquity.</figcaption>
    </figure>

    <div>
      <div class="panel">
        <h2>What the colour means</h2>
        <ul>{legend}</ul>
      </div>
      <figure class="panel" style="padding-bottom:.7rem">
        <h2>Babylonia in detail</h2>
        <div class="detail">
          <svg class="map" viewBox="0 0 {dW:.0f} {dH:.0f}" role="list"
               aria-label="Magnified detail of the Babylonia cluster">
            <rect width="{dW:.0f}" height="{dH:.0f}" fill="var(--land)"/>
            <g fill="none" stroke="var(--river)" stroke-width="3" opacity=".7"
               stroke-linejoin="round" stroke-linecap="round">
              <path d="{det_f.path(TIGRIS)}"/><path d="{det_f.path(EUPHRATES)}"/>
            </g>
            {d_labels}
            {d_markers}
          </svg>
        </div>
        <figcaption style="padding-top:.5rem">Roughly 4.5&times; the main map. These seven sites
          lie within about 80&nbsp;km and overlap at national scale.</figcaption>
      </figure>
    </div>
  </div>

  <div class="strip">
    <div class="panel plain">
      <h2>Region only — not mappable</h2>
      <ul>{rows(regions)}</ul>
    </div>
    <div class="panel plain">
      <h2>Named but unlocated</h2>
      <ul>{rows(unloc)}</ul>
    </div>{outlier_html}
  </div>

  <h2 class="sec">Every recorded location</h2>
  <table>
    <thead><tr><th class="n">Objects</th><th>Place</th><th>Coordinates</th>
      <th>Strongest evidence</th><th>Note</th></tr></thead>
    <tbody>
        {table_rows}
    </tbody>
  </table>

  <p class="caveat">Counts are objects, not claims, and each object is counted once at its
    strongest tier. Five objects whose museum record names two findspots are counted under both
    Babylon and Borsippa. “Found/Acquired” is a single British Museum field that does not separate
    where an object was found from where it was bought, so those sites evidence a market, not an
    excavation. Nothing here adjudicates a disputed findspot: the claim, its source and its
    locator remain in the corpus.</p>
</div>
"""
    out = GEO / "findspot_map.html"
    out.write_text(doc)
    print(f"wrote {out.relative_to(ROOT)} ({len(doc):,} bytes)")
    print(f"main {len(on_main)} sites · detail {len(in_detail)} · outliers {len(outliers)} "
          f"· regions {len(regions)} · unlocated {len(unloc)}")
    print(f"main frame {W:.0f}x{H:.0f}  detail frame {dW:.0f}x{dH:.0f} "
          f"({det_f.scale/main_f.scale:.1f}x)")


if __name__ == "__main__":
    main()
