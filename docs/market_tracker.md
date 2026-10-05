# Market tracker

Private to Mike (DISC-004). Two parts: a ledger of what the corpus already
records about bowls on the market, and a lead-only monitor for new listings.
Neither writes to the corpus.

## Email intelligence (2026-10-05)

The approved extension uses an append-only private operational ledger rather
than changing the scholarly corpus schema. Scheduled Codex passes read the exact
Gmail `IBI/Auction alerts` label and deposit raw MIME; the local processor has no
Gmail credentials. Mike confirmed both account names in the handoff identify
the same connected mailbox. Every message has a hash-bound ID receipt and dated
item dispositions. Whole-message extraction failures remain retryable; exact
replays add neither listings nor revisions. Revised extractions preserve originals.

Run pending deposits and produce a report on demand:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_market_intake.py run --enrich
PYTHONPATH=src .venv/bin/python scripts/run_market_intake.py report
```

The installed 06:40 New York LaunchAgent also runs this processing. The six-hour
watch reads fresh Gmail; the separate 07:00 morning digest checks Gmail again and
reports in the implementation chat. Schedules require this Mac and Codex running.
Reports live under `data/private/monitoring/market-agent/intake/reports/` as
immutable dated JSON/Markdown, with a reconstructable `latest.json` pointer.
The daily cursor advances only after the exact saved packet was reported,
using `scripts/run_market_intake.py ack --packet PATH`; the six-hour watch never
acknowledges it. Concurrent collectors use locks; either existing market runtime
kill switch or the intake's own `DISABLED` stops new intake.

`config/market_email_intake.json` records the full desired alert roster and
search terms, not a claim that subscriptions or full platform coverage exist.
Email-linked pages currently enabled: Barakat artwork pages and image CDN, and
the-saleroom current lot pages. Other URLs remain email-only review items with
explicit coverage gaps. Fresh robots checks, rate limits, bounded page/image
counts, and refusal of redirects/challenges apply. Protected descriptions and
local image bytes remain Mike-only; capture confers no public reuse permission.

Routine source comparisons and any specific questions for Mike now live in the
scheduled morning chat, following [market_chat_checks.md](market_chat_checks.md).
Version-bound private source-check receipts describe the actual comparison;
changed wording/evidence opens a new check. Source comparison does not decide
physical identity, authenticity or rights. The Market page is the evidence viewer.

The private console and generated Mike Access Market page show filters for
house, platform, relevance, complete sale dates, provenance flags and missing
results, plus disclosures for field history, archived evidence and item audit.
All controls are labeled dropdown/date filters, with an explicit explanation
that filtering never marks anything checked or approved. Repeated evidence is
compacted in display only; full underlying observations remain.
Administrative notices, literature, related amulets, excluded adjacent objects,
uncertain items and sale announcements have distinct dispositions. A digest's
quoted replies are source references, not new offers. Historical correspondence
is labeled, and reference counts are separate from unique excluded items.

Fields retain source wording and nulls: house/platform; sale name/number/ID;
lot/stock number; date/time/timezone; URL/title/full description and its scope;
stated language/script; dimensions/condition; estimate with parsed low/high only
where currency and number convention are explicit; starting/asking/hammer prices;
premium-inclusive total and premium; result wording; verbatim provenance;
literature; source image URLs and local image/hash receipts; quantity/price basis;
matched terms; source email IDs; first-seen time; status/relevance/notes.
No complete date, language, unit or price is invented from a partial statement.

Same-lot keys use house + sale ID/number/name + lot number when available,
otherwise canonical URL. Changes append previous/current observations; absent
later fields never blank earlier evidence. Outcome needs explicit source wording;
a disappearance remains unknown. Field evidence retains hashes and exact locators.
Agent refinements use a private JSON mapping deposited message keys to complete
item lists with `disposition`, `reason`, `locator` and these fields, through
`scripts/run_market_intake.py review --input PATH`. Any `extra_evidence` must
resolve to unchanged bytes in this intake archive. Whole submissions validate
before a single immutable commit. Image dHashes require registered byte receipts.

Match suggestions use scoped corpus identifiers, source URLs and reported
publication pointers. Across operational listings, dimensions, description,
provenance and perceptual image distance produce explained ranking scores for
Mike's review. Scores are heuristic, not probabilities; stock photos and shared
dealer wording can resemble each other. No suggestions write identity links.
Corpus suggestions also compare long distinctive catalogue descriptions and
exact archived image bytes; explicitly typed corpus dHash64 values are comparable
when present. No corpus-wide perceptual index is created by this extension (the
current corpus has no such values); operational images have byte-bound hashes.
Descriptive provenance flags
record absent inspected wording, undated vague collections, dates only after
1970, country mentions within provenance and changed provenance wording. They
are review prompts, never accusations or determinations of origin or legality.

The one-time past-results back-catalog remains unimplemented. A later approved
pass can use the same listing keys, immutable observations, evidence locators
and review queues, with its historical coverage recorded separately.

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
- Listing changes retain previous/current source wording and raw-page hashes in
  `observations/<timestamp>.jsonl`; the original lead is preserved.
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

Platforms the monitor cannot read (robots.txt, terms, bot challenges or
client-side rendering) are covered by the recon and proposed alert-email
workflow in [`market_agent_pass.md`](market_agent_pass.md). The Codex agent pass runs
every six hours over additional permitted pages and deposited alert emails.
Gmail alerts are not connected yet. Its evidence-bound leads are included in
the private Market view; runtime passes never ingest them into the corpus.

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

## Result reconciliation (2026-10-05)

The main table now combines recorded offers with separately source-compared
monitor results for the exact auction occasion. This fixes Apollo 4 October 2026
lot1419: sold, 300 GBP hammer for all three bowls, excluding buyer's premium.
The three component records retain their original offers; no individual price
is invented. A private fingerprint-bound result-link manifest joins the reported
outcome to display, filters, counts and gap lists without corpus edits or physical
identity decisions. Unlinked results and stale links appear in the daily packet
for the agent to compare; see [market_chat_checks.md](market_chat_checks.md).
Other historical offers explicitly say their outcome is unknown.
