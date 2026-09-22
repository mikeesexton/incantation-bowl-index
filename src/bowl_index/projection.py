"""The rights-gated release view of the corpus.

Both the file exporter and the reader API build their rows here. That is
deliberate: the gates that decide whether a text may be shown, whether a media
URL may be named, and whether a link would expose private capture storage must
exist in exactly one place. A second implementation is a second chance to
publish something withheld.

Shared scholar and public builds serve these tables unchanged. Mike-only
research surfaces use ``PrivateResearchProjection`` with the same table shapes,
but may expose material held privately that this release projection withholds.
"""

import json
import re

from .identity import COVERAGE_GROUPS, identity_rows
from .presentation import format_date, public_facets
from .publication import current_text_reviews
from .publications import current_registry, publication_keys
from .rights import current_media_reviews, media_evidence
from .scholarship import (
    SCOPE_LABELS, contributor_groups, decade_series, works,
)


EDITION_SOURCE_TYPES = ("book", "article", "chapter", "catalogue", "thesis", "excavation_report")

PROJECTION_COLUMNS = {
    "sources": ("id", "source_type", "title", "authors", "issued_year", "citation", "doi", "isbn"),
    "objects": ("id", "label", "object_type", "record_status", "authenticity"),
    "identifiers": ("object_id", "scheme", "value", "assigning_body"),
    "appearances": ("id", "source_id", "locator"),
    # Free-text review rationales are private; keep the relation structure only.
    "appearance_object_links": ("appearance_id", "object_id", "relation_type", "confidence"),
    # `rights_basis` and `license_url` describe the terms the content is published
    # under, so they are populated only where there is content. A source licence
    # narrower than this repository's CC BY 4.0 travels with its rows, and without
    # these two columns a consumer could not tell which rows those are.
    "texts": ("id", "object_id", "source_id", "text_type", "language", "script", "editor",
              "locator", "rights_status", "content_status", "content", "rights_basis",
              "license_url", "attribution", "rights_locator", "editorial_status",
              "access_citation", "access_locator", "access_url", "access_status"),
    "editions": ("object_id", "source_id", "source_type", "citation", "locator",
                 "access_url", "access_status"),
    "media": ("id", "object_id", "appearance_id", "source_id", "media_type", "url", "attribution",
              "rights_status", "rights_statement", "rights_locator", "license_url"),
    "identity_clusters": ("identity_id", "canonical_object_id", "member_ids", "display_name",
                          "display_date", "display_language", "display_collection",
                          "record_status", "member_count", "source_count", "appearance_count",
                          "completeness_score", "content_completeness", "reading_score"),
    "facts": ("object_id", "field", "field_group", "value", "recorded_value", "certainty",
              "source_id", "locator", "release_class"),
    # Project-authored browse labels. Every row points back to the raw claim that
    # generated it; this table never replaces or silently rewrites source wording.
    "facets": ("object_id", "facet_group", "facet_label", "source_field", "source_id", "locator"),
    "works": ("source_id", "title", "authors", "issued_year", "container_title", "citation",
              "doi", "source_type", "access_status", "scope", "scope_label", "scope_basis",
              "objects_published", "document_held"),
    "contributors": ("contributor_key", "display_name", "spellings", "works",
                     "objects_published", "first_year", "last_year", "needs_check"),
    "scholarship_decades": ("decade", "held", "field_control_list"),
    "publications": ("publication_key", "source_id", "resolution", "blocker", "objects",
                     "object_ids"),
}

# A fact is short and checkable. Free-text prose is not.
#
# The gate reuses the field model rather than inventing a second one: a claim is
# publishable as a fact when its field sits in a comparison group. That set was
# built to hold assertions that can be compared to one another, which is the same
# property that makes them facts rather than someone's expression — and it already
# excludes `catalogue_description`, the museum prose that kept the research
# snapshots out of Git. The length cap is belt and braces; the longest value in
# any comparison group today is 215 characters.
FACT_FIELDS = frozenset(field for fields in COVERAGE_GROUPS.values() for field in fields)
FACT_FIELD_GROUP = {field: group for group, fields in COVERAGE_GROUPS.items() for field in fields}
FACT_MAX_LENGTH = 300

