"""Mike-only projection of the private research bank.

This deliberately shares the public projection's table shapes and presentation
logic, but not its release decisions. It is for Mike's personal research
surfaces only: every stored text and every recorded media URL is visible. Shared
scholar and public builds continue to use ``Projection`` and fail closed.
"""

from pathlib import Path

from .db import PROJECT_ROOT
from .documents import source_document_status
from .projection import Projection
from .proofreading import current_text_reviews


DEFAULT_PRIVATE_MEDIA_ROOT = PROJECT_ROOT / "data" / "private" / "media"

# Provisional routes are research evidence, not comparable object properties.
# Keep them out of public fact release and automatic identity/publication metrics.
RESEARCH_LEAD_FIELDS = frozenset({
    "publication_pointer_report", "former_collection_designation_report",
})
PRIVATE_DESCRIPTION_FIELDS = {"handwriting": "practitioner", "named_person": "named_person"}


class PrivateResearchProjection(Projection):
    """A private reader snapshot; never use it in a shared or public builder."""

    def __init__(self, conn, media_root=None, capture_base=None, capture_urls=None):
        super().__init__(conn)
        self.media_root = Path(media_root or DEFAULT_PRIVATE_MEDIA_ROOT)
        self.capture_base = capture_base
        self.capture_links = {}
        if capture_base or capture_urls:
            no_document = {source_id for source_id, assessment in
                           source_document_status(conn).items()
                           if assessment["extent"] == "citation_only"}
            for row in conn.execute(
                "SELECT id,source_id FROM captures ORDER BY retrieved_at,id"
            ):
                if row["source_id"] and row["source_id"] not in no_document:
                    url = (capture_urls or {}).get(row["id"])
                    if url is None and capture_base:
                        url = capture_base + row["id"]
                    if url:
                        self.capture_links[row["source_id"]] = url

    def guard(self, name, rows):
        """Keep local capture paths out of the browser even in the private view."""
        for row in rows:
            for value in row.values():
                if isinstance(value, str) and self._leaks_storage(value):
                    raise ValueError(
                        "Private reader contains a capture storage path in " + name
                    )
        return rows

    def _texts(self):
        """Expose all stored text; distinguish private access from publication."""
        rows = super()._texts()
        content = {
            row["id"]: dict(row)
            for row in self.conn.execute("SELECT id,content,notes FROM texts")
        }
        checks = current_text_reviews(self.conn)
        for row in rows:
            # Earlier whole-section extraction rows were labelled summaries.
            # Keep their exact OCR available, but do not present it as prose.
            notes = content[row["id"]]["notes"] or ""
            if row["text_type"] == "summary":
                if ("Working historical OCR of the entire numbered section" in notes
                        or "Working full source-page OCR includes neighboring material" in notes
                        or "Full born-digital section working extraction with commentary and notes" in notes):
                    row["text_type"] = "source_ocr"
                elif "Born-digital working extraction; page headers" in notes:
                    row["text_type"] = "catalogue_extract"
            if row["source_id"] in self.capture_links:
                row["access_url"] = self.capture_links[row["source_id"]]
            if row["content_status"] == "included":
                continue
            row["content_status"] = "private_research"
            row["content"] = content[row["id"]]["content"]
            check = checks.get(row["id"])
            row["editorial_status"] = check["status"] if check else "not_checked"
        return rows

    def _editions(self):
        rows = super()._editions()
        for row in rows:
            if row["source_id"] in self.capture_links:
                row["access_url"] = self.capture_links[row["source_id"]]
        return rows

    def _fact_candidates(self, retain_source_wording=True):
        rows = super()._fact_candidates(retain_source_wording=retain_source_wording)
        for row in self.conn.execute(
            "SELECT object_id,field,value_text,value_json,certainty,source_id,locator "
            "FROM claims ORDER BY object_id,field,id"
        ):
            if row["field"] not in RESEARCH_LEAD_FIELDS and row["field"] not in PRIVATE_DESCRIPTION_FIELDS:
                continue
            value = row["value_text"] or row["value_json"]
            if value:
                rows.append({
                    "object_id": row["object_id"], "field": row["field"],
                    "field_group": PRIVATE_DESCRIPTION_FIELDS.get(row["field"], "research"), "value": value,
                    "recorded_value": value, "certainty": row["certainty"],
                    "source_id": row["source_id"], "locator": row["locator"],
                    "release_class": "private_research_lead",
                })
        return rows

    def _facts(self):
        """The private bank retains source wording and provisional research routes."""
        return self._fact_candidates()

    def _media(self):
        """Expose every recorded remote image URL, without implying reuse rights."""
        rows = []
        for media_id in sorted(self.evidence):
            evidence = self.evidence[media_id]
            review = self.reviews.get(media_id) or {}
            approved = review.get("public_reuse_decision") == "approved"
            local_derivative = self.media_root / (media_id + ".png")
            notes = evidence.get("notes") or ""
            native_facsimile = evidence["media_type"] == "scan" and notes.startswith(
                "Original-script edition facsimile;"
            )
            source_attribution = evidence.get("source_title") or evidence.get("source_url")
            if native_facsimile:
                source_attribution = notes.split(";", 1)[1].split(" Crop from registered capture", 1)[0].strip()
            rows.append({
                "id": evidence["id"],
                "object_id": evidence["object_id"],
                "appearance_id": evidence["appearance_id"],
                "source_id": evidence["source_id"],
                "media_type": (
                    "inscription_facsimile"
                    if native_facsimile
                    else evidence["media_type"]
                ),
                "url": (
                    "/api/private-media/" + media_id + ".png"
                    if local_derivative.is_file() else evidence["url"]
                ),
                "attribution": (
                    review.get("attribution") if approved
                    else source_attribution
                ),
                "rights_status": evidence["rights_status"],
                "rights_statement": (
                    review.get("rights_statement") if approved else
                    "Private research view only; no public reuse permission recorded."
                    + ((" " + review["rights_statement"])
                       if review.get("rights_statement") else "")
                ),
                "rights_locator": review.get("rights_locator"),
                "license_url": review.get("license_url") if approved else None,
            })
        return rows

    def gate_counts(self, texts=None):
        texts = self._texts() if texts is None else texts
        media = self._media()
        facts = self._fact_candidates()
        return {
            "texts_included_rows": sum(
                row["content_status"] == "included" for row in texts
            ),
            "texts_private_rows": sum(
                row["content_status"] == "private_research" for row in texts
            ),
            "texts_available_rows": len(texts),
            "texts_withheld_rows": 0,
            "media_approved_rows": len(self.approved),
            "media_private_rows": len(media) - len(self.approved),
            "media_available_rows": len(media),
            "media_local_derivative_rows": sum(
                row["url"].startswith("/api/private-media/") for row in media
            ),
            "media_withheld_rows": 0,
            "facts_included_rows": len(facts),
            "facts_private_wording_rows": sum(
                row["release_class"] == "review_source_wording" for row in facts
            ),
            "facts_withheld_wording_rows": 0,
            "source_captures_recorded_rows": self.capture_count,
            "source_capture_sources_linked": len(self.capture_links),
        }


def private_manifest(projection, tables, generated_at):
    """Describe personal access without making a public licence claim."""
    return {
        "generated_at": generated_at,
        "access_tier": "private_research",
        "access_notice": (
            "Mike's personal research bank. Content availability here is not "
            "permission to publish, redistribute, or share it."
        ),
        **projection.gate_counts(tables["texts"]),
        "tables": {
            name: {"rows": len(rows), "url": "/api/reader/" + name}
            for name, rows in tables.items()
        },
        "served_from": "Mike-only private research surface",
    }
