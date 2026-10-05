# Auction intelligence extension — Step 0 proposal

DISC-004 · Codex · 2026-10-05 · Awaiting Mike's implementation approval.

Mike supplied Claude's auction-email handoff and invited revisions based on the
existing project. This is the inspected implementation proposal required by its
Step 0. It does not change code, schema, monitoring permissions or schedules.
Email source expression and message IDs remain in the ignored private tree.

## Existing system

Bowlam is Python 3.9+ with a standard-library CLI and localhost HTTP research
console, SQLite, and HTML/JavaScript readers. `ibi` resolves to
`bowl_index.cli:main`; without installation use
`PYTHONPATH=src .venv/bin/python -m bowl_index.cli`. The console runs with
`ibi serve` on localhost port 8765. Mike Access is also built by
`scripts/build_mike_access.py`. No server was started for this inspection.

The private database is `data/private/ibi.sqlite3`, with 21 applied SQL migrations.
The read-only inspection counted 2,281 object records, 2,989 source appearances
and 994 sources. Object IDs use `IBI-*`; appearances use `APP-*` and sources
`SRC-*`. Physical identity, source appearances, source-attributed claims,
offer/sale events and review decisions are already separate. These counts do
not represent independently confirmed physical bowls.

| Existing component | Role | Extension needed |
|---|---|---|
| `src/bowl_index/market.py` | Private ledger, histories, metrics and report | Richer private listing/filter/match views and daily changes |
| `src/bowl_index/market_monitor.py` | Reviewed public collection and due result checks | Policy-reviewed adapters and additional fields |
| `src/bowl_index/market_agent.py` | Hash-bound email/page evidence and append-only observations | Gmail deposit receipts, complete dispositions, versioned lot extraction |
| `scripts/run_market_agent.py` | Collect/finish commands | One local command for deposited-mail processing and reporting |
| `scripts/run_market_monitor.py` | Corpus opened read-only without migration | Retain that boundary |
| Research console and Mike Access Market | Existing private presentation | Reuse; do not build a separate website |

The corpus-derived ledger currently contains 53 recorded appearances of 46
working identities from 29 houses/dealers, with nine recorded sales lacking a
price and 24 undated appearances. This is recorded coverage, not the whole trade.

The daily local collector is configured for 06:40 New York time. The existing
active Codex heartbeat `incantation-bowl-auction-watch` runs every six hours.
Its durable instructions are in `research/monitoring/market_agent_task_prompt.md`.
The agent registry has six additional permitted pages. Current email intake
accepts local `.eml` deposits only; its prior-processing test uses content hashes.
Agent leads are keyed by URL and retain only a subset of requested fields.
The current filter is bowl-keyword based, without durable excluded-object or
literature dispositions. Corpus match pointers use URLs or house/lot numbers;
image similarity and broader evidence scoring are absent.

## Read-only mailbox sample

Mike confirms that the connected mailbox identity and the handoff address reach
the same account. The exact `IBI/Auction alerts` label was found; the handoff's
`label:ibi-auction-alerts` search returned all five messages with no next page.
All five bodies were inspected using Gmail read tools; no mailbox mutation was
performed. This inspection does not mark them successfully ingested.

The label contains two account-registration emails and a three-message Barakat
thread: a general welcome, Mike's research questions, and the dealer's reply.
The correspondence contains three unique bowl listing links, repeated in quoted
text. All three dealer-scoped stock numbers already occur in the corpus. They
are historical follow-up leads; no present offer, price or sale result is verified.
The dealer's reply promises to check information; it supplies no new findspot
evidence. The sample has no ordinary keyword-alert digest, excluded adjacent
bowl, or literature notice, so those parsers need additional fixtures.

The private sample and source parts are at
`data/private/monitoring/market-agent/inspection/auction_email_step0_2026-10-05.json`.
Administrative account payloads were omitted from that saved sample. No email
links were opened and no source claim, object link or corpus row was written.

## Recommended changes to the handoff

1. Extend the existing private monitoring ledger. A new corpus schema is not
   required for the first release: use versioned operational receipts and JSONL
   under `data/private/monitoring/`, with readers compatible with existing files.
   Any later corpus tables must use a separately reviewed migration and manifest
   intake. Scheduled collection continues to open the corpus read-only.
2. Separate email evidence, listing appearances, sale occasions and physical
   identity. Preserve multi-bowl quantities without turning them into that many
   newly identified objects. Dealers' fixed-price items belong in scope too.
3. Append observations instead of overwriting a lot. A latest-value view can
   change while earlier descriptions, provenance and outcomes stay inspectable.
   Keep email claims distinct from page claims; absence on a later page does not
   erase a prior value or establish a sale.
4. Resolve a listing key from a reliable house + sale identifier + lot number,
   with source-platform IDs/URLs as aliases. Lot number without a sale is
   insufficient. Uncertain same-lot aliases remain review candidates. Two
   platforms repeating one sale must not count as two trade occasions.
5. Filter by item, not by the email's overall keywords. Split digests into lots;
   keep whole-sale notices as unresolved sale leads until item evidence exists.
   Ignore quoted copies, signatures and Mike's modern-bowl business link as new
   offers. Registration, activation and unsubscribe links are not listing URLs.
6. Preserve coverage gaps. Receiving an alert does not permit automated access
   to its destination. Reuse fresh robots checks and reviewed terms, redirect,
   challenge, timeout, size and rate controls for lot and image hosts. Blocked
   pages retain email evidence and a review reason. Do not enable a platform
   merely because its name appears in the handoff.
7. Treat matching scores as explainable ranking signals, not calibrated identity
   probabilities. An image hash needs the actual lawfully retained image bytes;
   shared stock photos, crops and similar bowls may mislead. Show which identifier,
   measurement, inscription, provenance or image supports each suggestion.
