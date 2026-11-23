import csv
import tempfile
import unittest
from pathlib import Path

from src.audit_race_integrity import audit_file


class RaceIntegrityAuditTests(unittest.TestCase):
    def test_counts_winners_and_includes_anomaly_examples(self):
        fields = ["date", "country", "course", "off_time", "race_id",
                  "preparation_decision", "research_win_outcome", "horse",
                  "finish_position", "source_finish_code"]
        rows = [
            ["2026-01-01", "GB", "A", "12:00", "1", "RESEARCH_ONLY", "0", "Horse A", "2", "2"],
            ["2026-01-01", "GB", "A", "12:00", "1", "RESEARCH_ONLY", "1", "Horse B", "1", "1"],
            ["2026-01-01", "GB", "B", "13:00", "2", "RESEARCH_ONLY", "0", "Horse C", "2", "2"],
            ["2026-01-01", "GB", "B", "13:00", "2", "RESEARCH_ONLY", "0", "Horse D", "3", "3"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "RESEARCH_ONLY", "1", "Horse E", "1", "1"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "RESEARCH_ONLY", "1", "Horse F", "1", "1"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "QUARANTINE", "", "Horse G", "NR", "NR"],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prepared.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            result = audit_file(path)
        summary = result["summary"]
        self.assertEqual(summary["race_groups"], 3)
        self.assertEqual(summary["research_only_runners"], 6)
        self.assertEqual(summary["races_with_no_recorded_winner"], 1)
        self.assertEqual(summary["races_with_one_recorded_winner"], 1)
        self.assertEqual(summary["races_with_multiple_recorded_winners_dead_heat_or_anomaly"], 1)
        self.assertEqual(summary["largest_race_group"], 2)
        self.assertEqual(result["winner_count_distribution"], {"0": 1, "1": 1, "2": 1})
        self.assertEqual(len(result["anomaly_examples_max_30"]), 2)
        self.assertEqual(result["anomaly_examples_max_30"][0]["recorded_winner_count"], 2)
        self.assertEqual(result["anomaly_examples_max_30"][0]["runners"][0]["horse"], "Horse E")


if __name__ == "__main__":
    unittest.main()
