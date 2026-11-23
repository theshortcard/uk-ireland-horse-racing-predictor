"""Prepare a research-only subset from staged UK/IRE results.

This utility never verifies results, approves source rights, or creates betting
prices. It preserves source fields and sends rows with unresolved identity,
duplicate runners, invalid timing, or unresolved finishing outcomes to quarantine.
The prepared output is explicitly research-only and must not be used for ROI.
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

REQUIRED = {
    "race_id", "date", "course", "country", "off_time", "horse",
    "finish_position", "result_status", "source_finish_code",
}
NON_FINISH_CODES = {
    "PU", "UR", "F", "BD", "RO", "SU", "REF", "DSQ", "CO", "L",
    "RR", "B", "U", "S", "LFT",
}
OUTPUT_EXTRA = ["preparation_decision", "preparation_reasons", "research_win_outcome"]


def valid_time(value: str) -> bool:
    return bool(re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value.strip()))


def finish_outcome(row: dict[str, str]) -> tuple[str, str]:
    position = (row.get("finish_position") or "").strip()
    code = (row.get("source_finish_code") or "").strip().upper()
    if position:
        try:
            parsed = float(position)
            if parsed > 0 and parsed.is_integer():
                return "known", "1" if int(parsed) == 1 else "0"
        except ValueError:
            pass
        return "invalid", ""
    if code in {"NR", "WD", "VOID"}:
        return "excluded", ""
    if code in NON_FINISH_CODES:
        return "known", "0"
    if not code or code == "-":
        return "missing", ""
    return "unknown", ""


def race_key(row: dict[str, str]) -> str:
    return "|".join((
        (row.get("date") or "").strip(),
        (row.get("country") or "").strip().upper(),
        (row.get("course") or "").strip().casefold(),
        (row.get("off_time") or "").strip(),
        (row.get("race_id") or "").strip(),
    ))


def prepare_file(input_path: Path, prepared_path: Path, quarantine_path: Path) -> Counter:
    counts: Counter = Counter()
    prepared_path.parent.mkdir(parents=True, exist_ok=True)
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="racing-prepare-") as temp_dir:
        db = sqlite3.connect(str(Path(temp_dir) / "seen.sqlite"))
        db.execute("CREATE TABLE seen (race_key TEXT, horse_key TEXT, PRIMARY KEY (race_key, horse_key))")
        with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as src:
            reader = csv.DictReader(src)
            if not reader.fieldnames:
                raise ValueError("Input CSV has no header")
            missing = REQUIRED - set(reader.fieldnames)
            if missing:
                raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
            fields = list(reader.fieldnames) + OUTPUT_EXTRA
            with prepared_path.open("w", encoding="utf-8", newline="") as good_handle, quarantine_path.open("w", encoding="utf-8", newline="") as bad_handle:
                good = csv.DictWriter(good_handle, fieldnames=fields)
                bad = csv.DictWriter(bad_handle, fieldnames=fields)
                good.writeheader()
                bad.writeheader()
                for row in reader:
                    counts["rows_seen"] += 1
                    reasons = []
                    race_id = (row.get("race_id") or "").strip()
                    course = (row.get("course") or "").strip()
                    horse = (row.get("horse") or "").strip()
                    country = (row.get("country") or "").strip().upper()
                    race_date = (row.get("date") or "").strip()
                    off_time = (row.get("off_time") or "").strip()

                    if not race_id or not course or not horse:
                        reasons.append("missing_race_identity")
                    if country not in {"GB", "IRE"}:
                        reasons.append("invalid_country")
                    try:
                        date.fromisoformat(race_date)
                    except ValueError:
                        reasons.append("invalid_date")
                    if not valid_time(off_time):
                        reasons.append("invalid_off_time")

                    outcome_status, outcome = finish_outcome(row)
                    if outcome_status == "excluded":
                        reasons.append("non_runner_or_void_result")
                    elif outcome_status == "missing":
                        reasons.append("missing_finish_outcome")
                    elif outcome_status == "invalid":
                        reasons.append("invalid_finish_position")
                    elif outcome_status == "unknown":
                        reasons.append("unrecognised_finish_code")

                    if not reasons:
                        key = race_key(row)
                        horse_key = " ".join(horse.casefold().split())
                        inserted = db.execute(
                            "INSERT OR IGNORE INTO seen(race_key, horse_key) VALUES (?, ?)",
                            (key, horse_key),
                        )
                        if inserted.rowcount == 0:
                            reasons.append("duplicate_runner_in_race")

                    row["preparation_decision"] = "QUARANTINE" if reasons else "RESEARCH_ONLY"
                    row["preparation_reasons"] = ";".join(reasons)
                    row["research_win_outcome"] = outcome if not reasons else ""
                    if reasons:
                        counts["quarantined_rows"] += 1
                        for reason in reasons:
                            counts[f"quarantine_reason|{reason}"] += 1
                        bad.writerow(row)
                    else:
                        counts["research_only_rows"] += 1
                        counts["research_win_outcome_1" if outcome == "1" else "research_win_outcome_0"] += 1
                        good.writerow(row)
                    if counts["rows_seen"] % 100000 == 0:
                        db.commit()
        db.commit()
        counts["unique_race_horse_pairs"] = db.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
        db.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Split staged results into research-only rows and quarantine.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--quarantine", required=True)
    args = parser.parse_args()
    source = Path(args.input)
    if not source.is_file():
        parser.error(f"Input file not found: {source}")
    try:
        counts = prepare_file(source, Path(args.prepared), Path(args.quarantine))
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print("Preparation complete. RESEARCH_ONLY rows remain unverified and are not approved for training or ROI.")
    for key, value in sorted(counts.items()):
        if not key.startswith("quarantine_reason|"):
            print(f"{key}: {value:,}")
    print("Quarantine reasons:")
    for key, value in sorted(counts.items()):
        if key.startswith("quarantine_reason|"):
            print(f"  {key.split('|', 1)[1]}: {value:,}")
    print(f"Prepared research-only CSV: {args.prepared}")
    print(f"Quarantine CSV: {args.quarantine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
