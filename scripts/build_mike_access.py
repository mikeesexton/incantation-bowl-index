"""Build Mike's structured, single-user private research surface.

This is not a release builder. It uses ``PrivateResearchProjection`` and retains
every stored text, recorded media row and source wording available to Mike's
private reader. Archived source scans are packaged by opaque capture ID in the
local snapshot. The generated directory contains protected third-party material,
is ignored by Git, and must never be promoted until a Cloudflare Access policy
admits Mike alone. Any shared or public reader must use ``Projection`` instead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from html import escape

from bowl_index.db import PROJECT_ROOT
from bowl_index.market import market_ledger
from bowl_index.private_captures import ARCHIVE_ROOT, capture_filename, capture_inventory, checked_capture_path
from bowl_index.private_projection import PrivateResearchProjection, private_manifest
from bowl_index.projection import PROJECTION_COLUMNS
from bowl_index.state import corpus_fingerprint
from build_scholar_preview import BASE_RULES, tokens


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
WEB = ROOT / "web"
OUT = ROOT / "site" / "mike-build"
PROMOTED = ROOT / "site" / "public" / "mike"

SECRET_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"data/private/"),
    re.compile(r"file://", re.I),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
)


def digest(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def inventory(projection, tables, manifest, captures):
    checks = []

    def record(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    payloads = {
        name: json.loads((OUT / "data" / (name + ".json")).read_text(encoding="utf-8"))
        for name in tables
    }
    schemas_ok = all(
        payloads[name]["columns"] == list(PROJECTION_COLUMNS[name])
        and all(set(row) == set(PROJECTION_COLUMNS[name]) for row in payloads[name]["rows"])
        for name in tables
    )
    record("projection_schema", schemas_ok,
           "%d private projected tables match their declared columns" % len(tables))

    db_texts = {row["id"]: row["content"] for row in projection.conn.execute(
        "SELECT id,content FROM texts"
    )}
    built_texts = {row["id"]: row["content"] for row in payloads["texts"]["rows"]}
    record("all_text_content_present", built_texts == db_texts,
           "%d/%d stored text rows carry their complete content" %
           (len(built_texts), len(db_texts)))

    contexts = json.loads((OUT / 'data' / 'source_contexts.json').read_text())["rows"]
    record('all_source_contexts_present', contexts == projection.source_contexts(),
           '%d checked contextual copies, outside bowl reading counts' % len(contexts))

    db_media = projection.conn.execute("SELECT count(*) FROM media").fetchone()[0]
    built_media = payloads["media"]["rows"]
    record("all_media_present", len(built_media) == db_media,
           "%d/%d recorded media rows are available" % (len(built_media), db_media))

    private_facts = projection._fact_candidates()
    record("all_source_wording_present", payloads["facts"]["rows"] == private_facts,
           "%d fact rows retain Mike-private source wording" % len(private_facts))

    staged_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(OUT.rglob("*"))
        if path.is_file() and path.suffix in {".json", ".js", ".css", ".html", ".txt"}
    )
    bad_patterns = [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(staged_text)]
    record("local_paths_and_secrets_absent", not bad_patterns,
           "no local path, private-directory or secret pattern")

    private_paths = [path for path in projection.private_storage if path and path in staged_text]
    record("capture_storage_paths_absent", not private_paths,
           "%d private capture paths tested" % len(projection.private_storage))

    packaged = [(row, OUT / "captures" / capture_filename(row)) for row in captures]
    capture_hashes_ok = all(
        path.is_file() and path.stat().st_size == row["byte_length"]
        and digest(path) == row["sha256"] for row, path in packaged
    )
    record("all_captures_packaged", capture_hashes_ok and len(packaged) == projection.capture_count,
           "%d/%d captures have exact archived bytes" % (len(packaged), projection.capture_count))

    if not all(check["passed"] for check in checks):
        failed = ", ".join(check["name"] for check in checks if not check["passed"])
        raise ValueError("Mike Access audit failed: " + failed)

    files = [
        {"path": str(path.relative_to(OUT)), "sha256": digest(path), "bytes": path.stat().st_size}
        for path in sorted(OUT.rglob("*")) if path.is_file()
    ]
    material = "\n".join(item["path"] + ":" + item["sha256"] for item in files)
    return {
        "schema_version": 1,
        "artifact": "Bowlam Mike Access private research bank",
        "snapshot_id": hashlib.sha256(material.encode()).hexdigest(),
        "built_at": manifest["generated_at"],
        "corpus_state_digest": corpus_fingerprint(projection.conn)["corpus_digest"],
        "access": {
            "audience": "Mike alone",
            "status": "local_complete_remote_pending_single_user_gate_and_private_object_storage",
            "shared_or_public_use": "forbidden; rebuild with Projection",
            "source_captures_held": projection.capture_count,
            "source_captures_packaged": len(packaged),
        },
        "projection_counts": {name: len(rows) for name, rows in tables.items()},
        "private_counts": projection.gate_counts(tables["texts"]),
        "audit_checks": checks,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--inventory", help="also write the content-free private snapshot inventory")
    args = parser.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    captures = capture_inventory(
        conn, lambda row: "./captures/" + capture_filename(row)
    )
    projection = PrivateResearchProjection(
        conn, capture_urls={row["id"]: row["url"] for row in captures}
    )
    tables = projection.tables()
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    (OUT / "captures").mkdir()
    for row in conn.execute("SELECT id,storage_path,mime_type,byte_length,sha256 FROM captures"):
        source = checked_capture_path(row, ARCHIVE_ROOT)
        if source.stat().st_size != row["byte_length"]:
            raise SystemExit("refusing to write: capture length mismatch " + row["id"])
        shutil.copy2(source, OUT / "captures" / capture_filename(row))

    # PrivateResearchProjection uses an API path for local derivatives. Static
    # Mike Access copies those exact files into its ignored build directory.
    local_media = []
    for row in tables["media"]:
        prefix = "/api/private-media/"
        if row["url"] and row["url"].startswith(prefix):
            name = row["url"].removeprefix(prefix)
            source = projection.media_root / name
            local_media.append((source, name))
            row["url"] = "./media/" + name

    if local_media:
        (OUT / "media").mkdir()
        for source, name in local_media:
            if not source.is_file():
                raise SystemExit("refusing to write: missing private media derivative " + name)
            shutil.copy2(source, OUT / "media" / name)

    manifest = private_manifest(projection, tables, generated_at)
    manifest["tables"] = {
        name: {"rows": len(rows), "url": "./data/%s.json" % name}
        for name, rows in tables.items()
    }
    manifest["served_from"] = "Mike-only authenticated research surface"
    manifest["source_captures_url"] = "./data/captures.json"
    manifest["source_contexts_url"] = "./data/source_contexts.json"
    (OUT / "data" / "source_contexts.json").write_text(
        json.dumps({"rows": projection.source_contexts()}, ensure_ascii=False), encoding="utf-8")
    (OUT / "data" / "captures.json").write_text(
        json.dumps({"rows": captures}, ensure_ascii=False), encoding="utf-8"
    )

    written = 0
    for name, rows in tables.items():
        payload = {"table": name, "columns": list(PROJECTION_COLUMNS[name]),
                   "total": len(rows), "offset": 0, "rows": rows}
        path = OUT / "data" / (name + ".json")
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        written += path.stat().st_size
    (OUT / "data" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    css = (WEB / "styles.css").read_text(encoding="utf-8")
    light, dark = tokens(css)
    faces = "\n".join(match.group(0) + "\n}" for match in
                      re.finditer(r"@font-face \{[^}]+", css))
    faces = faces.replace('url("/fonts/', 'url("./fonts/')
    (OUT / "mike.css").write_text(
        "/* Generated private Mike Access stylesheet. */\n" + faces
        + "\n\n:root {\n" + light + "\n}\n\n"
        + '@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {\n'
        + "\n".join("  " + line for line in dark.splitlines()) + "\n  }\n}\n"
        + BASE_RULES + "\n" + (WEB / "reading.css").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    ledger = market_ledger(conn, monitor_dir=ROOT / "data" / "private" / "monitoring" / "market")
    (OUT / "data" / "market.json").write_text(
        json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
    (OUT / "market.html").write_text(market_page(ledger, generated_at), encoding="utf-8")
    shutil.copy2(WEB / "reading.js", OUT / "reading.js")
    shutil.copytree(WEB / "fonts", OUT / "fonts")
    (OUT / "index.html").write_text(
        SHELL.replace("__GENERATED__", generated_at), encoding="utf-8")

    try:
        snapshot = inventory(projection, tables, manifest, captures)
    except ValueError as error:
        shutil.rmtree(OUT)
        raise SystemExit("refusing to write: %s" % error)
    inventory_text = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    (OUT / "private-snapshot.json").write_text(inventory_text, encoding="utf-8")
    if args.inventory:
        target = Path(args.inventory)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(inventory_text, encoding="utf-8")

    counts = snapshot["private_counts"]
    print("built %s" % OUT)
    print("  %d tables  ·  %.1f MB of private rows" % (len(tables), written / 1e6))
    print("  texts %d/%d  ·  media %d/%d  ·  local images %d" % (
        counts["texts_available_rows"], counts["texts_available_rows"],
        counts["media_available_rows"], counts["media_available_rows"],
        counts["media_local_derivative_rows"],
    ))
    print("  private audit %d/%d checks passed  ·  snapshot %s" % (
        sum(check["passed"] for check in snapshot["audit_checks"]),
        len(snapshot["audit_checks"]), snapshot["snapshot_id"][:12]))
    print("  source captures %d/%d packaged locally" % (
        snapshot["access"]["source_captures_packaged"], projection.capture_count))
    print("\nNot deployed. Promote only after bowlam.com/mike* is restricted to Mike alone")
    print("and the Pages aliases are covered by the host lock. Any second user requires")
    print("the shared Projection instead.")
    if PROMOTED.exists():
        print("\nWARNING: %s exists in the deployment tree." % PROMOTED)


SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Bowlam — Mike Access</title>
<link rel="stylesheet" href="mike.css">
</head>
<body>
<a class="skip-link" href="#explore-view">Skip to the bowls</a>
<header class="preview-bar">
  <strong><span class="preview-seal" aria-hidden="true">&#x10840;</span>Bowlam</strong>
<small>Mike Access &middot; structured personal research bank</small>
<nav aria-label="Mike Access sections"><a href="#/explore">Explore</a> &middot;
  <a href="#/scholarship">Scholarship and source files</a> &middot;
  <a href="#/contexts">Source passages</a> &middot;
  <a href="market.html">Market</a></nav>
</header>
<main><section id="explore-view" class="reading-room" aria-labelledby="explore-title"></section></main>
<footer class="preview-foot">
  <p>Private research access for Mike alone. This surface includes all stored
     text rows, recorded image links, and locally packaged archived source files.
     It is not a public or shared release.</p>
  <p><a href="private-snapshot.json">Private snapshot inventory</a>
     &middot; built __GENERATED__.</p>
</footer>
<script>
  window.READER_BASE = "./data";
  window.READER_SUFFIX = ".json";
  window.READER_STANDALONE = true;
</script>
<script src="reading.js" defer></script>
<script>
  addEventListener("DOMContentLoaded", function () {
    function go() {
      if (!location.hash.startsWith("#/explore") &&
          !location.hash.startsWith("#/contexts") &&
          !location.hash.startsWith("#/scholarship"))
        history.replaceState(null, "", "#/explore");
      window.ReadingRoom.render();
    }
    addEventListener("hashchange", go); go();
  });
</script>
</body>
</html>
"""


