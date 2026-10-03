"""Reproducible, append-only intake of hash-bound researcher-supplied files."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .ingest import SOURCE_FIELDS


def ingest_deposits(conn, manifest, project_root):
    """Validate the whole batch, then append sources and local capture receipts.

    The receipt is a deposit, never an HTTP retrieval or an access decision.
    Explicit IDs and the manifest's UTC time make rehearsal and replay exact.
    Existing source metadata and capture receipts cannot be replaced here.
    """
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("version 1 deposit manifest with entries required")
    reviewer = (manifest.get("reviewed_by") or "").strip()
    stamp = manifest.get("reviewed_at", "")
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if not reviewer or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("named reviewer and UTC deposit timestamp required")
    if conn.in_transaction:
        raise ValueError("deposit requires a clean transaction")
    root = Path(project_root).resolve()
    archive = root / "data/private/archive"
    lifecycle_stamp = parsed.strftime("%Y-%m-%d %H:%M:%S")
    sources = []
    source_ids = set()
    for source in manifest.get("new_sources", []):
        if set(source) != {"id", *SOURCE_FIELDS} or not source["id"]:
            raise ValueError("new source requires its id and all stable fields")
        if source["id"] in source_ids:
            raise ValueError("duplicate source id")
        source_ids.add(source["id"])
        payload = {**source, "created_at": lifecycle_stamp, "updated_at": lifecycle_stamp}
        old = conn.execute("SELECT * FROM sources WHERE id=?", (source["id"],)).fetchone()
        if old and dict(old) != payload:
            raise ValueError("existing source differs; use source correction workflow")
        sources.append((payload, bool(old)))

    entries = []
    capture_ids, markers = set(), set()
    for entry in manifest["entries"]:
        rel = Path(entry["path"])
        path = (root / rel).resolve()
        if rel.is_absolute() or ".." in rel.parts or not path.is_relative_to(root):
            raise ValueError("deposit file must remain inside project")
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != entry["sha256"] or len(body) != entry["byte_length"]:
            raise ValueError("deposit bytes changed")
        if entry["mime_type"] == "application/pdf" and not body.startswith(b"%PDF-"):
            raise ValueError("PDF deposit lacks PDF signature")
        capture_id, source_id = entry["id"], entry["source_id"]
        filename = entry["original_filename"]
        if not capture_id or not filename or Path(filename).name != filename:
            raise ValueError("capture id and plain original filename required")
        if not (entry.get("note") or "").strip():
            raise ValueError("deposit provenance note required")
        if source_id not in source_ids and not conn.execute(
            "SELECT 1 FROM sources WHERE id=?", (source_id,)
        ).fetchone():
            raise ValueError("deposit source missing")
        marker = "local-deposit:" + filename
        key = (marker, digest)
        if capture_id in capture_ids or key in markers:
            raise ValueError("duplicate capture id or deposited content marker")
        capture_ids.add(capture_id)
        markers.add(key)
        storage = Path("sha256") / digest[:2] / digest
        destination = archive / storage
        if destination.exists() and destination.read_bytes() != body:
            raise ValueError("existing archive bytes differ")
        headers = {
            "deposit": "researcher-supplied local file",
            "deposited_at": stamp, "reviewed_by": reviewer,
            "original_filename": filename, "note": entry["note"],
            "retrieval": "not fetched by this project; no robots or access-control decision was made",
            "provenance": entry.get("provenance", {}),
        }
        payload = dict(
            id=capture_id, source_id=source_id, url=marker, retrieved_at=stamp,
            mime_type=entry["mime_type"], status_code=None, sha256=digest,
            byte_length=len(body), storage_path=str(storage),
            rights_status=entry["rights_status"],
            headers_json=json.dumps(headers, ensure_ascii=False, sort_keys=True),
        )
        old = conn.execute("SELECT * FROM captures WHERE id=? OR (url=? AND sha256=?)",
                           (capture_id, marker, digest)).fetchall()
        if old and (len(old) != 1 or dict(old[0]) != payload):
            raise ValueError("existing capture differs; cannot replace a receipt")
        entries.append((payload, bool(old), destination, body))

    conn.execute("BEGIN IMMEDIATE")
    try:
        for payload, exists in sources:
            if not exists:
                cols = list(payload)
                conn.execute("INSERT INTO sources (%s) VALUES (%s)" % (
                    ",".join(cols), ",".join("?" for _ in cols)), list(payload.values()))
        for payload, exists, destination, body in entries:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with destination.open("xb") as stream:
                    stream.write(body)
            if destination.read_bytes() != body:
                raise ValueError("archived bytes failed verification")
            if not exists:
                cols = list(payload)
                conn.execute("INSERT INTO captures (%s) VALUES (%s)" % (
                    ",".join(cols), ",".join("?" for _ in cols)), list(payload.values()))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"new_sources": sum(not old for _, old in sources),
            "new_captures": sum(not old for _, old, _, _ in entries),
            "unchanged_captures": sum(old for _, old, _, _ in entries),
            "network_requests": 0}
