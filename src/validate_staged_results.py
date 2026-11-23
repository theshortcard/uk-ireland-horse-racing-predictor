"""Audit staged historical runner records without modifying or certifying them.

Uses a temporary SQLite index so duplicate and race-level checks remain bounded
in memory for multi-million-row CSV files. All findings are diagnostic only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

REQUIRED = {
    "race_id", "date", "course", "country", "off_time", "horse",
    "horse_age", "official_rating", "finish_position", "result_status",
}
NON_FINISH_CODES = {
    "PU", "UR", "F", "BD", "RO", "SU", "REF", "DSQ", "CO", "L",
    "RR", "VOID", "NR", "B", "U", "S",
}


def valid_time(value: str) -> bool:
    return bool(re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value.strip()))


def valid_nonnegative_number(value: str) -> bool:
    if not value.strip():
        return False
    try:
        number = float(value)
        return number >= 0 and number != float("inf") and number == number
    except ValueError:
        return False


def audit_file(input_path: Path) -> dict:
    counts: Counter = Counter()
    countries: Counter = Counter()
    finish_codes: Counter = Counter()
    min_date = max_date = None

    with tempfile.TemporaryDirectory(prefix="racing-audit-") as temp_dir:
        db = sqlite3.connect(str(Path(temp_dir) / "audit.sqlite"))
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("""
            CREATE TABLE runners (
                race_key TEXT NOT NULL,
                horse_key TEXT NOT NULL,
                PRIMARY KEY (race_key, horse_key)
            )
        """)
        db.execute("""
            CREATE TABLE races (
                race_key TEXT PRIMARY KEY,
                runner_count INTEGER NOT NULL,
                max_finish INTEGER NOT NULL
            )
        """)

        with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV has no header")
            missing = REQUIRED - set(reader.fieldnames)
            if missing:
                raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

            for row in reader:
                counts["rows"] += 1
                race_id = (row.get("race_id") or "").strip()
                course = (row.get("course") or "").strip()
                country = (row.get("country") or "").strip().upper()
                off_time = (row.get("off_time") or "").strip()
                horse = (row.get("horse") or "").strip()
                race_date = (row.get("date") or "").strip()
                if not race_id or not course or not horse:
                    counts["missing_race_identity_fields"] += 1
                    continue
                if country not in {"GB", "IRE"}:
                    counts["invalid_country"] += 1
                countries[country or "MISSING"] += 1

                try:
                    parsed_date = date.fromisoformat(race_date)
                    min_date = parsed_date if min_date is None else min(min_date, parsed_date)
                    max_date = parsed_date if max_date is None else max(max_date, parsed_date)
                except ValueError:
                    counts["invalid_date"] += 1

                if not valid_time(off_time):
                    counts["invalid_off_time"] += 1

                age = (row.get("horse_age") or "").strip()
                rating = (row.get("official_rating") or "").strip()
                if not age:
                    counts["missing_horse_age"] += 1
                elif not valid_nonnegative_number(age) or float(age) <= 0:
                    counts["invalid_horse_age"] += 1
                if not rating:
                    counts["missing_official_rating"] += 1
                elif not valid_nonnegative_number(rating):
                    counts["invalid_official_rating"] += 1

                position = (row.get("finish_position") or "").strip()
                numeric_position = 0
                if position:
                    try:
                        numeric_position = int(position)
                        if numeric_position <= 0:
                            counts["invalid_finish_position"] += 1
                            numeric_position = 0
                    except ValueError:
                        counts["invalid_finish_position"] += 1
                else:
                    code = (row.get("source_finish_code") or "").strip().upper()
                    if code:
                        finish_codes[code] += 1
                        if code not in NON_FINISH_CODES:
                            counts["unrecognised_finish_code"] += 1
                    else:
                        counts["missing_finish_outcome"] += 1

                race_key = "|".join((race_date, country, course.casefold(), off_time, race_id))
                horse_key = " ".join(horse.casefold().split())
                cursor = db.execute(
                    "INSERT OR IGNORE INTO runners(race_key, horse_key) VALUES (?, ?)",
                    (race_key, horse_key),
                )
                if cursor.rowcount == 0:
                    counts["duplicate_runner_rows"] += 1
                db.execute("""
                    INSERT INTO races(race_key, runner_count, max_finish)
                    VALUES (?, 1, ?)
                    ON CONFLICT(race_key) DO UPDATE SET
                        runner_count = runner_count + 1,
                        max_finish = MAX(max_finish, excluded.max_finish)
                """, (race_key, numeric_position))

                if counts["rows"] % 100000 == 0:
                    db.commit()

        db.commit()
        counts["race_groups"] = db.execute("SELECT COUNT(*) FROM races").fetchone()[0]
        counts["races_with_one_runner"] = db.execute(
            "SELECT COUNT(*) FROM races WHERE runner_count = 1"
        ).fetchone()[0]
        counts["races_with_more_than_40_rows"] = db.execute(
            "SELECT COUNT(*) FROM races WHERE runner_count > 40"
        ).fetchone()[0]
        counts["finish_positions_above_field_size"] = db.execute(
            "SELECT COUNT(*) FROM races WHERE max_finish > runner_count"
        ).fetchone()[0]
        db.close()

    return {
        "input": str(input_path),
        "counts": dict(counts),
        "countries": dict(countries),
        "finish_codes": dict(finish_codes.most_common(20)),
        "date_range": [
            min_date.isoformat() if min_date else None,
            max_date.isoformat() if max_date else None,
        ],
        "note": "Diagnostic only. Does not verify source rights, result accuracy, or pre-race odds.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit staged UK/IRE runner records.")
    parser.add_argument("--input", required=True, help="Staged CSV to audit")
    parser.add_argument("--output", default="", help="Optional JSON report path")
    args = parser.parse_args()
    path = Path(args.input)
    if not path.is_file():
        parser.error(f"Input file not found: {path}")
    try:
        report = audit_file(path)
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Audit report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
