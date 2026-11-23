import csv
import tempfile
import unittest
from pathlib import Path

from src.audit_race_integrity import audit_file


class RaceIntegrityAuditTests(unittest.TestCase):
    def test_counts_no_winner_single_winner_and_dead_heat_races(self):
        fields = ["date", "country", "course", "off_time", "race_id",
                  "preparation_decision", "research_win_outcome"]
        rows = [
            ["2026-01-01", "GB", "A", "12:00", "1", "RESEARCH_ONLY", "0"],
            ["2026-01-01", "GB", "A", "12:00", "1", "RESEARCH_ONLY", "1"],
            ["2026-01-01", "GB", "B", "13:00", "2", "RESEARCH_ONLY", "0"],
            ["2026-01-01", "GB", "B", "13:00", "2", "RESEARCH_ONLY", "0"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "RESEARCH_ONLY", "1"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "RESEARCH_ONLY", "1"],
            ["2026-01-01", "IRE", "C", "14:00", "3", "QUARANTINE", ""],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prepared.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            result = audit_file(path)
        self.assertEqual(result["race_groups"], 3)
        self.assertEqual(result["research_only_runners"], 6)
        self.assertEqual(result["races_with_no_recorded_winner"], 1)
        self.assertEqual(result["races_with_one_recorded_winner"], 1)
        self.assertEqual(result["races_with_multiple_recorded_winners_dead_heat_or_anomaly"], 1)
        self.assertEqual(result["largest_race_group"], 2)


if __name__ == "__main__":
    unittest.main()
