"""Opaque, Mike-only source-capture inventory for local research surfaces."""

from pathlib import Path

from .db import PROJECT_ROOT


ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "archive"


def capture_filename(row):
    # HTML is deliberately a download. A saved external page must not execute
    # as a same-origin application page inside Mike Access.
    suffix = ".pdf" if row["mime_type"] == "application/pdf" else ".bin"
    return row["id"] + suffix


def capture_inventory(conn, url_for):
    return [
        {
            "id": row["id"],
            "source_id": row["source_id"],
            "mime_type": row["mime_type"],
            "byte_length": row["byte_length"],
            "sha256": row["sha256"],
            "retrieved_at": row["retrieved_at"],
            "url": url_for(row),
        }
        for row in conn.execute(
            "SELECT id,source_id,mime_type,byte_length,sha256,retrieved_at "
            "FROM captures ORDER BY retrieved_at,id"
        )
    ]


def checked_capture_path(row, archive_root=ARCHIVE_ROOT):
    root = Path(archive_root).resolve()
    raw = root / row["storage_path"]
    candidate = raw.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("capture escapes private archive: " + row["id"]) from exc
    if not candidate.is_file() or raw.is_symlink():
        raise ValueError("capture missing or symlinked: " + row["id"])
    return candidate
