"""Offline integrity audit for a saved The Racing API free racecard snapshot.

This tool never calls the provider and never treats runner objects as confirmed
starters. It reports race identity/date/region/status and runner-count signals.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    races = payload.get("racecards")
    if not isinstance(races, list):
        raise ValueError("Snapshot must contain a 'racecards' list.")

    ids = [str(r.get("race_id", "")).strip() for r in races]
    missing_ids = sum(not value for value in ids)
    id_counts = Counter(value for value in ids if value)
    dates = Counter(str(r.get("date", "")) for r in races)
    regions = Counter(str(r.get("region", "")).lower() for r in races)
    courses = Counter(str(r.get("course", "")) for r in races)
    statuses = Counter(str(r.get("race_status", "")).lower() for r in races)

    course_time_keys = [
        (str(r.get("date", "")), str(r.get("course", "")).strip().lower(),
         str(r.get("off_time", "")).strip())
        for r in races
    ]
    course_time_counts = Counter(course_time_keys)

    runner_objects = 0
    reserve_runner_objects = 0
    declared_runner_objects = 0
    empty_runner_races = 0
    field_size_sum = 0
    field_size_known = 0
    field_size_mismatches = []
    duplicate_runner_names = []

    for race in races:
        runners = race.get("runners")
        if not isinstance(runners, list):
            runners = []
        runner_objects += len(runners)
        reserves = [
            runner for runner in runners
            if isinstance(runner, dict)
            and str(runner.get("number", "")).strip().upper().startswith("R")
        ]
        active_runners = [runner for runner in runners if runner not in reserves]
        reserve_runner_objects += len(reserves)
        declared_runner_objects += len(active_runners)
        if not runners:
            empty_runner_races += 1

        raw_field_size = race.get("field_size")
        try:
            field_size = int(raw_field_size) if raw_field_size not in (None, "") else None
        except (TypeError, ValueError):
            field_size = None
        if field_size is not None:
            field_size_sum += field_size
            field_size_known += 1
            if field_size != len(active_runners):
                field_size_mismatches.append({
                    "course": race.get("course"),
                    "date": race.get("date"),
                    "off_time": race.get("off_time"),
                    "field_size": field_size,
                    "declared_runner_objects": len(active_runners),
                    "all_runner_objects_including_reserves": len(runners),
                })

        names = [str(x.get("horse", "")).strip().casefold()
                 for x in runners if isinstance(x, dict) and x.get("horse")]
        dupes = sorted(name for name, count in Counter(names).items() if count > 1)
        if dupes:
            duplicate_runner_names.append({
                "course": race.get("course"),
                "off_time": race.get("off_time"),
                "horse_names": dupes,
            })

    return {
        "race_count": len(races),
        "unique_race_ids": len(id_counts),
        "missing_race_ids": missing_ids,
        "duplicate_race_ids": sorted(k for k, v in id_counts.items() if v > 1),
        "duplicate_course_off_time_keys": [
            {"date": k[0], "course": k[1], "off_time": k[2], "count": v}
            for k, v in course_time_counts.items() if v > 1
        ],
        "dates": dict(sorted(dates.items())),
        "regions": dict(sorted(regions.items())),
        "courses": dict(sorted(courses.items())),
        "race_statuses": dict(sorted(statuses.items())),
        "runner_objects": runner_objects,
        "declared_runner_objects_excluding_reserves": declared_runner_objects,
        "reserve_runner_objects": reserve_runner_objects,
        "empty_runner_races": empty_runner_races,
        "field_size_sum": field_size_sum,
        "field_size_known_races": field_size_known,
        "field_size_runner_object_mismatches": field_size_mismatches,
        "duplicate_runner_names": duplicate_runner_names,
        "provider_total": payload.get("total"),
        "provider_limit": payload.get("limit"),
        "provider_skip": payload.get("skip"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a saved free racecard JSON snapshot.")
    parser.add_argument("snapshot", type=Path, help="Path to the raw racecard JSON file")
    parser.add_argument("--output", type=Path, help="Optional path for a JSON audit report")
    args = parser.parse_args()

    payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
    report = audit_payload(payload)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
