# Market checks in the morning chat

DISC-004. Mike requested this workflow on 2026-10-05. The Market page is an
information and evidence viewer, not a personal checking checklist. Its House,
Platform, Relevance, Provenance, Result and sale-date controls only filter the
visible rows. They never approve, exclude, merge or mark a record reviewed.

## Routine source comparison — agent

The six-hour watch and morning task compare extracted details with the archived
email and any collected lot page. Check relevance and whether the message is a
new offer, historical correspondence, a quoted repeat or a sale announcement.
Check title, sale/lot/stock identifiers, dates, quantities, language/script scope,
full description, dimensions/units, price bases and outcome against exact source
wording. Distinguish dealer assertions from the researcher's questions. Inspect
source image URLs/copy receipts and descriptive provenance flags. A successful
fetch or automatic parse alone is not a completed comparison. Unknown fields
stay unknown; absent provenance or a price is not a task Mike must clear.

Run the report command to obtain current listing IDs, `listing_fingerprint`,
evidence hashes and locators. Read archived source bytes and compare up to ten
unchecked or changed listings per pass. Correct a wrong extraction with the
existing private `review` command, then check the corrected fingerprint. Save
an ignored draft JSON and run:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_market_intake.py source-check --input PATH
```

The JSON is `{"checks": [...]}`. Each item has `listing_id`, the exact current
`listing_fingerprint`, `status` (`checked`, `blocked`, `needs_correction`),
`note` describing the actual comparison, and `evidence` containing inspected
`sha256`/`locator` citations. A completed comparison cites the email and any
collected page. The whole batch validates before one immutable receipt. Source
bytes must still match, and a stale fingerprint rejects the check. Exact replay
is a no-op. Subsequent changed wording or evidence opens a new source comparison;
earlier receipts remain. This does not resolve identity suggestions or promote
any source assertion to verified historical fact. Report remaining blocked or
incorrect cases in chat, with the concrete gap.

The original scripted market/extra-page collectors keep their existing receipts.
Their leads and results must also be compared against those archived sources in
the chat pass, even though they use the older operational ledger. Keep that
comparison note with the digest; do not claim the new email check command covers
those older leads.

## Identity question — Mike in chat

After source comparison, the morning task asks at most three concrete questions
about unresolved corpus links or possible reappearances. Give the listing title,
house and source URL; proposed corpus record and existing locator; what agrees
(scoped stock number, image, wording or dimensions); and any conflicts. Ask
whether these refer to the same physical bowl, different bowls, or should remain
unresolved. Link the relevant private reader record where its actual identity
route is known. Use archived images for a useful private comparison when available.
Do not ask Mike to check every field or send him to an unexplained page queue.
Respect Mike's standing designation rulings and recorded answers: a repeated
same-source pointer is not a new identity question. Explain routine already-
represented listings compactly; ask only where a substantive decision remains.

For an explicit answer, first verify which exact question/candidate/version he
means. Save an append-only private JSON under
`data/private/monitoring/market-agent/intake/chat-responses/` with the shown
packet path/hash, listing ID/fingerprint, candidate IDs/basis, exact response,
UTC response date and disposition (`same_bowl`, `different_bowls`, `unresolved`).
Bind the response to the exact candidate fingerprint derived from those fields;
never transfer it to a changed listing/candidate or infer it from silence or a
source-check receipt. This receipt records Mike's statement, not a corpus merge
or a scholarly, authenticity, legal or reuse certification. Corpus changes still
require a separately reviewed manifest/ingest session. Until that happens, say
"Mike's answer recorded; corpus action pending" rather than "merged".

Check these response receipts and this chat before repeating a question. Keep
unanswered questions as carryovers with a short reminder only when useful;
a daily digest delivery does not complete them. The daily packet's separate
acknowledgment cursor still means only that the report was produced. New source
checks may clear routine extraction work while identity decisions remain open.

## Closed auction results and the main listings table

A saved monitor result must also reach the main ledger display. Inspect the
report's `market_result_followups` and `market_result_link_issues`; a captured
hammer price left only in the monitor panel is unfinished source work.

Compare the complete auction house, sale date, lot number, source URLs and lot
contents against the recorded offer. A repeated lot number or heuristic bowl
match is insufficient. This compares the same auction occasion across sources;
it does not decide physical identity across different lots. For an exact source
comparison, prepare a manifest and run:

```sh
PYTHONPATH=src .venv/bin/python scripts/reconcile_market_results.py --input PATH
```

Use `research/monitoring/apollo_1419_result_link_2026-10-05.json` as the factual
example. The manifest records version 1, reviewer, UTC comparison date, rationale,
explicit quantity wording, fingerprint of the complete immutable monitored result,
and exact object/source/event IDs and listing fingerprints from `market_listings`.
The whole batch validates the retained page bytes, explicit outcome, full house,
sale date and lot number before one append-only private receipt. No corpus write,
identity merge or replacement of an earlier offer/claim occurs. A result for a
group is always the whole lot's hammer price, never an allocated per-bowl price.
Unclear or conflicting source occasions remain follow-ups for chat.

The shared Market projection uses valid links for the main table, status filters,
counts and gap lists in both the console and Mike Access. It keeps original offer
fields and claims alongside the linked result source, date and receipt. A changed
recorded source/event or altered archived page stops applying that link and reports
the gap. Subsequent reviewed result corrections append a new receipt; old reports
remain. Offers without a linked outcome say “Offer recorded; outcome unknown”;
this does not establish present availability or an unsold result.
