"""Read-only ledger of the incantation-bowl market, for Mike Access only.

A listing is one source's report of one candidate record on the market: an
auction lot, a dealer's stock page, or a publication describing a sale. The
ledger groups listings by physical identity so repeat appearances of one bowl
read as a trade history. It never writes to the corpus.

Prices stay exactly as the source worded them. Currencies are not converted
and estimates are not reconciled. A recorded sale or offer says what a source
reports; it does not legitimize ownership, export history or authenticity.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .identity import identity_rows
from .market_monitor import monitor_leads


MARKET_SOURCE_TYPES = ("auction_record", "dealer_record")
MARKET_EVENT_TYPES = ("offer", "sale")
# Custody events give a market appearance its before and after.
HISTORY_EVENT_TYPES = ("ownership", "acquisition", "offer", "sale", "transfer", "loss")
MARKET_CLAIM_FIELDS = ("provenance", "export_status")
PRICE_FIELDS = ("sale_result", "sale_price")

STATUS_LABELS = {
    "upcoming": "Upcoming",
    "sold": "Sold, price recorded",
    "sold_no_price": "Recorded as sold, no price",
    "unsold": "Unsold",
    "offered": "Offered",
    "listing_only": "Listing, no offer or sale recorded",
}


def _is_market_claim(field):
    return field.startswith("sale_") or field in MARKET_CLAIM_FIELDS


def _status(event_type, claims, date, today):
    if event_type != "sale" and date and date >= today:
        return "upcoming"
    results = [c["value"] for c in claims if c["field"] in PRICE_FIELDS]
    if any(value.strip().casefold() == "unsold" for value in results):
        return "unsold"
    if event_type == "sale":
        return "sold" if results else "sold_no_price"
    if event_type == "offer":
        return "offered"
    return "listing_only"


def _identity_index(conn):
    index = {}
    for row in identity_rows(conn):
        identity = {
            "identity_id": row["identity_id"],
            "display_name": row["display_name"],
            "record_status": row["record_status"],
            "authenticity": row["authenticity"],
        }
        for object_id in json.loads(row["member_ids_json"]):
            index[object_id] = identity
    return index


def market_listings(conn, today=None, identities=None):
    """One row per offer or sale event, plus market-source appearances with neither.

    A source's market claims (estimate, result, provenance) attach to every event
    it reports for that record; the claim wording says which occasion it means.
    """
    today = today or datetime.now(timezone.utc).date().isoformat()
    sources = {row["id"]: dict(row) for row in conn.execute(
        "SELECT id,source_type,title,authors,publisher,issued_year,url,citation,access_status "
        "FROM sources")}
    events = defaultdict(list)
    for row in conn.execute(
        "SELECT id,object_id,source_id,event_type,start_date,end_date,place,actor,details,"
        "certainty,locator FROM events WHERE event_type IN (%s) ORDER BY id" %
        ",".join("?" * len(MARKET_EVENT_TYPES)), MARKET_EVENT_TYPES
    ):
        events[(row["object_id"], row["source_id"])].append(dict(row))
    appearances = defaultdict(list)
    for row in conn.execute(
        "SELECT l.object_id,a.id,a.source_id,a.locator,a.url,a.observed_at "
        "FROM appearance_object_links l JOIN appearances a ON a.id=l.appearance_id "
        "WHERE l.relation_type<>'rejected' ORDER BY a.id"
    ):
        appearances[(row["object_id"], row["source_id"])].append(dict(row))
    claims = defaultdict(list)
    for row in conn.execute(
        "SELECT object_id,source_id,field,value_text,value_json,certainty,locator "
        "FROM claims ORDER BY id"
    ):
        if _is_market_claim(row["field"]):
            claims[(row["object_id"], row["source_id"])].append({
                "field": row["field"],
                "value": row["value_text"] if row["value_text"] is not None else row["value_json"],
                "certainty": row["certainty"],
                "locator": row["locator"],
            })

    keys = set(events)
    keys.update(key for key in appearances
                if sources[key[1]]["source_type"] in MARKET_SOURCE_TYPES)
    identities = _identity_index(conn) if identities is None else identities
    blank = {"identity_id": None, "display_name": None,
             "record_status": None, "authenticity": None}
    rows = []
    for object_id, source_id in sorted(keys):
        source = sources[source_id]
        listing_claims = claims.get((object_id, source_id), [])
        seen = appearances.get((object_id, source_id), [])
        common = {
            "object_id": object_id,
            **identities.get(object_id, blank),
            "source_id": source_id,
            "source_type": source["source_type"],
            "source_title": source["title"],
            "citation": source["citation"],
            "url": next((a["url"] for a in seen if a["url"]), None) or source["url"],
            "access_status": source["access_status"],
            "observed_at": max((a["observed_at"] for a in seen if a["observed_at"]), default=None),
            "claims": listing_claims,
        }
        # A market source that reports no offer or sale is still a listing.
        for event in events.get((object_id, source_id)) or [None]:
            kind = event["event_type"] if event else None
            date = event["start_date"] if event else None
            status = _status(kind, listing_claims, date, today)
            rows.append({
                **common,
                "event_id": event["id"] if event else None,
                "event_type": kind,
                "house": (event and event["actor"]) or source["publisher"] or source["authors"],
                "house_reported": bool(event and event["actor"]),
                "place": event["place"] if event else None,
                "date": date,
                "locator": event["locator"] if event else "; ".join(a["locator"] for a in seen),
                "details": event["details"] if event else None,
                "status": status,
                "status_label": STATUS_LABELS[status],
            })
    rows.sort(key=lambda r: (r["date"] or r["observed_at"] or "", r["house"] or "",
                             r["object_id"], r["event_id"] or ""), reverse=True)
    return rows


def _occasions(rows):
    """Distinct market occasions: different dates, or different reported houses.

    Aggregator pages (Barnebys, Invaluable) repeat one sale, so a second source
    alone is not a second occasion, and only an event's own actor counts as a house.
    """
    events = [r for r in rows if r["event_type"]]
    dates = {r["date"] for r in events if r["date"]}
    houses = {r["house"].casefold() for r in events if r["house_reported"]}
    return max(len(dates), len(houses))


def identity_histories(conn, listings, identities=None):
    """Every custody event for identities seen on the market on more than one occasion."""
    by_identity = defaultdict(list)
    for row in listings:
        if row["identity_id"]:
            by_identity[row["identity_id"]].append(row)
    repeat = {key: rows for key, rows in by_identity.items() if _occasions(rows) > 1}
    if not repeat:
        return []
    identities = _identity_index(conn) if identities is None else identities
    object_to_identity = {
        object_id: identity["identity_id"] for object_id, identity in identities.items()
        if identity["identity_id"] in repeat}
    timeline = defaultdict(list)
    for row in conn.execute(
        "SELECT e.object_id,e.event_type,e.start_date,e.place,e.actor,e.details,e.locator,"
        "s.citation FROM events e JOIN sources s ON s.id=e.source_id WHERE e.event_type IN (%s)"
        % ",".join("?" * len(HISTORY_EVENT_TYPES)), HISTORY_EVENT_TYPES
    ):
        key = object_to_identity.get(row["object_id"])
        if key:
            timeline[key].append(dict(row))
    histories = []
    for key, rows in repeat.items():
        events = sorted(timeline[key], key=lambda e: (e["start_date"] or "9999", e["event_type"]))
        histories.append({
            "identity_id": key,
            "display_name": rows[0]["display_name"],
            "authenticity": rows[0]["authenticity"],
            "occasions": _occasions(rows),
            "source_count": len({r["source_id"] for r in rows}),
            "events": events,
        })
    histories.sort(key=lambda h: (-h["occasions"], h["identity_id"]))
    return histories


def market_gaps(conn, listings):
    unlinked = [dict(row) for row in conn.execute(
        "SELECT a.id,a.locator,a.url,s.title,s.source_type FROM appearances a "
        "JOIN sources s ON s.id=a.source_id WHERE s.source_type IN (%s) AND NOT EXISTS ("
        "SELECT 1 FROM appearance_object_links l WHERE l.appearance_id=a.id "
        "AND l.relation_type<>'rejected') ORDER BY a.id" % ",".join("?" * len(MARKET_SOURCE_TYPES)),
        MARKET_SOURCE_TYPES)]
    leads = [dict(row) for row in conn.execute(
        "SELECT id,description,url,status,priority FROM leads WHERE lead_type='auction' "
        "AND status IN ('open','in_progress','blocked') ORDER BY priority DESC,id")]
    return {
        "undated": [r for r in listings if not r["date"]],
        "sold_without_price": [r for r in listings if r["status"] == "sold_no_price"],
        "offered_without_outcome": [r for r in listings if r["status"] == "offered"],
        "unlinked_market_appearances": unlinked,
        "open_auction_leads": leads,
    }


def market_metrics(listings, histories, gaps):
    by_status = defaultdict(int)
    for row in listings:
        by_status[row["status"]] += 1
    return {
        "listings": len(listings),
        "identities": len({r["identity_id"] or r["object_id"] for r in listings}),
        "houses": len({(r["house"] or "").casefold() for r in listings if r["house"]}),
        "identities_on_market_more_than_once": len(histories),
        "by_status": dict(sorted(by_status.items())),
        "undated": len(gaps["undated"]),
        "sold_without_price": len(gaps["sold_without_price"]),
        "unlinked_market_appearances": len(gaps["unlinked_market_appearances"]),
        "open_auction_leads": len(gaps["open_auction_leads"]),
    }


def market_ledger(conn, today=None, monitor_dir=None):
    """The whole ledger. ``monitor_dir`` adds unreviewed leads from the listing monitor."""
    identities = _identity_index(conn)
    listings = market_listings(conn, today, identities)
    histories = identity_histories(conn, listings, identities)
    gaps = market_gaps(conn, listings)
    return {
        "schema_version": 1,
        "audience": "Mike alone",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metrics": market_metrics(listings, histories, gaps),
        "listings": listings,
        "repeat_identities": histories,
        "gaps": gaps,
        "monitor_leads": monitor_leads(monitor_dir) if monitor_dir else [],
    }


def _cell(value):
    return (value or "—").replace("|", "\\|").replace("\n", " ")


def _price(row):
    wanted = [c for c in row["claims"] if c["field"].startswith("sale_")]
    return "; ".join(c["value"] for c in wanted) or "—"


def write_market_report(conn, destination, today=None, monitor_dir=None):
    """Write the private Markdown ledger and its JSON twin beside it."""
    ledger = market_ledger(conn, today, monitor_dir)
    m = ledger["metrics"]
    L = [
        "# Market ledger",
        "",
        "> Private to Mike. Generated by `ibi report-market`. Every row is what one source",
        "> reports; prices keep the source's wording and currency. A sale record does not",
        "> establish lawful ownership, export history or authenticity.",
        "",
        "Generated: `%s`" % ledger["generated_at"],
        "",
        "| Measure | Current |",
        "|---|---:|",
        "| Listings (one per offer, sale or bare listing) | %d |" % m["listings"],
        "| Physical identities | %d |" % m["identities"],
        "| Houses and dealers | %d |" % m["houses"],
        "| Bowls on the market on more than one occasion | %d |" % m["identities_on_market_more_than_once"],
    ]
    for status, label in STATUS_LABELS.items():
        L.append("| %s | %d |" % (label, m["by_status"].get(status, 0)))
    L += [
        "| Listings without a date | %d |" % m["undated"],
        "| Market appearances linked to no record | %d |" % m["unlinked_market_appearances"],
        "| Open auction leads | %d |" % m["open_auction_leads"],
        "",
        "## Listings, newest first",
        "",
        "| Date | House | Bowl | Status | Price wording | Locator |",
        "|---|---|---|---|---|---|",
    ]
    for r in ledger["listings"]:
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            _cell(r["date"] or ("seen " + r["observed_at"][:10] if r["observed_at"] else None)),
            _cell(r["house"]), _cell((r["identity_id"] or r["object_id"]) + " " +
                                     (r["display_name"] or "")),
            r["status_label"], _cell(_price(r)), _cell(r["locator"])))
    L += ["", "## Bowls on the market more than once", ""]
    if not ledger["repeat_identities"]:
        L.append("None yet.")
    for h in ledger["repeat_identities"]:
        L += ["### %s — %s" % (h["identity_id"], h["display_name"] or "unnamed"), ""]
        for e in h["events"]:
            L.append("- %s · %s · %s — %s" % (
                e["start_date"] or "undated", e["event_type"], e["actor"] or e["place"] or "—",
                _cell(e["details"])))
        L.append("")
    L += ["## New listings from the monitor, awaiting review", ""]
    if not ledger["monitor_leads"]:
        L.append("None.")
    for lead in ledger["monitor_leads"]:
        match = lead.get("possible_match")
        result = lead.get("result") or {}
        outcome = ""
        if result.get("outcome"):
            outcome = " · " + result["outcome"].replace("_", " ")
            if result["outcome"] == "sold" and result.get("hammer_text"):
                outcome += " (hammer %s, before premium)" % result["hammer_text"]
        L.append("- %s · %s · estimate %s%s · seen %s%s — %s" % (
            lead["description"], result.get("sale_at_text") or lead.get("sale_date_text")
            or "date not shown", lead.get("estimate") or "not shown", outcome,
            lead["observed_at"][:10],
            " · possibly %s (%s)" % (match["identity_id"] or match["object_id"], match["basis"])
            if match else "", lead["url"]))
    L.append("")
    gaps = ledger["gaps"]
    L += [
        "## Gaps to chase",
        "",
        "Recorded as sold, no price: %s" % (", ".join(
            "%s (%s)" % (r["identity_id"] or r["object_id"], r["house"] or "—")
            for r in gaps["sold_without_price"]) or "none"),
        "",
        "Market appearances linked to no record: %s" % (", ".join(
            "%s %s" % (a["title"], a["locator"]) for a in gaps["unlinked_market_appearances"])
            or "none"),
        "",
        "Open auction leads: %s" % (", ".join(
            "%s (%s)" % (l["id"], l["status"]) for l in gaps["open_auction_leads"]) or "none"),
        "",
    ]
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(L) + "\n", encoding="utf-8")
    twin = destination.with_suffix(".json")
    twin.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"destination": str(destination), "json": str(twin), **m}
