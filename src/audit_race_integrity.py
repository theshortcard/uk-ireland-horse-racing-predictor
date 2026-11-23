"""Summarise race-level winner integrity in a research-only CSV.

This is diagnostic only: it does not verify results or certify source completeness.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import tempfile
from pathlib import Path

KEY_FIELDS = ("date", "country", "course", "off_time", "race_id")
REQUIRED = set(KEY_FIELDS) | {"research_win_outcome"}


def audit_file(input_path: Path) -> dict[str, int]:
    with tempfile.TemporaryDirectory(prefix="race-integrity-") as temp_dir:
        db = sqlite3.connect(str(Path(temp_dir) / "races.sqlite"))
        db.execute("""
            CREATE TABLE races (
                race_key TEXT PRIMARY KEY,
                runners INTEGER NOT NULL,
                winners INTEGER NOT NULL
            )
        """)
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("Input CSV has no header")
            missing = REQUIRED - set(reader.fieldnames)
            if missing:
                raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
            for row in reader:
                if (row.get("preparation_decision") or "").strip() != "RESEARCH_ONLY":
                    continue
                key = "\x1f".join((row.get(name) or "").strip().casefold() for name in KEY_FIELDS)
                if not all((row.get(name) or "").strip() for name in KEY_FIELDS):
                    continue
                winner = 1 if (row.get("research_win_outcome") or "").strip() == "1" else 0
                db.execute("""
                    INSERT INTO races(race_key, runners, winners) VALUES (?, 1, ?)
                    ON CONFLICT(race_key) DO UPDATE SET
                        runners = runners + 1,
                        winners = winners + excluded.winners
                """, (key, winner))
        row = db.execute("""
            SELECT COUNT(*), COALESCE(SUM(runners), 0),
                   COALESCE(SUM(CASE WHEN winners = 0 THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN winners = 1 THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN winners > 1 THEN 1 ELSE 0 END), 0),
                   COALESCE(MAX(runners), 0)
            FROM races
        """).fetchone()
        db.close()
    return {
        "race_groups": row[0],
        "research_only_runners": row[1],
        "races_with_no_recorded_winner": row[2],
        "races_with_one_recorded_winner": row[3],
        "races_with_multiple_recorded_winners_dead_heat_or_anomaly": row[4],
        "largest_race_group": row[5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit race-level winner counts in a research-only CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.input)
    if not source.is_file():
        parser.error(f"Input file not found: {source}")
    try:
        summary = audit_file(source)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print("Race-level integrity audit (diagnostic only; results remain UNVERIFIED):")
    for key, value in summary.items():
        print(f"{key}: {value:,}")
    print(f"Audit JSON: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
