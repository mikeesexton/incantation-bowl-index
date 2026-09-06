import json
import tempfile
import unittest
import sqlite3
from pathlib import Path

from bowl_index.archive import verify_archive
from bowl_index.collectors import (
    _british_museum_registration, collect_british_museum_related,
    load_british_museum_page_mappings,
    _parse_apotropaic_entries, _parse_nli_sru, _parse_penn_jsonld, _schoyen_attributes,
    _schoyen_urls, _source_scoped_index_key,
    normalize_penn_identifier,
)
from bowl_index.conflicts import triage_claim_conflicts, conflict_instances, apply_review_batch
from bowl_index.conflict_review import evidence_fingerprint
from bowl_index.conflict_review import _safe_classification
from bowl_index.conflict_review import review_is_current
from bowl_index.db import connect, migrate
from bowl_index.dedupe import (
    adjudicate_conflicting_unique_identifiers, adjudicate_exact_identifiers, queue_all, score_pair,
    adjudicate_distinct_enumerated_source_items, adjudicate_explicit_concordances,
)
from bowl_index.discovery import _plain, _relevant, _source_type
from bowl_index.export import export_all
from bowl_index.enrichment import derive_normalized_dimensions
from bowl_index.ingest import add_candidate, add_lead, add_source, load_compact_list, normalize_identifier
from bowl_index.identity import identity_rows
from bowl_index.montgomery import extract_translation_sections
from bowl_index.report import statistics
from bowl_index.pdf_catalogues import _canonical_identifiers, _split_designations
from bowl_index.queries import load_audit_log, load_coverage_log, load_saturation_log, load_search_log
from bowl_index.review import load_dedupe_reviews
from bowl_index.roadmap import roadmap_metrics, write_roadmap
from bowl_index.web import CorpusCatalog, serve


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.sqlite3"
        self.conn = connect(self.db_path)
        migrate(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def candidate(self, label, accession):
        return {
            "label": label,
            "source": {
                "source_type": "museum_record",
                "title": "Test museum record " + accession,
                "citation": "Test Museum, " + accession,
                "url": "https://example.org/" + accession,
            },
            "appearance": {"locator": accession, "confidence": 1.0},
            "identifiers": [{"scheme": "accession", "value": accession, "assigning_body": "Test Museum"}],
            "claims": [{"field": "current_location", "value_text": "Test Museum"}],
        }

    def test_candidate_requires_source(self):
        with self.assertRaises(ValueError):
            add_candidate(self.conn, {"label": "orphan", "appearance": {"locator": "x"}})

    def test_montgomery_translation_parser_handles_shared_text_and_scan_furniture(self):
        pages = [
            (123, "No. 1 (CBS 8693)\ntranscription\nTranslation\nFirst line\n(117)\n"),
            (124, "118 UNIVERSITY MUSEUM. BABYEONIAN SECTION.\nSecond line\nCommentary\nnotes\n"),
        ]
        for number in range(2, 21):
            pages.append((124 + number, "No. %s (CBS %s)\nCommentary\n" % (number, number)))
        pages.append((146, "No. 21 (CBS 16054)\ntext\n"))
        pages.append((147, "No. 22 (CBS 16006)\ntext\n"))
        pages.append((148, "No. 23 (CBS 16090)\nTranslation ot No. 22\nShared text\n"))
        pages.append((149, "20i UNIVERSITY MUSEUM. BABYLONIAN SECTION.\ncontinued\nCommentary\n"))
        for number in range(24, 41):
            pages.append((150 + number, "No. %s (CBS %s)\nCommentary\n" % (number, number)))
        translations = extract_translation_sections(pages)
        self.assertEqual(set(translations), {1, 22})
        self.assertEqual(translations[1]["content"], "First line\nSecond line")
        self.assertEqual(translations[22]["content"], "Shared text\ncontinued")
        self.assertEqual(translations[1]["printed_page_start"], 117)

    def test_sources_are_idempotent_by_doi_and_offline_citation(self):
        doi_source = {
            "source_type": "article", "title": "A study", "citation": "Study citation",
            "doi": "10.1234/EXAMPLE",
        }
        self.assertEqual(add_source(self.conn, doi_source), add_source(self.conn, {
            **doi_source, "doi": "10.1234/example", "citation": "Corrected study citation",
        }))
        offline_source = {
            "source_type": "chapter", "title": "A chapter", "citation": "Unique offline citation",
        }
        self.assertEqual(add_source(self.conn, offline_source), add_source(self.conn, offline_source))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sources").fetchone()[0], 2)
        self.assertEqual(
            self.conn.execute("SELECT citation FROM sources WHERE doi IS NOT NULL").fetchone()[0],
            "Corrected study citation",
        )

    def test_candidate_has_evidence(self):
        add_candidate(self.conn, self.candidate("Bowl A", "A-1"))
        self.conn.commit()
        stats = statistics(self.conn)
        self.assertEqual(stats["candidate_objects"], 1)
        self.assertEqual(stats["objects_without_evidence"], 0)

    def test_repeat_candidate_ingest_can_enrich_without_duplication(self):
        record = self.candidate("Bowl A", "A-1")
        object_id = add_candidate(self.conn, record)
        enriched = self.candidate("Bowl A", "A-1")
        enriched["claims"].append({"field": "material", "value_text": "ceramic"})
        enriched["texts"] = [{
            "text_type": "translation", "language": "English", "content": "A short text."
        }]
        enriched["events"] = [{"event_type": "observation", "details": "Checked again."}]
        self.assertEqual(add_candidate(self.conn, enriched), object_id)
        self.assertEqual(add_candidate(self.conn, enriched), object_id)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM objects").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM claims").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM texts").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM events").fetchone()[0], 1)

    def test_existing_object_can_receive_a_new_source_appearance(self):
        object_id = add_candidate(self.conn, self.candidate("Bowl A", "A-1"))
        second = self.candidate("Bowl A in a later catalogue", "CAT-7")
        second["object_id"] = object_id
        second["source"] = {
            "source_type": "catalogue",
            "title": "Later catalogue",
            "citation": "Later Catalogue (2026), no. 7",
            "url": "https://example.org/later-catalogue/7",
        }
        second["appearance"] = {"locator": "no. 7", "confidence": 0.95}
        second["identifiers"] = [{
            "scheme": "catalogue number", "value": "CAT-7", "assigning_body": "Later Catalogue"
        }]

        self.assertEqual(add_candidate(self.conn, second), object_id)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM objects").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM appearances").fetchone()[0], 2)
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM appearance_object_links WHERE object_id=?", (object_id,)
            ).fetchone()[0],
            2,
        )
        self.assertEqual(self.conn.execute("SELECT count(*) FROM identifiers").fetchone()[0], 2)

    def test_source_authenticity_alias_is_normalized(self):
        record = self.candidate("Disputed bowl", "D-1")
        record["authenticity"] = "suspected_modern_alteration"
        object_id = add_candidate(self.conn, record)
        authenticity = self.conn.execute(
            "SELECT authenticity FROM objects WHERE id=?", (object_id,)
        ).fetchone()[0]
        self.assertEqual(authenticity, "disputed")

    def test_leads_are_idempotent_with_or_without_a_source(self):
        lead = {"lead_type": "restricted_source", "description": "Obtain the catalogue."}
        self.assertEqual(add_lead(self.conn, lead), add_lead(self.conn, lead))
        sourced = {**lead, "description": "Resolve its five records.", "source": {
            "source_type": "article", "title": "Five records", "citation": "Five records citation",
            "doi": "10.1234/five",
        }}
        self.assertEqual(add_lead(self.conn, sourced), add_lead(self.conn, sourced))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM leads").fetchone()[0], 2)

    def test_distinct_leads_can_share_a_source_url(self):
        source_id = add_source(self.conn, {
            "source_type": "article",
            "title": "One article",
            "citation": "One article citation",
            "url": "https://example.test/article",
        })
        first = {
            "id": "LEAD-FIRST",
            "source_id": source_id,
            "lead_type": "citation",
            "description": "Check the first claim.",
            "url": "https://example.test/article",
        }
        second = {
            "id": "LEAD-SECOND",
            "source_id": source_id,
            "lead_type": "identifier",
            "description": "Check the second claim.",
            "url": "https://example.test/article",
        }

        self.assertEqual(add_lead(self.conn, first), "LEAD-FIRST")
        self.assertEqual(add_lead(self.conn, second), "LEAD-SECOND")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM leads").fetchone()[0], 2)

    def test_exact_identifier_scores_high_and_queues(self):
        first = add_candidate(self.conn, self.candidate("Bowl A", "A-1"))
        second_record = self.candidate("The same bowl elsewhere", "A-1")
        second_record["source"]["title"] += " second"
        second_record["source"]["citation"] += " second"
        second_record["source"]["url"] += "-second"
        second = add_candidate(self.conn, second_record)
        self.conn.commit()
        score, method, _ = score_pair(self.conn, first, second)
        self.assertEqual(method, "exact_identifier")
        self.assertGreater(score, 0.95)
        self.assertEqual(queue_all(self.conn), 1)
        self.assertEqual(adjudicate_exact_identifiers(self.conn), 1)
        status = self.conn.execute("SELECT status FROM dedupe_candidates").fetchone()[0]
        self.assertEqual(status, "same_object")

    def test_shared_bibliography_is_not_an_exact_identifier(self):
        first = add_candidate(self.conn, self.candidate("Bowl A", "A-1"))
        second = add_candidate(self.conn, self.candidate("Bowl B", "B-2"))
        source_ids = [row[0] for row in self.conn.execute("SELECT id FROM sources ORDER BY id")]
        for object_id, source_id in zip((first, second), source_ids):
            self.conn.execute(
                "INSERT INTO identifiers "
                "(id,object_id,source_id,scheme,value,normalized_value,confidence) "
                "VALUES (?,?,?,?,?,?,1)",
                ("extra-" + object_id, object_id, source_id, "bibliographic concordance", "Shared 2000", "shared 2000"),
            )
        self.conn.commit()
        score, method, _ = score_pair(self.conn, first, second)
        self.assertNotEqual(method, "exact_identifier")
        self.assertLess(score, 0.99)

    def test_conflicting_unique_identifiers_reject_a_fuzzy_pair(self):
        first_record = self.candidate("British Museum incantation bowl 100", "A-1")
        second_record = self.candidate("British Museum incantation bowl 101", "A-2")
        for record, value in ((first_record, "W_100"), (second_record, "W_101")):
            record["identifiers"] = [{
                "scheme": "British Museum object key", "value": value,
                "assigning_body": "The British Museum",
            }]
        first = add_candidate(self.conn, first_record)
        second = add_candidate(self.conn, second_record)
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-test", min(first, second), max(first, second), .52, "label_similarity", "test"),
        )
        self.assertEqual(adjudicate_conflicting_unique_identifiers(self.conn), 1)
        row = self.conn.execute(
            "SELECT status,decided_by FROM dedupe_candidates WHERE id='ded-test'"
        ).fetchone()
        self.assertEqual(row["status"], "different_objects")
        evidence = self.conn.execute(
            "SELECT supports_match,evidence_type FROM dedupe_evidence WHERE dedupe_id='ded-test'"
        ).fetchone()
        self.assertEqual(tuple(evidence), (-1, "conflicting_unique_identifier"))

    def test_generic_collection_designations_are_not_assumed_unique(self):
        first = add_candidate(self.conn, self.candidate("Context A", "A-1"))
        second = add_candidate(self.conn, self.candidate("Context B", "A-2"))
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-generic", min(first, second), max(first, second), .52, "label_similarity", "test"),
        )
        self.assertEqual(adjudicate_conflicting_unique_identifiers(self.conn), 0)
        self.assertEqual(
            self.conn.execute(
                "SELECT status FROM dedupe_candidates WHERE id='ded-generic'"
            ).fetchone()[0],
            "pending",
        )

    def test_different_numbers_in_one_publication_namespace_conflict(self):
        first_record = self.candidate("Catalogue item 10", "A-1")
        second_record = self.candidate("Catalogue item 11", "A-2")
        for record, value in (
            (first_record, "Segal 2000::010A"), (second_record, "Segal 2000::011A")
        ):
            record["identifiers"] = [{
                "scheme": "publication object key", "value": value,
                "assigning_body": "Source-scoped concordance",
            }]
        first = add_candidate(self.conn, first_record)
        second = add_candidate(self.conn, second_record)
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-namespace", min(first, second), max(first, second), .52, "label_similarity", "test"),
        )
        self.assertEqual(adjudicate_conflicting_unique_identifiers(self.conn), 1)
        self.assertEqual(
            self.conn.execute(
                "SELECT status FROM dedupe_candidates WHERE id='ded-namespace'"
            ).fetchone()[0],
            "different_objects",
        )

    def test_different_publication_namespaces_do_not_conflict(self):
        first_record = self.candidate("Catalogue item A", "A-1")
        second_record = self.candidate("Catalogue item B", "A-2")
        first_record["identifiers"] = [{
            "scheme": "publication object key", "value": "Segal 2000::010A",
            "assigning_body": "Source-scoped concordance",
        }]
        second_record["identifiers"] = [{
            "scheme": "publication object key", "value": "Montgomery 1913::10",
            "assigning_body": "Source-scoped concordance",
        }]
        first = add_candidate(self.conn, first_record)
        second = add_candidate(self.conn, second_record)
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-cross-namespace", min(first, second), max(first, second), .52, "label_similarity", "test"),
        )
        self.assertEqual(adjudicate_conflicting_unique_identifiers(self.conn), 0)

    def test_unambiguous_cross_scheme_concordance_is_accepted(self):
        source_record = self.candidate("Old publication name", "A-1")
        source_record["identifiers"] = [{
            "scheme": "bibliographic concordance", "value": "AP 9163"
        }]
        target_record = self.candidate("Museum catalogue name", "A-2")
        target_record["identifiers"] = [{
            "scheme": "collection designation", "value": "AP9163",
            "assigning_body": "Test Museum",
        }]
        add_candidate(self.conn, source_record)
        add_candidate(self.conn, target_record)
        self.assertEqual(adjudicate_explicit_concordances(self.conn), 1)
        row = self.conn.execute(
            "SELECT status,method FROM dedupe_candidates"
        ).fetchone()
        self.assertEqual(tuple(row), ("same_object", "explicit_concordance"))

    def test_ambiguous_cross_scheme_concordance_is_not_accepted(self):
        for number in ("A-1", "A-2"):
            record = self.candidate("Ambiguous source " + number, number)
            record["identifiers"] = [{
                "scheme": "bibliographic concordance", "value": "CBS 2972"
            }]
            add_candidate(self.conn, record)
        target = self.candidate("Museum target", "A-3")
        target["identifiers"] = [{
            "scheme": "collection designation", "value": "B2972",
            "assigning_body": "Penn Museum",
        }]
        add_candidate(self.conn, target)
        self.assertEqual(adjudicate_explicit_concordances(self.conn), 0)

    def test_reviewed_enumeration_rejects_distinct_items(self):
        title = "Aramaic Incantation Bowls Project"
        first_record = self.candidate("LMU project component 1", "A-1")
        second_record = self.candidate("LMU project component 2", "A-2")
        for record in (first_record, second_record):
            record["source"]["title"] = title
            record["source"]["citation"] = "LMU project page"
            record["source"]["url"] = "https://example.org/lmu"
        first = add_candidate(self.conn, first_record)
        second = add_candidate(self.conn, second_record)
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-enumerated", min(first, second), max(first, second), .52, "label_similarity", "test"),
        )
        self.assertEqual(adjudicate_distinct_enumerated_source_items(self.conn), 1)
        evidence = self.conn.execute(
            "SELECT supports_match,source_id FROM dedupe_evidence WHERE dedupe_id='ded-enumerated'"
        ).fetchone()
        self.assertEqual(evidence["supports_match"], -1)
        self.assertIsNotNone(evidence["source_id"])

    def test_checked_dedupe_review_is_idempotent(self):
        first = add_candidate(self.conn, self.candidate("Review A", "A-1"))
        second = add_candidate(self.conn, self.candidate("Review B", "A-2"))
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-review", min(first, second), max(first, second), .5, "label_similarity", "test"),
        )
        review = Path(self.temp.name) / "reviews.jsonl"
        review.write_text(json.dumps({
            "dedupe_id": "ded-review", "status": "different_objects",
            "decided_at": "2026-09-04T17:00:00Z", "decided_by": "test reviewer",
            "evidence": [{
                "evidence_type": "different_dimensions", "value_a": "10 cm",
                "value_b": "20 cm", "supports_match": -1, "notes": "Clearly distinct."
            }],
        }) + "\n", encoding="utf-8")
        self.assertEqual(load_dedupe_reviews(self.conn, review), 1)
        self.assertEqual(load_dedupe_reviews(self.conn, review), 1)
        self.assertEqual(
            self.conn.execute(
                "SELECT status FROM dedupe_candidates WHERE id='ded-review'"
            ).fetchone()[0],
            "different_objects",
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM dedupe_evidence WHERE dedupe_id='ded-review'"
            ).fetchone()[0],
            1,
        )

    def test_nli_dimensions_are_normalized_without_overtranslation(self):
        record = self.candidate("NLI bowl", "NLI-1")
        record["claims"] = [{
            "field": "dimensions_source_text", "value_text": "גובה: 75 ממ, הקף: 165 ממ"
        }]
        add_candidate(self.conn, record)
        self.assertEqual(derive_normalized_dimensions(self.conn), 1)
        self.assertEqual(derive_normalized_dimensions(self.conn), 0)
        row = self.conn.execute(
            "SELECT value_text,value_json,supersedes_claim_id FROM claims WHERE field='dimensions'"
        ).fetchone()
        self.assertIn("source field", row["value_text"])
        self.assertEqual(json.loads(row["value_json"])["height_mm"], 75)
        self.assertIsNotNone(row["supersedes_claim_id"])

    def test_identity_export_aggregates_same_object_members(self):
        first = add_candidate(self.conn, self.candidate("Sparse publication record", "A-1"))
        second_record = self.candidate("Rich museum record", "A-1")
        second_record["source"]["url"] += "-second"
        second_record["source"]["title"] += " second"
        second_record["source"]["citation"] += " second"
        second_record["claims"].extend([
            {"field": "dating", "value_text": "6th century"},
            {"field": "dimensions", "value_text": "Diameter 20 cm"},
        ])
        second = add_candidate(self.conn, second_record)
        queue_all(self.conn, threshold=.9)
        adjudicate_exact_identifiers(self.conn)
        rows = identity_rows(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["member_count"], 2)
        self.assertEqual(rows[0]["appearance_count"], 2)
        self.assertEqual(rows[0]["has_location"], 1)
        self.assertEqual(rows[0]["has_dating"], 1)
        self.assertEqual(rows[0]["has_dimensions"], 1)
        self.assertIn(first, rows[0]["member_ids_json"])
        self.assertIn(second, rows[0]["member_ids_json"])

    def test_research_console_search_and_dossier(self):
        record = self.candidate("Bowl for Gushnasp", "UI-1")
        record["claims"].extend([
            {"field": "inscription_language", "value_text": "Jewish Babylonian Aramaic"},
            {"field": "dating", "value_text": "sixth or seventh century"},
        ])
        object_id = add_candidate(self.conn, record)
        self.conn.commit()
        catalog = CorpusCatalog(self.db_path)
        results = catalog.search({"q": ["gushnasp aramaic"], "page_size": ["10"]})
        self.assertEqual(results["total"], 1)
        identity_id = results["items"][0]["identity_id"]
        dossier = catalog.dossier(identity_id)
        self.assertEqual(dossier["summary"]["member_ids"], [object_id])
        self.assertEqual(len(dossier["appearances"]), 1)
        self.assertEqual({claim["field"] for claim in dossier["claims"]}, {
            "current_location", "inscription_language", "dating",
        })

    def test_research_console_searches_private_text_content(self):
        record = self.candidate("Bowl with translated client", "UI-TEXT-1")
        record["texts"] = [{
            "text_type": "translation", "language": "English",
            "content": "Protection for the otherwise unindexed client Narsai.",
            "rights_status": "copyrighted", "public_ok": False,
        }]
        add_candidate(self.conn, record)
        self.conn.commit()
        catalog = CorpusCatalog(self.db_path)
        results = catalog.search({"q": ["narsai"], "page_size": ["10"]})
        self.assertEqual(results["total"], 1)

    def test_research_console_records_reversible_review(self):
        first = add_candidate(self.conn, self.candidate("Review object A", "UI-A"))
        second = add_candidate(self.conn, self.candidate("Review object B", "UI-B"))
        self.conn.execute(
            "INSERT INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            ("ded-ui", min(first, second), max(first, second), .5, "label_similarity", "test"),
        )
        self.conn.commit()
        catalog = CorpusCatalog(self.db_path)
        result = catalog.decide(
            "ded-ui", "different_objects", "Different accessions and physical descriptions."
        )
        self.assertEqual(result["status"], "different_objects")
        self.assertEqual(result["decided_by"], "local research UI")
        with self.assertRaises(ValueError):
            catalog.decide("ded-ui", "same_object", "too short")
        evidence = self.conn.execute(
            "SELECT supports_match,notes FROM dedupe_evidence WHERE dedupe_id='ded-ui'"
        ).fetchone()
        self.assertEqual(evidence["supports_match"], -1)
        self.assertIn("Decision changed from pending", evidence["notes"])

    def test_research_console_refuses_remote_binding(self):
        with self.assertRaises(ValueError):
            serve(self.db_path, host="0.0.0.0", port=0)

    def test_living_roadmap_combines_tasks_with_current_metrics(self):
        add_candidate(self.conn, self.candidate("Roadmap bowl", "ROAD-1"))
        self.conn.commit()
        metrics = roadmap_metrics(self.conn)
        self.assertEqual(metrics["candidate_records"], 1)
        config = Path(self.temp.name) / "roadmap.json"
        config.write_text(json.dumps({
            "maturity_levels": [{"level": 0, "name": "Test", "definition": "Test level."}],
            "workstreams": [{
                "id": "T", "title": "Test stream", "scope": "Test scope.",
                "current_level": 0, "target_level": 0, "steward": "Test",
                "tasks": [{
                    "id": "T-001", "title": "Test task", "status": "done",
                    "owner": "Test", "done_when": "The test passes.", "evidence": "It did."
                }],
            }],
            "handoff_gate": {
                "target_date": "2026-09-22",
                "metric_conditions": [{
                    "metric": "pending_dedupe", "operator": "<=", "target": 0,
                    "description": "No pending review"
                }],
                "required_task_ids": ["T-001"],
            },
            "purchase_register": {
                "policy": "Buy only after open and library routes are checked.",
                "items": [{
                    "priority": 1, "status": "needed", "title": "Test volume",
                    "year": 2013, "source_id": "SRC-TEST", "needed_for": "T-001",
                    "purchase_url": "https://example.test/book",
                }],
            },
            "offline_access_register": {
                "policy": "Use the local research library first.",
                "items": [{
                    "priority": 1, "status": "available_onsite", "title": "Library volume",
                    "year": 1975, "source_id": "SRC-LIB", "needed_for": "T-001",
                    "lccn": "75015949", "catalog_url": "https://lccn.loc.gov/75015949",
                    "call_number": "PJ5208.A5 I8 1975",
                }],
            },
            "change_log": [],
        }), encoding="utf-8")
        destination = Path(self.temp.name) / "roadmap.md"
        result = write_roadmap(self.conn, config, destination)
        self.assertTrue(result["handoff_ready"])
        self.assertEqual(result["task_status_counts"]["done"], 1)
        self.assertEqual(result["metric_gates_passing"], 1)
        self.assertEqual(result["required_tasks_done"], 1)
        rendered = destination.read_text(encoding="utf-8")
        self.assertIn("| Roadmap tasks | 1 done · 0 in progress · 0 queued · 0 blocked |", rendered)
        self.assertIn("| Candidate source records | 1 |", rendered)
        self.assertIn("## Offline research queue", rendered)
        self.assertIn("[75015949](https://lccn.loc.gov/75015949)", rendered)
        self.assertIn("`PJ5208.A5 I8 1975`", rendered)
        self.assertIn("## Publication purchase backups", rendered)
        self.assertIn("Test volume (2013) · `SRC-TEST`", rendered)
        self.assertIn("[Publisher](https://example.test/book)", rendered)
        self.assertIn("- [x] **T-001", rendered)

    def test_claim_conflict_triage_preserves_compatible_source_claims(self):
        record = self.candidate("Museum wording variants", "CONFLICT-1")
        record["claims"] = [
            {"field": "current_location", "value_text": "The British Museum"},
            {"field": "current_location", "value_text": "British Museum, London"},
        ]
        add_candidate(self.conn, record)
        self.conn.commit()
        review = Path(self.temp.name) / "conflicts.json"
        review.write_text(json.dumps({
            "expected_conflicted_identities": 1,
            "expected_conflict_instances": 1,
            "reviewed_at": "2026-09-04T23:00:00Z",
            "reviewed_by": "test",
            "overrides": [],
        }), encoding="utf-8")
        first = triage_claim_conflicts(self.conn, review)
        second = triage_claim_conflicts(self.conn, review)
        self.assertEqual(first["dispositions"], {"compatible": 1})
        self.assertEqual(second["dispositions"], {"compatible": 1})
        row = self.conn.execute(
            "SELECT disposition,review_method FROM claim_conflict_reviews"
        ).fetchone()
        self.assertEqual(tuple(row), ("compatible", "institution_name_variant"))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM claims").fetchone()[0], 2)
        identity = identity_rows(self.conn)[0]
        self.assertEqual(json.loads(identity["raw_conflict_fields_json"]), ["location"])
        self.assertEqual(json.loads(identity["conflict_fields_json"]), [])

        # Adding a third claim must reopen the field even though the flag count is unchanged.
        record["claims"].append({"field": "current_location", "value_text": "Private collection"})
        add_candidate(self.conn, record)
        identity = identity_rows(self.conn)[0]
        self.assertEqual(json.loads(identity["conflict_fields_json"]), ["location"])
        self.assertEqual(identity["conflict_reviewed_count"], 0)
        self.assertEqual(roadmap_metrics(self.conn)["untriaged_conflict_instances"], 1)
        # The original evidence and decision remain available for inspection.
        self.assertEqual(self.conn.execute("SELECT disposition FROM claim_conflict_reviews").fetchone()[0], "compatible")

    def test_compatibility_rules_do_not_erase_material_differences(self):
        cases = [
            ("dimensions", {"dimensions": {"diameter 15 cm", "diameter 25 cm"}}),
            ("dimensions", {"dimensions": {"diameter 15 cm", "diameter 15 inches"}}),
            ("dimensions", {"dimensions": {"height 15 cm", "diameter 15 cm"}}),
            ("dating", {"dating": {"600 CE"}, "period": {"Roman", "Modern"}}),
            ("location", {"current_location": {"British Museum", "Not British Museum"}}),
            ("language", {"inscription_language": {"Syriac", "Syriac?"}}),
            ("script", {"script": {"Estrangela", "Not Estrangela"}}),
            ("provenance", {"findspot": {"בבל", "ניפור"}}),
        ]
        for field, values in cases:
            with self.subTest(field=field, values=values):
                self.assertEqual(_safe_classification(field, values)[0], "unresolved")

    def test_review_reopens_on_same_count_evidence_changes(self):
        record = self.candidate("Variants", "STALE-1")
        record["claims"] = [
            {"field": "current_location", "value_text": "The British Museum"},
            {"field": "current_location", "value_text": "British Museum"},
        ]
        add_candidate(self.conn, record)
        path = Path(self.temp.name) / "review.json"
        path.write_text(json.dumps({"expected_conflicted_identities": 1,
            "expected_conflict_instances": 1, "reviewed_at": "2026-09-04T23:00:00Z",
            "reviewed_by": "test", "overrides": []}))
        triage_claim_conflicts(self.conn, path)
        claim = dict(self.conn.execute("SELECT * FROM claims LIMIT 1").fetchone())
        for field, value in [("value_text", "Private collection"), ("certainty", "uncertain"),
                             ("locator", "corrected locator")]:
            self.conn.execute("UPDATE claims SET %s=? WHERE id=?" % field, (value, claim["id"]))
            self.assertEqual(roadmap_metrics(self.conn)["untriaged_conflict_instances"], 1)
            self.conn.execute("UPDATE claims SET %s=? WHERE id=?" % field, (claim[field], claim["id"]))
            self.assertEqual(roadmap_metrics(self.conn)["untriaged_conflict_instances"], 0)
        self.conn.execute("UPDATE sources SET title='Corrected source'")
        self.assertEqual(roadmap_metrics(self.conn)["untriaged_conflict_instances"], 1)

    def test_orphan_review_cannot_satisfy_conflict_gate(self):
        record = self.candidate("Unreviewed", "ORPHAN-1")
        record["claims"].append({"field": "current_location", "value_text": "Elsewhere"})
        add_candidate(self.conn, record)
        self.conn.execute("INSERT INTO claim_conflict_reviews "
            "(id,identity_id,field_group,disposition,review_method,rationale,details_json,reviewed_by,reviewed_at) "
            "VALUES ('IBI-TEST','IDENT-ABSENT','location','compatible','test','test','{}','test','2026-09-04T23:00:00Z')")
        metrics = roadmap_metrics(self.conn)
        self.assertEqual(metrics["reviewed_conflict_instances"], 0)
        self.assertEqual(metrics["untriaged_conflict_instances"], 1)

    def test_membership_changes_and_malformed_evidence_invalidate_reviews(self):
        review = {"details_json": json.dumps({"member_ids": ["IBI-A"], "claim_evidence": []}),
                  "disposition": "unresolved", "review_method": "checked_override"}
        self.assertTrue(review_is_current(review, ["IBI-A"], []))
        self.assertFalse(review_is_current(review, ["IBI-A", "IBI-B"], []))
        for invalid in ["{}", "null", "invalid json"]:
            review["details_json"] = invalid
            self.assertFalse(review_is_current(review, ["IBI-A"], []))

    def review_batch(self):
        record = self.candidate("Review batch", "BATCH-1")
        record["claims"] = [{"field": "dimensions", "value_text": "Diameter 5 cm"},
                            {"field": "dimensions", "value_text": "Diameter 5.00 cm"}]
        add_candidate(self.conn, record)
        self.conn.commit()
        instance = conflict_instances(self.conn)[0]
        return {"schema_version": 2, "reviewed_by": "test reviewer",
                "reviewed_at": "2026-09-04T23:00:00Z", "entries": [{
                    "identity_id": instance["identity_id"], "field_group": "dimensions",
                    "evidence_sha256": evidence_fingerprint(instance["member_ids"], instance["claims"]),
                    "disposition": "compatible", "rationale": "Same measure and unit; decimal formatting only.",
                    "review_basis": "Stored claim comparison, not fresh source verification."}]}

    def test_evidence_bound_batch_is_idempotent_and_history_is_immutable(self):
        batch = self.review_batch()
        self.assertEqual(apply_review_batch(self.conn, batch)["changed"], 1)
        self.assertEqual(apply_review_batch(self.conn, batch)["changed"], 0)
        batch["entries"][0]["rationale"] = "Reconsidered; preserve the earlier decision."
        batch["entries"][0]["disposition"] = "unresolved"
        apply_review_batch(self.conn, batch)
        history = [json.loads(r[0]) for r in self.conn.execute(
            "SELECT snapshot_json FROM claim_conflict_review_history ORDER BY rowid")]
        self.assertEqual([r["disposition"] for r in history], ["compatible", "unresolved"])
        for statement in ["DELETE FROM claim_conflict_review_history",
                          "UPDATE claim_conflict_review_history SET review_id='changed'",
                          "DELETE FROM claim_conflict_reviews"]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.conn.execute(statement)

    def test_stale_batch_rejected_even_when_conflict_count_unchanged(self):
        batch = self.review_batch()
        self.conn.execute("UPDATE claims SET locator='changed locator'")
        self.conn.commit()
        with self.assertRaisesRegex(ValueError, "Evidence changed"):
            apply_review_batch(self.conn, batch)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM claim_conflict_reviews").fetchone()[0], 0)

    def test_batch_validation_is_atomic_and_rejects_duplicates(self):
        batch = self.review_batch()
        second = dict(batch["entries"][0], identity_id="IDENT-NONEXISTENT")
        batch["entries"].append(second)
        with self.assertRaisesRegex(ValueError, "absent conflict"):
            apply_review_batch(self.conn, batch)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM claim_conflict_review_history").fetchone()[0], 0)
        batch["entries"][1] = dict(batch["entries"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            apply_review_batch(self.conn, batch)

    def test_legacy_overrides_cannot_be_replayed(self):
        path = Path(self.temp.name) / "unsafe.json"
        path.write_text(json.dumps({"overrides": [{"disposition": "compatible"}]}))
        with self.assertRaisesRegex(ValueError, "count-only overrides"):
            triage_claim_conflicts(self.conn, path)

    def test_exports_are_machine_readable(self):
        record = self.candidate("Bowl A", "A-1")
        record["texts"] = [
            {
                "text_type": "translation", "language": "English",
                "content": "Restricted translation.", "rights_status": "copyrighted",
                "public_ok": False,
            },
            {
                "text_type": "summary", "language": "English",
                "content": "Public summary.", "rights_status": "open_license",
                "public_ok": True,
            },
        ]
        add_candidate(self.conn, record)
        self.conn.execute("UPDATE appearances SET raw_json=?", ('{\"private\": true}',))
        self.conn.commit()
        destination = Path(self.temp.name) / "exports"
        manifest = export_all(self.conn, destination)
        self.assertEqual(manifest["tables"]["objects"]["rows"], 1)
        self.assertEqual(manifest["tables"]["texts"]["redacted_contents"], 1)
        self.assertEqual(manifest["tables"]["appearances"]["redacted_raw_json"], 1)
        parsed = [json.loads(line) for line in (destination / "objects.jsonl").read_text().splitlines()]
        self.assertEqual(parsed[0]["label"], "Bowl A")
        texts = [json.loads(line) for line in (destination / "texts.jsonl").read_text().splitlines()]
        by_type = {item["text_type"]: item for item in texts}
        self.assertIsNone(by_type["translation"]["content"])
        self.assertEqual(by_type["summary"]["content"], "Public summary.")
        appearance = json.loads((destination / "appearances.jsonl").read_text().splitlines()[0])
        self.assertIsNone(appearance["raw_json"])

    def test_archive_verification_empty_is_valid(self):
        self.assertEqual(verify_archive(self.conn, Path(self.temp.name) / "archive"), [])

    def test_coverage_and_saturation_logs_are_reproducible(self):
        coverage = Path(self.temp.name) / "coverage.jsonl"
        coverage.write_text(json.dumps({
            "source_class": "museum", "target_name": "Test museum", "status": "searched",
            "notes": "Catalogue checked end to end."
        }) + "\n", encoding="utf-8")
        self.assertEqual(load_coverage_log(self.conn, coverage), 1)
        self.assertEqual(load_coverage_log(self.conn, coverage), 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coverage_targets").fetchone()[0], 1)
        saturation = Path(self.temp.name) / "saturation.jsonl"
        saturation.write_text(json.dumps({
            "name": "sweep one", "strategy": "independent index", "baseline_distinct_objects": 1000,
            "net_new_distinct_objects": 4, "revealed_new_source_class": False,
            "completed_at": "2026-09-04T00:00:00Z", "notes": "Checked."
        }) + "\n", encoding="utf-8")
        self.assertEqual(load_saturation_log(self.conn, saturation), 1)
        self.assertAlmostEqual(self.conn.execute("SELECT net_new_rate FROM saturation_sweeps").fetchone()[0], .004)
        object_id = add_candidate(self.conn, self.candidate("Audit bowl", "AUD-1"))
        audit = Path(self.temp.name) / "audit.jsonl"
        audit.write_text(json.dumps({
            "object_id": object_id, "stratum": "museum", "checked_at": "2026-09-04",
            "checked_by": "test", "citation_verified": True, "identifier_verified": True,
            "claims_source_attributed": True, "result": "pass", "notes": "Verified."
        }) + "\n", encoding="utf-8")
        self.assertEqual(load_audit_log(self.conn, audit), 1)
        self.assertEqual(load_audit_log(self.conn, audit), 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM manual_audits").fetchone()[0], 1)

    def test_malformed_penn_jsonld_is_recovered(self):
        malformed = (
            '{"description":"Line one\nA catalogue "quotation" survives",'
            '"identifier":"B1","name":"Hebrew Bowl",'
            '"thumbnailUrl":"https://example.org/image.jpg"}'
        )
        item = _parse_penn_jsonld(malformed, "Hebrew Bowl", "B1", "https://example.org/B1")
        self.assertEqual(item["identifier"], "B1")
        self.assertIn("quotation", item["description"])

    def test_penn_jsonld_list_values_are_normalized(self):
        block = json.dumps({
            "name": ["Hebrew Bowl"], "description": ["Fragment", "with ink"],
            "identifier": ["B2"], "material": ["Ceramic", "Ink"],
        })
        item = _parse_penn_jsonld(block, "Hebrew Bowl", "B2", "https://example.org/B2")
        self.assertEqual(item["name"], "Hebrew Bowl")
        self.assertEqual(item["description"], "Fragment with ink")

    def test_legacy_penn_b_prefix_normalizes_to_cbs(self):
        self.assertEqual(normalize_penn_identifier("B09008"), "cbs 9008")
        self.assertEqual(normalize_penn_identifier("85-48-899"), "85-48-899")

    def test_collection_designation_normalization_ignores_spacing(self):
        self.assertEqual(
            normalize_identifier("collection designation", " MS 2053 / 13 "),
            "ms2053/13",
        )

    def test_apotropaic_index_parser_and_scoped_keys(self):
        page = '<b>HEADER</b><p><b>AIT1</b> (=CAIB1)<br><b>AIT1</b> again</p>'
        self.assertEqual(_parse_apotropaic_entries(page)[0]["designation"], "AIT1")
        self.assertEqual(_source_scoped_index_key("AIT1"), "Montgomery 1913::1")
        self.assertEqual(_source_scoped_index_key("BM001A"), "Segal 2000::001A")

    def test_schoyen_parser_and_sitemap_filter(self):
        page = '<tr class="djc_attribute"><td><span class="djc_attribute-label">MS</span></td><td class="djc_value">2053/1</td></tr>'
        self.assertEqual(_schoyen_attributes(page)["MS"], "2053/1")
        sitemap = '<loc>https://x/incantation-bowl-ms-2053-1</loc><loc>https://x/tablet</loc>'
        self.assertEqual(_schoyen_urls(sitemap), ["https://x/incantation-bowl-ms-2053-1"])

    def test_nli_sru_parser_filters_to_numbered_bowls(self):
        xml = '''<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
          <numberOfRecords>2</numberOfRecords><records><record><recordData>
          <record xmlns="http://www.loc.gov/MARC21/slim"><controlfield tag="001">9971</controlfield>
          <datafield tag="090"><subfield code="a">Ms. Heb. 9467.1</subfield></datafield>
          <datafield tag="245"><subfield code="a">קערת השבעה מס' 12.</subfield></datafield>
          <datafield tag="340"><subfield code="a">גובה: 60 ממ</subfield></datafield>
          <datafield tag="939"><subfield code="a">public domain free use</subfield></datafield>
          </record></recordData></record><record><recordData>
          <record xmlns="http://www.loc.gov/MARC21/slim"><controlfield tag="001">9972</controlfield>
          <datafield tag="245"><subfield code="a">A book about bowls</subfield></datafield>
          </record></recordData></record></records></searchRetrieveResponse>'''
        total, bowls = _parse_nli_sru(xml.encode())
        self.assertEqual(total, 2)
        self.assertEqual(len(bowls), 1)
        self.assertEqual(bowls[0]["number"], 12)
        self.assertTrue(bowls[0]["public_domain"])

    def test_waller_composite_and_ait_concordances(self):
        self.assertEqual(
            _split_designations("CAMIB 71+72+73"),
            ["CAMIB 71", "CAMIB 72", "CAMIB 73"],
        )
        values = {item["value"] for item in _canonical_identifiers(
            "Isbell 08", "Isbell 1975", "Isbell 08 = AIT 3"
        )}
        self.assertIn("Montgomery 1913::3", values)

    def test_compact_ranges_support_formats_and_source_scoped_keys(self):
        manifest = {
            "source": {
                "source_type": "catalogue", "title": "Test list",
                "citation": "Test list citation", "url": "https://example.org/list",
            },
            "list_number_scheme": "Test number",
            "ranges": [{
                "start": 1, "end": 2, "format": "BM{number:03d}A",
                "canonical_key_format": "Segal 2000::{designation}",
                "section_pages": "1–2",
            }],
        }
        path = Path(self.temp.name) / "list.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(load_compact_list(self.conn, path), 2)
        keys = [row[0] for row in self.conn.execute(
            "SELECT value FROM identifiers WHERE scheme='publication object key' ORDER BY value"
        )]
        self.assertEqual(keys, ["Segal 2000::BM001A", "Segal 2000::BM002A"])

    def test_compact_list_allows_multiple_objects_in_one_footnote(self):
        manifest = {
            "source": {
                "source_type": "thesis", "title": "Shared note",
                "citation": "Shared note citation", "url": "https://example.org/shared",
            },
            "list_number_scheme": "Test number",
            "entries": [
                {"designation": "Object A", "locator": "p. 3, note 7"},
                {"designation": "Object B", "locator": "p. 3, note 7"},
            ],
        }
        path = Path(self.temp.name) / "shared.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        load_compact_list(self.conn, path)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM objects").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM appearances").fetchone()[0], 2)

    def test_british_museum_registration_url_value_is_conservative(self):
        self.assertEqual(
            _british_museum_registration(
                "https://www.britishmuseum.org/collection/object/W_1886-0109-2"
            ),
            "1886-0109-2",
        )
        self.assertEqual(
            _british_museum_registration(
                "https://www.britishmuseum.org/collection/object/W_Rm-III-31"
            ),
            "Rm-III-31",
        )

    def test_british_museum_seed_requires_exact_relation_count(self):
        path = Path(self.temp.name) / "bm.json"
        path.write_text(json.dumps({"relation_count": 159, "records": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            collect_british_museum_related(self.conn, path)

    def test_british_museum_page_mapping_enriches_an_existing_object(self):
        object_id = add_candidate(self.conn, self.candidate("BM bowl", "BM-1"))
        path = Path(self.temp.name) / "bm-enrichment.json"
        path.write_text(json.dumps({
            "observed_at": "2026-09-04",
            "records": [{
                "object_id": object_id, "segal": "001A", "museum_number": "91713",
                "url": "https://www.britishmuseum.org/collection/object/W_1980-0415-1",
                "dating": "6thC–8thC", "dimensions": "Diameter 17.3 cm; depth 7.2 cm",
                "inscription_language": "Aramaic",
            }],
        }), encoding="utf-8")
        self.assertEqual(load_british_museum_page_mappings(self.conn, path)["objects_touched"], 1)
        self.assertEqual(load_british_museum_page_mappings(self.conn, path)["objects_touched"], 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM objects").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM appearances").fetchone()[0], 2)
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM identifiers WHERE scheme='publication object key'"
            ).fetchone()[0],
            1,
        )

    def test_checked_search_log_updates_a_planned_query(self):
        self.conn.execute(
            "INSERT INTO search_queries(id,source_class,language,query,platform) VALUES (?,?,?,?,?)",
            ("q1", "museum", "en", '"incantation bowl"', "general_web"),
        )
        path = Path(self.temp.name) / "searches.jsonl"
        path.write_text(json.dumps({
            "source_class": "museum", "language": "en",
            "query": '"incantation bowl"', "platform": "general_web",
            "searched_at": "2026-09-04T00:00:00Z", "status": "searched",
            "result_count": 10, "net_new_candidates": 2,
        }) + "\n", encoding="utf-8")
        self.assertEqual(load_search_log(self.conn, path), 1)
        row = self.conn.execute(
            "SELECT status,result_count,net_new_candidates FROM search_queries WHERE id='q1'"
        ).fetchone()
        self.assertEqual(tuple(row), ("searched", 10, 2))

    def test_metadata_sweep_normalizes_markup_and_filters_titles(self):
        self.assertEqual(_plain("<i>Magic</i> &amp; bowls"), "Magic & bowls")
        self.assertTrue(_relevant("Two New Aramaic Incantation Bowls"))
        self.assertTrue(_relevant("Aramäische Zauberschalen"))
        self.assertFalse(_relevant("The morphology of cereal bowls"))
        self.assertEqual(_source_type("book-chapter"), "chapter")
        self.assertEqual(_source_type("dissertation"), "thesis")


if __name__ == "__main__":
    unittest.main()