MARKET_CSS = """
.market { padding: 1.5rem clamp(1rem, 4vw, 2.5rem) 2rem; max-width: 72rem; }
.market h1 { font: 600 1.6rem/1.2 var(--serif); margin: 0 0 .4rem; }
.market h2 { font: 600 1.15rem/1.3 var(--serif); margin: 2rem 0 .6rem; }
.market h3 { font: 600 1rem/1.3 var(--serif); margin: 1.2rem 0 .3rem; }
.market .lede { color: var(--brownink-soft); max-width: 62ch; margin: 0 0 1rem; }
.market-table-wrap { overflow-x: auto; }
.market table { border-collapse: collapse; width: 100%; font-size: .9rem; }
.market th, .market td { text-align: left; vertical-align: top; padding: .45rem .6rem;
  border-bottom: 1px solid var(--clay-line); }
.market th { font-weight: 600; color: var(--brownink-soft); white-space: nowrap; }
.market td.when { white-space: nowrap; }
.market .status { white-space: nowrap; }
.market .status-upcoming { color: var(--lapis); font-weight: 600; }
.market ul { padding-left: 1.2rem; margin: .2rem 0; }
.market li { margin: .2rem 0; }
.market .muted { color: var(--brownink-soft); }
"""


def market_page(ledger, generated_at):
    """Mike-only market ledger page. Rows say what each source reports."""
    m = ledger["metrics"]
    h = lambda value: escape(str(value)) if value not in (None, "") else "—"

    def bowl(row):
        key = row["identity_id"]
        name = h(row["display_name"] or row["object_id"])
        return '<a href="index.html#/explore/%s">%s</a>' % (escape(key), name) if key else name

    def when(row):
        if row["date"]:
            return h(row["date"])
        return "seen %s" % h(row["observed_at"][:10]) if row["observed_at"] else "—"

    def price(row):
        return h("; ".join(c["value"] for c in row["claims"] if c["field"].startswith("sale_")))

    def where(row):
        text = h(row["locator"])
        return '<a href="%s" rel="noreferrer">%s</a>' % (escape(row["url"]), text) if row["url"] else text

    rows = "\n".join(
        '<tr><td class="when">%s</td><td>%s</td><td>%s</td>'
        '<td class="status status-%s">%s</td><td>%s</td><td>%s</td></tr>' % (
            when(r), h(r["house"]), bowl(r), escape(r["status"]), h(r["status_label"]),
            price(r), where(r))
        for r in ledger["listings"])
    histories = "\n".join(
        '<h3><a href="index.html#/explore/%s">%s</a></h3><ul>%s</ul>' % (
            escape(item["identity_id"]), h(item["display_name"] or item["identity_id"]),
            "".join("<li>%s · %s · %s — %s</li>" % (
                h(e["start_date"] or "undated"), h(e["event_type"]),
                h(e["actor"] or e["place"]), h(e["details"])) for e in item["events"]))
        for item in ledger["repeat_identities"]) or '<p class="muted">None yet.</p>'
    gaps = ledger["gaps"]
    no_price = ", ".join(
        "%s (%s)" % (bowl(r), h(r["house"])) for r in gaps["sold_without_price"]) or "none"
    leads = ", ".join(
        "%s (%s)" % (h(lead["description"][:90]), h(lead["status"]))
        for lead in gaps["open_auction_leads"]) or "none"
    upcoming = m["by_status"].get("upcoming", 0)
    return MARKET_PAGE.format(
        css=MARKET_CSS, generated=escape(generated_at),
        summary="%d listings of %d bowls from %d houses and dealers. %d upcoming; "
                "%d recorded as sold, %d of them with a price." % (
                    m["listings"], m["identities"], m["houses"], upcoming,
                    m["by_status"].get("sold", 0) + m["by_status"].get("sold_no_price", 0),
                    m["by_status"].get("sold", 0)),
        rows=rows, histories=histories, no_price=no_price, leads=leads,
        monitor=monitor_section(ledger["monitor_leads"], bowl_link=lambda key: escape(key)),
        undated=m["undated"])


