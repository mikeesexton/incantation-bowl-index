"""Localhost-only projection of the private research bank.

This deliberately shares the public projection's table shapes and presentation
logic, but not its release decisions.  It is for Mike's personal research
console only: every stored text and every recorded media URL is visible, while
the public and Cloudflare Access builds continue to use ``Projection`` and fail
closed.
"""

from .projection import Projection


class PrivateResearchProjection(Projection):
    """A private reader snapshot; never use this class in an export builder."""

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
            row["id"]: row["content"]
            for row in self.conn.execute("SELECT id,content FROM texts")
        }
        for row in rows:
            if row["content_status"] == "included":
                continue
            row["content_status"] = "private_research"
            row["content"] = content[row["id"]]
        return rows

    def _fact_candidates(self, retain_source_wording=True):
        return super()._fact_candidates(retain_source_wording=retain_source_wording)

    def _facts(self):
        """The private bank retains source wording that the release view withholds."""
        return self._fact_candidates()

    def _media(self):
        """Expose every recorded remote image URL, without implying reuse rights."""
        rows = []
        for media_id in sorted(self.evidence):
            evidence = self.evidence[media_id]
            review = self.reviews.get(media_id) or {}
            approved = review.get("public_reuse_decision") == "approved"
            rows.append({
                "id": evidence["id"],
                "object_id": evidence["object_id"],
                "appearance_id": evidence["appearance_id"],
                "source_id": evidence["source_id"],
                "media_type": evidence["media_type"],
                "url": evidence["url"],
                "attribution": (
                    review.get("attribution") if approved
                    else evidence.get("source_title") or evidence.get("source_url")
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
            "media_withheld_rows": 0,
            "facts_included_rows": len(facts),
            "facts_private_wording_rows": sum(
                row["release_class"] == "review_source_wording" for row in facts
            ),
            "facts_withheld_wording_rows": 0,
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
        "served_from": "localhost-only private research console",
    }
