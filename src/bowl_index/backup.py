"""Read-only readiness checks for encrypted private-vault backups."""

import os
import shutil
import subprocess
from pathlib import Path


def _directory_status(value, project_root):
    if not value:
        return {"configured": False, "valid": False}
    path = Path(value).expanduser()
    status = {"configured": True, "path": str(path), "valid": False}
    if not path.is_absolute() or not path.is_dir():
        return status
    resolved = path.resolve()
    try:
        resolved.relative_to(project_root)
        status["inside_project"] = True
        return status
    except ValueError:
        status["inside_project"] = False
    status["writable"] = os.access(resolved, os.W_OK)
    status["device"] = resolved.stat().st_dev
    status["valid"] = status["writable"]
    status["path"] = str(resolved)
    status["encrypted_bundles"] = sum(
        1 for item in resolved.iterdir()
        if item.is_file() and item.name.endswith((".tar.gz.gpg", ".tar.zst.gpg", ".age"))
    )
    status["restore_receipts"] = sum(
        1 for item in resolved.iterdir()
        if item.is_file() and item.name.endswith(".restore.json")
    )
    return status


def _gpg_recipient_status(recipient, executable):
    result = {
        "available": bool(executable),
        "recipient_configured": bool(recipient),
        "recipient_resolves": False,
    }
    if not executable or not recipient:
        return result
    check = subprocess.run(
        [executable, "--batch", "--list-keys", recipient],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    result["recipient_resolves"] = check.returncode == 0
    return result


def private_backup_readiness(project_root, environ=None):
    """Report concrete blockers without creating, deleting or decrypting files."""
    project_root = Path(project_root).resolve()
    environ = dict(os.environ if environ is None else environ)
    private_root = project_root / "data" / "private"
    archive_root = private_root / "archive" / "sha256"
    rich_text_root = private_root / "rich_text"
    snapshots = private_root / "backups"

    archive_files = [path for path in archive_root.glob("*/*") if path.is_file()]
    snapshot_files = [path for path in snapshots.glob("*") if path.is_file()]
    encrypted_snapshots = [
        path for path in snapshot_files
        if path.name.endswith((".gpg", ".age"))
    ]
    local = _directory_status(environ.get("IBI_LOCAL_BACKUP_DIR"), project_root)
    off_device = _directory_status(environ.get("IBI_OFFDEVICE_BACKUP_DIR"), project_root)
    gpg = _gpg_recipient_status(
        environ.get("IBI_BACKUP_GPG_RECIPIENT"), shutil.which("gpg")
    )

    blockers = []
    if not gpg["available"]:
        blockers.append("GPG is not installed")
    elif not gpg["recipient_configured"]:
        blockers.append("IBI_BACKUP_GPG_RECIPIENT is not configured")
    elif not gpg["recipient_resolves"]:
        blockers.append("the configured GPG recipient does not resolve to a public key")
    if not local.get("valid"):
        blockers.append("IBI_LOCAL_BACKUP_DIR is not a writable directory outside the project")
    if not off_device.get("valid"):
        blockers.append("IBI_OFFDEVICE_BACKUP_DIR is not a writable directory outside the project")
    if local.get("valid") and off_device.get("valid"):
        if local["path"] == off_device["path"]:
            blockers.append("local and off-device destinations are the same directory")
        if local["device"] == off_device["device"]:
            blockers.append("off-device destination is on the same filesystem device")
        if local["encrypted_bundles"] < 1:
            blockers.append("local destination has no encrypted private-vault bundle")
        if off_device["encrypted_bundles"] < 1:
            blockers.append("off-device destination has no encrypted private-vault bundle")
        if local["restore_receipts"] + off_device["restore_receipts"] < 1:
            blockers.append("no sampled-restore receipt is present")
    if len(snapshot_files) > 10:
        blockers.append("local SQLite snapshot count exceeds the stated retention limit of ten")

    return {
        "ready": not blockers,
        "blockers": blockers,
        "private_bytes": sum(
            path.stat().st_size for path in private_root.rglob("*") if path.is_file()
        ) if private_root.exists() else 0,
        "archive_files": len(archive_files),
        "archive_bytes": sum(path.stat().st_size for path in archive_files),
        "rich_text_packages": sum(
            1 for path in rich_text_root.glob("*/manifest.json") if path.is_file()
        ) if rich_text_root.exists() else 0,
        "local_sqlite_snapshots": len(snapshot_files),
        "encrypted_local_snapshots": len(encrypted_snapshots),
        "gpg": gpg,
        "local_destination": local,
        "off_device_destination": off_device,
    }
