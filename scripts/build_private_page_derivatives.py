"""Render manifest-linked PDF pages into Mike Access's private media directory."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
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
    parser.add_argument("--scale-to", type=int, help="Maximum page dimension in pixels")
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
    rendered = {}
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
            if page not in rendered:
                with tempfile.TemporaryDirectory(prefix="ibi-page-") as tempdir:
                    page_file = Path(tempdir) / "page"
                    scale = (["-scale-to", str(args.scale_to)] if args.scale_to else ["-r", "150"])
                    subprocess.run(
                        [args.pdftoppm, "-f", str(page), "-l", str(page),
                         *scale, "-singlefile", "-png", str(source), str(page_file)],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                    )
                    rendered[page] = (outdir / f"_source_{args.capture_id}_{page}.png")
                    shutil.copyfile(page_file.with_suffix(".png"), rendered[page])
            shutil.copyfile(rendered[page], target)
            results.append({"media_id": record["id"], "pdf_page": page,
                            "sha256": sha256(target), "bytes": target.stat().st_size})
    receipt = {"capture_id": args.capture_id, "capture_sha256": capture["sha256"],
               "source_id": capture["source_id"], "scale_to": args.scale_to,
               "images": results}
    for intermediate in rendered.values():
        intermediate.unlink()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered {len(results)} private page images")


if __name__ == "__main__":
    main()
