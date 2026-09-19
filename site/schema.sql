-- D1 schema for the bowlam.com interest list.
--
-- This database is entirely separate from the corpus. It holds addresses
-- people volunteered on the landing page and nothing else: no bowl, no source,
-- no claim. Nothing here is ever joined to `data/private/ibi.sqlite3`.
--
-- Apply with:
--   cd site && npx wrangler d1 execute bowlam-interest --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS interest_signups (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  email         TEXT NOT NULL,
  created_at    TEXT NOT NULL,
  source        TEXT NOT NULL DEFAULT 'bowlam.com',
  -- Truncated hash of IP + date. Enough to rate-limit a burst, not enough to
  -- identify a person or link two days of activity. Never displayed, never
  -- exported with the address list.
  ip_day_hash   TEXT,
  -- Set when someone asks to be removed. Rows are retired, never deleted, so
  -- an unsubscribe cannot be undone by a later re-import of an old list.
  unsubscribed_at TEXT
);

-- Makes INSERT OR IGNORE the whole deduplication story, and keeps the endpoint
-- from revealing whether an address is already on the list.
CREATE UNIQUE INDEX IF NOT EXISTS interest_signups_email
  ON interest_signups (email);

CREATE INDEX IF NOT EXISTS interest_signups_created
  ON interest_signups (created_at);

-- Who to write to: everyone who has not asked to be removed.
CREATE VIEW IF NOT EXISTS interest_active AS
  SELECT id, email, created_at, source
  FROM interest_signups
  WHERE unsubscribed_at IS NULL
  ORDER BY created_at;
