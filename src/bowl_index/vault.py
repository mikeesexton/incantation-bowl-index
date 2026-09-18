"""Validation for private rich-text evidence packages.

The package remains under ``data/private/rich_text`` and outside Git.  This
module validates the small JSON manifest and TEI file without importing their
protected text into the corpus or implying permission to publish it.
"""

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
PRIVATE_LAYER = "private_research_vault"
TEXT_STATES = {"ocr", "corrected_rich_text"}
_FACS = re.compile(r"^capture:(CAP-[A-Z0-9]+)#page=([1-9][0-9]*)$")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_text(value, label):
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        raise ValueError("%s is required" % label)
    return value


def _utc_timestamp(value, label):
    value = _required_text(value, label)
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("%s must be an ISO 8601 timestamp" % label) from exc
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("%s must be UTC" % label)
    return value


def _package_file(package_root, relative_value, label):
    relative_value = _required_text(relative_value, "%s path" % label)
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("%s path must stay inside the package" % label)
    path = (package_root / relative).resolve()
    try:
        path.relative_to(package_root)
    except ValueError as exc:
        raise ValueError("%s path must stay inside the package" % label) from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError("%s file is missing or is a symlink" % label)
    return path, relative_value


def validate_rich_text_package(conn, package):
    """Validate one private package against the source and capture ledger.

    ``package`` may name the package directory or its ``manifest.json``.  The
    function is deliberately read-only and returns counts, not text content.
    """
    package = Path(package).expanduser().resolve()
    manifest_path = package / "manifest.json" if package.is_dir() else package
    package_root = manifest_path.parent.resolve()
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("private rich-text package manifest is missing or is a symlink")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("package manifest must be UTF-8 JSON") from exc

    if manifest.get("schema_version") != 1:
        raise ValueError("private rich-text package schema_version must be 1")
    package_id = _required_text(manifest.get("package_id"), "package_id")
    source_id = _required_text(manifest.get("source_id"), "source_id")
    capture_id = _required_text(manifest.get("capture_id"), "capture_id")
    document_sha = _required_text(manifest.get("document_sha256"), "document_sha256").lower()
    if len(document_sha) != 64:
        raise ValueError("document_sha256 must be a SHA-256 digest")

    source = conn.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone()
    capture = conn.execute(
        "SELECT source_id,sha256 FROM captures WHERE id=?", (capture_id,)
    ).fetchone()
    if source is None:
        raise ValueError("package source does not exist: %s" % source_id)
    if capture is None or capture["source_id"] != source_id:
        raise ValueError("package capture does not belong to source: %s" % capture_id)
    if capture["sha256"] != document_sha:
        raise ValueError("package document hash does not match the capture ledger")

    access = manifest.get("access") or {}
    if access.get("layer") != PRIVATE_LAYER or access.get("public_release") is not False:
        raise ValueError("package must be private_research_vault with public_release=false")
    for field in (
        "rights_status", "lawful_acquisition_basis", "copying_restrictions",
        "download_restrictions",
    ):
        _required_text(access.get(field), "access.%s" % field)

    transformation = manifest.get("transformation") or {}
    state = transformation.get("state")
    if state not in TEXT_STATES:
        raise ValueError("transformation.state must be ocr or corrected_rich_text")
    _required_text(transformation.get("created_by"), "transformation.created_by")
    _utc_timestamp(transformation.get("created_at"), "transformation.created_at")
    _required_text(transformation.get("method"), "transformation.method")

    text_path, text_relative = _package_file(
        package_root, manifest.get("text_path"), "TEI text"
    )
    text_sha = _required_text(manifest.get("text_sha256"), "text_sha256").lower()
    if len(text_sha) != 64 or _sha256(text_path) != text_sha:
        raise ValueError("TEI text hash does not match the package manifest")
    try:
        xml_text = text_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("TEI text must be UTF-8") from exc
    if xml_text != unicodedata.normalize("NFC", xml_text):
        raise ValueError("TEI text must use NFC-normalized Unicode")
    if "<!DOCTYPE" in xml_text.upper():
        raise ValueError("TEI text must not contain a DOCTYPE")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError("TEI text is not well-formed XML") from exc
    if root.tag != "{%s}TEI" % TEI_NAMESPACE:
        raise ValueError("rich text must use a TEI root in the TEI namespace")

    pages = root.findall(".//{%s}pb" % TEI_NAMESPACE)
    if not pages:
        raise ValueError("TEI text requires printed-page anchors with pb elements")
    image_pages = []
    for page in pages:
        _required_text(page.get("n"), "TEI pb@n")
        match = _FACS.match(page.get("facs") or "")
        if not match or match.group(1) != capture_id:
            raise ValueError(
                "TEI pb@facs must use capture:%s#page=<PDF page>" % capture_id
            )
        image_pages.append(int(match.group(2)))
    if len(image_pages) != len(set(image_pages)) or image_pages != sorted(image_pages):
        raise ValueError("TEI page-image coordinates must be unique and increasing")

    return {
        "valid": True,
        "package_id": package_id,
        "source_id": source_id,
        "capture_id": capture_id,
        "document_sha256": document_sha,
        "text_path": text_relative,
        "text_sha256": text_sha,
        "text_state": state,
        "page_anchors": len(pages),
        "first_image_page": image_pages[0],
        "last_image_page": image_pages[-1],
        "public_release": False,
    }
