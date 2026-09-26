import unittest

from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.publication_assessments import (
    apply_publication_assessments, current_publication_assessments,
)
from bowl_index.roadmap import roadmap_metrics


class PublicationAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        migrate(self.conn)
        self.object_id = add_candidate(self.conn, {
            "label": "Museum bowl",
            "record_status": "probable",
            "source": {
                "source_type": "museum_record", "title": "Museum relation",
                "citation": "Museum relation", "url": "https://example.org/relation",
            },
            "appearance": {"locator": "object 1"},
        })
        self.evidence_source = self.conn.execute(
            "SELECT source_id FROM object_source_evidence WHERE object_id=?",
            (self.object_id,),
        ).fetchone()[0]
        self.conn.execute(
            "INSERT INTO sources(id,source_type,title,citation) VALUES (?,?,?,?)",
            ("SRC-PUBLICATION", "book", "Edition", "Edition 2000"),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def manifest(self, **overrides):
        entry = {
            "id": "IBI-PUBASSESS-1", "object_id": self.object_id,
            "disposition": "linked", "publication_source_id": "SRC-PUBLICATION",
            "evidence_source_id": self.evidence_source,
            "evidence_locator": "Related objects: object 1",
            "publication_locator": None,
            "basis": "The museum explicitly links this object to the edition.",
        }
        entry.update(overrides)
        return {
            "schema_version": 1, "reviewed_by": "Test reviewer",
            "reviewed_at": "2026-09-26T23:30:00+00:00", "entries": [entry],
        }

    def test_linked_assessment_counts_as_link_and_research_disposition(self):
        result = apply_publication_assessments(self.conn, self.manifest())
        self.assertEqual((result["changed"], result["linked"]), (1, 1))
        metrics = roadmap_metrics(self.conn)
        self.assertEqual(metrics["publication_referenced_priority_identities"], 1)
        self.assertEqual(metrics["publication_assessed_priority_identities"], 1)
        self.assertEqual(metrics["publication_no_known_priority_identities"], 0)

    def test_no_known_edition_counts_only_as_research_disposition(self):
        manifest = self.manifest(
            disposition="no_known_edition", publication_source_id=None,
            publication_locator=None, basis="A documented publication search found no edition.",
        )
        apply_publication_assessments(self.conn, manifest)
        metrics = roadmap_metrics(self.conn)
        self.assertEqual(metrics["publication_referenced_priority_identities"], 0)
        self.assertEqual(metrics["publication_assessed_priority_identities"], 1)
        self.assertEqual(metrics["publication_no_known_priority_identities"], 1)

    def test_replay_is_noop_and_history_is_append_only(self):
        self.assertEqual(apply_publication_assessments(self.conn, self.manifest())["changed"], 1)
        self.assertEqual(apply_publication_assessments(self.conn, self.manifest())["changed"], 0)
        with self.assertRaises(ValueError):
            apply_publication_assessments(self.conn, self.manifest(basis="Changed basis"))
        with self.assertRaises(Exception):
            self.conn.execute("DELETE FROM publication_assessments")

    def test_evidence_source_must_belong_to_object(self):
        self.conn.execute(
            "INSERT INTO sources(id,source_type,title,citation) VALUES (?,?,?,?)",
            ("SRC-UNRELATED", "web_page", "Unrelated", "Unrelated"),
        )
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "not linked"):
            apply_publication_assessments(
                self.conn, self.manifest(evidence_source_id="SRC-UNRELATED")
            )


if __name__ == "__main__":
    unittest.main()
