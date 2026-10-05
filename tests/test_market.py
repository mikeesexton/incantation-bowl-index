import json, tempfile, unittest
from pathlib import Path
from bowl_index.db import connect, migrate
from bowl_index.ingest import add_candidate
from bowl_index.market import market_ledger, write_market_report


def lot(label, house, locator, events, claims=(), source_type="auction_record"):
    return {"label": label,
            "source": {"source_type": source_type, "title": label, "publisher": house,
                       "citation": label, "url": "https://example.org/" + label},
            "appearance": {"locator": locator, "observed_at": "2026-09-04", "confidence": 1},
            "claims": list(claims), "events": events}


class MarketLedgerTests(unittest.TestCase):
    """A sale is what a source reports, one row per occasion, never a corpus write."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.conn = connect(self.root / "db.sqlite3"); migrate(self.conn)
        # One source reporting two occasions for one bowl: a sale, then a resale offer.
        add_candidate(self.conn, lot("Christie's lot 734", "Artemis Gallery", "lot 113", [
            {"event_type": "sale", "start_date": "2000-12-07", "actor": "Christie's",
             "details": "Sold as lot 734."},
            {"event_type": "offer", "start_date": "2019-09-26", "actor": "Artemis Gallery",
             "details": "Offered as lot 113."}],
            [{"field": "sale_result", "value_text": "US$28,200 at Christie's in 2000"}]))
        add_candidate(self.conn, lot("Kedem lot 154", "Kedem", "lot 154", [
            {"event_type": "offer", "start_date": "2013-07-02", "actor": "Kedem",
             "details": "Offered; unsold."}],
            [{"field": "sale_result", "value_text": "Unsold"}]))
        add_candidate(self.conn, lot("Apollo lot 1419", "Apollo", "lot 1419", [
            {"event_type": "offer", "start_date": "2026-10-04", "actor": "Apollo",
             "details": "Future offer."}]))
        # An aggregator page with no event of its own.
        add_candidate(self.conn, lot("Barnebys record", "Barnebys", "record 1", []))
        self.conn.commit()

    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def ledger(self):
        return market_ledger(self.conn, today="2026-10-04")

    def test_each_occasion_is_its_own_row(self):
        rows = [r for r in self.ledger()["listings"] if r["source_title"] == "Christie's lot 734"]
        self.assertEqual(sorted((r["date"], r["status"]) for r in rows),
                         [("2000-12-07", "sold"), ("2019-09-26", "offered")])
        self.assertEqual({r["house"] for r in rows}, {"Christie's", "Artemis Gallery"})

    def test_statuses_follow_recorded_wording(self):
        by_title = {r["source_title"]: r["status"] for r in self.ledger()["listings"]}
        self.assertEqual(by_title["Kedem lot 154"], "unsold")
        self.assertEqual(by_title["Apollo lot 1419"], "upcoming")
        self.assertEqual(by_title["Barnebys record"], "listing_only")

    def test_price_wording_is_kept_verbatim(self):
        row = next(r for r in self.ledger()["listings"] if r["status"] == "sold")
        self.assertEqual(row["claims"][0]["value"], "US$28,200 at Christie's in 2000")

    def test_agent_leads_join_private_ledger_with_read_only_match_pointers(self):
        directory = self.root / "market-agent/leads"
        directory.mkdir(parents=True)
        lead = {"url": "https://example.org/Apollo lot 1419", "house": "Apollo",
                "lot_number": "1419", "title": "Incantation bowl", "description": "Bowl",
                "source_monitor_id": "agent:email", "platform_lot_id": "123",
                "observed_at": "2026-10-05T00:00:00Z", "status": "open"}
        (directory / "first.jsonl").write_text(json.dumps(lead) + "\n")
        before = self.conn.total_changes
        ledger = market_ledger(self.conn, monitor_dir=self.root / "market")
        self.assertEqual(self.conn.total_changes, before)
        self.assertEqual(len(ledger["monitor_leads"]), 1)
        self.assertEqual(ledger["monitor_leads"][0]["possible_match"]["basis"], "same URL")
        self.assertEqual(json.loads((directory / "first.jsonl").read_text()), lead)

    def test_repeat_needs_two_occasions_not_two_pages(self):
        histories = self.ledger()["repeat_identities"]
        self.assertEqual(len(histories), 1)
        self.assertEqual(histories[0]["occasions"], 2)
        self.assertEqual([e["event_type"] for e in histories[0]["events"]], ["sale", "offer"])

    def test_report_is_read_only_and_private(self):
        before = self.conn.total_changes
        out = write_market_report(self.conn, self.root / "private" / "market.md", today="2026-10-04")
        self.assertEqual(self.conn.total_changes, before)
        text = Path(out["destination"]).read_text()
        self.assertIn("Private to Mike", text)
        self.assertIn("does not\n> establish lawful ownership", text)
        twin = json.loads(Path(out["json"]).read_text())
        self.assertEqual(twin["audience"], "Mike alone")
        self.assertEqual(twin["metrics"]["listings"], 5)

    def test_research_console_serves_the_ledger_and_a_market_tab(self):
        from bowl_index.web import CorpusCatalog, WEB_ROOT
        ledger = CorpusCatalog(self.root / "db.sqlite3").market()
        self.assertEqual(ledger["metrics"]["listings"], 5)
        self.assertIn('data-route="market"', (WEB_ROOT / "index.html").read_text())
        self.assertIn('id="market-view"', (WEB_ROOT / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
