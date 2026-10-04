"""Lead-only monitor for new incantation-bowl lots on public auction search pages.

Like the shadow monitor, it never writes to the corpus. It fetches only search
pages listed in a reviewed registry, re-checks robots.txt on every run, keeps the
response bytes by content hash under the ignored private tree, and writes a lead
for each lot it has not seen before. A lead names any recorded listing it may
duplicate; deciding that is a review step, and so is ingesting the lot.
"""

import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment or ""))).strip()


def parse_the_saleroom(body, base_url):
    """Lot cards from a the-saleroom search page (server-rendered HTML)."""
    lots = []
    for card in re.split(r'<article class="panel item', body)[1:]:
        card = card.split("</article>", 1)[0]
        lot_id = re.search(r'id="lot-([0-9a-f-]{36})"', card)
        href = re.search(r'href="(/[^"]+/lot-[0-9a-f-]{36})"', card)
        if not (lot_id and href):
            continue
        number = re.search(r'<span class="lot-number">([^<]*)</span>', card)
        title = re.search(r'<span class="lot-title">(.*?)</span>', card, re.S)
        house = re.search(r'<div class="byline client-url">\s*<a[^>]*>(.*?)</a>', card, re.S)
        teaser = re.search(r'<div class="description">(.*?)</div>', card, re.S)
        estimate = re.search(r'<li class="estimate">.*?<span>Estimate</span>\s*<span>(.*?)</span>',
                             card, re.S)
        date = re.search(r'<div class="date[^"]*">\s*<span>Date:</span>\s*<strong>(.*?)</strong>',
                         card, re.S)
        auction = re.search(r'data-auction-ref="([^"]+)"', card)
        lots.append({
            "platform_lot_id": lot_id.group(1),
            "url": urllib.parse.urljoin(base_url, html.unescape(href.group(1))),
            "lot_number": _text(number.group(1)) if number else None,
            "title": _text(title.group(1)) if title else None,
            "house": _text(house.group(1)) if house else None,
            "teaser": _text(teaser.group(1)) if teaser else None,
            "estimate": _text(estimate.group(1)) if estimate else None,
            "sale_date_text": _text(date.group(1)) if date else None,
            "auction_ref": auction.group(1) if auction else None,
        })
    # The page always links a "next" page; its own item count says whether more exist.
    total = re.search(r"<div>(\d[\d,]*) item\(s\)</div>", body)
    truncated = bool(total) and int(total.group(1).replace(",", "")) > len(lots)
    return lots, truncated


PARSERS = {"the_saleroom": parse_the_saleroom}

# Platform search is fuzzy ("demon" finds "Devon"). A lot is a lead only if its own
# title or teaser uses one of these words; the rest are counted, not kept.
RELEVANT = re.compile(
    r"incantation|devil[- ]trap|demon[- ]trap|aramaic|mandaic|syriac|magic bowl|magical bowl",
    re.I)


def is_relevant(lot):
    return bool(RELEVANT.search(" ".join(filter(None, (lot.get("title"), lot.get("teaser"))))))


def _fetch(url, user_agent, timeout, max_bytes):
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(max_bytes + 1)[:max_bytes]
    except urllib.error.HTTPError as error:
        return error.code, b""


def _robots_body(url, user_agent, fetch, timeout):
    parts = urllib.parse.urlsplit(url)
    return fetch("%s://%s/robots.txt" % (parts.scheme, parts.netloc), user_agent, timeout, 1_000_000)


def _robots_decision(response, url, user_agent):
    """Fail closed: an unreadable robots.txt is not permission."""
    status, body = response
    if status == 404:
        return True, "robots.txt absent"
    if status != 200:
        return False, "robots.txt HTTP %s" % status
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.decode("utf-8", "replace").splitlines())
    return parser.can_fetch(user_agent, url), "robots.txt read"


