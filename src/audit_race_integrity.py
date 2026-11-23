"""Summarise race-level winner integrity in a research-only CSV.

This is diagnostic only: it does not verify results or certify source completeness.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path

KEY_FIELDS = ("date", "country", "course", "off_time", "race_id")
REQUIRED = set(KEY_FIELDS) | {"research_win_outcome", "horse", "finish_position", "source_finish_code"}


def audit_file(input_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="race-integrity-") as temp_dir:
        db = sqlite3.connect(str(Path(temp_dir) / "races.sqlite"))
        db.execute("""
            CREATE TABLE races (
                race_key TEXT PRIMARY KEY,
                date TEXT, country TEXT, course TEXT, off_time TEXT, race_id TEXT,
                runners INTEGER NOT NULL,
                winners INTEGER NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE runner_rows (
                race_key TEXT NOT NULL, horse TEXT, finish_position TEXT,
                source_finish_code TEXT, outcome TEXT
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
                values = [(row.get(name) or "").strip() for name in KEY_FIELDS]
                if not all(values):
                    continue
                key = "\x1f".join(value.casefold() for value in values)
                winner = 1 if (row.get("research_win_outcome") or "").strip() == "1" else 0
                db.execute("""
                    INSERT INTO races(race_key,date,country,course,off_time,race_id,runners,winners)
                    VALUES (?,?,?,?,?,?,1,?)
                    ON CONFLICT(race_key) DO UPDATE SET
                        runners = runners + 1,
                        winners = winners + excluded.winners
                """, (key, *values, winner))
                db.execute(
                    "INSERT INTO runner_rows VALUES (?,?,?,?,?)",
                    (key, row.get("horse", ""), row.get("finish_position", ""),
                     row.get("source_finish_code", ""), row.get("research_win_outcome", "")),
                )
        aggregate = db.execute("""
            SELECT COUNT(*), COALESCE(SUM(runners), 0),
                   COALESCE(SUM(CASE WHEN winners = 0 THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN winners = 1 THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN winners > 1 THEN 1 ELSE 0 END), 0),
                   COALESCE(MAX(runners), 0)
            FROM races
        """).fetchone()
        distribution = {
            str(winners): count for winners, count in db.execute(
                "SELECT winners, COUNT(*) FROM races GROUP BY winners ORDER BY winners"
            )
        }
        anomalies = []
        for race in db.execute("""
            SELECT race_key,date,country,course,off_time,race_id,runners,winners
            FROM races WHERE winners = 0 OR winners > 1
            ORDER BY winners DESC, date, course LIMIT 30
        """):
            race_key, race_date, country, course, off_time, race_id, runners, winners = race
            runner_details = [
                {"horse": horse, "finish_position": position,
                 "source_finish_code": code, "research_win_outcome": outcome}
                for horse, position, code, outcome in db.execute(
                    "SELECT horse,finish_position,source_finish_code,outcome FROM runner_rows WHERE race_key=? LIMIT 50",
                    (race_key,),
                )
            ]
            anomalies.append({
                "date": race_date, "country": country, "course": course,
                "off_time": off_time, "race_id": race_id,
                "runner_count": runners, "recorded_winner_count": winners,
                "runners": runner_details,
            })
        db.close()
    return {
        "summary": {
            "race_groups": aggregate[0],
            "research_only_runners": aggregate[1],
            "races_with_no_recorded_winner": aggregate[2],
            "races_with_one_recorded_winner": aggregate[3],
            "races_with_multiple_recorded_winners_dead_heat_or_anomaly": aggregate[4],
            "largest_race_group": aggregate[5],
        },
        "winner_count_distribution": distribution,
        "anomaly_examples_max_30": anomalies,
        "note": "Multiple winners may be legitimate dead heats. All source results remain UNVERIFIED; this report is diagnostic only.",
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
        report = audit_file(source)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print("Race-level integrity audit (diagnostic only; results remain UNVERIFIED):")
    for key, value in report["summary"].items():
        print(f"{key}: {value:,}")
    print("Winner-count distribution: " + json.dumps(report["winner_count_distribution"], sort_keys=True))
    print(f"Anomaly examples recorded: {len(report['anomaly_examples_max_30'])}")
    for example in report["anomaly_examples_max_30"]:
        winners = [runner["horse"] for runner in example["runners"] if runner["research_win_outcome"] == "1"]
        sample = {
            "date": example["date"], "country": example["country"],
            "course": example["course"], "off_time": example["off_time"],
            "race_id": example["race_id"], "runner_count": example["runner_count"],
            "winner_count": example["recorded_winner_count"], "winner_horses": winners,
        }
        print("ANOMALY_SAMPLE: " + json.dumps(sample, ensure_ascii=False))
    print(f"Audit JSON: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
