"""Build reviewed, private-only image derivatives from held PDF captures.

The checked manifest binds each extraction to a media row, capture, document
hash, PDF page and embedded-image index. Output stays under data/private and is
served only by the loopback-bound research console. This is access engineering,
not a public-reuse decision.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from bowl_index.db import PROJECT_ROOT, connect


DEFAULT_MANIFEST = (
    PROJECT_ROOT / "research" / "reviews" /
    "private_media_derivatives_2026-09-21.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "private" / "media"
ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "archive"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def build(conn, manifest_path=DEFAULT_MANIFEST, output=DEFAULT_OUTPUT):
    manifest_path = Path(manifest_path)
    output = Path(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("private media manifest must use schema_version 1")
    pdfimages = shutil.which("pdfimages")
    if not pdfimages:
        raise ValueError("pdfimages (Poppler) is required")
    output.mkdir(parents=True, exist_ok=True)
    built = []
    for entry in manifest.get("entries", []):
        row = conn.execute(
            "SELECT m.id media_id,m.source_id media_source,c.source_id capture_source,"
            "c.sha256,c.storage_path,c.mime_type FROM media m JOIN captures c ON c.id=? "
            "WHERE m.id=?",
            (entry["capture_id"], entry["media_id"]),
        ).fetchone()
        if not row:
            raise ValueError("unknown media/capture pair: " + entry["media_id"])
        if row["media_source"] != row["capture_source"]:
            raise ValueError("media and capture belong to different sources")
        if row["sha256"] != entry["capture_sha256"]:
            raise ValueError("stale capture hash for " + entry["media_id"])
        if row["mime_type"] != "application/pdf":
            raise ValueError("capture is not a PDF: " + entry["capture_id"])
        source = (ARCHIVE_ROOT / row["storage_path"]).resolve()
        if ARCHIVE_ROOT.resolve() not in source.parents or not source.is_file():
            raise ValueError("capture storage path is missing or unsafe")
        if digest(source) != entry["capture_sha256"]:
            raise ValueError("capture bytes do not match manifest hash")
        page = int(entry["pdf_page"])
        index = int(entry["embedded_image_index"])
        if page < 1 or index < 0:
            raise ValueError("PDF page and image index must be non-negative")
        with tempfile.TemporaryDirectory(prefix="ibi-private-media-") as temporary:
            prefix = Path(temporary) / "image"
            subprocess.run(
                [pdfimages, "-f", str(page), "-l", str(page), "-png",
                 str(source), str(prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            images = sorted(Path(temporary).glob("image-*.png"))
            if index >= len(images):
                raise ValueError(
                    "%s requested embedded image %d but page yielded %d"
                    % (entry["media_id"], index, len(images))
                )
            image = images[index]
            if not image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("pdfimages did not produce a PNG")
            destination = output / (entry["media_id"] + ".png")
            shutil.copyfile(image, destination)
        built.append({
            "media_id": entry["media_id"],
            "destination": str(destination.relative_to(PROJECT_ROOT)),
            "sha256": digest(destination),
            "bytes": destination.stat().st_size,
        })
    return built


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    conn = connect()
    try:
        rows = build(conn, args.manifest, args.output)
    finally:
        conn.close()
    print(json.dumps({"built": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
