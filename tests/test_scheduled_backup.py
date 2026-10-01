import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_scheduled_backup import execute_backup, prepare_snapshot, run


class ScheduledBackupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.database = self.root / "data/private/ibi.sqlite3"
        self.database.parent.mkdir(parents=True)
        self.source = sqlite3.connect(self.database)
        self.addCleanup(self.source.close)
        self.source.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE schema_migrations(version TEXT);
            INSERT INTO schema_migrations VALUES ('001');
            CREATE TABLE research(id INTEGER PRIMARY KEY, value TEXT);
            INSERT INTO research VALUES (1, 'committed in WAL');
        """)

    def test_recovery_copy_includes_wal_and_does_not_change_source(self):
        before = hashlib.sha256(self.database.read_bytes()).hexdigest()
        wal_before = Path(str(self.database) + "-wal").read_bytes()
        receipt = prepare_snapshot(self.root, "local")
        recovery = self.root / receipt["recovery_path"]
        with sqlite3.connect(recovery) as restored:
            self.assertEqual(restored.execute("SELECT value FROM research").fetchone(),
                             ("committed in WAL",))
            self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(restored.execute("PRAGMA journal_mode").fetchone(), ("delete",))
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).hexdigest(), before)
        self.assertEqual(Path(str(self.database) + "-wal").read_bytes(), wal_before)
        state = json.loads((recovery.parent / "db-state.json").read_text())
        self.assertEqual(state["corpus_digest"], receipt["corpus_digest"])
        self.assertFalse((self.root / "data/db-state.json").exists())

    def test_failed_backup_preserves_last_success_and_records_failure(self):
        receipts = self.root / "data/private/backup-receipts"
        receipts.mkdir()
        success = receipts / "last-success-local.json"
        success.write_text('{"result":"PASS","started_at":"previous run"}')
        with patch("run_scheduled_backup.execute_backup", return_value=7):
            self.assertEqual(run(self.root, "local"), 7)
        self.assertEqual(json.loads(success.read_text())["started_at"], "previous run")
        self.assertEqual(json.loads((receipts / "latest-local-scheduled.json").read_text())["result"], "FAIL")

    def test_timeout_stops_the_backup_child_as_well_as_its_shell(self):
        pid_file = self.root / "child.pid"
        program = """
import signal, subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
def stop(*args):
    child.wait(timeout=5)
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
Path(sys.argv[1]).write_text(str(child.pid))
time.sleep(60)
"""
        with (self.root / "test.log").open("w") as log:
            with self.assertRaises(subprocess.TimeoutExpired):
                execute_backup([sys.executable, "-c", program, str(pid_file)],
                               self.root, os.environ, log, timeout=0.5)
        child_pid = int(pid_file.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)
