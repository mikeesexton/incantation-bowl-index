# Read-only source-monitoring shadow run

This is the bounded DISC-003 / OPS-003 pilot named in the dataset-maturity
roadmap. It detects changes in reviewed public metadata endpoints without
opening or writing the corpus database.

The reviewed registry is `config/shadow_monitors.json`. Every enabled source
declares its endpoint, cadence, access and robots assessment, expected stable
identifier, and automation tier. `GET` and `HEAD` are the only permitted
methods. Broad crawling, full-text acquisition, automatic manifest ingestion,
identity resolution, rights decisions, and publication are out of scope.

Run one pass from the repository root:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_shadow_monitors.py
```

Raw response bodies are stored by SHA-256 under the ignored
`data/private/monitoring/raw/` directory. Each run writes a content-free JSON
receipt and updates a small comparison state file. The first observation is a
baseline. A later semantic fingerprint change creates a private JSONL lead; it
does not alter the corpus. Volatile API timing fields are excluded only from the
comparison fingerprint and remain present in the retained raw response.
Changing the reviewed registry deliberately starts a fresh baseline instead of
emitting false change leads against an incompatible fingerprint policy.

Create `data/private/monitoring/DISABLED` to stop a run before any request. An
atomic lock prevents overlapping runs. Requests have a byte ceiling, timeout,
bounded retry count, one-second delay, and a project user agent. A nonzero error
count makes the wrapper exit unsuccessfully after preserving the receipt.

The first pass is manual. Do not install a `launchd` schedule until the separate
standard research account and Healthchecks alert path in the Mac mini runbook
are configured and tested. OPS-004 completes only after fourteen full days of
reviewed receipts without silent loss, uncontrolled duplicates, rights leakage,
or unresolved operating failures.
