import contextlib
import io
import json
import multiprocessing
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from bowl_index import personal_audit as audit
from bowl_index.cli import main
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.state import corpus_fingerprint, write_state


DAY = datetime(2026, 10, 1, 13, tzinfo=timezone.utc)  # 9 a.m. New York


def prepare_worker(path, database, output, now=DAY):
    packet = audit.prepare(path, database, now=now)
    output.put((packet["batch"], [card["item_id"] for card in packet["cards"]]))


class PersonalAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "corpus.sqlite3"
        self.path = self.root / "private/audit/ledger.json"
        self.conn = connect(self.database)
        migrate(self.conn)
        for number in range(12):
            self.add(number)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def add(self, number, status="candidate"):
        return add_candidate(self.conn, {
            "label": "Audit bowl %s" % number, "record_status": status,
            "source": {"source_type": "museum_record", "title": "Museum %s" % number,
                       "citation": "Museum catalogue %s" % number, "url": "https://example.org/%s" % number},
            "appearance": {"locator": "No. %s" % number, "confidence": 1.0},
            "identifiers": [{"scheme": "accession", "value": "A%s" % number}],
            "claims": [{"field": "material", "value_text": "ceramic", "locator": "No. %s" % number}],
        })

    def initialize(self):
        return audit.initialize(self.path, self.database, now=DAY)

    def prepare(self, days=0):
        return audit.prepare(self.path, self.database, now=DAY + timedelta(days=days))

    def ledger(self):
        return json.loads(self.path.read_text())

    def record(self, packet, card, result="no_issues", notes="", days=0, **kwargs):
        return audit.record(str(card["number"]), result, card["fingerprint"], packet["batch"], notes,
                            self.path, self.database, now=DAY + timedelta(days=days), **kwargs)

    def test_complete_pass_fixed_order_final_short_batch_and_no_corpus_writes(self):
        before = corpus_fingerprint(self.conn)
        rejected = self.add(99, "rejected")
        self.conn.commit()
        before = corpus_fingerprint(self.conn)
        self.initialize()
        roster = self.ledger()["roster"]
        self.assertEqual(len(roster), 12)
        self.assertNotIn(rejected, [member for item in roster for member in item["members"]])
        expected = [entry["id"] for entry in roster]
        actual = []
        for day, size in enumerate((5, 5, 2)):
            packet = self.prepare(day)
            self.assertEqual(len(packet["cards"]), size)
            for card in packet["cards"]:
                actual.append(card["item_id"])
                self.record(packet, card, days=day)
            self.assertEqual(self.prepare(day)["cards"], [])
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(actual)), 12)
        self.assertTrue(self.prepare(3)["progress"]["complete"])
        self.assertEqual(before, corpus_fingerprint(self.conn))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_partial_carryover_preserves_numbers_and_missed_days(self):
        self.initialize()
        packet = self.prepare()
        for card in packet["cards"][:3]:
            self.record(packet, card)
        same_day = self.prepare()
        self.assertEqual([card["number"] for card in same_day["cards"]], [4, 5])
        carried = self.prepare(4)
        self.assertTrue(carried["carryover"])
        self.assertEqual([card["number"] for card in carried["cards"]], [1, 2, 3, 4, 5])
        self.assertEqual(carried["batch"], 2)
        self.assertEqual([c["item_id"] for c in carried["cards"][-2:]],
                         [c["item_id"] for c in packet["cards"][-2:]])
        self.assertEqual([c["item_id"] for c in carried["cards"][:3]],
                         [item["id"] for item in self.ledger()["roster"][5:8]])
        self.assertEqual(self.prepare(4)["cards"], carried["cards"])
        self.assertEqual(carried["no_completed_review_recorded"],
                         ["2026-10-02", "2026-10-03", "2026-10-04"])
        for card in carried["cards"]:
            self.record(carried, card, days=4)
        self.assertEqual(self.prepare(4)["cards"], [])
        self.assertEqual(len(self.prepare(5)["cards"]), 4)

    def test_same_day_retries_and_restart_do_not_duplicate_batches(self):
        self.initialize()
        initial = self.ledger()["roster"]
        self.assertEqual(self.initialize()["total"], 12)
        self.assertEqual(self.ledger()["roster"], initial)
        first, second = self.prepare(), self.prepare()
        self.assertEqual(first["cards"], second["cards"])
        self.assertEqual(len(self.ledger()["batches"]), 1)
        response = self.record(first, first["cards"][0])
        repeat = self.record(first, first["cards"][0])
        self.assertTrue(repeat["replayed"])
        self.assertEqual(response["review_id"], repeat["review_id"])
        self.assertEqual(repeat["progress"]["reviewed"], 1)

    def test_followup_does_not_block_and_not_finished_does_not_complete(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.record(packet, card, "not_finished", "Need more time")
        self.assertEqual(audit.read_status(self.path)["reviewed"], 0)
        self.record(packet, card, "followup", "Please check this accession")
        result = audit.read_status(self.path)
        self.assertEqual(result["reviewed"], 1)
        self.assertEqual(result["outstanding_followups"], 1)
        issue_id = result["issues"][0]["id"]
        audit.close_issue(issue_id, "Mike confirms the designation was correct", self.path, self.database, now=DAY)
        self.assertEqual(audit.read_status(self.path)["outstanding_followups"], 0)
        self.assertEqual(len([event for event in self.ledger()["events"] if event["type"] == "review_recorded"]), 2)

    def test_review_requires_presented_version_batch_and_notes(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        for reference, batch, fingerprint, result in (
            ("1", None, card["fingerprint"], "no_issues"),
            ("6", 1, card["fingerprint"], "no_issues"),
            ("1", 1, "unknown", "no_issues"),
            ("1", 1, card["fingerprint"], "followup"),
        ):
            with self.assertRaises(ValueError):
                audit.record(reference, result, fingerprint, batch, path=self.path, database=self.database, now=DAY)
        self.assertEqual(audit.read_status(self.path)["reviewed"], 0)

    def test_changed_pending_review_counts_shown_version_with_separate_followup(self):
        self.initialize()
        packet = self.prepare()
        saved = [item["id"] for item in self.ledger()["roster"]]
        self.add(123)
        card = packet["cards"][0]
        self.conn.execute("UPDATE claims SET value_text='glass' WHERE object_id=?", (card["members"][0],))
        self.conn.commit()
        result = self.record(packet, card)
        self.assertEqual(result["progress"]["reviewed"], 1)
        self.assertEqual(result["progress"]["outstanding_followups"], 1)
        entry = next(e for e in self.ledger()["roster"] if e["id"] == card["item_id"])
        self.assertEqual(entry["review_fingerprint"], card["fingerprint"])
        fresh = self.prepare(1)
        self.assertNotIn(card["item_id"], [c["item_id"] for c in fresh["cards"]])
        self.assertEqual([item["id"] for item in self.ledger()["roster"]][:12], saved)
        self.assertEqual(fresh["progress"]["total"], 13)
        self.record(fresh, fresh["cards"][0], days=1)

    def test_older_review_does_not_clear_new_evidence_followups(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.record(packet, card)
        self.conn.execute("UPDATE claims SET value_text='glass' WHERE object_id=?", (card["members"][0],))
        self.conn.commit()
        changed = self.prepare(1)
        issue = changed["progress"]["issues"][0]
        self.record(packet, card, days=1, request_id="later-explicit-old-version-review")
        self.assertEqual(audit.read_status(self.path)["outstanding_followups"], 1)
        self.assertEqual(audit.read_status(self.path)["issues"][0]["id"], issue["id"])

    def test_late_review_retains_actual_day_and_retries_do_not_repeat_completion(self):
        self.initialize()
        packet = self.prepare()
        self.prepare(2)
        for card in packet["cards"]:
            self.record(packet, card, days=2, reviewed_on="2026-10-01")
        self.assertEqual(self.ledger()["batches"][0]["completed_on"], "2026-10-01")
        self.assertTrue(self.record(packet, packet["cards"][0], days=2,
                                    reviewed_on="2026-10-01")["replayed"])
        self.assertNotIn("2026-10-01", self.prepare(2)["no_completed_review_recorded"])
        with self.assertRaisesRegex(ValueError, "precedes"):
            self.record(packet, packet["cards"][0], days=2, reviewed_on="2026-09-30")
        with self.assertRaisesRegex(ValueError, "future"):
            self.record(packet, packet["cards"][0], days=2, reviewed_on="2026-10-04")

    def test_final_partial_refill_preserves_sparse_original_numbers(self):
        self.initialize()
        first = self.prepare()
        for card in first["cards"]:
            self.record(first, card)
        second = self.prepare(1)
        for card in second["cards"][:4]:
            self.record(second, card, days=1)
        last = self.prepare(2)
        self.assertEqual([c["number"] for c in last["cards"]], [1, 2, 5])
        self.assertEqual(last["cards"][-1]["item_id"], second["cards"][-1]["item_id"])
        for card in last["cards"]:
            self.record(last, card, days=2)
        self.assertTrue(self.prepare(3)["progress"]["queue_complete"])

    def test_legacy_policy_upgrade_keeps_roster_and_presentations(self):
        self.initialize()
        first = self.prepare()
        for card in first["cards"][:3]:
            self.record(first, card)
        state = self.ledger()
        state.pop("policy")
        state.pop("daily_packets")
        audit._atomic_write(self.path, state)
        old_roster = state["roster"]
        old_batch = state["batches"][0]
        packet = self.prepare(1)
        self.assertEqual(len(packet["cards"]), 5)
        self.assertEqual(self.ledger()["roster"], old_roster)
        self.assertEqual(self.ledger()["batches"][0]["item_ids"], old_batch["item_ids"])
        self.assertEqual(self.ledger()["batches"][0]["presentations"], old_batch["presentations"])
        self.assertEqual(len([e for e in self.ledger()["events"]
                              if e["type"] == "audit_policy_updated"]), 1)
        self.prepare(1)
        self.assertEqual(len(self.ledger()["batches"]), 2)

    def test_changed_completed_evidence_keeps_history_and_opens_one_issue(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.record(packet, card)
        self.conn.execute("UPDATE sources SET citation='Corrected citation' WHERE id IN "
                          "(SELECT source_id FROM claims WHERE object_id=?)", (card["members"][0],))
        self.conn.commit()
        self.prepare(1)
        result = self.prepare(2)["progress"]
        self.assertEqual(result["reviewed"], 1)
        self.assertEqual(result["outstanding_followups"], 1)
        self.assertEqual(result["issues"][0]["kind"], "evidence_changed_after_review")

        fresh = audit.show(str(card["number"]), packet["batch"], self.path, self.database,
                           now=DAY + timedelta(days=2))
        self.assertTrue(fresh["cards"][0]["changed_since_previous_presentation"])
        self.record(fresh, fresh["cards"][0], days=2)
        self.assertEqual(audit.read_status(self.path)["outstanding_followups"], 0)
        self.assertEqual(audit.read_status(self.path)["reviewed"], 1)
        self.assertEqual(len([event for event in self.ledger()["events"]
                              if event["type"] == "review_recorded"]), 2)

    def test_merge_never_transfers_reviews_and_requires_explicit_retirement(self):
        self.initialize()
        packet = self.prepare()
        a, b = packet["cards"][:2]
        self.record(packet, a)
        self.conn.execute("INSERT INTO dedupe_candidates "
                          "(id,object_a_id,object_b_id,score,status,method,rationale) "
                          "VALUES ('DED-TEST',?,?,1,'same_object','test','Test fixture')",
                          tuple(sorted((a["members"][0], b["members"][0]))))
        self.conn.commit()
        changed = self.prepare(1)
        membership = [issue for issue in changed["progress"]["issues"]
                      if issue["kind"] == "membership_or_scope_changed"]
        self.assertEqual(len(membership), 2)
        replacement = self.ledger()["roster"][-1]
        self.assertEqual(set(replacement["members"]), set(a["members"] + b["members"]))
        self.assertEqual(replacement["status"], "pending")
        with self.assertRaisesRegex(ValueError, "--retire"):
            audit.close_issue(membership[0]["id"], "Mike reconciles", self.path, self.database, now=DAY)
        for issue in membership:
            audit.close_issue(issue["id"], "Mike will review the replacement from scratch",
                              self.path, self.database, now=DAY + timedelta(days=1), retire=True)
        self.assertEqual(audit.read_status(self.path)["retired"], 2)

    def test_review_of_pre_merge_version_counts_original_without_transferring(self):
        self.initialize()
        packet = self.prepare()
        a, b = packet["cards"][:2]
        self.conn.execute("INSERT INTO dedupe_candidates "
                          "(id,object_a_id,object_b_id,score,status,method,rationale) "
                          "VALUES ('DED-LATE',?,?,1,'same_object','test','Test fixture')",
                          tuple(sorted((a["members"][0], b["members"][0]))))
        self.conn.commit()
        result = self.record(packet, a)
        self.assertEqual(result["progress"]["reviewed"], 1)
        replacement = self.ledger()["roster"][-1]
        self.assertEqual(set(replacement["members"]), set(a["members"] + b["members"]))
        self.assertEqual(replacement["status"], "pending")
        self.assertTrue(any(issue["kind"] == "membership_or_scope_changed"
                            for issue in result["progress"]["issues"]))

    def test_split_appends_fresh_entries_and_preserves_original_completed_review(self):
        members = sorted(row[0] for row in self.conn.execute("SELECT id FROM objects LIMIT 2"))
        self.conn.execute("INSERT INTO dedupe_candidates "
                          "(id,object_a_id,object_b_id,score,status,method,rationale) "
                          "VALUES ('DED-SPLIT',?,?,1,'same_object','test','Test fixture')", members)
        self.conn.commit()
        self.initialize()
        merged = next(item for item in self.ledger()["roster"] if len(item["members"]) == 2)
        # Advance through the saved random order until the merged item is presented.
        for day in range(3):
            packet = self.prepare(day)
            for card in packet["cards"]:
                self.record(packet, card, days=day)
            if any(card["item_id"] == merged["id"] for card in packet["cards"]):
                break
        self.conn.execute("UPDATE dedupe_candidates SET status='different_objects' WHERE id='DED-SPLIT'")
        self.conn.commit()
        result = self.prepare(day + 1)
        new_items = self.ledger()["roster"][-2:]
        self.assertEqual({tuple(item["members"]) for item in new_items}, {(members[0],), (members[1],)})
        self.assertTrue(all(item["status"] == "pending" for item in new_items))
        old = next(item for item in self.ledger()["roster"] if item["id"] == merged["id"])
        self.assertEqual(old["status"], "completed")
        self.assertTrue(any(issue["item_id"] == merged["id"] for issue in result["progress"]["issues"]))

    def test_rejected_pending_bowl_requires_resolution_without_disappearing(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.conn.execute("UPDATE objects SET record_status='rejected' WHERE id=?", (card["members"][0],))
        self.conn.commit()
        next_packet = self.prepare(1)
        self.assertEqual(len(next_packet["cards"]), 5)
        self.assertIn("blocked", next_packet["cards"][0])
        self.assertEqual(next_packet["progress"]["remaining"], 12)
        issue = next_packet["progress"]["issues"][0]
        audit.close_issue(issue["id"], "Mike acknowledges the source-based exclusion",
                          self.path, self.database, now=DAY + timedelta(days=1), retire=True)
        self.assertEqual(audit.read_status(self.path)["remaining"], 11)

    def test_new_appearance_on_same_source_does_not_invalidate_unrelated_bowl(self):
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.record(packet, card)
        source = self.conn.execute("SELECT source_id FROM claims WHERE object_id=?",
                                   (card["members"][0],)).fetchone()[0]
        self.conn.execute("INSERT INTO appearances (id,source_id,locator,title) "
                          "VALUES ('APP-UNRELATED',?,'another entry','Other object')", (source,))
        self.conn.commit()
        self.assertEqual(self.prepare(1)["progress"]["outstanding_followups"], 0)

    def test_reminder_identity_saved_with_history(self):
        self.initialize()
        audit.configure_reminder("test-reminder", self.path, now=DAY)
        audit.configure_reminder("test-reminder", self.path, now=DAY)
        self.assertEqual(audit.read_status(self.path)["reminder"]["automation_id"], "test-reminder")
        self.assertEqual(len([event for event in self.ledger()["events"]
                              if event["type"] == "reminder_configured"]), 1)

    def test_read_failure_records_attempt_without_advancing(self):
        self.initialize()
        packet = self.prepare()
        before = self.ledger()
        failed = audit.prepare(self.path, self.root / "missing.sqlite3", now=DAY + timedelta(days=2))
        self.assertIn("error", failed)
        after = self.ledger()
        self.assertEqual(before["roster"], after["roster"])
        self.assertEqual(before["batches"], after["batches"])
        self.assertEqual(after["events"][-1]["outcome"], "failed")
        self.assertEqual(self.prepare(3)["batch"], packet["batch"])

    def test_atomic_write_failure_preserves_previous_ledger(self):
        self.initialize()
        before = self.path.read_bytes()
        with patch.object(audit.os, "replace", side_effect=OSError("simulated power loss")):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(".audit-*")), [])

    def test_concurrent_preparation_is_serialized(self):
        self.initialize()
        context = multiprocessing.get_context("spawn")
        output = context.Queue()
        workers = [context.Process(target=prepare_worker, args=(self.path, self.database, output))
                   for _ in range(3)]
        for worker in workers:
            worker.start()
        results = [output.get(timeout=20) for _ in workers]
        for worker in workers:
            worker.join(timeout=20)
            self.assertEqual(worker.exitcode, 0)
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(self.ledger()["batches"]), 1)
        self.assertEqual(len([event for event in self.ledger()["events"]
                              if event["type"] == "delivery_attempt"]), 3)

    def test_concurrent_next_day_refill_allocates_new_slots_once(self):
        self.initialize()
        first = self.prepare()
        for card in first["cards"][:3]:
            self.record(first, card)
        context = multiprocessing.get_context("spawn")
        output = context.Queue()
        workers = [context.Process(target=prepare_worker,
                                   args=(self.path, self.database, output, DAY + timedelta(days=1)))
                   for _ in range(3)]
        for worker in workers:
            worker.start()
        results = [output.get(timeout=20) for _ in workers]
        for worker in workers:
            worker.join(timeout=20)
            self.assertEqual(worker.exitcode, 0)
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(results[0][1]), 5)
        self.assertEqual(len(self.ledger()["batches"]), 2)
        self.assertEqual(len(self.ledger()["daily_packets"]), 2)

    def test_cli_audit_bypasses_writable_connection_and_migration(self):
        with patch("bowl_index.cli.connect", side_effect=AssertionError("writable corpus")), \
                patch("bowl_index.cli.migrate", side_effect=AssertionError("migration")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            main(["--db", str(self.database), "audit-init", "--ledger", str(self.path)])
            main(["--db", str(self.database), "audit-daily", "--ledger", str(self.path)])
        self.assertIn('"batch": 1', output.getvalue())
        self.assertEqual(audit.read_status(self.path)["reviewed"], 0)

    def test_drift_fails_closed_and_unreviewed_days_use_new_york_dates(self):
        (self.root / "data").mkdir()
        write_state(self.conn, self.root, "test")
        audit.initialize(self.path, self.database, now=DAY, project_root=self.root)
        self.conn.execute("UPDATE objects SET label='changed' WHERE id=(SELECT id FROM objects LIMIT 1)")
        self.conn.commit()
        failed = audit.prepare(self.path, self.database, now=DAY, project_root=self.root)
        self.assertIn("drifted", failed["error"])
        self.assertEqual(self.ledger()["batches"], [])
        self.assertEqual(audit._day(datetime(2026, 10, 2, 2, tzinfo=timezone.utc)), "2026-10-01")
        self.assertEqual(audit._day(datetime(2026, 12, 2, 4, tzinfo=timezone.utc)), "2026-12-01")

    def test_delivery_events_are_append_only_and_idempotent(self):
        self.initialize()
        packet = self.prepare()
        before = list(self.ledger()["events"])
        audit.delivery(packet["attempt_id"], "reported", path=self.path, now=DAY)
        audit.delivery(packet["attempt_id"], "reported", path=self.path, now=DAY)
        self.assertEqual(self.ledger()["events"][:len(before)], before)
        self.assertEqual(len(self.ledger()["events"]), len(before) + 1)
        self.assertEqual(audit.read_status(self.path)["reviewed"], 0)

    def test_manual_presentation_delivery_can_be_recorded(self):
        self.initialize()
        packet = self.prepare()
        shown = audit.show("1", packet["batch"], self.path, self.database, now=DAY)
        audit.delivery(shown["attempt_id"], "reported", path=self.path, now=DAY)
        self.assertEqual(self.ledger()["events"][-1]["type"], "delivery_result")

    def test_private_cards_have_citations_and_uncommissioned_remote_is_rejected(self):
        with self.assertRaises(ValueError):
            audit.initialize(self.path, self.database, reader_base="https://bowlam.com/mike", now=DAY)
        self.initialize()
        packet = self.prepare()
        card = packet["cards"][0]
        self.assertIn("/#/explore/IDENT-", card["reader_url"])
        self.assertEqual(card["facts"][0]["value"], "ceramic")
        self.assertTrue(card["facts"][0]["citation"])
        self.assertTrue(card["facts"][0]["locator"])
        rendered = audit.markdown(packet)
        self.assertIn("Full private record", rendered)
        self.assertIn("Museum catalogue", rendered)
        self.assertIn("batch and bowl numbers", rendered)


if __name__ == "__main__":
    unittest.main()
