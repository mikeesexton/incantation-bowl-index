# Draft brief: weekly market alert pass (Codex)

DRAFT, not yet scheduled. See `docs/market_agent_pass.md` for the design and the
decisions Mike must make first. Edit the bracketed parts once they are made.

---

You are running the weekly market alert pass for the Incantation Bowl Index
(DISC-004). Your job is to collect leads. You make no decisions.

**Before anything else**

- If `data/private/monitoring/market-agent/DISABLED` exists, stop and write
  nothing.
- Read `docs/market_agent_pass.md`, in particular the output contract.

**What you may read**

- New alert emails in [MAILBOX / LABEL, or `data/private/monitoring/market-agent/evidence/inbox/*.eml`]
  received since the last receipt in `data/private/monitoring/market-agent/runs/`.
- Existing leads in `data/private/monitoring/market/leads/` and
  `data/private/monitoring/market-agent/leads/`, so you can drop lots already
  recorded.
- Nothing else on the web. Do not open lot or search pages on LiveAuctioneers,
  Invaluable, Bidsquare, Barnebys, Sotheby's, Drouot, Catawiki, Heritage,
  Kedem, Freeman's, TimeLine or Trocadero. Their terms or bot protection rule
  it out. [Add any Tier 3 site Mike has approved for supervised runs only.]

**What counts as a lead**

A lot or item whose own title or description names an incantation bowl, a
devil-trap or demon-trap bowl, or an Aramaic, Mandaic, Syriac or magic bowl.
A plain "bowl" in an antiquities sale is not a lead. When unsure, include it
and say why in `description`.

**What you write**

Write only under `data/private/monitoring/market-agent/`:

- `evidence/<sha256>.eml`: each alert email a lead rests on, unchanged.
- `leads/<UTC stamp>.jsonl`: one JSON object per new lead. Use the keys listed
  in the output contract in `docs/market_agent_pass.md`. Copy price, estimate
  and date wording exactly as the email gives it. Never convert or normalise
  them.
- `runs/<UTC stamp>.json`: the receipt for this run, written even when there
  are no leads. It records the emails read (date, sender, subject, hash), the
  leads written, anything skipped and why, any errors, and `"corpus_writes": 0`.

**Never**

- Write to the database, `research/`, `docs/`, `task-log.md` or git.
- Log in, create accounts, bid, follow, watch, or click anything in an email
  except to read it.
- Solve or work around a CAPTCHA or bot check. Record the site as blocked and
  move on.
- Call two listings the same bowl, or judge authenticity, provenance or
  legality.

End with a short summary for the Scheduled inbox covering how many emails you
read, the new leads (house, lot and title) and anything blocked.
