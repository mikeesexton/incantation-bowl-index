import unittest
from bowl_index.robots import can_fetch

UA = "IncantationBowlIndexResearch/0.2 (+noncommercial scholarly monitoring; metadata only)"
SALEROOM = """User-agent: *
Disallow: */my-account*
Disallow: */archivelot*
Disallow: */*?pgSearchTerm*
Disallow: */en-us*
"""


class RobotsTests(unittest.TestCase):
    """Wildcards must match; urllib.robotparser treats them literally."""
    def test_wildcard_rules_match(self):
        self.assertFalse(can_fetch(SALEROOM, UA, "https://x.com/en-gb/archivelot/abc"))
        self.assertFalse(can_fetch(SALEROOM, UA, "https://x.com/en-us/lot"))
        self.assertFalse(can_fetch(SALEROOM, UA, "https://x.com/en-gb/search?pgSearchTerm=a"))
        self.assertTrue(can_fetch(SALEROOM, UA, "https://x.com/en-gb/search-results?searchTerm=a"))

    def test_longest_match_wins_and_allow_breaks_ties(self):
        rules = "User-agent: *\nDisallow: /search\nAllow: /search/public\nAllow: /a\nDisallow: /a\n"
        self.assertTrue(can_fetch(rules, UA, "https://x.com/search/public?q=1"))
        self.assertFalse(can_fetch(rules, UA, "https://x.com/search?q=1"))
        self.assertTrue(can_fetch(rules, UA, "https://x.com/a"))

    def test_end_anchor_and_specific_agent_group(self):
        rules = ("User-agent: *\nDisallow: /*.pdf$\n\n"
                 "User-agent: IncantationBowlIndexResearch\nDisallow: /\n")
        self.assertFalse(can_fetch(rules, UA, "https://x.com/page"))
        self.assertTrue(can_fetch(rules, "OtherBot/1.0", "https://x.com/file.pdf?x=1"))
        self.assertFalse(can_fetch(rules, "OtherBot/1.0", "https://x.com/file.pdf"))
        self.assertTrue(can_fetch("User-agent: *\nDisallow:\n", UA, "https://x.com/anything"))


if __name__ == "__main__":
    unittest.main()
