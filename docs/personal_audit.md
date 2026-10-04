# Mike's daily bowl audit

The daily reminder returns to the same Codex chat at **9 a.m.
America/New_York, every day**. It is a personal review of the stored record, not
source verification, a scholarly adjudication, identity approval, or a rights
decision. Mike Access is the full private reader, including protected texts and
recorded images. The reader is currently local at `http://127.0.0.1:8765/`;
remote Mike-only capture delivery remains a separate project.

## Queue and review behavior

- Initialize once from all non-rejected identities, including candidates. Save
  one shuffled order; never pick a new random sample each day. Source appearances
  already linked by the existing identity model are shown together.
- Give Mike a daily total of five bowls, including unfinished carryovers. On the
  next New York day, fill the available slots from the saved queue. Carryovers
  retain their bowl numbers; the new daily batch has its own batch number and
  retains every earlier presentation. A final packet can have fewer than five.
- Save one allocation per New York calendar day. Retries return that allocation's
  unfinished bowls, without adding more after same-day reviews. Missing several
  days creates only one current packet, not extra batches for the absent days.
- Reading a record, reporting delivery, or receiving a notification does not
  count as reviewing it. Neither the agent nor a scheduler may infer completion.
- Mike can say `batch 2, bowl 4: reviewed—no issues noticed`,
  `reviewed—follow-up needed: ...`, or `not finished`. Confirm the exact bowl and
  presented version from the ledger, then record his response. An unambiguous
  stable bowl identifier is also accepted, but the command still names the batch.
  Ask only when the response is ambiguous; do not guess which bowls were reviewed.
- A follow-up review counts toward the pass but opens a separate issue. Apply
  eventual corrections through the existing reviewed manifest/ingest workflows.
  Resolving an operational issue does not mutate the corpus.
- Record calendar days with an outstanding batch and no completed review as
  `no_completed_review_recorded`. This does not assert whether Mike opened it.
  Offline days are accounted for on the next successful preparation; do not
  create a backlog of new daily batches.
- Append newly eligible identities to the saved order. Identity membership or
  scope changes open reconciliation issues and append any replacement identities
  for a fresh review. Old entries and decisions remain in history. Do not silently
  retire, merge, split, or transfer their completed reviews.
- Changed evidence after a completed review opens a separate recheck issue;
  the historical review remains counted. An explicit review always counts for
  the exact version Mike saw, even when it was edited before his response was
  recorded. The reviewed fingerprint stays bound to that older version; changed
  evidence opens a separate follow-up and never puts the completed bowl back in
  the daily queue. Identity changes never transfer a review to a replacement.
  The daily packet highlights changes to an unfinished bowl.
- Stop daily reminders once the queue is complete. Report remaining follow-ups
  separately; audit completion does not certify their resolution. Discoveries
  after the automation stops require explicitly resuming it.

## Storage and commands

The ignored `data/private/personal-audit/ledger.json` contains the ordered roster,
stable object memberships, initial and reviewed fingerprints, retained batch
presentations, notes, issues, delivery attempts, per-day allocations, and
append-only event history. Each update takes an advisory file lock, writes a mode-0600 temporary file,
flushes it, and atomically replaces the snapshot. Include this directory in
private-vault backups. Never copy its payloads into Git, public exports, or a
shared reader. Protected source content is fingerprinted in memory; no source
scan or full transcription is copied into audit cards.

All commands below use the usual `PYTHONPATH=src .venv/bin/python -m bowl_index.cli`
prefix. Audit commands bypass writable database connections and migrations.
Default-corpus reads fail closed when the recorded corpus state has drifted.
`--db` and `--ledger` permit isolated test fixtures; do not use those overrides to
bypass a production drift warning.

```text
audit-init
audit-daily                         # JSON, including fingerprints and attempt ID
audit-daily --format markdown       # readable presentation with private links
audit-status                       # progress, issues, saved automation ID
audit-record 4 --batch 2 --result no_issues --fingerprint <shown-sha256>
audit-record 4 --batch 2 --result followup --fingerprint <shown-sha256> --notes <Mike's-notes>
audit-record 4 --batch 2 --result not_finished --fingerprint <shown-sha256>
audit-show 4 --batch 2              # explicitly re-present even a completed bowl
audit-resolve <issue-id> --notes <Mike's-resolution>
audit-resolve <membership-issue-id> --retire --notes <Mike's-rationale>
audit-delivery <attempt-id> --outcome reported
audit-delivery <attempt-id> --outcome failed --notes <failure>
audit-schedule <app-automation-id>
```

Use `--request-id` on review commands when a stable user-message identifier is
available. Exact command retries are idempotent; later deliberate reviews keep
their own events. Use `--reviewed-on YYYY-MM-DD` only when recording a delayed
explicit response whose original New York date is established in the chat; the
append-only event retains today's recording time separately. Accept the shown
fingerprint and record completion for that version; open a separate evidence
follow-up for a newer version. `audit-show` can present changed evidence for an
optional recheck, without blocking the main daily pass. Retiring a replaced or
rejected roster entry requires Mike's explicit operational resolution and does not retire an object in the corpus.

## Scheduler and chat handling

On a scheduled wakeup, first process any unrecorded **explicit Mike review
responses**, using the earlier presentation's batch and fingerprint. Then run
`audit-daily`. Render its cards as the daily overview with source citations and
locators, full-private-record links, missing fields, review concerns, and progress.
Keep numbers stable on carryover. Explain blocked records and report read failures
without advancing. Never claim a missing image link is a retained local image.

Record `audit-delivery ... --outcome reported` when preparing the user-facing
message for this chat; this means the report was produced, not that Mike saw it
or that an operating-system notification was received. If reporting fails, append
a failed outcome. Preparation itself also retains read failures without changing
the queue. No command marks a bowl complete except an explicit `audit-record`.

Mike clarified this cadence on 2026-10-04: five bowls every day, with partial
carryovers refilled and later edits tracked separately from his personal review.
This replaces the earlier unfilled-batch and changed-pending-version rules.
Existing version-1 ledgers are upgraded with an appended policy event and saved
daily allocations; the roster, earlier batches, presentations and reviews stay
intact. Sparse final packets retain their original numbers (for example 1, 2, 5).

The app automation is a heartbeat attached to the existing chat, not a new chat
per day. Its configured ID is saved with `audit-schedule`. On queue completion,
report the final progress and open follow-ups, then pause that exact automation
through the app tool. Preserve its other settings when updating it. If the
automation cannot be paused, report that failure instead of claiming it stopped.

The computer must be on and the desktop app running for local scheduled work.
The existing localhost reader must be running for links to open. Use the normal
`ibi serve` command to start it interactively if needed. Automated preparation
does not start a server, ingest corrections, regenerate exports, deploy, or change
tracked files. Progress survives a restart and missed scheduled runs.
