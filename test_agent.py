import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
import agent

def candles(count=200):
    return [[i * agent.HOUR, "100", "102", "99", "101", "1", (i+1)*agent.HOUR-1, "1000", 20]
            for i in range(count)]

class Calculations(unittest.TestCase):
    def test_closed_hour_and_seven_day_baseline(self):
        raw = candles(201)
        raw[199][4], raw[199][7] = "102", "2000"
        raw[200][4], raw[200][7] = "999999", "999999"
        r = agent.summarise("BTCUSDT", raw, 200*agent.HOUR)
        self.assertEqual(r["close"], 102)
        self.assertAlmostEqual(r["change_1h"], 2)
        self.assertAlmostEqual(r["change_24h"], (102/101-1)*100)
        self.assertEqual(r["volume_ratio"], 2)
        self.assertEqual(r["range_1h"], 3)
        self.assertEqual(r["range_ratio"], 1)
        self.assertEqual(len(r["closes"]), 24)

    def test_stale_gap_duplicates_and_invalid_prices_rejected(self):
        cases = [candles(199), candles()]
        cases[1].pop(170)
        duplicate = candles(); duplicate[190] = copy.deepcopy(duplicate[189]); cases.append(duplicate)
        invalid = candles(); invalid[-1][2] = "90"; cases.append(invalid)
        nan = candles(); nan[-1][4] = "NaN"; cases.append(nan)
        for raw in cases:
            with self.subTest(timestamp=raw[-1][0]), self.assertRaises(ValueError):
                agent.summarise("BTCUSDT", raw, 200*agent.HOUR)

    def test_zero_volume_is_unavailable(self):
        raw = candles()
        for row in raw: row[7] = "0"
        self.assertIsNone(agent.summarise("BTCUSDT", raw, 200*agent.HOUR)["volume_ratio"])

    def test_capability_and_symbol_validation(self):
        agent.assert_safe(agent.DEFAULT_CONFIG)
        for change in ({"allow_wallet_access": True}, {"allow_public_posting": "false"},
                       {"mode": "trading"}, {"symbols": []}, {"symbols": ["BTCUSDT", "BTCUSDT"]},
                       {"symbols": ["../escape"]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                agent.assert_safe(agent.DEFAULT_CONFIG | change)

class Pipeline(unittest.TestCase):
    def fresh(self, cutoff):
        raw = candles(); offset = cutoff - len(raw)*agent.HOUR
        for row in raw: row[0] += offset; row[6] += offset
        return raw

    def test_partial_coverage_marked_and_raw_data_saved(self):
        cutoff = int(agent.datetime.now(agent.UTC).timestamp()*1000)//agent.HOUR*agent.HOUR
        with tempfile.TemporaryDirectory() as folder, patch.object(agent, "get_json", side_effect=[
                self.fresh(cutoff), URLError("offline"), self.fresh(cutoff)]):
            root = Path(folder); r = agent.generate(root)
            page = (root/"site/index.html").read_text(encoding="utf-8")
            self.assertEqual(len(r["assets"]), 2)
            self.assertIn("ETHUSDT", r["errors"])
            self.assertIn("Partial coverage", page)
            self.assertNotIn("{{", page)
            self.assertTrue((root/r["raw_file"]).exists())

    def test_total_failure_preserves_previous_latest(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(agent, "get_json", side_effect=URLError("offline")):
            root=Path(folder); (root/"site").mkdir(); (root/"site/index.html").write_text("previous")
            with self.assertRaises(RuntimeError): agent.generate(root)
            self.assertEqual((root/"site/index.html").read_text(), "previous")
            log=json.loads((root/"state/activity.jsonl").read_text())
            self.assertEqual(log["action"], "fetch_failed")

if __name__ == "__main__": unittest.main()
