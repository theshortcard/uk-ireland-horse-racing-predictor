"""Convert one permitted The Racing API free snapshot into predictor CSV rows.

This adapter is deliberately conservative: it includes only declared races,
excludes explicit NR/N/R and reserve-number entries, and never invents odds.
Keep raw snapshots only as permitted by the provider's terms.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SOURCE_NAME = "The Racing API free racecards"
RACE_TIMEZONE = ZoneInfo("Europe/London")
OUTPUT_COLUMNS = [
    "race_id", "date", "course", "country", "off_time", "horse",
    "horse_age", "official_rating", "days_since_run", "odds_decimal",
    "odds_source", "odds_captured_at", "source_name", "retrieved_at",
]


def _local_off_time(race: dict[str, Any]) -> str:
    raw = str(race.get("off_dt", "")).strip()
    if not raw:
        raise ValueError("race is missing off_dt; refusing ambiguous off_time conversion")
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("race off_dt must include a timezone offset")
    return parsed.astimezone(RACE_TIMEZONE).strftime("%H:%M")


def convert_payload(
    payload: dict[str, Any], metadata: dict[str, Any]
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Return normalized active-runner CSV rows and import counts."""
    races = payload.get("racecards")
    if not isinstance(races, list):
        raise ValueError("Snapshot must contain a 'racecards' list.")

    retrieved_at = str(metadata.get("retrieved_at", "")).strip()
    if not retrieved_at:
        raise ValueError("Metadata must contain retrieved_at.")
    captured = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("Metadata retrieved_at must include a timezone offset")

    rows: list[dict[str, str]] = []
    counts = {
        "races_seen": len(races),
        "races_skipped_not_declared": 0,
        "races_skipped_unknown_region": 0,
        "races_included": 0,
        "runner_objects_seen": 0,
        "non_runners_excluded": 0,
        "reserves_excluded": 0,
        "runners_included": 0,
    }

    for race in races:
        if str(race.get("race_status", "")).strip().lower() != "declared":
            counts["races_skipped_not_declared"] += 1
            continue

        region = str(race.get("region", "")).strip().upper()
        if region not in {"GB", "IRE"}:
            counts["races_skipped_unknown_region"] += 1
            continue

        off_time = _local_off_time(race)
        counts["races_included"] += 1
        runners = race.get("runners")
        if not isinstance(runners, list):
            runners = []

        for runner in runners:
            counts["runner_objects_seen"] += 1
            if not isinstance(runner, dict):
                continue
            number = str(runner.get("number", "")).strip().upper()
            if number in {"NR", "N/R"}:
                counts["non_runners_excluded"] += 1
                continue
            if number.startswith("R"):
                counts["reserves_excluded"] += 1
                continue

            horse = str(runner.get("horse", "")).strip()
            if not horse:
                continue

            last_run = str(runner.get("last_run", "")).strip()
            age = str(runner.get("age", "")).strip()
            rating = str(runner.get("ofr", "")).strip()
            rows.append({
                "race_id": str(race.get("race_id", "")).strip(),
                "date": str(race.get("date", "")).strip(),
                "course": str(race.get("course", "")).strip(),
                "country": region,
                "off_time": off_time,
                "horse": horse,
                "horse_age": age,
                "official_rating": rating,
                "days_since_run": last_run,
                "odds_decimal": "",
                "odds_source": "",
                "odds_captured_at": "",
                "source_name": SOURCE_NAME,
                "retrieved_at": retrieved_at,
            })
            counts["runners_included"] += 1

    return rows, counts


def write_csv(rows: list[dict[str, str]], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert one raw Racing API free racecard snapshot to predictor CSV."
    )
    parser.add_argument("--snapshot", required=True, help="Raw racecards JSON snapshot")
    parser.add_argument("--metadata", required=True, help="Matching credential-free metadata JSON")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    payload = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    rows, counts = convert_payload(payload, metadata)
    write_csv(rows, args.output)

    print(json.dumps(counts, indent=2))
    print(f"Wrote {len(rows)} active runner rows to {args.output}")
    print("Odds were left blank; no market edge or EV can be calculated.")
    print("Only declared races were included; NR/N/R and reserve entries were excluded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
