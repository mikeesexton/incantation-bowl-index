import hashlib
import json
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .ids import new_id


USER_AGENT = "IncantationBowlIndexResearch/0.1 (+noncommercial scholarly corpus)"


def _utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def robots_allowed(url):
    parsed = urlparse(url)
    robots_url = "%s://%s/robots.txt" % (parsed.scheme, parsed.netloc)
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False, "robots.txt could not be verified"
    return parser.can_fetch(USER_AGENT, url), robots_url


def capture_url(conn, url, source_id=None, rights_status="unknown", archive_root=None):
    allowed, robots_note = robots_allowed(url)
    if not allowed:
        raise PermissionError("Fetch disallowed or unverifiable: %s" % robots_note)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            status = getattr(response, "status", 200)
            mime_type = response.headers.get_content_type()
            headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        raise RuntimeError("HTTP %s for %s" % (exc.code, url)) from exc

    digest = hashlib.sha256(body).hexdigest()
    root = Path(archive_root or Path(__file__).resolve().parents[2] / "data" / "private" / "archive")
    destination = root / "sha256" / digest[:2] / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(body)

    capture_id = new_id("capture")
    conn.execute(
        "INSERT OR IGNORE INTO captures "
        "(id, source_id, url, retrieved_at, mime_type, status_code, sha256, byte_length, "
        "storage_path, rights_status, headers_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            capture_id, source_id, url, _utcnow(), mime_type, status, digest, len(body),
            str(destination.relative_to(root)), rights_status, json.dumps(headers, sort_keys=True),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM captures WHERE url=? AND sha256=?", (url, digest)).fetchone()
    return dict(row)


def capture_file(conn, path, source_id=None, rights_status="unknown", note=None,
                 archive_root=None):
    """Archive a document supplied by the researcher rather than fetched.

    Same content-addressed store as `capture_url`, but the URL slot records a
    deposit marker instead of a fetch target. Nothing here made an access-control
    decision: the project did not retrieve this file, so no robots check applies
    and none is implied.
    """
    path = Path(path).expanduser()
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    root = Path(archive_root or Path(__file__).resolve().parents[2] / "data" / "private" / "archive")
    destination = root / "sha256" / digest[:2] / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(body)

    marker = "local-deposit:%s" % path.name
    suffix = path.suffix.lower()
    mime_type = {".pdf": "application/pdf", ".txt": "text/plain",
                 ".json": "application/json"}.get(suffix, "application/octet-stream")
    headers = {
        "deposit": "researcher-supplied local file",
        "deposited_at": _utcnow(),
        "original_filename": path.name,
        "note": note or "",
        "retrieval": "not fetched by this project; no robots or access-control decision was made",
    }
    conn.execute(
        "INSERT OR IGNORE INTO captures "
        "(id, source_id, url, retrieved_at, mime_type, status_code, sha256, byte_length, "
        "storage_path, rights_status, headers_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            new_id("capture"), source_id, marker, _utcnow(), mime_type, None, digest, len(body),
            str(destination.relative_to(root)), rights_status, json.dumps(headers, sort_keys=True),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM captures WHERE url=? AND sha256=?", (marker, digest)).fetchone()
    return dict(row)


def verify_archive(conn, archive_root=None):
    root = Path(archive_root or Path(__file__).resolve().parents[2] / "data" / "private" / "archive")
    problems = []
    for row in conn.execute("SELECT id, sha256, byte_length, storage_path FROM captures"):
        path = root / row["storage_path"]
        if not path.exists():
            problems.append({"capture_id": row["id"], "problem": "missing"})
            continue
        body = path.read_bytes()
        if len(body) != row["byte_length"]:
            problems.append({"capture_id": row["id"], "problem": "length_mismatch"})
        if hashlib.sha256(body).hexdigest() != row["sha256"]:
            problems.append({"capture_id": row["id"], "problem": "hash_mismatch"})
    return problems

