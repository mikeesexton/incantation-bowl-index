# Private auction agent routine

DISC-004. Mike authorized recurring collection on 2026-10-04. A Codex heartbeat
returns to the same chat every six hours. The existing daily 06:40 New York
LaunchAgent remains installed; the agent also runs its collector when available.
The market collector's lock prevents concurrent runs. On 2026-10-05 Mike approved
the Gmail extension and a separate 07:00 New York morning digest in its
implementation chat. The six-hour watch retains its existing chat and cadence.

The agent collects and reviews evidence, preserves changes and alerts Mike about
new leads, changed prices/outcomes/provenance wording and changed coverage gaps.
No unattended corpus intake or identity decision. Runtime passes are governed by
§6 of [project-rules.md](project-rules.md); implementation changes follow normal
session closure. Keep the computer on and Codex running for local scheduled
work ([official documentation](https://learn.chatgpt.com/docs/automations?surface=app)).

## Enabled coverage

- **the-saleroom**: six keyword searches; exact sale-time and widening outcome
  checks through the existing collector. New observations retain changed titles,
  descriptions, estimates and dates beside their previous wording and raw hashes.
- **Lot-tissimo**: German-locale first search page for “incantation bowl”.
- **Artemission**: New Additions and Near East first pages.
- **Christoph Bacher**, **Hixenbaugh**, **Ostracon**: reviewed Near Eastern first
  pages. Bacher pagination and Ostracon's image-only links limit coverage.
- **Alert emails**: read-only connected Gmail, exact `IBI/Auction alerts` label,
  canonical mailbox `mike92x@gmail.com` (Mike confirmed the handoff address is an
  alias). Paginated scans include labeled sent correspondence and read/unread
  mail. Raw MIME and message-ID receipts stay private; mailbox state is unchanged.
  Local `.eml` deposits remain supported. Reading a label does not verify that
  every desired alert subscription is configured.
- **Email-linked lot pages/images**: narrowly reviewed Barakat artwork/CDN routes
  and the-saleroom current lot routes in `config/market_email_intake.json`.
  Other destinations retain email evidence and explicit `unreviewed_route` gaps.

These are monitored pages, not complete inventories of those firms. Fresh
robots.txt is checked each pass. Redirects are recorded without following;
challenges, failures and incomplete pages remain explicit gaps. Every extra
page and the reason it was selected are in
[the registry](../config/market_agent_sources.json) and
[Claude's policy recon](../research/monitoring/market_platform_recon_2026-10-04.json).
Do not extend unattended coverage without reviewing the new endpoint and policy.

LiveAuctioneers, Invaluable, Bidsquare, Barnebys, Sotheby's and Drouot have recorded
automation prohibitions. Other sites in the recon have access challenges or
unverified endpoints. Browser automation is still automation. Use sanctioned
alerts or Mike's own manual deposits for these gaps. Do not use an agent to
circumvent their restrictions. Mike is setting up alerts separately; authentication,
new accounts, verification and any explicit restrictions stay with him.

## Running and stopping

The exact agent instructions are in
[market_agent_task_prompt.md](../research/monitoring/market_agent_task_prompt.md).

```sh
PYTHONPATH=src .venv/bin/python scripts/run_market_monitor.py
PYTHONPATH=src .venv/bin/python scripts/run_market_agent.py collect
# Read the returned evidence, create a private candidate JSON array, then:
PYTHONPATH=src .venv/bin/python scripts/run_market_agent.py finish --collection PATH --input PATH
```

`finish` validates the entire submission and evidence bytes before appending.
Replaying a completed identical submission changes nothing; a changed replay is
rejected. The combined private Market view calculates possible corpus matches
by the existing listing index, as review pointers only.

Pause the agent with `data/private/monitoring/market-agent/DISABLED` or pause its
Codex schedule. The scripted monitor has a separate `market/DISABLED` switch;
either switch also stops new email intake. `market-agent/intake/DISABLED` stops
only intake. Do not remove another run's lock without investigating.

The morning digest follows
[market_morning_digest_prompt.md](../research/monitoring/market_morning_digest_prompt.md).
It scans Gmail, consumes pending deposits, then reports an exact saved packet
and acknowledges only that packet. The six-hour pass never advances the daily
cursor. Both schedules need this Mac and the desktop app running; the installed
LaunchAgent can process existing deposits without an agent session.

## Private artifacts

All captures and extracted source expression stay in ignored `data/private/`:

- `market/raw/`, `leads/`, `observations/`, `results/`, `runs/`: scripted evidence.
- `market-agent/evidence/<sha256>.html|.robots|.eml`: immutable evidence bytes.
- `market-agent/collections/<UTC stamp>.json`: page/access/robots/email inventory.
- `market-agent/drafts/`: agent extraction proposals.
- `market-agent/leads/`: original new listing records, never rewritten.
- `market-agent/observations/`: previous/current listing values and evidence.
- `market-agent/runs/`: finalized extraction and newly consumed scripted records,
  including zero-lead runs and explicit `corpus_writes: 0`.
- `market-agent/intake/`: immutable raw MIME, archived lot pages/images, deposits,
  versioned message/item dispositions, field observations, byte-bound perceptual
  hashes, daily JSON/Markdown packets and exact-packet delivery receipts.

Candidates require a listing URL, title, exact evidence locator and collection
hash. A listing URL is a lead key, never an object identity. Equal house/lot
numbers across sales are not deduplicated. Missing fields remain null. Dates,
quantity, dealer provenance claims and price bases preserve source wording.

The first packet contains existing backlog, labelled as a baseline. Later runs
report changes only. Alerts about unchanged gaps are suppressed; new failures
still require attention. Source changes are observations, not corrections to
older claims. A disappeared item is not a sale result.

## Quantitative use

Count listing appearances separately from reviewed physical identities, trade
occasions and source-reported bowl quantities. Keep estimates, asking prices,
hammer prices and premium-inclusive totals separate, in their original currencies.
Report monitoring intervals, missed checks, first-page limits and platform gaps.
Do not use corpus size as the denominator of all bowls in circulation or treat
listing abundance/low prices as proof of looting, authenticity or historical
unprecedentedness. These records support testing those hypotheses.

Turning a lead into corpus evidence remains the manifest/ingest and review path
in [market_tracker.md](market_tracker.md). Private captures grant no public reuse
permission.
