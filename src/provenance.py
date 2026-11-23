"""Audit source provenance and price timing for supplied racing CSV data."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .io_utils import read_racecard

RACE_TIMEZONE = ZoneInfo("Europe/London")


def _parse_aware_timestamp(value: str, field: str, line: int, issues: list[str]) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        issues.append(f"Line {line}: {field} is missing.")
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        issues.append(f"Line {line}: {field} must be an ISO-8601 timestamp.")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        issues.append(f"Line {line}: {field} must include a timezone offset (for example +00:00 or Z).")
        return None
    return parsed


def audit_provenance(rows: list[dict[str, str]]) -> list[str]:
    """Return provenance and pre-off price timing issues for racecard/history rows."""
    issues: list[str] = []
    for line, row in enumerate(rows, start=2):
        source_name = (row.get("source_name") or "").strip()
        if not source_name:
            issues.append(f"Line {line}: source_name is missing.")

        retrieved_at = _parse_aware_timestamp(row.get("retrieved_at", ""), "retrieved_at", line, issues)

        odds_value = (row.get("odds_decimal") or "").strip()
        if odds_value:
            if not (row.get("odds_source") or "").strip():
                issues.append(f"Line {line}: odds_source is missing for a priced runner.")
            captured_at = _parse_aware_timestamp(
                row.get("odds_captured_at", ""), "odds_captured_at", line, issues
            )
            if captured_at and retrieved_at and captured_at > retrieved_at:
                issues.append(f"Line {line}: odds_captured_at is later than retrieved_at.")

            try:
                race_date = datetime.strptime((row.get("date") or "").strip(), "%Y-%m-%d").date()
                off_time = datetime.strptime((row.get("off_time") or "").strip(), "%H:%M").time()
            except ValueError:
                try:
                    race_date = datetime.strptime((row.get("date") or "").strip(), "%Y-%m-%d").date()
                    off_time = datetime.strptime((row.get("off_time") or "").strip(), "%H:%M:%S").time()
                except ValueError:
                    race_date = None
                    off_time = None
            if captured_at and race_date and off_time:
                scheduled_off = datetime.combine(race_date, off_time, tzinfo=RACE_TIMEZONE)
                if captured_at >= scheduled_off:
                    issues.append(f"Line {line}: odds_captured_at is at or after the scheduled off time.")

        if (row.get("finish_position") or "").strip():
            if not (row.get("result_source") or "").strip():
                issues.append(f"Line {line}: result_source is missing for a completed result.")
            _parse_aware_timestamp(
                row.get("result_verified_at", ""), "result_verified_at", line, issues
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit racing CSV source and odds timestamp provenance.")
    parser.add_argument("--input", required=True, help="Racecard or historical CSV")
    args = parser.parse_args()
    rows = read_racecard(args.input)
    issues = audit_provenance(rows)
    if issues:
        print("Provenance audit found issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"Provenance audit passed for {len(rows)} runner rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
