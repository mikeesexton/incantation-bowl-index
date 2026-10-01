"""Run an encrypted backup with a consistent SQLite recovery copy and receipt.

Only backup staging/status files are written; the research database is read-only.
The destination-specific recovery copy replaces the live database on restoration.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import tempfile

from bowl_index.state import corpus_fingerprint

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def prepare_snapshot(root: Path, destination: str):
    private = root / "data/private"
    staging = private / "backup-staging" / destination
    staging.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".preparing-", suffix=".sqlite3", dir=staging)
    os.close(fd)
    temporary = Path(temporary)
    try:
        with closing(sqlite3.connect((private / "ibi.sqlite3").as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(temporary)) as copy:
                source.backup(copy)
                copy.execute("PRAGMA journal_mode=DELETE")
                if copy.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise RuntimeError("SQLite integrity check failed")
                if copy.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise RuntimeError("SQLite foreign-key check failed")
                state = corpus_fingerprint(copy)
        state.update(recorded_at=now(), recorded_by="scheduled-backup",
                     note="Fingerprint of the consistent recovery copy; live state unchanged")
        target = staging / "ibi.sqlite3"
        temporary.replace(target)
        (staging / "db-state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        return {"corpus_digest": state["corpus_digest"],
                "database_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "recovery_path": str(target.relative_to(root))}
    finally:
        temporary.unlink(missing_ok=True)


def execute_backup(command, root, env, log, timeout=3 * 60 * 60):
    # Stop the entire shell/Restic process group on timeout, before releasing
    # the staging lock. Killing only the shell would leave Restic uploading.
    with subprocess.Popen(command, cwd=root, env=env, stdout=log,
                          stderr=subprocess.STDOUT, start_new_session=True) as job:
        try:
            return job.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(job.pid, signal.SIGTERM)
            try:
                job.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(job.pid, signal.SIGKILL)
                job.wait()
            raise


def run(root: Path, destination: str):
    os.umask(0o077)
    receipts = root / "data/private/backup-receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    with (receipts / f"{destination}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"A {destination} backup is already running; keeping that run.")
            return 0
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = receipts / f"{destination}-scheduled-backup-{timestamp}.log"
        status = {"destination": destination, "started_at": now(),
                  "result": "RUNNING", "log": str(log_path.relative_to(root))}
        status_path = receipts / f"latest-{destination}-scheduled.json"

        def save_status():
            temporary = status_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(status, indent=2) + "\n")
            temporary.replace(status_path)

        save_status()
        code = 1
        with log_path.open("w") as log:
            try:
                status.update(prepare_snapshot(root, destination))
                log.write(f"Consistent database recovery copy: {status['recovery_path']}\n")
                log.write(f"Corpus digest: {status['corpus_digest']}\n")
                log.flush()
                env = dict(os.environ, IBI_BACKUP_PREPARED=destination)
                code = execute_backup(
                    ["/bin/zsh", str(root / f"scripts/restic_{destination}_backup.zsh")],
                    root, env, log,
                )
            except Exception as error:
                log.write(f"Backup failed: {type(error).__name__}: {error}\n")
            status.update(finished_at=now(), exit_code=code,
                          result="PASS" if code == 0 else "FAIL")
            log.write(f"RESULT: {status['result']}\n")
        save_status()
        if code == 0:
            (receipts / f"last-success-{destination}.json").write_text(json.dumps(status, indent=2) + "\n")
        print(f"{destination}: {status['result']}; receipt {log_path}")
        return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", choices=("local", "b2"))
    args = parser.parse_args()
    return run(ROOT, args.destination)


if __name__ == "__main__":
    raise SystemExit(main())
