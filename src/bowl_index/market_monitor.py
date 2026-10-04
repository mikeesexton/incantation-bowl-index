"""Lead-only monitor for new incantation-bowl lots on public auction search pages.

Like the shadow monitor, it never writes to the corpus. It fetches only search
pages listed in a reviewed registry, re-checks robots.txt on every run, keeps the
response bytes by content hash under the ignored private tree, and writes a lead
for each lot it has not seen before. A lead names any recorded listing it may
duplicate; deciding that is a review step, and so is ingesting the lot.

After a lot's sale time the monitor re-reads its page on a widening schedule to
record the result the platform shows (hammer price, passed, or nothing). It never
follows a redirect that robots.txt forbids: finished lots that move to an
excluded archive address are recorded as unavailable, not read.
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .robots import can_fetch


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


def parse_the_saleroom_lot(body):
    """Sale time and closing state from a the-saleroom lot page.

    The page carries a hidden "auction closed" panel with an ``lot-is-ended`` flag
    and a hammer-price field that reads "Passed" until a price is set.
    """
    ended = re.search(r'id="lot-is-ended" value="([^"]*)"', body)
    when = re.search(r"<time datetime='(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})Z'>([^<]*)</time>",
                     body)
    price = re.search(r'<span id="closed-price" class="amount">([^<]*)</span>\s*'
                      r'<span class="currency closed-currency[^"]*">([^<]*)</span>', body)
    result = {
        "sale_at": "%sT%s:%s:%sZ" % when.groups()[:4] if when else None,
        "sale_at_text": _text(when.group(5)) if when else None,
        "hammer_text": None,
    }
    if ended is None:
        return {**result, "outcome": "unrecognized"}
    if ended.group(1).strip().casefold() != "true":
        return {**result, "outcome": "pending"}
    amount = _text(price.group(1)) if price else ""
    currency = _text(price.group(2)) if price else ""
    if re.search(r"\d", amount):
        return {**result, "outcome": "sold", "hammer_text": ("%s %s" % (amount, currency)).strip()}
    if amount.casefold() == "passed":
        return {**result, "outcome": "passed", "hammer_text": amount}
    return {**result, "outcome": "ended_other", "hammer_text": amount or None}


PARSERS = {"the_saleroom": parse_the_saleroom}
LOT_PARSERS = {"the_saleroom": parse_the_saleroom_lot}

# Days after the sale time at which a lot page is read again for its result.
RESULT_SCHEDULE_DAYS = (0.25, 1, 3, 7, 14)
FINAL_OUTCOMES = {"sold", "passed", "ended_other", "unavailable", "not_shown"}

# Platform search is fuzzy ("demon" finds "Devon"). A lot is a lead only if its own
# title or teaser uses one of these words; the rest are counted, not kept.
RELEVANT = re.compile(
    r"incantation|devil[- ]trap|demon[- ]trap|aramaic|mandaic|syriac|magic bowl|magical bowl",
    re.I)


def is_relevant(lot):
    return bool(RELEVANT.search(" ".join(filter(None, (lot.get("title"), lot.get("teaser"))))))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _fetch(url, user_agent, timeout, max_bytes):
    """(status, body, redirect location). Redirects are returned, never followed."""
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.8"})
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            return response.status, response.read(max_bytes + 1)[:max_bytes], None
    except urllib.error.HTTPError as error:
        location = error.headers.get("Location") if 300 <= error.code < 400 else None
        return error.code, b"", urllib.parse.urljoin(url, location) if location else None


def _robots_body(url, user_agent, fetch, timeout):
    parts = urllib.parse.urlsplit(url)
    return fetch("%s://%s/robots.txt" % (parts.scheme, parts.netloc), user_agent, timeout, 1_000_000)


def _robots_decision(response, url, user_agent):
    """Fail closed: an unreadable robots.txt is not permission."""
    status, body = response[:2]
    if status == 404:
        return True, "robots.txt absent"
    if status != 200:
        return False, "robots.txt HTTP %s" % status
    return can_fetch(body.decode("utf-8", "replace"), user_agent, url), "robots.txt read"


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
                                     settings["max_response_bytes"])[:2]
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
                                          "url": lot["url"], "terms": [term],
                                          "source_id": source["id"]}
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
        results = _check_results(config, state, destination, observed_at, fetch, robots,
                                 sleep, receipt, first_request)
        stamp = observed_at.replace(":", "").replace("-", "")
        _atomic_json(destination / "runs" / (stamp + ".json"), receipt)
        state["updated_at"] = observed_at
        _atomic_json(state_path, state)
        if leads:
            path = destination / "leads" / (stamp + ".jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(lead, ensure_ascii=False, sort_keys=True) + "\n"
                                    for lead in leads), encoding="utf-8")
        if results:
            path = destination / "results" / (stamp + ".jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
                                    for item in results), encoding="utf-8")
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def _parse_time(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _robots_for(url, robots, settings, fetch):
    host = urllib.parse.urlsplit(url).netloc
    if host not in robots:
        robots[host] = _robots_body(url, settings["user_agent"], fetch, settings["timeout_seconds"])
    return _robots_decision(robots[host], url, settings["user_agent"])


def _due(lot, now):
    """A lot page is read once to learn its sale time, then on RESULT_SCHEDULE_DAYS."""
    if lot.get("outcome") in FINAL_OUTCOMES:
        return False
    if not lot.get("sale_at"):
        return lot.get("result_checks", 0) == 0
    after = len(lot.get("post_sale_checks", []))
    if after >= len(RESULT_SCHEDULE_DAYS):
        return False
    return now >= _parse_time(lot["sale_at"]) + timedelta(days=RESULT_SCHEDULE_DAYS[after])


def _check_results(config, state, destination, observed_at, fetch, robots, sleep, receipt,
                   first_request):
    """Read due lot pages; record what each shows. Returns new result records."""
    settings = config["settings"]
    parsers = {source["id"]: LOT_PARSERS.get(source.get("result_parser"))
               for source in config["sources"] if source.get("enabled")}
    now = _parse_time(observed_at)
    receipt["result_checks"] = []
    results = []
    for key, lot in sorted(state["lots"].items()):
        parser = parsers.get(lot.get("source_id") or key.split("/", 1)[0])
        if parser is None or not _due(lot, now):
            continue
        if not first_request:
            sleep(settings["delay_seconds"])
        first_request = False
        check = {"lot": key, "url": lot["url"]}
        receipt["result_checks"].append(check)
        lot["result_checks"] = lot.get("result_checks", 0) + 1
        url, body, status = lot["url"], b"", None
        for _ in range(3):
            allowed, why = _robots_for(url, robots, settings, fetch)
            if not allowed:
                check["robots"] = "%s disallows %s" % (why, url)
                status = "robots_disallowed"
                break
            status, body, location = fetch(url, settings["user_agent"],
                                           settings["timeout_seconds"],
                                           settings["max_response_bytes"])
            if location and 300 <= status < 400:
                url = location
                continue
            break
        check["http_status"] = status
        if status == 200:
            digest = _sha256(body)
            raw = destination / "raw" / digest
            raw.parent.mkdir(parents=True, exist_ok=True)
            if not raw.exists():
                raw.write_bytes(body)
            parsed = parser(body.decode("utf-8", "replace"))
            parsed["raw_sha256"] = digest
        elif status in ("robots_disallowed", 404, 410):
            parsed = {"outcome": "unavailable", "hammer_text": None,
                      "reason": check.get("robots") or "lot page HTTP %s" % status}
        else:
            check["disposition"] = "error"
            continue
        if parsed.get("sale_at"):
            lot["sale_at"], lot["sale_at_text"] = parsed["sale_at"], parsed["sale_at_text"]
        if lot.get("sale_at") and now >= _parse_time(lot["sale_at"]):
            lot.setdefault("post_sale_checks", []).append(observed_at)
        outcome = parsed["outcome"]
        if outcome in ("pending", "unrecognized") and lot.get("sale_at") and \
                len(lot.get("post_sale_checks", [])) >= len(RESULT_SCHEDULE_DAYS):
            outcome = "not_shown"
        lot.update({"outcome": outcome, "hammer_text": parsed.get("hammer_text"),
                    "result_checked_at": observed_at})
        check.update({"disposition": "checked", "outcome": outcome})
        if outcome in FINAL_OUTCOMES:
            results.append({"lot": key, "url": lot["url"], "final_url": url,
                            "observed_at": observed_at, "sale_at": lot.get("sale_at"),
                            "outcome": outcome, "hammer_text": parsed.get("hammer_text"),
                            "price_basis": "hammer price as shown by the platform; "
                                           "excludes buyer's premium",
                            "reason": parsed.get("reason"),
                            "raw_sha256": parsed.get("raw_sha256")})
    receipt["results_recorded"] = len(results)
    return results


def monitor_leads(destination):
    """Every lead the monitor has written, newest first, with its latest result state."""
    destination = Path(destination)
    state = _load_state(destination / "state.json")["lots"]
    leads = []
    for path in sorted(destination.glob("leads/*.jsonl"), reverse=True):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            lead = json.loads(line)
            lot = state.get("%s/%s" % (lead["source_monitor_id"], lead["platform_lot_id"]), {})
            lead["result"] = {name: lot.get(name) for name in (
                "sale_at", "sale_at_text", "outcome", "hammer_text", "result_checked_at")}
            leads.append(lead)
    return leads
