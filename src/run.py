"""Command-line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from .io_utils import read_racecard, validate_racecard
from .report import build_report, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a UK/Irish horse racing baseline report.")
    parser.add_argument("--input", default="data/sample_racecard.csv", help="Path to racecard CSV")
    parser.add_argument("--output", default="reports/daily_report.md", help="Path for Markdown report")
    args = parser.parse_args()

    rows = read_racecard(args.input)
    issues = validate_racecard(rows)
    report = build_report(rows, issues)
    write_report(report, args.output)
    print(f"Report written to {Path(args.output)}")
    if issues:
        print(f"Completed with {len(issues)} data-quality warning(s).")
        return 1
    print("Completed with no structural validation issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
