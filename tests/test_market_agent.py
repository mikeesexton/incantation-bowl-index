import json
import tempfile
import unittest
from pathlib import Path

from bowl_index.market_agent import collect, finish
from bowl_index.market_monitor import monitor_leads


class MarketAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.agent = self.root / "market-agent"
        self.monitor = self.root / "market"
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({"schema_version": 1, "limits": "first page only",
            "pages": [{"id": "dealer", "url": "https://example.org/category"}]}))
        self.settings = {"user_agent": "test", "timeout_seconds": 2,
                         "max_response_bytes": 10000, "delay_seconds": 0}

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, now="2026-10-05T00:00:00Z", robots=b"User-agent: *\nAllow: /\n"):
        self.calls = []
        def fetch(url, *args):
            self.calls.append(url)
            return (200, robots if url.endswith("robots.txt") else
                    b'<a href="/item/123">Aramaic incantation bowl</a> GBP 400', None)
        return collect(self.config, self.agent, self.settings, fetch=fetch,
                       sleep=lambda seconds: None, now=now)

    def candidate(self, receipt, estimate="GBP 400"):
        return {"url": "https://example.org/item/123", "title": "Aramaic incantation bowl",
                "house": "Dealer", "lot_number": "123", "estimate": estimate,
                "locator": "item 123 link", "evidence_sha256": receipt["requests"][0]["sha256"]}

    def test_fresh_robots_denial_never_requests_category(self):
        result = self.capture(robots=b"User-agent: *\nDisallow: /\n")
        self.assertEqual(self.calls, ["https://example.org/robots.txt"])
        self.assertEqual(result["requests"][0]["disposition"], "robots_disallowed")

    def test_newsletter_form_captcha_does_not_hide_readable_catalogue(self):
        def fetch(url, *args):
            return (200, b"User-agent: *\nAllow: /\n", None) if url.endswith("robots.txt") else (
                200, b'<h1>Catalogue</h1><form class="elementor-g-recaptcha">Newsletter</form>', None)
        result = collect(self.config, self.agent, self.settings, fetch=fetch,
                         sleep=lambda seconds: None, now="2026-10-05T00:00:00Z")
        self.assertEqual(result["requests"][0]["disposition"], "collected")

    def test_redirect_and_challenge_are_not_extraction_evidence(self):
        for status, body, location in ((302, b"", "https://blocked.example/"),
                                       (200, b"verify you are human", None)):
            calls = []
            def fetch(url, *args):
                calls.append(url)
                return (404, b"not found", None) if url.endswith("robots.txt") else (status, body, location)
            out = self.agent / str(status)
            result = collect(self.config, out, self.settings, fetch=fetch,
                             sleep=lambda seconds: None, now="2026-10-05T00:00:00Z")
            self.assertEqual(len(calls), 2)
            self.assertNotEqual(result["requests"][0]["disposition"], "collected")
            with self.assertRaises(ValueError):
                finish(result["collection"], [{"url": "https://example.org/item/123",
                       "evidence_sha256": result["requests"][0].get("sha256")}], out, self.monitor)

    def test_new_lead_replay_and_later_price_change_retain_history(self):
        receipt = self.capture()
        candidate = self.candidate(receipt)
        result = finish(receipt["collection"], [candidate], self.agent, self.monitor)
        self.assertEqual(len(result["new_leads"]), 1)
        self.assertEqual(finish(receipt["collection"], [candidate], self.agent, self.monitor), result)
        later = self.capture(now="2026-10-05T06:00:00Z")
        changed = finish(later["collection"], [self.candidate(later, "GBP 500")],
                         self.agent, self.monitor)
        self.assertEqual(changed["new_leads"], [])
        self.assertEqual(changed["changes"][0]["previous"]["estimate"], "GBP 400")
        self.assertEqual(monitor_leads(self.monitor)[0]["estimate"], "GBP 500")
        original = next((self.agent / "leads").glob("*.jsonl"))
        self.assertEqual(json.loads(original.read_text())["estimate"], "GBP 400")
        with self.assertRaises(ValueError):
            finish(receipt["collection"], [self.candidate(receipt, "GBP 999")], self.agent, self.monitor)

    def test_whole_submission_validation_and_hash_tamper(self):
        receipt = self.capture()
        good = self.candidate(receipt)
        bad = {**good, "url": "https://uncollected.example/item"}
        with self.assertRaises(ValueError):
            finish(receipt["collection"], [good, bad], self.agent, self.monitor)
        self.assertFalse((self.agent / "leads").exists())
        Path(receipt["requests"][0]["path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            finish(receipt["collection"], [good], self.agent, self.monitor)

    def test_email_intake_and_kill_switch(self):
        inbox = self.agent / "evidence/inbox"
        inbox.mkdir(parents=True)
        (inbox / "alert.eml").write_bytes(b"Subject: Incantation bowl\n\nGBP 400\n")
        receipt = self.capture()
        candidate = self.candidate(receipt)
        candidate["url"] = "https://invaluable.com/lot/123"
        candidate["evidence_sha256"] = receipt["emails"][0]["sha256"]
        result = finish(receipt["collection"], [candidate], self.agent, self.monitor)
        self.assertEqual(result["new_leads"][0]["channel"], "alert_email")
        (self.agent / "DISABLED").touch()
        with self.assertRaises(RuntimeError):
            self.capture(now="2026-10-06T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
