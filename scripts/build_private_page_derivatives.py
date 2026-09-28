"""Render manifest-linked PDF pages into Mike Access's private media directory."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from bowl_index.db import PROJECT_ROOT, connect


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--capture-id", required=True)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    conn = connect()
    capture = conn.execute(
        "SELECT source_id,sha256,storage_path FROM captures WHERE id=?", (args.capture_id,)
    ).fetchone()
    if not capture:
        raise ValueError("unknown capture")
    source = (PROJECT_ROOT / "data/private/archive" / capture["storage_path"]).resolve()
    if sha256(source) != capture["sha256"]:
        raise ValueError("source bytes differ from registered capture")
    outdir = PROJECT_ROOT / "data/private/media"
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["source_id"] != capture["source_id"]:
            raise ValueError("manifest source and capture source differ")
        appearance = conn.execute(
            "SELECT id FROM appearances WHERE source_id=? AND locator=?",
            (row["source_id"], row["appearance"]["locator"]),
        ).fetchone()
        if not appearance:
            raise ValueError("manifest appearance was not ingested")
        for media in row.get("media", []):
            match = re.fullmatch(r"private-capture:" + re.escape(args.capture_id) + r"#page=(\d+)", media["url"])
            if not match:
                raise ValueError("media URL is not a page of this capture")
            page = int(match[1])
            record = conn.execute(
                "SELECT id FROM media WHERE appearance_id=? AND source_id=? AND url=?",
                (appearance["id"], row["source_id"], media["url"]),
            ).fetchone()
            if not record:
                raise ValueError("manifest media was not ingested")
            target = outdir / (record["id"] + ".png")
            subprocess.run(
                [args.pdftoppm, "-f", str(page), "-l", str(page),
                 "-r", "150", "-singlefile", "-png", str(source), str(target.with_suffix(""))],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            results.append({"media_id": record["id"], "pdf_page": page,
                            "sha256": sha256(target), "bytes": target.stat().st_size})
    receipt = {"capture_id": args.capture_id, "capture_sha256": capture["sha256"],
               "source_id": capture["source_id"], "images": results}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered {len(results)} private page images")


if __name__ == "__main__":
    main()
