"""Record the working database's identity in Git so two agents can detect drift.

The corpus lives in `data/private/ibi.sqlite3`, which is deliberately not
tracked. That makes it invisible to `git status`: an agent can open a clean
working tree over a database another agent has already changed. This module
writes a content fingerprint of every table into a tracked file so the change
is visible even though the data is not.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


STATE_FILE = Path("data") / "db-state.json"

# ANALYZE rewrites this whenever the planner reconsiders an index; it carries no
# research content and would report drift after a read-only session.
EXCLUDED_TABLES = {"sqlite_stat1"}


def _tables(conn):
    return [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        if row[0] not in EXCLUDED_TABLES
    ]


def _table_digest(conn, table):
    columns = [row[1] for row in conn.execute('PRAGMA table_info("%s")' % table)]
    if not columns:
        return 0, hashlib.sha256().hexdigest()
    selection = ",".join('"%s"' % column for column in columns)
    digest = hashlib.sha256()
    rows = 0
    for row in conn.execute('SELECT %s FROM "%s" ORDER BY %s' % (selection, table, selection)):
        rows += 1
        digest.update(repr(tuple(row)).encode("utf-8"))
        digest.update(b"\x1e")
    return rows, digest.hexdigest()


def corpus_fingerprint(conn):
    tables = {}
    for table in _tables(conn):
        rows, digest = _table_digest(conn, table)
        tables[table] = {"rows": rows, "digest": digest}
    combined = hashlib.sha256()
    for table in sorted(tables):
        combined.update(("%s:%s\n" % (table, tables[table]["digest"])).encode("utf-8"))
    migrations = [row[0] for row in conn.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    )]
    return {
        "schema_version": migrations[-1] if migrations else None,
        "migrations": len(migrations),
        "tables": tables,
        "corpus_digest": combined.hexdigest(),
    }


def read_state(project_root):
    path = Path(project_root) / STATE_FILE
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(conn, project_root, agent=None, note=None):
    path = Path(project_root) / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    state = corpus_fingerprint(conn)
    state["recorded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["recorded_by"] = agent or "unspecified"
    if note:
        state["note"] = note
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def compare_state(conn, project_root):
    recorded = read_state(project_root)
    current = corpus_fingerprint(conn)
    if recorded is None:
        return {
            "status": "unrecorded",
            "corpus_digest": current["corpus_digest"],
            "changed_tables": [],
            "detail": "No %s yet. Run `ibi state --write` to establish a baseline." % STATE_FILE,
        }
    if recorded.get("corpus_digest") == current["corpus_digest"]:
        return {
            "status": "match",
            "corpus_digest": current["corpus_digest"],
            "changed_tables": [],
            "recorded_at": recorded.get("recorded_at"),
            "recorded_by": recorded.get("recorded_by"),
        }
    changed = []
    before = recorded.get("tables", {})
    for table in sorted(set(before) | set(current["tables"])):
        was = before.get(table)
        now = current["tables"].get(table)
        if was == now:
            continue
        changed.append({
            "table": table,
            "recorded_rows": None if was is None else was.get("rows"),
            "current_rows": None if now is None else now.get("rows"),
        })
    return {
        "status": "drifted",
        "corpus_digest": current["corpus_digest"],
        "recorded_digest": recorded.get("corpus_digest"),
        "recorded_at": recorded.get("recorded_at"),
        "recorded_by": recorded.get("recorded_by"),
        "changed_tables": changed,
        "detail": (
            "The database has changed since the last recorded state. If you did not "
            "make these changes, find out who did before writing to the corpus."
        ),
    }
