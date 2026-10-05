"""Private evidence intake and change packets for the scheduled market agent.

The agent reads collected HTML and local alert emails, then submits candidate
observations. This module validates evidence hashes and appends private leads;
it never opens or writes the corpus. Listing URLs are keys, not bowl identities.
"""

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

from .market_monitor import (_atomic_json, _fetch, _robots_body, _robots_decision,
                             _utc_now, is_relevant, monitor_leads)


def _hash(body):
    return hashlib.sha256(body).hexdigest()


def _stamp(now):
    return now.replace(":", "").replace("-", "")


def _guard(root):
    if (root / "DISABLED").exists():
        raise RuntimeError("market agent disabled")


def collect(config_path, root, settings, fetch=_fetch, sleep=time.sleep, now=None):
    """Collect only reviewed URLs, with fresh robots evidence and no redirects."""
    root = Path(root)
    _guard(root)
    config = json.loads(Path(config_path).read_text())
    if config.get("schema_version") != 1:
        raise ValueError("unsupported market agent registry")
    now = now or _utc_now()
    receipt = {"schema_version": 1, "observed_at": now, "corpus_writes": 0,
               "config_sha256": _hash(Path(config_path).read_bytes()),
               "requests": [], "emails": [], "limitations": config.get("limits")}
    processed = {item["sha256"] for path in (root / "runs").glob("*.json")
                 for item in json.loads(path.read_text()).get("emails_read", [])}

    def archive(body, suffix):
        digest = _hash(body)
        path = root / "evidence" / (digest + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(body)
        return digest, str(path.resolve())

    for i, page in enumerate(config["pages"]):
        if i:
            sleep(settings["delay_seconds"])
        entry = {**page, "channel": "permitted_page"}
        receipt["requests"].append(entry)
        try:
            robots = _robots_body(page["url"], settings["user_agent"], fetch,
                                  settings["timeout_seconds"])
            entry["robots_http_status"] = robots[0]
            entry["robots_sha256"], entry["robots_path"] = archive(robots[1], ".robots")
            allowed, why = _robots_decision(robots, page["url"], settings["user_agent"])
            entry["robots"] = why
            if not allowed:
                entry["disposition"] = "robots_disallowed"
                continue
            sleep(settings["delay_seconds"])
            status, body, location = fetch(page["url"], settings["user_agent"],
                                           settings["timeout_seconds"],
                                           settings["max_response_bytes"])
            entry.update(http_status=status, redirect_not_followed=location)
            if status != 200:
                entry["disposition"] = "unavailable"
                continue
            entry["sha256"], entry["path"] = archive(body, ".html")
            challenge = re.search(rb"cf-chl-|captcha-delivery\.com|checking (?:your )?browser|verify you are human",
                                  body, re.I)
            entry["disposition"] = "challenge" if challenge else "collected"
            if len(body) >= settings["max_response_bytes"]:
                entry["disposition"] = "truncated"
        except Exception as error:
            entry.update(disposition="error", error=str(error))
    for path in sorted((root / "evidence" / "inbox").glob("*.eml")):
        digest, archived = archive(path.read_bytes(), ".eml")
        receipt["emails"].append({"channel": "alert_email", "sha256": digest, "path": archived,
                                 "previously_processed": digest in processed})
    path = root / "collections" / (_stamp(now) + ".json")
    if path.exists():
        raise ValueError("collection timestamp already exists")
    _atomic_json(path, receipt)
    return {"collection": str(path.resolve()), **receipt}


def finish(collection_path, candidates, root, monitor_dir, now=None):
    """Validate a complete extraction before writing; exact replay is harmless."""
    root, monitor_dir = Path(root), Path(monitor_dir)
    _guard(root)
    collection_path = Path(collection_path).resolve()
    if collection_path.parent != (root / "collections").resolve():
        raise ValueError("collection must be in this agent's collection directory")
    collection = json.loads(collection_path.read_text())
    evidence = {item["sha256"]: item for item in collection["requests"]
                if item.get("disposition") == "collected"}
    evidence.update({item["sha256"]: item for item in collection["emails"]})
    submitted = _hash(json.dumps(candidates, sort_keys=True, ensure_ascii=False).encode())
    stamp = _stamp(collection["observed_at"])
    receipt_path = root / "runs" / (stamp + ".json")
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["submission_sha256"] != submitted:
            raise ValueError("completed extraction cannot be replaced")
        return receipt
    now = now or _utc_now()
    completed = sorted((root / "runs").glob("*.json"))
    previous_receipt = json.loads(completed[-1].read_text()) if completed else {}
    consumed = set(previous_receipt.get("scripted_files", []))
    scripted_updates = {"leads": [], "observations": [], "results": []}
    for directory in scripted_updates:
        for path in sorted((monitor_dir / directory).glob("*.jsonl")):
            key = "%s/%s:%s" % (directory, path.name, _hash(path.read_bytes()))
            if key not in consumed:
                scripted_updates[directory].extend(json.loads(line) for line in
                    path.read_text(encoding="utf-8").splitlines() if line.strip())
            consumed.add(key)
    monitor_receipts = sorted((monitor_dir / "runs").glob("*.json"))
    scripted_coverage = json.loads(monitor_receipts[-1].read_text()) if monitor_receipts else None
    current = {lead["url"].rstrip("/"): lead for lead in monitor_leads(monitor_dir, root)}
    new, changes = [], []
    seen_urls = set()
    for candidate in candidates:
        url = candidate.get("url", "")
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username:
            raise ValueError("candidate requires a public listing URL")
        item = evidence.get(candidate.get("evidence_sha256"))
        if not item or _hash(Path(item["path"]).read_bytes()) != candidate["evidence_sha256"]:
            raise ValueError("missing or changed collection evidence")
        if item["channel"] == "permitted_page" and parsed.netloc != urlsplit(item["url"]).netloc:
            raise ValueError("page candidate must stay on the collected host")
        if not candidate.get("locator") or not candidate.get("title"):
            raise ValueError("candidate requires a title and evidence locator")
        if not is_relevant({"title": candidate["title"], "teaser": candidate.get("teaser")}):
            raise ValueError("candidate lacks bowl-specific terminology")
        key = url.rstrip("/")
        if key in seen_urls:
            raise ValueError("duplicate listing URL in extraction")
        seen_urls.add(key)
        values = {name: candidate.get(name) for name in (
            "url", "title", "house", "lot_number", "sale_date_text", "estimate", "teaser",
            "asking_price", "result_text", "provenance_text", "quantity_text", "price_basis")}
        values["url"] = url
        lead = {**values, "lead_type": "auction", "status": "open", "observed_at": now,
                "source_monitor_id": "agent:" + item.get("id", "alert-email"),
                "search_term": "agent extraction", "platform_lot_id": _hash(key.encode())[:24],
                "channel": item["channel"], "possible_match": None,
                "description": "%s: %s" % (values["house"] or "Unknown house", values["title"]),
                "evidence": {"sha256": candidate["evidence_sha256"], "path": item["path"],
                             "source_url": item.get("url"), "locator": candidate["locator"]},
                "automation_boundary": "Private lead only; no identity, authenticity, legality or rights decision."}
        previous = current.get(key)
        if previous is None:
            new.append(lead)
        old_values = {name: previous.get(name) for name in values} if previous else None
        if old_values != values:
            changes.append({"url": url, "observed_at": now, "previous": old_values,
                            "current": values, "evidence": lead["evidence"]})
    # Validation above must finish before any lead or observation file is written.
    for directory, rows in (("leads", new), ("observations", changes)):
        if rows:
            path = root / directory / (stamp + ".jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    receipt = {"schema_version": 1, "observed_at": now, "collection": str(collection_path),
               "submission_sha256": submitted, "corpus_writes": 0,
               "candidates": len(candidates), "new_leads": new, "changes": changes,
               "scripted_updates": scripted_updates, "scripted_files": sorted(consumed),
               "scripted_coverage": scripted_coverage,
               "first_packet_includes_backlog": not bool(completed),
               "coverage": collection["requests"], "emails_read": collection["emails"],
               "limitations": collection["limitations"]}
    _atomic_json(receipt_path, receipt)
    return receipt
