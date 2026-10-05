"""Private email/lot intelligence. Immutable operational runs; never corpus writes.

A committed run is the transaction boundary: views and processing state are
reconstructed from it, so a crash cannot mark mail processed without its items.
Mail/page content is untrusted evidence, never executable instructions.
"""
import base64
import hashlib
import html
import ipaddress
import json
import os
import re
import sqlite3
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .market_monitor import _atomic_json, _fetch, _robots_body, _robots_decision, _utc_now

VERSION = 3
FIELDS = ("url", "title", "house", "platform", "sale_name", "sale_number", "sale_id",
          "lot_number", "stock_number", "sale_date_text", "sale_at", "sale_timezone",
          "full_description", "language_stated", "script_stated", "dimensions_text",
          "condition_text", "estimate", "estimate_low", "estimate_high", "currency",
          "starting_bid", "asking_price", "hammer", "premium_total", "buyer_premium",
          "result_text", "provenance_text", "literature", "image_urls", "image_hashes",
          "quantity_text", "price_basis", "search_term", "keyword_hits", "market_status",
          "relevance", "item_type", "notes", "historical", "quoted", "description_scope")
DISPOSITIONS = {"relevant", "uncertain", "adjacent_excluded", "literature", "related_amulet",
                "unrelated", "administrative", "announcement", "needs_review"}
STATUSES = {"unknown", "upcoming", "offered", "sold", "unsold", "withdrawn"}
BOWL = re.compile(r"incantation|(?:devil|demon)[ -]?trap|(?:aramaic|syriac|mandaic|magic(?:al)?)\s+(?:terracotta\s+)?bowls?|zauberschale|beschwörungsschale|coupe\s+(?:magique|d.incantation)|bol\s+d.incantation|קערת\s+השבעה", re.I)
ADJACENT = re.compile(r"singing|tibetan|ottoman|islamic|healing|medicine|mixing|magic[ -]trick|decorative reproduction|modern reproduction", re.I)
ADMIN = re.compile(r"registration|activate (?:your |user )?account|confirm your email|verification code|password reset|welcome to biddr", re.I)
ACTION = re.compile(r"(?:login|activate|unsubscribe|preferences|register|sign.?up|reset|logout|bid-now|add-to-cart|checkout)", re.I)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


@contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # The parent is the shared agent runtime; both switches stop new intake.
    if any(p.exists() for p in (root / "DISABLED", root.parent / "DISABLED",
                               root.parent.parent / "market/DISABLED")):
        raise RuntimeError("market intake disabled")
    path = root / ".run.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("another market intake run is active") from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink()


def archive(root, body, suffix):
    key = digest(body)
    path = Path(root) / "evidence" / (key + suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError("archive hash collision or altered evidence")
    else:
        with path.open("xb") as stream:
            stream.write(body)
        path.chmod(0o600)
    return {"sha256": key, "path": str(path.resolve())}


def evidence_bytes(root, evidence):
    path = Path(evidence["path"]).resolve()
    if path.parent != (Path(root) / "evidence").resolve():
        raise ValueError("evidence outside intake archive")
    body = path.read_bytes()
    if digest(body) != evidence["sha256"]:
        raise ValueError("altered evidence")
    return body


def public_url(url):
    p = urlsplit(url or "")
    if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password:
        return False
    if p.port not in (None, 80, 443) or p.hostname.lower() in ("localhost", "localhost.localdomain") or "." not in p.hostname:
        return False
    try:
        if not ipaddress.ip_address(p.hostname).is_global:
            return False
    except ValueError:
        pass
    return not ACTION.search(p.path + "?" + p.query)


def canonical_url(url):
    if not public_url(url):
        raise ValueError("public listing URL required; action links forbidden")
    p = urlsplit(html.unescape(url).strip())
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", urlencode(query), ""))


def deposit_gmail(root, payload, config, now=None):
    """Accept raw Gmail connector snapshots, validating the entire batch first."""
    root = Path(root)
    account = payload.get("account", "").lower()
    if account not in config["accounts"] or payload.get("label") != config["label"]:
        raise ValueError("unexpected mailbox or label")
    account = config.get("canonical_account", config["accounts"][0]).lower()
    now = utc(now or _utc_now())
    messages = payload.get("messages")
    if not isinstance(messages, list) or not payload.get("label_id"):
        raise ValueError("message list and exact label ID required")
    prepared, ids = [], set()
    for message in messages:
        mid = message.get("id", "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", mid) or mid in ids:
            raise ValueError("invalid or duplicate Gmail message ID")
        ids.add(mid)
        if payload["label_id"] not in message.get("label_ids", []):
            raise ValueError("message outside requested label")
        raw = message.get("raw")
        if not isinstance(raw, str) or len(raw) > 30_000_000:
            raise ValueError("bounded raw MIME required")
        try:
            body = base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True)
        except Exception as exc:
            raise ValueError("invalid Gmail raw MIME") from exc
        if not body:
            raise ValueError("empty MIME")
        key = fingerprint([account, mid])
        path = root / "inbox" / (key + ".json")
        prepared.append((key, path, mid, body, message))
    with locked(root):
        # Validate every existing ID while holding the lock, before depositing
        # any new message. A concurrent deposit cannot hide conflicting bytes.
        for key, path, mid, body, message in prepared:
            if path.exists():
                previous = json.loads(path.read_text())
                if previous["evidence"]["sha256"] != digest(body):
                    raise ValueError("immutable message ID has different bytes")
                evidence_bytes(root, previous["evidence"])
        added = 0
        for key, path, mid, body, message in prepared:
            if path.exists():
                continue
            ev = archive(root, body, ".eml")
            received = message.get("internal_date")
            if received is None:
                try:
                    received = str(int(parsedate_to_datetime(str(BytesParser(policy=policy.default).parsebytes(body).get("Date"))).timestamp() * 1000))
                except (ValueError, TypeError):
                    received = None
            record = {"schema_version": 1, "key": key, "account": account, "message_id": mid,
                      "thread_id": message.get("thread_id"), "label": payload["label"],
                      "label_id": payload["label_id"], "received_at_ms": received,
                      "retrieved_at": now, "representation": "Gmail raw RFC 2822 MIME", "evidence": ev}
            _atomic_json(path, record)
            added += 1
        receipt = {"schema_version": 1, "account": account, "observed_at": now,
                   "count": len(messages), "deposited": added, "mailbox_mutations": 0,
                   "search_complete": payload.get("search_complete") is True,
                   "label_count": payload.get("label_count"),
                   "message_keys": [x[0] for x in prepared]}
        _atomic_json(root / "deposits" / (fingerprint(receipt) + ".json"), receipt)
    return receipt


