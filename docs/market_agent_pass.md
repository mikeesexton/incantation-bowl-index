# Market: covering the platforms the monitor cannot read

Private to Mike (DISC-004). This is recon and a proposed design, prepared on
2026-10-04 so the work can start when Mike asks. **Nothing here is enabled.**
The scripted monitor is described in [`market_tracker.md`](market_tracker.md).

Evidence:

- [`research/monitoring/market_platform_recon_2026-10-04.json`](../research/monitoring/market_platform_recon_2026-10-04.json)
  holds per-site robots.txt rules, terms on automated access, alert features,
  static-HTML checks and every URL fetched. Raw responses are in
  `data/private/monitoring/market/recon-2026-10-04/`.
- [`research/monitoring/codex_scheduled_tasks_recon_2026-10-04.md`](../research/monitoring/codex_scheduled_tasks_recon_2026-10-04.md)
  summarises what OpenAI's documentation says Codex can do unattended. Each
  claim is labelled as documented, silent or inferred.
- [`research/monitoring/market_agent_task_prompt.md`](../research/monitoring/market_agent_task_prompt.md)
  is the draft brief for the Codex task.

## The finding that shapes everything

A Codex agent driving a browser on a weekly schedule is still automated
access. Most of the platforms the monitor skips do not block it only by
accident.

- **LiveAuctioneers, Invaluable, Bidsquare, Barnebys, Sotheby's and Drouot**
  forbid robots, scrapers or systematic extraction in their terms, whatever
  their robots.txt allows. LiveAuctioneers, Invaluable and Bidsquare also
  disallow search in robots.txt.
- **Kedem, TimeLine's own site, Freeman's (formerly Hindman), Catawiki,
  Heritage, Gazette Drouot, Trocadero and the Artemis auction subdomain**
  put up bot challenges (Cloudflare, DataDome, Vercel, Akamai, proof of work).
  Getting an agent past one is bypassing an access control
  (`project-rules.md` §3).

An agent that runs keyword searches on those sites would break their terms
and the project's own robots policy, which the scripted monitor and
`ibi capture` both enforce. **Recommendation: don't build that.** Most of
these platforms offer free saved-search email alerts, which are the
sanctioned way to be told about new lots. Use the alerts instead, and give the
agent the part that is genuinely hard to script: reading those emails.

## Proposed design: three tiers

### Tier 1 — extend the existing script (no agent, no credits)

These allow it in robots.txt, have no anti-automation clause in their terms,
and serve lot titles in plain HTML:

| Site | Page | Note |
|---|---|---|
| Lot-tissimo | `/de-de/search-results?searchTerm={term}` | Same Auction Technology Group platform as the-saleroom; the existing parser may need only small changes. Avoid `/en-gb`, which is disallowed. |
| Artemission | `/NewAdditions.aspx`, `/ViewItems.aspx?CategoryID=1` | A new-additions page, ideal for a weekly diff. No robots.txt. |
| Christoph Bacher | `/en/category/alterorient/` | WooCommerce, 51 items, sortable by latest. |
| Hixenbaugh | `/product-category/near-eastern-art/` | Small inventory. |
| Ostracon | `/homeCatalogueNearEastern.html` | Items appear as image links only, so detect new item URLs rather than titles. No robots.txt. |
| Barakat | `barakatgallery.eu/artworks/categories/165-near-eastern/`, `/167-biblical/` | Category page not yet opened; confirm before adding. |
| Bonhams | `/department/ANT/antiquities/` | Permissive, but the page shows mostly past highlights; marginal. |

The-saleroom, which is already monitored, also carries TimeLine, Apollo,
Gorny & Mosch, Auktionshaus Stahl, some Setdart sales and Pax Romana's
historic sales.

### Tier 2 — saved-search alerts, parsed by a Codex task (the agent's job)

Mike creates the accounts and alerts. Agents may not create accounts or
enter passwords. Use the monitor's six search terms: incantation bowl, devil
trap bowl, demon trap bowl, syriac bowl, aramaic bowl and mandaic bowl.
Point every alert at one dedicated mailbox or label.

| Platform | Alert feature | Also covers | Status |
|---|---|---|---|
| Invaluable | "Follow this Keyword", plus saved searches | Kedem, Freeman's, Artemis, Artemission, Fernando Durán | Confirmed on a help page |
| LiveAuctioneers | Followed searches | Apollo, Artemis, Artemission, Hixenbaugh, Freeman's, Jasper52/Chairish | Inferred; help centre returned 403 |
| Catawiki | Unknown; check while signing up | 5 of the 53 recorded listings | Every page returned 403 |
| Bidspirit | Unknown | Kedem, Deutsch / Archaeological Center | JS-only app |
| Barnebys | Search alerts (free) | Many houses | Confirmed |
| Bidsquare | "My Alerts" | US houses | Confirmed |
| Drouot | Saved keyword alert (free account) | French houses | Confirmed |
| Lot-tissimo | Suchaufträge (free registration) | German houses | Confirmed; also Tier 1 |
| Heritage | Want List | — | Inferred from robots.txt |
| Christie's, Sotheby's, Bonhams | Department email sign-up | — | Christie's sign-up seen; Sotheby's has a site RSS feed (not opened) |
| Apollo, Setdart, Stahl, Gorny & Mosch, Bacher, Hixenbaugh, Barakat | Newsletters | — | Seen |

