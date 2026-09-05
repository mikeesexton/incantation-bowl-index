import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "private" / "ibi.sqlite3"
MIGRATIONS = PROJECT_ROOT / "migrations"


def db_path():
    return Path(os.environ.get("IBI_DB_PATH", str(DEFAULT_DB))).expanduser().resolve()


def connect(path=None):
    path = Path(path or db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        version = migration.stem
        if version in applied:
            continue
        conn.executescript(migration.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
        conn.commit()