class Document(HTMLParser):
    """Text/link offsets; no rendering, scripts, remote images or resource loads."""
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.chunks, self.links, self.images, self.jsonld = [], [], [], []
        self.anchor = None
        self.hidden = 0
        self.script = None
        self.blockquote = 0
        self.heading = None
        self.headings = []
        self.feed(body)
        self.text = "".join(self.chunks)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.hidden += 1
            if tag == "script" and a.get("type") == "application/ld+json":
                self.script = []
        if tag == "blockquote" or "gmail_quote" in a.get("class", ""):
            self.blockquote += 1
        if tag in ("p", "div", "tr", "li", "br", "h1", "h2", "h3", "h4"):
            self.chunks.append("\n")
        if tag in ("h1", "h2", "h3"):
            self.heading = (tag, len("".join(self.chunks)))
        if tag == "a":
            self.anchor = {"url": a.get("href", ""), "start": len("".join(self.chunks)),
                           "quoted": bool(self.blockquote)}
        if tag == "img" and a.get("src"):
            self.images.append(a["src"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            if self.script is not None:
                try:
                    self.jsonld.append(json.loads("".join(self.script)))
                except ValueError:
                    pass
                self.script = None
            self.hidden = max(0, self.hidden - 1)
        if tag == "a" and self.anchor:
            self.anchor["end"] = len("".join(self.chunks))
            self.anchor["title"] = "".join(self.chunks)[self.anchor["start"]:self.anchor["end"]].strip()
            self.links.append(self.anchor)
            self.anchor = None
        if self.heading and tag == self.heading[0]:
            self.headings.append("".join(self.chunks)[self.heading[1]:].strip())
            self.heading = None
        # gmail_quote wrappers can be nested divs; plain text quotation also checked.
        if tag == "blockquote":
            self.blockquote = max(0, self.blockquote - 1)

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if not self.hidden:
            self.chunks.append(data)


def classify(title, description=""):
    title, text = title or "", (title or "") + " " + (description or "")
    if re.search(r"(?:corpus|book|publication|monograph|ISBN)\b", title, re.I) and BOWL.search(text):
        return "literature", "publication, not a bowl offer"
    if re.search(r"amulet", title, re.I) and re.search(r"aramaic|syriac|mandaic", text, re.I):
        return "related_amulet", "related script tradition; not a bowl"
    if ADJACENT.search(title):
        return "adjacent_excluded", "later, unrelated or explicitly modern bowl category"
    if BOWL.search(text):
        if re.search(r"magic(?:al)?\s+bowl|coupe magique", title, re.I) and not re.search(r"ancient|mesopot|aramaic|syriac|mandaic|terracotta|incantation|sasanian", text, re.I):
            return "uncertain", "generic magic bowl; period and tradition not established"
        return "relevant", "source names an incantation bowl or script tradition"
    if re.search(r"bowl|schale|קערה", text, re.I):
        return "uncertain", "bowl identification needs review"
    return "unrelated", "no bowl or related item evidence"


def price_range(wording):
    if not wording:
        return None, None, None
    currency = next((code for pattern, code in ((r"\b(?:GBP|£)", "GBP"), (r"£", "GBP"),
                    (r"\bUSD\b|US\$", "USD"), (r"\bEUR\b|€", "EUR"), (r"\bCHF\b", "CHF"),
                    (r"\bILS\b|₪", "ILS")) if re.search(pattern, wording, re.I)), None)
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", wording)
    if not currency or not numbers or len(numbers) > 2:
        return None, None, currency
    if any(not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?", n) for n in numbers):
        return None, None, currency  # locale ambiguous: retain exact wording
    values = [float(n.replace(",", "")) for n in numbers]
    return values[0], values[-1], currency


def fields_from_text(text):
    """Only explicitly labelled values; no guessed dates, prices or currency."""
    aliases = {"house": r"(?:Auction house|House|Dealer)", "platform": r"Platform",
               "sale_name": r"Sale name", "sale_id": r"Sale ID", "sale_number": r"Sale number",
               "sale_date_text": r"(?:Auction date|Sale date)", "dimensions_text": r"Dimensions",
               "condition_text": r"Condition", "provenance_text": r"Provenance",
               "literature": r"(?:Literature|Publication references)", "estimate": r"Estimate",
               "starting_bid": r"Starting bid", "asking_price": r"(?:Asking price|Price)",
               "hammer": r"Hammer(?: price)?", "premium_total": r"(?:Price including premium|Total including premium)",
               "buyer_premium": r"Buyer.?s premium", "language_stated": r"Language",
               "script_stated": r"Script", "quantity_text": r"Quantity", "price_basis": r"Price basis",
               "search_term": r"(?:Matched search|Search term)", "result_text": r"Result"}
    out = {}
    for key, label in aliases.items():
        match = re.search(r"(?:^|\n)\s*" + label + r"\s*:\s*([^\n]+)", text, re.I)
        if match:
            out[key] = match.group(1).strip()
    lot = re.search(r"\b(?:Lot|Lote|Los)\s*(?:No\.?\s*)?[:#]?\s*(\d+[A-Za-z]?)\b", text, re.I)
    if lot:
        out["lot_number"] = lot.group(1)
    low, high, currency = price_range(out.get("estimate"))
    out.update(estimate_low=low, estimate_high=high, currency=currency)
    result = (out.get("result_text") or "").strip().casefold()
    out["market_status"] = ("unsold" if re.match(r"(?:unsold|passed)\b", result) else
                            "withdrawn" if result.startswith("withdrawn") else
                            "sold" if result.startswith("sold") or out.get("hammer") else "unknown")
    return out


def extract_email(body, source, config):
    message = BytesParser(policy=policy.default).parsebytes(body)
    subject = str(message.get("Subject", ""))
    sender = str(message.get("From", ""))
    pieces = {"text/plain": [], "text/html": []}
    if message.defects:
        raise ValueError("malformed MIME requires review: " + str(message.defects))
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            continue
        kind = part.get_content_type()
        if kind in pieces:
            try:
                pieces[kind].append(part.get_content())
            except (UnicodeError, LookupError) as exc:
                raise ValueError("undecodable MIME body") from exc
    plain = "\n".join(pieces["text/plain"])
    rich = Document("\n".join(pieces["text/html"]))
    text = rich.text if pieces["text/html"] else plain
    if ADMIN.search(subject) or ADMIN.search(plain[:600]):
        return [{"disposition": "administrative", "reason": "account setup or verification; no lot extraction",
                 "title": subject, "locator": "Subject", "quoted": False}], []
    links = rich.links
    if not links:
        links = [{"url": m.group(0).rstrip(").,>"), "title": "", "start": m.start(), "end": m.end(),
                  "quoted": text[max(0, text.rfind("\n", 0, m.start())):m.start()].lstrip().startswith(">")}
                 for m in re.finditer(r"https?://[^\s<>\"]+", text)]
    rows, seen = [], set()
    correspondence = bool(re.match(r"(?:re|fwd):", subject, re.I))
    for number, link in enumerate(links):
        if not public_url(link["url"]):
            continue
        url = canonical_url(link["url"])
        if url in seen:
            continue
        # A bounded link block, never the whole digest or surrounding unrelated lot.
        previous_end = links[number-1]["end"] if number else 0
        next_start = links[number+1]["start"] if number+1 < len(links) else len(text)
        start = max(previous_end, text.rfind("\n\n", previous_end, link["start"]) + 2)
        end = text.find("\n\n", link["end"], next_start)
        end = next_start if end < 0 else end
        block = text[start:end].strip()
        title = link["title"] or (block.splitlines()[0] if block else subject)
        if not BOWL.search(title + " " + block + " " + url) and not ADJACENT.search(title + " " + block) and not re.search(r"amulet|ISBN|corpus", title, re.I):
            continue
        # Dealer stock-only anchors are explicit identifiers, not invented page titles.
        quoted = link["quoted"] or text[:link["start"]].find(" wrote:") >= 0
        values = fields_from_text(block)
        relevance, reason = classify(title, block + " " + url)
        if re.search(r"(?:make|sell|my|our).*modern bowls", block, re.I) and not re.search(r"/artworks/|/lot[-/]|/item/", url):
            relevance, reason = "adjacent_excluded", "researcher's explicitly modern bowl business link, not an ancient offer"
        house = next((x for x in config["houses"] if x.lower().replace(" gallery", "") in sender.lower()), values.get("house"))
        house = house or next((x.get("house") for x in config["lot_routes"] if x["host"] == urlsplit(url).hostname and x.get("house")), None)
        stock = title if re.fullmatch(r"[A-Z]{1,3}\.\d{3,}", title) else None
        rows.append({**values, "url": url, "title": title, "house": house,
                     "stock_number": stock, "full_description": block, "description_scope": "email_link_block", "relevance": relevance,
                     "disposition": relevance, "reason": reason, "historical": correspondence,
                     "quoted": quoted, "item_type": "dealer_listing" if stock else "auction_lot",
                     "image_urls": [], "keyword_hits": [term for term in config["search_terms"]
                       if term.casefold() in (title + " " + block + " " + url).casefold()],
                     "locator": "MIME body link %d, character offsets %d–%d, anchor %s" %
                                (number+1, link["start"], link["end"], title),
                     "needs_review": True,
                     "notes": "Historical correspondence; present availability unchecked." if correspondence else
                              "Automatic bounded extraction; inspect against original email."})
        seen.add(url)
    if not rows:
        disposition = "announcement" if re.search(r"auction|sale|catalogue", subject + " " + text[:800], re.I) else "unrelated"
        if BOWL.search(text) or (not text.strip() and rich.images):
            disposition = "needs_review"
        rows.append({"title": subject, "disposition": disposition,
                     "reason": "No individual supported lot link; retain message for audit",
                     "locator": "Subject and MIME body", "needs_review": disposition in ("announcement", "needs_review")})
    issues = []
    if any(part.get_content_disposition() == "attachment" for part in message.walk()):
        issues.append("Attachments retained in MIME; not extracted")
    return rows, issues


def listing_key(item):
    if all(item.get(name) for name in ("house", "sale_id", "lot_number")):
        key = ["sale_lot", item["house"].strip().casefold(), item["sale_id"].strip(), item["lot_number"].strip()]
    else:
        key = ["url", canonical_url(item["url"])]
    return "MKT-" + fingerprint(key)[:24].upper()


def provenance_flags(item, previous=None):
    text = item.get("provenance_text")
    flags = []
    scope = "page" if item.get("page_checked") else "email"
    if not text:
        flags.append({"flag": "no_provenance_stated", "scope": scope, "basis": "No provenance in inspected " + scope})
    else:
        years = [int(x) for x in re.findall(r"\b(?:18|19|20)\d{2}\b", text)]
        if years and min(years) > 1970:
            flags.append({"flag": "stated_history_only_after_1970", "scope": scope, "basis": text})
        if not years and re.search(r"private collection|old .*collection|European collection", text, re.I):
            flags.append({"flag": "vague_undated_provenance", "scope": scope, "basis": text})
        countries = re.findall(r"\b(?:Iraq|Iran|Syria|Jordan|Lebanon|Egypt|Uzbekistan|Mesopotamia)\b", text, re.I)
        if countries:
            flags.append({"flag": "country_or_region_mention", "scope": scope, "basis": sorted(set(countries))})
    if previous and text and previous.get("provenance_text") and text != previous["provenance_text"]:
        flags.append({"flag": "changed_provenance_wording", "scope": scope,
                      "previous": previous["provenance_text"], "basis": text})
    return flags


def runs(root):
    records = [json.loads(p.read_text()) for p in sorted((Path(root) / "runs").glob("*.json"))]
    legacy = sorted((r for r in records if "sequence" not in r), key=lambda r: r["observed_at"])
    order = {fingerprint(r): i+1 for i, r in enumerate(legacy)}
    return sorted(records, key=lambda r: r.get("sequence", order.get(fingerprint(r), 0)))


def commit_run(root, run):
    """Called under the intake lock; explicit commit sequence handles same-second runs."""
    records = runs(root)
    run['sequence'] = max([r.get('sequence', i+1) for i,r in enumerate(records)] or [0]) + 1
    path = Path(root) / 'runs' / ('%012d-' % run['sequence'] + run['observed_at'].replace(':','').replace('-','') + '-' + fingerprint(run)[:12] + '.json')
    _atomic_json(path, run)
    return path


def view(root):
    listings, dispositions, processed, errors, coverage = {}, [], {}, [], []
    for run in runs(root):
        errors.extend(run.get("errors", []))
        coverage.extend(run.get("coverage", []))
        for message in run.get("messages", []):
            processed[message["key"]] = message
        for observation in run.get("observations", []):
            key = observation["listing_id"]
            if key not in listings:
                listings[key] = {"listing_id": key, "first_seen": observation["observed_at"],
                                 "aliases": [], "source_email_ids": [], "evidence": [], "history": []}
            row = listings[key]
            row.update(observation["current"])
            row["last_seen"] = observation["observed_at"]
            row["aliases"] = sorted(set(row["aliases"] + observation["aliases"]))
            row["source_email_ids"] = sorted(set(row["source_email_ids"] + observation.get("source_email_ids", [])))
            row["evidence"].extend(observation["evidence"])
            row["history"].append(observation)
            row["provenance_flags"] = observation["provenance_flags"]
            row["field_evidence"] = observation.get("field_evidence", {})
    dispositions = [item for message in processed.values() for item in message["items"]]
    active = [row for row in listings.values() if row.get("relevance") in ("relevant", "uncertain", "related_amulet")]
    excluded = [row for row in listings.values() if row not in active]
    checks = {}
    for path in sorted((Path(root) / "source-checks").glob("*.json")):
        for check in json.loads(path.read_text())["checks"]:
            checks[(check["listing_id"], check["listing_fingerprint"])] = check
    for row in active:
        row["listing_fingerprint"] = source_check_fingerprint(row)
        row["source_check"] = checks.get((row["listing_id"], row["listing_fingerprint"]))
    return {"schema_version": 1, "audience": "Mike alone", "listings": active, "excluded_listings": excluded,
            "dispositions": dispositions, "processed": processed, "errors": errors, "coverage": coverage,
            "counts": dict(Counter(x["disposition"] for x in dispositions))}


def source_check_fingerprint(listing):
    """Bind a source comparison to wording/evidence, not delivery or UI metadata."""
    return fingerprint({"listing_id": listing["listing_id"],
        "values": {k: listing.get(k) for k in FIELDS},
        "evidence": sorted({(e["sha256"], e["locator"]) for e in listing.get("evidence", [])})})


def record_source_checks(root, payload, now=None):
    """Append agent source comparisons; never a human identity/rights decision."""
    root = Path(root)
    now = utc(now or _utc_now())
    submitted = payload.get("checks")
    if not isinstance(submitted, list) or not submitted:
        raise ValueError("source checks required")
    with locked(root):
        latest = {r["listing_id"]: r for r in view(root)["listings"]}
        checks, seen = [], set()
        for item in submitted:
            row = latest.get(item.get("listing_id"))
            if not row or row["listing_id"] in seen:
                raise ValueError("unknown or duplicate listing in source check")
            seen.add(row["listing_id"])
            if item.get("listing_fingerprint") != row["listing_fingerprint"]:
                raise ValueError("source check refers to a stale listing version")
            if item.get("status") not in ("checked", "blocked", "needs_correction") or not item.get("note"):
                raise ValueError("source check needs status and comparison note")
            inspected = item.get("evidence")
            if not isinstance(inspected, list) or not inspected:
                raise ValueError("source check needs inspected evidence and locators")
            available = {e["sha256"]: e for e in row["evidence"]}
            for citation in inspected:
                if not citation.get("locator") or citation.get("sha256") not in available:
                    raise ValueError("source check citation is not archived listing evidence")
                evidence_bytes(root, available[citation["sha256"]])
            if item["status"] == "checked":
                kinds = {available[c["sha256"]]["kind"] for c in inspected}
                required = {e["kind"] for e in row["evidence"] if e["kind"] in ("email", "page")}
                if not required.issubset(kinds):
                    raise ValueError("completed comparison must cite email and any collected page")
            checks.append({"listing_id": row["listing_id"], "listing_fingerprint": row["listing_fingerprint"],
                "status": item["status"], "note": item["note"], "evidence": inspected,
                "checked_at": now, "actor": "agent source comparison",
                "meaning": "Compared extraction with cited sources; no identity, authenticity, rights or legal decision"})
        # Exact repeated comparisons do not create a new receipt or daily alert.
        pending = [c for c in checks if not latest[c["listing_id"]].get("source_check") or
            any(latest[c["listing_id"]]["source_check"].get(k) != c[k] for k in ("status", "note", "evidence"))]
        if not pending:
            return {"recorded": 0, "replay": True, "corpus_writes": 0}
        sequence = len(list((root / "source-checks").glob("*.json"))) + 1
        receipt = {"checked_at": now, "checks": pending, "sequence": sequence, "corpus_writes": 0}
        path = root / "source-checks" / ("%012d-" % sequence + fingerprint(receipt)[:12] + ".json")
        _atomic_json(path, receipt)
        return {"recorded": len(pending), "receipt": str(path.resolve()), "corpus_writes": 0}


def validate_items(items):
    if not isinstance(items, list) or not items:
        raise ValueError("every message needs item dispositions")
    for item in items:
        if item.get("disposition") not in DISPOSITIONS or not item.get("locator") or not item.get("reason"):
            raise ValueError("item needs disposition, reason and exact locator")
        if item.get("url"):
            canonical_url(item["url"])
        if item.get("disposition") in ("relevant", "uncertain", "related_amulet") and not item.get("title"):
            raise ValueError("listing title required")
        if item.get("market_status", "unknown") not in STATUSES:
            raise ValueError("unknown market status")
        if item.get("market_status") in ("sold", "unsold", "withdrawn") and not (item.get("result_text") or item.get("hammer")):
            raise ValueError("outcome requires explicit source wording")
        for ev in item.get("extra_evidence", []):
            if not ev.get("locator"):
                raise ValueError("page evidence locator required")
        for image in item.get("image_hashes") or []:
            if not re.fullmatch(r"[a-f0-9]{16}", image.get("dhash", "")) or not image.get("sha256") or not image.get("path"):
                raise ValueError("image matching requires byte-bound dHash receipt")


def observations(items, source, latest, now, root):
    result = []
    by_url = {url: row for row in latest.values() for url in row["aliases"]}
    for item in items:
        if not item.get("url"):
            continue
        key = listing_key(item)
        old = latest.get(key) or by_url.get(canonical_url(item["url"]))
        if item.get("disposition") not in ("relevant", "uncertain", "related_amulet") and old is None:
            continue
        if old:
            key = old["listing_id"]
        values = {name: item.get(name) for name in FIELDS}
        values.update(url=canonical_url(item["url"]), relevance=item["disposition"], page_checked=item.get("page_checked", False),
                      needs_review=item.get("needs_review", True))
        if not values.get("platform"):
            values["platform"] = (old or {}).get("platform") or urlsplit(values["url"]).hostname
        if old:
            # Missing later fields do not retract earlier evidence. Quoted mentions
            # add evidence only; they cannot change the current offer or wording.
            values = {name: old.get(name) if val is None or item.get("quoted") else val for name, val in values.items()}
            if values.get("market_status") == "unknown" and old.get("market_status") in ("sold", "unsold", "withdrawn"):
                values["market_status"] = old["market_status"]
            for field in ("image_urls", "image_hashes"):
                if not values.get(field):
                    values[field] = old.get(field)
        evs = [{**source["evidence"], "kind": "email", "locator": item["locator"],
                "message_id": source.get("message_id"), "source_key": source["key"]}] + item.get("extra_evidence", [])
        for ev in evs:
            evidence_bytes(root, ev)
        for name, citation in item.get("field_evidence", {}).items():
            if name not in FIELDS or not isinstance(citation, dict) or not citation.get("locator"):
                raise ValueError("field evidence needs a known field and exact locator")
            if citation.get("sha256") not in {ev["sha256"] for ev in evs}:
                raise ValueError("field evidence not bound to this observation's archived sources")
        for image in item.get("image_hashes") or []:
            evidence_bytes(root, image)
            receipts = [json.loads(p.read_text()) for p in (Path(root) / "images").glob("*.json")]
            if not any(r["sha256"] == image["sha256"] and r["dhash"] == image["dhash"] for r in receipts):
                raise ValueError("unregistered image hash")
        old_values = {name: old.get(name) for name in values} if old else None
        changed = old_values != values
        result.append({"listing_id": key, "observed_at": now, "previous": old_values,
                       "current": values, "changed": changed, "new": old is None,
                       "aliases": [canonical_url(item["url"])], "evidence": evs,
                       "source_email_ids": [source["message_id"]] if source.get("message_id") else [],
                       "provenance_flags": provenance_flags(values, old),
                       "field_evidence": {name: item.get("field_evidence", {}).get(name) or
                          ((old or {}).get("field_evidence", {}).get(name) if item.get(name) is None or item.get("quoted") else None) or
                          {"sha256": evs[-1]["sha256"], "locator": evs[-1]["locator"], "kind": evs[-1]["kind"]}
                          for name, val in values.items() if val is not None}})
        # Same batch items must see the preceding alias, too.
        merged = {**(old or {}), **values, "listing_id": key,
                  "aliases": sorted(set((old or {}).get("aliases", []) + [values["url"]]))}
        latest[key] = merged
        by_url[values["url"]] = merged
    return result


def process(root, config, now=None, overrides=None):
    """Process new mail or explicit evidence-bound revised extractions, atomically."""
    root = Path(root)
    now = utc(now or _utc_now())
    overrides = overrides or {}
    with locked(root):
        snapshot = view(root)
        latest = {x["listing_id"]: x for x in snapshot["listings"] + snapshot["excluded_listings"]}
        messages, updates, errors = [], [], []
        known = {json.loads(p.read_text())["key"]: p for p in (root / "inbox").glob("*.json")}
        if set(overrides) - set(known):
            raise ValueError("override for unknown deposited message")
        for key, path in sorted(known.items(), key=lambda pair: (json.loads(pair[1].read_text()).get("received_at_ms") or "", pair[0])):
            source = json.loads(path.read_text())
            previous = snapshot["processed"].get(key)
            if previous and key not in overrides and previous.get("parser_version") == VERSION:
                continue
            try:
                body = evidence_bytes(root, source["evidence"])
                items, issues = extract_email(body, source, config) if key not in overrides else (overrides[key], [])
                validate_items(items)
                extraction_hash = fingerprint(items)
                if previous and previous["extraction_sha256"] == extraction_hash and previous.get("parser_version") == VERSION:
                    continue
                observations_out = observations(items, source, latest, now, root)
                updates.extend(observations_out)
                messages.append({"key": key, "message_id": source.get("message_id"), "processed_at": now,
                                 "evidence": source["evidence"], "parser_version": VERSION,
                                 "extraction_sha256": extraction_hash, "items": items, "limitations": issues,
                                 "supersedes": previous.get("extraction_sha256") if previous else None})
            except Exception as exc:
                if key in overrides:
                    raise  # An agent submission validates wholly before any commit.
                errors.append({"source_key": key, "message_id": source.get("message_id"),
                               "observed_at": now, "error": str(exc), "retry_due": True})
        if not messages and not errors:
            return {"new_listings": 0, "changes": 0, "processed": 0, "errors": [], "replay": True, "corpus_writes": 0}
        run = {"schema_version": 1, "observed_at": now, "messages": messages,
               "observations": updates, "errors": errors, "corpus_writes": 0, "mailbox_mutations": 0,
               "new_listings": sum(x["new"] for x in updates),
               "changes": sum(x["changed"] and not x["new"] for x in updates), "processed": len(messages)}
        path = commit_run(root, run)
        return {"run": str(path.resolve()), **run}


def collect_page(root, url, config, settings, fetch=_fetch, sleep=time.sleep, now=None):
    """Reviewed lot routes only; fresh robots, no redirects or resource loads."""
    now = utc(now or _utc_now())
    receipt = {"url": url, "observed_at": now, "kind": "page", "disposition": "unreviewed_route"}
    if not public_url(url):
        receipt["disposition"] = "invalid_or_action_url"
        return receipt
    p = urlsplit(url)
    route = next((x for x in config["lot_routes"] if p.hostname == x["host"] and
                  re.fullmatch(x["path_pattern"], p.path) and not p.query), None)
    if not route:
        return receipt
    sleep(max(settings["delay_seconds"], route["delay_seconds"]))
    robots = _robots_body(url, settings["user_agent"], fetch, settings["timeout_seconds"])
    ev = archive(root, robots[1], ".robots")
    allowed, why = _robots_decision(robots, url, settings["user_agent"])
    receipt.update(robots_http_status=robots[0], robots=why, robots_evidence=ev, route=route)
    if not allowed or robots[0] == 200 and len(robots[1]) >= 1_000_000:
        receipt["disposition"] = "robots_disallowed_or_unreadable"
        return receipt
    sleep(max(settings["delay_seconds"], route["delay_seconds"]))
    status, body, location = fetch(url, settings["user_agent"], settings["timeout_seconds"], settings["max_response_bytes"])
    receipt.update(http_status=status, redirect_not_followed=location)
    if status != 200:
        receipt["disposition"] = "unavailable"
    elif len(body) >= settings["max_response_bytes"]:
        receipt["disposition"] = "truncated"
    elif re.search(rb"cf-chl-|captcha-delivery\.com|checking (?:your )?browser|verify you are human", body, re.I):
        receipt["disposition"] = "challenge"
    else:
        receipt.update(archive(root, body, ".html"))
        receipt["disposition"] = "collected"
    return receipt


def enrich(root, config, settings, fetch=_fetch, sleep=time.sleep, now=None, retry_failures=False):
    """Bounded repeat checks; failures retained, previous evidence never erased."""
    root = Path(root)
    now = utc(now or _utc_now())
    with locked(root):
        snapshot = view(root)
        recent = {x["url"]: x for x in snapshot["coverage"]}
        coverage, updates, errors = [], [], []
        latest = {x["listing_id"]: x for x in snapshot["listings"]}
        # Maximum ten lot pages per pass; failed pages become due again tomorrow.
        for row in snapshot["listings"]:
            prior = recent.get(row["url"])
            if prior and not (retry_failures and prior["disposition"] in ("unavailable", "robots_disallowed_or_unreadable")) and (datetime.fromisoformat(now.replace("Z", "+00:00")) -
                          datetime.fromisoformat(prior["observed_at"].replace("Z", "+00:00"))).total_seconds() < 86400:
                continue
            if len(coverage) >= 10:
                break
            try:
                capture = collect_page(root, row["url"], config, settings, fetch, sleep, now)
                coverage.append(capture)
                if capture["disposition"] != "collected":
                    continue
                doc = Document(evidence_bytes(root, capture).decode("utf-8", "replace"))
                values = fields_from_text(doc.text)
                # A generic page may contain other items. Full description and
                # headings are retained for agent review, not asserted as an item edition.
                values.update(url=row["url"], title=row["title"], relevance=row["relevance"],
                              disposition=row["relevance"], house=row.get("house"),
                              locator="Original email listing link", reason="Previously extracted listing; public page collected",
                              page_checked=True, needs_review=True,
                              extra_evidence=[{**capture, "locator": "Full lot HTML; bounded labelled fields require review"}])
                values["image_urls"] = [u for u in doc.images if public_url(u)] or None
                if capture["route"]["parser"] == "barakat":
                    values.update(parse_barakat(evidence_bytes(root, capture).decode("utf-8", "replace")))
                    values["extra_evidence"][0]["locator"] = "Dealer item heading; .stock_number; .dimensions; #artwork_description_2; image data-src"
                if capture["route"]["parser"] == "the_saleroom":
                    from .market_monitor import parse_the_saleroom_lot
                    result = parse_the_saleroom_lot(evidence_bytes(root, capture).decode("utf-8", "replace"))
                    values.update(sale_at=result["sale_at"], sale_date_text=result.get("sale_at_text"))
                    if result["outcome"] in ("sold", "passed"):
                        values.update(market_status="sold" if result["outcome"] == "sold" else "unsold",
                                      result_text=result["hammer_text"], hammer=result["hammer_text"] if result["outcome"] == "sold" else None)
                # Avoid replacing an explicit outcome with unknown due to absent fields.
                if values.get("market_status") == "unknown":
                    values.pop("market_status")
                # Missing label-only values aren't evidence to blank earlier fields.
                values = {k: v for k, v in values.items() if v is not None}
                validate_items([values])
                source_ev = next(e for e in row["evidence"] if e["kind"] == "email")
                source = {"key": source_ev["source_key"], "message_id": source_ev.get("message_id"), "evidence": source_ev}
                updates.extend(observations([values], source, latest, now, root))
            except Exception as exc:
                errors.append({"url": row["url"], "error": str(exc), "retry_due": True})
        if not coverage and not errors:
            return {"replay": True, "coverage": [], "corpus_writes": 0}
        run = {"schema_version": 1, "observed_at": now, "messages": [], "coverage": coverage,
               "observations": updates, "errors": errors, "new_listings": 0,
               "changes": sum(x["changed"] for x in updates), "corpus_writes": 0}
        path = commit_run(root, run)
        return {"run": str(path.resolve()), **run}


def corpus_matches(conn, listing):
    """Explainable candidates only. Never writes a link or merges identities."""
    results = []
    stock = listing.get("stock_number")
    if stock and listing.get("house"):
        for row in conn.execute("SELECT object_id,appearance_id,scheme,value,assigning_body FROM identifiers WHERE value=?", (stock,)):
            if row["assigning_body"] and row["assigning_body"].casefold() == listing["house"].casefold():
                results.append({**dict(row), "score": 1.0, "basis": "exact scoped stock number; confirm context", "decision": "awaiting Mike"})
    url = listing.get("url")
    if url:
        for row in conn.execute("SELECT l.object_id,a.id appearance_id,a.locator FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id WHERE a.url=? AND l.relation_type<>'rejected'", (url,)):
            if not any(x.get("object_id") == row["object_id"] for x in results):
                results.append({**dict(row), "score": 0.9, "basis": "same source appearance URL", "decision": "awaiting Mike"})
    literature = listing.get("literature")
    if literature:
        for row in conn.execute("SELECT object_id,source_id,locator,value_text FROM claims WHERE field LIKE '%publication%' OR field LIKE '%edition%'"):
            value = row["value_text"] or ""
            if len(value) >= 12 and value.casefold() in literature.casefold():
                results.append({**dict(row), "score": 0.6, "basis": "reported publication pointer; check catalogue number", "decision": "awaiting Mike"})
                if len(results) >= 10:
                    break
    # Long, distinctive source wording can propose a corpus appearance. Short
    # boilerplate and dimensions alone are never enough. Retain claim locators.
    description = re.sub(r"\s+", " ", listing.get("full_description") or "").strip().casefold()
    if len(description) >= 200:
        for row in conn.execute("SELECT object_id,appearance_id,source_id,locator,value_text FROM claims WHERE field IN ('catalogue_description','object_description','source_physical_description') AND value_text IS NOT NULL AND id NOT IN (SELECT supersedes_claim_id FROM claims WHERE supersedes_claim_id IS NOT NULL)"):
            text = re.sub(r"\s+", " ", row["value_text"]).strip().casefold()
            if len(text) < 200 or min(len(text), len(description)) / max(len(text), len(description)) < .8:
                continue
            similarity = SequenceMatcher(None, description, text).ratio()
            if similarity >= .93 and not any(x.get("object_id") == row["object_id"] for x in results):
                results.append({**dict(row), "score": round(.7 * similarity, 3),
                    "basis": "long catalogue description similarity %.2f; inspect shared dealer wording" % similarity,
                    "decision": "awaiting Mike"})
                results[-1].pop("value_text")
                if len(results) >= 10:
                    break
    # Exact archived bytes are useful even where no corpus perceptual index is
    # available. Only explicitly typed dHash64 values are comparable algorithms.
    for image in listing.get("image_hashes") or []:
        for row in conn.execute("SELECT m.object_id,m.appearance_id,m.source_id,m.id media_id FROM media m JOIN captures c ON c.id=m.capture_id WHERE c.sha256=?", (image["sha256"],)):
            if not any(x.get("object_id") == row["object_id"] for x in results):
                results.append({**dict(row), "score": .9, "basis": "same archived image bytes; inspect stock-photo reuse", "decision": "awaiting Mike"})
        for row in conn.execute("SELECT object_id,appearance_id,source_id,id media_id,perceptual_hash FROM media WHERE perceptual_hash LIKE 'dhash64:%'"):
            encoded = row["perceptual_hash"][8:]
            if not re.fullmatch(r"[a-f0-9]{16}", encoded):
                continue
            distance = bin(int(image["dhash"], 16) ^ int(encoded, 16)).count("1")
            if distance <= 6 and not any(x.get("object_id") == row["object_id"] for x in results):
                results.append({**dict(row), "score": .65, "basis": "corpus image dHash distance %d; inspect crops/stock photos" % distance, "decision": "awaiting Mike"})
    return results


def reappearance_matches(listings):
    candidates = []
    for i, a in enumerate(listings):
        for b in listings[i+1:]:
            signals = []
            if a.get("stock_number") and a.get("stock_number") == b.get("stock_number") and a.get("house") == b.get("house"):
                signals.append((0.7, "same dealer-scoped stock number"))
            for field, weight in (("dimensions_text", .25), ("provenance_text", .3), ("full_description", .3)):
                left, right = a.get(field) or "", b.get(field) or ""
                if len(left) >= 8 and len(right) >= 8:
                    similarity = SequenceMatcher(None, left.casefold(), right.casefold()).ratio()
                    if similarity >= .85:
                        signals.append((weight * similarity, field + " similarity %.2f" % similarity))
            for left in a.get("image_hashes") or []:
                for right in b.get("image_hashes") or []:
                    if left.get("dhash") and right.get("dhash"):
                        distance = bin(int(left["dhash"],16) ^ int(right["dhash"],16)).count("1")
                        if distance <= 6:
                            signals.append((.45, "image dHash distance %d; inspect stock photos/crops" % distance))
            if signals and sum(x[0] for x in signals) >= .25:
                candidates.append({"listing_ids": [a["listing_id"], b["listing_id"]],
                                   "score": min(.99, sum(x[0] for x in signals)),
                                   "basis": [x[1] for x in signals], "decision": "awaiting Mike"})
    return sorted(candidates, key=lambda x: x["score"], reverse=True)


def daily_report(root, conn=None, now=None, acknowledge=False):
    """Durable daily packet. Delivery cursor advances only on explicit ack."""
    from zoneinfo import ZoneInfo
    root = Path(root)
    now = utc(now or _utc_now())
    day = datetime.fromisoformat(now.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date().isoformat()
    with locked(root):
        snapshot = view(root)
        all_runs = runs(root)
        acknowledged = {key for p in (root / "deliveries").glob("*.json") for key in json.loads(p.read_text())["run_hashes"]}
        external_ack = {key for p in (root / "deliveries").glob("*.json") for key in json.loads(p.read_text()).get("external_hashes", [])}
        external_hashes, external_updates = [], {"leads": [], "observations": [], "results": []}
        for runtime in (root.parent, root.parent.parent / "market"):
            for category in external_updates:
                for p in sorted((runtime / category).glob("*.jsonl")):
                    token = str(p.resolve()) + ":" + digest(p.read_bytes())
                    if token not in external_ack:
                        external_hashes.append(token)
                        external_updates[category].extend(json.loads(line) for line in p.read_text().splitlines() if line.strip())
        pending = [r for r in all_runs if fingerprint(r) not in acknowledged]
        latest = {x["listing_id"]: x for x in snapshot["listings"]}
        if conn:
            for row in latest.values():
                row["corpus_matches"] = corpus_matches(conn, row)
        updated = [x for r in pending for x in r.get("observations", []) if x["changed"]]
        new_ids = list(dict.fromkeys(x["listing_id"] for x in updated if x["new"] and x["listing_id"] in latest))
        change_ids = list(dict.fromkeys(x["listing_id"] for x in updated if not x["new"] and x["listing_id"] in latest))
        coverage = {}
        for r in all_runs:
            for c in r.get("coverage", []):
                coverage[c["url"]] = c
        packet = {"schema_version": 1, "audience": "Mike alone", "day": day, "generated_at": now,
                  "baseline": not bool(acknowledged), "run_hashes": [fingerprint(r) for r in pending],
                  "external_hashes": external_hashes, "external_updates": external_updates,
                  "new_listings": [latest[x] for x in new_ids],
                  "results_updated": [latest[x] for x in change_ids if latest[x].get("market_status") in ("sold", "unsold", "withdrawn")],
                  "changed_listings": [latest[x] for x in change_ids],
                  "reappearance_candidates": reappearance_matches(list(latest.values())),
                  "corpus_candidates": [x for x in latest.values() if x.get("corpus_matches")],
                  "provenance_flags": [{"listing_id": x["listing_id"], "flags": x.get("provenance_flags", [])} for x in latest.values()],
                  "needs_review": [x for x in latest.values() if x.get("needs_review") and
                      (x.get("source_check") or {}).get("status") != "checked"],
                  "source_checks": [{"listing_id": x["listing_id"], "fingerprint": x["listing_fingerprint"],
                      "check": x.get("source_check")} for x in latest.values()],
                  "counts": snapshot["counts"], "listing_count": len(latest),
                  "unique_excluded_items": len({x.get("url") or fingerprint(x) for x in snapshot["dispositions"] if x["disposition"] == "adjacent_excluded"}),
                  "errors": [e for r in pending for e in r.get("errors", [])],
                  "coverage": list(coverage.values()), "corpus_writes": 0,
                  "mailbox_coverage": max((json.loads(p.read_text()) for p in (root / "deposits").glob("*.json")), key=lambda r: r["observed_at"], default=None),
                  "message": "No new listings or listing changes." if not updated and not any(external_updates.values()) else "%d new email listing leads; %d changed email listings; %d other new leads; %d other changes/results." % (len(new_ids), len(change_ids), len(external_updates["leads"]), len(external_updates["observations"])+len(external_updates["results"])),
                  "limitations": "Email-derived leads and reviewed lot routes only; historical correspondence is not a new current offer. Missing or blocked results are unknown, never sold."}
        # Immutable packet; latest.json is just a reconstructable convenience pointer.
        key = fingerprint(packet)
        path = root / "reports" / (day + "-" + key[:12] + ".json")
        if not path.exists():
            _atomic_json(path, packet)
        lines = ["# Bowlam auction watch — " + day, "", "Private to Mike. " + packet["message"], ""]
        if packet["baseline"]:
            lines += ["Initial baseline; includes historical leads.", ""]
        for section, rows in (("New listing leads", packet["new_listings"]), ("Results updated", packet["results_updated"]), ("Changed listings", packet["changed_listings"]), ("Awaiting review", packet["needs_review"])):
            if rows:
                lines += ["## " + section, ""]
                for row in rows:
                    money = "; ".join("%s %s" % (label, row[field]) for label, field in
                        (("estimate", "estimate"), ("asking", "asking_price"), ("hammer", "hammer"),
                         ("including premium", "premium_total")) if row.get(field)) or "price not stated"
                    lines.append("- %s · %s · %s · %s · [%s](%s)%s" % (row.get("title"), row.get("house") or "unknown house", row.get("sale_date_text") or "date unknown", money, row["listing_id"], row["url"], " · historical correspondence" if row.get("historical") else ""))
                lines.append("")
        lines += ["## Scheduled source checks", "", "Routine extraction checks run in chat; identity suggestions remain Mike's decisions.", ""]
        lines.extend("- %s: %s" % (x["listing_id"], (x["check"] or {}).get("status", "scheduled")) for x in packet["source_checks"])
        lines += ["", "## Dispositions", "", json.dumps(packet["counts"], ensure_ascii=False), "",
                  "%d unique adjacent/excluded item(s); counts above include quoted references." % packet["unique_excluded_items"], "",
                  "## Match candidates", ""]
        lines.extend("- %s: %s" % (row["listing_id"], json.dumps(row["corpus_matches"], ensure_ascii=False)) for row in packet["corpus_candidates"])
        lines.extend("- Possible reappearance: " + json.dumps(candidate, ensure_ascii=False) for candidate in packet["reappearance_candidates"])
        lines += ["", "## Provenance flags", ""]
        lines.extend("- %s: %s" % (row["listing_id"], "; ".join(f["flag"] for f in row["flags"])) for row in packet["provenance_flags"] if row["flags"])
        lines += ["", "## Other monitored pages", ""]
        for category, rows in external_updates.items():
            lines.extend("- %s: %s" % (category, json.dumps(row, ensure_ascii=False)) for row in rows)
        lines += ["",
                  "## Coverage and errors", ""]
        if packet["mailbox_coverage"]:
            lines.append("- Gmail label scan: %s; complete: %s; messages inspected: %s" % (packet["mailbox_coverage"]["observed_at"], packet["mailbox_coverage"]["search_complete"], packet["mailbox_coverage"]["count"]))
        lines.extend("- %s: %s" % (c["url"], c["disposition"]) for c in packet["coverage"])
        lines.extend("- " + e["error"] for e in packet["errors"])
        lines += ["", packet["limitations"]]
        md = path.with_suffix(".md")
        md.write_text("\n".join(lines) + "\n")
        _atomic_json(root / "reports/latest.json", {"path": str(path.resolve()), "sha256": digest(path.read_bytes())})
        if acknowledge:
            # Saved delivery receipt means the chat digest was produced, never read.
            _atomic_json(root / "deliveries" / (day + "-" + key[:12] + ".json"),
                         {"observed_at": now, "packet_sha256": digest(path.read_bytes()), "run_hashes": packet["run_hashes"], "external_hashes": packet["external_hashes"]})
        return {"report": str(path.resolve()), "markdown": str(md.resolve()), **packet}


def import_eml(root, path, now=None):
    """Researcher deposit; not an HTTP or Gmail retrieval claim."""
    root, path = Path(root), Path(path)
    now = utc(now or _utc_now())
    body = path.read_bytes()
    key = fingerprint(['local_eml', digest(body)])
    destination = root / 'inbox' / (key + '.json')
    with locked(root):
        if destination.exists():
            return {'deposited': 0, 'key': key}
        ev = archive(root, body, '.eml')
        _atomic_json(destination, {'schema_version': 1, 'key': key, 'message_id': None,
                     'account': None, 'received_at_ms': None, 'retrieved_at': now,
                     'representation': 'Researcher-deposited MIME', 'evidence': ev})
    return {'deposited': 1, 'key': key}


def ack_report(root, path, now=None):
    root, path = Path(root), Path(path).resolve()
    if path.parent != (root / 'reports').resolve() or path.name == 'latest.json':
        raise ValueError('exact saved packet required')
    packet = json.loads(path.read_text())
    if path.name != packet['day'] + '-' + fingerprint(packet)[:12] + '.json':
        raise ValueError('altered packet')
    with locked(root):
        known = {fingerprint(run) for run in runs(root)}
        if not set(packet['run_hashes']).issubset(known):
            raise ValueError('packet refers to unknown runs')
        ev = {'observed_at': utc(now or _utc_now()), 'packet_sha256': digest(path.read_bytes()),
              'run_hashes': packet['run_hashes'], 'external_hashes': packet.get('external_hashes', []),
              'meaning': 'Chat digest produced, not read'}
        destination = root / 'deliveries' / path.name
        if not destination.exists():
            _atomic_json(destination, ev)
        return {'acknowledged': str(path), 'runs': len(packet['run_hashes'])}


def difference_hash(path):
    """64-bit perceptual dHash from actual local image pixels; not identity proof.

    Uses macOS's image decoder when Pillow isn't installed. Only a temporary
    resized BMP is written; the deposited source bytes are never changed.
    """
    try:
        from PIL import Image
        with Image.open(path) as image:
            values = list(image.convert('L').resize((9, 8)).getdata())
    except ImportError:
        import struct
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory(prefix='ibi-image-hash-') as temp:
            bmp = Path(temp) / 'resized.bmp'
            subprocess.run(['/usr/bin/sips', '-s', 'format', 'bmp', '--resampleHeightWidth',
                            '8', '9', str(Path(path).resolve()), '--out', str(bmp)],
                           check=True, capture_output=True, timeout=20)
            body = bmp.read_bytes()
            offset = struct.unpack_from('<I', body, 10)[0]
            width, height = struct.unpack_from('<ii', body, 18)
            bits = struct.unpack_from('<H', body, 28)[0]
            compression = struct.unpack_from('<I', body, 30)[0]
            if width != 9 or abs(height) != 8 or bits not in (24, 32) or compression != 0:
                raise ValueError('unsupported resized BMP layout')
            stride = ((width * bits + 31) // 32) * 4
            values = []
            for y in range(8):
                start = offset + (7-y if height > 0 else y) * stride
                for x in range(9):
                    blue, green, red = body[start+x*(bits//8):start+x*(bits//8)+3]
                    values.append((red*299 + green*587 + blue*114)//1000)
    value = 0
    for y in range(8):
        for x in range(8):
            value = (value << 1) | (values[y*9+x] > values[y*9+x+1])
    return '%016x' % value


def image_receipt(root, path, url, now=None):
    if not public_url(url):
        raise ValueError('image source URL required')
    root, path = Path(root), Path(path)
    body = path.read_bytes()
    if len(body) > 20_000_000:
        raise ValueError('image too large')
    phash = difference_hash(path)
    with locked(root):
        ev = archive(root, body, path.suffix.lower())
        receipt = {**ev, 'url': url, 'dhash': phash, 'algorithm': 'dHash64',
                   'observed_at': utc(now or _utc_now()), 'kind': 'researcher_deposited_image',
                   'rights_status': 'unassessed', 'public_reuse': 'unapproved',
                   'notes': 'Local deposit; no HTTP access or reuse permission inferred.'}
        _atomic_json(root / 'images' / (fingerprint(receipt) + '.json'), receipt)
    return receipt


def selected_text(body, attribute, value):
    """Text of a named DOM section, retaining original HTML as the evidence."""
    class Section(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.depth, self.capture_depth, self.chunks, self.results = 0, None, [], []
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag not in ('br','img','meta','link','input','hr','source','wbr','area','embed'):
                self.depth += 1
            matches = value in a.get('class','').split() if attribute == 'class' else a.get(attribute) == value
            if self.capture_depth is None and matches:
                self.capture_depth = self.depth
                self.chunks = []
            if self.capture_depth is not None and tag in ('br','p','div'):
                self.chunks.append('\n')
        def handle_endtag(self, tag):
            if tag in ('br','img','meta','link','input','hr','source','wbr','area','embed'):
                return
            if self.capture_depth is not None and self.depth == self.capture_depth:
                self.results.append(''.join(self.chunks).strip())
                self.capture_depth = None
            if tag not in ('br','img','meta','link','input','hr','source','wbr','area','embed'):
                self.depth = max(0,self.depth-1)
        def handle_data(self, data):
            if self.capture_depth is not None:
                self.chunks.append(data)
    parser = Section()
    parser.feed(body)
    return parser.results[0] if parser.results else None


def parse_barakat(body):
    doc = Document(body)
    description = selected_text(body,'id','artwork_description_2') or selected_text(body,'id','artwork_description')
    if description:
        description = re.sub(r'\s*Close full details\s*$', '', description).strip()
        description = '\n'.join(re.sub(r'[ \t]+',' ',line).strip() for line in description.splitlines())
        description = re.sub(r'\n{3,}','\n\n',description)
    out = {'title': next((x for x in doc.headings if BOWL.search(x)),None),
           'stock_number': selected_text(body,'class','stock_number'),
           'dimensions_text': selected_text(body,'class','dimensions'),
           'full_description': description, 'description_scope': 'complete named dealer description, normalized spacing',
           'house': 'Barakat Gallery'}
    out['image_urls'] = sorted(set(re.findall(r'data-src="(https://[^\"]+)"',body)))
    if description:
        script = re.search(r'in (Jewish Babylonian Aramaic script)',description)
        language = re.search(r'written in (Jewish Aramaic)',description)
        if script:
            out['script_stated'] = script.group(1)
        if language:
            out['language_stated'] = language.group(1)
        reference = re.search(r'References:\s*(.*?)\s*The Following',description,re.S)
        if reference:
            out['literature'] = reference.group(1).strip()
    return {key:value for key,value in out.items() if value is not None}


def collect_images(root, config, settings, fetch=_fetch, sleep=time.sleep, now=None):
    """Archive only exact reviewed image routes, with current robots for the CDN."""
    root = Path(root)
    now = utc(now or _utc_now())
    with locked(root):
        snapshot = view(root)
        latest = {x['listing_id']: x for x in snapshot['listings']}
        seen = {x['url']: x for x in snapshot['coverage'] if x.get('kind') == 'image'}
        coverage, changes = [], []
        for row in snapshot['listings']:
            hashes = list(row.get('image_hashes') or [])
            for url in row.get('image_urls') or []:
                previous = seen.get(url)
                if previous and (previous['disposition'] == 'collected' or
                    previous.get('config_sha256') == fingerprint(config) and previous['disposition'] == 'unreviewed_image_route' or
                    (datetime.fromisoformat(now.replace('Z','+00:00')) - datetime.fromisoformat(previous['observed_at'].replace('Z','+00:00'))).total_seconds() < 86400):
                    continue
                if len(coverage) >= 5:
                    continue
                p = urlsplit(url)
                route = next((r for r in config.get('image_routes',[]) if p.hostname == r['host'] and re.fullmatch(r['path_pattern'],p.path) and not p.query),None)
                c = {'url':url,'kind':'image','observed_at':now,'listing_id':row['listing_id'],
                     'config_sha256':fingerprint(config), 'disposition':'unreviewed_image_route'}
                coverage.append(c)
                if not route or not public_url(url):
                    continue
                sleep(max(settings['delay_seconds'],route['delay_seconds']))
                robot = _robots_body(url,settings['user_agent'],fetch,settings['timeout_seconds'])
                allowed, why = _robots_decision(robot,url,settings['user_agent'])
                c.update(robots_http_status=robot[0],robots=why,robots_evidence=archive(root,robot[1],'.robots'))
                if not allowed or robot[0] == 200 and len(robot[1]) >= 1_000_000:
                    c['disposition']='robots_disallowed_or_unreadable'
                    continue
                sleep(max(settings['delay_seconds'],route['delay_seconds']))
                status,body,location=fetch(url,settings['user_agent'],settings['timeout_seconds'],settings['max_response_bytes'])
                c.update(http_status=status,redirect_not_followed=location)
                if status != 200 or len(body) >= settings['max_response_bytes']:
                    c['disposition']='unavailable_or_truncated'
                    continue
                ev=archive(root,body,'.img')
                try:
                    dhash=difference_hash(ev['path'])
                except Exception as error:
                    c.update(disposition='image_decode_failed',error=str(error),**ev)
                    continue
                receipt={**ev,'url':url,'dhash':dhash,'algorithm':'dHash64','observed_at':now,
                         'kind':'image','rights_status':'unassessed','public_reuse':'unapproved',
                         'robots_evidence':c['robots_evidence']}
                _atomic_json(root/'images'/(fingerprint(receipt)+'.json'),receipt)
                c.update(disposition='collected',**ev)
                hashes.append(receipt)
            if hashes != (row.get('image_hashes') or []):
                source_ev=next(e for e in row['evidence'] if e['kind']=='email')
                item={**row,'quoted':False,'image_hashes':hashes,'disposition':row['relevance'],
                      'reason':'Source-linked images archived with current robots permission',
                      'locator':source_ev['locator']}
                source={'key':source_ev['source_key'],'message_id':source_ev.get('message_id'),'evidence':source_ev}
                changes.extend(observations([item],source,latest,now,root))
        if not coverage:
            return {'coverage':[],'replay':True,'corpus_writes':0}
        run={'schema_version':1,'observed_at':now,'messages':[],'observations':changes,'coverage':coverage,
             'errors':[],'new_listings':0,'changes':len(changes),'corpus_writes':0}
        path=commit_run(root,run)
        return {'run':str(path.resolve()),**run}


def record_gap(root, gap, now=None):
    """Save connector failures privately instead of implying zero incoming mail."""
    if gap.get('channel') != 'gmail' or not gap.get('error'):
        raise ValueError('Gmail channel and specific failure required')
    now=utc(now or _utc_now())
    run={'schema_version':1,'observed_at':now,'messages':[],'observations':[],
         'coverage':[],'errors':[{'channel':'gmail','observed_at':now,'error':gap['error'],
                                'search_complete':False,'retry_due':True}], 'corpus_writes':0}
    with locked(root):
        path=commit_run(root,run)
    return {'run':str(path.resolve()),'errors':run['errors']}
