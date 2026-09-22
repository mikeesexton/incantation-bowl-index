"""Build Mike's complete, single-user private research surface.

This is not a release builder. It uses ``PrivateResearchProjection`` and retains
every stored text, recorded media row and source wording available to Mike's
private reader. The generated directory contains protected third-party material,
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

from bowl_index.db import PROJECT_ROOT
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(projection, tables, manifest):
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

    db_media = projection.conn.execute("SELECT count(*) FROM media").fetchone()[0]
    built_media = payloads["media"]["rows"]
    record("all_media_present", len(built_media) == db_media,
           "%d/%d recorded media rows are available" % (len(built_media), db_media))

    private_facts = projection._fact_candidates()
    record("all_source_wording_present", payloads["facts"]["rows"] == private_facts,
           "%d fact rows retain Mike-private source wording" % len(private_facts))

    staged_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(OUT.rglob("*")) if path.is_file()
    )
    bad_patterns = [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(staged_text)]
    record("local_paths_and_secrets_absent", not bad_patterns,
           "no local path, private-directory or secret pattern")

    private_paths = [path for path in projection.private_storage if path and path in staged_text]
    record("capture_storage_paths_absent", not private_paths,
           "%d private capture paths tested" % len(projection.private_storage))

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
            "status": "pending_single_user_access_gate_and_explicit_deployment",
            "shared_or_public_use": "forbidden; rebuild with Projection",
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
    projection = PrivateResearchProjection(conn)
    tables = projection.tables()
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)

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
    shutil.copy2(WEB / "reading.js", OUT / "reading.js")
    shutil.copytree(WEB / "fonts", OUT / "fonts")
    (OUT / "index.html").write_text(
        SHELL.replace("__GENERATED__", generated_at), encoding="utf-8")

    try:
        snapshot = inventory(projection, tables, manifest)
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
  <small>Mike Access &middot; complete personal research bank</small>
</header>
<main><section id="explore-view" class="reading-room" aria-labelledby="explore-title"></section></main>
<footer class="preview-foot">
  <p>Private research access for Mike alone. This surface includes complete held
     texts and recorded images; it is not a public or shared release.</p>
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
      if (!location.hash.startsWith("#/explore")) history.replaceState(null, "", "#/explore");
      window.ReadingRoom.render();
    }
    addEventListener("hashchange", go); go();
  });
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
