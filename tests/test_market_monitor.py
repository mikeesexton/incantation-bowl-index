import json, tempfile, unittest
from pathlib import Path
from bowl_index.market_monitor import (
    monitor_leads, parse_the_saleroom, possible_match, known_listing_index, run_market_monitor,
)

LOT = "370508bd-c7d7-4630-8ee2-b4b20119de4c"
CARD = """<article class="panel item "> <div class="lot-single " id="lot-{lot}" data-auction-ref="apollo-art10102">
<a href="/en-gb/auction-catalogues/apollo-art/catalogue-id-apollo-art10102/lot-{lot}">img</a>
<div class="lot-header"><h3><a href="/en-gb/auction-catalogues/apollo-art/catalogue-id-apollo-art10102/lot-{lot}">
<span class="lot-number">{number}</span><span class="lot-title">COLLECTION OF ARAMAIC TERRACOTTA DEVIL TRAP BOWLS</span></a></h3></div>
<div class="byline client-url"> <a href="/en-gb/auction-catalogues/apollo-art">Apollo Art Auctions</a> </div>
<div class="description"> <p>Ca. AD 600 - 800. &gt; A collection of three terracotta incantation bowls...</p> </div>
<li class="estimate"> <span>Estimate</span> <span> <strong>450</strong> <strong> - </strong> <strong>900</strong> <strong>GBP</strong> </span> </li>
<div class="date "> <span>Date:</span> <strong>04 Oct</strong> </div></div></article>"""
PAGE = "<html><body>%s</body></html>" % CARD.format(lot=LOT, number="1419")


def registry(root):
    path = root / "market.json"
    path.write_text(json.dumps({
        "schema_version": 1, "lead_only": True,
        "settings": {"user_agent": "test", "timeout_seconds": 5,
                     "max_response_bytes": 100000, "delay_seconds": 0},
        "search_terms": ["incantation bowl", "devil trap bowl"],
        "sources": [{"id": "the-saleroom", "enabled": True, "parser": "the_saleroom",
                     "search_url": "https://www.the-saleroom.com/search?searchTerm={term}"}],
    }))
    return path


def fetcher(robots=(200, b"User-agent: *\nAllow: /\n"), page=PAGE):
    calls = []
    def fetch(url, user_agent, timeout, max_bytes):
        calls.append(url)
        return robots if url.endswith("/robots.txt") else (200, page.encode())
    fetch.calls = calls
    return fetch


class MarketMonitorTests(unittest.TestCase):
    """New lots become leads once; nothing is decided or written to the corpus."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.config = registry(self.root); self.out = self.root / "market"

    def tearDown(self):
        self.temp.cleanup()

    def test_parser_reads_a_lot_card(self):
        lots, truncated = parse_the_saleroom(PAGE, "https://www.the-saleroom.com/search")
        self.assertFalse(truncated)
        self.assertEqual(lots[0]["lot_number"], "1419")
        self.assertEqual(lots[0]["house"], "Apollo Art Auctions")
        self.assertEqual(lots[0]["estimate"], "450 - 900 GBP")
        self.assertEqual(lots[0]["sale_date_text"], "04 Oct")
        self.assertTrue(lots[0]["teaser"].startswith("Ca. AD 600 - 800. >"))
        self.assertTrue(lots[0]["url"].startswith("https://www.the-saleroom.com/en-gb/"))

    def test_a_lot_found_by_two_terms_is_one_lead_and_never_repeats(self):
        first = run_market_monitor(self.config, self.out, fetch=fetcher(), now="2026-10-04T06:00:00Z")
        self.assertEqual(first["new_leads"], 1)
        self.assertEqual(first["corpus_writes"], 0)
        second = run_market_monitor(self.config, self.out, fetch=fetcher(), now="2026-10-11T06:00:00Z")
        self.assertEqual(second["new_leads"], 0)
        self.assertEqual(len(monitor_leads(self.out)), 1)
        state = json.loads((self.out / "state.json").read_text())
        self.assertEqual(state["lots"]["the-saleroom/" + LOT]["terms"],
                         ["incantation bowl", "devil trap bowl"])

    def test_robots_refusal_or_unreadable_robots_fails_closed(self):
        for robots in [(200, b"User-agent: *\nDisallow: /search\n"), (403, b"")]:
            out = self.root / str(robots[0])
            fetch = fetcher(robots=robots)
            receipt = run_market_monitor(self.config, out, fetch=fetch)
            self.assertEqual({r["disposition"] for r in receipt["requests"]}, {"robots_disallowed"})
            self.assertTrue(all(url.endswith("/robots.txt") for url in fetch.calls))

    def test_a_recorded_lot_is_flagged_not_merged(self):
        ledger = {"listings": [{"identity_id": "IDENT-1", "object_id": "IBI-1",
                                "house": "Apollo Art Auctions", "locator": "lot 1419, object 1 (left)",
                                "url": None, "date": "2026-10-04"}]}
        run_market_monitor(self.config, self.out, ledger=ledger, fetch=fetcher())
        lead = monitor_leads(self.out)[0]
        self.assertEqual(lead["possible_match"]["identity_id"], "IDENT-1")
        self.assertIn("sale not compared", lead["possible_match"]["basis"])
        self.assertEqual(lead["status"], "open")
        other = parse_the_saleroom(CARD.format(lot=LOT, number="7"), "https://x/")[0][0]
        self.assertIsNone(possible_match(other, known_listing_index(ledger)))

    def test_fuzzy_matches_are_counted_not_kept(self):
        devon = CARD.format(lot=LOT.replace("3", "4"), number="2").replace(
            "COLLECTION OF ARAMAIC TERRACOTTA DEVIL TRAP BOWLS", "A Crown Devon jug and bowl").replace(
            "A collection of three terracotta incantation bowls", "Pottery")
        page = "<div>2 item(s)</div>" + PAGE + devon
        receipt = run_market_monitor(self.config, self.out, fetch=fetcher(page=page))
        self.assertEqual(receipt["requests"][0]["lots"], 2)
        self.assertEqual(receipt["requests"][0]["relevant_lots"], 1)
        self.assertFalse(receipt["requests"][0]["more_pages_not_read"])
        self.assertEqual(receipt["new_leads"], 1)

    def test_a_short_page_is_flagged(self):
        _, truncated = parse_the_saleroom("<div>75 item(s)</div>" + PAGE, "https://x/")
        self.assertTrue(truncated)

    def test_kill_switch_and_registry_guard(self):
        self.out.mkdir(); (self.out / "DISABLED").touch()
        with self.assertRaises(RuntimeError):
            run_market_monitor(self.config, self.out, fetch=fetcher())
        bad = self.root / "bad.json"; bad.write_text(json.dumps({"schema_version": 1}))
        with self.assertRaises(ValueError):
            run_market_monitor(bad, self.root / "other", fetch=fetcher())


if __name__ == "__main__":
    unittest.main()
