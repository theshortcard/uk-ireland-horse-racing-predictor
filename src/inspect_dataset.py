"""Low-memory, read-only inspection of an unfamiliar racing CSV dataset."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROLE_ALIASES = {
    "date": {"date", "race_date", "meeting_date"},
    "country": {"country", "nation", "region"},
    "course": {"course", "racecourse", "track", "venue"},
    "horse": {"horse", "horse_name", "runner", "runner_name"},
    "odds": {"odds", "price", "sp", "starting_price", "odds_decimal"},
    "finish": {"finish_position", "position", "pos", "placing", "result"},
    "race_id": {"race_id", "raceid", "event_id"},
}


def inspect_csv(path: str | Path) -> dict[str, object]:
    """Inspect headers, completeness and examples without retaining the dataset."""
    file_path = Path(path)
    column_counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    country_counts: Counter[str] = Counter()
    date_min: str | None = None
    date_max: str | None = None
    row_count = 0

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV is empty or has no header row.")
        headers = [name.strip() if name else "" for name in reader.fieldnames]
        if any(not name for name in headers):
            raise ValueError("CSV contains a blank column name.")
        if len(set(headers)) != len(headers):
            raise ValueError("CSV contains duplicate column names.")
        reader.fieldnames = headers
        lowered = {name.casefold(): name for name in headers}
        country_col = next((lowered[a] for a in ROLE_ALIASES["country"] if a in lowered), None)
        date_col = next((lowered[a] for a in ROLE_ALIASES["date"] if a in lowered), None)

        for row in reader:
            if None in row:
                raise ValueError(f"CSV row {reader.line_num} has more values than the header.")
            row_count += 1
            for name in headers:
                value = (row.get(name) or "").strip()
                if value:
                    column_counts[name] += 1
                    samples = examples.setdefault(name, [])
                    if len(samples) < 3 and value not in samples:
                        samples.append(value)
            if country_col and (row.get(country_col) or "").strip():
                country_counts[(row[country_col] or "").strip()] += 1
            if date_col and (row.get(date_col) or "").strip():
                date_value = (row[date_col] or "").strip()
                date_min = date_value if date_min is None else min(date_min, date_value)
                date_max = date_value if date_max is None else max(date_max, date_value)

    if row_count == 0:
        raise ValueError("CSV contains a header but no data rows.")

    roles = {
        role: next((lowered[a] for a in aliases if a in lowered), None)
        for role, aliases in ROLE_ALIASES.items()
    }
    columns = []
    for name in headers:
        count = column_counts[name]
        columns.append({
            "name": name,
            "non_empty": count,
            "missing": row_count - count,
            "examples": examples.get(name, []),
        })
    return {
        "file": file_path.name,
        "rows": row_count,
        "columns": columns,
        "roles": roles,
        "country_counts": dict(sorted(country_counts.items())),
        "date_min": date_min,
        "date_max": date_max,
    }


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Dataset inspection",
        "",
        "> Read-only structural inspection. This does not verify provenance, licensing, correctness, or suitability for model training.",
        "",
        f"- File: `{summary['file']}`",
        f"- Data rows: {summary['rows']}",
        f"- Columns: {len(summary['columns'])}",
        "",
        "## Detected likely fields",
        "",
    ]
    for role, column in summary["roles"].items():
        lines.append(f"- {role}: {column or 'not detected'}")
    lines.extend(["", "## Coverage clues", ""])
    if summary["country_counts"]:
        lines.append("- Country values: " + ", ".join(f"{k} ({v})" for k, v in summary["country_counts"].items()))
    else:
        lines.append("- Country values: no recognised country column")
    if summary["date_min"] and summary["date_max"]:
        lines.append(f"- Date values observed: {summary['date_min']} to {summary['date_max']}")
    else:
        lines.append("- Date values observed: no recognised date column")
    lines.extend(["", "## Column completeness", "", "| Column | Non-empty | Missing | Examples |", "|---|---:|---:|---|"])
    for column in summary["columns"]:
        examples = "; ".join(str(value).replace("|", "\\|") for value in column["examples"])
        lines.append(f"| {column['name']} | {column['non_empty']} | {column['missing']} | {examples} |")
    lines.extend([
        "",
        "## Next checks before importing",
        "",
        "1. Confirm the dataset version, licence, upstream source acknowledgements and permitted model-development use.",
        "2. Check whether each row represents a runner, a race, or another entity.",
        "3. Verify country codes, date/time conventions, race identifiers, non-runner codes and finishing-position meanings.",
        "4. Confirm which ratings and prices were available before the race. Do not use post-race fields as predictors.",
        "5. Only then write a documented field mapping into the project historical CSV format.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an unfamiliar racing CSV without importing it.")
    parser.add_argument("--input", required=True, help="Path to source CSV")
    parser.add_argument("--output", default="reports/dataset_inspection.md", help="Markdown report path")
    args = parser.parse_args()
    summary = inspect_csv(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(summary), encoding="utf-8")
    print(f"Inspected {summary['rows']} rows and {len(summary['columns'])} columns. Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