8. Distinguish no ownership history stated, vague or undated history, and earliest
   stated history after 1970. Flag wording changes without deciding authenticity,
   lawful export or ownership. A regional statement about bowls generally is
   not an individual object's findspot or ownership history.

## First implementation scope after approval

### Email evidence and processing

Use only Gmail profile/label/search/read operations, scoped to the exact label.
Paginate all message IDs, include read and unread messages, archive raw MIME or
explicitly identified connector representations privately, and record account,
Gmail message ID, RFC Message-ID, received time, UTC retrieval time and byte hash.
Deduplicate by account + Gmail message ID; a message is completed only after its
item dispositions and extraction receipt are durable. Preserve failed attempts
and retry them. A later parser revision records a new extraction version, not a
replacement of the old one. Repeated quoted content points to its original
message and never creates an independent offer observation.

The Gmail connector is accessible to Codex turns, not automatically to a Python
LaunchAgent. Recommended first release: the scheduled Codex pass reads Gmail and
deposits evidence through a validated local adapter; the local command processes
deposits, collects permitted pages, checks due results and writes the report.
Do not store Gmail tokens or invent a direct connector endpoint in local code.
If Mike later wants Gmail collection with Codex closed, separately configure a
read-only Gmail API integration. Local `.eml` imports remain supported.

### Listing and disposition model

Retain source wording, field-level locators and evidence hashes beside normalized
values. Missing fields are null. Required fields:

| Group | Fields |
|---|---|
| Identity of offer | Stable private listing ID, aliases, house, platform, sale name/number/ID, lot number, URL, item type, source-reported quantity |
| Description | Title, full description, language and script as stated in separate fields, dimensions and units, condition, verbatim provenance, literature/publication references |
| Money | Estimate low/high/currency and exact wording, starting bid, asking price, hammer, premium-inclusive total, buyer premium wording/basis, lot versus per-object basis |
| Time and outcome | Source sale date/time and timezone where known, UTC observed time, first seen, last successfully checked, upcoming/sold/unsold/withdrawn/offered/unknown, exact result wording |
| Evidence | Source email IDs, email block/MIME locator, page capture hash and locator, matched term when actually known, image URLs and permitted local image hashes, access/reuse status |
| Review | Relevant/uncertain/adjacent-excluded/literature/unrelated/administrative disposition and reason, extraction status, descriptive flags, candidate matches and notes |

Do not manufacture the alert's matched search term from a word in the title.
Store observed keyword hits separately if the alert never identifies its query.
Do not infer sold from an ended date, disappearance or an inaccessible result.
Literature and related amulets retain their own type and cannot inflate bowl-lot
counts. Modern reproductions presented as ancient or disputed items remain
uncertain candidates; explicitly modern decorative reproductions are audited
exclusions. Keep an inspectable record of every item disposition.

### Matching and view

Reuse the corpus identifier index for exact institution/collection stock numbers
and publication pointers, with scope and rationale. Queue fuzzy measurement,
description, provenance and image candidates separately. No uncertain identity
merge or corpus link is written. Add private filters for sale date, house,
platform, relevance, missing results and provenance flags; show original/current
wording and evidence in the existing Market view. Source descriptions and images
stay private to Mike. Add results checks only for reviewed permitted adapters.

### Commands, schedules and daily packet

Provide one on-demand local command for deposited email processing and reporting,
with a shared lock, kill switch, bounded retries and durable partial-failure
receipts. Retain the existing 06:40 collector. Extend the existing six-hour Codex
pass for read-only Gmail collection; do not install another independent ingestion
loop. Add a morning digest in this chat at 07:00 America/New_York, based on saved
observations and a durable digest cursor, so six-hour alerts are not repeatedly
announced as new. The morning digest explicitly says when nothing changed,
while reporting failures or incomplete coverage separately.

Write dated private JSON and Markdown reports with new relevant listings, changed
outcomes/prices, pending reappearance/corpus candidates, provenance flags, review
items, excluded counts by reason, and fetch/parse errors. Distinguish historical
baseline from newly observed offers and first-seen from auction dates. Reports
must state the monitored interval and coverage limits rather than claim every
bowl on the worldwide market has been captured.

Local scheduled Codex work requires the computer and desktop app to be running;
see [official scheduling documentation](https://learn.chatgpt.com/docs/automations).
Update the existing runtime authorization in `docs/project-rules.md` §6 and the
saved task prompt only after approval and successful testing. No new accounts,
messages, bids or subscriptions are included.

## Validation and rollout

Replay the five current emails into an isolated private operational directory,
then verify zero new verified auction offers, three historical Barakat pointers,
two administrative dispositions, one general welcome, and no duplicate lots
from quoted replies. Verify mailbox labels/read state remain unchanged and corpus
fingerprint remains identical. Test ordinary multi-lot alerts, uncertain items,
adjacent exclusions, literature, missing URLs, result updates, stale evidence,
pagination, fetch restrictions, failed-extraction retries and repeated runs using
synthetic fixtures until real alert examples arrive. Show the private sample
before enabling revised scheduled behavior. Preserve existing receipts/readers.

The historical platform back-catalog remains a later phase: plan reviewed
platform adapters, capture permissions, completeness/pagination accounting and
the same listing/observation/matching model, but do not import it now.

## Decision requested

Approve extending the existing Market module with this private operational model,
read-only Gmail intake, evidence-preserving review queues and a 07:00 morning
digest. The corpus schema stays unchanged for this first release. This approval
checkpoint comes from Step 0 of Mike's supplied handoff: “Wait for my OK before
changing the schema or existing code.”
