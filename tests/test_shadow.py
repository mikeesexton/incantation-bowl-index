import json
import tempfile
import unittest
from pathlib import Path

from bowl_index.shadow import normalized_body, run_shadow


class ShadowMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "config.json"
        self.destination = self.root / "monitoring"
        self.config.write_text(json.dumps({
            "schema_version": 1,
            "shadow_only": True,
            "settings": {
                "user_agent": "test",
                "timeout_seconds": 1,
                "retry_count": 0,
                "max_response_bytes": 1000,
                "delay_seconds": 0,
            },
            "sources": [{
                "id": "example",
                "enabled": True,
                "lead_priority": 3,
                "requests": [{
                    "id": "metadata",
                    "url": "https://example.test/metadata",
                    "ignore_json_paths": ["meta.elapsed"],
                }],
            }],
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def fetch(body):
        def fake(_request, _agent, _timeout, _retries, _max_bytes, _sleep):
            return 200, {"content-type": "application/json"}, body
        return fake

    def test_baseline_repeat_and_change_create_only_change_lead(self):
        first = run_shadow(
            self.config, self.destination,
            fetcher=self.fetch(b'{"meta":{"elapsed":1},"items":[1]}'),
            now="2026-09-26T12:00:00Z",
        )
        self.assertEqual(first["summary"]["baseline"], 1)
        self.assertEqual(first["corpus_writes"], 0)
        self.assertFalse((self.destination / "leads").exists())

        second = run_shadow(
            self.config, self.destination,
            fetcher=self.fetch(b'{"meta":{"elapsed":9},"items":[1]}'),
            now="2026-09-26T13:00:00Z",
        )
        self.assertEqual(second["summary"]["unchanged"], 1)

        third = run_shadow(
            self.config, self.destination,
            fetcher=self.fetch(b'{"meta":{"elapsed":2},"items":[1,2]}'),
            now="2026-09-26T14:00:00Z",
        )
        self.assertEqual(third["summary"]["changed"], 1)
        lead_path = self.destination / "leads" / "20260926T140000Z.jsonl"
        lead = json.loads(lead_path.read_text(encoding="utf-8"))
        self.assertEqual(lead["source_monitor_id"], "example")
        self.assertIn("no corpus manifest", lead["automation_boundary"])

    def test_disable_switch_prevents_fetch(self):
        self.destination.mkdir(parents=True)
        (self.destination / "DISABLED").write_text("disabled\n")
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            run_shadow(self.config, self.destination, fetcher=self.fetch(b"{}"))

    def test_registry_change_starts_a_new_baseline_without_a_false_lead(self):
        run_shadow(
            self.config, self.destination, fetcher=self.fetch(b'{"items":[1]}'),
            now="2026-09-26T12:00:00Z",
        )
        value = json.loads(self.config.read_text(encoding="utf-8"))
        value["sources"][0]["requests"][0]["ignore_json_paths"].append("meta.other")
        self.config.write_text(json.dumps(value), encoding="utf-8")
        result = run_shadow(
            self.config, self.destination, fetcher=self.fetch(b'{"items":[2]}'),
            now="2026-09-26T13:00:00Z",
        )
        self.assertTrue(result["registry_changed"])
        self.assertEqual(result["summary"]["baseline"], 1)
        self.assertFalse((self.destination / "leads").exists())

    def test_json_normalization_ignores_only_declared_path(self):
        first = normalized_body(
            b'{"meta":{"elapsed":1},"items":[1]}', "application/json", ["meta.elapsed"]
        )
        second = normalized_body(
            b'{"items":[1],"meta":{"elapsed":999}}', "application/json", ["meta.elapsed"]
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
