"""Build the gated scholar preview — ACCESS-009.

This is the second public artefact and it is deliberately not the landing page.
ACCESS-008 serves a project-authored overview with *no* path from the page to
the corpus, and `tests/test_public_site.py` enforces that by forbidding
`/api/reader` and `#/explore` from appearing on it. The preview is the surface
that does show data, so it lives at its own path and is expected to be closed by
a Cloudflare Access policy before anyone is pointed at it.

What crosses the boundary is the reviewed release projection and nothing else.
The rows are built by `projection.Projection` — the same code the file exporter
and future public library use — so a row withheld from release is withheld from
every shared surface. The localhost reader deliberately uses a separate private
projection. The console's own `app.js`, with its review and refresh endpoints,
is never copied.

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
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

from bowl_index.projection import PROJECTION_COLUMNS, Projection
from bowl_index.public_export import projection_manifest
from bowl_index.state import corpus_fingerprint

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
WEB = ROOT / "web"
# Deliberately NOT under site/public. That directory is the Pages build output,
# so anything left there ships with the next `wrangler pages deploy` — and this
# artefact is data that ACCESS-009 says must sit behind an Access policy. Build
# it here, attach the policy, then promote it in one move.
OUT = ROOT / "site" / "preview-build"
PROMOTED = ROOT / "site" / "public" / "preview"

FORBIDDEN_ROW_KEYS = {
    "capture_id", "storage_path", "quotation", "notes", "value_text", "value_json",
    "normalized_value", "public_ok", "private_capture_status", "creator", "rights_holder",
}
LOCAL_OR_SECRET_PATTERNS = (
    re.compile(r"/Users/"), re.compile(r"data/private/"), re.compile(r"file://", re.I),
    re.compile(r"\blocalhost\b|127\.0\.0\.1", re.I),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
)

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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_candidate(projection, tables, manifest):
    """Audit the bytes staged for release and describe the exact candidate.

    The result is safe to commit: it contains hashes, counts and licence buckets,
    never the private wording or URLs that failed a gate. It remains pending until
    the project owner records approval.
    """
    checks = []

    def record(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    payloads = {}
    schemas_ok = True
    rows_match = True
    forbidden_keys = set()
    for name, expected in tables.items():
        payload = json.loads((OUT / "data" / (name + ".json")).read_text(encoding="utf-8"))
        payloads[name] = payload
        schemas_ok = schemas_ok and payload["columns"] == list(PROJECTION_COLUMNS[name])
        schemas_ok = schemas_ok and all(set(row) == set(PROJECTION_COLUMNS[name]) for row in payload["rows"])
        rows_match = rows_match and payload["rows"] == expected
        forbidden_keys.update(
            key for row in payload["rows"] for key in row if key in FORBIDDEN_ROW_KEYS
        )
    record("projection_schema", schemas_ok, "%d projected tables match their declared columns" % len(tables))
    record("projection_row_equivalence", rows_match, "built rows equal the shared in-memory projection")
    record("private_columns_absent", not forbidden_keys,
           "no capture, note, quotation, raw-value or reviewer-only columns")

    staged_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(OUT.rglob("*")) if path.is_file()
    )
    bad_patterns = [pattern.pattern for pattern in LOCAL_OR_SECRET_PATTERNS if pattern.search(staged_text)]
    record("local_paths_contacts_and_secrets_absent", not bad_patterns,
           "no local path, private-directory, localhost, email-address or secret pattern")

    private_paths = [path for path in projection.private_storage if path and path in staged_text]
    record("private_capture_paths_absent", not private_paths,
           "%d private capture paths tested" % len(projection.private_storage))

    facts_text = (OUT / "data" / "facts.json").read_text(encoding="utf-8")
    withheld_values = [
        row["value"] for row in projection._fact_candidates()
        if row["release_class"] == "review_source_wording"
    ]
    record("withheld_source_wording_absent", not any(value in facts_text for value in withheld_values),
           "%d priority wording values tested" % len(withheld_values))

    short_claims = [row for row in payloads["facts"]["rows"]
                    if row["release_class"] == "short_source_claim"]
    short_claims_ok = all(
        len(row["value"]) <= 80 and not re.search(r'“[^”]+”|‘[^’]+’|"[^"]+"', row["value"])
        and row["source_id"] and row["locator"] for row in short_claims
    )
    record("short_claim_boundary", short_claims_ok,
           "%d short factual claims are cited, at most 80 characters, and contain no quotation"
           % len(short_claims))

    texts = payloads["texts"]["rows"]
    text_gate_ok = all(
        (row["content"] is not None and row["rights_basis"] and row["content_status"] == "included")
        or (row["content"] is None and row["rights_basis"] is None
            and row["content_status"] == "withheld_consult_the_edition")
        for row in texts
    )
    record("text_gate", text_gate_ok,
           "%d included; %d withheld" % (
               manifest["texts_included_rows"], manifest["texts_withheld_rows"]))

    media = payloads["media"]["rows"]
    media_gate_ok = all(
        row["url"] and row["attribution"] and row["rights_statement"]
        and row["rights_locator"] for row in media
    )
    record("media_gate", media_gate_ok and len(media) == manifest["media_approved_rows"],
           "%d approved media rows carry status, attribution and evidence" % len(media))

    facets = payloads["facets"]["rows"]
    claim_keys = {
        (row["object_id"], row["field"], row["source_id"], row["locator"])
        for row in projection._fact_candidates()
    }
    facet_trace_ok = all(
        (row["object_id"], row["source_field"], row["source_id"], row["locator"]) in claim_keys
        for row in facets
    )
    record("facet_traceability", facet_trace_ok,
           "%d controlled labels resolve to a source claim" % len(facets))

    if not all(check["passed"] for check in checks):
        failed = ", ".join(check["name"] for check in checks if not check["passed"])
        raise ValueError("release audit failed: " + failed)

    files = [
        {"path": str(path.relative_to(OUT)), "sha256": digest(path), "bytes": path.stat().st_size}
        for path in sorted(OUT.rglob("*")) if path.is_file()
    ]
    candidate_material = "\n".join(item["path"] + ":" + item["sha256"] for item in files)
    text_buckets = Counter((row["rights_basis"], row["license_url"] or "") for row in texts
                           if row["content_status"] == "included")
    media_buckets = Counter(row["rights_status"] for row in media)
    state = corpus_fingerprint(projection.conn)
    return {
        "schema_version": 1,
        "artifact": "Bowlam gated scholar preview",
        "candidate_id": hashlib.sha256(candidate_material.encode()).hexdigest(),
        "built_at": manifest["generated_at"],
        "corpus_state_digest": state["corpus_digest"],
        "approval": {"status": "pending_owner_approval", "approved_by": None,
                     "approved_at": None, "note": None},
        "projection_counts": {name: len(rows) for name, rows in tables.items()},
        "withheld_counts": {
            "source_wording": manifest["facts_withheld_wording_rows"],
            "text_content": manifest["texts_withheld_rows"],
            "media": manifest["media_withheld_rows"],
            "private_capture_rows": projection.capture_count,
            "private_storage_paths": len(projection.private_storage),
        },
        "licensing": {
            "project_contribution": {"license": manifest["license"],
                                     "license_url": manifest["license_url"]},
            "texts": [
                {"rights_basis": basis, "license_url": url or None, "rows": count}
                for (basis, url), count in sorted(text_buckets.items())
            ],
            "media": [{"rights_status": status, "rows": count}
                      for status, count in sorted(media_buckets.items())],
            "scope_notice": manifest["license_scope"],
        },
        "audit_checks": checks,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--review-manifest",
                        help="also write the pending, content-free candidate manifest here")
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
    faces = faces.replace('url("/fonts/', 'url("./fonts/')
    (OUT / "preview.css").write_text(
        "/* Generated by scripts/build_scholar_preview.py — do not hand-edit. */\n"
        + faces + "\n\n:root {\n" + light + "\n}\n\n"
        + '@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {\n'
        + "\n".join("  " + line for line in dark.splitlines()) + "\n  }\n}\n"
        + BASE_RULES + "\n"
        + (WEB / "reading.css").read_text(encoding="utf-8"),
        encoding="utf-8")
    shutil.copy2(WEB / "reading.js", OUT / "reading.js")
    shutil.copytree(WEB / "fonts", OUT / "fonts")
    included_texts = [row for row in tables["texts"] if row["content_status"] == "included"]
    text_basis = Counter(row["rights_basis"] for row in included_texts)
    shell = SHELL.replace("__GENERATED__", manifest["generated_at"])
    shell = shell.replace("__PUBLIC_DOMAIN_TEXTS__", str(text_basis["public_domain_expired"]))
    shell = shell.replace("__OWN_WORK_TEXTS__", str(text_basis["own_work"]))
    shell = shell.replace("__OPEN_LICENSE_TEXTS__", str(text_basis["open_license"]))
    shell = shell.replace("__MEDIA_ROWS__", str(len(tables["media"])))
    (OUT / "index.html").write_text(shell, encoding="utf-8")

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

    try:
        candidate = release_candidate(projection, tables, manifest)
    except ValueError as error:
        shutil.rmtree(OUT)
        raise SystemExit("refusing to write: %s" % error)
    candidate_text = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"
    (OUT / "release-candidate.json").write_text(candidate_text, encoding="utf-8")
    if args.review_manifest:
        review_path = Path(args.review_manifest)
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(candidate_text, encoding="utf-8")

    counts = {k: manifest[k] for k in (
        "texts_included_rows", "texts_withheld_rows",
        "media_approved_rows", "media_withheld_rows")}
    print("built %s" % OUT)
    print("  %d tables  ·  %.1f MB of projected rows" % (len(tables), written / 1e6))
    print("  " + "  ·  ".join("%s %s" % (k.replace("_rows", "").replace("_", " "), v)
                              for k, v in counts.items()))
    print("  release audit %d/%d checks passed  ·  candidate %s" % (
        sum(check["passed"] for check in candidate["audit_checks"]),
        len(candidate["audit_checks"]), candidate["candidate_id"][:12]))
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
  <p>This preview serves a reviewed projection, not the working database.
     Withheld texts retain a citation and locator so the edition can be consulted.</p>
  <p>Reuse terms and attribution appear with each included item; source-specific
     terms continue to govern material not created by Bowlam.</p>
  <p><a href="release-candidate.json">Release inventory and passed privacy checks</a>
     &middot; built __GENERATED__.</p>
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
