"""The single gated view of the corpus.

Both the file exporter and the reader API build their rows here. That is
deliberate: the gates that decide whether a text may be shown, whether a media
URL may be named, and whether a link would leak a private capture must exist in
exactly one place. A second implementation is a second chance to publish
something withheld.

The reader API serves these tables unchanged, so a published static export and
the local console are the same bytes through the same code path.
"""

from .identity import identity_rows
from .publication import current_text_reviews
from .rights import current_media_reviews, media_evidence


EDITION_SOURCE_TYPES = ("book", "article", "chapter", "catalogue", "thesis", "excavation_report")

PROJECTION_COLUMNS = {
    "sources": ("id", "source_type", "title", "authors", "issued_year", "citation", "doi", "isbn"),
    "objects": ("id", "label", "object_type", "record_status", "authenticity"),
    "appearances": ("id", "source_id", "locator"),
    # Free-text review rationales are private; keep the relation structure only.
    "appearance_object_links": ("appearance_id", "object_id", "relation_type", "confidence"),
    "texts": ("id", "object_id", "source_id", "text_type", "language", "script", "editor",
              "locator", "rights_status", "content_status", "content", "access_citation",
              "access_locator", "access_url", "access_status"),
    "editions": ("object_id", "source_id", "source_type", "citation", "locator",
                 "access_url", "access_status"),
    "media": ("id", "object_id", "appearance_id", "source_id", "media_type", "url", "attribution"),
    "identity_clusters": ("identity_id", "canonical_object_id", "display_name", "record_status",
                          "member_count", "source_count", "appearance_count",
                          "completeness_score", "content_completeness", "reading_score"),
}

TABLE_NAMES = tuple(PROJECTION_COLUMNS)


class Projection:
    """A gated snapshot. Build once per corpus state; it does not watch the DB."""

    def __init__(self, conn):
        self.conn = conn
        reviews, evidence = current_media_reviews(conn), media_evidence(conn)
        approved = {k for k, r in reviews.items() if r["public_reuse_decision"] == "approved"}
        # Conflicting reviews for the same resource fail closed.
        blocked = {row["url"] for k, row in evidence.items() if k not in approved and row["url"]}
        approved = {k for k in approved if evidence[k]["url"] not in blocked}
        allowed = {evidence[k]["url"] for k in approved}
        self.reviews, self.evidence, self.approved = reviews, evidence, approved
        self.forbidden = blocked | {
            r["storage_path"] for r in conn.execute("SELECT storage_path FROM captures")
        } | {
            r["url"] for r in conn.execute("SELECT url FROM captures") if r["url"] not in allowed
        }
        self.approved_texts = {
            key for key, review in current_text_reviews(conn).items()
            if review["publication_decision"] == "approved"
        }

    # -- gates ---------------------------------------------------------------

    def access_link(self, doi, url):
        """A citation is a pointer only if a reader can act on it.

        Prefers a DOI, falls back to the source URL, and yields nothing rather
        than emitting a string the media/capture guard forbids. Callers always
        emit the citation and locator too, so a row never loses its pointer.
        """
        doi = (doi or "").strip()
        if doi:
            link = doi if doi.startswith("http") else "https://doi.org/" + doi
            if not self._leaks(link):
                return link
        url = (url or "").strip()
        if url.startswith(("http://", "https://")) and not self._leaks(url):
            return url
        return None

    def _leaks(self, value):
        return any(private and private in value for private in self.forbidden)

    def guard(self, name, rows):
        """Defence in depth: permitted metadata must not repeat a private reference."""
        for row in rows:
            for value in row.values():
                if isinstance(value, str) and self._leaks(value):
                    raise ValueError(
                        "Public projection contains a private media/capture reference in " + name)
        return rows

    # -- tables --------------------------------------------------------------

    def table(self, name):
        if name not in PROJECTION_COLUMNS:
            raise KeyError(name)
        return self.guard(name, getattr(self, "_" + name)())

    def tables(self):
        return {name: self.table(name) for name in TABLE_NAMES}

    def _plain(self, name):
        columns = PROJECTION_COLUMNS[name]
        return [dict(r) for r in self.conn.execute(
            "SELECT %s FROM %s ORDER BY id" % (",".join(columns), name))]

    def _sources(self):
        return self._plain("sources")

    def _objects(self):
        return self._plain("objects")

    def _appearances(self):
        return self._plain("appearances")

    def _appearance_object_links(self):
        return [dict(r) for r in self.conn.execute(
            "SELECT appearance_id,object_id,relation_type,confidence FROM appearance_object_links "
            "ORDER BY appearance_id,object_id")]

    def _texts(self):
        """Every text row is listed. Content appears only for a current approval;
        a withheld row still says what it is and where a reader can consult it."""
        rows = []
        for row in self.conn.execute(
            "SELECT t.id,t.object_id,t.source_id,t.text_type,t.language,t.script,t.editor,"
            "t.locator,t.rights_status,t.content,s.citation source_citation,s.url source_url,"
            "s.doi source_doi,s.access_status source_access_status "
            "FROM texts t JOIN sources s ON s.id=t.source_id ORDER BY t.id"
        ):
            row = dict(row)
            included = row["id"] in self.approved_texts
            rows.append({
                "id": row["id"], "object_id": row["object_id"], "source_id": row["source_id"],
                "text_type": row["text_type"], "language": row["language"],
                "script": row["script"], "editor": row["editor"], "locator": row["locator"],
                "rights_status": row["rights_status"],
                "content_status": "included" if included else "withheld_consult_the_edition",
                "content": row["content"] if included else None,
                "access_citation": row["source_citation"],
                "access_locator": row["locator"],
                "access_url": self.access_link(row["source_doi"], row["source_url"]),
                "access_status": row["source_access_status"],
            })
        return rows

    def _editions(self):
        """Where a bowl's text cannot be reproduced here, name the publications."""
        rows, seen = [], set()
        for row in self.conn.execute(
            "SELECT l.object_id,s.id source_id,s.source_type,s.citation,a.locator,s.url,s.doi,"
            "s.access_status FROM appearance_object_links l "
            "JOIN appearances a ON a.id=l.appearance_id JOIN sources s ON s.id=a.source_id "
            "WHERE s.source_type IN (%s) ORDER BY l.object_id,s.id,a.locator"
            % ",".join("?" for _ in EDITION_SOURCE_TYPES), EDITION_SOURCE_TYPES
        ):
            row = dict(row)
            key = (row["object_id"], row["source_id"], row["locator"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "object_id": row["object_id"], "source_id": row["source_id"],
                "source_type": row["source_type"], "citation": row["citation"],
                "locator": row["locator"],
                "access_url": self.access_link(row["doi"], row["url"]),
                "access_status": row["access_status"],
            })
        return rows

    def _media(self):
        keys = [k for k in PROJECTION_COLUMNS["media"] if k != "attribution"]
        return [
            {**{key: self.evidence[mid][key] for key in keys},
             "attribution": self.reviews[mid]["attribution"]}
            for mid in sorted(self.approved)
        ]

    def _identity_clusters(self):
        columns = PROJECTION_COLUMNS["identity_clusters"]
        return [{key: row[key] for key in columns} for row in identity_rows(self.conn)]

    # -- reporting -----------------------------------------------------------

    def gate_counts(self, texts=None):
        texts = self._texts() if texts is None else texts
        return {
            "texts_included_rows": len(self.approved_texts),
            "texts_withheld_rows": len(texts) - len(self.approved_texts),
            "media_approved_rows": len(self.approved),
            "media_withheld_rows": len(self.evidence) - len(self.approved),
        }