Each week the Codex task reads the new alert emails, keeps the lots whose own
title or description names an incantation, devil- or demon-trap, Aramaic,
Mandaic, Syriac or magic bowl, removes lots already recorded, and writes
leads. It does not follow links onto sites whose terms forbid automated
access. The email is the evidence.

### Tier 3 — Mike-present browsing (optional)

Kedem's own site, Catawiki and the Bidspirit house pages may have nothing an
alert covers. A short session with Mike at the keyboard, in his own browser
with Codex's Chrome extension or by hand, is ordinary use. It is not a
scheduled crawl. If an agent meets a challenge, it hands control to Mike and
never solves it. Bidspirit allows everything in robots.txt, but its terms
were not found, so read them before automating it.

## Output contract

The agent writes only private monitoring files. It never writes to the
corpus, the repository, the task log or git.

```
data/private/monitoring/market-agent/
  DISABLED                  # if present, stop before doing anything
  runs/<UTC stamp>.json     # receipt: emails read, sites skipped and why, leads written, corpus_writes: 0
  leads/<UTC stamp>.jsonl   # one lead per line, only when there are new leads
  evidence/<sha256>.eml|.png  # the alert email or screenshot each lead rests on
```

Lead lines use the scripted monitor's keys, so the review path stays the
same: `lead_type`, `status: "open"`, `source_monitor_id` (for example
`agent:invaluable-alert`), `search_term`, `observed_at`, `description`,
`url`, `title`, `house`, `lot_number`, `sale_date_text`, `estimate`,
`platform_lot_id` and `automation_boundary`. Each lead adds `channel`
(`alert_email` or `supervised_page`) and `evidence` (a hash and the message
date and subject, or the page URL and a screenshot hash). A lead counts as new
only if its URL, or its house plus lot number, is not already in either lead
directory.

**Still to build before the first run (small, Claude-side):**

- `monitor_leads()` and the Market tab read `market-agent/leads/` alongside
  `market/leads/`.
- `possible_match` is computed for agent leads by the same
  `known_listing_index`.
- A test for that merge.

The agent does not attempt `possible_match` itself.

## Running it in Codex

Per the Codex recon note, as of October 2026:

- **Scheduled task in the ChatGPT/Codex desktop app** (the "Automations"
  feature has been renamed Scheduled tasks). Use a weekly RRULE, run it on the
  local checkout, and have it invoke the prompt file. The Mac must be awake
  with the app open; whether missed runs catch up is undocumented. Runs are
  unattended with approvals set to `never`, so any site or app permission must
  be allowed in advance.
- OpenAI's docs don't say whether the built-in browser, the Chrome extension
  or Computer Use work inside a scheduled run. Test with **Run now** before
  relying on it.
- Reading a mailbox needs either a mail connector that Codex can use inside a
  scheduled task (Gmail triggers are web-only per the docs), or a small IMAP
  fetch script that drops `.eml` files into `evidence/inbox/` for the task to
  read. The script would use an app password that Mike stores in the macOS
  Keychain, never in the repo. The second option is more predictable.
- **Alternative:** launchd plus `codex exec -C <repo> -s workspace-write -c
  approval_policy="never" --output-schema … -o …`. This works without the
  desktop app, and Codex `exec` can load MCP servers. Tier 2 needs no browser
  at all.
- Writing into `data/private/` sits inside the workspace, so the default
  workspace-write sandbox is enough. Because the task doesn't commit, the
  read-only `.git` under that sandbox doesn't matter.
- Pin a current model. GPT-5.5 is reported to retire from Codex on
  2026-10-14.

## Decisions that are Mike's

1. Approve the recommendation that agents run no searches on platforms whose
   terms or robots.txt forbid it, using alerts there instead, or overrule it.
2. Choose the mailbox for alerts, then create the platform accounts and
   alerts. By recorded listings, Catawiki (5), LiveAuctioneers (4,
   including Apollo's sales there) and Kedem (2, through Invaluable or
   Bidspirit) matter most.
3. Choose a desktop scheduled task or launchd plus `codex exec`.
4. Whether to add the Tier 1 sites to the scripted registry. Claude or Codex
   can do that on request, through the usual reviewed registry change.

Leads from any tier are pointers only. Turning one into a record still goes
through the manifest and identity-review path in `market_tracker.md`.
