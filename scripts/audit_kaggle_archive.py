#!/usr/bin/env python3
"""Read-only audit of the Kaggle UK/IRE horse-racing archive."""
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(sys.argv[1])
IRISH_COURSES = {
    "bellewstown", "clonmel", "cork", "downpatrick", "dundalk", "fairyhouse",
    "galway", "gowran park", "kilbeggan", "killarney", "laytown",
    "leopardstown", "limerick", "listowel", "naas", "navan", "punchestown",
    "roscommon", "sligo", "thurles", "tipperary", "tramore", "wexford",
    "the curragh", "curragh",
}
EXPECTED = {"date", "course", "race_id", "off", "horse", "pos", "sp", "or"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d")

def clean(value):
    return (value or "").strip()

def parse_date(value):
    value = clean(value)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None

def audit_csv(path):
    print(f"\n=== CSV AUDIT: {path.relative_to(ROOT)} ===", flush=True)
    counts = Counter()
    courses = Counter()
    country_courses = Counter()
    dates = []
    race_keys = set()
    duplicate_runners = 0
    repeated_headers = 0
    invalid_dates = 0
    samples = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        normalized = {x.strip().lower() for x in fields}
        print("Columns:", len(fields), "| required core fields present:", sorted(EXPECTED & normalized), flush=True)
        if not EXPECTED.issubset(normalized):
            print("WARNING: expected fields missing:", sorted(EXPECTED - normalized), flush=True)
        for row in reader:
            counts["raw_rows"] += 1
            # Some old archive CSVs repeat their header as the first data row.
            if clean(row.get("date")).lower() == "date" and clean(row.get("horse")).lower() == "horse":
                repeated_headers += 1
                continue
            counts["data_rows"] += 1
            date = parse_date(row.get("date"))
            if date:
                dates.append(date)
            else:
                invalid_dates += 1
            course = clean(row.get("course"))
            if course:
                courses[course] += 1
                if course.casefold() in IRISH_COURSES:
                    country_courses["IRE_known_course_rows"] += 1
                else:
                    country_courses["course_not_in_Irish_allowlist_rows"] += 1
            for key in ("horse", "race_id", "pos", "sp", "or", "course", "date"):
                if not clean(row.get(key)):
                    counts[f"missing_{key}"] += 1
            race_id = clean(row.get("race_id"))
            if race_id and date and course and clean(row.get("off")):
                race_key = (date, course.casefold(), clean(row.get("off")), race_id)
                race_keys.add(race_key)
            horse = clean(row.get("horse"))
            if horse and date and course and race_id:
                # Count duplicates of identical horse entries within a date/course/race.
                runner_key = (date, course.casefold(), race_id, horse.casefold())
                if runner_key in seen_runners:
                    duplicate_runners += 1
                else:
                    seen_runners.add(runner_key)
            sp = clean(row.get("sp"))
            if sp:
                counts["sp_present"] += 1
                if re.fullmatch(r"\d+/\d+[A-Za-z]?", sp):
                    counts["sp_fractional_like"] += 1
                elif re.fullmatch(r"\d+(\.\d+)?", sp):
                    counts["sp_decimal_like"] += 1
                else:
                    counts["sp_other_format"] += 1
            pos = clean(row.get("pos")).upper()
            if pos:
                counts["pos_present"] += 1
                if pos in {"F", "PU", "UR", "BD", "RO", "RR", "DSQ", "SU", "REF"}:
                    counts["pos_non_numeric_status"] += 1
                elif not re.fullmatch(r"\d+(\.\d+)?", pos):
                    counts["pos_other_status"] += 1
            if len(samples) < 3:
                samples.append({k: clean(row.get(k))[:80] for k in ("date", "course", "race_id", "off", "horse", "pos", "sp", "or")})
            if counts["data_rows"] % 500000 == 0:
                print(f"Scanned {counts['data_rows']:,} data rows...", flush=True)
    # Use a local set scoped to this CSV, initialized lazily for duplicate detection.
    print("Rows:", json.dumps(dict(counts), sort_keys=True), flush=True)
    print("Repeated header rows skipped:", repeated_headers, "| invalid/unparsed dates:", invalid_dates, flush=True)
    print("Date range:", (min(dates), max(dates)) if dates else "none", flush=True)
    print("Distinct race keys (date/course/off/race_id):", len(race_keys), "| duplicate runner keys:", duplicate_runners, flush=True)
    print("Course rows by provisional classification:", json.dumps(dict(country_courses), sort_keys=True), flush=True)
    print("Most common courses:", json.dumps(courses.most_common(30), ensure_ascii=False), flush=True)
    print("Example records:", json.dumps(samples, ensure_ascii=False), flush=True)

def audit_html(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    text = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    print(f"\n=== HTML SUMMARY: {path.relative_to(ROOT)} ===")
    print("Bytes:", path.stat().st_size)
    print("Title:", re.sub(r"\s+", " ", title.group(1)).strip() if title else "not found")
    print("Text preview:", text[:1800])

def audit_db(path):
    print(f"\n=== SQLITE AUDIT: {path.relative_to(ROOT)} ===", flush=True)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        for (table,) in tables:
            safe = table.replace('"', '""')
            cols = [r[1] for r in con.execute(f'PRAGMA table_info("{safe}")')]
            row_count = con.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0]
            print("Table:", table, "| rows:", f"{row_count:,}", "| columns:", ", ".join(cols), flush=True)
            if {"date", "course", "race_id", "horse"}.issubset(set(cols)):
                date_range = con.execute(f'SELECT MIN(date), MAX(date) FROM "{safe}"').fetchone()
                print("Stored date range:", date_range, flush=True)
    finally:
        con.close()

def main():
    print("AUDIT LIMITATIONS: course-based Ireland identification uses a conservative explicit course-name allowlist; unlisted courses are not automatically confirmed as GB.", flush=True)
    for path in sorted(ROOT.rglob("*.csv")):
        if path.is_file():
            global seen_runners
            seen_runners = set()
            audit_csv(path)
    for path in sorted(ROOT.rglob("*.db")) + sorted(ROOT.rglob("*.sqlite")) + sorted(ROOT.rglob("*.sqlite3")):
        if path.is_file():
            audit_db(path)
    for name in ("README.md", "2025.html", "2026.html"):
        path = ROOT / name
        if path.exists():
            if path.suffix.lower() == ".html":
                audit_html(path)
            else:
                print(f"\n=== {name} ===")
                print(path.read_text(encoding="utf-8", errors="replace")[:4000])
    metadata = ROOT / "dataset-metadata.json"
    if metadata.exists():
        print("\n=== DATASET METADATA (selected fields) ===")
        try:
            data = json.loads(metadata.read_text(encoding="utf-8"))
            for key in ("title", "id", "licenses", "licensesName", "subtitle", "description", "keywords", "lastUpdated"):
                if key in data:
                    print(f"{key}: {str(data[key])[:3000]}")
        except Exception as exc:
            print("Metadata parse error:", repr(exc))

if __name__ == "__main__":
    main()
