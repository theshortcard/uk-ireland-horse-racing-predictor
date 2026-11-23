"""Command-line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from .io_utils import read_racecard, validate_racecard
from .provenance import audit_provenance
from .report import build_report, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a UK/Irish horse racing baseline report.")
    parser.add_argument("--input", default="data/sample_racecard.csv", help="Path to racecard CSV")
    parser.add_argument("--output", default="reports/daily_report.md", help="Path for Markdown report")
    args = parser.parse_args()

    rows = read_racecard(args.input)
    validation_issues = validate_racecard(rows)
    provenance_issues = audit_provenance(rows)
    report = build_report(rows, validation_issues)
    write_report(report, args.output)
    print(f"Report written to {Path(args.output)}")

    if validation_issues:
        print(f"Completed with {len(validation_issues)} structural validation warning(s).")
    else:
        print("Structural validation passed.")

    if provenance_issues:
        print(f"PRICE PROVENANCE GATE BLOCKED: {len(provenance_issues)} issue(s). Market edge and EV are suppressed.")
        return 1

    print("Price provenance checks passed. Market comparisons may be shown only for complete priced fields.")
    if validation_issues:
        return 1
    print("Completed with no structural or provenance issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
