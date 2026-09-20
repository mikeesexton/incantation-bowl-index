"""Build the gated scholar preview — ACCESS-009.

This is the second public artefact and it is deliberately not the landing page.
ACCESS-008 serves a project-authored overview with *no* path from the page to
the corpus, and `tests/test_public_site.py` enforces that by forbidding
`/api/reader` and `#/explore` from appearing on it. The preview is the surface
that does show data, so it lives at its own path and is expected to be closed by
a Cloudflare Access policy before anyone is pointed at it.

What crosses the boundary is the reviewed projection and nothing else. The rows
are built by `projection.Projection` — the same code the file exporter and the
local reader API use — so a row that is withheld here is withheld everywhere,
and there is no second implementation to disagree with the first. The console's
own `app.js`, with its review and refresh endpoints, is never copied.

Usage:

    PYTHONPATH=src .venv/bin/python scripts/build_scholar_preview.py

Writes `site/preview-build/`, which is outside the Pages output directory on
purpose: until a Cloudflare Access policy is attached, anything under
`site/public/` is served to anyone who asks. Attach the policy to
`bowlam.com/preview*` first, then promote:

    rm -rf site/public/preview && cp -R site/preview-build site/public/preview
    cd site && npx wrangler pages deploy
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from pathlib import Path

from bowl_index.projection import PROJECTION_COLUMNS, Projection
from bowl_index.public_export import projection_manifest

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
WEB = ROOT / "web"
# Deliberately NOT under site/public. That directory is the Pages build output,
# so anything left there ships with the next `wrangler pages deploy` — and this
# artefact is data that ACCESS-009 says must sit behind an Access policy. Build
# it here, attach the policy, then promote it in one move.
OUT = ROOT / "site" / "preview-build"
PROMOTED = ROOT / "site" / "public" / "preview"

# reading.css styles the reading room but inherits its palette from the console
# stylesheet. Rather than ship styles.css — the console is never deployed — lift
# exactly the tokens reading.css and the base rules below actually read. Missing
# one is a build failure, not a silent fallback to an unstyled page.
TOKENS = ("ink", "paper", "lapis", "amber", "amber-ink", "sans", "serif")

BASE_RULES = """
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; color: var(--ink); background: var(--paper); font: 1rem/1.48 var(--sans); }
a { color: inherit; }
button, input, select, textarea { font: inherit; color: inherit; }
button, select { cursor: pointer; }
.skip-link { position: fixed; top: -100px; left: 1rem; z-index: 50; padding: .7rem 1rem;
  background: var(--ink); color: var(--paper); }
.skip-link:focus { top: 1rem; }
.preview-bar { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: baseline;
  padding: .9rem clamp(1rem, 4vw, 2.5rem); border-bottom: 1px solid var(--clay-line);
  background: var(--reading-surface); }
.preview-bar strong { font: 600 1.05rem/1 var(--serif); letter-spacing: .01em; }
.preview-bar small { color: var(--brownink-soft); }
.preview-bar .preview-seal { font-family: var(--hebrew); margin-right: .45rem; }
.reading-room { display: block; }
.preview-foot { padding: 2rem clamp(1rem, 4vw, 2.5rem) 3rem; color: var(--brownink-soft);
  border-top: 1px solid var(--clay-line); font-size: .86rem; }
