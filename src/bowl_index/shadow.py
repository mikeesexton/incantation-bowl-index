"""Read-only source monitoring for the Mac mini shadow-run pilot.

This module deliberately has no database imports.  It fetches only endpoints
listed in a reviewed registry, retains response bytes by content hash under the
ignored private tree, and emits change leads without applying a corpus manifest.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SAFE_HEADERS = ("content-type", "content-length", "etag", "last-modified", "retry-after")


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug_timestamp(value):
    return value.replace("-", "").replace(":", "").replace("Z", "Z")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _remove_json_path(value, path):
    current = value
    parts = path.split(".")
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return
        current = current[part]
    if isinstance(current, dict):
        current.pop(parts[-1], None)


def normalized_body(body, content_type, ignored_paths):
    """Return stable bytes for semantic change detection while retaining raw bytes."""
    if "json" not in (content_type or "").casefold():
        return body
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return body
    for path in ignored_paths or []:
        _remove_json_path(value, path)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fetch(request_config, user_agent, timeout, retries, max_bytes, sleep=time.sleep):
    method = request_config.get("method", "GET").upper()
    if method not in {"GET", "HEAD"}:
        raise ValueError("shadow monitor permits only GET and HEAD")
    last_error = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                request_config["url"], method=method, headers={"User-Agent": user_agent}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise ValueError("response exceeded %s bytes" % max_bytes)
                headers = {
                    key: response.headers.get(key)
                    for key in SAFE_HEADERS
                    if response.headers.get(key) is not None
                }
                return int(response.status), headers, body
        except (OSError, urllib.error.URLError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                sleep(2 ** attempt)
    raise RuntimeError(str(last_error))


def _load_state(path):
    if not path.exists():
        return {"schema_version": 1, "requests": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_raw(raw_dir, digest, body):
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / digest
    if not path.exists():
        path.write_bytes(body)
    return path


def _change_lead(source, request_config, result, previous):
    return {
        "lead_type": "source_change",
        "source_monitor_id": source["id"],
        "request_id": request_config["id"],
        "description": "Reviewed monitoring endpoint changed during the read-only shadow run.",
        "url": request_config["url"],
        "status": "open",
        "priority": source.get("lead_priority", 3),
        "observed_at": result["observed_at"],
        "previous_fingerprint": previous["fingerprint"],
        "current_fingerprint": result["fingerprint"],
        "automation_boundary": "Lead only: no corpus manifest, merge, rights decision, or publication action was applied.",
    }


def run_shadow(config_path, destination, fetcher=None, now=None, sleep=time.sleep):
    """Run one bounded monitoring pass and return its content-free receipt."""
    config_path = Path(config_path)
    destination = Path(destination)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("shadow_only") is not True:
        raise ValueError("registry must be schema version 1 and shadow_only=true")

    destination.mkdir(parents=True, exist_ok=True)
    if (destination / "DISABLED").exists():
        raise RuntimeError("shadow monitoring is disabled by data/private/monitoring/DISABLED")
    lock_path = destination / ".run.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
    except FileExistsError as exc:
        raise RuntimeError("another shadow monitoring run is active") from exc

    observed_at = now or _utc_now()
    state_path = destination / "state.json"
    registry_digest = _sha256(config_path.read_bytes())
    loaded_state = _load_state(state_path)
    registry_changed = bool(loaded_state["requests"]) and (
        loaded_state.get("registry_sha256") != registry_digest
    )
    previous_state = (
        {"schema_version": 1, "requests": {}} if registry_changed else loaded_state
    )
    next_state = {
        "schema_version": 1,
        "updated_at": observed_at,
        "registry_sha256": registry_digest,
        "requests": dict(previous_state["requests"]),
    }
    receipt = {
        "schema_version": 1,
        "mode": "read_only_shadow",
        "observed_at": observed_at,
        "registry_sha256": registry_digest,
        "registry_changed": registry_changed,
        "results": [],
        "summary": {"baseline": 0, "unchanged": 0, "changed": 0, "errors": 0, "disabled": 0},
        "corpus_writes": 0,
    }
    leads = []
    fetch = fetcher or _fetch
    settings = config["settings"]

    try:
        for source in config["sources"]:
            if not source.get("enabled", False):
                receipt["summary"]["disabled"] += len(source.get("requests", []))
                continue
            for request_config in source["requests"]:
                key = "%s/%s" % (source["id"], request_config["id"])
                result = {
                    "source_id": source["id"],
                    "request_id": request_config["id"],
                    "method": request_config.get("method", "GET").upper(),
                    "url": request_config["url"],
                    "observed_at": observed_at,
                }
                try:
                    status, headers, body = fetch(
                        request_config,
                        settings["user_agent"],
                        settings["timeout_seconds"],
                        settings["retry_count"],
                        settings["max_response_bytes"],
                        sleep,
                    )
                    content_type = headers.get("content-type", "")
                    raw_digest = _sha256(body)
                    stable_body = normalized_body(
                        body, content_type, request_config.get("ignore_json_paths", [])
                    )
                    fingerprint_payload = {
                        "status": status,
                        "content_type": content_type.split(";", 1)[0].strip().casefold(),
                        "body_sha256": _sha256(stable_body),
                    }
                    fingerprint = _sha256(json.dumps(
                        fingerprint_payload, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8"))
                    _write_raw(destination / "raw", raw_digest, body)
                    previous = previous_state["requests"].get(key)
                    disposition = "baseline" if previous is None else (
                        "unchanged" if previous.get("fingerprint") == fingerprint else "changed"
                    )
                    result.update({
                        "disposition": disposition,
                        "http_status": status,
                        "response_headers": headers,
                        "byte_length": len(body),
                        "raw_sha256": raw_digest,
                        "fingerprint": fingerprint,
                    })
                    receipt["summary"][disposition] += 1
                    if disposition == "changed":
                        leads.append(_change_lead(source, request_config, result, previous))
                    next_state["requests"][key] = {
                        "fingerprint": fingerprint,
                        "raw_sha256": raw_digest,
                        "http_status": status,
                        "observed_at": observed_at,
                    }
                except Exception as exc:  # one endpoint must not suppress the rest of the receipt
                    result.update({"disposition": "error", "error": "%s: %s" % (type(exc).__name__, exc)})
                    receipt["summary"]["errors"] += 1
                receipt["results"].append(result)
                if settings.get("delay_seconds", 0):
                    sleep(settings["delay_seconds"])

        run_name = _slug_timestamp(observed_at) + ".json"
        _atomic_json(destination / "runs" / run_name, receipt)
        _atomic_json(state_path, next_state)
        if leads:
            leads_path = destination / "leads" / (_slug_timestamp(observed_at) + ".jsonl")
            leads_path.parent.mkdir(parents=True, exist_ok=True)
            leads_path.write_text(
                "".join(json.dumps(lead, ensure_ascii=False, sort_keys=True) + "\n" for lead in leads),
                encoding="utf-8",
            )
        return receipt
    finally:
        lock_path.unlink(missing_ok=True)
