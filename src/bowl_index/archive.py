import hashlib
import json
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .ids import new_id
from .robots import can_fetch


USER_AGENT = "IncantationBowlIndexResearch/0.1 (+noncommercial scholarly corpus)"


def _utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


MAX_REDIRECTS = 5


def _fetch_robots(robots_url):
    """(status, body) for robots.txt. Redirects are followed, as RFC 9309 allows."""
    request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return getattr(response, "status", 200), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def robots_allowed(url):
    """Whether USER_AGENT may fetch ``url``, with wildcard rules honoured.

    Status handling matches urllib.robotparser: 401/403 deny everything, any
    other 4xx means there is no robots file, and an unreachable or failing
    robots.txt is not permission.
    """
    parsed = urlparse(url)
    robots_url = "%s://%s/robots.txt" % (parsed.scheme, parsed.netloc)
    try:
        status, body = _fetch_robots(robots_url)
    except Exception:
        return False, "robots.txt could not be verified"
    if status == 200:
        return can_fetch(body.decode("utf-8", "replace"), USER_AGENT, url), robots_url
    if status in (401, 403):
        return False, robots_url
    if 400 <= status < 500:
        return True, robots_url
    return False, "robots.txt could not be verified"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _open(url):
    """Open one URL without following redirects; a 3xx arrives as HTTPError."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.build_opener(_NoRedirect).open(request, timeout=30)


def capture_url(conn, url, source_id=None, rights_status="unknown", archive_root=None):
    """Fetch and archive a URL. Every redirect hop is re-checked against robots.txt."""
    target = url
    for _ in range(MAX_REDIRECTS + 1):
        allowed, robots_note = robots_allowed(target)
        if not allowed:
            raise PermissionError("Fetch disallowed or unverifiable: %s (%s)" % (robots_note, target))
        try:
            with _open(target) as response:
                body = response.read()
                status = getattr(response, "status", 200)
                mime_type = response.headers.get_content_type()
                headers = dict(response.headers.items())
            break
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") if 300 <= exc.code < 400 else None
            if not location:
                raise RuntimeError("HTTP %s for %s" % (exc.code, target)) from exc
            target = urljoin(target, location)
    else:
        raise RuntimeError("Too many redirects for %s" % url)

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


def import_capture_receipts(conn, manifest, project_root):
    """Transfer earlier project retrievals from a hash-bound local rehearsal.

    No network request or fresh access permission is implied. Preserve the
    original capture row, including its URL, headers and retrieval timestamp.
    Validate all entries before appending anything; never replace a capture.
    """
    if manifest.get('schema_version') != 1 or not manifest.get('entries'):
        raise ValueError('A version 1 capture-transfer manifest is required')
    if not (manifest.get('reviewed_by') or '').strip():
        raise ValueError('Named reviewer required')
    stamp = datetime.fromisoformat(manifest['reviewed_at'].replace('Z', '+00:00'))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('UTC review timestamp required')
    root = Path(project_root).resolve()

    def checked(path, digest):
        rel = Path(path)
        resolved = (root / rel).resolve()
        if rel.is_absolute() or '..' in rel.parts or not resolved.is_relative_to(root):
            raise ValueError('Evidence must remain inside the project')
        if hashlib.sha256(resolved.read_bytes()).hexdigest() != digest:
            raise ValueError('Capture-transfer evidence changed')
        return resolved

    origin = checked(manifest['origin_database_path'], manifest['origin_database_sha256'])
    with sqlite3.connect(origin.as_uri() + '?mode=ro', uri=True) as prior:
        prior.row_factory = sqlite3.Row
        planned, seen = [], set()
        for entry in manifest['entries']:
            receipt = json.loads(checked(entry['receipt_path'], entry['receipt_sha256']).read_text())
            cid = receipt['id']
            if cid in seen:
                raise ValueError('Duplicate capture in transfer')
            seen.add(cid)
            original = prior.execute('SELECT * FROM captures WHERE id=?', (cid,)).fetchone()
            if not original or dict(original) != receipt:
                raise ValueError('Receipt differs from the original capture')
            if receipt['status_code'] != 200 or receipt['mime_type'] not in ('text/html', 'application/pdf'):
                raise ValueError('Transfer requires an earlier successful HTML or PDF retrieval')
            captured_at = datetime.fromisoformat(receipt['retrieved_at'].replace('Z', '+00:00'))
            if captured_at.utcoffset() is None or captured_at > stamp:
                raise ValueError('Original retrieval must precede review')
            if not conn.execute('SELECT 1 FROM sources WHERE id=?', (receipt['source_id'],)).fetchone():
                raise ValueError('Unknown capture source')
            body = checked('data/private/archive/' + receipt['storage_path'], receipt['sha256'])
            if body.stat().st_size != receipt['byte_length']:
                raise ValueError('Capture length differs')
            if receipt['mime_type'] == 'application/pdf' and not body.read_bytes().startswith(b'%PDF-'):
                raise ValueError('Expected actual PDF bytes')
            robots = checked(entry['robots_path'], entry['robots_sha256'])
            robots_status = entry.get('robots_status_code')
            if robots_status not in (200, 404) or not entry.get('retrieval_basis', '').strip():
                raise ValueError('Original robots response and retrieval basis required')
            expected = urlparse(receipt['url'])
            robots_url = '%s://%s/robots.txt' % (expected.scheme, expected.netloc)
            if entry.get('robots_url') != robots_url:
                raise ValueError('Robots evidence host differs')
            if robots_status == 404:
                # A verified missing robots file permits retrieval.
                # Retain the actual404 bytes and a separate original response
                # receipt; never parse those bytes as a200 permission statement.
                response = json.loads(checked(entry['robots_response_path'],
                                              entry['robots_response_sha256']).read_text())
                observed = datetime.fromisoformat(response['retrieved_at'].replace('Z', '+00:00'))
                if (response['url'] != robots_url or response['status_code'] != 404
                        or response['body_sha256'] != entry['robots_sha256']
                        or observed.utcoffset() is None or observed.utcoffset().total_seconds() != 0
                        or observed > captured_at):
                    raise ValueError('Verified missing-robots response differs')
                permitted = True
            else:
                permitted = can_fetch(robots.read_text(), USER_AGENT, receipt['url'])
            if not permitted:
                raise ValueError('Original robots evidence does not permit retrieval')
            existing = conn.execute('SELECT * FROM captures WHERE id=? OR (url=? AND sha256=?)',
                                    (cid, receipt['url'], receipt['sha256'])).fetchone()
            if existing:
                if dict(existing) != receipt:
                    raise ValueError('Existing capture differs; transfer cannot overwrite')
            else:
                planned.append(receipt)
        with conn:
            for receipt in planned:
                columns = list(receipt)
                conn.execute('INSERT INTO captures (' + ','.join(columns) + ') VALUES ('
                             + ','.join('?' for _ in columns) + ')', [receipt[k] for k in columns])
    return {'entries': len(seen), 'changed': len(planned), 'unchanged': len(seen) - len(planned),
            'network_requests': 0}