def _norm(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def known_listing_index(ledger):
    """Recorded listings keyed for lookup: by URL, and by (house token, lot number)."""
    by_url, by_lot = {}, {}
    for row in ledger.get("listings", []):
        if row.get("url"):
            by_url[row["url"].rstrip("/")] = row
        for number in re.findall(r"\blot (\d+)\b", (row.get("locator") or "").casefold()):
            for token in _norm(row.get("house")).split()[:1]:
                by_lot[(token, number)] = row
    return by_url, by_lot


def possible_match(lot, index):
    by_url, by_lot = index
    row = by_url.get(lot["url"].rstrip("/"))
    basis = "same URL"
    if row is None and lot.get("lot_number"):
        token = (_norm(lot.get("house")).split() or [""])[0]
        row = by_lot.get((token, lot["lot_number"].strip()))
        basis = "same house and lot number; sale not compared"
    if row is None:
        return None
    return {"identity_id": row.get("identity_id"), "object_id": row.get("object_id"),
            "locator": row.get("locator"), "date": row.get("date"), "basis": basis}


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _load_state(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema_version": 1, "lots": {}}


def run_market_monitor(config_path, destination, ledger=None, fetch=None, now=None,
                       sleep=time.sleep):
    """One bounded pass over the registry. Returns its receipt; writes leads for unseen lots."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("lead_only") is not True:
        raise ValueError("registry must be schema version 1 and lead_only=true")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / "DISABLED").exists():
        raise RuntimeError("market monitoring is disabled by %s" % (destination / "DISABLED"))
    lock = destination / ".run.lock"
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError as exc:
        raise RuntimeError("another market monitoring run is active") from exc

    settings = config["settings"]
    fetch = fetch or _fetch
    observed_at = now or _utc_now()
    state_path = destination / "state.json"
    state = _load_state(state_path)
    index = known_listing_index(ledger or {})
    receipt = {"schema_version": 1, "mode": "lead_only", "observed_at": observed_at,
               "registry_sha256": _sha256(Path(config_path).read_bytes()),
               "requests": [], "new_leads": 0, "corpus_writes": 0}
    leads, first_request, robots = [], True, {}
    try:
        for source in config["sources"]:
            if not source.get("enabled"):
                continue
            parser = PARSERS[source["parser"]]
            for term in config["search_terms"]:
                url = source["search_url"].format(term=urllib.parse.quote_plus(term))
                entry = {"source_id": source["id"], "term": term, "url": url}
                receipt["requests"].append(entry)
                if not first_request:
                    sleep(settings["delay_seconds"])
                first_request = False
                host = urllib.parse.urlsplit(url).netloc
                if host not in robots:
                    robots[host] = _robots_body(url, settings["user_agent"], fetch,
                                                settings["timeout_seconds"])
                allowed, why = _robots_decision(robots[host], url, settings["user_agent"])
                entry["robots"] = why
                if not allowed:
                    entry["disposition"] = "robots_disallowed"
                    continue
                status, body = fetch(url, settings["user_agent"], settings["timeout_seconds"],
                                     settings["max_response_bytes"])
                entry["http_status"] = status
                if status != 200:
                    entry["disposition"] = "error"
                    continue
                digest = _sha256(body)
                raw = destination / "raw" / digest
                raw.parent.mkdir(parents=True, exist_ok=True)
                if not raw.exists():
                    raw.write_bytes(body)
                lots, truncated = parser(body.decode("utf-8", "replace"), url)
                relevant = [lot for lot in lots if is_relevant(lot)]
                entry.update({"disposition": "parsed", "raw_sha256": digest,
                              "lots": len(lots), "relevant_lots": len(relevant),
                              "more_pages_not_read": truncated})
                for lot in relevant:
                    key = "%s/%s" % (source["id"], lot["platform_lot_id"])
                    seen = state["lots"].get(key)
                    if seen:
                        seen["last_seen"] = observed_at
                        seen.setdefault("terms", [])
                        if term not in seen["terms"]:
                            seen["terms"].append(term)
                        continue
                    match = possible_match(lot, index)
                    state["lots"][key] = {"first_seen": observed_at, "last_seen": observed_at,
                                          "url": lot["url"], "terms": [term]}
                    leads.append({
                        "lead_type": "auction",
                        "status": "open",
                        "source_monitor_id": source["id"],
                        "search_term": term,
                        "observed_at": observed_at,
                        "description": "%s, lot %s: %s" % (
                            lot["house"] or "Unknown house", lot["lot_number"] or "?",
                            lot["title"] or "untitled"),
                        **lot,
                        "possible_match": match,
                        "automation_boundary": "Lead only: no corpus manifest, merge, "
                                               "authenticity or rights decision was applied.",
                    })
        receipt["new_leads"] = len(leads)
        stamp = observed_at.replace(":", "").replace("-", "")
        _atomic_json(destination / "runs" / (stamp + ".json"), receipt)
        state["updated_at"] = observed_at
        _atomic_json(state_path, state)
        if leads:
            path = destination / "leads" / (stamp + ".jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(lead, ensure_ascii=False, sort_keys=True) + "\n"
                                    for lead in leads), encoding="utf-8")
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def monitor_leads(destination):
    """Every lead the monitor has written, newest first."""
    leads = []
    for path in sorted(Path(destination).glob("leads/*.jsonl"), reverse=True):
        leads.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                     if line.strip())
    return leads
