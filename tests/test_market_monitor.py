import json, tempfile, unittest
from pathlib import Path
from bowl_index.market_monitor import (
    monitor_leads, parse_the_saleroom, parse_the_saleroom_lot, possible_match,
    known_listing_index, run_market_monitor,
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
LOT_URL = ("https://www.the-saleroom.com/en-gb/auction-catalogues/apollo-art/"
           "catalogue-id-apollo-art10102/lot-" + LOT)


def lot_page(ended="false", amount="Passed"):
    """The closed-lot panel as the-saleroom ships it (hidden until the lot ends)."""
    return ("""<div class="ui basic segment auction-closed hide">
 <input type="hidden" id="lot-is-ended" value="%s" />
 <strong><span class="data"><time datetime="2026-10-04T12-00-00Z"><time datetime='2026-10-04T12-00-00Z'>04 Oct 2026 13:00 BST</time></time></span></strong>
 <label for="hammer_price">Hammer Price:</label>
 <strong>
 <span id="closed-price" class="amount">%s</span>
 <span class="currency closed-currency hide"> GBP</span>
 </strong></div>""" % (ended, amount)).encode()


def registry(root):
    path = root / "market.json"
    path.write_text(json.dumps({
        "schema_version": 1, "lead_only": True,
        "settings": {"user_agent": "test", "timeout_seconds": 5,
                     "max_response_bytes": 100000, "delay_seconds": 0},
        "search_terms": ["incantation bowl", "devil trap bowl"],
        "sources": [{"id": "the-saleroom", "enabled": True, "parser": "the_saleroom",
                     "result_parser": "the_saleroom",
                     "search_url": "https://www.the-saleroom.com/search?searchTerm={term}"}],
    }))
    return path


def fetcher(robots=(200, b"User-agent: *\nAllow: /\n"), page=PAGE, lots=None):
    """Fake network: robots.txt, search pages, and lot pages by URL."""
    calls = []
    lots = lots if lots is not None else {LOT_URL: (200, lot_page(), None)}
    def fetch(url, user_agent, timeout, max_bytes):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return robots
        if url in lots:
            return lots[url]
        return 200, page.encode(), None
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

    def test_lot_page_states(self):
        self.assertEqual(parse_the_saleroom_lot(lot_page().decode())["outcome"], "pending")
        sold = parse_the_saleroom_lot(lot_page("true", "600").decode())
        self.assertEqual((sold["outcome"], sold["hammer_text"]), ("sold", "600 GBP"))
        self.assertEqual(sold["sale_at"], "2026-10-04T12:00:00Z")
        self.assertEqual(parse_the_saleroom_lot(lot_page("true").decode())["outcome"], "passed")
        self.assertEqual(parse_the_saleroom_lot("<html></html>")["outcome"], "unrecognized")

    def test_result_is_read_after_the_sale_and_recorded_once(self):
        run = lambda now, lots=None: run_market_monitor(
            self.config, self.out, fetch=fetcher(lots=lots), now=now)
        first = run("2026-10-04T06:00:00Z")          # learns the sale time
        self.assertEqual(first["result_checks"][0]["outcome"], "pending")
        early = run("2026-10-04T13:00:00Z")          # before sale + 6 hours
        self.assertEqual(early["result_checks"], [])
        sold = {LOT_URL: (200, lot_page("true", "600"), None)}
        after = run("2026-10-04T19:00:00Z", sold)
        self.assertEqual(after["results_recorded"], 1)
        self.assertEqual(run("2026-10-06T06:00:00Z", sold)["result_checks"], [])
        lead = monitor_leads(self.out)[0]
        self.assertEqual((lead["result"]["outcome"], lead["result"]["hammer_text"]), ("sold", "600 GBP"))
        record = json.loads(next((self.out / "results").glob("*.jsonl")).read_text())
        self.assertIn("excludes buyer's premium", record["price_basis"])

    def test_redirect_to_an_excluded_archive_is_not_followed(self):
        archive = "https://www.the-saleroom.com/en-gb/archivelot/" + LOT
        robots = (200, b"User-agent: *\nDisallow: */archivelot*\n")
        fetch = fetcher(robots=robots, lots={LOT_URL: (301, b"", archive)})
        receipt = run_market_monitor(self.config, self.out, fetch=fetch, now="2026-10-05T06:00:00Z")
        self.assertEqual(receipt["result_checks"][0]["outcome"], "unavailable")
        self.assertNotIn(archive, fetch.calls)

    def test_a_result_never_shown_stops_after_the_schedule(self):
        for now in ["2026-10-04T06:00:00Z", "2026-10-04T19:00:00Z", "2026-10-05T13:00:00Z",
                    "2026-10-07T13:00:00Z", "2026-10-11T13:00:00Z", "2026-10-18T13:00:00Z"]:
            receipt = run_market_monitor(self.config, self.out, fetch=fetcher(), now=now)
        self.assertEqual(receipt["result_checks"][0]["outcome"], "not_shown")
        later = run_market_monitor(self.config, self.out, fetch=fetcher(), now="2026-11-01T06:00:00Z")
        self.assertEqual(later["result_checks"], [])

    def test_kill_switch_and_registry_guard(self):
        self.out.mkdir(); (self.out / "DISABLED").touch()
        with self.assertRaises(RuntimeError):
            run_market_monitor(self.config, self.out, fetch=fetcher())
        bad = self.root / "bad.json"; bad.write_text(json.dumps({"schema_version": 1}))
        with self.assertRaises(ValueError):
            run_market_monitor(bad, self.root / "other", fetch=fetcher())


if __name__ == "__main__":
    unittest.main()
