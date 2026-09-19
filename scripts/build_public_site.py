"""Build the static bowlam.com landing page.

ACCESS-008 requires that the public page carry "no path from the page to the
corpus". So the page is generated here, once, from a reviewed snapshot, and
ships as flat HTML: no `/api/` call, no corpus query at view time, no link into
the research console.

What crosses the boundary is deliberately narrow. Only **aggregates** are baked
in — four totals, the per-decade publication counts, and the snapshot digest
that produced them. The per-identity array that the console's own introduction
endpoint returns (`identities`, each row carrying an `identity_id`) is dropped
here and never written to the output. The coverage field on the public page is
drawn from the totals alone, so its circles carry no identifier and assert
nothing about any individual bowl.

Usage:

    PYTHONPATH=src .venv/bin/python scripts/build_public_site.py

Then review `site/public/index.html` and deploy it yourself. This script does
not deploy: agents do not publish (docs/project-rules.md §3).
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

from bowl_index.web import CorpusCatalog

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
SRC = ROOT / "site" / "src"
OUT = ROOT / "site" / "public"
FONTS = ROOT / "web" / "fonts"

# Fonts the public page actually uses. The Hebrew subset is here for exactly
# one glyph — the bet in the wordmark. Frank Ruhl Libre is a Hebrew typeface,
# so the letter belongs in it rather than in whatever Hebrew face the visitor's
# system happens to substitute. The page still publishes no bowl text.
PUBLIC_FONTS = (
    "frank-ruhl-libre-latin.woff2",
    "frank-ruhl-libre-latin-ext.woff2",
    "frank-ruhl-libre-hebrew.woff2",
    "frank-ruhl-libre-OFL.txt",
)

COVERAGE_COPY = {
    "text_edition": {
        "kicker": "Reading the words",
        "heading": "Read their words.",
        "body": "Scholarly editions that read and translate these bowls are "
                "recorded against the objects they describe.",
        "label": "Text",
        "legend": "has a text reference",
        "total_label": "bowls with a text reference",
    },
    "provenance": {
        "kicker": "Tracing a journey",
        "heading": "Follow their journeys.",
        "body": "Published accounts of where bowls were found, and the "
                "collections they have passed through, are recorded as claims "
                "attributed to their sources.",
        "label": "Provenance",
        "legend": "has provenance information",
        "total_label": "bowls with provenance information",
    },
    "image": {
        "kicker": "Seeing the object",
        "heading": "Look closer.",
        "body": "Photographs and drawings in publications and collection "
                "catalogues are indexed as references, not reproduced here.",
        "label": "Images",
        "legend": "has an image reference",
        "total_label": "bowls with an image reference",
    },
}


# Milliseconds between one bar starting to grow and the next. With ~18 decades
# this gives a cascade of roughly 2.4s on top of each bar's own 1.2s rise. The
# console uses 120ms; a little slower reads better for someone scrolling gently.
BAR_STAGGER_MS = 140


def number(value: int) -> str:
    return f"{value:,}"


def build_chart(decades: list[dict], current_year: int) -> tuple[str, str, str]:
    """Static twin of renderChart() in web/home.js."""
    current = current_year // 10 * 10
    years = [row["decade"] for row in decades]
    start, end = min(current, *years), max(current, *years)
    by_decade = {row["decade"]: row for row in decades}
    rows = []
    for decade in range(start, end + 1, 10):
        rows.append(by_decade.get(decade)
                    or {"decade": decade, "indexed": 0, "incomplete": decade == current})

    ceiling = max(5, -(-max(1, *[row["indexed"] for row in rows]) // 5) * 5)
    width, left, right, top, baseline = 1000, 44, 16, 28, 278
    step = (width - left - right) / len(rows)
    bar_width = min(42, step * 0.65)

    grid = "".join(
        f'<line x1="{left}" y1="{baseline - (baseline - top) * i / 5:.1f}" x2="984" '
        f'y2="{baseline - (baseline - top) * i / 5:.1f}" stroke="#c9bfad" stroke-width=".7"/>'
        f'<text x="31" y="{baseline - (baseline - top) * i / 5 + 4:.1f}" text-anchor="end">'
        f'{ceiling * i // 5}</text>'
        for i in range(6)
    )

    label_every = max(1, -(-len(rows) // 9))
    bars = []
    for index, row in enumerate(rows):
        x = left + step * index + step / 2
        height = row["indexed"] / ceiling * (baseline - top)
        incomplete = row["incomplete"]
        show_label = index % label_every == 0 or index == len(rows) - 1
        title = (f'{row["decade"]}s: {row["indexed"]} indexed publications'
                 + ("; current decade, incomplete" if incomplete else ""))
        value_text = (f'<text x="{x:.1f}" y="{baseline - height - 9:.1f}" text-anchor="middle">'
                      f'{row["indexed"]}</text>') if row["indexed"] else ""
        axis_text = (f'<text x="{x:.1f}" y="307" text-anchor="middle">{row["decade"]}'
                     f'{"*" if incomplete else ""}</text>') if show_label else ""
        bars.append(
            f'<g><title>{html.escape(title)}</title>'
            f'<rect class="intro-bar intro-bar-{index + 1}'
            f'{" intro-bar-current" if incomplete else ""}" x="{x - bar_width / 2:.1f}" '
            f'y="{baseline - height:.1f}" width="{bar_width:.1f}" height="{height:.1f}" '
            f'style="animation-delay:{index * BAR_STAGGER_MS}ms"/>'
            f'{value_text}{axis_text}</g>'
        )

    desc = "; ".join(f'{row["decade"]}s: {row["indexed"]}' for row in rows)

    # Narrow screens get the same data turned on its side. A vertical bar chart
    # with 18 decades cannot be read at 327px without scrolling, and scrolling
    # it kept the reveal animation from ever firing: an 800px-wide SVG in a
    # 375px viewport tops out at an intersectionRatio of ~0.47, under the 0.5
    # the cascade waits for. Rows are cheap in a direction phones have to spare.
    h_width, h_label, h_track, h_pitch, h_bar, h_top = 320, 40, 258, 25, 13, 24
    h_height = h_top + h_pitch * len(rows) + 8
    h_grid = "".join(
        f'<line x1="{h_label + 2 + h_track * i / 2:.1f}" y1="20" '
        f'x2="{h_label + 2 + h_track * i / 2:.1f}" y2="{h_height - 8}" '
        f'stroke="#3d4542" stroke-width=".7"/>'
        f'<text x="{h_label + 2 + h_track * i / 2:.1f}" y="12" text-anchor="middle">'
        f'{ceiling * i // 2}</text>'
        for i in range(3)
    )
    h_bars = []
    for index, row in enumerate(rows):
        y = h_top + h_pitch * index
        length = row["indexed"] / ceiling * h_track
        incomplete = row["incomplete"]
        title = (f'{row["decade"]}s: {row["indexed"]} indexed publications'
                 + ("; current decade, incomplete" if incomplete else ""))
        h_bars.append(
            f'<g><title>{html.escape(title)}</title>'
            f'<text x="{h_label - 4}" y="{y + h_bar - 2:.1f}" text-anchor="end">'
            f'{row["decade"]}{"*" if incomplete else ""}</text>'
            f'<rect class="intro-bar intro-bar-{index + 1}'
            f'{" intro-bar-current" if incomplete else ""}" x="{h_label + 2}" '
            f'y="{y:.1f}" width="{max(length, 1.5):.1f}" height="{h_bar}" '
            f'style="animation-delay:{index * BAR_STAGGER_MS}ms"/>'
            f'<text x="{h_label + 2 + max(length, 1.5) + 5:.1f}" y="{y + h_bar - 2:.1f}">'
            f'{row["indexed"]}</text></g>'
        )
    svg_stacked = (
        f'<svg class="intro-chart-svg-h" viewBox="0 0 {h_width} {h_height}" role="img" '
        'aria-labelledby="intro-chart-title-h intro-chart-desc-h">'
        '<title id="intro-chart-title-h">Scholarly publications indexed, by decade</title>'
        f'<desc id="intro-chart-desc-h">{html.escape(desc)}. The current decade is '
        'incomplete. Exact values are also available in the table.</desc>'
        '<defs><pattern id="intro-current-decade-h" width="7" height="7" '
        'patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#5d4939"/>'
        '<path d="M-1 1l8 8M5-1l3 3" stroke="#d9954f" stroke-width="2"/></pattern></defs>'
        f'{h_grid}{"".join(h_bars)}</svg>'
    )

    svg = (
        '<svg class="intro-chart-svg" viewBox="0 0 1000 330" role="img" '
        'aria-labelledby="intro-chart-title intro-chart-desc">'
        '<title id="intro-chart-title">Scholarly publications indexed, by decade</title>'
        f'<desc id="intro-chart-desc">{html.escape(desc)}. The current decade is incomplete. '
        'Exact values are also available in the table.</desc>'
        '<defs><pattern id="intro-current-decade" width="7" height="7" patternUnits="userSpaceOnUse">'
        '<rect width="7" height="7" fill="#5d4939"/>'
        '<path d="M-1 1l8 8M5-1l3 3" stroke="#d9954f" stroke-width="2"/></pattern></defs>'
        f'{grid}{"".join(bars)}</svg>'
    ) + svg_stacked
    table = (
        '<table><caption>Indexed publications; current decade marked incomplete</caption>'
        '<thead><tr><th scope="col">Decade</th><th scope="col">Publications</th></tr></thead><tbody>'
        + "".join(
            f'<tr><th scope="row">{row["decade"]}s'
            f'{" (incomplete)" if row["incomplete"] else ""}</th>'
            f'<td>{number(row["indexed"])}</td></tr>' for row in rows)
        + "</tbody></table>"
    )
    return svg, table, str(current)


def build_field(total: int, coverage: dict[str, int]) -> tuple[str, str]:
    """Aggregate coverage field.

    The console draws one circle per identity from real per-bowl flags. This
    page has no per-bowl data by design, so it draws `total` circles and marks
    the correct *number* for each category, choosing which ones from a fixed
    seed. The proportion is exact; the assignment is illustrative, and the
    caption on the page says so rather than implying per-bowl truth.
    """
    cols = max(1, int((total * 1.5) ** 0.5 + 0.999))
    rows_count = -(-total // cols)
    width, height = cols * 13 + 16, max(60, rows_count * 13 + 16)

    circles = "".join(
        f'<circle cx="{14 + index % cols * 13}" cy="{14 + index // cols * 13}" '
        f'r="4.2" class="intro-circle" data-i="{index}"/>'
        for index in range(total)
    )
    field = (f'<svg id="intro-circle-field" viewBox="0 0 {width} {height}" role="img" '
             f'aria-labelledby="intro-field-title intro-field-desc">'
             f'<title id="intro-field-title">Bowl documentation coverage</title>'
             f'<desc id="intro-field-desc">{number(total)} circles, one for each bowl in the '
             f'index. Selecting a category highlights the number of bowls that have that kind '
             f'of reference.</desc><g aria-hidden="true">{circles}</g></svg>')

    # Deterministic membership so a rebuild with unchanged counts is a no-op diff.
    selections = {"all": list(range(total))}
    for field_name, count in coverage.items():
        picker = random.Random(f"bowlam:{field_name}:{total}:{count}")
        selections[field_name] = sorted(picker.sample(range(total), min(count, total)))
    return field, json.dumps(selections, separators=(",", ":"))


def render(payload: dict, snapshot_id: str, built_at: str, css_hash: str = "dev") -> str:
    total = payload["identity_count"]
    records = payload["source_record_count"]
    coverage = payload["coverage"]
    chart_svg, chart_table, current = build_chart(
        payload["scholarship"]["decades"], payload["snapshot"]["current_year"])
    field_svg, selections = build_field(total, coverage)
    undated = payload["scholarship"]["undated_count"]

    buttons = "".join(
        f'<button type="button" data-coverage="{key}" aria-pressed="false">'
        f'{COVERAGE_COPY[key]["label"]}</button>' for key in COVERAGE_COPY
    )
    steps = "".join(
        f'<article class="intro-coverage-step" data-step="{key}">'
        f'<span class="intro-kicker">{COVERAGE_COPY[key]["kicker"]}</span>'
        f'<h3>{COVERAGE_COPY[key]["heading"]}</h3>'
        f'<p class="intro-coverage-number">{number(coverage[key])}'
        f'<span> / {number(total)}</span>'
        f'<small>{100 * coverage[key] / total:.1f}% of bowls</small></p>'
        f'<p>{COVERAGE_COPY[key]["body"]}</p></article>'
        for key in COVERAGE_COPY
    )
    legends = json.dumps({key: COVERAGE_COPY[key]["legend"] for key in COVERAGE_COPY},
                         separators=(",", ":"))
    total_labels = json.dumps(
        {"all": "bowls in the index",
         **{key: COVERAGE_COPY[key]["total_label"] for key in COVERAGE_COPY}},
        separators=(",", ":"))

    hero_svg = (SRC / "bowl.svg").read_text(encoding="utf-8").strip()
    map_svg = (SRC / "map.svg").read_text(encoding="utf-8").strip()

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bowlam · The Incantation Bowl Index</title>
<meta name="description" content="An index of Mesopotamian incantation bowls: what is known about them, what has been published about them, and what this project deliberately does not republish.">
<meta property="og:title" content="Bowlam · The Incantation Bowl Index">
<meta property="og:description" content="An index of Mesopotamian incantation bowls — {number(total)} bowls drawn from {number(records)} source records.">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
<!-- Generated by scripts/build_public_site.py from corpus snapshot
     {snapshot_id[:16]} at {built_at}. Aggregate counts only; no per-object
     data, no corpus endpoint. Do not hand-edit — rebuild instead. -->
<link rel="stylesheet" href="public.css?v={css_hash}">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="topbar">
  <a class="wordmark" href="/" aria-label="Bowlam home">
    <span class="wordmark-seal" lang="he" aria-hidden="true">ב</span>
    <span><strong>Bowlam</strong><small>The Incantation Bowl Index</small></span>
  </a>
</header>

<main id="main" tabindex="-1">
<div class="intro-wrap">

  <section class="intro-hero intro-chapter" aria-labelledby="home-title">
    <div class="intro-hero-copy">
      <h1 id="home-title">Small vessels.<br>Human hopes.<br><em>Enduring questions.</em></h1>
      <p class="intro-lead">Ancient spells. Everyday fears. Discover the lives hidden in incantation bowls.</p>
      <button class="intro-scroll" type="button" data-scroll="intro-origins">Discover their story <span aria-hidden="true">↓</span></button>
    </div>
    <figure class="intro-bowl-figure">
      {hero_svg}
      <figcaption><span class="intro-caption-rule"></span>An artist’s impression</figcaption>
    </figure>
    <div class="intro-hero-foot"><span>Clay / Language / Memory</span><span>Spells that outlived their makers</span></div>
  </section>

  <section id="intro-origins" class="intro-chapter intro-origins" aria-labelledby="origins-title">
    <div class="intro-prose">
      <h2 id="origins-title">Protection,<br>close to home.</h2>
      <p>A spell against illness. A shield for a family. Written on ordinary clay, these words reveal what people feared—and what they hoped to keep safe.</p>
      <p>Originating in Mesopotamia, in present-day Iraq and neighboring Iran, most bowls were made in the sixth and seventh centuries CE, in late antiquity—a world that changed with the rise of Islam.</p>
    </div>
    <figure class="intro-map-figure">
      {map_svg}
      <figcaption><span class="intro-region-key"></span> Approximate region of bowl finds · modern borders omitted. <a href="https://www.csmc.uni-hamburg.de/publications/aom/026-en.html" target="_blank" rel="noreferrer">About the region ↗</a></figcaption>
    </figure>
  </section>

  <section class="intro-chapter intro-rediscovery" aria-labelledby="rediscovery-title">
    <div class="intro-section-heading"><h2 id="rediscovery-title">A thousand years later,<br><em>the bowls resurface.</em></h2></div>
    <div class="intro-milestones">
      <article><span class="intro-date" data-year="1850" aria-label="1850">1850</span><h3>A discovery at Nippur</h3><p>Austen Henry Layard uncovers an inscribed bowl at Nippur. Ancient spells return to view.</p></article>
      <article><span class="intro-date" data-year="1853" aria-label="1853">1853</span><h3>The first texts in print</h3><p>Thomas Ellis publishes bowl texts in Layard’s book. The work of reading their spells begins.</p></article>
    </div>
    <details class="intro-sources"><summary>Sources for the story</summary><p><a href="https://scholars.depaul.edu/ws/portalfiles/portal/39957201/fulltext.pdf" target="_blank" rel="noreferrer">Brodie and Kersel, “WikiLeaks, Text, and Archaeology,” in Archaeologies of Text (2014), p. 200</a> dates Layard’s finds at Babylon and Nippur to 1850. Earlier bowls reached the British Museum in 1841.</p><p><a href="https://www.britishmuseum.org/collection/object/W_1841-0726-90_1" target="_blank" rel="noreferrer">British Museum: Ellis’s 1853 publication</a>, in Layard, pp. 521–522.</p></details>
  </section>

  <section class="intro-chapter intro-scholarship" aria-labelledby="scholarship-title">
    <div class="intro-section-heading"><h2 id="scholarship-title">More pages.<br>More questions.</h2><p>Each generation finds more to uncover.</p></div>
    <figure class="intro-chart-figure">
      <div class="intro-chart-heading"><strong>Scholarly publications indexed, by decade</strong><span>Publications / decade</span></div>
      <div id="intro-chart">{chart_svg}</div>
      <figcaption>Publications in the index, grouped by decade. * {current}s: current decade, incomplete. {number(undated)} undated works excluded. Dated scholarly works in this index; not a complete census of scholarship.</figcaption>
      <p class="intro-chart-hint">Open the table below for exact figures by decade.</p>
      <details class="intro-chart-table"><summary>Read the chart as a table</summary><div id="intro-chart-data">{chart_table}</div></details>
    </figure>
  </section>

  <section class="intro-chapter intro-coverage" aria-labelledby="coverage-title">
    <div class="intro-section-heading"><h2 id="coverage-title">A world of bowls.<br><em>One place to explore.</em></h2><p>Bowlam brings together the bowls, their words, and their journeys. Our aim: the most complete index possible.</p></div>
    <div class="intro-coverage-layout">
      <div class="intro-field-panel">
        <div class="intro-field-heading"><strong id="intro-total">{number(total)}</strong><span id="intro-total-label">bowls in the index</span></div>
        <div class="intro-controls" role="group" aria-label="Highlight recorded evidence">
          <button type="button" data-coverage="all" aria-pressed="true">All bowls</button>{buttons}
        </div>
        {field_svg}
        <p id="intro-selection" class="intro-selection" role="status">{number(total)} bowls in the index.</p>
        <p class="intro-field-legend"><span class="intro-dot"></span> Recorded <span class="intro-dot intro-dot-muted"></span> Not recorded in this index</p>
      </div>
      <div class="intro-coverage-steps">
        <article class="intro-coverage-step" data-step="all">
          <span class="intro-kicker">The collection</span>
          <h3>Meet the collection.</h3>
          <p>The index brings together {number(total)} bowls from {number(records)} source records — each one an appearance of a bowl in a publication, a catalogue or a collection, linked to the object it appears to describe.</p>
          <p>The collection grows as research continues.</p>
        </article>
        {steps}
      </div>
    </div>
    <p class="intro-coverage-note">Each circle stands for one bowl in the index. Highlighting shows how many bowls carry each kind of reference — some carry all three. Which circles light up is illustrative: this page publishes totals, not records for individual bowls.</p>
  </section>

  <section class="intro-chapter intro-withheld" aria-labelledby="withheld-title">
    <div class="intro-section-heading">
      <h2 id="withheld-title">What we index,<br><em>and what we hold back.</em></h2>
      <p>An index of who said what about which bowl is useful only if it is honest about its own limits.</p>
    </div>
    <div class="intro-withheld-grid">
      <article>
        <h3>A bowl is not a catalogue entry.</h3>
        <p>The same bowl can appear in several publications under several numbers. The index keeps those appearances separate and records how confident it is that they describe one object, rather than silently merging them.</p>
      </article>
      <article>
        <h3>Every statement has a source.</h3>
        <p>Dates, findspots, measurements and readings are recorded as claims attributed to a publication, with a page or catalogue locator. Where sources disagree, both readings are kept.</p>
      </article>
      <article>
        <h3>We do not republish other people’s work.</h3>
        <p>Modern transcriptions, translations, commentary and photographs belong to the scholars, publishers and collections that made them. The index records that they exist and where to find them. It does not reproduce them.</p>
      </article>
      <article>
        <h3>Provenance is reported, not settled.</h3>
        <p>Many bowls left Iraq and Iran in circumstances that are contested or undocumented. Recording what a source reports about an object’s history is not a statement that its ownership, export or authenticity is established.</p>
      </article>
    </div>
  </section>

  <section class="intro-chapter intro-interest" aria-labelledby="interest-title">
    <div class="intro-section-heading">
      <h2 id="interest-title">The index is still being built.</h2>
      <p>Leave an address and we will write when there is something worth reading — new coverage, a public release, or access for researchers.</p>
    </div>
    <form class="interest-form" id="interest-form" method="post" action="/api/interest" novalidate>
      <label for="interest-email">Email address</label>
      <input id="interest-email" name="email" type="email" required autocomplete="email"
             placeholder="you@example.org" inputmode="email" spellcheck="false">
      <div class="interest-hp" aria-hidden="true">
        <label for="interest-website">Leave this field empty</label>
        <input id="interest-website" name="website" type="text" tabindex="-1" autocomplete="off">
      </div>
      <button type="submit">Keep me posted</button>
    </form>
    <p class="interest-status" id="interest-status" role="status" aria-live="polite"></p>
    <p class="interest-note">We use your address only to send occasional updates about this project. No third-party tracking, no list sharing, and every message carries a one-click unsubscribe.</p>
  </section>

</div>
</main>

<footer class="intro-footer">
  <p>Bowlam · The Incantation Bowl Index</p>
  <p>Counts from the research snapshot of {built_at}.</p>
  <a href="#main">Back to the beginning ↑</a>
</footer>

<script>
(function () {{
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  document.querySelectorAll("[data-scroll]").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var target = document.getElementById(button.dataset.scroll);
      if (target) target.scrollIntoView({{behavior: reduced.matches ? "auto" : "smooth", block: "start"}});
    }});
  }});

  // Coverage field. Every number here was baked in at build time; nothing is fetched.
  var SELECTIONS = {selections};
  var LEGENDS = {legends};
  var TOTAL_LABELS = {total_labels};
  var TOTAL = {total};
  var circles = Array.prototype.slice.call(document.querySelectorAll(".intro-circle"));
  var status = document.getElementById("intro-selection");

  function setCoverage(field) {{
    var chosen = SELECTIONS[field];
    var marked = new Uint8Array(TOTAL);
    for (var i = 0; i < chosen.length; i++) marked[chosen[i]] = 1;
    circles.forEach(function (circle, index) {{
      circle.classList.toggle("is-softened", field !== "all" && !marked[index]);
    }});
    document.querySelectorAll("[data-coverage]").forEach(function (button) {{
      button.setAttribute("aria-pressed", String(button.dataset.coverage === field));
    }});
    var message = field === "all"
      ? chosen.length.toLocaleString() + " bowls in the index."
      : chosen.length.toLocaleString() + " of " + TOTAL.toLocaleString() + " ("
        + (100 * chosen.length / TOTAL).toFixed(1) + "%) " + LEGENDS[field] + ".";
    if (status) status.textContent = message;
    var totalEl = document.getElementById("intro-total");
    var labelEl = document.getElementById("intro-total-label");
    if (totalEl) totalEl.textContent = chosen.length.toLocaleString();
    if (labelEl) labelEl.textContent = TOTAL_LABELS[field];
    var desc = document.getElementById("intro-field-desc");
    if (desc) desc.textContent = message
      + " Each circle represents one bowl. Lighter circles have no reference of this kind.";
  }}

  // Scrolling through the coverage chapters advances the field, the way the
  // console's introduction does. On a phone the panel is sticky rather than
  // beside the steps, so the reading line sits below it instead of mid-screen.
  var desktop = matchMedia("(min-width: 701px)");
  var panel = document.querySelector(".intro-field-panel");
  var lastStep = null, frame = 0;
  function readingFloor() {{
    if (desktop.matches || !panel) return 100;
    // Steps behind the sticky panel are not being read, whatever the geometry says.
    return Math.max(100, Math.min(panel.getBoundingClientRect().bottom, innerHeight));
  }}
  function onScroll() {{
    if (frame) return;
    frame = requestAnimationFrame(function () {{
      frame = 0;
      var steps = [].slice.call(document.querySelectorAll("[data-step]"));
      var floor = readingFloor();
      var target = desktop.matches
        ? innerHeight * 0.52
        : floor + (innerHeight - floor) * 0.45;
      var visible = steps.filter(function (step) {{
        var box = step.getBoundingClientRect();
        return box.bottom > floor && box.top < innerHeight;
      }});
      if (!visible.length) return;
      var closest = visible.reduce(function (a, b) {{
        return Math.abs(a.getBoundingClientRect().top + a.offsetHeight / 2 - target) <
               Math.abs(b.getBoundingClientRect().top + b.offsetHeight / 2 - target) ? a : b;
      }});
      // A clicked button stays selected until scrolling reaches another chapter.
      if (closest.dataset.step !== lastStep) {{
        lastStep = closest.dataset.step;
        setCoverage(lastStep);
      }}
    }});
  }}
  addEventListener("scroll", onScroll, {{passive: true}});
  addEventListener("resize", onScroll, {{passive: true}});
  onScroll();

  document.querySelectorAll("[data-coverage]").forEach(function (button) {{
    button.addEventListener("click", function () {{ setCoverage(button.dataset.coverage); }});
  }});

  // The rediscovery dates ramp from 750 to their real year. aria-label carries
  // the true year throughout, so a screen reader never reads the intermediate
  // counting values as fact.
  var dates = [].slice.call(document.querySelectorAll("[data-year]"));
  function animateYear(date, delay) {{
    var first = 750, last = Number(date.dataset.year), duration = 3200;
    date.textContent = String(first);
    setTimeout(function () {{
      var started = performance.now();
      var tick = function (now) {{
        var progress = Math.min(1, (now - started) / duration);
        var eased = 1 - Math.pow(1 - progress, 3);
        date.textContent = String(Math.round(first + (last - first) * eased));
        if (progress < 1) requestAnimationFrame(tick);
      }};
      requestAnimationFrame(tick);
    }}, delay);
  }}

  if (!reduced.matches && "IntersectionObserver" in window) {{
    dates.forEach(function (date) {{ date.textContent = "750"; }});
    var pending = [].slice.call(document.querySelectorAll(
      ".intro-milestones, .intro-map, .intro-chart-svg, .intro-chart-svg-h, "
      + ".intro-section-heading"));

    function revealNode(node) {{
      var at = pending.indexOf(node);
      if (at < 0) return;
      pending.splice(at, 1);
      reveal.unobserve(node);
      node.classList.add("is-in-view", "is-revealing");
      if (node.classList.contains("intro-milestones")) {{
        dates.forEach(function (date, index) {{ animateYear(date, index * 280); }});
      }}
    }}

    var reveal = new IntersectionObserver(function (entries) {{
      entries.forEach(function (entry) {{
        if (!entry.isIntersecting) return;
        // The chart's bars cascade for several seconds, so it waits until it is
        // genuinely on screen rather than starting on a first sliver.
        var chart = entry.target.classList.contains("intro-chart-svg")
                 || entry.target.classList.contains("intro-chart-svg-h");
        var needed = chart ? 0.5 : 0.18;
        // An element larger than the viewport can never reach 0.5, so also
        // accept "it fills most of the screen" — otherwise the cascade that
        // ratio is guarding simply never runs.
        var box = entry.intersectionRect;
        var fills = box.height >= innerHeight * 0.6 || box.width >= innerWidth * 0.9;
        if (entry.intersectionRatio < needed && !fills) return;
        revealNode(entry.target);
      }});
    }}, {{threshold: [0.18, 0.5]}});
    pending.forEach(function (node) {{ reveal.observe(node); }});

    // A fast scroll can carry a section past the viewport between observer
    // samples. These sections start hidden — the map's shaded find region at
    // opacity 0, the chart bars at scaleY(.02) — so a missed sample leaves the
    // content permanently invisible, not merely unanimated. Reveal anything
    // that has already gone by.
    addEventListener("scroll", function () {{
      for (var i = pending.length - 1; i >= 0; i--) {{
        if (pending[i].getBoundingClientRect().bottom < 0) revealNode(pending[i]);
      }}
    }}, {{passive: true}});
  }}

  // Interest capture. Posts to the Pages Function in site/functions/api/interest.js.
  var form = document.getElementById("interest-form");
  var note = document.getElementById("interest-status");
  if (form) form.addEventListener("submit", function (event) {{
    event.preventDefault();
    var button = form.querySelector("button");
    var email = form.querySelector("#interest-email");
    note.className = "interest-status";
    if (!email.value || !email.checkValidity()) {{
      note.classList.add("is-error");
      note.textContent = "Please enter an email address we can reach you at.";
      email.focus();
      return;
    }}
    button.disabled = true;
    button.textContent = "Sending…";
    fetch(form.action, {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{
        email: email.value.trim(),
        website: form.querySelector("#interest-website").value
      }})
    }}).then(function (response) {{
      return response.json().then(function (body) {{ return {{ok: response.ok, body: body}}; }});
    }}).then(function (result) {{
      if (!result.ok) throw new Error(result.body && result.body.error || "Something went wrong.");
      form.reset();
      note.classList.add("is-ok");
      note.textContent = "Thank you — we will be in touch when there is news.";
      button.textContent = "Keep me posted";
    }}).catch(function (error) {{
      note.classList.add("is-error");
      note.textContent = error.message || "We could not save that address. Please try again.";
      button.textContent = "Keep me posted";
    }}).then(function () {{
      button.disabled = false;
    }});
  }});
}})();
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="corpus database")
    args = parser.parse_args()

    payload = CorpusCatalog(args.db).introduction()
    snapshot_id = payload["snapshot"]["id"]
    built_at = datetime.now(timezone.utc).strftime("%-d %B %Y")

    # Belt and braces: the per-identity array must not reach the output.
    payload.pop("identities", None)

    OUT.mkdir(parents=True, exist_ok=True)
    css_hash = hashlib.sha256((SRC / "public.css").read_bytes()).hexdigest()[:8]
    (OUT / "index.html").write_text(
        render(payload, snapshot_id, built_at, css_hash), encoding="utf-8")
    for name in ("public.css", "_headers", "robots.txt"):
        shutil.copyfile(SRC / name, OUT / name)

    (OUT / "fonts").mkdir(exist_ok=True)
    for name in PUBLIC_FONTS:
        shutil.copyfile(FONTS / name, OUT / "fonts" / name)

    rendered = (OUT / "index.html").read_text(encoding="utf-8")
    for leak in ("IDENT-", "/api/introduction", "#/explore", "#/search", "127.0.0.1"):
        if leak in rendered:
            raise SystemExit(f"refusing to write: output contains {leak!r}")

    print(f"built {OUT / 'index.html'}")
    print(f"  stylesheet public.css?v={css_hash}")
    print(f"  snapshot {snapshot_id[:16]}  ·  {number(payload['identity_count'])} bowls  ·  "
          f"{len(rendered) // 1024} KB")
    print("  aggregates only; no per-identity rows, no corpus endpoint")
    print("\nNot deployed. Review the page, then deploy it yourself:")
    print("  cd site && npx wrangler pages deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
