"""CSV input and validation helpers."""
from __future__ import annotations

import csv
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
        race_id = (row.get("race_id") or "").strip()
        horse = (row.get("horse") or "").strip()
        if not race_id:
            issues.append(f"Line {line}: race_id is blank.")
        if not horse:
            issues.append(f"Line {line}: horse is blank.")
        key = (race_id, horse.casefold())
        if race_id and horse and key in seen:
            issues.append(f"Line {line}: duplicate horse '{horse}' in race '{race_id}'.")
        seen.add(key)

        country = (row.get("country") or "").strip().upper()
        if country and country not in ALLOWED_COUNTRIES:
            issues.append(f"Line {line}: country must be GB or IRE, got '{country}'.")

        for field in ("horse_age", "official_rating", "odds_decimal"):
            value = (row.get(field) or "").strip()
            if value:
                try:
                    number = float(value)
                except ValueError:
                    issues.append(f"Line {line}: {field} must be numeric.")
                    continue
                if field == "odds_decimal" and number <= 1:
                    issues.append(f"Line {line}: decimal odds must be greater than 1.0.")
                if field == "horse_age" and number <= 0:
                    issues.append(f"Line {line}: horse_age must be positive.")
    return issues