.preview-foot p { margin: .4rem 0; max-width: 62ch; }
"""


def block(css: str, start: str, end_at: int | None = None) -> str:
    index = css.index(start)
    return css[index:css.index("\n}", index)]


def tokens(css: str) -> tuple[str, str]:
    """The light and dark values of exactly the tokens the preview needs.

    Every token must resolve in `:root`. The dark block only overrides colour —
    the typefaces do not change with the scheme — so a token missing there is
    expected and simply inherits.
    """
    light_src = block(css, ":root {")
    dark_src = block(css, ':root:not([data-theme="light"]) {')
    out = []
    for source, required in ((light_src, True), (dark_src, False)):
        found = []
        for name in TOKENS:
            match = re.search(r"^\s*--%s\s*:\s*([^;]+);" % re.escape(name), source, re.M)
            if not match:
                if required:
                    raise SystemExit(
                        "refusing to write: --%s is no longer in web/styles.css" % name)
                continue
            found.append("  --%s: %s;" % (name, match.group(1).strip()))
        out.append("\n".join(found))
    return out[0], out[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    projection = Projection(conn)
    tables = projection.tables()
    manifest = projection_manifest(projection, tables)
    manifest["tables"] = {
        name: {"rows": len(rows), "url": "./data/%s.json" % name}
        for name, rows in tables.items()
    }
    manifest["served_from"] = "gated scholar preview"

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)

    written = 0
    for name, rows in tables.items():
        payload = {"table": name, "columns": list(PROJECTION_COLUMNS[name]),
                   "total": len(rows), "offset": 0, "rows": rows}
        path = OUT / "data" / ("%s.json" % name)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        written += path.stat().st_size
    (OUT / "data" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    css = (WEB / "styles.css").read_text(encoding="utf-8")
    light, dark = tokens(css)
    faces = "\n".join(match.group(0) + "\n}" for match in
                      re.finditer(r"@font-face \{[^}]+", css))
    (OUT / "preview.css").write_text(
        "/* Generated by scripts/build_scholar_preview.py — do not hand-edit. */\n"
        + faces + "\n\n:root {\n" + light + "\n}\n\n"
        + '@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {\n'
        + "\n".join("  " + line for line in dark.splitlines()) + "\n  }\n}\n"
        + BASE_RULES + "\n"
        + (WEB / "reading.css").read_text(encoding="utf-8"),
        encoding="utf-8")
    shutil.copy2(WEB / "reading.js", OUT / "reading.js")
    (OUT / "index.html").write_text(SHELL.replace(
        "__GENERATED__", manifest["generated_at"]), encoding="utf-8")

    # Belt and braces. Projection.guard already refuses a private capture path
    # per table; check the bytes that actually reached disk.
    private = {row["storage_path"] for row in conn.execute("SELECT storage_path FROM captures")}
    for path in sorted(OUT.rglob("*")):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        for secret in private:
            if secret and secret in body:
                shutil.rmtree(OUT)
                raise SystemExit("refusing to write: %s names private capture storage" % path.name)

    counts = {k: manifest[k] for k in (
        "texts_included_rows", "texts_withheld_rows",
        "media_approved_rows", "media_withheld_rows")}
    print("built %s" % OUT)
    print("  %d tables  ·  %.1f MB of projected rows" % (len(tables), written / 1e6))
    print("  " + "  ·  ".join("%s %s" % (k.replace("_rows", "").replace("_", " "), v)
                              for k, v in counts.items()))
    print("\nNot deployed. This directory is outside site/public, so it cannot ship")
    print("by accident. Attach the Access policy to bowlam.com/preview* first, then:")
    print("  rm -rf site/public/preview && cp -R site/preview-build site/public/preview")
    print("  cd site && npx wrangler pages deploy")
    if PROMOTED.exists():
        print("\nNOTE: %s already exists and WILL deploy. Remove it if the gate is not up."
              % PROMOTED)


SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Bowlam — scholar preview</title>
<link rel="stylesheet" href="preview.css">
</head>
<body>
<a class="skip-link" href="#explore-view">Skip to the bowls</a>
<header class="preview-bar">
  <strong><span class="preview-seal" aria-hidden="true">&#x10840;</span>Bowlam</strong>
  <small>Scholar preview &middot; a reviewed export of the Incantation Bowl Index</small>
</header>
<main>
  <section id="explore-view" class="reading-room" aria-labelledby="explore-title"></section>
</main>
<footer class="preview-foot">
  <p>This preview serves a reviewed export, not the working database. Withheld
     rows keep their citation and locator so the edition can be consulted.</p>
  <p>Rows carry their own <code>rights_basis</code> and <code>license_url</code>;
     where a source licence is narrower than this index's CC BY 4.0, that licence
     governs. Built __GENERATED__.</p>
</footer>
<script>
  window.READER_BASE = "./data";
  window.READER_SUFFIX = ".json";
  window.READER_STANDALONE = true;
</script>
<script src="reading.js" defer></script>
<script>
  // The console routes with app.js; the preview needs only the reading room.
  addEventListener("DOMContentLoaded", function () {
    function go() {
      if (!location.hash.startsWith("#/explore")) {
        history.replaceState(null, "", "#/explore");
      }
      window.ReadingRoom.render();
    }
    addEventListener("hashchange", go);
    go();
  });
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
