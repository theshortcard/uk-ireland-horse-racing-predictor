"""Create a conservative, non-betting staging CSV from the Kaggle results archive.

This importer does not certify the archive, verify results, or convert SP to odds.
Only explicitly recognised GB/IRE courses are included; unknown/overseas venues
are counted and excluded. Output rows remain UNVERIFIED for manual review.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

# Explicit allowlists. Course aliases are normalised by removing bracketed
# surface/region notes before matching; unrecognised names are never guessed.
IRE_COURSES = {
    "bellewstown", "clonmel", "cork", "downpatrick", "dundalk", "fairyhouse",
    "galway", "gowran park", "kilbeggan", "killarney", "laytown",
    "leopardstown", "limerick", "listowel", "naas", "navan", "punchestown",
    "roscommon", "sligo", "thurles", "tipperary", "tramore", "wexford",
    "curragh", "the curragh",
}
GB_COURSES = {
    "ascot", "ayr", "bangor-on-dee", "bangor", "bath", "beverley", "brighton",
    " Carlisle".strip(), "cartmel", "catterick", "chelmsford", "cheltenham",
    "chepstow", "chester", "doncaster", "epsom", "exeter", "fakenham",
    "fontwell", "goodwood", "hamilton", "haydock", "hereford", "hexham",
    "huntingdon", "kelso", "kempton", "leicester", "lingfield", "ludlow",
    "market rasen", "musselburgh", "newbury", "newcastle", "newmarket",
    "newton abbot", "nottingham", "perth", "plumpton", "pontefract",
    "redcar", "ripon", "salisbury", "sandown", "sedgefield", "southwell",
    "stratford", "taunton", "thirsk", "uttoxeter", "warwick", "wetherby",
    "wincanton", "windsor", "wolverhampton", "worcester", "york",
    "folkestone", "great yarmouth", "leicester", "towcester",
}
OUTPUT_FIELDS = [
    "race_id", "date", "course", "country", "off_time", "horse",
    "horse_age", "official_rating", "days_since_run", "odds_decimal",
    "odds_source", "odds_captured_at", "source_name", "retrieved_at",
    "finish_position", "runner_status", "result_status", "result_source",
    "result_verified_at", "source_sp", "source_finish_code",
]
SOURCE_NAME = "Kaggle community archive: deltaromeo/horse-racing-results-ukireland-2015-2025"


def clean(value: object) -> str:
    return str(value or "").strip()


def normalise_course(value: str) -> str:
    value = re.sub(r"\s*\([^)]*\)", "", clean(value)).strip()
    return re.sub(r"\s+", " ", value).casefold()


def classify_course(value: str) -> str | None:
    raw = clean(value)
    # Explicit country suffix is useful only when it agrees with a known course.
    suffix_ire = bool(re.search(r"\(IRE\)\s*$", raw, re.I))
    name = normalise_course(raw)
    if name in IRE_COURSES:
        return "IRE"
    if name in GB_COURSES and not suffix_ire:
        return "GB"
    return None


def parse_date(value: str) -> str:
    value = clean(value)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def convert_row(row: dict[str, str], source_file: str) -> dict[str, str] | None:
    course = clean(row.get("course"))
    country = classify_course(course)
    date = parse_date(row.get("date", ""))
    horse = clean(row.get("horse"))
    race_id = clean(row.get("race_id"))
    off_time = clean(row.get("off"))
    if not (country and date and horse and race_id and off_time):
        return None

    raw_pos = clean(row.get("pos"))
    numeric_position = raw_pos if re.fullmatch(r"\d+(?:\.0)?", raw_pos) else ""
    # SP is preserved only as source context. It is never a decimal price.
    return {
        "race_id": race_id,
        "date": date,
        "course": course,
        "country": country,
        "off_time": off_time,
        "horse": horse,
        "horse_age": clean(row.get("age")),
        "official_rating": clean(row.get("or")).replace("–", "").replace("-", ""),
        "days_since_run": "",
        "odds_decimal": "",
        "odds_source": "",
        "odds_captured_at": "",
        "source_name": SOURCE_NAME,
        "retrieved_at": "",
        "finish_position": numeric_position,
        "runner_status": "RUNNER",
        "result_status": "UNVERIFIED",
        "result_source": "",
        "result_verified_at": "",
        "source_sp": clean(row.get("sp")),
        "source_finish_code": "" if numeric_position else raw_pos,
    }


def stage_files(inputs: list[Path], output: Path) -> Counter:
    counts: Counter = Counter()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for input_path in inputs:
            with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as in_handle:
                reader = csv.DictReader(in_handle)
                if not reader.fieldnames:
                    counts["files_without_header"] += 1
                    continue
                missing = {"date", "course", "race_id", "off", "horse", "pos", "sp", "or"} - set(reader.fieldnames)
                if missing:
                    counts["files_missing_required_columns"] += 1
                    counts["missing_column_names"] += len(missing)
                    continue
                for row in reader:
                    counts["source_rows"] += 1
                    if clean(row.get("date")).casefold() == "date" and clean(row.get("horse")).casefold() == "horse":
                        counts["repeated_header_rows"] += 1
                        continue
                    country = classify_course(clean(row.get("course")))
                    if country is None:
                        counts["excluded_unknown_or_overseas_course"] += 1
                        continue
                    converted = convert_row(row, input_path.name)
                    if converted is None:
                        counts["excluded_invalid_or_missing_core_fields"] += 1
                        continue
                    counts[f"included_{country}_rows"] += 1
                    if not converted["finish_position"]:
                        counts["non_numeric_finish_codes"] += 1
                    if converted["source_sp"]:
                        counts["source_sp_present_not_used_as_odds"] += 1
                    writer.writerow(converted)
    counts["staged_rows"] = counts["included_GB_rows"] + counts["included_IRE_rows"]
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage recognised GB/IRE archive results without treating SP as pre-race odds.")
    parser.add_argument("--input", action="append", required=True, help="Source CSV; repeat for each archive CSV")
    parser.add_argument("--output", default="data/external/kaggle_results_staging.csv")
    args = parser.parse_args()
    inputs = [Path(item) for item in args.input]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        parser.error("Input file(s) not found: " + ", ".join(missing))
    counts = stage_files(inputs, Path(args.output))
    print("Staging complete. These are unverified records, not approved backtest data.")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value:,}")
    print("odds_decimal is intentionally blank; source_sp is retained separately.")
    print("result_status is UNVERIFIED; result_source and result_verified_at are intentionally blank.")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
