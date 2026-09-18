import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bowl_index.backup import private_backup_readiness


class PrivateBackupReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        archive = self.root / "data" / "private" / "archive" / "sha256" / "ab"
        archive.mkdir(parents=True)
        (archive / ("a" * 64)).write_bytes(b"capture")
        backups = self.root / "data" / "private" / "backups"
        backups.mkdir()
        (backups / "before-one.sqlite3.gz").write_bytes(b"snapshot")

    def tearDown(self):
        self.temp.cleanup()

    @patch("bowl_index.backup.shutil.which", return_value="/usr/local/bin/gpg")
    def test_missing_operator_configuration_is_reported_without_writes(self, _which):
        result = private_backup_readiness(self.root, environ={})
        self.assertFalse(result["ready"])
        self.assertEqual(result["archive_files"], 1)
        self.assertEqual(result["local_sqlite_snapshots"], 1)
        self.assertIn("IBI_BACKUP_GPG_RECIPIENT is not configured", result["blockers"])
        self.assertIn(
            "IBI_OFFDEVICE_BACKUP_DIR is not a writable directory outside the project",
            result["blockers"],
        )

    @patch("bowl_index.backup.shutil.which", return_value="/usr/local/bin/gpg")
    @patch("bowl_index.backup.subprocess.run")
    def test_same_device_destinations_do_not_satisfy_off_device_gate(self, run, _which):
        run.return_value.returncode = 0
        local = Path(self.temp.name) / "local"
        remote = Path(self.temp.name) / "remote"
        local.mkdir(); remote.mkdir()
        (local / "vault.tar.gz.gpg").write_bytes(b"encrypted")
        (remote / "vault.tar.gz.gpg").write_bytes(b"encrypted")
        (remote / "vault.restore.json").write_text("{}")
        result = private_backup_readiness(self.root, environ={
            "IBI_BACKUP_GPG_RECIPIENT": "ABCD1234",
            "IBI_LOCAL_BACKUP_DIR": str(local),
            "IBI_OFFDEVICE_BACKUP_DIR": str(remote),
        })
        self.assertFalse(result["ready"])
        self.assertIn("off-device destination is on the same filesystem device", result["blockers"])
        self.assertTrue(result["gpg"]["recipient_resolves"])

    @patch("bowl_index.backup.shutil.which", return_value=None)
    def test_project_internal_destination_is_rejected(self, _which):
        internal = self.root / "data" / "private" / "backups"
        result = private_backup_readiness(self.root, environ={
            "IBI_LOCAL_BACKUP_DIR": str(internal),
            "IBI_OFFDEVICE_BACKUP_DIR": str(internal),
        })
        self.assertFalse(result["local_destination"]["valid"])
        self.assertTrue(result["local_destination"]["inside_project"])


if __name__ == "__main__":
    unittest.main()