# Conservative triage, not a legal conclusion. Values in these fields are more
# likely to preserve source expression. Public-domain wording and short claims
# are identified separately; longer wording from a non-public-domain source is
# the bounded human queue. An open release can prefer ``facets`` in every tier.
SOURCE_WORDING_REVIEW_FIELDS = frozenset({
    "text_content", "text_feature", "textual_feature", "text_characterization",
    "catalogue_classification", "text_purpose", "text_function", "text_tradition",
    "installation_instruction", "provenance", "provenance_summary", "collection_history",
    "excavation_context", "associated_find", "iconography_or_caption",
    "authenticity_assessment", "technical_test",
})
SOURCE_WORDING_PRIORITY_LENGTH = 80
EMBEDDED_QUOTATION = re.compile(r'“[^”]+”|‘[^’]+’|"[^"]+"')

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
        self.reviews, self.evidence, self.approved = reviews, evidence, approved
        capture_rows = list(conn.execute("SELECT storage_path FROM captures"))
        self.capture_count = len(capture_rows)
        self.private_storage = {r["storage_path"] for r in capture_rows}
        self.forbidden = blocked | self.private_storage
        # A dict, not a set: an approved row has to publish the terms it was
        # approved under. `in` and `len` behave the same, so the gates above and
        # the counts below are unchanged.
        self.approved_texts = {
            key: review for key, review in current_text_reviews(conn).items()
            if review["publication_decision"] == "approved"
        }

    # -- gates ---------------------------------------------------------------

    def access_link(self, doi, url):
        """A citation is a pointer only if a reader can act on it.

        Prefers a DOI, falls back to the source URL, and yields nothing rather
        than emitting a string the media/private-storage guard forbids. A
        capture's public source URL is not private merely because the project
        archived a copy; only its storage path remains forbidden. Callers
        always emit the citation and locator too, so a row never loses its
        pointer.
        """
        doi = (doi or "").strip()
        if doi:
            link = doi if doi.startswith("http") else "https://doi.org/" + doi
            if not self._leaks_storage(link):
                return link
        url = (url or "").strip()
        if url.startswith(("http://", "https://")) and not self._leaks_storage(url):
            return url
        return None

    def _leaks_storage(self, value):
        return any(private and private in value for private in self.private_storage)

    def _leaks(self, value):
        return any(private and private in value for private in self.forbidden)

    def guard(self, name, rows):
        """Defence in depth: permitted metadata must not repeat a private reference."""
        for row in rows:
            for key, value in row.items():
                # This field is a bibliographic pointer, not a media release.
                # It may name the same public page that a media row cites, but
                # it may never expose the archived copy's storage location.
                if key == "access_url" and isinstance(value, str):
                    if self._leaks_storage(value):
                        raise ValueError(
                            "Public projection contains a private media/capture reference in " + name)
                    continue
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

    def _identifiers(self):
        return self._plain("identifiers")

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
            review = self.approved_texts.get(row["id"])
            included = review is not None
            rows.append({
                "id": row["id"], "object_id": row["object_id"], "source_id": row["source_id"],
                "text_type": row["text_type"], "language": row["language"],
                "script": row["script"], "editor": row["editor"], "locator": row["locator"],
                "rights_status": row["rights_status"],
                "content_status": "included" if included else "withheld_consult_the_edition",
                "content": row["content"] if included else None,
                "rights_basis": review["rights_basis"] if included else None,
                "license_url": review["license_url"] if included else None,
                "attribution": review["attribution"] if included else None,
                "rights_locator": review["rights_locator"] if included else None,
                "editorial_status": review["editorial_status"] if included else None,
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
        evidence_keys = [
            key for key in PROJECTION_COLUMNS["media"]
            if key not in {"attribution", "rights_statement", "rights_locator", "license_url"}
        ]
        return [
            {**{key: self.evidence[mid][key] for key in evidence_keys},
             **{key: self.reviews[mid][key] for key in (
                 "attribution", "rights_statement", "rights_locator", "license_url")}}
            for mid in sorted(self.approved)
        ]

    def _identity_clusters(self):
        columns = PROJECTION_COLUMNS["identity_clusters"]
        rows = []
        for row in identity_rows(self.conn):
            projected = {key: row[key] for key in columns if key != "member_ids"}
            # Kept as the stored JSON string so the CSV and JSONL agree.
            projected["member_ids"] = row["member_ids_json"]
            rows.append({key: projected[key] for key in columns})
        return rows

    def _works(self):
        rows = works(self.conn)
        for row in rows:
            row["scope_label"] = SCOPE_LABELS.get(row["scope"], "Not yet classified")
            row["document_held"] = int(row["document_held"])
        return [{key: row[key] for key in PROJECTION_COLUMNS["works"]} for row in rows]

    def _contributors(self):
        rows = contributor_groups(self.conn)
        for row in rows:
            # A JSON string keeps the CSV and JSONL forms identical.
            row["spellings"] = json.dumps(row["spellings"], ensure_ascii=False)
            row["needs_check"] = int(row["needs_check"])
        return [{key: row[key] for key in PROJECTION_COLUMNS["contributors"]} for row in rows]

    def _publications(self):
        """Which bowls a publication publishes — the question SCHOL-004 made askable."""
        counts, registry = publication_keys(self.conn), current_registry(self.conn)
        members = {}
        for row in self.conn.execute(
            "SELECT object_id,value FROM identifiers WHERE scheme=? AND object_id IS NOT NULL",
            ("publication object key",)
        ):
            key = row["value"].split("::")[0].strip()
            key = re.sub(r"\s+(?:bowl|popularity bowl)\b.*$", "", key, flags=re.I).strip()
            members.setdefault(key, set()).add(row["object_id"])
        rows = []
        for key in sorted(counts, key=lambda k: -counts[k]):
            entry = registry.get(key, {})
            rows.append({
                "publication_key": key,
                "source_id": entry.get("source_id"),
                "resolution": entry.get("resolution", "unregistered"),
                "blocker": entry.get("blocker"),
                "objects": counts[key],
                "object_ids": json.dumps(sorted(members.get(key, [])), ensure_ascii=False),
            })
        return rows

    def _scholarship_decades(self):
        return decade_series(self.conn)

    def _fact_candidates(self, retain_source_wording=False):
        """Short, checkable assertions about an object, with their source.

        Without this the projection can say a bowl exists and nothing about it —
        not where it is, what language it is in, or who it protects.
        """
        rows = []
        for row in self.conn.execute(
            "SELECT c.object_id,c.field,c.value_text,c.value_json,c.normalized_value,c.certainty,"
            "c.source_id,c.locator,s.rights_status source_rights_status FROM claims c "
            "JOIN sources s ON s.id=c.source_id ORDER BY c.object_id,c.field,c.id"
        ):
            if row["field"] not in FACT_FIELDS:
                continue
            value = row["normalized_value"] or row["value_text"] or row["value_json"]
            if not value or len(value) > FACT_MAX_LENGTH:
                continue
            recorded_value = row["value_text"] or row["value_json"] or value
            if row["field"] == "dating":
                value = format_date(value)
            release_class = "factual_metadata"
            if row["field"] in SOURCE_WORDING_REVIEW_FIELDS:
                if row["source_rights_status"] == "public_domain":
                    release_class = "public_domain_source_wording"
                elif (len(value) <= SOURCE_WORDING_PRIORITY_LENGTH
                      and not EMBEDDED_QUOTATION.search(value)):
                    release_class = "short_source_claim"
                else:
                    release_class = "review_source_wording"
            # Raw source wording is useful for explaining a normalized display
            # value, but it must pass the same expression gate independently.
            safe_recorded_value = recorded_value
            if (not retain_source_wording
                    and row["field"] in SOURCE_WORDING_REVIEW_FIELDS
                    and row["source_rights_status"] != "public_domain"
                    and (len(recorded_value) > SOURCE_WORDING_PRIORITY_LENGTH
                         or EMBEDDED_QUOTATION.search(recorded_value))):
                safe_recorded_value = value
            rows.append({
                "object_id": row["object_id"], "field": row["field"],
                "field_group": FACT_FIELD_GROUP[row["field"]], "value": value,
                "recorded_value": safe_recorded_value,
                "certainty": row["certainty"], "source_id": row["source_id"],
                "locator": row["locator"],
                "release_class": release_class,
            })
        return rows

    def _facts(self):
        """Public fact rows; longer uncleared source wording fails closed."""
        return [
            row for row in self._fact_candidates()
            if row["release_class"] != "review_source_wording"
        ]

    def _facets(self):
        """Controlled visitor labels derived from, and traceable to, raw facts."""
        rows = []
        # Facet wording is the project's own. It may safely express the
        # underlying fact even when the longer raw source wording is withheld.
        for fact in self._fact_candidates():
            for label in public_facets(fact["field"], fact["field_group"], fact["value"]):
                rows.append({
                    "object_id": fact["object_id"], "facet_group": fact["field_group"],
                    "facet_label": label, "source_field": fact["field"],
                    "source_id": fact["source_id"], "locator": fact["locator"],
                })
        return rows

    # -- reporting -----------------------------------------------------------

    def gate_counts(self, texts=None):
        texts = self._texts() if texts is None else texts
        fact_candidates = self._fact_candidates()
        return {
            "texts_included_rows": len(self.approved_texts),
            "texts_withheld_rows": len(texts) - len(self.approved_texts),
            "media_approved_rows": len(self.approved),
            "media_withheld_rows": len(self.evidence) - len(self.approved),
            "facts_included_rows": sum(
                row["release_class"] != "review_source_wording" for row in fact_candidates
            ),
            "facts_withheld_wording_rows": sum(
                row["release_class"] == "review_source_wording" for row in fact_candidates
            ),
        }
