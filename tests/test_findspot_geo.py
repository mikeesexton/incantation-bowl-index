import json
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "research/geo"
DB = ROOT / "data/private/ibi.sqlite3"

TIERS = {"excavation_stratified", "excavation_reported", "site_reported",
         "acquisition_site", "region_only", "unlocated"}


def load(name):
    return json.loads((GEO / name).read_text())


class GazetteerTests(unittest.TestCase):
    """The gazetteer is reference data held beside the corpus, not inside it.
    These tests keep it honest: every mapping resolves, and no coordinate drifts."""

    def setUp(self):
        self.gaz = load("findspot_gazetteer.json")
        self.norm = load("findspot_normalization.json")

    def test_every_mapping_resolves_to_a_known_place(self):
        known = set(self.gaz["places"]) | set(self.gaz["unlocated"]) | set(self.gaz["regions"])
        for m in self.norm["mappings"]:
            for key in m["places"]:
                self.assertIn(key, known, f"{m['value']!r} points at unknown place {key!r}")

    def test_every_mapping_declares_a_documented_tier(self):
        documented = set(self.gaz["tiers"]) | {"region_only"}
        for m in self.norm["mappings"]:
            self.assertIn(m["tier"], TIERS)
            self.assertIn(m["tier"], documented, f"{m['tier']!r} is undocumented")

    def test_mapping_values_are_unique(self):
        values = [m["value"] for m in self.norm["mappings"]]
        self.assertEqual(len(values), len(set(values)))

    def test_no_place_is_defined_twice(self):
        groups = [set(self.gaz[k]) for k in ("places", "unlocated", "regions")]
        for i, a in enumerate(groups):
            for b in groups[i + 1:]:
                self.assertEqual(a & b, set())

    def test_located_places_carry_plausible_coordinates(self):
        for key, p in self.gaz["places"].items():
            self.assertIsInstance(p["lat"], (int, float), key)
            self.assertIsInstance(p["lon"], (int, float), key)
            self.assertTrue(-90 <= p["lat"] <= 90, key)
            self.assertTrue(-180 <= p["lon"] <= 180, key)

    def test_regions_and_unlocated_places_carry_no_coordinates(self):
        for group in ("regions", "unlocated"):
            for key, p in self.gaz[group].items():
                self.assertNotIn("lat", p, f"{key} must not be given a point")
                self.assertNotIn("lon", p, f"{key} must not be given a point")

    def test_region_and_unlocated_strings_never_claim_a_site_tier(self):
        loose = set(self.gaz["regions"]) | set(self.gaz["unlocated"])
        site_tiers = {"excavation_stratified", "excavation_reported",
                      "site_reported", "acquisition_site"}
        for m in self.norm["mappings"]:
            if set(m["places"]) & loose:
                self.assertNotIn(m["tier"], site_tiers, m["value"])


class CorpusParityTests(unittest.TestCase):
    """The mapping must cover the working corpus exactly, in both directions.
    Skipped where the untracked database is absent or cannot be read."""

    def setUp(self):
        if not DB.exists():
            self.skipTest("working database not present")
        # The corpus runs in WAL mode, where a plain mode=ro connection has to
        # create the -shm file and cannot, so it fails whenever the last writer
        # closed cleanly and removed it. immutable=1 reads the file directly and
        # skips the WAL machinery, which is what this snapshot check wants. The
        # skip below stays as a guard: the open error surfaces on first query.
        try:
            con = sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
            self.addCleanup(con.close)
            self.corpus = {r[0] for r in con.execute(
                "select distinct value_text from claims where field='findspot'")}
        except sqlite3.OperationalError as exc:
            self.skipTest(f"database not readable read-only: {exc}")
        self.mapped = {m["value"] for m in load("findspot_normalization.json")["mappings"]}

    def test_no_findspot_string_is_unmapped(self):
        self.assertEqual(self.corpus - self.mapped, set())

    def test_no_mapping_is_orphaned(self):
        self.assertEqual(self.mapped - self.corpus, set())


if __name__ == "__main__":
    unittest.main()