def monitor_section(leads, bowl_link):
    """Unreviewed lots from the listing monitor, shown above the ledger."""
    if not leads:
        return ""
    h = lambda value: escape(str(value)) if value not in (None, "") else "—"
    items = []
    for lead in leads:
        match = lead.get("possible_match")
        note = ""
        if match and match.get("identity_id"):
            note = ' <span class="muted">· possibly <a href="index.html#/explore/%s">%s</a> (%s)</span>' % (
                bowl_link(match["identity_id"]), h(match["identity_id"]), h(match["basis"]))
        items.append('<li><a href="%s" rel="noreferrer">%s</a> · %s · estimate %s '
                     '<span class="muted">· seen %s</span>%s</li>' % (
                         escape(lead["url"]), h(lead["description"]),
                         h(lead.get("sale_date_text") or "date not shown"),
                         h(lead.get("estimate")), h(lead["observed_at"][:10]), note))
    return ("<h2>New listings awaiting review</h2>\n<p class=\"lede\">Found by the listing "
            "monitor and not yet checked or recorded.</p>\n<ul>%s</ul>" % "".join(items))


MARKET_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Bowlam — Market</title>
<link rel="stylesheet" href="mike.css">
<style>{css}</style>
</head>
<body>
<header class="preview-bar">
  <strong><span class="preview-seal" aria-hidden="true">&#x10840;</span>Bowlam</strong>
<small>Mike Access &middot; market ledger</small>
<nav aria-label="Mike Access sections"><a href="index.html#/explore">Explore</a> &middot;
  <a href="index.html#/scholarship">Scholarship and source files</a> &middot;
  <a href="market.html" aria-current="page">Market</a></nav>
</header>
<main class="market">
<h1>Market</h1>
<p class="lede">{summary} Prices keep each source's wording and currency. A recorded
sale does not establish lawful ownership, export history or authenticity.</p>
{monitor}
<h2>Listings, newest first</h2>
<div class="market-table-wrap"><table>
<thead><tr><th>Date</th><th>House</th><th>Bowl</th><th>Status</th><th>Price wording</th><th>Lot or record</th></tr></thead>
<tbody>
{rows}
</tbody></table></div>
<h2>Bowls on the market more than once</h2>
{histories}
<h2>Gaps to chase</h2>
<p><strong>Recorded as sold, no price:</strong> {no_price}</p>
<p><strong>Listings without a sale date:</strong> {undated}</p>
<p><strong>Open auction leads:</strong> {leads}</p>
</main>
<footer class="preview-foot">
  <p>Private research access for Mike alone. Built {generated}.</p>
</footer>
</body>
</html>
"""


if __name__ == "__main__":
    main()
