# Market tracker

Private to Mike (DISC-004). Two parts: a ledger of what the corpus already
records about bowls on the market, and a lead-only monitor for new listings.
Neither writes to the corpus.

## Ledger

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli report-market
```

Writes `data/private/reports/market_ledger.md` and `.json` (ignored by Git).
`scripts/build_mike_access.py` also renders it as `market.html` in Mike Access.

- One row per recorded offer or sale event, plus any auction- or dealer-record
  appearance that reports neither. A source's estimate, result, provenance and
  export claims attach to every event it reports for that record.
- Prices keep the source's wording and currency. Nothing is converted or reconciled.
- Status comes from the recorded event type and price wording: upcoming, sold
  (price recorded), recorded as sold without a price, unsold, offered, or bare listing.
- "On the market more than once" needs two different dates or two different
  reported houses. An aggregator page repeating one sale does not count.
- A recorded sale says what a source reports. It does not establish lawful
  ownership, export history or authenticity (`project-rules.md` §4).

## Monitor

```sh
PYTHONPATH=src .venv/bin/python scripts/run_market_monitor.py
```

- Reads only the search pages in `config/market_monitors.json`, re-checks
  robots.txt each run, and fails closed if robots.txt is unreadable.
- Writes run receipts, raw pages by hash, `state.json` and
  `leads/<timestamp>.jsonl` under `data/private/monitoring/market/`.
  `touch data/private/monitoring/market/DISABLED` stops it.
- A lot becomes a lead once, and only if its own title or teaser names
  incantation, devil/demon-trap, Aramaic, Mandaic, Syriac or magic bowls.
- **Results.** Each lead's lot page is read once to learn its exact sale time,
  then again 6 hours and 1, 3, 7 and 14 days after it. The first page showing the
  lot as ended records `sold` (with the hammer price as shown, which excludes the
  buyer's premium), `passed` or `ended`. Lots still not ended after the last
  check are recorded as `not_shown`. Redirects are followed by hand and only where
  robots.txt allows; the-saleroom excludes `*/archivelot*`, so a lot moved there is
  recorded as `unavailable`, never read. Final results go to `results/<timestamp>.jsonl`.
  The closed-lot format was read from the page template; no real closed lot had
  been observed when this was written, so check the first `sold` record against
  the lot page.
- robots.txt is matched with `bowl_index.robots`, which honours `*` and `$`
  wildcards. Python's `urllib.robotparser` does not.
- `possible_match` points at a recorded listing with the same URL, or the same
  house and lot number. It is a pointer for review, never a merge.
- The registry lists every platform that was checked and excluded, with the
  reason. Only the-saleroom is enabled as of 2026-10-04; most other platforms
  disallow search in robots.txt or render results client-side.

### Schedule

Daily at 06:40 local time (America/New_York) by the LaunchAgent template
`config/launchd/org.incantation-bowl-index.market-monitor.plist`, installed in
`~/Library/LaunchAgents/` on 2026-10-04 at Mike's request. It does not run at
login, needs no Claude session, and logs to `launchd.log` / `launchd-error.log`
in the monitor directory. A pass is six search pages plus any due lot pages,
ten seconds apart.

```sh
launchctl print gui/$(id -u)/org.incantation-bowl-index.market-monitor
launchctl kickstart gui/$(id -u)/org.incantation-bowl-index.market-monitor   # run now
launchctl bootout gui/$(id -u)/org.incantation-bowl-index.market-monitor     # stop
```

To pause without unloading: `touch data/private/monitoring/market/DISABLED`.

The monitor only collects. Review of its leads and results stays with Mike, or
with Claude when Mike asks.

## Turning a lead or result into a record

Review the lot page by hand. If it belongs in the corpus, write a candidate
manifest under `research/seeds/` (`source_type: auction_record`, an `offer`
or `sale` event, `sale_estimate` / `sale_result` claims in the source's wording)
and apply it with `ibi ingest`. A monitor result becomes a `sale_result` claim only
through such a manifest, citing the lot page and the result's raw-page hash. Link
it to an existing bowl only through the identity review workflow
(`docs/research_protocol.md`). The next ledger build picks it up.
