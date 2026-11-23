"""CSV input and validation helpers."""
from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = {
    "race_id", "date", "course", "country", "off_time", "horse",
    "horse_age", "official_rating", "odds_decimal",
}
ALLOWED_COUNTRIES = {"GB", "IRE"}


def read_racecard(path: str | Path) -> list[dict[str, str]]:
    """Read a racecard CSV and return rows as dictionaries."""
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV is empty or has no header row.")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        return [dict(row) for row in reader]


def validate_racecard(rows: list[dict[str, str]]) -> list[str]:
    """Return human-readable data-quality issues; an empty list means valid."""
    issues: list[str] = []
    seen: set[tuple[str, str]] = set()
    if not rows:
        return ["No runners found in the racecard."]

    for line, row in enumerate(rows, start=2):
        for field in ("race_id", "date", "course", "country", "off_time", "horse"):
            if not (row.get(field) or "").strip():
                issues.append(f"Line {line}: {field} is blank.")

        race_id = (row.get("race_id") or "").strip()
        horse = (row.get("horse") or "").strip()
        key = (race_id, horse.casefold())
        if race_id and horse and key in seen:
            issues.append(f"Line {line}: duplicate horse '{horse}' in race '{race_id}'.")
        if race_id and horse:
            seen.add(key)

        country = (row.get("country") or "").strip().upper()
        if country and country not in ALLOWED_COUNTRIES:
            issues.append(f"Line {line}: country must be GB or IRE, got '{country}'.")

        race_date = (row.get("date") or "").strip()
        if race_date:
            try:
                datetime.strptime(race_date, "%Y-%m-%d")
            except ValueError:
                issues.append(f"Line {line}: date must use YYYY-MM-DD.")

        off_time = (row.get("off_time") or "").strip()
        if off_time:
            valid_time = False
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    datetime.strptime(off_time, fmt)
                    valid_time = True
                    break
                except ValueError:
                    pass
            if not valid_time:
                issues.append(f"Line {line}: off_time must use HH:MM or HH:MM:SS.")

        for field in ("horse_age", "official_rating", "odds_decimal"):
            value = (row.get(field) or "").strip()
            if not value:
                continue
            try:
                number = float(value)
            except ValueError:
                issues.append(f"Line {line}: {field} must be numeric.")
                continue
            if not math.isfinite(number):
                issues.append(f"Line {line}: {field} must be a finite number.")
                continue
            if field == "odds_decimal" and number <= 1:
                issues.append(f"Line {line}: decimal odds must be greater than 1.0.")
            if field == "horse_age" and number <= 0:
                issues.append(f"Line {line}: horse_age must be positive.")
            if field == "official_rating" and number < 0:
                issues.append(f"Line {line}: official_rating cannot be negative.")
    return issues
